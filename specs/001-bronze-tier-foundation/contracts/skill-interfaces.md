# Skill Interface Contracts: Bronze Tier

**Branch**: `001-bronze-tier-foundation` | **Date**: 2026-02-12

Bronze Tier does not expose REST APIs or network endpoints. All
"contracts" are local skill interfaces — Claude Code custom commands
that accept inputs and produce outputs via the filesystem.

## Skill: vault-read

**Command**: `/vault-read`
**Location**: `.claude/skills/vault-read/SKILL.md`

**Input**:
- `folder`: Vault subfolder to read (e.g., `Needs_Action`, `Done`, `Inbox`)

**Output**:
- List of Markdown files with parsed YAML frontmatter and body content
- Each item includes: filename, frontmatter fields, body text

**Error cases**:
- Folder does not exist → Return error message: "Folder not found: {folder}"
- Folder is empty → Return empty list with message: "No items in {folder}"
- File has invalid frontmatter → Skip file, include warning in output

---

## Skill: vault-write

**Command**: `/vault-write`
**Location**: `.claude/skills/vault-write/SKILL.md`

**Input**:
- `path`: Target file path relative to vault root (e.g., `Done/report-001.md`)
- `content`: Full Markdown content including YAML frontmatter

**Output**:
- Confirmation: "Written: {path}" on success
- File is created (or overwritten if exists) at the specified path

**Error cases**:
- Parent directory does not exist → Return error: "Directory not found: {parent}"
- Write permission denied → Return error: "Permission denied: {path}"
- Content is empty → Return error: "Content cannot be empty"

---

## Skill: process-inbox

**Command**: `/process-inbox`
**Location**: `.claude/skills/process-inbox/SKILL.md`

**Input**:
- None (operates on the configured vault path)

**Output**:
- For each item in `/Needs_Action`:
  - Summary report written to `/Done/<original-filename>`
  - Original removed from `/Needs_Action`
- `Dashboard.md` updated with current counts and recent activity
- Summary of actions taken (items processed, items skipped, errors)

**Error cases**:
- `/Needs_Action` is empty → Update Dashboard with "no pending items", return message
- Malformed frontmatter in item → Skip item, log warning, continue with remaining items
- Write failure (disk full, permissions) → Log error for affected item, continue with remaining items, report failures in summary

---

## Watcher Interface (Python Script)

**Script**: `src/watchers/gmail_watcher.py`

**CLI Arguments**:
- `--vault-path` (required): Path to the Obsidian vault root
- `--interval` (optional, default: 60): Polling interval in seconds
- `--credentials` (optional, default: `./credentials.json`): Path to OAuth2 credentials file

**Output**:
- Creates `.md` files in `<vault-path>/Needs_Action/` for each new unread email
- Updates `<vault-path>/.watcher_state.json` with processed IDs
- Logs to stdout/stderr

**Error cases**:
- Missing credentials file → Exit with error: "credentials.json not found at {path}"
- Invalid/expired OAuth token → Attempt refresh; if fails, exit with: "Re-authentication required"
- Network error → Log warning, continue polling on next interval
- Lock file exists (another instance running) → Exit with: "Watcher already running (PID: {pid})"

---

## Setup Script Interface

**Script**: `src/scripts/setup_vault.py`

**CLI Arguments**:
- `--vault-path` (required): Path where the vault should be created

**Output**:
- Creates vault directory structure with folders and seed files
- Prints created paths to stdout

**Idempotency**:
- If vault exists, only creates missing folders/files
- Never overwrites existing files

**Error cases**:
- Invalid path → Exit with error: "Cannot create vault at {path}: {reason}"
- Permission denied → Exit with error: "Permission denied: {path}"
