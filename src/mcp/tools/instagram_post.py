"""Instagram posting tool via Meta Graph API — Gold Tier.

Gold Tier — US3: Multi-Social Media (FR-007).
Posts to Instagram Business accounts using the Graph API (two-step media creation).
"""

import logging
import os
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def post_to_instagram(
    caption,
    image_url,
    ig_user_id=None,
    access_token=None,
):
    """Post an image with caption to Instagram.

    Uses the two-step Graph API process:
    1. Create media container with image URL and caption.
    2. Publish the container.

    Args:
        caption: Post caption text.
        image_url: Public URL of the image to post.
        ig_user_id: Instagram Business account ID. Reads META_IG_USER_ID from env if None.
        access_token: Page Access Token. Reads META_PAGE_ACCESS_TOKEN from env if None.

    Returns:
        Dict with status, post_id on success; status, error on failure.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    ig_user_id = ig_user_id or os.getenv("META_IG_USER_ID", "")
    access_token = access_token or os.getenv("META_PAGE_ACCESS_TOKEN", "")

    if not ig_user_id or not access_token:
        return {
            "status": "error",
            "error": "Missing META_IG_USER_ID or META_PAGE_ACCESS_TOKEN",
            "timestamp": timestamp,
        }

    if not image_url:
        return {
            "status": "error",
            "error": "image_url is required for Instagram posts",
            "timestamp": timestamp,
        }

    # Test mode: simulate posting
    if os.getenv("TEST_MODE", "").lower() == "true":
        return {
            "status": "posted",
            "post_id": f"test_ig_{int(datetime.now().timestamp())}",
            "platform": "instagram",
            "timestamp": timestamp,
            "test_mode": True,
        }

    try:
        # Step 1: Create media container
        container_url = f"{GRAPH_API_BASE}/{ig_user_id}/media"
        container_resp = requests.post(
            container_url,
            data={
                "image_url": image_url,
                "caption": caption or "",
                "access_token": access_token,
            },
            timeout=30,
        )
        container_resp.raise_for_status()
        container_id = container_resp.json().get("id")

        if not container_id:
            return {
                "status": "error",
                "error": "Failed to create media container — no ID returned",
                "timestamp": timestamp,
            }

        # Brief wait for container processing
        time.sleep(2)

        # Step 2: Publish the container
        publish_url = f"{GRAPH_API_BASE}/{ig_user_id}/media_publish"
        publish_resp = requests.post(
            publish_url,
            data={
                "creation_id": container_id,
                "access_token": access_token,
            },
            timeout=30,
        )
        publish_resp.raise_for_status()
        post_id = publish_resp.json().get("id", "")

        return {
            "status": "posted",
            "post_id": post_id,
            "platform": "instagram",
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
            "error": f"Instagram API error: {error_detail}",
            "timestamp": timestamp,
        }
    except requests.ConnectionError:
        return {
            "status": "error",
            "error": "Cannot connect to Instagram Graph API",
            "timestamp": timestamp,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"{type(e).__name__}: {e}",
            "timestamp": timestamp,
        }
