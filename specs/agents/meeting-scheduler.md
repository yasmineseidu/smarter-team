# Meeting Scheduler Agent - Production Specification

## Overview

**Agent Name:** `meeting_scheduler`

**Category:** Meeting Management

**Purpose:** Autonomously book, reschedule, and manage meetings through natural conversation using Cal.com API v2, handling the complete booking lifecycle from intent detection to confirmation.

**Priority:** Phase 1 - MVP Foundation

**Dependencies:**
- Response Handler Agent (detects meeting intent from inbound emails/messages)
- Cal.com API v2 integration
- Database: meetings, meeting_requests, available_slots tables
- Zep memory (for context about lead preferences, timezone, availability patterns)

---

## System Prompt

```
You are a professional meeting scheduler for Smarter Team, an AI agency. Your role is to make scheduling meetings effortless and delightful.

**Core Responsibilities:**
1. Detect meeting intent from natural language (e.g., "Let's schedule a call", "Can we talk?", "When are you free?")
2. Fetch available time slots from Cal.com and offer 3-5 options
3. Handle timezone conversions and present times in the lead's local timezone
4. Confirm bookings with clear, friendly language
5. Send calendar invites automatically after confirmation
6. Handle rescheduling and cancellations gracefully
7. Update lead status to MEETING_BOOKED in CRM after successful booking

**Tone & Style:**
- Professional but warm and conversational
- Concise - avoid lengthy explanations
- Always confirm timezone and lead's preferred time format (12h/24h)
- Use the lead's name when you have it
- Show excitement about the upcoming meeting

**Examples:**

User: "Let's schedule a call to discuss our project"
You: "I'd love to chat! I have availability at:
- Tuesday, Dec 10 at 2:00 PM EST
- Wednesday, Dec 11 at 10:00 AM EST
- Thursday, Dec 12 at 3:30 PM EST

Which works best for you?"

User: "Wednesday at 10 AM works"
You: "Perfect! You're confirmed for Wednesday, December 11 at 10:00 AM EST. I've sent a calendar invite to your email. Looking forward to our conversation!"

User: "Actually, can we push it to 2 PM instead?"
You: "Absolutely! I've rescheduled our meeting to Wednesday, December 11 at 2:00 PM EST. You'll receive an updated calendar invite shortly."

**Important Rules:**
- ALWAYS verify timezone before confirming
- NEVER book a slot without explicit confirmation from the lead
- If a requested time isn't available, offer 3 alternatives nearby
- For complex scheduling (multiple attendees, recurring meetings), escalate to human with context
- Track all booking attempts in database for analytics
```

---

## Agent Architecture

### Base Class
Extends `BaseAgent` from `src/agents/base_agent.py`

### File Structure
```
src/agents/meeting_scheduler/
├── __init__.py           # Export MeetingSchedulerAgent
├── agent.py              # Main agent class
├── tools.py              # Tool functions for Cal.com integration
├── prompts.py            # System prompt constants
├── schemas.py            # Pydantic models for requests/responses
└── exceptions.py         # Custom exceptions (SlotUnavailableError, etc.)
```

---

## Tools

### 1. `get_available_slots`

**Description:** Fetch available time slots from Cal.com API v2 for a specific event type.

**Parameters:**
```python
@dataclass
class GetAvailableSlotsParams:
    event_type_id: int           # Cal.com event type ID
    start_date: str              # ISO 8601 UTC start date (e.g., "2025-12-10T00:00:00Z")
    end_date: str                # ISO 8601 UTC end date
    timezone: str = "UTC"        # IANA timezone (e.g., "America/New_York")
    duration_minutes: int = 30   # Meeting duration
```

**Returns:**
```python
@dataclass
class AvailableSlot:
    start_time: str              # ISO 8601 UTC time
    end_time: str                # ISO 8601 UTC time
    start_time_local: str        # Formatted in lead's timezone
    end_time_local: str          # Formatted in lead's timezone

@dataclass
class GetAvailableSlotsResponse:
    slots: list[AvailableSlot]
    event_type_id: int
    timezone: str
```

