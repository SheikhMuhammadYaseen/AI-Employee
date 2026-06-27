---
name: odoo-accounting
description: Natural language interface for Odoo accounting operations including invoices, payments, and financial reports.
---

# Odoo Accounting

Natural language interface for Odoo accounting operations.

## Available Operations

### Create Invoice
```bash
python -c "
from src.mcp.tools.odoo_invoice import create_invoice
result = create_invoice(
    partner_name='Client Corp',
    invoice_date='2026-02-12',
    due_date='2026-03-12',
    lines=[{'description': 'Consulting', 'quantity': 10, 'unit_price': 150}]
)
print(result)
"
```

### Record Payment
```bash
python -c "
from src.mcp.tools.odoo_payment import record_payment
result = record_payment(invoice_id=42, amount=1500, payment_date='2026-02-12')
print(result)
"
```

### Financial Summary
```bash
python -c "
from src.mcp.tools.odoo_reports import get_financial_summary
result = get_financial_summary('2026-01-01', '2026-12-31')
print(result)
"
```

### List Invoices
```bash
python -c "
from src.mcp.tools.odoo_invoice import list_invoices
result = list_invoices(start_date='2026-02-01', state='posted')
print(result)
"
```

### Health Check
```bash
python -c "
from src.mcp.tools.odoo_client import OdooClient
client = OdooClient()
print(client.health_check())
"
```

## Prerequisites

- Odoo running: `docker compose -f docker-compose.gold.yml up -d`
- Environment variables set: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD
