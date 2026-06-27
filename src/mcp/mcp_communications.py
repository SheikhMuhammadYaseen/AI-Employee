"""MCP Communications Server — Gold Tier.

Migrated from Silver's server.py. Exposes email_send tool.
Gold Tier — US5: Multiple MCP Servers (FR-010).
Transport: stdio.
"""

import json
import asyncio
from datetime import datetime, timezone

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.mcp.tools.email_send import send_email

server = Server("gold-communications")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="email_send",
            description="Send an email via Gmail SMTP after human approval",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body text"},
                    "reply_to": {"type": "string", "description": "Optional message ID to reply to"},
                },
                "required": ["to", "subject", "body"],
            },
        ),
        Tool(
            name="health_check",
            description="Check communications MCP server health",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name, arguments):
    timestamp = datetime.now(timezone.utc).isoformat()

    if name == "email_send":
        result = send_email(
            to=arguments.get("to", ""),
            subject=arguments.get("subject", ""),
            body=arguments.get("body", ""),
            reply_to=arguments.get("reply_to"),
        )
    elif name == "health_check":
        result = {"status": "ok", "server": "gold-communications", "timestamp": timestamp}
    else:
        result = {"status": "error", "error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
