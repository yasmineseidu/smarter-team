# Error Monitor Agent

## Category
System & Administration

## Purpose
Track and alert on system errors

## Monitoring
- Agent failures
- API errors
- Webhook failures
- Database errors
- Integration issues

## Process
1. Log all errors
2. Classify severity
3. Alert on critical errors
4. Track error patterns
5. Generate daily error report

## Database Tables
- `error_logs`
- `error_alerts`

## Integrations
- Sentry (error tracking)
- Slack/Telegram (alerts)
- PagerDuty (critical alerts, optional)

## Priority
Phase 7 - Polish & Scale

## Dependencies
- All system components (receives errors from all)

## Human-in-the-Loop
- Critical errors require immediate human attention
- Error patterns reviewed for fixes

## Error Classification

### Severity Levels
```
CRITICAL:
- Database connection lost
- Payment processing failure
- Authentication system down
- Data corruption detected
Action: Immediate alert, wake human if needed

HIGH:
- Agent completely failed
- External API down
- Webhook delivery failed 3+ times
- Email delivery blocked
Action: Urgent alert, fix within 1 hour

MEDIUM:
- Agent partial failure
- API rate limit hit
- Slow response times
- Non-critical integration issue
Action: Alert, fix within 24 hours

LOW:
- Validation errors
- Expected failures (invalid email)
- Minor integration hiccups
Action: Log only, review in daily report
```

## Error Logging Schema
```json
{
  "id": "uuid",
  "created_at": "timestamp",
  "agent_name": "lead_list_builder",
  "error_type": "api_error",
  "error_message": "Apify API returned 429",
  "stack_trace": "...",
  "severity": "medium",
  "context": {
    "lead_id": "uuid",
    "request_id": "uuid",
    "retry_count": 2
  },
  "resolved": false,
  "resolved_at": null,
  "resolution_notes": null
}
```

## Alert Templates

### Critical Alert
```
🚨 CRITICAL ERROR

System: {{system_name}}
Error: {{error_message}}
Time: {{timestamp}}

IMMEDIATE ACTION REQUIRED

Context:
{{context}}

Stack trace:
{{stack_trace_summary}}

Dashboard: {{error_dashboard_link}}
```

### High Severity Alert
```
⚠️ HIGH SEVERITY ERROR

Agent: {{agent_name}}
Error: {{error_type}}
Message: {{error_message}}
Time: {{timestamp}}

Action needed within 1 hour.

Occurrences in last hour: {{count}}

Context:
{{context}}
```

### Daily Error Report
```
📊 DAILY ERROR REPORT - {{date}}

SUMMARY
- Critical: {{critical_count}}
- High: {{high_count}}
- Medium: {{medium_count}}
- Low: {{low_count}}
- Total: {{total_count}}

TOP ERRORS
{{for error in top_errors}}
{{rank}}. {{error.type}} ({{error.count}}x)
   Agent: {{error.agent}}
   Last: {{error.last_occurrence}}
{{/for}}

PATTERNS DETECTED
{{patterns}}

RESOLVED TODAY
{{resolved_count}} errors resolved

NEEDS ATTENTION
{{unresolved_critical_count}} critical errors unresolved
```

## Error Patterns to Detect
```
Pattern 1: Spike in errors
- >10 errors in 5 minutes from same source
- Alert immediately

Pattern 2: Recurring error
- Same error >5 times in 1 hour
- Flag for investigation

Pattern 3: Cascade failure
- Multiple systems failing simultaneously
- Likely root cause issue

Pattern 4: Time-based errors
- Errors occurring at specific times
- May indicate scheduled job issues
```

## Auto-Resolution
```
Some errors can be auto-resolved:

API Rate Limit:
- Auto-queue and retry
- Mark resolved when successful

Temporary Network Issue:
- Auto-retry with backoff
- Mark resolved if succeeds within 3 retries

Invalid Data:
- Log and skip record
- Mark as expected failure
```

## Cron Schedule
- Continuous - Monitor and log errors
- Every 5 minutes - Check for error spikes
- Daily at 8:00 AM - Generate daily error report
