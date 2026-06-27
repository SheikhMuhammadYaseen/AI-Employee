# Implementation Plan: Gold Tier — Autonomous Employee

**Branch**: `003-gold-tier-autonomous` | **Date**: 2026-02-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/003-gold-tier-autonomous/spec.md`
**Extends**: Silver Tier (`specs/002-silver-tier-assistant/`)

## Summary

Extend the Silver Tier into a fully autonomous AI employee with Odoo Community accounting integration (self-hosted via Docker, JSON-RPC), multi-platform social posting (Facebook/Instagram via Meta Graph API, X via Tweepy, Mastodon carried forward), three independent MCP servers (social, accounting, communications), a Ralph Wiggum autonomous task loop, weekly Monday CEO Briefing generation, comprehensive audit logging with daily rotation, error recovery with exponential backoff, service health tracking, and architecture documentation. All components remain local-only with mandatory human approval for external actions.

## Technical Context

**Language/Version**: Python 3.11+ (all components); Markdown (skills/commands)
**Primary Dependencies**:
- Silver (carried forward): `google-api-python-client`, `google-auth-oauthlib`, `python-frontmatter`, `pyyaml`, `playwright`, `Mastodon.py`, `mcp`
- New: `tweepy` (X/Twitter API v2), `requests` (Meta Graph API HTTP calls), `docker` (Odoo local setup — runtime dependency, not Python package)
**Storage**: Local filesystem (Markdown + YAML frontmatter, JSON state/config); Odoo PostgreSQL (via Docker, for accounting data only)
**Testing**: `pytest` for unit tests; Odoo test database for accounting; Meta/X test apps for social; manual acceptance per spec scenarios
**Target Platform**: Windows 10+ / macOS / Linux (local desktop, cross-platform)
**Project Type**: Single project (extending Silver structure)
**Performance Goals**: MCP tool calls complete in <5 seconds (Odoo JSON-RPC <2s); Ralph Wiggum loop iteration <60 seconds; CEO Briefing generation <30 seconds; 50+ vault items per scheduler cycle (SC-010)
**Constraints**: Local-only; no cloud; human approval mandatory for all external actions; free tools only; test Odoo data only (no real banking); Docker required for Odoo
**Scale/Scope**: Single user, one Odoo instance, one Facebook Page, one X account, one Mastodon account, one vault, ~200 items/day maximum

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Spec-Driven Development | Plan derives from approved Gold spec only; extends Silver/Bronze artifacts; no unapproved features | PASS |
| II. Agent Behavior Rules | All code generated via Claude Code; human-in-the-loop for all external actions (FR-020); Ralph Wiggum loop respects approval gates; comprehensive audit logging (FR-014) | PASS |
| III. Tier Governance | Gold-scoped only: Odoo Community, multi-social, CEO briefing, Ralph Wiggum loop. No Platinum features (no cloud, no Docker orchestration beyond local Odoo, no multi-tenancy) | PASS |
| IV. Technology Constraints | Python + MCP (constitution Hands/Actions); Odoo Community (constitution Gold+ ERP); Mastodon (free focus); Docker local-only; Tweepy for X (free tier) | PASS |
| V. Quality Principles | Clean Architecture (Perception->Reasoning->Action extended with Audit layer); modular MCP servers; error recovery; documentation required; daily log rotation | PASS |

**Result**: All gates PASS. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/003-gold-tier-autonomous/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: setup and usage guide
├── contracts/
│   ├── mcp-accounting.md    # Phase 1: Odoo MCP tool contracts
│   ├── mcp-social.md        # Phase 1: Social MCP tool contracts
│   └── mcp-communications.md # Phase 1: Email MCP tool contracts
└── tasks.md             # Phase 2: created by /sp.tasks (not yet)
```

### Source Code (repository root)

