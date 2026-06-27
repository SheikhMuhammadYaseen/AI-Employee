---
name: vault-write
description: Write content to a specified path in the vault with YAML frontmatter preservation.
---

# Vault Write
**Inputs**: `$ARGUMENTS` — the target file path relative to vault root (e.g., `Done/report-001.md`)
**Outputs**: Confirmation of file creation or an error message.
**Error Handling**: Reports directory-not-found, permission-denied, and empty-content errors.

## Instructions

You are writing a file to the AI Employee's Obsidian vault.

1. Parse the arguments:
   - The first argument is the target path relative to vault root (e.g., `Done/report-001.md`)
   - The remaining content (or content you've been asked to write) is the file body

2. Validate:
   - If no path is provided, respond with: "Error: No target path specified. Usage: /vault-write <path>"
   - If the parent directory does not exist under `vault/`, respond with: "Error: Directory not found: vault/[parent]/"
   - If no content is provided, respond with: "Error: Content cannot be empty"

3. Write the file:
   - Create the file at `vault/<path>` with the provided content
   - If the content includes YAML frontmatter (between `---` markers), preserve it exactly
   - If the file already exists, overwrite it

4. Confirm: "Written: vault/<path>"

## Example Usage

```
/vault-write Done/report-001.md
(Then provide the Markdown content to write)

/vault-write Dashboard.md
(Then provide the updated dashboard content)
```
