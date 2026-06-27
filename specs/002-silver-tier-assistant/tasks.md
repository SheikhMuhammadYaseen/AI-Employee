# Tasks: Silver Tier — Functional Assistant

**Input**: Design documents from `specs/002-silver-tier-assistant/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/skill-interfaces.md, contracts/mcp-tools.md
**Extends**: Bronze Tier (all 34 tasks complete, 26/26 tests pass)

**Tests**: Tests are included as unit and integration tasks per spec acceptance scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6, US7)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `.claude/commands/` at repository root
- Vault is a runtime artifact at `vault/` (gitignored)

---

## Phase 1: Setup (Silver Infrastructure)

**Purpose**: Extend Bronze infrastructure with Silver dependencies, directories, and configuration

- [x] T001 Update `requirements.txt` with Silver dependencies: `playwright`, `Mastodon.py`, `mcp`
- [x] T002 Update `.gitignore` with Silver-specific entries: `.watcher_state_*.json`, `.whatsapp_session/`, `*.lock`
- [x] T003 [P] Update `.env.example` with Silver environment variables: `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MASTODON_INSTANCE_URL`, `MASTODON_ACCESS_TOKEN`, `WHATSAPP_SESSION_PATH`, `WHATSAPP_KEYWORDS`
- [x] T004 [P] Create Silver directory structure: `src/mcp/`, `src/mcp/tools/`, `src/reasoning/`, `src/approval/`, `src/scheduling/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Templates and base classes that all user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create `src/watchers/base_watcher.py` with shared base class: `BaseWatcher` with `__init__`, `acquire_lock`, `release_lock`, `load_state`, `save_state`, `is_processed`, `mark_processed`, `create_vault_item`, abstract `run` per contracts/skill-interfaces.md
- [x] T006 [P] Create `src/templates/plan_item_template.md` with YAML frontmatter fields (type, linked_item, status, priority, created_date, total_steps, completed_steps) and checkbox body per data-model.md Plan Item entity
- [x] T007 [P] Create `src/templates/approval_draft_template.md` with YAML frontmatter fields (type, target, status, created_date, linked_item, mcp_tool) and approval checkbox body per data-model.md Approval Draft entity
- [x] T008 Update `src/scripts/setup_vault.py` to create Silver folders: `Pending_Approval/` and `Logs/` in addition to Bronze folders per FR-005, FR-014
- [x] T009 [P] Create `tests/unit/test_base_watcher.py` with tests: (1) state load/save, (2) lock acquire/release, (3) processed ID tracking with 10K cap, (4) vault item creation with correct frontmatter

**Checkpoint**: Templates and base class ready — user story implementation can now begin

---

## Phase 3: User Story 1 — WhatsApp Watcher (Priority: P1) MVP

**Goal**: Playwright-based watcher monitors WhatsApp Web for urgent messages, creates vault items in /Needs_Action

**Independent Test**: Start the WhatsApp watcher, send a test message containing "urgent", verify `.md` file appears in `/Needs_Action`

### Implementation for User Story 1

- [x] T010 [US1] Create `src/watchers/whatsapp_watcher.py` with CLI argument parsing: `--vault-path` (required), `--interval` (default 10), `--session-path` (default `~/.whatsapp_session`), `--keywords` (default `urgent,asap,deadline,emergency`), `--headless` (default false) per contracts/skill-interfaces.md WhatsApp Watcher Interface
- [x] T011 [US1] Implement Playwright browser session management in `src/watchers/whatsapp_watcher.py`: launch Chromium with persistent context at `--session-path`, detect QR code page vs. connected state, save session state on clean exit per research.md R1, R8
- [x] T012 [US1] Implement WhatsApp message monitoring in `src/watchers/whatsapp_watcher.py`: poll DOM for new messages, extract sender/timestamp/content, match against keyword list and Company Handbook priority contacts per FR-001
- [x] T013 [US1] Implement urgent message filtering and vault item creation in `src/watchers/whatsapp_watcher.py`: for urgent matches create `.md` file in `/Needs_Action` with type=whatsapp frontmatter, use BaseWatcher.create_vault_item per FR-001, data-model.md Vault Item
- [x] T014 [US1] Implement reconnection and error handling in `src/watchers/whatsapp_watcher.py`: detect disconnection, retry 3 times with 30s wait, exit gracefully on auth failure with clear re-scan message per spec acceptance scenario 4, edge case

### Tests for User Story 1