```text
src/
├── scripts/
│   └── setup_vault.py              # Bronze (unchanged)
├── watchers/
│   ├── base_watcher.py             # Silver (unchanged)
│   ├── gmail_watcher.py            # Silver (unchanged)
│   └── whatsapp_watcher.py         # Silver (unchanged)
├── mcp/
│   ├── mcp_social.py               # NEW: US3/US5 Social MCP server (Mastodon + FB/IG + X)
│   ├── mcp_accounting.py           # NEW: US1/US5 Odoo accounting MCP server
│   ├── mcp_communications.py       # RENAMED: Silver server.py → communications MCP
│   ├── router.py                   # NEW: US5 MCP server registry and health checker
│   ├── tools/
│   │   ├── email_send.py           # Silver (unchanged)
│   │   ├── mastodon_post.py        # Silver (unchanged)
│   │   ├── facebook_post.py        # NEW: US3 Facebook Graph API posting
│   │   ├── instagram_post.py       # NEW: US3 Instagram Graph API posting
│   │   ├── x_post.py               # NEW: US3 X/Twitter posting via Tweepy
│   │   ├── social_summary.py       # NEW: US3 Social engagement summary
│   │   ├── odoo_invoice.py         # NEW: US1 Odoo invoice create/list
│   │   ├── odoo_payment.py         # NEW: US1 Odoo payment record/list
│   │   ├── odoo_reports.py         # NEW: US1 Odoo financial summaries
│   │   └── odoo_client.py          # NEW: US1 Shared Odoo JSON-RPC client
│   └── config.py                   # Silver (extended with new server configs)
├── reasoning/
│   ├── classifier.py               # Silver (unchanged)
│   ├── planner.py                  # Silver (unchanged)
│   └── ralph_wiggum.py             # NEW: US4 Autonomous loop engine
├── approval/
│   └── checker.py                  # Silver (extended for multi-platform routing)
├── scheduling/
│   ├── scheduler.py                # Silver (extended with weekly briefing trigger)
│   └── scheduler_config.json       # Silver (extended with Gold components)
├── briefing/
│   └── briefing_generator.py       # NEW: US2 Weekly CEO briefing generation
├── logging/
│   └── audit_logger.py             # NEW: US6 Structured audit logging
├── health/
│   └── service_health.py           # NEW: US7 Service health tracking
├── recovery/
│   └── retry.py                    # NEW: US7 Retry decorator with exponential backoff
└── templates/
    ├── dashboard_template.md       # Bronze (unchanged)
    ├── vault_item_template.md      # Bronze (unchanged)
    ├── handbook_template.md        # Bronze (unchanged)
    ├── plan_item_template.md       # Silver (unchanged)
    ├── approval_draft_template.md  # Silver (unchanged)
    └── briefing_template.md        # NEW: US2 CEO Briefing template

.claude/
└── commands/
    ├── vault-read.md               # Bronze (unchanged)
    ├── vault-write.md              # Bronze (unchanged)
    ├── process-inbox.md            # Silver (unchanged)
    ├── plan-task.md                # Silver (unchanged)
    ├── check-approvals.md          # Silver (extended for multi-platform)
    ├── generate-social-post.md     # Silver (extended for multi-platform)
    ├── run-pipeline.md             # Silver (extended with Gold components)
    ├── ralph-wiggum.md             # NEW: US4 Autonomous task loop skill
    ├── generate-briefing.md        # NEW: US2 CEO briefing skill
    ├── audit-report.md             # NEW: US6 Audit log query skill
    └── odoo-accounting.md          # NEW: US1 Odoo accounting skill

vault/                              # Runtime artifact (gitignored)
├── Dashboard.md                    # Extended with service health
├── Briefing.md                     # NEW: Weekly CEO briefing (overwritten)
├── Architecture.md                 # NEW: US8 System architecture doc
├── Lessons_Learned.md              # NEW: US8 Operational insights
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
├── Pending_Approval/
├── Done/
│   └── briefing-*.md               # Archived weekly briefings
├── Logs/
│   ├── mcp-YYYY-MM-DD.md           # NEW: Daily MCP invocation logs
│   ├── classification-YYYY-MM-DD.md # NEW: Daily classification logs
│   ├── approval-YYYY-MM-DD.md      # NEW: Daily approval transition logs
│   ├── loop-YYYY-MM-DD.md          # NEW: Daily Ralph Wiggum logs
│   └── scheduler-*.md              # Silver (unchanged format)
└── .service_health.json            # NEW: Service health state file

docker-compose.gold.yml             # NEW: Odoo + PostgreSQL Docker setup

tests/
├── unit/
│   ├── test_setup_vault.py         # Bronze (unchanged)
│   ├── test_gmail_watcher.py       # Bronze (unchanged)
│   ├── test_base_watcher.py        # Silver (unchanged)
│   ├── test_whatsapp_watcher.py    # Silver (unchanged)
│   ├── test_classifier.py          # Silver (unchanged)
│   ├── test_planner.py             # Silver (unchanged)
│   ├── test_approval_checker.py    # Silver (unchanged)
│   ├── test_mcp_tools.py           # Silver (unchanged)
│   ├── test_odoo_client.py         # NEW: Odoo JSON-RPC client tests
│   ├── test_odoo_tools.py          # NEW: Odoo MCP tool tests
│   ├── test_social_tools.py        # NEW: FB/IG/X posting tool tests
│   ├── test_ralph_wiggum.py        # NEW: Ralph Wiggum loop tests
│   ├── test_briefing_generator.py  # NEW: CEO briefing generation tests
│   ├── test_audit_logger.py        # NEW: Audit logging tests
│   ├── test_retry.py               # NEW: Retry/backoff tests
│   └── test_service_health.py      # NEW: Service health tracking tests
└── integration/
    ├── test_end_to_end.py          # Bronze (unchanged)
    ├── test_watcher_pipeline.py    # Silver (unchanged)
    ├── test_approval_flow.py       # Silver (unchanged)
    ├── test_odoo_integration.py    # NEW: Odoo Docker integration tests
    ├── test_ralph_wiggum_flow.py   # NEW: Full loop execution test
    └── test_briefing_flow.py       # NEW: Briefing generation test
```

