# Lovable Prompt — Agent Swarm Dashboard

Paste the entire prompt below into Lovable to rebuild the dashboard. This is a single unified prompt that generates all 5 pages. It preserves every API call exactly as-is — only the visual layer changes.

**Backend URL**: Set `NEXT_PUBLIC_API_URL` in your Lovable project environment to your deployed Railway URL. Defaults to `http://localhost:8000`.

---

## The Prompt

```
Rebuild the entire dashboard UI from scratch. Do NOT change any API calls, endpoints, request bodies, or response handling. Only the visual presentation changes.

DESIGN SYSTEM (apply globally):
- border-radius: 0 on EVERYTHING. Zero rounded corners anywhere. No exceptions.
- Font: "IBM Plex Mono" (import from Google Fonts) for all text. Monospace everywhere.
- Background: flat #0a0a0a (near-black). No gradients anywhere.
- Cards/containers: 1px solid #333 border, background #111. No shadows, no blur, no glassmorphism.
- Text: #e0e0e0 for body, #ffffff for headings, #666 for muted/secondary.
- Accent color: #00ff41 (terminal green) for active states, success, and primary actions.
- Error/danger: #ff3333.
- Warning: #ffaa00.
- Buttons: background #222, border 1px solid #444, text #e0e0e0. On hover: border-color #00ff41, text #00ff41. No gradients, no rounded corners.
- Inputs/textareas: background #0a0a0a, border 1px solid #333, text #e0e0e0. On focus: border-color #00ff41.
- Status indicators: small squares (not circles, not dots). 8x8px. Green=#00ff41, Yellow=#ffaa00, Red=#ff3333, Gray=#444.
- No animations, no transitions, no hover glow effects. Instant state changes only.
- Spacing: tight, utilitarian. Padding 12px on cards, 8px on smaller elements.
- No decorative elements. No icons unless they convey essential meaning.
- Page max-width: 960px, centered.
- Navigation: horizontal top bar with plain text links, underline on active page. No icons in nav.

API_BASE_URL: use `process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"` everywhere.

Build these 5 pages with a shared layout and top navigation bar:

---

PAGE 1: WATCHFACE (/watchface)

Purpose: Configure the Galaxy Watch 4 (40mm, 396x396px AMOLED) display.

Layout:
- Left column (50%): Configuration form
- Right column (50%): Live preview (dark square, 396x396 scaled to fit, showing current status text, color, and animation if set)

