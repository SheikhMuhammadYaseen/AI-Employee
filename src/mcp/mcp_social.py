"""MCP Social Media Server — Gold Tier.

Gold Tier — US3/US5: Exposes social posting tools as MCP tools.
Platforms: Mastodon (from Silver), Facebook, Instagram, X.
Transport: stdio.
"""

import json
import asyncio
from datetime import datetime, timezone

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.mcp.tools.mastodon_post import post_to_mastodon
from src.mcp.tools.facebook_post import post_to_facebook
from src.mcp.tools.instagram_post import post_to_instagram
from src.mcp.tools.x_post import post_to_x
from src.mcp.tools.linkedin_post import post_to_linkedin
from src.mcp.tools.social_summary import social_engagement_summary

server = Server("gold-social")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="mastodon_post",
            description="Publish a status post to Mastodon",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Post content (max 500 chars)"},
                    "visibility": {"type": "string", "enum": ["public", "unlisted", "private", "direct"], "default": "public"},
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="facebook_post",
            description="Post a message to a Facebook Page",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Post content"},
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="instagram_post",
            description="Post an image with caption to Instagram",
            inputSchema={
                "type": "object",
                "properties": {
                    "caption": {"type": "string", "description": "Post caption"},
                    "image_url": {"type": "string", "description": "Public URL of image to post"},
                },
                "required": ["caption", "image_url"],
            },
        ),
        Tool(
            name="x_post",
            description="Post a tweet to X (Twitter)",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Tweet text (max 280 chars)"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="linkedin_post",
            description="Post a text share to LinkedIn",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Post text (max 3000 chars)"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="social_engagement_summary",
            description="Get social media engagement summary for a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
            },
        ),
        Tool(
            name="health_check",
            description="Check social MCP server health",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name, arguments):
    timestamp = datetime.now(timezone.utc).isoformat()

    if name == "mastodon_post":
        result = post_to_mastodon(
            content=arguments.get("content", ""),
            visibility=arguments.get("visibility", "public"),
        )
    elif name == "facebook_post":
        result = post_to_facebook(message=arguments.get("message", ""))
    elif name == "instagram_post":
        result = post_to_instagram(
            caption=arguments.get("caption", ""),
            image_url=arguments.get("image_url", ""),
        )
    elif name == "x_post":
        result = post_to_x(text=arguments.get("text", ""))
    elif name == "linkedin_post":
        result = post_to_linkedin(text=arguments.get("text", ""))
    elif name == "social_engagement_summary":
        result = social_engagement_summary(
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
        )
    elif name == "health_check":
        result = {"status": "ok", "server": "gold-social", "timestamp": timestamp}
    else:
        result = {"status": "error", "error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
