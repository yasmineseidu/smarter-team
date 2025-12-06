# Meeting Reminder Agent - Production Specification

## Overview

**Category**: Meeting Management
**Purpose**: Reduce no-shows through automated multi-channel reminders at strategic intervals
**Priority**: Phase 1 - MVP Foundation
**Dependencies**: Meeting Scheduler Agent (provides meeting data)

## System Prompt

```
You are the Meeting Reminder Agent for Smarter Team, responsible for sending timely,
professional reminders that reduce no-shows and maintain strong client relationships.

Your responsibilities:
1. Monitor upcoming meetings and send reminders at optimal times (24h, 2h, 15min before)
2. Personalize reminder content using lead/meeting context from memory
3. Choose appropriate channels (email vs SMS) based on timing and availability
4. Track reminder delivery and engagement metrics
5. Handle timezone conversions and scheduling edge cases
6. Log all reminder activity for analytics

Communication style:
- Friendly and professional, not robotic
- Concise - respect the recipient's time
- Include clear meeting details and action items
- Make it easy to join (one-click links)

Important rules:
- NEVER send duplicate reminders for the same meeting/interval
- ALWAYS verify timezone before sending
- ALWAYS include meeting link and time in reminders
- NEVER send reminders for cancelled meetings
- If phone number unavailable, skip SMS reminders (no errors)
- Log failures but continue with other reminders

Error handling:
- Email failures: Log and retry once after 5 minutes
- SMS failures: Log but do not retry (avoid duplicate charges)
- Database errors: Log and alert via monitoring
- Timezone parsing errors: Default to UTC and log warning
```

## Tools

### 1. `query_upcoming_meetings`

**Description**: Query database for meetings needing reminders in the next N hours.

**Parameters**:
- `hours_ahead` (int, required): How many hours ahead to look (1-48)
- `reminder_type` (str, required): Filter by reminder interval ("24h", "2h", "15min")

**Returns**:
```python
{
    "meetings": [
        {
            "id": str,                    # Meeting UUID
            "lead_id": str,               # Lead UUID
            "scheduled_time": str,        # ISO 8601 timestamp
            "timezone": str,              # IANA timezone (e.g., "America/New_York")
            "meeting_link": str,          # Cal.com meeting URL
            "duration_minutes": int,      # Meeting duration
            "lead_name": str,             # Lead full name
            "lead_email": str,            # Lead email
            "lead_phone": str | None,     # Lead phone (E.164 format)
            "last_reminder_sent": str | None,  # Last reminder type sent
        }
    ],
    "count": int
}
```

**Implementation**:
```python
async def query_upcoming_meetings(
    hours_ahead: int,
    reminder_type: str,
) -> dict[str, Any]:
    """
    Query meetings needing reminders.

    Filters:
    - Meeting status = CONFIRMED
    - Meeting time is between NOW and NOW + hours_ahead
    - Reminder not already sent for this interval
    - Meeting not cancelled
    """
    # SQL query with SQLAlchemy async
    pass
```

### 2. `send_email_reminder`

**Description**: Send email reminder via configured email provider.

**Parameters**:
- `meeting_id` (str, required): Meeting UUID
- `recipient_email` (str, required): Lead email address
- `recipient_name` (str, required): Lead first name or full name
- `subject` (str, required): Email subject line
- `body` (str, required): Email body (HTML supported)
- `meeting_time` (str, required): Meeting time in recipient's timezone
- `meeting_link` (str, required): Cal.com meeting URL

**Returns**:
```python
{
    "success": bool,
    "message_id": str | None,      # Provider's message ID
    "error": str | None,            # Error message if failed
    "timestamp": str                # ISO 8601 send time
}
```

**Implementation**:
```python
async def send_email_reminder(
    meeting_id: str,
    recipient_email: str,
    recipient_name: str,
    subject: str,
    body: str,
    meeting_time: str,
    meeting_link: str,
) -> dict[str, Any]:
    """
    Send email via Instantly.ai or Gmail integration.

    Steps:
    1. Validate inputs (email format, non-empty fields)
    2. Render email template with personalization
    3. Send via integration client
    4. Log to reminder_logs table
    5. Return delivery status
    """
    pass
```

### 3. `send_sms_reminder`

**Description**: Send SMS reminder via configured SMS provider.

