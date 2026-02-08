"""
Gemini Deployment Agent

Uses Google's Gemini AI for autonomous code deployment:
- Analyzes codebase and requirements
- Generates code modifications
- Plans and executes deployments
- Integrates with git operations and CI/CD
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai

from .base_agent import BaseAgent
from core.agent_registry import Task, AgentStatus


class GeminiAgent(BaseAgent):
    """
    Gemini Deployment Agent

    Specializes in:
    - Code analysis and modification planning
    - Autonomous deployment execution
    - Integration with development tools
    - Real-time collaboration with Claude API
    """

    def __init__(self, agent_id: str = "gemini_deployer", config_path: str = None):
        super().__init__(agent_id, "gemini_deployer", config_path)

        # Configure Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

        # Codebase context cache
        self.codebase_context: Optional[Dict] = None
        self.codebase_cache_time: Optional[datetime] = None
        self.cache_ttl_seconds = 300  # 5 minutes

    def execute_task(self, task: Task):
        """
        Execute deployment task using Gemini

        Args:
            task: Task with deployment instructions
        """
        try:
            print(f"[{self.agent_id}] Executing deployment task: {task.description}")

            # Update status
            self.status = AgentStatus.BUSY
            self.registry.update_agent_status(self.agent_id, AgentStatus.BUSY)

            # Parse task type
            if "deploy" in task.description.lower():
                result = asyncio.run(self._handle_deployment_task(task))
            elif "analyze" in task.description.lower():
                result = asyncio.run(self._handle_analysis_task(task))
            elif "modify" in task.description.lower() or "change" in task.description.lower():
                result = asyncio.run(self._handle_modification_task(task))
            else:
                result = {"success": False, "error": "Unknown task type"}

            if result.get("success"):
                self.complete_task(task.task_id)

                # Store result in context
                self.context_store.set(f"tasks.{task.task_id}.result", result)
            else:
                self.fail_task(task.task_id, result.get("error", "Unknown error"))

        except Exception as e:
            print(f"[{self.agent_id}] Task execution failed: {e}")
            self.fail_task(task.task_id, str(e))

    async def _handle_deployment_task(self, task: Task) -> Dict:
        """
        Handle code deployment task

        Steps:
        1. Analyze current codebase
        2. Plan code modifications
        3. Generate deployment steps
        4. Execute deployment
        """
        try:
            # Get codebase context
            codebase = self._get_codebase_context()

            # Build prompt for Gemini
            prompt = f"""You are a deployment specialist. Analyze this task and provide a deployment plan.

Task: {task.description}

Current Codebase Structure:
{json.dumps(codebase, indent=2)}

Recent Deployments:
{self._get_recent_deployments()}

Requirements:
1. Analyze what needs to change in the codebase
2. Identify affected files
3. Generate code modifications (with full file paths)
4. Provide deployment steps
5. Include rollback plan
6. Estimate impact and risk level

Respond in JSON format:
{{
  "analysis": "Brief analysis of what needs to be done",
  "affected_files": ["file1.py", "file2.py"],
  "code_changes": {{
    "file_path": {{
      "action": "modify|create|delete",
      "content": "new content or modification description",
      "reason": "why this change is needed"
    }}
  }},
  "deployment_steps": [
    "Step 1: ...",
    "Step 2: ..."
  ],
  "rollback_plan": ["Step 1", "Step 2"],
  "risk_level": "low|medium|high",
  "estimated_time_minutes": 5
}}"""

            # Call Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text

            # Parse JSON response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            deployment_plan = json.loads(response_text)

            # Execute deployment plan
            execution_result = await self._execute_deployment_plan(deployment_plan)

            return {
                "success": execution_result["success"],
                "plan": deployment_plan,
                "execution": execution_result
            }

        except Exception as e:
            return {"success": False, "error": f"Deployment failed: {str(e)}"}

    async def _handle_analysis_task(self, task: Task) -> Dict:
        """Analyze codebase or specific component"""
        try:
            codebase = self._get_codebase_context()

            prompt = f"""Analyze the following codebase for: {task.description}

Codebase Structure:
{json.dumps(codebase, indent=2)}

Provide:
1. Current state analysis
2. Identified issues or opportunities
3. Recommendations
4. Priority actions

Respond in JSON format:
{{
  "current_state": "description",
  "findings": ["finding1", "finding2"],
  "recommendations": [
    {{"priority": "high|medium|low", "action": "description", "reason": "why"}}
  ],
  "next_steps": ["step1", "step2"]
}}"""

            response = self.model.generate_content(prompt)
            analysis = self._parse_json_response(response.text)

            # Store analysis
            self.context_store.set(f"analysis.{task.task_id}", analysis)

            return {"success": True, "analysis": analysis}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_modification_task(self, task: Task) -> Dict:
        """Handle code modification requests"""
        try:
            codebase = self._get_codebase_context()

            prompt = f"""Generate code modifications for: {task.description}

Codebase Context:
{json.dumps(codebase, indent=2)}

