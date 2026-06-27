"""X (Twitter) posting tool via Tweepy — Gold Tier.

Gold Tier — US3: Multi-Social Media (FR-007).
Posts tweets using Tweepy with OAuth 1.0a authentication.
"""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MAX_TWEET_LENGTH = 280


def post_to_x(
    text,
    api_key=None,
    api_secret=None,
    access_token=None,
    access_secret=None,
):
    """Post a tweet to X (Twitter).

    Args:
        text: Tweet text (max 280 characters).
        api_key: X API key. Reads X_API_KEY from env if None.
        api_secret: X API secret. Reads X_API_SECRET from env if None.
        access_token: X access token. Reads X_ACCESS_TOKEN from env if None.
        access_secret: X access secret. Reads X_ACCESS_SECRET from env if None.

    Returns:
        Dict with status, post_id on success; status, error on failure.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if len(text) > MAX_TWEET_LENGTH:
        return {
            "status": "error",
            "error": f"Tweet exceeds {MAX_TWEET_LENGTH} characters ({len(text)} given)",
            "timestamp": timestamp,
        }

    if not text or not text.strip():
        return {
            "status": "error",
            "error": "Tweet text cannot be empty",
            "timestamp": timestamp,
        }

    if api_key is None:
        api_key = os.getenv("X_API_KEY", "")
    if api_secret is None:
        api_secret = os.getenv("X_API_SECRET", "")
    if access_token is None:
        access_token = os.getenv("X_ACCESS_TOKEN", "")
    if access_secret is None:
        access_secret = os.getenv("X_ACCESS_SECRET", "")

    if not all([api_key, api_secret, access_token, access_secret]):
        return {
            "status": "error",
            "error": "Missing X API credentials (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)",
            "timestamp": timestamp,
        }

    # Test mode: simulate posting
    if os.getenv("TEST_MODE", "").lower() == "true":
        return {
            "status": "posted",
            "post_id": f"test_x_{int(datetime.now().timestamp())}",
            "platform": "x",
            "timestamp": timestamp,
            "test_mode": True,
        }

    try:
        import tweepy

        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )

        response = client.create_tweet(text=text)
        tweet_id = response.data.get("id", "") if response.data else ""

        return {
            "status": "posted",
            "post_id": str(tweet_id),
            "platform": "x",
            "timestamp": timestamp,
        }

    except ImportError:
        return {
            "status": "error",
            "error": "Tweepy not installed. Run: pip install tweepy",
            "timestamp": timestamp,
        }
    except Exception as e:
        error_type = type(e).__name__
        return {
            "status": "error",
            "error": f"{error_type}: {e}",
            "timestamp": timestamp,
        }
