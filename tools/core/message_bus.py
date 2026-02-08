"""
Message Bus - Inter-agent communication system

Provides event-driven communication between agents using either Redis Streams
or an in-memory queue for testing.
"""

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Optional, Callable, Dict
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """Types of messages that can be sent between agents"""
    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    ESCALATION = "escalation"


@dataclass
class Message:
    """Structure for messages passed between agents"""
    id: str
    timestamp: str
    from_agent: str
    to_agent: str  # or "broadcast" for all agents
    message_type: MessageType
    payload: Dict
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    requires_response: bool = False
    correlation_id: Optional[str] = None  # For linking request/response pairs

    def to_dict(self) -> Dict:
        """Convert message to dictionary for serialization"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create message from dictionary"""
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)


class MessageBusInterface(ABC):
    """Abstract interface for message bus implementations"""

    @abstractmethod
    def publish_message(self, from_agent: str, to_agent: str, message_type: MessageType,
                       payload: Dict, priority: str = "normal",
                       requires_response: bool = False) -> str:
        """Publish a message to the bus"""
        pass

    @abstractmethod
    def broadcast_message(self, from_agent: str, message_type: MessageType,
                         payload: Dict, priority: str = "normal") -> List[str]:
        """Broadcast a message to all agents"""
        pass

    @abstractmethod
    def subscribe_to_messages(self, agent_id: str, callback: Callable[[Message], None]) -> None:
        """Subscribe to messages for a specific agent"""
        pass

    @abstractmethod
    def get_pending_messages(self, agent_id: str, limit: int = 10) -> List[Message]:
        """Get pending messages for an agent"""
        pass

    @abstractmethod
    def acknowledge_message(self, message_id: str) -> bool:
        """Acknowledge that a message has been processed"""
        pass

    @abstractmethod
    def get_message_status(self, message_id: str) -> Optional[Dict]:
        """Get the status of a specific message"""
        pass


