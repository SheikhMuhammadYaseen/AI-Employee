# AI Employee Dashboard

A Streamlit-based control panel for managing your Personal AI Employee. This dashboard provides a complete UI to monitor services, process inbox items, approve actions, generate reports, and configure all integrations — without touching any code or config files.

## Demo Mode vs Live Mode

This dashboard currently runs in **Demo Mode** with sample/showcase data. The demo data is **not real** — it exists only to demonstrate what each feature looks like and how it works.

**When you connect real APIs and accounts via the Configuration page, the dashboard automatically switches to Live Mode with real data.** No code changes needed.

| | Demo Mode (Current) | Live Mode (With Real APIs) |
|---|---|---|
| **Financial Data** | Sample numbers ($14,200 revenue etc.) | Real data from your Odoo accounting |
| **Service Health** | Hardcoded status badges | Real-time pings to each API |
| **Inbox Items** | Example emails/messages | Actual emails from Gmail, WhatsApp messages |
| **Social Studio** | Sample engagement stats | Real post analytics from each platform |
| **Review Desk** | Fake draft items | Real drafts that actually send emails/posts when approved |
| **Executive Brief** | Sample weekly report | Generated from your actual data |
| **Activity Log** | Example log entries | Real activity logs from the system |

**How to switch to Live Mode:** Go to **Configuration** → Configure your API credentials → Click **"Save & Test Connection"** → Start the watchers. That's it.

## Quick Start

```bash
cd dashboard
pip install -r requirements.txt
streamlit run Home.py
```

The dashboard opens at `http://localhost:8501` with a dark theme.

## Pages Overview

### Home (Dashboard Overview)

The main landing page with a bird's-eye view of everything.

| Section | What It Shows |
|---------|--------------|
| KPI Cards | Pending items, processed items, pending approvals, services online |
| Pipeline Flow | Visual flow: Inbox → Needs Action → Plans → Pending Approval → Done |
| Financial Overview | Revenue, expenses, net cash flow, receivables + bar chart |
| Service Health Grid | Status of all 7 connected services at a glance |
| Recent Activity | Last 10 actions taken by the AI Employee |

**Auto-Refresh:** Toggle in the sidebar to auto-refresh the page every 15/30/60/120 seconds.

---

### 1. Inbox Hub

Central inbox for all incoming items across workflow stages — process, classify, and route.

**How it works:**
1. Items arrive in the **Inbox** folder (via Gmail/WhatsApp watchers or manually).
2. Click **"Process Items"** to classify each item:
   - **Simple** → Moved directly to Done.
   - **Complex** → A plan is generated, stays in Needs Action.
   - **Action Required** → An approval draft is created in Pending Approval.
3. Use the **"Preview only"** checkbox to dry-run without moving files.
4. Browse all items across 5 tabs with search and filter.

---

### 2. Review Desk

Review and approve or reject actions the AI Employee wants to take.

**How it works:**
1. Items that need human approval appear here (e.g., sending an email, posting on social media).
2. Click **"Approve"** or **"Reject"** on each item (2-step confirmation to prevent mistakes).
3. After deciding on items, click **"Process All Decisions"** to execute approved actions and archive rejected ones.
4. Stale approvals (waiting 48+ hours) show a warning.

---

### 3. Executive Brief

Generate and view weekly executive briefing reports.

**How it works:**
1. Click **"Generate New"** to create a briefing for the selected date.
2. The briefing includes 5 sections:
   - Financial Summary (revenue, expenses, trends)
   - Operational Status (service health, automation stats)
   - Social Media Activity (posts, engagements by platform)
   - Bottlenecks & Risks (issues detected)
   - Recommended Actions (next steps)
3. Toggle between **Formatted View** (charts + cards) and **Full Text** (raw markdown).
4. **Download** the briefing as a markdown file.
5. View past briefings in the History section.

---

### 4. Social Studio

Manage social media content and engagement across 5 platforms.

**Supported Platforms:** LinkedIn, Mastodon, Facebook, Instagram, X (Twitter)

**How it works:**
1. View engagement metrics per platform (posts, engagements, followers).
2. To create new posts:
   - Enter your **topic/content** in the text area.
   - Select **target platforms** (multi-select).
   - Choose **tone** (Professional, Casual, Informative, etc.).
   - Toggle **hashtags** and **call-to-action**.
   - Click **"Generate Drafts"** → drafts are created in Pending Approval.
3. Each draft respects platform character limits (X=280, Mastodon=500, LinkedIn=3000, etc.).
4. Drafts must be approved on the Review Desk page before posting.

---

### 5. Financials

Accounting dashboard powered by Odoo integration.

**What it shows:**
- 4 KPI cards: Revenue, Expenses, Net Cash Flow, Receivables
- Revenue vs Expenses bar chart (weekly)
- Monthly Trend line chart (6 months)
- 3 tabs: **Invoices**, **Payments**, **Overdue** with full data tables

**Data Source:** Odoo Community via JSON-RPC. Configure Odoo credentials in Configuration.

---

### 6. Activity Log

Browse all system activity logs by category and date.

