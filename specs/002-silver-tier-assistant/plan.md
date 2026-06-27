# Implementation Plan: Silver Tier — Functional Assistant

**Branch**: `002-silver-tier-assistant` | **Date**: 2026-02-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/002-silver-tier-assistant/spec.md`
**Extends**: Bronze Tier (`specs/001-bronze-tier-foundation/`)

## Summary

Extend the Bronze Tier foundation into a practical, multi-source assistant with two watchers (Gmail + WhatsApp), a Claude reasoning loop that generates Plan.md files for complex tasks, a human-in-the-loop approval workflow via `/Pending_Approval`, an MCP server for external actions (email send + Mastodon post), OS-native scheduling, and four new Claude Code skills. All components are local-only and human-approved before any external action.

## Technical Context

**Language/Version**: Python 3.11+ (watchers, MCP server, scheduler scripts); Markdown (skills/commands)
**Primary Dependencies**:
- Bronze (carried forward): `google-api-python-client`, `google-auth-oauthlib`, `python-frontmatter`, `pyyaml`
- New: `playwright` (WhatsApp Web automation), `Mastodon.py` (Mastodon API client), `mcp` (Model Context Protocol SDK for Python), `smtplib` (stdlib, Gmail SMTP send)
**Storage**: Local filesystem (Markdown files with YAML frontmatter, JSON state files)
**Testing**: `pytest` for unit tests; manual acceptance testing per spec scenarios
**Target Platform**: Windows 10+ / macOS / Linux (local desktop, cross-platform)
**Project Type**: Single project (extending Bronze structure)
**Performance Goals**: Watchers complete poll in <10 seconds each; reasoning loop processes 10 items per run; MCP tool calls complete in <30 seconds; scheduler cycle completes in <5 minutes
**Constraints**: Local-only; no cloud; human approval mandatory for all external actions; <200MB disk for vault+state+logs; free tools only
**Scale/Scope**: Single user, single Gmail + single WhatsApp account, one Mastodon account, one vault, ~200 items/day maximum

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Spec-Driven Development | Plan derives from approved Silver spec only; no unapproved features; Bronze artifacts reused | PASS |
| II. Agent Behavior Rules | All code generated via Claude Code; human-in-the-loop for all external actions (FR-009); no feature invention | PASS |
| III. Tier Governance | No Gold/Platinum features (no Odoo, no audit dashboards, no cloud, no Ralph Wiggum loop — FR-015) | PASS |
| IV. Technology Constraints | Python + Playwright for WhatsApp (constitution-approved); Mastodon API (free focus); MCP server (constitution Hands/Actions); local-first | PASS |
| V. Quality Principles | Clean Architecture (Perception→Reasoning→Action extended); approval safety gate; error handling with retry/log; modular skills | PASS |

**Result**: All gates PASS. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-silver-tier-assistant/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: setup and usage guide
├── contracts/
│   ├── skill-interfaces.md   # Phase 1: new skill contracts
│   └── mcp-tools.md          # Phase 1: MCP server tool contracts
└── tasks.md             # Phase 2: created by /sp.tasks (not yet)
```

### Source Code (repository root)

