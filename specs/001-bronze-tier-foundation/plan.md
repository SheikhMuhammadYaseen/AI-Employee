# Implementation Plan: Bronze Tier Foundation

**Branch**: `001-bronze-tier-foundation` | **Date**: 2026-02-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-bronze-tier-foundation/spec.md`

## Summary

Build the foundation layer of the Personal AI Employee: an Obsidian vault with standard folder structure, a single Python-based Gmail watcher that creates structured Markdown items, and Claude Code skills (custom commands) for reading, writing, and processing vault contents. All components are local-only, file-based, and designed to be extended by Silver+ tiers without reinvention.

## Technical Context

**Language/Version**: Python 3.13+ (watcher, setup script); Markdown (skills/commands)
**Primary Dependencies**: `google-api-python-client`, `google-auth-oauthlib`, `python-frontmatter`, `pyyaml`
**Storage**: Local filesystem (Markdown files with YAML frontmatter, JSON state file)
**Testing**: Manual acceptance testing per spec scenarios; `pytest` for unit tests on watcher/setup utilities
**Target Platform**: Windows 10+ / macOS / Linux (local desktop, cross-platform)
**Project Type**: Single project
**Performance Goals**: Watcher poll completes in <5 seconds; processing skill handles 50 items per run without timeout
**Constraints**: Local-only; no cloud; no network actions beyond Gmail read; <100MB disk for vault+state
**Scale/Scope**: Single user, single Gmail account, one vault, ~100 items/day maximum

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Spec-Driven Development | Plan derives from approved spec only; no unapproved features | PASS |
| II. Agent Behavior Rules | All code generated via Claude Code; no manual coding; no feature invention | PASS |
| III. Tier Governance | No Silver/Gold/Platinum features (no MCP, no Odoo, no cloud, no multiple watchers) | PASS |
| IV. Technology Constraints | Python 3.13+, Google API for Gmail, Obsidian vault, local-first, no unauthorized libs | PASS |
| V. Quality Principles | Separation of concerns (Perception→Reasoning→Action), modular skills, error handling, documentation | PASS |

**Result**: All gates PASS. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-tier-foundation/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: setup and usage guide
├── contracts/
│   └── skill-interfaces.md  # Phase 1: skill input/output contracts
└── tasks.md             # Phase 2: created by /sp.tasks (not yet)
```

### Source Code (repository root)

```text
src/
├── scripts/
│   └── setup_vault.py          # US1: Idempotent vault creation
├── watchers/
│   └── gmail_watcher.py        # US2: Gmail polling watcher
└── templates/
    ├── dashboard_template.md   # Template for Dashboard.md generation
    ├── vault_item_template.md  # Template for Needs_Action items
    └── handbook_template.md    # Seed content for Company_Handbook.md

.claude/
└── commands/
    ├── vault-read.md           # US4: Skill to read vault folder
    ├── vault-write.md          # US4: Skill to write vault file
    └── process-inbox.md        # US3/US4: Orchestration skill

vault/                          # Created by setup script (gitignored)
├── Dashboard.md
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
├── Done/
└── .watcher_state.json         # Hidden state file (gitignored)

tests/
├── unit/
│   ├── test_setup_vault.py     # Setup script tests
│   └── test_gmail_watcher.py   # Watcher utility tests
└── integration/
    └── test_end_to_end.py      # Full flow: setup → watcher → process
```

**Structure Decision**: Single project layout. The `src/` directory holds Python scripts organized by function (scripts, watchers, templates). Claude Code skills live in `.claude/commands/` per Claude Code conventions. The vault itself is a runtime artifact created by the setup script, gitignored to keep secrets and user data out of source control.

