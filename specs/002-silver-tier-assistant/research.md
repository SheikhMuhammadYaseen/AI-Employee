# Research: Silver Tier — Functional Assistant

**Branch**: `002-silver-tier-assistant` | **Date**: 2026-02-12
**Input**: Technical Context unknowns from plan.md
**Extends**: Bronze Tier research decisions (R1-R6 carried forward)

## R1: WhatsApp Web Automation with Playwright

**Decision**: Use Playwright (Python) to automate WhatsApp Web for message monitoring.

**Rationale**:
- Constitution Principle IV explicitly mandates "Playwright for WhatsApp" — this is not optional.
- WhatsApp has no official public API for personal accounts (Business API requires Meta verification and is paid).
- Playwright provides reliable cross-browser automation with built-in auto-wait and network interception.

**Alternatives considered**:
- `selenium` + ChromeDriver: More fragile, requires separate driver management. Playwright handles browser binaries natively.
- `whatsapp-web.js` (Node.js): Would require Node.js in the watcher layer, breaking single-language consistency.
- Baileys (unofficial WhatsApp Web API): Reverse-engineered protocol; unstable, ToS violation risk.

**Key findings**:
- WhatsApp Web requires QR code scan on first use. Playwright can persist browser context (cookies/session) to avoid re-scan on subsequent runs.
- Session persistence: Store browser state in a local directory (e.g., `~/.whatsapp_session/`). This directory MUST be gitignored and never synced.
- Message detection: Monitor the DOM for new message elements. Use CSS selectors to extract sender, timestamp, and message text.
- Urgent keyword detection: Match message text against configurable keywords (`urgent`, `asap`, `deadline`, `emergency`) and priority contacts from Company Handbook.
- Reconnection: If WhatsApp Web disconnects, Playwright can detect the "Phone not connected" banner and attempt page reload (3 retries before graceful exit).
- Install: `pip install playwright && playwright install chromium` (installs Chromium browser binary ~130MB).
- Rate: Poll DOM every 5-10 seconds within a session; no API rate limits since it's browser automation.

## R2: Mastodon API Integration

**Decision**: Use `Mastodon.py` library for posting to Mastodon and reading notifications.

**Rationale**:
- Constitution mandates Mastodon as the free alternative to LinkedIn/X (Principle IV: Free Focus).
- `Mastodon.py` is the established Python library for Mastodon API, well-maintained, and handles OAuth2, pagination, and rate limits.

**Alternatives considered**:
- Raw HTTP requests: More code to maintain, no automatic rate limit handling.
- `atproto` (Bluesky): Different protocol (AT Protocol), not Mastodon-compatible.
- LinkedIn API: Paid tier required for posting; violates Free Focus mandate.

**Key findings**:
- Setup: User creates an "Application" on their Mastodon instance → gets `client_id`, `client_secret`, `access_token`.
- Posting: `mastodon.status_post(content, visibility='public')` returns the post URL.
- Rate limits: Mastodon instances typically allow 300 requests per 5 minutes. One post per scheduled cycle is well within limits.
- Error handling: `Mastodon.py` raises `MastodonAPIError` for rate limits, auth failures, and server errors.
- Content: Posts should be <500 characters (Mastodon default limit). The `/generate-social-post` skill generates content within this limit.
- Install: `pip install Mastodon.py`.

## R3: MCP Server Architecture (Python)

**Decision**: Implement the MCP server in Python using the official `mcp` SDK (PyPI package `mcp`).

**Rationale**:
- Constitution allows "Node.js or Python" for MCP servers (Principle IV).
- Python keeps the entire Silver stack in one language, reducing setup complexity.
- The `mcp` Python SDK provides `@server.tool()` decorator for registering tools, automatic JSON-RPC handling, and stdio/SSE transport.

**Alternatives considered**:
- Node.js MCP SDK (`@modelcontextprotocol/sdk`): Would introduce a second language and runtime. Viable but adds complexity.
- Custom JSON-RPC server: Reinvents the wheel; MCP SDK handles protocol compliance.

**Key findings**:
- MCP SDK pattern: Define a server with `Server("silver-mcp")`, register tools with decorators, run via `server.run()`.
- Transport: Use stdio transport for Claude Code integration (Claude Code connects to MCP servers via stdio pipe).
- Tool registration: Each tool in `src/mcp/tools/` is imported and registered in `server.py`.
- Tool contract: Each tool function receives typed arguments and returns a result string/dict.
- Claude Code config: Add MCP server to `.claude/settings.json` or project MCP config so Claude Code can discover and invoke tools.
- Install: `pip install mcp`.

## R4: Gmail SMTP for Email Sending

**Decision**: Use Python's built-in `smtplib` with Gmail SMTP for sending approved emails.

**Rationale**:
- No additional library needed — `smtplib` is in Python's standard library.
- Gmail SMTP is well-documented and reliable for personal use.
- Separate from Gmail API read-only scope used by the watcher (different auth mechanism).

