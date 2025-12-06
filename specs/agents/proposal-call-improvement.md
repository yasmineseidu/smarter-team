# Call Improvement Agent - Technical Specification

**Agent Category:** Proposal & Closing
**Priority:** Phase 3 - Closing & Proposals
**Version:** 1.0.0
**Last Updated:** 2025-12-05
**Refined From:** plan/agents/proposal-call-improvement.md

## Overview

The Call Improvement Agent analyzes sales call transcripts to provide coaching insights and track performance improvement over time. It evaluates call quality based on talk time ratios, question quality, objection handling effectiveness, and closing ability. The agent generates actionable coaching suggestions and maintains historical performance trends to help sales teams improve their skills.

## Dependencies

### Upstream Agents
- **Call Transcript Processor Agent**: Provides analyzed transcripts with insights and metadata
- **Meeting Scheduler Agent**: Provides meeting context and attendee information

### Downstream Agents
- **Response Check-in Agent**: Receives coaching reminders for follow-up
- **Sales Agent**: Receives real-time coaching alerts (future enhancement)

### Third-Party Integrations
- **Anthropic Claude**: AI analysis for coaching insight extraction
- **Internal Database**: Stores call scores and improvement suggestions
- **Email Service**: Sends weekly improvement reports

## Data Models

### Database Tables

#### call_scores
```sql
CREATE TABLE call_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID REFERENCES call_transcripts(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id),
    meeting_id UUID REFERENCES meetings(id),

    -- Overall Score (0-100)
    total_score INTEGER NOT NULL CHECK (total_score >= 0 AND total_score <= 100),
    grade VARCHAR(2) NOT NULL, -- A+, A, B+, B, C+, C, D, F

    -- Score Breakdown
    talk_time_score INTEGER NOT NULL CHECK (talk_time_score >= 0 AND talk_time_score <= 25),
    question_score INTEGER NOT NULL CHECK (question_score >= 0 AND question_score <= 25),
    objection_score INTEGER NOT NULL CHECK (objection_score >= 0 AND objection_score <= 25),
    next_steps_score INTEGER NOT NULL CHECK (next_steps_score >= 0 AND next_steps_score <= 25),

    -- Detailed Metrics
    talk_time_ratio DECIMAL(5,2) NOT NULL, -- Percentage (0.00-100.00)
    question_count INTEGER DEFAULT 0,
    open_ended_questions INTEGER DEFAULT 0,
    discovery_questions INTEGER DEFAULT 0,
    pain_focused_questions INTEGER DEFAULT 0,
    objections_handled INTEGER DEFAULT 0,
    objections_resolved INTEGER DEFAULT 0,
    closing_attempts INTEGER DEFAULT 0,
    next_steps_defined BOOLEAN DEFAULT FALSE,
    next_steps_agreed BOOLEAN DEFAULT FALSE,
    next_steps_scheduled BOOLEAN DEFAULT FALSE,

    -- Metadata
    call_duration_seconds INTEGER NOT NULL,
    speaker_count INTEGER NOT NULL DEFAULT 2,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_version VARCHAR(50),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Trend Analysis
    running_average_score DECIMAL(5,2), -- Last 10 calls average
    improvement_trend VARCHAR(20) CHECK (improvement_trend IN ('improving', 'stable', 'declining')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_call_scores_transcript_id ON call_scores(transcript_id);
CREATE INDEX idx_call_scores_lead_id ON call_scores(lead_id);
CREATE INDEX idx_call_scores_meeting_id ON call_scores(meeting_id);
CREATE INDEX idx_call_scores_analyzed_at ON call_scores(analyzed_at DESC);
CREATE INDEX idx_call_scores_total_score ON call_scores(total_score);
```

