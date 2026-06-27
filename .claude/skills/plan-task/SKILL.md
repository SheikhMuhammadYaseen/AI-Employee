---
name: plan-task
description: Generate a Plan.md with checkbox steps for a complex vault item requiring multi-step execution.
---

# Plan Task
**Inputs**: `$ARGUMENTS` — filename of the item in `/Needs_Action` (e.g., `email-20260212-urgent-project.md`)
**Outputs**: Plan.md created in `/Needs_Action` with linked checkboxes, original item updated with `status: planned`
**Error Handling**: If item not found, report error. If item already planned, skip. If step extraction fails, use generic steps.

## Instructions

You are the AI Employee generating an action plan. Follow these steps precisely:

### Step 1: Read Company Handbook

Read `vault/Company_Handbook.md` to understand processing rules, priority contacts, and task preferences.

### Step 2: Read the Target Item

Read the item file from `vault/Needs_Action/$ARGUMENTS`:
- Parse YAML frontmatter (type, from, subject, date, status, priority)
- Read the body content
- If the file doesn't exist, report: "Error: Item not found: $ARGUMENTS"
- If `status` is already `planned`, report: "Item already has a plan. Skipping."

### Step 3: Analyze and Extract Steps

Analyze the item content and break it down into actionable steps:
1. Look for numbered lists, bullet points, or sequential instructions in the body
2. If the item mentions external actions (reply, send, post, forward), note these as steps requiring approval
3. Apply Company Handbook rules for priority and handling preferences
4. Each step should be concrete, single-action, and completable

### Step 4: Generate Plan.md

Create a Plan.md file in `vault/Needs_Action/` with:
- YAML frontmatter: `type: plan`, `linked_item: [original filename]`, `status: in_progress`, `priority: [from original]`, `created_date: [ISO timestamp]`, `total_steps: [count]`, `completed_steps: 0`
- Body with `# Plan: [subject]` heading
- `## Steps` section with `- [ ] Step description` checkboxes
- Steps that require external actions should note: "(requires approval in /Pending_Approval)"
- `## Notes` section with context from Company Handbook

### Step 5: Update Original Item

Update the original item in `vault/Needs_Action/$ARGUMENTS`:
- Set `status: planned`
- Set `classification: complex`
- Add `linked_plan: [plan filename]`

### Step 6: Report

Report the plan created:
- Plan filename and path
- Number of steps generated
- Any steps requiring external approval
