# System Response Outcome Tracker Agent - Production Specification

## Overview

**Category**: System & Administration
**Priority**: Phase 1 - Critical for Learning System
**Agent Name**: `system_response_outcome_tracker`
**Purpose**: Track every agent response and measure eventual outcomes to identify what works and continuously improve system performance through data-driven insights.

**Mission**: Transform every response into a learning opportunity by tracking outcomes, identifying success patterns, and feeding actionable insights back to all generating agents. The foundation of the learning system.

**Dependencies**:
- All response-generating agents (cold_email_copywriter, response_email_handler, etc.)
- Email service providers (Instantly, SendGrid) - webhook integrations
- Calendar systems (Cal.com) - meeting booking webhooks
- CRM systems - deal closure events
- system-learning-feedback - receives aggregated success data
- system-agent-performance-analyst - receives performance metrics
- system-knowledge-base-manager - receives KB effectiveness data
- system-correction-approval-orchestrator - provides A/B test validation

---

## System Prompt

```
You are the System Response Outcome Tracker Agent for Smarter Team, the measurement foundation that powers the entire learning system.

Your mission is to track EVERY agent response, measure its eventual outcomes, calculate success scores, and identify patterns that separate high-performing responses from underperforming ones.

**Core Responsibilities:**
1. Log every agent response with complete context (agent, type, content, metadata, A/B test group)
2. Track outcomes through the complete funnel: sent → opened → clicked → replied → meeting → deal
3. Calculate 0-10 success scores based on weighted outcomes
4. Detect success patterns across agents, content types, industries, and contexts
5. Provide real-time effectiveness metrics and performance dashboards
6. Validate A/B test results with statistical significance testing
7. Feed insights to the learning system for continuous improvement

**Measurement Capabilities:**
- Multi-stage funnel tracking (open → click → reply → positive reply → meeting → deal)
- Attribution modeling (which response drove which outcome)
- Time-to-outcome analysis (how long until conversion)
- Success pattern detection (what content/timing/approach works)
- A/B test statistical validation (chi-square, 95% confidence)
- Cross-agent performance comparison
- Industry/persona/context-specific effectiveness

**Success Score Calculation (0-10 scale):**
- Base: 1 point for successfully sending
- Email Opened: +3 points (30% weight)
- Link Clicked: +2 points (20% weight)
- Reply Received: +3 points (30% weight)
- Positive Reply: +1 bonus point
- Meeting Booked: +4 points (40% weight)
- Deal Closed: +5 points (50% weight)
- Maximum: 10 points (cap at 10 even if multiple outcomes)

**Outcome Attribution Rules:**
- Primary attribution: Response that directly triggered outcome
- Multi-touch: Track entire conversation sequence
- Time window: Outcomes within 30 days of response
- Tie-breaking: Most recent response gets credit

**Pattern Detection Thresholds:**
- Minimum sample size: 10 responses for pattern detection
- Statistical significance: 95% confidence (p < 0.05)
- Minimum improvement: 20% better than baseline
- Context consistency: Same industry/persona/lead stage

**Webhook Processing:**
- Real-time processing for all email events (open, click, reply)
- Idempotent handling (duplicate webhook protection)
- Sentiment analysis on reply content using Claude
- Automatic success score recalculation on new outcomes
- Pattern re-evaluation on significant metric changes

**Behavioral Guidelines:**
- Track everything, analyze intelligently
- Provide real-time metrics for operational dashboards
- Use statistical rigor for pattern detection (avoid false positives)
- Consider context dimensions (industry, company size, persona, lead stage)
- Identify underperforming patterns as aggressively as successful ones
- Validate A/B tests thoroughly before declaring winners
- Feed insights to learning system for prompt/template improvements

**Decision Making:**
- Pattern Significance: Require minimum 10 samples, 95% confidence
- A/B Test Winner: 95% confidence, minimum 100 samples per variant
- Success Threshold: >7.0 score = high-performing, <4.0 = underperforming
- Outlier Handling: Remove statistical outliers (>3 standard deviations)
- Missing Data: Handle gracefully, mark outcomes as 'pending' until confirmed

**Communication Style:**
- Data-driven and quantitative
- Clear success/failure indicators
- Actionable insights with specific recommendations
- Statistical evidence for all claims
- Visual-friendly data structures (tables, charts)

You have access to tools for logging responses, tracking outcomes via webhooks, calculating success scores, detecting patterns, generating effectiveness reports, and validating A/B tests. Use these tools systematically to measure everything and identify what drives success.
```

---

## Agent Implementation

### Class Definition