**Parameters**:
- `meeting_id` (str, required): Meeting UUID
- `recipient_phone` (str, required): Lead phone in E.164 format (+1234567890)
- `recipient_name` (str, required): Lead first name
- `message` (str, required): SMS body (max 160 chars recommended)
- `meeting_time` (str, required): Meeting time in recipient's timezone
- `meeting_link` (str, required): Cal.com meeting URL

**Returns**:
```python
{
    "success": bool,
    "message_id": str | None,      # Provider's message SID
    "error": str | None,            # Error message if failed
    "timestamp": str,               # ISO 8601 send time
    "cost": float | None            # SMS cost in USD (if available)
}
```

**Implementation**:
```python
async def send_sms_reminder(
    meeting_id: str,
    recipient_phone: str,
    recipient_name: str,
    message: str,
    meeting_time: str,
    meeting_link: str,
) -> dict[str, Any]:
    """
    Send SMS via Twilio/similar provider.

    Steps:
    1. Validate phone number format (E.164)
    2. Check SMS character count (warn if >160)
    3. Send via SMS integration client
    4. Log to reminder_logs table with cost tracking
    5. Return delivery status
    """
    pass
```

### 4. `log_reminder_sent`

**Description**: Record reminder delivery in database for tracking and deduplication.

**Parameters**:
- `meeting_id` (str, required): Meeting UUID
- `reminder_type` (str, required): "24h", "2h", or "15min"
- `channel` (str, required): "email" or "sms"
- `success` (bool, required): Whether delivery succeeded
- `message_id` (str, optional): Provider's message ID
- `error` (str, optional): Error message if failed
- `sent_at` (str, required): ISO 8601 timestamp of send attempt

**Returns**:
```python
{
    "log_id": str,                  # UUID of reminder_log entry
    "created_at": str               # ISO 8601 timestamp
}
```

**Implementation**:
```python
async def log_reminder_sent(
    meeting_id: str,
    reminder_type: str,
    channel: str,
    success: bool,
    message_id: str | None = None,
    error: str | None = None,
    sent_at: str | None = None,
) -> dict[str, Any]:
    """
    Insert into reminder_logs table.

    Also updates meetings.last_reminder_sent for deduplication.
    """
    pass
```

### 5. `format_timezone_display`

**Description**: Convert UTC time to recipient's timezone with human-friendly formatting.

**Parameters**:
- `utc_time` (str, required): ISO 8601 UTC timestamp
- `target_timezone` (str, required): IANA timezone (e.g., "America/Los_Angeles")

**Returns**:
```python
{
    "formatted_time": str,          # "Tuesday, Dec 5 at 2:30 PM PST"
    "iso_time": str,                # ISO 8601 in target timezone
    "timezone_abbr": str            # "PST", "EST", etc.
}
```

**Implementation**:
```python
async def format_timezone_display(
    utc_time: str,
    target_timezone: str,
) -> dict[str, Any]:
    """
    Use pytz or zoneinfo for timezone conversion.

    Handles DST transitions automatically.
    """
    pass
```

### 6. `get_meeting_context`

**Description**: Retrieve additional context about the meeting from memory/database.

**Parameters**:
- `meeting_id` (str, required): Meeting UUID
- `lead_id` (str, required): Lead UUID

**Returns**:
```python
{
    "lead": {
        "first_name": str,
        "company": str | None,
        "last_interaction": str | None,  # Summary of last email/call
    },
    "meeting": {
        "booked_at": str,               # When meeting was scheduled
        "notes": str | None,            # Meeting description/notes
        "prep_available": bool,         # Has Meeting Prep Agent run?
    },
    "context_summary": str              # 1-2 sentence summary for personalization
}
```

**Implementation**:
```python
async def get_meeting_context(
    meeting_id: str,
    lead_id: str,
) -> dict[str, Any]:
    """
    Pull from:
    1. meetings table (notes, booked_at)
    2. leads table (company, last_interaction)
    3. Zep memory (optional: conversation history summary)
    """
    pass
```

## Reminder Templates

### 24 Hours Before - Email

**Subject**: Looking forward to our call tomorrow!

**Body**:
```html
Hi {{first_name}},

Just a friendly reminder about our call tomorrow at {{meeting_time}}.

Here's your meeting link:
{{meeting_link}}

Looking forward to chatting!

Best,
Smarter Team

---
Need to reschedule? Reply to this email and we'll find a better time.
```

### 24 Hours Before - SMS

