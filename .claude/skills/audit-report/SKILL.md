---
name: audit-report
description: Generate a formatted audit report from vault logs for the specified date range.
---

# Audit Report

Generate a formatted audit report from vault logs.

## Instructions

1. Scan `vault/Logs/` for audit log files within the specified date range.
2. Aggregate entries by category (mcp, classification, approval, loop, scheduler).
3. Report success/failure counts, error patterns, and notable events.

## Usage

```bash
python -c "
from src.logging.audit_logger import summarize_week
from datetime import datetime, timedelta
end = datetime.now()
start = end - timedelta(days=7)
summary = summarize_week('./vault', start, end)
print(f'Total entries: {summary[\"total_entries\"]}')
for cat, stats in summary['categories'].items():
    print(f'  {cat}: {stats[\"entries\"]} entries, {stats[\"failures\"]} failures')
if summary['error_patterns']:
    print(f'Error patterns: {len(summary[\"error_patterns\"])}')
"
```

## Categories

- **mcp**: MCP tool invocations (create_invoice, email_send, etc.)
- **classification**: Item classification decisions
- **approval**: Approval workflow transitions
- **loop**: Ralph Wiggum loop iterations
- **scheduler**: Scheduler run results

## Output

Structured summary with:
- Entry counts per category
- Success/failure breakdown
- Recurring error patterns
- Date range covered
