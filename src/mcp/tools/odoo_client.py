"""Odoo JSON-RPC client for Gold Tier accounting integration.

Connects to local Odoo Community v19+ via JSON-RPC endpoint.
Handles authentication, session management, and execute_kw calls.
"""

import json
import os
import logging

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class OdooConnectionError(ConnectionError):
    """Raised when Odoo is unreachable."""
    pass


class OdooAuthError(Exception):
    """Raised when Odoo authentication fails."""
    pass


class OdooClient:
    """JSON-RPC client for Odoo Community."""

    def __init__(self, url=None, db=None, username=None, password=None):
        self.url = url or os.getenv("ODOO_URL", "http://localhost:8069")
        self.db = db or os.getenv("ODOO_DB", "odoo_gold")
        self.username = username or os.getenv("ODOO_USER", "admin")
        self.password = password or os.getenv("ODOO_PASSWORD", "admin")
        self.uid = None
        self._request_id = 0

    def _jsonrpc(self, service, method, args):
        """Make a JSON-RPC call to Odoo.

        Args:
            service: Odoo service ('common', 'object', 'db').
            method: Method name.
            args: List of arguments.

        Returns:
            JSON-RPC result.

        Raises:
            OdooConnectionError: If Odoo is unreachable.
        """
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args,
            },
            "id": self._request_id,
        }

        try:
            response = requests.post(
                f"{self.url}/jsonrpc",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
        except requests.ConnectionError as e:
            raise OdooConnectionError(f"Odoo connection failed: {e}") from e
        except requests.Timeout as e:
            raise OdooConnectionError(f"Odoo request timeout: {e}") from e
        except requests.HTTPError as e:
            raise OdooConnectionError(f"Odoo HTTP error: {e}") from e

        result = response.json()

        if "error" in result:
            error_data = result["error"]
            message = error_data.get("message", str(error_data))
            raise OdooConnectionError(f"Odoo RPC error: {message}")

        return result.get("result")

    def authenticate(self):
        """Authenticate with Odoo and store uid.

        Returns:
            int: User ID.

        Raises:
            OdooAuthError: If credentials are invalid.
        """
        uid = self._jsonrpc("common", "login", [self.db, self.username, self.password])

        if not uid:
            raise OdooAuthError(
                f"Authentication failed for user '{self.username}' on database '{self.db}'"
            )

        self.uid = uid
        logger.info("Authenticated with Odoo as uid=%d", uid)
        return uid

    def execute_kw(self, model, method, args=None, kwargs=None):
        """Execute a method on an Odoo model.

        Args:
            model: Odoo model name (e.g., 'account.move').
            method: Method name (e.g., 'create', 'search_read').
            args: Positional arguments.
            kwargs: Keyword arguments.

        Returns:
            Method result.
        """
        if self.uid is None:
            self.authenticate()

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        return self._jsonrpc(
            "object",
            "execute_kw",
            [self.db, self.uid, self.password, model, method, args, kwargs],
        )

    def search_read(self, model, domain=None, fields=None, limit=50, order=None):
        """Convenience method for search_read.

        Args:
            model: Odoo model name.
            domain: Search domain (list of tuples).
            fields: List of field names to return.
            limit: Maximum records.
            order: Sort order string.

        Returns:
            List of record dicts.
        """
        if domain is None:
            domain = []

        kwargs = {"limit": limit}
        if fields:
            kwargs["fields"] = fields
        if order:
            kwargs["order"] = order

        return self.execute_kw(model, "search_read", [domain], kwargs)

    def health_check(self):
        """Check Odoo connectivity and return server info.

        Returns:
            Dict with status, version, database info.
        """
        try:
            version = self._jsonrpc("common", "version", [])
            return {
                "status": "ok",
                "server": "mcp_accounting",
                "odoo_version": version.get("server_version", "unknown"),
                "database": self.db,
            }
        except (OdooConnectionError, Exception) as e:
            return {
                "status": "error",
                "server": "mcp_accounting",
                "error": str(e),
            }
