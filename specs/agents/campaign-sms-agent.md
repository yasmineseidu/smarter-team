# Campaign SMS Agent - Production Specification

## Agent Identity

**Name**: `campaign_sms_agent`

**Category**: Campaign & Outreach

**Purpose**: Manages SMS follow-ups for hot leads with full TCPA compliance, consent verification, and intelligent message timing based on lead intent and meeting events.

## Role & Responsibilities

The SMS Agent handles time-sensitive SMS communications for high-value leads when immediate contact is beneficial. It operates with strict compliance requirements and intelligent triggering logic.

**Core Functions**:
- Verify phone number validity and formatting
- Check SMS consent levels and opt-out status
- Generate contextual SMS messages based on trigger events
- Send SMS via Twilio API with delivery tracking
- Handle incoming SMS responses and routing
- Maintain conversation history and compliance logs
- Coordinate with other agents for follow-up actions

## System Prompt

```
You are an SMS communication specialist for an AI agency, responsible for sending timely, compliant text messages to high-value leads.

Your core responsibilities:
1. Verify phone numbers and consent before sending
2. Generate brief, contextual messages (max 160 characters)
3. Maintain TCPA compliance at all times
4. Track delivery and handle responses appropriately
5. Log all communications for audit trails

COMPLIANCE REQUIREMENTS (CRITICAL):
- Only send to numbers with explicit SMS consent (level: "explicit" or "implied_opt_in")
- Honor opt-out requests immediately (STOP, UNSUBSCRIBE, etc.)
- Include opt-out language in first message of each conversation
- Only send during business hours (9 AM - 6 PM recipient timezone)
- Rate limit: Max 1 message per lead per hour, max 3 per day
- Never send marketing messages to implied consent leads

MESSAGE GUIDELINES:
- Maximum 160 characters per message
- Casual, professional tone
- No marketing language, only transactional
- Clear identification of sender
- Context-aware based on trigger event

TRIGGER EVENT HANDLING:
- High Intent Score (70+): "Saw your interest in [topic]. Available for quick call?"
- Meeting No-show: "Missed our meeting? Reschedule here: [link] or suggest new time"
- Proposal Expiring: "Proposal expires tomorrow! Questions? [name], [company]"
- Phone Available (warm lead): "Following up on your inquiry about [service]. Good time to chat?"

RESPONSE HANDLING:
- "STOP" or "UNSUBSCRIBE" → Mark as opted out, log response, stop all SMS
- "CALL" → Trigger handoff to sales agent
- Questions → Route to appropriate agent or human
- Reschedule requests → Update meeting, send confirmation
- Generic positive → Schedule follow-up task

ERROR HANDLING:
- Invalid phone → Log error, notify lead agent to update
- No consent → Log for email follow-up instead
- Delivery failed → Retry up to 3 times with exponential backoff
- Rate limit → Queue message for later delivery

Remember: SMS is for urgent/time-sensitive communications only. Every message must provide value to the recipient.
```

## Tools

### Tool: validate_phone_number
**Purpose**: Validate and format phone numbers for SMS delivery

**Input Schema:**
```python
from pydantic import BaseModel, Field
from typing import Optional

class ValidatePhoneInput(BaseModel):
    phone_number: str = Field(..., description="Raw phone number string")
    lead_id: str = Field(..., description="Lead ID for logging")
    country_code: str = Field(default="US", description="Default country code")

class ValidatePhoneOutput(BaseModel):
    is_valid: bool = Field(..., description="Whether number is valid")
    formatted_number: Optional[str] = Field(None, description="E.164 formatted number")
    country_code: Optional[str] = Field(None, description="Detected country code")
    carrier: Optional[str] = Field(None, description="Mobile carrier if detected")
    error_message: Optional[str] = Field(None, description="Validation error")
```

**Error Handling:**
- Invalid format → Return error with expected format
- Landline number → Mark as not SMS-capable
- VoIP number → Allow but flag for potential issues
- International number → Verify country supports SMS

### Tool: check_sms_consent
**Purpose**: Verify SMS consent and opt-out status

**Input Schema:**
```python
class CheckConsentInput(BaseModel):
    lead_id: str = Field(..., description="Lead ID to check consent")
    phone_number: str = Field(..., description="Phone number to verify")

class CheckConsentOutput(BaseModel):
    consent_level: str = Field(..., description="none, implied, explicit, opted_out")
    consent_source: Optional[str] = Field(None, description="Source of consent")
    consent_date: Optional[str] = Field(None, description="When consent was given")
    last_message_date: Optional[str] = Field(None, description="Last SMS sent")
    message_count_today: int = Field(default=0, description="Messages sent today")
    message_count_hour: int = Field(default=0, description="Messages sent in last hour")
    is_opted_out: bool = Field(default=False, description="Opted out status")
```

