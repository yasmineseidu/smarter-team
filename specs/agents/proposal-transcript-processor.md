# Call Transcript Processor Agent - Technical Specification

**Agent Category:** Proposal & Closing
**Priority:** Phase 3 - Closing & Proposals
**Version:** 1.0.0
**Last Updated:** 2025-12-05

## Overview

The Call Transcript Processor Agent extracts actionable insights from meeting recordings received via Fathom webhooks. It uses Claude AI to analyze transcripts, identify key business signals (pain points, budget, decision makers, objections), create structured action items, and feed insights to downstream agents (Proposal Creation, Sales).

## Dependencies

### Upstream Agents
- **Meeting Scheduler Agent**: Provides meeting context (attendees, purpose, pre-call notes)

### Downstream Agents
- **Proposal Creation Agent**: Receives call insights for proposal generation
- **Sales Agent**: Receives lead qualification updates
- **Task Management**: Action items auto-created in ClickUp/Todoist

### Third-Party Integrations
- **Fathom**: Webhook receiver for transcript data (POST /webhooks/fathom/recording_ready)
- **Anthropic Claude**: AI analysis for insight extraction
- **ClickUp API**: Action item creation
- **Todoist API**: Alternative task management

## Data Models

### Database Tables

#### call_transcripts
```sql
CREATE TABLE call_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fathom_recording_id VARCHAR(255) UNIQUE NOT NULL,
    lead_id UUID REFERENCES leads(id),
    meeting_id UUID REFERENCES meetings(id),
    call_date TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds INTEGER NOT NULL,
    transcript_text TEXT NOT NULL,
    participants JSONB NOT NULL,  -- [{"name": "...", "email": "..."}]
    fathom_video_url TEXT,
    fathom_share_url TEXT,
    raw_webhook_payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_call_transcripts_lead_id ON call_transcripts(lead_id);
CREATE INDEX idx_call_transcripts_meeting_id ON call_transcripts(meeting_id);
CREATE INDEX idx_call_transcripts_call_date ON call_transcripts(call_date);
CREATE INDEX idx_call_transcripts_fathom_recording_id ON call_transcripts(fathom_recording_id);
```

#### call_insights
```sql
CREATE TABLE call_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID REFERENCES call_transcripts(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id),

    -- Summary & Sentiment
    summary TEXT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,  -- positive, neutral, negative
    likelihood_to_close DECIMAL(3,2) CHECK (likelihood_to_close >= 0 AND likelihood_to_close <= 1),

    -- Key Points
    key_points JSONB NOT NULL DEFAULT '[]',  -- ["point1", "point2"]

    -- Pain Points
    pain_points JSONB NOT NULL DEFAULT '[]',
    -- [{"pain": "...", "severity": "high|medium|low", "mentioned_at": "..."}]

    -- Budget & Timeline
    budget_mentioned BOOLEAN DEFAULT FALSE,
    budget_range VARCHAR(100),
    budget_timeline VARCHAR(100),
    budget_details JSONB DEFAULT '{}',

    -- Decision Makers
    decision_makers JSONB NOT NULL DEFAULT '[]',
    -- [{"name": "...", "role": "...", "influence": "high|medium|low", "contact": "..."}]

    -- Objections
    objections JSONB NOT NULL DEFAULT '[]',
    -- [{"objection": "...", "response_given": "...", "resolved": true|false, "severity": "..."}]

    -- Next Steps
    next_steps JSONB NOT NULL DEFAULT '[]',  -- ["step1", "step2"]

    -- Metadata
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_duration_ms INTEGER,
    model_version VARCHAR(50),  -- e.g., "claude-opus-4-5"
    confidence_score DECIMAL(3,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_call_insights_transcript_id ON call_insights(transcript_id);
CREATE INDEX idx_call_insights_lead_id ON call_insights(lead_id);
CREATE INDEX idx_call_insights_sentiment ON call_insights(sentiment);
CREATE INDEX idx_call_insights_likelihood_to_close ON call_insights(likelihood_to_close DESC);
CREATE INDEX idx_call_insights_processed_at ON call_insights(processed_at DESC);
```