#### improvement_suggestions
```sql
CREATE TABLE improvement_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_score_id UUID REFERENCES call_scores(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id),

    -- Suggestion Details
    category VARCHAR(50) NOT NULL, -- 'talk_time', 'questioning', 'objections', 'closing', 'general'
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('critical', 'high', 'normal', 'low')),
    title VARCHAR(200) NOT NULL,
    suggestion TEXT NOT NULL,

    -- Context
    specific_moment VARCHAR(1000), -- Timestamp or quote from transcript
    current_behavior VARCHAR(500),
    recommended_behavior VARCHAR(500),

    -- Example
    example_phrase VARCHAR(500), -- What to say instead
    why_it_works VARCHAR(500), -- Psychology behind the suggestion

    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'acknowledged', 'practicing', 'mastered')),
    acknowledged_at TIMESTAMP WITH TIME ZONE,

    -- Effectiveness Tracking
    follow_up_score_id UUID REFERENCES call_scores(id), -- Next call to check improvement
    improvement_observed BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_improvement_suggestions_call_score_id ON improvement_suggestions(call_score_id);
CREATE INDEX idx_improvement_suggestions_lead_id ON improvement_suggestions(lead_id);
CREATE INDEX idx_improvement_suggestions_category ON improvement_suggestions(category);
CREATE INDEX idx_improvement_suggestions_priority ON improvement_suggestions(priority);
CREATE INDEX idx_improvement_suggestions_status ON improvement_suggestions(status);
```

#### coaching_sessions
```sql
CREATE TABLE coaching_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) NOT NULL,

    -- Session Details
    session_date DATE NOT NULL,
    call_count_reviewed INTEGER NOT NULL DEFAULT 0,
    average_score DECIMAL(5,2),
    previous_average DECIMAL(5,2),
    score_change DECIMAL(5,2),

    -- Key Areas
    strengths JSONB DEFAULT '[]', -- Array of strength descriptions
    focus_areas JSONB DEFAULT '[]', -- Array of improvement areas

    -- Top Suggestions
    top_suggestions JSONB DEFAULT '[]', -- Array of suggestion IDs with titles

    -- Engagement
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    email_opened BOOLEAN DEFAULT FALSE,
    email_opened_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(lead_id, session_date)
);

CREATE INDEX idx_coaching_sessions_lead_id ON coaching_sessions(lead_id);
CREATE INDEX idx_coaching_sessions_session_date ON coaching_sessions(session_date DESC);
```

### Pydantic Models

