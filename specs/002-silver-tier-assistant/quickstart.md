# Quickstart: Silver Tier — Functional Assistant

**Branch**: `002-silver-tier-assistant` | **Date**: 2026-02-12
**Prerequisites**: Bronze Tier fully operational (vault created, Gmail watcher tested)

## Prerequisites Checklist

Before starting Silver Tier setup:

- [ ] Bronze Tier vault exists and opens in Obsidian
- [ ] Gmail watcher has been tested with real credentials
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Obsidian installed and vault path known
- [ ] WhatsApp Web accessible in a browser (phone connected)
- [ ] Mastodon account created on any instance (e.g., mastodon.social)
- [ ] Gmail App Password generated (for sending — separate from reading)

## Step 1: Install Silver Dependencies

```bash
# From project root
pip install -r requirements.txt
# Silver-specific additions:
pip install playwright Mastodon.py mcp
# Install Chromium browser for Playwright
playwright install chromium
```

## Step 2: Configure Environment Variables

Update `.env` file with Silver-specific variables:

```bash
# Bronze (already configured)
VAULT_PATH=./vault
CREDENTIALS_PATH=./credentials.json
POLL_INTERVAL=60

# Silver additions
GMAIL_ADDRESS=your.email@gmail.com
GMAIL_APP_PASSWORD=your-app-password-here
MASTODON_INSTANCE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your-mastodon-access-token
WHATSAPP_SESSION_PATH=~/.whatsapp_session
WHATSAPP_KEYWORDS=urgent,asap,deadline,emergency
```

### How to Get Mastodon Access Token

1. Log into your Mastodon instance web UI
2. Go to Preferences → Development → New Application
3. Name: "AI Employee Silver"
4. Scopes: `write:statuses` (minimum needed)
5. Submit → Copy the "Access Token"

### How to Get Gmail App Password

1. Go to Google Account → Security
2. Enable 2-Step Verification (if not already)
3. Go to Security → App passwords
4. Select app: "Mail", device: "Other (AI Employee)"
5. Copy the generated 16-character password

## Step 3: Set Up Vault Extension

Run the vault setup to add Silver folders:

```bash
python src/scripts/setup_vault.py --vault-path ./vault
# Silver adds: /Pending_Approval and /Logs folders
```

Verify in Obsidian:
- [ ] `/Pending_Approval` folder exists
- [ ] `/Logs` folder exists
- [ ] Bronze folders still intact (`/Inbox`, `/Needs_Action`, `/Done`)

## Step 4: Initialize WhatsApp Watcher

First run requires QR code scan:

```bash
python src/watchers/whatsapp_watcher.py --vault-path ./vault --headless false
```

1. Browser opens with WhatsApp Web
2. Scan QR code with your phone
3. Wait for "Connected" status
4. Send yourself a test message containing "urgent"
5. Verify: `vault/Needs_Action/whatsapp-*.md` file appears
6. Stop the watcher (Ctrl+C)

Subsequent runs will reuse the saved session.

## Step 5: Test Gmail Watcher (Bronze Compatibility)

Confirm Bronze Gmail watcher still works alongside WhatsApp:

```bash
# Terminal 1: Gmail watcher
python src/watchers/gmail_watcher.py --vault-path ./vault --interval 30

# Terminal 2: WhatsApp watcher
python src/watchers/whatsapp_watcher.py --vault-path ./vault
```

- [ ] Both watchers run without conflicts
- [ ] Each creates its own state file (`.watcher_state_gmail.json`, `.watcher_state_whatsapp.json`)
- [ ] New items appear in `/Needs_Action` from both sources

## Step 6: Test Reasoning Loop

Place a complex test item in `/Needs_Action`:

```markdown
---
type: manual
from: test
subject: Prepare Q1 report and send to team
date: 2026-02-12T10:00:00Z
status: pending
source_id: test-001
---

Need to prepare the Q1 report. Steps: gather data from finance,
draft the summary, review with manager, and send final version
to the entire team by Friday.
```

Run the processing skill:
```bash
# In Claude Code
/process-inbox
```

Verify:
- [ ] Item classified as "complex" (multiple steps detected)
- [ ] `Plan.md` created in `/Needs_Action` with checkbox steps
- [ ] Dashboard updated with Active Plans section

