---
id: 004
title: Implement Gold Tier Autonomous Employee
stage: green
date: 2026-02-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: 003-gold-tier-autonomous
branch: 003-phase3-ai-chatbot
user: developer
command: /sp.implement
labels: ["gold-tier", "implementation", "odoo", "social-media", "ralph-wiggum", "mcp", "ceo-briefing", "audit-logging", "error-recovery"]
links:
  spec: specs/003-gold-tier-autonomous/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - src/mcp/tools/odoo_client.py
  - src/mcp/tools/odoo_invoice.py
  - src/mcp/tools/odoo_payment.py
  - src/mcp/tools/odoo_reports.py
  - src/mcp/mcp_accounting.py
  - src/mcp/tools/facebook_post.py
  - src/mcp/tools/instagram_post.py
  - src/mcp/tools/x_post.py
  - src/mcp/tools/social_summary.py
  - src/mcp/mcp_social.py
  - src/mcp/mcp_communications.py
  - src/mcp/router.py
  - src/briefing/briefing_generator.py
  - src/templates/briefing_template.md
  - src/reasoning/ralph_wiggum.py
  - src/recovery/retry.py
  - src/logging/audit_logger.py
  - src/health/service_health.py
  - src/approval/checker.py
  - src/reasoning/classifier.py
  - src/scheduling/scheduler_config.json
  - src/scripts/setup_vault.py
  - docker-compose.gold.yml
  - .env.example
  - .gitignore
  - requirements.txt
  - README.md
  - .claude/skills/generate-briefing/SKILL.md
  - .claude/skills/ralph-wiggum/SKILL.md
  - .claude/skills/audit-report/SKILL.md
  - .claude/skills/odoo-accounting/SKILL.md
  - .claude/skills/generate-architecture/SKILL.md
  - .claude/skills/generate-social-post/SKILL.md
  - .claude/skills/check-approvals/SKILL.md
  - .claude/skills/run-pipeline/SKILL.md
  - tests/unit/test_retry.py
  - tests/unit/test_audit_logger.py
  - tests/unit/test_service_health.py
  - tests/unit/test_odoo_client.py
  - tests/unit/test_odoo_tools.py
  - tests/unit/test_briefing_generator.py
  - tests/unit/test_social_tools.py
  - tests/unit/test_ralph_wiggum.py
  - tests/integration/test_odoo_integration.py
  - tests/integration/test_briefing_flow.py
  - tests/integration/test_ralph_wiggum_flow.py
  - tests/integration/test_gold_pipeline.py
tests:
  - tests/unit/test_retry.py (12 tests)
  - tests/unit/test_audit_logger.py (14 tests)
  - tests/unit/test_service_health.py (15 tests)
  - tests/unit/test_odoo_client.py (9 tests)
  - tests/unit/test_odoo_tools.py (11 tests)
  - tests/unit/test_briefing_generator.py (16 tests)
  - tests/unit/test_social_tools.py (17 tests)
  - tests/unit/test_ralph_wiggum.py (24 tests)
  - tests/integration/test_odoo_integration.py (3 tests, skipped)
  - tests/integration/test_briefing_flow.py (2 tests)
  - tests/integration/test_ralph_wiggum_flow.py (4 tests)
  - tests/integration/test_gold_pipeline.py (4 tests)
outcome: success
evaluation: 74/74 tasks completed, 236 tests passing (128 new Gold tests), all acceptance criteria met
---

# Prompt

Implement Gold Tier of the "Personal AI Employee" project.

Instructions: Implement ALL Gold tasks from /sp.task, adhere to spec/plan/constitution. Build on Silver/Bronze. Generate files/code.

Context:
- Previous tiers ready.
- Use test Odoo, demo social posts.
- Add Ralph Wiggum via prompt loop.
- Weekly cron for Briefing.
- Log everything.

Rules:
* No Platinum/cloud.
* Safe demo (TEST_MODE=true).
* Output: Generated files, setup, demo steps (e.g., trigger audit).

Satisfy Gold: Autonomous multi-step, Odoo integrate, social summaries, weekly briefing, loop works.

# Response

## Implementation Summary

Completed ALL 74 Gold Tier tasks across 11 phases:

### Phase 1-2: Setup & Foundational (T001-T012)
- Docker Compose for Odoo v19 + PostgreSQL 16
- Retry decorator with exponential backoff (1s, 2s, 4s)
- Structured audit logger (5 categories, daily rotation)
- Service health tracker (operational → degraded → unavailable)

### Phase 3: Odoo Accounting (T013-T020)
- OdooClient with JSON-RPC at /jsonrpc endpoint
- Invoice create/list, payment record/list, financial summary
- MCP accounting server (6 tools) with stdio transport

### Phase 4: CEO Briefing (T021-T029)
- Briefing template with 5 sections and trend indicators
- Generator collecting from Odoo, audit logs, social activity, health
- Archival of previous briefings, graceful degradation

### Phase 5: Multi-Social (T030-T040)
- Facebook (Graph API), Instagram (2-step), X (Tweepy)
- Social engagement summary from vault/Done
- Social MCP server + communications MCP server
- Approval checker extended for 5 platform types

### Phase 6: Ralph Wiggum (T041-T047)
- Autonomous loop with parse_plan, classify_step, execute_step
- Max 10 iterations, 30 min timeout, nesting depth 2
- Approval draft creation for action steps
- TASK_COMPLETE / AWAITING_APPROVAL / LOOP_TIMEOUT states

### Phase 7: Multi-MCP Infrastructure (T048-T051)
- Router/registry for 3 servers with fault isolation
- Tool-to-server lookup across all registered servers

### Phase 8-9: Audit Integration & Error Recovery (T052-T063)
- Audit logging integrated into classifier, approval checker
- Service health tracking for all external services

### Phase 10-11: Documentation & Polish (T064-T074)
- 12 Claude Code skills (5 new Gold skills)
- Architecture documentation skill
- README updated with Gold architecture and setup

### Test Results
- **236 passed**, 3 skipped, 2 pre-existing Silver failures
- 128 new Gold tests covering all components