```python
from datetime import datetime, date
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TalkTimeAnalysis(BaseModel):
    """Talk time analysis results."""
    ratio: Decimal = Field(..., ge=0, le=100, description="Sales rep talk time percentage")
    score: int = Field(..., ge=0, le=25, description="Talk time score (0-25)")
    feedback: str = Field(..., description="Specific feedback on talk time")


class QuestionAnalysis(BaseModel):
    """Question quality analysis."""
    total_questions: int = Field(..., ge=0)
    open_ended: int = Field(..., ge=0)
    discovery: int = Field(..., ge=0)
    pain_focused: int = Field(..., ge=0)
    score: int = Field(..., ge=0, le=25, description="Question score (0-25)")
    feedback: str = Field(..., description="Feedback on questioning technique")


class ObjectionAnalysis(BaseModel):
    """Objection handling analysis."""
    total_objections: int = Field(..., ge=0)
    acknowledged: int = Field(..., ge=0)
    clarifying_questions: int = Field(..., ge=0)
    effective_responses: int = Field(..., ge=0)
    resolved: int = Field(..., ge=0)
    score: int = Field(..., ge=0, le=25, description="Objection handling score (0-25)")
    feedback: str = Field(..., description="Feedback on objection handling")


class ClosingAnalysis(BaseModel):
    """Closing and next steps analysis."""
    closing_attempts: int = Field(..., ge=0)
    next_step_defined: bool
    next_step_scheduled: bool
    both_parties_agreed: bool
    score: int = Field(..., ge=0, le=25, description="Closing score (0-25)")
    feedback: str = Field(..., description="Feedback on closing effectiveness")


class CallScoreExtraction(BaseModel):
    """Complete call score analysis."""

    -- Overall Assessment
    total_score: int = Field(..., ge=0, le=100, description="Total score out of 100")
    grade: str = Field(..., pattern="^[A-F][+]?|F$", description="Letter grade")
    confidence_score: Decimal = Field(..., ge=0, le=1, description="Analysis confidence")

    -- Detailed Analyses
    talk_time: TalkTimeAnalysis
    questioning: QuestionAnalysis
    objections: ObjectionAnalysis
    closing: ClosingAnalysis

    -- Summary
    strengths: list[str] = Field(default_factory=list, max_items=5)
    improvement_areas: list[str] = Field(default_factory=list, max_items=5)

    -- Specific Moments
    effective_moments: list[dict] = Field(default_factory=list, max_items=10)
    improvement_moments: list[dict] = Field(default_factory=list, max_items=10)

    -- Recommendations
    suggestions: list[dict] = Field(default_factory=list, max_items=10)
    practice_exercises: list[str] = Field(default_factory=list, max_items=5)

    @field_validator("grade", mode="before")
    @classmethod
    def calculate_grade(cls, v: Any, values: Any) -> str:
        """Calculate letter grade from total_score."""
        if isinstance(v, str):
            return v
        score = values.get("total_score", 0)
        if score >= 97:
            return "A+"
        elif score >= 93:
            return "A"
        elif score >= 90:
            return "A-"
        elif score >= 87:
            return "B+"
        elif score >= 83:
            return "B"
        elif score >= 80:
            return "B-"
        elif score >= 77:
            return "C+"
        elif score >= 73:
            return "C"
        elif score >= 70:
            return "C-"
        elif score >= 67:
            return "D+"
        elif score >= 60:
            return "D"
        else:
            return "F"


class ImprovementSuggestionCreate(BaseModel):
    """Improvement suggestion to be created."""
    category: str = Field(..., pattern="^(talk_time|questioning|objections|closing|general)$")
    priority: str = Field(..., pattern="^(critical|high|normal|low)$")
    title: str = Field(..., min_length=5, max_length=200)
    suggestion: str = Field(..., min_length=10, max_length=1000)
    specific_moment: str | None = Field(None, max_length=1000)
    current_behavior: str | None = Field(None, max_length=500)
    recommended_behavior: str | None = Field(None, max_length=500)
    example_phrase: str | None = Field(None, max_length=500)
    why_it_works: str | None = Field(None, max_length=500)


class CoachingReportData(BaseModel):
    """Data for weekly coaching report."""
    lead_id: str
    period_start: date
    period_end: date
    calls_reviewed: int
    average_score: Decimal
    score_change: Decimal
    trend: str = Field(..., pattern="^(improving|stable|declining)$")
    top_strengths: list[str]
    focus_areas: list[str]
    top_suggestions: list[dict]
    practice_plan: list[str]
```

## Agent Implementation

### System Prompt

```python
CALL_IMPROVEMENT_SYSTEM_PROMPT = """You are an expert sales coach and trainer with 15+ years of experience analyzing sales calls and providing actionable feedback. Your role is to evaluate sales call performance and provide specific, actionable coaching recommendations.

**Your Expertise:**
- Sales methodology (SPIN, Challenger, MEDDIC)
- Question technique and discovery
- Objection handling psychology
- Closing and next step management
- Adult learning and behavior change

**Scoring Criteria (100 points total):**

**1. Talk Time Ratio (25 points)**
- <30%: 25 points (Excellent listening)
- 30-40%: 20 points (Good balance)
- 40-50%: 15 points (Talking too much)
- 50-60%: 10 points (Dominating)
- >60%: 5 points (Not listening)

**2. Question Quality (25 points)**
- Open-ended questions: +5 points each (max 15)
- Discovery questions about situation/pain: +5 points
- Pain-focused questions: +5 points
- Note: Rate questions by depth and insight generated

**3. Objection Handling (25 points)**
- Acknowledge objection: +5 points
- Ask clarifying question: +5 points
- Provide relevant response: +10 points
- Confirm resolution: +5 points
- Score per objection, average across all objections

**4. Next Steps & Closing (25 points)**
- Clear next step defined: +10 points
- Specific date/time set: +10 points
- Both parties agreed: +5 points

**Analysis Guidelines:**

**Talk Time Analysis:**
- Calculate exact percentage of sales rep talk time
- Consider context (demo calls may have more talk)
- Look for patterns of interruption vs. thoughtful pauses
- Identify if rep is presenting vs. having conversation

**Question Assessment:**
- Count total questions asked
- Categorize by type (open/closed, discovery, pain-focused)
- Evaluate question quality based on responses generated
- Look for question progression and strategy

**Objection Evaluation:**
- Identify all objections raised (explicit and implicit)
- Assess response quality and relevance
- Check if objection was truly resolved or just bypassed
- Note psychological techniques used (empathy, reframing)

**Closing Review:**
- Verify next steps are clear and specific
- Check if both parties committed to action items
- Assess closing confidence and professionalism
- Note if closing attempt matched call context

**Coaching Philosophy:**
- Be specific and actionable with feedback
- Explain psychology behind recommendations
- Provide example phrases and scripts
- Focus on 1-2 key areas per call to avoid overwhelm
- Reinforce positive behaviors, don't just criticize

**Output Requirements:**
Return valid JSON matching the CallScoreExtraction schema. Include:
- Accurate scoring with detailed breakdowns
- 3-5 specific strengths to reinforce
- 2-3 priority improvement areas with examples
- Exact moments from transcript with timestamps
- Practice exercises for skill development
- psychologically-informed coaching tips

Remember: Your goal is to build confidence while driving improvement. Balance constructive criticism with positive reinforcement."""
```