#### call_action_items
```sql
CREATE TABLE call_action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID REFERENCES call_transcripts(id) ON DELETE CASCADE,
    insight_id UUID REFERENCES call_insights(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id),

    -- Task Details
    task_description TEXT NOT NULL,
    owner VARCHAR(50) NOT NULL,  -- "us" or "them"
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'normal',  -- critical, high, normal, low

    -- External Integration
    clickup_task_id VARCHAR(100),
    todoist_task_id VARCHAR(100),
    integration_synced_at TIMESTAMP WITH TIME ZONE,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_call_action_items_transcript_id ON call_action_items(transcript_id);
CREATE INDEX idx_call_action_items_insight_id ON call_action_items(insight_id);
CREATE INDEX idx_call_action_items_lead_id ON call_action_items(lead_id);
CREATE INDEX idx_call_action_items_status ON call_action_items(status);
CREATE INDEX idx_call_action_items_due_date ON call_action_items(due_date);
CREATE INDEX idx_call_action_items_owner ON call_action_items(owner);
```

### Pydantic Models

```python
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Participant(BaseModel):
    """Meeting participant."""
    name: str
    email: str | None = None


class PainPoint(BaseModel):
    """Identified pain point from call."""
    pain: str
    severity: str = Field(..., pattern="^(high|medium|low)$")
    mentioned_at: str | None = None  # Timestamp or quote from transcript


class DecisionMaker(BaseModel):
    """Decision maker identified in call."""
    name: str
    role: str
    influence: str = Field(..., pattern="^(high|medium|low)$")
    contact: str | None = None


class Objection(BaseModel):
    """Objection raised during call."""
    objection: str
    response_given: str | None = None
    resolved: bool = False
    severity: str | None = Field(None, pattern="^(high|medium|low)$")


class BudgetDetails(BaseModel):
    """Budget information extracted from call."""
    mentioned: bool = False
    range: str | None = None
    timeline: str | None = None
    additional_notes: dict[str, Any] = Field(default_factory=dict)


class ActionItemCreate(BaseModel):
    """Action item to be created."""
    task: str = Field(..., min_length=5, max_length=500)
    owner: str = Field(..., pattern="^(us|them)$")
    due: str | None = None  # ISO date string
    priority: str = Field(default="normal", pattern="^(critical|high|normal|low)$")


class CallInsightExtraction(BaseModel):
    """Structured extraction from call transcript."""
    summary: str = Field(..., min_length=20, max_length=1000)
    key_points: list[str] = Field(default_factory=list, max_length=20)
    pain_points: list[PainPoint] = Field(default_factory=list, max_length=15)
    budget: BudgetDetails
    decision_makers: list[DecisionMaker] = Field(default_factory=list, max_length=10)
    objections: list[Objection] = Field(default_factory=list, max_length=10)
    next_steps: list[str] = Field(default_factory=list, max_length=10)
    action_items: list[ActionItemCreate] = Field(default_factory=list, max_length=20)
    sentiment: str = Field(..., pattern="^(positive|neutral|negative)$")
    likelihood_to_close: Decimal = Field(..., ge=0, le=1)
    confidence_score: Decimal = Field(default=Decimal("0.0"), ge=0, le=1)

    @field_validator("likelihood_to_close", "confidence_score", mode="before")
    @classmethod
    def validate_decimal(cls, v: Any) -> Decimal:
        """Convert float to Decimal."""
        if isinstance(v, float):
            return Decimal(str(v))
        return v


class FathomWebhookPayload(BaseModel):
    """Fathom webhook payload structure."""
    recording_id: str
    meeting_date: datetime
    duration_seconds: int
    transcript: str
    participants: list[Participant]
    video_url: str | None = None
    share_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

## Agent Implementation

### System Prompt

```python
TRANSCRIPT_PROCESSOR_SYSTEM_PROMPT = """You are an expert sales call analyst for an AI agency. Your role is to extract actionable business intelligence from meeting transcripts.

**Your Responsibilities:**
1. Analyze call transcripts thoroughly and identify key business signals
2. Extract structured data including pain points, budget, decision makers, and objections
3. Assess deal quality with sentiment and likelihood to close
4. Create specific, actionable follow-up tasks

**Analysis Guidelines:**

**Pain Points:**
- Identify explicit and implicit problems mentioned
- Rate severity based on urgency, frequency, and emotional intensity
- Quote or reference specific transcript sections

**Budget & Timeline:**
- Flag any mention of budget, even indirect (e.g., "we have funds allocated")
- Extract timeline signals (Q1 2025, next quarter, ASAP, etc.)
- Note budget constraints or flexibility

**Decision Makers:**
- Identify who has authority (titles: CEO, CTO, VP, Director)
- Assess influence level based on:
  - Role seniority
  - Speaking time and decisiveness
  - Use of "I will decide" vs "I need to check with..."
- Capture contact information if mentioned

**Objections:**
- Document all concerns, hesitations, or blockers
- Record our response if given
- Mark as resolved/unresolved based on prospect's reaction
- Prioritize unresolved objections for follow-up

**Sentiment & Likelihood:**
- Positive: Enthusiastic, ready to move forward, budget confirmed
- Neutral: Interested but cautious, needs more info
- Negative: Skeptical, cost concerns, competitive alternatives mentioned
- Likelihood to close: 0.0-1.0 based on buying signals

**Action Items:**
- Create specific tasks with clear owners ("us" or "them")
- Set realistic due dates based on urgency discussed
- Prioritize tasks: critical (deals at risk), high (time-sensitive), normal, low

**Output Format:**
Return valid JSON matching the CallInsightExtraction schema. Be precise, factual, and avoid assumptions not supported by the transcript.

**Quality Standards:**
- Summary: 2-4 sentences capturing the call's essence
- Key points: 3-8 most important topics discussed
- Always provide confidence_score (0.0-1.0) based on transcript clarity and completeness
"""
```

### Tool Definitions

```python
from typing import Any


