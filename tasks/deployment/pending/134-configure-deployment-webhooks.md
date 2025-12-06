# Task 233: Configure Deployment Webhooks

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure webhooks in Coolify for automated deployments and integrate with GitHub, Slack, and monitoring services for deployment notifications.

## Prerequisites

- [ ] Task 232 completed (GitHub Actions configured)
- [ ] Coolify services deployed
- [ ] Notification channels configured (Slack, email, etc.)

## Implementation Checklist

- [ ] Set up Coolify deployment webhooks
- [ ] Configure GitHub webhook integration
- [ ] Set up deployment notifications
- [ ] Test webhook triggers
- [ ] Configure webhook security

## Configuration Details

### Coolify Webhook URLs

**Get webhook URLs from Coolify:**

1. Navigate to service in Coolify
2. Click "Webhooks" tab
3. Copy webhook URL for each service
4. Add to GitHub secrets

```bash
# Production webhooks
PROD_BACKEND_WEBHOOK=https://coolify.domain.com/webhooks/deploy/backend-prod-id
PROD_WORKER_WEBHOOK=https://coolify.domain.com/webhooks/deploy/worker-prod-id
PROD_BEAT_WEBHOOK=https://coolify.domain.com/webhooks/deploy/beat-prod-id
PROD_FRONTEND_WEBHOOK=https://coolify.domain.com/webhooks/deploy/frontend-prod-id

# Staging webhooks (if applicable)
STAGING_BACKEND_WEBHOOK=https://coolify.domain.com/webhooks/deploy/backend-staging-id
```

### GitHub Webhook Configuration

**In GitHub repository:**

1. Go to Settings → Webhooks
2. Add webhook
3. Payload URL: Coolify webhook URL
4. Content type: application/json
5. Events: Push events, Pull request events
6. Active: ✓

### Slack Notification Webhook

Create incoming webhook in Slack:

```bash
# Slack webhook for notifications
SLACK_WEBHOOK=https://hooks.slack.com/services/T00/B00/xxx

# Example notification payload
{
  "text": "Deployment started",
  "attachments": [
    {
      "color": "good",
      "fields": [
        {"title": "Environment", "value": "Production", "short": true},
        {"title": "Service", "value": "Backend", "short": true},
        {"title": "Commit", "value": "abc123", "short": true}
      ]
    }
  ]
}
```

## Verification

```bash
# Test webhook manually
curl -X POST \
  -H "Authorization: Bearer $COOLIFY_TOKEN" \
  https://coolify.domain.com/webhooks/deploy/service-id

# Monitor Coolify logs
# Check deployment starts
# Verify notifications sent
```

## Notes

- **Security**: Use HTTPS and bearer tokens
- **Rate limits**: Implement rate limiting for webhooks
- **Idempotency**: Handle duplicate webhook calls
- **Logging**: Log all webhook events for audit
