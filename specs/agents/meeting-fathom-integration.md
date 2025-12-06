# Meeting Fathom Integration Agent - Production Specification

## Overview

**Agent Name:** `meeting_fathom_integration`

**Category:** Meeting Management

**Purpose:** Automatically capture, process, and route call recordings and transcripts from Fathom after meetings end. Serves as the bridge between Fathom's recording platform and the Smarter Team intelligence pipeline, ensuring every sales conversation is captured, stored, and analyzed for actionable insights.

**Priority:** Phase 1 - MVP Foundation

**Dependencies:**
- **Meeting Scheduler Agent** - Provides meeting metadata (lead_id, meeting_id, type)
- **Proposal Transcript Processor Agent** - Receives transcripts for insight extraction
- **Meeting Prep Agent** - Provides talking points used during call (for comparison)
- **Zep Memory Integration** - Stores conversation context for long-term learning
- **Fathom API** - Webhook source and API for fetching recordings/transcripts
- **Cal.com** - MEETING_ENDED webhook trigger

---

## System Prompt

```
You are the Meeting Fathom Integration Agent for Smarter Team, an AI agency automation platform.

Your role is to seamlessly capture and route call recordings and transcripts from Fathom, ensuring no sales conversation goes unanalyzed.

**Core Responsibilities:**
1. Receive and validate Fathom webhooks for recording_ready events
2. Fetch complete transcript data with speaker labels and timestamps
3. Match recordings to existing meetings using Cal.com event IDs
4. Store raw transcripts and metadata in the database
5. Handoff transcripts to Proposal Transcript Processor for analysis
6. Archive conversation context in Zep memory for future reference
7. Track recording quality metrics and flag issues

**Data Quality Standards:**
- Validate transcript completeness (minimum 30 seconds duration)
- Ensure speaker labels are present (minimum 2 speakers for sales calls)
- Verify timestamp accuracy (no gaps > 30 seconds)
- Check audio quality indicators from Fathom
- Flag low-confidence transcripts for manual review

**Error Handling:**
- If meeting matching fails, create orphaned transcript record for manual review
- If Fathom API returns incomplete data, retry up to 3 times with exponential backoff
- If transcript is empty or corrupted, log error and notify ops team
- Never block webhook processing - queue failures for async retry

**Integration Flow:**
1. Receive webhook → Validate signature → Store raw payload
2. Fetch full transcript from Fathom API
3. Match to meeting record (via fathom_recording_id or Cal.com event)
4. Enrich with meeting metadata (lead, campaign, prep notes)
5. Store in call_transcripts table
6. Handoff to Transcript Processor (high priority)
7. Store summary in Zep memory

**Tone & Style:**
- Reliable and deterministic (no guesswork on matching)
- Defensive programming (assume external APIs can fail)
- Comprehensive logging (track every step for debugging)
- Performance-focused (process webhooks in <5 seconds)

**Important Rules:**
- ALWAYS validate Fathom webhook signatures (security critical)
- NEVER skip storing raw webhook payload (audit trail)
- NEVER assume meeting exists - verify before linking
- ALWAYS handoff to Transcript Processor even if meeting not found (insights still valuable)
- Track processing latency and alert if p95 > 10 seconds
```

---

## Agent Architecture

### Base Class
Extends `BaseAgent` from `src/agents/base_agent.py`

### File Structure
```
src/agents/meeting_fathom_integration/
├── __init__.py           # Export MeetingFathomIntegrationAgent
├── agent.py              # Main agent class
├── tools.py              # Tool functions for Fathom API
├── prompts.py            # System prompt constants
├── schemas.py            # Pydantic models for webhooks/API
└── exceptions.py         # Custom exceptions (FathomAPIError, etc.)
```

---

## Tools

### 1. `validate_fathom_webhook`

**Description:** Verify webhook signature to ensure request is from Fathom.

**Parameters:**
```python
@dataclass
class ValidateFathomWebhookParams:
    payload: dict[str, Any]        # Raw webhook payload
    signature: str                 # X-Fathom-Signature header
    timestamp: str                 # X-Fathom-Timestamp header
```

**Returns:**
```python
@dataclass
class ValidateFathomWebhookResponse:
    valid: bool
    error_reason: str | None = None
```

**Implementation Notes:**
- Use HMAC-SHA256 with `FATHOM_WEBHOOK_SECRET` from environment
- Reject webhooks older than 5 minutes (replay attack prevention)
- Compare signatures using constant-time comparison (`hmac.compare_digest`)
- Log all validation failures with full headers for security audit

**Error Handling:**
- Raises `InvalidWebhookSignatureError` if signature doesn't match
- Raises `WebhookTimestampExpiredError` if timestamp > 5 minutes old
- Returns `valid=False` with reason for non-critical failures

---

### 2. `fetch_fathom_transcript`

**Description:** Fetch complete transcript data from Fathom API.

**Parameters:**
```python
@dataclass
class FetchFathomTranscriptParams:
    recording_id: str              # Fathom recording ID
    include_video_url: bool = True # Include video download URL
    include_metadata: bool = True  # Include participant metadata
```

**Returns:**
```python
@dataclass
class FathomTranscript:
    recording_id: str
    transcript_text: str           # Full plaintext transcript
    transcript_json: dict          # Structured with timestamps/speakers
    participants: list[dict]       # [{"name": str, "email": str, "duration": int}]
    duration_seconds: int
    recorded_at: str               # ISO 8601 datetime
    video_url: str | None
    share_url: str | None
    audio_quality_score: float     # 0.0-1.0
    transcript_confidence: float   # 0.0-1.0
    speaker_count: int
    metadata: dict[str, Any]
```

