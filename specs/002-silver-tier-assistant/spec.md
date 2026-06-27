# Feature Specification: Silver Tier — Functional Assistant

**Feature Branch**: `002-silver-tier-assistant`
**Created**: 2026-02-12
**Status**: Draft
**Input**: User description: "Create the Silver Tier specification for the Personal AI Employee project — extending Bronze with multiple watchers, reasoning loop, social posting, MCP server, approval workflow, and scheduling."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - WhatsApp Watcher (Priority: P1)

As a user, I want a second watcher that monitors my WhatsApp messages for urgent items and creates vault entries in `/Needs_Action`, so that the AI agent covers my most critical communication channels beyond email.

The WhatsApp watcher MUST:
- Use browser automation to connect to WhatsApp Web and monitor incoming messages.
- Detect messages flagged as urgent (keywords: "urgent", "asap", "deadline", "emergency", or messages from contacts marked as priority in the Company Handbook).
- Create a structured `.md` file in `/Needs_Action` with frontmatter (type: whatsapp, from, subject/contact, date, content snippet, suggested actions).
- Coexist with the Bronze Gmail watcher without conflicts (separate state files, separate lock files).

**Why this priority**: Multiple watchers are the defining upgrade from Bronze to Silver. WhatsApp is the most common personal/business messaging channel, making it the highest-value second source.

**Independent Test**: Start the WhatsApp watcher, send a test message containing "urgent", and verify a correctly formatted `.md` file appears in `/Needs_Action`.

**Acceptance Scenarios**:

1. **Given** the WhatsApp watcher is running and authenticated, **When** an urgent message arrives, **Then** a `.md` file is created in `/Needs_Action` within 30 seconds containing the sender, message content, timestamp, and "whatsapp" type.
2. **Given** a non-urgent message arrives, **When** the watcher processes it, **Then** no file is created in `/Needs_Action` (only urgent messages trigger action).
3. **Given** both Gmail and WhatsApp watchers are running simultaneously, **When** both detect new items, **Then** each creates separate vault items without file conflicts or state corruption.
4. **Given** the WhatsApp Web session expires or disconnects, **When** the watcher detects the disconnection, **Then** it logs a clear error and attempts reconnection, or exits gracefully after 3 retries.

---

### User Story 2 - Claude Reasoning Loop with Plan Generation (Priority: P2)

As a user, I want the AI to automatically analyze new items in `/Needs_Action` and generate a `Plan.md` file with checkboxes for multi-step tasks, so that complex items are broken down into actionable steps rather than just summarized.

The reasoning loop MUST:
- Detect when new items appear in `/Needs_Action` (triggered by scheduler or manual invocation).
- Read Company Handbook rules to understand priorities and preferences.
- For simple items (single-action): process immediately (Bronze behavior — summarize and move to `/Done`).
- For complex items (multi-step): generate a `Plan.md` in `/Needs_Action` with checkbox steps, keeping the original item linked.
- For items requiring external action (reply, post, send): generate a draft in `/Pending_Approval` instead of acting immediately.

**Why this priority**: The reasoning loop transforms the agent from a simple reader/writer (Bronze) into a planner that breaks down work and routes actions appropriately.

**Independent Test**: Place a complex item in `/Needs_Action` (e.g., "Prepare Q1 report: gather data, draft summary, send to team"), invoke the reasoning skill, and verify a `Plan.md` with checkboxes is generated.

**Acceptance Scenarios**:

1. **Given** a simple item exists in `/Needs_Action`, **When** the reasoning loop processes it, **Then** it is summarized and moved to `/Done` (Bronze behavior preserved).
2. **Given** a complex item with multiple steps exists in `/Needs_Action`, **When** the reasoning loop processes it, **Then** a `Plan.md` is created with checkbox steps, linked to the original item.
3. **Given** an item requiring an external action (e.g., "reply to this email"), **When** the reasoning loop processes it, **Then** a draft is created in `/Pending_Approval` with the proposed action and an approval checkbox.
4. **Given** the Company Handbook marks certain senders as high priority, **When** an item from that sender is processed, **Then** it is flagged as high priority in the plan.

---

### User Story 3 - Human-in-the-Loop Approval Workflow (Priority: P3)

As a user, I want all external actions (sending emails, posting on social media, replying to messages) to require my explicit approval in Obsidian before execution, so that I maintain control and the AI never acts without my consent.