async def create_clickup_task(
    task_description: str,
    due_date: str | None,
    priority: str,
    lead_id: str,
) -> dict[str, Any]:
    """
    Create a task in ClickUp.

    Args:
        task_description: Task description
        due_date: Due date (ISO format)
        priority: Task priority (critical, high, normal, low)
        lead_id: Associated lead ID for custom field

    Returns:
        ClickUp task response with task_id
    """
    # Will be implemented in src/integrations/clickup.py
    pass


async def create_todoist_task(
    task_description: str,
    due_date: str | None,
    priority: str,
    lead_id: str,
) -> dict[str, Any]:
    """
    Create a task in Todoist.

    Args:
        task_description: Task description
        due_date: Due date (ISO format)
        priority: Task priority (1-4 mapping from our priority levels)
        lead_id: Associated lead ID in description

    Returns:
        Todoist task response with task_id
    """
    # Will be implemented in src/integrations/todoist.py
    pass


async def update_lead_qualification(
    lead_id: str,
    likelihood_to_close: float,
    budget_mentioned: bool,
    decision_makers_count: int,
    sentiment: str,
) -> dict[str, Any]:
    """
    Update lead qualification score based on call insights.

    Args:
        lead_id: Lead UUID
        likelihood_to_close: Likelihood score (0.0-1.0)
        budget_mentioned: Whether budget was discussed
        decision_makers_count: Number of decision makers identified
        sentiment: Call sentiment (positive/neutral/negative)

    Returns:
        Updated lead record
    """
    # Updates leads table with qualification data
    pass


async def fetch_meeting_context(
    meeting_id: str,
) -> dict[str, Any]:
    """
    Fetch meeting context from Meeting Scheduler Agent.

    Args:
        meeting_id: Meeting UUID

    Returns:
        Meeting context including attendees, purpose, pre-call notes
    """
    # Retrieves from meetings table
    pass
