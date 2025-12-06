# Meeting Sales Call Analytics Agent - Technical Specification

**Agent Category:** Meeting Management
**Priority:** Phase 2 - Intelligence & Optimization
**Version:** 1.0.0
**Last Updated:** 2025-12-05
**Refined From:** plan/agents/meeting-sales-call-analytics.md

## Overview

The Meeting Sales Call Analytics Agent analyzes sales call transcripts at scale to provide team-level insights, identify performance patterns, and generate coaching opportunities. Unlike the individual Call Improvement Agent, this agent focuses on aggregate analytics across ALL calls, tracking team trends, benchmarking top performers, and identifying systematic improvement opportunities.

## Dependencies

### Upstream Agents
- **Call Transcript Processor Agent**: Provides analyzed transcripts with structured insights
- **Meeting Scheduler Agent**: Provides meeting context and metadata
- **Call Improvement Agent**: Provides individual call scores for aggregation

### Downstream Agents
- **System Agent Performance Analyst**: Receives analytics for agent performance tracking
- **Campaign Copywriting Agent**: Receives insights on effective messaging patterns
- **Response Check-in Agent**: Receives coaching opportunity alerts

### Third-Party Integrations
- **Anthropic Claude**: AI analysis for pattern identification and insights
- **Internal Database**: Queries call scores, transcripts, and performance metrics
- **Visualization**: Analytics dashboard data generation

## Data Models

### Database Tables

#### call_analytics
```sql
CREATE TABLE call_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID REFERENCES call_transcripts(id) ON DELETE CASCADE,
    call_score_id UUID REFERENCES call_scores(id),
    lead_id UUID REFERENCES leads(id),
    meeting_id UUID REFERENCES meetings(id),
    sales_rep_id UUID,  -- Future: reference to users table

    -- Talk Ratio Analysis
    total_words INTEGER NOT NULL DEFAULT 0,
    sales_rep_words INTEGER NOT NULL DEFAULT 0,
    prospect_words INTEGER NOT NULL DEFAULT 0,
    sales_rep_talk_percentage DECIMAL(5,2) NOT NULL,  -- 0.00-100.00
    talk_ratio_score INTEGER CHECK (talk_ratio_score >= 0 AND talk_ratio_score <= 100),

    -- Question Analysis
    total_questions INTEGER NOT NULL DEFAULT 0,
    open_ended_questions INTEGER NOT NULL DEFAULT 0,
    closed_questions INTEGER NOT NULL DEFAULT 0,
    discovery_questions INTEGER NOT NULL DEFAULT 0,
    pain_questions INTEGER NOT NULL DEFAULT 0,
    question_effectiveness_score INTEGER CHECK (question_effectiveness_score >= 0 AND question_effectiveness_score <= 100),

    -- Objection Handling
    total_objections INTEGER NOT NULL DEFAULT 0,
    objections_acknowledged INTEGER NOT NULL DEFAULT 0,
    objections_resolved INTEGER NOT NULL DEFAULT 0,
    objection_handling_score INTEGER CHECK (objection_handling_score >= 0 AND objection_handling_score <= 100),

    -- Sentiment Flow
    opening_sentiment VARCHAR(20),  -- positive, neutral, negative
    middle_sentiment VARCHAR(20),
    closing_sentiment VARCHAR(20),
    overall_sentiment_trajectory VARCHAR(20),  -- improving, stable, declining
    sentiment_transitions JSONB DEFAULT '[]',  -- [{timestamp, from, to, trigger}]

    -- Closing Effectiveness
    closing_attempts INTEGER NOT NULL DEFAULT 0,
    next_steps_clarity_score INTEGER CHECK (next_steps_clarity_score >= 0 AND next_steps_clarity_score <= 100),
    commitment_strength VARCHAR(20),  -- strong, medium, weak, none

    -- Call Outcome Correlation
    call_outcome VARCHAR(50),  -- positive, neutral, negative, no_show
    conversion_likelihood DECIMAL(3,2),  -- From call_insights

    -- Metadata
    call_duration_seconds INTEGER NOT NULL,
    call_type VARCHAR(50),  -- discovery, demo, technical, closing
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_version VARCHAR(50),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_call_analytics_transcript_id ON call_analytics(transcript_id);
CREATE INDEX idx_call_analytics_call_score_id ON call_analytics(call_score_id);
CREATE INDEX idx_call_analytics_sales_rep_id ON call_analytics(sales_rep_id);
CREATE INDEX idx_call_analytics_call_type ON call_analytics(call_type);
CREATE INDEX idx_call_analytics_call_outcome ON call_analytics(call_outcome);
CREATE INDEX idx_call_analytics_analyzed_at ON call_analytics(analyzed_at DESC);
```

