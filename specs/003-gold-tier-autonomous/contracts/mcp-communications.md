# MCP Communications Server Contracts

**Server**: `mcp_communications` | **Entry Point**: `src/mcp/mcp_communications.py`
**Transport**: stdio | **Migrated from**: Silver `server.py`

## Tool: `email_send`

Send an email via Gmail SMTP. Migrated from Silver unchanged.

### Input

```json
{
  "to": "string (required) — Recipient email address.",
  "subject": "string (required) — Email subject line.",
  "body": "string (required) — Email body text (plain text).",
  "from_email": "string (optional) — Sender address (default: from .env GMAIL_ADDRESS).",
  "app_password": "string (optional) — Gmail App Password (default: from .env GMAIL_APP_PASSWORD)."
}
```

### Output (success)

```json
{
  "status": "sent",
  "to": "john@example.com",
  "subject": "Re: Updated Proposal",
  "timestamp": "2026-02-12T10:30:00Z"
}
```

### Output (error)

```json
{
  "status": "error",
  "error": "SMTP connection failed: Connection refused",
  "retries_attempted": 3
}
```

### Acceptance Criteria
- Email delivered to recipient
- Subject and body match input
- Gmail App Password from `.env` (never hardcoded)
- Audit log entry written to `/Logs/mcp-<date>.md`

---

## Tool: `health_check`

Check communications MCP server status.

### Input

```json
{}
```

### Output

```json
{
  "status": "ok",
  "server": "mcp_communications",
  "smtp": "reachable",
  "timestamp": "2026-02-12T10:00:00Z"
}
```

---

## Future Extensions (Platinum)

These tools may be added in Platinum Tier:
- `whatsapp_send` — Send WhatsApp messages (requires Business API)
- `slack_send` — Post to Slack channels
- `sms_send` — Send SMS via Twilio or similar

The server architecture supports adding new tools by creating files in `src/mcp/tools/` and registering them in `mcp_communications.py`.