class InMemoryMessageBus(MessageBusInterface):
    """
    In-memory message bus implementation for testing and development

    Simple queue-based system that stores messages in memory.
    Data is lost when process stops.
    """

    def __init__(self):
        self.messages: Dict[str, List[Message]] = {}  # agent_id -> messages
        self.message_store: Dict[str, Message] = {}  # message_id -> message
        self.acknowledged: set = set()
        self.subscribers: Dict[str, List[Callable]] = {}  # agent_id -> callbacks

    def publish_message(self, from_agent: str, to_agent: str, message_type: MessageType,
                       payload: Dict, priority: str = "normal",
                       requires_response: bool = False) -> str:
        """Publish a message to a specific agent"""
        message = Message(
            id=f"msg_{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now().isoformat(),
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            priority=priority,
            requires_response=requires_response
        )

        # Store message
        self.message_store[message.id] = message

        # Add to recipient's queue
        if to_agent not in self.messages:
            self.messages[to_agent] = []
        self.messages[to_agent].append(message)

        # Sort by priority
        self._sort_queue(to_agent)

        # Trigger subscriber callbacks
        if to_agent in self.subscribers:
            for callback in self.subscribers[to_agent]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Error in subscriber callback: {e}")

        return message.id

    def broadcast_message(self, from_agent: str, message_type: MessageType,
                         payload: Dict, priority: str = "normal") -> List[str]:
        """Broadcast a message to all agents"""
        message_ids = []

        # Get all unique agent IDs
        all_agents = set(self.messages.keys()) | set(self.subscribers.keys())

        # Don't send broadcast to self
        all_agents.discard(from_agent)

        for agent_id in all_agents:
            msg_id = self.publish_message(
                from_agent=from_agent,
                to_agent=agent_id,
                message_type=message_type,
                payload=payload,
                priority=priority
            )
            message_ids.append(msg_id)

        return message_ids

    def subscribe_to_messages(self, agent_id: str, callback: Callable[[Message], None]) -> None:
        """Subscribe to messages for a specific agent"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)

        # Initialize message queue if needed
        if agent_id not in self.messages:
            self.messages[agent_id] = []

    def get_pending_messages(self, agent_id: str, limit: int = 10) -> List[Message]:
        """Get pending (unacknowledged) messages for an agent"""
        if agent_id not in self.messages:
            return []

        pending = [
            msg for msg in self.messages[agent_id]
            if msg.id not in self.acknowledged
        ]

        return pending[:limit]

    def acknowledge_message(self, message_id: str) -> bool:
        """Mark a message as acknowledged/processed"""
        if message_id in self.message_store:
            self.acknowledged.add(message_id)
            return True
        return False

    def get_message_status(self, message_id: str) -> Optional[Dict]:
        """Get status information about a message"""
        if message_id not in self.message_store:
            return None

        message = self.message_store[message_id]
        return {
            "message_id": message_id,
            "acknowledged": message_id in self.acknowledged,
            "from_agent": message.from_agent,
            "to_agent": message.to_agent,
            "timestamp": message.timestamp,
            "message_type": message.message_type.value
        }

    def _sort_queue(self, agent_id: str):
        """Sort message queue by priority"""
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        self.messages[agent_id].sort(
            key=lambda m: priority_order.get(m.priority, 2)
        )


class RedisMessageBus(MessageBusInterface):
    """
    Redis-based message bus implementation for production use

    Uses Redis Streams for durable, scalable message passing.
    Requires Redis server to be running.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis message bus

        Args:
            redis_url: Redis connection URL from .env
        """
        try:
            import redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()  # Test connection
        except ImportError:
            raise ImportError("Redis package not installed. Run: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Could not connect to Redis: {e}")

    def publish_message(self, from_agent: str, to_agent: str, message_type: MessageType,
                       payload: Dict, priority: str = "normal",
                       requires_response: bool = False) -> str:
        """Publish a message using Redis Streams"""
        message = Message(
            id=f"msg_{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now().isoformat(),
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            priority=priority,
            requires_response=requires_response
        )

        # Use Redis Stream for the target agent
        stream_name = f"agent:{to_agent}:messages"

        # Add to stream
        self.redis.xadd(
            stream_name,
            {
                "message_id": message.id,
                "data": json.dumps(message.to_dict())
            }
        )

        # Store message details in hash for status lookup
        self.redis.hset(
            f"message:{message.id}",
            mapping={
                "from_agent": from_agent,
                "to_agent": to_agent,
                "timestamp": message.timestamp,
                "acknowledged": "false"
            }
        )

        return message.id

    def broadcast_message(self, from_agent: str, message_type: MessageType,
                         payload: Dict, priority: str = "normal") -> List[str]:
        """Broadcast message to all registered agents"""
        message_ids = []

        # Get all agent streams
        agent_streams = self.redis.keys("agent:*:messages")

        for stream in agent_streams:
            # Extract agent_id from stream name (agent:AGENT_ID:messages)
            agent_id = stream.split(":")[1]

            # Don't broadcast to self
            if agent_id == from_agent:
                continue

            msg_id = self.publish_message(
                from_agent=from_agent,
                to_agent=agent_id,
                message_type=message_type,
                payload=payload,
                priority=priority
            )
            message_ids.append(msg_id)

        return message_ids

    def subscribe_to_messages(self, agent_id: str, callback: Callable[[Message], None]) -> None:
        """
        Subscribe to messages using Redis Streams

        Note: This is a blocking operation. Run in a separate thread.
        """
        stream_name = f"agent:{agent_id}:messages"

        # Create consumer group if it doesn't exist
        try:
            self.redis.xgroup_create(stream_name, agent_id, id="0", mkstream=True)
        except Exception:
            pass  # Group already exists

        # Listen for new messages
        while True:
            messages = self.redis.xreadgroup(
                agent_id,
                agent_id,
                {stream_name: ">"},
                count=10,
                block=1000  # Block for 1 second
            )

            for stream, message_list in messages:
                for msg_id, data in message_list:
                    try:
                        message_data = json.loads(data['data'])
                        message = Message.from_dict(message_data)
                        callback(message)

                        # Acknowledge message in stream
                        self.redis.xack(stream_name, agent_id, msg_id)
                    except Exception as e:
                        print(f"Error processing message: {e}")

    def get_pending_messages(self, agent_id: str, limit: int = 10) -> List[Message]:
        """Get pending messages from Redis Stream"""
        stream_name = f"agent:{agent_id}:messages"

        # Read pending messages (not yet acknowledged)
        try:
            pending = self.redis.xpending_range(
                stream_name,
                agent_id,
                min="-",
                max="+",
                count=limit
            )

            messages = []
            for item in pending:
                msg_id = item['message_id']
                data = self.redis.xrange(stream_name, msg_id, msg_id)
                if data:
                    message_data = json.loads(data[0][1]['data'])
                    messages.append(Message.from_dict(message_data))

            return messages
        except Exception:
            return []

    def acknowledge_message(self, message_id: str) -> bool:
        """Mark message as acknowledged"""
        key = f"message:{message_id}"
        if self.redis.exists(key):
            self.redis.hset(key, "acknowledged", "true")
            return True
        return False

    def get_message_status(self, message_id: str) -> Optional[Dict]:
        """Get message status from Redis"""
        key = f"message:{message_id}"
        if not self.redis.exists(key):
            return None

        return self.redis.hgetall(key)


class MessageBus:
    """
    Factory class for creating the appropriate message bus implementation
    """

    @staticmethod
    def create(bus_type: str = "in_memory", **kwargs) -> MessageBusInterface:
        """
        Create a message bus instance

        Args:
            bus_type: "in_memory" or "redis"
            **kwargs: Additional arguments passed to the implementation

        Returns:
            MessageBusInterface implementation
        """
        if bus_type == "in_memory":
            return InMemoryMessageBus()
        elif bus_type == "redis":
            redis_url = kwargs.get("redis_url", "redis://localhost:6379")
            return RedisMessageBus(redis_url)
        else:
            raise ValueError(f"Unknown message bus type: {bus_type}")


# Example usage
if __name__ == "__main__":
    # Create in-memory bus for testing
    bus = MessageBus.create("in_memory")

    # Publish a task assignment
    msg_id = bus.publish_message(
        from_agent="coordinator",
        to_agent="developer_agent",
        message_type=MessageType.TASK_ASSIGNMENT,
        payload={
            "task_id": "task_123",
            "workflow": "development/add_feature",
            "description": "Add dark mode toggle to settings"
        },
        priority="high",
        requires_response=True
    )

    print(f"Published message: {msg_id}")

    # Get pending messages
    pending = bus.get_pending_messages("developer_agent")
    print(f"Pending messages for developer_agent: {len(pending)}")

    for msg in pending:
        print(f"  - {msg.message_type.value}: {msg.payload}")

    # Acknowledge message
    bus.acknowledge_message(msg_id)
    print(f"Acknowledged message: {msg_id}")
