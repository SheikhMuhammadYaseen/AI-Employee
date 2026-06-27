---
id: 002
title: Create Gold Tier Technical Plan
stage: plan
date: 2026-02-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: 003-gold-tier-autonomous
branch: 003-gold-tier-autonomous
user: developer
command: /sp.plan
labels: ["gold-tier", "plan", "odoo", "social-media", "ralph-wiggum", "mcp", "ceo-briefing"]
links:
  spec: specs/003-gold-tier-autonomous/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-gold-tier-autonomous/plan.md
  - specs/003-gold-tier-autonomous/research.md
  - specs/003-gold-tier-autonomous/data-model.md
  - specs/003-gold-tier-autonomous/quickstart.md
  - specs/003-gold-tier-autonomous/contracts/mcp-accounting.md
  - specs/003-gold-tier-autonomous/contracts/mcp-social.md
  - specs/003-gold-tier-autonomous/contracts/mcp-communications.md
tests:
  - N/A (plan phase)
---

## Prompt

Create the Gold Tier technical plan for the Personal AI Employee Autonomous Employee, based strictly on Gold specification, global constitution, and previous tiers.

Plan describes HOW without new features.

1. High-Level Structure: Extend Silver with Odoo Docker/local + multiple MCP + social APIs + Ralph Wiggum loop + weekly cron.
2. Odoo Integration: Self-host Odoo Community, MCP server calls JSON-RPC for create invoice/payment/read reports.
3. Social Extensions: FB/IG via Graph API, X via v2 API (or Mastodon fallback); skills for post + summarize.
4. Multiple MCP: Separate servers/scripts (e.g., mcp_social.py, mcp_odoo.py).
5. CEO Briefing: Cron job weekly (Monday) triggers Claude to audit /Accounting + tasks → generate Briefing.md.
6. Ralph Wiggum Loop: Stop hook in Claude prompts (re-feed until "TASK_COMPLETE" or max iterations).
7. Error Recovery: Retries (exponential backoff), degradation (skip actions, log).
8. Logging: All to /Logs/gold_audit.md with timestamps.
9. Agent Skills: New for audit, Odoo calls, multi-social, loop management.
10. Documentation: /Docs/gold_architecture.md + lessons.md.

Constraints:
* Local/self-hosted only.
* Test safe (test Odoo DB, demo posts).
* Reuse Silver approval for sensitive.

Plan ensures full autonomy with safety.

## Response snapshot

Gold Tier technical plan created with 7 artifacts: plan.md (main implementation plan with architecture, 10 design decisions, 2 constitution checks — all PASS), research.md (10 research decisions: R1-Odoo Docker/JSON-RPC, R2-Meta Graph API, R3-X API v2/Tweepy, R4-Multiple MCP architecture, R5-Ralph Wiggum loop, R6-CEO Briefing, R7-Audit logging, R8-Error recovery, R9-Tweepy selection, R10-Docker Compose setup), data-model.md (9 entities: Odoo Invoice, Odoo Payment, Financial Summary, CEO Briefing, Social Post Extended, Engagement Summary, Ralph Wiggum Session, Audit Log Entry, Service Health Status), 3 MCP tool contracts (accounting: 6 tools, social: 6 tools, communications: 2 tools), and quickstart.md (11-step setup guide with demo walkthrough and troubleshooting).

## Outcome

- ✅ Impact: Complete Gold Tier technical plan — 10 design decisions, 10 research items, 9 data entities, 14 MCP tool contracts, 11-step quickstart
- 🧪 Tests: N/A (plan phase)
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md, contracts/mcp-accounting.md, contracts/mcp-social.md, contracts/mcp-communications.md
- 🔁 Next prompts: /sp.tasks for Gold Tier task breakdown
- 🧠 Reflection: Maintained clear separation between Silver carry-forward and Gold-new components; Docker Compose for Odoo simplifies setup significantly; three MCP servers provide clean fault isolation

## Evaluation notes (flywheel)

- Failure modes observed: Setup-plan script resolves wrong git root (known issue, bypassed with direct paths)
- Graders run and results (PASS/FAIL): Constitution Check 5/5 PASS (pre-design), 5/5 PASS (post-design)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
