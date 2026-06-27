#!/usr/bin/env python3
"""Gmail watcher for the Personal AI Employee — Bronze Tier.

Polls Gmail for new unread emails and creates structured Markdown files
in the vault's /Needs_Action folder. Uses OAuth2 with gmail.readonly scope.

Usage:
    python src/watchers/gmail_watcher.py --vault-path ./vault
    python src/watchers/gmail_watcher.py --vault-path ./vault --interval 120
    python src/watchers/gmail_watcher.py --vault-path ./vault --credentials ./creds.json
"""

import argparse
import atexit
import base64
import json
import logging
import os
import re
import signal
import sys
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

import frontmatter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("gmail_watcher")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MAX_PROCESSED_IDS = 10_000
MAX_BODY_CHARS = 500


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

    def acquire(self) -> None:
        if self.lock_path.exists():
            try:
                existing_pid = int(self.lock_path.read_text().strip())
                if _is_process_alive(existing_pid):
                    logger.error(
                        "Watcher already running (PID: %d). Exiting.", existing_pid
                    )
                    sys.exit(1)
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

    def release(self) -> None:
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
    """Manages the JSON state file tracking processed email IDs."""

    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.data = {"source": "gmail", "last_poll": None, "processed_ids": []}

    def load(self) -> None:
        if self.state_path.exists():
            try:
                self.data = json.loads(
                    self.state_path.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Corrupt state file, starting fresh: %s", e)
                self.data = {
                    "source": "gmail",
                    "last_poll": None,
                    "processed_ids": [],
                }

    def save(self) -> None:
        self.data["last_poll"] = datetime.now(timezone.utc).isoformat()
        # Cap processed IDs at MAX_PROCESSED_IDS
        ids = self.data["processed_ids"]
        if len(ids) > MAX_PROCESSED_IDS:
            self.data["processed_ids"] = ids[-MAX_PROCESSED_IDS:]
        self.state_path.write_text(
            json.dumps(self.data, indent=2), encoding="utf-8"
        )

    def is_processed(self, msg_id: str) -> bool:
        return msg_id in self.data["processed_ids"]

    def mark_processed(self, msg_id: str) -> None:
        if msg_id not in self.data["processed_ids"]:
            self.data["processed_ids"].append(msg_id)


# ---------------------------------------------------------------------------
# Gmail API helpers
# ---------------------------------------------------------------------------

def authenticate(credentials_path: Path, token_path: Path):
    """Authenticate with Gmail API using OAuth2. Returns a service object."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                logger.error(
                    "Re-authentication required. Delete %s and re-run.",
                    token_path,
                )
                sys.exit(1)
        else:
            if not credentials_path.exists():
                logger.error(
                    "credentials.json not found at %s", credentials_path
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_unread_ids(service) -> list[str]:
    """Fetch IDs of all unread messages."""
    results = (
        service.users()
        .messages()
        .list(userId="me", q="is:unread")
        .execute()
    )
    return [msg["id"] for msg in results.get("messages", [])]


def fetch_message(service, msg_id: str) -> dict:
    """Fetch full message details and extract structured data."""
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=msg_id, format="full")
        .execute()
    )

    headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}
    sender = headers.get("from", "unknown")
    subject = headers.get("subject", "(no subject)")
    date_str = headers.get("date", "")

    # Parse date to ISO format
    try:
        # Gmail dates can vary; store raw if parsing fails
        internal_date_ms = int(msg.get("internalDate", 0))
        date_iso = datetime.fromtimestamp(
            internal_date_ms / 1000, tz=timezone.utc
        ).isoformat()
    except (ValueError, OSError):
        date_iso = date_str

    # Extract plain text body
    body = _extract_body(msg["payload"])
    if len(body) > MAX_BODY_CHARS:
        body = body[:MAX_BODY_CHARS] + "..."

    return {
        "source_id": msg_id,
        "from": sender,
        "subject": subject,
        "date": date_iso,
        "body": body,
    }


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text from message payload."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode(
            "utf-8", errors="replace"
        )

    for part in payload.get("parts", []):
        text = _extract_body(part)
        if text:
            return text

    # Fallback: try to decode body data even if mime type doesn't match
    if payload.get("body", {}).get("data"):
        raw = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
            "utf-8", errors="replace"
        )
        # Strip HTML tags if present
        clean = re.sub(r"<[^>]+>", "", unescape(raw))
        return clean.strip()

    return ""


# ---------------------------------------------------------------------------
# Vault item creation
# ---------------------------------------------------------------------------

def _slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a filesystem-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")


def create_vault_item(vault_path: Path, email_data: dict) -> Path:
    """Create a structured Markdown file in /Needs_Action for an email."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    slug = _slugify(email_data["subject"])
    filename = f"email-{timestamp}-{slug}.md"

    post = frontmatter.Post(
        content=email_data["body"],
        type="email",
        **{
            "from": email_data["from"],
            "subject": email_data["subject"],
            "date": email_data["date"],
            "status": "pending",
            "suggested_actions": [],
            "source_id": email_data["source_id"],
            "processed_date": None,
        },
    )

    target = vault_path / "Needs_Action" / filename
    try:
        target.write_text(frontmatter.dumps(post), encoding="utf-8")
        logger.info("Created vault item: %s", target.name)
        return target
    except OSError as e:
        logger.error("Failed to write vault item %s: %s", target, e)
        raise


# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Gmail watcher for the Personal AI Employee."
    )
    parser.add_argument(
        "--vault-path", required=True, help="Path to the Obsidian vault root."
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds (default: 60).",
    )
    parser.add_argument(
        "--credentials",
        default="./credentials.json",
        help="Path to OAuth2 credentials file (default: ./credentials.json).",
    )
    return parser.parse_args(argv)


def poll_once(service, state: WatcherState, vault_path: Path) -> int:
    """Run a single poll cycle. Returns number of new items created."""
    unread_ids = fetch_unread_ids(service)
    new_count = 0

    for msg_id in unread_ids:
        if state.is_processed(msg_id):
            continue

        try:
            email_data = fetch_message(service, msg_id)
            create_vault_item(vault_path, email_data)
            state.mark_processed(msg_id)
            new_count += 1
        except Exception as e:
            logger.error("Failed to process message %s: %s", msg_id, e)

    state.save()
    return new_count


def main(argv=None):
    args = parse_args(argv)
    vault_path = Path(args.vault_path).resolve()
    credentials_path = Path(args.credentials).resolve()
    token_path = credentials_path.parent / "token.json"
    interval = args.interval

    # Validate vault exists
    needs_action = vault_path / "Needs_Action"
    if not needs_action.is_dir():
        logger.error(
            "Vault not found at %s. Run setup_vault.py first.", vault_path
        )
        sys.exit(1)

    # Acquire lock
    lock = LockFile(vault_path / ".watcher.lock")
    lock.acquire()

    # Handle signals for clean shutdown
    def _signal_handler(signum, frame):
        logger.info("Received signal %d. Shutting down.", signum)
        lock.release()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Authenticate
    logger.info("Authenticating with Gmail API...")
    service = authenticate(credentials_path, token_path)
    logger.info("Authenticated. Polling every %d seconds.", interval)

    # Load state
    state = WatcherState(vault_path / ".watcher_state.json")
    state.load()

    # Polling loop
    while True:
        try:
            new_count = poll_once(service, state, vault_path)
            if new_count > 0:
                logger.info("Created %d new vault item(s).", new_count)
            else:
                logger.debug("No new emails.")
        except Exception as e:
            logger.error("Poll failed: %s. Retrying in %ds.", e, interval)

        time.sleep(interval)


if __name__ == "__main__":
    main()
