# Feature Specification: Gold Tier — Autonomous Employee

**Feature Branch**: `003-gold-tier-autonomous`
**Created**: 2026-02-12
**Status**: Draft
**Input**: User description: "Create the Gold Tier specification for the Personal AI Employee project — full autonomy with cross-domain integration, Odoo accounting, multi-social posting, weekly audits, Ralph Wiggum loop, and comprehensive audit logging."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Odoo Accounting Integration (Priority: P1)

As a business owner, I want the AI agent to interact with my Odoo Community accounting system so that it can create invoices, record payments, and pull financial reports — enabling the weekly audit and CEO briefing features.

The Odoo integration MUST:
- Connect to a local/self-hosted Odoo Community instance (v19+) via its standard remote procedure call interface.
- Create customer invoices with line items, due dates, and tax calculations.
- Record customer payments against open invoices.
- Pull financial summaries: revenue totals, outstanding receivables, overdue invoices, and expense summaries for a given date range.
- Use a dedicated MCP server to expose accounting operations as tools the agent can invoke.
- Never store or expose real banking credentials; operate against a test Odoo instance during development.

**Why this priority**: Accounting integration is the foundation for the weekly audit and CEO briefing — the defining Gold Tier features. Without financial data, the briefing has no substance.

**Independent Test**: Invoke the accounting MCP tool to create a test invoice in Odoo, verify it appears in Odoo's invoice list, then pull a revenue summary that includes the new invoice.

**Acceptance Scenarios**:

1. **Given** a running Odoo instance with test data, **When** the agent creates an invoice via the accounting MCP tool, **Then** the invoice is visible in Odoo with correct line items, amounts, and customer details.
2. **Given** an open invoice exists in Odoo, **When** the agent records a payment against it, **Then** the invoice status updates to "paid" and the payment is logged.
3. **Given** the agent requests a revenue summary for the current month, **When** the accounting tool queries Odoo, **Then** a summary is returned with total revenue, outstanding receivables, and overdue count.
4. **Given** Odoo is unreachable, **When** the agent attempts an accounting operation, **Then** the operation fails gracefully with a logged error and the agent continues with other tasks.

---

### User Story 2 - Weekly CEO Briefing with Audit (Priority: P2)

As a CEO/business owner, I want the AI to automatically generate a comprehensive Monday morning briefing document that summarizes the week's financial health, operational bottlenecks, and key actions taken — so that I start each week fully informed without manual report compilation.

The weekly briefing MUST:
- Run automatically every Monday morning (triggered by the scheduler).
- Pull financial data from Odoo: weekly revenue, expenses, outstanding invoices, overdue payments.
- Pull operational data from the vault: tasks completed, tasks pending, approval actions taken, errors logged.
- Pull social media metrics: posts published, engagement summary (if available from platforms).
- Generate a `Briefing.md` file in the vault root with standardized sections: Financial Summary, Operational Status, Social Media Activity, Bottlenecks & Risks, Recommended Actions.
- Include trend indicators (up/down/stable) compared to the previous week.
- Flag any critical items requiring immediate attention.

**Why this priority**: The weekly briefing is the signature Gold Tier deliverable — it demonstrates the agent operating as a "senior employee" who proactively prepares executive-level reports.

**Independent Test**: Trigger the briefing skill manually, verify a `Briefing.md` is generated with all required sections populated from Odoo test data and vault activity logs.

**Acceptance Scenarios**:

1. **Given** it is Monday morning and the scheduler triggers the briefing, **When** the briefing skill runs, **Then** a `Briefing.md` is created in the vault with Financial Summary, Operational Status, Social Media Activity, Bottlenecks & Risks, and Recommended Actions sections.
2. **Given** Odoo has financial data for the past week, **When** the briefing pulls accounting data, **Then** the Financial Summary section shows accurate revenue, expenses, outstanding receivables, and overdue invoices with trend indicators.
3. **Given** the vault has activity logs from the past week, **When** the briefing compiles operational data, **Then** it lists items processed, plans generated, approvals executed, and errors encountered.
4. **Given** Odoo is unavailable during briefing generation, **When** the briefing skill runs, **Then** the Financial Summary section shows "Data unavailable — Odoo connection failed" and all other sections are still populated.

---