### Tool Definitions

```python
from typing import Any


async def calculate_call_score(
    transcript_text: str,
    speaker_labels: list[str] | None = None,
) -> dict[str, Any]:
    """
    Analyze sales call transcript and calculate performance score.

    Args:
        transcript_text: Full call transcript with speaker labels
        speaker_labels: Optional list of speaker identifiers

    Returns:
        CallScoreExtraction with detailed analysis and scores
    """
    # Will use Claude API with the system prompt above
    pass


async def store_call_score(
    transcript_id: str,
    lead_id: str | None,
    meeting_id: str | None,
    score_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Store call score analysis in database.

    Args:
        transcript_id: UUID of transcript
        lead_id: UUID of lead (optional)
        meeting_id: UUID of meeting (optional)
        score_data: CallScoreExtraction data

    Returns:
        Created call_score record with ID
    """
    # Insert into call_scores table
    # Calculate running average and trend
    pass


async def create_improvement_suggestions(
    call_score_id: str,
    lead_id: str | None,
    suggestions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Store improvement suggestions from call analysis.

    Args:
        call_score_id: UUID of call score record
        lead_id: UUID of lead (optional)
        suggestions: List of suggestions from analysis

    Returns:
        Created improvement_suggestion records
    """
    # Bulk insert into improvement_suggestions table
    pass


async def generate_weekly_coaching_report(
    lead_id: str,
    report_date: date,
) -> dict[str, Any]:
    """
    Generate weekly coaching report with trends and recommendations.

    Args:
        lead_id: UUID of sales rep/lead
        report_date: Date for report (typically week end)

    Returns:
        Coaching report data with trends and top suggestions
    """
    # Analyze last 7 days of calls
    # Calculate trends and improvement areas
    # Generate focused practice plan
    pass


async def send_coaching_email(
    lead_id: str,
    report_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Send coaching report via email.

    Args:
        lead_id: UUID of sales rep/lead
        report_data: Coaching report data

    Returns:
        Email delivery status and details
    """
    # Use email service integration
    pass


async def track_improvement_progress(
    lead_id: str,
    suggestion_id: str,
    new_call_score_id: str,
) -> dict[str, Any]:
    """
    Track if improvement was observed in subsequent calls.

    Args:
        lead_id: UUID of sales rep/lead
        suggestion_id: UUID of suggestion being tracked
        new_call_score_id: UUID of recent call to check

    Returns:
        Improvement assessment and updated suggestion status
    """
    # Compare call performance to previous
    # Check if targeted skill improved
    pass
```

### Agent Class

