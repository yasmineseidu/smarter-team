# Proposal Tracking Agent - Specification

## Metadata

**Agent Name**: ProposalTrackingAgent
**Category**: Proposal & Closing
**Phase**: Phase 3 - Closing & Proposals
**Dependencies**: Proposal Creation Agent, Email Handler Agent
**Priority**: High (critical for closing deals)

## Purpose

Autonomously track proposal engagement and execute intelligent follow-up sequences based on prospect behavior (views, downloads, signatures). Maximizes close rates through data-driven, personalized follow-ups across a 14-day cadence.

## System Architecture

### Agent Class Structure

```python
from src.agents.base_agent import BaseAgent

class ProposalTrackingAgent(BaseAgent):
    """
    Tracks proposal engagement and executes intelligent follow-up sequences.

    Monitors PandaDoc webhooks for proposal activity and triggers contextual
    follow-ups based on prospect behavior. Uses Claude for dynamic personalization
    and escalates to reactivation pool after cadence completion.
    """

    def __init__(self):
        super().__init__(
            name="proposal_tracking",
            description="Tracks proposal engagement and executes follow-up sequences"
        )
        self._register_tools()

    @property
    def system_prompt(self) -> str:
        """Return system prompt for proposal tracking."""
        # See System Prompt section below

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process proposal tracking tasks.

        Supported task types:
        - webhook.document_viewed: Update tracking metrics
        - webhook.document_signed: Transition to CLOSED_WON
        - webhook.document_expired: Move to reactivation pool
        - schedule.daily_followup: Send scheduled follow-ups
        - action.manual_followup: Human-triggered follow-up
        """
```

### Database Schema

#### `proposal_tracking` Table
```sql
CREATE TABLE proposal_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,

    -- Tracking status
    status VARCHAR(50) NOT NULL DEFAULT 'SENT',
    -- Status values: SENT, VIEWED, DOWNLOADED, EXPIRED, SIGNED, REACTIVATION

    -- Engagement metrics
    total_views INTEGER DEFAULT 0,
    total_time_spent INTEGER DEFAULT 0,  -- seconds
    unique_viewers INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    print_count INTEGER DEFAULT 0,

    -- Timeline
    sent_at TIMESTAMPTZ NOT NULL,
    first_viewed_at TIMESTAMPTZ,
    last_viewed_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,

    -- Follow-up tracking
    last_followup_sent_at TIMESTAMPTZ,
    next_followup_scheduled_at TIMESTAMPTZ,
    followup_sequence_day INTEGER DEFAULT 0,  -- 0, 1, 3, 5, 7, 10, 14
    total_followups_sent INTEGER DEFAULT 0,

    -- Metadata
    proposal_value DECIMAL(10, 2),
    proposal_url TEXT NOT NULL,
    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_proposal_tracking_status ON proposal_tracking(status);
CREATE INDEX idx_proposal_tracking_next_followup ON proposal_tracking(next_followup_scheduled_at)
    WHERE next_followup_scheduled_at IS NOT NULL;
CREATE INDEX idx_proposal_tracking_client ON proposal_tracking(client_id);
```

#### `proposal_views` Table
```sql
CREATE TABLE proposal_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_tracking_id UUID NOT NULL REFERENCES proposal_tracking(id) ON DELETE CASCADE,

    -- Viewer details
    viewer_email VARCHAR(255),
    viewer_ip_address INET,
    viewer_user_agent TEXT,

    -- Session tracking
    session_id VARCHAR(100),
    viewed_at TIMESTAMPTZ NOT NULL,
    time_spent INTEGER,  -- seconds on document

    -- Page-level tracking
    pages_viewed JSONB,  -- {"page_1": 30, "page_2": 45} (seconds per page)
    sections_viewed TEXT[],  -- ["pricing", "deliverables", "timeline"]

    -- Actions during view
    downloaded BOOLEAN DEFAULT FALSE,
    printed BOOLEAN DEFAULT FALSE,
    forwarded BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_proposal_views_tracking ON proposal_views(proposal_tracking_id);
CREATE INDEX idx_proposal_views_session ON proposal_views(session_id);
CREATE INDEX idx_proposal_views_timestamp ON proposal_views(viewed_at);
```

