---
id: 001
title: Create Global Constitution
stage: constitution
date: 2026-02-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: 003-phase3-ai-chatbot
user: human
command: /sp.constitution
labels: ["constitution", "governance", "hackathon", "tier-governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A
---

## Prompt

Create a single global constitution for the entire "Personal AI Employee" hackathon project covering Bronze through Platinum Tiers.

This constitution serves as the supreme governing document for building an autonomous Digital FTE (Full-Time Equivalent) AI agent, as defined in the "Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026" document. It ensures structured, spec-driven development, maintains privacy and local-first principles, and prevents scope creep across tiers. All work must adhere to this constitution, which remains stable unless explicitly amended through a formal spec update process.

1. Spec-Driven Development
* All development follows the strict workflow: Constitution → Specs → Plan → Tasks → Implement. No exceptions.
* No agent may write code, generate files, or perform actions without approved specs and tasks derived from them.
* Specifications define WHAT to build; Plans define HOW; Tasks break it into atomic steps; Implementation executes only those tasks.
* Refinements or changes must occur at the spec level first, triggering updates to plans and tasks. No ad-hoc modifications during implementation.
* Use Spec Kit commands (/sp.specify, /sp.plan, /sp.task, /sp.implement) to enforce this process, with history tracking via Obsidian logs or state files for smooth workflow across tiers.
* Each tier's output (e.g., files, scripts) becomes input for the next, ensuring evolutionary progression without reinvention.

2. Agent Behavior Rules
* No manual coding by humans: All code generation, skills, and implementations must be prompted through Claude Code or equivalent AI tools.
* No feature invention: Agents must not add unapproved features, even if "helpful." Stick strictly to the current tier's specs.
* No deviation from approved specifications: If ambiguity arises, clarify via /sp.clarify command before proceeding.
* Human-in-the-loop for sensitive actions: All approvals (e.g., sending emails, posts) require explicit human review in Obsidian before execution.
* Proactive but controlled: Agents use Ralph Wiggum Stop Hook to iterate until tasks are complete, but only within spec boundaries.
* History and audit: Every step logs to Obsidian /Logs folder, including prompts, outputs, and decisions, to track what happened before for future tiers.

3. Tier Governance
* The project is divided into four tiers (Bronze: Foundation, Silver: Functional Assistant, Gold: Autonomous Employee, Platinum: Always-On Cloud + Local Executive), each strictly scoped by its specification.
* No future-tier features may leak into earlier tiers (e.g., no cloud in Bronze, no Odoo in Silver).
* Progression is evolutionary: Each tier builds on the previous (e.g., Silver extends Bronze watchers), but must remain compatible with higher tiers.
* Tier completion criteria: Fulfill all deliverables from the hackathon document (e.g., Bronze: basic vault + watcher + read/write; Gold: full integrations + audits).
* If a tier fails acceptance criteria, revert to spec refinement before re-implementing.

4. Technology Constraints
* Brain/Reasoning: Claude Code (primary), with Ralph Wiggum Stop Hook for iteration.
* Memory/GUI: Obsidian (local Markdown vault for dashboard, plans, logs, approvals).
* Senses/Perception: Lightweight Python scripts (watchers) for monitoring (e.g., Gmail, WhatsApp, files, Mastodon API for social in higher tiers).
* Hands/Actions: Model Context Protocol (MCP) servers in Node.js or Python for external actions (e.g., email send, social posts).
* Other Tools: Python 3.13+, Node.js v24+, GitHub for vault sync, Odoo Community (Gold+), Mastodon API (free alternative for social integrations like X/LinkedIn).
* Local-First: All data stays local; no cloud unless in Platinum. Privacy-focused: No syncing secrets (tokens, creds).
* Free Focus: Use free tiers (e.g., Oracle Cloud Free VM for Platinum, Mastodon over paid X API).
* No Extras: No unauthorized libraries; stick to document examples (e.g., Playwright for WhatsApp, Google API for Gmail).

5. Quality Principles
* Clean Architecture: Separation of concerns (Perception → Reasoning → Action), modular and testable code.
* Privacy and Security: Human approval for sensitive actions; secrets never synced or exposed.
* Autonomy with Safety: Proactive (watchers wake agent), but graceful degradation on errors.
* Scalability: Design for exponential scaling (e.g., easy duplication in higher tiers).
* Documentation: All tiers include architecture docs and lessons learned in Obsidian.
* Testing: Atomic tasks must include acceptance criteria; full tier demos required (e.g., Platinum: offline handling).
* Cloud-Native Readiness (Platinum+): Use Docker/Kubernetes if needed, but start simple.

This constitution governs all agents, prompts, and implementations. Violations trigger full tier rollback.

## Response snapshot

Created the global constitution for the Personal AI Employee hackathon project at `.specify/memory/constitution.md` (v1.0.0). The constitution codifies all 5 user-specified principles (Spec-Driven Development, Agent Behavior Rules, Tier Governance, Technology Constraints, Quality Principles) with MUST/MUST NOT language. Added Tier Scope Reference table, formal Amendment Procedure, and Governance section. Includes Sync Impact Report as HTML comment. All template placeholders resolved. Templates checked for consistency: spec and tasks templates OK, plan template flagged for future Constitution Check alignment.

## Outcome

- ✅ Impact: Constitution v1.0.0 ratified — supreme governing document for Bronze through Platinum tiers
- 🧪 Tests: N/A (governance document, not code)
- 📁 Files: .specify/memory/constitution.md (created/overwritten)
- 🔁 Next prompts: `/sp.specify` for first Bronze tier feature spec
- 🧠 Reflection: User provided comprehensive 5-principle input; mapped cleanly to template structure with one extra principle slot removed

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Manual validation PASS — no unresolved placeholders, dates ISO, principles declarative
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Align plan-template.md Constitution Check section with 5 concrete principles on first /sp.plan run
