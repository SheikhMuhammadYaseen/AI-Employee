"""Odoo payment MCP tools — record and list payments.

Gold Tier — US1: Odoo Accounting Integration (FR-002).
"""

import logging

from src.mcp.tools.odoo_client import OdooClient, OdooConnectionError

logger = logging.getLogger(__name__)


def record_payment(invoice_id, amount, payment_date, journal="bank", client=None):
    """Record a payment against an open invoice.

    Args:
        invoice_id: Odoo invoice record ID.
        amount: Payment amount.
        payment_date: Payment date (YYYY-MM-DD).
        journal: 'bank' or 'cash' (default: 'bank').
        client: OdooClient instance (optional).

    Returns:
        Dict with status, payment_id, invoice_id, amount, invoice_payment_state.
    """
    if client is None:
        client = OdooClient()

    try:
        # Verify invoice exists
        invoices = client.search_read(
            "account.move",
            [("id", "=", invoice_id), ("move_type", "=", "out_invoice")],
            fields=["id", "state", "payment_state", "partner_id", "amount_residual"],
            limit=1,
        )

        if not invoices:
            return {
                "status": "error",
                "error": f"Invoice {invoice_id} not found or not a customer invoice",
            }

        invoice = invoices[0]

        if invoice.get("payment_state") == "paid":
            return {
                "status": "error",
                "error": f"Invoice {invoice_id} is already fully paid",
            }

        # Find journal
        journal_type = "bank" if journal == "bank" else "cash"
        journals = client.search_read(
            "account.journal",
            [("type", "=", journal_type)],
            fields=["id"],
            limit=1,
        )

        if not journals:
            return {
                "status": "error",
                "error": f"No {journal_type} journal found in Odoo",
            }

        journal_id = journals[0]["id"]
        partner_id = invoice["partner_id"]
        if isinstance(partner_id, list):
            partner_id = partner_id[0]

        # Create payment
        payment_vals = {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": partner_id,
            "amount": amount,
            "date": payment_date,
            "journal_id": journal_id,
            "ref": f"Payment for invoice #{invoice_id}",
        }

        payment_id = client.execute_kw("account.payment", "create", [payment_vals])

        # Post the payment
        client.execute_kw("account.payment", "action_post", [[payment_id]])

        # Re-read invoice to get updated payment state
        updated = client.search_read(
            "account.move",
            [("id", "=", invoice_id)],
            fields=["payment_state"],
            limit=1,
        )

        payment_state = updated[0]["payment_state"] if updated else "unknown"

        return {
            "status": "recorded",
            "payment_id": payment_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "invoice_payment_state": payment_state,
        }

    except OdooConnectionError as e:
        return {"status": "error", "error": str(e)}


def list_payments(start_date=None, end_date=None, limit=50, client=None):
    """List payments with optional filters.

    Returns:
        Dict with status, count, payments list.
    """
    if client is None:
        client = OdooClient()

    try:
        domain = [("payment_type", "=", "inbound")]

        if start_date:
            domain.append(("date", ">=", start_date))
        if end_date:
            domain.append(("date", "<=", end_date))

        payments = client.search_read(
            "account.payment",
            domain,
            fields=["id", "partner_id", "amount", "date", "state", "ref"],
            limit=limit,
            order="date desc",
        )

        return {
            "status": "success",
            "count": len(payments),
            "payments": [
                {
                    "id": p["id"],
                    "partner": p.get("partner_id", [0, ""])[1] if isinstance(p.get("partner_id"), list) else str(p.get("partner_id", "")),
                    "amount": p.get("amount", 0),
                    "date": p.get("date", ""),
                    "state": p.get("state", ""),
                    "ref": p.get("ref", ""),
                }
                for p in payments
            ],
        }

    except OdooConnectionError as e:
        return {"status": "error", "error": str(e)}
