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
import json
import anthropic

# Import agents
# Using absolute imports for Railway compatibility
try:
    from dashboard.app.agents.coordinator import CoordinatorAgent
    from dashboard.app.agents.gemini_agent import GeminiAgent
    # from dashboard.app.agents.developer_agent import DeveloperAgent
    # from dashboard.app.agents.tester_agent import TesterAgent
    # from dashboard.app.agents.deployer_agent import DeployerAgent
    # from dashboard.app.agents.data_processor import DataProcessorAgent
except ImportError:
    # Fallback for local development
    from app.agents.coordinator import CoordinatorAgent
    from app.agents.gemini_agent import GeminiAgent
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
from core.agent_registry import Task

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
gemini_agent: Optional[GeminiAgent] = None
claude_client: Optional[anthropic.Anthropic] = None
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
    global coordinator, gemini_agent, claude_client, agents

    print("🚀 Starting Agent Swarm...")

    # Start coordinator
    coordinator = CoordinatorAgent()
    coordinator.startup()
    agents["coordinator"] = coordinator

    # Initialize Claude API client for enhanced reasoning
    try:
        claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        if claude_api_key:
            claude_client = anthropic.Anthropic(api_key=claude_api_key)
            print("✓ Claude API client initialized")
        else:
            print("⚠️  ANTHROPIC_API_KEY not set - advanced reasoning disabled")
    except Exception as e:
        print(f"⚠️  Claude API initialization failed: {e}")

    # Initialize Gemini deployment agent
    try:
        if os.getenv("GOOGLE_API_KEY"):
            gemini_agent = GeminiAgent()
            gemini_agent.startup()
            agents["gemini_deployer"] = gemini_agent
            print("✓ Gemini deployment agent ready")
        else:
            print("⚠️  GOOGLE_API_KEY not set - deployment agent disabled")
    except Exception as e:
        print(f"⚠️  Gemini agent initialization failed: {e}")

    # Initialize default watch config
    coordinator.context_store.set_context("watch.config", {
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
    config = coordinator.context_store.get_context("watch.config", {
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

    # Deployment intent (NEW - for Gemini agent)
    if any(word in message_lower for word in ["deploy", "build", "push", "release", "update code", "modify", "add feature", "fix bug"]):
        return {
            "intent": "deploy_code",
            "original_message": message
        }

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


async def process_with_claude_api(message: str, context: dict) -> dict:
    """
    Use Claude API to interpret command and plan actions

    This provides enhanced reasoning for complex tasks beyond simple keyword matching
    """
    if not claude_client:
        # Fallback to simple intent parsing
        return parse_intent(message)

    try:
        # Build context-aware prompt
        system_prompt = f"""You are an intelligent agent coordinator. You receive voice commands from a Galaxy Watch 4.

Available capabilities:
- Calendar management (Google Calendar API)
- Slack notifications and daily briefs
- Context saving (memory storage)
- Code deployment (via Gemini agent with full codebase access)
- Web scraping and data processing

Current system context:
- Recent deployments: {len(context.get('deployments', []))}
- Saved contexts: {len(context.get('saved_contexts', {}))}
- Active agents: {context.get('active_agents', [])}

Analyze the user's command and return a JSON action plan with:
{{
  "intent": "calendar|slack|save_context|deploy_code|unknown",
  "confidence": 0.0-1.0,
  "task_description": "detailed description of what to do",
  "parameters": {{}},
  "reasoning": "why you chose this interpretation"
}}"""

        response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": message
            }]
        )

        # Parse Claude's response
        response_text = response.content[0].text

        # Extract JSON (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        action_plan = json.loads(response_text)
        action_plan["original_message"] = message

        print(f"🤖 Claude API reasoning: {action_plan.get('reasoning', 'N/A')}")

        return action_plan

    except Exception as e:
        print(f"⚠️  Claude API error: {e}")
        # Fallback to simple intent parsing
        return parse_intent(message)


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
        coordinator.context_store.set_context("watch.config.status", f"✓ Event created: {event_details['title']}")

        print(f"✅ Calendar event created: {event_details['title']} at {event_details['start_time']}")

        return {
            "reply_text": f"Calendar event created: {event_details['title']}",
            "action": "calendar_created"
        }
    except Exception as e:
        print(f"❌ Calendar error: {e}")
        coordinator.context_store.set_context("watch.config.status", "✗ Calendar error")
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
        coordinator.context_store.set_context("watch.config.status", "✓ Slack brief sent")

        print(f"✅ Slack brief sent successfully")

        return {
            "reply_text": "Daily brief sent to Slack!",
            "action": "slack_posted"
        }
    except Exception as e:
        print(f"❌ Slack error: {e}")
        coordinator.context_store.set_context("watch.config.status", "✗ Slack error")
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
        coordinator.context_store.set_context(f"saved_contexts.{context_id}", {
            "text": context_text,
            "timestamp": datetime.now().isoformat(),
            "source": "watch_voice_command"
        })

        # Update watch status
        coordinator.context_store.set_context("watch.config.status", "✓ Context saved")

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


async def handle_deployment_intent(message: str, action_plan: dict = None):
    """
    Handle code deployment requests via Gemini agent

    This enables autonomous deployment from voice commands!
    """
    try:
        if not gemini_agent:
            return {
                "reply_text": "Deployment agent not available. Check GOOGLE_API_KEY.",
                "action": "deployment_unavailable"
            }

        print(f"🚀 Deployment intent: {message}")

        # Update watch status
        coordinator.context_store.set_context("watch.config.status", "🚀 Planning deployment...")

        # Create deployment task
        task = Task(
            task_id=f"deploy_{datetime.now().timestamp()}",
            workflow="deployment/autonomous_deploy.md",
            description=action_plan.get('task_description', message) if action_plan else message,
            priority="high",
            assigned_at=datetime.now().isoformat()
        )

        # Execute via Gemini agent (async)
        gemini_agent.execute_task(task)

        # Update watch status
        coordinator.context_store.set_context("watch.config.status", "⚙️ Deploying...")

        print(f"✅ Deployment task submitted to Gemini agent")

        return {
            "reply_text": "Deployment started! Gemini agent is analyzing and deploying.",
            "action": "deployment_started",
            "task_id": task.task_id
        }

    except Exception as e:
        print(f"❌ Deployment error: {e}")
        coordinator.context_store.set_context("watch.config.status", "✗ Deployment error")
        return {
            "reply_text": f"Deployment failed: {str(e)}",
            "action": "deployment_error"
        }


@app.post("/functions/v1/chat", response_model=ChatResponse)
async def receive_chat(request: ChatRequest):
    """
    Receives voice messages from watch app
    Routes to appropriate handlers via Claude API (if available) or keyword matching

    This is the DECENTRALIZED AUTONOMOUS SYSTEM in action:
    Watch → WiFi → This endpoint → Claude API (reasoning) → Gemini Agent (deployment)
    """
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    print(f"⌚ Watch message: {request.message}")

    # Get system context for Claude API
    context = {
        "deployments": coordinator.context_store.get_context("deployments", []),
        "saved_contexts": coordinator.context_store.get_context("saved_contexts", {}),
        "active_agents": [a for a in agents.keys()]
    }

    # Use Claude API for enhanced reasoning (if available)
    if claude_client:
        print("🤖 Using Claude API for intent analysis...")
        intent_data = await process_with_claude_api(request.message, context)
    else:
        # Fallback to simple keyword matching
        print("🔍 Using keyword-based intent parsing...")
        intent_data = parse_intent(request.message)

    intent = intent_data["intent"]
    print(f"🎯 Detected intent: {intent} (confidence: {intent_data.get('confidence', 'N/A')})")

    # Route to appropriate handler
    if intent == "deploy_code":
        # Autonomous deployment via Gemini agent!
        response = await handle_deployment_intent(request.message, intent_data)
    elif intent == "calendar":
        response = await handle_calendar_intent(request.message)
    elif intent == "slack":
        response = await handle_slack_intent(request.message)
    elif intent == "save_context":
        response = await handle_context_intent(request.message)
    else:
        # Unknown intent - fallback to coordinator routing
        coordinator.context_store.update_context("watch.config.status", "Processing message...")
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
            coordinator.context_store.update_context("watch.config.status", "Agent Swarm Idle")
            response = {
                "reply_text": "I didn't understand that command. Try: 'schedule meeting', 'send slack brief', 'deploy feature', or 'save context'",
                "action": "unknown"
            }

    return ChatResponse(**response)


@app.get("/api/saved-contexts")
async def get_saved_contexts():
    """Get all saved contexts for display in dashboard"""
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    contexts_data = coordinator.context_store.get_context("saved_contexts", {})

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

    coordinator.context_store.set_context("watch.config", config.dict())

    return {
        "status": "updated",
        "config": config,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/deployments")
async def get_deployments():
    """
    Get deployment history for dashboard monitoring

    Shows all autonomous deployments executed by Gemini agent
    """
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    deployments = coordinator.context_store.get_context("deployments", [])

    # Sort by timestamp (newest first)
    deployments.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "deployments": deployments,
        "total": len(deployments),
        "agent_status": "online" if gemini_agent else "offline"
    }


@app.get("/api/deployments/{task_id}")
async def get_deployment_details(task_id: str):
    """Get specific deployment details"""
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    # Check in tasks first
    task_result = coordinator.context_store.get_context(f"tasks.{task_id}.result")
    if task_result:
        return {
            "task_id": task_id,
            "result": task_result,
            "timestamp": datetime.now().isoformat()
        }

    # Check in deployments
    deployments = coordinator.context_store.get_context("deployments", [])
    for deployment in deployments:
        if deployment.get("task_id") == task_id:
            return deployment

    raise HTTPException(status_code=404, detail=f"Deployment {task_id} not found")


@app.get("/api/codebase/context")
async def get_codebase_context():
    """
    Get current codebase context for dashboard display

    Shows project structure, recent changes, deployment targets
    """
    if not gemini_agent:
        return {
            "error": "Gemini agent not initialized",
            "message": "Set GOOGLE_API_KEY to enable codebase analysis"
        }

    context = gemini_agent._get_codebase_context()

    return {
        "codebase": context,
        "cache_age_seconds": (datetime.now() - gemini_agent.codebase_cache_time).total_seconds() if gemini_agent.codebase_cache_time else 0,
        "last_updated": gemini_agent.codebase_cache_time.isoformat() if gemini_agent.codebase_cache_time else None
    }


@app.post("/api/codebase/refresh")
async def refresh_codebase_context():
    """Force refresh of codebase context cache"""
    if not gemini_agent:
        raise HTTPException(status_code=503, detail="Gemini agent not initialized")

    # Clear cache to force rebuild
    gemini_agent.codebase_context = None
    gemini_agent.codebase_cache_time = None

    # Get fresh context
    context = gemini_agent._get_codebase_context()

    return {
        "status": "refreshed",
        "codebase": context,
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