Configuration form fields:
- "Status Text" — text input. The text displayed on the watch face.
- "Primary Color" — text input for hex color (e.g. #9333EA). Show a small color swatch next to input.
- "Screen Size" — read-only display: "396 x 396px (Samsung Galaxy Watch 4, 40mm)"
- "Animation URL" — text input for Lottie animation URL.
- "Push to Watch" button — calls POST /api/update-watch-config with body: { status, animation_url, primary_color }

Below the form, an "Animation Library" section:
- A simple table with columns: Name, URL, Status Assignment
- "Status Assignment" is a dropdown to bind an animation to a status keyword (e.g. "idle", "processing", "error", "success")
- An "Add Animation" row at the bottom with inputs for name and URL
- Store animation library in localStorage.
- Animation specs note displayed as plain text: "Lottie JSON only. Optimize for 396x396px AMOLED. Keep file size under 500KB."

On page load, call GET /functions/v1/watch-config and populate the form with current values.

---

PAGE 2: CHAT (/chat)

Purpose: Conversation interface with the Conductor agent.

Layout:
- Left sidebar (240px): Conversation list
- Main area: Active conversation

Left sidebar:
- List of conversation subjects. Each is a row with the subject name and a small timestamp.
- Each row is editable: double-click to rename the subject manually.
- At the top of the sidebar: "New Conversation" button (plain text with + prefix).
- Conversations are stored in localStorage with structure: { id, subject, messages[], created_at, updated_at }
- The Conductor agent automatically categorizes and renames conversation subjects based on content. After each assistant reply, use a simple heuristic: if subject is still "New Conversation", set it to the first 40 characters of the first user message.

Main chat area:
- Messages displayed as simple rows. No chat bubbles.
- User messages: left-aligned, text color #e0e0e0, prefix "> " in #666.
- Assistant messages: left-aligned, text color #00ff41, prefix "$ " in #666.
- Input at bottom: full-width textarea, 2 rows, with "Send" button to the right.
- On send: POST to /functions/v1/chat with { message: text }. Display the reply_text from response as assistant message.
- Show "Sending..." as a disabled assistant message row while waiting for response.
- After receiving response, also POST to /api/tasks with { description: message, priority: "normal" } to ensure the agent swarm processes it.

Below the chat, a "Saved Contexts" section:
- Fetched from GET /api/saved-contexts on page load.
- Simple table: Timestamp | Text | Source
- Auto-refresh every 10 seconds.

---

PAGE 3: CONNECTORS (/connectors)

Purpose: Manage all external service connections and LLM providers.

Section 1 — "Service Connectors":
- Grid of connector cards (2 columns). Each card shows:
  - Connector name (plain text, bold)
  - Status: "Connected" (#00ff41) or "Not Configured" (#666)
  - An API key input field (type=password, with show/hide toggle)
  - "Save" button per connector
- Default connectors to show:
  - Slack (key: SLACK_BOT_TOKEN)
  - Twitter/X (key: TWITTER_API_KEY)
  - LinkedIn (key: LINKEDIN_CLIENT_ID)
  - Facebook (key: FACEBOOK_ACCESS_TOKEN)
  - Instagram (key: INSTAGRAM_ACCESS_TOKEN)
  - Google Calendar (key: GOOGLE_CALENDAR_CREDENTIALS)
  - Google Sheets (key: GOOGLE_SHEETS_CREDENTIALS)
  - GitHub (key: GITHUB_TOKEN)
- "Add Connector" row at the bottom: text inputs for name and API key field name.
- All keys stored in localStorage (display-only; actual keys are in backend .env).
- Quick post section: select a connector from dropdown, type content, click "Post" → calls POST /api/connectors/post with { connector, content }.

Section 2 — "LLM Providers":
- Same card layout. Each card shows:
  - Provider name
  - Model name (text input)
  - API key input (password field)
  - "Test Connection" button (for now just validates key is non-empty and shows success)
- Default LLM providers:
  - Anthropic / Claude (key: ANTHROPIC_API_KEY, model: claude-sonnet-4-5-20250929)
  - Google / Gemini (key: GOOGLE_API_KEY, model: gemini-pro)
  - OpenAI / GPT (key: OPENAI_API_KEY, model: gpt-4)
  - Mistral (key: MISTRAL_API_KEY)
  - Groq (key: GROQ_API_KEY)
- "Add LLM Provider" row at bottom.
- All stored in localStorage.

---

PAGE 4: AGENTS (/agents)

Purpose: Agent configuration, context management, and sub-agent orchestration.

Section 1 — "Context" (two equal columns):

Left column — "Workflow Context":
- A large textarea (12 rows, full-width) showing the current software architecture context.
- On page load, fetch GET /api/codebase/context and display the codebase object as formatted text.
- "Refresh" button that calls POST /api/codebase/refresh and reloads.
- Label: "Continuously updated by the Conductor Agent. Describes the full software architecture, tools, and workflows."

Right column — "User Context":
- A large textarea (12 rows, full-width) for user-specific context.
- Editable. Stored in localStorage under key "user_context".
- Label: "Important context about the user. Updated by the Conductor Agent and editable manually."
- Auto-save on blur.

Section 2 — "Conductor Agent":
- "Model" dropdown: populated from the LLM providers saved on the Connectors page (read from localStorage). Default: "Anthropic / Claude".
- Current status: fetch from GET /api/agents and find the coordinator agent. Show status, current tasks, completed tasks, failed tasks as inline key:value pairs.

Section 3 — "Sub-Agents":
- Table with columns: Name | Role | Model | Max Context | Status | Actions
- On page load, fetch GET /api/agents and populate.
- Status shown as colored square indicator (idle=green, busy=yellow, error=red).
- "Add Sub-Agent" form below the table: Name, Role (dropdown: developer, tester, deployer, data_processor), Model (dropdown from LLM providers), Max Context (number input, tokens).
- Sub-agent additions stored in localStorage.
- Note below table: "The Conductor distributes work to sub-agents, respecting each agent's context limit."

---

PAGE 5: STATUS (/status)

Purpose: System health, deployment history, and operational overview.

Section 1 — "System Health":
- Fetch GET /health on page load. Show:
  - Backend: "Online" / "Offline" with status square
  - Coordinator: status
  - Total Agents: count
  - Active Tasks / Completed Tasks / Failed Tasks: as inline numbers
- Auto-refresh every 5 seconds.

Section 2 — "Agent Overview":
- Fetch GET /api/agents. Simple table:
  - Agent ID | Role | Status | Active | Completed | Failed | Capabilities
- Capabilities shown as comma-separated plain text.
- Auto-refresh every 5 seconds.

Section 3 — "Deployment History":
- Fetch GET /api/deployments. Table:
  - Timestamp | Project | Target | Status | URL
- Status: "success" in green, "failed" in red.
- If URL exists, make it a clickable link.

Section 4 — "System Stats":
- Fetch GET /api/system/stats. Display the raw JSON response in a monospace pre block with syntax highlighting (just color strings green, numbers yellow, keys white).
- "Refresh" button to re-fetch.

---

IMPORTANT RULES:
1. Do NOT change any fetch() URLs, request bodies, or response handling logic. The API contract is fixed.
2. Do NOT add any new API endpoints or modify existing ones.
3. All localStorage usage is for frontend-only display preferences (connector labels, animation library, user context, conversation history). The real API keys live in the backend .env.
4. Use Shadcn UI components (Button, Input, Textarea, Card, Table, Badge, Tabs) but override all border-radius to 0.
5. Use sonner for toast notifications. Keep toast messages short and plain.
6. The entire app should feel like a well-made developer tool — think pgAdmin, Grafana dark mode, or a terminal dashboard. No consumer app aesthetics.
```

---

## API Reference

These are the endpoints the dashboard calls. All are served by the FastAPI backend.

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Health
GET  /
GET  /health

// Agents
GET  /api/agents
GET  /api/agents/{agent_id}

// Tasks
POST /api/tasks                    // { description, priority, task_type? }

// Watch Integration
GET  /functions/v1/watch-config
POST /functions/v1/chat            // { message }
POST /api/update-watch-config      // { status, animation_url, primary_color }
POST /api/watch-message            // { message, device_id? }

// Contexts
GET  /api/saved-contexts

// Connectors
POST /api/connectors/post          // { connector, content, media? }

// Deployments
GET  /api/deployments
GET  /api/deployments/{task_id}

// Codebase
GET  /api/codebase/context
POST /api/codebase/refresh

// System
GET  /api/system/stats
```
