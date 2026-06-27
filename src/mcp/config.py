#!/usr/bin/env python3
"""MCP server configuration loader — Silver Tier.

Loads configuration from environment variables and .env file.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_config() -> dict:
    """Load MCP server configuration from environment."""
    return {
        "vault_path": os.getenv("VAULT_PATH", "./vault"),
        "gmail_address": os.getenv("GMAIL_ADDRESS", ""),
        "gmail_app_password": os.getenv("GMAIL_APP_PASSWORD", ""),
        "mastodon_instance_url": os.getenv("MASTODON_INSTANCE_URL", ""),
        "mastodon_access_token": os.getenv("MASTODON_ACCESS_TOKEN", ""),
    }
