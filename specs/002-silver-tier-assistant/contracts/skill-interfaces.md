# Skill Interface Contracts: Silver Tier

**Branch**: `002-silver-tier-assistant` | **Date**: 2026-02-12
**Extends**: Bronze Tier contracts (vault-read, vault-write, process-inbox carried forward)

Bronze skills (`/vault-read`, `/vault-write`, `/process-inbox`) remain unchanged.
`/process-inbox` is extended to route items through the classification pipeline.

---

## Skill: plan-task

**Command**: `/plan-task`
**Location**: `.claude/skills/plan-task/SKILL.md`

**Input**:
- `item`: Filename of a complex vault item in `/Needs_Action` (e.g., `email-20260212T143022-q1-budget-review.md`)

**Output**:
- Creates a `Plan.md` file in `/Needs_Action` with:
  - YAML frontmatter (type: plan, linked_item, status: in_progress, priority, created_date, total_steps, completed_steps: 0)
  - Markdown checkbox list with actionable steps
  - Notes section with context and dependencies
- Updates the original vault item's frontmatter: `status: planned`, `linked_plan: <plan-filename>`
- Returns confirmation: "Plan created: {plan-filename} ({N} steps)"

**Behavior**:
1. Read the specified vault item from `/Needs_Action`
2. Read Company Handbook for rules and preferences
3. Analyze the item to identify discrete steps
4. For steps requiring external action (send, reply, post), note that they will generate approval drafts
5. Create the Plan.md file
6. Update the original item's frontmatter

**Error cases**:
- Item not found → Return error: "Item not found: {filename}"
- Item already has a linked plan → Return warning: "Plan already exists: {existing_plan}"
- Item is classified as simple → Return warning: "Item is simple; plan not needed. Process directly."

---

## Skill: check-approvals

**Command**: `/check-approvals`
**Location**: `.claude/skills/check-approvals/SKILL.md`

**Input**:
- None (scans `/Pending_Approval` folder)

**Output**:
- For each **approved** draft (contains `- [x] Approved`):
  - Invokes the appropriate MCP tool (based on `mcp_tool` frontmatter field)
  - If MCP succeeds: Moves draft to `/Done` with `status: executed`, `executed_date: now`
  - If MCP fails: Moves draft to `/Done` with `status: failed`, logs error in `/Logs`
- For each **rejected** draft (contains `- [x] Rejected`):
  - Moves draft to `/Done` with `status: rejected`
  - No MCP tool invoked
- For each **pending** draft (no checkbox checked):
  - If >24 hours old: Flags in Dashboard as "awaiting approval"
  - Otherwise: Leaves in `/Pending_Approval`
- Updates Dashboard.md with current approval status
- Returns summary: "Processed {N} approvals: {X} executed, {Y} rejected, {Z} pending"

**Behavior**:
1. Read all `.md` files from `/Pending_Approval`
2. Parse each file's frontmatter and body
3. Check checkbox state: `- [x] Approved`, `- [x] Rejected`, or neither
4. Process approved items sequentially (one at a time to avoid MCP race conditions)
5. Move processed items to `/Done`
6. Update Dashboard

**Error cases**:
- `/Pending_Approval` is empty → Return message: "No pending approvals"
- MCP server not running → Log error, mark draft as "pending - server unavailable", retry next cycle
- MCP tool returns error → Log error with details, mark draft as "failed", move to `/Done`
- Multiple drafts approved simultaneously → Process sequentially in creation-date order

---

## Skill: generate-social-post

**Command**: `/generate-social-post`
**Location**: `.claude/skills/generate-social-post/SKILL.md`

**Input**:
- `topic` (optional): Specific topic for the post. If omitted, generate based on Company Handbook preferences and recent activity.

**Output**:
- Creates a draft social media post in `/Pending_Approval` with:
  - YAML frontmatter (type: mastodon-post, target: mastodon, status: pending, created_date, mcp_tool: mastodon_post)
  - Post content (<500 characters for Mastodon)
  - Approval checkboxes
- Returns confirmation: "Social post draft created: {filename}"

**Behavior**:
1. Read Company Handbook for business context, tone preferences, and posting guidelines
2. If topic provided, generate post about that topic
3. If no topic, analyze recent `/Done` items and Company Handbook for post ideas
4. Generate post content within Mastodon's 500-character limit
5. Include relevant hashtags (3-5)
6. Create the approval draft in `/Pending_Approval`

**Error cases**:
- Company Handbook missing or unreadable → Use generic professional tone
- Generated content exceeds 500 chars → Truncate and add "..." indicator
- `/Pending_Approval` folder missing → Create it, then write draft

---

## Skill: run-pipeline

**Command**: `/run-pipeline`
**Location**: `.claude/skills/run-pipeline/SKILL.md`

**Input**:
- `components` (optional): Comma-separated list of components to run. Default: all.
  - Valid values: `gmail`, `whatsapp`, `reasoning`, `approvals`