```python
from typing import Any, Dict, List, Optional, Tuple, Literal
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json
import asyncio
from collections import defaultdict, Counter
from decimal import Decimal

from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger


class OutcomeType(str, Enum):
    """Types of response outcomes to track."""
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    EMAIL_REPLIED = "email_replied"
    MEETING_BOOKED = "meeting_booked"
    DEAL_CLOSED = "deal_closed"
    POSITIVE_REPLY = "positive_reply"
    NEGATIVE_REPLY = "negative_reply"


class SentimentCategory(str, Enum):
    """Sentiment categories for reply analysis."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"


class PatternType(str, Enum):
    """Types of success patterns to detect."""
    OPENING_LINE = "opening_line"
    PERSONALIZATION_TYPE = "personalization_type"
    VALUE_PROPOSITION = "value_proposition"
    CALL_TO_ACTION = "call_to_action"
    TIMING_PATTERN = "timing_pattern"
    LENGTH_PATTERN = "length_pattern"
    INDUSTRY_SPECIFIC = "industry_specific"
    PERSONA_SPECIFIC = "persona_specific"


@dataclass
class ResponseOutcome:
    """Structured data for a single outcome event."""
    outcome_type: OutcomeType
    occurred_at: datetime
    response_id: str
    metadata: Dict[str, Any]


@dataclass
class SuccessPattern:
    """Identified success pattern."""
    pattern_type: PatternType
    description: str
    sample_count: int
    avg_success_score: float
    statistical_significance: float
    context_filter: Dict[str, Any]
    examples: List[str]
    recommendation: str


class ResponseOutcomeTrackerAgent(BaseAgent):
    """
    System Response Outcome Tracker agent for comprehensive response measurement.

    Tracks every agent response through the complete outcome funnel and identifies
    patterns that drive success.
    """

    def __init__(self):
        super().__init__(
            name="system_response_outcome_tracker",
            description="Tracks all agent responses and outcomes for learning"
        )

        # Register tools
        self.register_tool(
            log_response,
            "log_response",
            "Log a new agent response with full metadata"
        )
        self.register_tool(
            track_email_open,
            "track_email_open",
            "Process email open event from webhook"
        )
        self.register_tool(
            track_email_click,
            "track_email_click",
            "Process link click event from webhook"
        )
        self.register_tool(
            track_email_reply,
            "track_email_reply",
            "Process email reply event with sentiment analysis"
        )
        self.register_tool(
            track_meeting_booked,
            "track_meeting_booked",
            "Process meeting booking event"
        )
        self.register_tool(
            track_deal_closed,
            "track_deal_closed",
            "Process deal closure event"
        )
        self.register_tool(
            calculate_success_score,
            "calculate_success_score",
            "Calculate 0-10 success score for a response"
        )
        self.register_tool(
            detect_success_patterns,
            "detect_success_patterns",
            "Identify patterns in high-performing responses"
        )
        self.register_tool(
            generate_effectiveness_report,
            "generate_effectiveness_report",
            "Generate performance report by agent/type/context"
        )
        self.register_tool(
            validate_ab_test,
            "validate_ab_test",
            "Validate A/B test with statistical significance"
        )

    @property
    def system_prompt(self) -> str:
        # Return the full system prompt from above
        return """..."""  # Full prompt from above

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process response tracking tasks.

        Supported task types:
        - log_response: Log new agent response
        - process_webhook: Process outcome webhook
        - calculate_scores: Recalculate success scores
        - detect_patterns: Run pattern detection
        - generate_report: Create effectiveness report
        - validate_test: Validate A/B test results
        """
        task_type = task.get("type")

        if task_type == "log_response":
            return await self._log_response_task(task.get("response_data"))
        elif task_type == "process_webhook":
            return await self._process_webhook(task.get("webhook_data"))
        elif task_type == "calculate_scores":
            return await self._calculate_scores_batch(task.get("lookback_hours", 24))
        elif task_type == "detect_patterns":
            return await self._detect_patterns_task(task.get("filters"))
        elif task_type == "generate_report":
            return await self._generate_report_task(task.get("report_config"))
        elif task_type == "validate_test":
            return await self._validate_test_task(task.get("ab_test_id"))
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _log_response_task(self, response_data: dict) -> dict[str, Any]:
        """Log a new response."""
        # Implementation details
        pass

    async def _process_webhook(self, webhook_data: dict) -> dict[str, Any]:
        """Process incoming webhook event."""
        # Implementation details
        pass

    async def _calculate_scores_batch(self, lookback_hours: int) -> dict[str, Any]:
        """Batch recalculate success scores."""
        # Implementation details
        pass

    async def _detect_patterns_task(self, filters: dict) -> dict[str, Any]:
        """Run pattern detection analysis."""
        # Implementation details
        pass

    async def _generate_report_task(self, config: dict) -> dict[str, Any]:
        """Generate effectiveness report."""
        # Implementation details
        pass

    async def _validate_test_task(self, ab_test_id: str) -> dict[str, Any]:
        """Validate A/B test statistical significance."""
        # Implementation details
        pass
```

---

## Tool Definitions

### 1. log_response

**Purpose**: Log every agent response with full context for tracking

**Parameters**:
```python
{
    "message_id": str,                  # UUID of the message
    "campaign_id": str | None,          # Campaign UUID if applicable
    "lead_id": str,                     # Lead UUID
    "agent_name": str,                  # Name of generating agent
    "agent_version": str,               # Agent version
    "agent_type": str,                  # copywriter, responder, scheduler
    "original_content": str,            # Full response content
    "original_subject": str | None,     # Email subject line
    "prompt_used": str,                 # Prompt that generated response
    "generation_time_ms": int,          # Time to generate response
    "context": dict,                    # Full context data
    "ab_test_group": str | None,        # A, B, control
    "ab_test_id": str | None,           # A/B test UUID
    "corrected_content": str | None,    # Human corrections if any
    "corrected_by": str | None,         # Who made corrections
    "correction_reason": str | None     # Why it was corrected
}
```

**Returns**:
```python
{
    "response_id": str,                 # UUID of tracked response
    "logged_at": str,                   # ISO timestamp
    "initial_success_score": float,     # Initial score (usually 1.0)
    "tracking_status": str,             # active, pending_outcomes
    "context_fingerprint": str          # Hash of context for pattern matching
}
```

**Implementation**:
```python
async def log_response(
    message_id: str,
    campaign_id: str | None,
    lead_id: str,
    agent_name: str,
    agent_version: str,
    agent_type: str,
    original_content: str,
    original_subject: str | None,
    prompt_used: str,
    generation_time_ms: int,
    context: dict,
    ab_test_group: str | None = None,
    ab_test_id: str | None = None,
    corrected_content: str | None = None,
    corrected_by: str | None = None,
    correction_reason: str | None = None
) -> dict[str, Any]:
    """
    Log a new agent response for outcome tracking.

    Creates entry in response_tracking table with initial success score.
    Extracts context fingerprint for pattern matching.
    """
    from sqlalchemy import insert
    from src.database import get_async_session
    from src.models import ResponseTracking
    import hashlib
    import time

    logger = get_agent_logger("response_tracker.log")
    start_time = time.time()

    # Generate context fingerprint for pattern matching
    context_str = json.dumps(context, sort_keys=True)
    context_fingerprint = hashlib.sha256(context_str.encode()).hexdigest()[:16]

    # Initial success score (1 point for sending)
    initial_score = 1.0

    async with get_async_session() as session:
        # Insert response tracking record
        stmt = insert(ResponseTracking).values(
            message_id=message_id,
            campaign_id=campaign_id,
            lead_id=lead_id,
            agent_name=agent_name,
            agent_version=agent_version,
            agent_type=agent_type,
            original_content=original_content,
            original_subject=original_subject,
            generated_at=datetime.utcnow(),
            generation_time_ms=generation_time_ms,
            prompt_used=prompt_used,
            corrected_content=corrected_content,
            corrected_by=corrected_by,
            corrected_at=datetime.utcnow() if corrected_by else None,
            correction_reason=correction_reason,
            ab_test_group=ab_test_group,
            ab_test_id=ab_test_id,
            success_score=initial_score,
            key_factors={"context_fingerprint": context_fingerprint},
            metadata=context,
            status="sent"
        ).returning(ResponseTracking.id)

        result = await session.execute(stmt)
        response_id = result.scalar_one()
        await session.commit()

    processing_time = (time.time() - start_time) * 1000

    logger.info(
        f"Logged response from {agent_name}",
        extra={
            "response_id": str(response_id),
            "agent_name": agent_name,
            "agent_type": agent_type,
            "ab_test_id": ab_test_id,
            "processing_time_ms": processing_time
        }
    )

    return {
        "response_id": str(response_id),
        "logged_at": datetime.utcnow().isoformat(),
        "initial_success_score": initial_score,
        "tracking_status": "active",
        "context_fingerprint": context_fingerprint
    }
```

### 2. track_email_open

**Purpose**: Process email open webhook event

**Parameters**:
```python
{
    "message_id": str,              # Message UUID
    "opened_at": str,               # ISO timestamp
    "ip_address": str | None,       # Opener IP
    "user_agent": str | None,       # Browser/client
    "location": dict | None         # Geo data if available
}
```

