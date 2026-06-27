# Quickstart: Gold Tier — Autonomous Employee

**Branch**: `003-gold-tier-autonomous` | **Date**: 2026-02-12
**Prerequisites**: Silver Tier complete and operational

## 1. Prerequisites

### Required Software
- Python 3.11+ (already installed from Silver)
- Docker Desktop (for Odoo)
- Git (already configured from Silver)

### Required Accounts (Test/Dev Only)
- **Odoo**: Local Docker instance (no external account needed)
- **Meta (Facebook/Instagram)**: Developer account at developers.facebook.com + test Facebook Page
- **X (Twitter)**: Developer account at developer.x.com (Free tier)
- **Mastodon**: Existing account from Silver Tier
- **Gmail**: Existing App Password from Silver Tier

## 2. Install Dependencies

```bash
# From project root
pip install tweepy requests
# Silver dependencies already installed: python-frontmatter pyyaml playwright Mastodon.py mcp
```

## 3. Start Odoo via Docker

```bash
# From project root
docker compose -f docker-compose.gold.yml up -d

# Wait ~30 seconds for Odoo to initialize
# Verify: open http://localhost:8069 in browser
# Default login: admin / admin
```

### Verify Odoo Accounting
1. Log in to http://localhost:8069
2. Navigate to Invoicing app (should be pre-installed)
3. Confirm demo data is loaded (sample partners, chart of accounts)

### Reset Odoo Test Data (if needed)
```bash
docker compose -f docker-compose.gold.yml down -v
docker compose -f docker-compose.gold.yml up -d
```

## 4. Configure Environment Variables

Add Gold Tier variables to `.env` (Silver variables already present):

```env
# === Gold Tier: Odoo ===
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_gold
ODOO_USER=admin
ODOO_PASSWORD=admin

# === Gold Tier: Meta (Facebook/Instagram) ===
META_PAGE_ACCESS_TOKEN=your_page_access_token_here
META_PAGE_ID=your_page_id_here
META_IG_USER_ID=your_ig_user_id_here

# === Gold Tier: X (Twitter) ===
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_token_secret
```

## 5. Set Up Meta Developer App (Facebook/Instagram)

1. Go to https://developers.facebook.com → Create App → Business type
2. Add "Facebook Login" and "Instagram Graph API" products
3. Generate Page Access Token:
   - Go to Graph API Explorer
   - Select your App → Get User Token → select `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`
   - Exchange for long-lived token (60-day expiry)
4. Copy Page ID and Instagram User ID to `.env`
5. **Test Mode**: Use the Test Page created with your app (posts won't be public)

## 6. Set Up X Developer Account

1. Go to https://developer.x.com → Sign up for Free tier
2. Create a Project and App → copy API Key + Secret
3. Generate Access Token + Secret (with Read and Write permissions)
4. Copy all four values to `.env`
5. **Test Mode**: Free tier posts are real — use a test/secondary account

## 7. Configure MCP Servers

Add all three MCP servers to Claude Code configuration:

```json
{
  "mcpServers": {
    "gold-social": {
      "command": "python",
      "args": ["src/mcp/mcp_social.py"],
      "cwd": "."
    },
    "gold-accounting": {
      "command": "python",
      "args": ["src/mcp/mcp_accounting.py"],
      "cwd": "."
    },
    "gold-communications": {
      "command": "python",
      "args": ["src/mcp/mcp_communications.py"],
      "cwd": "."
    }
  }
}
```

## 8. Initialize Gold Vault Extensions

```bash
python src/scripts/setup_vault.py --vault-path ./vault --verbose
# This creates any missing Gold directories (/Logs subcategories, etc.)
```

## 9. Run Tests

```bash
# Unit tests (no external services needed — all mocked)
pytest tests/unit/ -v

# Integration tests (requires Odoo Docker running)
pytest tests/integration/test_odoo_integration.py -v

# Full test suite
pytest tests/ -v
```

## 10. Demo: Full Gold Tier Pipeline

### Step 1: Verify Odoo Connection
```bash
# Use the accounting MCP health check
# Via Claude Code: invoke gold-accounting.health_check
```

### Step 2: Create a Test Invoice
```bash
# Via Claude Code: invoke gold-accounting.create_invoice
# Input: partner_name="Test Corp", invoice_date="2026-02-12", due_date="2026-03-12", lines=[{description: "Consulting", quantity: 10, unit_price: 150}]
# Expected: Invoice created in Odoo with ID
```

### Step 3: Record a Payment
```bash
# Via Claude Code: invoke gold-accounting.record_payment
# Input: invoice_id=<from step 2>, amount=1500, payment_date="2026-02-12"
# Expected: Payment recorded, invoice marked as paid
```

### Step 4: Generate Social Post (Multi-Platform)
```bash
# Via Claude Code: /generate-social-post
# Creates drafts in /Pending_Approval for each configured platform
# Approve in Obsidian → /check-approvals posts to approved platforms
```

### Step 5: Run Ralph Wiggum Loop
```bash
# Create a test Plan.md with 3 steps (1 simple, 1 action-required, 1 simple)
# Via Claude Code: /ralph-wiggum vault/Needs_Action/plan-test.md
# Watch: simple steps auto-complete, action step creates approval draft, loop pauses
# Approve the draft → re-run: loop completes remaining steps
```

### Step 6: Generate CEO Briefing
```bash
# Via Claude Code: /generate-briefing
# Or wait for Monday morning scheduler trigger
# Check: vault/Briefing.md has all 5 sections populated
```

### Step 7: Check Audit Logs
```bash
# Via Claude Code: /audit-report --date today
# Check: vault/Logs/ has entries for all actions performed
```

### Step 8: Test Error Recovery
```bash
# Stop Odoo: docker compose -f docker-compose.gold.yml stop odoo
# Run scheduler: python src/scheduling/scheduler.py --once
# Expected: Odoo operations fail gracefully, other operations succeed
# Check: .service_health.json shows odoo as degraded/unavailable
# Restart: docker compose -f docker-compose.gold.yml start odoo
```

## 11. Scheduler Setup (Automated Runs)

### Windows Task Scheduler
```cmd
schtasks /create /tn "GoldPipeline" /tr "python \"E:\it practice\aiemployee\src\scheduling\scheduler.py\" --config \"E:\it practice\aiemployee\src\scheduling\scheduler_config.json\"" /sc minute /mo 5
```

### Linux/macOS Cron
```bash
*/5 * * * * cd "/path/to/aiemployee" && python src/scheduling/scheduler.py --config src/scheduling/scheduler_config.json
```

### Monday Briefing (Weekly)
The scheduler automatically checks if today is Monday and triggers the briefing component. No separate cron job needed — it's built into the scheduler's weekly check.

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Odoo won't start | Check Docker Desktop is running. Run `docker compose -f docker-compose.gold.yml logs odoo` |
| "Connection refused" on Odoo | Wait 30s after `docker compose up`. Odoo takes time to initialize. |
| Meta token expired | Regenerate in Graph API Explorer. Long-lived tokens last 60 days. |
| X API 403 Forbidden | Check Free tier limits (50 posts/15min). Verify App has Write permissions. |
| Ralph Wiggum timeout | Check `/Logs/loop-<date>.md` for iteration details. Increase max if needed in config. |
| Briefing missing sections | Check `.service_health.json` for unavailable services. Briefing generates partial content. |
