# MCP Accounting Server Contracts

**Server**: `mcp_accounting` | **Entry Point**: `src/mcp/mcp_accounting.py`
**Transport**: stdio | **Backend**: Odoo Community v19+ (JSON-RPC)

## Tool: `create_invoice`

Create a customer invoice in Odoo.

### Input

```json
{
  "partner_name": "string (required) — Customer name. Resolved to partner_id via search.",
  "invoice_date": "string (required) — YYYY-MM-DD format.",
  "due_date": "string (required) — YYYY-MM-DD format.",
  "lines": [
    {
      "description": "string (required) — Line item description.",
      "quantity": "number (required) — Quantity.",
      "unit_price": "number (required) — Price per unit."
    }
  ],
  "currency": "string (optional) — ISO 4217 code (default: company currency)."
}
```

### Output (success)

```json
{
  "status": "created",
  "invoice_id": 42,
  "invoice_number": "INV/2026/0001",
  "partner": "Test Corp",
  "amount_total": 1500.00,
  "state": "draft"
}
```

### Output (error)

```json
{
  "status": "error",
  "error": "Odoo connection failed: Connection refused",
  "retries_attempted": 3
}
```

### Acceptance Criteria
- Invoice appears in Odoo with correct line items, amounts, customer
- Invoice state is `draft` until explicitly posted
- Partner is created if not found (with `is_company=True`)
- Audit log entry written to `/Logs/mcp-<date>.md`

---

## Tool: `record_payment`

Record a payment against an open invoice.

### Input

```json
{
  "invoice_id": "integer (required) — Odoo invoice record ID.",
  "amount": "number (required) — Payment amount.",
  "payment_date": "string (required) — YYYY-MM-DD format.",
  "journal": "string (optional) — 'bank' or 'cash' (default: 'bank')."
}
```

### Output (success)

```json
{
  "status": "recorded",
  "payment_id": 15,
  "invoice_id": 42,
  "amount": 1500.00,
  "invoice_payment_state": "paid"
}
```

### Output (error)

```json
{
  "status": "error",
  "error": "Invoice 42 not found or already fully paid"
}
```

### Acceptance Criteria
- Payment is linked to the specified invoice
- Invoice `payment_state` updates to `paid` (full) or `partial`
- Payment state is `posted` after creation
- Audit log entry written

---

## Tool: `get_financial_summary`

Pull aggregated financial data for a date range.

### Input

```json
{
  "start_date": "string (required) — YYYY-MM-DD.",
  "end_date": "string (required) — YYYY-MM-DD."
}
```

### Output (success)

```json
{
  "status": "success",
  "start_date": "2026-02-03",
  "end_date": "2026-02-09",
  "total_revenue": 15000.00,
  "total_expenses": 8500.00,
  "outstanding_receivables": 4200.00,
  "overdue_count": 2,
  "overdue_amount": 1800.00,
  "payments_received": 12000.00,
  "net_cash_flow": 3500.00,
  "invoice_count": 5,
  "payment_count": 3
}
```

### Output (error — graceful degradation)

```json
{
  "status": "unavailable",
  "error": "Odoo connection failed",
  "message": "Financial data unavailable — Odoo connection failed"
}
```

### Acceptance Criteria
- Revenue = sum of posted `out_invoice` amounts in date range
- Expenses = sum of posted `in_invoice` amounts in date range
- Overdue = invoices with `invoice_date_due < today` and `payment_state != 'paid'`
- Returns graceful degradation message when Odoo unreachable

---

## Tool: `list_invoices`

List invoices with optional filters.

### Input

```json
{
  "start_date": "string (optional) — Filter invoices from this date.",
  "end_date": "string (optional) — Filter invoices until this date.",
  "state": "string (optional) — Filter by state: 'draft', 'posted', 'cancel'.",
  "payment_state": "string (optional) — Filter: 'not_paid', 'paid', 'partial'.",
  "limit": "integer (optional) — Max results (default: 50)."
}
```

### Output (success)

```json
{
  "status": "success",
  "count": 5,
  "invoices": [
    {
      "id": 42,
      "number": "INV/2026/0001",
      "partner": "Test Corp",
      "date": "2026-02-05",
      "due_date": "2026-03-07",
      "amount_total": 1500.00,
      "amount_residual": 0.00,
      "state": "posted",
      "payment_state": "paid"
    }
  ]
}
```

### Acceptance Criteria
- Returns all matching invoices within filters
- Sorted by date descending
- Amount fields accurate to 2 decimal places

---

## Tool: `list_payments`

List payments with optional filters.

### Input

```json
{
  "start_date": "string (optional)",
  "end_date": "string (optional)",
  "limit": "integer (optional, default: 50)"
}
```

### Output (success)

```json
{
  "status": "success",
  "count": 3,
  "payments": [
    {
      "id": 15,
      "partner": "Test Corp",
      "amount": 1500.00,
      "date": "2026-02-08",
      "state": "posted",
      "ref": "INV/2026/0001"
    }
  ]
}
```

---

## Tool: `health_check`

Check if the Odoo connection is operational.

### Input

```json
{}
```

### Output

```json
{
  "status": "ok",
  "server": "mcp_accounting",
  "odoo_version": "19.0",
  "database": "odoo_gold",
  "timestamp": "2026-02-12T10:00:00Z"
}
```
