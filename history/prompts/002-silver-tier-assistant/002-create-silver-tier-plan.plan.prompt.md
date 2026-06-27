---
id: 002
title: Create Silver Tier Technical Plan
stage: plan
date: 2026-02-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-silver-tier-assistant
branch: 002-silver-tier-assistant
user: human
command: /sp.plan
labels: ["silver-tier", "plan", "watchers", "mcp", "approval", "scheduling", "architecture"]
links:
  spec: specs/002-silver-tier-assistant/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-silver-tier-assistant/plan.md
  - specs/002-silver-tier-assistant/research.md
  - specs/002-silver-tier-assistant/data-model.md
  - specs/002-silver-tier-assistant/quickstart.md
  - specs/002-silver-tier-assistant/contracts/skill-interfaces.md
  - specs/002-silver-tier-assistant/contracts/mcp-tools.md
tests:
  - N/A (planning phase)
---

## Prompt

Create the Silver Tier technical plan for the Personal AI Employee Functional Assistant, based strictly on the Silver Tier specification, global constitution, and completed Bronze Tier.

The plan describes HOW to implement approved requirements without new features.

1. High-Level Structure: Extend Bronze vault + multiple Python watchers + Claude Code for reasoning + MCP server (Node.js/Python) for actions + scheduling.
2. Vault Extension: Add /Pending_Approval folder for drafts; Plan.md with checkboxes (YAML or Markdown list); /Logs for scheduling/errors.
3. Multiple Watchers: Use base_watcher.py template; Add WhatsApp Watcher (Playwright, keywords trigger) and/or LinkedIn (API if free, or Mastodon alternative); Trigger .md in /Needs_Action.
4. Claude Reasoning Loop: Prompt Claude "On new /Needs_Action file, create Plan.md with steps, then draft action in /Pending_Approval if needed."
5. MCP Server Setup: Simple Node.js/Python server for actions (e.g., send email via SMTP or social post via Mastodon.py); Integrate with Claude via file triggers.
6. Human Approval Workflow: Watcher/Claude draft → Obsidian checkbox approve; Approved file → MCP execute script (cron-triggered).
7. Scheduling: Cron jobs (Linux) or Task Scheduler (Windows) for watchers + periodic Claude "Check vault" command.
8. Agent Skills Extension: New skills for multi-watcher handling, plan creation, approval check, posting.
9. Error Handling: Retries in watchers/MCP, logs to /Logs/silver_errors.md.

Constraints:
* Reuse Bronze watcher/read-write.
* No Odoo/accounting, no weekly audits (Gold).
* No Ralph Wiggum (Gold).
* Test with safe actions (e.g., Mastodon test post, email to self).
* Local-only, free tools.

The plan ensures evolutionary continuity from Bronze to Silver.

## Response snapshot

Created the Silver Tier technical plan with 6 artifacts across `specs/002-silver-tier-assistant/`. The plan defines 10 key design decisions (D1-D10): base watcher class extraction, Playwright for WhatsApp, Mastodon.py for social posting, Python MCP server (not Node.js), three-way item classification, file-based approval workflow, per-watcher state files, OS-native scheduling via wrapper, Gmail SMTP for sending, and MCP action logging. Architecture extends Bronze's Perception→Reasoning→Action with a Safety Gate (Pending_Approval) and Scheduling layer. Research covers 8 technology decisions (R1-R8). Data model defines 7 entities (5 new + 2 extended from Bronze). Contracts specify 4 new skills, 2 MCP tools, WhatsApp watcher interface, base watcher class, approval checker, and scheduler. Constitution check: 5/5 PASS both pre-design and post-design.

## Outcome

- ✅ Impact: Silver Tier plan complete — 10 design decisions, 8 research findings, 7 entities, 6 skill/tool contracts, full architecture
- 🧪 Tests: N/A (planning phase)
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md, contracts/skill-interfaces.md, contracts/mcp-tools.md
- 🔁 Next prompts: `/sp.tasks` to break the Silver Tier plan into atomic implementation tasks
- 🧠 Reflection: Python-only stack decision (D4) simplifies Silver significantly — no Node.js runtime needed. Per-watcher state files (D7) cleanly solve the multi-watcher conflict risk. The Safety Gate architecture pattern (Pending_Approval as human checkpoint) is the key Silver innovation — it enables external actions while maintaining constitution-mandated human control.

## Evaluation notes (flywheel)

- Failure modes observed: Context window ran out during initial plan creation, requiring continuation in new session. `pages` parameter bug in Read tool required workaround (omit instead of empty string). PowerShell scripts still resolve to wrong git root.
- Graders run and results (PASS/FAIL): Constitution Check PASS (5/5 pre-design, 5/5 post-design)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
