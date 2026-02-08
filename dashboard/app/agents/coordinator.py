"""
Coordinator Agent - Central orchestration for the agent swarm

Responsibilities:
- Routes tasks to appropriate specialized agents
- Resolves conflicts (e.g., multiple agents needing same resource)
- Monitors task progress and agent health
- Handles escalations to human
"""

import sys
import os
from typing import Dict, List, Optional
import time

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../tools'))

from .base_agent import BaseAgent
from core.agent_registry import Task, AgentStatus
from core.message_bus import MessageType


class CoordinatorAgent(BaseAgent):
    """
    Central coordination agent that routes tasks and manages the swarm
    """

    def __init__(self, agent_id: str = "coordinator-1"):
        super().__init__(agent_id=agent_id, role="coordinator")

        # Workflow registry for task routing
        self.workflow_registry: Dict = {}

        # Task queue for pending tasks
        self.task_queue: List[Dict] = []

    def startup(self) -> bool:
        """Start coordinator with additional workflow registry loading"""
        if not super().startup():
            return False

        # Load workflow registry
        self._load_workflow_registry()

        print(f"[{self.agent_id}] Coordinator ready to route tasks")
        return True

    def _load_workflow_registry(self):
        """Load workflow registry from config"""
        import yaml

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.workflow_registry = config.get('workflow_registry', {})
        print(f"[{self.agent_id}] Loaded {len(self.workflow_registry)} workflow mappings")

    def execute_task(self, task: Task):
        """
        Execute coordinator task - mainly routing and monitoring

        Args:
            task: Task to execute
        """
        try:
            print(f"[{self.agent_id}] Executing task: {task.description}")

            # Coordinator tasks are typically routing or monitoring
            if "route" in task.description.lower():
                self._route_task(task)
            elif "monitor" in task.description.lower():
                self._monitor_agents()
            elif "health" in task.description.lower():
                self._health_check()
            else:
                # Generic task - analyze and route
                self._analyze_and_route(task)

            self.complete_task(task.task_id)

        except Exception as e:
            error_msg = f"Coordinator task failed: {str(e)}"
            print(f"[{self.agent_id}] {error_msg}")
            self.fail_task(task.task_id, error_msg)

    def route_incoming_task(self, task_description: str, priority: str = "normal") -> bool:
        """
        Route an incoming task to appropriate agent

        Args:
            task_description: Description of the task
            priority: Task priority (urgent, high, normal, low)

        Returns:
            True if task was routed successfully
        """
        try:
            print(f"\n[{self.agent_id}] === Routing New Task ===")
            print(f"Description: {task_description}")
            print(f"Priority: {priority}")

            # 1. Analyze task to determine type
            task_type = self._analyze_task_type(task_description)
            print(f"Task type: {task_type}")

            # 2. Find appropriate workflow
            workflow_info = self._find_workflow(task_type)
            if not workflow_info:
                print(f"[{self.agent_id}] No workflow found for task type: {task_type}")
                return False

            print(f"Workflow: {workflow_info.get('workflow', 'N/A')}")

            # 3. Find available agent
            assigned_agent = workflow_info.get('assigned_agent')
            available_agents = self.registry.get_available_agents()

            # Filter for role match
            target_agents = [a for a in available_agents if a.role == assigned_agent]

            if not target_agents:
                print(f"[{self.agent_id}] No available agents for role: {assigned_agent}")
                # Queue task for later
                self.task_queue.append({
                    'description': task_description,
                    'priority': priority,
                    'task_type': task_type,
                    'workflow': workflow_info
                })
                return False

            # Choose agent with least workload
            target_agent = min(target_agents, key=lambda a: len(a.current_tasks))
            print(f"Assigned to: {target_agent.agent_id}")

            # 4. Create task and send assignment
            import uuid
            task = Task(
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                workflow=workflow_info['workflow'],
                description=task_description,
                priority=priority,
                assigned_at=time.time()
            )

            # Send TASK_ASSIGNMENT message
            self.send_message(
                to_agent=target_agent.agent_id,
                message_type=MessageType.TASK_ASSIGNMENT,
                payload={
                    'task_id': task.task_id,
                    'workflow': task.workflow,
                    'description': task.description,
                    'priority': task.priority,
                    'required_tools': workflow_info.get('required_tools', [])
                },
                priority=priority
            )

            # Update context store
            self.context_store.append_to_list('workflows.in_progress', task.task_id)

            print(f"[{self.agent_id}] ✓ Task routed successfully\n")
            return True

        except Exception as e:
            print(f"[{self.agent_id}] Error routing task: {e}")
            return False

    def _analyze_task_type(self, description: str) -> str:
        """
        Analyze task description to determine task type

        Args:
            description: Task description

        Returns:
            Task type string
        """
        description_lower = description.lower()

        # Check for keywords
        if any(word in description_lower for word in ['add', 'create', 'implement', 'new feature']):
            if 'watch' in description_lower or 'android' in description_lower:
                return 'add_watch_feature'
            else:
                return 'add_dashboard_feature'

        elif any(word in description_lower for word in ['fix', 'bug', 'error', 'issue']):
            return 'fix_bug'

        elif any(word in description_lower for word in ['test', 'verify', 'validate']):
            return 'run_tests'

        elif any(word in description_lower for word in ['deploy', 'release', 'publish']):
            if 'dashboard' in description_lower:
                return 'deploy_dashboard'
            elif 'watch' in description_lower:
                return 'build_watch_app'
            else:
                return 'deploy_dashboard'

        elif any(word in description_lower for word in ['scrape', 'fetch', 'download']):
            return 'scrape_website'

        elif any(word in description_lower for word in ['post', 'tweet', 'social']):
            return 'send_slack_message'  # Or other social media

        # Default
        return 'add_dashboard_feature'

    def _find_workflow(self, task_type: str) -> Optional[Dict]:
        """Find workflow info for task type"""
        return self.workflow_registry.get(task_type)

    def _route_task(self, task: Task):
        """Route a task to appropriate agent"""
        self.route_incoming_task(task.description, task.priority)

    def _monitor_agents(self):
        """Monitor all active agents and their status"""
        print(f"\n[{self.agent_id}] === Agent Status Monitor ===")

        agents = self.registry.get_active_agents()

        for agent in agents:
            status_info = self.registry.get_agent_status(agent.agent_id)
            print(f"{agent.agent_id} ({agent.role}):")
            print(f"  Status: {status_info['status']}")
            print(f"  Tasks: {status_info['current_tasks']}/{agent.max_concurrent_tasks}")
            print(f"  Completed: {status_info['completed_tasks']}")
            print(f"  Failed: {status_info['failed_tasks']}")
            print()

    def _health_check(self):
        """Perform system health check"""
        print(f"\n[{self.agent_id}] === System Health Check ===")

        stats = self.registry.get_system_stats()

        print(f"Total Agents: {stats['total_agents']}")
        print(f"Active Tasks: {stats['active_tasks']}")
        print(f"Completed: {stats['completed_tasks']}")
        print(f"Failed: {stats['failed_tasks']}")
        print(f"\nAgents by Status:")
        for status, count in stats['agents_by_status'].items():
            print(f"  {status}: {count}")
        print()

    def _analyze_and_route(self, task: Task):
        """Analyze task and route to appropriate agent"""
        self.route_incoming_task(task.description, task.priority)

    def process_queued_tasks(self):
        """Process any queued tasks if agents become available"""
        if not self.task_queue:
            return

        print(f"[{self.agent_id}] Processing {len(self.task_queue)} queued tasks")

        # Try to route queued tasks
        successfully_routed = []
        for queued_task in self.task_queue:
            if self.route_incoming_task(
                queued_task['description'],
                queued_task['priority']
            ):
                successfully_routed.append(queued_task)

        # Remove successfully routed tasks
        for task in successfully_routed:
            self.task_queue.remove(task)

        if successfully_routed:
            print(f"[{self.agent_id}] Routed {len(successfully_routed)} queued tasks")


# Example usage and testing
if __name__ == "__main__":
    # Create coordinator
    coordinator = CoordinatorAgent()

    # Start coordinator in separate thread
    import threading
    coordinator_thread = threading.Thread(target=coordinator.run, daemon=True)
    coordinator_thread.start()

    # Wait for startup
    time.sleep(2)

    # Test routing some tasks
    print("\n" + "="*50)
    print("TESTING COORDINATOR TASK ROUTING")
    print("="*50 + "\n")

    test_tasks = [
        ("Add dark mode toggle to watch app", "high"),
        ("Fix bug in dashboard API", "urgent"),
        ("Run integration tests", "normal"),
        ("Deploy dashboard to staging", "normal"),
    ]

    for description, priority in test_tasks:
        coordinator.route_incoming_task(description, priority)
        time.sleep(1)

    # Monitor agents
    time.sleep(2)
    coordinator._monitor_agents()
    coordinator._health_check()

    # Keep running
    try:
        while True:
            time.sleep(10)
            coordinator.process_queued_tasks()
    except KeyboardInterrupt:
        print("\nShutting down coordinator...")
        coordinator.shutdown()
