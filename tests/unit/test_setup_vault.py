"""Unit tests for setup_vault.py — Obsidian vault creation."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path so we can import the script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
from scripts.setup_vault import create_vault, main


class TestCreateVault:
    """Tests for the create_vault function."""

    def test_fresh_vault_creates_all_folders_and_files(self, tmp_path):
        """Given a fresh path, vault creation produces 3 folders + 2 seed files."""
        vault = tmp_path / "test_vault"
        created = create_vault(vault)

        assert vault.exists()
        assert (vault / "Inbox").is_dir()
        assert (vault / "Needs_Action").is_dir()
        assert (vault / "Done").is_dir()
        assert (vault / "Dashboard.md").is_file()
        assert (vault / "Company_Handbook.md").is_file()
        # .gitkeep files in each folder
        assert (vault / "Inbox" / ".gitkeep").exists()
        assert (vault / "Needs_Action" / ".gitkeep").exists()
        assert (vault / "Done" / ".gitkeep").exists()
        assert len(created) > 0

    def test_idempotent_rerun_does_not_overwrite(self, tmp_path):
        """Given an existing vault, re-running does not overwrite files."""
        vault = tmp_path / "test_vault"
        create_vault(vault)

        # Modify a file to detect overwrites
        dashboard = vault / "Dashboard.md"
        original_content = dashboard.read_text(encoding="utf-8")
        dashboard.write_text("CUSTOM CONTENT", encoding="utf-8")

        # Run again
        created = create_vault(vault)

        # File should NOT be overwritten
        assert dashboard.read_text(encoding="utf-8") == "CUSTOM CONTENT"
        # No new seed files created (only possibly .gitkeep if missing)
        seed_files_created = [
            p for p in created
            if p.endswith("Dashboard.md") or p.endswith("Company_Handbook.md")
        ]
        assert len(seed_files_created) == 0

    def test_dashboard_has_valid_frontmatter(self, tmp_path):
        """Dashboard.md should have YAML frontmatter with expected fields."""
        vault = tmp_path / "test_vault"
        create_vault(vault)

        content = (vault / "Dashboard.md").read_text(encoding="utf-8")
        assert content.startswith("---")
        assert "last_updated:" in content
        assert "items_pending:" in content
        assert "items_processed:" in content

    def test_handbook_has_valid_sections(self, tmp_path):
        """Company_Handbook.md should have Processing Rules, Preferences, Constraints."""
        vault = tmp_path / "test_vault"
        create_vault(vault)

        content = (vault / "Company_Handbook.md").read_text(encoding="utf-8")
        assert "## Processing Rules" in content
        assert "## Preferences" in content
        assert "## Constraints" in content


class TestMainCLI:
    """Tests for the CLI entry point."""

    def test_main_with_valid_path(self, tmp_path, capsys):
        """Main should succeed with a valid --vault-path."""
        vault = tmp_path / "cli_vault"
        main(["--vault-path", str(vault)])

        captured = capsys.readouterr()
        assert "Setting up vault at:" in captured.out
        assert "Done." in captured.out
        assert vault.exists()

    def test_main_with_verbose(self, tmp_path, capsys):
        """Main with --verbose should print detailed output."""
        vault = tmp_path / "verbose_vault"
        main(["--vault-path", str(vault), "--verbose"])

        captured = capsys.readouterr()
        assert "Folder:" in captured.out or "Created:" in captured.out
