# Onboarding Stuck Detector Agent - Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Priority:** Phase 4 - Client Delivery
**Agent Type:** Monitoring + Automation
**Coverage Target:** >85%
**Refined From:** plan/agents/onboarding-stuck-detector.md

---

## Overview

The Onboarding Stuck Detector Agent proactively monitors client onboarding progress and identifies stalled workflows. It runs hourly checks, sends automated reminders to clients, alerts the agency owner when escalations are needed, and tracks all stuck detection events. The agent uses time-based patterns, heartbeat mechanisms, and state machines to detect and resolve onboarding bottlenecks before they impact client experience.

**Key Responsibilities:**
- Monitor all active onboarding workflows hourly
- Detect four types of stuck conditions (intake form, access requests, kickoff scheduling, communication gaps)
- Send personalized reminder emails to clients
- Escalate to agency owner via Slack/Telegram after multiple failed attempts
- Track all events and maintain state across runs
- Provide metrics and observability for onboarding health

---

## Agent Configuration

### BaseAgent Properties

```python
name: "onboarding_stuck_detector"
description: "Detects and resolves stalled client onboarding workflows"
```

### Dependencies

**Agent Dependencies:**
- `onboarding_orchestrator` - Provides onboarding status and state transitions
- `internal_setup` - Coordinates for access request issues

**Integration Dependencies:**
- Email service (SendGrid/SMTP) - Client reminders
- Slack/Telegram API - Owner escalations
- Database (PostgreSQL) - State tracking and queries
- Redis - Distributed locking and caching

### Runtime Configuration

```python
class OnboardingStuckDetectorConfig:
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower for consistent behavior
    max_retries: int = 3
    timeout_seconds: int = 60
    check_interval_minutes: int = 60  # Hourly checks
    reminder_limit: int = 2  # Max reminders before escalation
    escalation_days: int = 7  # Days before escalating
    stuck_threshold_days: int = 10  # Days before marking as ONBOARDING_STUCK
```

---

## System Prompt

```
You are the Onboarding Stuck Detector Agent for Smarter Team, an AI agency automation system.

Your role is to proactively monitor client onboarding progress and identify stalled workflows before they become problems.

CORE RESPONSIBILITIES:
1. Monitor all active onboarding workflows hourly using cron triggers
2. Detect four types of stuck conditions with precise time-based rules
3. Send personalized reminder emails to clients when workflows stall
4. Track all communications and avoid duplicate reminders
5. Escalate to agency owner when reminders don't resolve issues
6. Maintain accurate state across all monitoring cycles

STUCK DETECTION RULES (strict):
- Intake Form Stuck: Form sent >3 days ago AND not completed
- Access Request Stuck: Access requested >2 days ago AND not received
- Kickoff Stuck: Onboarding started >5 days ago AND kickoff not scheduled
- Communication Stuck: Last communication >5 days ago (any type)

ESCALATION PROTOCOL:
1. First Detection: Send reminder email to client
2. 48 Hours Later: Send second reminder if still stuck
3. 48 Hours Later: Alert agency owner via Slack/Telegram
4. 72 Hours Later: Mark onboarding as ONBOARDING_STUCK

BUSINESS RULES:
- Count business days only (exclude weekends)
- Check for existing reminders to avoid duplicates
- Log every action for audit trail
- Use Redis distributed locks to prevent concurrent processing
- Handle timezone differences correctly (use client's timezone)

COMMUNICATION STYLE:
- Professional but friendly tone
- Action-oriented with clear next steps
- Include direct links to forms/resources
- Acknowledge potential client issues
- Offer assistance and remove friction

DECISION LOGIC:
- Always check if reminder already sent in last 48 hours
- Verify onboarding is still in ONBOARDING state
- Confirm client hasn't already responded
- Check for recent manual overrides by human staff
```

---

## Tools

### Tool: check_onboarding_status

**Purpose:** Query database for onboarding records that need checking

**Input Schema:**
```python
class CheckOnboardingStatusInput(BaseModel):
    check_type: str = Field(..., description="Type of check: intake, access, kickoff, communication")
    hours_since_last_check: int = Field(default=1, description="Minimum hours since last check")
    limit: int = Field(default=100, ge=1, le=1000, description="Max records to process")
```

