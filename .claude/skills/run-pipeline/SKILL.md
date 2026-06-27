---
name: run-pipeline
description: Orchestrate the full Gold Tier pipeline - process inbox, generate plans, check approvals, run health checks, and update Dashboard.
---

# Run Pipeline
**Inputs**: None (operates on the configured vault at `vault/`)
**Outputs**: Full pipeline summary with items processed, plans generated, approvals executed, health status, Dashboard updated
**Error Handling**: Each stage runs independently. Failures in one stage don't block others. All errors logged. Service health tracked.

## Instructions

You are the AI Employee running the full Silver pipeline. Execute each stage in order:

### Stage 1: Process Inbox (Reasoning Loop)

Read all items in `vault/Needs_Action/`:

1. For each `.md` file, parse frontmatter and body
2. **Classify** each item using three-way classification:
   - **simple**: Single-action, informational items → process immediately per Bronze `/process-inbox` skill, move to `/Done`
   - **complex**: Multi-step tasks with numbered lists or multiple actions → invoke `/plan-task [filename]` to generate Plan.md
   - **action_required**: Items needing external action (reply, send, post) → create approval draft in `/Pending_Approval`
3. Apply Company Handbook rules for classification overrides
4. Log classification results

### Stage 2: Check Approvals

Invoke the `/check-approvals` skill:
1. Process any approved drafts in `/Pending_Approval`
2. Move rejected drafts to `/Done`
3. Flag stale drafts (>24 hours)

### Stage 3: Update Dashboard

Update `vault/Dashboard.md` with:
- Current counts: Needs_Action, Pending_Approval, Done, Logs
- Recent activity table (last 10 items processed)
- Pending approval warnings
- Pipeline run timestamp

### Stage 4: Report Summary

Provide a summary:

```
## Pipeline Run Summary

- **Items classified**: [count] (simple: N, complex: N, action_required: N)
- **Plans generated**: [count]
- **Approvals processed**: [count] (executed: N, rejected: N, pending: N)
- **Errors**: [count] (details if any)
- **Dashboard updated**: Yes/No
- **Next run**: Scheduled in [interval] minutes
```

### Stage 5: Health Checks (Gold Tier)

Check health of all MCP servers and external services:
1. Run `python -c "from src.mcp.router import health_check_all; print(health_check_all())"`
2. Update Dashboard with service health status table
3. Flag any services that have been unavailable for >1 hour

### Stage 6: Weekly Briefing Check (Gold Tier)

If today is Monday and it's between 6-9 AM:
1. Invoke `/generate-briefing` to create CEO Briefing
2. Log briefing generation result

### Error Handling

- If Stage 1 fails for a specific item, skip it and continue with the next
- If Stage 2 fails (MCP unavailable), log the error and continue to Stage 3
- Always complete Stage 3 (Dashboard update) even if previous stages had errors
- Service health is tracked automatically via ServiceHealthTracker
- Log all errors to `vault/Logs/pipeline-[timestamp].md`