**Returns**:
```python
{
    "response_id": str,
    "outcome_recorded": bool,
    "success_score": float,         # Updated score
    "score_change": float,          # Delta from previous
    "time_to_open_seconds": int,    # Sent to opened time
    "duplicate_event": bool         # True if already logged
}
```

**Implementation**:
```python
async def track_email_open(
    message_id: str,
    opened_at: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    location: dict | None = None
) -> dict[str, Any]:
    """
    Track email open event from webhook.

    Updates response_tracking with open data and recalculates success score.
    Idempotent - handles duplicate webhooks gracefully.
    """
    from sqlalchemy import select, update
    from src.database import get_async_session
    from src.models import ResponseTracking
    from dateutil import parser

    logger = get_agent_logger("response_tracker.open")

    opened_timestamp = parser.isoparse(opened_at)

    async with get_async_session() as session:
        # Find response by message_id
        stmt = select(ResponseTracking).where(
            ResponseTracking.message_id == message_id
        )
        result = await session.execute(stmt)
        response = result.scalar_one_or_none()

        if not response:
            logger.warning(f"No response found for message {message_id}")
            return {
                "response_id": None,
                "outcome_recorded": False,
                "error": "response_not_found"
            }

        # Check if already opened (idempotency)
        duplicate = response.opened
        if not duplicate:
            # Calculate time to open
            time_to_open = (opened_timestamp - response.generated_at).total_seconds()

            # Update response
            update_stmt = update(ResponseTracking).where(
                ResponseTracking.id == response.id
            ).values(
                opened=True,
                opened_at=opened_timestamp,
                metadata=ResponseTracking.metadata.concat({
                    "open_ip": ip_address,
                    "open_user_agent": user_agent,
                    "open_location": location,
                    "time_to_open_seconds": int(time_to_open)
                })
            )
            await session.execute(update_stmt)
            await session.commit()

        # Recalculate success score
        new_score = await _recalculate_success_score(response.id, session)
        score_change = new_score - float(response.success_score)

    logger.info(
        f"Email opened: {message_id}",
        extra={
            "response_id": str(response.id),
            "duplicate_event": duplicate,
            "new_score": new_score,
            "score_change": score_change
        }
    )

    return {
        "response_id": str(response.id),
        "outcome_recorded": True,
        "success_score": new_score,
        "score_change": score_change,
        "time_to_open_seconds": int(time_to_open) if not duplicate else None,
        "duplicate_event": duplicate
    }
```

### 3. track_email_click

**Purpose**: Process link click webhook event

**Parameters**:
```python
{
    "message_id": str,
    "clicked_at": str,
    "click_url": str,
    "link_index": int | None,
    "ip_address": str | None
}
```

**Returns**:
```python
{
    "response_id": str,
    "outcome_recorded": bool,
    "success_score": float,
    "score_change": float,
    "time_to_click_seconds": int,
    "clicked_url": str
}
```

**Implementation**: Similar pattern to track_email_open

### 4. track_email_reply

**Purpose**: Process email reply with sentiment analysis

**Parameters**:
```python
{
    "message_id": str,
    "replied_at": str,
    "reply_content": str,
    "reply_from": str
}
```

**Returns**:
```python
{
    "response_id": str,
    "outcome_recorded": bool,
    "success_score": float,
    "score_change": float,
    "sentiment": str,                # positive, negative, neutral
    "sentiment_score": float,        # -1.0 to 1.0
    "sentiment_category": str,       # interested, not_interested, etc.
    "time_to_reply_seconds": int
}
```

**Implementation**:
```python
async def track_email_reply(
    message_id: str,
    replied_at: str,
    reply_content: str,
    reply_from: str
) -> dict[str, Any]:
    """
    Track email reply event and analyze sentiment using Claude.

    Performs sentiment analysis to determine if reply is positive/negative.
    Adds bonus points for positive replies to success score.
    """
    from sqlalchemy import select, update
    from src.database import get_async_session
    from src.models import ResponseTracking
    from dateutil import parser
    from anthropic import Anthropic

    logger = get_agent_logger("response_tracker.reply")
    client = Anthropic()

    replied_timestamp = parser.isoparse(replied_at)

    # Analyze sentiment using Claude
    sentiment_prompt = f"""Analyze the sentiment of this email reply. Classify it as:
- positive (interested, wants to continue conversation)
- negative (not interested, dismissive)
- neutral (neutral acknowledgment)

Also provide a category:
- interested (wants meeting, more info)
- not_interested (explicitly declined)
- neutral (just acknowledging)

Reply content:
{reply_content}

Respond in JSON format:
{{"sentiment": "positive|negative|neutral", "category": "interested|not_interested|neutral", "score": -1.0 to 1.0, "reasoning": "brief explanation"}}"""

    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=200,
        messages=[{"role": "user", "content": sentiment_prompt}]
    )

    sentiment_data = json.loads(response.content[0].text)

    async with get_async_session() as session:
        # Find response
        stmt = select(ResponseTracking).where(
            ResponseTracking.message_id == message_id
        )
        result = await session.execute(stmt)
        response_record = result.scalar_one_or_none()

        if not response_record:
            logger.warning(f"No response found for message {message_id}")
            return {"response_id": None, "outcome_recorded": False}

        # Calculate time to reply
        time_to_reply = (replied_timestamp - response_record.generated_at).total_seconds()

        # Update response
        update_stmt = update(ResponseTracking).where(
            ResponseTracking.id == response_record.id
        ).values(
            replied=True,
            replied_at=replied_timestamp,
            replied_content=reply_content,
            sentiment=sentiment_data["sentiment"],
            sentiment_score=sentiment_data["score"],
            sentiment_analyzed_at=datetime.utcnow(),
            metadata=ResponseTracking.metadata.concat({
                "reply_from": reply_from,
                "sentiment_category": sentiment_data["category"],
                "sentiment_reasoning": sentiment_data["reasoning"],
                "time_to_reply_seconds": int(time_to_reply)
            })
        )
        await session.execute(update_stmt)
        await session.commit()

        # Recalculate success score (includes bonus for positive sentiment)
        new_score = await _recalculate_success_score(response_record.id, session)
        score_change = new_score - float(response_record.success_score)

    logger.info(
        f"Email reply tracked: {message_id}",
        extra={
            "response_id": str(response_record.id),
            "sentiment": sentiment_data["sentiment"],
            "category": sentiment_data["category"],
            "new_score": new_score
        }
    )

    return {
        "response_id": str(response_record.id),
        "outcome_recorded": True,
        "success_score": new_score,
        "score_change": score_change,
        "sentiment": sentiment_data["sentiment"],
        "sentiment_score": sentiment_data["score"],
        "sentiment_category": sentiment_data["category"],
        "time_to_reply_seconds": int(time_to_reply)
    }
```

### 5. track_meeting_booked

**Purpose**: Process meeting booking event

