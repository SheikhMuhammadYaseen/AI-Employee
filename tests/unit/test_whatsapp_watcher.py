"""Tests for WhatsApp watcher — Silver Tier (T015)."""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import frontmatter
import pytest

from src.watchers.whatsapp_watcher import WhatsAppWatcher, _message_hash


# ---------------------------------------------------------------------------
# Message hash tests
# ---------------------------------------------------------------------------

class TestMessageHash:
    def test_consistent_hash(self):
        h1 = _message_hash("Alice", "12:00", "Hello world")
        h2 = _message_hash("Alice", "12:00", "Hello world")
        assert h1 == h2

    def test_different_messages_different_hash(self):
        h1 = _message_hash("Alice", "12:00", "Hello")
        h2 = _message_hash("Bob", "12:00", "Hello")
        assert h1 != h2

    def test_hash_is_16_chars(self):
        h = _message_hash("sender", "time", "content")
        assert len(h) == 16

    def test_long_content_truncated(self):
        long_msg = "a" * 500
        raw = f"sender|time|{long_msg[:100]}"
        expected = hashlib.sha256(raw.encode()).hexdigest()[:16]
        assert _message_hash("sender", "time", long_msg) == expected


# ---------------------------------------------------------------------------
# Keyword matching tests
# ---------------------------------------------------------------------------

class TestKeywordMatching:
    def setup_method(self):
        self.tmp = Path("__test_not_used__")

    def _make_watcher(self, tmp_path, keywords=None):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)
        w = WhatsAppWatcher(
            vault_path=vault,
            interval=10,
            keywords=keywords or ["urgent", "asap", "deadline", "emergency"],
        )
        return w

    def test_urgent_keyword_detected(self, tmp_path):
        w = self._make_watcher(tmp_path)
        assert w._is_urgent("This is URGENT please respond") is True

    def test_asap_keyword_detected(self, tmp_path):
        w = self._make_watcher(tmp_path)
        assert w._is_urgent("Need this ASAP") is True

    def test_non_urgent_message_skipped(self, tmp_path):
        w = self._make_watcher(tmp_path)
        assert w._is_urgent("Hey, how are you doing?") is False

    def test_case_insensitive_matching(self, tmp_path):
        w = self._make_watcher(tmp_path)
        assert w._is_urgent("EMERGENCY meeting now") is True

    def test_custom_keywords(self, tmp_path):
        w = self._make_watcher(tmp_path, keywords=["help", "critical"])
        assert w._is_urgent("I need help with this") is True
        assert w._is_urgent("This is urgent") is False


# ---------------------------------------------------------------------------
# Vault item creation tests (via poll_once with mocked DOM)
# ---------------------------------------------------------------------------

class TestWhatsAppVaultItem:
    def test_vault_item_has_whatsapp_type(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)
        w = WhatsAppWatcher(vault_path=vault, interval=10)
        w.state.load()

        path = w.create_vault_item(
            item_type="whatsapp",
            sender="+1234567890",
            subject="Urgent delivery",
            date_iso="2026-02-12T10:00:00Z",
            body="Package arriving urgently",
            source_id="hash123",
            extra_frontmatter={"priority": "high"},
        )

        post = frontmatter.load(str(path))
        assert post["type"] == "whatsapp"
        assert post["from"] == "+1234567890"
        assert post["status"] == "pending"
        assert post["priority"] == "high"


# ---------------------------------------------------------------------------
# State tracking tests
# ---------------------------------------------------------------------------

class TestWhatsAppState:
    def test_state_file_uses_whatsapp_source(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)
        w = WhatsAppWatcher(vault_path=vault)
        assert "whatsapp" in w.state.state_path.name

    def test_processed_messages_tracked(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)
        w = WhatsAppWatcher(vault_path=vault)
        w.state.load()
        w.state.mark_processed("msg_hash_1")
        w.state.save()
        assert w.state.is_processed("msg_hash_1")


# ---------------------------------------------------------------------------
# Lock file tests
# ---------------------------------------------------------------------------

class TestWhatsAppLock:
    def test_lock_file_uses_whatsapp_name(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)
        w = WhatsAppWatcher(vault_path=vault)
        assert "whatsapp" in w.lock.lock_path.name

    def test_lock_prevents_concurrent_instances(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "Needs_Action").mkdir(parents=True)
        w1 = WhatsAppWatcher(vault_path=vault)
        w2 = WhatsAppWatcher(vault_path=vault)
        assert w1.lock.acquire() is True
        assert w2.lock.acquire() is False
        w1.lock.release()
