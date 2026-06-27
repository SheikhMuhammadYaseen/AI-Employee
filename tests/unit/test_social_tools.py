"""Unit tests for social media tools — LinkedIn, Facebook, Instagram, X (T039)."""

import os
import unittest
from unittest.mock import MagicMock, patch


class TestLinkedInPost(unittest.TestCase):
    """Test LinkedIn posting tool."""

    def test_missing_credentials(self):
        from src.mcp.tools.linkedin_post import post_to_linkedin

        result = post_to_linkedin(text="Hello", author_id="", access_token="")
        assert result["status"] == "error"
        assert "Missing" in result["error"]

    def test_empty_text(self):
        from src.mcp.tools.linkedin_post import post_to_linkedin

        result = post_to_linkedin(text="", author_id="urn:li:person:123", access_token="tok")
        assert result["status"] == "error"
        assert "empty" in result["error"]

    def test_exceeds_char_limit(self):
        from src.mcp.tools.linkedin_post import post_to_linkedin

        result = post_to_linkedin(text="x" * 3001)
        assert result["status"] == "error"
        assert "3000" in result["error"]

    @patch.dict(os.environ, {"TEST_MODE": "true"})
    def test_test_mode(self):
        from src.mcp.tools.linkedin_post import post_to_linkedin

        result = post_to_linkedin(text="Test post", author_id="urn:li:person:123", access_token="tok")
        assert result["status"] == "posted"
        assert result.get("test_mode") is True
        assert result["platform"] == "linkedin"

    @patch("src.mcp.tools.linkedin_post.requests.post")
    def test_post_success(self, mock_post):
        from src.mcp.tools.linkedin_post import post_to_linkedin

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"id": "urn:li:share:12345"}
        mock_post.return_value = mock_resp

        result = post_to_linkedin(text="Hello LinkedIn", author_id="urn:li:person:123", access_token="tok")
        assert result["status"] == "posted"
        assert result["post_id"] == "urn:li:share:12345"

    @patch("src.mcp.tools.linkedin_post.requests.post")
    def test_connection_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.ConnectionError("refused")

        from src.mcp.tools.linkedin_post import post_to_linkedin
        result = post_to_linkedin(text="Hi", author_id="urn:li:person:123", access_token="tok")
        assert result["status"] == "error"
        assert "Cannot connect" in result["error"]


class TestFacebookPost(unittest.TestCase):
    """Test Facebook posting tool."""

    def test_missing_credentials(self):
        from src.mcp.tools.facebook_post import post_to_facebook

        result = post_to_facebook(message="Hello", page_id="", access_token="")
        assert result["status"] == "error"
        assert "Missing" in result["error"]

    def test_empty_message(self):
        from src.mcp.tools.facebook_post import post_to_facebook

        result = post_to_facebook(message="", page_id="123", access_token="tok")
        assert result["status"] == "error"
        assert "empty" in result["error"]

    @patch.dict(os.environ, {"TEST_MODE": "true"})
    def test_test_mode(self):
        from src.mcp.tools.facebook_post import post_to_facebook

        result = post_to_facebook(message="Test post", page_id="123", access_token="tok")
        assert result["status"] == "posted"
        assert result.get("test_mode") is True
        assert result["platform"] == "facebook"

    @patch("src.mcp.tools.facebook_post.requests.post")
    def test_post_success(self, mock_post):
        from src.mcp.tools.facebook_post import post_to_facebook

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"id": "123_456"}
        mock_post.return_value = mock_resp

        result = post_to_facebook(message="Hello FB", page_id="123", access_token="tok")
        assert result["status"] == "posted"
        assert result["post_id"] == "123_456"

    @patch("src.mcp.tools.facebook_post.requests.post")
    def test_connection_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.ConnectionError("refused")

        from src.mcp.tools.facebook_post import post_to_facebook
        result = post_to_facebook(message="Hi", page_id="123", access_token="tok")
        assert result["status"] == "error"
        assert "Cannot connect" in result["error"]


