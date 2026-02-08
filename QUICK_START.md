# Quick Start: Agent Swarm + Lovable Dashboard

## What You Have Now

✅ **Agent Swarm Backend** - FastAPI server with 5 specialized agents ([dashboard/app/main.py](dashboard/app/main.py))
✅ **Lovable Prompts** - Ready-to-use prompts for building your interface ([LOVABLE_PROMPTS.md](LOVABLE_PROMPTS.md))
✅ **Workflows** - SOPs for agents in `workflows/` directory
✅ **Tools** - Python scripts for deterministic execution in `tools/`

## What You Need to Do

### Option A: Quick Demo (Recommended)

If you want to test this ASAP without fixing disk space issues:

**1. Deploy Backend to Cloud**

The easiest way is to use a free cloud service:

**Using Railway.app (Recommended - Free tier available):**
```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login
railway login

# Initialize project
cd "/Users/vik043/Desktop/Agentic Workflow/dashboard"
railway init

# Deploy
railway up
```

Your backend will get a URL like: `https://your-app.railway.app`

**OR Using Render.com (Also free):**
1. Go to https://render.com/
2. Click "New" → "Web Service"
3. Connect your GitHub repo (or push this code to GitHub first)
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python -m app.main`
6. Deploy!

**2. Build Lovable Interface**

1. Go to https://lovable.dev/
2. Create new project or open existing
3. Copy **Prompt 1** from [LOVABLE_PROMPTS.md](LOVABLE_PROMPTS.md)
4. Paste into Lovable chat
5. Wait for generation (1-2 minutes)
6. Update the API URL in the code to your Railway/Render URL
7. Test the interface!

**3. Start Using It**

- Submit tasks through the Lovable interface
- Watch agents process tasks in real-time
- Use social media connectors
- Deploy code changes

### Option B: Local Development (If you have disk space)

**1. Free Up Disk Space**

```bash
# Check disk usage
df -h

# Clean up common space hogs:
# - Empty Trash
# - Delete old Xcode/Android Studio builds
# - Clear pip cache: pip cache purge
# - Clear npm cache: npm cache clean --force
# - Delete old Docker images: docker system prune -a
```

**2. Install Dependencies**

```bash
cd "/Users/vik043/Desktop/Agentic Workflow/dashboard"
pip install fastapi uvicorn pydantic anthropic python-dotenv pyyaml redis requests tweepy facebook-sdk slack-sdk
```

**3. Set Up Environment**

Create `.env` file:
```bash
cd "/Users/vik043/Desktop/Agentic Workflow"
nano .env
```

Add:
```bash
# Required for agents
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional - for connectors (add only what you'll use)
SLACK_BOT_TOKEN=your_slack_token
TWITTER_API_KEY=your_twitter_key
# ... etc
```

**4. Start Backend**

```bash
cd "/Users/vik043/Desktop/Agentic Workflow/dashboard"
python -m app.main
```

Server runs at: http://localhost:8000

**5. Build Lovable Interface**

Same as Option A, but use `http://localhost:8000` as API URL

## Agent Deployment Explained

### Do Agents Need to Be "Deployed"?

The agents run as part of the FastAPI backend. When you start the backend, agents automatically initialize:

```python
# From dashboard/app/main.py

@app.on_event("startup")
async def startup_event():
    # This runs when backend starts
    coordinator = CoordinatorAgent()
    coordinator.startup()  # ← Agent starts here
```

So **deploying the backend = deploying the agents**. No separate deployment needed!

### Can Agents Deploy Code?

**YES!** Agents have access to:

✅ **Watch App Deployment** - via [dashboard/app/agents/deployer_agent.py](dashboard/app/agents/deployer_agent.py)
- Builds Android APK using Gradle
- Can push to device via ADB
- Creates deployable artifacts

✅ **Dashboard Deployment** - also via deployer agent
- Deploys FastAPI backend to Cloud Run, Vercel, Railway, etc.
- Performs health checks
- Automated rollback on failure

✅ **Lovable Sync** - via [tools/development/lovable_sync.py](tools/development/lovable_sync.py)
- Syncs from GitHub
- Makes code changes
- Pushes back to GitHub
- Creates PRs

✅ **Git Operations** - via [tools/development/git_operations.py](tools/development/git_operations.py)
- Creates branches
- Commits changes
- Pushes to remote
- Creates PRs

### How to Give Agents Code to Deploy

**From Lovable Dashboard:**

1. Submit a task: "Deploy the watch app with the new voice recognition feature"
2. Coordinator routes to Deployer Agent
3. Deployer Agent:
   - Builds APK via `tools/development/android_build.py`
   - Runs tests
   - Creates deployable artifact
4. You get notified when done

**From Watch:**

1. Send voice message: "Build and deploy the new feature"
2. Message goes to dashboard API
3. Coordinator interprets task
4. Developer Agent makes changes
5. Tester Agent validates
6. Deployer Agent deploys

## Testing the System

### Test 1: Backend Health Check

```bash
curl http://localhost:8000/health
# OR your deployed URL:
curl https://your-app.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "coordinator": "online",
  "agents": 5,
  "active_tasks": 0
}
```

### Test 2: Submit a Task

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Test task: analyze the watch app code",
    "priority": "normal"
  }'
```

Should return:
```json
{
  "task_id": "task_1234567890.123",
  "status": "assigned",
  "message": "Task routed successfully to agent swarm"
}
```

### Test 3: Check Agents

```bash
curl http://localhost:8000/api/agents
```

Should return list of 5 agents with their status.

## Troubleshooting

### "Coordinator not initialized"

Backend hasn't fully started. Wait 5-10 seconds after running `python -m app.main`, then try again.

### "Module not found" errors

Dependencies not installed. Run:
```bash
pip install fastapi uvicorn pydantic anthropic
```

### CORS errors in Lovable

The backend has CORS enabled with `allow_origins=["*"]`. If you still get CORS errors:

1. Make sure backend is actually running
2. Check the API URL is correct in Lovable code
3. Use browser dev tools (F12) to see the exact error

### Agents not processing tasks

1. Check `.env` has `ANTHROPIC_API_KEY`
2. Check backend logs for errors
3. Verify coordinator is running: `GET /api/agents`

## What's Next?

Once you have the Lovable interface connected to the backend:

1. **Add features via voice** - speak to your watch, let agents implement
2. **Deploy autonomously** - agents handle git, testing, deployment
3. **Scale connectors** - add more social media, productivity tools
4. **Monitor everything** - use the analytics dashboard (Prompt 6)
5. **Self-improvement** - agents learn from failures and update workflows

## Need Help?

The agents can help you! Once the system is running, submit a task:

"Help me understand how to deploy the watch app"

The developer agent will guide you through the process.
