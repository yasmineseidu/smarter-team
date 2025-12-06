# Revenue Tracking Agent

## Category
Payment & Financial

## Purpose
Track financial metrics

## Metrics
- MRR (Monthly Recurring Revenue)
- ARR (Annual Recurring Revenue)
- Revenue per client
- Revenue per campaign
- Revenue per niche
- Cost per acquisition
- Lifetime value

## Process
1. Track all revenue events
2. Calculate metrics
3. Generate weekly/monthly reports
4. Dashboard updates

## Database Tables
- `revenue_events`
- `revenue_metrics`
- `financial_reports`

## Integrations
- Stripe API (revenue data)
- QuickBooks API (expense data)
- Internal database (attribution data)

## Priority
Phase 4 - Client Delivery

## Dependencies
- Payment Processing Agent (provides payment events)
- Campaign Performance (provides attribution data)

## Human-in-the-Loop
- Reports are informational
- Strategic decisions based on data require human

## Calculated Metrics

### MRR (Monthly Recurring Revenue)
```
Sum of all active retainer contracts / 12 months
```

### ARR (Annual Recurring Revenue)
```
MRR * 12
```

### Revenue per Client
```
Total revenue from client / Number of projects
```

### Revenue per Campaign
```
Sum of revenue from leads in campaign / Campaign cost
```

### Cost per Acquisition
```
Total marketing spend / Number of new clients
```

### Lifetime Value (LTV)
```
Average revenue per client * Average client lifespan
```

### LTV:CAC Ratio
```
LTV / Cost per Acquisition
Target: >3:1
```

## Report Format
```
REVENUE REPORT: {{period}}

SUMMARY
- Total Revenue: ${{total}}
- MRR: ${{mrr}}
- ARR: ${{arr}}
- New Clients: {{new_clients}}
- Churned Clients: {{churned}}

BY CAMPAIGN
| Campaign | Leads | Deals | Revenue | ROI |
|----------|-------|-------|---------|-----|
| {{name}} | {{n}} | {{n}} | ${{n}} | {{x}}x |

BY NICHE
| Niche | Leads | Deals | Revenue | LTV |
|-------|-------|-------|---------|-----|
| {{name}} | {{n}} | {{n}} | ${{n}} | ${{n}} |

TOP CLIENTS
1. {{client}} - ${{revenue}}
2. {{client}} - ${{revenue}}
3. {{client}} - ${{revenue}}

TRENDS
- Revenue vs last period: {{change}}%
- Pipeline value: ${{pipeline}}
- Forecast: ${{forecast}}
```

## Cron Schedule
- Monthly on 1st at 8:00 AM - Generate monthly revenue report
- Weekly on Monday at 8:00 AM - Generate weekly summary
