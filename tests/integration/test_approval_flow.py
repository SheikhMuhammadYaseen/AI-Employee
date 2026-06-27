"""Integration tests for the approval workflow — Silver Tier (T044)."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import frontmatter
import pytest

from src.approval.checker import check_approvals


class TestApprovalFlowIntegration:
    """End-to-end approval flow: draft → approve/reject → execute → Done."""

    def _setup_vault(self, tmp_path):
        """Create a minimal vault structure."""
        for folder in ["Needs_Action", "Pending_Approval", "Done", "Logs"]:
            (tmp_path / folder).mkdir(parents=True, exist_ok=True)
        return tmp_path

    def _create_draft(self, vault, name, content_text, mcp_tool, state="pending"):
        if state == "approved":
            checkbox = "- [x] Approved\n- [ ] Rejected"
        elif state == "rejected":
            checkbox = "- [ ] Approved\n- [x] Rejected"
        else:
            checkbox = "- [ ] Approved\n- [ ] Rejected"

        post = frontmatter.Post(
            content=(
                f"## Content\n\n{content_text}\n\n"
                f"## Approval\n\n{checkbox}"
            ),
            type="social_post",
            target="mastodon",
            mcp_tool=mcp_tool,
            status="pending",
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        path = vault / "Pending_Approval" / name
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
        return path

    @patch("src.approval.checker._execute_mcp_action", return_value=True)
    def test_approved_draft_executed_and_moved_to_done(self, mock_exec, tmp_path):
        vault = self._setup_vault(tmp_path)
        self._create_draft(vault, "test-post.md", "Hello world!", "mastodon_post", "approved")

        counts = check_approvals(vault)

        assert counts["executed"] == 1
        assert (vault / "Done" / "test-post.md").exists()
        assert not (vault / "Pending_Approval" / "test-post.md").exists()

        # Check Done file has executed status
        done_post = frontmatter.load(str(vault / "Done" / "test-post.md"))
        assert done_post["status"] == "executed"

    def test_rejected_draft_moved_to_done(self, tmp_path):
        vault = self._setup_vault(tmp_path)
        self._create_draft(vault, "rejected.md", "Bad post", "mastodon_post", "rejected")

        counts = check_approvals(vault)

        assert counts["rejected"] == 1
        assert (vault / "Done" / "rejected.md").exists()
        done_post = frontmatter.load(str(vault / "Done" / "rejected.md"))
        assert done_post["status"] == "rejected"

    @patch("src.approval.checker._execute_mcp_action", return_value=False)
    def test_mcp_failure_logged_and_moved_to_done(self, mock_exec, tmp_path):
        vault = self._setup_vault(tmp_path)
        self._create_draft(vault, "fail.md", "Will fail", "mastodon_post", "approved")

        counts = check_approvals(vault)

        assert counts["failed"] == 1
        done_post = frontmatter.load(str(vault / "Done" / "fail.md"))
        assert done_post["status"] == "failed"
