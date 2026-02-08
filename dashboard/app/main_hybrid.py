"""
Hybrid FastAPI - Real functionality without complex agent initialization

This version:
- Saves real watch messages
- Has intent parsing
- Uses Claude API (optional)
- NO coordinator/agent initialization (what causes crashes)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import os
import anthropic

app = FastAPI(title="Agent Swarm API - Hybrid Mode")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replaces complex ContextStore)
saved_contexts: Dict[str, Dict] = {}
deployments: List[Dict] = []
watch_config = {
    "status": "Agent Swarm Online (Hybrid Mode)",
    "animation_url": "https://lottie.host/4e6fbdae-9e0c-4b6f-915d-d3e9b8b8c8a8/TbWqGjFQCE.json",
    "primary_color": "#9333EA"
}

# Claude API client (optional)
claude_client = None
try:
    if os.getenv("ANTHROPIC_API_KEY"):
        claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        print("✓ Claude API initialized")
except Exception as e:
    print(f"⚠️  Claude API init failed: {e}")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply_text: str
    action: str

class WatchConfig(BaseModel):
    status: str
    animation_url: str
    primary_color: str

@app.on_event("startup")
async def startup():
    print("🚀 Agent Swarm (Hybrid Mode) - Starting...")
    print("✓ No complex agent initialization")
    print("✓ Real message storage enabled")
    print("✓ Intent parsing enabled")
    print("🤖 Hybrid Mode Online!")

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Agent Swarm API (Hybrid)",
        "mode": "hybrid",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "coordinator": "hybrid_mode",
        "agents": 1,
        "active_tasks": 0,
        "completed_tasks": len(saved_contexts),
        "failed_tasks": 0
    }

@app.get("/api/agents")
def get_agents():
    return {
        "total": 1,
        "agents": [
            {
                "agent_id": "hybrid-coordinator",
                "role": "coordinator",
                "status": "idle",
                "current_tasks": 0,
                "completed_tasks": len(saved_contexts),
                "failed_tasks": 0,
                "capabilities": ["message_storage", "intent_parsing", "claude_api"]
            }
        ]
    }

@app.get("/api/system/stats")
def system_stats():
    return {
        "agents": {
            "total_agents": 1,
            "active_tasks": 0,
            "completed_tasks": len(saved_contexts),
            "failed_tasks": 0
        },
        "projects": {},
        "workflows": {
            "in_progress": [],
            "completed": list(saved_contexts.keys()),
            "failed": []
        }
    }

@app.get("/api/saved-contexts")
def get_saved_contexts():
    """Return REAL saved contexts from watch messages"""
    contexts = [
        {
            "id": context_id,
            **context_data
        }
        for context_id, context_data in saved_contexts.items()
    ]

    # Sort by timestamp (newest first)
    contexts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "contexts": contexts,
        "total": len(contexts)
    }

@app.get("/api/deployments")
def get_deployments():
    return {
        "deployments": deployments,
        "total": len(deployments),
        "agent_status": "online" if os.getenv("GOOGLE_API_KEY") else "offline"
    }

@app.get("/functions/v1/watch-config")
def get_watch_config():
    return WatchConfig(**watch_config)

@app.post("/api/update-watch-config")
def update_watch_config(config: WatchConfig):
    global watch_config
    watch_config = config.dict()
    return {
        "status": "updated",
        "config": config,
        "timestamp": datetime.now().isoformat()
    }

class WatchMessageRequest(BaseModel):
    message: str
    device_id: Optional[str] = "lovable_dashboard"

@app.post("/api/watch-message")
async def send_watch_message(request: WatchMessageRequest):
    """
    Endpoint for Lovable dashboard to send messages to the watch
    The message gets processed by Claude API and response is sent to watch
    """
    global watch_config

    print(f"📱 Lovable message: {request.message}")

    try:
        # Process message with Claude API if available
        if claude_client:
            response = claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=256,
                messages=[{
                    "role": "user",
                    "content": f"You are a helpful AI assistant on a Galaxy Watch. Respond concisely (max 50 words) to: {request.message}"
                }]
            )
            reply_text = response.content[0].text
        else:
            # Fallback response without Claude
            reply_text = f"Received: {request.message}"

        # Update watch config with the response
        watch_config["status"] = reply_text[:100]  # Limit to 100 chars for watch display
        watch_config["primary_color"] = "#00FF00"  # Green to indicate new message

        print(f"🤖 Claude reply: {reply_text}")

        return {
            "status": "success",
            "reply": reply_text,
            "timestamp": datetime.now().isoformat(),
            "message": "Response sent to watch via config update"
        }

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def parse_intent(message: str) -> dict:
    """Simple keyword-based intent parser"""
    message_lower = message.lower()

    if any(word in message_lower for word in ["schedule", "meeting", "calendar"]):
        return {"intent": "calendar", "original_message": message}

    if any(word in message_lower for word in ["slack", "brief", "summary"]):
        return {"intent": "slack", "original_message": message}

    if any(word in message_lower for word in ["save context", "remember", "note"]):
        return {"intent": "save_context", "original_message": message}

    if any(word in message_lower for word in ["deploy", "build", "push"]):
        return {"intent": "deploy_code", "original_message": message}

    return {"intent": "unknown", "original_message": message}

async def process_with_claude(message: str) -> dict:
    """Enhanced intent parsing with Claude API"""
    if not claude_client:
        return parse_intent(message)

    try:
        response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": f"Analyze this voice command and determine intent (calendar/slack/save_context/deploy_code/unknown): '{message}'"
            }]
        )

        text = response.content[0].text.lower()

        if "calendar" in text:
            return {"intent": "calendar", "original_message": message, "confidence": 0.9}
        elif "slack" in text:
            return {"intent": "slack", "original_message": message, "confidence": 0.9}
        elif "context" in text or "save" in text:
            return {"intent": "save_context", "original_message": message, "confidence": 0.9}
        elif "deploy" in text:
            return {"intent": "deploy_code", "original_message": message, "confidence": 0.9}

        return {"intent": "unknown", "original_message": message, "confidence": 0.5}
    except Exception as e:
        print(f"Claude API error: {e}")
        return parse_intent(message)

@app.post("/functions/v1/chat")
async def chat(request: ChatRequest):
    """
    REAL MESSAGE PROCESSING
    - Stores messages in memory
    - Parses intent
    - Returns appropriate response
    """
    print(f"⌚ Watch message: {request.message}")

    # Parse intent (with Claude if available)
    if claude_client:
        intent_data = await process_with_claude(request.message)
    else:
        intent_data = parse_intent(request.message)

    intent = intent_data["intent"]
    print(f"🎯 Intent: {intent}")

    # Handle based on intent
    if intent == "save_context" or intent == "unknown":
        # Save message to storage
        context_text = request.message.replace("save context:", "").replace("Save context:", "").strip()
        context_id = f"context_{datetime.now().timestamp()}"

        saved_contexts[context_id] = {
            "text": context_text,
            "timestamp": datetime.now().isoformat(),
            "source": "watch_voice_command",
            "intent": intent
        }

        # Update watch status
        watch_config["status"] = "✓ Message saved"

        print(f"💾 Saved: {context_text[:50]}...")

        return ChatResponse(
            reply_text=f"Message saved! ({len(saved_contexts)} total)",
            action="context_saved"
        )

    elif intent == "calendar":
        watch_config["status"] = "📅 Calendar feature (needs API setup)"
        return ChatResponse(
            reply_text="Calendar integration available with Google Calendar API",
            action="calendar_intent"
        )

    elif intent == "slack":
        watch_config["status"] = "💬 Slack feature (needs API setup)"
        return ChatResponse(
            reply_text="Slack integration available with SLACK_BOT_TOKEN",
            action="slack_intent"
        )

    elif intent == "deploy_code":
        watch_config["status"] = "🚀 Deployment feature (needs Gemini API)"
        return ChatResponse(
            reply_text="Deployment agent available with GOOGLE_API_KEY",
            action="deploy_intent"
        )

    else:
        return ChatResponse(
            reply_text="Message received in hybrid mode",
            action="processed"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print("=" * 60)
    print("🚀 Agent Swarm API - HYBRID MODE")
    print("✓ Real message storage (no database required)")
    print("✓ Intent parsing with Claude API (optional)")
    print("✓ All endpoints working")
    print("✗ No complex agent initialization (prevents crashes)")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port)