```

### Agent Class

```python
"""Call Transcript Processor Agent."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from anthropic import AsyncAnthropic
from pydantic import ValidationError

from src.agents.base_agent import BaseAgent
from src.config import Settings, get_agent_logger


class TranscriptProcessorAgent(BaseAgent):
    """
    Processes call transcripts from Fathom to extract actionable insights.

    Analyzes meeting recordings to identify pain points, budget signals,
    decision makers, objections, and creates follow-up action items.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the Transcript Processor Agent.

        Args:
            settings: Application settings with API keys
        """
        super().__init__(
            name="transcript_processor",
            description="Extracts insights from call transcripts and creates action items",
        )
        self.settings = settings
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Register tools
        self.register_tool(
            create_clickup_task,
            "create_clickup_task",
            "Create action item in ClickUp project management",
        )
        self.register_tool(
            create_todoist_task,
            "create_todoist_task",
            "Create action item in Todoist task manager",
        )
        self.register_tool(
            update_lead_qualification,
            "update_lead_qualification",
            "Update lead qualification based on call insights",
        )
        self.register_tool(
            fetch_meeting_context,
            "fetch_meeting_context",
            "Retrieve meeting context and pre-call notes",
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for transcript analysis."""
        return TRANSCRIPT_PROCESSOR_SYSTEM_PROMPT

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process incoming transcript analysis task.

        Args:
            task: Task payload with transcript data

        Returns:
            Processing result with insights and action items created

        Raises:
            ValueError: If transcript_id or transcript_text missing
            ValidationError: If AI extraction doesn't match schema
        """
        task_type = task.get("type")

        if task_type == "process_transcript":
            return await self._process_transcript(task)
        elif task_type == "reprocess_transcript":
            return await self._reprocess_transcript(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _process_transcript(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Main transcript processing workflow.

        Steps:
        1. Validate input and fetch meeting context
        2. Analyze transcript with Claude AI
        3. Store insights in database
        4. Create action items in ClickUp/Todoist
        5. Handoff to Proposal Agent if high likelihood
        6. Update lead qualification

        Args:
            task: Task with transcript_id, transcript_text, lead_id, meeting_id

        Returns:
            Processing result with insights, action_items_created, handoffs
        """
        transcript_id = task.get("transcript_id")
        transcript_text = task.get("transcript_text")
        lead_id = task.get("lead_id")
        meeting_id = task.get("meeting_id")

        if not transcript_id or not transcript_text:
            raise ValueError("transcript_id and transcript_text are required")

        start_time = datetime.utcnow()
        self.logger.info(
            "Processing transcript",
            extra={
                "transcript_id": transcript_id,
                "lead_id": lead_id,
                "transcript_length": len(transcript_text),
            },
        )

        try:
            # Step 1: Fetch meeting context
            meeting_context = {}
            if meeting_id:
                meeting_context = await fetch_meeting_context(meeting_id)
                self.logger.debug("Fetched meeting context", extra={"meeting_id": meeting_id})

            # Step 2: Analyze transcript with Claude
            extraction = await self._extract_insights(transcript_text, meeting_context)

            # Step 3: Store insights in database
            insight_id = await self._store_insights(transcript_id, lead_id, extraction)

            # Step 4: Create action items
            action_items_created = await self._create_action_items(
                transcript_id,
                insight_id,
                lead_id,
                extraction.action_items,
            )

            # Step 5: Update lead qualification
            if lead_id:
                await update_lead_qualification(
                    lead_id=lead_id,
                    likelihood_to_close=float(extraction.likelihood_to_close),
                    budget_mentioned=extraction.budget.mentioned,
                    decision_makers_count=len(extraction.decision_makers),
                    sentiment=extraction.sentiment,
                )

            # Step 6: Handoff to Proposal Agent if high likelihood (>0.7)
            handoffs = []
            if extraction.likelihood_to_close >= 0.7 and lead_id:
                proposal_task_id = await self.handoff_to(
                    target_agent="proposal_creation",
                    payload={
                        "lead_id": lead_id,
                        "transcript_id": transcript_id,
                        "insights": extraction.model_dump(),
                        "trigger": "high_close_likelihood",
                    },
                    priority="high",
                )
                handoffs.append({"agent": "proposal_creation", "task_id": proposal_task_id})
                self.logger.info(
                    "Handed off to Proposal Creation",
                    extra={"task_id": proposal_task_id, "likelihood": float(extraction.likelihood_to_close)},
                )

            processing_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            self.log_action(
                "transcript.processed",
                {
                    "transcript_id": transcript_id,
                    "insight_id": insight_id,
                    "action_items_created": action_items_created,
                    "likelihood_to_close": float(extraction.likelihood_to_close),
                    "sentiment": extraction.sentiment,
                    "processing_duration_ms": processing_duration_ms,
                },
            )

            return {
                "status": "completed",
                "transcript_id": transcript_id,
                "insight_id": insight_id,
                "insights": extraction.model_dump(),
                "action_items_created": action_items_created,
                "handoffs": handoffs,
                "processing_duration_ms": processing_duration_ms,
            }

        except ValidationError as e:
            self.logger.error(
                "Validation error during extraction",
                extra={"transcript_id": transcript_id, "error": str(e)},
            )
            raise
        except Exception as e:
            self.logger.error(
                "Error processing transcript",
                extra={"transcript_id": transcript_id, "error": str(e)},
            )
            raise

    async def _extract_insights(
        self,
        transcript_text: str,
        meeting_context: dict[str, Any],
    ) -> CallInsightExtraction:
        """
        Extract structured insights from transcript using Claude.

        Args:
            transcript_text: Full call transcript
            meeting_context: Optional context from meeting scheduler

        Returns:
            Validated CallInsightExtraction

        Raises:
            ValidationError: If Claude output doesn't match schema
        """
        context_str = ""
        if meeting_context:
            context_str = f"\n\nMeeting Context:\n{json.dumps(meeting_context, indent=2)}"

        user_prompt = f"""Analyze this sales call transcript and extract structured insights.
{context_str}

Transcript:
{transcript_text}

Return ONLY valid JSON matching the CallInsightExtraction schema. No markdown, no extra text."""

        response = await self.anthropic.messages.create(
            model="claude-opus-4-5",
            max_tokens=4000,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.3,  # Lower temperature for structured extraction
        )

        content = response.content[0].text

        # Parse JSON from Claude response
        try:
            extraction_data = json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse Claude JSON", extra={"content": content[:500]})
            raise ValueError(f"Claude returned invalid JSON: {e}")

        # Validate against Pydantic schema
        extraction = CallInsightExtraction(**extraction_data)

        self.logger.info(
            "Extracted insights from transcript",
            extra={
                "sentiment": extraction.sentiment,
                "likelihood_to_close": float(extraction.likelihood_to_close),
                "pain_points_count": len(extraction.pain_points),
                "action_items_count": len(extraction.action_items),
            },
        )

        return extraction

    async def _store_insights(
        self,
        transcript_id: str,
        lead_id: str | None,
        extraction: CallInsightExtraction,
    ) -> str:
        """
        Store extracted insights in call_insights table.

        Args:
            transcript_id: Transcript UUID
            lead_id: Lead UUID (optional)
            extraction: Validated extraction

        Returns:
            Insight ID (UUID as string)
        """
        # Database insert logic here
        # Returns UUID of created call_insights record
        pass

    async def _create_action_items(
        self,
        transcript_id: str,
        insight_id: str,
        lead_id: str | None,
        action_items: list[ActionItemCreate],
    ) -> int:
        """
        Create action items in database and ClickUp/Todoist.

        Args:
            transcript_id: Transcript UUID
            insight_id: Insight UUID
            lead_id: Lead UUID (optional)
            action_items: List of action items to create

        Returns:
            Count of action items created
        """
        created_count = 0

        for item in action_items:
            # Insert into call_action_items table
            action_item_id = await self._insert_action_item_db(
                transcript_id, insight_id, lead_id, item
            )

            # Create in ClickUp (prefer) or Todoist
            try:
                if self.settings.CLICKUP_API_KEY:
                    result = await create_clickup_task(
                        task_description=item.task,
                        due_date=item.due,
                        priority=item.priority,
                        lead_id=lead_id or "",
                    )
                    # Update action_item with clickup_task_id
                    await self._update_action_item_integration(
                        action_item_id, clickup_task_id=result["task_id"]
                    )
                elif self.settings.TODOIST_API_KEY:
                    result = await create_todoist_task(
                        task_description=item.task,
                        due_date=item.due,
                        priority=item.priority,
                        lead_id=lead_id or "",
                    )
                    # Update action_item with todoist_task_id
                    await self._update_action_item_integration(
                        action_item_id, todoist_task_id=result["task_id"]
                    )

                created_count += 1

            except Exception as e:
                self.logger.error(
                    "Failed to create action item in external system",
                    extra={"action_item_id": action_item_id, "error": str(e)},
                )
                # Continue processing other items

        self.logger.info(
            "Created action items",
            extra={"count": created_count, "total": len(action_items)},
        )

        return created_count

    async def _insert_action_item_db(
        self,
        transcript_id: str,
        insight_id: str,
        lead_id: str | None,
        item: ActionItemCreate,
    ) -> str:
        """Insert action item into database."""
        # Database insert logic
        pass

    async def _update_action_item_integration(
        self,
        action_item_id: str,
        clickup_task_id: str | None = None,
        todoist_task_id: str | None = None,
    ) -> None:
        """Update action item with external task ID."""
        # Database update logic
        pass

    async def _reprocess_transcript(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Reprocess an existing transcript (e.g., after prompt improvements).

        Args:
            task: Task with transcript_id

        Returns:
            Processing result
        """
        transcript_id = task.get("transcript_id")

        if not transcript_id:
            raise ValueError("transcript_id is required for reprocessing")

        # Fetch original transcript from database
        transcript_data = await self._fetch_transcript(transcript_id)

        # Reprocess with current logic
        return await self._process_transcript({
            "type": "process_transcript",
            "transcript_id": transcript_id,
            "transcript_text": transcript_data["transcript_text"],
            "lead_id": transcript_data.get("lead_id"),
            "meeting_id": transcript_data.get("meeting_id"),
        })

    async def _fetch_transcript(self, transcript_id: str) -> dict[str, Any]:
        """Fetch transcript from database."""
        # Database fetch logic
        pass
```

## Webhook Handler

```python
"""Fathom webhook handler for transcript processing."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError

from src.agents.transcript_processor.agent import TranscriptProcessorAgent
from src.config import Settings

router = APIRouter(prefix="/webhooks/fathom", tags=["webhooks"])


@router.post("/recording_ready", status_code=status.HTTP_202_ACCEPTED)
async def fathom_recording_ready(request: Request) -> dict[str, Any]:
    """
    Handle Fathom recording_ready webhook.

    Triggered when a Fathom recording is processed and transcript is ready.

    Request Body:
        FathomWebhookPayload: Webhook payload from Fathom

    Returns:
        Accepted response with task_id for tracking

    Raises:
        HTTPException 400: Invalid payload
        HTTPException 500: Processing error
    """
    try:
        payload = await request.json()

        # Validate webhook payload
        try:
            webhook_data = FathomWebhookPayload(**payload)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook payload: {e}",
            )

        # Store transcript in database
        transcript_id = await _store_transcript(webhook_data, payload)

        # Trigger async processing via Celery
        from src.tasks.transcript_tasks import process_transcript_task

        task = process_transcript_task.delay(
            transcript_id=str(transcript_id),
            transcript_text=webhook_data.transcript,
            lead_id=None,  # TODO: Match lead from participants/meeting
            meeting_id=None,  # TODO: Match meeting from recording_id
        )

        return {
            "status": "accepted",
            "transcript_id": str(transcript_id),
            "task_id": task.id,
            "message": "Transcript queued for processing",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {e}",
        )


