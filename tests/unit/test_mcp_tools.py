"""Tests for MCP tools (Mastodon + Email) — Silver Tier (T029)."""

from unittest.mock import patch, MagicMock

import pytest

from src.mcp.tools.mastodon_post import post_to_mastodon
from src.mcp.tools.email_send import send_email


# ---------------------------------------------------------------------------
# Mastodon post tests
# ---------------------------------------------------------------------------

class TestMastodonPost:
    def test_successful_post(self):
        mock_mastodon_module = MagicMock()
        mock_client = MagicMock()
        mock_client.status_post.return_value = {
            "url": "https://mastodon.social/@test/123",
            "id": "123",
        }
        mock_mastodon_module.Mastodon.return_value = mock_client

        with patch.dict("sys.modules", {"mastodon": mock_mastodon_module}):
            result = post_to_mastodon(
                content="Hello Mastodon!",
                instance_url="https://mastodon.social",
                access_token="fake-token",
            )

        assert result["status"] == "posted"
        assert "123" in result["post_id"]
        assert "mastodon.social" in result["post_url"]

    def test_content_over_500_chars_rejected(self):
        long_content = "a" * 501
        result = post_to_mastodon(content=long_content)
        assert result["status"] == "error"
        assert "500" in result["error"]

    def test_missing_credentials(self):
        result = post_to_mastodon(
            content="Test",
            instance_url="",
            access_token="",
        )
        assert result["status"] == "error"
        assert "Missing" in result["error"]

    def test_api_error_handled(self):
        mock_mastodon_module = MagicMock()
        mock_client = MagicMock()
        mock_client.status_post.side_effect = Exception("API rate limit exceeded")
        mock_mastodon_module.Mastodon.return_value = mock_client

        with patch.dict("sys.modules", {"mastodon": mock_mastodon_module}):
            result = post_to_mastodon(
                content="Test post",
                instance_url="https://mastodon.social",
                access_token="fake-token",
            )

        assert result["status"] == "error"
        assert "rate limit" in result["error"].lower() or "Exception" in result["error"]

    def test_exactly_500_chars_accepted(self):
        # Should not error — exactly at limit. Will fail on missing creds though.
        content = "a" * 500
        result = post_to_mastodon(content=content)
        # Will error on missing creds, but NOT on content length
        assert "500 characters" not in result.get("error", "")


# ---------------------------------------------------------------------------
# Email send tests
# ---------------------------------------------------------------------------

class TestEmailSend:
    def test_missing_credentials(self):
        result = send_email(
            to="test@example.com",
            subject="Test",
            body="Hello",
            gmail_address="",
            gmail_app_password="",
        )
        assert result["status"] == "error"
        assert "Missing" in result["error"]

    def test_invalid_email_address(self):
        result = send_email(
            to="not-an-email",
            subject="Test",
            body="Hello",
            gmail_address="me@gmail.com",
            gmail_app_password="secret",
        )
        assert result["status"] == "error"
        assert "Invalid" in result["error"]

    @patch("src.mcp.tools.email_send.smtplib.SMTP")
    def test_successful_send(self, MockSMTP):
        mock_server = MagicMock()
        MockSMTP.return_value.__enter__ = MagicMock(return_value=mock_server)
        MockSMTP.return_value.__exit__ = MagicMock(return_value=False)

        result = send_email(
            to="dest@example.com",
            subject="Test Subject",
            body="Test Body",
            gmail_address="me@gmail.com",
            gmail_app_password="app-password",
        )

        assert result["status"] == "sent"
        assert "timestamp" in result

    @patch("src.mcp.tools.email_send.smtplib.SMTP")
    def test_auth_failure_handled(self, MockSMTP):
        import smtplib
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        MockSMTP.return_value.__enter__ = MagicMock(return_value=mock_server)
        MockSMTP.return_value.__exit__ = MagicMock(return_value=False)

        result = send_email(
            to="dest@example.com",
            subject="Test",
            body="Test",
            gmail_address="me@gmail.com",
            gmail_app_password="wrong-password",
        )

        assert result["status"] == "error"
        assert "authentication" in result["error"].lower()

    def test_empty_to_address(self):
        result = send_email(
            to="",
            subject="Test",
            body="Hello",
            gmail_address="me@gmail.com",
            gmail_app_password="secret",
        )
        assert result["status"] == "error"
