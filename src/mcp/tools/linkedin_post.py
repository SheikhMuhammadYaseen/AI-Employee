"""LinkedIn posting tool via LinkedIn Share API — Silver Tier.

Silver Tier — US4: Social Media Posting (FR-006).
Posts to LinkedIn using the Share API v2 with OAuth 2.0.
"""

import logging
import os
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
MAX_CONTENT_LENGTH = 3000


def post_to_linkedin(
    text,
    author_id=None,
    access_token=None,
):
    """Post a text share to LinkedIn.

    Args:
        text: Post content text (max 3000 chars).
        author_id: LinkedIn person URN (e.g., 'urn:li:person:XXXXXX').
            Reads LINKEDIN_AUTHOR_ID from env if None.
        access_token: OAuth 2.0 access token with w_member_social scope.
            Reads LINKEDIN_ACCESS_TOKEN from env if None.

    Returns:
        Dict with status, post_id on success; status, error on failure.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if not text or not text.strip():
        return {
            "status": "error",
            "error": "Post text cannot be empty",
            "timestamp": timestamp,
        }

    if len(text) > MAX_CONTENT_LENGTH:
        return {
            "status": "error",
            "error": f"Content exceeds {MAX_CONTENT_LENGTH} characters ({len(text)} given)",
            "timestamp": timestamp,
        }

    if author_id is None:
        author_id = os.getenv("LINKEDIN_AUTHOR_ID", "")
    if access_token is None:
        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")

    if not author_id or not access_token:
        return {
            "status": "error",
            "error": "Missing LINKEDIN_AUTHOR_ID or LINKEDIN_ACCESS_TOKEN",
            "timestamp": timestamp,
        }

    # Test mode: simulate posting
    if os.getenv("TEST_MODE", "").lower() == "true":
        return {
            "status": "posted",
            "post_id": f"test_li_{int(datetime.now().timestamp())}",
            "platform": "linkedin",
            "timestamp": timestamp,
            "test_mode": True,
        }

    try:
        url = f"{LINKEDIN_API_BASE}/ugcPosts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        payload = {
            "author": author_id,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "posted",
            "post_id": data.get("id", ""),
            "platform": "linkedin",
            "timestamp": timestamp,
        }

    except requests.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json().get("message", str(e))
        except Exception:
            error_detail = str(e)
        return {
            "status": "error",
            "error": f"LinkedIn API error: {error_detail}",
            "timestamp": timestamp,
        }
    except requests.ConnectionError:
        return {
            "status": "error",
            "error": "Cannot connect to LinkedIn API",
            "timestamp": timestamp,
        }
    except Exception as e:
        error_type = type(e).__name__
        return {
            "status": "error",
            "error": f"{error_type}: {e}",
            "timestamp": timestamp,
        }