async def _store_transcript(
    webhook_data: FathomWebhookPayload,
    raw_payload: dict[str, Any],
) -> UUID:
    """
    Store transcript in call_transcripts table.

    Args:
        webhook_data: Validated webhook payload
        raw_payload: Raw webhook JSON for audit trail

    Returns:
        Transcript UUID
    """
    # Database insert logic
    # Returns UUID of created call_transcripts record
    pass
```

## Error Handling

### Error Scenarios

1. **Invalid Webhook Payload**
   - Response: 400 Bad Request
   - Action: Log validation errors, return specific field errors

2. **Claude API Failure**
   - Response: Retry up to 3 times with exponential backoff
   - Action: Store transcript for manual review if all retries fail

3. **Invalid JSON from Claude**
   - Response: Log error, retry with temperature=0.1
   - Action: Fallback to basic extraction if schema validation fails

4. **ClickUp/Todoist API Failure**
   - Response: Store action items in database only
   - Action: Retry sync later via scheduled task

5. **Database Errors**
   - Response: 500 Internal Server Error
   - Action: Log full error context, alert monitoring

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def _extract_insights_with_retry(
    self,
    transcript_text: str,
    meeting_context: dict[str, Any],
) -> CallInsightExtraction:
    """Extract insights with automatic retry on failure."""
    return await self._extract_insights(transcript_text, meeting_context)
```

