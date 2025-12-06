# Task 237: Configure Alerts and Notifications

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Set up alerting rules and notification channels for service failures, high resource usage, deployment events, and error spikes.

## Prerequisites

- [ ] Task 236 completed (Logging and monitoring configured)
- [ ] Notification channels set up (Slack, email, etc.)

## Implementation Checklist

- [ ] Configure Coolify alert rules
- [ ] Set up notification channels (Slack, email)
- [ ] Define alert thresholds
- [ ] Test alert delivery
- [ ] Create on-call rotation (optional)

## Configuration Details

### Alert Rules

```yaml
Service Health Alerts:
  - Service down: Immediate alert
  - Health check failure: Alert after 3 consecutive failures
  - Service restart: Alert after 2 restarts in 5 minutes

Resource Alerts:
  - CPU > 80%: Alert after 5 minutes
  - Memory > 85%: Alert after 5 minutes
  - Disk > 90%: Immediate alert

Performance Alerts:
  - Response time > 2s: Alert after 100 requests
  - Error rate > 5%: Alert after 50 requests
  - Queue depth > 1000: Alert after 5 minutes

Deployment Alerts:
  - Deployment started: Notification
  - Deployment failed: Immediate alert
  - Deployment succeeded: Notification
  - Rollback triggered: Immediate alert
```

### Notification Channels

**Slack Integration:**

```bash
# Create incoming webhook in Slack
# Add to Coolify notification settings
SLACK_WEBHOOK=https://hooks.slack.com/services/...
SLACK_CHANNEL=#deployments
```

**Email Alerts:**

```bash
# Configure in Coolify settings
ALERT_EMAIL=ops@smarter-team.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Example Alert Payload

```json
{
  "alert": "Service Down",
  "service": "smarter-team-backend",
  "severity": "critical",
  "timestamp": "2025-12-06T10:00:00Z",
  "details": {
    "health_check": "failed",
    "consecutive_failures": 3,
    "last_error": "Connection refused"
  },
  "actions": [
    "Check service logs",
    "Verify database connectivity",
    "Consider rollback if recently deployed"
  ]
}
```

## Verification

```bash
# Test alert by killing a service
docker stop smarter-team-backend
# Wait for alert (should arrive within 2-3 minutes)

# Restart service
docker start smarter-team-backend
# Wait for recovery notification

# Verify alerts in notification channels
```

## Notes

- **Alert fatigue**: Set appropriate thresholds
- **Escalation**: Critical alerts to multiple channels
- **Quiet hours**: Optional for non-critical alerts
- **On-call**: Integrate with PagerDuty/Opsgenie if needed
