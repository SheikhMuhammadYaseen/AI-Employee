"""Tests for the approval checker — Silver Tier (T025)."""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import frontmatter
import pytest

from src.approval.checker import (
    _check_approval_state,
    _extract_action_content,
    check_approvals,
)


# ---------------------------------------------------------------------------
# Approval state parsing tests
# ---------------------------------------------------------------------------

class TestCheckApprovalState:
    def test_approved_detected(self):
        content = "Some text\n- [x] Approved\nMore text"
        assert _check_approval_state(content) == "approved"

    def test_rejected_detected(self):
        content = "Some text\n- [x] Rejected\nMore text"
        assert _check_approval_state(content) == "rejected"

    def test_pending_when_unchecked(self):
        content = "Some text\n- [ ] Approved\n- [ ] Rejected"
        assert _check_approval_state(content) == "pending"

    def test_approved_case_insensitive(self):
        content = "- [X] APPROVED"
        assert _check_approval_state(content) == "approved"

    def test_no_checkboxes_is_pending(self):
        content = "Just some text without checkboxes."
        assert _check_approval_state(content) == "pending"


# ---------------------------------------------------------------------------
# Action content extraction tests
# ---------------------------------------------------------------------------

class TestExtractActionContent:
    def test_extracts_type_and_target(self):
        post = frontmatter.Post(
            content="## Content\n\nHello world\n\n## Approval",
            type="social_post",
            target="mastodon",
            mcp_tool="mastodon_post",
        )
        result = _extract_action_content(post)
        assert result["type"] == "social_post"
        assert result["target"] == "mastodon"
        assert result["mcp_tool"] == "mastodon_post"
        assert result["content"] == "Hello world"

    def test_extracts_email_subject(self):
        post = frontmatter.Post(
            content="**Subject**: Test Email\n\n## Content\n\nEmail body here\n\n## Approval",
            type="email",
            target="test@example.com",
            mcp_tool="email_send",
        )
        result = _extract_action_content(post)
        assert result["subject"] == "Test Email"


# ---------------------------------------------------------------------------
# Full approval workflow tests
# ---------------------------------------------------------------------------

class TestCheckApprovals:
    def _create_draft(self, vault_path, name, state="pending", mcp_tool="mastodon_post", hours_old=0):
        """Helper to create a test approval draft."""
        pending = vault_path / "Pending_Approval"
        pending.mkdir(parents=True, exist_ok=True)
        (vault_path / "Done").mkdir(exist_ok=True)
        (vault_path / "Logs").mkdir(exist_ok=True)

        created = datetime.now(timezone.utc) - timedelta(hours=hours_old)

        if state == "approved":
            checkbox = "- [x] Approved\n- [ ] Rejected"
        elif state == "rejected":
            checkbox = "- [ ] Approved\n- [x] Rejected"
        else:
            checkbox = "- [ ] Approved\n- [ ] Rejected"

        post = frontmatter.Post(
            content=f"## Content\n\nTest content\n\n## Approval\n\n{checkbox}",
            type="social_post",
            target="mastodon",
            mcp_tool=mcp_tool,
            status="pending",
            created_date=created.isoformat(),
        )
        path = pending / name
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
        return path

    def test_rejected_draft_moves_to_done(self, tmp_path):
        self._create_draft(tmp_path, "rejected-draft.md", state="rejected")
        counts = check_approvals(tmp_path, dry_run=False)
        assert counts["rejected"] == 1
        assert (tmp_path / "Done" / "rejected-draft.md").exists()
        assert not (tmp_path / "Pending_Approval" / "rejected-draft.md").exists()

    def test_pending_draft_left_in_place(self, tmp_path):
        self._create_draft(tmp_path, "pending-draft.md", state="pending")
        counts = check_approvals(tmp_path, dry_run=False)
        assert counts["pending"] == 1
        assert (tmp_path / "Pending_Approval" / "pending-draft.md").exists()

    def test_stale_draft_counted(self, tmp_path):
        self._create_draft(tmp_path, "stale-draft.md", state="pending", hours_old=25)
        counts = check_approvals(tmp_path, dry_run=False)
        assert counts["pending"] == 1

    @patch("src.approval.checker._execute_mcp_action", return_value=True)
    def test_approved_draft_executes_and_moves(self, mock_exec, tmp_path):
        self._create_draft(tmp_path, "approved-draft.md", state="approved")
        counts = check_approvals(tmp_path, dry_run=False)
        assert counts["executed"] == 1
        assert mock_exec.called

    @patch("src.approval.checker._execute_mcp_action", return_value=False)
    def test_mcp_failure_handled_gracefully(self, mock_exec, tmp_path):
        self._create_draft(tmp_path, "fail-draft.md", state="approved")
        counts = check_approvals(tmp_path, dry_run=False)
        assert counts["failed"] == 1

    def test_empty_pending_folder(self, tmp_path):
        (tmp_path / "Pending_Approval").mkdir(parents=True)
        counts = check_approvals(tmp_path, dry_run=False)
        assert counts == {"executed": 0, "rejected": 0, "pending": 0, "failed": 0}

    def test_no_pending_folder(self, tmp_path):
        counts = check_approvals(tmp_path, dry_run=False)
        assert counts == {"executed": 0, "rejected": 0, "pending": 0, "failed": 0}
