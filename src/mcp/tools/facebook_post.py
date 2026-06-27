"""Facebook posting tool via Meta Graph API — Gold Tier.

Gold Tier — US3: Multi-Social Media (FR-007).
Posts to Facebook Pages using the Graph API.
"""

import logging
import os
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def post_to_facebook(
    message,
    page_id=None,
    access_token=None,
):
    """Post a message to a Facebook Page.

    Args:
        message: Post content text.
        page_id: Facebook Page ID. Reads META_PAGE_ID from env if None.
        access_token: Page Access Token. Reads META_PAGE_ACCESS_TOKEN from env if None.

    Returns:
        Dict with status, post_id on success; status, error on failure.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if page_id is None:
        page_id = os.getenv("META_PAGE_ID", "")
    if access_token is None:
        access_token = os.getenv("META_PAGE_ACCESS_TOKEN", "")

    if not page_id or not access_token:
        return {
            "status": "error",
            "error": "Missing META_PAGE_ID or META_PAGE_ACCESS_TOKEN",
            "timestamp": timestamp,
        }

    if not message or not message.strip():
        return {
            "status": "error",
            "error": "Message content cannot be empty",
            "timestamp": timestamp,
        }

    # Test mode: simulate posting
    if os.getenv("TEST_MODE", "").lower() == "true":
        return {
            "status": "posted",
            "post_id": f"test_fb_{int(datetime.now().timestamp())}",
            "platform": "facebook",
            "timestamp": timestamp,
            "test_mode": True,
        }

    try:
        url = f"{GRAPH_API_BASE}/{page_id}/feed"
        resp = requests.post(
            url,
            data={"message": message, "access_token": access_token},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "posted",
            "post_id": data.get("id", ""),
            "platform": "facebook",
            "timestamp": timestamp,
        }

    except requests.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json().get("error", {}).get("message", str(e))
        except Exception:
            error_detail = str(e)
        return {
            "status": "error",
            "error": f"Facebook API error: {error_detail}",
            "timestamp": timestamp,
        }
    except requests.ConnectionError:
        return {
            "status": "error",
            "error": "Cannot connect to Facebook Graph API",
            "timestamp": timestamp,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"{type(e).__name__}: {e}",
            "timestamp": timestamp,
        }