## Testing Requirements

### Coverage Target: >85%

### Unit Tests

**File:** `__tests__/unit/agents/transcript_processor/test_agent.py`

1. **Initialization**
   - Agent has correct name and description
   - Tools registered (4 tools)
   - System prompt is set
   - Anthropic client initialized

2. **Insight Extraction**
   - Valid transcript produces valid CallInsightExtraction
   - Handles missing fields gracefully
   - Temperature=0.3 used for structured output
   - Validates against Pydantic schema

3. **Action Item Creation**
   - Creates items in ClickUp when CLICKUP_API_KEY set
   - Falls back to Todoist when ClickUp unavailable
   - Stores all items in database
   - Returns correct count

4. **Lead Qualification Update**
   - Updates lead with likelihood_to_close
   - Updates budget_mentioned flag
   - Updates decision_makers_count
   - Updates sentiment

5. **Agent Handoff**
   - Hands off to Proposal Agent when likelihood >= 0.7
   - Includes transcript insights in payload
   - Sets priority to "high"
   - Returns task_id

6. **Error Handling**
   - Raises ValueError on missing transcript_id
   - Raises ValidationError on invalid Claude output
   - Logs errors with context
   - Retries Claude API calls

**File:** `__tests__/unit/agents/transcript_processor/test_models.py`

