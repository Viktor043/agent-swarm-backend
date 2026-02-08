"""
Agent Registry - Track active agents and their status

Maintains a registry of all active agents in the swarm, their capabilities,
current tasks, and health status.
"""

import yaml
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path


class AgentStatus(Enum):
    """Status of an agent"""
    STARTING = "starting"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class Task:
    """Represents a task assigned to an agent"""
    task_id: str
    workflow: str
    description: str
    priority: str
    assigned_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed


@dataclass
class Agent:
    """Represents an agent in the swarm"""
    agent_id: str
    role: str
    capabilities: List[str]
    workflows: List[str]
    status: AgentStatus
    current_tasks: List[Task] = field(default_factory=list)
    completed_tasks: int = 0
    failed_tasks: int = 0
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    max_concurrent_tasks: int = 3
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert agent to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Agent':
        """Create agent from dictionary"""
        data['status'] = AgentStatus(data['status'])
        data['current_tasks'] = [
            Task(**task) if isinstance(task, dict) else task
            for task in data.get('current_tasks', [])
        ]
        return cls(**data)


class AgentRegistry:
    """
    Registry for tracking active agents

    Uses context store as backend for persistent storage.
    """

    def __init__(self, context_store, config_path: str = None):
        """
        Initialize agent registry

        Args:
            context_store: ContextStore instance for persistence
            config_path: Path to agent_roles.yaml config file
        """
        self.context_store = context_store

        if config_path is None:
            config_path = "/Users/vik043/Desktop/Agentic Workflow/config/agent_roles.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load agent configuration from YAML"""
        if not self.config_path.exists():
            return {"agents": {}}

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def register_agent(self, agent_id: str, role: str, capabilities: List[str] = None,
                      workflows: List[str] = None, metadata: Dict = None) -> bool:
        """
        Register a new agent in the system

        Args:
            agent_id: Unique identifier for the agent
            role: Agent role (coordinator, developer_agent, etc.)
            capabilities: List of capabilities (overrides config if provided)
            workflows: List of workflows (overrides config if provided)
            metadata: Additional metadata

        Returns:
            True if registration successful
        """
        # Check if agent already registered
        if self._is_registered(agent_id):
            return False

        # Get capabilities and workflows from config if not provided
        if role in self.config.get('agents', {}):
            role_config = self.config['agents'][role]
            if capabilities is None:
                capabilities = role_config.get('capabilities', [])
            if workflows is None:
                workflows = role_config.get('workflows', [])
            max_concurrent = role_config.get('max_concurrent_tasks', 3)
        else:
            if capabilities is None:
                capabilities = []
            if workflows is None:
                workflows = []
            max_concurrent = 3

        # Create agent object
        agent = Agent(
            agent_id=agent_id,
            role=role,
            capabilities=capabilities,
            workflows=workflows,
            status=AgentStatus.STARTING,
            max_concurrent_tasks=max_concurrent,
            metadata=metadata or {}
        )

        # Store in context
        self._save_agent(agent)

        # Add to active agents list
        active_agents = self.context_store.get_context("system.active_agents", [])
        active_agents.append(agent_id)
        self.context_store.set_context("system.active_agents", active_agents)

        return True

    def deregister_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the registry

        Args:
            agent_id: Agent to deregister

        Returns:
            True if successful
        """
        if not self._is_registered(agent_id):
            return False

        # Remove from active agents list
        active_agents = self.context_store.get_context("system.active_agents", [])
        if agent_id in active_agents:
            active_agents.remove(agent_id)
            self.context_store.set_context("system.active_agents", active_agents)

        # Delete agent data
        self.context_store.delete_context(f"agents.{agent_id}")

        return True

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get agent by ID

        Args:
            agent_id: Agent identifier

        Returns:
            Agent object or None if not found
        """
        agent_data = self.context_store.get_context(f"agents.{agent_id}")
        if agent_data:
            return Agent.from_dict(agent_data)
        return None

    def get_active_agents(self) -> List[Agent]:
        """
        Get all active agents

        Returns:
            List of Agent objects
        """
        agent_ids = self.context_store.get_context("system.active_agents", [])
        agents = []

        for agent_id in agent_ids:
            agent = self.get_agent(agent_id)
            if agent:
                agents.append(agent)

        return agents

    def get_agents_by_role(self, role: str) -> List[Agent]:
        """Get all agents with a specific role"""
        all_agents = self.get_active_agents()
        return [agent for agent in all_agents if agent.role == role]

    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        """Get all agents with a specific capability"""
        all_agents = self.get_active_agents()
        return [agent for agent in all_agents if capability in agent.capabilities]

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        agent.status = status
        agent.last_heartbeat = datetime.now().isoformat()
        self._save_agent(agent)
        return True

    def heartbeat(self, agent_id: str) -> bool:
        """
        Update agent's last heartbeat timestamp

        Args:
            agent_id: Agent sending heartbeat

        Returns:
            True if successful
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        agent.last_heartbeat = datetime.now().isoformat()
        self._save_agent(agent)
        return True

    def assign_task(self, agent_id: str, task: Task) -> bool:
        """
        Assign a task to an agent

        Args:
            agent_id: Agent to assign task to
            task: Task object

        Returns:
            True if assignment successful
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        # Check if agent has capacity
        if len(agent.current_tasks) >= agent.max_concurrent_tasks:
            return False

        # Add task to agent's current tasks
        task.assigned_at = datetime.now().isoformat()
        task.status = "pending"
        agent.current_tasks.append(task)
        agent.status = AgentStatus.BUSY
        self._save_agent(agent)

        return True

    def start_task(self, agent_id: str, task_id: str) -> bool:
        """Mark a task as started"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        for task in agent.current_tasks:
            if task.task_id == task_id:
                task.status = "in_progress"
                task.started_at = datetime.now().isoformat()
                self._save_agent(agent)
                return True

        return False

    def complete_task(self, agent_id: str, task_id: str) -> bool:
        """Mark a task as completed"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        # Find and remove task from current tasks
        task_to_complete = None
        for i, task in enumerate(agent.current_tasks):
            if task.task_id == task_id:
                task_to_complete = agent.current_tasks.pop(i)
                break

        if not task_to_complete:
            return False

        # Update task
        task_to_complete.status = "completed"
        task_to_complete.completed_at = datetime.now().isoformat()

        # Update agent stats
        agent.completed_tasks += 1

        # Update status
        if len(agent.current_tasks) == 0:
            agent.status = AgentStatus.IDLE

        self._save_agent(agent)

        # Store completed task in context
        self.context_store.append_to_list("workflows.completed", task_to_complete.task_id)

        return True

    def fail_task(self, agent_id: str, task_id: str, error_message: str = None) -> bool:
        """Mark a task as failed"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        # Find and remove task from current tasks
        task_to_fail = None
        for i, task in enumerate(agent.current_tasks):
            if task.task_id == task_id:
                task_to_fail = agent.current_tasks.pop(i)
                break

        if not task_to_fail:
            return False

        # Update task
        task_to_fail.status = "failed"
        task_to_fail.completed_at = datetime.now().isoformat()

        # Update agent stats
        agent.failed_tasks += 1

        # Update status
        if len(agent.current_tasks) == 0:
            agent.status = AgentStatus.IDLE

        self._save_agent(agent)

        # Store failed task in context
        self.context_store.append_to_list("workflows.failed", {
            "task_id": task_id,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        })

        return True

    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """
        Get detailed status of an agent

        Returns:
            Dictionary with agent status information
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        return {
            "agent_id": agent.agent_id,
            "role": agent.role,
            "status": agent.status.value,
            "current_tasks": len(agent.current_tasks),
            "completed_tasks": agent.completed_tasks,
            "failed_tasks": agent.failed_tasks,
            "capacity": f"{len(agent.current_tasks)}/{agent.max_concurrent_tasks}",
            "last_heartbeat": agent.last_heartbeat
        }

    def get_available_agents(self, capability: str = None) -> List[Agent]:
        """
        Get agents that are available to take on new tasks

        Args:
            capability: Optional capability filter

        Returns:
            List of available agents
        """
        all_agents = self.get_active_agents()
        available = []

        for agent in all_agents:
            # Check if agent has capacity
            if len(agent.current_tasks) < agent.max_concurrent_tasks:
                # Check status
                if agent.status in [AgentStatus.IDLE, AgentStatus.BUSY]:
                    # Check capability if specified
                    if capability is None or capability in agent.capabilities:
                        available.append(agent)

        return available

    def _is_registered(self, agent_id: str) -> bool:
        """Check if an agent is registered"""
        return self.context_store.get_context(f"agents.{agent_id}") is not None

    def _save_agent(self, agent: Agent):
        """Save agent to context store"""
        self.context_store.set_context(f"agents.{agent.agent_id}", agent.to_dict())

    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        agents = self.get_active_agents()

        total_tasks = 0
        total_completed = 0
        total_failed = 0

        for agent in agents:
            total_tasks += len(agent.current_tasks)
            total_completed += agent.completed_tasks
            total_failed += agent.failed_tasks

        return {
            "total_agents": len(agents),
            "active_tasks": total_tasks,
            "completed_tasks": total_completed,
            "failed_tasks": total_failed,
            "agents_by_status": {
                "idle": len([a for a in agents if a.status == AgentStatus.IDLE]),
                "busy": len([a for a in agents if a.status == AgentStatus.BUSY]),
                "error": len([a for a in agents if a.status == AgentStatus.ERROR]),
                "starting": len([a for a in agents if a.status == AgentStatus.STARTING])
            }
        }


# Example usage
if __name__ == "__main__":
    from context_store import ContextStore

    # Create context store
    context = ContextStore.create("json_file")

    # Create registry
    registry = AgentRegistry(context)

    # Register agents
    registry.register_agent("coord-1", "coordinator")
    registry.register_agent("dev-1", "developer_agent")
    registry.register_agent("test-1", "tester_agent")

    # Update status
    registry.update_agent_status("coord-1", AgentStatus.IDLE)
    registry.update_agent_status("dev-1", AgentStatus.IDLE)

    # Create and assign task
    task = Task(
        task_id="task_001",
        workflow="development/add_feature",
        description="Add dark mode toggle",
        priority="high"
    )
    registry.assign_task("dev-1", task)

    # Get system stats
    stats = registry.get_system_stats()
    print(f"System stats: {stats}")

    # Get available agents
    available = registry.get_available_agents()
    print(f"Available agents: {[a.agent_id for a in available]}")
