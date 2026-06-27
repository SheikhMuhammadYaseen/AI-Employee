# MCP Tool Contracts: Silver Tier

**Branch**: `002-silver-tier-assistant` | **Date**: 2026-02-12
**Server**: `src/mcp/server.py`
**Transport**: stdio (for Claude Code integration)

## Server Configuration

**Server name**: `silver-mcp`
**Protocol**: Model Context Protocol (MCP) via stdio transport
**Language**: Python (using `mcp` SDK)

Claude Code configuration (`.claude/settings.json` or project MCP config):
```json
{
  "mcpServers": {
    "silver-mcp": {
      "command": "python",
      "args": ["src/mcp/server.py"],
      "env": {
        "VAULT_PATH": "./vault"
      }
    }
  }
}
```

---

## Tool: email_send

**Description**: Send an email via Gmail SMTP after human approval.

**Module**: `src/mcp/tools/email_send.py`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "to": {
      "type": "string",
      "description": "Recipient email address"
    },
    "subject": {
      "type": "string",
      "description": "Email subject line"
    },
    "body": {
      "type": "string",
      "description": "Email body text (plain text)"
    },
    "reply_to": {
      "type": "string",
      "description": "Optional message ID to reply to"
    }
  },
  "required": ["to", "subject", "body"]
}
```

### Output

- **Success**: `{"status": "sent", "message_id": "<generated-id>", "timestamp": "<ISO8601>"}`
- **Failure**: `{"status": "error", "error": "<error-message>", "timestamp": "<ISO8601>"}`

### Environment Variables

- `GMAIL_ADDRESS`: Sender Gmail address (from `.env`)
- `GMAIL_APP_PASSWORD`: Gmail App Password (from `.env`)

### Error Cases

| Error | Response | Recovery |
|-------|----------|----------|
| Invalid recipient | `{"status": "error", "error": "Invalid email address"}` | Fix draft and re-approve |
| Auth failure | `{"status": "error", "error": "SMTP authentication failed"}` | Check App Password in .env |
| Network error | `{"status": "error", "error": "Connection to smtp.gmail.com failed"}` | Retry next cycle |
| Rate limit | `{"status": "error", "error": "Gmail daily send limit reached"}` | Wait 24 hours |

---

## Tool: mastodon_post

**Description**: Publish a status post to Mastodon after human approval.

**Module**: `src/mcp/tools/mastodon_post.py`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "content": {
      "type": "string",
      "description": "Post content text (max 500 characters)",
      "maxLength": 500
    },
    "visibility": {
      "type": "string",
      "enum": ["public", "unlisted", "private", "direct"],
      "default": "public",
      "description": "Post visibility level"
    }
  },
  "required": ["content"]
}
```

### Output

- **Success**: `{"status": "posted", "post_url": "<mastodon-post-url>", "post_id": "<id>", "timestamp": "<ISO8601>"}`
- **Failure**: `{"status": "error", "error": "<error-message>", "timestamp": "<ISO8601>"}`

### Environment Variables

- `MASTODON_INSTANCE_URL`: Mastodon instance URL (e.g., `https://mastodon.social`)
- `MASTODON_ACCESS_TOKEN`: API access token (from `.env`)

### Error Cases

| Error | Response | Recovery |
|-------|----------|----------|
| Content too long | `{"status": "error", "error": "Content exceeds 500 characters"}` | Truncate in draft |
| Auth failure | `{"status": "error", "error": "Invalid access token"}` | Regenerate token |
| Rate limit | `{"status": "error", "error": "Rate limit exceeded. Retry after {seconds}s"}` | Wait and retry |
| Instance down | `{"status": "error", "error": "Cannot connect to {instance_url}"}` | Retry next cycle |

---

## Logging Contract

Every MCP tool invocation MUST log to the vault regardless of success or failure.

### Log Entry Format

Each tool call generates a `.md` file in `<vault_path>/Logs/`:

**Filename**: `mcp-<timestamp>-<tool-name>.md`

**Frontmatter**:
```yaml
type: mcp_action
tool: <tool_name>
result: success | failure
error_message: <message or null>
timestamp: <ISO8601>
linked_draft: <approval-draft-filename>
parameters:
  <sanitized parameters - no passwords/tokens>
```

### Sanitization Rules

- NEVER log `GMAIL_APP_PASSWORD` or `MASTODON_ACCESS_TOKEN`
- Email body: Log first 200 characters only
- Mastodon content: Log full content (it's public)
- Recipient addresses: Log fully (needed for audit)