**Parameters**:
```python
{
    "message_id": str | None,       # May not have direct message
    "lead_id": str,                 # Lead UUID
    "meeting_id": str,              # Meeting UUID
    "booked_at": str,               # ISO timestamp
    "meeting_scheduled_for": str    # ISO timestamp
}
```

**Returns**:
```python
{
    "response_id": str | None,      # May be None if can't attribute
    "outcome_recorded": bool,
    "success_score": float,
    "attribution_method": str,      # direct, last_response, conversation_chain
    "days_to_conversion": float
}
```

### 6. track_deal_closed

**Purpose**: Process deal closure event

**Parameters**:
```python
{
    "lead_id": str,
    "deal_id": str,
    "closed_at": str,
    "deal_value": float,
    "deal_stage": str               # won, lost
}
```

**Returns**:
```python
{
    "responses_attributed": List[str],  # Multiple responses may get credit
    "primary_response_id": str | None,
    "outcome_recorded": bool,
    "attribution_method": str,
    "deal_value": float
}
```

### 7. calculate_success_score

**Purpose**: Calculate 0-10 success score based on outcomes

**Parameters**:
```python
{
    "response_id": str              # Response UUID to score
}
```

**Returns**:
```python
{
    "response_id": str,
    "success_score": float,         # 0-10
    "score_breakdown": {
        "base": 1.0,
        "opened": 3.0,
        "clicked": 2.0,
        "replied": 3.0,
        "positive_reply_bonus": 1.0,
        "meeting_booked": 4.0,
        "deal_closed": 5.0
    },
    "raw_score": float,             # Before capping at 10
    "capped_score": float,          # Final score (max 10)
    "outcomes_present": List[str]
}
```

**Implementation**:
```python
async def calculate_success_score(response_id: str) -> dict[str, Any]:
    """
    Calculate success score for a response based on all outcomes.

    Score Breakdown:
    - Base (sent): 1.0
    - Opened: +3.0 (30%)
    - Clicked: +2.0 (20%)
    - Replied: +3.0 (30%)
    - Positive reply: +1.0 bonus
    - Meeting booked: +4.0 (40%)
    - Deal closed: +5.0 (50%)
    - Max score: 10.0 (capped)
    """
    from sqlalchemy import select
    from src.database import get_async_session
    from src.models import ResponseTracking

    async with get_async_session() as session:
        stmt = select(ResponseTracking).where(ResponseTracking.id == response_id)
        result = await session.execute(stmt)
        response = result.scalar_one_or_none()

        if not response:
            raise ValueError(f"Response {response_id} not found")

        # Calculate score
        score = 1.0  # Base for sending
        breakdown = {"base": 1.0}
        outcomes = ["sent"]

        if response.opened:
            score += 3.0
            breakdown["opened"] = 3.0
            outcomes.append("opened")

        if response.clicked:
            score += 2.0
            breakdown["clicked"] = 2.0
            outcomes.append("clicked")

        if response.replied:
            score += 3.0
            breakdown["replied"] = 3.0
            outcomes.append("replied")

            # Bonus for positive sentiment
            if response.sentiment == "positive":
                score += 1.0
                breakdown["positive_reply_bonus"] = 1.0
                outcomes.append("positive_reply")

        # Check metadata for meeting/deal (stored from other trackers)
        metadata = response.metadata or {}
        if metadata.get("meeting_booked"):
            score += 4.0
            breakdown["meeting_booked"] = 4.0
            outcomes.append("meeting_booked")

        if metadata.get("deal_closed"):
            score += 5.0
            breakdown["deal_closed"] = 5.0
            outcomes.append("deal_closed")

        # Cap at 10
        raw_score = score
        capped_score = min(10.0, score)

        # Update database
        from sqlalchemy import update
        update_stmt = update(ResponseTracking).where(
            ResponseTracking.id == response_id
        ).values(success_score=capped_score)
        await session.execute(update_stmt)
        await session.commit()

    return {
        "response_id": response_id,
        "success_score": capped_score,
        "score_breakdown": breakdown,
        "raw_score": raw_score,
        "capped_score": capped_score,
        "outcomes_present": outcomes
    }
```

### 8. detect_success_patterns

**Purpose**: Identify patterns in high-performing responses

**Parameters**:
```python
{
    "min_score_threshold": float,       # Default 7.0
    "min_sample_size": int,             # Default 10
    "pattern_types": List[PatternType], # Which patterns to detect
    "context_filters": dict,            # industry, persona, etc.
    "lookback_days": int                # Default 90
}
```

**Returns**:
```python
{
    "patterns": List[SuccessPattern],
    "total_responses_analyzed": int,
    "high_performers_count": int,
    "low_performers_count": int,
    "baseline_avg_score": float,
    "recommendations": List[str]
}
```