```text
src/
├── scripts/
│   └── setup_vault.py          # Bronze (unchanged)
├── watchers/
│   ├── base_watcher.py         # NEW: Shared base class for watchers
│   ├── gmail_watcher.py        # Bronze (extended with base class)
│   └── whatsapp_watcher.py     # NEW: US1 WhatsApp Web monitor
├── mcp/
│   ├── server.py               # NEW: US5 MCP server entry point
│   ├── tools/
│   │   ├── email_send.py       # NEW: US5 Gmail SMTP send tool
│   │   └── mastodon_post.py    # NEW: US4/US5 Mastodon post tool
│   └── config.py               # NEW: US5 MCP server configuration
├── reasoning/
│   ├── classifier.py           # NEW: US2 Item classification logic
│   └── planner.py              # NEW: US2 Plan.md generation
├── approval/
│   └── checker.py              # NEW: US3 Approval workflow checker
├── scheduling/
│   ├── scheduler.py            # NEW: US6 Pipeline orchestrator
│   └── scheduler_config.json   # NEW: US6 Schedule intervals config
└── templates/
    ├── dashboard_template.md   # Bronze (unchanged)
    ├── vault_item_template.md  # Bronze (unchanged)
    ├── handbook_template.md    # Bronze (unchanged)
    ├── plan_item_template.md   # NEW: US2 Plan.md template
    └── approval_draft_template.md  # NEW: US3 Pending Approval template

.claude/
└── commands/
    ├── vault-read.md           # Bronze (unchanged)
    ├── vault-write.md          # Bronze (unchanged)
    ├── process-inbox.md        # Bronze (extended for Silver routing)
    ├── plan-task.md            # NEW: US7 Generate Plan.md skill
    ├── check-approvals.md      # NEW: US7 Approval checker skill
    ├── generate-social-post.md # NEW: US7 Social post draft skill
    └── run-pipeline.md         # NEW: US7 Full pipeline skill

vault/                          # Runtime artifact (gitignored)
├── Dashboard.md
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
├── Pending_Approval/           # NEW: Silver approval drafts
├── Done/
├── Logs/                       # NEW: Silver scheduling/error logs
└── .watcher_state_*.json       # Per-watcher state files (gitignored)

tests/
├── unit/
│   ├── test_setup_vault.py     # Bronze (unchanged)
│   ├── test_gmail_watcher.py   # Bronze (unchanged)
│   ├── test_base_watcher.py    # NEW: Base watcher tests
│   ├── test_whatsapp_watcher.py # NEW: WhatsApp watcher tests
│   ├── test_classifier.py      # NEW: Reasoning classifier tests
│   ├── test_planner.py         # NEW: Plan.md generation tests
│   ├── test_approval_checker.py # NEW: Approval workflow tests
│   └── test_mcp_tools.py       # NEW: MCP tool tests
└── integration/
    ├── test_end_to_end.py      # Bronze (extended)
    ├── test_watcher_pipeline.py # NEW: Multi-watcher pipeline test
    └── test_approval_flow.py    # NEW: Draft→approve→execute test
```

**Structure Decision**: Extends Bronze single-project layout. New directories added: `src/mcp/` for the MCP server, `src/reasoning/` for the Claude reasoning loop helpers, `src/approval/` for the approval workflow checker, `src/scheduling/` for the pipeline orchestrator. Bronze files remain unchanged at their original locations. Four new Claude Code skills added to `.claude/commands/`. Vault extended with `/Pending_Approval` and `/Logs` folders.

## Architecture: Extended Perception → Reasoning → Action

