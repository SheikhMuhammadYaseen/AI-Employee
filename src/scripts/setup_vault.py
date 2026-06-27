#!/usr/bin/env python3
"""Idempotent Obsidian vault setup script for the Personal AI Employee.

Creates the vault directory structure with standard folders and seed files.
Running multiple times is safe — existing files are never overwritten.

Usage:
    python src/scripts/setup_vault.py --vault-path ./vault
    python src/scripts/setup_vault.py --vault-path ./vault --verbose
"""

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

FOLDERS = ["Inbox", "Needs_Action", "Done", "Pending_Approval", "Logs", "Plans"]

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

SEED_FILES = {
    "Dashboard.md": "dashboard_template.md",
    "Company_Handbook.md": "handbook_template.md",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Create an Obsidian vault for the Personal AI Employee."
    )
    parser.add_argument(
        "--vault-path",
        required=True,
        help="Path where the vault should be created.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output for each operation.",
    )
    return parser.parse_args(argv)


def create_vault(vault_path: Path, verbose: bool = False) -> list[str]:
    """Create vault structure. Returns list of created paths."""
    created = []

    # Create root directory
    try:
        vault_path.mkdir(parents=True, exist_ok=True)
        if verbose:
            print(f"  Vault root: {vault_path}")
    except PermissionError:
        print(f"ERROR: Permission denied: {vault_path}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"ERROR: Cannot create vault at {vault_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Create folders
    for folder_name in FOLDERS:
        folder = vault_path / folder_name
        try:
            folder.mkdir(exist_ok=True)
            # Add .gitkeep so Obsidian sees empty folders
            gitkeep = folder / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
                created.append(str(gitkeep))
            if verbose:
                print(f"  Folder: {folder}")
        except PermissionError:
            print(f"ERROR: Permission denied: {folder}", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"ERROR: Cannot create folder {folder}: {e}", file=sys.stderr)
            sys.exit(1)

    # Create seed files (only if they don't exist)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for target_name, template_name in SEED_FILES.items():
        target = vault_path / target_name
        if target.exists():
            if verbose:
                print(f"  Skipped (exists): {target}")
            continue

        template = TEMPLATE_DIR / template_name
        if not template.exists():
            print(
                f"WARNING: Template not found: {template}. "
                f"Creating empty {target_name}.",
                file=sys.stderr,
            )
            target.touch()
            created.append(str(target))
            continue

        try:
            content = template.read_text(encoding="utf-8")
            # Replace date placeholders
            content = content.replace("{last_updated}", now_iso)
            content = content.replace("{last_edited}", now_iso)
            target.write_text(content, encoding="utf-8")
            created.append(str(target))
            if verbose:
                print(f"  Created: {target}")
        except PermissionError:
            print(f"ERROR: Permission denied: {target}", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"ERROR: Cannot write {target}: {e}", file=sys.stderr)
            sys.exit(1)

    return created


def main(argv=None):
    args = parse_args(argv)
    vault_path = Path(args.vault_path).resolve()

    print(f"Setting up vault at: {vault_path}")
    created = create_vault(vault_path, verbose=args.verbose)

    if created:
        print(f"\nCreated {len(created)} new item(s):")
        for path in created:
            print(f"  + {path}")
    else:
        print("\nVault already complete. No changes made.")

    print("\nDone. Open this folder as a vault in Obsidian.")


if __name__ == "__main__":
    main()