#### analytics_metrics
```sql
CREATE TABLE analytics_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(50) NOT NULL,  -- team_performance, top_performer, skill_trend
    metric_period VARCHAR(20) NOT NULL,  -- daily, weekly, monthly, quarterly
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Aggregated Metrics
    total_calls INTEGER NOT NULL DEFAULT 0,
    total_sales_reps INTEGER NOT NULL DEFAULT 0,

    -- Average Scores
    avg_talk_ratio DECIMAL(5,2),
    avg_question_effectiveness DECIMAL(5,2),
    avg_objection_handling DECIMAL(5,2),
    avg_closing_effectiveness DECIMAL(5,2),
    avg_overall_score DECIMAL(5,2),

    -- Conversion Metrics
    positive_outcome_rate DECIMAL(5,2),
    avg_conversion_likelihood DECIMAL(5,2),

    -- Distribution Analysis
    score_distribution JSONB DEFAULT '{}',  -- {0-20: 5, 21-40: 10, ...}
    top_performers JSONB DEFAULT '[]',  -- [{rep_id, score, rank}]
    improvement_opportunities JSONB DEFAULT '[]',  -- [{category, gap, priority}]

    -- Metadata
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(metric_type, metric_period, period_start, period_end)
);

CREATE INDEX idx_analytics_metrics_type ON analytics_metrics(metric_type);
CREATE INDEX idx_analytics_metrics_period ON analytics_metrics(metric_period, period_start);
```

#### coaching_opportunities
```sql
CREATE TABLE coaching_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sales_rep_id UUID NOT NULL,
    opportunity_type VARCHAR(50) NOT NULL,  -- talk_ratio, questioning, objections, closing

    -- Opportunity Details
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    current_performance DECIMAL(5,2) NOT NULL,
    target_performance DECIMAL(5,2) NOT NULL,
    performance_gap DECIMAL(5,2) NOT NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('critical', 'high', 'medium', 'low')),

    -- Evidence
    sample_call_ids JSONB DEFAULT '[]',  -- [uuid1, uuid2, uuid3]
    pattern_examples JSONB DEFAULT '[]',  -- Specific examples from calls

    -- Benchmark Comparison
    team_average DECIMAL(5,2),
    top_performer_average DECIMAL(5,2),
    percentile_rank INTEGER,  -- 0-100

    -- Recommendations
    specific_actions JSONB DEFAULT '[]',  -- ["action1", "action2"]
    training_resources JSONB DEFAULT '[]',  -- [{type, title, url}]
    expected_impact TEXT,

    -- Status
    status VARCHAR(20) DEFAULT 'identified' CHECK (status IN ('identified', 'assigned', 'in_progress', 'resolved', 'archived')),
    assigned_to UUID,  -- Coach/manager UUID
    assigned_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,

    -- Follow-up Tracking
    follow_up_call_ids JSONB DEFAULT '[]',  -- Calls after coaching
    improvement_observed BOOLEAN DEFAULT FALSE,
    improvement_percentage DECIMAL(5,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_coaching_opportunities_sales_rep_id ON coaching_opportunities(sales_rep_id);
CREATE INDEX idx_coaching_opportunities_type ON coaching_opportunities(opportunity_type);
CREATE INDEX idx_coaching_opportunities_priority ON coaching_opportunities(priority);
CREATE INDEX idx_coaching_opportunities_status ON coaching_opportunities(status);
CREATE INDEX idx_coaching_opportunities_created_at ON coaching_opportunities(created_at DESC);
```

#### team_performance_snapshots
```sql
CREATE TABLE team_performance_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL UNIQUE,

    -- Team-Level Metrics
    total_calls INTEGER NOT NULL DEFAULT 0,
    active_sales_reps INTEGER NOT NULL DEFAULT 0,

    -- Performance Averages
    avg_talk_ratio DECIMAL(5,2) NOT NULL,
    avg_question_score DECIMAL(5,2) NOT NULL,
    avg_objection_score DECIMAL(5,2) NOT NULL,
    avg_closing_score DECIMAL(5,2) NOT NULL,
    avg_overall_score DECIMAL(5,2) NOT NULL,

    -- Outcome Metrics
    conversion_rate DECIMAL(5,2) NOT NULL,
    positive_sentiment_rate DECIMAL(5,2) NOT NULL,

    -- Top Performers
    top_performer_id UUID,
    top_performer_score DECIMAL(5,2),

    -- Improvement Areas
    weakest_skill VARCHAR(50),  -- talk_ratio, questioning, objections, closing
    weakest_skill_score DECIMAL(5,2),

    -- Trend Analysis
    trend_direction VARCHAR(20),  -- improving, stable, declining
    week_over_week_change DECIMAL(5,2),
    month_over_month_change DECIMAL(5,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_team_snapshots_date ON team_performance_snapshots(snapshot_date DESC);
```

### Pydantic Models

