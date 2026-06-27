---
name: ralph-wiggum
description: Run the Ralph Wiggum autonomous task loop on a Plan.md file with auto-execute and approval-based steps.
---

# Ralph Wiggum — Autonomous Task Loop

Run the Ralph Wiggum autonomous task loop on a Plan.md file.

## Instructions

1. Parse the target Plan.md file for checkbox steps.
2. Classify each step as 'simple' (auto-execute) or 'action_required' (needs approval).
3. Iterate through the plan:
   - Simple steps: mark as completed automatically.
   - Action steps: create approval drafts in `/Pending_Approval`.
4. Continue iterating until all steps complete or limits reached.

## Usage

```bash
python -c "
from src.reasoning.ralph_wiggum import RalphWiggumLoop
loop = RalphWiggumLoop('./vault')
result = loop.run('./vault/Plans/my-task.md')
print(f'Status: {result[\"status\"]}')
print(f'Iterations: {result.get(\"iterations\", 0)}')
print(f'Steps completed: {result.get(\"steps_completed\", 0)}/{result.get(\"steps_total\", 0)}')
"
```

## Limits

- **Max iterations**: 10
- **Max duration**: 30 minutes
- **Max nesting depth**: 2

## Status Values

- `TASK_COMPLETE`: All steps done
- `AWAITING_APPROVAL`: Paused, action steps need human approval
- `LOOP_TIMEOUT`: Time limit exceeded
- `LOOP_MAX_ITERATIONS`: Iteration limit exceeded

## Approval Flow

When action steps create drafts in `/Pending_Approval`:
1. Review the draft file
2. Check `[x] Approved` or `[x] Rejected`
3. Re-run the loop to continue processing