#### `proposal_followups` Table
```sql
CREATE TABLE proposal_followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_tracking_id UUID NOT NULL REFERENCES proposal_tracking(id) ON DELETE CASCADE,

    -- Follow-up metadata
    sequence_day INTEGER NOT NULL,  -- 1, 3, 5, 7, 10, 14
    followup_type VARCHAR(50) NOT NULL,
    -- Types: just_sent, no_view_reminder, questions, value_add, deadline_reminder, final_push

    -- Content
    subject_line TEXT NOT NULL,
    email_body TEXT NOT NULL,
    personalization_context JSONB,  -- Data used for Claude personalization

    -- Delivery tracking
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    replied_at TIMESTAMPTZ,

    -- Email provider tracking
    email_provider_id VARCHAR(255),  -- External email service ID
    email_status VARCHAR(50),  -- queued, sent, delivered, opened, clicked, replied, bounced, failed

    -- Sentiment analysis (from reply)
    reply_sentiment VARCHAR(20),  -- positive, neutral, negative, objection
    reply_intent VARCHAR(50),  -- interested, not_interested, needs_info, meeting_request

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_proposal_followups_tracking ON proposal_followups(proposal_tracking_id);
CREATE INDEX idx_proposal_followups_scheduled ON proposal_followups(scheduled_for)
    WHERE sent_at IS NULL;
CREATE INDEX idx_proposal_followups_type ON proposal_followups(followup_type);
```

## Tool Definitions

### 1. `track_proposal_view`
```python
async def track_proposal_view(
    proposal_id: str,
    viewer_email: str | None,
    session_id: str,
    time_spent: int,
    pages_viewed: dict[str, int],
    actions: dict[str, bool]  # {downloaded, printed, forwarded}
) -> dict[str, Any]:
    """
    Track a proposal view event from PandaDoc webhook.

    Updates proposal_tracking metrics and creates proposal_views record.
    Triggers intelligent follow-up logic based on engagement patterns.

    Args:
        proposal_id: UUID of the proposal
        viewer_email: Email of viewer (if available)
        session_id: PandaDoc session identifier
        time_spent: Total seconds spent viewing
        pages_viewed: Map of page IDs to seconds spent
        actions: Boolean flags for download, print, forward

    Returns:
        {
            "status": "success",
            "tracking_id": "uuid",
            "total_views": 5,
            "engagement_score": 85,
            "next_action": "schedule_followup" | "none"
        }

    Raises:
        ValueError: If proposal_id not found
    """
```

### 2. `calculate_engagement_score`
```python
async def calculate_engagement_score(
    tracking_id: str
) -> int:
    """
    Calculate engagement score (0-100) based on viewing behavior.

    Scoring algorithm:
    - First view: +20 points
    - Each additional view: +10 points (max +40)
    - Downloaded: +15 points
    - Printed: +10 points
    - Time spent > 5 min: +15 points
    - Time spent > 10 min: +25 points
    - Multiple viewers: +15 points
    - Viewed pricing section: +10 points

    Args:
        tracking_id: UUID of proposal_tracking record

    Returns:
        Engagement score (0-100)
    """
```