```python
from datetime import datetime, date
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TalkRatioAnalysis(BaseModel):
    """Talk ratio analysis results."""
    total_words: int = Field(..., ge=0)
    sales_rep_words: int = Field(..., ge=0)
    prospect_words: int = Field(..., ge=0)
    sales_rep_percentage: Decimal = Field(..., ge=0, le=100)
    score: int = Field(..., ge=0, le=100)
    assessment: str  # "excellent", "good", "too_much", "dominating"


class QuestionPatternAnalysis(BaseModel):
    """Question effectiveness analysis."""
    total_questions: int = Field(..., ge=0)
    open_ended: int = Field(..., ge=0)
    closed: int = Field(..., ge=0)
    discovery: int = Field(..., ge=0)
    pain_focused: int = Field(..., ge=0)
    effectiveness_score: int = Field(..., ge=0, le=100)
    patterns: list[str] = Field(default_factory=list)


class ObjectionHandlingAnalysis(BaseModel):
    """Objection handling effectiveness."""
    total_objections: int = Field(..., ge=0)
    acknowledged: int = Field(..., ge=0)
    resolved: int = Field(..., ge=0)
    handling_score: int = Field(..., ge=0, le=100)
    techniques_used: list[str] = Field(default_factory=list)


class SentimentFlowAnalysis(BaseModel):
    """Sentiment progression through call."""
    opening: str = Field(..., pattern="^(positive|neutral|negative)$")
    middle: str = Field(..., pattern="^(positive|neutral|negative)$")
    closing: str = Field(..., pattern="^(positive|neutral|negative)$")
    trajectory: str = Field(..., pattern="^(improving|stable|declining)$")
    transitions: list[dict] = Field(default_factory=list)


class CallScorecardData(BaseModel):
    """Complete call scorecard."""
    call_id: str
    transcript_id: str
    sales_rep_id: str | None
    call_type: str
    call_outcome: str

    talk_ratio: TalkRatioAnalysis
    questions: QuestionPatternAnalysis
    objections: ObjectionHandlingAnalysis
    sentiment_flow: SentimentFlowAnalysis

    closing_attempts: int
    next_steps_clarity: int
    commitment_strength: str

    overall_score: int = Field(..., ge=0, le=100)
    conversion_likelihood: Decimal = Field(..., ge=0, le=1)


class TeamAnalyticsData(BaseModel):
    """Aggregated team performance data."""
    period_start: date
    period_end: date
    total_calls: int
    active_reps: int

    avg_talk_ratio: Decimal
    avg_question_score: Decimal
    avg_objection_score: Decimal
    avg_closing_score: Decimal
    avg_overall_score: Decimal

    conversion_rate: Decimal
    positive_sentiment_rate: Decimal

    top_performers: list[dict]
    improvement_opportunities: list[dict]
    trend_direction: str


class CoachingOpportunityCreate(BaseModel):
    """Coaching opportunity to create."""
    sales_rep_id: str
    opportunity_type: str = Field(..., pattern="^(talk_ratio|questioning|objections|closing)$")
    title: str = Field(..., min_length=10, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    current_performance: Decimal = Field(..., ge=0, le=100)
    target_performance: Decimal = Field(..., ge=0, le=100)
    performance_gap: Decimal
    priority: str = Field(..., pattern="^(critical|high|medium|low)$")
    sample_call_ids: list[str] = Field(default_factory=list, max_length=10)
    pattern_examples: list[str] = Field(default_factory=list, max_length=5)
    team_average: Decimal | None = None
    top_performer_average: Decimal | None = None
    percentile_rank: int | None = Field(None, ge=0, le=100)
    specific_actions: list[str] = Field(default_factory=list, max_length=5)
    training_resources: list[dict] = Field(default_factory=list)
    expected_impact: str | None = None
```

## Agent Implementation

### System Prompt

```python
SALES_CALL_ANALYTICS_SYSTEM_PROMPT = """You are an expert sales performance analyst specializing in team-level insights and coaching optimization. Your role is to analyze call performance patterns across the entire sales team and identify systematic improvement opportunities.

**Your Expertise:**
- Sales performance analytics and benchmarking
- Pattern recognition across large call datasets
- Coaching needs assessment and prioritization
- Statistical analysis of conversation dynamics
- Team performance optimization strategies

**Core Analysis Dimensions:**

**1. Talk-to-Listen Ratios**
- Ideal ratio: 30-40% sales rep, 60-70% prospect
- Excellent (<30%): Strong active listening
- Good (30-40%): Balanced conversation
- Too Much (40-60%): May be over-presenting
- Dominating (>60%): Not listening enough
- Track trends: Is rep improving over time?

**2. Question Effectiveness**
- Count and categorize: Open-ended, closed, discovery, pain-focused
- Quality indicators:
  - Open-ended questions drive deeper insights
  - Discovery questions uncover needs
  - Pain-focused questions build urgency
- Effectiveness score based on:
  - Question-to-statement ratio
  - Depth of prospect responses
  - Progression from surface to deep questions

**3. Objection Handling**
- Identify all objections (price, timing, competition, authority)
- Score handling technique:
  - Did rep acknowledge the objection?
  - Did they ask clarifying questions?
  - Was response relevant and confident?
  - Was objection resolved or deferred?
- Pattern analysis: Which objections are handled best/worst?

**4. Sentiment Flow**
- Track sentiment at opening, middle, closing
- Trajectory patterns:
  - Improving: Opening negative → Closing positive (best)
  - Stable: Consistent sentiment throughout
  - Declining: Opening positive → Closing negative (concerning)
- Identify triggers for sentiment shifts

**5. Closing Techniques**
- Count closing attempts (trial closes, assumptive language)
- Evaluate next steps clarity (specific date/time vs vague "follow up")
- Assess commitment strength (strong buy-in vs non-committal)
- Correlation with conversion outcomes

**Team-Level Analytics:**
- Compare individual performance to team averages
- Identify top performers and their distinguishing techniques
- Find systematic weaknesses across the team
- Spot coaching opportunities with highest ROI
- Track improvement trends over time

**Coaching Opportunity Identification:**
When performance gap > 15 points from team average:
- Critical priority: Gap > 30 points or declining trend
- High priority: Gap 20-30 points
- Medium priority: Gap 15-20 points
- Low priority: Gap < 15 points but worth noting

**Output Requirements:**
- Provide specific, data-driven insights
- Include concrete examples from call transcripts
- Quantify performance gaps and improvement potential
- Recommend prioritized coaching actions
- Track effectiveness of past coaching interventions

**Quality Standards:**
- All scores must be evidence-based from transcript analysis
- Comparisons must use statistically valid sample sizes (min 5 calls)
- Trends require minimum 3 data points
- Coaching recommendations must be actionable and specific"""
```

