# Research: Bronze Tier Foundation

**Branch**: `001-bronze-tier-foundation` | **Date**: 2026-02-12
**Input**: Technical Context unknowns from plan.md

## R1: Gmail API Integration Pattern

**Decision**: Use Google API Python Client (`google-api-python-client`) with OAuth2 via `google-auth-oauthlib` for Gmail access.

**Rationale**:
- Constitution mandates "Google API for Gmail" (Principle IV).
- The `google-api-python-client` is Google's official Python SDK, free, and well-documented.
- OAuth2 with offline refresh tokens allows polling without re-authentication.
- Only `gmail.readonly` scope needed for Bronze (read-only; no sending).

**Alternatives considered**:
- IMAP via `imaplib`: Simpler but does not use Google API as mandated; less structured metadata.
- Gmail push notifications (Pub/Sub): Out of scope for Bronze (no real-time streaming).

**Key findings**:
- OAuth2 credentials flow: User runs a one-time browser auth, stores `token.json` locally.
- Credentials file (`credentials.json`) downloaded from Google Cloud Console.
- Both files MUST be in `.gitignore` and never synced.
- Polling pattern: `users().messages().list(userId='me', q='is:unread')` returns message IDs; then `users().messages().get()` for full content.
- Rate limits: Gmail API free tier allows 250 quota units/second per user — polling every 60s uses ~2-3 units per poll (well within limits).

## R2: Vault Item Markdown Format

**Decision**: Use YAML frontmatter in `.md` files for structured metadata, with Markdown body for content.

**Rationale**:
- Obsidian natively supports YAML frontmatter and displays it in Properties view.
- YAML is human-readable, easy to parse in Python (`pyyaml` or `python-frontmatter`).
- Keeps vault files useful both for the agent (parseable) and the user (readable in Obsidian).

**Alternatives considered**:
- JSON files: Not Obsidian-native; poor UX for human review.
- Plain Markdown with custom headers: Harder to parse reliably; no standard structure.

**Key findings**:
- Use `python-frontmatter` library for reading/writing YAML frontmatter in Markdown files.
- Frontmatter fields: `type`, `from`, `subject`, `date`, `status`, `suggested_actions`.
- Body: Content snippet (first 500 chars of email body, plain text).

## R3: Watcher State Management

**Decision**: Use a local JSON file (`watcher_state.json`) to track processed email IDs.

**Rationale**:
- Simplest approach that meets the requirement (FR-004).
- JSON is human-readable and easy to debug.
- No database dependency (local-first constraint).

**Alternatives considered**:
- SQLite: Overkill for Bronze; a single watcher tracking one source.
- Gmail labels (mark as read): Modifies user's Gmail state; violates read-only principle for Bronze.

**Key findings**:
- Store `{ "processed_ids": ["msg_id_1", "msg_id_2", ...], "last_poll": "ISO_DATE" }`.
- On each poll, compare fetched unread IDs against processed list.
- Cap the processed_ids list at 10,000 entries (rotate oldest) to prevent unbounded growth.

## R4: Claude Code Skill Architecture

**Decision**: Implement skills as Claude Code custom slash commands using `.claude/commands/` directory with prompt-based Markdown files.

**Rationale**:
- Claude Code natively supports custom slash commands as `.md` files in `.claude/commands/`.
- Each command file becomes an invocable skill (e.g., `/vault-read`, `/vault-write`, `/process-inbox`).
- No external framework needed; leverages Claude Code's built-in capability.
- Skills are composable: `/process-inbox` can reference logic from `/vault-read` and `/vault-write`.

**Alternatives considered**:
- Python scripts called by Claude Code: Adds complexity; mixes languages unnecessarily for the "brain" layer.
- MCP servers: Explicitly out of scope for Bronze (FR-009).

**Key findings**:
- `.claude/skills/vault-read/SKILL.md` — Prompt that reads and parses `.md` files from a specified vault folder.
- `.claude/skills/vault-write/SKILL.md` — Prompt that writes content to a specified vault path.
- `.claude/skills/process-inbox/SKILL.md` — Orchestration prompt that reads `/Needs_Action`, processes items, writes reports to `/Done`, updates `Dashboard.md`.
- Each command file documents its inputs, outputs, and error handling in the prompt itself.

## R5: Dashboard.md Update Strategy

**Decision**: Full rewrite of Dashboard.md on each processing run using a templated format.

**Rationale**:
- Dashboard is a summary view, not an append log. Full rewrite ensures consistency.
- Avoids complex merge logic for a file that represents current state.
- Template includes: pending count, processed count, last run timestamp, recent activity (last 10 items).

**Alternatives considered**:
- Append-only log: Grows unbounded; harder to read as a dashboard.
- Partial update (find-and-replace sections): Fragile; risks corruption if format changes.

## R6: Lock File for Concurrent Watcher Prevention

**Decision**: Use a `.watcher.lock` file with PID written inside; check on startup.

**Rationale**:
- Simple, no external dependencies.
- PID check allows detecting stale locks (if the process crashed without cleanup).

**Alternatives considered**:
- `fcntl.flock()`: Unix-only; not cross-platform (user may be on Windows per constitution).
- `portalocker` library: External dependency; violates "no extras" constraint.

**Key findings**:
- On startup: check if `.watcher.lock` exists. If yes, read PID and check if process is alive.
- If alive: exit with warning. If stale: delete lock and proceed.
- On clean shutdown: delete lock file.
- Use `atexit` and signal handlers for cleanup.