```python
"""Call Improvement Agent."""

import json
from datetime import date, datetime
from typing import Any
from uuid import UUID

from anthropic import AsyncAnthropic
from pydantic import ValidationError

from src.agents.base_agent import BaseAgent
from src.config import Settings, get_agent_logger


class CallImprovementAgent(BaseAgent):
    """
    Analyzes sales calls to provide coaching and track improvement.

    Evaluates call quality across multiple dimensions,
    generates actionable feedback, and maintains
    performance trends over time.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the Call Improvement Agent.

        Args:
            settings: Application settings with API keys
        """
        super().__init__(
            name="call_improvement",
            description="Analyzes sales calls and provides coaching insights",
        )
        self.settings = settings
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Register tools
        self.register_tool(
            calculate_call_score,
            "calculate_call_score",
            "Analyze transcript and calculate performance score",
        )
        self.register_tool(
            store_call_score,
            "store_call_score",
            "Store call score in database",
        )
        self.register_tool(
            create_improvement_suggestions,
            "create_improvement_suggestions",
            "Store improvement suggestions",
        )
        self.register_tool(
            generate_weekly_coaching_report,
            "generate_weekly_coaching_report",
            "Generate weekly coaching report",
        )
        self.register_tool(
            send_coaching_email,
            "send_coaching_email",
            "Send coaching report via email",
        )
        self.register_tool(
            track_improvement_progress,
            "track_improvement_progress",
            "Track improvement over time",
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for call analysis."""
        return CALL_IMPROVEMENT_SYSTEM_PROMPT

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process incoming call improvement task.

        Args:
            task: Task payload with type and parameters

        Returns:
            Processing result with scores and suggestions

        Raises:
            ValueError: If required parameters missing
            ValidationError: If AI output doesn't match schema
        """
        task_type = task.get("type")

        if task_type == "analyze_call":
            return await self._analyze_call(task)
        elif task_type == "generate_weekly_report":
            return await self._generate_weekly_report(task)
        elif task_type == "track_improvement":
            return await self._track_improvement(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _analyze_call(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a sales call and provide coaching insights.

        Steps:
        1. Extract transcript and metadata
        2. Analyze with Claude API
        3. Store scores in database
        4. Create improvement suggestions
        5. Update trends and averages
        6. Trigger weekly report if Friday

        Args:
            task: Task with transcript_id, transcript_text, lead_id, meeting_id

        Returns:
            Analysis result with scores and suggestions
        """
        transcript_id = task.get("transcript_id")
        transcript_text = task.get("transcript_text")
        lead_id = task.get("lead_id")
        meeting_id = task.get("meeting_id")
        speaker_labels = task.get("speaker_labels", ["Sales Rep", "Prospect"])

        if not transcript_id or not transcript_text:
            raise ValueError("transcript_id and transcript_text are required")

        start_time = datetime.utcnow()
        self.logger.info(
            "Analyzing call for coaching",
            extra={
                "transcript_id": transcript_id,
                "lead_id": lead_id,
                "transcript_length": len(transcript_text),
            },
        )

        try:
            # Step 1: Analyze transcript with Claude
            extraction = await self._extract_call_score(
                transcript_text, speaker_labels
            )

            # Step 2: Store score in database
            score_record = await store_call_score(
                transcript_id=transcript_id,
                lead_id=lead_id,
                meeting_id=meeting_id,
                score_data=extraction.model_dump(),
            )

            # Step 3: Create improvement suggestions
            suggestions = await create_improvement_suggestions(
                call_score_id=score_record["id"],
                lead_id=lead_id,
                suggestions=extraction.suggestions,
            )

            # Step 4: Check if weekly report needed
            await self._check_weekly_report(lead_id)

            # Step 5: Log completion
            processing_duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            self.log_action(
                "call.analyzed",
                {
                    "transcript_id": transcript_id,
                    "score_id": score_record["id"],
                    "total_score": extraction.total_score,
                    "grade": extraction.grade,
                    "suggestions_count": len(suggestions),
                    "processing_duration_ms": processing_duration_ms,
                },
            )

            return {
                "status": "completed",
                "transcript_id": transcript_id,
                "score_id": score_record["id"],
                "analysis": extraction.model_dump(),
                "suggestions_created": len(suggestions),
                "processing_duration_ms": processing_duration_ms,
            }

        except ValidationError as e:
            self.logger.error(
                "Validation error during call analysis",
                extra={"transcript_id": transcript_id, "error": str(e)},
            )
            raise
        except Exception as e:
            self.logger.error(
                "Error analyzing call",
                extra={"transcript_id": transcript_id, "error": str(e)},
            )
            raise

    async def _extract_call_score(
        self,
        transcript_text: str,
        speaker_labels: list[str],
    ) -> CallScoreExtraction:
        """
        Extract call score analysis using Claude.

        Args:
            transcript_text: Full call transcript
            speaker_labels: List of speaker identifiers

        Returns:
            Validated CallScoreExtraction
        """
        user_prompt = f"""Analyze this sales call transcript and provide coaching evaluation.

Speaker Labels: {", ".join(speaker_labels)}

Transcript:
{transcript_text}

Return ONLY valid JSON matching the CallScoreExtraction schema. No markdown, no extra text."""

        response = await self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.3,  # Lower temperature for consistent scoring
        )

        content = response.content[0].text

        # Parse JSON from Claude response
        try:
            extraction_data = json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(
                "Failed to parse Claude JSON",
                extra={"content": content[:500]}
            )
            raise ValueError(f"Claude returned invalid JSON: {e}")

        # Validate against Pydantic schema
        extraction = CallScoreExtraction(**extraction_data)

        self.logger.info(
            "Extracted call score analysis",
            extra={
                "total_score": extraction.total_score,
                "grade": extraction.grade,
                "talk_time_ratio": float(extraction.talk_time.ratio),
                "question_count": extraction.questioning.total_questions,
                "objections_handled": extraction.objections.total_objections,
            },
        )

        return extraction

    async def _check_weekly_report(self, lead_id: str) -> None:
        """
        Check if weekly report should be generated and sent.

        Args:
            lead_id: Sales rep UUID to check
        """
        if not lead_id:
            return

        # Check if today is Friday and report not sent
        today = date.today()
        if today.weekday() == 4:  # Friday
            # Check if report already sent this week
            existing = await self._check_coaching_report_exists(lead_id, today)
            if not existing:
                # Generate and send report
                report_data = await generate_weekly_coaching_report(lead_id, today)
                await send_coaching_email(lead_id, report_data)

                self.logger.info(
                    "Weekly coaching report sent",
                    extra={"lead_id": lead_id, "report_date": today}
                )

    async def _check_coaching_report_exists(self, lead_id: str, report_date: date) -> bool:
        """Check if coaching report already exists for the week."""
        # Query coaching_sessions table
        pass

    async def _generate_weekly_report(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Generate weekly coaching report.

        Args:
            task: Task with lead_id and report_date

        Returns:
            Generated coaching report
        """
        lead_id = task.get("lead_id")
        report_date = task.get("report_date", date.today())

        if not lead_id:
            raise ValueError("lead_id is required for weekly report")

        report_data = await generate_weekly_coaching_report(lead_id, report_date)

        self.logger.info(
            "Generated weekly coaching report",
            extra={
                "lead_id": lead_id,
                "report_date": report_date,
                "calls_reviewed": report_data["calls_reviewed"],
                "average_score": float(report_data["average_score"]),
            }
        )

        return {
            "status": "completed",
            "lead_id": lead_id,
            "report_date": report_date,
            "report": report_data,
        }

    async def _track_improvement(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Track if improvement was made based on coaching.

        Args:
            task: Task with lead_id, suggestion_id, new_call_score_id

        Returns:
            Improvement tracking result
        """
        lead_id = task.get("lead_id")
        suggestion_id = task.get("suggestion_id")
        new_call_score_id = task.get("new_call_score_id")

        if not all([lead_id, suggestion_id, new_call_score_id]):
            raise ValueError("lead_id, suggestion_id, and new_call_score_id are required")

        result = await track_improvement_progress(
            lead_id, suggestion_id, new_call_score_id
        )

        self.logger.info(
            "Tracked improvement progress",
            extra={
                "lead_id": lead_id,
                "suggestion_id": suggestion_id,
                "improvement_observed": result["improvement_observed"],
            }
        )

        return {
            "status": "completed",
            "lead_id": lead_id,
            "suggestion_id": suggestion_id,
            "result": result,
        }
```

