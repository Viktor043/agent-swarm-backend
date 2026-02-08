# Lovable Prompts for Agent Swarm Interface

Use these prompts in Lovable to build your agent swarm dashboard. You have unlimited credits, so iterate until it's perfect!

## Prompt 1: Create the Main Dashboard Page

```
Create a modern agent swarm dashboard with the following:

1. Header with title "Agent Swarm Control Center" and status indicator (green dot if backend is online)

2. Main Task Submission Section:
   - Large text area for task description
   - Dropdown for priority (normal, high, urgent)
   - Submit button that calls POST /api/tasks
   - Recent tasks list below showing task_id, status, and message

3. Agent Status Grid (3 columns on desktop, 1 on mobile):
   - Show each agent as a card with:
     - Agent name and role icon
     - Status badge (idle, busy, offline)
     - Current task count
     - Completed tasks count
     - Failed tasks count
   - Auto-refresh every 5 seconds calling GET /api/agents

4. Watch Messages Section:
   - List of recent messages from the watch
   - Each message shows timestamp and text
   - Click to route message to specific connector

5. Style:
   - Dark mode with gradient background (purple/blue)
   - Glassmorphism cards
   - Smooth animations on status changes
   - Use Shadcn UI components throughout
   - Responsive mobile-first design

API Base URL: http://localhost:8000 (or your deployed URL)
```

## Prompt 2: Social Media Connector Interface

```
Add a Social Media Connector panel to the dashboard:

1. Four tabs: Twitter, LinkedIn, Facebook, Instagram

2. For each tab:
   - Text area for post content (with character counter)
   - Image upload zone (drag & drop)
   - Preview of post
   - Post button that calls POST /api/connectors/post with:
     {
       "connector": "twitter", // or linkedin, facebook, instagram
       "content": "message text",
       "media": []
     }
   - Recent posts history (timestamp, platform, content, status)

3. Quick Actions Section:
   - "Post to All Platforms" button (posts to all 4 at once)
   - Schedule post for later (date/time picker)
   - Save as draft

4. Style:
   - Platform-specific brand colors for each tab
   - Icons for each platform
   - Success/error toast notifications
   - Loading states during posting

Integrate with the main dashboard layout as a collapsible sidebar
```

## Prompt 3: Agent Deployment Controls

```
Create an Agent Deployment page with:

1. Agent List Table showing:
   - Agent Name (Coordinator, Developer, Tester, Deployer, Data Processor)
   - Status (Running, Stopped, Error)
   - Start/Stop buttons for each agent
   - Logs button (opens modal with recent agent logs)
   - Configuration button (edit agent settings)

2. System Status Section:
   - Backend API status (ping /health endpoint)
   - Message bus status (Redis connection)
   - Context store status
   - Active tasks count
   - System uptime

3. Deployment Actions:
   - "Start All Agents" button
   - "Stop All Agents" button
   - "Restart Agent System" button
   - "View System Logs" button

4. Configuration Panel:
   - Environment variables editor (masked for secrets)
   - Workflow directory path
   - Tools directory path
   - Save configuration button

5. Style:
   - Command center aesthetic (think mission control)
   - Real-time status updates via polling
   - Color-coded status indicators
   - Terminal-style logs display
```

## Prompt 4: Code Deployment Interface

```
Add a Code Deployment section:

1. Watch App Deployment:
   - Current version display
   - "Build APK" button → calls agent to build watch-app
   - Download APK button (once built)
   - Deploy to device button
   - Build logs viewer

2. Dashboard Deployment:
   - Current deployment URL
   - "Deploy to Production" button
   - Deployment status tracker (building, deploying, deployed)
   - Rollback button (reverts to previous version)
   - Deployment logs

3. GitHub Integration:
   - Current branch display
   - Pending PRs count
   - "Create PR" button for current changes
   - Merge PR button (with approval)

4. Lovable Sync:
   - "Sync from GitHub" button
   - "Push to GitHub" button
   - Sync status indicator
   - Last sync timestamp

5. Style:
   - DevOps dashboard aesthetic
   - Progress bars for deployments
   - Success/error states with clear messaging
   - Logs in monospace font with syntax highlighting
```