### Tool Definitions

```python
from typing import Any


async def analyze_talk_ratios(
    transcript_text: str,
    speaker_labels: list[str],
) -> dict[str, Any]:
    """
    Analyze talk time distribution between speakers.

    Args:
        transcript_text: Full call transcript with speaker labels
        speaker_labels: List of speaker identifiers [sales_rep, prospect]

    Returns:
        TalkRatioAnalysis with word counts, percentages, scores
    """
    # Count words per speaker
    # Calculate percentages
    # Score based on ideal 30-40% range
    pass


async def analyze_question_patterns(
    transcript_text: str,
    sales_rep_label: str,
) -> dict[str, Any]:
    """
    Identify and categorize questions asked during call.

    Args:
        transcript_text: Full call transcript
        sales_rep_label: Identifier for sales rep speaker

    Returns:
        QuestionPatternAnalysis with counts and effectiveness score
    """
    # Extract questions using Claude
    # Categorize: open/closed, discovery, pain-focused
    # Score based on quality and progression
    pass


async def analyze_objection_handling(
    transcript_text: str,
    sales_rep_label: str,
) -> dict[str, Any]:
    """
    Analyze how objections were identified and handled.

    Args:
        transcript_text: Full call transcript
        sales_rep_label: Identifier for sales rep speaker

    Returns:
        ObjectionHandlingAnalysis with scores and techniques
    """
    # Identify objections
    # Evaluate response quality
    # Score resolution effectiveness
    pass


async def analyze_sentiment_flow(
    transcript_text: str,
) -> dict[str, Any]:
    """
    Track sentiment progression through the call.

    Args:
        transcript_text: Full call transcript

    Returns:
        SentimentFlowAnalysis with opening/middle/closing sentiment
    """
    # Analyze sentiment at three stages
    # Identify trajectory pattern
    # Find sentiment transition triggers
    pass


async def generate_call_scorecard(
    transcript_id: str,
    transcript_text: str,
    call_context: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate comprehensive scorecard for single call.

    Args:
        transcript_id: UUID of transcript
        transcript_text: Full call transcript
        call_context: Metadata (call_type, duration, outcome)

    Returns:
        CallScorecardData with all metrics analyzed
    """
    # Run all analysis functions
    # Combine into comprehensive scorecard
    # Store in call_analytics table
    pass


async def generate_team_analytics(
    period_start: date,
    period_end: date,
) -> dict[str, Any]:
    """
    Generate team-level performance analytics for period.

    Args:
        period_start: Start date for analysis
        period_end: End date for analysis

    Returns:
        TeamAnalyticsData with aggregated metrics
    """
    # Query all calls in period
    # Aggregate scores across team
    # Identify top performers
    # Find improvement opportunities
    pass


async def identify_coaching_opportunities(
    sales_rep_id: str,
    lookback_days: int = 30,
) -> list[dict[str, Any]]:
    """
    Identify coaching opportunities for specific rep.

    Args:
        sales_rep_id: UUID of sales rep
        lookback_days: Days of history to analyze

    Returns:
        List of CoachingOpportunityCreate objects
    """
    # Get rep's call history
    # Compare to team averages
    # Identify significant gaps
    # Prioritize by impact potential
    pass


async def compare_top_performers(
    metric: str,
    top_n: int = 3,
) -> dict[str, Any]:
    """
    Compare top performers to identify best practices.

    Args:
        metric: Metric to compare (talk_ratio, questioning, objections, closing)
        top_n: Number of top performers to analyze

    Returns:
        Analysis of what top performers do differently
    """
    # Get top N performers for metric
    # Extract common patterns/techniques
    # Generate actionable insights
    pass
```

### Agent Class

