---
id: 001
title: Create Silver Tier Specification
stage: spec
date: 2026-02-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: 002-silver-tier-assistant
branch: 002-silver-tier-assistant
user: human
command: /sp.specify
labels: ["silver-tier", "specification", "watchers", "mcp", "approval", "scheduling"]
links:
  spec: specs/002-silver-tier-assistant/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-silver-tier-assistant/spec.md
  - specs/002-silver-tier-assistant/checklists/requirements.md
tests:
  - N/A
---

## Prompt

Create the Silver Tier specification for the "Personal AI Employee" project, building directly on the completed Bronze Tier.

Silver Tier Scope (Functional Assistant):
* Extend Bronze foundation to make the AI a practical, multi-source assistant with basic external actions and human safety.
* Add multiple monitoring sources, planning, and controlled actions (e.g., sending with approval).
* Focus on making AI reactive and useful for personal/business tasks.

Required Features (Silver Level ONLY, extending Bronze):
1. Multiple Watchers: At least two (e.g., Gmail + WhatsApp OR LinkedIn mentions; use document templates like whatsapp_watcher.py with Playwright).
2. Claude Reasoning Loop: Automatically create Plan.md files with checkboxes for multi-step tasks when watcher triggers.
3. Automatic Social Posting: Generate and post on LinkedIn (or Mastodon as free alternative) about business to generate sales/leads.
4. One Working MCP Server: For external actions (e.g., sending emails or social posts; Node.js or Python MCP setup).
5. Human-in-the-Loop Approval Workflow: AI drafts actions in /Pending_Approval folder; user approves/edits/rejects via Obsidian checkbox before execution.
6. Basic Scheduling: Use cron or Task Scheduler to run watchers and Claude loops periodically (e.g., every 5-10 minutes).
7. All AI functionality implemented as Agent Skills (extend Bronze skills, e.g., new skills for planning, approval check, posting).

Specification must include:
* User Stories: E.g., "As a user, I want AI to monitor WhatsApp urgent messages and draft replies for approval."
* Updated Data Model: Plan.md with checkboxes, Pending_Approval.md with draft + approve checkbox.
* Interaction Flow: Watcher → Claude reasoning → Plan.md → Draft in Pending_Approval → Human approve → MCP execute.
* Acceptance Criteria: Multiple watchers trigger; Plan.md generated; Draft approved → real post/send (test with safe action); scheduling works.
* Error Cases: Watcher fail, approval missing, MCP error (graceful retry/log).

Strict Constraints:
* Build on Bronze: Reuse existing vault, single watcher, read/write.
* No full autonomy yet (no Odoo, no audits, no cloud).
* No Ralph Wiggum loop (add in Gold).
* Local-first, privacy: No secrets sync, human approval mandatory for sends.
* Comply with global constitution: No new features outside spec, history via logs.

This specification defines WHAT Silver Tier must deliver, evolving from Bronze foundation.

## Response snapshot

Created the Silver Tier Functional Assistant specification at `specs/002-silver-tier-assistant/spec.md` on branch `002-silver-tier-assistant`. The spec defines 7 prioritized user stories: (P1) WhatsApp Watcher, (P2) Claude Reasoning Loop with Plan.md generation, (P3) Human-in-the-Loop Approval Workflow, (P4) Social Media Posting via Mastodon, (P5) MCP Server for External Actions, (P6) Basic Scheduling, (P7) Extended Agent Skills. Includes 15 functional requirements (FR-001 through FR-015), 5 key entities (Plan Item, Approval Draft, MCP Action Log, Schedule Configuration, extended Vault Item), 8 measurable success criteria, 5 edge cases, explicit scope boundaries. Quality checklist passes all 16 items. No NEEDS CLARIFICATION markers — all requirements are concrete and testable.

## Outcome

- ✅ Impact: Silver Tier spec complete — 7 user stories, 15 FRs, 8 success criteria, all passing quality checklist
- 🧪 Tests: N/A (specification phase)
- 📁 Files: specs/002-silver-tier-assistant/spec.md, specs/002-silver-tier-assistant/checklists/requirements.md
- 🔁 Next prompts: `/sp.plan` to create the Silver Tier implementation plan
- 🧠 Reflection: Silver spec cleanly extends Bronze — reuses vault structure, adds /Pending_Approval folder, adds 4 new skills while preserving existing ones. Mastodon chosen over LinkedIn per constitution free-focus mandate. No NEEDS CLARIFICATION needed — user input was comprehensive.

## Evaluation notes (flywheel)

- Failure modes observed: None — manual branch/directory creation avoided PowerShell script issue
- Graders run and results (PASS/FAIL): Quality checklist PASS (16/16 items)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
