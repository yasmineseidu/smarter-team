# Task: Implement Onboarding Stuck Detector Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/onboarding-stuck-detector.md
**Created:** 2025-01-05
**Priority:** Phase 4 - Client Delivery

## Summary

Implement the Onboarding Stuck Detector Agent that proactively monitors client onboarding progress and resolves stalled workflows. The agent runs hourly checks, sends automated reminders, escalates when needed, and maintains state across runs using time-based detection patterns and distributed locking.

## Files to Create

### Core Agent Files
- `app/backend/src/agents/onboarding_stuck_detector/__init__.py`
- `app/backend/src/agents/onboarding_stuck_detector/agent.py`
- `app/backend/src/agents/onboarding_stuck_detector/tools.py`
- `app/backend/src/agents/onboarding_stuck_detector/schemas.py`
- `app/backend/src/agents/onboarding_stuck_detector/prompts.py`
- `app/backend/src/agents/onboarding_stuck_detector/exceptions.py`

### Database & Tasks
- `app/backend/src/tasks/onboarding_tasks.py`
- `app/backend/src/models/onboarding.py` (extend if needed)

### Tests
- `app/backend/__tests__/unit/agents/test_onboarding_stuck_detector.py`
- `app/backend/__tests__/unit/agents/test_onboarding_stuck_detector_tools.py`
- `app/backend/__tests__/integration/test_onboarding_stuck_detector_integration.py`

### Configuration
- `app/backend/src/config/monitoring.py` (if needed)

## Implementation Checklist

### Phase 1: Foundation
- [ ] Create agent directory structure with __init__.py
- [ ] Implement OnboardingStuckDetectorAgent class extending BaseAgent
- [ ] Define all Pydantic schemas in schemas.py
- [ ] Create custom exceptions in exceptions.py
- [ ] Add system prompt to prompts.py

### Phase 2: Tools Implementation
- [ ] Implement check_onboarding_status tool with database queries
- [ ] Implement send_reminder_email tool with SendGrid/SMTP integration
- [ ] Implement send_escalation_alert tool with Slack/Telegram support
- [ ] Implement update_onboarding_state tool with optimistic locking
- [ ] Add comprehensive error handling for all tools

### Phase 3: Core Logic
- [ ] Implement stuck detection rules (4 types)
- [ ] Add business day calculation (exclude weekends)
- [ ] Implement timezone handling logic
- [ ] Add duplicate reminder prevention
- [ ] Implement escalation workflow logic

### Phase 4: Distributed Processing
- [ ] Add Redis distributed locking
- [ ] Implement cron job scheduling
- [ ] Add concurrent processing prevention
- [ ] Implement state recovery mechanisms
- [ ] Add dead letter queue for failed operations

### Phase 5: Integration & Handoffs
- [ ] Implement handoff to onboarding_orchestrator
- [ ] Implement handoff to internal_setup agent
- [ ] Add event subscription handling
- [ ] Integrate with existing onboarding workflow

### Phase 6: Monitoring & Observability
- [ ] Add structured logging throughout
- [ ] Implement Prometheus metrics
- [ ] Add health check endpoints
- [ ] Create alerting rules
- [ ] Add performance monitoring

### Phase 7: Testing
- [ ] Write unit tests for all tools
- [ ] Write unit tests for agent logic
- [ ] Write integration tests for end-to-end workflows
- [ ] Add performance tests
- [ ] Create test fixtures and mocks

### Phase 8: Documentation & Deployment
- [ ] Update API documentation
- [ ] Create operational runbook
- [ ] Add deployment configuration
- [ ] Create monitoring dashboards

## Detailed Implementation Notes

### Database Queries
```sql
-- Get stuck intake forms
SELECT * FROM onboardings
WHERE state = 'ONBOARDING'
  AND intake_form_sent = TRUE
  AND intake_form_completed = FALSE
  AND intake_form_sent <= NOW() - INTERVAL '3 days'
  AND (last_reminder_sent IS NULL
       OR last_reminder_sent <= NOW() - INTERVAL '48 hours');

-- Get stuck access requests
SELECT * FROM onboardings
WHERE state = 'ONBOARDING'
  AND access_requests @> '[{"status": "requested"}]'
  AND access_requests @> '[{"requested_at": <= NOW() - INTERVAL "2 days"}]'

-- Get stuck kickoff scheduling
SELECT * FROM onboardings
WHERE state = 'ONBOARDING'
  AND started_at <= NOW() - INTERVAL '5 days'
  AND kickoff_scheduled = FALSE;
```

### Redis Locking Pattern
```python
import redis
import time
import json

def acquire_lock(redis_client, client_id: str, timeout: int = 300) -> bool:
    lock_key = f"onboarding_stuck_check:{client_id}"
    lock_value = json.dumps({
        "timestamp": time.time(),
        "agent": "onboarding_stuck_detector"
    })

    acquired = redis_client.set(
        lock_key,
        lock_value,
        nx=True,
        ex=timeout
    )

    return acquired is not None

def release_lock(redis_client, client_id: str, lock_value: str) -> bool:
    lock_key = f"onboarding_stuck_check:{client_id}"

    # Script to ensure we only release our own lock
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    return redis_client.eval(script, 1, lock_key, lock_value) == 1
```