```python
"""Meeting Sales Call Analytics Agent."""

import json
from datetime import datetime, date, timedelta
from typing import Any
from uuid import UUID

from anthropic import AsyncAnthropic
from pydantic import ValidationError

from src.agents.base_agent import BaseAgent
from src.config import Settings, get_agent_logger


class SalesCallAnalyticsAgent(BaseAgent):
    """
    Analyzes sales call performance at team level.

    Generates aggregate analytics, identifies patterns,
    benchmarks top performers, and creates coaching opportunities.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the Sales Call Analytics Agent.

        Args:
            settings: Application settings with API keys
        """
        super().__init__(
            name="sales_call_analytics",
            description="Team-level sales call analytics and coaching insights",
        )
        self.settings = settings
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Register tools
        self.register_tool(
            analyze_talk_ratios,
            "analyze_talk_ratios",
            "Analyze talk time distribution",
        )
        self.register_tool(
            analyze_question_patterns,
            "analyze_question_patterns",
            "Analyze question effectiveness",
        )
        self.register_tool(
            analyze_objection_handling,
            "analyze_objection_handling",
            "Analyze objection handling",
        )
        self.register_tool(
            analyze_sentiment_flow,
            "analyze_sentiment_flow",
            "Track sentiment progression",
        )
        self.register_tool(
            generate_call_scorecard,
            "generate_call_scorecard",
            "Generate comprehensive call scorecard",
        )
        self.register_tool(
            generate_team_analytics,
            "generate_team_analytics",
            "Generate team performance analytics",
        )
        self.register_tool(
            identify_coaching_opportunities,
            "identify_coaching_opportunities",
            "Identify coaching opportunities",
        )
        self.register_tool(
            compare_top_performers,
            "compare_top_performers",
            "Compare top performer techniques",
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for analytics."""
        return SALES_CALL_ANALYTICS_SYSTEM_PROMPT

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process incoming analytics task.

        Args:
            task: Task payload with type and parameters

        Returns:
            Processing result with analytics data

        Raises:
            ValueError: If required parameters missing
        """
        task_type = task.get("type")

        if task_type == "analyze_call":
            return await self._analyze_call(task)
        elif task_type == "generate_team_analytics":
            return await self._generate_team_analytics(task)
        elif task_type == "identify_coaching_opportunities":
            return await self._identify_coaching_opportunities(task)
        elif task_type == "compare_top_performers":
            return await self._compare_top_performers(task)
        elif task_type == "generate_daily_snapshot":
            return await self._generate_daily_snapshot(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _analyze_call(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze single call for analytics metrics.

        Steps:
        1. Extract transcript and metadata
        2. Run all analysis functions
        3. Generate comprehensive scorecard
        4. Store in call_analytics table
        5. Check if coaching opportunity identified

        Args:
            task: Task with transcript_id, transcript_text, call_context

        Returns:
            Analysis result with scorecard
        """
        transcript_id = task.get("transcript_id")
        transcript_text = task.get("transcript_text")
        call_context = task.get("call_context", {})

        if not transcript_id or not transcript_text:
            raise ValueError("transcript_id and transcript_text are required")

        start_time = datetime.utcnow()
        self.logger.info(
            "Analyzing call for analytics",
            extra={
                "transcript_id": transcript_id,
                "call_type": call_context.get("call_type"),
            },
        )

        try:
            # Generate comprehensive scorecard
            scorecard = await generate_call_scorecard(
                transcript_id=transcript_id,
                transcript_text=transcript_text,
                call_context=call_context,
            )

            # Store in database
            analytics_id = await self._store_call_analytics(scorecard)

            # Check for coaching opportunities
            if scorecard.get("sales_rep_id"):
                await self._check_coaching_opportunity(
                    scorecard["sales_rep_id"],
                    scorecard,
                )

            processing_duration_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            self.log_action(
                "call.analyzed",
                {
                    "transcript_id": transcript_id,
                    "analytics_id": analytics_id,
                    "overall_score": scorecard.get("overall_score"),
                    "processing_duration_ms": processing_duration_ms,
                },
            )

            return {
                "status": "completed",
                "transcript_id": transcript_id,
                "analytics_id": analytics_id,
                "scorecard": scorecard,
                "processing_duration_ms": processing_duration_ms,
            }

        except Exception as e:
            self.logger.error(
                "Error analyzing call",
                extra={"transcript_id": transcript_id, "error": str(e)},
            )
            raise

    async def _generate_team_analytics(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Generate team-level analytics for specified period.

        Args:
            task: Task with period_start, period_end, metric_period

        Returns:
            Team analytics data
        """
        period_start = task.get("period_start", date.today() - timedelta(days=7))
        period_end = task.get("period_end", date.today())
        metric_period = task.get("metric_period", "weekly")

        self.logger.info(
            "Generating team analytics",
            extra={
                "period_start": period_start,
                "period_end": period_end,
                "metric_period": metric_period,
            },
        )

        analytics_data = await generate_team_analytics(
            period_start=period_start,
            period_end=period_end,
        )

        # Store in analytics_metrics table
        metrics_id = await self._store_analytics_metrics(
            metric_type="team_performance",
            metric_period=metric_period,
            period_start=period_start,
            period_end=period_end,
            analytics_data=analytics_data,
        )

        self.logger.info(
            "Team analytics generated",
            extra={
                "metrics_id": metrics_id,
                "total_calls": analytics_data.get("total_calls"),
                "avg_score": analytics_data.get("avg_overall_score"),
            },
        )

        return {
            "status": "completed",
            "metrics_id": metrics_id,
            "period_start": period_start,
            "period_end": period_end,
            "analytics": analytics_data,
        }

    async def _identify_coaching_opportunities(
        self, task: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Identify coaching opportunities for rep or team.

        Args:
            task: Task with sales_rep_id (optional), lookback_days

        Returns:
            List of coaching opportunities
        """
        sales_rep_id = task.get("sales_rep_id")
        lookback_days = task.get("lookback_days", 30)

        if sales_rep_id:
            # Identify for specific rep
            opportunities = await identify_coaching_opportunities(
                sales_rep_id=sales_rep_id,
                lookback_days=lookback_days,
            )
        else:
            # Identify for entire team
            opportunities = await self._identify_team_coaching_opportunities(
                lookback_days
            )

        # Store opportunities in database
        created_count = 0
        for opp in opportunities:
            await self._store_coaching_opportunity(opp)
            created_count += 1

        self.logger.info(
            "Coaching opportunities identified",
            extra={
                "sales_rep_id": sales_rep_id,
                "opportunities_count": created_count,
            },
        )

        return {
            "status": "completed",
            "sales_rep_id": sales_rep_id,
            "opportunities": opportunities,
            "created_count": created_count,
        }

    async def _compare_top_performers(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Compare top performers to extract best practices.

        Args:
            task: Task with metric, top_n

        Returns:
            Comparison analysis
        """
        metric = task.get("metric", "overall_score")
        top_n = task.get("top_n", 3)

        self.logger.info(
            "Comparing top performers",
            extra={"metric": metric, "top_n": top_n},
        )

        comparison = await compare_top_performers(metric=metric, top_n=top_n)

        # Optionally store insights
        # Could create coaching_opportunities or best_practices records

        self.logger.info(
            "Top performer comparison completed",
            extra={"metric": metric, "patterns_found": len(comparison.get("patterns", []))},
        )

        return {
            "status": "completed",
            "metric": metric,
            "top_n": top_n,
            "comparison": comparison,
        }

    async def _generate_daily_snapshot(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Generate daily team performance snapshot.

        Args:
            task: Task with snapshot_date (optional)

        Returns:
            Snapshot data
        """
        snapshot_date = task.get("snapshot_date", date.today() - timedelta(days=1))

        self.logger.info(
            "Generating daily snapshot",
            extra={"snapshot_date": snapshot_date},
        )

        # Get analytics for the day
        analytics = await generate_team_analytics(
            period_start=snapshot_date,
            period_end=snapshot_date,
        )

        # Store in team_performance_snapshots
        snapshot_id = await self._store_team_snapshot(snapshot_date, analytics)

        self.logger.info(
            "Daily snapshot generated",
            extra={
                "snapshot_id": snapshot_id,
                "snapshot_date": snapshot_date,
            },
        )

        return {
            "status": "completed",
            "snapshot_id": snapshot_id,
            "snapshot_date": snapshot_date,
            "snapshot": analytics,
        }

    async def _store_call_analytics(self, scorecard: dict[str, Any]) -> str:
        """Store call analytics in database."""
        # Database insert logic
        pass

    async def _store_analytics_metrics(
        self,
        metric_type: str,
        metric_period: str,
        period_start: date,
        period_end: date,
        analytics_data: dict[str, Any],
    ) -> str:
        """Store analytics metrics in database."""
        # Database insert logic
        pass

    async def _store_coaching_opportunity(self, opportunity: dict[str, Any]) -> str:
        """Store coaching opportunity in database."""
        # Database insert logic
        pass

    async def _store_team_snapshot(
        self, snapshot_date: date, analytics: dict[str, Any]
    ) -> str:
        """Store team performance snapshot in database."""
        # Database insert logic
        pass

    async def _check_coaching_opportunity(
        self, sales_rep_id: str, scorecard: dict[str, Any]
    ) -> None:
        """Check if call reveals coaching opportunity."""
        # Compare scores to team average
        # If gap > 15 points, create coaching opportunity
        pass

    async def _identify_team_coaching_opportunities(
        self, lookback_days: int
    ) -> list[dict[str, Any]]:
        """Identify coaching opportunities across entire team."""
        # Query all reps
        # Identify gaps for each
        pass
```

