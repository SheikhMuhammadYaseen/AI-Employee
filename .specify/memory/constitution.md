<!--
  SYNC IMPACT REPORT
  ==================================================
  Version change: 0.0.0 (template) → 1.0.0 (initial ratification)
  Bump rationale: MAJOR — first concrete constitution replacing
  all template placeholders. No prior version existed.

  Modified principles:
  - [PRINCIPLE_1] → I. Spec-Driven Development
  - [PRINCIPLE_2] → II. Agent Behavior Rules
  - [PRINCIPLE_3] → III. Tier Governance
  - [PRINCIPLE_4] → IV. Technology Constraints
  - [PRINCIPLE_5] → V. Quality Principles

  Added sections:
  - Principle VI removed (user specified exactly 5 principles)
  - Section 2: "Tier Scope Reference" (new)
  - Section 3: "Amendment Procedure" (new)
  - Governance fully populated

  Removed sections:
  - Template PRINCIPLE_6 slot (user specified 5 principles)

  Templates requiring updates:
  - .specify/templates/plan-template.md — Constitution Check section
    references generic gates; ⚠ pending manual alignment with
    5-principle structure once first feature plan is created.
  - .specify/templates/spec-template.md — No structural conflict; ✅ OK
  - .specify/templates/tasks-template.md — No structural conflict; ✅ OK

  Follow-up TODOs: None. All placeholders resolved.
  ==================================================
-->
# Personal AI Employee Constitution

## Core Principles

### I. Spec-Driven Development

- All development MUST follow the strict workflow:
  Constitution → Specs → Plan → Tasks → Implement. No exceptions.
- No agent may write code, generate files, or perform actions without
  approved specs and tasks derived from them.
- Specifications define WHAT to build; Plans define HOW; Tasks break
  work into atomic steps; Implementation executes only those tasks.
- Refinements or changes MUST occur at the spec level first, triggering
  updates to plans and tasks. No ad-hoc modifications during
  implementation.
- Use Spec Kit commands (`/sp.specify`, `/sp.plan`, `/sp.tasks`,
  `/sp.implement`) to enforce this process, with history tracking via
  Obsidian logs or state files for smooth workflow across tiers.
- Each tier's output (files, scripts, configs) becomes input for the
  next, ensuring evolutionary progression without reinvention.

### II. Agent Behavior Rules

- **No manual coding by humans**: All code generation, skills, and
  implementations MUST be prompted through Claude Code or equivalent
  AI tools.
- **No feature invention**: Agents MUST NOT add unapproved features,
  even if perceived as "helpful." Stick strictly to the current
  tier's specs.
- **No deviation from approved specifications**: If ambiguity arises,
  clarify via `/sp.clarify` command before proceeding.
- **Human-in-the-loop for sensitive actions**: All approvals (sending
  emails, social posts, external API calls) require explicit human
  review in Obsidian before execution.
- **Proactive but controlled**: Agents use Ralph Wiggum Stop Hook to
  iterate until tasks are complete, but only within spec boundaries.
- **History and audit**: Every step MUST log to the Obsidian `/Logs`
  folder, including prompts, outputs, and decisions, to track what
  happened before for future tiers.

### III. Tier Governance

- The project is divided into four tiers, each strictly scoped by its
  specification:
  - **Bronze**: Foundation (basic vault + watcher + read/write)
  - **Silver**: Functional Assistant (extends Bronze watchers)
  - **Gold**: Autonomous Employee (full integrations + audits + Odoo)
  - **Platinum**: Always-On Cloud + Local Executive
- No future-tier features may leak into earlier tiers (e.g., no cloud
  in Bronze, no Odoo in Silver).
- Progression is evolutionary: each tier builds on the previous but
  MUST remain compatible with higher tiers.
- Tier completion criteria: fulfill all deliverables from the hackathon
  document for that tier.
- If a tier fails acceptance criteria, revert to spec refinement before
  re-implementing. No partial promotions.

### IV. Technology Constraints

- **Brain/Reasoning**: Claude Code (primary), with Ralph Wiggum Stop
  Hook for iteration.
- **Memory/GUI**: Obsidian (local Markdown vault for dashboard, plans,
  logs, approvals).