The approval workflow MUST:
- Create draft actions as `.md` files in a new `/Pending_Approval` vault folder.
- Each draft includes: the proposed action, target (recipient/platform), content, and an approval checkbox (`- [ ] Approved`).
- The user reviews, edits if needed, and checks the approval box in Obsidian.
- An approval-checker skill monitors `/Pending_Approval` for checked items and triggers execution via the MCP server.
- Rejected items (user deletes or adds `- [x] Rejected`) are moved to `/Done` with a "rejected" status.

**Why this priority**: Human approval is constitutionally mandated (Principle II) for all sensitive external actions. This workflow is the safety gate that enables Silver's new outbound capabilities.

**Independent Test**: Place a draft action in `/Pending_Approval`, check the approval box in Obsidian, run the approval checker, and verify the action is executed (or simulated in test mode).

**Acceptance Scenarios**:

1. **Given** the reasoning loop identifies an external action needed, **When** it creates a draft, **Then** the draft appears in `/Pending_Approval` with clear action description and unchecked approval box.
2. **Given** the user checks the `Approved` box in Obsidian, **When** the approval checker runs, **Then** the approved action is executed via the MCP server and the draft is moved to `/Done` with status "approved".
3. **Given** the user marks a draft as `Rejected`, **When** the approval checker runs, **Then** the draft is moved to `/Done` with status "rejected" and no action is executed.
4. **Given** a draft has been in `/Pending_Approval` for more than 24 hours without action, **When** the approval checker runs, **Then** it flags the item in Dashboard.md as "awaiting approval" but does NOT auto-approve or auto-reject.

---

### User Story 4 - Social Media Posting via MCP Server (Priority: P4)

As a user, I want the AI to generate business-relevant social media posts and publish them (after my approval) to LinkedIn and Mastodon, so that I can maintain an active online presence for lead generation without manual effort.

The social posting system MUST:
- Generate post content based on business topics, Company Handbook guidelines, and recent activity.
- Create draft posts in `/Pending_Approval` with the proposed content and target platform.
- After approval, send the post via an MCP server that interfaces with the LinkedIn API and Mastodon API.
- Automatically post on LinkedIn about business to generate sales (primary sales channel).
- Log the posted content and link in `/Done` for record-keeping.

**Why this priority**: Social posting is the first true "external action" demonstrating the MCP server and approval workflow end-to-end. LinkedIn is the primary B2B sales channel; Mastodon is used as an additional free platform per constitution.

**Independent Test**: Generate a draft social post, approve it, and verify it is published to LinkedIn and/or a test Mastodon account.

**Acceptance Scenarios**:

1. **Given** the social posting skill is invoked, **When** it generates a post, **Then** a draft appears in `/Pending_Approval` with the post content, target platform (LinkedIn or Mastodon), and approval checkbox.
2. **Given** the user approves a LinkedIn post draft, **When** the approval checker triggers the MCP server, **Then** the post is published to the configured LinkedIn account via the Share API and a confirmation with the post ID is logged in `/Done`.
3. **Given** the user approves a Mastodon post draft, **When** the approval checker triggers the MCP server, **Then** the post is published to the configured Mastodon account and a confirmation with the post URL is logged in `/Done`.
4. **Given** the LinkedIn or Mastodon API returns an error (rate limit, auth failure), **When** the MCP server attempts to post, **Then** it logs the error, marks the draft as "failed" in `/Done`, and does not retry automatically.
5. **Given** the user wants to schedule recurring posts, **When** configured via Company Handbook preferences, **Then** the system generates one draft post per configured interval (e.g., daily) for approval.

---

### User Story 5 - MCP Server for External Actions (Priority: P5)

As a user, I want a working MCP (Model Context Protocol) server that enables the AI to perform approved external actions (sending emails, posting to social media), so that the agent can act on my behalf after approval.

The MCP server MUST:
- Expose tools that Claude Code can invoke for external actions.
- Support at minimum: sending emails via Gmail API, posting to LinkedIn API, and posting to Mastodon API.
- Accept only approved actions (called by the approval-checker after user consent).
- Log every action taken (tool invoked, parameters, result, timestamp) to the vault.
- Handle errors gracefully (network failures, auth errors, rate limits) with clear error messages.

**Why this priority**: The MCP server is the "hands" upgrade — it gives the agent the ability to act externally, not just read and write locally.

**Independent Test**: Invoke the MCP server's email-send tool with a test recipient and verify the email is sent (or simulated). Invoke the Mastodon-post tool and verify the post appears.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** the approval checker invokes the email-send tool with approved parameters, **Then** the email is sent via Gmail API and a log entry is created in the vault.
2. **Given** the MCP server is running, **When** the approval checker invokes the mastodon-post tool with approved content, **Then** the post is published and a log entry with the post URL is created.
3. **Given** an MCP tool call fails (network error, auth error), **When** the error occurs, **Then** it is logged with details and the corresponding draft is marked as "failed" in `/Done`.
4. **Given** Claude Code is configured with the MCP server, **When** a skill references an MCP tool, **Then** Claude Code can invoke it through the standard MCP protocol.