```text
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│   PERCEPTION         │     │    REASONING          │     │     ACTION            │
│ (Senses)             │     │ (Brain)               │     │ (Hands)               │
│                      │     │                       │     │                       │
│ gmail_watcher.py     │     │ Claude Code           │     │ /check-approvals      │
│ whatsapp_watcher.py  │──>  │ /process-inbox        │──>  │ Reads /Pending_       │
│                      │     │ Classifies items:     │     │ Approval for checked  │
│ Both create .md in   │     │ - Simple → /Done      │     │ items, then invokes   │
│ /Needs_Action        │     │ - Complex → Plan.md   │     │ MCP server tools      │
│                      │     │ - Action → /Pending_  │     │                       │
│                      │     │   Approval draft      │     │ MCP Server:           │
│                      │     │                       │     │ - email_send          │
│                      │     │ /plan-task             │     │ - mastodon_post       │
│                      │     │ /generate-social-post  │     │                       │
│                      │     │                       │     │ Results logged to     │
│                      │     │                       │     │ /Done + /Logs         │
└─────────────────────┘     └──────────────────────┘     └──────────────────────┘
                                                                    ▲
                         ┌─────────────────────┐                    │
                         │   SAFETY GATE        │                   │
                         │                      │                   │
                         │ /Pending_Approval    │───────────────────┘
                         │ Human checks box     │
                         │ in Obsidian          │
                         │                      │
                         └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│   SCHEDULING (OS-native: Task Scheduler / cron)                             │
│                                                                             │
│   Every 5 min: watchers → reasoning loop → approval checker                │
│   /run-pipeline orchestrates the full cycle                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Layer | Responsibility | Inputs | Outputs |
|-----------|-------|---------------|--------|---------|
| `base_watcher.py` | Perception | Shared watcher infrastructure (state, lock, vault write) | Config | Base class for all watchers |
| `gmail_watcher.py` | Perception | Monitor Gmail (Bronze, refactored to use base) | Gmail API, `--vault-path` | `.md` files in `/Needs_Action` |
| `whatsapp_watcher.py` | Perception | Monitor WhatsApp Web for urgent messages | Playwright, `--vault-path` | `.md` files in `/Needs_Action` |
| `classifier.py` | Reasoning | Classify items as simple/complex/action-required | Vault item `.md` | Classification result |
| `planner.py` | Reasoning | Generate Plan.md with checkboxes | Complex item | `Plan.md` in `/Needs_Action` |
| `/process-inbox` | Reasoning | Extended: route items based on classification | `/Needs_Action` items | `/Done`, Plan.md, or `/Pending_Approval` |
| `/plan-task` | Reasoning | Generate Plan.md for a specific item | Complex vault item | `Plan.md` with checkbox steps |
| `/generate-social-post` | Reasoning | Create draft social media post | Company Handbook | Draft in `/Pending_Approval` |
| `/check-approvals` | Action | Scan `/Pending_Approval` for approved/rejected items | Approval folder | MCP tool calls or archive |
| `/run-pipeline` | Orchestration | Run full cycle: watchers→reasoning→approval | None | Full pipeline execution |
| `server.py` | Action | MCP server exposing email-send and mastodon-post | Tool calls from approval checker | External actions + logs |
| `email_send.py` | Action | Send email via Gmail SMTP | Recipient, subject, body | Sent email + log entry |
| `mastodon_post.py` | Action | Post to Mastodon | Content text | Published post + log entry |
| `checker.py` | Action | Parse approval files, trigger MCP actions | `/Pending_Approval` files | Executed actions + `/Done` moves |
| `scheduler.py` | Scheduling | Orchestrate timed pipeline runs | Config JSON | Watcher + reasoning + approval runs |
| `Company_Handbook.md` | Memory | Store user rules, priorities, social preferences | User edits | Read by reasoning + social skills |
| `Dashboard.md` | Memory | Display current state | Updated by processing | Human-readable summary |

## Key Design Decisions

### D1: Base Watcher Class Extraction

Extract common watcher functionality (state management, lock files, vault item creation, error handling) from `gmail_watcher.py` into `base_watcher.py`. Both Gmail and WhatsApp watchers inherit from this base. This prevents code duplication and ensures consistent behavior (per constitution Quality Principle: modular, testable code).

### D2: Playwright for WhatsApp Web Automation

Use Playwright (Python) to automate WhatsApp Web in a headless or headed browser session. Playwright is constitution-approved ("Playwright for WhatsApp" per Principle IV). The watcher connects to an existing WhatsApp Web session, monitors for messages matching urgent keywords, and creates vault items.

**Trade-off**: Playwright requires a browser runtime (~200MB), but it's the only constitution-approved approach for WhatsApp monitoring without an official API.

### D3: Mastodon.py for Social Posting

Use `Mastodon.py` library to interface with the Mastodon API. Constitution mandates Mastodon as the free alternative to LinkedIn/X (Principle IV: Free Focus). The library handles OAuth2, rate limits, and API versioning.

### D4: Python MCP Server (not Node.js)

Implement the MCP server in Python using the official `mcp` SDK rather than Node.js. This keeps the entire Silver stack in a single language (Python), reduces setup complexity, and allows reuse of existing libraries (Mastodon.py, smtplib). Constitution allows "Node.js or Python" for MCP servers (Principle IV).

### D5: Three-Way Item Classification

The reasoning loop classifies items into three categories:
1. **Simple** (single-action): Process immediately → move to `/Done` (Bronze behavior preserved)
2. **Complex** (multi-step): Generate `Plan.md` with checkboxes in `/Needs_Action`
3. **Action-required** (external): Create draft in `/Pending_Approval`

Classification uses keyword heuristics in `classifier.py` (e.g., presence of "reply", "send", "post" → action-required; multiple action verbs → complex; otherwise → simple). Claude Code enhances this via the `/process-inbox` skill.

### D6: File-Based Approval Workflow

Approvals use Obsidian-native Markdown checkboxes. No database, no web UI, no external service. The approval checker is a Python script that parses `.md` files in `/Pending_Approval` looking for `- [x] Approved` or `- [x] Rejected` patterns. This aligns with the vault-as-SSOT principle (D2 from Bronze).

### D7: Per-Watcher State Files

Each watcher maintains its own state file: `.watcher_state_gmail.json`, `.watcher_state_whatsapp.json`. This prevents state conflicts when multiple watchers run simultaneously (FR-002). Bronze's single `.watcher_state.json` is migrated to `.watcher_state_gmail.json`.

### D8: OS-Native Scheduling via Wrapper Script

The scheduler uses a Python wrapper (`scheduler.py`) that is invoked by OS-native tools (Task Scheduler on Windows, cron on Linux/macOS). The wrapper reads `scheduler_config.json` for intervals and enabled components, then sequentially runs: watchers → reasoning loop → approval checker. This avoids building a custom daemon while leveraging OS-proven scheduling.

### D9: Gmail SMTP for Email Sending

Use Python's built-in `smtplib` with Gmail's SMTP server for sending emails (after approval). This requires an App Password (not the same OAuth2 as reading). The user generates an App Password from Google Account settings. No additional library needed.

### D10: MCP Action Logging to Vault

Every MCP tool invocation is logged as a `.md` file in `/Logs/` with YAML frontmatter (tool name, parameters, result, timestamp, linked approval draft). This satisfies FR-010 and SC-006 audit requirements without building a separate logging system.

## Complexity Tracking

> No violations found. All design choices use the simplest viable approach.

| Aspect | Approach | Why Simplest |
|--------|----------|-------------|
| WhatsApp monitoring | Playwright automation | Constitution-mandated; no official API alternative |
| Social posting | Mastodon.py library | Single library, free API, constitution-mandated |
| MCP server | Python MCP SDK | Same language as watchers; no Node.js setup needed |
| Approval workflow | Markdown checkboxes in Obsidian | No database, no web UI, vault-native |
| Scheduling | OS-native + Python wrapper | No custom daemon, proven OS scheduler |
| Item classification | Keyword heuristics + Claude | Simple defaults, AI enhancement via skills |
| Email sending | stdlib smtplib | Zero dependency, built into Python |
| Action logging | Markdown files in /Logs | Vault-native, human-readable, no database |

## Security Considerations

- All Bronze security rules carried forward (credentials in .gitignore, gmail.readonly scope for reading)
- WhatsApp session data (browser profile) MUST be stored locally only, NEVER synced
- Mastodon API access token stored in `.env` file (gitignored), NEVER hardcoded
- Gmail App Password for SMTP sending stored in `.env` file (gitignored), NEVER hardcoded
- MCP server runs on localhost only — no network exposure
- ALL external actions require explicit human approval (FR-009) — the system CANNOT auto-send
- MCP action logs in `/Logs/` may contain sensitive content — vault MUST remain gitignored
- Lock files per watcher prevent race conditions with scheduled runs

## Gold Tier Extension Points

These are NOT implemented in Silver but the architecture explicitly supports them:

- **Odoo integration**: New MCP tools can be added to `src/mcp/tools/` without modifying existing tools
- **Ralph Wiggum loop**: The `/run-pipeline` skill can be extended with iteration/retry logic
- **Full audit trails**: `/Logs/` folder structure supports comprehensive audit reporting
- **Additional watchers**: New scripts in `src/watchers/` follow the base_watcher.py pattern
- **More MCP tools**: Tool registration in `server.py` is modular — add files to `src/mcp/tools/`

## Post-Design Constitution Re-Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Spec-Driven Development | All components trace to Silver spec FRs; no unapproved features | PASS |
| II. Agent Behavior Rules | Human approval mandatory (D6); all code AI-generated; no feature invention | PASS |
| III. Tier Governance | No Odoo (D4 uses MCP not ERP); no Ralph Wiggum (D8 uses simple scheduler); no cloud | PASS |
| IV. Technology Constraints | Playwright (approved), Mastodon.py (free focus), Python MCP (approved), local-first | PASS |
| V. Quality Principles | Modular (base_watcher, skill per function); testable; documented; error handling with logs | PASS |

**Result**: All gates PASS post-design. Architecture is Silver-scoped and Gold-ready.
