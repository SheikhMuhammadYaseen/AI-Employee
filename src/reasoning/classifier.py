#!/usr/bin/env python3
"""Item classifier for the Personal AI Employee — Silver Tier.

Classifies vault items into three categories:
- simple: Single-action items (process immediately, move to /Done)
- complex: Multi-step items (generate Plan.md with checkboxes)
- action_required: Items needing external action (create draft in /Pending_Approval)
"""

import re

# Keywords that suggest external action is needed
ACTION_KEYWORDS = [
    "reply", "respond", "send", "forward", "post", "publish",
    "email", "message", "contact", "call", "schedule meeting",
    "share", "tweet", "announce",
]

# Keywords that suggest a complex multi-step task
COMPLEX_KEYWORDS = [
    "prepare", "gather", "review and", "compile", "organize",
    "steps:", "step 1", "first,", "then,", "finally,",
    "1.", "2.", "3.", "plan", "report",
]


def classify(frontmatter: dict, body: str) -> str:
    """Classify a vault item as 'simple', 'complex', or 'action_required'.

    Args:
        frontmatter: Parsed YAML frontmatter dict from the vault item.
        body: The body text content of the vault item.

    Returns:
        One of: "simple", "complex", "action_required"
    """
    # If classification is already set, respect it
    if frontmatter.get("classification"):
        return frontmatter["classification"]

    text = body.lower()
    subject = str(frontmatter.get("subject", "")).lower()
    combined = f"{subject} {text}"

    # Count matches for each category
    action_score = sum(1 for kw in ACTION_KEYWORDS if kw in combined)
    complex_score = sum(1 for kw in COMPLEX_KEYWORDS if kw in combined)

    # Check for numbered lists (strong complex indicator)
    numbered_list = len(re.findall(r"^\s*\d+[\.\)]\s", body, re.MULTILINE))
    if numbered_list >= 2:
        complex_score += 3

    # Check for multiple action verbs (strong complex indicator)
    action_verbs = len(re.findall(
        r"\b(review|prepare|draft|send|gather|create|update|check|verify)\b",
        combined,
    ))
    if action_verbs >= 3:
        complex_score += 2

    # Priority: action_required > complex > simple
    if action_score >= 2:
        return "action_required"
    if complex_score >= 2:
        return "complex"
    if action_score >= 1:
        return "action_required"

    result = "simple"

    # Gold Tier: Audit log classification decisions
    try:
        from src.logging.audit_logger import log_action
        vault_path = frontmatter.get("_vault_path", "")
        if vault_path:
            log_action(vault_path, "classification", "classify_item", details={
                "result": result,
                "context": subject[:100] if subject else "unknown",
            })
    except Exception:
        pass  # Don't fail classification on logging errors

    return result