---

### User Story 6 - Basic Scheduling (Priority: P6)

As a user, I want watchers and the reasoning loop to run automatically on a schedule (every 5-10 minutes), so that the AI agent works continuously without me manually triggering each component.

Scheduling MUST:
- Run all watchers (Gmail + WhatsApp) on configurable intervals.
- Run the reasoning loop after watchers complete to process new items.
- Run the approval checker to execute approved actions.
- Use the operating system's native scheduling (Task Scheduler on Windows, cron on Linux/macOS).
- Log each scheduled run to the vault for audit.

**Why this priority**: Scheduling makes the agent proactive rather than manually triggered. It's the final piece that ties all Silver components into a continuous workflow.

**Independent Test**: Configure the scheduler, wait for two cycles, and verify that watchers have polled, new items are processed, and approved actions are executed.

**Acceptance Scenarios**:

1. **Given** the scheduler is configured with a 5-minute interval, **When** 5 minutes elapse, **Then** all watchers run, the reasoning loop processes new items, and the approval checker executes approved actions.
2. **Given** a watcher fails during a scheduled run, **When** the failure occurs, **Then** the error is logged and other watchers and the reasoning loop still execute (partial failure does not block the pipeline).
3. **Given** no new items are detected during a scheduled run, **When** the cycle completes, **Then** it completes silently without errors or unnecessary vault writes.
4. **Given** the user wants to change the schedule interval, **When** they modify the scheduler configuration, **Then** the new interval takes effect on the next cycle without restarting the system.

---

### User Story 7 - Extended Agent Skills (Priority: P7)

As a user, I want all new Silver functionality packaged as reusable, documented Claude Code skills, so that the skill library grows incrementally and remains composable for Gold+ tiers.

New skills MUST include:
- `/plan-task` — Generate a Plan.md with checkboxes for a complex item.
- `/check-approvals` — Scan `/Pending_Approval` for approved/rejected items and trigger execution or archival.
- `/generate-social-post` — Create a draft social media post for approval.
- `/run-pipeline` — Orchestrate the full cycle: watchers → reasoning → approval check.

**Why this priority**: Skills are the architectural pattern. Packaging Silver's new capabilities as skills ensures consistency and extensibility.

**Independent Test**: Invoke each new skill individually and verify correct behavior.

**Acceptance Scenarios**:

1. **Given** `/plan-task` is invoked with a complex item, **When** it runs, **Then** a Plan.md with checkbox steps is created.
2. **Given** `/check-approvals` is invoked, **When** approved items exist in `/Pending_Approval`, **Then** they are executed and moved to `/Done`.
3. **Given** `/generate-social-post` is invoked, **When** it runs, **Then** a draft post appears in `/Pending_Approval`.
4. **Given** `/run-pipeline` is invoked, **When** it runs, **Then** all watchers, reasoning, and approval checking execute in sequence.

---

### Edge Cases

- What happens when the WhatsApp Web session requires QR code re-scan?
  - The watcher MUST detect the authentication state and prompt the user to re-scan, then resume monitoring after re-authentication.
- What happens when multiple drafts are approved simultaneously?
  - The approval checker MUST process them sequentially to avoid race conditions with the MCP server.
- What happens when the MCP server is not running when an approved action is triggered?
  - The approval checker MUST log an error and leave the draft in `/Pending_Approval` with a "pending - server unavailable" note, retrying on the next cycle.
- What happens when the Gmail watcher (Bronze) and WhatsApp watcher (Silver) both create items for the same event?
  - Each watcher operates independently. Deduplication is NOT required in Silver — each source creates its own vault item.
- What happens when a scheduled run overlaps with a manual invocation?
  - Lock files (one per watcher, one for the reasoning loop) MUST prevent concurrent execution of the same component.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a WhatsApp watcher using browser automation that monitors for urgent messages and creates structured `.md` files in `/Needs_Action`.
