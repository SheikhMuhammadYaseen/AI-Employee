"""Tests for the BaseWatcher shared infrastructure — Silver Tier."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import frontmatter
import pytest

from src.watchers.base_watcher import (
    BaseWatcher,
    LockFile,
    WatcherState,
    slugify,
)


# ---------------------------------------------------------------------------
# Concrete test subclass
# ---------------------------------------------------------------------------

class DummyWatcher(BaseWatcher):
    """Minimal concrete watcher for testing."""

    def poll_once(self) -> int:
        return 0


# ---------------------------------------------------------------------------
# WatcherState tests
# ---------------------------------------------------------------------------

class TestWatcherState:
    def test_load_creates_fresh_when_missing(self, tmp_path):
        state = WatcherState(tmp_path / ".state.json", source="test")
        state.load()
        assert state.data["source"] == "test"
        assert state.data["processed_ids"] == []

    def test_save_and_reload(self, tmp_path):
        state_path = tmp_path / ".state.json"
        state = WatcherState(state_path, source="test")
        state.mark_processed("id1")
        state.mark_processed("id2")
        state.save()

        state2 = WatcherState(state_path, source="test")
        state2.load()
        assert state2.is_processed("id1")
        assert state2.is_processed("id2")
        assert state2.data["last_poll"] is not None

    def test_is_processed(self, tmp_path):
        state = WatcherState(tmp_path / ".state.json", source="test")
        assert not state.is_processed("id1")
        state.mark_processed("id1")
        assert state.is_processed("id1")

    def test_duplicate_ids_not_added(self, tmp_path):
        state = WatcherState(tmp_path / ".state.json", source="test")
        state.mark_processed("id1")
        state.mark_processed("id1")
        assert state.data["processed_ids"].count("id1") == 1

    def test_caps_at_10k(self, tmp_path):
        state_path = tmp_path / ".state.json"
        state = WatcherState(state_path, source="test")
        for i in range(10_500):
            state.data["processed_ids"].append(f"id_{i}")
        state.save()

        state2 = WatcherState(state_path, source="test")
        state2.load()
        assert len(state2.data["processed_ids"]) == 10_000

    def test_corrupt_state_file(self, tmp_path):
        state_path = tmp_path / ".state.json"
        state_path.write_text("not json at all")
        state = WatcherState(state_path, source="test")
        state.load()
        assert state.data["processed_ids"] == []


# ---------------------------------------------------------------------------
# LockFile tests
# ---------------------------------------------------------------------------

class TestLockFile:
    def test_acquire_and_release(self, tmp_path):
        lock_path = tmp_path / ".test.lock"
        lock = LockFile(lock_path)
        assert lock.acquire() is True
        assert lock_path.exists()
        lock.release()
        assert not lock_path.exists()

    def test_stale_lock_removed(self, tmp_path):
        lock_path = tmp_path / ".test.lock"
        lock_path.write_text("99999999")  # Non-existent PID
        lock = LockFile(lock_path)
        assert lock.acquire() is True

    def test_active_lock_prevents_acquisition(self, tmp_path):
        lock_path = tmp_path / ".test.lock"
        lock_path.write_text(str(os.getpid()))  # Current process = alive
        lock = LockFile(lock_path)
        assert lock.acquire() is False


# ---------------------------------------------------------------------------
# Vault item creation tests
# ---------------------------------------------------------------------------

class TestCreateVaultItem:
    def test_creates_md_with_correct_frontmatter(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)

        watcher = DummyWatcher(vault, "test", 60)
        path = watcher.create_vault_item(
            item_type="whatsapp",
            sender="+1234567890",
            subject="Urgent delivery update",
            date_iso="2026-02-12T16:00:00Z",
            body="Package arriving today!",
            source_id="hash_abc123",
        )

        assert path.exists()
        post = frontmatter.load(str(path))
        assert post["type"] == "whatsapp"
        assert post["from"] == "+1234567890"
        assert post["status"] == "pending"
        assert post["source_id"] == "hash_abc123"
        assert "Package arriving today!" in post.content

    def test_filename_convention(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)

        watcher = DummyWatcher(vault, "test", 60)
        path = watcher.create_vault_item(
            item_type="whatsapp",
            sender="test",
            subject="Hello World",
            date_iso="2026-02-12T16:00:00Z",
            body="test",
            source_id="id1",
        )

        assert path.name.startswith("whatsapp-")
        assert path.name.endswith(".md")
        assert "hello-world" in path.name


# ---------------------------------------------------------------------------
# Slugify tests
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("Re: Meeting @ 3pm!") == "re-meeting-3pm"

    def test_max_length(self):
        result = slugify("a" * 100, max_len=20)
        assert len(result) <= 20
