"""Unit tests for Odoo JSON-RPC client (T018)."""

import unittest
from unittest.mock import patch, MagicMock

from src.mcp.tools.odoo_client import OdooClient, OdooConnectionError, OdooAuthError


class TestOdooClient(unittest.TestCase):
    """Test OdooClient JSON-RPC methods."""

    def _mock_response(self, result=None, error=None, status_code=200):
        """Create a mock requests.Response."""
        resp = MagicMock()
        resp.status_code = status_code
        resp.raise_for_status = MagicMock()
        if status_code >= 400:
            import requests
            resp.raise_for_status.side_effect = requests.HTTPError()

        body = {"jsonrpc": "2.0", "id": 1}
        if error:
            body["error"] = error
        else:
            body["result"] = result
        resp.json.return_value = body
        return resp

    @patch("src.mcp.tools.odoo_client.requests.post")
    def test_authenticate_success(self, mock_post):
        mock_post.return_value = self._mock_response(result=2)

        client = OdooClient(url="http://localhost:8069", db="test", username="admin", password="admin")
        uid = client.authenticate()

        assert uid == 2
        assert client.uid == 2
        mock_post.assert_called_once()

    @patch("src.mcp.tools.odoo_client.requests.post")
    def test_authenticate_failure(self, mock_post):
        mock_post.return_value = self._mock_response(result=False)

        client = OdooClient()
        with self.assertRaises(OdooAuthError):
            client.authenticate()

    @patch("src.mcp.tools.odoo_client.requests.post")
    def test_connection_error(self, mock_post):
        import requests as req
        mock_post.side_effect = req.ConnectionError("refused")

        client = OdooClient()
        with self.assertRaises(OdooConnectionError):
            client.authenticate()

    @patch("src.mcp.tools.odoo_client.requests.post")
    def test_execute_kw_auto_authenticates(self, mock_post):
        # First call: authenticate, second call: execute_kw
        mock_post.side_effect = [
            self._mock_response(result=2),  # auth
            self._mock_response(result=[{"id": 1, "name": "INV/001"}]),  # search_read
        ]

        client = OdooClient()
        result = client.execute_kw("account.move", "search_read", [[]])

        assert result == [{"id": 1, "name": "INV/001"}]
        assert mock_post.call_count == 2

    @patch("src.mcp.tools.odoo_client.requests.post")
    def test_search_read(self, mock_post):
        mock_post.side_effect = [
            self._mock_response(result=2),
            self._mock_response(result=[{"id": 1}, {"id": 2}]),
        ]

        client = OdooClient()
        result = client.search_read("res.partner", [("name", "=", "Test")])

        assert len(result) == 2

    @patch("src.mcp.tools.odoo_client.requests.post")
    def test_health_check_success(self, mock_post):
        mock_post.return_value = self._mock_response(
            result={"server_version": "19.0"}
        )

        client = OdooClient()
        health = client.health_check()

        assert health["status"] == "ok"
        assert health["odoo_version"] == "19.0"

    @patch("src.mcp.tools.odoo_client.requests.post")
    def test_health_check_failure(self, mock_post):
        import requests as req
        mock_post.side_effect = req.ConnectionError("refused")

        client = OdooClient()
        health = client.health_check()

        assert health["status"] == "error"
        assert "refused" in health["error"]

    @patch("src.mcp.tools.odoo_client.requests.post")
    def test_rpc_error_raises(self, mock_post):
        mock_post.return_value = self._mock_response(
            error={"message": "Access denied"}
        )

        client = OdooClient()
        with self.assertRaises(OdooConnectionError) as ctx:
            client.authenticate()

        assert "Access denied" in str(ctx.exception)

    @patch("src.mcp.tools.odoo_client.requests.post")
    def test_timeout_raises_connection_error(self, mock_post):
        import requests as req
        mock_post.side_effect = req.Timeout("timeout")

        client = OdooClient()
        with self.assertRaises(OdooConnectionError):
            client.authenticate()


if __name__ == "__main__":
    unittest.main()