1. **Pydantic Model Validation**
   - CallInsightExtraction validates all fields
   - Decimal conversion for likelihood_to_close
   - Pattern validation for sentiment, severity, owner
   - List length constraints enforced

### Integration Tests

**File:** `__tests__/integration/test_fathom_webhook.py`

1. **Webhook Processing**
   - POST /webhooks/fathom/recording_ready accepts valid payload
   - Returns 202 with transcript_id and task_id
   - Stores transcript in database
   - Triggers Celery task

2. **End-to-End Flow**
   - Webhook → Database → Celery → Agent → Insights → Action Items
   - ClickUp task created
   - Lead qualification updated
   - Proposal Agent handoff triggered

3. **Error Responses**
   - 400 on invalid payload
   - 500 on database error
   - Proper error messages returned

### Fixtures

**File:** `__tests__/fixtures/transcript_processor_fixtures.py`

```python
import pytest
from datetime import datetime
from decimal import Decimal


@pytest.fixture
def sample_transcript_text() -> str:
    """Sample sales call transcript."""
    return """
    Sales Rep: Thanks for joining today. Can you tell me about your current challenges?

    CTO (John Smith): We're struggling with manual data entry. Our team spends 10 hours
    a week on this, and it's error-prone. We need automation.

    Sales Rep: I understand. What's your timeline for solving this?

    CTO: We want something in place by Q1 2025. Budget-wise, we have $50k-$75k allocated.

    Sales Rep: Great. Who else is involved in the decision?

    CTO: I'll make the final call, but our VP of Operations will need to sign off.

    Sales Rep: Any concerns about implementing an AI solution?

    CTO: Just data security. We handle sensitive customer information.

    Sales Rep: We're SOC 2 compliant and can provide a BAA if needed.

    CTO: Perfect. Let's move forward with a proposal.
    """


@pytest.fixture
def sample_fathom_payload() -> dict:
    """Sample Fathom webhook payload."""
    return {
        "recording_id": "fathom_rec_12345",
        "meeting_date": "2025-12-05T14:00:00Z",
        "duration_seconds": 1800,
        "transcript": sample_transcript_text(),
        "participants": [
            {"name": "Sales Rep", "email": "sales@agency.com"},
            {"name": "John Smith", "email": "john@client.com"},
        ],
        "video_url": "https://fathom.video/rec/12345",
        "share_url": "https://fathom.video/share/12345",
        "metadata": {},
    }


@pytest.fixture
def expected_insights() -> dict:
    """Expected insights extraction from sample transcript."""
    return {
        "summary": "Discovery call with CTO to discuss automation needs. Budget confirmed at $50k-$75k for Q1 2025 implementation.",
        "key_points": [
            "Manual data entry takes 10 hours/week",
            "Budget: $50k-$75k",
            "Timeline: Q1 2025",
            "Data security is primary concern",
        ],
        "pain_points": [
            {
                "pain": "Manual data entry consuming 10 hours/week with errors",
                "severity": "high",
                "mentioned_at": "CTO: We're struggling with manual data entry...",
            }
        ],
        "budget": {
            "mentioned": True,
            "range": "$50k-$75k",
            "timeline": "Q1 2025",
            "additional_notes": {},
        },
        "decision_makers": [
            {
                "name": "John Smith",
                "role": "CTO",
                "influence": "high",
                "contact": "john@client.com",
            },
            {
                "name": "VP of Operations",
                "role": "VP of Operations",
                "influence": "medium",
                "contact": None,
            },
        ],
        "objections": [
            {
                "objection": "Data security concerns with sensitive customer information",
                "response_given": "SOC 2 compliant, can provide BAA",
                "resolved": True,
                "severity": "medium",
            }
        ],
        "next_steps": ["Create proposal", "Provide SOC 2 documentation"],
        "action_items": [
            {
                "task": "Create proposal with automation solution",
                "owner": "us",
                "due": "2025-12-10",
                "priority": "high",
            },
            {
                "task": "Send SOC 2 compliance documentation",
                "owner": "us",
                "due": "2025-12-06",
                "priority": "high",
            },
        ],
        "sentiment": "positive",
        "likelihood_to_close": 0.85,
        "confidence_score": 0.9,
    }
```

