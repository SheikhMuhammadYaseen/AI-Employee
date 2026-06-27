"""Integration tests for watcher pipeline — Silver Tier (T045)."""

from pathlib import Path

import frontmatter
import pytest

from src.watchers.base_watcher import WatcherState, BaseWatcher, slugify
from src.reasoning.classifier import classify
from src.reasoning.planner import generate_plan


class DummyWatcher(BaseWatcher):
    """Concrete watcher for testing."""
    def poll_once(self) -> int:
        return 0


class TestWatcherPipeline:
    """Test that watchers → reasoning → planning chain works."""

    def _setup_vault(self, tmp_path):
        for folder in ["Needs_Action", "Pending_Approval", "Done", "Logs"]:
            (tmp_path / folder).mkdir(parents=True, exist_ok=True)
        return tmp_path

    def test_two_watchers_no_state_conflict(self, tmp_path):
        vault = self._setup_vault(tmp_path)

        w1 = DummyWatcher(vault, "gmail", 60)
        w2 = DummyWatcher(vault, "whatsapp", 10)

        # Each watcher has its own state file
        assert "gmail" in w1.state.state_path.name
        assert "whatsapp" in w2.state.state_path.name
        assert w1.state.state_path != w2.state.state_path

        # Both can load and save independently
        w1.state.load()
        w2.state.load()
        w1.state.mark_processed("gmail_id_1")
        w2.state.mark_processed("whatsapp_id_1")
        w1.state.save()
        w2.state.save()

        assert w1.state.is_processed("gmail_id_1")
        assert not w1.state.is_processed("whatsapp_id_1")
        assert w2.state.is_processed("whatsapp_id_1")
        assert not w2.state.is_processed("gmail_id_1")

    def test_watcher_creates_item_then_classifier_works(self, tmp_path):
        vault = self._setup_vault(tmp_path)
        w = DummyWatcher(vault, "test", 60)

        # Simulate watcher creating an item
        path = w.create_vault_item(
            item_type="email",
            sender="boss@company.com",
            subject="Prepare quarterly report",
            date_iso="2026-02-12T10:00:00Z",
            body="1. Gather sales data\n2. Compile into spreadsheet\n3. Create presentation\n4. Review with team",
            source_id="email_123",
        )

        # Classifier should detect complex
        post = frontmatter.load(str(path))
        result = classify(post.metadata, post.content)
        assert result == "complex"

    def test_complex_item_gets_plan(self, tmp_path):
        vault = self._setup_vault(tmp_path)
        w = DummyWatcher(vault, "test", 60)

        path = w.create_vault_item(
            item_type="email",
            sender="boss@company.com",
            subject="Prepare quarterly report",
            date_iso="2026-02-12T10:00:00Z",
            body="1. Gather sales data\n2. Compile analysis\n3. Create presentation",
            source_id="email_456",
        )

        # Generate plan
        plan_path = generate_plan(path, vault)

        assert plan_path.exists()
        plan_post = frontmatter.load(str(plan_path))
        assert plan_post["type"] == "plan"
        assert plan_post["total_steps"] == 3
        assert "- [ ]" in plan_post.content

        # Original item updated
        orig_post = frontmatter.load(str(path))
        assert orig_post["status"] == "planned"

    def test_action_required_item_classified(self, tmp_path):
        vault = self._setup_vault(tmp_path)
        w = DummyWatcher(vault, "test", 60)

        path = w.create_vault_item(
            item_type="whatsapp",
            sender="+1234567890",
            subject="Reply to client",
            date_iso="2026-02-12T10:00:00Z",
            body="Please reply to the client and send them the proposal.",
            source_id="wa_789",
        )

        post = frontmatter.load(str(path))
        result = classify(post.metadata, post.content)
        assert result == "action_required"

    def test_simple_item_classified(self, tmp_path):
        vault = self._setup_vault(tmp_path)
        w = DummyWatcher(vault, "test", 60)

        path = w.create_vault_item(
            item_type="email",
            sender="noreply@newsletter.com",
            subject="Weekly digest",
            date_iso="2026-02-12T10:00:00Z",
            body="Here is your weekly summary of industry news.",
            source_id="email_simple",
        )

        post = frontmatter.load(str(path))
        result = classify(post.metadata, post.content)
        assert result == "simple"
