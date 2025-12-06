# Email Deliverability Monitor Agent

## Category
Campaign & Outreach

## Purpose
Track and maintain sender reputation

## Metrics
- Bounce rate (target: <2%)
- Spam complaint rate (target: <0.1%)
- Open rate (benchmark tracking)
- Domain health score

## Process
1. Monitor bounce webhooks from Instantly
2. Track spam complaints
3. Alert if thresholds exceeded
4. Auto-pause campaigns at risk
5. Generate weekly deliverability report

## Database Tables
- `deliverability_metrics`
- `domain_health`
- `deliverability_alerts`

## Integrations
- Instantly webhooks (bounce, complaint events)
- Email health monitoring tools

## Priority
Phase 3 - Closing & Proposals

## Dependencies
- Campaign Creation Agent (provides active campaigns)

## Human-in-the-Loop
- Alerts sent when thresholds exceeded
- Campaign pause decisions may require approval

## Thresholds
- Bounce rate > 2%: Warning
- Bounce rate > 5%: Auto-pause campaign
- Spam rate > 0.1%: Warning
- Spam rate > 0.3%: Auto-pause campaign

## Webhook
- Receives: `instantly/email_bounced`

## Cron Schedule
- Weekly on Monday 8:30 AM - Generate deliverability report
