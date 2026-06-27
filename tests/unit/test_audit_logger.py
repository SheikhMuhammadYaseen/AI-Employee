"""Unit tests for structured audit logger (T011)."""

import os
import tempfile
import unittest
from datetime import datetime, timezone

from src.logging.audit_logger import (
    log_action,
    sanitize_params,
    summarize_week,
    _get_log_path,
)


class TestSanitizeParams(unittest.TestCase):
    """Test parameter sanitization."""

    def test_redacts_password(self):
        result = sanitize_params({"password": "secret123"})
        assert result["password"] == "***REDACTED***"

    def test_redacts_token(self):
        result = sanitize_params({"access_token": "tok_abc"})
        assert result["access_token"] == "***REDACTED***"

    def test_redacts_api_key(self):
        result = sanitize_params({"api_key": "key123"})
        assert result["api_key"] == "***REDACTED***"

    def test_truncates_long_strings(self):
        result = sanitize_params({"body": "x" * 250})
        assert "[250 chars]" in result["body"]

    def test_preserves_safe_values(self):
        result = sanitize_params({"partner": "Test Corp", "amount": 1500})
        assert result["partner"] == "Test Corp"
        assert result["amount"] == 1500

    def test_nested_dict_sanitized(self):
        result = sanitize_params({"config": {"api_secret": "s3cr3t"}})
        assert result["config"]["api_secret"] == "***REDACTED***"

    def test_non_dict_returned_as_is(self):
        assert sanitize_params("just a string") == "just a string"


class TestLogAction(unittest.TestCase):
    """Test log entry writing."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, "Logs"), exist_ok=True)

    def test_creates_log_file(self):
        log_action(self.tmpdir, "mcp", "create_invoice", {"result": "success"})

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = os.path.join(self.tmpdir, "Logs", f"mcp-{today}.md")
        assert os.path.exists(log_path)

    def test_log_entry_format(self):
        log_action(
            self.tmpdir, "mcp", "create_invoice",
            {
                "server": "mcp_accounting",
                "tool": "create_invoice",
                "parameters": {"partner": "Test Corp"},
                "result": "success",
                "duration_seconds": 1.5,
            },
        )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = os.path.join(self.tmpdir, "Logs", f"mcp-{today}.md")
        with open(log_path, "r") as f:
            content = f.read()

        assert "### [" in content
        assert "create_invoice" in content
        assert "**Server**: mcp_accounting" in content
        assert "**Result**: success" in content
        assert "**Duration**: 1.5s" in content

    def test_daily_rotation(self):
        """Different dates create different files."""
        log_action(self.tmpdir, "mcp", "action1")

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = os.path.join(self.tmpdir, "Logs", f"mcp-{today}.md")
        assert os.path.exists(log_path)

    def test_multiple_entries_same_file(self):
        log_action(self.tmpdir, "mcp", "action1", {"result": "success"})
        log_action(self.tmpdir, "mcp", "action2", {"result": "failure"})

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = os.path.join(self.tmpdir, "Logs", f"mcp-{today}.md")
        with open(log_path, "r") as f:
            content = f.read()

        assert content.count("### [") == 2
        assert "entry_count: 2" in content

    def test_different_categories(self):
        log_action(self.tmpdir, "mcp", "tool_call")
        log_action(self.tmpdir, "approval", "approve_draft")

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert os.path.exists(os.path.join(self.tmpdir, "Logs", f"mcp-{today}.md"))
        assert os.path.exists(os.path.join(self.tmpdir, "Logs", f"approval-{today}.md"))

    def test_error_message_logged(self):
        log_action(
            self.tmpdir, "mcp", "failed_call",
            {"result": "failure", "error_message": "Connection refused"},
        )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = os.path.join(self.tmpdir, "Logs", f"mcp-{today}.md")
        with open(log_path, "r") as f:
            content = f.read()

        assert "**Error**: Connection refused" in content

    def test_linked_artifact(self):
        log_action(
            self.tmpdir, "approval", "execute",
            {"linked_artifact": "email-send-20260212.md"},
        )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = os.path.join(self.tmpdir, "Logs", f"approval-{today}.md")
        with open(log_path, "r") as f:
            content = f.read()

        assert "email-send-20260212.md" in content

    def test_sensitive_params_sanitized_in_log(self):
        log_action(
            self.tmpdir, "mcp", "post",
            {"parameters": {"access_token": "real_token", "message": "hello"}},
        )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = os.path.join(self.tmpdir, "Logs", f"mcp-{today}.md")
        with open(log_path, "r") as f:
            content = f.read()

        assert "real_token" not in content
        assert "***REDACTED***" in content


class TestSummarizeWeek(unittest.TestCase):
    """Test weekly log summary for CEO Briefing."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_empty_logs_returns_zero(self):
        result = summarize_week(
            self.tmpdir,
            datetime(2026, 2, 3, tzinfo=timezone.utc),
            datetime(2026, 2, 9, tzinfo=timezone.utc),
        )
        assert result["total_entries"] == 0

    def test_counts_entries(self):
        log_action(self.tmpdir, "mcp", "call1", {"result": "success"})
        log_action(self.tmpdir, "mcp", "call2", {"result": "failure", "error_message": "err"})

        now = datetime.now(timezone.utc)
        result = summarize_week(self.tmpdir, now, now)

        assert result["total_entries"] == 2
        assert result["categories"]["mcp"]["entries"] == 2
        assert result["categories"]["mcp"]["successes"] == 1
        assert result["categories"]["mcp"]["failures"] == 1

    def test_error_patterns_extracted(self):
        log_action(
            self.tmpdir, "mcp", "fail",
            {"result": "failure", "error_message": "Connection refused"},
        )

        now = datetime.now(timezone.utc)
        result = summarize_week(self.tmpdir, now, now)

        assert len(result["error_patterns"]) == 1
        assert "Connection refused" in result["error_patterns"][0]["error"]


if __name__ == "__main__":
    unittest.main()
