---
name: generate-briefing
description: Generate the weekly CEO Briefing report with financial, operational, and social activity summaries.
---

# Generate CEO Briefing

Generate the weekly CEO Briefing report.

## Instructions

1. Run the briefing generator to collect data from all sources:
   - Financial data from Odoo (if available)
   - Operational status from service health tracker
   - Social media activity from vault/Done
   - Audit log summary for the week

2. The briefing will be saved to `vault/Briefing.md` (previous briefing archived to `vault/Done/`).

3. Handle partial data gracefully — if Odoo is unavailable, note it in the Financial Summary section.

## Usage

```bash
python -c "
from src.briefing.briefing_generator import generate_briefing
result = generate_briefing('./vault')
print(f'Status: {result[\"status\"]}')
print(f'File: {result.get(\"file_path\", \"N/A\")}')
print(f'Bottlenecks: {result.get(\"bottleneck_count\", 0)}')
"
```

## Expected Output

- `vault/Briefing.md` with 5 sections: Financial Summary, Operational Status, Social Activity, Bottlenecks, Recommended Actions
- Previous briefing archived to `vault/Done/briefing-<date>.md`
- Trend indicators comparing current vs previous week

## Error Handling

- If Odoo unavailable: Financial section shows warning, other sections still populated
- If no audit logs: Operational section shows zero counts
- If no social activity: Social section shows "No social activity"
