# 🚀 Deployment Guide: Watch App Integration Complete

## ✅ What I Just Completed

I've successfully integrated your Galaxy Watch 4 app with the FastAPI agent swarm backend:

### Backend Changes ([dashboard/app/main.py](dashboard/app/main.py))
✅ Added 3 new data models: `WatchConfig`, `ChatRequest`, `ChatResponse`
✅ Added `GET /functions/v1/watch-config` - watch polls this every 3 seconds for status updates
✅ Added `POST /functions/v1/chat` - receives voice messages from watch
✅ Added `POST /api/update-watch-config` - Lovable dashboard can control watch display
✅ Initialized default watch config in startup (purple color, agent swarm status)

### Watch App Changes ([watch-app/.../KinNetwork.kt](watch-app/app/src/main/java/com/example/kin/presentation/network/KinNetwork.kt))
✅ Changed `BASE_URL` from Supabase to FastAPI (currently set to `http://10.0.2.2:8000/` for Android emulator)
✅ Removed Supabase authentication headers
✅ Kept device token header for security

---

## 🎯 Next Steps (Your Action Items)

### Step 1: Deploy FastAPI Backend

**Option A: Deploy to Railway (Recommended - Free, 5 minutes)**

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login to Railway
railway login

# Navigate to dashboard directory
cd "/Users/vik043/Desktop/Agentic Workflow/dashboard"

# Initialize Railway project
railway init

# Deploy!
railway up
```

After deployment, Railway will give you a URL like: `https://your-project.up.railway.app`

**Option B: Deploy to Render (Also Free)**

1. Go to https://render.com/
2. Click "New" → "Web Service"
3. Connect your GitHub repo (or create one and push this code)
4. Set:
   - Build Command: `pip install fastapi uvicorn pydantic anthropic python-dotenv pyyaml`
   - Start Command: `python -m app.main`
5. Add environment variable: `ANTHROPIC_API_KEY=your_key_here`
6. Deploy!

**Option C: Run Locally (for testing)**

```bash
cd "/Users/vik043/Desktop/Agentic Workflow/dashboard"

# Install minimal dependencies
pip install fastapi uvicorn pydantic anthropic python-dotenv pyyaml

# Run server
python -m app.main
```

Server will run at `http://localhost:8000`

---

### Step 2: Update Watch App with Backend URL

Once you have your deployed URL (e.g., `https://your-project.up.railway.app`):

1. Open [watch-app/.../KinNetwork.kt](watch-app/app/src/main/java/com/example/kin/presentation/network/KinNetwork.kt:42)
2. Change line 42:
   ```kotlin
   private const val BASE_URL = "https://your-project.up.railway.app/"
   ```
3. Make sure the URL ends with a `/`

---

### Step 3: Rebuild Watch APK

```bash
cd "/Users/vik043/Desktop/Agentic Workflow/watch-app"

# Build APK
./gradlew assembleDebug

# APK will be created at:
# app/build/outputs/apk/debug/app-debug.apk
```

---

### Step 4: Install APK on Galaxy Watch 4

**Method A: ADB over USB**

```bash
# Connect watch via USB, enable debugging
adb devices

# Should show your watch device
# Then install:
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

**Method B: ADB over WiFi**

```bash
# On watch: Settings → Developer options → ADB debugging → Enable
# Get watch IP address from Settings → About → Status

adb connect 192.168.1.XXX:5555  # Replace with your watch's IP
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

---

### Step 5: Test the Integration

**Test Backend Health:**
```bash
curl https://your-backend-url/health

# Expected response:
{
  "status": "healthy",
  "coordinator": "online",
  "agents": 5,
  ...
}
```

**Test Watch Config Endpoint:**
```bash
curl https://your-backend-url/functions/v1/watch-config

# Expected response:
{
  "status": "Agent Swarm Online",
  "animation_url": "https://lottie.host/...",
  "primary_color": "#9333EA"
}
```

**Test Chat Endpoint:**
```bash
curl -X POST https://your-backend-url/functions/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test from terminal"}'

# Expected response:
{
  "reply_text": "Message received! Processing now.",
  "action": "task_queued"
}
```

**Test on Watch:**
1. Open watch app
2. Watch should display "Agent Swarm Online" (polled from backend)
3. Speak a message: "Test message"
4. Should vibrate and show "Sending..."
5. Check backend logs - should see "⌚ Watch message: Test message"
6. Watch status should update to "Processing message..."

---

### Step 6: Build Lovable Dashboard

