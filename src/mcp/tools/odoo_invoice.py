"""Odoo invoice MCP tools — create and list invoices.

Gold Tier — US1: Odoo Accounting Integration (FR-001).
"""

import logging
from datetime import datetime, timezone

from src.mcp.tools.odoo_client import OdooClient, OdooConnectionError

logger = logging.getLogger(__name__)


def _resolve_partner(client, partner_name):
    """Find or create a partner by name.

    Returns:
        int: Partner ID.
    """
    partners = client.search_read(
        "res.partner",
        [("name", "ilike", partner_name)],
        fields=["id", "name"],
        limit=1,
    )

    if partners:
        return partners[0]["id"]

    # Create new partner
    partner_id = client.execute_kw(
        "res.partner", "create",
        [{"name": partner_name, "is_company": True}],
    )
    logger.info("Created new partner '%s' with id=%d", partner_name, partner_id)
    return partner_id


def create_invoice(partner_name, invoice_date, due_date, lines, currency=None, client=None):
    """Create a customer invoice in Odoo.

    Args:
        partner_name: Customer name (resolved to partner_id).
        invoice_date: Invoice date (YYYY-MM-DD).
        due_date: Due date (YYYY-MM-DD).
        lines: List of dicts with keys: description, quantity, unit_price.
        currency: ISO 4217 currency code (optional).
        client: OdooClient instance (optional, creates default if None).

    Returns:
        Dict with status, invoice_id, invoice_number, partner, amount_total, state.
    """
    if client is None:
        client = OdooClient()

    try:
        partner_id = _resolve_partner(client, partner_name)

        # Build invoice line items
        invoice_lines = []
        for line in lines:
            invoice_lines.append((0, 0, {
                "name": line["description"],
                "quantity": line["quantity"],
                "price_unit": line["unit_price"],
            }))

        # Create invoice
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": partner_id,
            "invoice_date": invoice_date,
            "invoice_date_due": due_date,
            "invoice_line_ids": invoice_lines,
        }

        invoice_id = client.execute_kw("account.move", "create", [invoice_vals])

        # Read back the created invoice
        invoice = client.search_read(
            "account.move",
            [("id", "=", invoice_id)],
            fields=["name", "amount_total", "state", "partner_id"],
            limit=1,
        )

        if invoice:
            inv = invoice[0]
            return {
                "status": "created",
                "invoice_id": invoice_id,
                "invoice_number": inv.get("name", ""),
                "partner": partner_name,
                "amount_total": inv.get("amount_total", 0),
                "state": inv.get("state", "draft"),
            }

        return {
            "status": "created",
            "invoice_id": invoice_id,
            "invoice_number": "",
            "partner": partner_name,
            "amount_total": 0,
            "state": "draft",
        }

    except OdooConnectionError as e:
        return {
            "status": "error",
            "error": str(e),
            "retries_attempted": 0,
        }


def list_invoices(start_date=None, end_date=None, state=None, payment_state=None, limit=50, client=None):
    """List invoices with optional filters.

    Returns:
        Dict with status, count, invoices list.
    """
    if client is None:
        client = OdooClient()

    try:
        domain = [("move_type", "=", "out_invoice")]

        if start_date:
            domain.append(("invoice_date", ">=", start_date))
        if end_date:
            domain.append(("invoice_date", "<=", end_date))
        if state:
            domain.append(("state", "=", state))
        if payment_state:
            domain.append(("payment_state", "=", payment_state))

        invoices = client.search_read(
            "account.move",
            domain,
            fields=[
                "id", "name", "partner_id", "invoice_date",
                "invoice_date_due", "amount_total", "amount_residual",
                "state", "payment_state",
            ],
            limit=limit,
            order="invoice_date desc",
        )

        return {
            "status": "success",
            "count": len(invoices),
            "invoices": [
                {
                    "id": inv["id"],
                    "number": inv.get("name", ""),
                    "partner": inv.get("partner_id", [0, ""])[1] if isinstance(inv.get("partner_id"), list) else str(inv.get("partner_id", "")),
                    "date": inv.get("invoice_date", ""),
                    "due_date": inv.get("invoice_date_due", ""),
                    "amount_total": inv.get("amount_total", 0),
                    "amount_residual": inv.get("amount_residual", 0),
                    "state": inv.get("state", ""),
                    "payment_state": inv.get("payment_state", ""),
                }
                for inv in invoices
            ],
        }

    except OdooConnectionError as e:
        return {"status": "error", "error": str(e)}
