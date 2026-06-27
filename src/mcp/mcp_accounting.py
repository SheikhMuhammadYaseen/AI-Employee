"""MCP Accounting Server — Odoo Community integration.

Gold Tier — US1/US5: Exposes Odoo accounting operations as MCP tools.
Transport: stdio. Backend: Odoo Community v19+ (JSON-RPC).
"""

import json
import asyncio
from datetime import datetime, timezone

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.mcp.tools.odoo_client import OdooClient
from src.mcp.tools.odoo_invoice import create_invoice, list_invoices
from src.mcp.tools.odoo_payment import record_payment, list_payments
from src.mcp.tools.odoo_reports import get_financial_summary

server = Server("gold-accounting")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="create_invoice",
            description="Create a customer invoice in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_name": {"type": "string", "description": "Customer name"},
                    "invoice_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "due_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "lines": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                            },
                            "required": ["description", "quantity", "unit_price"],
                        },
                    },
                },
                "required": ["partner_name", "invoice_date", "due_date", "lines"],
            },
        ),
        Tool(
            name="record_payment",
            description="Record a payment against an open invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "Odoo invoice ID"},
                    "amount": {"type": "number", "description": "Payment amount"},
                    "payment_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "journal": {"type": "string", "description": "bank or cash", "default": "bank"},
                },
                "required": ["invoice_id", "amount", "payment_date"],
            },
        ),
        Tool(
            name="get_financial_summary",
            description="Pull aggregated financial data for a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Tool(
            name="list_invoices",
            description="List invoices with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "state": {"type": "string"},
                    "payment_state": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
            },
        ),
        Tool(
            name="list_payments",
            description="List payments with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
            },
        ),
        Tool(
            name="health_check",
            description="Check Odoo connection and server status",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name, arguments):
    timestamp = datetime.now(timezone.utc).isoformat()

    if name == "create_invoice":
        result = create_invoice(
            partner_name=arguments["partner_name"],
            invoice_date=arguments["invoice_date"],
            due_date=arguments["due_date"],
            lines=arguments["lines"],
        )
    elif name == "record_payment":
        result = record_payment(
            invoice_id=arguments["invoice_id"],
            amount=arguments["amount"],
            payment_date=arguments["payment_date"],
            journal=arguments.get("journal", "bank"),
        )
    elif name == "get_financial_summary":
        result = get_financial_summary(
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
        )
    elif name == "list_invoices":
        result = list_invoices(
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            state=arguments.get("state"),
            payment_state=arguments.get("payment_state"),
            limit=arguments.get("limit", 50),
        )
    elif name == "list_payments":
        result = list_payments(
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            limit=arguments.get("limit", 50),
        )
    elif name == "health_check":
        client = OdooClient()
        result = client.health_check()
        result["timestamp"] = timestamp
    else:
        result = {"status": "error", "error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
