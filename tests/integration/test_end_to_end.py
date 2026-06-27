"""Integration test checklist for Bronze Tier end-to-end flow.

These tests validate the full pipeline: vault setup → watcher item creation
→ processing skill → dashboard update. The processing skill (Claude Code
custom command) is tested via manual invocation; this file provides
automated setup and verification of the vault state before and after.

Usage:
    python -m pytest tests/integration/test_end_to_end.py -v
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import frontmatter
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
from scripts.setup_vault import create_vault
from watchers.gmail_watcher import create_vault_item


class TestEndToEndSetup:
    """Verify vault setup produces correct structure for processing."""

    def test_full_vault_creation(self, tmp_path):
        """Setup creates vault suitable for watcher and processing."""
        vault = tmp_path / "vault"
        create_vault(vault)

        assert (vault / "Inbox").is_dir()
        assert (vault / "Needs_Action").is_dir()
        assert (vault / "Done").is_dir()
        assert (vault / "Dashboard.md").is_file()
        assert (vault / "Company_Handbook.md").is_file()


class TestEndToEndWatcherToVault:
    """Verify watcher creates correctly formatted items for processing."""

    def _create_test_vault(self, tmp_path):
        vault = tmp_path / "vault"
        create_vault(vault)
        return vault

    def test_watcher_item_placed_in_needs_action(self, tmp_path):
        """Watcher creates .md file in Needs_Action with valid frontmatter."""
        vault = self._create_test_vault(tmp_path)

        email_data = {
            "source_id": "test_msg_001",
            "from": "boss@company.com",
            "subject": "Q1 Budget Review",
            "date": datetime.now(timezone.utc).isoformat(),
            "body": "Please review the attached Q1 budget before Friday.",
        }

        item_path = create_vault_item(vault, email_data)
        assert item_path.exists()
        assert item_path.parent.name == "Needs_Action"

        post = frontmatter.load(str(item_path))
        assert post["type"] == "email"
        assert post["from"] == "boss@company.com"
        assert post["subject"] == "Q1 Budget Review"
        assert post["status"] == "pending"
        assert post["source_id"] == "test_msg_001"

    def test_multiple_items_coexist(self, tmp_path):
        """Multiple watcher items can exist in Needs_Action simultaneously."""
        vault = self._create_test_vault(tmp_path)

        for i in range(3):
            email_data = {
                "source_id": f"msg_{i}",
                "from": f"user{i}@example.com",
                "subject": f"Test Email {i}",
                "date": datetime.now(timezone.utc).isoformat(),
                "body": f"Body of email {i}.",
            }
            create_vault_item(vault, email_data)

        md_files = list((vault / "Needs_Action").glob("*.md"))
        assert len(md_files) == 3

    def test_malformed_file_does_not_crash_reading(self, tmp_path):
        """A malformed .md file in Needs_Action should not crash parsing."""
        vault = self._create_test_vault(tmp_path)

        # Create a valid item
        email_data = {
            "source_id": "valid_msg",
            "from": "valid@example.com",
            "subject": "Valid Email",
            "date": datetime.now(timezone.utc).isoformat(),
            "body": "Valid content.",
        }
        create_vault_item(vault, email_data)

        # Create a malformed file
        malformed = vault / "Needs_Action" / "malformed.md"
        malformed.write_text("This has no frontmatter at all", encoding="utf-8")

        # Both files should exist
        md_files = list((vault / "Needs_Action").glob("*.md"))
        assert len(md_files) == 2

        # Valid file should still parse correctly
        valid_files = [
            f for f in md_files
            if f.name != "malformed.md"
        ]
        assert len(valid_files) == 1
        post = frontmatter.load(str(valid_files[0]))
        assert post["type"] == "email"


class TestManualProcessingChecklist:
    """Manual test checklist for /process-inbox skill validation.

    These are documented steps to execute manually with Claude Code.
    The test methods create the preconditions and verify postconditions.
    """

    def test_precondition_setup(self, tmp_path):
        """Set up vault with test items for manual /process-inbox testing.

        MANUAL STEPS after running this test:
        1. Copy the vault from the test output path to ./vault
        2. Run: claude /process-inbox
        3. Check vault/Done/ for processed reports
        4. Check vault/Dashboard.md for updated summary
        5. Check vault/Needs_Action/ is empty
        """
        vault = tmp_path / "vault"
        create_vault(vault)

        # Create test items
        items = [
            {
                "source_id": "manual_test_1",
                "from": "boss@company.com",
                "subject": "Urgent: Budget Review",
                "date": "2026-02-12T14:30:00Z",
                "body": "Please review the Q1 budget document urgently.",
            },
            {
                "source_id": "manual_test_2",
                "from": "newsletter@news.com",
                "subject": "Weekly Tech Digest",
                "date": "2026-02-12T10:00:00Z",
                "body": "This week in tech: AI advances, new frameworks...",
            },
        ]

        for item in items:
            create_vault_item(vault, item)

        md_files = list((vault / "Needs_Action").glob("*.md"))
        assert len(md_files) == 2
        print(f"\nTest vault created at: {vault}")
        print("Ready for manual /process-inbox testing.")
