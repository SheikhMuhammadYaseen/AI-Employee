---
name: check-approvals
description: Scan /Pending_Approval for drafts and process approved/rejected items via MCP tools.
---

# Check Approvals
**Inputs**: None (operates on the configured vault at `vault/`)
**Outputs**: Summary of processed approvals, MCP action results logged to /Logs, Dashboard updated
**Error Handling**: MCP failures logged, pending items left in place, stale items flagged.

## Instructions

You are the AI Employee checking the approval queue. Follow these steps precisely:

### Step 1: Scan Pending Approvals

Read all `.md` files from `vault/Pending_Approval/`:
- Parse YAML frontmatter (type, target, mcp_tool, status, created_date, linked_item)
- Read the body content and check for approval checkboxes
- If `/Pending_Approval` is empty, report "No pending approvals." and skip to Step 5.

### Step 2: Classify Each Draft

For each draft, check the checkbox state:
- `- [x] Approved` → mark as approved, proceed to Step 3
- `- [x] Rejected` → mark as rejected, proceed to Step 4
- Neither checked → leave as pending, check if stale (>24 hours since `created_date`)
  - If stale, flag: "Warning: Draft [filename] has been pending for >24 hours"

### Step 3: Execute Approved Actions

For each approved draft:
1. Read the `mcp_tool` field from frontmatter (e.g., `mastodon_post`, `email_send`, `facebook_post`, `instagram_post`, `x_post`)
2. Extract the content from `## Content` section
3. Report what action will be taken: "Executing [mcp_tool] for [target]..."
4. **For `mastodon_post`**: Invoke mastodon_post tool
5. **For `email_send`**: Invoke email_send tool
6. **For `facebook_post`**: Invoke facebook_post tool (Gold Tier)
7. **For `instagram_post`**: Invoke instagram_post tool (Gold Tier)
8. **For `x_post`**: Invoke x_post tool (Gold Tier)
9. Log the result to `vault/Logs/mcp-[timestamp]-[tool].md`
10. Move the draft to `vault/Done/` with `status: executed` and `executed_date: [ISO timestamp]`
11. If MCP fails: log the error, move draft to `vault/Done/` with `status: failed`

### Step 4: Process Rejected Drafts

For each rejected draft:
1. Move to `vault/Done/` with `status: rejected` and `executed_date: [ISO timestamp]`
2. Log: "Rejected: [filename] — moved to /Done"

### Step 5: Update Dashboard

Update `vault/Dashboard.md` to include:
- Count of items in each folder (Pending_Approval, Needs_Action, Done)
- List of recently executed/rejected actions
- Any stale approval warnings
- Last check timestamp
