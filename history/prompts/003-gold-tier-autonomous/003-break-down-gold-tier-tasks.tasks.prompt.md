---
id: 003
title: Break Down Gold Tier Tasks
stage: tasks
date: 2026-02-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: 003-gold-tier-autonomous
branch: 003-gold-tier-autonomous
user: developer
command: /sp.tasks
labels: ["gold-tier", "tasks", "breakdown", "odoo", "social-media", "ralph-wiggum", "mcp", "ceo-briefing"]
links:
  spec: specs/003-gold-tier-autonomous/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-gold-tier-autonomous/tasks.md
tests:
  - N/A (task generation phase)
---

## Prompt

Break the Gold Tier technical plan into atomic implementation tasks, building on Silver/Bronze.

Tasks (include ID, Description, Preconditions, Output, Artifacts, References):

1. Task ID: GOLD-01 — Setup Odoo Community local (Docker or install) and test JSON-RPC.
2. Task ID: GOLD-02 — Create MCP server for Odoo actions (invoice create/read).
3. Task ID: GOLD-03 — Integrate FB/IG and X APIs for posting + summary generation.
4. Task ID: GOLD-04 — Implement Ralph Wiggum loop in Claude prompts for multi-step.
5. Task ID: GOLD-05 — Build weekly audit/CEO Briefing generation (cron + Claude).
6. Task ID: GOLD-06 — Add error recovery, logging, graceful degradation.
7. Task ID: GOLD-07 — Extend Agent Skills and documentation.

Rules: Sequential, no Platinum, demo-safe.

## Response snapshot

Gold Tier tasks.md generated with 74 atomic tasks across 11 phases: Phase 1 Setup (6 tasks), Phase 2 Foundational (6 tasks — retry, audit logging, service health), Phases 3-10 mapping to 8 user stories (US1: Odoo Accounting 8 tasks, US2: CEO Briefing 9 tasks, US3: Multi-Social 11 tasks, US4: Ralph Wiggum 7 tasks, US5: Multi-MCP 4 tasks, US6: Audit Integration 6 tasks, US7: Error Recovery 6 tasks, US8: Documentation 4 tasks), Phase 11 Polish (7 tasks). All tasks follow strict checklist format with IDs (T001-T074), [P] parallel markers, [US] story labels, and exact file paths. Dependency graph and parallel execution opportunities documented.

## Outcome

- ✅ Impact: 74 atomic tasks organized by user story — immediately executable by LLM without additional context
- 🧪 Tests: N/A (task generation phase)
- 📁 Files: tasks.md
- 🔁 Next prompts: /sp.implement for Gold Tier implementation
- 🧠 Reflection: Mapped 7 high-level GOLD tasks to 74 atomic tasks with clear file paths; foundational modules (retry, logging, health) extracted to Phase 2 to unblock all user stories; MVP path is Phases 1-3 (Odoo accounting)

## Evaluation notes (flywheel)

- Failure modes observed: check-prerequisites script returns wrong paths (known issue, bypassed)
- Graders run and results (PASS/FAIL): Format validation — all 74 tasks follow checklist format with checkbox, ID, labels, file paths
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