## Error Handling

### Error Scenarios

1. **Insufficient Call Data**
   - Response: Return warning with minimum sample size needed
   - Action: Log issue, suggest extending analysis period

2. **Claude API Failure**
   - Response: Retry up to 3 times with exponential backoff
   - Action: Use cached aggregate data if available

3. **Invalid Transcript Format**
   - Response: Skip call, log error
   - Action: Alert monitoring for pattern of failures

4. **Database Query Timeouts**
   - Response: Implement query timeout (30s)
   - Action: Break large queries into batches

5. **Division by Zero in Calculations**
   - Response: Handle edge case (zero calls in period)
   - Action: Return null/N/A for metrics

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def _analyze_with_retry(
    self,
    transcript_text: str,
    analysis_function: callable,
) -> dict[str, Any]:
    """Execute analysis with automatic retry on failure."""
    return await analysis_function(transcript_text)
```

## Testing Requirements

### Coverage Target: >85%

### Unit Tests

**File:** `__tests__/unit/agents/sales_call_analytics/test_agent.py`

1. **Initialization**
   - Agent has correct name and description
   - All 8 tools registered
   - System prompt is set
   - Anthropic client initialized

2. **Talk Ratio Analysis**
   - Correctly counts words per speaker
   - Calculates percentages accurately
   - Scores based on ideal 30-40% range
   - Handles edge cases (one-sided calls)

3. **Question Pattern Analysis**
   - Identifies all questions in transcript
   - Categorizes correctly (open/closed, discovery, pain)
   - Calculates effectiveness score
   - Handles transcripts with no questions

4. **Objection Handling Analysis**
   - Detects objections in transcript
   - Evaluates acknowledgment and resolution
   - Scores handling technique
   - Handles calls with no objections

5. **Sentiment Flow Analysis**
   - Tracks sentiment at three stages
   - Identifies trajectory pattern
   - Finds transition triggers
   - Handles calls with consistent sentiment

6. **Team Analytics Generation**
   - Aggregates metrics across multiple calls
   - Calculates team averages correctly
   - Identifies top performers
   - Finds improvement opportunities

7. **Coaching Opportunity Identification**
   - Compares rep to team average
   - Identifies significant gaps (>15 points)
   - Prioritizes correctly
   - Generates actionable recommendations

8. **Error Handling**
   - Handles missing transcript gracefully
   - Validates sample size requirements
   - Retries on API failures
   - Logs errors with context

### Integration Tests

**File:** `__tests__/integration/test_sales_call_analytics_workflow.py`

1. **End-to-End Call Analysis**
   - Transcript → Analytics → Scorecard Storage
   - Coaching opportunity creation
   - Team metrics update

2. **Weekly Analytics Generation**
   - Queries 7 days of calls
   - Generates team-level insights
   - Stores in analytics_metrics table

3. **Agent Handoff**
   - Receives handoff from Transcript Processor
   - Provides insights to Performance Analyst
   - Triggers coaching alerts

### Fixtures

**File:** `__tests__/fixtures/sales_call_analytics_fixtures.py`

```python
import pytest
from decimal import Decimal