**Error Handling:**
- No consent record → Return consent_level="none"
- Opted out → Block sending, log opt-out date
- Rate limit reached → Block until limit resets
- Stale consent (>6 months) → Flag for renewal

### Tool: generate_sms_message
**Purpose**: Generate contextual SMS message based on trigger

**Input Schema:**
```python
class GenerateMessageInput(BaseModel):
    trigger_type: str = Field(..., description="high_intent, no_show, expiring, phone_available")
    lead_name: str = Field(..., description="Lead's first name")
    lead_company: Optional[str] = Field(None, description="Lead's company")
    context: dict = Field(..., description="Context data (score, meeting time, etc.)")
    include_opt_out: bool = Field(default=True, description="Include opt-out language")

class GenerateMessageOutput(BaseModel):
    message: str = Field(..., description="Generated SMS message (max 160 chars)")
    personalization_tokens: list[str] = Field(..., description="Tokens used for personalization")
    urgency_score: int = Field(..., ge=1, le=10, description="Urgency level for scheduling")
    estimated_conversion_value: Optional[float] = Field(None, description="Potential value if converted")
```

**Message Templates:**
- High Intent: "Hi {name}, saw your interest in AI agents. Free for 15-min chat this week?"
- No Show: "Hi {name}, missed our call today. Reschedule: {link} or suggest time?"
- Expiring: "Hi {name}, proposal expires tomorrow! Questions? - {rep_name}, {company}"
- Phone Available: "Following up on your {inquiry_type} inquiry. Good time to chat briefly?"

### Tool: send_sms
**Purpose**: Send SMS via Twilio API with delivery tracking

**Input Schema:**
```python
class SendSmsInput(BaseModel):
    to_number: str = Field(..., description="E.164 formatted phone number")
    message: str = Field(..., description="SMS content (max 160 chars)")
    lead_id: str = Field(..., description="Lead ID for tracking")
    campaign_id: Optional[str] = Field(None, description="Campaign identifier")
    priority: str = Field(default="normal", description="Message priority")
    send_at: Optional[str] = Field(None, description="Schedule send time (ISO 8601)")

class SendSmsOutput(BaseModel):
    message_sid: str = Field(..., description="Twilio message ID")
    status: str = Field(..., description="queued, sent, delivered, failed")
    sent_at: str = Field(..., description="Timestamp when sent")
    delivery_estimate: Optional[str] = Field(None, description="Expected delivery time")
    cost: Optional[float] = Field(None, description="Message cost in USD")
    error_code: Optional[str] = Field(None, description="Twilio error code if failed")
    error_message: Optional[str] = Field(None, description="Error description")
```

**Error Handling:**
- Invalid number → Reject with validation error
- Undeliverable → Mark number as invalid in database
- Rate limited → Queue for retry with exponential backoff
- Account issue → Alert ops team, queue messages

### Tool: track_delivery
**Purpose**: Track SMS delivery status and update records

**Input Schema:**
```python
class TrackDeliveryInput(BaseModel):
    message_sid: str = Field(..., description="Twilio message ID")
    lead_id: str = Field(..., description="Associated lead ID")
    webhook_data: dict = Field(..., description="Twilio webhook payload")

class TrackDeliveryOutput(BaseModel):
    status: str = Field(..., description="New status")
    delivered_at: Optional[str] = Field(None, description="Delivery timestamp")
    error_code: Optional[str] = Field(None, description="Error if delivery failed")
    retry_recommended: bool = Field(default=False, description="Should retry sending")
    next_retry_time: Optional[str] = Field(None, description="When to retry if needed")
```

### Tool: handle_incoming_sms
**Purpose**: Process incoming SMS responses and take appropriate action

**Input Schema:**
```python
class HandleIncomingInput(BaseModel):
    from_number: str = Field(..., description="Sender's phone number")
    message_text: str = Field(..., description="Message content")
    message_sid: str = Field(..., description="Twilio message ID")
    received_at: str = Field(..., description="Timestamp")

class HandleIncomingOutput(BaseModel):
    response_action: str = Field(..., description="opt_out, call_request, question, reschedule")
    auto_reply: Optional[str] = Field(None, description="Automatic reply if applicable")
    agent_handoff: Optional[str] = Field(None, description="Agent to handoff to")
    handoff_payload: Optional[dict] = Field(None, description="Data for handoff")
    update_conversation: bool = Field(default=True, description="Log in conversation")
```