- **Senses/Perception**: Lightweight Python scripts (watchers) for
  monitoring (Gmail, WhatsApp, files, Mastodon API in higher tiers).
- **Hands/Actions**: Model Context Protocol (MCP) servers in Node.js
  or Python for external actions (email send, social posts).
- **Runtime**: Python 3.13+, Node.js v24+.
- **Source Control**: GitHub for vault sync.
- **ERP**: Odoo Community (Gold+ only).
- **Social**: Mastodon API (free alternative for X/LinkedIn
  integrations).
- **Local-First**: All data stays local; no cloud unless in Platinum.
  Privacy-focused: secrets (tokens, credentials) MUST NEVER be synced.
- **Free Focus**: Use free tiers exclusively (Oracle Cloud Free VM for
  Platinum, Mastodon over paid X API).
- **No Extras**: No unauthorized libraries; stick to document-approved
  tools (Playwright for WhatsApp, Google API for Gmail).

### V. Quality Principles

- **Clean Architecture**: Separation of concerns
  (Perception → Reasoning → Action), modular and testable code.
- **Privacy and Security**: Human approval for sensitive actions;
  secrets MUST NEVER be synced or exposed.
- **Autonomy with Safety**: Proactive (watchers wake agent), but
  graceful degradation on errors.
- **Scalability**: Design for exponential scaling (easy duplication
  in higher tiers).
- **Documentation**: All tiers MUST include architecture docs and
  lessons learned in Obsidian.
- **Testing**: Atomic tasks MUST include acceptance criteria; full
  tier demos required (e.g., Platinum: offline handling).
- **Cloud-Native Readiness** (Platinum+): Use Docker/Kubernetes if
  needed, but start simple.

## Tier Scope Reference

| Tier | Scope | Key Deliverables | Excluded |
|------|-------|-----------------|----------|
| **Bronze** | Foundation | Obsidian vault, file watcher, basic read/write MCP | Cloud, Odoo, social API |
| **Silver** | Functional Assistant | Extended watchers (Gmail, WhatsApp), task processing | Cloud, Odoo |
| **Gold** | Autonomous Employee | Full integrations, Odoo Community, audit trails, Mastodon | Cloud deployment |
| **Platinum** | Always-On Cloud + Local | Oracle Cloud VM, Docker, offline handling, full autonomy | — |

**Progression rule**: Each tier's artifacts (scripts, configs, MCP
servers) MUST be reusable as inputs for the next tier. No reinvention.

## Amendment Procedure

1. **Proposal**: Any amendment MUST be proposed as a spec-level change
   using `/sp.specify` with stage `constitution`.
2. **Review**: The proposer MUST document the rationale, affected
   principles, and downstream impacts (plans, tasks, templates).
3. **Approval**: Amendments require explicit human approval in Obsidian
   before taking effect.
4. **Propagation**: Upon approval, all dependent artifacts (plan
   templates, spec templates, task templates, command files) MUST be
   reviewed and updated for consistency within the same session.
5. **Versioning**: Constitution version follows semantic versioning:
   - **MAJOR**: Backward-incompatible governance/principle removals or
     redefinitions.
   - **MINOR**: New principle/section added or materially expanded
     guidance.
   - **PATCH**: Clarifications, wording, typo fixes, non-semantic
     refinements.
6. **Audit**: All amendments MUST be logged as PHRs in
   `history/prompts/constitution/` with full before/after diffs.

## Governance

This constitution is the supreme governing document for the Personal
AI Employee project. All agents, prompts, specs, plans, tasks, and
implementations MUST comply with these principles.

- **Supremacy**: This constitution supersedes all other practices,
  defaults, and conventions. In case of conflict, the constitution
  wins.
- **Compliance verification**: Every spec, plan, and task MUST include
  a Constitution Check gate verifying alignment with all five
  principles before implementation proceeds.
- **Violation response**: Any violation of this constitution triggers
  a full tier rollback to spec refinement. No exceptions.
- **Complexity justification**: Any deviation from the simplest viable
  approach MUST be documented with rationale in the relevant plan.
- **Runtime guidance**: Use `CLAUDE.md` for runtime development
  guidance and agent-specific behavior rules that complement (but
  never override) this constitution.

**Version**: 1.0.0 | **Ratified**: 2026-02-12 | **Last Amended**: 2026-02-12
