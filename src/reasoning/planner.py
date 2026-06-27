#!/usr/bin/env python3
"""Plan generator for the Personal AI Employee — Silver Tier.

Generates Plan.md files with checkbox steps for complex vault items.
Plans are linked to the original item and created in /Needs_Action.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

from src.watchers.base_watcher import slugify


def _extract_steps(body: str, subject: str) -> list[str]:
    """Extract actionable steps from item body text."""
    steps = []

    # Try to extract numbered items
    numbered = re.findall(r"^\s*\d+[\.\)]\s*(.+)$", body, re.MULTILINE)
    if numbered:
        for item in numbered:
            steps.append(item.strip())
        return steps

    # Try to extract from bullet points
    bullets = re.findall(r"^\s*[-*]\s+(.+)$", body, re.MULTILINE)
    if bullets:
        for item in bullets:
            steps.append(item.strip())
        return steps

    # Try to split by action verbs
    sentences = re.split(r"[.;]\s+", body)
    action_verbs = (
        "review", "prepare", "draft", "send", "gather", "create",
        "update", "check", "verify", "compile", "organize", "contact",
        "schedule", "reply", "respond", "forward", "share",
    )
    for sentence in sentences:
        sentence = sentence.strip()
        if any(v in sentence.lower() for v in action_verbs) and len(sentence) > 10:
            steps.append(sentence)

    # Fallback: generate generic steps
    if not steps:
        steps = [
            f"Review: {subject}",
            "Analyze content and determine required actions",
            "Execute necessary actions",
            "Follow up and confirm completion",
        ]

    return steps


def generate_plan(item_path: Path, vault_path: Path) -> Path:
    """Generate a Plan.md with checkbox steps for a complex vault item.

    Args:
        item_path: Path to the vault item in /Needs_Action.
        vault_path: Path to the vault root.

    Returns:
        Path to the created Plan.md file.
    """
    post = frontmatter.load(str(item_path))

    subject = post.get("subject", "Unknown Task")
    sender = post.get("from", "unknown")
    priority = post.get("priority", "normal")
    body = post.content

    steps = _extract_steps(body, subject)
    now_iso = datetime.now(timezone.utc).isoformat()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    slug = slugify(subject)
    plan_filename = f"plan-{timestamp}-{slug}.md"

    # Build checkbox list
    steps_md = "\n".join(f"- [ ] {step}" for step in steps)

    # Build plan content
    plan_content = (
        f"# Plan: {subject}\n\n"
        f"**Original item**: {item_path.name}\n"
        f"**From**: {sender}\n\n"
        f"## Steps\n\n"
        f"{steps_md}\n\n"
        f"## Notes\n\n"
        f"- Steps requiring external actions will generate approval drafts in /Pending_Approval\n"
        f"- Check off steps as you complete them\n"
    )

    # Create Plan.md with frontmatter
    plan_post = frontmatter.Post(
        content=plan_content,
        type="plan",
        linked_item=item_path.name,
        status="in_progress",
        priority=priority,
        created_date=now_iso,
        total_steps=len(steps),
        completed_steps=0,
    )

    plan_path = vault_path / "Needs_Action" / plan_filename
    plan_path.write_text(frontmatter.dumps(plan_post), encoding="utf-8")

    # Update original item to link to plan
    post["status"] = "planned"
    post["classification"] = "complex"
    post["linked_plan"] = plan_filename
    item_path.write_text(frontmatter.dumps(post), encoding="utf-8")

    return plan_path