## Error Handling

### Error Scenarios

1. **Invalid Transcript Format**
   - Response: 400 Bad Request
   - Action: Log format issues, return specific error message

2. **Missing Speaker Labels**
   - Response: Default to ["Speaker 1", "Speaker 2"]
   - Action: Log warning, proceed with analysis

3. **Claude API Failure**
   - Response: Retry up to 3 times with exponential backoff
   - Action: Store raw transcript for manual review if all retries fail

4. **Invalid JSON from Claude**
   - Response: Retry with temperature=0.1
   - Action: Log error, use fallback scoring if persistent

5. **Database Errors**
   - Response: 500 Internal Server Error
   - Action: Log full error context, alert monitoring

6. **Score Out of Range**
   - Response: Log warning, clamp to valid range
   - Action: Continue processing with adjusted score

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def _extract_call_score_with_retry(
    self,
    transcript_text: str,
    speaker_labels: list[str],
) -> CallScoreExtraction:
    """Extract call score with automatic retry on failure."""
    return await self._extract_call_score(transcript_text, speaker_labels)
```

## Testing Requirements

### Coverage Target: >85%

### Unit Tests

**File:** `__tests__/unit/agents/call_improvement/test_agent.py`

1. **Initialization**
   - Agent has correct name and description
   - All 6 tools registered
   - System prompt is set
   - Anthropic client initialized

2. **Score Calculation**
   - Valid transcript produces valid CallScoreExtraction
   - Talk time ratio calculated correctly
   - Question counting works for various types
   - Objection handling scored appropriately
   - Closing next steps evaluated correctly

3. **Grade Calculation**
   - Score 97+ returns "A+"
   - Score 93-96 returns "A"
   - Score 0-59 returns "F"
   - Grade validates with regex pattern

4. **Improvement Suggestions**
   - Creates suggestions for each category
   - Priority levels assigned correctly
   - Specific moments captured from transcript
   - Example phrases provided

5. **Trend Analysis**
   - Running average calculated correctly
   - Trend detection works (improving/stable/declining)
   - Handles first call edge case

6. **Error Handling**
   - Handles missing transcript gracefully
   - Validates against Pydantic schema
   - Retries on Claude API failures
   - Logs errors with context

### Integration Tests

**File:** `__tests__/integration/test_call_improvement_workflow.py`

1. **End-to-End Analysis**
   - Transcript → Analysis → Score Storage → Suggestions
   - Weekly report generation on Friday
   - Email sending for coaching reports

2. **Agent Handoff**
   - Receives handoff from Transcript Processor
   - Triggers analysis with correct data

3. **Improvement Tracking**
   - Tracks suggestions across multiple calls
   - Updates suggestion status based on improvement

### Fixtures

**File:** `__tests__/fixtures/call_improvement_fixtures.py`

```python
import pytest
from decimal import Decimal