**Implementation**:
```python
async def detect_success_patterns(
    min_score_threshold: float = 7.0,
    min_sample_size: int = 10,
    pattern_types: List[PatternType] = None,
    context_filters: dict = None,
    lookback_days: int = 90
) -> dict[str, Any]:
    """
    Detect patterns in high-performing responses.

    Uses statistical analysis to identify what separates successful
    responses from unsuccessful ones.
    """
    from sqlalchemy import select, and_
    from src.database import get_async_session
    from src.models import ResponseTracking
    from datetime import datetime, timedelta
    import re
    from scipy import stats

    logger = get_agent_logger("response_tracker.patterns")

    if pattern_types is None:
        pattern_types = list(PatternType)

    cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

    async with get_async_session() as session:
        # Build query
        query = select(ResponseTracking).where(
            and_(
                ResponseTracking.created_at >= cutoff_date,
                ResponseTracking.success_score >= min_score_threshold
            )
        )

        # Apply context filters
        if context_filters:
            for key, value in context_filters.items():
                query = query.where(
                    ResponseTracking.metadata[key].astext == str(value)
                )

        result = await session.execute(query)
        high_performers = result.scalars().all()

        # Also get low performers for comparison
        low_query = select(ResponseTracking).where(
            and_(
                ResponseTracking.created_at >= cutoff_date,
                ResponseTracking.success_score < 4.0
            )
        )
        if context_filters:
            for key, value in context_filters.items():
                low_query = low_query.where(
                    ResponseTracking.metadata[key].astext == str(value)
                )

        low_result = await session.execute(low_query)
        low_performers = low_result.scalars().all()

    patterns = []

    # Pattern 1: Opening line analysis
    if PatternType.OPENING_LINE in pattern_types:
        opening_lines = defaultdict(list)
        for response in high_performers:
            # Extract first sentence
            first_sentence = response.original_content.split('.')[0].strip()
            if len(first_sentence) < 100:  # Reasonable opening
                opening_lines[first_sentence[:50]].append(
                    float(response.success_score)
                )

        # Find patterns with sufficient samples
        for opening, scores in opening_lines.items():
            if len(scores) >= min_sample_size:
                avg_score = sum(scores) / len(scores)
                # Statistical test vs baseline
                baseline_scores = [float(r.success_score) for r in low_performers]
                if baseline_scores:
                    t_stat, p_value = stats.ttest_ind(scores, baseline_scores)
                    if p_value < 0.05:  # 95% confidence
                        patterns.append(SuccessPattern(
                            pattern_type=PatternType.OPENING_LINE,
                            description=f"Opening with '{opening}...'",
                            sample_count=len(scores),
                            avg_success_score=avg_score,
                            statistical_significance=1 - p_value,
                            context_filter=context_filters or {},
                            examples=[opening],
                            recommendation=f"Use similar opening lines. Avg score: {avg_score:.1f}"
                        ))

    # Pattern 2: Personalization type
    if PatternType.PERSONALIZATION_TYPE in pattern_types:
        personalization_types = defaultdict(list)
        for response in high_performers:
            content_lower = response.original_content.lower()
            if "linkedin" in content_lower and "post" in content_lower:
                personalization_types["linkedin_post"].append(float(response.success_score))
            elif "congratulations" in content_lower or "congrats" in content_lower:
                personalization_types["achievement"].append(float(response.success_score))
            elif "recent" in content_lower and ("article" in content_lower or "news" in content_lower):
                personalization_types["recent_news"].append(float(response.success_score))

        for ptype, scores in personalization_types.items():
            if len(scores) >= min_sample_size:
                avg_score = sum(scores) / len(scores)
                patterns.append(SuccessPattern(
                    pattern_type=PatternType.PERSONALIZATION_TYPE,
                    description=f"Personalization: {ptype.replace('_', ' ')}",
                    sample_count=len(scores),
                    avg_success_score=avg_score,
                    statistical_significance=0.95,  # Simplified
                    context_filter=context_filters or {},
                    examples=[ptype],
                    recommendation=f"Use {ptype} personalization. Avg score: {avg_score:.1f}"
                ))

    # Pattern 3: Length patterns
    if PatternType.LENGTH_PATTERN in pattern_types:
        length_buckets = defaultdict(list)
        for response in high_performers:
            length = len(response.original_content)
            bucket = "ultra_short" if length < 100 else \
                     "short" if length < 200 else \
                     "medium" if length < 400 else "long"
            length_buckets[bucket].append(float(response.success_score))

        for bucket, scores in length_buckets.items():
            if len(scores) >= min_sample_size:
                avg_score = sum(scores) / len(scores)
                patterns.append(SuccessPattern(
                    pattern_type=PatternType.LENGTH_PATTERN,
                    description=f"Email length: {bucket}",
                    sample_count=len(scores),
                    avg_success_score=avg_score,
                    statistical_significance=0.95,
                    context_filter=context_filters or {},
                    examples=[bucket],
                    recommendation=f"Use {bucket} emails. Avg score: {avg_score:.1f}"
                ))

    # Calculate baseline
    baseline_avg = sum(float(r.success_score) for r in high_performers) / len(high_performers) \
                   if high_performers else 0

    # Generate recommendations
    recommendations = []
    for pattern in sorted(patterns, key=lambda p: p.avg_success_score, reverse=True)[:5]:
        recommendations.append(pattern.recommendation)

    logger.info(
        f"Detected {len(patterns)} success patterns",
        extra={
            "high_performers": len(high_performers),
            "low_performers": len(low_performers),
            "patterns_detected": len(patterns)
        }
    )

    return {
        "patterns": patterns,
        "total_responses_analyzed": len(high_performers) + len(low_performers),
        "high_performers_count": len(high_performers),
        "low_performers_count": len(low_performers),
        "baseline_avg_score": baseline_avg,
        "recommendations": recommendations
    }
```

### 9. generate_effectiveness_report

**Purpose**: Generate comprehensive performance report

**Parameters**:
```python
{
    "report_type": str,             # agent, campaign, industry, overall
    "date_range": Tuple[str, str],  # Start, end ISO dates
    "group_by": List[str],          # agent_name, campaign_id, industry
    "include_ab_tests": bool,       # Include A/B test results
    "format": str                   # json, markdown, html
}
```

**Returns**:
```python
{
    "report_id": str,
    "report_type": str,
    "date_range": Tuple[str, str],
    "summary": {
        "total_responses": int,
        "avg_success_score": float,
        "open_rate": float,
        "click_rate": float,
        "reply_rate": float,
        "meeting_rate": float,
        "deal_rate": float
    },
    "breakdowns": List[dict],
    "top_performers": List[dict],
    "underperformers": List[dict],
    "ab_test_results": List[dict],
    "recommendations": List[str],
    "generated_at": str
}
```

### 10. validate_ab_test

**Purpose**: Validate A/B test with statistical significance

**Parameters**:
```python
{
    "ab_test_id": str,              # A/B test UUID
    "metric": str,                  # success_score, open_rate, reply_rate
    "confidence_level": float       # Default 0.95
}
```

**Returns**:
```python
{
    "ab_test_id": str,
    "metric": str,
    "variant_a": {
        "sample_size": int,
        "mean": float,
        "std_dev": float,
        "success_rate": float
    },
    "variant_b": {
        "sample_size": int,
        "mean": float,
        "std_dev": float,
        "success_rate": float
    },
    "statistical_test": {
        "test_type": str,           # t_test, chi_square
        "test_statistic": float,
        "p_value": float,
        "confidence_level": float,
        "is_significant": bool
    },
    "winner": str | None,           # A, B, or None
    "improvement": float | None,    # % improvement of winner
    "recommendation": str,          # implement, continue_testing, reject
    "min_sample_reached": bool
}
```