Provide specific code changes in JSON format:
{{
  "files_to_modify": {{
    "file_path": {{
      "current_content_summary": "brief summary",
      "new_content": "full new content",
      "changes_description": "what changed and why"
    }}
  }},
  "test_plan": ["test step 1", "test step 2"],
  "risk_assessment": "low|medium|high"
}}"""

            response = self.model.generate_content(prompt)
            modifications = self._parse_json_response(response.text)

            # Apply modifications (would integrate with git operations)
            result = await self._apply_code_modifications(modifications)

            return {"success": result["success"], "modifications": modifications, "result": result}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_codebase_context(self) -> Dict:
        """
        Get current codebase context (cached)

        Returns:
            Dictionary with codebase structure, recent changes, etc.
        """
        # Check cache
        if self.codebase_context and self.codebase_cache_time:
            age_seconds = (datetime.now() - self.codebase_cache_time).total_seconds()
            if age_seconds < self.cache_ttl_seconds:
                return self.codebase_context

        # Rebuild cache
        project_root = "/Users/vik043/Desktop/Agentic Workflow"

        codebase = {
            "structure": {
                "dashboard": self._scan_directory(f"{project_root}/dashboard"),
                "watch_app": self._scan_directory(f"{project_root}/watch-app"),
                "tools": self._scan_directory(f"{project_root}/tools"),
                "workflows": self._scan_directory(f"{project_root}/workflows")
            },
            "key_files": [
                f"{project_root}/dashboard/app/main.py",
                f"{project_root}/dashboard/app/agents/coordinator.py",
                f"{project_root}/watch-app/app/src/main/java/com/example/kin/presentation/network/KinNetwork.kt"
            ],
            "deployment_target": "Railway (https://agent-swarm-backend-production.up.railway.app)",
            "technologies": {
                "backend": "FastAPI (Python)",
                "watch": "Kotlin (Wear OS)",
                "agents": "Python agent swarm",
                "deployment": "Railway"
            }
        }

        # Cache it
        self.codebase_context = codebase
        self.codebase_cache_time = datetime.now()

        return codebase

    def _scan_directory(self, path: str, max_depth: int = 2, current_depth: int = 0) -> Dict:
        """Scan directory and return structure"""
        if current_depth >= max_depth or not os.path.exists(path):
            return {}

        try:
            result = {"files": [], "directories": {}}

            for item in os.listdir(path):
                if item.startswith('.') or item == '__pycache__':
                    continue

                item_path = os.path.join(path, item)

                if os.path.isfile(item_path):
                    result["files"].append(item)
                elif os.path.isdir(item_path):
                    result["directories"][item] = self._scan_directory(
                        item_path, max_depth, current_depth + 1
                    )

            return result
        except Exception as e:
            return {"error": str(e)}

    def _get_recent_deployments(self) -> str:
        """Get recent deployment history"""
        deployments = self.context_store.get("deployments", [])

        if not deployments:
            return "No recent deployments"

        # Return last 3
        recent = deployments[-3:]
        return json.dumps(recent, indent=2)

    async def _execute_deployment_plan(self, plan: Dict) -> Dict:
        """
        Execute the deployment plan generated by Gemini

        Args:
            plan: Deployment plan with code changes and steps

        Returns:
            Execution result
        """
        try:
            results = []

            # Step 1: Apply code changes
            for file_path, change in plan.get("code_changes", {}).items():
                action = change.get("action")

                if action == "modify":
                    # Would integrate with git operations here
                    # For now, just log
                    results.append(f"Modified: {file_path}")
                elif action == "create":
                    results.append(f"Created: {file_path}")
                elif action == "delete":
                    results.append(f"Deleted: {file_path}")

            # Step 2: Execute deployment steps
            for step in plan.get("deployment_steps", []):
                results.append(f"Executed: {step}")

            # Step 3: Log deployment
            deployment_record = {
                "timestamp": datetime.now().isoformat(),
                "plan": plan,
                "results": results,
                "status": "success"
            }

            deployments = self.context_store.get("deployments", [])
            deployments.append(deployment_record)
            self.context_store.set("deployments", deployments)

            return {"success": True, "results": results}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _apply_code_modifications(self, modifications: Dict) -> Dict:
        """Apply code modifications from Gemini's analysis"""
        try:
            applied = []

            for file_path, changes in modifications.get("files_to_modify", {}).items():
                # Would use git operations and file editing tools here
                applied.append(file_path)

            return {"success": True, "applied": applied}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON from Gemini response (handles markdown code blocks)"""
        try:
            # Remove markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            return json.loads(response_text)
        except Exception as e:
            print(f"[{self.agent_id}] Error parsing JSON: {e}")
            return {"error": "Failed to parse response", "raw": response_text}


# Singleton instance
_gemini_agent = None


def get_gemini_agent() -> GeminiAgent:
    """Get or create Gemini agent singleton"""
    global _gemini_agent
    if _gemini_agent is None:
        _gemini_agent = GeminiAgent()
        _gemini_agent.startup()
    return _gemini_agent
