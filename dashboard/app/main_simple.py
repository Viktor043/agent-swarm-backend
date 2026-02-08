"""
Simplified FastAPI for Railway - Guaranteed to start
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os

app = FastAPI(title="Agent Swarm API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply_text: str
    action: str

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Agent Swarm API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "coordinator": "online",
        "agents": 1,
        "active_tasks": 0,
        "completed_tasks": 0,
        "failed_tasks": 0
    }

@app.get("/api/agents")
def get_agents():
    return {
        "total": 1,
        "agents": [
            {
                "agent_id": "coordinator-1",
                "role": "coordinator",
                "status": "idle",
                "current_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "capabilities": ["task_routing", "monitoring"]
            }
        ]
    }

@app.get("/api/system/stats")
def system_stats():
    return {
        "agents": {
            "total_agents": 1,
            "active_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0
        },
        "projects": {},
        "workflows": {
            "in_progress": [],
            "completed": [],
            "failed": []
        }
    }

@app.get("/api/saved-contexts")
def saved_contexts():
    return {
        "contexts": [],
        "total": 0
    }

@app.get("/api/deployments")
def deployments():
    return {
        "deployments": [],
        "total": 0,
        "agent_status": "online" if os.getenv("GOOGLE_API_KEY") else "offline"
    }

@app.get("/functions/v1/watch-config")
def watch_config():
    return {
        "status": "Agent Swarm Online",
        "animation_url": "https://lottie.host/4e6fbdae-9e0c-4b6f-915d-d3e9b8b8c8a8/TbWqGjFQCE.json",
        "primary_color": "#9333EA"
    }

@app.post("/functions/v1/chat")
def chat(request: ChatRequest):
    return ChatResponse(
        reply_text="Message received! (Simplified mode)",
        action="received"
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print("=" * 50)
    print("🚀 SIMPLIFIED Agent Swarm API")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=port)