**API Endpoint:** `GET /v1/recordings/{recording_id}/transcript`

**Authentication:** `Bearer {FATHOM_API_KEY}` header

**Error Handling:**
- `FathomAPIError`: API request failed (rate limit, network, auth)
- `TranscriptNotReadyError`: Recording still processing (retry after delay)
- `RecordingNotFoundError`: Invalid recording_id
- `TranscriptEmptyError`: Transcript returned but empty (flag for review)

**Implementation Notes:**
- Use `BaseIntegrationClient` for HTTP requests
- Retry on 429 (rate limit) with exponential backoff
- Validate transcript has minimum 30 seconds content
- Parse speaker labels and timestamps from JSON format
- Store both plaintext and structured JSON versions

---

### 3. `match_meeting_to_transcript`

**Description:** Link Fathom recording to existing meeting record in database.

**Parameters:**
```python
@dataclass
class MatchMeetingParams:
    fathom_recording_id: str
    cal_event_id: str | None = None      # From meeting metadata
    scheduled_at: str | None = None       # ISO 8601 datetime
    participant_emails: list[str] = []    # Match by attendees
```

**Returns:**
```python
@dataclass
class MatchMeetingResponse:
    meeting_id: str | None         # UUID if match found
    lead_id: str | None            # Associated lead
    campaign_id: str | None        # Associated campaign
    confidence: str                # "high" | "medium" | "low" | "no_match"
    match_method: str              # "cal_event_id" | "timestamp_participant" | "participant_only" | "none"
```

**Matching Logic (Priority Order):**
1. **Exact Cal.com Event ID match** (confidence: high)
   - Query `meetings` table where `cal_event_id = {cal_event_id}`
2. **Timestamp + Participant Email match** (confidence: medium)
   - Query meetings within ±15 minutes of `scheduled_at`
   - Match participant emails with lead email
3. **Participant Email only** (confidence: low)
   - Match lead by email from participants
   - Return most recent scheduled meeting for that lead
4. **No match** (confidence: no_match)
   - Create orphaned transcript record for manual review
   - Log for ops team follow-up

**Error Handling:**
- Returns `meeting_id=None` if no match found (not an error)
- Logs warning if confidence is "low" or "no_match"
- Creates alert if >20% of transcripts have "no_match" (data quality issue)

---

### 4. `store_transcript`

**Description:** Save transcript and metadata to `call_transcripts` table.

**Parameters:**
```python
@dataclass
class StoreTranscriptParams:
    fathom_recording_id: str
    transcript_text: str
    transcript_json: dict
    participants: list[dict]
    duration_seconds: int
    recorded_at: str
    video_url: str | None
    share_url: str | None
    meeting_id: str | None         # Can be None if no match
    lead_id: str | None
    raw_webhook_payload: dict
```

**Returns:**
```python
@dataclass
class StoreTranscriptResponse:
    transcript_id: str             # UUID of created record
    created_at: str
```

**Database Schema:**
```sql
CREATE TABLE call_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fathom_recording_id VARCHAR(255) UNIQUE NOT NULL,
    lead_id UUID REFERENCES leads(id),
    meeting_id UUID REFERENCES meetings(id),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds INTEGER NOT NULL,
    transcript_text TEXT NOT NULL,
    transcript_json JSONB NOT NULL,
    participants JSONB NOT NULL,
    fathom_video_url TEXT,
    fathom_share_url TEXT,
    audio_quality_score DECIMAL(3,2),
    transcript_confidence DECIMAL(3,2),
    speaker_count INTEGER,
    raw_webhook_payload JSONB NOT NULL,
    matched_to_meeting BOOLEAN DEFAULT FALSE,
    match_confidence VARCHAR(20),
    match_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_call_transcripts_fathom_id (fathom_recording_id),
    INDEX idx_call_transcripts_meeting_id (meeting_id),
    INDEX idx_call_transcripts_lead_id (lead_id),
    INDEX idx_call_transcripts_recorded_at (recorded_at DESC)
);
```

**Implementation Notes:**
- Store raw webhook payload for audit trail
- Set `matched_to_meeting = TRUE` if meeting_id is not None
- Record `match_confidence` and `match_method` for analytics
- Update `meetings.fathom_recording_id` if match found (bidirectional link)

---

### 5. `store_in_zep_memory`

**Description:** Archive conversation summary in Zep for long-term context.

**Parameters:**
```python
@dataclass
class StoreInZepParams:
    lead_id: str                   # Zep user ID
    transcript_text: str
    meeting_id: str
    meeting_type: str              # "discovery", "demo", "closing"
    participants: list[str]        # Participant names
    key_topics: list[str]          # Extracted by Claude (preview)
```

**Returns:**
```python
@dataclass
class StoreInZepResponse:
    memory_id: str                 # Zep memory ID
    stored_at: str
```

**Zep Integration Notes:**
- Use Zep `add_memory` API with `user_id = lead_id`
- Session ID: `meeting-{meeting_id}`
- Memory type: `conversation`
- Metadata: `{"source": "fathom", "meeting_type": "...", "duration": ...}`
- Extract 3-5 key topics using Claude (lightweight prompt)
- Store full transcript as memory content