```
Reminder: Call with Smarter Team tomorrow at {{meeting_time}}. Link: {{meeting_link}}
```

### 2 Hours Before - Email

**Subject**: See you in 2 hours!

**Body**:
```html
Hi {{first_name}},

Quick reminder - we're meeting at {{meeting_time}} today.

Join here: {{meeting_link}}

See you soon!
```

### 15 Minutes Before - SMS

```
Starting in 15 min! Join here: {{meeting_link}}
```

## Database Schema

### `meeting_reminders` table

**Purpose**: Track which reminders have been sent for each meeting.

```sql
CREATE TABLE meeting_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    reminder_24h_sent_at TIMESTAMPTZ NULL,
    reminder_2h_sent_at TIMESTAMPTZ NULL,
    reminder_15min_sent_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_meeting_reminders_meeting ON meeting_reminders(meeting_id);
CREATE INDEX idx_meeting_reminders_24h ON meeting_reminders(reminder_24h_sent_at) WHERE reminder_24h_sent_at IS NULL;
CREATE INDEX idx_meeting_reminders_2h ON meeting_reminders(reminder_2h_sent_at) WHERE reminder_2h_sent_at IS NULL;
CREATE INDEX idx_meeting_reminders_15min ON meeting_reminders(reminder_15min_sent_at) WHERE reminder_15min_sent_at IS NULL;
```

### `reminder_logs` table

**Purpose**: Audit log of all reminder attempts (success and failures).

```sql
CREATE TABLE reminder_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    reminder_type VARCHAR(10) NOT NULL CHECK (reminder_type IN ('24h', '2h', '15min')),
    channel VARCHAR(10) NOT NULL CHECK (channel IN ('email', 'sms')),
    recipient VARCHAR(255) NOT NULL,  -- Email or phone
    success BOOLEAN NOT NULL,
    message_id VARCHAR(255) NULL,     -- Provider's message ID
    error_message TEXT NULL,
    cost_usd DECIMAL(6,4) NULL,       -- SMS cost tracking
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reminder_logs_meeting ON reminder_logs(meeting_id);
CREATE INDEX idx_reminder_logs_sent_at ON reminder_logs(sent_at DESC);
CREATE INDEX idx_reminder_logs_success ON reminder_logs(success);
```

## Celery Task Configuration

### Task: `send_meeting_reminders`

**Schedule**: Runs every hour via Celery Beat

**Cron**: `0 * * * *` (hourly at :00)

**Priority**: High (reminders are time-sensitive)

**Max Retries**: 0 (rely on next hourly run to catch failures)

**Soft Time Limit**: 5 minutes

**Implementation**:
```python
from celery import Celery
from src.agents.meeting_reminder.agent import MeetingReminderAgent

@celery_app.task(
    bind=True,
    name="send_meeting_reminders",
    max_retries=0,
    soft_time_limit=300,  # 5 minutes
)
async def send_meeting_reminders(self) -> dict[str, Any]:
    """
    Celery Beat task to send meeting reminders.

    Runs hourly to check for meetings needing reminders.
    """
    agent = MeetingReminderAgent(
        name="meeting_reminder",
        description="Sends automated meeting reminders"
    )

    # Process each reminder interval
    results = {
        "24h": await agent.process_task({"reminder_type": "24h"}),
        "2h": await agent.process_task({"reminder_type": "2h"}),
        "15min": await agent.process_task({"reminder_type": "15min"}),
    }

    return {
        "status": "completed",
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Celery Beat Config** (`src/tasks/beat_schedule.py`):
```python
from celery.schedules import crontab

beat_schedule = {
    "send-meeting-reminders": {
        "task": "send_meeting_reminders",
        "schedule": crontab(minute=0),  # Every hour at :00
        "options": {"priority": 7}       # High priority (0-9 scale)
    }
}
```

## Agent Implementation Pattern

### Class Structure

```python
from typing import Any
from src.agents.base_agent import BaseAgent
from src.integrations.email_client import EmailClient  # Instantly.ai or Gmail
from src.integrations.sms_client import SMSClient      # Twilio/similar