### Mock Setup

```python
@pytest.fixture
def mock_anthropic_response(monkeypatch):
    """Mock Anthropic API to return valid extraction."""
    from unittest.mock import AsyncMock

    async def mock_create(*args, **kwargs):
        return MagicMock(
            content=[MagicMock(text=json.dumps(expected_insights()))]
        )

    monkeypatch.setattr(
        "anthropic.AsyncAnthropic.messages.create",
        AsyncMock(side_effect=mock_create),
    )


@pytest.fixture
def mock_clickup_client(monkeypatch):
    """Mock ClickUp task creation."""
    async def mock_create_task(*args, **kwargs):
        return {"task_id": "clickup_123", "status": "created"}

    monkeypatch.setattr(
        "src.integrations.clickup.create_task",
        AsyncMock(side_effect=mock_create_task),
    )
```

## Human-in-the-Loop

### Review Gates

**Gate 1: Call Summary Review**
- **Trigger:** After insight extraction, before action item creation
- **Reviewer:** Sales team member
- **Review UI:** Dashboard showing summary, pain points, budget, sentiment
- **Actions:** Approve, Edit Summary, Flag for Manual Review
- **Timeout:** Auto-approve after 2 hours if no response

**Gate 2: Action Item Approval**
- **Trigger:** Before syncing to ClickUp/Todoist
- **Reviewer:** Sales manager
- **Review UI:** List of proposed action items with due dates
- **Actions:** Approve All, Edit Items, Remove Items
- **Timeout:** Auto-approve after 4 hours

### Confidence Thresholds

- **confidence_score < 0.6:** Flag for manual review (do not auto-create action items)
- **confidence_score 0.6-0.8:** Create action items, require approval before sync
- **confidence_score > 0.8:** Auto-create and sync action items

## Monitoring & Observability

### Metrics

1. **Processing Time**
   - p50, p95, p99 transcript processing duration
   - Alert: p95 > 30 seconds

2. **Extraction Quality**
   - Average confidence_score per day
   - Alert: confidence < 0.7 for >20% of transcripts

3. **Action Item Creation Rate**
   - Items created per transcript (avg)
   - Alert: Sudden drop (< 50% of baseline)

4. **Handoff Rate**
   - % of transcripts triggering Proposal Agent handoff
   - Alert: Rate < 10% (may indicate low lead quality)

### Logging

```python
# Key log events
logger.info("Processing transcript", extra={"transcript_id": "...", "lead_id": "..."})
logger.info("Extracted insights", extra={"sentiment": "...", "likelihood": 0.85})
logger.info("Created action items", extra={"count": 5})
logger.info("Handed off to Proposal Creation", extra={"task_id": "..."})
logger.error("Failed to parse Claude JSON", extra={"content": "..."})
```

## Performance Considerations

1. **Transcript Length:** Max 50,000 characters (~2 hour call). Longer transcripts split into chunks.
2. **Claude API:** Use max_tokens=4000, temperature=0.3 for structured output.
3. **Concurrent Processing:** Max 5 concurrent transcript analyses to avoid Claude rate limits.
4. **Database Indexes:** Added on lead_id, transcript_id, call_date for fast lookups.

## Future Enhancements

1. **Multi-speaker Sentiment:** Track sentiment per speaker for coaching insights.
2. **Competitive Mentions:** Flag when competitors are mentioned.
3. **Talk-to-Listen Ratio:** Calculate sales rep talk time vs prospect talk time.
4. **Custom Extraction Templates:** Allow custom fields per industry/use case.
5. **Transcript Search:** Full-text search across all transcripts.