### User Story 3 - Multi-Social Media Posting and Summaries (Priority: P3)

As a business owner, I want the AI agent to post content to Facebook/Instagram and X (Twitter) in addition to Mastodon, and generate engagement summaries — so that my business presence is maintained across all major platforms from a single approval workflow.

The multi-social integration MUST:
- Add Facebook/Instagram posting via the Meta Graph interface (business page posting, not personal profiles).
- Add X (Twitter) posting via the standard posting interface.
- Reuse the Silver approval workflow: all social posts go through `/Pending_Approval` before publishing.
- Support per-platform content adaptation (character limits: X=280, Mastodon=500, Facebook/Instagram=no practical limit).
- Generate weekly social engagement summaries (posts published, reach/impressions if available) for inclusion in the CEO briefing.
- Each platform exposed as a separate tool on a dedicated social media MCP server.

**Why this priority**: Multi-platform social posting extends Silver's Mastodon-only capability to cover all major business platforms, making the agent a complete social media manager.

**Independent Test**: Create a social post draft, approve it, verify it publishes to the configured test accounts on each platform, and verify the engagement summary includes the new post.

**Acceptance Scenarios**:

1. **Given** a social post draft is approved in `/Pending_Approval`, **When** the target is Facebook/Instagram, **Then** the post is published to the configured business page and logged.
2. **Given** a social post draft is approved with target X, **When** the post content exceeds 280 characters, **Then** the system returns an error before attempting to post and the draft remains actionable.
3. **Given** multiple social posts were published this week, **When** the weekly summary is requested, **Then** a summary lists all posts by platform with dates and any available engagement metrics.
4. **Given** a platform's credentials are invalid or the service is down, **When** a post is attempted, **Then** the failure is logged, the draft is marked as "failed" in `/Done`, and other platform posts are not affected.

---

### User Story 4 - Ralph Wiggum Autonomous Task Loop (Priority: P4)

As a user, I want the AI agent to autonomously iterate on multi-step tasks until they are complete, checking off plan steps, handling sub-tasks, and creating approval drafts as needed — so that complex workflows don't require manual step-by-step invocation.

