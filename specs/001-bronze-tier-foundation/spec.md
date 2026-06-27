# Feature Specification: Bronze Tier Foundation

**Feature Branch**: `001-bronze-tier-foundation`
**Created**: 2026-02-12
**Status**: Draft
**Input**: User description: "Create the Bronze Tier specification for the Personal AI Employee project — foundation layer with Obsidian vault, single watcher, and Claude Code read/write interaction."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Obsidian Vault Setup (Priority: P1)

As a user, I want a pre-configured Obsidian vault with a standard folder structure and seed files so that the AI agent has a working memory layer from day one.

The vault MUST contain:
- `Dashboard.md` at the vault root — a summary page the agent updates with current status, recent activity, and pending items.
- `Company_Handbook.md` at the vault root — a rules/policies reference file the agent reads to understand user preferences and constraints.
- `/Inbox` folder — a drop zone for raw incoming items (not yet triaged).
- `/Needs_Action` folder — items the agent MUST process next.
- `/Done` folder — completed/archived items.

**Why this priority**: Without the vault structure, no other component (watcher, agent interaction) has a place to read from or write to. This is the literal foundation.

**Independent Test**: Create the vault structure on disk, open it in Obsidian, and verify all folders and seed files are present and navigable.

**Acceptance Scenarios**:

1. **Given** a fresh local machine with Obsidian installed, **When** the setup script runs, **Then** the vault directory is created with `/Inbox`, `/Needs_Action`, `/Done` folders and `Dashboard.md` and `Company_Handbook.md` files at the root.
2. **Given** the vault has been created, **When** the user opens the vault in Obsidian, **Then** all folders and files appear in the sidebar and are readable/editable.
3. **Given** the vault already exists at the target path, **When** the setup script runs again, **Then** it does NOT overwrite existing content (idempotent — only creates missing items).

---

### User Story 2 - Single Watcher Detects New Items (Priority: P2)

As a user, I want a single watcher script that monitors one source (Gmail inbox via Google API) and creates a Markdown file in `/Needs_Action` whenever a new unread email arrives, so that the AI agent knows there is work to do.

The watcher MUST:
- Connect to Gmail using OAuth2 credentials stored locally (never synced).
- Poll for new unread emails at a configurable interval (default: 60 seconds).
- For each new unread email, create a `.md` file in `/Needs_Action` with structured frontmatter (type, from, subject, date, content snippet, suggested actions).
- Mark the email as "seen" by the watcher (local state file) to avoid duplicates.

**Why this priority**: The watcher is the "senses" layer. Without it, the agent has no stimulus — nothing arrives in the vault automatically.

**Independent Test**: Configure the watcher with test Gmail credentials, send a test email, and verify a correctly formatted `.md` file appears in `/Needs_Action` within one polling cycle.

**Acceptance Scenarios**:

1. **Given** the watcher is running with valid Gmail credentials, **When** a new unread email arrives, **Then** a `.md` file is created in `/Needs_Action` within one polling interval containing the email's type, sender, subject, date, content snippet, and suggested actions.
2. **Given** the watcher has already processed an email, **When** the same email is still in the inbox on the next poll, **Then** no duplicate `.md` file is created.
3. **Given** there are no new unread emails, **When** the watcher polls, **Then** no files are created and the watcher continues polling without error.
4. **Given** the watcher cannot reach Gmail (network error), **When** a poll attempt fails, **Then** the watcher logs the error locally and retries on the next interval without crashing.

---

### User Story 3 - Claude Code Reads and Writes to Vault (Priority: P3)

As a user, I want Claude Code to read items from `/Needs_Action`, process them (summarize, suggest actions), and write results back to the vault (update `Dashboard.md` and/or create a report in `/Done`), so that the AI agent demonstrates basic reasoning and action on vault contents.

Claude Code interaction MUST:
- Read all `.md` files in `/Needs_Action`.
- Parse the structured frontmatter to understand each item.
- Generate a summary and suggested next actions for each item.
- Write a processed report `.md` file into `/Done` for each handled item.
- Update `Dashboard.md` with a current summary of recent activity (items processed, items pending, last run timestamp).
- Move or mark the original `/Needs_Action` file as processed (move to `/Done` or delete from `/Needs_Action`).

**Why this priority**: This is the "brain + hands" layer — the agent reads, reasons, and writes. It depends on the vault (US1) existing and ideally on the watcher (US2) populating it, but can be tested independently with manually placed files.

**Independent Test**: Manually place a structured `.md` file in `/Needs_Action`, invoke the Claude Code processing skill, and verify a report appears in `/Done` and `Dashboard.md` is updated.

**Acceptance Scenarios**:

1. **Given** one or more `.md` files exist in `/Needs_Action`, **When** the processing skill is invoked, **Then** each file is read, a summary report is created in `/Done`, and the original is removed from `/Needs_Action`.
2. **Given** the processing skill has completed, **When** the user opens `Dashboard.md`, **Then** it shows the count of items processed, items still pending, and the timestamp of the last run.
3. **Given** `/Needs_Action` is empty, **When** the processing skill is invoked, **Then** it completes without error and `Dashboard.md` reflects "no pending items."
4. **Given** a `.md` file in `/Needs_Action` has malformed or missing frontmatter, **When** the processing skill runs, **Then** it logs a warning, skips the malformed file (does not crash), and continues processing other files.

---

### User Story 4 - Reusable Agent Skills (Priority: P4)

As a user, I want all AI functionality packaged as reusable, invocable skills (e.g., vault-read skill, vault-write skill, process-inbox skill) so that future tiers can compose and extend them without rewriting core logic.

Skills MUST:
- Be individually invocable (each skill can be called standalone).
- Accept clear inputs and produce clear outputs.
- Be documented with a description, expected inputs, and expected outputs.
- Handle errors gracefully (return error information rather than crashing).

