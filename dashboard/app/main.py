"""
FastAPI Dashboard - API for agent swarm interaction

This is the backend that your Lovable dashboard will communicate with.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import asyncio
from datetime import datetime

# Import agents
# Using absolute imports for Railway compatibility
try:
    from dashboard.app.agents.coordinator import CoordinatorAgent
    # from dashboard.app.agents.developer_agent import DeveloperAgent
    # from dashboard.app.agents.tester_agent import TesterAgent
    # from dashboard.app.agents.deployer_agent import DeployerAgent
    # from dashboard.app.agents.data_processor import DataProcessorAgent
except ImportError:
    # Fallback for local development
    from app.agents.coordinator import CoordinatorAgent
    # from app.agents.developer_agent import DeveloperAgent
    # from app.agents.tester_agent import TesterAgent
    # from app.agents.deployer_agent import DeployerAgent
    # from app.agents.data_processor import DataProcessorAgent

# Import connectors
import sys
import os
# Add tools directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../tools'))

from connectors.google_calendar import get_calendar_client, parse_calendar_command
from connectors.slack_client import get_slack_client

app = FastAPI(title="Agent Swarm Dashboard API")

# CORS for Lovable dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Lovable domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances (initialized on startup)
coordinator: Optional[CoordinatorAgent] = None
agents: Dict[str, any] = {}


# Request/Response Models
class TaskRequest(BaseModel):
    description: str
    priority: str = "normal"
    task_type: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class AgentStatusResponse(BaseModel):
    agent_id: str
    role: str
    status: str
    current_tasks: int
    completed_tasks: int
    failed_tasks: int


class WatchMessageRequest(BaseModel):
    message: str
    device_id: Optional[str] = None


# Watch App Data Models (for Supabase-compatible endpoints)
class WatchConfig(BaseModel):
    status: str
    animation_url: str
    primary_color: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply_text: Optional[str] = None
    action: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize all agents on startup"""
    global coordinator, agents

    print("🚀 Starting Agent Swarm...")

    # Start coordinator
    coordinator = CoordinatorAgent()
    coordinator.startup()
    agents["coordinator"] = coordinator

    # Initialize default watch config
    coordinator.context_store.set("watch.config", {
        "status": "Agent Swarm Online",
        "animation_url": "https://lottie.host/4e6fbdae-9e0c-4b6f-915d-d3e9b8b8c8a8/TbWqGjFQCE.json",  # Default Lottie animation
        "primary_color": "#9333EA"  # Purple
    })

    print("✓ Coordinator ready")
    print("✓ Watch config initialized")
    print("🤖 Agent Swarm Online!")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Agent Swarm Dashboard API",
        "timestamp": datetime.now().isoformat(),
        "agents": len(agents)
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    stats = coordinator.registry.get_system_stats()

    return {
        "status": "healthy",
        "coordinator": "online",
        "agents": stats["total_agents"],
        "active_tasks": stats["active_tasks"],
        "completed_tasks": stats["completed_tasks"],
        "failed_tasks": stats["failed_tasks"]
    }


@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskRequest):
    """
    Create a new task for the agent swarm

    This is the main endpoint your Lovable dashboard will call!
    """
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    print(f"📋 New task received: {task.description}")

    # Route task through coordinator
    success = coordinator.route_incoming_task(
        task_description=task.description,
        priority=task.priority
    )

    if success:
        return TaskResponse(
            task_id=f"task_{datetime.now().timestamp()}",
            status="assigned",
            message=f"Task routed successfully to agent swarm"
        )
    else:
        raise HTTPException(
            status_code=503,
            detail="No agents available. Task queued for later."
        )


@app.get("/api/agents")
async def list_agents():
    """Get all active agents and their status"""
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    agents_list = coordinator.registry.get_active_agents()

    return {
        "total": len(agents_list),
        "agents": [
            {
                "agent_id": agent.agent_id,
                "role": agent.role,
                "status": agent.status.value,
                "current_tasks": len(agent.current_tasks),
                "completed_tasks": agent.completed_tasks,
                "failed_tasks": agent.failed_tasks,
                "capabilities": agent.capabilities
            }
            for agent in agents_list
        ]
    }