**Output Schema:**
```python
class OnboardingRecord(BaseModel):
    client_id: str
    onboarding_id: str
    client_name: str
    client_email: str
    timezone: str
    onboarding_start_date: datetime
    current_state: str
    stuck_type: str | None
    days_stuck: int | None
    last_reminder_sent: datetime | None
    reminder_count: int
    access_requests: list[dict]
    communication_history: list[dict]

class CheckOnboardingStatusOutput(BaseModel):
    records: list[OnboardingRecord]
    total_count: int
    check_timestamp: datetime
    processing_time_ms: float
```

**Error Handling:**
- Database timeout → Retry 3x with exponential backoff
- Connection error → Log and return empty results
- Invalid timezone → Default to UTC

**Example:**
```python
# Input
{"check_type": "intake", "hours_since_last_check": 1}

# Output
{
    "records": [
        {
            "client_id": "cli_123",
            "onboarding_id": "onb_456",
            "client_name": "Acme Corp",
            "client_email": "john@acme.com",
            "timezone": "America/New_York",
            "onboarding_start_date": "2025-01-01T10:00:00Z",
            "current_state": "ONBOARDING",
            "stuck_type": "intake",
            "days_stuck": 4,
            "last_reminder_sent": "2025-01-03T14:00:00Z",
            "reminder_count": 1,
            "access_requests": [],
            "communication_history": [...]
        }
    ],
    "total_count": 1,
    "check_timestamp": "2025-01-05T09:00:00Z",
    "processing_time_ms": 125.5
}
```

### Tool: send_reminder_email

**Purpose:** Send personalized reminder email to client

**Input Schema:**
```python
class ReminderEmailInput(BaseModel):
    client_id: str
    onboarding_id: str
    reminder_type: str = Field(..., description="intake, access, kickoff, communication")
    recipient_email: str
    recipient_name: str
    stuck_days: int
    reminder_count: int
    custom_message: str | None = None
    include_links: bool = True
```

**Output Schema:**
```python
class ReminderEmailOutput(BaseModel):
    success: bool
    email_id: str | None
    sent_timestamp: datetime
    error_message: str | None
    bounce_detected: bool
    next_reminder_date: datetime | None
```

**Error Handling:**
- Email service rate limit (429) → Backoff 60 seconds, retry once
- Invalid email → Log error, skip sending, mark for manual review
- Service unavailable → Queue for retry in 30 minutes
- Bounce detected → Flag account for human follow-up

**Templates:**

**Intake Form Reminder:**
```html
Subject: Quick reminder: Intake form for {{company_name}}

Hi {{first_name}},

Just checking in - I noticed the intake form is still pending. This helps us prepare for your kickoff call and ensures we have all the information needed to get started.

Here's the link again: {{intake_form_link}}

The form only takes about 10 minutes to complete. If you have any questions or need help with anything, please let me know!

Best regards,
{{signature}}
```

### Tool: send_escalation_alert

**Purpose:** Send alert to agency owner via Slack/Telegram

**Input Schema:**
```python
class EscalationAlertInput(BaseModel):
    client_id: str
    onboarding_id: str
    client_name: str
    stuck_type: str
    stuck_days: int
    reminders_sent: int
    last_communication: datetime | None
    risk_level: str = Field(..., description="medium, high, critical")
    recommended_action: str | None = None
```

**Output Schema:**
```python
class EscalationAlertOutput(BaseModel):
    success: bool
    alert_id: str
    sent_timestamp: datetime
    channels: list[str]
    error_message: str | None
    follow_up_required: bool
```

**Error Handling:**
- Slack API error → Try Telegram as fallback
- Both channels fail → Send email alert, log critical error
- Rate limit → Queue alert, retry in 5 minutes
- Invalid webhook → Alert dev team via monitoring system

### Tool: update_onboarding_state

**Purpose:** Update onboarding record with reminder/escalation data

**Input Schema:**
```python
class UpdateOnboardingStateInput(BaseModel):
    onboarding_id: str
    action: str = Field(..., description="reminder_sent, escalated, marked_stuck")
    action_details: dict[str, Any]
    next_check_date: datetime | None = None
    state_change: dict[str, Any] | None = None
```

**Output Schema:**
```python
class UpdateOnboardingStateOutput(BaseModel):
    success: bool
    updated_at: datetime
    previous_state: str | None
    new_state: str | None
    changes_applied: list[str]
    error_message: str | None
```

