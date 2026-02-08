# Discover Workflows

## Objective
Dynamically discover and validate available workflows based on current task requirements and agent capabilities.

## Required Inputs
- Task description or type (e.g., "add_feature", "fix_bug", "deploy_dashboard")
- Agent role and capabilities
- Optional: Specific workflow category (core, development, testing, deployment, connectors, data)

## Execution Steps

1. **Parse Task Requirements**
   - Extract task type from description or explicit type parameter
   - Identify keywords that indicate required capabilities:
     - "add", "create", "implement" → development workflow
     - "fix", "debug", "resolve" → bug fixing workflow
     - "deploy", "release", "publish" → deployment workflow
     - "test", "verify", "validate" → testing workflow
     - "scrape", "fetch", "process" → data workflow
   - Determine priority level (urgent, high, normal, low)

2. **Query Workflow Registry**
   - Tool: `config/agent_roles.yaml`
   - Look up workflow_registry section
   - Find workflows matching the task type
   - Example: task type "add_watch_feature" → workflow "workflows/development/android_development.md"
   - Get assigned_agent for the task type
   - Check if current agent matches assigned_agent or has required capabilities

3. **List Available Workflows**
   - Tool: `tools/core/workflow_parser.py`
   - Use `list_workflows()` method to get all workflows in relevant category
   - Filter workflows based on agent's configured workflows from agent_roles.yaml
   - For developer_agent: development/*, some testing/* workflows
   - For tester_agent: testing/*, some development/code_review workflows
   - For deployer_agent: deployment/* workflows
   - For data_processor: data/*, connectors/* workflows
   - For coordinator: core/* workflows

4. **Validate Prerequisites**
   - For each potential workflow:
     - Tool: `tools/core/workflow_parser.py`
     - Parse workflow using `parse_workflow()` method
     - Extract required_tools from workflow definition
     - Check if each required tool exists in `tools/` directory
     - Verify tool files are executable/importable
   - Check if dependencies are met:
     - Required credentials available in `.env`
     - External services accessible (Redis, APIs, etc.)
     - Required project files exist (for android_development, check watch-app/ exists)

5. **Load Workflow Content**
   - Tool: `tools/core/workflow_parser.py`
   - Parse the selected workflow markdown file
   - Extract structured information:
     - Objective
     - Required inputs
     - Execution steps (with tools and sub-workflows)
     - Expected outputs
     - Edge cases
   - Create WorkflowDefinition object
   - Validate workflow has all required sections

6. **Estimate Execution Complexity**
   - Count number of execution steps
   - Identify sub-workflow calls (recursive complexity)
   - Estimate duration based on:
     - Number of steps: simple (1-3), moderate (4-7), complex (8+)
     - Tool execution time (fast: file operations, slow: builds, deployments)
     - External dependencies (APIs, network calls)
   - Categorize as: quick (<5 min), moderate (5-30 min), long (30+ min)

7. **Return Execution Plan**
   - Provide structured execution plan:
     ```json
     {
       "workflow_path": "workflows/development/add_feature.md",
       "workflow_title": "Add Feature",
       "objective": "Add new feature to codebase",
       "required_tools": ["git_operations.py", "run_pytest.py"],
       "estimated_duration": "moderate",
       "dependencies": ["git", "pytest"],
       "steps_count": 6,
       "prerequisites_met": true
     }
     ```
   - Include any warnings about missing tools or unmet prerequisites
   - Suggest alternative workflows if primary choice is unavailable

## Expected Outputs
- Validated workflow ready for execution
- WorkflowDefinition object with parsed content
- List of required tools with paths
- Execution complexity estimate
- Understanding of dependencies on other agents (if sub-workflows require coordination)

## Edge Cases
- **No matching workflow found**:
  - Search for generic workflows (e.g., `core/handle_failure.md` as fallback)
  - Request human guidance via escalation
  - Attempt to use most similar workflow with modifications
  - Log the gap and suggest creating new workflow

- **Multiple workflows match**:
  - Use priority system from agent_roles.yaml
  - Prefer more specific workflows over generic ones
  - Check workflow_registry for explicit task type mapping
  - If still ambiguous, ask coordinator agent to decide
  - Default to simplest workflow (fewest steps)

- **Required tools missing**:
  - Log detailed information about missing tools
  - Check if tool can be created programmatically
  - Search for alternative tools that provide same capability
  - If tool is critical, escalate to coordinator
  - Request tool creation workflow: `workflows/development/create_tool.md`

- **Workflow file corrupted or invalid**:
  - Attempt to parse with error recovery
  - Check git history for last valid version
  - Fall back to similar workflow in same category
  - Log corruption details for human review

- **Circular workflow dependencies**:
  - Detect when workflow A calls workflow B which calls workflow A
  - Break cycle by using simplified version of one workflow
  - Log warning about circular dependency
  - Suggest refactoring workflows to remove cycle

- **Prerequisites not met**:
  - List specific unmet prerequisites
  - Attempt automatic resolution (install dependencies, start services)
  - If cannot auto-resolve, provide clear instructions to human
  - Estimate time to resolve and update task priority

## Learning Loop
- Track which workflows are most frequently used
- Identify workflows that consistently fail prerequisite checks
- Document common missing tools and add to standard tool set
- Note task types that don't have matching workflows (gaps)
- Update workflow_registry with new discovered patterns
- If multiple workflows often match, refine task type detection logic
