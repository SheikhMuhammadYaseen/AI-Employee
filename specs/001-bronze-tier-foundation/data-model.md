# Data Model: Bronze Tier Foundation

**Branch**: `001-bronze-tier-foundation` | **Date**: 2026-02-12
**Source**: spec.md Key Entities + research.md decisions

## Entity: Vault Item

A Markdown file representing an actionable item in the vault.

**Location**: `/Needs_Action/<filename>.md` (pending) or `/Done/<filename>.md` (processed)

**Filename convention**: `<type>-<timestamp>-<slug>.md`
- Example: `email-20260212T143022-meeting-invite.md`

### Frontmatter Fields (YAML)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Source type: `email`, `file`, `manual` |
| `from` | string | Yes | Sender or origin (e.g., email address) |
| `subject` | string | Yes | Subject line or title |
| `date` | string (ISO 8601) | Yes | Date received (e.g., `2026-02-12T14:30:22Z`) |
| `status` | string | Yes | `pending` or `done` |
| `suggested_actions` | list of strings | No | AI-generated action suggestions |
| `source_id` | string | Yes | Unique identifier from source (e.g., Gmail message ID) |
| `processed_date` | string (ISO 8601) | No | Date the item was processed by the agent |

### Body

Plain text content snippet (first 500 characters of the email body, stripped of HTML).

### Example

```markdown
---
type: email
from: boss@company.com
subject: Q1 Budget Review Meeting
date: 2026-02-12T14:30:22Z
status: pending
suggested_actions:
  - Review attached budget document
  - Prepare summary for team
source_id: 18d4a2b3c4e5f6a7
---

Hi team,

Please review the attached Q1 budget document before our meeting
on Friday. I'd like each department head to prepare a brief
summary of their spending vs. projections...
```

## Entity: Dashboard

A single Markdown file summarizing current vault state.

**Location**: Vault root `/Dashboard.md`

### Structure

```markdown
---
last_updated: 2026-02-12T15:00:00Z
items_pending: 3
items_processed: 12
---

# Dashboard

## Current Status

- **Pending items**: 3
- **Processed items**: 12
- **Last run**: 2026-02-12 15:00

## Recent Activity

| Date | Item | Action |
|------|------|--------|
| 2026-02-12 15:00 | Q1 Budget Review Meeting | Summarized and moved to Done |
| 2026-02-12 14:45 | Weekly Standup Notes | Summarized and moved to Done |
| 2026-02-12 14:30 | Invoice #4521 | Summarized and moved to Done |

## Pending Items

- [ ] New vendor proposal from vendor@example.com
- [ ] Team lunch poll from admin@company.com
- [ ] Security update notification from it@company.com
```

## Entity: Company Handbook

A reference Markdown file with user-defined rules and preferences.

**Location**: Vault root `/Company_Handbook.md`

### Structure

```markdown
---
last_edited: 2026-02-12T10:00:00Z
---

# Company Handbook

## Processing Rules

- Emails from `boss@company.com` are always high priority
- Meeting invites should include a calendar reminder suggestion
- Newsletters can be archived without detailed summary

## Preferences

- Summaries should be concise (3-5 bullet points)
- Use professional tone in all generated content
- Flag anything mentioning "urgent" or "deadline" as high priority

## Constraints

- Never auto-reply to any email
- Never share email content outside the vault
- Always preserve original sender information
```

## Entity: Watcher State

A local JSON file tracking processed items to prevent duplicates.

**Location**: `<vault_root>/.watcher_state.json` (hidden file, not visible in Obsidian)

### Schema

```json
{
  "source": "gmail",
  "last_poll": "2026-02-12T15:00:00Z",
  "processed_ids": [
    "18d4a2b3c4e5f6a7",
    "18d4a2b3c4e5f6a8"
  ]
}
```

### Rules

- `processed_ids` array capped at 10,000 entries (oldest removed first).
- `last_poll` updated after every successful poll cycle.
- File is created on first run if it does not exist.
- File MUST be listed in `.gitignore`.

## Entity Relationships

```text
Watcher State ──tracks──> Vault Items (via source_id)
Vault Items ──summarized in──> Dashboard
Company Handbook ──read by──> Processing Skill (influences summary generation)
```

## State Transitions

```text
[Email arrives in Gmail]
    │
    ▼
[Watcher polls] ──creates──> Vault Item (status: pending, in /Needs_Action)
    │
    ▼
[Watcher State updated] ──records──> source_id
    │
    ▼
[Processing Skill invoked]
    │
    ├──reads──> Company Handbook (for rules)
    ├──reads──> Vault Item (from /Needs_Action)
    │
    ▼
[Vault Item processed]
    ├──writes──> Report in /Done (status: done)
    ├──updates──> Dashboard.md (counts, recent activity)
    └──removes──> Original from /Needs_Action
```