**Error Handling:**
- Concurrent modification → Use optimistic locking, retry once
- Invalid state transition → Log error, require manual review
- Database constraint → Rollback, investigate data integrity

---

## Error Handling Matrix

| Error Type | Detection | Response | Retry | Alert |
|------------|-----------|----------|-------|-------|
| Database timeout | Query >30s | Exponential backoff | Yes (3x) | No |
| Email service down | 5xx response | Queue for retry | Yes (in 30m) | Yes |
| Slack webhook fail | 4xx/5xx response | Try Telegram fallback | Yes (once) | Yes |
| Invalid timezone | Validation error | Default to UTC | No | No |
| Concurrent processing | Redis lock fails | Skip, let other run | No | No |
| Client email bounce | Bounce webhook | Flag for human review | No | Yes |
| Rate limit exceeded | 429 response | Backoff + queue | Yes | No |
| Memory/CPU high | Prometheus alert | Scale up resources | N/A | Yes |

### Recovery Strategies

1. **Graceful Degradation:** Continue processing other onboardings if one fails
2. **Circuit Breaker:** Temporarily skip integrations after 3 consecutive failures
3. **Dead Letter Queue:** Failed operations stored for manual review
4. **State Recovery:** Reconcile state from database on restart
5. **Distributed Locking:** Prevent multiple instances from processing same client

---

## Multi-Agent Integration

### Handoff Scenarios

**To Onboarding Orchestrator:**
```python
await self.handoff_to(
    target_agent="onboarding_orchestrator",
    payload={
        "action": "manual_override_required",
        "client_id": client_id,
        "onboarding_id": onboarding_id,
        "reason": "stuck_onboarding_escalated",
        "details": {
            "stuck_type": "intake",
            "stuck_days": 8,
            "reminders_sent": 2,
            "escalation_sent": True
        }
    },
    priority="high"
)
```

**To Internal Setup Agent:**
```python
await self.handoff_to(
    target_agent="internal_setup",
    payload={
        "action": "access_request_expedite",
        "client_id": client_id,
        "pending_requests": access_requests,
        "reason": "client_unresponsive_to_reminders"
    },
    priority="normal"
)
```

### Event Subscriptions

- `onboarding.started` - Begin monitoring
- `onboarding.form_completed` - Clear intake stuck condition
- `onboarding.access_received` - Clear access stuck condition
- `onboarding.kickoff_scheduled` - Clear kickoff stuck condition
- `onboarding.communication_sent` - Update last communication timestamp
- `onboarding.completed` - Stop monitoring

---

## Testing Strategy

### Unit Tests

```python
class TestOnboardingStuckDetector:
    @pytest.mark.asyncio
    async def test_intake_form_stuck_detection(self):
        """Verify 3+ day stuck intake forms are detected"""

    @pytest.mark.asyncio
    async def test_reminder_email_generation(self):
        """Verify correct template used and personalization applied"""

    @pytest.mark.asyncio
    async def test_duplicate_reminder_prevention(self):
        """Verify reminders not sent within 48 hours"""

    @pytest.mark.asyncio
    async def test_escalation_after_two_reminders(self):
        """Verify escalation triggered after reminder limit"""

    @pytest.mark.asyncio
    async def test_weekend_day_counting(self):
        """Verify business day calculation excludes weekends"""

    @pytest.mark.asyncio
    async def test_timezone_handling(self):
        """Verify client timezone respected in calculations"""
```

### Integration Tests

```python
class TestOnboardingStuckDetectorIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_stuck_workflow(self):
        """Complete workflow from detection to escalation"""

    @pytest.mark.asyncio
    async def test_concurrent_processing_prevention(self):
        """Verify Redis locks prevent duplicate processing"""

    @pytest.mark.asyncio
    async def test_email_service_failover(self):
        """Verify behavior when email service unavailable"""

    @pytest.mark.asyncio
    async def test_slack_telegram_fallback(self):
        """Verify Slack fails over to Telegram"""
```

### Mock Strategy

