"""Structured audit logger for Gold Tier.

Writes structured Markdown log entries to vault/Logs/<category>-<YYYY-MM-DD>.md.
Categories: mcp, classification, approval, loop, scheduler.
Supports daily rotation and parameter sanitization (FR-014, FR-015).
"""

import os
import re
from datetime import datetime, timezone

import frontmatter


SENSITIVE_KEYS = {
    "password", "token", "secret", "access_token", "app_password",
    "api_key", "api_secret", "access_secret", "credentials",
}


def sanitize_params(params):
    """Redact sensitive values from parameters dict."""
    if not isinstance(params, dict):
        return params

    sanitized = {}
    for key, value in params.items():
        if any(s in key.lower() for s in SENSITIVE_KEYS):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, str) and len(value) > 200:
            sanitized[key] = f"[{len(value)} chars]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_params(value)
        else:
            sanitized[key] = value

    return sanitized


def _get_log_path(vault_path, category, date=None):
    """Get the log file path for a category and date."""
    if date is None:
        date = datetime.now(timezone.utc)

    date_str = date.strftime("%Y-%m-%d")
    logs_dir = os.path.join(vault_path, "Logs")
    os.makedirs(logs_dir, exist_ok=True)
    return os.path.join(logs_dir, f"{category}-{date_str}.md")


def _ensure_log_file(log_path, category, date=None):
    """Create log file with frontmatter if it doesn't exist."""
    if date is None:
        date = datetime.now(timezone.utc)

    if not os.path.exists(log_path):
        date_str = date.strftime("%Y-%m-%d")
        content = f"""---
type: audit_log
category: {category}
date: {date_str}
entry_count: 0
---

# {category.upper()} Audit Log: {date_str}
"""
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(content)


def log_action(vault_path, category, action, details=None):
    """Append a structured log entry to the category's daily log file.

    Args:
        vault_path: Path to the vault root.
        category: Log category (mcp, classification, approval, loop, scheduler).
        action: Action name (e.g., 'create_invoice', 'classify_item').
        details: Dict with optional keys: server, tool, parameters, result,
                 duration_seconds, error_message, linked_artifact, context.
    """
    now = datetime.now(timezone.utc)
    log_path = _get_log_path(vault_path, category, now)
    _ensure_log_file(log_path, category, now)

    if details is None:
        details = {}

    time_str = now.strftime("%H:%M:%S")

    # Build entry lines
    entry_lines = [f"\n### [{time_str}] {action}\n"]

    if "server" in details:
        entry_lines.append(f"- **Server**: {details['server']}")
    if "tool" in details:
        entry_lines.append(f"- **Tool**: {details['tool']}")
    if "category" in details and details["category"] != category:
        entry_lines.append(f"- **Category**: {details['category']}")
    if "parameters" in details:
        sanitized = sanitize_params(details["parameters"])
        entry_lines.append(f"- **Parameters**: {sanitized}")
    if "result" in details:
        entry_lines.append(f"- **Result**: {details['result']}")
    if "duration_seconds" in details:
        entry_lines.append(f"- **Duration**: {details['duration_seconds']:.1f}s")
    if "error_message" in details:
        entry_lines.append(f"- **Error**: {details['error_message']}")
    if "linked_artifact" in details:
        entry_lines.append(f"- **Linked**: {details['linked_artifact']}")
    if "context" in details:
        entry_lines.append(f"- **Context**: {details['context']}")

    entry_text = "\n".join(entry_lines) + "\n"

    # Append entry
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry_text)

    # Update entry count in frontmatter
    _update_entry_count(log_path)


def _update_entry_count(log_path):
    """Update the entry_count in the log file's frontmatter."""
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Count ### entries
        count = content.count("\n### [")

        # Update frontmatter entry_count
        content = re.sub(
            r"entry_count: \d+",
            f"entry_count: {count}",
            content,
            count=1,
        )

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass  # Don't fail on count update


def summarize_week(vault_path, start_date, end_date):
    """Summarize audit logs for a date range (for CEO Briefing).

    Args:
        vault_path: Path to vault root.
        start_date: Start date (datetime or date object).
        end_date: End date (datetime or date object).

    Returns:
        Dict with category breakdowns, totals, error patterns.
    """
    logs_dir = os.path.join(vault_path, "Logs")
    if not os.path.isdir(logs_dir):
        return {"total_entries": 0, "categories": {}, "error_patterns": []}

    categories = ["mcp", "classification", "approval", "loop", "scheduler"]
    summary = {
        "total_entries": 0,
        "categories": {},
        "error_patterns": [],
    }

    from datetime import timedelta

    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        for cat in categories:
            log_file = os.path.join(logs_dir, f"{cat}-{date_str}.md")
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    entries = content.count("\n### [")
                    successes = content.count("**Result**: success")
                    failures = content.count("**Result**: failure")

                    if cat not in summary["categories"]:
                        summary["categories"][cat] = {
                            "entries": 0, "successes": 0, "failures": 0
                        }

                    summary["categories"][cat]["entries"] += entries
                    summary["categories"][cat]["successes"] += successes
                    summary["categories"][cat]["failures"] += failures
                    summary["total_entries"] += entries

                    # Extract error patterns
                    for line in content.split("\n"):
                        if "**Error**:" in line:
                            error = line.split("**Error**:")[-1].strip()
                            summary["error_patterns"].append(
                                {"date": date_str, "category": cat, "error": error}
                            )
                except Exception:
                    pass

        current += timedelta(days=1)

    return summary