- [x] T015 [P] [US1] Create `tests/unit/test_whatsapp_watcher.py` with tests: (1) keyword matching detects urgent messages, (2) non-urgent messages are skipped, (3) vault item has correct whatsapp frontmatter, (4) state file tracks WhatsApp message hashes, (5) lock file prevents concurrent instances — use mocked Playwright per spec acceptance scenarios 1-4

**Checkpoint**: WhatsApp watcher functional — second watcher source operational

---

## Phase 4: User Story 2 — Claude Reasoning Loop with Plan Generation (Priority: P2)

**Goal**: Classify items as simple/complex/action-required, generate Plan.md for complex items

**Independent Test**: Place a complex item in `/Needs_Action`, invoke reasoning, verify Plan.md with checkboxes is generated

### Implementation for User Story 2

- [x] T016 [US2] Create `src/reasoning/classifier.py` with `classify(frontmatter, body) -> str` function returning `"simple"`, `"complex"`, or `"action_required"` using keyword heuristics per plan.md D5, research.md R5
- [x] T017 [US2] Create `src/reasoning/planner.py` with `generate_plan(item_path, vault_path) -> Path` function that reads a vault item, generates Plan.md with checkbox steps using plan_item_template.md, links to original item per FR-004, data-model.md Plan Item
- [x] T018 [US2] Update `.claude/skills/process-inbox/SKILL.md` to add Silver three-way classification routing: simple → /Done (Bronze behavior), complex → invoke planner, action_required → create draft in /Pending_Approval per FR-003, contracts/skill-interfaces.md Extended process-inbox

### Tests for User Story 2

- [x] T019 [P] [US2] Create `tests/unit/test_classifier.py` with tests: (1) simple item classified correctly, (2) complex multi-step item classified correctly, (3) action-required item with "reply"/"send" classified correctly, (4) Company Handbook priority sender override, (5) edge case empty body per spec acceptance scenarios 1-4
- [x] T020 [P] [US2] Create `tests/unit/test_planner.py` with tests: (1) Plan.md created with correct frontmatter, (2) checkbox steps generated, (3) original item linked, (4) step count matches per FR-004

**Checkpoint**: Reasoning loop classifies and plans — agent breaks down complex tasks

---

## Phase 5: User Story 3 — Human-in-the-Loop Approval Workflow (Priority: P3)

**Goal**: Draft external actions in /Pending_Approval, user approves/rejects via Obsidian checkbox, checker processes

**Independent Test**: Place a draft in `/Pending_Approval`, check approval box, run checker, verify action executed

### Implementation for User Story 3

- [x] T021 [US3] Create `src/approval/checker.py` with CLI args `--vault-path` (required), `--dry-run` (default false): scan `/Pending_Approval` for `.md` files, parse frontmatter and checkbox state (`- [x] Approved`, `- [x] Rejected`) per FR-007, contracts/skill-interfaces.md check-approvals
- [x] T022 [US3] Implement approval processing in `src/approval/checker.py`: for approved items invoke MCP tool (read mcp_tool from frontmatter), move to /Done with status=executed; for rejected items move to /Done with status=rejected; process sequentially per spec acceptance scenarios 2-3, edge case
- [x] T023 [US3] Implement stale detection in `src/approval/checker.py`: if draft >24 hours old without action, flag in Dashboard as "awaiting approval" per spec acceptance scenario 4
- [x] T024 [US3] Implement MCP error handling in `src/approval/checker.py`: if MCP server unavailable log error and leave draft in /Pending_Approval with "pending - server unavailable" note; if MCP tool fails log error and move to /Done with status=failed per edge cases

### Tests for User Story 3

- [x] T025 [P] [US3] Create `tests/unit/test_approval_checker.py` with tests: (1) approved draft detected correctly, (2) rejected draft moves to /Done, (3) pending draft left in place, (4) stale draft flagged after 24h, (5) MCP failure handled gracefully — use mocked MCP per spec acceptance scenarios 1-4

**Checkpoint**: Approval workflow operational — human safety gate works

---

## Phase 6: User Story 4 — Social Media Posting via Mastodon (Priority: P4)

**Goal**: Generate social post drafts, publish to Mastodon after approval via MCP

**Independent Test**: Generate draft social post, approve it, verify published to test Mastodon account

### Implementation for User Story 4

