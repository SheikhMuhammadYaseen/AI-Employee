---
id: 002
title: Create Bronze Tier Technical Plan
stage: plan
date: 2026-02-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-bronze-tier-foundation
branch: 001-bronze-tier-foundation
user: human
command: /sp.plan
labels: ["bronze-tier", "plan", "architecture", "vault", "watcher", "skills"]
links:
  spec: specs/001-bronze-tier-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-tier-foundation/plan.md
  - specs/001-bronze-tier-foundation/research.md
  - specs/001-bronze-tier-foundation/data-model.md
  - specs/001-bronze-tier-foundation/quickstart.md
  - specs/001-bronze-tier-foundation/contracts/skill-interfaces.md
tests:
  - N/A
---

## Prompt

Create the Bronze Tier technical plan for the Personal AI Employee foundation.

The plan is derived strictly from the Bronze Tier specification and global constitution. It describes HOW to implement the approved requirements without introducing new features.

1. High-Level Structure: Single Python watcher script + Obsidian vault + Claude Code integration.
2. Vault Design: Local Markdown files; Dashboard.md as YAML-frontmatter summary; Company_Handbook.md as rules list.
3. Watcher Implementation: Use base_watcher.py template; for Gmail: Google API with OAuth; create .md with YAML metadata (type, from, etc.).
4. Claude Code Flow: Point to vault folder; prompt to read /Needs_Action, process, write to Dashboard.md or /Done.
5. Agent Skills: Prompt Claude to generate SKILL.md files with reusable prompts (e.g., "Skill: Summarize Needs_Action").
6. Error Handling: Try/except in scripts; log to console or /Logs; graceful exit on failures.

Constraints:
* In-memory or local only; no persistence beyond files.
* No external actions beyond file write.
* No future concepts (e.g., no MCP, Ralph Wiggum yet).
* Reuse document examples (e.g., gmail_watcher.py code).

The plan ensures continuity and sets up for Silver Tier extension.

## Response snapshot

Created the Bronze Tier implementation plan with 5 artifacts:

1. **plan.md** — Main implementation plan covering technical context, constitution check (all 5 gates PASS), project structure (src/scripts, src/watchers, .claude/commands, vault, tests), Perception→Reasoning→Action architecture, 5 key design decisions, security considerations, and Silver Tier extension points.

2. **research.md** — 6 research decisions: R1 Gmail API pattern (google-api-python-client + OAuth2), R2 Vault item format (YAML frontmatter), R3 Watcher state (JSON file with 10K cap), R4 Skill architecture (Claude Code custom commands), R5 Dashboard strategy (full rewrite per run), R6 Lock file (PID-based cross-platform).

3. **data-model.md** — 4 entities with full field definitions: Vault Item (8 frontmatter fields), Dashboard (YAML header + Markdown body), Company Handbook (rules/preferences structure), Watcher State (JSON schema). Includes entity relationships and state transition diagram.

4. **quickstart.md** — 7-step setup guide: clone, install deps, Gmail OAuth, vault init, watcher run, process inbox, verify success criteria. Includes troubleshooting table.

5. **contracts/skill-interfaces.md** — Interface contracts for 3 skills (vault-read, vault-write, process-inbox) plus watcher CLI and setup script CLI. Each defines inputs, outputs, and error cases.

## Outcome

- ✅ Impact: Complete Bronze Tier technical plan — 5 artifacts, all constitution gates pass, architecture documented
- 🧪 Tests: N/A (planning phase, no code)
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md, contracts/skill-interfaces.md
- 🔁 Next prompts: `/sp.tasks` to generate the Bronze Tier task breakdown
- 🧠 Reflection: Plan stays strictly within Bronze scope — no MCP, no scheduling, no cloud. Skills implemented as Claude Code custom commands rather than Python scripts, keeping Perception (Python) and Reasoning (Claude) cleanly separated.

## Evaluation notes (flywheel)

- Failure modes observed: setup-plan.ps1 resolved git root to parent directory (E:\it practice) instead of aiemployee subdirectory; update-agent-context.ps1 failed for same reason. Worked around by creating artifacts manually.
- Graders run and results (PASS/FAIL): Constitution Check PASS (5/5 gates); all NEEDS CLARIFICATION resolved in research.md
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Fix git root detection in PowerShell scripts when working directory is a subdirectory of the git repo
