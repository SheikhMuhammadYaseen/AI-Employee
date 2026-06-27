"""Social engagement summary tool — Gold Tier.

Gold Tier — US3: Multi-Social Media (FR-008).
Scans vault/Done for social post records and generates engagement summaries.
"""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def social_engagement_summary(start_date=None, end_date=None, vault_path=None):
    """Generate a social media engagement summary.

    Args:
        start_date: Start date (YYYY-MM-DD string). Defaults to 7 days ago.
        end_date: End date (YYYY-MM-DD string). Defaults to today.
        vault_path: Path to vault root. Reads VAULT_PATH from env if None.

    Returns:
        Dict with platform breakdown, totals, and status.
    """
    vault_path = vault_path or os.getenv("VAULT_PATH", "./vault")
    now = datetime.now(timezone.utc)

    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        end_dt = now

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        from datetime import timedelta
        start_dt = end_dt - timedelta(days=7)

    done_dir = os.path.join(vault_path, "Done")
    if not os.path.isdir(done_dir):
        return {
            "status": "success",
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "platforms": {},
            "total_posts": 0,
            "total_engagements": 0,
        }

    try:
        import frontmatter as fm
    except ImportError:
        return {
            "status": "error",
            "error": "python-frontmatter not installed",
        }

    platform_types = {
        "mastodon-post": "mastodon",
        "facebook-post": "facebook",
        "instagram-post": "instagram",
        "x-post": "x",
        "linkedin-post": "linkedin",
    }

    platforms = {}
    total_posts = 0

    for filename in sorted(os.listdir(done_dir)):
        if not filename.endswith(".md"):
            continue

        try:
            filepath = os.path.join(done_dir, filename)
            post = fm.load(filepath)
            meta = post.metadata

            post_type = meta.get("type", "")
            if post_type not in platform_types:
                continue

            # Date filter
            executed_date = meta.get("executed_date", "")
            if isinstance(executed_date, str) and executed_date:
                post_date = datetime.fromisoformat(executed_date.replace("Z", "+00:00"))
                if not (start_dt <= post_date <= end_dt):
                    continue

            platform = platform_types[post_type]
            if platform not in platforms:
                platforms[platform] = {
                    "posts": 0,
                    "engagements": 0,
                    "post_ids": [],
                }

            platforms[platform]["posts"] += 1
            platforms[platform]["post_ids"].append(meta.get("post_id", filename))
            total_posts += 1

        except Exception:
            continue

    return {
        "status": "success",
        "start_date": start_dt.strftime("%Y-%m-%d"),
        "end_date": end_dt.strftime("%Y-%m-%d"),
        "platforms": platforms,
        "total_posts": total_posts,
        "total_engagements": sum(p["engagements"] for p in platforms.values()),
    }
