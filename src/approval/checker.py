#!/usr/bin/env python3
"""Approval workflow checker for the Personal AI Employee — Silver Tier.

Scans /Pending_Approval for drafts with checked approval/rejection boxes.
Approved items are executed via MCP tools. Rejected items are archived.

Usage:
    python src/approval/checker.py --vault-path ./vault
    python src/approval/checker.py --vault-path ./vault --dry-run
"""

import argparse
import json
import logging
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("approval_checker")

STALE_HOURS = 24


def _check_approval_state(content: str) -> str:
    """Parse checkbox state from approval draft content.

    Returns: 'approved', 'rejected', or 'pending'
    """
    if re.search(r"-\s*\[x\]\s*Approved", content, re.IGNORECASE):
        return "approved"
    if re.search(r"-\s*\[x\]\s*Rejected", content, re.IGNORECASE):
        return "rejected"
    return "pending"


def _extract_action_content(post) -> dict:
    """Extract action parameters from an approval draft."""
    fm = post.metadata
    body = post.content

    result = {
        "type": fm.get("type", "unknown"),
        "target": fm.get("target", ""),
        "mcp_tool": fm.get("mcp_tool", ""),
        "linked_item": fm.get("linked_item"),
    }

    # Extract content section from body
    content_match = re.search(
        r"## Content\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL
    )
    if content_match:
        result["content"] = content_match.group(1).strip()

    # Extract subject for emails
    subject_match = re.search(r"\*\*Subject\*\*:\s*(.+)", body)
    if subject_match:
        result["subject"] = subject_match.group(1).strip()

    return result


def _create_mcp_log(
    vault_path: Path,
    tool: str,
    result_status: str,
    linked_draft: str,
    parameters: dict,
    error_message: str = "",
):
    """Create an MCP action log entry in /Logs."""
    logs_dir = vault_path / "Logs"
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc)
    ts_str = timestamp.strftime("%Y%m%dT%H%M%S")
    filename = f"mcp-{ts_str}-{tool}.md"

    # Sanitize parameters (remove secrets)
    safe_params = {
        k: v for k, v in parameters.items()
        if k not in ("password", "token", "secret", "app_password")
    }
    # Truncate long content
    if "body" in safe_params and len(str(safe_params["body"])) > 200:
        safe_params["body"] = str(safe_params["body"])[:200] + "..."

    log_post = frontmatter.Post(
        content=(
            f"# MCP Action Log: {tool}\n\n"
            f"**Tool**: {tool}\n"
            f"**Result**: {'✅ Success' if result_status == 'success' else '❌ Failure'}\n"
            f"**Time**: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"{error_message if error_message else 'Action completed successfully.'}\n"
        ),
        type="mcp_action",
        tool=tool,
        result=result_status,
        error_message=error_message or None,
        timestamp=timestamp.isoformat(),
        linked_draft=linked_draft,
        parameters=safe_params,
    )

    log_path = logs_dir / filename
    log_path.write_text(frontmatter.dumps(log_post), encoding="utf-8")
    logger.info("Created MCP log: %s", filename)
    return log_path