@pytest.fixture
def excellent_call_transcript() -> str:
    """High-quality sales call with excellent listening."""
    return """
    Sales Rep: Tell me about your current challenges.

    Prospect: We're drowning in manual processes. Our team spends 20 hours a week on data entry, and we still make mistakes. It's costing us deals because we can't respond quickly enough.

    Sales Rep: That sounds incredibly frustrating. Can you give me a specific example?

    Prospect: Last week, we lost a $50k deal because it took us 3 days to generate a proposal. The competitor responded in 24 hours.

    Sales Rep: Ouch. How often does this happen?

    Prospect: At least twice a month. We're probably losing $100k+ in revenue.

    Sales Rep: If we could cut that proposal time to 4 hours, what would that mean for your team?

    Prospect: Game-changing. We'd close 30% more deals, easily.

    Sales Rep: Let's schedule a demo for Thursday at 2 PM to show you exactly how we solve this.

    Prospect: Perfect. Send the invite.
    """


@pytest.fixture
def poor_call_transcript() -> str:
    """Low-quality call with rep dominating."""
    return """
    Sales Rep: Let me tell you about our amazing product. We have AI-powered automation, machine learning, cloud-based infrastructure, real-time analytics, custom integrations, enterprise security, 24/7 support, and we've helped 500+ companies. Our customers see 40% efficiency gains on average. We have features A, B, C, D, E, F, G, and H. [continues for 10 minutes]

    Prospect: Okay but how much does it—

    Sales Rep: Great question, but let me first show you our implementation process. We have a 4-week onboarding, dedicated customer success manager, training materials, and ongoing support. [continues for 5 more minutes]

    Prospect: I actually need to jump to another meeting.

    Sales Rep: Just 2 more minutes! Let me show you our pricing tiers.
    """


@pytest.fixture
def expected_excellent_scorecard() -> dict:
    """Expected scorecard for excellent call."""
    return {
        "talk_ratio": {
            "sales_rep_percentage": 28.0,
            "score": 95,
            "assessment": "excellent",
        },
        "questions": {
            "total_questions": 5,
            "open_ended": 4,
            "discovery": 3,
            "pain_focused": 2,
            "effectiveness_score": 92,
        },
        "objections": {
            "total_objections": 0,
            "score": 100,
        },
        "sentiment_flow": {
            "opening": "neutral",
            "middle": "negative",
            "closing": "positive",
            "trajectory": "improving",
        },
        "overall_score": 94,
    }