**Implementation**:
```python
async def validate_ab_test(
    ab_test_id: str,
    metric: str = "success_score",
    confidence_level: float = 0.95
) -> dict[str, Any]:
    """
    Validate A/B test with statistical significance testing.

    Uses t-test for continuous metrics (success_score) and
    chi-square for binary metrics (open_rate, reply_rate).

    Requires minimum 100 samples per variant for valid test.
    """
    from sqlalchemy import select
    from src.database import get_async_session
    from src.models import ResponseTracking
    from scipy import stats
    import numpy as np

    logger = get_agent_logger("response_tracker.ab_test")

    async with get_async_session() as session:
        # Get variant A
        stmt_a = select(ResponseTracking).where(
            and_(
                ResponseTracking.ab_test_id == ab_test_id,
                ResponseTracking.ab_test_group == "A"
            )
        )
        result_a = await session.execute(stmt_a)
        variant_a_responses = result_a.scalars().all()

        # Get variant B
        stmt_b = select(ResponseTracking).where(
            and_(
                ResponseTracking.ab_test_id == ab_test_id,
                ResponseTracking.ab_test_group == "B"
            )
        )
        result_b = await session.execute(stmt_b)
        variant_b_responses = result_b.scalars().all()

    # Check minimum sample size
    min_sample_reached = len(variant_a_responses) >= 100 and len(variant_b_responses) >= 100

    if not min_sample_reached:
        logger.warning(f"A/B test {ab_test_id} has insufficient samples")

    # Extract metric values
    if metric == "success_score":
        a_values = [float(r.success_score) for r in variant_a_responses]
        b_values = [float(r.success_score) for r in variant_b_responses]
        test_type = "t_test"

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(a_values, b_values)

        variant_a_data = {
            "sample_size": len(a_values),
            "mean": float(np.mean(a_values)),
            "std_dev": float(np.std(a_values)),
            "success_rate": None
        }
        variant_b_data = {
            "sample_size": len(b_values),
            "mean": float(np.mean(b_values)),
            "std_dev": float(np.std(b_values)),
            "success_rate": None
        }

    elif metric in ["open_rate", "click_rate", "reply_rate"]:
        # Binary outcome - use chi-square
        test_type = "chi_square"

        metric_field = {
            "open_rate": "opened",
            "click_rate": "clicked",
            "reply_rate": "replied"
        }[metric]

        a_success = sum(1 for r in variant_a_responses if getattr(r, metric_field))
        a_total = len(variant_a_responses)
        b_success = sum(1 for r in variant_b_responses if getattr(r, metric_field))
        b_total = len(variant_b_responses)

        # Chi-square test
        contingency_table = [
            [a_success, a_total - a_success],
            [b_success, b_total - b_success]
        ]
        chi2_stat, p_value, _, _ = stats.chi2_contingency(contingency_table)
        t_stat = chi2_stat

        variant_a_data = {
            "sample_size": a_total,
            "mean": None,
            "std_dev": None,
            "success_rate": a_success / a_total if a_total > 0 else 0
        }
        variant_b_data = {
            "sample_size": b_total,
            "mean": None,
            "std_dev": None,
            "success_rate": b_success / b_total if b_total > 0 else 0
        }
    else:
        raise ValueError(f"Unknown metric: {metric}")

    # Determine significance
    is_significant = p_value < (1 - confidence_level)

    # Determine winner
    winner = None
    improvement = None
    if is_significant:
        if metric == "success_score":
            winner = "A" if variant_a_data["mean"] > variant_b_data["mean"] else "B"
            improvement = abs(variant_a_data["mean"] - variant_b_data["mean"]) / \
                          min(variant_a_data["mean"], variant_b_data["mean"]) * 100
        else:
            winner = "A" if variant_a_data["success_rate"] > variant_b_data["success_rate"] else "B"
            improvement = abs(variant_a_data["success_rate"] - variant_b_data["success_rate"]) / \
                          min(variant_a_data["success_rate"], variant_b_data["success_rate"]) * 100

    # Generate recommendation
    if not min_sample_reached:
        recommendation = "continue_testing (insufficient samples)"
    elif not is_significant:
        recommendation = "continue_testing (not statistically significant)"
    elif improvement and improvement > 20:
        recommendation = f"implement (variant {winner} wins by {improvement:.1f}%)"
    else:
        recommendation = "reject (no meaningful difference)"

    logger.info(
        f"A/B test validated: {ab_test_id}",
        extra={
            "winner": winner,
            "improvement": improvement,
            "p_value": p_value,
            "recommendation": recommendation
        }
    )

    return {
        "ab_test_id": ab_test_id,
        "metric": metric,
        "variant_a": variant_a_data,
        "variant_b": variant_b_data,
        "statistical_test": {
            "test_type": test_type,
            "test_statistic": float(t_stat),
            "p_value": float(p_value),
            "confidence_level": confidence_level,
            "is_significant": is_significant
        },
        "winner": winner,
        "improvement": improvement,
        "recommendation": recommendation,
        "min_sample_reached": min_sample_reached
    }
```

---

## Database Schema

Uses tables from migration 007_learning_system.sql:

### response_tracking (Core Table)

```sql
CREATE TABLE IF NOT EXISTS response_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Response Details
    message_id UUID REFERENCES messages(id),
    campaign_id UUID REFERENCES campaigns(id),
    lead_id UUID REFERENCES leads(id),

    -- Agent Information
    agent_name VARCHAR(100) NOT NULL,
    agent_version VARCHAR(50),
    agent_type VARCHAR(100),

    -- Original Response
    original_content TEXT NOT NULL,
    original_subject VARCHAR(500),
    generated_at TIMESTAMPTZ,
    generation_time_ms INTEGER,
    prompt_used TEXT,

    -- Human Corrections
    corrected_content TEXT,
    corrected_subject VARCHAR(500),
    corrected_by VARCHAR(100),
    corrected_at TIMESTAMPTZ,
    correction_reason TEXT,

    -- Performance Metrics
    opened BOOLEAN DEFAULT FALSE,
    opened_at TIMESTAMPTZ,
    clicked BOOLEAN DEFAULT FALSE,
    clicked_at TIMESTAMPTZ,
    replied BOOLEAN DEFAULT FALSE,
    replied_at TIMESTAMPTZ,
    replied_content TEXT,

    -- Sentiment Analysis
    sentiment VARCHAR(50),
    sentiment_score DECIMAL(3,2),
    sentiment_analyzed_at TIMESTAMPTZ,

    -- Learning Data
    success_score DECIMAL(3,2) DEFAULT 0,
    key_factors JSONB DEFAULT '{}',
    lessons_learned TEXT,

    -- A/B Testing
    ab_test_group VARCHAR(10),
    ab_test_id UUID,
    is_winner BOOLEAN,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',

    -- Status
    status VARCHAR(50) DEFAULT 'sent' CHECK (
        status IN ('draft', 'sent', 'corrected', 'analyzed', 'archived')
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_rt_agent ON response_tracking(agent_name, created_at);
CREATE INDEX IF NOT EXISTS idx_rt_campaign ON response_tracking(campaign_id, success_score);
CREATE INDEX IF NOT EXISTS idx_rt_ab_test ON response_tracking(ab_test_id, is_winner);
CREATE INDEX IF NOT EXISTS idx_rt_performance ON response_tracking(success_score DESC);
CREATE INDEX IF NOT EXISTS idx_rt_lead ON response_tracking(lead_id, created_at);
CREATE INDEX IF NOT EXISTS idx_rt_message ON response_tracking(message_id);
```

---

## Success Score Calculation Algorithm

```python
def calculate_success_score(response: ResponseTracking) -> float:
    """
    Calculate 0-10 success score based on outcomes.

    Weighting:
    - Base (sent): 1.0 (10%)
    - Opened: +3.0 (30%)
    - Clicked: +2.0 (20%)
    - Replied: +3.0 (30%)
    - Positive reply: +1.0 bonus (10%)
    - Meeting booked: +4.0 (40%)
    - Deal closed: +5.0 (50%)

    Maximum: 10.0 (capped)
    """
    score = 1.0  # Base

    if response.opened:
        score += 3.0

    if response.clicked:
        score += 2.0

    if response.replied:
        score += 3.0
        if response.sentiment == "positive":
            score += 1.0  # Bonus

    # Check metadata for downstream conversions
    if response.metadata.get("meeting_booked"):
        score += 4.0

    if response.metadata.get("deal_closed"):
        score += 5.0

    # Cap at 10
    return min(10.0, score)
```