### Business Day Calculation
```python
from datetime import datetime, timedelta
import holidays

us_holidays = holidays.US()

def is_business_day(date: datetime) -> bool:
    """Check if date is a business day (Mon-Fri, not holiday)"""
    return date.weekday() < 5 and date.date() not in us_holidays

def business_days_between(start: datetime, end: datetime) -> int:
    """Calculate business days between two dates"""
    business_days = 0
    current = start.date()
    end_date = end.date()

    while current <= end_date:
        if is_business_day(datetime.combine(current, datetime.min.time())):
            business_days += 1
        current += timedelta(days=1)

    return business_days
```

### Email Templates Storage
```python
# In prompts.py
EMAIL_TEMPLATES = {
    "intake_reminder": {
        "subject": "Quick reminder: Intake form for {company_name}",
        "template": """Hi {first_name},

Just checking in - I noticed the intake form is still pending. This helps us prepare for your kickoff call and ensures we have all the information needed to get started.

Here's the link again: {intake_form_link}

The form only takes about 10 minutes to complete. If you have any questions or need help with anything, please let me know!

Best regards,
{signature}
"""
    },
    "access_reminder": {
        "subject": "Access request follow-up",
        "template": """Hi {first_name},

Following up on the access credentials I requested. We need these to begin work:

{access_list}

Please let me know if there are any blockers or if you need help.

Best regards,
{signature}
"""
    },
    "kickoff_reminder": {
        "subject": "Schedule your kickoff call",
        "template": """Hi {first_name},

Let's schedule your kickoff call to get started! You can book a time that works for you here:

{calendly_link}

This 30-minute call will help us understand your goals and plan the project. Looking forward to speaking with you!

Best regards,
{signature}
"""
    },
    "general_checkin": {
        "subject": "Checking in on your onboarding",
        "template": """Hi {first_name},

I wanted to check in - it's been a few days since we connected about your onboarding.

Is everything okay? Let me know if there's anything I can help with to move things forward.

Best regards,
{signature}
"""
    }
}
```

## Acceptance Criteria

[ ] Agent successfully detects all four types of stuck conditions
[ ] Reminders are sent with proper personalization and links
[ ] No duplicate reminders sent within 48-hour window
[ ] Escalations triggered after 2 failed reminders
[ ] Weekends excluded from day calculations
[ ] Client timezones respected in all operations
[ ] Redis locks prevent concurrent processing
[ ] All errors handled gracefully with logging
[ ] Integration with existing onboarding workflow
[ ] Unit test coverage >90%, integration test coverage >85%
[ ] Performance: <5 minutes to process 100 onboardings
[ ] Monitoring and alerting configured

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_onboarding_stuck_detector.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_onboarding_stuck_detector_integration.py -v

# Type checking
mypy app/backend/src/agents/onboarding_stuck_detector/

# Linting
ruff check app/backend/src/agents/onboarding_stuck_detector/

# Test coverage
pytest --cov=app/backend/src/agents/onboarding_stuck_detector --cov-report=html

# Manual smoke test
python -c "
from app.backend.src.agents.onboarding_stuck_detector import OnboardingStuckDetectorAgent
agent = OnboardingStuckDetectorAgent()
print('Agent initialized successfully:', agent.name)
"
```

## Dependencies

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
SENDGRID_API_KEY=sg_...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...

# Slack/Telegram
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=https://...
```

### Python Dependencies (add to pyproject.toml)
```toml
[project.optional-dependencies]
onboarding-monitoring = [
    "sendgrid>=6.10.0",
    "aiosmtplib>=3.0.0",
    "slack-sdk>=3.26.0",
    "python-telegram-bot>=20.7",
    "holidays>=0.40",
    "prometheus-client>=0.19.0"
]
```

## Rollout Plan

1. **Phase 1 (Week 1):** Core agent implementation and unit tests
2. **Phase 2 (Week 2):** Integration with email and messaging services
3. **Phase 3 (Week 3):** Distributed processing and error handling
4. **Phase 4 (Week 4):** Monitoring, observability, and performance testing
5. **Phase 5 (Week 5):** Integration testing with production data (read-only)
6. **Phase 6 (Week 6):** Production rollout with feature flag

## Risk Mitigation

- **High Risk:** Email delivery failures → Implement fallback channels
- **Medium Risk:** Database performance → Add proper indexing
- **Low Risk:** Timezone bugs → Extensive timezone testing

## Success Metrics

- **Onboarding completion time:** Reduce by 20%
- **Client satisfaction:** Improve NPS by 10 points
- **Agent efficiency:** <5% false positive stuck detection rate
- **System reliability:** 99.9% uptime
