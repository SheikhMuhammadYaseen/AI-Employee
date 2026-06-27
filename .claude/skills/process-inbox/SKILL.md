---
name: process-inbox
description: Orchestrate reading items from /Needs_Action, processing them with AI reasoning, writing reports to /Done, and updating Dashboard.md.
---

# Process Inbox
**Inputs**: None (operates on the configured vault at `vault/`)
**Outputs**: Summary of items processed, reports created in /Done, updated Dashboard.md
**Error Handling**: Skips malformed items, handles empty inbox, reports failures without crashing.
**Composition**: This skill orchestrates `/vault-read` (reading) and `/vault-write` (writing) patterns.

## Instructions

You are the AI Employee processing the inbox. Follow these steps precisely:

### Step 1: Read Company Handbook

Read `vault/Company_Handbook.md` to understand processing rules, preferences, and constraints.
Apply these rules to all processing below.

### Step 2: Read Needs_Action Items

Read all `.md` files from `vault/Needs_Action/`:
- Parse YAML frontmatter (type, from, subject, date, status, source_id)
- Read the body content
- Ignore non-`.md` files and log a notice
- If a file has malformed/missing frontmatter, skip it and note: "Warning: Skipped [filename] — invalid frontmatter"
- If `/Needs_Action` is empty, skip to Step 5 with "no pending items"

### Step 3: Classify Each Item (Silver Three-Way Classification)

For each valid item in `/Needs_Action`, classify using these rules:

**Classification A — simple**: Informational items, single-action tasks, FYI notifications
- Indicators: no action verbs (reply, send, forward), short content, no numbered lists
- Route: Process immediately (summarize + suggested actions) → move to `/Done` (Bronze behavior)

**Classification B — complex**: Multi-step tasks requiring a plan
- Indicators: numbered lists (1. 2. 3.), multiple action verbs (review AND prepare AND send), keywords like "prepare", "compile", "organize", "steps"
- Route: Invoke `/plan-task [filename]` to generate Plan.md with checkbox steps in `/Needs_Action`

**Classification C — action_required**: Items needing external action (email reply, social post, etc.)
- Indicators: keywords like "reply", "respond", "send", "forward", "post", "publish", "email", "contact"
- Route: Create an approval draft in `vault/Pending_Approval/` with:
  - YAML frontmatter: `type`, `target`, `mcp_tool` (email_send or mastodon_post), `status: pending`, `created_date`, `linked_item`
  - Body: `## Content` section with drafted action, `## Approval` section with checkboxes `- [ ] Approved` / `- [ ] Rejected`

Apply Company Handbook rules for classification overrides (e.g., priority contacts always get action_required).

### Step 4: Process by Classification

**For simple items** (Classification A):
1. Generate a concise summary (3-5 bullet points) capturing who, what, urgency
2. Generate 2-3 suggested next actions
3. Create a report file in `vault/Done/` with the same filename as the original:
   ```markdown
   ---
   type: [original type]
   from: [original from]
   subject: [original subject]
   date: [original date]
   status: done
   classification: simple
   suggested_actions:
     - [action 1]
     - [action 2]
   source_id: [original source_id]
   processed_date: [current ISO timestamp]
   ---

   ## Summary

   [3-5 bullet point summary]

   ## Suggested Actions

   - [action 1 with details]
   - [action 2 with details]

   ## Original Content

   [first 500 chars of original body]
   ```
4. Delete the original file from `vault/Needs_Action/`

**For complex items** (Classification B):
1. Invoke `/plan-task [filename]` to generate a Plan.md
2. The original item stays in `/Needs_Action` with `status: planned`
3. Do NOT move to `/Done` — user works through the plan checkboxes

**For action_required items** (Classification C):
1. Draft the appropriate action (email reply, social post, etc.)
2. Create approval draft in `vault/Pending_Approval/` using the approval_draft_template
3. The original item stays in `/Needs_Action` with `status: awaiting_approval`
4. Log: "Created approval draft for [filename] → Pending_Approval/[draft_name]"

### Step 5: Update Dashboard

Rewrite `vault/Dashboard.md` with current state:

```markdown
---
last_updated: [current ISO timestamp]
items_pending: [count of remaining files in Needs_Action]
items_processed: [count of files in Done]
---

# Dashboard

## Current Status

- **Pending items**: [count]
- **Processed items**: [count]
- **Last run**: [current date and time]

## Recent Activity

| Date | Item | Action |
|------|------|--------|
[last 10 processed items, newest first]

## Pending Items

[checklist of remaining Needs_Action items, or "No pending items."]
```

### Step 6: Report Summary

Print a summary:
```
Processing complete:
- Items classified: [N] (simple: N, complex: N, action_required: N)
- Items skipped (errors): [N]
- Reports created in /Done: [N]
- Plans generated in /Needs_Action: [N]
- Approval drafts created in /Pending_Approval: [N]
- Dashboard updated: Yes
- Remaining in /Needs_Action: [N]
- Pending approvals: [N]
```

## Example Usage

```
/process-inbox
```

No arguments needed. The skill operates on the vault at `vault/`.
