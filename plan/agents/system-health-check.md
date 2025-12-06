# Health Check Agent

## Category
System & Administration

## Purpose
Verify all integrations working

## Checks (Hourly)
- Instantly API connection
- Reoon API connection
- Cal.com API connection
- Fathom webhook receiving
- PandaDoc API connection
- Stripe API connection
- All database connections

## Process
1. Run health checks hourly
2. Log results
3. Alert on failures
4. Track uptime metrics

## Database Tables
- `health_checks`
- `uptime_metrics`

## Integrations
- All external services (checking them)
- Slack/Telegram (alerts)
- Status page (optional)

## Priority
Phase 7 - Polish & Scale

## Dependencies
- All integrated services

## Human-in-the-Loop
- Alerts on failures require investigation
- Prolonged outages may require manual intervention

## Health Check Definitions

### API Checks
```python
HEALTH_CHECKS = {
    "instantly": {
        "type": "api",
        "endpoint": "https://api.instantly.ai/api/v1/account/status",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200
    },
    "reoon": {
        "type": "api",
        "endpoint": "https://api.reoon.com/api/v1/status",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200
    },
    "cal_com": {
        "type": "api",
        "endpoint": "https://api.cal.com/v1/me",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200
    },
    "pandadoc": {
        "type": "api",
        "endpoint": "https://api.pandadoc.com/public/v1/documents",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200
    },
    "stripe": {
        "type": "api",
        "endpoint": "https://api.stripe.com/v1/balance",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200
    }
}
```

### Database Checks
```python
DATABASE_CHECKS = {
    "postgres_primary": {
        "type": "database",
        "query": "SELECT 1",
        "timeout": 5
    },
    "redis": {
        "type": "redis",
        "command": "PING",
        "expected": "PONG",
        "timeout": 5
    },
    "pinecone": {
        "type": "api",
        "endpoint": "describe_index_stats",
        "timeout": 10
    }
}
```

### Webhook Checks
```python
WEBHOOK_CHECKS = {
    "instantly_webhook": {
        "type": "webhook",
        "last_received_threshold": 3600,  # Alert if no webhook in 1 hour
        "webhook_type": "instantly_reply"
    },
    "fathom_webhook": {
        "type": "webhook",
        "last_received_threshold": 86400,  # Alert if no webhook in 24 hours
        "webhook_type": "fathom_recording"
    }
}
```

## Health Check Results Schema
```json
{
  "id": "uuid",
  "created_at": "timestamp",
  "service": "instantly",
  "endpoint": "https://api.instantly.ai/...",
  "status": "healthy",  // healthy, degraded, down
  "response_time_ms": 145,
  "error_message": null
}
```

## Status Levels
```
HEALTHY:
- Response received within timeout
- Expected status code
- No errors

DEGRADED:
- Response received but slow (>2x normal)
- Partial functionality
- Intermittent issues

DOWN:
- No response within timeout
- Error status code
- Connection refused
```

## Alert Rules
```
Single failure:
- Log only
- May be transient

2 consecutive failures:
- Send warning alert
- Continue monitoring

3+ consecutive failures:
- Send critical alert
- Mark service as DOWN
- Activate fallback if available

Recovery:
- Send recovery notification
- Update status to HEALTHY
```

## Alert Format
```
🔴 SERVICE DOWN

Service: {{service}}
Status: DOWN
Last healthy: {{last_healthy_time}}
Failures: {{consecutive_failures}}

Error: {{error_message}}
Response time: {{response_time}}ms (threshold: {{timeout}}ms)

Impact:
{{affected_workflows}}

Fallback: {{fallback_status}}
```

## Uptime Metrics
```sql
-- Calculate uptime percentage
SELECT
    service,
    COUNT(*) FILTER (WHERE status = 'healthy') * 100.0 / COUNT(*) as uptime_pct,
    AVG(response_time_ms) as avg_response_time,
    MAX(response_time_ms) as max_response_time
FROM health_checks
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY service;
```

## Status Page Data
```json
{
  "overall_status": "operational",
  "services": [
    {"name": "Email Sending", "status": "operational", "uptime": 99.9},
    {"name": "Calendar Integration", "status": "operational", "uptime": 99.8},
    {"name": "Payment Processing", "status": "operational", "uptime": 100},
    {"name": "AI Services", "status": "degraded", "uptime": 98.5}
  ],
  "incidents": []
}
```

## Cron Schedule
- Every hour - Run all health checks
- Every 5 minutes - Check critical services (database, core APIs)