### 3. `schedule_followup`
```python
async def schedule_followup(
    tracking_id: str,
    followup_type: str,
    delay_hours: int | None = None
) -> dict[str, Any]:
    """
    Schedule next follow-up email based on cadence or engagement.

    Cadence schedule (default):
    - Day 1 (0 hours): Just sent confirmation
    - Day 3 (72 hours): No view reminder OR questions check-in
    - Day 5 (120 hours): Value-add content
    - Day 7 (168 hours): Deadline reminder
    - Day 10 (240 hours): Penultimate push
    - Day 14 (336 hours): Final outreach

    Args:
        tracking_id: UUID of proposal_tracking record
        followup_type: Type of follow-up (just_sent, no_view_reminder, etc.)
        delay_hours: Override default cadence delay

    Returns:
        {
            "followup_id": "uuid",
            "scheduled_for": "ISO timestamp",
            "sequence_day": 3,
            "type": "questions"
        }
    """
```

### 4. `personalize_followup`
```python
async def personalize_followup(
    tracking_id: str,
    template_type: str,
    context: dict[str, Any]
) -> dict[str, str]:
    """
    Use Claude to personalize follow-up email based on engagement data.

    Personalization inputs:
    - Viewing behavior (which sections viewed, time spent)
    - Previous email interactions
    - Industry and company context
    - Proposal value and complexity
    - Days since sent

    Args:
        tracking_id: UUID of proposal_tracking record
        template_type: Base template to personalize
        context: Additional context (company_info, pain_points, etc.)

    Returns:
        {
            "subject_line": "Personalized subject",
            "email_body": "Personalized body with dynamic content",
            "personalization_tags": ["pricing_focused", "timeline_concerns"]
        }
    """
```

### 5. `transition_proposal_state`
```python
async def transition_proposal_state(
    tracking_id: str,
    new_status: str,
    metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Transition proposal to new state and trigger appropriate workflows.

    State transitions:
    - SENT → VIEWED: First view detected
    - VIEWED → DOWNLOADED: Document downloaded
    - SENT/VIEWED → SIGNED: Signature received (handoff to payment agent)
    - SENT/VIEWED → EXPIRED: Expiration date reached
    - Any → REACTIVATION: Follow-up cadence completed without signature

    Args:
        tracking_id: UUID of proposal_tracking record
        new_status: Target status
        metadata: Additional context for transition

    Returns:
        {
            "previous_status": "SENT",
            "new_status": "VIEWED",
            "handoffs": ["payment_agent"],  # If applicable
            "actions_taken": ["cancelled_followups", "scheduled_payment_email"]
        }
    """
```

### 6. `analyze_proposal_engagement`
```python
async def analyze_proposal_engagement(
    tracking_id: str
) -> dict[str, Any]:
    """
    Analyze engagement patterns to suggest next actions.

    Pattern detection:
    - High engagement, no signature: Likely has questions
    - Multiple viewers: Decision-making process
    - Viewed pricing repeatedly: Price sensitivity
    - Quick drop-off: Wrong fit or busy
    - No views after 3 days: Email likely missed

    Args:
        tracking_id: UUID of proposal_tracking record

    Returns:
        {
            "engagement_level": "high" | "medium" | "low",
            "patterns": ["price_sensitive", "multiple_stakeholders"],
            "recommended_action": "offer_call",
            "urgency": "high" | "medium" | "low",
            "insights": "Viewed pricing 3x, suggests interest but concern about cost"
        }
    """
```

### 7. `get_next_pending_followups`
```python
async def get_next_pending_followups(
    limit: int = 50
) -> list[dict[str, Any]]:
    """
    Retrieve next batch of pending follow-ups for scheduled task.

    Used by daily Celery task to send queued follow-ups.
    Filters by scheduled_for <= NOW and sent_at IS NULL.

    Args:
        limit: Max number of follow-ups to retrieve

    Returns:
        List of follow-up records ready to send
    """
```

## System Prompt