def _execute_mcp_action(action: dict, vault_path: Path, draft_name: str, dry_run: bool) -> bool:
    """Execute an MCP tool action. Returns True on success."""
    tool = action.get("mcp_tool", "")

    if dry_run:
        logger.info("[DRY RUN] Would execute %s with target=%s", tool, action.get("target"))
        _create_mcp_log(vault_path, tool, "success", draft_name, action, "Dry run — no action taken.")
        return True

    try:
        if tool == "email_send":
            from src.mcp.tools.email_send import send_email
            result = send_email(
                to=action.get("target", ""),
                subject=action.get("subject", ""),
                body=action.get("content", ""),
            )
        elif tool == "mastodon_post":
            from src.mcp.tools.mastodon_post import post_to_mastodon
            result = post_to_mastodon(content=action.get("content", ""))
        elif tool == "facebook_post":
            from src.mcp.tools.facebook_post import post_to_facebook
            result = post_to_facebook(message=action.get("content", ""))
        elif tool == "instagram_post":
            from src.mcp.tools.instagram_post import post_to_instagram
            result = post_to_instagram(
                caption=action.get("content", ""),
                image_url=action.get("target", ""),
            )
        elif tool == "x_post":
            from src.mcp.tools.x_post import post_to_x
            result = post_to_x(text=action.get("content", ""))
        elif tool == "linkedin_post":
            from src.mcp.tools.linkedin_post import post_to_linkedin
            result = post_to_linkedin(text=action.get("content", ""))
        else:
            raise ValueError(f"Unknown MCP tool: {tool}")

        if result.get("status") in ("sent", "posted"):
            _create_mcp_log(vault_path, tool, "success", draft_name, action)
            return True
        else:
            error_msg = result.get("error", "Unknown error")
            _create_mcp_log(vault_path, tool, "failure", draft_name, action, error_msg)
            return False

    except ImportError as e:
        error_msg = f"MCP tool module not available: {e}"
        logger.error(error_msg)
        _create_mcp_log(vault_path, tool, "failure", draft_name, action, error_msg)
        return False
    except Exception as e:
        error_msg = f"MCP execution error: {e}"
        logger.error(error_msg)
        _create_mcp_log(vault_path, tool, "failure", draft_name, action, error_msg)
        return False


def _move_to_done(file_path: Path, vault_path: Path, new_status: str):
    """Move a draft to /Done with updated status."""
    post = frontmatter.load(str(file_path))
    post["status"] = new_status
    post["executed_date"] = datetime.now(timezone.utc).isoformat()

    done_path = vault_path / "Done" / file_path.name
    done_path.write_text(frontmatter.dumps(post), encoding="utf-8")
    file_path.unlink()
    logger.info("Moved %s to Done (status: %s)", file_path.name, new_status)


def check_approvals(vault_path: Path, dry_run: bool = False) -> dict:
    """Scan /Pending_Approval and process approved/rejected items.

    Returns summary dict with counts.
    """
    pending_dir = vault_path / "Pending_Approval"
    if not pending_dir.exists():
        logger.info("No /Pending_Approval folder found.")
        return {"executed": 0, "rejected": 0, "pending": 0, "failed": 0}

    md_files = sorted(pending_dir.glob("*.md"), key=lambda f: f.stat().st_mtime)
    if not md_files:
        logger.info("No pending approvals.")
        return {"executed": 0, "rejected": 0, "pending": 0, "failed": 0}

    counts = {"executed": 0, "rejected": 0, "pending": 0, "failed": 0}

    for file_path in md_files:
        try:
            post = frontmatter.load(str(file_path))
            state = _check_approval_state(post.content)

            if state == "approved":
                action = _extract_action_content(post)
                success = _execute_mcp_action(action, vault_path, file_path.name, dry_run)
                if success:
                    _move_to_done(file_path, vault_path, "executed")
                    counts["executed"] += 1
                else:
                    _move_to_done(file_path, vault_path, "failed")
                    counts["failed"] += 1

            elif state == "rejected":
                _move_to_done(file_path, vault_path, "rejected")
                counts["rejected"] += 1

            else:
                # Check if stale (>24 hours)
                created = post.get("created_date")
                if created:
                    try:
                        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        age_hours = (
                            datetime.now(timezone.utc) - created_dt
                        ).total_seconds() / 3600
                        if age_hours > STALE_HOURS:
                            logger.warning(
                                "Draft %s is stale (%.1f hours). Flagging.",
                                file_path.name, age_hours,
                            )
                    except (ValueError, TypeError):
                        pass
                counts["pending"] += 1

        except Exception as e:
            logger.error("Error processing %s: %s", file_path.name, e)
            counts["failed"] += 1

    logger.info(
        "Processed approvals: %d executed, %d rejected, %d pending, %d failed",
        counts["executed"], counts["rejected"], counts["pending"], counts["failed"],
    )
    return counts


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Approval checker for the Personal AI Employee."
    )
    parser.add_argument(
        "--vault-path", required=True, help="Path to the Obsidian vault root."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse approvals but don't execute MCP tools.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    vault_path = Path(args.vault_path).resolve()
    check_approvals(vault_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