```python
@pytest.fixture
def mock_email_service():
    with patch('src.integrations.email.EmailService.send') as mock:
        mock.return_value = {"id": "email_123", "status": "sent"}
        yield mock

@pytest.fixture
def mock_slack_client():
    with patch('src.integrations.slack.SlackClient.send_message') as mock:
        mock.return_value = {"ok": True, "ts": "1234567890"}
        yield mock

@pytest.fixture
def mock_database():
    with patch('src.agents.onboarding_stuck_detector.queries') as mock:
        mock.get_stuck_onboardings.return_value = test_onboardings
        yield mock
```

### Test Coverage Requirements

- **Agent logic**: 90%+
- **Tool functions**: 95%+
- **Error handling**: 90%+
- **Integration points**: 85%+

---

## Performance & Scaling

### Expected Volume
- **Active onboardings**: 50-200 concurrent
- **Hourly checks**: 1 cron execution
- **Reminder emails**: 20-50/day
- **Escalations**: 2-5/week

### Optimization Strategies

1. **Batch Processing**: Process records in batches of 50
2. **Caching**: Cache client timezone and preferences in Redis
3. **Indexing**: Database indexes on onboarding_state, timestamps
4. **Connection Pooling**: Reuse database connections
5. **Async Operations**: Parallel email/Slack sending

### Resource Limits

```python
class ResourceLimits:
    max_concurrent_emails: int = 10
    max_db_connections: int = 20
    max_processing_time_minutes: int = 45
    max_memory_mb: int = 512
```

---

## Observability

### Logging Strategy

```python
logger = get_agent_logger("onboarding_stuck_detector")

# Structured logging examples
logger.info(
    "Stuck onboarding detected",
    extra={
        "client_id": client_id,
        "stuck_type": "intake",
        "stuck_days": 4,
        "detection_timestamp": datetime.utcnow().isoformat()
    }
)

logger.warning(
    "Escalation triggered",
    extra={
        "client_id": client_id,
        "reminders_sent": 2,
        "escalation_channel": "slack",
        "risk_level": "high"
    }
)
```

### Metrics to Track

1. **Business Metrics:**
   - Onboarding stuck rate (by type)
   - Average time to resolve stuck issues
   - Reminder effectiveness rate
   - Escalation frequency

2. **Technical Metrics:**
   - Processing duration per check
   - Email delivery success rate
   - Slack/Telegram alert success rate
   - Database query performance

3. **Health Metrics:**
   - Agent uptime
   - Error rates by type
   - Memory usage
   - Queue depth

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Counters
STUCK_DETECTIONS = Counter('onboarding_stuck_detections_total', 'Total stuck detections', ['type'])
REMINDERS_SENT = Counter('onboarding_reminders_sent_total', 'Reminders sent', ['type'])
ESCALATIONS = Counter('onboarding_escalations_total', 'Escalations sent', ['channel'])

# Histograms
PROCESSING_TIME = Histogram('onboarding_stuck_processing_seconds', 'Processing duration')

# Gauges
ACTIVE_ONBOARDINGS = Gauge('onboarding_active_count', 'Active onboarding count')
STUCK_ONBOARDINGS = Gauge('onboarding_stuck_count', 'Stuck onboarding count', ['type'])
```

---

## Security

### Data Protection

1. **PII Handling:** Client emails and names encrypted in database
2. **API Keys:** Stored in environment variables, rotated monthly
3. **Audit Trail:** All actions logged with user agent and IP
4. **Rate Limiting:** Prevent email bombing detection

### Permissions

- **Database:** Read-only access to onboarding tables, write access to alerts table
- **Email:** Send-only permissions, no inbox access
- **Slack/Telegram:** Webhook posting only, no admin rights

### Compliance

- **GDPR:** Client data processing with consent
- **CAN-SPAM:** Compliance for email sending
- **SOC2:** Audit logging and access controls

---

## Acceptance Criteria

- [ ] Agent detects all four types of stuck conditions with 100% accuracy
- [ ] Reminders sent within 1 hour of detection
- [ ] No duplicate reminders sent within 48 hours
- [ ] Escalations sent after 2 failed reminders
- [ ] Business days only counted in time calculations
- [ ] Client timezones respected in all communications
- [ ] All errors handled gracefully with appropriate logging
- [ ] 99.9% uptime with automated recovery from failures
- [ ] Integration tests covering all error scenarios
- [ ] Performance under 100 concurrent onboardings
- [ ] Complete audit trail maintained for compliance
- [ ] Alerts configured for critical failures
- [ ] Documentation updated with operational procedures