## Step 7: Test Approval Workflow

Place a test approval draft in `/Pending_Approval`:

```markdown
---
type: email-send
target: your.own.email@gmail.com
status: pending
created_date: 2026-02-12T12:00:00Z
mcp_tool: email_send
---

# Draft: Test Email

**To**: your.own.email@gmail.com
**Subject**: Silver Tier Test Email

## Content

This is a test email from the AI Employee Silver Tier.
If you receive this, the approval workflow is working!

## Approval

- [ ] Approved
- [ ] Rejected
```

1. Open the file in Obsidian
2. Check the `Approved` checkbox
3. Run: `/check-approvals`
4. Verify:
   - [ ] Email received at your own address
   - [ ] Draft moved to `/Done` with `status: executed`
   - [ ] MCP action log created in `/Logs`

## Step 8: Test Social Posting

```bash
# In Claude Code
/generate-social-post
```

1. Verify draft appears in `/Pending_Approval`
2. Review and edit the post content in Obsidian
3. Check "Approved" checkbox
4. Run: `/check-approvals`
5. Verify:
   - [ ] Post appears on your Mastodon profile
   - [ ] Draft moved to `/Done` with status: executed and post URL
   - [ ] MCP action log in `/Logs`

## Step 9: Test MCP Server Directly

```bash
# Start MCP server standalone for testing
python src/mcp/server.py
```

Verify the server starts without errors and lists available tools.

## Step 10: Configure Scheduling

### Windows (Task Scheduler)

```powershell
schtasks /create /tn "SilverPipeline" /tr "python E:\path\to\src\scheduling\scheduler.py --vault-path E:\path\to\vault --once" /sc minute /mo 5
```

### Linux/macOS (cron)

```bash
# Edit crontab
crontab -e
# Add line:
*/5 * * * * cd /path/to/project && python src/scheduling/scheduler.py --vault-path ./vault --once >> /tmp/silver-pipeline.log 2>&1
```

Verify:
- [ ] Scheduler runs every 5 minutes
- [ ] Logs appear in `/Logs/scheduler-*.md`
- [ ] Dashboard shows scheduler status with last run time

## Step 11: Full Pipeline Test

Run the complete pipeline manually:

```bash
# In Claude Code
/run-pipeline
```

Or via scheduler:

```bash
python src/scheduling/scheduler.py --vault-path ./vault --once
```

Verify:
- [ ] Gmail watcher polls (or reports no new emails)
- [ ] WhatsApp watcher polls (or reports no new messages)
- [ ] Reasoning loop processes any new items
- [ ] Approval checker processes any approved drafts
- [ ] Pipeline log created in `/Logs`
- [ ] Dashboard fully updated

## Success Criteria Validation

After completing all steps, validate Silver Tier success criteria:

| SC | Criterion | Test |
|----|-----------|------|
| SC-001 | Both watchers run 1 hour without crashes | Run Steps 5 for 1 hour |
| SC-002 | 90%+ classification accuracy on 20 items | Place 20 diverse test items, verify classification |
| SC-003 | Approved draft executed within one cycle | Approve a draft, wait for scheduler cycle |
| SC-004 | Test email sent + test Mastodon post published | Steps 7 and 8 |
| SC-005 | Scheduler runs 24 hours without failure | Leave scheduler running overnight |
| SC-006 | All actions logged with audit trail | Check `/Logs` for 10 consecutive actions |
| SC-007 | No action without approval | Attempt to trigger action without checking box |
| SC-008 | All new skills individually invocable | Run each skill from Steps 6-8 |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| WhatsApp "Phone not connected" | Phone offline or WhatsApp logged out | Reconnect phone, restart watcher |
| Gmail SMTP auth failed | Wrong App Password or 2FA issue | Regenerate App Password |
| Mastodon 401 Unauthorized | Invalid or expired token | Regenerate access token |
| "Watcher already running" | Stale lock file | Delete `.watcher.lock` manually |
| Playwright browser not found | Chromium not installed | Run `playwright install chromium` |
| MCP server won't start | Missing dependencies | Run `pip install mcp` |
