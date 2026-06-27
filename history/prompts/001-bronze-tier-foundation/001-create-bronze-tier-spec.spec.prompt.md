---
id: 001
title: Create Bronze Tier Spec
stage: spec
date: 2026-02-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-bronze-tier-foundation
branch: 001-bronze-tier-foundation
user: human
command: /sp.specify
labels: ["bronze-tier", "specification", "foundation", "vault", "watcher"]
links:
  spec: specs/001-bronze-tier-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-tier-foundation/spec.md
  - specs/001-bronze-tier-foundation/checklists/requirements.md
tests:
  - N/A
---

## Prompt

Create the Bronze Tier specification for the "Personal AI Employee" project.

Bronze Tier Scope (Foundation - Minimum Viable Deliverable):
* Basic local setup for an AI agent that monitors a single source and interacts with Obsidian vault.
* No advanced actions, integrations, or autonomy beyond simple read/write.
* Focus on establishing the core architecture: Brain (Claude Code), Memory (Obsidian), Senses (one watcher).

Required Features (Basic Level ONLY):
1. Obsidian Vault Setup: Dashboard.md for summaries, Company_Handbook.md for rules, basic folders (/Inbox, /Needs_Action, /Done).
2. Single Watcher Script: Monitor one source (e.g., Gmail or file system) and create .md files in /Needs_Action on changes.
3. Claude Code Interaction: Read from vault (/Needs_Action), write to vault (e.g., update Dashboard.md or create report in /Done).
4. Agent Skills: Implement all AI functionality as reusable skills (e.g., read/write skill).

Specification must include:
* Clear user stories: E.g., "As a user, I want a watcher to detect new emails so that tasks are flagged."
* Data Model: .md file format (type, from, subject, content, suggested actions).
* Interaction Flow: Watcher triggers → Claude command → Vault update.
* Acceptance Criteria: Watcher creates file on test input; Claude successfully reads/writes; no errors in basic run.
* Error Cases: Invalid credentials, no new items, file write failures.

Strict Constraints:
* No multiple watchers or integrations (e.g., no WhatsApp, social).
* No MCP actions or sending (only local file ops).
* No scheduling, loops, or audits.
* No references to higher tiers (e.g., no Odoo, cloud).
* Comply with global constitution: Local-first, privacy-focused.

This specification complies with the global constitution and defines WHAT Bronze Tier must deliver, evolving the project foundation.

## Response snapshot

Created the Bronze Tier Foundation specification at `specs/001-bronze-tier-foundation/spec.md` on branch `001-bronze-tier-foundation`. The spec defines 4 prioritized user stories: (P1) Obsidian Vault Setup, (P2) Single Gmail Watcher, (P3) Claude Code Read/Write Processing, (P4) Reusable Agent Skills. Includes 10 functional requirements (FR-001 through FR-010), 4 key entities (Vault Item, Dashboard, Company Handbook, Watcher State), 6 measurable success criteria, 5 edge cases, explicit scope boundaries (in-scope and out-of-scope per constitution), and documented assumptions. Quality checklist at `checklists/requirements.md` passes all validation items. No NEEDS CLARIFICATION markers — all requirements are concrete and testable. Spec is ready for `/sp.plan`.

## Outcome

- ✅ Impact: Bronze Tier spec complete — 4 user stories, 10 FRs, 6 success criteria, all passing quality checklist
- 🧪 Tests: N/A (specification phase, no code)
- 📁 Files: specs/001-bronze-tier-foundation/spec.md, specs/001-bronze-tier-foundation/checklists/requirements.md
- 🔁 Next prompts: `/sp.plan` to create the Bronze Tier implementation plan
- 🧠 Reflection: User input was highly detailed — allowed zero NEEDS CLARIFICATION markers. Constitution constraints (Gmail, Python, Obsidian, Claude Code) are architectural mandates, not implementation leakage.

## Evaluation notes (flywheel)

- Failure modes observed: PowerShell create-new-feature.ps1 script failed on positional argument parsing with long multiline descriptions; manually created branch and directories.
- Graders run and results (PASS/FAIL): Quality checklist PASS (all 16/16 items)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test create-new-feature.ps1 with simpler single-line descriptions to verify script works for future features
