#!/usr/bin/env python3
"""MCP server for the Personal AI Employee — Silver Tier.

Exposes email_send and mastodon_post tools via Model Context Protocol.
Runs on stdio transport for Claude Code integration.

Usage:
    python src/mcp/server.py
"""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_server")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.mcp.config import get_config


def create_server():
    """Create and configure the MCP server."""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
    except ImportError:
        logger.error("MCP SDK not installed. Run: pip install mcp")
        sys.exit(1)

    server = Server("silver-mcp")
    config = get_config()

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="email_send",
                description="Send an email via Gmail SMTP after human approval.",
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
                name="linkedin_post",
                description="Post a text share to LinkedIn after human approval.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Post text (max 3000 chars)"},
                    },
                    "required": ["text"],
                },
            ),
            Tool(
                name="mastodon_post",
                description="Publish a status post to Mastodon after human approval.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Post content (max 500 chars)", "maxLength": 500},
                        "visibility": {"type": "string", "enum": ["public", "unlisted", "private", "direct"], "default": "public"},
                    },
                    "required": ["content"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "email_send":
            from src.mcp.tools.email_send import send_email
            result = send_email(
                to=arguments.get("to", ""),
                subject=arguments.get("subject", ""),
                body=arguments.get("body", ""),
                reply_to=arguments.get("reply_to"),
            )
        elif name == "linkedin_post":
            from src.mcp.tools.linkedin_post import post_to_linkedin
            result = post_to_linkedin(
                text=arguments.get("text", ""),
            )
        elif name == "mastodon_post":
            from src.mcp.tools.mastodon_post import post_to_mastodon
            result = post_to_mastodon(
                content=arguments.get("content", ""),
                visibility=arguments.get("visibility", "public"),
            )
        else:
            result = {"status": "error", "error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    return server


async def main():
    """Run the MCP server on stdio transport."""
    from mcp.server.stdio import stdio_server

    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