@pytest.fixture
def good_transcript() -> str:
    """High-quality sales call transcript."""
    return """
    Sales Rep: Thanks for your time today. To start, could you tell me about your current challenges with data management?

    Prospect: We're struggling with scattered spreadsheets. It takes our team hours to consolidate reports each month.

    Sales Rep: That sounds frustrating. How many hours are we talking about exactly?

    Prospect: Probably 20-30 hours per month across the team. And we still make mistakes.

    Sales Rep: I understand. What's the impact of those mistakes?

    Prospect: We've made wrong decisions based on bad data twice this quarter.

    Sales Rep: That's significant. If we could eliminate that manual work and ensure accuracy, what would that mean for your team?

    Prospect: It would be game-changing. We could focus on analysis instead of data wrangling.

    Sales Rep: Let's schedule a demo for Thursday at 2 PM to show you exactly how we solve this. Would that work?

    Prospect: Yes, Thursday at 2 PM sounds perfect.
    """


@pytest.fixture
def poor_transcript() -> str:
    """Low-quality sales call transcript."""
    return """
    Sales Rep: Let me tell you about our amazing product. It has features A, B, C, D, and E.
    [continues talking for 10 minutes straight]

    Prospect: I have a question about pricing?

    Sales Rep: I'll get to that. Let me also mention features F, G, and H. Our customers love these features.

    Prospect: Actually, we need to go soon.

    Sales Rep: Just give me 5 more minutes to show you the dashboard. It's really cool.

    Prospect: Maybe we should schedule another call.

    Sales Rep: Or we could decide now. We have a special offer if you sign today.
    """