**Categories:**
- Service Calls (MCP tool invocations)
- Item Processing (classification decisions)
- Approvals (approve/reject actions)
- Automation Runs (loop executions)
- Scheduled Tasks (scheduler cycles)

**Views:**
- **Daily Log View** — Individual log entries per day, expandable.
- **Weekly Summary** — Aggregated stats with charts: activity by category (donut), daily activity (stacked bar), top actions, and detected issues.

---

### 7. System Status

Monitor the health of all connected services and integrations.

**Services Monitored:** Odoo, Gmail, LinkedIn, Mastodon, Facebook, Instagram, X (Twitter)

**How it works:**
1. Shows real-time status for each service (Operational / Degraded / Unavailable).
2. Displays last active time, recent error count, and error details.
3. Click **"Check All Services"** to ping every service and update status.
4. **Capabilities** section shows what each integration can do.

---

### 8. Automation

View and manage automated task schedules and manual runs.

**How it works:**
1. Shows all configured automated tasks with their enabled/paused status.
2. Displays the run interval and recent run history.
3. Click **"Run Now"** to manually trigger all active tasks immediately.
4. Configure the schedule (interval + which tasks to enable) on the Configuration page.

---

### 9. Configuration

Central configuration page for all services, watchers, and automation.

#### Connected Services
Configure API credentials for 8 services directly from the UI:

| Service | Credentials Required |
|---------|---------------------|
| Gmail | Email address + App Password |
| Odoo | URL, Database, Username, Password |
| LinkedIn | Access Token + Author ID |
| Mastodon | Instance URL + Access Token |
| Facebook | Page ID + Page Access Token |
| Instagram | IG User ID + Page Access Token |
| X (Twitter) | API Key, API Secret, Access Token, Access Secret |
| WhatsApp | Browser QR code (no API keys) |

**For each service:**
- Click **"Configure"** to expand the credential form.
- Fill in your credentials and click **"Save & Test Connection"** — credentials are saved to `.env` and the connection is tested in real-time.
- Click **"Clear Credentials"** to remove saved credentials.

#### Watchers
Start/stop background processes that poll for new items:
- **Gmail Watcher** — Polls Gmail for new emails.
- **WhatsApp Watcher** — Monitors WhatsApp Web for messages.

#### Automation Schedule
- Set the **polling interval** (1-60 minutes).
- Toggle individual tasks on/off (approval checker, inbox watcher, health monitor).
- Click **"Save Schedule"** to persist changes.

---

## Project Structure

```
dashboard/
├── Home.py                   # Home page (Dashboard Overview)
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml           # Dark theme + server config
├── pages/
│   ├── 1_Inbox_Hub.py        # Inbox processing & classification
│   ├── 2_Review_Desk.py      # Human-in-the-loop approval system
│   ├── 3_Executive_Brief.py  # CEO weekly briefing generator
│   ├── 4_Social_Studio.py    # Multi-platform social media management
│   ├── 5_Financials.py       # Odoo accounting dashboard
│   ├── 6_Activity_Log.py     # Activity log browser
│   ├── 7_System_Status.py    # Service monitoring
│   ├── 8_Automation.py       # Automation task runner
│   └── 9_Configuration.py    # Service configuration & watchers
└── utils/
    ├── connection_tester.py   # Per-service API connection tests
    ├── env_manager.py         # Read/write .env file (atomic)
    ├── formatters.py          # Currency, timestamps, friendly names
    ├── icons.py               # Lucide SVG icon library (40+ icons)
    ├── path_setup.py          # PROJECT_ROOT and VAULT_PATH setup
    ├── theme.py               # Custom dark theme CSS injection
    └── vault_reader.py        # Vault markdown file parser
```

## Key Features

- **Demo Mode** — Ships with realistic demo data. All pages gracefully fall back to demo when no services are connected.
- **Live Mode** — Connect real APIs via Configuration and everything switches to live data automatically.
- **Auto-Refresh** — Configurable auto-refresh on the home page (15s to 120s intervals).
- **Human-in-the-Loop** — Every external action (email, social post, payment) requires explicit approval before execution.
- **Dark Theme** — Custom dark UI with cyan/green accent colors.
- **Atomic Config Writes** — `.env` file updates use temp file + rename to prevent corruption.
- **Real-time Connection Testing** — Test API connections directly from the dashboard with detailed feedback.

## Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web dashboard framework |
| `plotly` | Interactive charts and graphs |
| `python-frontmatter` | Parse vault markdown files with YAML headers |
| `python-dotenv` | Environment variable management |
| `streamlit-autorefresh` | Auto-refresh pages on a timer |
| `requests` | HTTP requests for API connection testing |
| `pandas` | Data tables and dataframes |

## Data Flow

```
Gmail/WhatsApp Watchers → vault/Inbox/
                              ↓
Inbox Hub (classify) → vault/Needs_Action/
                              ↓
              ┌─── Simple → vault/Done/
              ├─── Complex → Plan generated
              └─── Action → vault/Pending_Approval/
                              ↓
Review Desk (approve/reject) → Execute via MCP tools
                              ↓
                         vault/Done/ + vault/Logs/
```
