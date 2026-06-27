# Research: Gold Tier — Autonomous Employee

**Branch**: `003-gold-tier-autonomous` | **Date**: 2026-02-12
**Input**: Technical Context unknowns from plan.md + Gold spec
**Extends**: Silver Tier research decisions (R1-R8 carried forward)

## R1: Odoo Community Self-Hosted via Docker

**Decision**: Run Odoo Community Edition 19.0 locally via Docker Compose with PostgreSQL backend. Interact via JSON-RPC (XML-RPC deprecated in Odoo 17+).

**Rationale**:
- Constitution Principle IV mandates "Odoo Community (Gold+ only)" and local-first deployment.
- Docker provides reproducible, isolated environments — no system-level PostgreSQL install needed.
- Odoo 19+ uses JSON-RPC as the primary external API (the `/jsonrpc` endpoint replaces legacy XML-RPC).

**Alternatives considered**:
- Native install (apt/pip): Requires PostgreSQL install, system Python conflicts, harder to reset test data.
- Odoo.sh (cloud): Violates local-first mandate.
- Odoo REST API module: Third-party addon, not part of Community Edition by default.

**Key findings**:
- Docker image: `odoo:19.0` from Docker Hub (official). Paired with `postgres:16` container.
- Compose setup: Two services — `odoo` (port 8069) and `db` (PostgreSQL, port 5432).
- JSON-RPC endpoint: `http://localhost:8069/jsonrpc` (POST with JSON body).
- Authentication: Call `common.login(db, username, password)` → returns `uid`. Use `uid` + password for subsequent `object.execute_kw` calls.
- Key models for Gold:
  - `account.move` (invoices/bills — Odoo 14+ unified model)
  - `account.payment` (payments)
  - `account.move.line` (invoice line items)
  - `res.partner` (customers/vendors)
- Invoice creation: `execute_kw('account.move', 'create', [{...}])` with `move_type: 'out_invoice'`.
- Payment recording: `execute_kw('account.payment', 'create', [{...}])` then `action_post()` to confirm.
- Financial reports: Query `account.move` with domain filters `[('move_type','=','out_invoice'),('date','>=',start),('date','<=',end)]` and aggregate amounts.
- Test data: Odoo ships with demo data (`-e demo` flag or `--without-demo=False`). Includes sample partners, products, and chart of accounts.
- Reset: `docker compose down -v && docker compose up -d` wipes and recreates all data.
- Install: `docker compose up -d` (requires Docker Desktop on Windows).

## R2: Meta Graph API for Facebook/Instagram Posting

**Decision**: Use Meta Graph API v19.0 for Facebook Page posting and Instagram business account posting.

**Rationale**:
- Gold spec FR-006 requires Facebook/Instagram posting via "Meta business page interface."
- Graph API is the only official way to post to Facebook Pages and Instagram business accounts.
- Free for basic posting (no ad spend required for organic posts).

**Alternatives considered**:
- Buffer/Hootsuite API: Third-party; adds dependency and may require paid plans for API access.
- Direct Facebook sharing URL: Only opens browser dialog; cannot programmatically post.
- Selenium automation: Fragile, ToS violation risk, login detection.

**Key findings**:
- Setup: Create a Meta App at developers.facebook.com → get App ID + App Secret.
- Page Access Token: User grants `pages_manage_posts` permission → exchange for long-lived Page Access Token (60-day expiry, can be refreshed).
- Instagram: Requires `instagram_basic` + `instagram_content_publish` permissions. Instagram must be linked to a Facebook Page.
- Facebook post: `POST /{page-id}/feed?message={text}&access_token={token}` → returns post ID.
- Instagram post: Two-step process — (1) Create media container: `POST /{ig-user-id}/media?caption={text}` (2) Publish: `POST /{ig-user-id}/media_publish?creation_id={id}`.
- Rate limits: 200 calls per user per hour (posting is 1 call per post, well within limits).
- Engagement metrics: `GET /{post-id}/insights` for reach, impressions, engagement. Requires `read_insights` permission.
- Python library: Use `requests` (stdlib-adjacent, already available). No dedicated Meta SDK needed — raw HTTP is simpler for a few endpoints.
- Token storage: Page Access Token in `.env` as `META_PAGE_ACCESS_TOKEN`. NEVER hardcoded.
- Test mode: Meta provides Test Pages/Apps that don't publish publicly.