## Architecture: Perception → Reasoning → Action

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   PERCEPTION     │     │    REASONING      │     │     ACTION       │
│ (Senses)         │     │ (Brain)           │     │ (Hands)          │
│                  │     │                   │     │                  │
│ gmail_watcher.py │────>│ Claude Code       │────>│ vault-write      │
│ Polls Gmail      │     │ /process-inbox    │     │ Write to /Done   │
│ Creates .md in   │     │ Reads /Needs_     │     │ Update Dashboard │
│ /Needs_Action    │     │ Action, applies   │     │ Remove from      │
│                  │     │ Company_Handbook   │     │ /Needs_Action    │
│                  │     │ rules, generates   │     │                  │
│                  │     │ summaries          │     │                  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Component Responsibilities

| Component | Layer | Responsibility | Inputs | Outputs |
|-----------|-------|---------------|--------|---------|
| `setup_vault.py` | Setup | Create vault structure | `--vault-path` | Folders + seed files on disk |
| `gmail_watcher.py` | Perception | Monitor Gmail, create vault items | Gmail API, `--vault-path` | `.md` files in `/Needs_Action` |
| `/vault-read` | Reasoning | Read and parse vault items | Folder name | Parsed item list |
| `/vault-write` | Action | Write content to vault | Path + content | File on disk |
| `/process-inbox` | Reasoning+Action | Orchestrate read→process→write | None (uses vault path) | Reports in `/Done`, updated Dashboard |
| `Company_Handbook.md` | Memory | Store user rules/preferences | User edits | Read by processing skill |
| `Dashboard.md` | Memory | Display current state | Updated by processing skill | Human-readable summary |

## Key Design Decisions

### D1: Skills as Claude Code Custom Commands (not Python scripts)

The "brain" layer uses Claude Code's native custom command system (`.claude/commands/*.md`) rather than Python scripts. This keeps the reasoning layer in the AI's domain and avoids mixing concerns. Python is only used for the "senses" layer (watcher) and setup utilities.

### D2: Vault as Single Source of Truth

The Obsidian vault is the only data store. There is no database, no external state service. The vault IS the state. This aligns with the constitution's local-first mandate and makes the system transparent — everything is a readable Markdown file.

### D3: Polling Over Push

The Gmail watcher uses polling (every N seconds) rather than push notifications. This is simpler, has no webhook infrastructure requirements, and is appropriate for Bronze tier's scope. Silver+ tiers may upgrade to push.

### D4: Idempotent Setup

The setup script can run multiple times without data loss. This prevents accidental destruction of user-curated vault content and makes the system robust to re-installation or updates.

### D5: Cross-Platform Lock File

The watcher uses a PID-based lock file rather than OS-specific locking mechanisms. This works on Windows, macOS, and Linux without external dependencies.

## Complexity Tracking

> No violations found. All design choices use the simplest viable approach.

| Aspect | Approach | Why Simplest |
|--------|----------|-------------|
| Storage | Local Markdown files | No database setup, human-readable, Obsidian-native |
| State tracking | JSON file | No external dependencies, easy to debug |
| Skills | Claude Code custom commands | Built-in feature, no framework needed |
| Watcher | Single-file Python script | Minimal code, no async framework |
| Lock mechanism | PID file | Cross-platform, no external library |

## Security Considerations

- `credentials.json` and `token.json` MUST be in `.gitignore`
- `.watcher_state.json` MUST be in `.gitignore` (contains no secrets but is runtime state)
- `vault/` directory MUST be in `.gitignore` (may contain private email content)
- Gmail API scope limited to `gmail.readonly` — no send/modify capability
- No network calls except Gmail API polling (no telemetry, no analytics, no cloud sync)

## Silver Tier Extension Points

These are NOT implemented in Bronze but the architecture explicitly supports them:

- **Additional watchers**: New scripts in `src/watchers/` follow the same pattern (poll → create `.md` → update state)
- **Additional skills**: New `.claude/commands/*.md` files extend capabilities
- **MCP servers**: Can be added alongside skills without modifying existing components
- **Multiple sources**: Watcher state JSON supports a `source` field for differentiation