- **FR-002**: System MUST support at least two watchers running simultaneously (Gmail from Bronze + WhatsApp from Silver) without state conflicts.
- **FR-003**: System MUST provide a reasoning loop that classifies items as simple (process immediately), complex (generate Plan.md), or action-required (create draft in `/Pending_Approval`).
- **FR-004**: System MUST generate `Plan.md` files with checkbox steps for complex multi-step items, linked to the original vault item.
- **FR-005**: System MUST create a `/Pending_Approval` vault folder for draft actions requiring human consent.
- **FR-006**: Each draft in `/Pending_Approval` MUST include: proposed action, target, content, and an approval checkbox that the user can check/uncheck in Obsidian.
- **FR-007**: System MUST provide an approval-checker that detects checked/rejected items in `/Pending_Approval` and triggers execution or archival.
- **FR-008**: System MUST provide at least one working MCP server exposing tools for: sending emails (Gmail API) and posting to social media (Mastodon API).
- **FR-009**: All external actions (email send, social post) MUST be executed only after explicit human approval — never automatically.
- **FR-010**: System MUST log every MCP action (tool, parameters, result, timestamp) to the vault for audit.
- **FR-011**: System MUST support basic scheduling via OS-native tools (Task Scheduler / cron) to run watchers, reasoning loop, and approval checker on configurable intervals (default: 5 minutes).
- **FR-012**: System MUST provide new Claude Code skills: `/plan-task`, `/check-approvals`, `/generate-social-post`, `/run-pipeline`.
- **FR-013**: All credentials and tokens MUST be stored locally only (constitution mandate). WhatsApp session data, Mastodon API keys, and Gmail tokens MUST NEVER be synced.
- **FR-014**: System MUST reuse Bronze vault structure, extending it with `/Pending_Approval` folder and new file types.
- **FR-015**: System MUST NOT include Odoo integration, full audit trails, cloud deployment, or Ralph Wiggum iteration loop (scoped to Gold/Platinum).

### Key Entities

- **Plan Item**: A Markdown file with checkbox steps for a complex task. Key attributes: linked item reference, steps (checkbox list), status (in_progress/complete), priority, created date.
- **Approval Draft**: A Markdown file in `/Pending_Approval` representing a proposed external action. Key attributes: action type (email-send, social-post), target (recipient/platform), content (draft text), approval status (pending/approved/rejected), created date.
- **MCP Action Log**: A record of every external action executed by the MCP server. Key attributes: tool name, parameters, result (success/failure), error message (if any), timestamp, linked approval draft.
- **Schedule Configuration**: Settings defining when and how often each component runs. Key attributes: component name, interval, last run timestamp, enabled/disabled flag.
- **Vault Item (extended)**: Bronze entity extended with new type values: `whatsapp` (in addition to `email`).

### Assumptions

- The user has WhatsApp Web accessible and can scan a QR code for initial authentication.
- The user has a Mastodon account (any instance) and can generate an API access token.
- Bronze Tier vault and Gmail watcher are already set up and functioning.
- The user's operating system supports cron (Linux/macOS) or Task Scheduler (Windows).
- The MCP server runs locally as a background process.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both Gmail and WhatsApp watchers run simultaneously for 1 hour without crashes, conflicts, or state corruption.
- **SC-002**: The reasoning loop correctly classifies 90%+ of test items as simple, complex, or action-required (verified across 20 diverse test items).
- **SC-003**: An approved draft in `/Pending_Approval` is executed (email sent or post published) within one scheduler cycle after approval.
- **SC-004**: The MCP server successfully sends a test email and publishes a test Mastodon post with zero errors on the first approved attempt.
- **SC-005**: The scheduler runs all components (watchers + reasoning + approval check) at the configured interval for 24 hours with zero unrecoverable failures.
- **SC-006**: Every external action is logged in the vault with tool name, result, and timestamp — verified by audit of 10 consecutive actions.
- **SC-007**: No external action executes without explicit human approval — verified by attempting to trigger an action without checking the approval box.
- **SC-008**: All new skills (`/plan-task`, `/check-approvals`, `/generate-social-post`, `/run-pipeline`) are individually invocable and return correct results.

## Scope Boundaries

### In Scope
- WhatsApp watcher (browser automation, urgent message detection)
- Claude reasoning loop with Plan.md generation
- `/Pending_Approval` workflow with Obsidian checkbox approval
- One MCP server with email-send and mastodon-post tools
- Mastodon social posting (free alternative per constitution)
- Basic OS-native scheduling (cron / Task Scheduler)
- 4 new Claude Code skills
- Extension of Bronze vault structure

### Out of Scope (explicitly excluded per constitution)
- Odoo integration (Gold tier)
- Full audit trails and compliance dashboards (Gold tier)
- Ralph Wiggum iteration loop / autonomous retry (Gold tier)
- Cloud deployment, Docker, or remote infrastructure (Platinum tier)
- LinkedIn API (paid; using Mastodon per constitution free-focus mandate)
- Push notifications or real-time streaming
- Multi-user support or team collaboration features
- Automated scheduling without OS-native tools (no custom daemon)