@pytest.fixture
def expected_good_score() -> dict:
    """Expected analysis for good transcript."""
    return {
        "total_score": 92,
        "grade": "A-",
        "talk_time": {"ratio": 35.0, "score": 20},
        "questioning": {"total_questions": 5, "open_ended": 4, "score": 25},
        "objections": {"total_objections": 0, "score": 25},
        "closing": {"next_step_defined": True, "next_step_scheduled": True, "score": 22},
        "strengths": ["Excellent discovery questions", "Listens more than talks"],
        "improvement_areas": ["None significant - maintain current approach"],
    }


@pytest.fixture
def expected_poor_score() -> dict:
    """Expected analysis for poor transcript."""
    return {
        "total_score": 35,
        "grade": "F",
        "talk_time": {"ratio": 85.0, "score": 5},
        "questioning": {"total_questions": 0, "open_ended": 0, "score": 0},
        "objections": {"total_objections": 2, "acknowledged": 0, "score": 5},
        "closing": {"next_step_defined": False, "score": 25},
        "strengths": ["Persistent"],
        "improvement_areas": [
            "Talk time ratio (85% - prospect couldn't speak)",
            "Question technique (no discovery questions)",
            "Objection handling (ignored prospect needs)",
        ],
    }
```

## Human-in-the-Loop

### Review Gates

**Gate 1: Critical Suggestions**
- **Trigger:** When 'critical' priority suggestions generated
- **Reviewer:** Sales manager
- **Review UI:** Dashboard showing suggestion with transcript context
- **Actions:** Approve, Modify, Dismiss, Schedule coaching session
- **Timeout:** Auto-approve after 24 hours

**Gate 2: Grade F Alerts**
- **Trigger:** When call receives grade F
- **Reviewer:** Sales director
- **Review UI:** Full call analysis with trends
- **Actions:** Mandatory coaching session, Additional training, Reassign lead
- **Timeout:** Must review within 4 hours

### Confidence Thresholds

- **confidence_score < 0.6:** Flag for manual review (suggest manager review)
- **confidence_score 0.6-0.8:** Process but note lower confidence
- **confidence_score > 0.8:** Full automated processing

## Monitoring & Observability

### Metrics

1. **Analysis Quality**
   - Average confidence_score per day
   - Alert: confidence < 0.7 for >20% of calls
   - Score distribution tracking

2. **Improvement Tracking**
   - % of suggestions marked as "mastered"
   - Average time to mastery
   - Score improvement rate per rep

3. **Engagement Metrics**
   - Weekly report open rate
   - Click-through on practice exercises
   - Coaching session requests

4. **Performance Metrics**
   - Processing time per call (p50, p95)
   - Error rate for analysis failures
   - Database query performance

### Logging

```python
# Key log events
logger.info("Analyzing call for coaching", extra={"transcript_id": "...", "lead_id": "..."})
logger.info("Extracted call score", extra={"total_score": 85, "grade": "B"})
logger.info("Created improvement suggestions", extra={"count": 5, "priority": "high"})
logger.info("Weekly coaching report sent", extra={"lead_id": "...", "report_date": "..."}).
logger.error("Failed to parse Claude JSON", extra={"content": "..."})
```

## Performance Considerations

1. **Transcript Length:** Max 20,000 characters (~1.5 hour call)
2. **Claude API:** Use max_tokens=4000, temperature=0.3 for consistent scoring
3. **Batch Processing:** Weekly reports run in batches of 50 reps
4. **Database Indexes:** Optimized for trend analysis queries
5. **Caching:** Cache rep averages and trends for 1 hour

## Future Enhancements

1. **Real-time Coaching:** Live call analysis with whispered suggestions
2. **Video Analysis:** Include body language and presentation skills
3. **Peer Comparison:** Anonymous benchmarking across team
4. **Custom Scorecards:** Industry-specific scoring criteria
5. **Gamification:** Achievements and leaderboards for improvement
6. **Integration with CRMs:** Sync scores to Salesforce, HubSpot
7. **Voice Analysis:** Tone, pace, and fillers detection
