"""
Lovable Sync - Synchronize Lovable project with local environment

Provides tools to:
- Clone Lovable project from GitHub
- Sync local changes back to GitHub
- Analyze React component structure
- Maintain bidirectional sync between Lovable and local development
"""

import os
import subprocess
import json
from typing import Optional, Dict, List
from pathlib import Path


class LovableSync:
    """
    Sync Lovable-generated dashboard with local development environment
    """

    def __init__(self, config_path: str = None):
        """
        Initialize Lovable sync

        Args:
            config_path: Path to .env file with GitHub credentials
        """
        self.project_root = "/Users/vik043/Desktop/Agentic Workflow"
        self.lovable_local_path = os.path.join(self.project_root, "lovable-dashboard")

        # Load configuration
        self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]):
        """Load GitHub configuration from .env"""
        if config_path is None:
            config_path = os.path.join(self.project_root, ".env")

        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                for line in f:
                    if line.startswith('GITHUB_REPO='):
                        self.github_repo = line.split('=')[1].strip()
                    elif line.startswith('GITHUB_TOKEN='):
                        self.github_token = line.split('=')[1].strip()

    def clone_or_sync(self) -> str:
        """
        Clone Lovable project from GitHub or sync if already exists

        Returns:
            Path to local Lovable project
        """
        if os.path.exists(self.lovable_local_path):
            print(f"[LovableSync] Project exists, syncing...")
            return self.sync_from_github()
        else:
            print(f"[LovableSync] Cloning from GitHub...")
            return self.clone_from_github()

    def clone_from_github(self) -> str:
        """
        Clone Lovable project from GitHub

        Returns:
            Path to cloned project
        """
        try:
            # Construct GitHub URL with token
            if hasattr(self, 'github_token') and hasattr(self, 'github_repo'):
                repo_url = f"https://{self.github_token}@github.com/{self.github_repo}.git"
            else:
                # Fallback to SSH if no token
                repo_url = f"git@github.com:{getattr(self, 'github_repo', 'user/repo')}.git"

            # Clone repository
            subprocess.run(
                ["git", "clone", repo_url, self.lovable_local_path],
                check=True,
                capture_output=True
            )

            print(f"[LovableSync] ✓ Cloned to {self.lovable_local_path}")
            return self.lovable_local_path

        except subprocess.CalledProcessError as e:
            print(f"[LovableSync] ✗ Clone failed: {e.stderr.decode()}")
            raise

    def sync_from_github(self) -> str:
        """
        Sync local Lovable project with GitHub (pull latest)

        Returns:
            Path to synced project
        """
        try:
            os.chdir(self.lovable_local_path)

            # Pull latest changes
            subprocess.run(
                ["git", "pull", "origin", "main"],
                check=True,
                capture_output=True
            )

            print(f"[LovableSync] ✓ Synced from GitHub")
            return self.lovable_local_path

        except subprocess.CalledProcessError as e:
            print(f"[LovableSync] ✗ Sync failed: {e.stderr.decode()}")
            raise

    def push_to_github(self, branch: str = "main", commit_message: str = "Update from agent swarm"):
        """
        Push local changes to GitHub

        Args:
            branch: Branch to push to
            commit_message: Commit message
        """
        try:
            os.chdir(self.lovable_local_path)

            # Add all changes
            subprocess.run(["git", "add", "."], check=True)

            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True,
                capture_output=True
            )

            # Push
            subprocess.run(
                ["git", "push", "origin", branch],
                check=True,
                capture_output=True
            )

            print(f"[LovableSync] ✓ Pushed to GitHub: {branch}")

        except subprocess.CalledProcessError as e:
            # If no changes, that's okay
            if "nothing to commit" in e.stderr.decode():
                print(f"[LovableSync] No changes to push")
            else:
                print(f"[LovableSync] ✗ Push failed: {e.stderr.decode()}")
                raise

    def get_component_structure(self) -> Dict[str, List[str]]:
        """
        Analyze React component structure

        Returns:
            Dictionary mapping component names to file paths
        """
        components = {}

        if not os.path.exists(self.lovable_local_path):
            print(f"[LovableSync] Project not found, run clone_or_sync() first")
            return components

        # Find React components (typically in src/components or src/)
        src_path = os.path.join(self.lovable_local_path, "src")

        if os.path.exists(src_path):
            for root, dirs, files in os.walk(src_path):
                for file in files:
                    if file.endswith(('.tsx', '.jsx')):
                        component_name = file.replace('.tsx', '').replace('.jsx', '')
                        file_path = os.path.join(root, file)

                        if component_name not in components:
                            components[component_name] = []
                        components[component_name].append(file_path)

        print(f"[LovableSync] Found {len(components)} React components")
        return components

    def read_component(self, component_name: str) -> Optional[str]:
        """
        Read source code of a React component

        Args:
            component_name: Name of component (without extension)

        Returns:
            Component source code or None if not found
        """
        components = self.get_component_structure()

        if component_name in components:
            component_path = components[component_name][0]
            with open(component_path, 'r') as f:
                return f.read()

        return None

    def create_component(self, component_name: str, code: str, component_type: str = "tsx"):
        """
        Create a new React component

        Args:
            component_name: Name of component
            code: Component source code
            component_type: File extension (tsx or jsx)
        """
        components_dir = os.path.join(self.lovable_local_path, "src", "components")
        os.makedirs(components_dir, exist_ok=True)

        component_file = os.path.join(components_dir, f"{component_name}.{component_type}")

        with open(component_file, 'w') as f:
            f.write(code)

        print(f"[LovableSync] ✓ Created component: {component_name}")

    def get_project_info(self) -> Dict:
        """
        Get information about Lovable project

        Returns:
            Dictionary with project metadata
        """
        info = {
            "path": self.lovable_local_path,
            "exists": os.path.exists(self.lovable_local_path),
            "components": [],
            "dependencies": {}
        }

        if info["exists"]:
            # Get component list
            info["components"] = list(self.get_component_structure().keys())

            # Read package.json for dependencies
            package_json_path = os.path.join(self.lovable_local_path, "package.json")
            if os.path.exists(package_json_path):
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    info["dependencies"] = package_data.get("dependencies", {})

        return info


# Example usage
if __name__ == "__main__":
    sync = LovableSync()

    print("=== Lovable Sync Tool ===\n")

    # Clone or sync project
    print("1. Syncing Lovable project...")
    project_path = sync.clone_or_sync()
    print(f"   Project path: {project_path}\n")

    # Get project info
    print("2. Getting project info...")
    info = sync.get_project_info()
    print(f"   Components found: {len(info['components'])}")
    if info['components']:
        print(f"   Sample components: {info['components'][:5]}\n")

    # Get component structure
    print("3. Analyzing component structure...")
    components = sync.get_component_structure()
    for comp_name in list(components.keys())[:3]:
        print(f"   - {comp_name}: {components[comp_name][0]}")

    print("\n✓ Lovable sync tool ready for agent use")
