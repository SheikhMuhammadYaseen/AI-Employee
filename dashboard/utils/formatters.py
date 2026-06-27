"""Formatting helpers for the dashboard."""

from datetime import datetime, timezone


def format_currency(amount, symbol: str = "$") -> str:
    """Format a number as currency."""
    try:
        val = float(amount)
        if val < 0:
            return f"-{symbol}{abs(val):,.2f}"
        return f"{symbol}{val:,.2f}"
    except (TypeError, ValueError):
        return f"{symbol}0.00"


def format_status_badge(status: str) -> str:
    """Return a colored dot + text status string for dataframes."""
    mapping = {
        "operational": "\u25cf Operational",
        "ok": "\u25cf OK",
        "success": "\u25cf Success",
        "approved": "\u25cf Approved",
        "done": "\u25cf Done",
        "degraded": "\u25b2 Degraded",
        "warning": "\u25b2 Warning",
        "pending": "\u25cb Pending",
        "unavailable": "\u25cf Unavailable",
        "down": "\u25cf Down",
        "error": "\u2717 Error",
        "failed": "\u2717 Failed",
        "rejected": "\u2717 Rejected",
        "timeout": "\u25cf Timeout",
    }
    key = status.lower().strip() if status else "unknown"
    return mapping.get(key, f"\u25cb {status.title() if status else 'Unknown'}")


def format_timestamp(dt_str: str, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Parse an ISO timestamp string and format it for display."""
    if not dt_str or dt_str == "None":
        return "—"
    try:
        dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        return str(dt_str)[:16] if dt_str else "—"


def time_ago(dt_str: str) -> str:
    """Return a human-readable 'time ago' string."""
    if not dt_str or dt_str == "None":
        return "—"
    try:
        dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        seconds = int(delta.total_seconds())

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = seconds // 60
            return f"{mins}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        else:
            days = seconds // 86400
            return f"{days}d ago"
    except (ValueError, TypeError):
        return "—"


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    text = str(text).strip()
    return text[:max_len] + "..." if len(text) > max_len else text


def friendly_name(filename: str) -> str:
    """Turn a raw vault filename into a human-readable name.

    'email-20260212T100000-urgent-client-request.md' -> 'Urgent Client Request'
    'action-20260213T190500-reply-client-proposal.md' -> 'Reply Client Proposal'
    """
    import re
    name = filename
    # Remove .md extension
    name = name.replace(".md", "")
    # Remove common prefixes
    for prefix in ("email-", "action-", "plan-", "loop-action-", "whatsapp-"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    # Remove ISO timestamps (20260212T100000)
    name = re.sub(r"\d{8}T\d{6}-?", "", name)
    # Remove date-only patterns (2026-02-12-)
    name = re.sub(r"\d{4}-\d{2}-\d{2}-?", "", name)
    # Replace hyphens/underscores with spaces
    name = name.replace("-", " ").replace("_", " ")
    # Clean up extra spaces
    name = " ".join(name.split()).strip()
    # Title case
    return name.title() if name else "Item"