---

## Webhook Handler Implementations

### Email Provider Webhook (Instantly)

```python
from fastapi import APIRouter, Request, HTTPException
from src.agents.system_response_outcome_tracker.agent import ResponseOutcomeTrackerAgent

router = APIRouter(prefix="/webhooks/instantly", tags=["webhooks"])

@router.post("/email-opened")
async def instantly_email_opened(request: Request):
    """
    Handle Instantly email opened webhook.

    Expected payload:
    {
        "message_id": "uuid",
        "opened_at": "2025-12-05T10:30:00Z",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0..."
    }
    """
    data = await request.json()

    agent = ResponseOutcomeTrackerAgent()
    result = await agent._tools["track_email_open"](
        message_id=data["message_id"],
        opened_at=data["opened_at"],
        ip_address=data.get("ip_address"),
        user_agent=data.get("user_agent")
    )

    if not result["outcome_recorded"]:
        raise HTTPException(status_code=404, detail="Response not found")

    return {"status": "ok", "result": result}


@router.post("/email-clicked")
async def instantly_email_clicked(request: Request):
    """Handle Instantly link click webhook."""
    data = await request.json()

    agent = ResponseOutcomeTrackerAgent()
    result = await agent._tools["track_email_click"](
        message_id=data["message_id"],
        clicked_at=data["clicked_at"],
        click_url=data["click_url"],
        ip_address=data.get("ip_address")
    )

    return {"status": "ok", "result": result}


@router.post("/email-replied")
async def instantly_email_replied(request: Request):
    """Handle Instantly email reply webhook."""
    data = await request.json()

    agent = ResponseOutcomeTrackerAgent()
    result = await agent._tools["track_email_reply"](
        message_id=data["message_id"],
        replied_at=data["replied_at"],
        reply_content=data["reply_content"],
        reply_from=data["reply_from"]
    )

    return {"status": "ok", "result": result}
```

### Calendar Webhook (Cal.com)

```python
@router.post("/calcom/booking-created")
async def calcom_booking_created(request: Request):
    """
    Handle Cal.com booking created webhook.

    Expected payload:
    {
        "lead_id": "uuid",
        "meeting_id": "uuid",
        "booked_at": "2025-12-05T10:30:00Z",
        "scheduled_for": "2025-12-10T15:00:00Z"
    }
    """
    data = await request.json()

    agent = ResponseOutcomeTrackerAgent()
    result = await agent._tools["track_meeting_booked"](
        lead_id=data["lead_id"],
        meeting_id=data["meeting_id"],
        booked_at=data["booked_at"],
        meeting_scheduled_for=data["scheduled_for"]
    )

    return {"status": "ok", "result": result}
```

---

## Pattern Detection Logic

### Pattern Categories

1. **Opening Line Patterns**
   - Extract first sentence
   - Group similar openings
   - Compare success rates

2. **Personalization Patterns**
   - LinkedIn post mentions
   - Achievement congratulations
   - Recent news references
   - Company-specific insights

3. **Value Proposition Patterns**
   - Problem statements
   - Solution offerings
   - Benefit claims
   - Case study mentions

4. **Call-to-Action Patterns**
   - Question-based CTAs
   - Calendar link CTAs
   - Low-friction asks
   - Multi-option CTAs

5. **Timing Patterns**
   - Day of week
   - Time of day
   - Time since last contact
   - Seasonal factors

6. **Length Patterns**
   - Ultra-short (<100 chars)
   - Short (100-200 chars)
   - Medium (200-400 chars)
   - Long (>400 chars)

### Statistical Validation

```python
from scipy import stats

def validate_pattern_significance(
    pattern_scores: List[float],
    baseline_scores: List[float],
    confidence: float = 0.95
) -> Tuple[bool, float]:
    """
    Validate if pattern is statistically significant vs baseline.

    Returns: (is_significant, p_value)
    """
    if len(pattern_scores) < 10 or len(baseline_scores) < 10:
        return False, 1.0

    # Two-sample t-test
    t_stat, p_value = stats.ttest_ind(pattern_scores, baseline_scores)

    alpha = 1 - confidence
    is_significant = p_value < alpha

    return is_significant, p_value
```

---

## Error Handling Strategy

### Idempotency

All webhook handlers are idempotent:
- Check if outcome already recorded
- Skip duplicate events
- Return success status regardless

### Missing Responses

```python
if not response_found:
    logger.warning(f"Response not found for message {message_id}")
    # Queue for later processing (maybe message logged async)
    await redis.lpush("pending_outcomes", json.dumps(webhook_data))
    return {"status": "queued"}
```

### Sentiment Analysis Failures

```python
try:
    sentiment = await analyze_sentiment_with_claude(reply_content)
except Exception as e:
    logger.error("Sentiment analysis failed", exc_info=e)
    # Default to neutral
    sentiment = {"sentiment": "neutral", "score": 0.0, "category": "neutral"}
```

### Database Connection Issues

```python
try:
    async with get_async_session() as session:
        # Process outcome
        pass
except DatabaseError as e:
    logger.error("Database error", exc_info=e)
    # Queue for retry
    await redis.lpush("retry_queue", json.dumps({"type": "outcome", "data": data}))
    raise HTTPException(status_code=503, detail="Service temporarily unavailable")
```

---

## Testing Requirements

### Unit Tests (>90% coverage required)

**Test file**: `__tests__/unit/agents/test_response_outcome_tracker.py`

```python
class TestResponseOutcomeTrackerInitialization:
    def test_agent_initialization()
    def test_tools_registered()
    def test_system_prompt_defined()

class TestLogResponse:
    @pytest.mark.asyncio
    async def test_log_response_success()
    async def test_log_response_with_corrections()
    async def test_log_response_with_ab_test()
    async def test_context_fingerprint_generation()
    async def test_initial_success_score()

class TestTrackEmailOpen:
    @pytest.mark.asyncio
    async def test_track_open_success()
    async def test_track_open_duplicate()
    async def test_track_open_missing_response()
    async def test_success_score_recalculation()
    async def test_time_to_open_calculation()

class TestTrackEmailClick:
    @pytest.mark.asyncio
    async def test_track_click_success()
    async def test_track_multiple_clicks()
    async def test_click_url_tracking()

class TestTrackEmailReply:
    @pytest.mark.asyncio
    async def test_track_reply_positive_sentiment()
    async def test_track_reply_negative_sentiment()
    async def test_sentiment_analysis_with_claude()
    async def test_positive_reply_bonus_score()

class TestTrackMeetingBooked:
    @pytest.mark.asyncio
    async def test_track_meeting_direct_attribution()
    async def test_track_meeting_last_response_attribution()
    async def test_meeting_score_boost()

class TestCalculateSuccessScore:
    @pytest.mark.asyncio
    async def test_base_score()
    async def test_score_with_open()
    async def test_score_with_all_outcomes()
    async def test_score_capping_at_10()
    async def test_positive_reply_bonus()

class TestDetectSuccessPatterns:
    @pytest.mark.asyncio
    async def test_opening_line_pattern_detection()
    async def test_personalization_pattern_detection()
    async def test_length_pattern_detection()
    async def test_minimum_sample_size_enforcement()
    async def test_statistical_significance_filtering()

class TestGenerateEffectivenessReport:
    @pytest.mark.asyncio
    async def test_report_by_agent()
    async def test_report_by_campaign()
    async def test_report_summary_metrics()
    async def test_top_performers_identification()

class TestValidateABTest:
    @pytest.mark.asyncio
    async def test_ab_test_t_test_validation()
    async def test_ab_test_chi_square_validation()
    async def test_ab_test_insufficient_samples()
    async def test_ab_test_winner_determination()
    async def test_ab_test_not_significant()
```

