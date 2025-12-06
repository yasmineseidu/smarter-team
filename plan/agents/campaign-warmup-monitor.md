# Email Warmup Monitor Agent

## Category
Campaign & Outreach

## Purpose
Track warmup progress for sending domains

## Process
1. Track warmup emails sent/received
2. Monitor warmup engagement rates
3. Alert on warmup issues
4. Track domain reputation progression
5. Recommend when domain is ready for volume

## Database Tables
- `domain_warmup`
- `warmup_metrics`

## Integrations
- Instantly API (warmup tracking)
- Domain reputation services

## Priority
Phase 3 - Closing & Proposals

## Dependencies
- Campaign Creation Agent (provides domains to track)

## Human-in-the-Loop
- Domain readiness recommendations reviewed before scaling

## Warmup Stages
1. Week 1-2: 10-20 emails/day
2. Week 3-4: 30-50 emails/day
3. Week 5-6: 75-100 emails/day
4. Week 7+: Full volume (up to daily limit)

## Alerts
- Warmup engagement drop > 20%
- Deliverability issues detected
- Domain flagged by providers
