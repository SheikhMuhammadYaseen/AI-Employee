"""Integration tests for Odoo accounting (T020).

Requires Docker Odoo running: docker compose -f docker-compose.gold.yml up -d
Skip with: pytest tests/integration/test_odoo_integration.py -k "not odoo" or mark skip.
"""

import os
import unittest

import pytest

# Skip all tests if Odoo is not running
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")

try:
    import requests
    resp = requests.get(f"{ODOO_URL}/web/database/list", timeout=5)
    ODOO_AVAILABLE = resp.status_code == 200
except Exception:
    ODOO_AVAILABLE = False


@pytest.mark.skipif(not ODOO_AVAILABLE, reason="Odoo Docker not running")
class TestOdooIntegration(unittest.TestCase):
    """Integration tests requiring live Odoo instance."""

    def test_health_check(self):
        from src.mcp.tools.odoo_client import OdooClient
        client = OdooClient()
        health = client.health_check()
        assert health["status"] == "ok"

    def test_create_and_list_invoice(self):
        from src.mcp.tools.odoo_invoice import create_invoice, list_invoices

        result = create_invoice(
            partner_name="Integration Test Corp",
            invoice_date="2026-02-12",
            due_date="2026-03-12",
            lines=[{"description": "Test Service", "quantity": 1, "unit_price": 100}],
        )

        assert result["status"] == "created"
        assert result["invoice_id"] > 0

        # List should include new invoice
        invoices = list_invoices(start_date="2026-02-12")
        assert invoices["status"] == "success"
        assert invoices["count"] > 0

    def test_financial_summary(self):
        from src.mcp.tools.odoo_reports import get_financial_summary

        result = get_financial_summary("2026-01-01", "2026-12-31")
        assert result["status"] == "success"
        assert "total_revenue" in result
        assert "total_expenses" in result


if __name__ == "__main__":
    unittest.main()