**Alternatives considered**:
- Gmail API with `gmail.send` scope: More complex OAuth2 scope management; requires modifying existing watcher auth flow.
- SendGrid/Mailgun: External services; violates local-first and free-focus mandates.

**Key findings**:
- SMTP server: `smtp.gmail.com`, port 587 (TLS).
- Authentication: Gmail App Password (generated in Google Account → Security → App passwords). Regular password won't work with 2FA enabled.
- App Password stored in `.env` as `GMAIL_APP_PASSWORD`, NEVER hardcoded.
- Send flow: Connect → STARTTLS → Login → Send MIME message → Quit.
- Rate limits: Gmail allows 500 emails/day for personal accounts. Silver's approval workflow ensures low volume.

## R5: Item Classification Strategy

**Decision**: Use keyword-based heuristic classification in Python, enhanced by Claude Code reasoning via the `/process-inbox` skill.

**Rationale**:
- Simple keyword matching handles the majority of cases (spec SC-002: 90%+ accuracy target).
- Claude Code's reasoning layer adds context-awareness for edge cases.
- No ML model needed — avoids complexity and dependency bloat.

**Alternatives considered**:
- LLM-only classification: Every item sent to Claude API — expensive, slow, unnecessary for clear cases.
- Rule engine (e.g., Drools): Enterprise overkill for a personal assistant.

**Key findings**:
- **Simple indicators**: Single action verb, informational content, newsletters, notifications.
- **Complex indicators**: Multiple steps mentioned, "prepare", "gather", "review and send", numbered lists.
- **Action-required indicators**: "reply", "send", "post", "forward", "schedule meeting", "respond".
- `classifier.py` exports a `classify(item_frontmatter, item_body) -> str` function returning `"simple"`, `"complex"`, or `"action_required"`.
- Company Handbook rules can override classification (e.g., "all emails from boss@company.com are action-required").

## R6: Approval File Format

**Decision**: Use YAML frontmatter + Markdown body with Obsidian-compatible checkboxes for approval drafts.

**Rationale**:
- Consistent with Bronze vault item format (YAML frontmatter + body).
- Obsidian renders checkboxes natively — user clicks to approve/reject without leaving the note app.
- Parseable by Python (`python-frontmatter` + regex for checkbox state).

**Key findings**:
- Checkbox pattern: `- [ ] Approved` (unchecked) → `- [x] Approved` (checked by user).
- Rejection: `- [x] Rejected` checkbox, OR user deletes the file.
- Parsing: Read file, check if `- [x] Approved` or `- [x] Rejected` appears in body.
- Stale detection: Compare file creation date against current time. If >24 hours without action, flag in Dashboard.
- File naming: `<action-type>-<timestamp>-<slug>.md` (e.g., `email-send-20260212T160000-reply-to-boss.md`).

## R7: OS-Native Scheduling

**Decision**: Use a Python wrapper script invoked by Windows Task Scheduler or cron, reading configuration from a JSON file.

**Rationale**:
- Constitution mandates "cron or Task Scheduler" for scheduling (Principle IV).
- A Python wrapper provides cross-platform entry point — same script works whether invoked by cron or Task Scheduler.
- JSON config allows interval changes without modifying the script or OS scheduler.

**Alternatives considered**:
- `schedule` Python library: Would require a long-running Python process (daemon). OS schedulers are more robust for periodic tasks.
- `APScheduler`: External dependency; overkill for simple periodic invocation.
- Pure cron/Task Scheduler (no wrapper): Would require OS-specific commands for each component. Python wrapper provides uniform interface.

**Key findings**:
- Windows: `schtasks /create /tn "SilverPipeline" /tr "python scheduler.py" /sc minute /mo 5`
- Linux/macOS: `*/5 * * * * cd /path/to/project && python src/scheduling/scheduler.py`
- Config file (`scheduler_config.json`): `{"interval_minutes": 5, "components": {"gmail_watcher": true, "whatsapp_watcher": true, "reasoning_loop": true, "approval_checker": true}}`
- Lock file: The scheduler itself uses a lock file to prevent overlapping runs.
- Logging: Each run appends to `/Logs/scheduler-<date>.md`.

## R8: Browser Session Persistence for WhatsApp

**Decision**: Persist Playwright browser context (cookies, local storage) in a dedicated local directory.

**Rationale**:
- WhatsApp Web requires QR code scan once. Without session persistence, user would need to re-scan every time the watcher starts.
- Playwright's `browser.new_context(storage_state=path)` and `context.storage_state(path=path)` enable session save/restore.

**Key findings**:
- Storage directory: `~/.whatsapp_session/` (user home, outside vault).
- On first run: Browser opens with WhatsApp Web, user scans QR. Session saved.
- On subsequent runs: Browser loads saved session. If session expired, detect QR code page and prompt user.
- Session expiry: WhatsApp Web sessions last ~14 days without the phone being connected. Watcher detects expiry and logs clear re-authentication instruction.
- This directory MUST be in `.gitignore` and never synced (constitution: secrets never synced).
