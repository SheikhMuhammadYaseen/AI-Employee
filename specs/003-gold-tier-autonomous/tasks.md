# Tasks: Gold Tier — Autonomous Employee

**Input**: Design documents from `specs/003-gold-tier-autonomous/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/
**Extends**: Silver Tier complete (48/48 tasks, 108 tests passing)

**Organization**: Tasks grouped by user story (P1-P8 from spec) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1-US8)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Gold Tier project setup — new dependencies, Docker, directory structure, shared utilities

- [x] T001 Install Gold Tier Python dependencies: `pip install tweepy requests` and verify existing Silver deps in requirements.txt
- [x] T002 Create docker-compose.gold.yml at project root for Odoo Community v19 + PostgreSQL 16 per research.md R10
- [x] T003 Create Gold Tier directory structure: `src/briefing/`, `src/logging/`, `src/health/`, `src/recovery/` with `__init__.py` files
- [x] T004 Update .env.example with Gold Tier variables: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD, META_PAGE_ACCESS_TOKEN, META_PAGE_ID, META_IG_USER_ID, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
- [x] T005 [P] Update .gitignore with Gold patterns: docker volumes, .service_health.json, Briefing.md, odoo session files
- [x] T006 [P] Update requirements.txt with all Gold Tier dependencies (tweepy, requests added to existing)

**Checkpoint**: Gold infrastructure ready — Docker Compose file exists, directories created, dependencies installable

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cross-cutting modules that ALL user stories depend on — retry, audit logging, service health

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Create retry decorator with exponential backoff in src/recovery/retry.py — @retry(max_attempts=3, backoff_base=1, backoff_factor=2) per research.md R8
- [x] T008 Create structured audit logger in src/logging/audit_logger.py — log_action(category, action, details) writing to vault/Logs/<category>-<YYYY-MM-DD>.md per data-model.md Audit Log Entry
- [x] T009 Create service health tracker in src/health/service_health.py — update_health(service, success), get_health(service), get_all_health() reading/writing vault/.service_health.json per data-model.md Service Health Status
- [x] T010 Write unit tests for retry decorator in tests/unit/test_retry.py — test backoff timing, max attempts, exception types, success on retry
- [x] T011 [P] Write unit tests for audit logger in tests/unit/test_audit_logger.py — test log entry format, daily rotation, category files, sanitization
- [x] T012 [P] Write unit tests for service health in tests/unit/test_service_health.py — test status transitions (operational→degraded→unavailable→operational), JSON persistence

**Checkpoint**: Foundation ready — retry, logging, and health modules tested and available for all stories

---

## Phase 3: User Story 1 — Odoo Accounting Integration (Priority: P1) MVP

**Goal**: Connect to local Odoo via JSON-RPC. Create invoices, record payments, pull financial summaries.

**Independent Test**: Invoke create_invoice MCP tool → verify invoice in Odoo → pull financial summary including new invoice.

### Implementation for User Story 1

- [x] T013 [US1] Create Odoo JSON-RPC client in src/mcp/tools/odoo_client.py — OdooClient class with authenticate(), execute_kw(), health_check() per research.md R1
- [x] T014 [US1] Create invoice tool in src/mcp/tools/odoo_invoice.py — create_invoice(partner_name, invoice_date, due_date, lines) and list_invoices(filters) per contracts/mcp-accounting.md
- [x] T015 [US1] Create payment tool in src/mcp/tools/odoo_payment.py — record_payment(invoice_id, amount, payment_date, journal) and list_payments(filters) per contracts/mcp-accounting.md
- [x] T016 [US1] Create financial reports tool in src/mcp/tools/odoo_reports.py — get_financial_summary(start_date, end_date) aggregating revenue, expenses, receivables per contracts/mcp-accounting.md
- [x] T017 [US1] Create accounting MCP server in src/mcp/mcp_accounting.py — register all Odoo tools + health_check using mcp SDK with stdio transport
- [x] T018 [US1] Write unit tests for Odoo client in tests/unit/test_odoo_client.py — mock JSON-RPC responses for auth, execute_kw, connection errors
- [x] T019 [P] [US1] Write unit tests for Odoo tools in tests/unit/test_odoo_tools.py — mock OdooClient for invoice create/list, payment record/list, financial summary
- [x] T020 [US1] Write integration test for Odoo in tests/integration/test_odoo_integration.py — requires Docker Odoo running; create invoice, record payment, verify summary

**Checkpoint**: Odoo accounting fully operational via MCP — invoices, payments, reports working against Docker instance

---

## Phase 4: User Story 2 — Weekly CEO Briefing with Audit (Priority: P2)

**Goal**: Auto-generate Monday morning Briefing.md with Financial Summary, Operational Status, Social Activity, Bottlenecks, Actions.

**Independent Test**: Trigger briefing skill manually → verify Briefing.md created with all 5 sections populated from Odoo test data and vault logs.

**Depends on**: US1 (Odoo data for Financial Summary), Phase 2 (audit logs for Operational Status)

### Implementation for User Story 2

- [x] T021 [US2] Create briefing template in src/templates/briefing_template.md — 5-section structure with trend indicator placeholders per data-model.md CEO Briefing
- [x] T022 [US2] Create briefing generator in src/briefing/briefing_generator.py — collect_financial_data(), collect_operational_data(), collect_social_data(), detect_bottlenecks(), generate_briefing() per plan.md D4
- [x] T023 [US2] Implement trend calculation in src/briefing/briefing_generator.py — compare current vs previous week metrics, return up/down/stable per spec FR-005
- [x] T024 [US2] Implement briefing archival: move previous Briefing.md to vault/Done/briefing-<date>.md before generating new one
- [x] T025 [US2] Create CEO briefing agent skill in .claude/skills/generate-briefing/SKILL.md — invoke briefing generator, handle partial data, report results
- [x] T026 [US2] Extend scheduler in src/scheduling/scheduler.py — add weekly Monday check (weekday==0, hour 6-9) to trigger briefing_generator per research.md R6
- [x] T027 [US2] Update scheduler_config.json — add briefing_generator component with weekly schedule and enabled flag
- [x] T028 [US2] Write unit tests for briefing generator in tests/unit/test_briefing_generator.py — test each section generation, trend calculation, graceful degradation when sources unavailable
- [x] T029 [US2] Write integration test for briefing in tests/integration/test_briefing_flow.py — generate full briefing with mock Odoo data and real vault logs

**Checkpoint**: Weekly briefing auto-generates with all 5 sections — financial, operational, social, bottlenecks, actions

---

## Phase 5: User Story 3 — Multi-Social Media Posting and Summaries (Priority: P3)

**Goal**: Post to Facebook/Instagram and X in addition to Mastodon. Generate weekly engagement summaries.

**Independent Test**: Create social post draft → approve → verify published to test accounts on each platform → verify engagement summary includes new post.

### Implementation for User Story 3

- [x] T030 [P] [US3] Create Facebook posting tool in src/mcp/tools/facebook_post.py — post_to_facebook(message, page_id, access_token) using Meta Graph API per contracts/mcp-social.md and research.md R2
- [x] T031 [P] [US3] Create Instagram posting tool in src/mcp/tools/instagram_post.py — post_to_instagram(caption, image_url, ig_user_id, access_token) using Meta Graph API two-step process per contracts/mcp-social.md
- [x] T032 [P] [US3] Create X posting tool in src/mcp/tools/x_post.py — post_to_x(text) using Tweepy with 280-char pre-validation per contracts/mcp-social.md and research.md R3/R9
- [x] T033 [US3] Create social engagement summary tool in src/mcp/tools/social_summary.py — social_engagement_summary(start_date, end_date) scanning Done folder + platform APIs per contracts/mcp-social.md
- [x] T034 [US3] Create social MCP server in src/mcp/mcp_social.py — register mastodon_post (migrated from Silver server.py), facebook_post, instagram_post, x_post, social_engagement_summary, health_check
- [x] T035 [US3] Migrate mastodon_post from Silver's server.py to mcp_social.py — move tool registration, keep src/mcp/tools/mastodon_post.py unchanged
- [x] T036 [US3] Rename Silver's src/mcp/server.py to src/mcp/mcp_communications.py — update email_send registration, add health_check tool per plan.md D7
- [x] T037 [US3] Update src/approval/checker.py — extend platform routing to handle facebook-post, instagram-post, x-post approval types in addition to existing email-send, mastodon-post
- [x] T038 [US3] Update .claude/skills/generate-social-post/SKILL.md — add multi-platform targeting with per-platform content adaptation (char limits: X=280, Mastodon=500) per spec FR-008
- [x] T039 [P] [US3] Write unit tests for social tools in tests/unit/test_social_tools.py — mock Graph API and Tweepy for FB/IG/X posting, char limit validation, error handling
- [x] T040 [US3] Update .claude/skills/check-approvals/SKILL.md — document multi-platform approval types

**Checkpoint**: Social posts publishable to 5 platforms (LinkedIn, Mastodon, Facebook, Instagram, X) through single approval workflow

---

## Phase 6: User Story 4 — Ralph Wiggum Autonomous Task Loop (Priority: P4)

**Goal**: Autonomously iterate through Plan.md steps — complete simple actions, create approval drafts for action steps, re-check after approvals.

**Independent Test**: Create Plan.md with 5 steps (3 simple, 2 action-required) → start loop → simple steps auto-complete, action steps create drafts, loop pauses → approve drafts → loop resumes and completes.

**Depends on**: US3 (social MCP for action steps), US1 (accounting MCP for action steps), Phase 2 (audit logging)

### Implementation for User Story 4

- [x] T041 [US4] Create Ralph Wiggum loop engine in src/reasoning/ralph_wiggum.py — RalphWiggumLoop class with parse_plan(), classify_step(), execute_step(), create_approval_draft(), check_approvals(), run_iteration() per research.md R5
- [x] T042 [US4] Implement iteration limits in src/reasoning/ralph_wiggum.py — max 10 iterations, max 30 minutes, nesting depth max 2 per spec FR-013
- [x] T043 [US4] Implement Plan.md frontmatter tracking in src/reasoning/ralph_wiggum.py — update loop_status, loop_iteration, steps_completed, steps_awaiting_approval per data-model.md Ralph Wiggum Session
- [x] T044 [US4] Implement loop logging — each iteration writes to vault/Logs/loop-<date>.md via audit_logger per spec FR-014
- [x] T045 [US4] Create Ralph Wiggum agent skill in .claude/skills/ralph-wiggum/SKILL.md — orchestrate loop: accept Plan.md path, invoke ralph_wiggum.py, report progress, handle TASK_COMPLETE/LOOP_TIMEOUT
- [x] T046 [US4] Write unit tests for Ralph Wiggum in tests/unit/test_ralph_wiggum.py — test step parsing, classification, iteration limits, timeout, approval draft creation, nesting depth enforcement
- [x] T047 [US4] Write integration test for Ralph Wiggum in tests/integration/test_ralph_wiggum_flow.py — create test Plan.md with mixed steps, run loop, verify completion and approval draft creation

**Checkpoint**: Ralph Wiggum loop completes multi-step plans autonomously with approval gates and enforced limits

---

## Phase 7: User Story 5 — Multiple MCP Servers (Priority: P5)

**Goal**: Three independent MCP servers (social, accounting, communications) with fault isolation and independent restart.

**Independent Test**: Start all three servers → invoke one tool on each → verify success. Stop accounting server → invoke social post → verify it still works.

**Note**: The individual MCP servers are created in US1 (accounting) and US3 (social, communications). This phase handles the multi-server infrastructure.

### Implementation for User Story 5

- [x] T048 [US5] Create MCP server router/registry in src/mcp/router.py — register_server(), get_server_status(), health_check_all() per plan.md D2
- [x] T049 [US5] Update Claude Code MCP configuration in .claude/settings.json or project MCP config — register all three servers (gold-social, gold-accounting, gold-communications) per quickstart.md step 7
- [x] T050 [US5] Implement graceful failure handling in src/mcp/router.py — if one server down, others continue; log which server failed per spec FR-010/FR-011
- [x] T051 [US5] Add health_check tool to each MCP server (mcp_social.py, mcp_accounting.py, mcp_communications.py) per contracts

**Checkpoint**: Three MCP servers independently operational with fault isolation verified

---

## Phase 8: User Story 6 — Comprehensive Audit Logging (Priority: P6)

**Goal**: Every significant agent action logged in searchable audit trail with daily rotation.

**Independent Test**: Trigger several agent actions (classify, approve, loop iteration) → verify corresponding log entries in vault/Logs/ with correct metadata.

**Note**: The audit_logger module is created in Phase 2 (T008). This phase integrates it across all components.

### Implementation for User Story 6

- [x] T052 [US6] Integrate audit logging into approval checker — log approval transitions (created, approved, rejected, executed, failed) to vault/Logs/approval-<date>.md in src/approval/checker.py
- [x] T053 [P] [US6] Integrate audit logging into classifier — log classification decisions to vault/Logs/classification-<date>.md in src/reasoning/classifier.py
- [x] T054 [P] [US6] Integrate audit logging into all MCP tools — log every invocation to vault/Logs/mcp-<date>.md with server name, tool name, sanitized params, result, duration
- [x] T055 [US6] Integrate audit logging into scheduler — log each run to vault/Logs/scheduler-<date>.md (extend existing Silver log format) in src/scheduling/scheduler.py
- [x] T056 [US6] Create audit report agent skill in .claude/skills/audit-report/SKILL.md — query logs by date/category, generate formatted summary
- [x] T057 [US6] Implement weekly log summary function in src/logging/audit_logger.py — summarize_week(start, end) scanning all category files, counting by result, identifying error patterns for CEO Briefing

**Checkpoint**: 100% of MCP invocations, classifications, approvals, loop iterations, and scheduler runs captured in structured audit logs

---

## Phase 9: User Story 7 — Error Recovery and Graceful Degradation (Priority: P7)

**Goal**: Automatic retry for transient failures, graceful degradation when services unavailable, service health tracking visible in Dashboard.

**Independent Test**: Disable Odoo → run scheduler → verify non-accounting tasks complete normally → verify Odoo failure logged → verify Dashboard shows Odoo unavailable.

**Note**: The retry decorator and service health modules are created in Phase 2 (T007, T009). This phase integrates them.

### Implementation for User Story 7

- [x] T058 [US7] Wrap all Odoo JSON-RPC calls with @retry decorator in src/mcp/tools/odoo_client.py — 3 retries, exponential backoff, update service health on each attempt
- [x] T059 [P] [US7] Wrap all social API calls with @retry in src/mcp/tools/facebook_post.py, instagram_post.py, x_post.py, mastodon_post.py
- [x] T060 [P] [US7] Wrap email SMTP calls with @retry in src/mcp/tools/email_send.py
- [x] T061 [US7] Implement Dashboard health status update — scheduler reads .service_health.json and updates Dashboard.md with service status table per spec FR-018
- [x] T062 [US7] Implement 1-hour alert flag — if service unavailable > 1 hour, add warning flag to Dashboard.md per spec FR-018
- [x] T063 [US7] Update scheduler to handle component failures gracefully — if one component fails, continue with others, log failure per spec FR-017

**Checkpoint**: System continues operating when individual services fail; health visible in Dashboard; retries succeed on transient errors

---

## Phase 10: User Story 8 — Architecture Documentation (Priority: P8)

**Goal**: Generate and maintain Architecture.md and Lessons_Learned.md in the vault.

**Independent Test**: Invoke documentation skill → verify Architecture.md and Lessons_Learned.md created with accurate system description.

### Implementation for User Story 8

- [x] T064 [US8] Create Architecture.md documentation skill in .claude/skills/generate-architecture/SKILL.md — generate vault/Architecture.md with component diagram, data flows, MCP topology, integration points per spec US8
- [x] T065 [US8] Create initial vault/Architecture.md — Gold Tier system design document reflecting current plan.md architecture
- [x] T066 [US8] Create initial vault/Lessons_Learned.md — document operational insights from Bronze/Silver/Gold development
- [x] T067 [US8] Create Odoo accounting agent skill in .claude/skills/odoo-accounting/SKILL.md — natural language interface for Odoo operations (create invoice, check payments, get summary)

**Checkpoint**: Architecture and lessons learned documentation accurately reflects Gold Tier system state

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing, scheduler updates, README, final validation

- [x] T068 Extend src/scripts/setup_vault.py — ensure Gold vault directories created (Logs subdirectories, Briefing archival in Done)
- [x] T069 Update src/scheduling/scheduler_config.json — add all Gold components (mcp_accounting health check, mcp_social health check, briefing_generator weekly, audit log rotation)
- [x] T070 Update .claude/skills/run-pipeline/SKILL.md — extend Silver pipeline skill with Gold components (multi-MCP health checks, audit logging, Ralph Wiggum orchestration)
- [x] T071 Write integration test for full Gold pipeline in tests/integration/test_gold_pipeline.py — end-to-end: watcher→classify→plan→ralph-wiggum→approve→execute→log→briefing
- [x] T072 Update README.md with Gold Tier documentation — architecture diagram, setup instructions, demo steps, test count, tier progression
- [x] T073 Verify all tests pass: run `pytest tests/ -v` and confirm Gold + Silver tests all green
- [x] T074 Run Gold Tier demo end-to-end: Odoo invoice→payment→briefing→social post→Ralph Wiggum loop→audit log review

**Checkpoint**: Gold Tier fully operational — all acceptance criteria from spec met, demo-safe, documented

---

## Dependencies

```text
Phase 1 (Setup)
  └─> Phase 2 (Foundational: retry, logging, health)
        └─> Phase 3 (US1: Odoo Accounting) ──────────┐
        └─> Phase 5 (US3: Multi-Social) ─────────────┤
              └─> Phase 4 (US2: CEO Briefing) ◄───────┤ (needs Odoo + Social data)
              └─> Phase 6 (US4: Ralph Wiggum) ◄───────┤ (needs MCP tools for actions)
        └─> Phase 7 (US5: Multi-MCP Infra) ◄──────────┘ (servers created in US1/US3)
        └─> Phase 8 (US6: Audit Integration) ──── can start after Phase 2
        └─> Phase 9 (US7: Error Recovery Integration) ── can start after Phase 2
        └─> Phase 10 (US8: Documentation) ──── can start anytime
              └─> Phase 11 (Polish) ◄─── all phases complete