The Ralph Wiggum loop MUST:
- Take a Plan.md file (generated by Silver's planner) and autonomously work through each checkbox step.
- For steps that require external action (send email, post to social, create invoice), create an approval draft in `/Pending_Approval` and pause that step until approved.
- After completing all possible steps (or pausing on approval-blocked steps), re-read the Plan.md to check if approvals have been granted and continue.
- Limit iterations to prevent runaway loops: maximum 10 iterations per plan, maximum 30 minutes total execution time.
- Log each iteration with actions taken, steps completed, and reasons for pausing.
- Update the Plan.md with checked-off steps and status notes after each iteration.

**Why this priority**: The Ralph Wiggum loop is what transforms the agent from reactive (Silver: wait for human to trigger each step) to autonomous (Gold: work through plans independently).

**Independent Test**: Create a Plan.md with 5 steps (mix of simple and action-required), start the loop, verify it completes simple steps, creates approval drafts for action steps, and pauses appropriately.

**Acceptance Scenarios**:

1. **Given** a Plan.md with 5 checkbox steps where 3 are simple actions, **When** the loop runs, **Then** it completes the 3 simple steps (checks them off), creates approval drafts for the 2 action steps, and pauses.
2. **Given** a paused plan with approved action drafts, **When** the loop re-iterates, **Then** it detects the approvals, executes the approved actions, checks off those steps, and marks the plan as complete.
3. **Given** a loop has iterated 10 times without completing, **When** the 11th iteration would start, **Then** the loop stops, logs a timeout warning, and creates a summary of completed vs. remaining steps.
4. **Given** a step execution fails (e.g., MCP tool error), **When** the loop encounters the failure, **Then** it logs the error, marks the step as "failed", and continues to the next step.

---

### User Story 5 - Multiple MCP Servers (Priority: P5)

As a system operator, I want the agent to use multiple specialized MCP servers (social media, accounting, email) rather than a single server — so that different action domains are isolated, independently deployable, and independently restartable.

The multi-MCP architecture MUST:
- Split tools across domain-specific MCP servers: one for social media (Mastodon, Facebook/Instagram, X), one for accounting (Odoo), one for communications (email, future messaging).
- Route tool invocations to the correct MCP server based on the tool name or action domain.
- Handle individual server failures gracefully: if the accounting server is down, social posting and email still work.
- Support starting/stopping individual servers independently.
- Log all MCP tool invocations with server identity, parameters (sanitized), and results.

**Why this priority**: Multi-MCP servers provide operational isolation and fault tolerance. They're an infrastructure concern that supports all other Gold features.

**Independent Test**: Start all three MCP servers, invoke one tool on each, verify all succeed. Stop the accounting server, invoke a social post, verify it still works.

**Acceptance Scenarios**:

1. **Given** all MCP servers are running, **When** the agent invokes tools across all domains, **Then** each invocation routes to the correct server and completes successfully.
2. **Given** one MCP server is stopped, **When** the agent invokes a tool on a running server, **Then** the invocation succeeds without errors from the stopped server.
3. **Given** a tool invocation fails, **When** the failure is logged, **Then** the log entry includes the server name, tool name, parameters (with secrets redacted), error message, and timestamp.

---

### User Story 6 - Comprehensive Audit Logging (Priority: P6)

As a business owner, I want every significant agent action, decision, and error to be logged in a searchable audit trail — so that I can review what the agent did, why it did it, and troubleshoot any issues.

The audit logging MUST:
- Log all MCP tool invocations (parameters sanitized, result status).
- Log all classification decisions (item classified as simple/complex/action_required, reasoning).
- Log all approval workflow transitions (created, approved, rejected, executed, failed).
- Log all Ralph Wiggum loop iterations (plan ID, step, action taken, result).
- Log all scheduler runs with component results.
- Store logs in `/Logs` as structured Markdown files with frontmatter for querying.
- Support daily log rotation (one log file per day per category).
- Include a weekly log summary as part of the CEO briefing.

**Why this priority**: Audit logging is required by the constitution (Principle II) and is essential for the weekly briefing. It's a cross-cutting concern that all other Gold features depend on.

**Independent Test**: Trigger several agent actions (classify an item, approve a draft, run a loop iteration), verify each generates a corresponding log entry in `/Logs` with correct metadata.

**Acceptance Scenarios**:

1. **Given** an MCP tool is invoked, **When** the action completes (success or failure), **Then** a log entry is created in `/Logs` within 1 second with tool name, result status, timestamp, and sanitized parameters.
2. **Given** a week of agent activity, **When** the log summary is generated, **Then** it shows total actions by category, success/failure rates, and any error patterns.
3. **Given** a daily log file exceeds reasonable size, **When** the next log entry is written, **Then** it goes into the current day's file (daily rotation ensures no single file grows unbounded).

---

### User Story 7 - Error Recovery and Graceful Degradation (Priority: P7)

As a user, I want the agent to recover from failures automatically where possible and continue operating with reduced functionality when services are unavailable — so that a single service outage doesn't halt the entire system.

Error recovery MUST:
- Implement retry logic for transient failures: 3 retries with exponential backoff for all external service calls.
- Degrade gracefully when services are down: if Odoo is unavailable, skip accounting features but continue with social posting and email; if a social platform is down, post to remaining platforms.
- Maintain a service health status in the vault (Dashboard.md or dedicated Health.md) showing which services are operational.
- Alert the user (via Dashboard flag or dedicated notification) when a service has been down for more than 1 hour.
- Never crash or halt entirely due to a single component failure.

**Why this priority**: Error recovery is essential for an "autonomous employee" — a real employee doesn't stop all work because one system is down.

**Independent Test**: Disable Odoo access, run the scheduler, verify the agent processes non-accounting tasks normally and logs the Odoo failure.

**Acceptance Scenarios**:

1. **Given** an external service returns a transient error, **When** the agent retries the operation, **Then** it succeeds on a subsequent attempt (up to 3 retries with increasing delays).
2. **Given** Odoo has been unreachable for 2 hours, **When** the Dashboard is checked, **Then** it shows Odoo status as "unavailable since [timestamp]" with an alert flag.
3. **Given** the social media MCP server is down, **When** the scheduler runs a full cycle, **Then** the email and accounting components complete normally, and the social media failure is logged without blocking other operations.

---

### User Story 8 - Architecture Documentation (Priority: P8)

As a project maintainer, I want the AI to generate and maintain architecture documentation and lessons learned in the Obsidian vault — so that the project's design decisions and operational insights are captured for future tiers.

Documentation MUST:
- Generate an `Architecture.md` in the vault documenting the Gold Tier system design: component diagram, data flows, MCP server topology, integration points.
- Maintain a `Lessons_Learned.md` capturing operational insights, common errors encountered, and workarounds discovered during Gold Tier operation.
- Update documentation when significant changes occur (new integrations, new MCP servers, new skills).
- All documentation written as Obsidian-compatible Markdown.

**Why this priority**: Documentation is required by the constitution (Principle V) and is essential for Platinum Tier progression, but it doesn't block any functional features.

**Independent Test**: Invoke the documentation skill, verify `Architecture.md` and `Lessons_Learned.md` are created in the vault with accurate content reflecting the current system state.

**Acceptance Scenarios**:

1. **Given** the Gold Tier system is fully operational, **When** the documentation skill is invoked, **Then** an `Architecture.md` is created showing all components, MCP servers, and data flows.
2. **Given** an error pattern has been logged 3+ times, **When** the lessons learned are updated, **Then** the error pattern and its workaround are documented.

---

### Edge Cases

- **Odoo connection drops mid-transaction**: Invoice creation started but Odoo becomes unreachable before confirmation. The agent MUST detect the incomplete state and log it for manual review rather than assuming success.
- **Ralph Wiggum loop infinite regression**: A plan step generates a sub-plan which generates another sub-plan. The loop MUST enforce a maximum nesting depth of 2 to prevent infinite recursion.
- **Social post approved for multiple platforms but one fails**: Successfully posted platforms MUST be logged as "posted" while the failed platform is logged as "failed" — no rollback of successful posts.
- **Weekly briefing runs but no data exists**: First-time run with empty Odoo and empty logs. The briefing MUST still generate a valid document with "No data available" sections rather than failing.
- **Concurrent plan execution**: Two Ralph Wiggum loops running on different plans simultaneously. Each loop MUST operate on its own plan file with independent lock files to prevent conflicts.
- **Stale credentials**: An access token expires during a long-running loop iteration. The agent MUST detect the auth failure, log it, and not retry with the same expired credentials indefinitely.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to a local Odoo Community instance (v19+) and create customer invoices with line items, due dates, and tax calculations.
- **FR-002**: System MUST record customer payments against open invoices in Odoo and update invoice status.
- **FR-003**: System MUST pull financial summaries from Odoo: revenue totals, outstanding receivables, overdue invoices for a given date range.
- **FR-004**: System MUST automatically generate a `Briefing.md` every Monday morning with sections: Financial Summary, Operational Status, Social Media Activity, Bottlenecks & Risks, Recommended Actions.
- **FR-005**: System MUST include trend indicators (up/down/stable vs. previous week) in each Briefing.md section where comparable data exists.
- **FR-006**: System MUST post content to Facebook/Instagram via the Meta business page interface after human approval.
- **FR-007**: System MUST post content to X (Twitter) after human approval, enforcing the 280-character limit before attempting to post.
- **FR-008**: System MUST adapt post content per platform (character limits, formatting) when generating multi-platform social drafts.
- **FR-009**: System MUST generate weekly social engagement summaries listing posts by platform, dates, and available metrics.
- **FR-010**: System MUST operate multiple MCP servers: one for social media, one for accounting, one for communications.
- **FR-011**: System MUST route tool invocations to the correct MCP server based on the tool's domain.
- **FR-012**: System MUST implement the Ralph Wiggum autonomous loop: iterate through Plan.md steps, complete simple actions, create approval drafts for action steps, re-check after approvals.
- **FR-013**: System MUST enforce Ralph Wiggum loop limits: maximum 10 iterations per plan, maximum 30 minutes total execution.
- **FR-014**: System MUST log every MCP tool invocation, classification decision, approval transition, loop iteration, and scheduler run to `/Logs` as structured Markdown with frontmatter.
- **FR-015**: System MUST implement daily log rotation (one file per day per category).
- **FR-016**: System MUST retry transient external service failures up to 3 times with increasing delays between attempts.
- **FR-017**: System MUST continue operating with reduced functionality when individual external services are unavailable.
- **FR-018**: System MUST maintain service health status visible in the Dashboard showing operational/unavailable state per service.
- **FR-019**: System MUST generate and maintain `Architecture.md` and `Lessons_Learned.md` in the vault.
- **FR-020**: System MUST reuse Silver/Bronze approval workflow for all external actions (no direct posting without approval).
- **FR-021**: System MUST never store or expose real banking credentials; all Odoo development uses test data.

### Key Entities

- **Odoo Invoice**: Represents a customer invoice with line items, amounts, tax, due date, customer reference, and payment status.
- **Odoo Payment**: Represents a payment recorded against an invoice with amount, date, and payment method.
- **Financial Summary**: Aggregated financial data for a date range: total revenue, total expenses, outstanding receivables, overdue count, cash flow.
- **CEO Briefing**: Weekly summary document with standardized sections, trend indicators, and recommended actions.
- **Social Post (Extended)**: Extends Silver's social post with multi-platform targeting (Mastodon, Facebook/Instagram, X), per-platform content variants, and engagement metrics.
- **Engagement Summary**: Weekly rollup of social activity per platform: posts count, reach/impressions, engagement rate.
- **Ralph Wiggum Session**: Represents one autonomous loop execution: plan reference, iteration count, steps completed, steps pending, approval blocks, timeout status.
- **Audit Log Entry**: Structured log record with category (mcp, classification, approval, loop, scheduler), timestamp, action, result, context, and linked artifacts.
- **Service Health Status**: Per-service operational state: service name, status (operational/degraded/unavailable), last successful contact, last error.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An invoice created via the agent appears in Odoo within 5 seconds of the MCP tool invocation.
- **SC-002**: The weekly CEO Briefing is generated automatically each Monday with all 5 required sections populated (Financial, Operational, Social, Bottlenecks, Actions).
- **SC-003**: Social posts can be published to 3+ platforms (Mastodon, Facebook/Instagram, X) through a single approval workflow.
- **SC-004**: The Ralph Wiggum loop completes a 5-step plan (with 2 action-required steps) end-to-end without manual intervention beyond approvals.
- **SC-005**: When one external service is unavailable, the agent continues processing tasks using remaining services with no system-wide interruption.
- **SC-006**: 100% of MCP tool invocations, approval transitions, and loop iterations are captured in searchable audit logs within 1 second of the event.
- **SC-007**: Failed external operations are automatically retried up to 3 times before being marked as failed.
- **SC-008**: Architecture and lessons learned documentation accurately reflects the current Gold Tier system state.
- **SC-009**: All external actions (posts, emails, invoices) require explicit human approval before execution — zero unapproved external actions.
- **SC-010**: The system handles 50+ vault items per scheduling cycle without performance degradation.

## Assumptions

- A local Odoo Community v19+ instance is available for development and testing with demo/test data loaded.
- Facebook/Instagram Meta Graph interface access is available via a business page (not personal account).
- X (Twitter) posting interface access is available via developer credentials.
- The Silver Tier approval workflow, watchers, reasoning, and scheduling are fully operational and can be extended.
- Ralph Wiggum loop is implemented as a Claude Code skill (agent-driven iteration), not a standalone Python daemon.
- "Engagement metrics" availability depends on platform access level; the system will capture what is available and note "metrics unavailable" where access is limited.
- All development and testing uses test credentials and test Odoo data — no production financial systems.

## Scope Boundaries

### In Scope
- Odoo Community integration (invoices, payments, reports) via MCP
- Facebook/Instagram and X social posting via MCP
- Weekly CEO Briefing generation
- Ralph Wiggum autonomous task loop
- Multiple MCP servers (social, accounting, communications)
- Comprehensive audit logging with daily rotation
- Error recovery with retry and graceful degradation
- Architecture and lessons learned documentation

### Out of Scope
- Cloud deployment (Platinum Tier)
- Multi-tenancy or multi-user support
- Real banking/payment processing (test data only)
- Odoo modules beyond accounting (CRM, HR, inventory)
- Push notifications or real-time alerts (beyond Dashboard flags)
- AI-generated financial analysis or predictions (reporting only, no forecasting)
- Video or image content creation for social media
- Personal WhatsApp/Gmail content syncing to Odoo