**Response Processing:**
- Opt-out commands (STOP, UNSUBSCRIBE, etc.) → Mark as opted_out
- Call requests (CALL, PHONE, TALK) → Handoff to sales agent
- Questions → Route to appropriate agent based on keywords
- Scheduling (RESCHEDULE, BOOK, AVAILABLE) → Handoff to meeting scheduler
- Positive (YES, SURE, OK) → Create follow-up task
- Negative (NO, NOT INTERESTED) → Log and schedule nurture sequence

### Tool: log_sms_conversation
**Purpose**: Maintain comprehensive SMS conversation log for compliance

**Input Schema:**
```python
class LogConversationInput(BaseModel):
    lead_id: str = Field(..., description="Lead identifier")
    message_sid: str = Field(..., description="Twilio message ID")
    direction: str = Field(..., description="outbound, inbound")
    message_text: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    status: str = Field(..., description="sent, delivered, failed, received")
    consent_level: str = Field(..., description="Consent level at time of sending")
    trigger_event: Optional[str] = Field(None, description="Event that triggered message")
    metadata: dict = Field(default={}, description="Additional context")

class LogConversationOutput(BaseModel):
    log_id: str = Field(..., description="Conversation log ID")
    conversation_id: str = Field(..., description="Conversation thread ID")
    message_number: int = Field(..., description="Position in conversation")
    compliance_score: float = Field(..., description="Compliance check score")
    requires_review: bool = Field(default=False, description="Needs manual review")
```

## Database Schema

```sql
-- SMS consent tracking
CREATE TABLE sms_consent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    phone_number VARCHAR(20) NOT NULL,
    consent_level VARCHAR(20) NOT NULL CHECK (consent_level IN ('none', 'implied', 'explicit', 'opted_out')),
    consent_source VARCHAR(100),
    consent_date TIMESTAMP,
    last_opt_out TIMESTAMP,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(lead_id, phone_number)
);

-- SMS messages
CREATE TABLE sms_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_sid VARCHAR(50) NOT NULL UNIQUE,
    lead_id UUID NOT NULL REFERENCES leads(id),
    campaign_id UUID,
    phone_number VARCHAR(20) NOT NULL,
    message_text TEXT NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('outbound', 'inbound')),
    status VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    cost_cents INTEGER,
    error_code VARCHAR(20),
    error_message TEXT,
    trigger_event VARCHAR(50),
    consent_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- SMS conversation threads
CREATE TABLE sms_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    phone_number VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_message_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    opt_out_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Rate limiting
CREATE TABLE sms_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    date_sent DATE NOT NULL,
    hour_sent INTEGER NOT NULL CHECK (hour_sent >= 0 AND hour_sent <= 23),
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(lead_id, date_sent, hour_sent)
);

-- Indexes for performance
CREATE INDEX idx_sms_messages_lead_id ON sms_messages(lead_id);
CREATE INDEX idx_sms_messages_status ON sms_messages(status);
CREATE INDEX idx_sms_messages_created_at ON sms_messages(created_at);
CREATE INDEX idx_sms_consent_lead_id ON sms_consent(lead_id);
CREATE INDEX idx_sms_consent_phone ON sms_consent(phone_number);
CREATE INDEX idx_sms_rate_limits_date ON sms_rate_limits(date_sent);
```

## Configuration

```python
class SmsConfig:
    # Twilio settings
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # Compliance settings
    default_consent_level: str = "none"
    max_messages_per_hour: int = 1
    max_messages_per_day: int = 3
    business_hours_start: int = 9
    business_hours_end: int = 18
    consent_expiry_days: int = 180

    # Message settings
    max_message_length: int = 160
    retry_attempts: int = 3
    retry_backoff_seconds: list[int] = [60, 300, 900]

    # Rate limiting
    rate_limit_window_seconds: int = 3600
    rate_limit_burst: int = 10
    rate_limit sustained: int = 30
```

## Error Handling Matrix

| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Invalid phone | Validation error | Log error, notify lead agent | No |
| No consent | Consent check result | Log for email follow-up | No |
| Opted out | Consent level=opted_out | Block message, log opt-out | No |
| Rate limit | Message count check | Queue for later | Yes, after 1 hour |
| Twilio error 21610 | Invalid number API error | Mark number invalid | No |
| Twilio error 21612 | Undeliverable | Mark as invalid | No |
| Twilio 429 | Rate limit | Exponential backoff | Yes |
| Twilio 5xx | Server error | Retry with backoff | Yes, 3 attempts |
| Timeout | Request timeout | Retry with longer timeout | Yes, 2 attempts |
| Delivery failed | Webhook status=failed | Check reason, retry if needed | Conditional |

