---
name: vault-task-processor
description: Read markdown files from the Obsidian vault (/Needs_Action), analyze their contents, and generate structured summaries or reports into Dashboard.md or /Done. Use when the AI Employee needs to process newly detected items from a watcher in Bronze Tier.
---

# Vault Task Processor

Process pending action files inside the Obsidian vault and update local markdown files accordingly.

## Instructions

When invoked to process tasks:

1. **Locate Pending Items**
   - Scan the `/Needs_Action` folder.
   - Identify all `.md` files not yet processed.
   - Ignore empty or malformed files.

2. **Parse File Structure**
   Each file must contain YAML-style metadata:
   - `type`
   - `from`
   - `subject`
   - `content`
   - `suggested_actions`

   Extract only explicitly present fields.
   Do not infer missing values.

3. **Analyze Content**
   - Summarize the main intent of the message.
   - Identify whether it requires:
      - Information only
      - Follow-up
      - Payment attention
      - Flagging per Company_Handbook rules

4. **Apply Company Rules**
   - Read `Company_Handbook.md`
   - Ensure all decisions comply with listed rules.
   - Do not invent new policies.

5. **Generate Output**
   Depending on instruction:
   - Update `Dashboard.md` summary section
   - OR create a structured report file inside `/Done`
   - Maintain consistent markdown formatting.

6. **Mark as Processed**
   - Move processed file to `/Done`
   - OR clearly indicate it has been handled.
   - Do not delete files silently.

---

## Constraints

- Local vault operations only.
- No external API calls.
- No message sending or MCP usage.
- No scheduling or background loops.
- No assumptions beyond provided file content.
- Must comply strictly with Bronze Tier scope.

---

## Example Triggers

- "Process new items in /Needs_Action"
- "Summarize pending messages"
- "Update dashboard with latest tasks"
- "Analyze inbox files"

---

## Output Quality

Ensure:
- Clear and structured summaries
- No hallucinated information
- Strict rule compliance
- Clean markdown formatting
- No extra features beyond Bronze scope
