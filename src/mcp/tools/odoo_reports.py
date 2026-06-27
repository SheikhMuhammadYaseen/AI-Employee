"""Odoo financial reports MCP tools — pull summaries.

Gold Tier — US1: Odoo Accounting Integration (FR-003).
"""

import logging
from datetime import datetime

from src.mcp.tools.odoo_client import OdooClient, OdooConnectionError

logger = logging.getLogger(__name__)


def get_financial_summary(start_date, end_date, client=None):
    """Pull aggregated financial data for a date range.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        client: OdooClient instance (optional).

    Returns:
        Dict with financial metrics or error with graceful degradation.
    """
    if client is None:
        client = OdooClient()

    try:
        # Revenue: sum of posted customer invoices
        revenue_invoices = client.search_read(
            "account.move",
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("invoice_date", ">=", start_date),
                ("invoice_date", "<=", end_date),
            ],
            fields=["amount_total"],
            limit=1000,
        )
        total_revenue = sum(inv.get("amount_total", 0) for inv in revenue_invoices)
        invoice_count = len(revenue_invoices)

        # Expenses: sum of posted vendor bills
        expense_bills = client.search_read(
            "account.move",
            [
                ("move_type", "=", "in_invoice"),
                ("state", "=", "posted"),
                ("invoice_date", ">=", start_date),
                ("invoice_date", "<=", end_date),
            ],
            fields=["amount_total"],
            limit=1000,
        )
        total_expenses = sum(bill.get("amount_total", 0) for bill in expense_bills)

        # Outstanding receivables: unpaid customer invoices (all time)
        outstanding = client.search_read(
            "account.move",
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "in", ["not_paid", "partial"]),
            ],
            fields=["amount_residual"],
            limit=1000,
        )
        outstanding_receivables = sum(inv.get("amount_residual", 0) for inv in outstanding)

        # Overdue: invoices past due date
        today = datetime.now().strftime("%Y-%m-%d")
        overdue = client.search_read(
            "account.move",
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "in", ["not_paid", "partial"]),
                ("invoice_date_due", "<", today),
            ],
            fields=["amount_residual"],
            limit=1000,
        )
        overdue_count = len(overdue)
        overdue_amount = sum(inv.get("amount_residual", 0) for inv in overdue)

        # Payments received in period
        payments = client.search_read(
            "account.payment",
            [
                ("payment_type", "=", "inbound"),
                ("state", "=", "posted"),
                ("date", ">=", start_date),
                ("date", "<=", end_date),
            ],
            fields=["amount"],
            limit=1000,
        )
        payments_received = sum(p.get("amount", 0) for p in payments)
        payment_count = len(payments)

        net_cash_flow = payments_received - total_expenses

        return {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "outstanding_receivables": round(outstanding_receivables, 2),
            "overdue_count": overdue_count,
            "overdue_amount": round(overdue_amount, 2),
            "payments_received": round(payments_received, 2),
            "net_cash_flow": round(net_cash_flow, 2),
            "invoice_count": invoice_count,
            "payment_count": payment_count,
        }

    except OdooConnectionError as e:
        return {
            "status": "unavailable",
            "error": str(e),
            "message": "Financial data unavailable — Odoo connection failed",
        }