@app.get("/api/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get specific agent status"""
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    status = coordinator.registry.get_agent_status(agent_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return status


@app.post("/api/watch-message")
async def receive_watch_message(message: WatchMessageRequest):
    """
    Receive message from Galaxy Watch

    This is called when your watch sends a voice message
    """
    print(f"⌚ Watch message: {message.message}")

    # Create task to process the message
    if coordinator:
        coordinator.route_incoming_task(
            task_description=f"Process watch message: {message.message}",
            priority="high"
        )

    return {
        "status": "received",
        "message": "Watch message queued for processing",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/connectors/post")
async def post_to_connector(data: Dict):
    """
    Post to social media or other connectors

    Example:
    {
        "connector": "twitter",
        "content": "Hello from my watch!",
        "media": []
    }
    """
    connector = data.get("connector", "twitter")
    content = data.get("content", "")

    print(f"📱 Posting to {connector}: {content}")

    # Route to data processor agent
    if coordinator:
        coordinator.route_incoming_task(
            task_description=f"Post to {connector}: {content}",
            priority="normal"
        )

    return {
        "status": "posted",
        "connector": connector,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/system/stats")
async def get_system_stats():
    """Get system-wide statistics"""
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    stats = coordinator.registry.get_system_stats()
    context = coordinator.context_store.snapshot_context()

    return {
        "agents": stats,
        "projects": context.get("projects", {}),
        "workflows": context.get("workflows", {}),
        "metrics": context.get("metrics", {})
    }


# ============================================================================
# WATCH APP INTEGRATION ENDPOINTS (Supabase-compatible)
# ============================================================================

@app.get("/functions/v1/watch-config")
async def get_watch_config():
    """
    Polled by watch app every 3 seconds to get current configuration
    Agents can update this to change watch appearance/status
    """
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    # Get current config from context store
    config = coordinator.context_store.get("watch.config", {
        "status": "Connecting...",
        "animation_url": "",
        "primary_color": "#FFFFFF"
    })

    return WatchConfig(**config)


# ============================================================================
# INTENT PARSING & DEMO HANDLERS
# ============================================================================

def parse_intent(message: str) -> dict:
    """Simple keyword-based intent parser for demo features"""
    message_lower = message.lower()

    # Calendar intent
    if any(word in message_lower for word in ["schedule", "meeting", "calendar", "book", "appointment"]):
        return {
            "intent": "calendar",
            "original_message": message
        }

    # Slack intent
    if any(word in message_lower for word in ["slack", "brief", "summary", "report"]):
        return {
            "intent": "slack",
            "original_message": message
        }

    # Context saving intent
    if any(word in message_lower for word in ["save context", "remember", "note", "record"]):
        return {
            "intent": "save_context",
            "original_message": message
        }

    return {"intent": "unknown", "original_message": message}


async def handle_calendar_intent(message: str):
    """Handle calendar booking from voice command"""
    try:
        print(f"📅 Calendar intent: {message}")

        # Parse the command
        event_details = parse_calendar_command(message)

        # Create the event
        calendar_client = get_calendar_client()
        event_link = calendar_client.create_event(
            summary=event_details["title"],
            start_time=event_details["start_time"],
            duration_minutes=event_details["duration"]
        )

        # Update watch status
        coordinator.context_store.set("watch.config.status", f"✓ Event created: {event_details['title']}")

        print(f"✅ Calendar event created: {event_details['title']} at {event_details['start_time']}")

        return {
            "reply_text": f"Calendar event created: {event_details['title']}",
            "action": "calendar_created"
        }
    except Exception as e:
        print(f"❌ Calendar error: {e}")
        coordinator.context_store.set("watch.config.status", "✗ Calendar error")
        return {
            "reply_text": "Failed to create calendar event. Check Google Calendar setup.",
            "action": "calendar_error"
        }


async def handle_slack_intent(message: str):
    """Handle Slack posting from voice command"""
    try:
        print(f"💬 Slack intent: {message}")

        # Send daily brief
        slack_client = get_slack_client()
        slack_client.send_daily_brief()

        # Update watch status
        coordinator.context_store.set("watch.config.status", "✓ Slack brief sent")

        print(f"✅ Slack brief sent successfully")

        return {
            "reply_text": "Daily brief sent to Slack!",
            "action": "slack_posted"
        }
    except Exception as e:
        print(f"❌ Slack error: {e}")
        coordinator.context_store.set("watch.config.status", "✗ Slack error")
        return {
            "reply_text": "Failed to send Slack message. Check SLACK_BOT_TOKEN.",
            "action": "slack_error"
        }


async def handle_context_intent(message: str):
    """Save conversation context"""
    try:
        # Remove the "save context:" prefix if present
        context_text = message.replace("save context:", "").replace("Save context:", "").strip()

        # Store in context store with timestamp
        context_id = f"context_{datetime.now().timestamp()}"
        coordinator.context_store.set(f"saved_contexts.{context_id}", {
            "text": context_text,
            "timestamp": datetime.now().isoformat(),
            "source": "watch_voice_command"
        })

        # Update watch status
        coordinator.context_store.set("watch.config.status", "✓ Context saved")

        print(f"💾 Context saved: {context_text[:50]}...")

        return {
            "reply_text": "Context saved successfully!",
            "action": "context_saved"
        }
    except Exception as e:
        print(f"Context save error: {e}")
        return {
            "reply_text": "Failed to save context",
            "action": "context_error"
        }


@app.post("/functions/v1/chat", response_model=ChatResponse)
async def receive_chat(request: ChatRequest):
    """
    Receives voice messages from watch app
    Routes to demo feature handlers based on intent
    """
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    print(f"⌚ Watch message: {request.message}")

    # Parse intent
    intent_data = parse_intent(request.message)
    intent = intent_data["intent"]

    print(f"🎯 Detected intent: {intent}")

    # Route to appropriate handler
    if intent == "calendar":
        response = await handle_calendar_intent(request.message)
    elif intent == "slack":
        response = await handle_slack_intent(request.message)
    elif intent == "save_context":
        response = await handle_context_intent(request.message)
    else:
        # Unknown intent - fallback to old coordinator routing
        coordinator.context_store.update("watch.config.status", "Processing message...")
        success = coordinator.route_incoming_task(
            task_description=f"Process watch message: {request.message}",
            priority="high"
        )
        if success:
            response = {
                "reply_text": "Message received! Processing now.",
                "action": "task_queued"
            }
        else:
            coordinator.context_store.update("watch.config.status", "Agent Swarm Idle")
            response = {
                "reply_text": "I didn't understand that command.",
                "action": "unknown"
            }

    return ChatResponse(**response)


@app.get("/api/saved-contexts")
async def get_saved_contexts():
    """Get all saved contexts for display in dashboard"""
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    contexts_data = coordinator.context_store.get("saved_contexts", {})

    # Convert to list format
    contexts = [
        {
            "id": context_id,
            **context_data
        }
        for context_id, context_data in contexts_data.items()
    ]

    # Sort by timestamp (newest first)
    contexts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {"contexts": contexts, "total": len(contexts)}


@app.post("/api/update-watch-config")
async def update_watch_config(config: WatchConfig):
    """
    Called by Lovable dashboard to update watch appearance
    Allows dashboard to control watch display remotely
    """
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    coordinator.context_store.set("watch.config", config.dict())

    return {
        "status": "updated",
        "config": config,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    import os

    print("="*50)
    print("🚀 Agent Swarm Dashboard API")
    print("="*50)

    # Railway provides PORT env variable
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

