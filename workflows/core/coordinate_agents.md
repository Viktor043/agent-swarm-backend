# Coordinate Agents

## Objective
Coordinate multiple agents working on interdependent tasks without creating bottlenecks. Route incoming tasks to appropriate specialized agents and resolve conflicts.

## Required Inputs
- Task from user, watch device, scheduled job, or another agent
- Current system context from context store
- Agent registry with active agents and their status

## Execution Steps

1. **Analyze Incoming Task**
   - Parse task description and extract:
     - Task type (feature, bug, deployment, test, data processing)
     - Priority level (urgent, high, normal, low)
     - Required capabilities
     - Deadline or time constraints (if any)
   - Break down complex tasks into subtasks if needed:
     - "Add feature X to watch app" → [design, implement, test, build]
     - "Deploy dashboard with new connector" → [test, build, deploy, verify]
   - Identify dependencies between subtasks (must be done in order vs can parallelize)
   - Estimate total effort and timeline

2. **Discover Appropriate Workflow**
   - Workflow: `workflows/core/discover_workflows.md`
   - For each (sub)task, identify the workflow to execute
   - Verify workflow exists and is valid
   - Check required tools are available
   - Log workflow selection reasoning for transparency

3. **Check Agent Availability**
   - Tool: `tools/core/agent_registry.py`
   - Query active agents: `get_active_agents()`
   - For each (sub)task:
     - Get agents with required capability: `get_agents_by_capability()`
     - Check agent capacity: `get_available_agents()`
     - Filter agents by status (IDLE or BUSY with available capacity)
   - Rank available agents by:
     - Current workload (prefer less busy agents)
     - Past success rate on similar tasks
     - Specialization match (perfect fit > partial fit)

4. **Check for Resource Conflicts**
   - Query context store for potential conflicts:
     - Git operations: Check if any agent is working on same branch
     - File operations: Check if any agent is modifying same files
     - Deployments: Ensure no deployment currently in progress
     - External services: Check rate limits and availability
   - If conflicts detected:
     - Implement queueing system for sequential execution
     - Communicate wait times to requesting agent
     - Update task priority if urgent

5. **Assign Tasks to Agents**
   - Tool: `tools/core/message_bus.py`
   - For each (sub)task and selected agent:
     - Create Task object with:
       - task_id (unique identifier)
       - workflow path
       - description
       - priority
       - required inputs
       - deadline
     - Tool: `tools/core/agent_registry.py`
     - Assign task to agent: `assign_task(agent_id, task)`
     - Tool: `tools/core/message_bus.py`
     - Send TASK_ASSIGNMENT message to agent:
       ```json
       {
         "message_type": "TASK_ASSIGNMENT",
         "payload": {
           "task_id": "task_123",
           "workflow": "development/add_feature",
           "description": "Add dark mode toggle",
           "priority": "high",
           "inputs": {...},
           "requires_response": true
         }
       }
       ```
   - Log all task assignments for audit trail

6. **Monitor Progress**
   - Subscribe to status updates from assigned agents via message bus
   - Update context store as tasks progress:
     - `workflows.in_progress` when task starts
     - `workflows.completed` when task finishes successfully
     - `workflows.failed` when task fails
   - Track elapsed time for each task
   - Update agent status in registry based on messages:
     - STATUS_UPDATE messages → update agent.last_heartbeat
     - TASK_COMPLETE messages → call `complete_task()`
     - TASK_FAILED messages → call `fail_task()`
   - Monitor for stuck tasks (no update in 15 minutes):
     - Send health check message to agent
     - If no response, mark agent as ERROR status
     - Reassign task to another agent

7. **Handle Agent Responses and Escalations**
   - Process REQUEST messages from agents:
     - Requests for human approval on critical actions
     - Requests for additional resources or tools
     - Requests for clarification on requirements
   - Process ESCALATION messages:
     - Task cannot be completed automatically
     - Multiple failures on same task
     - Security-sensitive operations requiring human oversight
   - Forward escalations to human via:
     - Slack notification (urgent)
     - Email (normal priority)
     - Dashboard alert (for awareness)

8. **Resolve Conflicts and Deadlocks**
   - Detect circular dependencies:
     - Agent A waiting for Agent B, Agent B waiting for Agent A
     - Use timeout mechanism to break deadlock
   - Resolve resource contention:
     - Implement priority-based queuing
     - Higher priority tasks get resources first
     - Communicate delays to lower priority tasks
   - Handle agent failures:
     - If agent becomes unresponsive, redistribute its tasks
     - Use `get_available_agents()` to find replacements
     - Preserve task context for seamless handoff

9. **Update System Context**
   - Tool: `tools/core/context_store.py`
   - After task completion, update relevant context:
     - `projects.watch-app.last_build` if watch app was built
     - `projects.dashboard.deployment_status` if dashboard was deployed
     - `metrics.total_tasks_completed` increment counter
     - `system.current_tasks` remove completed task
   - Log completion details for reporting
   - Update workflow learning notes if valuable insights gained

10. **Completion Verification**
    - For multi-step tasks, verify all subtasks completed successfully
    - Run integration checks if needed:
      - After feature addition, verify tests pass
      - After deployment, verify health checks pass
    - If any subtask failed:
      - Workflow: `workflows/core/handle_failure.md`
      - Decide whether to retry, rollback, or escalate
    - Send final status update to task requester
    - Update context store with final state

## Expected Outputs
- Tasks successfully distributed to appropriate agents
- Progress tracked and monitored in real-time
- Conflicts resolved or queued appropriately
- System context updated with current state
- Successful completion confirmed or failures escalated

## Edge Cases
- **No agents available for task**:
  - Queue task for later execution
  - Estimate wait time based on current agent workload
  - If urgent, notify human that system is at capacity
  - Consider starting additional agent instances if supported

- **Agent becomes unresponsive mid-task**:
  - Wait for heartbeat timeout (2 minutes)
  - Mark agent as ERROR status
  - Reassign incomplete task to another agent
  - Preserve task progress if possible (check git commits, partial outputs)
  - Log incident for post-mortem analysis

- **Circular dependencies detected**:
  - Break cycle by choosing one task to execute first
  - Use heuristics: higher priority, simpler task, less dependencies
  - Restructure tasks to remove circular dependency if possible
  - Log warning about suboptimal task decomposition

- **Resource contention (git branch conflicts)**:
  - Implement queue: first task gets branch, others wait
  - Estimate wait times and communicate to waiting agents
  - If urgent, suggest creating parallel branches
  - Monitor for deadlocks (mutual waiting)

- **All agents at maximum capacity**:
  - Queue new tasks with estimated start time
  - If critical task, check if lower priority tasks can be paused
  - Alert human if sustained high load
  - Suggest increasing agent capacity (more instances)

- **Task fails multiple times (3+)**:
  - Escalate to human with detailed failure history
  - Check if workflow needs updating
  - Verify prerequisites are actually met
  - Consider if task is fundamentally not automatable

- **Conflicting priorities**:
  - Use priority order: urgent > high > normal > low
  - Within same priority, use FIFO (first in, first out)
  - Allow human override of priorities via message bus
  - Balance fairness (don't starve low priority tasks indefinitely)

## Learning Loop
- Track which task assignments succeed vs fail
- Identify bottleneck agents (always at capacity)
- Note tasks that frequently cause conflicts
- Update workflow_registry if better agent assignments discovered
- Log average task completion times for capacity planning
- Identify patterns in escalations (same types of tasks consistently escalated)
- Refine conflict resolution heuristics based on outcomes
- Document unexpected edge cases and their solutions
