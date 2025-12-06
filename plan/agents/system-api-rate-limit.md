# API Rate Limit Manager Agent

## Category
System & Administration

## Purpose
Prevent API throttling

## Limits to Track

| Service | Limit | Threshold | Action at Threshold |
|---------|-------|-----------|---------------------|
| Instantly | 50k/day | 90% | Throttle |
| Apollo | 1k/month | 90% | Switch to backup |
| Hunter | 5k/month | 90% | Switch to backup |
| Reoon | 10k/month | 90% | Alert |
| OpenAI | 10k tokens/min | 80% | Queue requests |
| Claude | Per plan | 80% | Queue requests |

## Process
1. Track all API calls
2. Monitor usage against limits
3. Throttle at 90%
4. Queue at 95%
5. Alert on approaching limits

## Database Tables
- `api_usage`
- `api_limits`
- `api_alerts`

## Integrations
- All external API clients
- Internal request queue

## Priority
Phase 7 - Polish & Scale

## Dependencies
- All agents that make external API calls

## Human-in-the-Loop
- Limit increase decisions
- Fallback provider selection
- Cost approval for overages

## Usage Tracking

### Per-Request Logging
```python
async def log_api_call(service: str, endpoint: str, tokens: int = 0):
    await db.execute("""
        INSERT INTO api_usage (service, endpoint, request_count, tokens_used, created_at)
        VALUES ($1, $2, 1, $3, NOW())
    """, service, endpoint, tokens)
```

### Usage Aggregation
```sql
-- Current period usage
SELECT
    service,
    SUM(request_count) as total_requests,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost
FROM api_usage
WHERE created_at >= date_trunc('day', NOW())  -- or 'month' for monthly limits
GROUP BY service;
```

## Rate Limit Configuration
```json
{
  "instantly": {
    "limit": 50000,
    "period": "day",
    "throttle_at": 0.9,
    "queue_at": 0.95,
    "fallback": null
  },
  "reoon": {
    "limit": 10000,
    "period": "month",
    "throttle_at": 0.9,
    "queue_at": 0.95,
    "fallback": "zerobounce"
  },
  "claude": {
    "limit_tokens": 1000000,
    "limit_requests": 1000,
    "period": "minute",
    "throttle_at": 0.8,
    "queue_at": 0.9,
    "fallback": null
  }
}
```

## Throttling Logic
```python
async def check_rate_limit(service: str) -> dict:
    config = RATE_LIMITS[service]
    current_usage = await get_current_usage(service, config['period'])
    usage_pct = current_usage / config['limit']

    if usage_pct >= config['queue_at']:
        return {"action": "queue", "delay_seconds": 60}
    elif usage_pct >= config['throttle_at']:
        return {"action": "throttle", "delay_seconds": 10}
    else:
        return {"action": "proceed", "delay_seconds": 0}
```

## Alert Conditions
```
WARNING (80%):
- Send Slack/Telegram notification
- No action required

THROTTLE (90%):
- Send urgent notification
- Add delay between requests
- Consider switching to fallback

CRITICAL (95%):
- Send critical alert
- Queue all non-essential requests
- Switch to fallback if available
- May pause affected workflows
```

## Alert Format
```
⚠️ API RATE LIMIT WARNING

Service: {{service}}
Current Usage: {{current}} / {{limit}} ({{percentage}}%)
Period: {{period}}
Threshold: {{threshold}}%

Action: {{action}}

Current queue depth: {{queue_size}}
Estimated time to limit: {{time_remaining}}
```

## Fallback Providers
```
Email Verification:
  Primary: Reoon
  Fallback: ZeroBounce, NeverBounce

Email Enrichment:
  Waterfall: Muraena → Tomba → Icypeas → Findymail

AI:
  Primary: Claude
  Fallback: OpenAI GPT-4

Search:
  Primary: Serper
  Fallback: Google Custom Search
```

## Cost Tracking
```sql
-- Monthly cost by service
SELECT
    service,
    SUM(cost_usd) as monthly_cost
FROM api_usage
WHERE created_at >= date_trunc('month', NOW())
GROUP BY service
ORDER BY monthly_cost DESC;
```

## Cron Schedule
- Every 5 minutes - Check usage levels
- Hourly - Send usage summary if approaching limits
- Monthly last day at 5:00 PM - Generate API cost report