- [x] T026 [US4] Create `src/mcp/tools/mastodon_post.py` with `post(content, visibility="public") -> dict` function using `Mastodon.py` library, returns `{"status": "posted", "post_url": ..., "post_id": ...}` on success per contracts/mcp-tools.md mastodon_post
- [x] T027 [US4] Implement error handling in `src/mcp/tools/mastodon_post.py`: catch `MastodonAPIError` for rate limits, auth failures, server errors; return error dict per contracts/mcp-tools.md error cases
- [x] T028 [US4] Implement MCP action logging in `src/mcp/tools/mastodon_post.py`: after every invocation write log `.md` to vault `/Logs/` with frontmatter (tool, result, timestamp, linked_draft, parameters) per FR-010, data-model.md MCP Action Log

### Tests for User Story 4

- [x] T029 [P] [US4] Create `tests/unit/test_mcp_tools.py` with tests: (1) mastodon_post returns success with URL, (2) content >500 chars returns error, (3) auth failure handled, (4) action log created in /Logs — use mocked Mastodon.py per spec acceptance scenarios 1-3

**Checkpoint**: Mastodon posting works end-to-end through approval flow

---

## Phase 7: User Story 5 — MCP Server for External Actions (Priority: P5)

**Goal**: Working MCP server exposing email-send and mastodon-post tools

**Independent Test**: Start MCP server, invoke email-send and mastodon-post tools, verify actions and logs

### Implementation for User Story 5

- [x] T030 [US5] Create `src/mcp/tools/email_send.py` with `send(to, subject, body, reply_to=None) -> dict` function using `smtplib` with Gmail SMTP (smtp.gmail.com:587), returns success/error dict per contracts/mcp-tools.md email_send, research.md R4
- [x] T031 [US5] Implement MCP action logging in `src/mcp/tools/email_send.py`: after every invocation write log `.md` to vault `/Logs/` with sanitized parameters (no passwords) per FR-010, contracts/mcp-tools.md Logging Contract
- [x] T032 [US5] Create `src/mcp/config.py` with configuration loading from `.env` file: `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MASTODON_INSTANCE_URL`, `MASTODON_ACCESS_TOKEN`, `VAULT_PATH` per research.md R3, R4
- [x] T033 [US5] Create `src/mcp/server.py` MCP server entry point using `mcp` Python SDK: register `email_send` and `mastodon_post` tools, configure stdio transport, load config from environment per contracts/mcp-tools.md Server Configuration, research.md R3

**Checkpoint**: MCP server running with two external action tools

---

## Phase 8: User Story 6 — Basic Scheduling (Priority: P6)

**Goal**: OS-native scheduling runs watchers, reasoning, and approval checker on configurable intervals

**Independent Test**: Configure scheduler, wait two cycles, verify all components ran

### Implementation for User Story 6

- [x] T034 [US6] Create `src/scheduling/scheduler_config.json` with default configuration: interval_minutes=5, component enable flags, vault_path, log_path per data-model.md Schedule Configuration
- [x] T035 [US6] Create `src/scheduling/scheduler.py` with CLI args `--config`, `--vault-path`, `--once`: read config, sequentially run enabled components (watchers → reasoning → approval), use lock file to prevent overlap per FR-011, contracts/skill-interfaces.md Scheduler Interface, research.md R7
- [x] T036 [US6] Implement scheduler logging in `src/scheduling/scheduler.py`: each run creates `/Logs/scheduler-<date>.md` with run summary, component results, errors per FR-011
- [x] T037 [US6] Implement partial failure handling in `src/scheduling/scheduler.py`: if one component fails log error and continue with remaining components per spec acceptance scenario 2

**Checkpoint**: Automated scheduling ties all Silver components together

---

## Phase 9: User Story 7 — Extended Agent Skills (Priority: P7)

**Goal**: Package all Silver functionality as reusable Claude Code skills

**Independent Test**: Invoke each new skill individually and verify correct behavior

### Implementation for User Story 7

- [x] T038 [US7] Create `.claude/skills/plan-task/SKILL.md` with prompt instructions per contracts/skill-interfaces.md plan-task: accept item filename, read item + Company Handbook, generate Plan.md with checkboxes, update original item
- [x] T039 [P] [US7] Create `.claude/skills/check-approvals/SKILL.md` with prompt instructions per contracts/skill-interfaces.md check-approvals: scan /Pending_Approval, process approved/rejected/pending items, invoke MCP, update Dashboard
- [x] T040 [P] [US7] Create `.claude/skills/generate-social-post/SKILL.md` with prompt instructions per contracts/skill-interfaces.md generate-social-post: read Company Handbook, generate <500 char Mastodon post, create draft in /Pending_Approval
- [x] T041 [US7] Create `.claude/skills/run-pipeline/SKILL.md` with prompt instructions per contracts/skill-interfaces.md run-pipeline: orchestrate full cycle watchers→reasoning→approval, log results, update Dashboard

