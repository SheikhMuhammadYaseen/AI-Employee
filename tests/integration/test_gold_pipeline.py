"""Integration test for full Gold Tier pipeline (T071)."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock


class TestGoldPipeline(unittest.TestCase):
    """End-to-end Gold Tier pipeline test."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        for d in ["Needs_Action", "Pending_Approval", "Done", "Logs", "Plans"]:
            os.makedirs(os.path.join(self.tmpdir, d), exist_ok=True)

    def test_classify_plan_execute_log(self):
        """Test: classify item -> create plan -> ralph wiggum -> log."""
        from src.reasoning.classifier import classify
        from src.reasoning.ralph_wiggum import RalphWiggumLoop
        from src.logging.audit_logger import log_action

        # Step 1: Classify a complex item
        fm = {"subject": "Weekly report preparation"}
        body = "1. Gather data\n2. Analyze trends\n3. Summarize findings"
        classification = classify(fm, body)
        assert classification == "complex"

        # Step 2: Create a plan
        plan_path = os.path.join(self.tmpdir, "Plans", "weekly-report.md")
        with open(plan_path, "w") as f:
            f.write("# Weekly Report Plan\n\n")
            f.write("- [ ] Read the latest data\n")
            f.write("- [ ] Analyze trends\n")
            f.write("- [ ] Summarize findings\n")

        # Step 3: Run Ralph Wiggum loop
        loop = RalphWiggumLoop(self.tmpdir)
        result = loop.run(plan_path)
        assert result["status"] == "TASK_COMPLETE"

        # Step 4: Log the action
        log_action(self.tmpdir, "loop", "ralph_wiggum_complete", details={
            "result": "success",
            "steps_completed": result["steps_completed"],
        })

        # Verify log exists
        log_files = os.listdir(os.path.join(self.tmpdir, "Logs"))
        assert any("loop-" in f for f in log_files)

    def test_service_health_tracking(self):
        """Test service health tracking across components."""
        from src.health.service_health import ServiceHealthTracker

        tracker = ServiceHealthTracker(self.tmpdir)

        tracker.update_health("odoo", True)
        tracker.update_health("mastodon", True)
        tracker.update_health("facebook", False, "Connection refused")

        health = tracker.get_all_health()
        assert health["odoo"]["status"] == "operational"
        assert health["facebook"]["error_count"] == 1

    def test_audit_log_weekly_summary(self):
        """Test audit log weekly summary generation."""
        from src.logging.audit_logger import log_action, summarize_week
        from datetime import datetime, timezone, timedelta

        log_action(self.tmpdir, "mcp", "create_invoice", details={"result": "success"})
        log_action(self.tmpdir, "mcp", "send_email", details={"result": "failure", "error_message": "SMTP error"})
        log_action(self.tmpdir, "approval", "approve_email", details={"result": "success"})

        now = datetime.now(timezone.utc)
        summary = summarize_week(self.tmpdir, now - timedelta(days=1), now + timedelta(days=1))
        assert summary["total_entries"] >= 2

    def test_mcp_router_tool_lookup(self):
        """Test MCP router can find tools across servers."""
        from src.mcp.router import get_server_for_tool, list_all_tools

        assert get_server_for_tool("create_invoice") == "gold-accounting"
        assert get_server_for_tool("facebook_post") == "gold-social"
        assert get_server_for_tool("email_send") == "gold-communications"

        all_tools = list_all_tools()
        assert len(all_tools) >= 10


if __name__ == "__main__":
    unittest.main()