**API Endpoint:** `GET /v2/slots/available`

**Query Parameters:**
- `startTime`: ISO 8601 UTC datetime string
- `endTime`: ISO 8601 UTC datetime string (optional, defaults to +7 days)
- `eventTypeId`: Cal.com event type ID
- `timeZone`: IANA timezone string

**Error Handling:**
- `CalComAPIError`: Cal.com API request failed (rate limit, network, auth)
- `NoSlotsAvailableError`: No slots found in requested timeframe
- `InvalidTimezoneError`: Invalid IANA timezone provided

**Implementation Notes:**
- Use `BaseIntegrationClient` for HTTP requests
- Cache slots for 5 minutes to reduce API calls
- Convert UTC times to lead's timezone using `pytz`
- Format times in a human-friendly way: "Tuesday, Dec 10 at 2:00 PM EST"

---

### 2. `create_booking`

**Description:** Create a booking in Cal.com API v2.

**Parameters:**
```python
@dataclass
class CreateBookingParams:
    event_type_id: int           # Cal.com event type ID
    start_time: str              # ISO 8601 UTC datetime
    attendee_name: str           # Lead's full name
    attendee_email: str          # Lead's email
    attendee_timezone: str       # IANA timezone
    notes: str = ""              # Optional booking notes/context
    metadata: dict[str, Any] | None = None  # Custom metadata (lead_id, source, etc.)
```

**Returns:**
```python
@dataclass
class CreateBookingResponse:
    booking_id: int              # Cal.com booking ID
    booking_uid: str             # Cal.com booking UID (unique identifier)
    start_time: str              # ISO 8601 UTC datetime
    end_time: str                # ISO 8601 UTC datetime
    attendee_name: str
    attendee_email: str
    status: str                  # "ACCEPTED" | "PENDING" | "CANCELLED"
    meeting_url: str             # Video meeting URL (if applicable)
```

**API Endpoint:** `POST /v2/bookings`

**Request Body:**
```json
{
  "eventTypeId": 123,
  "start": "2025-12-10T14:00:00Z",
  "attendee": {
    "name": "John Doe",
    "email": "john@example.com",
    "timeZone": "America/New_York"
  },
  "metadata": {
    "lead_id": "lead-123",
    "source": "cold_email",
    "agent": "meeting_scheduler"
  }
}
```

**Error Handling:**
- `BookingConflictError`: Slot no longer available (race condition)
- `InvalidEmailError`: Email validation failed
- `CalComAPIError`: General API failure
- `EventTypeNotFoundError`: Invalid event_type_id

**Implementation Notes:**
- Validate email format before sending
- Store booking_uid in database for webhook matching
- Send confirmation email via Response Handler Agent after successful booking
- Update lead status to `MEETING_BOOKED` in database
- Store booking in Zep memory for context in future conversations

---

### 3. `reschedule_booking`

**Description:** Reschedule an existing booking to a new time.

**Parameters:**
```python
@dataclass
class RescheduleBookingParams:
    booking_uid: str             # Cal.com booking UID
    new_start_time: str          # ISO 8601 UTC datetime
    rescheduling_reason: str = ""  # Optional reason for analytics
```

**Returns:**
```python
@dataclass
class RescheduleBookingResponse:
    booking_id: int
    booking_uid: str
    old_start_time: str          # Previous time
    new_start_time: str          # New time
    status: str                  # "ACCEPTED"
```

**API Endpoint:** `PATCH /v2/bookings/{bookingUid}`

**Request Body:**
```json
{
  "start": "2025-12-11T16:00:00Z",
  "reschedulingReason": "Lead requested different time"
}
```

**Error Handling:**
- `BookingNotFoundError`: Invalid booking_uid
- `BookingConflictError`: New time slot unavailable
- `BookingAlreadyCancelledError`: Cannot reschedule cancelled booking
- `CalComAPIError`: API failure

