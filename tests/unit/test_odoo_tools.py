"""Unit tests for Odoo invoice/payment/reports tools (T019)."""

import unittest
from unittest.mock import MagicMock, patch

from src.mcp.tools.odoo_invoice import create_invoice, list_invoices
from src.mcp.tools.odoo_payment import record_payment, list_payments
from src.mcp.tools.odoo_reports import get_financial_summary
from src.mcp.tools.odoo_client import OdooConnectionError


class TestCreateInvoice(unittest.TestCase):
    """Test invoice creation tool."""

    def _mock_client(self):
        client = MagicMock()
        client.search_read.side_effect = [
            [{"id": 10, "name": "Test Corp"}],  # partner lookup
            [{"id": 42, "name": "INV/2026/0001", "amount_total": 1500.0, "state": "draft", "partner_id": [10, "Test Corp"]}],  # invoice readback
        ]
        client.execute_kw.return_value = 42  # invoice create
        return client

    def test_create_invoice_success(self):
        client = self._mock_client()
        result = create_invoice(
            partner_name="Test Corp",
            invoice_date="2026-02-12",
            due_date="2026-03-12",
            lines=[{"description": "Consulting", "quantity": 10, "unit_price": 150}],
            client=client,
        )

        assert result["status"] == "created"
        assert result["invoice_id"] == 42
        assert result["amount_total"] == 1500.0
        assert result["state"] == "draft"

    def test_create_invoice_new_partner(self):
        client = MagicMock()
        client.search_read.side_effect = [
            [],  # partner not found
            [{"id": 42, "name": "INV/001", "amount_total": 100, "state": "draft", "partner_id": [11, "New Corp"]}],
        ]
        client.execute_kw.side_effect = [11, 42]  # create partner, create invoice

        result = create_invoice(
            partner_name="New Corp",
            invoice_date="2026-02-12",
            due_date="2026-03-12",
            lines=[{"description": "Service", "quantity": 1, "unit_price": 100}],
            client=client,
        )

        assert result["status"] == "created"

    def test_create_invoice_connection_error(self):
        client = MagicMock()
        client.search_read.side_effect = OdooConnectionError("Connection refused")

        result = create_invoice(
            partner_name="Test",
            invoice_date="2026-02-12",
            due_date="2026-03-12",
            lines=[{"description": "X", "quantity": 1, "unit_price": 10}],
            client=client,
        )

        assert result["status"] == "error"
        assert "Connection refused" in result["error"]


class TestListInvoices(unittest.TestCase):
    def test_list_invoices_success(self):
        client = MagicMock()
        client.search_read.return_value = [
            {"id": 1, "name": "INV/001", "partner_id": [10, "Corp"], "invoice_date": "2026-02-01",
             "invoice_date_due": "2026-03-01", "amount_total": 500, "amount_residual": 0,
             "state": "posted", "payment_state": "paid"},
        ]

        result = list_invoices(client=client)
        assert result["status"] == "success"
        assert result["count"] == 1
        assert result["invoices"][0]["number"] == "INV/001"

    def test_list_invoices_with_filters(self):
        client = MagicMock()
        client.search_read.return_value = []

        result = list_invoices(start_date="2026-02-01", state="posted", client=client)
        assert result["status"] == "success"
        assert result["count"] == 0


class TestRecordPayment(unittest.TestCase):
    def test_record_payment_success(self):
        client = MagicMock()
        client.search_read.side_effect = [
            [{"id": 42, "state": "posted", "payment_state": "not_paid", "partner_id": [10, "Corp"], "amount_residual": 1500}],  # invoice
            [{"id": 1}],  # journal
            [{"payment_state": "paid"}],  # updated invoice
        ]
        client.execute_kw.side_effect = [15, None]  # create payment, action_post

        result = record_payment(invoice_id=42, amount=1500, payment_date="2026-02-12", client=client)

        assert result["status"] == "recorded"
        assert result["payment_id"] == 15
        assert result["invoice_payment_state"] == "paid"

    def test_record_payment_invoice_not_found(self):
        client = MagicMock()
        client.search_read.return_value = []

        result = record_payment(invoice_id=999, amount=100, payment_date="2026-02-12", client=client)
        assert result["status"] == "error"
        assert "not found" in result["error"]

    def test_record_payment_already_paid(self):
        client = MagicMock()
        client.search_read.return_value = [
            {"id": 42, "state": "posted", "payment_state": "paid", "partner_id": [10, "Corp"], "amount_residual": 0},
        ]

        result = record_payment(invoice_id=42, amount=100, payment_date="2026-02-12", client=client)
        assert result["status"] == "error"
        assert "already fully paid" in result["error"]


class TestListPayments(unittest.TestCase):
    def test_list_payments_success(self):
        client = MagicMock()
        client.search_read.return_value = [
            {"id": 1, "partner_id": [10, "Corp"], "amount": 500, "date": "2026-02-08", "state": "posted", "ref": "INV/001"},
        ]

        result = list_payments(client=client)
        assert result["status"] == "success"
        assert result["count"] == 1


class TestFinancialSummary(unittest.TestCase):
    def test_financial_summary_success(self):
        client = MagicMock()
        client.search_read.side_effect = [
            [{"amount_total": 5000}, {"amount_total": 3000}],  # revenue
            [{"amount_total": 2000}],  # expenses
            [{"amount_residual": 1500}],  # outstanding
            [{"amount_residual": 500}],  # overdue
            [{"amount": 4000}],  # payments
        ]

        result = get_financial_summary("2026-02-03", "2026-02-09", client=client)

        assert result["status"] == "success"
        assert result["total_revenue"] == 8000.0
        assert result["total_expenses"] == 2000.0
        assert result["outstanding_receivables"] == 1500.0
        assert result["overdue_count"] == 1
        assert result["payments_received"] == 4000.0
        assert result["net_cash_flow"] == 2000.0

    def test_financial_summary_connection_error(self):
        client = MagicMock()
        client.search_read.side_effect = OdooConnectionError("refused")

        result = get_financial_summary("2026-02-03", "2026-02-09", client=client)

        assert result["status"] == "unavailable"
        assert "Odoo connection failed" in result["message"]


if __name__ == "__main__":
    unittest.main()