**Structure Decision**: Extends Silver single-project layout. New directories: `src/briefing/` for CEO Briefing, `src/logging/` for structured audit logging, `src/health/` for service health tracking, `src/recovery/` for retry utilities. MCP layer expanded from single server to three domain-specific servers. Silver's `server.py` renamed to `mcp_communications.py`. Four new Claude Code skills added. `docker-compose.gold.yml` at project root for Odoo local setup.

## Architecture: Extended Perception -> Reasoning -> Action + Audit

```text
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────────────┐
│   PERCEPTION         │     │    REASONING          │     │     ACTION                │
│ (Senses)             │     │ (Brain)               │     │ (Hands)                   │
│                      │     │                       │     │                           │
│ gmail_watcher.py     │     │ Claude Code           │     │ MCP Social Server         │
│ whatsapp_watcher.py  │──>  │ /process-inbox        │──>  │  mastodon_post             │
│                      │     │ /plan-task             │     │  facebook_post             │
│ Both create .md in   │     │ /generate-social-post  │     │  instagram_post            │
│ /Needs_Action        │     │ /generate-briefing     │     │  x_post                   │
│                      │     │ /ralph-wiggum          │     │  social_summary            │
│                      │     │ /audit-report          │     │                           │
│                      │     │ /odoo-accounting       │     │ MCP Accounting Server     │
│                      │     │                       │     │  create_invoice            │
│                      │     │ Classifies items:     │     │  record_payment            │
│                      │     │ simple/complex/action  │     │  get_financial_summary     │
│                      │     │                       │     │  list_invoices             │
│                      │     │                       │     │  list_payments             │
│                      │     │                       │     │                           │
│                      │     │                       │     │ MCP Communications Server  │
│                      │     │                       │     │  email_send                │
└─────────────────────┘     └──────────────────────┘     └──────────────────────────┘
         │                           │                              │
         │                           │                              │
         ▼                           ▼                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│   AUDIT LAYER (Cross-Cutting)                                          │
│                                                                        │
│ audit_logger.py → /Logs/<category>-<date>.md                          │
│ service_health.py → .service_health.json → Dashboard.md               │
│ retry.py → Exponential backoff on all external calls                  │
└────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│   SAFETY GATE (Human-in-the-Loop)                                       │
│                                                                         │
│ /Pending_Approval → Human checks box in Obsidian → /check-approvals    │
│ ALL external actions (posts, emails, invoices) require approval (FR-020)│
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│   AUTONOMOUS LOOP (Ralph Wiggum)                                        │
│                                                                         │
│ /ralph-wiggum reads Plan.md → iterates steps → creates approval drafts │
│ Re-checks after approvals → completes or times out (10 iter / 30 min) │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│   SCHEDULING                                                            │
│                                                                         │
│ scheduler.py (OS-native: Task Scheduler / cron)                        │
│ Every 5 min: watchers → reasoning → approval checker                   │
│ Weekly Monday: CEO Briefing generation                                  │
│ Each run: service health check → log results                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Layer | Responsibility | Inputs | Outputs |
|-----------|-------|---------------|--------|---------|
| `mcp_social.py` | Action | Social MCP server (Mastodon + FB/IG + X) | Tool calls | Posts + logs |
| `mcp_accounting.py` | Action | Odoo accounting MCP server | Tool calls | Invoices/payments/reports |
| `mcp_communications.py` | Action | Email MCP server (migrated from Silver) | Tool calls | Sent emails + logs |
| `router.py` | Action | MCP server registry + health probing | Server configs | Health check results |
| `odoo_client.py` | Action | Odoo JSON-RPC client (auth, execute_kw) | Credentials, method, args | Odoo API responses |
| `odoo_invoice.py` | Action | Create/list invoices via JSON-RPC | Invoice data | Created invoice ID |
| `odoo_payment.py` | Action | Record/list payments via JSON-RPC | Payment data | Payment confirmation |
| `odoo_reports.py` | Action | Pull financial summaries from Odoo | Date range | Aggregated financial data |
| `facebook_post.py` | Action | Post to Facebook Page via Graph API | Content, token | Post ID + URL |
| `instagram_post.py` | Action | Post to Instagram via Graph API | Content, token | Post ID + URL |
| `x_post.py` | Action | Post to X via Tweepy | Content, credentials | Tweet ID + URL |
| `social_summary.py` | Action | Generate social engagement summary | Date range | Summary by platform |
| `ralph_wiggum.py` | Reasoning | Autonomous task loop engine | Plan.md path | Step completion/approval drafts |
| `briefing_generator.py` | Reasoning | Weekly CEO briefing aggregation | Odoo data + logs + social | Briefing.md |
| `audit_logger.py` | Audit | Structured log writer | Category, action, details | Log entries in /Logs |
| `service_health.py` | Audit | Service health tracking | Health check results | .service_health.json |
| `retry.py` | Recovery | Retry decorator with backoff | Function, max_attempts | Retried result or error |
| `/ralph-wiggum` | Skill | Orchestrate autonomous loop | Plan.md reference | Loop execution |
| `/generate-briefing` | Skill | Generate CEO briefing on demand | None (uses current data) | Briefing.md |
| `/audit-report` | Skill | Query and summarize audit logs | Date range, category | Formatted report |
| `/odoo-accounting` | Skill | Odoo operations via natural language | User instruction | Invoice/payment/report |

## Key Design Decisions

### D1: Odoo JSON-RPC via Dedicated Client Module

Create `odoo_client.py` as a shared Odoo JSON-RPC client. All Odoo tools (`odoo_invoice.py`, `odoo_payment.py`, `odoo_reports.py`) use this client. The client handles authentication (login → uid), session management, and JSON-RPC request formatting.

**Trade-off**: Custom JSON-RPC client vs. `odoorpc` library. Custom client avoids an external dependency and gives full control over error handling. The JSON-RPC calls are simple POST requests with known structure.

### D2: Three Separate MCP Server Processes

Split Silver's single MCP server into three domain-specific servers: social, accounting, communications. Each is a standalone Python process with its own `mcp.Server()` instance. Claude Code connects to all three via stdio transport configured in `.claude/settings.json`.

**Trade-off**: Three processes vs. one: more resource usage (~30MB each) but provides fault isolation (spec FR-010). If Odoo is down, social posting still works.

### D3: Ralph Wiggum as Python Module + Claude Code Skill

The loop engine lives in `src/reasoning/ralph_wiggum.py` (Python) for step parsing, iteration tracking, and limit enforcement. The Claude Code skill `/ralph-wiggum` orchestrates the loop by calling the Python module and using Claude's reasoning for step execution decisions.

**Trade-off**: Pure Python daemon vs. Claude-driven loop. Claude-driven provides natural language understanding for interpreting plan steps but costs more per iteration. Limit of 10 iterations (spec FR-013) keeps costs bounded.

### D4: Briefing as Scheduler Component with Graceful Degradation

`briefing_generator.py` is a scheduler component that only runs on Mondays. It calls each data source independently (Odoo, vault logs, social) and builds the briefing section by section. If any source fails, that section shows "Data unavailable" and other sections still populate.

**Trade-off**: Monolithic vs. section-by-section generation. Section-by-section allows partial briefings when services are degraded (spec US2 acceptance scenario 4).

### D5: Daily Log Rotation by Category

Audit logs use one file per day per category (5 categories: mcp, classification, approval, loop, scheduler). This prevents single-file bloat and enables efficient querying by date and category.

**Trade-off**: Individual files vs. single rolling log. Multiple files enable targeted querying (e.g., "show all MCP calls on Feb 12") without parsing one massive file.

### D6: Service Health as JSON State File

Service health tracking uses a lightweight JSON file (`.service_health.json`) updated by the retry module after each external call. The Dashboard skill reads this file to display service status. No database or monitoring daemon needed.

**Trade-off**: JSON file vs. in-memory tracking. JSON persists across process restarts and is readable by all components without shared state.

### D7: Silver MCP Server Migration

Rename Silver's `server.py` to `mcp_communications.py` and migrate `email_send` tool. Silver's `mastodon_post` tool moves to `mcp_social.py`. This is a file reorganization, not a rewrite — tool code in `src/mcp/tools/` remains unchanged.

### D8: Meta Graph API via Raw Requests

Use Python `requests` library for Facebook/Instagram Graph API calls rather than a dedicated SDK. The API surface is small (2-3 endpoints for posting) and raw HTTP keeps dependencies minimal.

### D9: Tweepy for X API

Use `tweepy` library for X/Twitter integration. Handles OAuth 1.0a complexity (signature generation, nonce, timestamp) that would be tedious with raw requests. Free tier limitation (no engagement metrics) is documented and logged.

### D10: Retry Decorator Pattern

A `@retry` decorator in `src/recovery/retry.py` wraps all external service calls. Uses exponential backoff (1s, 2s, 4s) and updates service health on each attempt. This avoids duplicating retry logic across 10+ tool functions.

## Security Considerations

- All Silver/Bronze security rules carried forward
- Odoo credentials (`ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`) in `.env` (gitignored), NEVER hardcoded
- Meta Page Access Token in `.env` as `META_PAGE_ACCESS_TOKEN` (gitignored)
- X API credentials (`X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET`) in `.env` (gitignored)
- Odoo test database only — no real financial data (spec FR-021)
- Audit logs sanitize sensitive parameters: tokens, passwords, full email bodies redacted (spec FR-014)
- MCP servers run on localhost only — no network exposure
- ALL external actions require explicit human approval (FR-020) — zero unapproved actions (SC-009)
- Docker containers use isolated network; Odoo port 8069 bound to localhost only
- Ralph Wiggum loop enforces iteration + time limits to prevent runaway execution (FR-013)
- Lock files per plan prevent concurrent loop execution on same plan

## Complexity Tracking

> No violations found. All design choices use the simplest viable approach for Gold Tier requirements.

| Aspect | Approach | Why Simplest |
|--------|----------|-------------|
| Odoo integration | Docker Compose + JSON-RPC | One command setup; standard Odoo API; no custom modules |
| Social posting (FB/IG) | Raw requests to Graph API | 2-3 endpoints; no SDK dependency needed |
| Social posting (X) | Tweepy library | OAuth 1.0a is complex; library handles it; one pip install |
| Multiple MCP servers | 3 standalone Python processes | Direct fault isolation; same MCP SDK pattern as Silver |
| Ralph Wiggum loop | Python module + Claude skill | Iteration logic in Python; reasoning in Claude; limits enforced |
| CEO Briefing | Section-by-section aggregation | Independent data sources; graceful partial generation |
| Audit logging | Markdown files, daily rotation | Vault-native; human-readable; no database; queryable by date |
| Service health | JSON state file | Persists across restarts; lightweight; no daemon |
| Error recovery | Decorator with backoff | DRY pattern; applied consistently to all external calls |
| Documentation | Obsidian Markdown | Constitution-mandated; vault-native |

## Platinum Tier Extension Points

These are NOT implemented in Gold but the architecture explicitly supports them:

- **Cloud deployment**: Docker Compose can be deployed to Oracle Cloud VM
- **Always-on daemon**: Scheduler can be replaced with a long-running process
- **Multi-tenancy**: MCP servers can be containerized and multiplexed
- **Additional integrations**: New MCP tools follow the same pattern (add to tools/, register in server)
- **Real-time alerts**: Service health can emit webhooks/push notifications
- **AI forecasting**: Briefing generator can be extended with financial analysis models

## Post-Design Constitution Re-Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Spec-Driven Development | All components trace to Gold spec FRs (FR-001 to FR-021); no unapproved features; Silver/Bronze artifacts reused | PASS |
| II. Agent Behavior Rules | Human approval mandatory for all external actions (D2, FR-020); Ralph Wiggum respects approval gates (D3); comprehensive audit logging (D5, FR-014) | PASS |
| III. Tier Governance | No Platinum features (no cloud, no multi-tenancy, no real-time alerts, no orchestration beyond local Docker); Odoo is Gold-scoped (Principle III) | PASS |
| IV. Technology Constraints | Python + MCP (constitution approved); Odoo Community via Docker (Gold+ approved); Tweepy (free tier); Mastodon (free focus); local-first | PASS |
| V. Quality Principles | Modular MCP servers (D2); retry/recovery (D10); daily audit logs (D5); architecture docs (US8); testable components; graceful degradation | PASS |

**Result**: All gates PASS post-design. Architecture is Gold-scoped and Platinum-ready.
