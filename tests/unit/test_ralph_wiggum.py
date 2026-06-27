"""Unit tests for Ralph Wiggum autonomous loop (T046)."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from src.reasoning.ralph_wiggum import (
    RalphWiggumLoop,
    LoopTimeout,
    LoopMaxIterations,
    MAX_ITERATIONS,
    MAX_DURATION_MINUTES,
    MAX_NESTING_DEPTH,
)


class TestParsePlan(unittest.TestCase):
    """Test plan parsing."""

    def _write_plan(self, tmpdir, content):
        path = os.path.join(tmpdir, "Plan.md")
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_parse_simple_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = self._write_plan(tmpdir, "- [ ] Read the inbox\n- [ ] Summarize emails\n")
            loop = RalphWiggumLoop(tmpdir)
            steps = loop.parse_plan(plan)
            assert len(steps) == 2
            assert steps[0]["text"] == "Read the inbox"
            assert steps[0]["status"] == "pending"

    def test_parse_completed_steps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = self._write_plan(tmpdir, "- [x] Already done\n- [ ] Still pending\n")
            loop = RalphWiggumLoop(tmpdir)
            steps = loop.parse_plan(plan)
            assert steps[0]["status"] == "completed"
            assert steps[1]["status"] == "pending"

    def test_parse_empty_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = self._write_plan(tmpdir, "# My Plan\n\nNo checkboxes here.\n")
            loop = RalphWiggumLoop(tmpdir)
            steps = loop.parse_plan(plan)
            assert len(steps) == 0

    def test_plan_not_found(self):
        loop = RalphWiggumLoop("/tmp")
        with self.assertRaises(FileNotFoundError):
            loop.parse_plan("/nonexistent/Plan.md")


class TestClassifyStep(unittest.TestCase):
    """Test step classification."""

    def test_classify_simple(self):
        loop = RalphWiggumLoop("/tmp")
        assert loop._classify_step("Read the inbox") == "simple"
        assert loop._classify_step("Analyze the data") == "simple"
        assert loop._classify_step("Summarize findings") == "simple"

    def test_classify_action_required(self):
        loop = RalphWiggumLoop("/tmp")
        assert loop._classify_step("Send email to client") == "action_required"
        assert loop._classify_step("Post to Mastodon") == "action_required"
        assert loop._classify_step("Create invoice for consulting") == "action_required"

    def test_classify_default_simple(self):
        loop = RalphWiggumLoop("/tmp")
        assert loop._classify_step("Do something unknown") == "simple"


class TestExecuteStep(unittest.TestCase):
    """Test step execution."""

    def test_execute_simple_step(self):
        loop = RalphWiggumLoop("/tmp")
        step = {"index": 0, "text": "Read inbox", "step_type": "simple", "status": "pending"}
        result = loop.execute_step(step)
        assert result["status"] == "completed"
        assert step["status"] == "completed"


class TestCreateApprovalDraft(unittest.TestCase):
    """Test approval draft creation."""

    def test_create_draft(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loop = RalphWiggumLoop(tmpdir)
            step = {
                "index": 0,
                "text": "Send email to client",
                "step_type": "action_required",
                "status": "pending",
                "line": "- [ ] Send email to client",
            }
            result = loop.create_approval_draft(step)
            assert result["status"] == "awaiting_approval"
            assert os.path.exists(result["draft_path"])
            assert step["status"] == "awaiting_approval"

            # Verify draft content
            with open(result["draft_path"]) as f:
                content = f.read()
            assert "email_send" in content
            assert "Approved" in content


class TestInferMcpTool(unittest.TestCase):
    """Test MCP tool inference from step text."""

    def test_infer_email(self):
        loop = RalphWiggumLoop("/tmp")
        assert loop._infer_mcp_tool("Send email to John") == "email_send"

    def test_infer_mastodon(self):
        loop = RalphWiggumLoop("/tmp")
        assert loop._infer_mcp_tool("Post to Mastodon") == "mastodon_post"

    def test_infer_facebook(self):
        loop = RalphWiggumLoop("/tmp")
        assert loop._infer_mcp_tool("Post to Facebook page") == "facebook_post"

    def test_infer_x(self):
        loop = RalphWiggumLoop("/tmp")
        assert loop._infer_mcp_tool("Tweet the announcement") == "x_post"

    def test_infer_invoice(self):
        loop = RalphWiggumLoop("/tmp")
        assert loop._infer_mcp_tool("Create invoice for services") == "create_invoice"

    def test_infer_unknown(self):
        loop = RalphWiggumLoop("/tmp")
        assert loop._infer_mcp_tool("Do something unusual") == "unknown"


class TestIterationLimits(unittest.TestCase):
    """Test loop iteration and time limits."""

    def test_max_iterations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = os.path.join(tmpdir, "Plan.md")
            # Create a plan that can never complete (no checkboxes will be marked)
            with open(plan_path, "w") as f:
                f.write("- [ ] Wait forever\n")

            loop = RalphWiggumLoop(tmpdir, max_iterations=2)
            # Prevent the step from actually completing
            loop.parse_plan(plan_path)
            loop.start_time = datetime.now(timezone.utc)

            # Force pending on each iteration
            with patch.object(loop, 'execute_step', side_effect=lambda s: None):
                with self.assertRaises(LoopMaxIterations):
                    for _ in range(3):
                        loop.run_iteration()

    def test_time_limit(self):
        loop = RalphWiggumLoop("/tmp", max_duration_minutes=0)
        loop.start_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        with self.assertRaises(LoopTimeout):
            loop._check_time_limit()

    def test_nesting_depth_exceeded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = os.path.join(tmpdir, "Plan.md")
            with open(plan_path, "w") as f:
                f.write("- [ ] Test\n")

            loop = RalphWiggumLoop(tmpdir, nesting_depth=MAX_NESTING_DEPTH + 1)
            result = loop.run(plan_path)
            assert result["status"] == "error"
            assert "nesting" in result["error"].lower()


class TestRunFullLoop(unittest.TestCase):
    """Test full loop execution."""

    def test_run_all_simple_steps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = os.path.join(tmpdir, "Plan.md")
            with open(plan_path, "w") as f:
                f.write("- [ ] Read data\n- [ ] Analyze results\n- [ ] Log findings\n")

            loop = RalphWiggumLoop(tmpdir)
            result = loop.run(plan_path)
            assert result["status"] == "TASK_COMPLETE"
            assert result["steps_completed"] == 3
            assert result["steps_total"] == 3

    def test_run_with_action_steps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = os.path.join(tmpdir, "Plan.md")
            with open(plan_path, "w") as f:
                f.write("- [ ] Read inbox\n- [ ] Send email reply\n- [ ] Log action\n")

            loop = RalphWiggumLoop(tmpdir)
            result = loop.run(plan_path)
            assert result["status"] == "AWAITING_APPROVAL"
            assert result["steps_awaiting"] >= 1

    def test_run_empty_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = os.path.join(tmpdir, "Plan.md")
            with open(plan_path, "w") as f:
                f.write("# Empty plan\n")

            loop = RalphWiggumLoop(tmpdir)
            result = loop.run(plan_path)
            assert result["status"] == "TASK_COMPLETE"
            assert result["iterations"] == 0


class TestCheckApprovals(unittest.TestCase):
    """Test approval checking."""

    def test_check_approved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pending_dir = os.path.join(tmpdir, "Pending_Approval")
            os.makedirs(pending_dir)

            draft_path = os.path.join(pending_dir, "test-draft.md")
            with open(draft_path, "w") as f:
                f.write("---\ntype: loop-action\n---\n- [x] Approved\n- [ ] Rejected\n")

            loop = RalphWiggumLoop(tmpdir)
            loop.steps = [{"index": 0, "status": "awaiting_approval", "draft_path": draft_path}]

            processed = loop.check_approvals()
            assert 0 in processed
            assert loop.steps[0]["status"] == "completed"


class TestGetProgress(unittest.TestCase):
    """Test progress reporting."""

    def test_progress(self):
        loop = RalphWiggumLoop("/tmp")
        loop.steps = [
            {"status": "completed"},
            {"status": "pending"},
            {"status": "awaiting_approval"},
        ]
        loop.iteration = 2
        loop.status = "running"

        progress = loop.get_progress()
        assert progress["steps_total"] == 3
        assert progress["steps_completed"] == 1
        assert progress["steps_pending"] == 1
        assert progress["steps_awaiting"] == 1


if __name__ == "__main__":
    unittest.main()
