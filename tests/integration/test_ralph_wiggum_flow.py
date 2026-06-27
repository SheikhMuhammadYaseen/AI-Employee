"""Integration test for Ralph Wiggum autonomous loop (T047)."""

import os
import tempfile
import unittest

from src.reasoning.ralph_wiggum import RalphWiggumLoop


class TestRalphWiggumFlow(unittest.TestCase):
    """Test Ralph Wiggum loop with real Plan.md files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, "Pending_Approval"), exist_ok=True)
        os.makedirs(os.path.join(self.tmpdir, "Logs"), exist_ok=True)

    def _write_plan(self, steps):
        plan_path = os.path.join(self.tmpdir, "Plan.md")
        with open(plan_path, "w") as f:
            f.write("# Test Plan\n\n")
            for step in steps:
                f.write(f"- [ ] {step}\n")
        return plan_path

    def test_simple_plan_completes(self):
        plan_path = self._write_plan([
            "Read the inbox",
            "Analyze findings",
            "Log the results",
        ])

        loop = RalphWiggumLoop(self.tmpdir)
        result = loop.run(plan_path)
        assert result["status"] == "TASK_COMPLETE"
        assert result["steps_completed"] == 3

    def test_mixed_plan_pauses_for_approval(self):
        plan_path = self._write_plan([
            "Read the inbox",
            "Send email to client",
            "Log the results",
        ])

        loop = RalphWiggumLoop(self.tmpdir)
        result = loop.run(plan_path)
        assert result["status"] == "AWAITING_APPROVAL"
        assert result["steps_awaiting"] >= 1

        pending_dir = os.path.join(self.tmpdir, "Pending_Approval")
        drafts = os.listdir(pending_dir)
        assert len(drafts) >= 1

    def test_plan_updates_with_progress(self):
        plan_path = self._write_plan([
            "Read data",
            "Summarize results",
        ])

        loop = RalphWiggumLoop(self.tmpdir)
        loop.run(plan_path)

        with open(plan_path) as f:
            content = f.read()
        assert "[x]" in content

    def test_five_step_mixed_plan(self):
        plan_path = self._write_plan([
            "Check inbox for new items",
            "Analyze the weekly reports",
            "Send email update to team",
            "Post summary to Mastodon",
            "Archive processed items",
        ])

        loop = RalphWiggumLoop(self.tmpdir)
        result = loop.run(plan_path)
        assert result["status"] == "AWAITING_APPROVAL"
        assert result["steps_awaiting"] >= 2


if __name__ == "__main__":
    unittest.main()