**Output**:
- Executes the full Silver pipeline in sequence:
  1. Run Gmail watcher (one poll cycle)
  2. Run WhatsApp watcher (one poll cycle)
  3. Run reasoning loop (process all `/Needs_Action` items)
  4. Run approval checker (process all `/Pending_Approval` items)
- Logs run summary to `/Logs/pipeline-<timestamp>.md`
- Updates Dashboard with scheduler status
- Returns summary: "Pipeline complete: {watchers_items} new items, {processed} processed, {approvals} approvals handled"

**Behavior**:
1. Check lock file — abort if another pipeline is running
2. Acquire pipeline lock
3. Execute components in order (Gmail → WhatsApp → Reasoning → Approvals)
4. If a component fails, log the error and continue with remaining components
5. Release pipeline lock
6. Write summary log to `/Logs`
7. Update Dashboard scheduler status

**Error cases**:
- Pipeline already running (lock file exists with active PID) → Return error: "Pipeline already running (PID: {pid})"
- Individual component failure → Log error, continue with remaining components, report partial success
- All components fail → Log error, return error summary

---

## Extended Skill: process-inbox (Silver Override)

**Command**: `/process-inbox`
**Location**: `.claude/skills/process-inbox/SKILL.md` (updated)

**Changes from Bronze**:
- After reading items from `/Needs_Action`, classifies each item using the three-way classification:
  - **Simple**: Process immediately (Bronze behavior — summarize, move to `/Done`)
  - **Complex**: Invoke `/plan-task` to generate Plan.md
  - **Action-required**: Create approval draft in `/Pending_Approval`
- Reads the `classification` field if already set, or runs classification heuristics
- Updates Dashboard with new Silver sections (Pending Approvals, Active Plans)

---

## Watcher Interface: WhatsApp Watcher (Python Script)

**Script**: `src/watchers/whatsapp_watcher.py`

**CLI Arguments**:
- `--vault-path` (required): Path to the Obsidian vault root
- `--interval` (optional, default: 10): DOM polling interval in seconds
- `--session-path` (optional, default: `~/.whatsapp_session`): Path to Playwright session storage
- `--keywords` (optional, default: `urgent,asap,deadline,emergency`): Comma-separated urgent keywords
- `--headless` (optional, default: false): Run browser in headless mode

**Output**:
- Creates `.md` files in `<vault-path>/Needs_Action/` for each urgent message
- Updates `<vault-path>/.watcher_state_whatsapp.json` with processed IDs
- Logs to stdout/stderr

**Error cases**:
- Session expired (QR code required) → Log: "WhatsApp session expired. Please re-scan QR code." Exit with code 2.
- Browser not installed → Log: "Chromium not installed. Run: playwright install chromium". Exit with code 1.
- Connection lost (phone disconnected) → Retry 3 times with 30-second wait, then exit with code 3.
- Lock file exists (another instance running) → Exit with: "WhatsApp watcher already running (PID: {pid})"

---

## Watcher Interface: Base Watcher (Python Class)

**Module**: `src/watchers/base_watcher.py`

**Class**: `BaseWatcher`

**Methods**:
- `__init__(vault_path, source_name, interval)`: Initialize watcher with vault path and source identifier
- `acquire_lock() -> bool`: Acquire per-watcher lock file. Returns False if already locked.
- `release_lock()`: Release lock file.
- `load_state() -> dict`: Load watcher state from `.watcher_state_<source>.json`
- `save_state(state: dict)`: Save watcher state
- `is_processed(item_id: str) -> bool`: Check if item was already processed
- `mark_processed(item_id: str)`: Add item to processed list (with 10K cap)
- `create_vault_item(frontmatter: dict, body: str) -> str`: Write `.md` file to `/Needs_Action`, return filename
- `run()`: Abstract method — subclasses implement poll logic

**Inheritance**:
- `GmailWatcher(BaseWatcher)` — refactored from Bronze
- `WhatsAppWatcher(BaseWatcher)` — new Silver watcher

---

## Approval Checker Interface (Python Script)

**Script**: `src/approval/checker.py`

**CLI Arguments**:
- `--vault-path` (required): Path to the Obsidian vault root
- `--mcp-server` (optional, default: `localhost:stdio`): MCP server connection string
- `--dry-run` (optional, default: false): Parse approvals but don't execute MCP tools

**Output**:
- Processes approved/rejected drafts in `/Pending_Approval`
- Moves processed drafts to `/Done`
- Creates MCP action logs in `/Logs`
- Returns exit code 0 on success, 1 on partial failure, 2 on total failure

---

## Scheduler Interface (Python Script)

**Script**: `src/scheduling/scheduler.py`

**CLI Arguments**:
- `--config` (optional, default: `src/scheduling/scheduler_config.json`): Path to schedule config
- `--vault-path` (required): Path to the Obsidian vault root
- `--once` (optional, default: false): Run one cycle and exit (for OS scheduler)

**Output**:
- Runs configured components in sequence
- Logs each run to `/Logs/scheduler-<date>.md`
- Returns exit code 0 on success, 1 on partial failure