**Implementation Notes:**
- Verify booking exists in database before calling API
- Log rescheduling reason for analytics
- Send updated calendar invite via Response Handler
- Update booking record in database with new time
- Store reschedule event in Zep memory

---

### 4. `cancel_booking`

**Description:** Cancel an existing booking.

**Parameters:**
```python
@dataclass
class CancelBookingParams:
    booking_uid: str             # Cal.com booking UID
    cancellation_reason: str = ""  # Optional reason for analytics
    notify_attendee: bool = True  # Send cancellation email
```

**Returns:**
```python
@dataclass
class CancelBookingResponse:
    booking_id: int
    booking_uid: str
    status: str                  # "CANCELLED"
    cancelled_at: str            # ISO 8601 UTC datetime
```

**API Endpoint:** `DELETE /v2/bookings/{bookingUid}`

**Query Parameters:**
- `reason`: Cancellation reason
- `notifyAttendee`: Boolean (true/false)

**Error Handling:**
- `BookingNotFoundError`: Invalid booking_uid
- `BookingAlreadyCancelledError`: Booking already cancelled
- `CalComAPIError`: API failure

**Implementation Notes:**
- Update booking status to `CANCELLED` in database
- Log cancellation reason for churn analysis
- Send cancellation confirmation via Response Handler
- Store cancellation in Zep memory
- Do NOT delete booking record (keep for analytics)

---

### 5. `detect_timezone`

**Description:** Detect lead's timezone from email metadata, IP address, or past conversations.

**Parameters:**
```python
@dataclass
class DetectTimezoneParams:
    lead_id: str
    email_headers: dict[str, str] | None = None  # Email headers with timezone info
    ip_address: str | None = None                # IP for geolocation fallback
```

**Returns:**
```python
@dataclass
class DetectTimezoneResponse:
    timezone: str                # IANA timezone (e.g., "America/New_York")
    confidence: str              # "high" | "medium" | "low"
    source: str                  # "email_headers" | "ip_geolocation" | "memory" | "default"
```

**Implementation Notes:**
- Check Zep memory first for previously confirmed timezone
- Parse email headers for timezone hints
- Use IP geolocation as fallback (integrate with ipinfo.io or similar)
- Default to "America/New_York" (EST) if all else fails
- If confidence is "low", ask lead to confirm timezone explicitly
- Store confirmed timezone in Zep memory and database

---

### 6. `format_time_options`

**Description:** Format available slots into human-friendly time options.

**Parameters:**
```python
@dataclass
class FormatTimeOptionsParams:
    slots: list[AvailableSlot]
    timezone: str
    max_options: int = 5
    date_format: str = "%A, %B %d at %I:%M %p %Z"  # e.g., "Tuesday, Dec 10 at 2:00 PM EST"
```

**Returns:**
```python
@dataclass
class FormatTimeOptionsResponse:
    formatted_options: list[str]  # Human-readable time strings
    raw_slots: list[AvailableSlot]  # Original slot data for booking
```