## Prompt 5: Live Watch Communication

```
Create a Watch Communication panel:

1. Live Message Feed:
   - Real-time display of messages from Galaxy Watch
   - Each message shows:
     - Timestamp
     - Message text
     - Device ID
     - Status (received, processing, completed)

2. Quick Actions per Message:
   - "Send to Slack" button
   - "Email This" button
   - "Post to Twitter" button
   - "Add to Calendar" button
   - "Custom Task" (opens task submission form pre-filled)

3. Message History:
   - Searchable list of all watch messages
   - Filter by date, status, connector
   - Export to CSV

4. Watch Configuration:
   - Send config updates to watch via /api/watch-config endpoint
   - Set animation URL
   - Set status text
   - Set primary color
   - "Push to Watch" button

5. Test Panel:
   - Send test message to watch
   - Simulate watch message from dashboard
   - Test connector integrations

6. Style:
   - Chat interface aesthetic
   - Message bubbles with smooth animations
   - Real-time updates (poll every 2 seconds)
   - Connector icons next to each action button
```

## Prompt 6: Analytics & Monitoring Dashboard

```
Add an Analytics page showing:

1. Task Metrics:
   - Total tasks processed (today, week, month)
   - Success rate percentage
   - Average task completion time
   - Most common task types (pie chart)

2. Agent Performance:
   - Tasks completed per agent (bar chart)
   - Agent uptime percentage
   - Failed tasks by agent
   - Current workload distribution

3. Connector Usage:
   - Posts per platform (line chart over time)
   - Most used connector
   - Connector error rates
   - API rate limit status

4. System Health:
   - API response time graph
   - Memory usage
   - CPU usage
   - Database query count

5. Recent Activity Timeline:
   - Chronological log of all system events
   - Filterable by agent, task type, status
   - Click to view details

6. Style:
   - Dashboard with data visualization
   - Interactive charts (use Recharts library)
   - Refresh button to reload metrics
   - Export data to CSV/PDF
```

## How to Use These Prompts in Lovable

1. **Go to Lovable.dev** and create a new project or open your existing dashboard project

2. **Start with Prompt 1** - paste the entire prompt into Lovable's chat

3. **Iterate** - Lovable will generate the code. Review it, then ask for modifications:
   - "Make the cards more glassmorphic"
   - "Add more animations"
   - "Change the color scheme to cyan/purple"

4. **Add features sequentially** - Once Prompt 1 is done, use Prompt 2, then 3, etc.

5. **Configure API endpoint** - Update the API base URL to point to your deployed FastAPI backend

6. **Test locally** - Lovable provides a preview. Test all buttons and API calls

7. **Deploy** - Use Lovable's one-click deploy to get a live URL

## API Endpoints Your Lovable App Will Call

```typescript
// Example API calls from your Lovable frontend:

// Submit a task to agents
const response = await fetch('http://localhost:8000/api/tasks', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    description: "Build new watch app feature",
    priority: "high"
  })
});

// Get all agents status
const agents = await fetch('http://localhost:8000/api/agents');
const agentData = await agents.json();

// Post to social media
const post = await fetch('http://localhost:8000/api/connectors/post', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    connector: "twitter",
    content: "Hello from my Galaxy Watch!"
  })
});

// Send watch message
const watchMsg = await fetch('http://localhost:8000/api/watch-message', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Test message",
    device_id: "watch_001"
  })
});
```

## Next Steps

1. **Copy Prompt 1** and paste it into Lovable
2. **Let Lovable generate** the dashboard (should take 1-2 minutes)
3. **Review and iterate** - ask for changes until you're happy
4. **Deploy the FastAPI backend** (we'll do this next)
5. **Connect Lovable to backend** by updating the API URL
6. **Test end-to-end** - submit a task from Lovable, watch agents process it

Your unlimited credits mean you can iterate as much as you want!
```
