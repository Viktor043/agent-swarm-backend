"""
Context Store - Shared context management for agent swarm

Provides persistent storage for system state that all agents can access.
Supports both Redis and JSON file backends.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Callable
from pathlib import Path
from datetime import datetime
import threading


class ContextStoreInterface(ABC):
    """Abstract interface for context store implementations"""

    @abstractmethod
    def get_context(self, path: str, default: Any = None) -> Any:
        """
        Get value at a specific context path

        Args:
            path: Dot-notation path (e.g., "system.active_agents")
            default: Default value if path doesn't exist

        Returns:
            Value at path or default
        """
        pass

    @abstractmethod
    def set_context(self, path: str, value: Any) -> bool:
        """
        Set value at a specific context path

        Args:
            path: Dot-notation path
            value: Value to set

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def update_context(self, path: str, updates: Dict) -> bool:
        """
        Update a dictionary at path with new values (merge)

        Args:
            path: Dot-notation path to dictionary
            updates: Dictionary of updates to merge

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def delete_context(self, path: str) -> bool:
        """Delete value at path"""
        pass

    @abstractmethod
    def snapshot_context(self) -> Dict:
        """Get complete snapshot of all context"""
        pass

    @abstractmethod
    def watch_context(self, path: str, callback: Callable[[Any], None]) -> None:
        """Watch for changes at a specific path (optional feature)"""
        pass


class JSONFileContextStore(ContextStoreInterface):
    """
    JSON file-based context store for development and testing

    Stores context in a JSON file on disk. Simple and portable,
    but not suitable for high-frequency updates or multi-process access.
    """

    def __init__(self, file_path: str = None, auto_save: bool = True):
        """
        Initialize JSON context store

        Args:
            file_path: Path to JSON file. Defaults to .tmp/context_store.json
            auto_save: Automatically save after each modification
        """
        if file_path is None:
            file_path = "/Users/vik043/Desktop/Agentic Workflow/.tmp/context_store.json"

        self.file_path = Path(file_path)
        self.auto_save = auto_save
        self.context: Dict = {}
        self.watchers: Dict[str, list] = {}  # path -> list of callbacks
        self.lock = threading.Lock()

        # Create parent directory if needed
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing context
        self._load()

    def _load(self):
        """Load context from JSON file"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r') as f:
                    self.context = json.load(f)
            except json.JSONDecodeError:
                # File is corrupted, start fresh
                self.context = {}
                self._save()
        else:
            # Initialize with default structure
            self.context = {
                "system": {
                    "active_agents": [],
                    "current_tasks": [],
                    "last_health_check": None,
                    "uptime_start": datetime.now().isoformat()
                },
                "projects": {
                    "watch-app": {
                        "branch": "main",
                        "last_build": None,
                        "test_coverage": 0.0
                    },
                    "dashboard": {
                        "branch": "main",
                        "deployment_status": "unknown",
                        "active_connectors": []
                    }
                },
                "workflows": {
                    "in_progress": [],
                    "completed": [],
                    "failed": []
                },
                "metrics": {
                    "total_tasks_completed": 0,
                    "total_failures": 0,
                    "average_task_duration": 0.0
                }
            }
            self._save()

    def _save(self):
        """Save context to JSON file"""
        with self.lock:
            try:
                # Write to temp file first (atomic write)
                temp_path = self.file_path.with_suffix('.tmp')
                with open(temp_path, 'w') as f:
                    json.dump(self.context, f, indent=2)

                # Rename temp file to actual file
                temp_path.replace(self.file_path)
            except Exception as e:
                print(f"Error saving context: {e}")

    def get_context(self, path: str, default: Any = None) -> Any:
        """Get value at path using dot notation"""
        with self.lock:
            keys = path.split('.')
            value = self.context

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value

    def set_context(self, path: str, value: Any) -> bool:
        """Set value at path using dot notation"""
        with self.lock:
            keys = path.split('.')
            current = self.context

            # Navigate to parent
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set value
            current[keys[-1]] = value

            if self.auto_save:
                self._save()

            # Trigger watchers
            self._trigger_watchers(path, value)

            return True

    def update_context(self, path: str, updates: Dict) -> bool:
        """Update dictionary at path with new values"""
        current_value = self.get_context(path, {})

        if not isinstance(current_value, dict):
            return False

        # Merge updates
        current_value.update(updates)
        return self.set_context(path, current_value)

    def delete_context(self, path: str) -> bool:
        """Delete value at path"""
        with self.lock:
            keys = path.split('.')
            current = self.context

            # Navigate to parent
            for key in keys[:-1]:
                if key not in current:
                    return False
                current = current[key]

            # Delete key
            if keys[-1] in current:
                del current[keys[-1]]

                if self.auto_save:
                    self._save()

                return True

            return False

    def snapshot_context(self) -> Dict:
        """Get complete snapshot of context"""
        with self.lock:
            # Return deep copy
            return json.loads(json.dumps(self.context))

    def watch_context(self, path: str, callback: Callable[[Any], None]) -> None:
        """Register a callback to be triggered when path changes"""
        if path not in self.watchers:
            self.watchers[path] = []
        self.watchers[path].append(callback)

    def _trigger_watchers(self, path: str, value: Any):
        """Trigger all watchers for a given path"""
        if path in self.watchers:
            for callback in self.watchers[path]:
                try:
                    callback(value)
                except Exception as e:
                    print(f"Error in watcher callback: {e}")

    def append_to_list(self, path: str, item: Any) -> bool:
        """Convenience method to append item to a list at path"""
        current_list = self.get_context(path, [])

        if not isinstance(current_list, list):
            return False

        current_list.append(item)
        return self.set_context(path, current_list)

    def remove_from_list(self, path: str, item: Any) -> bool:
        """Convenience method to remove item from a list at path"""
        current_list = self.get_context(path, [])

        if not isinstance(current_list, list):
            return False

        if item in current_list:
            current_list.remove(item)
            return self.set_context(path, current_list)

        return False

    def increment(self, path: str, amount: int = 1) -> bool:
        """Convenience method to increment a numeric value"""
        current_value = self.get_context(path, 0)

        if not isinstance(current_value, (int, float)):
            return False

        return self.set_context(path, current_value + amount)