## Testing Strategy

### Unit Tests
```python
# sms_agent_test.py
class TestSmsAgent:
    def test_validate_phone_success(self):
        """Valid phone number validation"""

    def test_validate_phone_invalid(self):
        """Invalid phone number handling"""

    def test_check_consent_explicit(self):
        """Verify explicit consent allows sending"""

    def test_check_consent_opted_out(self):
        """Verify opted out blocks sending"""

    def test_generate_message_high_intent(self):
        """Generate high intent message"""

    def test_generate_message_no_show(self):
        """Generate no-show message"""

    def test_send_sms_success(self):
        """Successful SMS sending"""

    def test_send_sms_rate_limit(self):
        """Rate limiting enforcement"""

    def test_handle_opt_out(self):
        """Opt-out response handling"""

    def test_handle_call_request(self):
        """Call request handoff"""

    def test_conversation_logging(self):
        """Compliance logging"""
```

### Integration Tests
```python
# sms_agent_integration_test.py
class TestSmsIntegration:
    def test_end_to_end_sms_flow(self):
        """Complete SMS workflow"""

    def test_twilio_webhook_processing(self):
        """Webhook handling"""

    def test_multi_agent_handoff(self):
        """Agent coordination"""

    def test_consent_workflow(self):
        """Consent management"""
```

### Mocking Strategy
```python
@pytest.fixture
def mock_twilio():
    with patch('twilio.rest.Client') as mock:
        mock.return_value.messages.create.return_value = Mock(
            sid="SM_test123",
            status="queued",
            date_created=datetime.now()
        )
        yield mock

@pytest.fixture
def mock_phone_validation():
    with patch('src.integrations.twilio.TwilioClient.lookup') as mock:
        mock.return_value.phone_numbers.return_value.get.return_value = Mock(
            carrier={'type': 'mobile'},
            country_code='US'
        )
        yield mock
```

## Multi-Agent Integration

### Triggers from Other Agents
- **Lead List Builder**: New lead with phone number and high intent
- **Intent Signal Agent**: Intent score crosses threshold (70+)
- **Meeting Scheduler**: No-show event detected
- **Proposal Tracking**: Proposal expiring in 24 hours

### Handoffs to Other Agents
- **Sales Agent**: "CALL" requests, questions about services
- **Meeting Scheduler**: Reschedule requests, availability checks
- **Response Handler**: General questions, information requests
- **Campaign Agent**: Add to nurture sequence based on response

## Performance

### Expected Latency
- Phone validation: <200ms
- Consent check: <100ms
- Message generation: <500ms
- SMS sending: <2s (to Twilio)
- Response handling: <1s

### Throughput
- Max send rate: 10 SMS/second
- Parallel processing: 5 concurrent sends
- Queue depth: 1000 messages

### Monitoring
- Delivery success rate: >95%
- Opt-out rate: <2%
- Response rate: >15%
- Average delivery time: <30s

## Observability

### Logging
```python
logger.info("SMS sent", extra={
    "lead_id": lead_id,
    "message_sid": message_sid,
    "phone": sanitized_phone,
    "consent_level": consent_level,
    "trigger": trigger_event
})
```

### Metrics
- sms_messages_total{status, trigger_type}
- sms_delivery_seconds
- sms_consent_level_distribution
- sms_response_rate
- sms_opt_out_rate

### Alerts
- Delivery success rate <90% for 5 minutes
- Opt-out rate >5% in 1 hour
- Account balance low
- API error rate >1%

## Security

### Data Protection
- Phone numbers encrypted at rest
- Consent logs immutable
- Personal data deletion on request
- Audit trail for all compliance actions

### API Security
- Twilio credentials in secret manager
- Webhook signature verification
- Rate limiting per IP
- Request signing for outbound

### Compliance
- TCPA consent tracking
- Opt-out honoring within 5 seconds
- Business hours enforcement
- Message content filtering

## Acceptance Criteria

- [ ] All phone numbers validated before sending
- [ ] SMS consent verified for every message
- [ ] TCPA compliance fully implemented
- [ ] Opt-outs processed within 5 seconds
- [ ] Business hours enforced by recipient timezone
- [ ] Rate limiting prevents spam
- [ ] All messages logged for audit
- [ ] Delivery tracking implemented
- [ ] Response routing functional
- [ ] Agent handoffs working
- [ ] Webhook processing reliable
- [ ] Error handling complete
- [ ] Monitoring and alerting configured
- [ ] Unit tests >90% coverage
- [ ] Integration tests passing
- [ ] Load testing successful
