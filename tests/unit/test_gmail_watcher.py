"""Unit tests for gmail_watcher.py — state management, vault items, lock file."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
from watchers.gmail_watcher import (
    LockFile,
    WatcherState,
    _slugify,
    create_vault_item,
)


class TestWatcherState:
    """Tests for WatcherState — load, save, dedup, capping."""

    def test_load_creates_default_on_missing_file(self, tmp_path):
        state = WatcherState(tmp_path / ".watcher_state.json")
        state.load()
        assert state.data["source"] == "gmail"
        assert state.data["processed_ids"] == []

    def test_save_and_reload_preserves_ids(self, tmp_path):
        path = tmp_path / ".watcher_state.json"
        state = WatcherState(path)
        state.load()
        state.mark_processed("msg_001")
        state.mark_processed("msg_002")
        state.save()

        state2 = WatcherState(path)
        state2.load()
        assert "msg_001" in state2.data["processed_ids"]
        assert "msg_002" in state2.data["processed_ids"]

    def test_duplicate_ids_not_added(self, tmp_path):
        state = WatcherState(tmp_path / ".watcher_state.json")
        state.load()
        state.mark_processed("msg_001")
        state.mark_processed("msg_001")
        assert state.data["processed_ids"].count("msg_001") == 1

    def test_is_processed_returns_correct_result(self, tmp_path):
        state = WatcherState(tmp_path / ".watcher_state.json")
        state.load()
        state.mark_processed("msg_001")
        assert state.is_processed("msg_001") is True
        assert state.is_processed("msg_999") is False

    def test_caps_at_max_ids(self, tmp_path):
        state = WatcherState(tmp_path / ".watcher_state.json")
        state.load()
        for i in range(10_500):
            state.mark_processed(f"msg_{i:06d}")
        state.save()

        state2 = WatcherState(tmp_path / ".watcher_state.json")
        state2.load()
        assert len(state2.data["processed_ids"]) == 10_000
        # Oldest should be removed, newest should remain
        assert "msg_010499" in state2.data["processed_ids"]
        assert "msg_000000" not in state2.data["processed_ids"]

    def test_corrupt_state_file_resets(self, tmp_path):
        path = tmp_path / ".watcher_state.json"
        path.write_text("NOT VALID JSON", encoding="utf-8")
        state = WatcherState(path)
        state.load()
        assert state.data["processed_ids"] == []


class TestVaultItemCreation:
    """Tests for creating vault item Markdown files."""

    def test_creates_file_with_correct_frontmatter(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)

        email_data = {
            "source_id": "abc123",
            "from": "test@example.com",
            "subject": "Test Email Subject",
            "date": "2026-02-12T14:30:00Z",
            "body": "Hello, this is a test email body.",
        }

        result = create_vault_item(vault, email_data)
        assert result.exists()
        assert result.parent.name == "Needs_Action"

        import frontmatter as fm
        post = fm.load(str(result))
        assert post["type"] == "email"
        assert post["from"] == "test@example.com"
        assert post["subject"] == "Test Email Subject"
        assert post["status"] == "pending"
        assert post["source_id"] == "abc123"
        assert post.content == "Hello, this is a test email body."

    def test_filename_follows_convention(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)

        email_data = {
            "source_id": "xyz",
            "from": "a@b.com",
            "subject": "Meeting Invite",
            "date": "2026-02-12T10:00:00Z",
            "body": "content",
        }

        result = create_vault_item(vault, email_data)
        assert result.name.startswith("email-")
        assert "meeting-invite" in result.name
        assert result.suffix == ".md"


class TestSlugify:
    """Tests for the _slugify helper."""

    def test_basic_slugify(self):
        assert _slugify("Hello World") == "hello-world"

    def test_special_characters_removed(self):
        assert _slugify("Re: Budget $500!") == "re-budget-500"

    def test_max_length_enforced(self):
        result = _slugify("a" * 100, max_len=20)
        assert len(result) <= 20


class TestLockFile:
    """Tests for the PID-based lock file mechanism."""

    def test_acquire_creates_lock_with_pid(self, tmp_path):
        lock_path = tmp_path / ".watcher.lock"
        lock = LockFile(lock_path)
        lock.acquire()
        assert lock_path.exists()
        assert lock_path.read_text().strip() == str(os.getpid())
        lock.release()

    def test_release_removes_lock(self, tmp_path):
        lock_path = tmp_path / ".watcher.lock"
        lock = LockFile(lock_path)
        lock.acquire()
        lock.release()
        assert not lock_path.exists()

    def test_stale_lock_is_cleaned_up(self, tmp_path):
        lock_path = tmp_path / ".watcher.lock"
        # Write a fake PID that definitely doesn't exist
        lock_path.write_text("999999999")

        lock = LockFile(lock_path)
        # Should not raise — stale lock should be cleaned
        lock.acquire()
        assert lock_path.read_text().strip() == str(os.getpid())
        lock.release()

    def test_active_lock_prevents_acquisition(self, tmp_path):
        lock_path = tmp_path / ".watcher.lock"
        # Write current PID (simulating another running instance)
        lock_path.write_text(str(os.getpid()))

        lock = LockFile(lock_path)
        with pytest.raises(SystemExit):
            lock.acquire()