## R3: X (Twitter) API v2 for Posting

**Decision**: Use X API v2 Free tier for posting tweets. If Free tier access is unavailable or restricted, fall back to Mastodon cross-posting.

**Rationale**:
- Gold spec FR-007 requires X posting. API v2 is the current standard.
- Free tier allows 1,500 tweets/month write + limited read (sufficient for Gold scope).
- Constitution Free Focus: Use free tier; fall back to Mastodon if X API costs arise.

**Alternatives considered**:
- X API v1.1: Deprecated for new apps, being phased out.
- Mastodon-only: Would satisfy the social posting requirement but not the spec's explicit X mention.
- Nitter/scraping: Unofficial, unreliable, ToS violation.

**Key findings**:
- Setup: Create a Developer Project at developer.x.com → get API Key + Secret + Bearer Token + OAuth 1.0a credentials.
- Free tier: Write access (post tweets), limited read (1,500 tweets/month).
- Post tweet: `POST /2/tweets` with Bearer Token or OAuth 1.0a. Body: `{"text": "content"}`.
- Character limit: 280 characters (enforced client-side before API call per spec FR-007).
- Rate limits: 50 requests per 15 minutes for posting (Free tier). One post per approval cycle is well within limits.
- Engagement metrics: `GET /2/tweets/{id}?tweet.fields=public_metrics` for retweet_count, like_count, reply_count. Requires Basic tier ($100/month) — **not available on Free tier**.
- Fallback strategy: If X API access is denied or costs, post to Mastodon instead and log "X unavailable, posted to Mastodon as fallback."
- Python library: Use `requests` with OAuth 1.0a signing (via `requests-oauthlib`). Alternatively, `tweepy` library handles OAuth automatically.
- Decision: Use `tweepy` (well-maintained, handles OAuth complexity). Install: `pip install tweepy`.
- Token storage: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET` in `.env`.

## R4: Multiple MCP Servers Architecture

**Decision**: Run three separate MCP server processes: `mcp_social.py` (Mastodon + Facebook/Instagram + X), `mcp_accounting.py` (Odoo), and extend existing `server.py` (email — renamed to `mcp_communications.py`).

**Rationale**:
- Gold spec FR-010/FR-011 requires "multiple MCP servers: one for social media, one for accounting, one for communications."
- Separate processes provide fault isolation (spec US5: "if the accounting server is down, social posting and email still work").
- Each server can be started/stopped independently.

**Alternatives considered**:
- Single server with tool namespacing: Simpler but violates fault isolation requirement (one crash takes down everything).
- Microservices with HTTP: Over-engineered for local-only use; MCP stdio is simpler.
- Dynamic tool loading in one server: Still single process; doesn't satisfy independent restart requirement.

**Key findings**:
- MCP server pattern: Each server is a standalone Python script using `mcp` SDK with `@server.tool()` decorators.
- Claude Code config: Register all three servers in `.claude/settings.json` MCP section. Claude Code connects to each via stdio.
- Tool routing: Claude Code handles routing automatically — tools are namespaced by server. Agent invokes `social.mastodon_post` or `accounting.create_invoice`.
- Server naming:
  - `mcp_social.py`: Tools — `mastodon_post`, `facebook_post`, `instagram_post`, `social_engagement_summary`
  - `mcp_accounting.py`: Tools — `create_invoice`, `record_payment`, `get_financial_summary`, `list_invoices`, `list_payments`
  - `mcp_communications.py`: Tools — `email_send` (migrated from Silver `server.py`)
- Health check: Each MCP server exposes a `health_check` tool that returns `{"status": "ok", "server": "<name>", "timestamp": "..."}`.
- Startup: `python src/mcp/mcp_social.py`, `python src/mcp/mcp_accounting.py`, `python src/mcp/mcp_communications.py`.
- Graceful shutdown: Each server catches SIGTERM/SIGINT and logs shutdown to `/Logs`.

## R5: Ralph Wiggum Loop Implementation

**Decision**: Implement as a Claude Code skill (`ralph-wiggum.md`) that reads a Plan.md, iterates through steps, creates approval drafts, and re-checks until complete or limits reached. Uses a "TASK_COMPLETE" sentinel or max iterations.

**Rationale**:
- Constitution Principle II: "Agents use Ralph Wiggum Stop Hook to iterate until tasks are complete, but only within spec boundaries."
- Spec FR-012/FR-013: Autonomous iteration with 10 iteration / 30 minute limits.
- Implementation as a Claude Code skill keeps the loop within Claude's reasoning context (not a standalone Python daemon).

**Alternatives considered**:
- Python daemon with API calls to Claude: Adds Claude API dependency and cost; loses Claude Code's native tool access.
- Recursive bash script: No access to Claude reasoning; can't handle complex decisions.
- Webhook-based triggers: Requires server infrastructure; violates local-first simplicity.

**Key findings**:
- Loop structure:
  1. Read Plan.md → parse checkbox steps
  2. For each unchecked step:
     a. If simple action (review, write, gather): Execute directly and check off
     b. If external action (send, post, invoice): Create approval draft in `/Pending_Approval`, mark step as "awaiting approval"
     c. If approval-blocked: Skip to next step
  3. After all steps processed: Check if any approvals were granted since last iteration
  4. If all steps done → write "TASK_COMPLETE" to Plan.md, move to `/Done`
  5. If not done and iterations < 10 and time < 30 min → re-iterate
  6. If limits reached → write "LOOP_TIMEOUT" and summary to Plan.md, log warning
- Iteration tracking: YAML frontmatter in Plan.md gets `loop_iteration: N`, `loop_started: <timestamp>`.
- Nesting prevention: If a step generates a sub-plan, the loop processes it inline (depth 1) but refuses to nest further (max depth 2 per spec edge case).
- Lock file: `plan-<id>.lock` prevents concurrent loops on the same plan.
- Logging: Each iteration writes to `/Logs/gold_audit.md` with action, result, timestamp.

## R6: Weekly CEO Briefing Generation

**Decision**: Implement as a scheduler component (`briefing_generator.py`) triggered by the scheduler on Monday mornings. Aggregates data from Odoo (via MCP), vault logs, and social summaries into a `Briefing.md`.

**Rationale**:
- Spec FR-004/FR-005: Automatic Monday briefing with 5 sections and trend indicators.
- Scheduler already runs periodically (Silver); add a "weekly" component that only fires on Mondays.

**Key findings**:
- Scheduler check: `datetime.today().weekday() == 0` (Monday = 0 in Python).
- Time window: Run between 06:00-09:00 local time (configurable in scheduler_config.json).
- Data sources:
  - **Financial**: Call `mcp_accounting.get_financial_summary(start=last_monday, end=this_sunday)` for current week and previous week.
  - **Operational**: Scan `/Done` files from past week (count by type, status). Scan `/Logs` for errors.
  - **Social**: Call `mcp_social.social_engagement_summary(start=last_monday, end=this_sunday)`.
- Trend indicators: Compare current vs. previous week. Revenue up > 5% → "up", down > 5% → "down", else "stable". Same pattern for all metrics.
- Critical item flags: Overdue invoices > 7 days, error count > 10 in week, approval items pending > 48 hours.
- Output: `vault/Briefing.md` (overwritten each week; previous briefings archived to `/Done/briefing-<date>.md`).
- Graceful degradation: If Odoo unavailable, Financial Summary shows "Data unavailable — Odoo connection failed." Other sections still populated.

## R7: Audit Logging Architecture

**Decision**: Use structured Markdown files in `/Logs` with YAML frontmatter, one file per day per category. Categories: `mcp`, `classification`, `approval`, `loop`, `scheduler`.

**Rationale**:
- Spec FR-014/FR-015: All actions logged with daily rotation.
- Extends Silver's simple log files with structured entries and categories.
- Markdown + YAML is consistent with all other vault artifacts.

**Key findings**:
- File naming: `/Logs/<category>-<YYYY-MM-DD>.md` (e.g., `mcp-2026-02-12.md`).
- Each log entry appended as a Markdown section:
  ```markdown
  ### [HH:MM:SS] action_name
  - **Category**: mcp
  - **Tool**: create_invoice
  - **Server**: mcp_accounting
  - **Parameters**: {customer: "Test Corp", amount: 1500} (sanitized)
  - **Result**: success
  - **Duration**: 1.2s
  - **Linked**: invoice-20260212T100000.md
  ```
- Sanitization: Passwords, tokens, and full email bodies are redacted. Only action names, targets, and result status logged.
- Daily rotation: Logger checks if file exists for today; creates new if not. Previous days' files remain.
- Weekly summary: `briefing_generator.py` scans all log files from past week, counts by category/result, identifies error patterns.
- Python module: `src/logging/audit_logger.py` with `log_action(category, action, details)` function used by all components.

## R8: Error Recovery with Exponential Backoff

**Decision**: Implement a retry decorator/utility with exponential backoff (1s, 2s, 4s) for all external service calls. Graceful degradation via service health tracking.

**Rationale**:
- Spec FR-016/FR-017: 3 retries with increasing delays; continue operating when services unavailable.
- Exponential backoff prevents thundering herd on recovering services.

**Key findings**:
- Retry pattern: `@retry(max_attempts=3, backoff_base=1, backoff_factor=2)` decorator.
- Delays: 1s → 2s → 4s (total max wait: 7 seconds before giving up).
- Exception handling: Catch `ConnectionError`, `TimeoutError`, `requests.HTTPError(5xx)`. Don't retry on 4xx (client error).
- Service health: `src/health/service_health.py` maintains a JSON file `vault/.service_health.json`:
  ```json
  {
    "odoo": {"status": "operational", "last_ok": "2026-02-12T10:00:00", "last_error": null, "error_count": 0},
    "mastodon": {"status": "operational", "last_ok": "2026-02-12T10:00:00", "last_error": null, "error_count": 0},
    "facebook": {"status": "unavailable", "last_ok": "2026-02-11T15:00:00", "last_error": "2026-02-12T10:05:00", "error_count": 3}
  }
  ```
- Status transitions:
  - `operational` → 3 consecutive failures → `degraded` → 3 more failures → `unavailable`
  - Any success → back to `operational`
- Dashboard update: Scheduler reads health file and updates `Dashboard.md` with service status section.
- Alert: If any service `unavailable` for > 1 hour, flag in Dashboard with warning.
- Python: No external library needed. Use `time.sleep()` for backoff, `functools.wraps` for decorator.

## R9: Tweepy vs. Requests-OAuthlib for X API

**Decision**: Use `tweepy` library for X (Twitter) API v2 integration.

**Rationale**:
- `tweepy` handles OAuth 1.0a User Context authentication and v2 API endpoints natively.
- Simpler than manually signing requests with `requests-oauthlib`.
- Well-maintained, widely used, good documentation.

**Key findings**:
- Install: `pip install tweepy`.
- Client: `tweepy.Client(consumer_key=..., consumer_secret=..., access_token=..., access_token_secret=...)`.
- Post: `client.create_tweet(text="content")` → returns tweet data with ID.
- Engagement (Basic tier only): `client.get_tweet(id, tweet_fields=["public_metrics"])`.
- Free tier limitation: No engagement metrics read. Log "engagement metrics unavailable on Free tier" in weekly summary.
- Error handling: `tweepy.errors.TweepyException` base class; `tweepy.errors.Forbidden` for rate limits.

## R10: Docker Compose for Odoo Local Setup

**Decision**: Provide a `docker-compose.gold.yml` in the project root for one-command Odoo + PostgreSQL setup.

**Rationale**:
- Simplifies Odoo setup for development and testing.
- Constitution mandates local-only; Docker is local.
- Reproducible environment with demo data.

**Key findings**:
- Compose file:
  ```yaml
  services:
    db:
      image: postgres:16
      environment:
        POSTGRES_DB: odoo_gold
        POSTGRES_USER: odoo
        POSTGRES_PASSWORD: odoo_test
      volumes:
        - odoo-db:/var/lib/postgresql/data
    odoo:
      image: odoo:19.0
      depends_on: [db]
      ports: ["8069:8069"]
      environment:
        HOST: db
        USER: odoo
        PASSWORD: odoo_test
      command: -- --database=odoo_gold --init=account --without-demo=False
  volumes:
    odoo-db:
  ```
- First run: `docker compose -f docker-compose.gold.yml up -d` → initializes Odoo with accounting module and demo data.
- Reset: `docker compose -f docker-compose.gold.yml down -v && docker compose -f docker-compose.gold.yml up -d`.
- Default admin: `admin` / `admin` (Odoo demo default).
- Accounting module: `--init=account` installs Chart of Accounts, enables invoice/payment features.
