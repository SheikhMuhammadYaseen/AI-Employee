"""MCP Server router/registry — Gold Tier.

Gold Tier — US5: Multiple MCP Servers (FR-010, FR-011).
Manages multiple MCP servers with health checks and fault isolation.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Registry of known MCP servers
MCP_SERVERS = {
    "gold-accounting": {
        "module": "src.mcp.mcp_accounting",
        "description": "Odoo accounting operations",
        "tools": ["create_invoice", "record_payment", "get_financial_summary", "list_invoices", "list_payments"],
    },
    "gold-social": {
        "module": "src.mcp.mcp_social",
        "description": "Social media posting (Mastodon, Facebook, Instagram, X, LinkedIn)",
        "tools": ["mastodon_post", "facebook_post", "instagram_post", "x_post", "linkedin_post", "social_engagement_summary"],
    },
    "gold-communications": {
        "module": "src.mcp.mcp_communications",
        "description": "Email communications",
        "tools": ["email_send"],
    },
}


def register_server(name, module, description="", tools=None):
    """Register a new MCP server in the registry.

    Args:
        name: Server identifier.
        module: Python module path for the server.
        description: Human-readable description.
        tools: List of tool names the server provides.
    """
    MCP_SERVERS[name] = {
        "module": module,
        "description": description,
        "tools": tools or [],
    }
    logger.info("Registered MCP server: %s", name)


def get_server_status(name):
    """Get status of a specific MCP server.

    Args:
        name: Server identifier.

    Returns:
        Dict with server info and status.
    """
    if name not in MCP_SERVERS:
        return {"status": "unknown", "error": f"Server '{name}' not registered"}

    server = MCP_SERVERS[name]
    return {
        "name": name,
        "status": "registered",
        "module": server["module"],
        "description": server["description"],
        "tools": server["tools"],
    }


def health_check_all(health_tracker=None):
    """Check health of all registered MCP servers.

    Args:
        health_tracker: Optional ServiceHealthTracker instance for status lookup.

    Returns:
        Dict mapping server names to health status.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    results = {}

    for name, server in MCP_SERVERS.items():
        health = {"name": name, "registered": True, "timestamp": timestamp}

        if health_tracker:
            svc_health = health_tracker.get_health(name)
            if svc_health:
                health["status"] = svc_health.get("status", "unknown")
                health["last_ok"] = svc_health.get("last_ok")
                health["error_count"] = svc_health.get("error_count", 0)
            else:
                health["status"] = "not_tracked"
        else:
            health["status"] = "registered"

        health["tools_count"] = len(server.get("tools", []))
        results[name] = health

    return results


def get_server_for_tool(tool_name):
    """Find which MCP server provides a given tool.

    Args:
        tool_name: Name of the tool to find.

    Returns:
        Server name string, or None if not found.
    """
    for name, server in MCP_SERVERS.items():
        if tool_name in server.get("tools", []):
            return name
    return None


def list_all_tools():
    """List all tools across all registered servers.

    Returns:
        Dict mapping tool names to their server name.
    """
    tools = {}
    for name, server in MCP_SERVERS.items():
        for tool in server.get("tools", []):
            tools[tool] = name
    return tools