class RedisContextStore(ContextStoreInterface):
    """
    Redis-based context store for production use

    Uses Redis hashes and keys for fast, distributed access.
    Suitable for multi-process/multi-server deployments.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "context"):
        """
        Initialize Redis context store

        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for all context keys
        """
        try:
            import redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
        except ImportError:
            raise ImportError("Redis package not installed. Run: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Could not connect to Redis: {e}")

        self.prefix = prefix

    def _make_key(self, path: str) -> str:
        """Convert dot-notation path to Redis key"""
        return f"{self.prefix}:{path}"

    def get_context(self, path: str, default: Any = None) -> Any:
        """Get value from Redis"""
        key = self._make_key(path)
        value = self.redis.get(key)

        if value is None:
            return default

        # Try to deserialize JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def set_context(self, path: str, value: Any) -> bool:
        """Set value in Redis"""
        key = self._make_key(path)

        # Serialize to JSON
        serialized = json.dumps(value)
        self.redis.set(key, serialized)

        # Publish change notification for watchers
        self.redis.publish(f"{self.prefix}:watch:{path}", serialized)

        return True

    def update_context(self, path: str, updates: Dict) -> bool:
        """Update dictionary value in Redis"""
        current_value = self.get_context(path, {})

        if not isinstance(current_value, dict):
            return False

        current_value.update(updates)
        return self.set_context(path, current_value)

    def delete_context(self, path: str) -> bool:
        """Delete value from Redis"""
        key = self._make_key(path)
        return self.redis.delete(key) > 0

    def snapshot_context(self) -> Dict:
        """Get all context as a dictionary"""
        snapshot = {}
        pattern = f"{self.prefix}:*"

        for key in self.redis.scan_iter(match=pattern):
            # Remove prefix from key
            path = key[len(self.prefix) + 1:]
            value = self.get_context(path)

            # Build nested dictionary
            self._set_nested(snapshot, path.split('.'), value)

        return snapshot

    def _set_nested(self, d: Dict, keys: list, value: Any):
        """Set value in nested dictionary using list of keys"""
        for key in keys[:-1]:
            if key not in d:
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value

    def watch_context(self, path: str, callback: Callable[[Any], None]) -> None:
        """
        Watch for changes at path using Redis pub/sub

        Note: This is a blocking operation. Run in a separate thread.
        """
        pubsub = self.redis.pubsub()
        pubsub.subscribe(f"{self.prefix}:watch:{path}")

        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    value = json.loads(message['data'])
                    callback(value)
                except Exception as e:
                    print(f"Error in watcher callback: {e}")


class ContextStore:
    """Factory class for creating context store implementations"""

    @staticmethod
    def create(store_type: str = "json_file", **kwargs) -> ContextStoreInterface:
        """
        Create a context store instance

        Args:
            store_type: "json_file" or "redis"
            **kwargs: Additional arguments for the implementation

        Returns:
            ContextStoreInterface implementation
        """
        if store_type == "json_file":
            file_path = kwargs.get("file_path")
            auto_save = kwargs.get("auto_save", True)
            return JSONFileContextStore(file_path, auto_save)
        elif store_type == "redis":
            redis_url = kwargs.get("redis_url", "redis://localhost:6379")
            prefix = kwargs.get("prefix", "context")
            return RedisContextStore(redis_url, prefix)
        else:
            raise ValueError(f"Unknown context store type: {store_type}")


# Example usage
if __name__ == "__main__":
    # Create JSON file context store
    store = ContextStore.create("json_file")

    # Set some values
    store.set_context("system.active_agents", ["coordinator", "developer_agent"])
    store.set_context("projects.watch-app.branch", "feature/new-ui")
    store.set_context("metrics.total_tasks_completed", 42)

    # Get values
    active_agents = store.get_context("system.active_agents", [])
    print(f"Active agents: {active_agents}")

    current_branch = store.get_context("projects.watch-app.branch")
    print(f"Watch app branch: {current_branch}")

    # Update dictionary
    store.update_context("projects.dashboard", {
        "deployment_status": "healthy",
        "last_deployment": datetime.now().isoformat()
    })

    # Append to list
    store.append_to_list("system.active_agents", "tester_agent")

    # Increment counter
    store.increment("metrics.total_tasks_completed")

    # Get full snapshot
    snapshot = store.snapshot_context()
    print(f"\nFull context snapshot:")
    print(json.dumps(snapshot, indent=2))