```

## Parallel Execution Opportunities

| Tasks | Can Run In Parallel | Reason |
|-------|-------------------|--------|
| T005, T006 | Yes | Different files (.gitignore vs requirements.txt) |
| T010, T011, T012 | Yes | Different test files, no shared state |
| T030, T031, T032 | Yes | Different social platform tools, independent files |
| T039, T019 | Yes | Different test files |
| T052, T053, T054 | Partial | T053 and T054 parallel; T052 sequential (modifies checker.py) |
| T058, T059, T060 | Partial | T059 and T060 parallel; T058 sequential (modifies odoo_client.py) |

## Implementation Strategy

1. **MVP (Phase 1-3)**: Setup + Foundational + Odoo Accounting = demonstrate core Gold capability
2. **Social Extension (Phase 5)**: Add multi-platform posting = complete social media manager
3. **Autonomy (Phase 4, 6)**: CEO Briefing + Ralph Wiggum = autonomous employee behavior
4. **Infrastructure (Phase 7, 8, 9)**: Multi-MCP, audit integration, error recovery = production-grade reliability
5. **Documentation (Phase 10)**: Architecture + lessons learned = knowledge capture
6. **Polish (Phase 11)**: Integration tests, README, demo = tier completion

**Total Tasks**: 74
**Per User Story**: US1=8, US2=9, US3=11, US4=7, US5=4, US6=6, US7=6, US8=4
**Setup/Foundational**: 12
**Polish**: 7
