#!/usr/bin/env python3
"""Mastodon posting tool for the Personal AI Employee — Silver Tier.

Publishes status posts to Mastodon after human approval.
Uses the Mastodon.py library for API interaction.
"""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 500


def post_to_mastodon(
    content: str,
    visibility: str = "public",
    instance_url: str | None = None,
    access_token: str | None = None,
) -> dict:
    """Post a status to Mastodon.

    Args:
        content: Post content text (max 500 chars).
        visibility: Post visibility (public, unlisted, private, direct).
        instance_url: Mastodon instance URL. Reads MASTODON_INSTANCE_URL from env if None.
        access_token: API access token. Reads MASTODON_ACCESS_TOKEN from env if None.

    Returns:
        Dict with status, post_url, post_id on success; status, error on failure.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if len(content) > MAX_CONTENT_LENGTH:
        return {
            "status": "error",
            "error": f"Content exceeds {MAX_CONTENT_LENGTH} characters ({len(content)} given)",
            "timestamp": timestamp,
        }

    if instance_url is None:
        instance_url = os.getenv("MASTODON_INSTANCE_URL", "")
    if access_token is None:
        access_token = os.getenv("MASTODON_ACCESS_TOKEN", "")

    if not instance_url or not access_token:
        return {
            "status": "error",
            "error": "Missing MASTODON_INSTANCE_URL or MASTODON_ACCESS_TOKEN",
            "timestamp": timestamp,
        }

    try:
        from mastodon import Mastodon, MastodonAPIError

        client = Mastodon(
            access_token=access_token,
            api_base_url=instance_url,
        )

        result = client.status_post(content, visibility=visibility)

        return {
            "status": "posted",
            "post_url": result.get("url", ""),
            "post_id": str(result.get("id", "")),
            "timestamp": timestamp,
        }

    except ImportError:
        return {
            "status": "error",
            "error": "Mastodon.py not installed. Run: pip install Mastodon.py",
            "timestamp": timestamp,
        }
    except Exception as e:
        error_type = type(e).__name__
        return {
            "status": "error",
            "error": f"{error_type}: {e}",
            "timestamp": timestamp,
        }
