#!/usr/bin/env python3
"""Email sending tool for the Personal AI Employee — Silver Tier.

Sends emails via Gmail SMTP after human approval.
Uses Python's built-in smtplib with Gmail App Password authentication.
"""

import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(
    to: str,
    subject: str,
    body: str,
    reply_to: str | None = None,
    gmail_address: str | None = None,
    gmail_app_password: str | None = None,
) -> dict:
    """Send an email via Gmail SMTP.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text (plain text).
        reply_to: Optional message ID to set as reply.
        gmail_address: Sender address. Reads GMAIL_ADDRESS from env if None.
        gmail_app_password: App Password. Reads GMAIL_APP_PASSWORD from env if None.

    Returns:
        Dict with status, message_id on success; status, error on failure.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if gmail_address is None:
        gmail_address = os.getenv("GMAIL_ADDRESS", "")
    if gmail_app_password is None:
        gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")

    if not gmail_address or not gmail_app_password:
        return {
            "status": "error",
            "error": "Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD",
            "timestamp": timestamp,
        }

    if not to or "@" not in to:
        return {
            "status": "error",
            "error": f"Invalid email address: {to}",
            "timestamp": timestamp,
        }

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = gmail_address
        msg["To"] = to
        msg["Subject"] = subject
        if reply_to:
            msg["In-Reply-To"] = reply_to

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(gmail_address, gmail_app_password)
            server.send_message(msg)

        return {
            "status": "sent",
            "message_id": msg.get("Message-ID", ""),
            "timestamp": timestamp,
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "status": "error",
            "error": "SMTP authentication failed. Check GMAIL_APP_PASSWORD.",
            "timestamp": timestamp,
        }
    except smtplib.SMTPException as e:
        return {
            "status": "error",
            "error": f"SMTP error: {e}",
            "timestamp": timestamp,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Connection to {SMTP_SERVER} failed: {e}",
            "timestamp": timestamp,
        }
