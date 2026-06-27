"""Shared vault file reading and parsing utilities."""

import re
from pathlib import Path

import frontmatter
import streamlit as st


@st.cache_data(ttl=60)
def list_vault_items(folder) -> list[dict]:
    """Scan a vault folder and return parsed items with frontmatter.

    Returns list of dicts with keys: path, filename, metadata (dict), body (str).
    """
    folder = Path(folder)
    items = []
    if not folder.exists():
        return items

    for f in sorted(folder.glob("*.md")):
        if f.name.startswith("."):
            continue
        try:
            post = frontmatter.load(str(f))
            items.append({
                "path": f,
                "filename": f.name,
                "metadata": dict(post.metadata),
                "body": post.content,
            })
        except Exception:
            items.append({
                "path": f,
                "filename": f.name,
                "metadata": {},
                "body": f.read_text(encoding="utf-8", errors="replace"),
            })
    return items


def read_vault_item(path: Path) -> dict:
    """Read a single vault markdown file.

    Returns dict with: path, filename, metadata, body.
    """
    try:
        post = frontmatter.load(str(path))
        return {
            "path": path,
            "filename": path.name,
            "metadata": dict(post.metadata),
            "body": post.content,
        }
    except Exception:
        return {
            "path": path,
            "filename": path.name,
            "metadata": {},
            "body": path.read_text(encoding="utf-8", errors="replace") if path.exists() else "",
        }


@st.cache_data(ttl=60)
def count_items_by_folder(vault_path) -> dict:
    """Count markdown items in each vault folder.

    Returns dict mapping folder name to count.
    """
    vault_path = Path(vault_path)
    folders = ["Inbox", "Needs_Action", "Plans", "Pending_Approval", "Done"]
    counts = {}
    for name in folders:
        folder = vault_path / name
        if folder.exists():
            counts[name] = len([
                f for f in folder.glob("*.md")
                if not f.name.startswith(".")
            ])
        else:
            counts[name] = 0
    return counts


@st.cache_data(ttl=60)
def get_recent_activity(vault_path) -> list[dict]:
    """Parse Dashboard.md Recent Activity table.

    Returns list of dicts with: date, item, action.
    """
    vault_path = Path(vault_path)
    dashboard_path = vault_path / "Dashboard.md"
    if not dashboard_path.exists():
        return []

    try:
        post = frontmatter.load(str(dashboard_path))
        content = post.content
    except Exception:
        return []

    activities = []
    in_table = False
    for line in content.splitlines():
        line = line.strip()
        if "| Date | Item | Action |" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                activities.append({
                    "date": parts[0],
                    "item": parts[1],
                    "action": parts[2],
                })
        elif in_table and not line.startswith("|"):
            break

    return activities


def read_dashboard_md(vault_path: Path) -> dict:
    """Read Dashboard.md frontmatter for KPI values.

    Returns dict with: items_pending, items_processed, items_awaiting_approval, last_updated.
    """
    dashboard_path = vault_path / "Dashboard.md"
    if not dashboard_path.exists():
        return {
            "items_pending": 0,
            "items_processed": 0,
            "items_awaiting_approval": 0,
            "last_updated": "—",
        }

    try:
        post = frontmatter.load(str(dashboard_path))
        return {
            "items_pending": post.metadata.get("items_pending", 0),
            "items_processed": post.metadata.get("items_processed", 0),
            "items_awaiting_approval": post.metadata.get("items_awaiting_approval", 0),
            "last_updated": post.metadata.get("last_updated", "—"),
        }
    except Exception:
        return {
            "items_pending": 0,
            "items_processed": 0,
            "items_awaiting_approval": 0,
            "last_updated": "—",
        }


@st.cache_data(ttl=60)
def read_briefing_md(vault_path) -> dict:
    """Read Briefing.md and return metadata + body.

    Returns dict with: metadata (dict), body (str), exists (bool).
    """
    vault_path = Path(vault_path)
    briefing_path = vault_path / "Briefing.md"
    if not briefing_path.exists():
        return {"metadata": {}, "body": "", "exists": False}

    try:
        post = frontmatter.load(str(briefing_path))
        return {
            "metadata": dict(post.metadata),
            "body": post.content,
            "exists": True,
        }
    except Exception:
        return {"metadata": {}, "body": "", "exists": False}


@st.cache_data(ttl=60)
def list_log_files(vault_path, category: str = None) -> list[dict]:
    """List log files from vault/Logs.

    Args:
        category: Optional filter (mcp, classification, approval, loop, scheduler).

    Returns list of dicts with: path, filename, metadata, body.
    """
    vault_path = Path(vault_path)
    logs_dir = vault_path / "Logs"
    if not logs_dir.exists():
        return []

    items = []
    for f in sorted(logs_dir.glob("*.md"), reverse=True):
        if f.name.startswith("."):
            continue
        try:
            post = frontmatter.load(str(f))
            meta = dict(post.metadata)
            if category and meta.get("category", "") != category:
                # Also check filename prefix
                if not f.name.startswith(category):
                    continue
            items.append({
                "path": f,
                "filename": f.name,
                "metadata": meta,
                "body": post.content,
            })
        except Exception:
            continue
    return items


def parse_log_entries(body: str) -> list[dict]:
    """Parse individual log entries from a log file body.

    Returns list of dicts with: time, action, result, context.
    """
    entries = []
    current = {}
    for line in body.splitlines():
        time_match = re.match(r"###\s*\[(\d{2}:\d{2}:\d{2})\]\s*(.*)", line.strip())
        if time_match:
            if current:
                entries.append(current)
            current = {
                "time": time_match.group(1),
                "action": time_match.group(2).strip(),
                "result": "",
                "context": "",
            }
        elif line.strip().startswith("- **Result**:"):
            if current:
                current["result"] = line.split(":", 1)[-1].strip()
        elif line.strip().startswith("- **Context**:"):
            if current:
                current["context"] = line.split(":", 1)[-1].strip()
    if current:
        entries.append(current)
    return entries