class MeetingReminderAgent(BaseAgent):
    """
    Sends automated meeting reminders via email and SMS.
    """

    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)

        # Register tools
        self.register_tool(query_upcoming_meetings, "query_upcoming_meetings")
        self.register_tool(send_email_reminder, "send_email_reminder")
        self.register_tool(send_sms_reminder, "send_sms_reminder")
        self.register_tool(log_reminder_sent, "log_reminder_sent")
        self.register_tool(format_timezone_display, "format_timezone_display")
        self.register_tool(get_meeting_context, "get_meeting_context")

    @property
    def system_prompt(self) -> str:
        return """[Full system prompt from above]"""

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process reminder sending for a specific interval.

        Args:
            task: {"reminder_type": "24h" | "2h" | "15min"}
        """
        reminder_type = task.get("reminder_type", "24h")

        # Map reminder type to hours ahead
        hours_map = {"24h": 24, "2h": 2, "15min": 0.25}
        hours_ahead = hours_map[reminder_type]

        # Query meetings
        meetings_data = await query_upcoming_meetings(
            hours_ahead=hours_ahead,
            reminder_type=reminder_type
        )

        sent_count = 0
        failed_count = 0

        for meeting in meetings_data["meetings"]:
            try:
                # Get additional context
                context = await get_meeting_context(
                    meeting_id=meeting["id"],
                    lead_id=meeting["lead_id"]
                )

                # Format meeting time
                time_display = await format_timezone_display(
                    utc_time=meeting["scheduled_time"],
                    target_timezone=meeting["timezone"]
                )

                # Send appropriate reminders based on interval
                if reminder_type == "24h":
                    # Send both email and SMS
                    await self._send_24h_reminders(meeting, context, time_display)
                elif reminder_type == "2h":
                    # Email only
                    await self._send_2h_reminder(meeting, context, time_display)
                else:  # 15min
                    # SMS only (if phone available)
                    await self._send_15min_reminder(meeting, context, time_display)

                sent_count += 1

            except Exception as e:
                self.logger.error(
                    f"Failed to send reminder for meeting {meeting['id']}",
                    extra={"error": str(e)}
                )
                failed_count += 1

        return {
            "reminder_type": reminder_type,
            "meetings_processed": len(meetings_data["meetings"]),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "status": "completed"
        }
```

## Error Handling Strategy

### Email Failures
1. **Network errors**: Retry once after 5-minute delay
2. **Invalid email**: Log error, mark as failed, alert monitoring
3. **Provider rate limits**: Exponential backoff, queue for next run
4. **Bounce/reject**: Log in reminder_logs, update lead status

### SMS Failures
1. **Invalid phone number**: Log error, skip SMS (no retry)
2. **Provider errors**: Log error, do not retry (avoid duplicate charges)
3. **Phone number unavailable**: Skip SMS gracefully (expected scenario)

### Database Failures
1. **Connection errors**: Retry with exponential backoff (3 attempts)
2. **Constraint violations**: Log and skip (likely duplicate reminder)
3. **Query timeouts**: Alert monitoring, fail gracefully

### Timezone Parsing Errors
1. **Invalid timezone string**: Default to UTC, log warning
2. **DST transition edge cases**: Use pytz/zoneinfo built-in handling
3. **Missing timezone**: Default to account timezone or UTC

### General Error Handling
- All errors logged with structured logging (`extra` fields)
- Critical errors (DB down, auth failures) trigger monitoring alerts
- Non-critical errors (individual reminder failures) logged but don't block batch
- Retry logic: Email retries yes (cheap), SMS retries no (costly)

## Integrations Required

### Email Provider
- **Primary**: Instantly.ai API (for campaign tracking)
- **Fallback**: Gmail API (via Google OAuth)
- **Config**: `INSTANTLY_API_KEY` or `GMAIL_CREDENTIALS_JSON`

### SMS Provider
- **Recommended**: Twilio (industry standard)
- **Alternatives**: AWS SNS, Plivo, Vonage
- **Config**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

### Database
- **Primary**: Supabase PostgreSQL (via SQLAlchemy async)
- **Connection pool**: 10-20 connections for reminder tasks

### Memory (Optional)
- **Zep**: For retrieving conversation context to personalize reminders
- **Fallback**: Database-only approach if Zep not configured

## Testing Requirements

### Unit Tests (Target: >85% coverage)

**File**: `app/backend/__tests__/unit/agents/test_meeting_reminder.py`

1. **Agent Initialization**
   - Verify tools are registered
   - System prompt is set correctly

2. **Tool Testing**
   - `query_upcoming_meetings`: Mock database, verify filters
   - `send_email_reminder`: Mock email client, verify template rendering
   - `send_sms_reminder`: Mock SMS client, verify character limits
   - `log_reminder_sent`: Mock database, verify deduplication
   - `format_timezone_display`: Test multiple timezones, DST transitions
   - `get_meeting_context`: Mock memory/database queries

3. **Reminder Logic**
   - 24h reminders send both email and SMS
   - 2h reminders send email only
   - 15min reminders send SMS only (if phone available)
   - Skip SMS gracefully when phone number is None

4. **Error Handling**
   - Email retry logic on network errors
   - SMS no-retry on failures
   - Invalid timezone fallback to UTC
   - Database connection failures

5. **Deduplication**
   - Don't send duplicate reminders for same meeting/interval
   - Check `meeting_reminders` table before sending

### Integration Tests

**File**: `app/backend/__tests__/integration/test_meeting_reminder_agent.py`

1. **End-to-End Reminder Flow**
   - Create test meeting in database
   - Run agent with reminder_type="24h"
   - Verify email sent (mock provider)
   - Verify SMS sent (mock provider)
   - Verify logs created in `reminder_logs`
   - Verify `meeting_reminders` table updated

2. **Celery Task Integration**
   - Schedule `send_meeting_reminders` task
   - Verify task executes successfully
   - Check task result contains all reminder types

3. **Database Integration**
   - Test with real PostgreSQL (test database)
   - Verify indexes are used (EXPLAIN ANALYZE)
   - Test concurrent reminder sends (no race conditions)

4. **Timezone Handling**
   - Test meetings across multiple timezones
   - Verify correct time display for each recipient
   - Test DST transitions (spring forward, fall back)

### Fixtures

**File**: `app/backend/__tests__/fixtures/meeting_reminder_fixtures.py`

```python
import pytest
from datetime import datetime, timedelta

@pytest.fixture
def mock_meeting():
    """Sample meeting data for testing."""
    return {
        "id": "mtg_123",
        "lead_id": "lead_456",
        "scheduled_time": (datetime.utcnow() + timedelta(hours=23)).isoformat(),
        "timezone": "America/Los_Angeles",
        "meeting_link": "https://cal.com/smarter-team/discovery",
        "duration_minutes": 30,
        "lead_name": "John Doe",
        "lead_email": "john@example.com",
        "lead_phone": "+14155551234",
        "last_reminder_sent": None
    }

@pytest.fixture
def mock_email_client(mocker):
    """Mock email client for testing."""
    return mocker.patch("src.integrations.email_client.EmailClient")

@pytest.fixture
def mock_sms_client(mocker):
    """Mock SMS client for testing."""
    return mocker.patch("src.integrations.sms_client.SMSClient")
```

### Test Coverage Targets
- **Tools**: >90% (isolated function testing)
- **Agent class**: >85% (process_task and helper methods)
- **Integration**: >80% (end-to-end flows)
- **Error paths**: 100% (all error handlers tested)

## Performance Considerations

### Scalability
- **Batch size**: Process up to 100 meetings per reminder interval
- **Concurrency**: Use asyncio.gather() for parallel reminder sends
- **Rate limiting**: Respect provider rate limits (email: 100/min, SMS: 10/sec)

### Database Optimization
- **Indexes**: On meeting_reminders (reminder_*_sent_at WHERE NULL)
- **Query optimization**: Single query per reminder interval (not per meeting)
- **Connection pooling**: Reuse connections across reminder batch

### Monitoring Metrics
- **Reminders sent**: Counter by type (24h, 2h, 15min) and channel (email, SMS)
- **Delivery rate**: Success vs failure percentage
- **Latency**: Time to send all reminders per interval
- **Error rate**: Track provider errors, database errors, timezone errors

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Create `meeting_reminders` table migration
- [ ] Create `reminder_logs` table migration
- [ ] Implement `BaseAgent` extension for `MeetingReminderAgent`
- [ ] Add system prompt with error handling rules
- [ ] Register all 6 tools with agent

### Phase 2: Tool Implementation
- [ ] Implement `query_upcoming_meetings` with SQLAlchemy async
- [ ] Implement `send_email_reminder` with Instantly.ai integration
- [ ] Implement `send_sms_reminder` with Twilio integration
- [ ] Implement `log_reminder_sent` with deduplication logic
- [ ] Implement `format_timezone_display` with pytz/zoneinfo
- [ ] Implement `get_meeting_context` with memory integration

### Phase 3: Reminder Logic
- [ ] Implement 24h reminder flow (email + SMS)
- [ ] Implement 2h reminder flow (email only)
- [ ] Implement 15min reminder flow (SMS only)
- [ ] Add template rendering with personalization
- [ ] Add error handling for each reminder type

### Phase 4: Celery Integration
- [ ] Create `send_meeting_reminders` Celery task
- [ ] Configure Celery Beat schedule (hourly cron)
- [ ] Add task monitoring and alerting
- [ ] Test task execution in development

### Phase 5: Testing
- [ ] Write unit tests for all 6 tools (>90% coverage)
- [ ] Write agent process_task tests (>85% coverage)
- [ ] Write integration tests for end-to-end flow
- [ ] Write timezone handling tests (DST edge cases)
- [ ] Write error handling tests (all error paths)

### Phase 6: Integration & Deployment
- [ ] Set up email provider credentials (Instantly.ai or Gmail)
- [ ] Set up SMS provider credentials (Twilio)
- [ ] Run database migrations in staging
- [ ] Deploy Celery Beat to staging
- [ ] Monitor first 24 hours of reminder sends
- [ ] Tune rate limits and batch sizes
- [ ] Deploy to production

### Phase 7: Monitoring & Iteration
- [ ] Set up Prometheus metrics for reminder sends
- [ ] Configure alerts for high failure rates
- [ ] Review reminder_logs weekly for patterns
- [ ] Gather feedback on reminder timing/content
- [ ] A/B test reminder templates (future)

## Success Metrics

### Primary KPIs
- **No-show rate reduction**: Target <15% (from typical 20-30%)
- **Delivery success rate**: Target >98% for email, >95% for SMS
- **Reminder latency**: Send all reminders within 5 minutes of schedule

### Secondary Metrics
- **Engagement rate**: Track email opens, link clicks
- **Opt-out rate**: Monitor unsubscribe requests
- **Cost per reminder**: Track SMS costs, optimize send logic
- **Error rate**: Target <2% overall error rate

## Future Enhancements (Not in MVP)

1. **Smart send-time optimization**: Learn optimal reminder times per lead
2. **A/B testing framework**: Test different templates and timing
3. **Multi-language support**: Detect lead language, send localized reminders
4. **Calendar integration**: Add to Google Calendar / Outlook
5. **Reminder preferences**: Allow leads to customize reminder frequency
6. **Voice call reminders**: Integration with Retell AI for voice reminders
7. **Engagement tracking**: Monitor which reminders reduce no-shows most
8. **Predictive no-show detection**: Use ML to identify high-risk meetings

## Dependencies

### Python Packages
- `sqlalchemy[asyncio]>=2.0.44` - Database ORM
- `asyncpg>=0.31.0` - PostgreSQL async driver
- `celery>=5.6.0` - Task queue
- `redis>=6.4.0` - Celery broker
- `httpx>=0.27.0` - HTTP client for integrations
- `pytz>=2024.1` - Timezone handling
- `python-dateutil>=2.8.2` - Date parsing
- `jinja2>=3.1.2` - Template rendering

### External Services
- **Instantly.ai** or **Gmail**: Email delivery
- **Twilio**: SMS delivery
- **Supabase PostgreSQL**: Database
- **Redis**: Celery broker
- **Zep** (optional): Memory context

## Security Considerations

1. **API Key Management**: Store in environment variables, never in code
2. **Phone Number Privacy**: Hash phone numbers in logs, comply with TCPA
3. **Email Privacy**: Follow CAN-SPAM, include unsubscribe links
4. **Rate Limiting**: Prevent abuse of reminder system
5. **Input Validation**: Sanitize all user inputs (names, emails, phones)
6. **Audit Logging**: Log all reminder sends for compliance

## Compliance

- **CAN-SPAM Act**: Include unsubscribe link in all emails
- **TCPA (SMS)**: Only send SMS to leads who provided consent
- **GDPR**: Allow leads to opt out of reminders
- **Data Retention**: Delete reminder logs after 90 days (configurable)

---

## References

- [Claude Agent SDK Python Docs](https://docs.claude.com/en/docs/agent-sdk/python)
- [Celery Beat Scheduling Guide](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [Cal.com API Documentation](https://cal.com/docs/api-reference)
- [Twilio SMS Best Practices](https://www.twilio.com/docs/sms/best-practices)

---

**Specification Version**: 1.0
**Last Updated**: 2025-12-05
**Status**: Ready for Implementation
