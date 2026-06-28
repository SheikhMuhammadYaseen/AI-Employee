# Personal AI Employee — Gold Tier

An autonomous AI employee that monitors multiple sources (Gmail, WhatsApp), integrates with Odoo accounting, posts to 5 social platforms (LinkedIn, Mastodon, Facebook, Instagram, X), generates weekly CEO Briefings, and autonomously completes multi-step tasks via the Ralph Wiggum loop — all managed through an Obsidian vault with human‑in‑the‑loop approval.

> All code in this project is AI‑generated via Claude Code, per the project constitution (Principle II: Agent Behavior Rules).

## Architecture

```
 Perception              Reasoning               Safety Gate             Action
 (Senses)                (Brain)                 (Human)                 (Hands)

 gmail_watcher.py --+                                         +-- gold-accounting --> Odoo (JSON-RPC)
                    +--> classifier.py --> planner.py --+     |    create_invoice, record_payment,
 whatsapp_watcher.py/   (3-way classify)   (Plan.md)   |     |    get_financial_summary
                                                        v     |
                          simple -----------------> /Done     +-- gold-social --> 5 platforms
                          complex ----------------> Plan.md   |    linkedin, mastodon, facebook, instagram, x
                          action_required --------> /Pending  |
                                                        |     +-- gold-communications --> Gmail SMTP
                               Ralph Wiggum Loop <-----+     |    email_send
                               (auto-iterate Plan.md)        |
                                                     [x] Approved?
                                                        |
                                                  checker.py --> MCP Router --> 3 servers
                                                                          |
                              Audit Logger <------ all actions -----------+
                              Service Health <----- all services
                              CEO Briefing <------- weekly Monday
```

## Gold Tier Documentation
- Architecture details: `vault/Architecture.md`
- Operational insights: `vault/Lessons_Learned.md`
- Audit logs: `vault/Logs/` (daily rotated Markdown files)
- Quick start, usage, and development guides are all in this README.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials:
# - Gmail OAuth2 (credentials.json) for Gmail watcher
# - Gmail App Password for email sending via MCP
# - LinkedIn OAuth2 token for LinkedIn posting (w_member_social scope)
# - Mastodon access token for social posting
# - Facebook Page Access Token, Instagram User ID, X API credentials, Odoo DB credentials
```

### 3. Set Up Gmail OAuth2 (Watcher)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Create OAuth 2.0 Client ID (Desktop application)
4. Download as `credentials.json` in the project root

### 4. Initialize the Vault

```bash
python src/scripts/setup_vault.py --vault-path ./vault
```

Open `vault/` as a vault in Obsidian. You'll see: Inbox, Needs_Action, Pending_Approval, Done, Logs.

### 5. Run Watchers

```bash
# Gmail watcher (Bronze + Silver)
python src/watchers/gmail_watcher.py --vault-path ./vault

# WhatsApp watcher (Silver) — requires first‑time QR scan
python src/watchers/whatsapp_watcher.py --vault-path ./vault
```

### 6. Process Inbox with Silver Reasoning

```bash
# Three‑way classification: simple → Done, complex → Plan.md, action → Pending_Approval
claude /process-inbox

# Or run the full pipeline (classify + check approvals + update dashboard)
claude /run-pipeline
```

### 7. Approve Actions in Obsidian

Open `vault/Pending_Approval/` in Obsidian. Check `- [x] Approved` or `- [x] Rejected`, then:

```bash
# Process approved/rejected drafts
claude /check-approvals
```

### 8. Start Odoo (Gold Tier)

```bash
docker compose -f docker-compose.gold.yml up -d
# Odoo available at http://localhost:8069 (admin/admin, test DB with demo data)
```

### 9. Generate Social Posts (Multi‑Platform)

```bash
claude /generate-social-post "weekly business update"
# Creates drafts for LinkedIn, Mastodon, Facebook, Instagram, X in /Pending_Approval
```

### 10. Generate CEO Briefing

```bash
claude /generate-briefing
# Auto‑generates `vault/Briefing.md` with financial, operational, social, bottlenecks, actions
```

### 11. Run Ralph Wiggum Loop

```bash
claude /ralph-wiggum
# Autonomously iterates through Plan.md steps, creates approval drafts for action steps
```

### 12. Streamlit Dashboard

```bash
cd dashboard
pip install -r requirements.txt
streamlit run Home.py
# Opens at http://localhost:8501 with dark theme
```

A full web UI with 10 pages: Home, Inbox Hub, Review Desk, Executive Brief, Social Studio, Financials, Activity Log, System Status, Automation, Configuration. Runs in demo mode by default; connect real APIs via the Configuration page for live mode.

### 13. Automated Scheduling

```bash
# Run all components once
python src/scheduling/scheduler.py --vault-path ./vault --once