```
You are the Proposal Tracking Agent for Smarter Team, responsible for maximizing proposal-to-close conversion rates through intelligent, data-driven follow-up sequences.

## Core Responsibilities

1. **Real-time Engagement Tracking**
   - Monitor PandaDoc webhook events (views, downloads, signatures)
   - Calculate engagement scores based on viewing behavior
   - Identify high-intent signals (multiple views, pricing focus, downloads)
   - Detect red flags (no views, quick drop-offs, expired proposals)

2. **Intelligent Follow-up Sequencing**
   - Execute 14-day follow-up cadence: Days 1, 3, 5, 7, 10, 14
   - Personalize every follow-up based on engagement data
   - Adapt messaging based on viewing patterns
   - Escalate to human for high-value deals or complex objections

3. **Behavioral Analysis**
   - Identify decision-making patterns (multiple viewers = committee)
   - Detect price sensitivity (repeated pricing section views)
   - Recognize urgency signals (rapid engagement, deadline awareness)
   - Flag stalled deals for intervention

## Follow-up Cadence Logic

**Day 1 (Immediately after send)**: Confirmation + availability
- Template: "just_sent"
- Tone: Professional, helpful
- CTA: "Let me know if you have any questions"

**Day 3**: Context-dependent
- IF no views: "no_view_reminder" (gentle nudge, check spam)
- IF viewed: "questions" (offer to clarify anything)
- Tone: Conversational, non-pushy

**Day 5**: Value-add content
- Template: "value_add"
- Include: Case study, testimonial, or relevant insight
- Tone: Educational, not salesy

**Day 7**: Deadline reminder
- Template: "deadline_reminder"
- Mention: Proposal expiration date
- Tone: Helpful urgency, not aggressive

**Day 10**: Penultimate push
- Template: "penultimate_push"
- Offer: Quick call to discuss concerns
- Tone: Understanding, solution-focused

**Day 14**: Final outreach
- Template: "final_push"
- Message: Last follow-up, offer to revisit later
- Tone: Respectful, leaving door open

## Personalization Guidelines

1. **High Engagement (80+ score)**
   - Assume interest, focus on moving forward
   - Offer specific next steps (contract signing, kickoff call)
   - Mention sections they engaged with most

2. **Medium Engagement (50-79 score)**
   - Address potential concerns proactively
   - Provide additional information on viewed sections
   - Offer call to discuss questions

3. **Low Engagement (<50 score)**
   - Check if proposal was received
   - Offer to re-send or schedule intro call
   - Keep door open for future timing

4. **Multiple Viewers**
   - Acknowledge decision-making process
   - Offer group call or separate stakeholder conversations
   - Provide executive summary for busy stakeholders

5. **Price-Focused Behavior**
   - Emphasize ROI and value proposition
   - Offer case studies with measurable outcomes
   - Consider flexible payment terms (human approval required)

## State Transition Rules

- **SIGNED**: Immediately handoff to payment_agent, cancel all pending follow-ups
- **EXPIRED**: Move to reactivation pool, notify sales team
- **No response after Day 14**: Mark for reactivation, pause follow-ups for 6 months

## Escalation Triggers

Escalate to human review when:
- Proposal value > $50,000
- Negative sentiment detected in reply
- Competitor mentioned in reply
- Custom pricing requested
- Legal or compliance questions raised
- No engagement after 3 follow-ups

## Tone & Voice

- Professional but conversational
- Never pushy or aggressive
- Empathetic to prospect's timeline
- Focus on helping, not just closing
- Use "we" language to build partnership
- Keep emails under 150 words (concise = respectful)

## Quality Standards

- Personalization required for every follow-up (no generic blasts)
- Subject lines must be curiosity-driven or value-focused
- No more than 1 CTA per email
- Always provide easy opt-out (respect prospect's time)
- Track and learn from reply patterns to improve sequences
```

## Webhook Integration

### PandaDoc Webhook Handler

**Endpoint**: `POST /webhooks/pandadoc`

**Webhook Events**:

1. **`document.viewed`**
```json
{
  "event": "document.viewed",
  "data": {
    "id": "proposal_uuid",
    "session_id": "session_123",
    "recipient": {
      "email": "client@example.com"
    },
    "metadata": {
      "time_spent": 180,
      "pages_viewed": {"1": 60, "2": 90, "3": 30},
      "downloaded": false,
      "printed": false
    },
    "timestamp": "2025-12-05T10:30:00Z"
  }
}
```

