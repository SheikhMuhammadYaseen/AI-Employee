# Tasks: Bronze Tier Foundation

**Input**: Design documents from `specs/001-bronze-tier-foundation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/skill-interfaces.md

**Tests**: Tests are included as unit and integration tasks per spec acceptance scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `.claude/commands/` at repository root
- Vault is a runtime artifact at `vault/` (gitignored)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency management, and gitignore configuration

- [x] T001 Create project directory structure: `src/scripts/`, `src/watchers/`, `src/templates/`, `.claude/commands/`, `tests/unit/`, `tests/integration/` at repository root
- [x] T002 Create `requirements.txt` at repository root with dependencies: `google-api-python-client`, `google-auth-oauthlib`, `python-frontmatter`, `pyyaml`, `pytest`
- [x] T003 [P] Create `.gitignore` at repository root with entries: `credentials.json`, `token.json`, `vault/`, `.watcher_state.json`, `.watcher.lock`, `__pycache__/`, `*.pyc`, `.env`
- [x] T004 [P] Create `.env.example` at repository root documenting required environment setup (vault path, credentials path) without actual secrets

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Markdown templates that all user stories depend on — vault item format, dashboard format, handbook seed content

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create vault item Markdown template in `src/templates/vault_item_template.md` with YAML frontmatter fields (type, from, subject, date, status, suggested_actions, source_id, processed_date) and body placeholder per data-model.md Vault Item entity
- [x] T006 [P] Create dashboard Markdown template in `src/templates/dashboard_template.md` with YAML frontmatter (last_updated, items_pending, items_processed), Current Status section, Recent Activity table, and Pending Items checklist per data-model.md Dashboard entity
- [x] T007 [P] Create Company Handbook seed content in `src/templates/handbook_template.md` with YAML frontmatter (last_edited), Processing Rules section, Preferences section, and Constraints section per data-model.md Company Handbook entity

**Checkpoint**: Templates ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Obsidian Vault Setup (Priority: P1) MVP

**Goal**: Idempotent setup script creates a fully functional Obsidian vault with standard folders and seed files

**Independent Test**: Run `setup_vault.py --vault-path ./test_vault`, verify all folders and files exist, run again and verify no overwrites

### Implementation for User Story 1

- [x] T008 [US1] Create `src/scripts/setup_vault.py` with CLI argument parsing: `--vault-path` (required) using `argparse`; validate path is writable; exit with clear error on invalid path per contracts/skill-interfaces.md Setup Script Interface
- [x] T009 [US1] Implement vault directory creation in `src/scripts/setup_vault.py`: create `vault-path/Inbox/`, `vault-path/Needs_Action/`, `vault-path/Done/` folders; use `os.makedirs(exist_ok=True)` for idempotency per FR-001, FR-010
- [x] T010 [US1] Implement seed file creation in `src/scripts/setup_vault.py`: copy `src/templates/dashboard_template.md` to `vault-path/Dashboard.md` and `src/templates/handbook_template.md` to `vault-path/Company_Handbook.md` ONLY if files do not already exist; print each created path to stdout per FR-001, FR-010
- [x] T011 [US1] Add `.gitkeep` files to empty vault folders (`Inbox/`, `Needs_Action/`, `Done/`) to ensure Obsidian recognizes them; add error handling for permission denied with clear error message per spec edge case

### Tests for User Story 1

- [x] T012 [P] [US1] Create `tests/unit/test_setup_vault.py` with tests: (1) fresh vault creation produces all 3 folders + 2 files, (2) idempotent re-run does not overwrite existing files, (3) invalid path exits with error, (4) vault is openable in Obsidian-compatible structure per spec acceptance scenarios 1-3

**Checkpoint**: User Story 1 is fully functional — vault can be created and opened in Obsidian

---

## Phase 4: User Story 2 — Single Gmail Watcher (Priority: P2)

**Goal**: Python watcher script polls Gmail for unread emails and creates structured Markdown files in /Needs_Action

**Independent Test**: Configure with Gmail OAuth credentials, send a test email, verify `.md` file appears in `/Needs_Action` within one poll cycle

### Implementation for User Story 2

- [x] T013 [US2] Create `src/watchers/gmail_watcher.py` with CLI argument parsing: `--vault-path` (required), `--interval` (optional, default 60), `--credentials` (optional, default `./credentials.json`) using `argparse` per contracts/skill-interfaces.md Watcher Interface
- [x] T014 [US2] Implement OAuth2 authentication flow in `src/watchers/gmail_watcher.py`: load `credentials.json`, check for existing `token.json`, run browser-based auth if no token, save token locally, use `gmail.readonly` scope only per research.md R1, FR-002, FR-008
- [x] T015 [US2] Implement Gmail polling logic in `src/watchers/gmail_watcher.py`: call `users().messages().list(userId='me', q='is:unread')` to get unread message IDs, then `users().messages().get()` for full content (headers + body), extract sender, subject, date, and first 500 chars of plain text body per FR-002, FR-003, research.md R1
- [x] T016 [US2] Implement watcher state management in `src/watchers/gmail_watcher.py`: load/create `.watcher_state.json` in vault root, compare fetched IDs against `processed_ids`, skip already-processed emails, append new IDs after processing, cap array at 10,000 entries (remove oldest), update `last_poll` timestamp per FR-004, research.md R3, data-model.md Watcher State
- [x] T017 [US2] Implement vault item file creation in `src/watchers/gmail_watcher.py`: for each new email, generate filename as `email-<timestamp>-<slug>.md`, write YAML frontmatter (type, from, subject, date, status=pending, source_id) + body content to `vault-path/Needs_Action/` using `python-frontmatter` per FR-003, data-model.md Vault Item
- [x] T018 [US2] Implement polling loop in `src/watchers/gmail_watcher.py`: wrap poll-and-process in a `while True` loop with `time.sleep(interval)`, catch network errors with `try/except` and log to stderr without crashing, catch auth errors and exit with "Re-authentication required" message per FR-005, spec acceptance scenario 4
- [x] T019 [US2] Implement lock file mechanism in `src/watchers/gmail_watcher.py`: on startup check for `.watcher.lock` in vault root, read PID and verify process alive using `os.kill(pid, 0)`, exit if alive with "Watcher already running" message, delete stale lock and proceed if dead, register `atexit` handler and signal handlers for cleanup per research.md R6, spec edge case

### Tests for User Story 2

- [x] T020 [P] [US2] Create `tests/unit/test_gmail_watcher.py` with tests: (1) state file load/save correctly tracks IDs, (2) duplicate emails skipped, (3) vault item file has correct frontmatter structure, (4) lock file prevents concurrent instances, (5) state file caps at 10,000 entries — use mocked Gmail API per spec acceptance scenarios 1-4

**Checkpoint**: User Story 2 is fully functional — watcher detects emails and creates vault items

---

## Phase 5: User Story 3 — Claude Code Reads and Writes to Vault (Priority: P3)

**Goal**: Claude Code processing skill reads /Needs_Action, generates summaries, writes reports to /Done, and updates Dashboard.md

**Independent Test**: Place a manually created `.md` file in `/Needs_Action`, invoke `/process-inbox`, verify report in `/Done` and updated `Dashboard.md`

### Implementation for User Story 3

- [x] T021 [US3] Create `.claude/skills/process-inbox/SKILL.md` with prompt instructions: (1) read all `.md` files from `vault/Needs_Action/`, (2) for each file parse YAML frontmatter and body, (3) read `vault/Company_Handbook.md` for processing rules and preferences, (4) generate a concise summary (3-5 bullets) and suggested next actions for each item per FR-006, contracts/skill-interfaces.md process-inbox
- [x] T022 [US3] Add report generation instructions to `.claude/skills/process-inbox/SKILL.md`: for each processed item, create a report `.md` file in `vault/Done/` with frontmatter (type, from, subject, date, status=done, processed_date=now) and body containing the summary + suggested actions; remove the original from `vault/Needs_Action/` per FR-006, spec acceptance scenario 1
- [x] T023 [US3] Add Dashboard update instructions to `.claude/skills/process-inbox/SKILL.md`: after processing all items, rewrite `vault/Dashboard.md` using the template format from `src/templates/dashboard_template.md` — update pending count, processed count, last run timestamp, recent activity table (last 10 items), and pending items checklist per FR-006, research.md R5, spec acceptance scenarios 2-3
- [x] T024 [US3] Add error handling instructions to `.claude/skills/process-inbox/SKILL.md`: skip `.md` files with malformed/missing frontmatter (log warning), ignore non-`.md` files, handle empty `/Needs_Action` gracefully (update Dashboard with "no pending items"), report summary of actions taken at the end per spec acceptance scenario 4, spec edge cases

### Tests for User Story 3

- [x] T025 [P] [US3] Create `tests/integration/test_end_to_end.py` with manual test checklist: (1) place test `.md` file in vault/Needs_Action, (2) invoke `/process-inbox`, (3) verify report in vault/Done with correct frontmatter, (4) verify Dashboard.md updated, (5) verify original removed from Needs_Action, (6) verify malformed file skipped gracefully — document as executable manual steps per spec acceptance scenarios 1-4

**Checkpoint**: User Story 3 is fully functional — Claude Code processes vault items end-to-end

---

## Phase 6: User Story 4 — Reusable Agent Skills (Priority: P4)

**Goal**: Package all AI functionality as individually invocable, documented Claude Code custom commands

**Independent Test**: Invoke `/vault-read`, `/vault-write` individually with valid and invalid inputs, verify correct output and error messages

### Implementation for User Story 4

- [x] T026 [US4] Create `.claude/skills/vault-read/SKILL.md` with prompt instructions: accept a `folder` argument (e.g., `Needs_Action`, `Done`, `Inbox`), read all `.md` files from `vault/<folder>/`, parse YAML frontmatter, return list of items with filename, frontmatter fields, and body text; handle folder-not-found, empty folder, and invalid frontmatter errors per FR-007, contracts/skill-interfaces.md vault-read
- [x] T027 [P] [US4] Create `.claude/skills/vault-write/SKILL.md` with prompt instructions: accept `path` (relative to vault root) and `content` arguments, write the content as a Markdown file at `vault/<path>`, confirm success with "Written: {path}"; handle directory-not-found, permission-denied, and empty-content errors per FR-007, contracts/skill-interfaces.md vault-write
- [x] T028 [US4] Update `.claude/skills/process-inbox/SKILL.md` to reference `/vault-read` and `/vault-write` skills in its instructions, documenting the composition pattern (process-inbox orchestrates vault-read + reasoning + vault-write) per FR-007, spec acceptance scenario 3
- [x] T029 [US4] Add documentation header to each skill file (`.claude/skills/vault-read/SKILL.md`, `.claude/skills/vault-write/SKILL.md`, `.claude/skills/process-inbox/SKILL.md`): include skill name, description, expected inputs, expected outputs, error handling behavior, and example usage per FR-007, spec acceptance scenario 4

**Checkpoint**: All skills are individually invocable and documented

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling hardening, security verification, documentation, and end-to-end validation

- [x] T030 [P] Add comprehensive error handling to `src/scripts/setup_vault.py`: catch `PermissionError`, `OSError`, `FileExistsError` with user-friendly messages; add `--verbose` flag for detailed output per spec edge cases
- [x] T031 [P] Add comprehensive error handling to `src/watchers/gmail_watcher.py`: catch `google.auth.exceptions.RefreshError` for expired tokens, `HttpError` for API failures, `json.JSONDecodeError` for corrupt state file, `IOError` for file write failures — all with user-friendly stderr messages per spec edge cases, FR-005
- [x] T032 Verify `.gitignore` completeness: confirm `credentials.json`, `token.json`, `vault/`, `.watcher_state.json`, `.watcher.lock` are all listed; run `git status` to verify no secrets are tracked per FR-008, SC-006
- [x] T033 [P] Create `README.md` at repository root with Bronze Tier overview: project description, architecture diagram (Perception→Reasoning→Action), setup instructions (link to quickstart.md), usage examples, and contribution note that all code is AI-generated per constitution Principle II
- [x] T034 Run full end-to-end validation per `specs/001-bronze-tier-foundation/quickstart.md` Steps 1-7: setup vault, run watcher with test email, process inbox, verify all success criteria (SC-001 through SC-006)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — templates need directory structure
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — setup script uses templates
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — watcher uses vault item template
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — processing uses dashboard template
- **User Story 4 (Phase 6)**: Depends on User Story 3 (Phase 5) — skills formalize what process-inbox already does
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — independent of US1 (uses its own vault path)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — independent of US2 (can use manually placed files)
- **User Story 4 (P4)**: Depends on User Story 3 — formalizes the process-inbox skill created in US3

### Within Each User Story

- Implementation tasks before test tasks
- CLI argument parsing before business logic
- Core logic before error handling
- Tests validate the completed story

### Parallel Opportunities

- T003 and T004 can run in parallel (different files, no dependencies)
- T005, T006, T007 — T006 and T007 can run in parallel (different template files)
- T012 can run in parallel with T013+ (different files: tests vs watcher)
- T020 can run in parallel with T021+ (different files: tests vs skills)
- T025 can run in parallel with T026+ (different files: tests vs skills)
- T026 and T027 can run in parallel (different skill files)
- T030, T031, T032, T033 can all run in parallel (different files, independent concerns)
- **User Stories 1, 2, 3 can all proceed in parallel** after Phase 2 (they touch different files)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T007)
3. Complete Phase 3: User Story 1 (T008-T012)
4. **STOP and VALIDATE**: Run setup script, open vault in Obsidian
5. Deploy/demo if ready — vault creation is the minimum viable deliverable

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (vault created!)
3. Add User Story 2 → Test independently → Demo (watcher running!)
4. Add User Story 3 → Test independently → Demo (agent processes items!)
5. Add User Story 4 → Test independently → Demo (skills formalized!)
6. Polish → Full Bronze Tier complete

### Task Summary

| Phase | Story | Tasks | Parallel |
|-------|-------|-------|----------|
| Phase 1: Setup | — | T001-T004 (4 tasks) | T003, T004 |
| Phase 2: Foundational | — | T005-T007 (3 tasks) | T006, T007 |
| Phase 3: US1 Vault Setup | P1 | T008-T012 (5 tasks) | T012 |
| Phase 4: US2 Gmail Watcher | P2 | T013-T020 (8 tasks) | T020 |
| Phase 5: US3 Process Inbox | P3 | T021-T025 (5 tasks) | T025 |
| Phase 6: US4 Agent Skills | P4 | T026-T029 (4 tasks) | T027 |
| Phase 7: Polish | — | T030-T034 (5 tasks) | T030, T031, T032, T033 |
| **Total** | | **34 tasks** | |
