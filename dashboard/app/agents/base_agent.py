"""
Base Agent - Foundation class for all agents in the swarm

Provides common functionality for agent lifecycle, communication, and workflow execution.
"""

import sys
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import time

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../tools'))

from core.workflow_parser import WorkflowParser, WorkflowDefinition
from core.message_bus import MessageBus, Message, MessageType
from core.context_store import ContextStore
from core.agent_registry import AgentRegistry, AgentStatus, Task


class BaseAgent(ABC):
    """
    Base class for all agents in the swarm

    Provides:
    - Agent lifecycle management (startup, shutdown, heartbeat)
    - Message bus communication
    - Context store access
    - Workflow discovery and execution
    - Error handling and recovery
    """

    def __init__(self, agent_id: str, role: str, config_path: str = None):
        """
        Initialize base agent

        Args:
            agent_id: Unique identifier for this agent instance
            role: Agent role (coordinator, developer_agent, etc.)
            config_path: Path to agent_roles.yaml (optional)
        """
        self.agent_id = agent_id
        self.role = role
        self.status = AgentStatus.STARTING
        self.running = False
        self.config_path = config_path or "/Users/vik043/Desktop/Agentic Workflow/config/agent_roles.yaml"

        # Core systems (initialized in startup)
        self.context_store: Optional[ContextStore] = None
        self.message_bus: Optional[MessageBus] = None
        self.registry: Optional[AgentRegistry] = None
        self.workflow_parser: Optional[WorkflowParser] = None

        # Agent capabilities and workflows (loaded from config)
        self.capabilities: List[str] = []
        self.workflows: List[str] = []
        self.max_concurrent_tasks: int = 3

        # Current tasks
        self.current_tasks: List[Task] = []

        # Heartbeat thread
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.heartbeat_interval: int = 60  # seconds

    def startup(self) -> bool:
        """
        Start the agent and initialize all systems

        Returns:
            True if startup successful
        """
        try:
            print(f"[{self.agent_id}] Starting {self.role} agent...")

            # 1. Initialize core systems
            self._initialize_core_systems()

            # 2. Load configuration
            self._load_configuration()

            # 3. Register with system
            self._register_with_system()

            # 4. Load current context
            self._load_context()

            # 5. Discover available workflows
            self._discover_workflows()

            # 6. Subscribe to message bus
            self._subscribe_to_messages()

            # 7. Start heartbeat
            self._start_heartbeat()

            # 8. Update status to IDLE
            self.status = AgentStatus.IDLE
            self.registry.update_agent_status(self.agent_id, AgentStatus.IDLE)
            self.running = True

            print(f"[{self.agent_id}] ✓ Agent started successfully")
            return True

        except Exception as e:
            print(f"[{self.agent_id}] ✗ Startup failed: {e}")
            self.status = AgentStatus.ERROR
            return False

    def _initialize_core_systems(self):
        """Initialize context store, message bus, and registry"""
        # Create context store (JSON file for now, can switch to Redis)
        self.context_store = ContextStore.create("json_file")

        # Create message bus (in-memory for now, can switch to Redis)
        self.message_bus = MessageBus.create("in_memory")

        # Create agent registry
        self.registry = AgentRegistry(self.context_store, self.config_path)

        # Create workflow parser
        self.workflow_parser = WorkflowParser()

        print(f"[{self.agent_id}] Core systems initialized")

    def _load_configuration(self):
        """Load agent capabilities and workflows from config"""
        import yaml

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        if self.role in config.get('agents', {}):
            role_config = config['agents'][self.role]
            self.capabilities = role_config.get('capabilities', [])
            self.workflows = role_config.get('workflows', [])
            self.max_concurrent_tasks = role_config.get('max_concurrent_tasks', 3)

        print(f"[{self.agent_id}] Configuration loaded: {len(self.capabilities)} capabilities, {len(self.workflows)} workflows")

    def _register_with_system(self):
        """Register agent with the agent registry"""
        success = self.registry.register_agent(
            agent_id=self.agent_id,
            role=self.role,
            capabilities=self.capabilities,
            workflows=self.workflows
        )

        if not success:
            raise Exception("Failed to register with agent registry")

        print(f"[{self.agent_id}] Registered with system")

    def _load_context(self):
        """Load current system context"""
        active_agents = self.context_store.get_context("system.active_agents", [])
        current_tasks = self.context_store.get_context("system.current_tasks", [])

        print(f"[{self.agent_id}] Context loaded: {len(active_agents)} active agents, {len(current_tasks)} current tasks")

    def _discover_workflows(self):
        """Discover and cache available workflows"""
        # Get all workflows for this agent's role
        available_workflows = []
        for workflow_category in ['core', 'development', 'testing', 'deployment', 'connectors', 'data']:
            workflows = self.workflow_parser.list_workflows(workflow_category)
            available_workflows.extend(workflows)

        print(f"[{self.agent_id}] Discovered {len(available_workflows)} workflows")

    def _subscribe_to_messages(self):
        """Subscribe to message bus for task assignments"""
        def message_handler(message: Message):
            """Handle incoming messages"""
            try:
                if message.message_type == MessageType.TASK_ASSIGNMENT:
                    self._handle_task_assignment(message)
                elif message.message_type == MessageType.REQUEST:
                    self._handle_request(message)
                elif message.message_type == MessageType.BROADCAST:
                    self._handle_broadcast(message)
            except Exception as e:
                print(f"[{self.agent_id}] Error handling message: {e}")

        self.message_bus.subscribe_to_messages(self.agent_id, message_handler)
        print(f"[{self.agent_id}] Subscribed to message bus")

    def _start_heartbeat(self):
        """Start heartbeat thread to maintain registration"""
        def heartbeat_loop():
            while self.running:
                try:
                    self.registry.heartbeat(self.agent_id)
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    print(f"[{self.agent_id}] Heartbeat error: {e}")

        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        print(f"[{self.agent_id}] Heartbeat started")

    def _handle_task_assignment(self, message: Message):
        """Handle task assignment from coordinator"""
        payload = message.payload
        task = Task(
            task_id=payload.get('task_id'),
            workflow=payload.get('workflow'),
            description=payload.get('description'),
            priority=payload.get('priority', 'normal'),
            assigned_at=datetime.now().isoformat()
        )

        # Add to current tasks
        self.current_tasks.append(task)
        self.registry.assign_task(self.agent_id, task)
        self.status = AgentStatus.BUSY

        print(f"[{self.agent_id}] Task assigned: {task.task_id} - {task.description}")

        # Execute task (subclass implements)
        self.execute_task(task)

    def _handle_request(self, message: Message):
        """Handle request messages from other agents"""
        # Subclass can override
        pass

    def _handle_broadcast(self, message: Message):
        """Handle broadcast messages"""
        # Subclass can override
        pass

    @abstractmethod
    def execute_task(self, task: Task):
        """
        Execute a task (implemented by subclass)

        Args:
            task: Task to execute
        """
        pass

    def complete_task(self, task_id: str):
        """Mark task as completed"""
        self.registry.complete_task(self.agent_id, task_id)

        # Remove from current tasks
        self.current_tasks = [t for t in self.current_tasks if t.task_id != task_id]

        # Update status
        if len(self.current_tasks) == 0:
            self.status = AgentStatus.IDLE
            self.registry.update_agent_status(self.agent_id, AgentStatus.IDLE)

        print(f"[{self.agent_id}] Task completed: {task_id}")

    def fail_task(self, task_id: str, error_message: str):
        """Mark task as failed"""
        self.registry.fail_task(self.agent_id, task_id, error_message)

        # Remove from current tasks
        self.current_tasks = [t for t in self.current_tasks if t.task_id != task_id]

        # Update status
        if len(self.current_tasks) == 0:
            self.status = AgentStatus.IDLE
            self.registry.update_agent_status(self.agent_id, AgentStatus.IDLE)

        print(f"[{self.agent_id}] Task failed: {task_id} - {error_message}")

    def send_message(self, to_agent: str, message_type: MessageType, payload: Dict, priority: str = "normal"):
        """Send message to another agent"""
        msg_id = self.message_bus.publish_message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            priority=priority
        )
        return msg_id

    def broadcast(self, message_type: MessageType, payload: Dict, priority: str = "normal"):
        """Broadcast message to all agents"""
        msg_ids = self.message_bus.broadcast_message(
            from_agent=self.agent_id,
            message_type=message_type,
            payload=payload,
            priority=priority
        )
        return msg_ids

    def get_workflow(self, workflow_path: str) -> Optional[WorkflowDefinition]:
        """
        Get workflow definition by path

        Args:
            workflow_path: Path to workflow file (e.g., "core/agent_startup.md")

        Returns:
            WorkflowDefinition or None if not found
        """
        try:
            return self.workflow_parser.parse_workflow(workflow_path)
        except Exception as e:
            print(f"[{self.agent_id}] Error loading workflow {workflow_path}: {e}")
            return None

    def shutdown(self):
        """Shutdown agent gracefully"""
        print(f"[{self.agent_id}] Shutting down...")
        self.running = False

        # Deregister from system
        if self.registry:
            self.registry.deregister_agent(self.agent_id)

        # Wait for heartbeat thread to stop
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)

        print(f"[{self.agent_id}] Shutdown complete")

    def run(self):
        """
        Main agent loop - starts agent and keeps it running

        Call this to start the agent. It will run until shutdown() is called.
        """
        if not self.startup():
            return

        print(f"[{self.agent_id}] Entering main loop...")

        try:
            while self.running:
                # Agent is event-driven via message bus callbacks
                # Just keep alive and let callbacks handle work
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n[{self.agent_id}] Interrupted by user")
        finally:
            self.shutdown()


# Example usage
if __name__ == "__main__":
    # This is an abstract class, so we can't instantiate it directly
    # See coordinator.py, developer_agent.py, etc. for concrete implementations
    pass