**Implementation Notes:**
- Group slots by day if multiple options on same day
- Prioritize business hours (9 AM - 5 PM in lead's timezone)
- Spread options across different days when possible
- Use 12-hour format by default (with AM/PM)
- Include timezone abbreviation (EST, PST, etc.)

---

## Database Schema

### Table: `meetings`

Stores all meeting bookings (past, present, future).

```sql
CREATE TABLE meetings (
    id BIGSERIAL PRIMARY KEY,
    booking_uid VARCHAR(255) UNIQUE NOT NULL,        -- Cal.com booking UID
    booking_id INTEGER NOT NULL,                      -- Cal.com booking ID
    lead_id UUID NOT NULL REFERENCES leads(id),
    event_type_id INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    attendee_name VARCHAR(255) NOT NULL,
    attendee_email VARCHAR(255) NOT NULL,
    attendee_timezone VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,                     -- ACCEPTED, PENDING, CANCELLED, COMPLETED, NO_SHOW
    meeting_url TEXT,                                -- Video meeting link
    notes TEXT,                                      -- Booking notes
    metadata JSONB,                                  -- Custom metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,

    INDEX idx_lead_id (lead_id),
    INDEX idx_booking_uid (booking_uid),
    INDEX idx_start_time (start_time),
    INDEX idx_status (status)
);
```

### Table: `meeting_requests`

Tracks all meeting scheduling attempts (successful or failed).

```sql
CREATE TABLE meeting_requests (
    id BIGSERIAL PRIMARY KEY,
    lead_id UUID NOT NULL REFERENCES leads(id),
    request_type VARCHAR(50) NOT NULL,               -- BOOKING, RESCHEDULE, CANCELLATION
    status VARCHAR(50) NOT NULL,                     -- PENDING, COMPLETED, FAILED
    requested_time TIMESTAMP WITH TIME ZONE,
    timezone VARCHAR(100),
    context JSONB,                                   -- Conversation context, intent signals
    error_message TEXT,                              -- Error if failed
    booking_uid VARCHAR(255) REFERENCES meetings(booking_uid),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_lead_id (lead_id),
    INDEX idx_status (status),
    INDEX idx_request_type (request_type)
);
```

### Table: `available_slots` (Cache)

Caches Cal.com available slots to reduce API calls.

```sql
CREATE TABLE available_slots (
    id BIGSERIAL PRIMARY KEY,
    event_type_id INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(100) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,    -- 5 minutes after cached_at

    INDEX idx_event_type_expires (event_type_id, expires_at),
    INDEX idx_start_time (start_time)
);
```

---

## Webhooks

### Webhook Endpoint

`POST /webhooks/calcom`

**Authentication:** HMAC signature verification using `CALCOM_WEBHOOK_SECRET`

### Event Types

Cal.com sends webhooks for the following booking events:

1. **BOOKING_CREATED**
   - Triggered when a new booking is created
   - Update meeting status to `ACCEPTED`
   - Send confirmation email via Response Handler
   - Update lead status to `MEETING_BOOKED`

2. **BOOKING_RESCHEDULED**
   - Triggered when a booking is rescheduled
   - Update meeting record with new start/end times
   - Send updated calendar invite
   - Log rescheduling event for analytics

3. **BOOKING_CANCELLED**
   - Triggered when a booking is cancelled
   - Update meeting status to `CANCELLED`
   - Send cancellation confirmation
   - Update lead status (if no other active meetings)

4. **BOOKING_NO_SHOW_UPDATED**
   - Triggered when host/attendee marks no-show
   - Update meeting status to `NO_SHOW`
   - Handoff to No-Show Handler Agent
   - Log no-show for lead scoring

5. **MEETING_ENDED**
   - Triggered when meeting ends (if Cal Video used)
   - Update meeting status to `COMPLETED`
   - Handoff to Transcript Processing Agent (if recording exists)

### Webhook Payload Structure

```json
{
  "triggerEvent": "BOOKING_CREATED",
  "createdAt": "2025-12-05T14:30:00Z",
  "payload": {
    "uid": "booking-uid-123",
    "id": 12345,
    "title": "Discovery Call",
    "startTime": "2025-12-10T14:00:00Z",
    "endTime": "2025-12-10T14:30:00Z",
    "attendees": [
      {
        "email": "john@example.com",
        "name": "John Doe",
        "timeZone": "America/New_York"
      }
    ],
    "organizer": {
      "email": "team@smarterteam.ai",
      "name": "Smarter Team"
    },
    "metadata": {
      "lead_id": "lead-123",
      "source": "cold_email"
    }
  }
}
```

### Webhook Handler Implementation

```python
# src/webhooks/calcom_webhook.py

from fastapi import APIRouter, Request, HTTPException, Header
from src.agents.meeting_scheduler.schemas import WebhookPayload
from src.config import settings
import hmac
import hashlib

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/calcom")
async def handle_calcom_webhook(
    request: Request,
    x_cal_signature: str = Header(None)
):
    """Handle incoming Cal.com webhooks."""
    body = await request.body()

    # Verify webhook signature
    if not verify_signature(body, x_cal_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event_type = payload.get("triggerEvent")

    # Route to appropriate handler
    if event_type == "BOOKING_CREATED":
        await handle_booking_created(payload)
    elif event_type == "BOOKING_RESCHEDULED":
        await handle_booking_rescheduled(payload)
    elif event_type == "BOOKING_CANCELLED":
        await handle_booking_cancelled(payload)
    elif event_type == "BOOKING_NO_SHOW_UPDATED":
        await handle_no_show(payload)
    elif event_type == "MEETING_ENDED":
        await handle_meeting_ended(payload)

    return {"status": "received"}

def verify_signature(body: bytes, signature: str) -> bool:
    """Verify HMAC signature from Cal.com."""
    expected = hmac.new(
        settings.CALCOM_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## Error Handling Strategy

### Error Categories

1. **API Errors (CalComAPIError)**
   - Rate limiting: Retry with exponential backoff (max 3 retries)
   - Network errors: Retry after 5 seconds
   - Authentication errors: Alert ops team, do NOT retry
   - Log all API errors with full request/response for debugging

2. **Validation Errors**
   - Invalid email: Return friendly error, ask lead to confirm email
   - Invalid timezone: Default to EST, ask lead to confirm
   - Invalid date: Suggest nearest available slots

3. **Business Logic Errors**
   - Slot unavailable: Offer 3 alternative times
   - Booking conflict: Explain conflict, offer alternatives
   - No slots available: Escalate to human with context

4. **Webhook Errors**
   - Invalid signature: Log warning, return 401
   - Duplicate webhook: Check idempotency, skip if already processed
   - Unknown event type: Log warning, return 200 (acknowledge receipt)

### Escalation Rules

Escalate to human when:
- Lead requests > 3 reschedules in 7 days (potential issue)
- Complex scheduling (multiple attendees, recurring meetings)
- Custom requests not supported by Cal.com API
- Lead expresses frustration or confusion
- Booking fails 3+ times (technical issue)

### Retry Logic

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(CalComRateLimitError),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def create_booking_with_retry(params: CreateBookingParams):
    """Create booking with automatic retry on rate limit."""
    return await cal_client.create_booking(params)
```

---

## Cal.com API Integration

### Client Implementation

```python
# src/integrations/calcom.py

from src.integrations.base import BaseIntegrationClient
from src.config import settings

class CalComClient(BaseIntegrationClient):
    """Cal.com API v2 client."""

    def __init__(self):
        super().__init__(
            name="calcom",
            base_url="https://api.cal.com/v2",
            api_key=settings.CAL_COM_API_KEY,
            timeout=30.0
        )

    async def get_available_slots(
        self,
        event_type_id: int,
        start_time: str,
        end_time: str | None = None,
        timezone: str = "UTC"
    ) -> dict:
        """Fetch available slots."""
        params = {
            "eventTypeId": event_type_id,
            "startTime": start_time,
            "timeZone": timezone
        }
        if end_time:
            params["endTime"] = end_time

        return await self.get("/slots/available", params=params)

    async def create_booking(
        self,
        event_type_id: int,
        start: str,
        attendee: dict,
        metadata: dict | None = None
    ) -> dict:
        """Create a new booking."""
        payload = {
            "eventTypeId": event_type_id,
            "start": start,
            "attendee": attendee,
            "metadata": metadata or {}
        }
        return await self.post("/bookings", json=payload)

    async def reschedule_booking(
        self,
        booking_uid: str,
        new_start: str,
        reason: str = ""
    ) -> dict:
        """Reschedule an existing booking."""
        payload = {"start": new_start}
        if reason:
            payload["reschedulingReason"] = reason

        return await self.patch(f"/bookings/{booking_uid}", json=payload)

    async def cancel_booking(
        self,
        booking_uid: str,
        reason: str = "",
        notify: bool = True
    ) -> dict:
        """Cancel a booking."""
        params = {
            "reason": reason,
            "notifyAttendee": str(notify).lower()
        }
        return await self.delete(f"/bookings/{booking_uid}", params=params)
```

---

## Conversational Booking Flow

### Flow Diagram

```
1. Intent Detection
   ↓
2. Context Gathering (timezone, preferences from memory)
   ↓
3. Fetch Available Slots (Cal.com API)
   ↓
4. Format & Present Options (3-5 times)
   ↓
5. Receive Confirmation
   ↓
6. Create Booking (Cal.com API)
   ↓
7. Send Confirmation Email
   ↓
8. Update Lead Status (MEETING_BOOKED)
   ↓
9. Store in Memory (for future context)
```

### Example Conversation

```
Lead: "Can we schedule a discovery call?"

Agent: "Absolutely! I'd love to discuss how we can help. I have these times available this week:
- Tuesday, Dec 10 at 2:00 PM EST
- Wednesday, Dec 11 at 10:30 AM EST
- Thursday, Dec 12 at 3:00 PM EST

Which works best for you? (I'm in EST - let me know if you're in a different timezone)"

Lead: "Thursday at 3 PM works. I'm in PST btw"

Agent: "Perfect! Just to confirm - that's Thursday, December 12 at 3:00 PM PST (6:00 PM EST). You're all set! I've sent a calendar invite to john@example.com. Looking forward to our conversation!"

Lead: "Actually, can we do 1 PM PST instead?"

Agent: "Of course! I've updated our meeting to Thursday, December 12 at 1:00 PM PST (4:00 PM EST). You'll receive an updated calendar invite shortly."
```

### Edge Cases

1. **No slots available in requested timeframe**
   - Offer slots in next available week
   - Ask if lead has specific time preferences

2. **Lead doesn't confirm timezone**
   - Use detected timezone from email/IP
   - Confirm timezone in booking confirmation

3. **Ambiguous time reference**
   - "Tomorrow at 2" → Clarify AM/PM and timezone
   - "Next week" → Offer specific dates

4. **Multiple meeting requests**
   - Ask lead to specify which topic/service
   - Offer different event types if applicable

5. **Booking fails (race condition)**
   - Apologize, explain slot just got booked
   - Immediately offer 3 nearest alternatives

---

## Testing Requirements

### Unit Tests (Coverage > 90%)

1. **Tool Functions**
   - `test_get_available_slots_success`
   - `test_get_available_slots_no_slots`
   - `test_get_available_slots_invalid_timezone`
   - `test_create_booking_success`
   - `test_create_booking_conflict`
   - `test_create_booking_invalid_email`
   - `test_reschedule_booking_success`
   - `test_reschedule_booking_not_found`
   - `test_cancel_booking_success`
   - `test_cancel_booking_already_cancelled`
   - `test_detect_timezone_from_memory`
   - `test_detect_timezone_from_email_headers`
   - `test_detect_timezone_from_ip`
   - `test_format_time_options_business_hours`
   - `test_format_time_options_max_limit`

2. **Agent Logic**
   - `test_agent_initialization`
   - `test_agent_system_prompt`
   - `test_process_booking_request`
   - `test_process_rescheduling_request`
   - `test_process_cancellation_request`
   - `test_handoff_to_no_show_handler`

3. **Cal.com Client**
   - `test_calcom_client_authentication`
   - `test_calcom_client_rate_limiting`
   - `test_calcom_client_error_handling`
   - `test_calcom_client_retry_logic`

### Integration Tests (Coverage > 85%)

1. **End-to-End Booking Flow**
   - `test_complete_booking_flow`
   - `test_booking_with_timezone_conversion`
   - `test_booking_with_memory_context`

2. **Webhook Handling**
   - `test_webhook_signature_verification`
   - `test_handle_booking_created_webhook`
   - `test_handle_booking_rescheduled_webhook`
   - `test_handle_booking_cancelled_webhook`
   - `test_handle_no_show_webhook`
   - `test_webhook_idempotency`

3. **Database Operations**
   - `test_create_meeting_record`
   - `test_update_meeting_status`
   - `test_query_upcoming_meetings`
   - `test_cache_available_slots`

4. **Agent Handoffs**
   - `test_handoff_to_response_handler`
   - `test_handoff_to_no_show_handler`
   - `test_handoff_to_transcript_processor`

### Mock Data Fixtures

```python
# __tests__/fixtures/meeting_scheduler_fixtures.py

@pytest.fixture
def mock_cal_slots():
    """Mock Cal.com available slots response."""
    return {
        "slots": [
            {
                "time": "2025-12-10T14:00:00Z",
                "bookingUid": None
            },
            {
                "time": "2025-12-11T15:00:00Z",
                "bookingUid": None
            },
            {
                "time": "2025-12-12T16:00:00Z",
                "bookingUid": None
            }
        ]
    }

@pytest.fixture
def mock_cal_booking_response():
    """Mock Cal.com booking creation response."""
    return {
        "id": 12345,
        "uid": "booking-uid-123",
        "title": "Discovery Call",
        "startTime": "2025-12-10T14:00:00Z",
        "endTime": "2025-12-10T14:30:00Z",
        "status": "ACCEPTED",
        "attendees": [
            {
                "email": "john@example.com",
                "name": "John Doe",
                "timeZone": "America/New_York"
            }
        ]
    }

@pytest.fixture
def mock_webhook_payload():
    """Mock Cal.com webhook payload."""
    return {
        "triggerEvent": "BOOKING_CREATED",
        "createdAt": "2025-12-05T14:30:00Z",
        "payload": {
            "uid": "booking-uid-123",
            "id": 12345,
            "startTime": "2025-12-10T14:00:00Z",
            "endTime": "2025-12-10T14:30:00Z",
            "attendees": [{"email": "john@example.com", "name": "John Doe"}],
            "metadata": {"lead_id": "lead-123"}
        }
    }
```

---

## Performance & Scalability

### Caching Strategy
- Cache available slots for 5 minutes (reduce API calls)
- Use Redis for distributed caching across workers
- Invalidate cache when booking is created in that timeframe

### Rate Limiting
- Cal.com API rate limit: 100 requests/minute
- Implement token bucket algorithm in client
- Queue booking requests during high traffic
- Monitor rate limit headers and back off proactively

### Database Indexing
- Index on `lead_id`, `booking_uid`, `start_time`, `status`
- Use partial index on `status IN ('ACCEPTED', 'PENDING')` for active meetings
- Archive completed/cancelled meetings older than 6 months

### Monitoring
- Track booking success rate (target: > 98%)
- Monitor average booking flow completion time (target: < 30 seconds)
- Alert on webhook processing delays (> 10 seconds)
- Track reschedule/cancellation rates for analytics

---

## Security Considerations

1. **Webhook Authentication**
   - Verify HMAC signature on all incoming webhooks
   - Use constant-time comparison to prevent timing attacks
   - Reject unsigned webhooks immediately

2. **Data Privacy**
   - Store only necessary attendee information
   - Encrypt sensitive data at rest (emails, names)
   - Comply with GDPR/CCPA for data deletion requests

3. **Rate Limiting**
   - Prevent abuse by limiting bookings per lead (max 5 pending)
   - Implement CAPTCHA for public booking endpoints

4. **Input Validation**
   - Sanitize all user inputs (names, emails, notes)
   - Validate email format before API calls
   - Prevent SQL injection in database queries

---

## Implementation Checklist

### Phase 1: Core Booking (Week 1)
- [ ] Create agent file structure (`agent.py`, `tools.py`, `schemas.py`, etc.)
- [ ] Implement `CalComClient` integration
- [ ] Implement `get_available_slots` tool
- [ ] Implement `create_booking` tool
- [ ] Implement timezone detection
- [ ] Create database migrations (meetings, meeting_requests, available_slots)
- [ ] Write unit tests for tools (>90% coverage)
- [ ] Write integration tests for Cal.com client

### Phase 2: Rescheduling & Cancellation (Week 2)
- [ ] Implement `reschedule_booking` tool
- [ ] Implement `cancel_booking` tool
- [ ] Add rescheduling flow to agent
- [ ] Add cancellation flow to agent
- [ ] Write tests for reschedule/cancel flows
- [ ] Implement retry logic with exponential backoff

### Phase 3: Webhooks (Week 2)
- [ ] Create webhook endpoint (`/webhooks/calcom`)
- [ ] Implement signature verification
- [ ] Implement BOOKING_CREATED handler
- [ ] Implement BOOKING_RESCHEDULED handler
- [ ] Implement BOOKING_CANCELLED handler
- [ ] Implement BOOKING_NO_SHOW_UPDATED handler
- [ ] Implement MEETING_ENDED handler
- [ ] Write webhook integration tests
- [ ] Test webhook idempotency

### Phase 4: Conversational Intelligence (Week 3)
- [ ] Integrate Zep memory for context
- [ ] Implement timezone persistence in memory
- [ ] Add preference tracking (time of day, meeting duration)
- [ ] Implement `format_time_options` with smart defaults
- [ ] Add multi-turn conversation support
- [ ] Test complete booking conversation flow

### Phase 5: Error Handling & Edge Cases (Week 3)
- [ ] Implement all custom exceptions
- [ ] Add comprehensive error messages
- [ ] Implement escalation to human logic
- [ ] Add fallback responses for API failures
- [ ] Test all edge cases (no slots, conflicts, etc.)
- [ ] Add logging for all critical paths

### Phase 6: Optimization & Monitoring (Week 4)
- [ ] Implement slot caching with Redis
- [ ] Add rate limiting to Cal.com client
- [ ] Optimize database queries with indexes
- [ ] Add performance monitoring (datadog/sentry)
- [ ] Add success/failure rate tracking
- [ ] Load test booking flow (100 concurrent bookings)

### Phase 7: Production Readiness (Week 4)
- [ ] Code review by senior engineer
- [ ] Security audit (webhook signatures, input validation)
- [ ] Update documentation
- [ ] Create runbook for common issues
- [ ] Deploy to staging environment
- [ ] End-to-end testing in staging
- [ ] Deploy to production
- [ ] Monitor for 48 hours post-deployment

---

## Success Metrics

- **Booking Success Rate:** > 98% (bookings created successfully)
- **Average Booking Time:** < 30 seconds (from intent to confirmation)
- **Reschedule Rate:** < 10% (indicates good initial scheduling)
- **Cancellation Rate:** < 5%
- **No-Show Rate:** < 8% (industry standard is 10-15%)
- **Lead Satisfaction:** > 4.5/5 (measured via post-meeting survey)
- **API Uptime:** > 99.9% (Cal.com dependency)
- **Webhook Processing Time:** < 5 seconds (99th percentile)

---

## References

### Cal.com API Documentation
- [Create a booking](https://cal.com/docs/api-reference/v2/bookings/create-a-booking)
- [Get available slots](https://cal.com/docs/api-reference/v2/slots/get-available-slots)
- [Webhooks documentation](https://cal.com/docs/core-features/webhooks)

### Internal Documentation
- BaseAgent implementation: `app/backend/src/agents/base_agent.py`
- BaseIntegrationClient: `app/backend/src/integrations/base.py`
- Project conventions: `.project/CONVENTIONS.md`
- Testing patterns: `app/backend/__tests__/`

---

**Last Updated:** 2025-12-05
**Spec Version:** 1.0.0
**Status:** Ready for Implementation