**Action**: Call `track_proposal_view()`, update engagement score, schedule next follow-up if needed.

2. **`document.completed`** (Signed)
```json
{
  "event": "document.completed",
  "data": {
    "id": "proposal_uuid",
    "completed_at": "2025-12-05T15:45:00Z",
    "recipient": {
      "email": "client@example.com"
    }
  }
}
```

**Action**: Call `transition_proposal_state("SIGNED")`, handoff to payment agent, cancel pending follow-ups.

3. **`document.expired`**
```json
{
  "event": "document.expired",
  "data": {
    "id": "proposal_uuid",
    "expired_at": "2025-12-19T23:59:59Z"
  }
}
```

**Action**: Call `transition_proposal_state("EXPIRED")`, move to reactivation pool.

### Webhook Security

- Validate webhook signature using `PANDADOC_WEBHOOK_KEY`
- Implement idempotency (de-duplicate webhook retries)
- Handle webhook failures gracefully (retry logic)

**Implementation**:
```python
# src/webhooks/pandadoc.py
from fastapi import APIRouter, HTTPException, Header
import hmac
import hashlib

router = APIRouter(prefix="/webhooks/pandadoc", tags=["webhooks"])

async def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify PandaDoc webhook signature."""
    expected = hmac.new(
        settings.pandadoc_webhook_key.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@router.post("")
async def handle_pandadoc_webhook(
    request: Request,
    x_pandadoc_signature: str = Header(...)
):
    """Handle PandaDoc webhook events."""
    # Verify signature, parse event, route to appropriate handler
```

## Celery Scheduled Tasks

### Daily Follow-up Task

**Task**: `proposal_tracking.send_daily_followups`
**Schedule**: Daily at 3:00 PM local time (highest open rates)
**Cron**: `0 15 * * *` (3:00 PM UTC, adjust for timezone)

```python
# src/tasks/proposal_tasks.py
from src.celery_app import celery_app
from src.config import get_agent_logger

logger = get_agent_logger("proposal_tracking_tasks")

@celery_app.task(bind=True, max_retries=3)
async def send_daily_followups(self):
    """
    Send scheduled follow-up emails for proposals.

    1. Fetch pending follow-ups (scheduled_for <= NOW)
    2. Personalize each follow-up with Claude
    3. Send via email integration
    4. Update tracking records
    5. Schedule next follow-up in cadence
    """
    agent = ProposalTrackingAgent()
    pending = await agent.get_next_pending_followups(limit=100)

    results = {
        "sent": 0,
        "failed": 0,
        "skipped": 0
    }

    for followup in pending:
        try:
            # Personalize and send
            # Update records
            results["sent"] += 1
        except Exception as e:
            logger.error(f"Failed to send followup: {e}")
            results["failed"] += 1

    return results
```

## Error Handling

### Critical Errors (Halt & Escalate)
- PandaDoc API authentication failure
- Database connection lost
- Email service unavailable for >1 hour

### Recoverable Errors (Retry)
- Webhook delivery failure (retry 3x with exponential backoff)
- Email send failure (retry 3x, then mark for manual review)
- Claude API timeout (retry 2x, fallback to template)

### Graceful Degradation
- If Claude API unavailable: Use pre-defined templates without personalization
- If engagement data missing: Use default cadence timing
- If email service down: Queue follow-ups for later retry

## Testing Requirements

### Unit Tests (>90% coverage required)

**File**: `__tests__/unit/agents/test_proposal_tracking_agent.py`

