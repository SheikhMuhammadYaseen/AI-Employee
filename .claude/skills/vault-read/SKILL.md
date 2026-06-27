---
name: vault-read
description: Read and parse all Markdown files from a specified vault folder with YAML frontmatter extraction.
---

# Vault Read
**Inputs**: `$ARGUMENTS` — the vault subfolder name (e.g., `Needs_Action`, `Done`, `Inbox`)
**Outputs**: A formatted list of items with their YAML frontmatter fields and body content.
**Error Handling**: Reports folder-not-found, empty folder, and invalid frontmatter gracefully.

## Instructions

You are reading items from the AI Employee's Obsidian vault.

1. Determine the target folder: `vault/$ARGUMENTS/`
   - If `$ARGUMENTS` is empty, default to `Needs_Action`
   - If the folder does not exist, respond with: "Error: Folder not found: vault/$ARGUMENTS/"

2. List all `.md` files in the target folder.
   - Ignore non-`.md` files (e.g., `.gitkeep`, images). Log a notice if non-`.md` files are found.
   - If no `.md` files exist, respond with: "No items in $ARGUMENTS."

3. For each `.md` file:
   - Read the file content
   - Parse the YAML frontmatter between `---` markers
   - Extract fields: type, from, subject, date, status, suggested_actions, source_id, processed_date
   - Extract the body text (everything after the second `---`)
   - If frontmatter is malformed or missing, skip the file and note: "Warning: Skipped [filename] — invalid frontmatter"

4. Present each item in this format:
   ```
   ### [filename]
   - **Type**: [type]
   - **From**: [from]
   - **Subject**: [subject]
   - **Date**: [date]
   - **Status**: [status]
   - **Source ID**: [source_id]

   **Content**:
   [body text, first 200 characters]
   ```

5. End with a summary: "Found [N] item(s) in $ARGUMENTS."

## Example Usage

```
/vault-read Needs_Action
/vault-read Done
/vault-read Inbox
```