class TestInstagramPost(unittest.TestCase):
    """Test Instagram posting tool."""

    def test_missing_credentials(self):
        from src.mcp.tools.instagram_post import post_to_instagram

        result = post_to_instagram(caption="Hi", image_url="http://img.jpg", ig_user_id="", access_token="")
        assert result["status"] == "error"

    def test_missing_image_url(self):
        from src.mcp.tools.instagram_post import post_to_instagram

        result = post_to_instagram(caption="Hi", image_url="", ig_user_id="123", access_token="tok")
        assert result["status"] == "error"
        assert "image_url" in result["error"]

    @patch.dict(os.environ, {"TEST_MODE": "true"})
    def test_test_mode(self):
        from src.mcp.tools.instagram_post import post_to_instagram

        result = post_to_instagram(caption="Test", image_url="http://img.jpg", ig_user_id="123", access_token="tok")
        assert result["status"] == "posted"
        assert result["platform"] == "instagram"
        assert result.get("test_mode") is True

    @patch("src.mcp.tools.instagram_post.requests.post")
    def test_two_step_success(self, mock_post):
        from src.mcp.tools.instagram_post import post_to_instagram

        container_resp = MagicMock()
        container_resp.raise_for_status = MagicMock()
        container_resp.json.return_value = {"id": "container_1"}

        publish_resp = MagicMock()
        publish_resp.raise_for_status = MagicMock()
        publish_resp.json.return_value = {"id": "ig_post_42"}

        mock_post.side_effect = [container_resp, publish_resp]

        result = post_to_instagram(
            caption="Test caption", image_url="http://img.jpg",
            ig_user_id="123", access_token="tok",
        )
        assert result["status"] == "posted"
        assert result["post_id"] == "ig_post_42"
        assert mock_post.call_count == 2


class TestXPost(unittest.TestCase):
    """Test X (Twitter) posting tool."""

    def test_exceeds_char_limit(self):
        from src.mcp.tools.x_post import post_to_x

        result = post_to_x(text="x" * 281)
        assert result["status"] == "error"
        assert "280" in result["error"]

    def test_empty_text(self):
        from src.mcp.tools.x_post import post_to_x

        result = post_to_x(text="")
        assert result["status"] == "error"
        assert "empty" in result["error"]

    def test_missing_credentials(self):
        from src.mcp.tools.x_post import post_to_x

        result = post_to_x(text="Hello", api_key="", api_secret="", access_token="", access_secret="")
        assert result["status"] == "error"
        assert "Missing" in result["error"]

    @patch.dict(os.environ, {"TEST_MODE": "true"})
    def test_test_mode(self):
        from src.mcp.tools.x_post import post_to_x

        result = post_to_x(text="Test tweet", api_key="k", api_secret="s", access_token="t", access_secret="as")
        assert result["status"] == "posted"
        assert result["platform"] == "x"
        assert result.get("test_mode") is True

    def test_post_success(self):
        import sys

        mock_tweepy = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {"id": "tweet_123"}
        mock_client.create_tweet.return_value = mock_response
        mock_tweepy.Client.return_value = mock_client

        sys.modules["tweepy"] = mock_tweepy
        try:
            from src.mcp.tools.x_post import post_to_x

            result = post_to_x(
                text="Hello X", api_key="k", api_secret="s",
                access_token="t", access_secret="as",
            )
            assert result["status"] == "posted"
            assert result["post_id"] == "tweet_123"
        finally:
            del sys.modules["tweepy"]


class TestSocialSummary(unittest.TestCase):
    """Test social engagement summary."""

    def test_no_done_dir(self):
        from src.mcp.tools.social_summary import social_engagement_summary

        result = social_engagement_summary(vault_path="/nonexistent")
        assert result["status"] == "success"
        assert result["total_posts"] == 0

    def test_with_dates(self):
        from src.mcp.tools.social_summary import social_engagement_summary

        result = social_engagement_summary(
            start_date="2026-02-01", end_date="2026-02-10", vault_path="/nonexistent"
        )
        assert result["status"] == "success"
        assert result["start_date"] == "2026-02-01"
        assert result["end_date"] == "2026-02-10"


if __name__ == "__main__":
    unittest.main()