```python
class TestProposalTrackingAgent:
    async def test_track_proposal_view_creates_record(self):
        """Test that tracking a view creates database records."""

    async def test_calculate_engagement_score_algorithm(self):
        """Test engagement score calculation with various scenarios."""

    async def test_schedule_followup_respects_cadence(self):
        """Test that follow-ups are scheduled per 14-day cadence."""

    async def test_personalize_followup_with_claude(self):
        """Test Claude personalization with mock API."""

    async def test_transition_to_signed_handoff_payment(self):
        """Test SIGNED status triggers handoff to payment agent."""

    async def test_transition_to_expired_moves_reactivation(self):
        """Test EXPIRED status moves to reactivation pool."""

    async def test_analyze_engagement_patterns(self):
        """Test pattern detection for various engagement scenarios."""

    async def test_high_engagement_next_action(self):
        """Test high engagement (80+) recommends moving forward."""

    async def test_low_engagement_reminder_logic(self):
        """Test low engagement (<50) triggers reminder emails."""

    async def test_multiple_viewers_detection(self):
        """Test detection of multiple viewers (stakeholder involvement)."""
```

### Integration Tests (>85% coverage required)

**File**: `__tests__/integration/test_proposal_tracking_integration.py`

```python
class TestProposalTrackingIntegration:
    async def test_pandadoc_webhook_viewed_updates_tracking(self):
        """Test end-to-end webhook → tracking update flow."""

    async def test_pandadoc_webhook_signed_triggers_handoff(self):
        """Test signature webhook triggers payment agent handoff."""

    async def test_daily_followup_celery_task(self):
        """Test scheduled Celery task sends pending follow-ups."""

    async def test_followup_cadence_full_sequence(self):
        """Test complete 14-day follow-up sequence execution."""

    async def test_webhook_signature_validation(self):
        """Test webhook security signature verification."""

    async def test_idempotent_webhook_handling(self):
        """Test duplicate webhooks don't create duplicate records."""
```

### E2E Tests (Playwright)

**File**: `tests/e2e/proposal-tracking.spec.ts`

```typescript
test('proposal tracking dashboard shows engagement metrics', async ({ page }) => {
  // Navigate to proposal tracking dashboard
  // Verify engagement scores displayed
  // Check follow-up schedule shown correctly
});

test('manual follow-up trigger sends email', async ({ page }) => {
  // Trigger manual follow-up from UI
  // Verify email queued in database
  // Check confirmation message displayed
});
```

## Performance Requirements

- Webhook processing: <500ms response time
- Engagement score calculation: <200ms
- Follow-up personalization (Claude): <3 seconds
- Daily follow-up task: Process 100 follow-ups in <5 minutes

## Monitoring & Alerts

### Key Metrics
- Follow-up open rate (target: >25%)
- Follow-up reply rate (target: >10%)
- Proposal-to-close rate (target: >30%)
- Average days to signature (target: <7 days)
- Engagement score distribution

### Alerts
- Follow-up send failures (alert if >5% fail rate)
- Webhook processing delays (alert if >1 minute lag)
- Low engagement after Day 5 (alert for high-value deals)
- Proposal expiring in 48 hours with no views

## Security & Compliance

- Never expose proposal content to unauthorized parties
- Redact sensitive pricing info in logs
- Respect GDPR/CCPA opt-out requests immediately
- Encrypt proposal URLs in database
- Audit trail for all follow-up sends and state changes

## Success Criteria

- [ ] All webhook events processed within 500ms
- [ ] Follow-up personalization working with Claude
- [ ] 14-day cadence executing on schedule
- [ ] State transitions trigger correct handoffs
- [ ] Test coverage >85% for agent
- [ ] Test coverage >90% for tools
- [ ] No PII leakage in logs
- [ ] Webhook signature validation enforced
- [ ] Graceful degradation when Claude API unavailable

## Future Enhancements (Post-MVP)

- A/B test follow-up templates
- ML-based optimal send time prediction
- Sentiment analysis on proposal comments
- Integration with video messaging (Loom)
- Proposal heat maps (which sections most viewed)
- Automated pricing negotiation workflows
- Multi-language follow-up support