@pytest.fixture
def expected_poor_scorecard() -> dict:
    """Expected scorecard for poor call."""
    return {
        "talk_ratio": {
            "sales_rep_percentage": 87.0,
            "score": 15,
            "assessment": "dominating",
        },
        "questions": {
            "total_questions": 0,
            "effectiveness_score": 0,
        },
        "objections": {
            "total_objections": 2,
            "acknowledged": 0,
            "score": 10,
        },
        "sentiment_flow": {
            "opening": "neutral",
            "middle": "neutral",
            "closing": "negative",
            "trajectory": "declining",
        },
        "overall_score": 22,
    }
```

## Human-in-the-Loop

### Review Gates

**Gate 1: Coaching Opportunity Approval**
- **Trigger:** When coaching opportunity identified with priority "critical" or "high"
- **Reviewer:** Sales manager
- **Review UI:** Dashboard showing performance gap, sample calls, recommendations
- **Actions:** Approve and Assign, Modify Priority, Dismiss, Request More Data
- **Timeout:** Auto-approve "medium" and "low" priority after 48 hours

**Gate 2: Team Analytics Review**
- **Trigger:** Weekly team analytics generation
- **Reviewer:** Sales director
- **Review UI:** Analytics dashboard with trends, top performers, team averages
- **Actions:** Acknowledge, Request Deep Dive, Schedule Team Meeting
- **Timeout:** Auto-archive after 7 days

### Confidence Thresholds

- **Sample size < 5 calls:** Flag as "insufficient data", do not generate coaching opportunities
- **Sample size 5-10 calls:** Generate opportunities but mark as "limited confidence"
- **Sample size > 10 calls:** Full confidence, proceed with all actions

## Monitoring & Observability

### Metrics

1. **Analysis Volume**
   - Calls analyzed per day
   - Alert: <10 calls/day for 3 consecutive days

2. **Coaching Opportunity Generation**
   - Opportunities created per week
   - Alert: Zero opportunities for 2 consecutive weeks

3. **Performance Trend Tracking**
   - Week-over-week team score change
   - Alert: Declining trend for 3 consecutive weeks

4. **Processing Performance**
   - Analysis time per call (p50, p95)
   - Alert: p95 > 60 seconds

### Logging

```python
# Key log events
logger.info("Analyzing call for analytics", extra={"transcript_id": "...", "call_type": "..."})
logger.info("Call scorecard generated", extra={"overall_score": 85, "talk_ratio": 35.2})
logger.info("Team analytics generated", extra={"period": "...", "total_calls": 42})
logger.info("Coaching opportunity identified", extra={"sales_rep_id": "...", "gap": 23.5})
logger.error("Insufficient sample size", extra={"calls_found": 3, "required": 5})
```

## Performance Considerations

1. **Transcript Length:** Max 50,000 characters per call
2. **Batch Processing:** Team analytics run in batches of 100 calls
3. **Database Optimization:** Indexes on sales_rep_id, analyzed_at, call_outcome
4. **Caching:** Cache team averages for 1 hour to reduce query load
5. **Async Processing:** Use Celery for all analytics generation

## Cron Schedule

```python
# Hourly - Analyze new call transcripts
0 * * * * analyze_new_calls

# Daily at 2:00 AM - Generate daily team snapshot
0 2 * * * generate_daily_snapshot

# Weekly on Monday 6:00 AM - Generate weekly team analytics
0 6 * * 1 generate_weekly_analytics

# Weekly on Monday 7:00 AM - Identify coaching opportunities
0 7 * * 1 identify_team_coaching_opportunities

# Monthly on 1st at 8:00 AM - Generate monthly performance report
0 8 1 * * generate_monthly_report
```

## Success Metrics

1. **Analytics Coverage**: >95% of calls analyzed within 24 hours
2. **Coaching Effectiveness**: >60% of coaching opportunities show improvement
3. **Team Performance**: Month-over-month score improvement trend
4. **Top Performer Identification**: Successfully identify top 10% performers
5. **Insight Actionability**: >80% of generated insights lead to coaching actions

## Implementation Checklist

- [ ] Database tables created (call_analytics, analytics_metrics, coaching_opportunities, team_performance_snapshots)
- [ ] Agent class implemented with all tools
- [ ] System prompt defined and tested
- [ ] Talk ratio analysis function implemented
- [ ] Question pattern analysis function implemented
- [ ] Objection handling analysis function implemented
- [ ] Sentiment flow analysis function implemented
- [ ] Call scorecard generation implemented
- [ ] Team analytics aggregation implemented
- [ ] Coaching opportunity identification implemented
- [ ] Top performer comparison implemented
- [ ] Unit tests written (>85% coverage)
- [ ] Integration tests written
- [ ] Fixtures created
- [ ] Error handling implemented
- [ ] Retry logic implemented
- [ ] Logging configured
- [ ] Monitoring dashboards created
- [ ] Cron jobs scheduled
- [ ] Human approval gates configured
- [ ] Documentation complete
- [ ] Code review completed
- [ ] Performance testing completed

## Version History

- **v1.0.0**: Initial specification with core analytics capabilities