**Error Handling:**
- Non-blocking: If Zep fails, log error but continue processing
- Retry once on timeout
- Alert ops if >5% of Zep stores fail

---

### 6. `handoff_to_transcript_processor`

**Description:** Trigger Proposal Transcript Processor agent to analyze transcript.

**Parameters:**
```python
@dataclass
class HandoffToProcessorParams:
    transcript_id: str
    lead_id: str | None
    meeting_id: str | None
    transcript_text: str
    priority: str = "high"         # Always high priority for transcripts
```

**Returns:**
```python
@dataclass
class HandoffResponse:
    task_id: str                   # Celery task ID
    agent: str                     # "proposal_transcript_processor"
```

**Implementation:**
Uses `BaseAgent.handoff_to()` method:
```python
task_id = await self.handoff_to(
    target_agent="proposal_transcript_processor",
    payload={
        "type": "process_transcript",
        "transcript_id": transcript_id,
        "transcript_text": transcript_text,
        "lead_id": lead_id,
        "meeting_id": meeting_id,
    },
    priority="high"
)
```

**Error Handling:**
- If handoff fails, queue transcript for manual processing
- Log failure with full context
- Alert if handoff failure rate > 2%

---

### 7. `update_meeting_record`

**Description:** Update `meetings` table with Fathom recording details.

**Parameters:**
```python
@dataclass
class UpdateMeetingParams:
    meeting_id: str
    fathom_recording_id: str
    recording_url: str
    transcript_text: str
    duration_seconds: int
```

**Returns:**
```python
@dataclass
class UpdateMeetingResponse:
    updated: bool
    meeting_id: str
```

**Database Update:**
```sql
UPDATE meetings
SET
    fathom_recording_id = '{fathom_recording_id}',
    recording_url = '{recording_url}',
    transcript = '{transcript_text}',
    duration_minutes = {duration_seconds} / 60,
    status = CASE WHEN status = 'scheduled' THEN 'completed' ELSE status END,
    updated_at = NOW()
WHERE id = '{meeting_id}';
```

**Implementation Notes:**
- Update meeting status to 'completed' if still 'scheduled'
- Store recording_url for easy access
- Truncate transcript if > 50,000 characters (store full version in call_transcripts)
- Trigger `meeting_completed` webhook for downstream agents

---

### 8. `check_transcript_quality`

**Description:** Validate transcript quality and flag issues.

**Parameters:**
```python
@dataclass
class CheckQualityParams:
    transcript_text: str
    transcript_json: dict
    duration_seconds: int
    speaker_count: int
    audio_quality_score: float
    transcript_confidence: float
```

**Returns:**
```python
@dataclass
class QualityCheckResponse:
    quality_score: float           # 0.0-1.0 overall quality
    issues: list[str]              # ["low_audio_quality", "missing_speakers", ...]
    needs_manual_review: bool
    review_reason: str | None
```

**Quality Criteria:**
1. **Minimum Duration**: >= 30 seconds (flag if shorter)
2. **Speaker Labels**: >= 2 speakers for sales calls (flag if 1 or 0)
3. **Audio Quality**: >= 0.7 (flag if < 0.7)
4. **Transcript Confidence**: >= 0.8 (flag if < 0.8)
5. **Timestamp Gaps**: No gaps > 30 seconds (flag if found)
6. **Empty Sections**: No empty speaker turns > 10% of transcript

**Manual Review Triggers:**
- quality_score < 0.6
- duration_seconds < 30
- speaker_count < 2 and meeting_type = "discovery"
- audio_quality_score < 0.5
- transcript_confidence < 0.7

**Implementation Notes:**
- Calculate quality_score as weighted average:
  - audio_quality: 30%
  - transcript_confidence: 40%
  - speaker_labeling: 20%
  - duration_completeness: 10%
- Log all flagged issues for monitoring
- Create task in ClickUp if `needs_manual_review = True`

---

## Database Schema

### Table: `call_transcripts`

