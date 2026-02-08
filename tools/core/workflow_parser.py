"""
Workflow Parser - Parse and validate workflow markdown files

This tool reads workflow markdown files and extracts structured information
that agents can use to execute tasks deterministically.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    number: int
    description: str
    tool: Optional[str] = None
    workflow_reference: Optional[str] = None
    code_example: Optional[str] = None


@dataclass
class WorkflowDefinition:
    """Complete workflow definition parsed from markdown"""
    file_path: str
    title: str
    objective: str
    required_inputs: List[str] = field(default_factory=list)
    execution_steps: List[WorkflowStep] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    edge_cases: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    learning_notes: List[str] = field(default_factory=list)


class WorkflowParser:
    """Parse markdown workflow files into structured definitions"""

    def __init__(self, workflows_dir: str = None):
        """
        Initialize the workflow parser

        Args:
            workflows_dir: Root directory containing workflow files
                          Defaults to /Users/vik043/Desktop/Agentic Workflow/workflows/
        """
        if workflows_dir is None:
            workflows_dir = "/Users/vik043/Desktop/Agentic Workflow/workflows"
        self.workflows_dir = Path(workflows_dir)

    def parse_workflow(self, workflow_path: str) -> WorkflowDefinition:
        """
        Parse a workflow markdown file into a WorkflowDefinition

        Args:
            workflow_path: Relative path from workflows_dir (e.g., "core/agent_startup.md")
                          or absolute path to the workflow file

        Returns:
            WorkflowDefinition object with parsed content

        Raises:
            FileNotFoundError: If workflow file doesn't exist
            ValueError: If workflow format is invalid
        """
        # Handle both relative and absolute paths
        if os.path.isabs(workflow_path):
            file_path = Path(workflow_path)
        else:
            file_path = self.workflows_dir / workflow_path

        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self._parse_content(content, str(file_path))

    def _parse_content(self, content: str, file_path: str) -> WorkflowDefinition:
        """Parse markdown content into workflow definition"""

        # Extract title (first # heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Untitled Workflow"

        # Extract sections
        objective = self._extract_section(content, "Objective")
        required_inputs_text = self._extract_section(content, "Required Inputs")
        execution_steps_text = self._extract_section(content, "Execution Steps")
        expected_outputs_text = self._extract_section(content, "Expected Outputs")
        edge_cases_text = self._extract_section(content, "Edge Cases")
        learning_text = self._extract_section(content, "Learning Loop")

        # Parse lists
        required_inputs = self._extract_list_items(required_inputs_text)
        expected_outputs = self._extract_list_items(expected_outputs_text)
        edge_cases = self._extract_list_items(edge_cases_text)
        learning_notes = self._extract_list_items(learning_text)

        # Parse execution steps
        execution_steps = self._parse_execution_steps(execution_steps_text)

        # Extract tool requirements from steps
        required_tools = self._extract_tool_requirements(execution_steps)

        return WorkflowDefinition(
            file_path=file_path,
            title=title,
            objective=objective,
            required_inputs=required_inputs,
            execution_steps=execution_steps,
            expected_outputs=expected_outputs,
            edge_cases=edge_cases,
            required_tools=required_tools,
            learning_notes=learning_notes
        )

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content of a section by name"""
        # Match ## Section Name
        pattern = rf'^##\s+{re.escape(section_name)}\s*$(.*?)(?=^##\s|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_list_items(self, text: str) -> List[str]:
        """Extract bullet points or numbered list items from text"""
        if not text:
            return []

        items = []
        # Match both - bullets and numbered lists
        for match in re.finditer(r'^(?:[-*]|\d+\.)\s+(.+)$', text, re.MULTILINE):
            items.append(match.group(1).strip())

        return items

    def _parse_execution_steps(self, steps_text: str) -> List[WorkflowStep]:
        """Parse execution steps from the Execution Steps section"""
        if not steps_text:
            return []

        steps = []
        # Match numbered steps (1. Step description)
        step_pattern = r'^(\d+)\.\s+\*\*(.+?)\*\*\s*$(.*?)(?=^\d+\.|\Z)'

        for match in re.finditer(step_pattern, steps_text, re.MULTILINE | re.DOTALL):
            step_num = int(match.group(1))
            description = match.group(2).strip()
            step_content = match.group(3).strip()

            # Extract tool reference (- Tool: xxx)
            tool = None
            tool_match = re.search(r'-\s+Tool:\s+`?([^`\n]+)`?', step_content)
            if tool_match:
                tool = tool_match.group(1).strip()

            # Extract workflow reference (- Workflow: xxx)
            workflow_ref = None
            workflow_match = re.search(r'-\s+Workflow:\s+`?([^`\n]+)`?', step_content)
            if workflow_match:
                workflow_ref = workflow_match.group(1).strip()

            # Extract code examples (```...```)
            code_example = None
            code_match = re.search(r'```(?:\w+)?\n(.*?)\n```', step_content, re.DOTALL)
            if code_match:
                code_example = code_match.group(1).strip()

            steps.append(WorkflowStep(
                number=step_num,
                description=description,
                tool=tool,
                workflow_reference=workflow_ref,
                code_example=code_example
            ))

        return steps

    def _extract_tool_requirements(self, steps: List[WorkflowStep]) -> List[str]:
        """Extract unique list of required tools from workflow steps"""
        tools = set()
        for step in steps:
            if step.tool:
                tools.add(step.tool)
        return sorted(list(tools))

    def validate_workflow(self, workflow: WorkflowDefinition) -> List[str]:
        """
        Validate that a workflow has all required components

        Args:
            workflow: WorkflowDefinition to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not workflow.title or workflow.title == "Untitled Workflow":
            errors.append("Workflow must have a title")

        if not workflow.objective:
            errors.append("Workflow must define an objective")

        if not workflow.execution_steps:
            errors.append("Workflow must have at least one execution step")

        if not workflow.expected_outputs:
            errors.append("Workflow must define expected outputs")

        # Check that all referenced tools exist
        for tool in workflow.required_tools:
            tool_path = self._resolve_tool_path(tool)
            if not tool_path.exists():
                errors.append(f"Required tool not found: {tool}")

        return errors

    def _resolve_tool_path(self, tool_reference: str) -> Path:
        """
        Resolve a tool reference to an absolute path

        Args:
            tool_reference: Tool reference like "tools/core/message_bus.py"

        Returns:
            Absolute Path to the tool file
        """
        tools_dir = Path("/Users/vik043/Desktop/Agentic Workflow/tools")

        # Remove "tools/" prefix if present
        if tool_reference.startswith("tools/"):
            tool_reference = tool_reference[6:]

        return tools_dir / tool_reference

    def list_workflows(self, category: Optional[str] = None) -> List[str]:
        """
        List all available workflows, optionally filtered by category

        Args:
            category: Category subdirectory (e.g., "core", "development", "testing")

        Returns:
            List of workflow file paths relative to workflows_dir
        """
        if category:
            search_dir = self.workflows_dir / category
        else:
            search_dir = self.workflows_dir

        if not search_dir.exists():
            return []

        workflows = []
        for md_file in search_dir.rglob("*.md"):
            rel_path = md_file.relative_to(self.workflows_dir)
            workflows.append(str(rel_path))

        return sorted(workflows)

    def get_workflow_info(self, workflow_path: str) -> Dict[str, any]:
        """
        Get quick summary info about a workflow without full parsing

        Args:
            workflow_path: Relative path to workflow file

        Returns:
            Dictionary with title, objective, and required_tools
        """
        try:
            workflow = self.parse_workflow(workflow_path)
            return {
                "title": workflow.title,
                "objective": workflow.objective,
                "required_tools": workflow.required_tools,
                "num_steps": len(workflow.execution_steps),
                "file_path": workflow.file_path
            }
        except Exception as e:
            return {
                "title": "Error",
                "objective": f"Failed to parse: {str(e)}",
                "required_tools": [],
                "num_steps": 0,
                "file_path": workflow_path
            }


# Example usage
if __name__ == "__main__":
    parser = WorkflowParser()

    # List all workflows
    print("Available workflows:")
    for workflow_path in parser.list_workflows():
        print(f"  - {workflow_path}")

    # Example: Parse a specific workflow (when it exists)
    # workflow = parser.parse_workflow("core/agent_startup.md")
    # print(f"\nWorkflow: {workflow.title}")
    # print(f"Objective: {workflow.objective}")
    # print(f"Steps: {len(workflow.execution_steps)}")
    # print(f"Required tools: {workflow.required_tools}")