# Run on a 5‑minute interval (or cron)
python src/scheduling/scheduler.py --config src/scheduling/scheduler_config.json
```

## Project Structure

```
src/
├── watchers/
│   ├── base_watcher.py          # Shared base class (state, lock, vault write)
│   ├── gmail_watcher.py         # Gmail polling watcher (Bronze)
│   └── whatsapp_watcher.py      # WhatsApp Web watcher (Silver, Playwright)
├── reasoning/
│   ├── classifier.py            # Three‑way item classifier (+ Gold audit logging)
│   ├── planner.py               # Plan.md generator with checkboxes
│   └── ralph_wiggum.py          # Gold: Autonomous task loop engine
├── approval/
│   └── checker.py               # Approval workflow (6 platform types)
├── mcp/
│   ├── server.py                # Silver MCP server (kept for compatibility)
│   ├── mcp_accounting.py        # Gold: Odoo accounting MCP server
│   ├── mcp_social.py            # Gold: Multi‑social MCP server (5 platforms)
│   ├── mcp_communications.py    # Gold: Email MCP server
│   ├── router.py                # Gold: MCP server registry/router
│   ├── config.py                # Environment config loader
│   └── tools/
│       ├── email_send.py        # Gmail SMTP email sender
│       ├── linkedin_post.py     # LinkedIn Share API poster (Silver)
│       ├── mastodon_post.py     # Mastodon API poster
│       ├── facebook_post.py     # Gold: Facebook Graph API poster
│       ├── instagram_post.py    # Gold: Instagram Graph API poster
│       ├── x_post.py            # Gold: X/Twitter Tweepy poster
│       ├── social_summary.py    # Gold: Social engagement summary
│       ├── odoo_client.py       # Gold: Odoo JSON‑RPC client
│       ├── odoo_invoice.py      # Gold: Invoice create/list
│       ├── odoo_payment.py      # Gold: Payment record/list
│       └── odoo_reports.py      # Gold: Financial summary
├── briefing/
│   └── briefing_generator.py    # Gold: CEO Weekly Briefing generator
├── logging/
│   └── audit_logger.py          # Gold: Structured audit logging
├── health/
│   └── service_health.py        # Gold: Service health tracker
├── recovery/
│   └── retry.py                 # Gold: Retry with exponential backoff
├── scheduling/
│   ├── scheduler.py             # Component scheduler with logging
│   └── scheduler_config.json    # Schedule config (Silver + Gold components)
├── scripts/
│   └── setup_vault.py           # Vault creation (idempotent)
└── templates/
    ├── briefing_template.md     # Gold: CEO Briefing template
    ├── vault_item_template.md   # Vault item template
    ├── plan_item_template.md    # Plan.md template (Silver)
    └── approval_draft_template.md # Approval draft template

.claude/skills/
├── vault-read.md                # Read vault items
├── vault-write.md               # Write vault files
├── process-inbox.md             # Process inbox (3‑way classification)
├── plan-task.md                 # Generate Plan.md for complex items
├── check-approvals.md           # Process approval queue (5 platforms)
├── generate-social-post.md      # Multi‑platform social post drafts
├── run-pipeline.md              # Full pipeline orchestration (Gold)
├── ralph-wiggum.md              # Gold: Autonomous task loop
├── generate-briefing.md         # Gold: CEO Weekly Briefing
├── audit-report.md              # Gold: Audit log report
├── odoo-accounting.md           # Gold: Odoo accounting interface
└── generate-architecture.md     # Gold: Architecture documentation

docker-compose.gold.yml          # Odoo Community v19 + PostgreSQL 16

dashboard/                       # Streamlit web dashboard
├── Home.py                      # Home page (Dashboard Overview)
├── requirements.txt
├── .streamlit/config.toml       # Dark theme + server config
├── pages/                       # 9 pages (Inbox Hub → Configuration)
└── utils/                       # theme, vault_reader, icons, connection_tester, etc.

vault/                           # Obsidian vault (gitignored)
├── Dashboard.md
├── Company_Handbook.md
├── Briefing.md                  # Gold: Weekly CEO Briefing
├── Needs_Action/
├── Pending_Approval/
├── Done/
├── Plans/                       # Gold: Ralph Wiggum task plans
└── Logs/                        # Audit logs (5 categories, daily rotation)

tests/
├── unit/                        # 170+ unit tests
└── integration/                 # 66+ integration tests
```

## Running Tests

```bash
python -m pytest tests/ -v
# 247 tests total: 247 passed, 3 skipped (Odoo integration requires Docker)
```

## Tier Progression

### Bronze Tier (Complete)
- Single Obsidian vault with standard folders
- Gmail watcher (polling)
- Claude Code read/write/process skills
- Local‑only, privacy‑focused

### Silver Tier (Complete)
- Multiple watchers: Gmail + WhatsApp (Playwright)
- Three‑way classification: simple / complex / action_required
- Plan.md generation with checkbox steps
- Human‑in‑the‑loop approval workflow
- MCP server with email_send + linkedin_post + mastodon_post tools
- Automated scheduling with partial failure handling
- 7 Claude Code skills for full pipeline orchestration
- 108 tests (all passing)

### Gold Tier (Current)
- **Odoo Accounting Integration**: JSON‑RPC client, invoices, payments, financial summaries via Docker Odoo v19
- **Multi‑Social Media**: LinkedIn, Facebook, Instagram, X (Twitter) posting + Mastodon — 5 platforms via LinkedIn Share API, Graph API, and Tweepy
- **3 MCP Servers**: gold‑accounting, gold‑social, gold‑communications with fault isolation
- **Weekly CEO Briefing**: Auto‑generated Monday mornings with financial, operational, social, bottleneck, and action sections
- **Ralph Wiggum Loop**: Autonomous multi‑step task completion with approval gates and enforced limits (10 iterations, 30 min)
- **Comprehensive Audit Logging**: 5 categories (mcp, classification, approval, loop, scheduler) with daily rotation
- **Error Recovery**: Exponential backoff retries, service health tracking (operational → degraded → unavailable)
- **12 Claude Code Skills**: Extended from Silver with Ralph Wiggum, briefing, audit, Odoo, and architecture skills
- **Streamlit Dashboard**: Full web UI in `dashboard/` — 10 pages, real-time monitoring, auto-refresh, dark theme, demo mode fallback
- **247 tests** (139 new Gold tests)

See project specs and design documents in the `specs/` directory for full specification, plans, and task breakdown.
Project completed with assistance from Claude (AI).
