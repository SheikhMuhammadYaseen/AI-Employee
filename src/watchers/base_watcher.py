#!/usr/bin/env python3
"""Base watcher class for the Personal AI Employee — Silver Tier.

Provides shared infrastructure for all watchers: state management,
lock files, vault item creation, and error handling. Specific watchers
(Gmail, WhatsApp) inherit from this base.

Usage:
    Subclass BaseWatcher and implement the `poll_once` method.
"""

import atexit
import json
import logging
import os
import re
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

logger = logging.getLogger(__name__)

MAX_PROCESSED_IDS = 10_000


# ---------------------------------------------------------------------------
# Lock file management
# ---------------------------------------------------------------------------

def _is_process_alive(pid: int) -> bool:
    """Check if a process with the given PID is alive."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


class LockFile:
    """PID-based lock file to prevent concurrent watcher instances."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._acquired = False

    def acquire(self) -> bool:
        """Acquire the lock. Returns True if successful, False if already held."""
        if self.lock_path.exists():
            try:
                existing_pid = int(self.lock_path.read_text().strip())
                if _is_process_alive(existing_pid):
                    logger.error(
                        "Watcher already running (PID: %d). Exiting.", existing_pid
                    )
                    return False
                else:
                    logger.warning(
                        "Stale lock file found (PID %d is dead). Removing.",
                        existing_pid,
                    )
                    self.lock_path.unlink()
            except (ValueError, OSError):
                logger.warning("Corrupt lock file. Removing.")
                self.lock_path.unlink(missing_ok=True)

        self.lock_path.write_text(str(os.getpid()))
        self._acquired = True
        atexit.register(self.release)
        return True

    def release(self) -> None:
        """Release the lock file."""
        if self._acquired and self.lock_path.exists():
            try:
                self.lock_path.unlink()
            except OSError:
                pass
            self._acquired = False


# ---------------------------------------------------------------------------
# Watcher state management
# ---------------------------------------------------------------------------

class WatcherState:
    """Manages the JSON state file tracking processed item IDs."""

    def __init__(self, state_path: Path, source: str = "unknown"):
        self.state_path = state_path
        self.source = source
        self.data = {"source": source, "last_poll": None, "processed_ids": []}

    def load(self) -> None:
        """Load state from disk, or initialize fresh if missing/corrupt."""
        if self.state_path.exists():
            try:
                self.data = json.loads(
                    self.state_path.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Corrupt state file, starting fresh: %s", e)
                self.data = {
                    "source": self.source,
                    "last_poll": None,
                    "processed_ids": [],
                }

    def save(self) -> None:
        """Save state to disk with timestamp and ID cap."""
        self.data["last_poll"] = datetime.now(timezone.utc).isoformat()
        ids = self.data["processed_ids"]
        if len(ids) > MAX_PROCESSED_IDS:
            self.data["processed_ids"] = ids[-MAX_PROCESSED_IDS:]
        self.state_path.write_text(
            json.dumps(self.data, indent=2), encoding="utf-8"
        )

    def is_processed(self, item_id: str) -> bool:
        """Check if an item has already been processed."""
        return item_id in self.data["processed_ids"]

    def mark_processed(self, item_id: str) -> None:
        """Mark an item as processed."""
        if item_id not in self.data["processed_ids"]:
            self.data["processed_ids"].append(item_id)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a filesystem-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")


# ---------------------------------------------------------------------------
# Base watcher class
# ---------------------------------------------------------------------------

class BaseWatcher(ABC):
    """Abstract base class for all watchers.

    Subclasses must implement `poll_once()` which is called on each cycle.
    """

    def __init__(self, vault_path: Path, source_name: str, interval: int = 60):
        self.vault_path = vault_path
        self.source_name = source_name
        self.interval = interval

        # Per-watcher state and lock files
        self.state = WatcherState(
            vault_path / f".watcher_state_{source_name}.json",
            source=source_name,
        )
        self.lock = LockFile(
            vault_path / f".watcher_{source_name}.lock"
        )

    def setup(self) -> bool:
        """Initialize watcher: acquire lock, load state. Returns True if ready."""
        needs_action = self.vault_path / "Needs_Action"
        if not needs_action.is_dir():
            logger.error(
                "Vault not found at %s. Run setup_vault.py first.", self.vault_path
            )
            return False

        if not self.lock.acquire():
            return False

        self.state.load()
        return True

    def create_vault_item(
        self,
        item_type: str,
        sender: str,
        subject: str,
        date_iso: str,
        body: str,
        source_id: str,
        extra_frontmatter: dict | None = None,
    ) -> Path:
        """Create a structured Markdown file in /Needs_Action."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        slug = slugify(subject)
        filename = f"{item_type}-{timestamp}-{slug}.md"

        fm_data = {
            "type": item_type,
            "from": sender,
            "subject": subject,
            "date": date_iso,
            "status": "pending",
            "suggested_actions": [],
            "source_id": source_id,
            "processed_date": None,
        }
        if extra_frontmatter:
            fm_data.update(extra_frontmatter)

        post = frontmatter.Post(content=body, **fm_data)

        target = self.vault_path / "Needs_Action" / filename
        try:
            target.write_text(frontmatter.dumps(post), encoding="utf-8")
            logger.info("Created vault item: %s", target.name)
            return target
        except OSError as e:
            logger.error("Failed to write vault item %s: %s", target, e)
            raise

    def cleanup(self) -> None:
        """Release lock and save state."""
        self.state.save()
        self.lock.release()

    @abstractmethod
    def poll_once(self) -> int:
        """Run a single poll cycle. Returns number of new items created.

        Subclasses must implement this method.
        """
        ...
