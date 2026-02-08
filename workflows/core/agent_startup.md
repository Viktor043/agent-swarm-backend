# Agent Startup

## Objective
Initialize an agent and prepare it for autonomous operation within the agent swarm.

## Required Inputs
- Agent role (coordinator, developer_agent, tester_agent, deployer_agent, data_processor)
- Agent ID (unique identifier for this agent instance)
- Configuration from `config/agent_roles.yaml`

## Execution Steps

1. **Load Configuration**
   - Tool: `tools/core/workflow_parser.py`
   - Read agent-specific configuration from `config/agent_roles.yaml`
   - Extract capabilities, workflows, and max_concurrent_tasks for the agent's role
   - Load API credentials from `.env` file
   - Verify all required environment variables are present

2. **Initialize Core Systems**
   - Tool: `tools/core/context_store.py`
   - Create or connect to context store (JSON file or Redis based on config)
   - Tool: `tools/core/message_bus.py`
   - Create or connect to message bus (in-memory or Redis based on config)
   - Verify connectivity to both systems

3. **Register with System**
   - Tool: `tools/core/agent_registry.py`
   - Register agent with the agent registry
   - Provide agent_id, role, capabilities, and workflows
   - Set initial status to STARTING
   - Add self to active agents list in context store

4. **Load Current Context**
   - Tool: `tools/core/context_store.py`
   - Fetch current system state:
     - Active agents: `system.active_agents`
     - Current tasks: `system.current_tasks`
     - Project states: `projects.watch-app` and `projects.dashboard`
   - Understand what other agents are doing
   - Check for any pending tasks assigned to this agent

5. **Discover Available Workflows**
   - Workflow: `workflows/core/discover_workflows.md`
   - Build internal map of executable workflows for this agent's role
   - Validate that required tools exist for each workflow
   - Cache workflow definitions for quick access

6. **Subscribe to Message Bus**
   - Tool: `tools/core/message_bus.py`
   - Subscribe to messages addressed to this agent
   - Subscribe to broadcast messages (all agents)
   - Set up message handler callback function
   - Begin listening for task assignments

7. **Update Status to IDLE**
   - Tool: `tools/core/agent_registry.py`
   - Update agent status from STARTING to IDLE
   - Send heartbeat to registry
   - Signal ready to accept tasks

8. **Enter Main Loop**
   - Enter listening state for task assignments
   - Monitor message bus for:
     - Task assignments from coordinator
     - Status requests
     - Broadcast notifications
   - Send heartbeat every 60 seconds to maintain registration
   - Process messages as they arrive

## Expected Outputs
- Agent operational and registered in agent registry
- Listening for tasks on message bus
- Context loaded and current
- Status: IDLE and ready to accept work
- Heartbeat mechanism active

## Edge Cases
- **If `.env` missing**: Log error with list of required environment variables, request human intervention, exit gracefully
- **If context store unavailable**: Operate in degraded mode with local state only, log warning, attempt reconnection every 30 seconds
- **If message bus down**: Fall back to polling database for tasks, log error, continue operation with reduced functionality
- **If agent_roles.yaml missing or invalid**: Use default configuration with minimal capabilities, log warning, continue with basic functionality
- **If another agent with same ID already registered**: Generate new unique ID by appending timestamp, log warning, continue with new ID
- **If no coordinator agent present**: Operate independently without central coordination, check for coordinator every 5 minutes

## Learning Loop
- Track common startup errors and solutions
- Document environment-specific quirks (macOS paths, Redis versions, etc.)
- Update this workflow with discovered dependencies
- If startup consistently fails at a specific step, add pre-flight checks earlier in the process
