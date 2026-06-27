#!/usr/bin/env python3
"""WhatsApp watcher for the Personal AI Employee — Silver Tier.

Monitors WhatsApp Web for urgent messages using Playwright browser
automation. Creates structured Markdown files in the vault's /Needs_Action
folder for messages matching urgent keywords.

Usage:
    python src/watchers/whatsapp_watcher.py --vault-path ./vault
    python src/watchers/whatsapp_watcher.py --vault-path ./vault --headless
    python src/watchers/whatsapp_watcher.py --vault-path ./vault --keywords "urgent,asap,help"
"""

import argparse
import hashlib
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("whatsapp_watcher")

# Import base watcher from Silver infrastructure
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.watchers.base_watcher import BaseWatcher

DEFAULT_KEYWORDS = ["urgent", "asap", "deadline", "emergency"]
MAX_RETRIES = 3
RETRY_WAIT = 30


def _message_hash(sender: str, timestamp: str, content: str) -> str:
    """Generate a unique hash for a WhatsApp message."""
    raw = f"{sender}|{timestamp}|{content[:100]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class WhatsAppWatcher(BaseWatcher):
    """Monitors WhatsApp Web for urgent messages via Playwright."""

    def __init__(
        self,
        vault_path: Path,
        interval: int = 10,
        session_path: str = "~/.whatsapp_session",
        keywords: list[str] | None = None,
        headless: bool = False,
    ):
        super().__init__(vault_path, "whatsapp", interval)
        self.session_path = Path(session_path).expanduser()
        self.keywords = keywords or DEFAULT_KEYWORDS
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    def _launch_browser(self):
        """Launch Playwright browser with persistent session."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error(
                "Playwright not installed. Run: pip install playwright && "
                "playwright install chromium"
            )
            sys.exit(1)

        self.session_path.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        self.page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    def _wait_for_connection(self) -> bool:
        """Wait for WhatsApp Web to be connected. Returns True if connected."""
        logger.info("Waiting for WhatsApp Web connection...")
        for attempt in range(MAX_RETRIES):
            try:
                # Wait for the main chat list to appear (indicates connected)
                self.page.wait_for_selector(
                    'div[aria-label="Chat list"], div[data-testid="chat-list"]',
                    timeout=60_000,
                )
                logger.info("WhatsApp Web connected.")
                return True
            except Exception:
                # Check if QR code is shown
                qr = self.page.query_selector(
                    'canvas[aria-label="Scan this QR code to link a device"], '
                    'div[data-testid="qrcode"]'
                )
                if qr:
                    logger.warning(
                        "WhatsApp session expired. Please scan the QR code "
                        "in the browser window to re-authenticate."
                    )
                    if self.headless:
                        logger.error(
                            "Cannot scan QR code in headless mode. "
                            "Run with --headless false first."
                        )
                        return False
                    # Wait longer for user to scan
                    try:
                        self.page.wait_for_selector(
                            'div[aria-label="Chat list"], div[data-testid="chat-list"]',
                            timeout=120_000,
                        )
                        logger.info("QR scanned, WhatsApp Web connected.")
                        return True
                    except Exception:
                        pass

                logger.warning(
                    "Connection attempt %d/%d failed. Retrying in %ds...",
                    attempt + 1, MAX_RETRIES, RETRY_WAIT,
                )
                time.sleep(RETRY_WAIT)

        logger.error("Failed to connect after %d attempts.", MAX_RETRIES)
        return False

    def _is_urgent(self, message_text: str) -> bool:
        """Check if a message matches urgent keywords."""
        text_lower = message_text.lower()
        return any(kw.lower() in text_lower for kw in self.keywords)

    def _extract_new_messages(self) -> list[dict]:
        """Extract new messages from WhatsApp Web DOM."""
        messages = []
        try:
            # WhatsApp Web 2024/2025 structure uses role="row" for message rows
            # and spans with title attribute containing message text
            msg_rows = self.page.query_selector_all('div[role="row"]')

            for row in msg_rows[-20:]:  # Check last 20 message rows
                try:
                    # Extract message text from span with title attribute
                    text_el = row.query_selector('span[title]')
                    if not text_el:
                        # Fallback: look for span with dir="ltr" inside _ak8k class
                        text_el = row.query_selector('div._ak8k span[dir="ltr"]')

                    text = ""
                    if text_el:
                        # Try title attribute first, then inner text
                        text = text_el.get_attribute("title") or text_el.inner_text()

                    if not text:
                        continue

                    # Extract sender (phone number or contact name)
                    sender_el = row.query_selector('span[title^="+"], span._ao3e')
                    sender = "Unknown"
                    if sender_el:
                        sender = sender_el.get_attribute("title") or sender_el.inner_text()

                    # Extract timestamp
                    time_el = row.query_selector('span[class*="x1fgarty"]')
                    timestamp = time_el.inner_text() if time_el else ""

                    messages.append({
                        "sender": sender,
                        "text": text,
                        "timestamp": timestamp,
                    })
                except Exception:
                    continue
        except Exception as e:
            logger.warning("Error extracting messages: %s", e)

        return messages

    def poll_once(self) -> int:
        """Poll WhatsApp Web for new urgent messages."""
        messages = self._extract_new_messages()
        new_count = 0

        for msg in messages:
            if not self._is_urgent(msg["text"]):
                continue

            msg_id = _message_hash(msg["sender"], msg["timestamp"], msg["text"])
            if self.state.is_processed(msg_id):
                continue

            try:
                subject = msg["text"][:50] if len(msg["text"]) > 50 else msg["text"]
                self.create_vault_item(
                    item_type="whatsapp",
                    sender=msg["sender"],
                    subject=subject,
                    date_iso=datetime.now(timezone.utc).isoformat(),
                    body=msg["text"],
                    source_id=msg_id,
                    extra_frontmatter={"priority": "high"},
                )
                self.state.mark_processed(msg_id)
                new_count += 1
            except Exception as e:
                logger.error("Failed to process message from %s: %s", msg["sender"], e)

        self.state.save()
        return new_count

    def run(self):
        """Main watcher loop."""
        if not self.setup():
            sys.exit(1)

        try:
            self._launch_browser()
            if not self._wait_for_connection():
                sys.exit(2)

            logger.info(
                "WhatsApp watcher running. Keywords: %s. Interval: %ds.",
                self.keywords, self.interval,
            )

            while True:
                try:
                    new_count = self.poll_once()
                    if new_count:
                        logger.info("Created %d new vault item(s).", new_count)
                except Exception as e:
                    logger.error("Poll error: %s", e)

                time.sleep(self.interval)

        except KeyboardInterrupt:
            logger.info("Shutting down WhatsApp watcher.")
        finally:
            self._close_browser()
            self.cleanup()

    def _close_browser(self):
        """Safely close browser resources."""
        try:
            if self.browser:
                self.browser.close()
            if hasattr(self, "_playwright") and self._playwright:
                self._playwright.stop()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="WhatsApp watcher for the Personal AI Employee."
    )
    parser.add_argument(
        "--vault-path", required=True, help="Path to the Obsidian vault root."
    )
    parser.add_argument(
        "--interval", type=int, default=10,
        help="DOM polling interval in seconds (default: 10).",
    )
    parser.add_argument(
        "--session-path", default="~/.whatsapp_session",
        help="Path to Playwright session storage (default: ~/.whatsapp_session).",
    )
    parser.add_argument(
        "--keywords", default="urgent,asap,deadline,emergency",
        help="Comma-separated urgent keywords (default: urgent,asap,deadline,emergency).",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run browser in headless mode (no GUI).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    watcher = WhatsAppWatcher(
        vault_path=Path(args.vault_path).resolve(),
        interval=args.interval,
        session_path=args.session_path,
        keywords=[k.strip() for k in args.keywords.split(",")],
        headless=args.headless,
    )
    watcher.run()


if __name__ == "__main__":
    main()