**Checkpoint**: All Silver skills individually invocable

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, integration testing, documentation, .gitignore verification

- [x] T042 [P] Add comprehensive error handling to `src/watchers/whatsapp_watcher.py`: catch Playwright timeout, browser crash, DOM changes; log errors with clear recovery instructions per spec edge cases
- [x] T043 [P] Add comprehensive error handling to `src/mcp/server.py`: catch tool registration errors, connection failures, invalid parameters per FR-008
- [x] T044 [P] Create `tests/integration/test_approval_flow.py` with tests: (1) draft created → approved → MCP executed → moved to Done, (2) draft rejected → moved to Done, (3) MCP failure → logged and marked failed per spec acceptance scenarios
- [x] T045 [P] Create `tests/integration/test_watcher_pipeline.py` with tests: (1) both watchers create items without conflicts, (2) reasoning classifies items, (3) full pipeline runs per SC-001, SC-002
- [x] T046 Verify `.gitignore` completeness: confirm `.watcher_state_*.json`, `.whatsapp_session/`, all Silver additions listed; run `git status` to verify no secrets tracked per FR-013
- [x] T047 [P] Update `README.md` with Silver Tier section: architecture diagram, new features, setup instructions, link to quickstart per constitution Principle V
- [x] T048 Run full end-to-end validation per `specs/002-silver-tier-assistant/quickstart.md` Steps 1-11: verify all success criteria (SC-001 through SC-008)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — base class needs directory structure
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — WhatsApp watcher uses BaseWatcher
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — reasoning uses templates
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — approval checker uses templates
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — Mastodon tool uses templates
- **User Story 5 (Phase 7)**: Depends on US4 (Phase 6) — MCP server registers mastodon_post tool
- **User Story 6 (Phase 8)**: Depends on all watchers + reasoning + approval (Phases 3-5)
- **User Story 7 (Phase 9)**: Depends on all user stories being functional
- **Polish (Phase 10)**: Depends on all user stories being complete

### Parallel Opportunities

- T003 and T004 can run in parallel (different files)
- T006, T007, T009 can run in parallel (different files)
- User Stories 1, 2, 3, 4 can all proceed in parallel after Phase 2
- T038-T041 (skills) — T039 and T040 can run in parallel
- T042, T043, T044, T045, T047 can all run in parallel (different files)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T009)
3. Complete Phase 3: User Story 1 (T010-T015)
4. **STOP and VALIDATE**: Start WhatsApp watcher, test with urgent message

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (WhatsApp watcher running!)
3. Add User Story 2 → Test independently → Demo (reasoning classifies + plans!)
4. Add User Story 3 → Test independently → Demo (approval workflow works!)
5. Add User Story 4 + 5 → Test independently → Demo (Mastodon posting + email sending!)
6. Add User Story 6 → Test independently → Demo (automated scheduling!)
7. Add User Story 7 → Test independently → Demo (skills formalized!)
8. Polish → Full Silver Tier complete

### Task Summary

| Phase | Story | Tasks | Parallel |
|-------|-------|-------|----------|
| Phase 1: Setup | — | T001-T004 (4 tasks) | T003, T004 |
| Phase 2: Foundational | — | T005-T009 (5 tasks) | T006, T007, T009 |
| Phase 3: US1 WhatsApp | P1 | T010-T015 (6 tasks) | T015 |
| Phase 4: US2 Reasoning | P2 | T016-T020 (5 tasks) | T019, T020 |
| Phase 5: US3 Approval | P3 | T021-T025 (5 tasks) | T025 |
| Phase 6: US4 Mastodon | P4 | T026-T029 (4 tasks) | T029 |
| Phase 7: US5 MCP Server | P5 | T030-T033 (4 tasks) | — |
| Phase 8: US6 Scheduling | P6 | T034-T037 (4 tasks) | — |
| Phase 9: US7 Skills | P7 | T038-T041 (4 tasks) | T039, T040 |
| Phase 10: Polish | — | T042-T048 (7 tasks) | T042-T045, T047 |
| **Total** | | **48 tasks** | |