Complete table definition (extends Tool #4):

```sql
CREATE TABLE call_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fathom_recording_id VARCHAR(255) UNIQUE NOT NULL,
    lead_id UUID REFERENCES leads(id),
    meeting_id UUID REFERENCES meetings(id),

    -- Recording Details
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds INTEGER NOT NULL,
    speaker_count INTEGER,

    -- Transcript Content
    transcript_text TEXT NOT NULL,
    transcript_json JSONB NOT NULL,         -- Structured with timestamps/speakers
    participants JSONB NOT NULL,            -- [{"name": "...", "email": "...", "duration": ...}]

    -- Fathom Links
    fathom_video_url TEXT,
    fathom_share_url TEXT,

    -- Quality Metrics
    audio_quality_score DECIMAL(3,2),
    transcript_confidence DECIMAL(3,2),
    quality_score DECIMAL(3,2),
    quality_issues TEXT[] DEFAULT '{}',
    needs_manual_review BOOLEAN DEFAULT FALSE,
    review_reason TEXT,

    -- Matching Metadata
    matched_to_meeting BOOLEAN DEFAULT FALSE,
    match_confidence VARCHAR(20),           -- "high", "medium", "low", "no_match"
    match_method VARCHAR(50),               -- "cal_event_id", "timestamp_participant", etc.

    -- Processing Status
    processor_handoff_task_id VARCHAR(100), -- Celery task ID
    processor_handoff_at TIMESTAMP WITH TIME ZONE,
    zep_memory_id VARCHAR(100),
    zep_stored_at TIMESTAMP WITH TIME ZONE,

    -- Audit Trail
    raw_webhook_payload JSONB NOT NULL,
    webhook_received_at TIMESTAMP WITH TIME ZONE,
    processing_duration_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_call_transcripts_fathom_id (fathom_recording_id),
    INDEX idx_call_transcripts_meeting_id (meeting_id),
    INDEX idx_call_transcripts_lead_id (lead_id),
    INDEX idx_call_transcripts_recorded_at (recorded_at DESC),
    INDEX idx_call_transcripts_quality (quality_score DESC) WHERE needs_manual_review = TRUE,
    INDEX idx_call_transcripts_unmatched (matched_to_meeting) WHERE matched_to_meeting = FALSE
);

-- Trigger for updated_at
CREATE TRIGGER update_call_transcripts_updated_at
    BEFORE UPDATE ON call_transcripts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Updates to `meetings` Table

Add Fathom integration fields:

```sql
-- Add to existing meetings table (from core-schema.md)
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS fathom_recording_id VARCHAR(255);
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS fathom_share_url TEXT;

-- Index for reverse lookup
CREATE INDEX IF NOT EXISTS idx_meetings_fathom_id ON meetings(fathom_recording_id);
```

---

## Webhooks

### Webhook Endpoint

`POST /webhooks/fathom/recording_ready`

**Authentication:** Webhook signature verification (HMAC-SHA256)

### Event Types

Fathom sends webhooks for the following events:

1. **recording_ready**
   - Triggered when recording is processed and transcript is available
   - Contains recording_id, transcript, participants, metadata
   - Primary event handled by this agent

2. **recording_updated**
   - Triggered when human transcript or corrections are added
   - Reprocess transcript if confidence improves
   - Update existing record

### Webhook Payload Structure

```json
{
  "event": "recording_ready",
  "timestamp": "2025-12-05T16:30:00Z",
  "recording": {
    "id": "fathom_rec_abc123xyz",
    "created_at": "2025-12-05T14:00:00Z",
    "duration_seconds": 1845,
    "video_url": "https://app.fathom.video/recordings/abc123",
    "share_url": "https://share.fathom.video/xyz789",
    "participants": [
      {
        "name": "Sales Rep",
        "email": "sales@smarterteam.ai",
        "duration_seconds": 920
      },
      {
        "name": "John Doe",
        "email": "john@client.com",
        "duration_seconds": 925
      }
    ],
    "transcript": {
      "text": "Full plaintext transcript...",
      "json": {
        "segments": [
          {
            "speaker": "Sales Rep",
            "start": 0.0,
            "end": 3.5,
            "text": "Thanks for joining today, John."
          },
          {
            "speaker": "John Doe",
            "start": 4.0,
            "end": 8.2,
            "text": "Happy to be here. Let's discuss our needs."
          }
        ]
      },
      "confidence": 0.92,
      "language": "en-US"
    },
    "audio_quality": {
      "score": 0.88,
      "background_noise": "low",
      "clarity": "high"
    },
    "metadata": {
      "platform": "zoom",
      "recording_type": "cloud",
      "cal_event_id": "cal_evt_xyz123"
    }
  }
}
```

### Webhook Handler Implementation

```python
# src/webhooks/fathom_webhook.py

from fastapi import APIRouter, Request, HTTPException, Header
from src.agents.meeting_fathom_integration.agent import MeetingFathomIntegrationAgent
from src.agents.meeting_fathom_integration.schemas import FathomWebhookPayload
from src.config import settings
import hmac
import hashlib
from datetime import datetime

router = APIRouter(prefix="/webhooks/fathom", tags=["webhooks"])

@router.post("/recording_ready")
async def handle_fathom_recording_ready(
    request: Request,
    x_fathom_signature: str = Header(None),
    x_fathom_timestamp: str = Header(None)
):
    """Handle Fathom recording_ready webhook."""
    body = await request.body()

    # Verify webhook signature
    if not verify_fathom_signature(body, x_fathom_signature, x_fathom_timestamp):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()

    # Validate webhook timestamp (prevent replay attacks)
    webhook_time = datetime.fromisoformat(x_fathom_timestamp.replace('Z', '+00:00'))
    if (datetime.utcnow() - webhook_time).total_seconds() > 300:
        raise HTTPException(status_code=401, detail="Webhook timestamp expired")

    # Queue async processing via Celery
    from src.tasks.fathom_tasks import process_fathom_recording

    task = process_fathom_recording.delay(
        recording_id=payload["recording"]["id"],
        webhook_payload=payload,
        webhook_received_at=datetime.utcnow().isoformat()
    )

    return {
        "status": "received",
        "recording_id": payload["recording"]["id"],
        "task_id": task.id
    }

def verify_fathom_signature(body: bytes, signature: str, timestamp: str) -> bool:
    """Verify HMAC signature from Fathom."""
    if not signature or not timestamp:
        return False

    # Construct signature payload: timestamp + body
    sig_payload = f"{timestamp}.{body.decode('utf-8')}"

    expected = hmac.new(
        settings.FATHOM_WEBHOOK_SECRET.encode(),
        sig_payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## Error Handling Strategy

### Error Categories

1. **Webhook Validation Errors**
   - Invalid signature: Log security warning, return 401
   - Expired timestamp: Log warning, return 401
   - Malformed payload: Log error with payload sample, return 400
   - All validation errors logged for security audit

2. **Fathom API Errors**
   - Rate limiting (429): Retry with exponential backoff (max 3 retries)
   - Transcript not ready (202): Retry after 60 seconds (max 5 retries)
   - Network errors (5xx): Retry after 5 seconds (max 3 retries)
   - Authentication errors (401): Alert ops team, do NOT retry
   - Log all API errors with full request/response

3. **Meeting Matching Errors**
   - No match found: NOT an error - create orphaned record
   - Multiple matches found: Use highest confidence match, log warning
   - Low confidence match: Store match but flag for manual review
   - Track match failure rate as KPI

4. **Storage Errors**
   - Database errors: Retry once, then queue for manual intervention
   - Zep errors: Non-blocking - log error but continue
   - Disk full: Alert ops immediately (critical)

5. **Handoff Errors**
   - Celery task failed: Queue for retry (max 3 attempts)
   - Transcript Processor unavailable: Queue with delay
   - Alert if handoff failure rate > 2%

### Escalation Rules

Escalate to human when:
- Transcript quality score < 0.6 (needs manual review)
- Meeting matching failed for >20% of recordings (systemic issue)
- Fathom API errors persist for >1 hour (integration down)
- Webhook signature failures spike (potential security issue)
- Storage failures occur (data loss risk)

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(FathomRateLimitError),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def fetch_transcript_with_retry(recording_id: str):
    """Fetch transcript with automatic retry on rate limit."""
    return await fathom_client.get_transcript(recording_id)
```

---

## Fathom API Integration

### Client Implementation

```python
# src/integrations/fathom.py

from src.integrations.base import BaseIntegrationClient
from src.config import settings

class FathomClient(BaseIntegrationClient):
    """Fathom API client."""

    def __init__(self):
        super().__init__(
            name="fathom",
            base_url="https://api.fathom.video/v1",
            api_key=settings.FATHOM_API_KEY,
            timeout=30.0
        )

    async def get_transcript(
        self,
        recording_id: str,
        include_json: bool = True
    ) -> dict:
        """Fetch transcript for a recording."""
        params = {"include_json": str(include_json).lower()}
        return await self._request(
            "GET",
            f"/recordings/{recording_id}/transcript",
            params=params
        )

    async def get_recording_metadata(
        self,
        recording_id: str
    ) -> dict:
        """Fetch recording metadata."""
        return await self._request(
            "GET",
            f"/recordings/{recording_id}"
        )

    async def download_video(
        self,
        recording_id: str,
        output_path: str
    ) -> str:
        """Download video file (optional feature)."""
        response = await self._request(
            "GET",
            f"/recordings/{recording_id}/download",
            stream=True
        )

        with open(output_path, "wb") as f:
            async for chunk in response.aiter_bytes():
                f.write(chunk)

        return output_path
```

---

## Cal.com Integration (MEETING_ENDED Webhook)

### Alternative Trigger Flow

In addition to Fathom webhooks, this agent can be triggered by Cal.com MEETING_ENDED events:

**Cal.com Webhook Handler:**
```python
# src/webhooks/calcom_webhook.py (existing file - add handler)

@router.post("/calcom")
async def handle_calcom_webhook(request: Request, x_cal_signature: str = Header(None)):
    """Handle Cal.com webhooks."""
    # ... existing signature verification ...

    payload = await request.json()
    event_type = payload.get("triggerEvent")

    if event_type == "MEETING_ENDED":
        await handle_meeting_ended(payload)

    # ... other event handlers ...

async def handle_meeting_ended(payload: dict):
    """Trigger Fathom integration to check for recording."""
    meeting_id = payload["payload"]["metadata"].get("meeting_id")
    cal_event_id = payload["payload"]["uid"]

    # Queue check for Fathom recording (may not be ready immediately)
    from src.tasks.fathom_tasks import check_fathom_recording

    check_fathom_recording.apply_async(
        args=[meeting_id, cal_event_id],
        countdown=300  # Wait 5 minutes for Fathom processing
    )
```

**Celery Task:**
```python
# src/tasks/fathom_tasks.py

@celery_app.task(bind=True, max_retries=5)
def check_fathom_recording(self, meeting_id: str, cal_event_id: str):
    """
    Check if Fathom recording is ready for a meeting.

    Retries every 5 minutes for up to 25 minutes (5 retries).
    """
    try:
        # Query call_transcripts for this cal_event_id
        transcript = db.query(CallTranscript).filter(
            CallTranscript.meeting_id == meeting_id
        ).first()

        if transcript:
            logger.info(f"Fathom recording found for meeting {meeting_id}")
            return {"status": "found", "transcript_id": str(transcript.id)}

        # Not ready yet - retry
        raise TranscriptNotReadyError(f"Recording not ready for {cal_event_id}")

    except TranscriptNotReadyError:
        # Retry after 5 minutes
        raise self.retry(countdown=300)
    except Exception as e:
        logger.error(f"Error checking Fathom recording: {e}")
        raise
```

---

## Process Flow

### Main Workflow (Async)

```python
async def process_task(task: dict[str, Any]) -> dict[str, Any]:
    """
    Process Fathom recording webhook.

    Args:
        task: {
            "type": "process_fathom_recording",
            "recording_id": str,
            "webhook_payload": dict,
            "webhook_received_at": str
        }

    Returns:
        {
            "transcript_id": str,
            "meeting_id": str | None,
            "handoff_task_id": str,
            "zep_memory_id": str | None,
            "processing_duration_ms": int
        }
    """
    recording_id = task["recording_id"]
    webhook_payload = task["webhook_payload"]
    webhook_received_at = task["webhook_received_at"]

    start_time = datetime.utcnow()

    self.logger.info(
        "Processing Fathom recording",
        extra={
            "recording_id": recording_id,
            "webhook_received_at": webhook_received_at
        }
    )

    try:
        # Step 1: Fetch full transcript from Fathom API
        transcript_data = await fetch_fathom_transcript(
            recording_id=recording_id,
            include_video_url=True,
            include_metadata=True
        )

        # Step 2: Check transcript quality
        quality_check = await check_transcript_quality(
            transcript_text=transcript_data.transcript_text,
            transcript_json=transcript_data.transcript_json,
            duration_seconds=transcript_data.duration_seconds,
            speaker_count=transcript_data.speaker_count,
            audio_quality_score=transcript_data.audio_quality_score,
            transcript_confidence=transcript_data.transcript_confidence
        )

        # Step 3: Match to existing meeting
        match_result = await match_meeting_to_transcript(
            fathom_recording_id=recording_id,
            cal_event_id=transcript_data.metadata.get("cal_event_id"),
            scheduled_at=transcript_data.recorded_at,
            participant_emails=[p["email"] for p in transcript_data.participants if p.get("email")]
        )

        # Step 4: Store transcript in database
        transcript_id = await store_transcript(
            fathom_recording_id=recording_id,
            transcript_text=transcript_data.transcript_text,
            transcript_json=transcript_data.transcript_json,
            participants=transcript_data.participants,
            duration_seconds=transcript_data.duration_seconds,
            recorded_at=transcript_data.recorded_at,
            video_url=transcript_data.video_url,
            share_url=transcript_data.share_url,
            meeting_id=match_result.meeting_id,
            lead_id=match_result.lead_id,
            raw_webhook_payload=webhook_payload,
            quality_score=quality_check.quality_score,
            quality_issues=quality_check.issues,
            needs_manual_review=quality_check.needs_manual_review,
            match_confidence=match_result.confidence,
            match_method=match_result.match_method
        )

        # Step 5: Update meeting record if match found
        if match_result.meeting_id:
            await update_meeting_record(
                meeting_id=match_result.meeting_id,
                fathom_recording_id=recording_id,
                recording_url=transcript_data.video_url or transcript_data.share_url,
                transcript_text=transcript_data.transcript_text,
                duration_seconds=transcript_data.duration_seconds
            )

        # Step 6: Store in Zep memory (non-blocking)
        zep_memory_id = None
        if match_result.lead_id:
            try:
                zep_result = await store_in_zep_memory(
                    lead_id=match_result.lead_id,
                    transcript_text=transcript_data.transcript_text,
                    meeting_id=match_result.meeting_id or "unmatched",
                    meeting_type="discovery",  # TODO: Get from meeting record
                    participants=[p["name"] for p in transcript_data.participants],
                    key_topics=[]  # Will be extracted by Transcript Processor
                )
                zep_memory_id = zep_result.memory_id
            except Exception as e:
                self.logger.error("Zep storage failed (non-blocking)", extra={"error": str(e)})

        # Step 7: Handoff to Transcript Processor
        handoff_result = await handoff_to_transcript_processor(
            transcript_id=transcript_id,
            lead_id=match_result.lead_id,
            meeting_id=match_result.meeting_id,
            transcript_text=transcript_data.transcript_text,
            priority="high"
        )

        processing_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Step 8: Log completion
        self.log_action(
            "fathom_recording.processed",
            {
                "recording_id": recording_id,
                "transcript_id": transcript_id,
                "meeting_matched": match_result.meeting_id is not None,
                "match_confidence": match_result.confidence,
                "quality_score": quality_check.quality_score,
                "needs_review": quality_check.needs_manual_review,
                "handoff_task_id": handoff_result.task_id,
                "processing_duration_ms": processing_duration_ms
            }
        )

        return {
            "status": "completed",
            "transcript_id": transcript_id,
            "meeting_id": match_result.meeting_id,
            "handoff_task_id": handoff_result.task_id,
            "zep_memory_id": zep_memory_id,
            "processing_duration_ms": processing_duration_ms
        }

    except Exception as e:
        self.logger.error(
            "Error processing Fathom recording",
            extra={"recording_id": recording_id, "error": str(e)}
        )
        raise
```

---

## Testing Requirements

### Unit Tests (Coverage > 90%)

**Test File:** `__tests__/unit/agents/test_meeting_fathom_integration.py`

**Test Cases:**
1. `test_validate_webhook_valid_signature` - Valid HMAC signature passes
2. `test_validate_webhook_invalid_signature` - Invalid signature rejected
3. `test_validate_webhook_expired_timestamp` - Old timestamp rejected
4. `test_fetch_fathom_transcript_success` - API returns valid transcript
5. `test_fetch_fathom_transcript_not_ready` - Handles 202 response
6. `test_fetch_fathom_transcript_rate_limit` - Retries on 429
7. `test_match_meeting_by_cal_event_id` - Exact match found
8. `test_match_meeting_by_timestamp_participant` - Fuzzy match works
9. `test_match_meeting_no_match` - Returns None gracefully
10. `test_store_transcript_with_meeting` - Database insert with match
11. `test_store_transcript_orphaned` - Database insert without match
12. `test_update_meeting_record` - Meeting record updated
13. `test_check_transcript_quality_high` - Quality score calculated
14. `test_check_transcript_quality_low` - Flags for manual review
15. `test_handoff_to_processor` - Celery task created
16. `test_store_in_zep_memory` - Zep API called correctly

### Integration Tests (Coverage > 85%)

**Test File:** `__tests__/integration/test_fathom_webhook.py`

**Test Cases:**
1. `test_webhook_end_to_end` - Full webhook → storage → handoff flow
2. `test_webhook_signature_verification` - Real HMAC verification
3. `test_fathom_api_integration` - Actual API call (mocked)
4. `test_meeting_matching_database` - Database query logic
5. `test_transcript_storage` - Database insert and retrieval
6. `test_zep_integration` - Zep memory storage (mocked)
7. `test_handoff_to_processor` - Celery task triggering
8. `test_quality_check_workflow` - Quality assessment pipeline
9. `test_orphaned_transcript_handling` - No-match scenario
10. `test_duplicate_webhook_idempotency` - Same recording_id twice

### Mock Data Fixtures

**File:** `__tests__/fixtures/fathom_fixtures.py`

```python
import pytest
from datetime import datetime

@pytest.fixture
def mock_fathom_webhook_payload():
    """Mock Fathom recording_ready webhook payload."""
    return {
        "event": "recording_ready",
        "timestamp": "2025-12-05T16:30:00Z",
        "recording": {
            "id": "fathom_rec_test123",
            "created_at": "2025-12-05T14:00:00Z",
            "duration_seconds": 1800,
            "video_url": "https://app.fathom.video/recordings/test123",
            "share_url": "https://share.fathom.video/test456",
            "participants": [
                {
                    "name": "Sales Rep",
                    "email": "sales@smarterteam.ai",
                    "duration_seconds": 900
                },
                {
                    "name": "Jane Doe",
                    "email": "jane@client.com",
                    "duration_seconds": 900
                }
            ],
            "transcript": {
                "text": "Sales Rep: Thanks for joining today, Jane...",
                "json": {
                    "segments": [
                        {
                            "speaker": "Sales Rep",
                            "start": 0.0,
                            "end": 3.5,
                            "text": "Thanks for joining today, Jane."
                        }
                    ]
                },
                "confidence": 0.92,
                "language": "en-US"
            },
            "audio_quality": {
                "score": 0.88,
                "background_noise": "low",
                "clarity": "high"
            },
            "metadata": {
                "platform": "zoom",
                "cal_event_id": "cal_evt_xyz789"
            }
        }
    }

@pytest.fixture
def mock_meeting_record():
    """Mock existing meeting record for matching."""
    return {
        "id": "meeting-uuid-123",
        "lead_id": "lead-uuid-456",
        "campaign_id": "campaign-uuid-789",
        "cal_event_id": "cal_evt_xyz789",
        "scheduled_at": "2025-12-05T14:00:00Z",
        "duration_minutes": 30,
        "meeting_type": "discovery",
        "status": "scheduled"
    }
```

---

## Implementation Checklist

### Phase 1: Core Integration (Week 1)
- [ ] Create agent file structure (`agent.py`, `tools.py`, `schemas.py`, etc.)
- [ ] Implement `FathomClient` integration
- [ ] Implement `validate_fathom_webhook` tool
- [ ] Implement `fetch_fathom_transcript` tool
- [ ] Implement webhook endpoint (`/webhooks/fathom/recording_ready`)
- [ ] Create database migration for `call_transcripts` table
- [ ] Write unit tests for webhook validation (>90% coverage)
- [ ] Write unit tests for Fathom API client

### Phase 2: Meeting Matching (Week 1-2)
- [ ] Implement `match_meeting_to_transcript` tool (all 4 matching strategies)
- [ ] Implement `store_transcript` tool with database inserts
- [ ] Implement `update_meeting_record` tool
- [ ] Add indexes to `meetings` table for Fathom lookups
- [ ] Write tests for matching logic (exact, fuzzy, no-match scenarios)
- [ ] Test orphaned transcript handling

### Phase 3: Quality & Handoffs (Week 2)
- [ ] Implement `check_transcript_quality` tool
- [ ] Implement `handoff_to_transcript_processor` tool
- [ ] Implement `store_in_zep_memory` tool (Zep integration)
- [ ] Add quality scoring algorithm
- [ ] Write tests for quality checks
- [ ] Write tests for handoff flows

### Phase 4: Agent Logic (Week 2-3)
- [ ] Implement `system_prompt` property
- [ ] Implement `process_task` method with full workflow
- [ ] Add error handling for all edge cases
- [ ] Add logging at each step
- [ ] Add timing metrics logging
- [ ] Test manual agent invocation

### Phase 5: Celery Integration (Week 3)
- [ ] Create Celery task: `src/tasks/fathom_tasks.py`
- [ ] Implement `process_fathom_recording` task
- [ ] Implement `check_fathom_recording` task (for Cal.com MEETING_ENDED)
- [ ] Add retry logic for Fathom API calls
- [ ] Test task execution locally
- [ ] Test retry scenarios

### Phase 6: Cal.com Integration (Week 3)
- [ ] Add MEETING_ENDED handler to Cal.com webhook
- [ ] Implement delayed check for Fathom recording
- [ ] Test end-to-end: Cal.com → wait → Fathom → process
- [ ] Verify bidirectional linking (meetings ↔ call_transcripts)

### Phase 7: Testing (Week 3-4)
- [ ] Create test fixtures: `__tests__/fixtures/fathom_fixtures.py`
- [ ] Write unit tests for all 8 tools (>90% coverage)
- [ ] Write integration test for webhook processing
- [ ] Write integration tests for edge cases (quality issues, matching failures, API errors)
- [ ] Run `make test` and verify >85% agent coverage
- [ ] Fix any failing tests

### Phase 8: Quality Assurance (Week 4)
- [ ] Run `make lint` and fix all linting errors
- [ ] Run `make typecheck` and fix all type errors
- [ ] Run `make format` to format code
- [ ] Run `make check` to verify all quality gates pass
- [ ] Manual testing with real Fathom webhooks (staging)
- [ ] Test quality flagging with low-quality recording
- [ ] Test orphaned transcript flow

### Phase 9: Documentation & Deployment (Week 4)
- [ ] Update root `CLAUDE.md` with Fathom integration details
- [ ] Add Fathom environment variables to `.env.example`
- [ ] Document webhook setup instructions for Fathom dashboard
- [ ] Create runbook for troubleshooting common issues
- [ ] Move task to `tasks/backend/_completed/`
- [ ] Update `tasks/TASK-LOG.md` with completion notes
- [ ] Create PR with all changes

### Phase 10: Monitoring & Optimization (Post-Launch)
- [ ] Set up alerts for webhook signature failures
- [ ] Monitor transcript matching rate (target >80%)
- [ ] Track transcript quality score distribution
- [ ] Monitor processing latency (target <5 seconds p95)
- [ ] Track Zep storage success rate
- [ ] Monitor handoff failure rate (alert if >2%)

---

## Success Metrics

- **Webhook Processing Time:** < 5 seconds (p95)
- **Meeting Match Rate:** > 80% (with confidence "high" or "medium")
- **Transcript Quality Score:** > 0.8 average
- **Manual Review Rate:** < 10% of recordings
- **Handoff Success Rate:** > 98%
- **Zep Storage Success Rate:** > 95%
- **API Uptime (Fathom):** > 99.5%
- **Zero Data Loss:** All webhooks stored (even if processing fails)

---

## Security Considerations

1. **Webhook Authentication**
   - Verify HMAC signature on all incoming webhooks
   - Use constant-time comparison to prevent timing attacks
   - Reject webhooks older than 5 minutes (replay prevention)
   - Log all signature validation failures for security audit

2. **Data Privacy**
   - Store transcripts with encryption at rest (Supabase default)
   - Redact PII before storing in Zep memory (names, emails, phone numbers)
   - Comply with GDPR/CCPA for transcript deletion requests
   - Limit access to transcripts via Row Level Security (RLS)

3. **API Key Security**
   - Store `FATHOM_API_KEY` and `FATHOM_WEBHOOK_SECRET` in environment variables
   - Never log API keys or webhook secrets
   - Rotate keys quarterly

4. **Rate Limiting**
   - Implement token bucket for Fathom API calls
   - Monitor rate limit headers and back off proactively
   - Alert if approaching rate limits

5. **Input Validation**
   - Sanitize all user inputs from transcripts before storage
   - Validate JSON structure of webhook payloads
   - Prevent SQL injection via parameterized queries

---

## Performance Considerations

1. **Webhook Response Time:** Must respond to webhooks in <5 seconds (Fathom timeout)
2. **Async Processing:** Queue heavy processing (transcript analysis) for background tasks
3. **Database Indexing:** Added on `fathom_recording_id`, `meeting_id`, `lead_id`, `recorded_at`
4. **Transcript Size:** Max 100,000 characters (~3 hour call). Truncate if longer.
5. **Concurrent Processing:** Max 10 concurrent Fathom API calls (rate limit protection)

---

## Future Enhancements (Post-MVP)

1. **Speaker Identification:** Map "Speaker 1/2" to actual names using voice recognition
2. **Real-time Transcription:** Integrate Fathom live transcription (if available)
3. **Video Highlights:** Extract key moments from video using AI (Fathom feature)
4. **Sentiment Tracking:** Track speaker sentiment changes over time
5. **Coaching Insights:** Compare talking points used vs. planned (from Meeting Prep)
6. **Human Transcript Upgrade:** Automatically request human transcript for high-value deals
7. **Multi-language Support:** Handle non-English transcripts
8. **Recording Storage:** Download and archive video files locally (optional)

---

## References

### Fathom API Documentation
- [API Reference](https://docs.fathom.video/api)
- [Webhooks Documentation](https://docs.fathom.video/webhooks)
- [Authentication](https://docs.fathom.video/authentication)

### Internal Documentation
- BaseAgent implementation: `/Users/yasmineseidu/Desktop/Coding/smarter-team/app/backend/src/agents/base_agent.py`
- BaseIntegrationClient: `/Users/yasmineseidu/Desktop/Coding/smarter-team/app/backend/src/integrations/base.py`
- Meeting Scheduler Spec: `/Users/yasmineseidu/Desktop/Coding/smarter-team/specs/agents/meeting-scheduler.md`
- Transcript Processor Spec: `/Users/yasmineseidu/Desktop/Coding/smarter-team/specs/agents/proposal-transcript-processor.md`
- Database Schema: `/Users/yasmineseidu/Desktop/Coding/smarter-team/specs/database-schema/core-schema.md`
- Project conventions: `/Users/yasmineseidu/Desktop/Coding/smarter-team/.project/CONVENTIONS.md`

---

**Last Updated:** 2025-12-05
**Spec Version:** 1.0.0
**Status:** Ready for Implementation