1. Go to https://lovable.dev/
2. Open your project (or create new)
3. Copy **Prompt 1** from [LOVABLE_PROMPTS.md](LOVABLE_PROMPTS.md:5-39)
4. Paste into Lovable chat
5. Wait for generation (1-2 minutes)
6. In the generated code, update `API_BASE_URL`:
   ```typescript
   const API_BASE_URL = "https://your-backend-url";
   ```
7. Test the dashboard:
   - Task submission should call `/api/tasks`
   - Agent status should show 5 agents
   - Watch config update should work

---

## 🔧 Environment Variables

Create a `.env` file in the dashboard directory:

```bash
cd "/Users/vik043/Desktop/Agentic Workflow"
nano .env
```

Add:
```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# For device authentication (matches watch app)
DEVICE_TOKEN=uPzTmdc37OJLre1H3pXJvkDNesVmLcuk

# Optional - add as needed for connectors
SLACK_BOT_TOKEN=your_slack_token
TWITTER_API_KEY=your_twitter_key
# ... etc
```

---

## 🧪 End-to-End Test

Once everything is deployed:

1. **Speak to your watch**: "Post to Twitter: Hello world!"
2. **Watch sends message** → `POST /functions/v1/chat`
3. **Backend receives** → Coordinator routes to Data Processor Agent
4. **Agent processes** → (Future: will post to Twitter via connector)
5. **Watch config updates** → Status changes to "Processing complete"
6. **Watch polls** → Sees updated status within 3 seconds
7. **Lovable dashboard** → Shows task completion in agent status

---

## 📋 Deployment Checklist

- [ ] Deploy FastAPI backend to Railway/Render/Cloud
- [ ] Get deployment URL
- [ ] Update `BASE_URL` in KinNetwork.kt with deployment URL
- [ ] Rebuild watch APK: `./gradlew assembleDebug`
- [ ] Install APK on Galaxy Watch 4 via ADB
- [ ] Test watch config endpoint with curl
- [ ] Test chat endpoint with curl
- [ ] Open watch app and verify it connects
- [ ] Speak a test message on watch
- [ ] Verify message appears in backend logs
- [ ] Build Lovable dashboard with Prompt 1
- [ ] Update Lovable dashboard API_BASE_URL
- [ ] Test task submission from Lovable
- [ ] Test agent status display in Lovable
- [ ] Test watch config update from Lovable

---

## 🎉 What You'll Have After Deployment

- ✅ Watch app connects to your FastAPI agent swarm backend
- ✅ Voice messages from watch trigger agent processing
- ✅ Agents can update watch display via config endpoint
- ✅ Lovable dashboard shows real-time agent status
- ✅ Dashboard can submit tasks to agents
- ✅ Dashboard can control watch appearance remotely
- ✅ Full integration: **Watch ↔ FastAPI Agents ↔ Lovable Dashboard**

---

## 🐛 Troubleshooting

**Watch app crashes on launch:**
- Check BASE_URL is correct and ends with `/`
- Verify backend is actually running at that URL
- Check backend logs for connection attempts

**"Coordinator not initialized" error:**
- Backend needs 5-10 seconds to start up
- Wait and try again
- Check backend logs for startup errors

**Watch shows "Connecting..." forever:**
- Backend is down or unreachable
- Check network connectivity
- Verify BASE_URL in KinNetwork.kt
- Test endpoint with curl

**Voice messages not working:**
- Check backend logs for "⌚ Watch message:" entries
- Verify `/functions/v1/chat` endpoint returns 200
- Check device token matches in .env and KinNetwork.kt

**Lovable dashboard can't connect:**
- CORS is enabled with `allow_origins=["*"]`
- Check API_BASE_URL in Lovable code
- Open browser console (F12) to see exact error
- Verify backend is accessible from browser

---

## 📞 Need Help?

If you get stuck:
1. Check backend logs for errors
2. Use curl to test endpoints directly
3. Verify all URLs end with `/`
4. Ensure `.env` file has ANTHROPIC_API_KEY

**Quick Links:**
- [LOVABLE_PROMPTS.md](LOVABLE_PROMPTS.md) - All 6 prompts for building dashboard
- [QUICK_START.md](QUICK_START.md) - Detailed setup guide
- [LOVABLE_EXAMPLE_COMPONENT.tsx](LOVABLE_EXAMPLE_COMPONENT.tsx) - Reference React code

---

**Ready to deploy!** Start with Step 1 above. The integration is complete and ready to test.