**Why this priority**: Skills are an architectural enabler for Silver+ tiers. Bronze proves the pattern with 2-3 basic skills; higher tiers add more.

**Independent Test**: Invoke each skill individually with valid and invalid inputs and verify correct outputs and error handling.

**Acceptance Scenarios**:

1. **Given** a vault-read skill exists, **When** invoked with a folder path (e.g., `/Needs_Action`), **Then** it returns a list of `.md` files with their parsed frontmatter and content.
2. **Given** a vault-write skill exists, **When** invoked with content and a target path (e.g., `/Done/report-001.md`), **Then** the file is created at the specified path with the provided content.
3. **Given** a process-inbox skill exists, **When** invoked, **Then** it orchestrates vault-read on `/Needs_Action`, processes each item, calls vault-write for reports in `/Done`, and updates `Dashboard.md`.
4. **Given** any skill is invoked with invalid input (e.g., nonexistent path), **When** the skill runs, **Then** it returns a structured error message without crashing.

---

### Edge Cases

- What happens when the vault directory path does not exist or is inaccessible (permissions)?
  - The setup script MUST report a clear error and exit without partial creation.
- What happens when Gmail OAuth2 credentials are missing, expired, or invalid?
  - The watcher MUST log a clear credential error and exit gracefully (not loop endlessly).
- What happens when `/Needs_Action` contains non-Markdown files (e.g., images, PDFs)?
  - The processing skill MUST ignore non-`.md` files and log a notice.
- What happens when the disk is full and a file write fails?
  - The write skill MUST catch the error, log it, and report failure without corrupting existing files.
- What happens when two watcher instances run simultaneously?
  - The watcher MUST use a local lock file to prevent concurrent execution. If locked, the second instance MUST exit with a warning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create an Obsidian-compatible vault with `/Inbox`, `/Needs_Action`, `/Done` folders and `Dashboard.md`, `Company_Handbook.md` seed files via an idempotent setup script.
- **FR-002**: System MUST provide a single watcher script that monitors Gmail for new unread emails using OAuth2 and local credentials.
- **FR-003**: Watcher MUST create a structured `.md` file in `/Needs_Action` for each new unread email, containing frontmatter with type, from, subject, date, content snippet, and suggested actions.
- **FR-004**: Watcher MUST track processed emails in a local state file to prevent duplicate `.md` file creation.
- **FR-005**: Watcher MUST poll at a configurable interval (default: 60 seconds) and handle network/auth errors without crashing.
- **FR-006**: System MUST provide a Claude Code processing skill that reads all `.md` files from `/Needs_Action`, generates summary reports in `/Done`, and updates `Dashboard.md`.
- **FR-007**: System MUST provide reusable skills (vault-read, vault-write, process-inbox) that are individually invocable, documented, and handle errors gracefully.
- **FR-008**: All credentials and tokens MUST be stored locally only, never committed to source control or synced to any remote service.
- **FR-009**: System MUST NOT include multiple watchers, MCP action servers, scheduling, loop automation, audit trails, or any feature scoped to Silver/Gold/Platinum tiers.
- **FR-010**: Setup script MUST be idempotent — running it multiple times MUST NOT overwrite existing vault content.

### Key Entities

- **Vault Item**: A Markdown file representing an actionable item. Key attributes: type (email, file, etc.), source (sender/origin), subject, date received, content (body or snippet), suggested actions, status (pending/done).
- **Dashboard**: A single Markdown file (`Dashboard.md`) summarizing current vault state. Key attributes: items pending count, items processed count, last updated timestamp, recent activity log.
- **Company Handbook**: A reference Markdown file (`Company_Handbook.md`) containing user-defined rules, preferences, and constraints the agent reads before processing. Key attributes: rules list, preferences, last edited date.
- **Watcher State**: A local file tracking which source items have already been processed. Key attributes: item ID, timestamp processed, source identifier.

### Assumptions

- The user has Obsidian installed locally and can open a vault from a filesystem path.
- The user has a Gmail account and can create OAuth2 credentials via Google Cloud Console (free tier).
- Python 3.13+ is installed locally for the watcher script.
- Claude Code is installed and available for invoking agent skills.
- The vault resides on a local filesystem with standard read/write permissions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can run the setup script and have a fully functional vault open in Obsidian within 5 minutes.
- **SC-002**: The watcher detects and creates a vault item for a new test email within 2 minutes of the email arriving (accounting for one polling cycle).
- **SC-003**: The processing skill handles all pending items in `/Needs_Action` and produces correctly formatted reports in `/Done` with zero crashes across 10 consecutive runs with varied input.
- **SC-004**: `Dashboard.md` accurately reflects the current vault state (pending count, processed count, last run timestamp) after every processing run.
- **SC-005**: Each reusable skill can be invoked independently with valid input and returns correct output, and with invalid input returns a structured error — verified across all defined skills.
- **SC-006**: No credentials, tokens, or secrets appear in any committed file or synced location — verified by repository scan.

## Scope Boundaries

### In Scope
- Single Obsidian vault with 3 folders + 2 seed files
- Single Gmail watcher (polling, not push)
- Claude Code read/write/process skills
- Local-only credential storage
- Idempotent setup script

### Out of Scope (explicitly excluded per constitution)
- Multiple watchers or additional integrations (WhatsApp, file system, social)
- MCP action servers or outbound actions (sending emails, posting)
- Scheduling, cron jobs, or automated loops (watcher runs manually or via single invocation)
- Audit trails, compliance logging, or reporting dashboards beyond `Dashboard.md`
- Any cloud deployment, Docker, or remote infrastructure
- Odoo, Mastodon, or any third-party service integration
- Push notifications or real-time streaming (Gmail push API)
