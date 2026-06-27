"""Tests for the plan generator — Silver Tier (T020)."""

from pathlib import Path

import frontmatter
import pytest

from src.reasoning.planner import generate_plan, _extract_steps


# ---------------------------------------------------------------------------
# Step extraction tests
# ---------------------------------------------------------------------------

class TestExtractSteps:
    def test_numbered_list_extraction(self):
        body = "1. Gather data\n2. Analyze trends\n3. Write report"
        steps = _extract_steps(body, "Test")
        assert len(steps) == 3
        assert "Gather data" in steps[0]

    def test_bullet_list_extraction(self):
        body = "- Review document\n- Draft response\n- Send email"
        steps = _extract_steps(body, "Test")
        assert len(steps) == 3

    def test_action_verb_extraction(self):
        body = "Review the proposal. Draft a response to the client. Send the final version."
        steps = _extract_steps(body, "Test")
        assert len(steps) >= 2

    def test_fallback_generic_steps(self):
        body = "Something vague."
        steps = _extract_steps(body, "My Task")
        assert len(steps) >= 3
        assert any("My Task" in s for s in steps)


# ---------------------------------------------------------------------------
# Plan generation tests
# ---------------------------------------------------------------------------

class TestGeneratePlan:
    def _create_item(self, vault_path, subject="Test Task", body="1. Step one\n2. Step two\n3. Step three"):
        """Create a test vault item in /Needs_Action."""
        needs_action = vault_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)

        post = frontmatter.Post(
            content=body,
            type="email",
            subject=subject,
            status="pending",
            priority="normal",
            **{"from": "test@example.com"},
        )
        item_path = needs_action / "test-item.md"
        item_path.write_text(frontmatter.dumps(post), encoding="utf-8")
        return item_path

    def test_plan_created_with_frontmatter(self, tmp_path):
        item_path = self._create_item(tmp_path)
        plan_path = generate_plan(item_path, tmp_path)

        assert plan_path.exists()
        post = frontmatter.load(str(plan_path))
        assert post["type"] == "plan"
        assert post["status"] == "in_progress"
        assert post["linked_item"] == "test-item.md"

    def test_plan_has_checkbox_steps(self, tmp_path):
        item_path = self._create_item(tmp_path)
        plan_path = generate_plan(item_path, tmp_path)

        content = plan_path.read_text(encoding="utf-8")
        assert "- [ ]" in content

    def test_plan_step_count_matches(self, tmp_path):
        item_path = self._create_item(tmp_path, body="1. First\n2. Second\n3. Third")
        plan_path = generate_plan(item_path, tmp_path)

        post = frontmatter.load(str(plan_path))
        assert post["total_steps"] == 3

    def test_original_item_updated(self, tmp_path):
        item_path = self._create_item(tmp_path)
        plan_path = generate_plan(item_path, tmp_path)

        post = frontmatter.load(str(item_path))
        assert post["status"] == "planned"
        assert post["classification"] == "complex"
        assert post.get("linked_plan") is not None

    def test_plan_links_to_original(self, tmp_path):
        item_path = self._create_item(tmp_path)
        plan_path = generate_plan(item_path, tmp_path)

        content = plan_path.read_text(encoding="utf-8")
        assert "test-item.md" in content