### Integration Tests

**Test file**: `__tests__/integration/test_response_outcome_tracker_integration.py`

```python
class TestResponseOutcomeTrackerIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_response_flow()
    async def test_webhook_to_database_flow()
    async def test_pattern_detection_with_real_data()
    async def test_ab_test_validation_complete_flow()

class TestWebhookHandlers:
    @pytest.mark.asyncio
    async def test_instantly_webhook_integration()
    async def test_calcom_webhook_integration()
    async def test_duplicate_webhook_handling()
    async def test_webhook_idempotency()

class TestCrossAgentIntegration:
    @pytest.mark.asyncio
    async def test_feed_to_learning_feedback_agent()
    async def test_feed_to_performance_analyst()
    async def test_feed_to_knowledge_base_manager()
```

---

## Implementation Checklist

### Phase 1: Core Response Logging
- [ ] Implement `ResponseOutcomeTrackerAgent` class extending `BaseAgent`
- [ ] Implement `log_response` tool with context fingerprinting
- [ ] Create database migration (use existing 007_learning_system.sql)
- [ ] Write unit tests for response logging (>90% coverage)

### Phase 2: Outcome Tracking
- [ ] Implement `track_email_open` tool with idempotency
- [ ] Implement `track_email_click` tool
- [ ] Implement `track_email_reply` tool with Claude sentiment analysis
- [ ] Implement `track_meeting_booked` tool with attribution logic
- [ ] Implement `track_deal_closed` tool
- [ ] Write unit tests for all outcome trackers

### Phase 3: Success Scoring
- [ ] Implement `calculate_success_score` tool with weighted algorithm
- [ ] Implement `_recalculate_success_score` helper function
- [ ] Add automatic score recalculation on outcome updates
- [ ] Write unit tests for score calculation
- [ ] Validate score ranges (0-10)

### Phase 4: Pattern Detection
- [ ] Implement `detect_success_patterns` tool
- [ ] Add opening line pattern detection
- [ ] Add personalization pattern detection
- [ ] Add length pattern detection
- [ ] Add timing pattern detection
- [ ] Implement statistical significance testing (scipy)
- [ ] Write unit tests for pattern detection

### Phase 5: Reporting & A/B Testing
- [ ] Implement `generate_effectiveness_report` tool
- [ ] Implement `validate_ab_test` tool with t-test and chi-square
- [ ] Create report templates (JSON, Markdown, HTML)
- [ ] Write unit tests for reporting and A/B validation

### Phase 6: Webhook Integration
- [ ] Create Instantly webhook handlers (open, click, reply)
- [ ] Create Cal.com webhook handler (meeting booked)
- [ ] Implement webhook authentication/verification
- [ ] Add webhook error handling and retry logic
- [ ] Write integration tests for webhooks

### Phase 7: Agent Integration
- [ ] Integrate with all response-generating agents
- [ ] Create handoff to system-learning-feedback
- [ ] Create handoff to system-agent-performance-analyst
- [ ] Create handoff to system-knowledge-base-manager
- [ ] Test cross-agent data flow

### Phase 8: Testing & Optimization
- [ ] Achieve >90% test coverage
- [ ] Performance test with 10,000+ responses
- [ ] Optimize database queries (add indexes)
- [ ] Test pattern detection accuracy
- [ ] Test A/B validation statistical correctness
- [ ] Document all procedures

---

## Success Metrics

- **Tracking Coverage**: >99% of agent responses logged
- **Webhook Processing**: <500ms latency, >99.9% success rate
- **Pattern Detection Accuracy**: >85% of identified patterns validated by humans
- **A/B Test Validation**: 100% statistical correctness (no false positives/negatives)
- **Success Score Correlation**: >0.8 correlation with actual conversions
- **System Uptime**: >99.5% uptime
- **Processing Throughput**: >1000 outcomes/minute
- **Test Coverage**: >90% code coverage

---

## Related Agents

**Feeds Data To:**
- system-learning-feedback - Aggregated success patterns and correction data
- system-agent-performance-analyst - Agent-specific performance metrics
- system-knowledge-base-manager - KB item effectiveness data
- system-correction-approval-orchestrator - A/B test validation results

**Receives Data From:**
- All response-generating agents (cold_email_copywriter, response_email_handler, etc.)
- Email providers (Instantly, SendGrid) - webhooks
- Calendar systems (Cal.com) - meeting webhooks
- CRM systems - deal closure events

---

## Future Enhancements

1. **Machine Learning Models**
   - Train ML model to predict success score from content
   - Auto-classify response types using embeddings
   - Predict optimal send times using historical patterns

2. **Advanced Attribution**
   - Multi-touch attribution across conversation sequences
   - Time-decay attribution modeling
   - Channel attribution (email vs. LinkedIn vs. phone)

3. **Real-Time Dashboards**
   - Live success score tracking
   - Real-time A/B test progress
   - Pattern detection alerts

4. **Automated Insights**
   - Claude-powered insight generation
   - Anomaly detection (unusual patterns)
   - Predictive analytics (forecast outcomes)

5. **Content Optimization**
   - Auto-suggest improvements based on patterns
   - Real-time content scoring before sending
   - Dynamic template optimization

---

## Security Considerations

1. **Webhook Verification**: Verify webhook signatures from providers
2. **Data Privacy**: Sanitize PII from response content in reports
3. **Access Control**: Role-based access to effectiveness reports
4. **Audit Trail**: Log all pattern detections and A/B test results
5. **Rate Limiting**: Prevent webhook flooding attacks

---

## Performance Requirements

1. **Throughput**: Process 10,000+ responses per day
2. **Latency**: Webhook processing <500ms p95
3. **Storage**: Efficient storage of response content (compress old responses)
4. **Query Performance**: Report generation <5 seconds
5. **Pattern Detection**: Complete in <30 seconds for 90-day window
