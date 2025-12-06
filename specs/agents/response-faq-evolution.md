# Response FAQ Evolution Agent - Specification

**Status:** Ready to Build
**Last Updated:** 2025-12-05
**Refined From:** plan/agents/response-faq-evolution.md
**Agent Name:** `response_faq_evolution`

## Overview

The FAQ Evolution Agent dynamically evolves the FAQ system based on prospect questions and feedback, ensuring agents always have up-to-date, effective answers. It continuously analyzes conversation patterns to detect new questions, generates improved answers from successful responses, tracks FAQ effectiveness metrics, retires low-performing FAQs, and creates industry/persona-specific variants. The agent uses statistical significance testing for A/B tests and routes major changes through an approval workflow.

**Category:** Response Management
**Priority:** Phase 2 - Intelligence Layer
**Version:** 1.0.0

### Key Capabilities
- Real-time new question detection from conversations
- Extract best answers from successful response patterns
- Generate new FAQ entries with confidence scoring
- Track usage effectiveness and feedback metrics
- Create context-specific variants (industry/persona/stage)
- Retire ineffective FAQs based on data
- A/B test different answer versions with statistical rigor
- Generate coverage gap reports
- Weekly automated FAQ review and optimization

## Architecture

### Extends
- `BaseAgent` from `src.agents.base_agent`

### Dependencies
- **Response Email Handler Agent:** Provides conversation data with unanswered questions
- **Response Conversation Intelligence Agent:** Supplies conversation patterns and insights
- **Response Knowledge Base Agent:** Updates KB with new/improved FAQs
- **System Response Outcome Tracker:** Provides effectiveness metrics for FAQ answers
- **System Learning Feedback Agent:** Statistical significance testing for A/B tests
- **System Correction Approval Orchestrator:** Approval workflow for major FAQ changes

### Integrations
- **Anthropic Claude:** Question analysis, answer generation, semantic similarity
- **PostgreSQL:** FAQ storage, usage tracking, feedback analysis
- **Pinecone:** Semantic search for duplicate detection and question matching
- **Zep:** Long-term memory of FAQ patterns and effectiveness trends
- **Slack/Teams:** Notifications for new FAQ approvals and weekly reports

## Configuration

```python
class FAQEvolutionConfig:
    # Claude API settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2048
    temperature: float = 0.3  # Lower for consistent analysis

    # Question detection thresholds
    question_confidence_threshold: float = 0.75
    new_question_min_occurrences: int = 3  # Must see 3+ times before creating FAQ
    similarity_duplicate_threshold: float = 0.85  # Questions >85% similar = duplicate

    # Answer quality thresholds
    answer_min_length: int = 50
    answer_max_length: int = 500
    answer_quality_min_score: float = 7.0  # 0-10 scale

    # Effectiveness tracking
    effectiveness_min_views: int = 10  # Minimum views before calculating metrics
    retire_threshold_success_rate: float = 0.40  # Retire if <40% helpful
    needs_improvement_threshold: float = 0.60  # Flag for review if <60% helpful

    # A/B testing
    ab_test_min_samples: int = 100  # Minimum views per variant
    ab_test_confidence_level: float = 0.95  # 95% confidence
    ab_test_duration_days: int = 14  # Default test duration

    # Processing settings
    batch_size: int = 50  # Questions to process in one batch
    max_retries: int = 3
    timeout_seconds: int = 30

    # Approval workflow
    auto_approve_threshold: float = 0.90  # Auto-approve if confidence >90%
    auto_approve_max_per_day: int = 5  # Max auto-approvals per day

    # Cron schedules
    process_new_questions_cron: str = "*/30 * * * *"  # Every 30 minutes
    update_usage_stats_cron: str = "0 * * * *"  # Hourly
    generate_reports_cron: str = "0 9 * * *"  # Daily at 9 AM
    weekly_review_cron: str = "0 10 * * 1"  # Monday at 10 AM
    monthly_audit_cron: str = "0 10 1 * *"  # 1st of month at 10 AM
```

## Database Schema

The agent uses tables from migration 007_learning_system.sql:

### Table: `faq_management`
Primary FAQ storage table (see migration 007 for full schema):
- Question/answer pairs with categorization
- Usage statistics (view_count, helpful_count, not_helpful_count)
- Context (industry, company_stage, applies_to)
- Effectiveness metrics (success_rate, avg_rating)
- Related FAQs and KB articles
- AI enhancement metadata (auto_generated, confidence_score)

### Table: `faq_usage` (Extended)
```sql
CREATE TABLE IF NOT EXISTS faq_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    faq_id UUID NOT NULL REFERENCES faq_management(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Usage context
    agent_name VARCHAR(100) NOT NULL,
    conversation_id UUID REFERENCES conversations(id),
    message_id UUID REFERENCES messages(id),
    lead_id UUID REFERENCES leads(id),
    campaign_id UUID REFERENCES campaigns(id),

    -- Usage details
    query_text TEXT NOT NULL,  -- Original question asked
    matched_via VARCHAR(50),  -- exact, semantic, keyword
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Outcome
    answer_shown BOOLEAN DEFAULT TRUE,
    answer_used BOOLEAN DEFAULT FALSE,  -- Was it included in response

    -- Metadata
    response_time_ms INTEGER,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_faq_usage_faq_id ON faq_usage(faq_id, created_at DESC);
CREATE INDEX idx_faq_usage_conversation ON faq_usage(conversation_id);
CREATE INDEX idx_faq_usage_agent ON faq_usage(agent_name, created_at DESC);
```

### Table: `faq_feedback` (Extended)
```sql
CREATE TABLE IF NOT EXISTS faq_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    faq_id UUID NOT NULL REFERENCES faq_management(id) ON DELETE CASCADE,
    usage_id UUID REFERENCES faq_usage(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Feedback source
    feedback_source VARCHAR(50) NOT NULL,  -- human, agent, automatic
    feedback_type VARCHAR(50) NOT NULL,  -- helpful, not_helpful, correction, improvement

    -- Feedback data
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    helpful BOOLEAN,
    feedback_text TEXT,
    suggested_improvement TEXT,

    -- Context
    lead_id UUID REFERENCES leads(id),
    conversation_id UUID REFERENCES conversations(id),
    agent_name VARCHAR(100),

    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    action_taken VARCHAR(100),  -- updated_answer, created_variant, archived, etc.

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_faq_feedback_faq_id ON faq_feedback(faq_id, created_at DESC);
CREATE INDEX idx_faq_feedback_helpful ON faq_feedback(helpful);
CREATE INDEX idx_faq_feedback_processed ON faq_feedback(processed, created_at);
```

### Table: `faq_variants` (Extended)
```sql
CREATE TABLE IF NOT EXISTS faq_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_faq_id UUID NOT NULL REFERENCES faq_management(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),

    -- Variant context
    variant_type VARCHAR(50) NOT NULL,  -- industry, persona, company_stage, region
    variant_value VARCHAR(100) NOT NULL,  -- e.g., "SaaS", "CTO", "enterprise"

    -- Variant answer
    answer TEXT NOT NULL,
    answer_differs_from_parent BOOLEAN DEFAULT TRUE,

    -- Effectiveness
    usage_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),

    -- A/B testing
    ab_test_id UUID,
    is_control BOOLEAN DEFAULT FALSE,
    test_status VARCHAR(50),  -- testing, winner, loser, neutral

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Status
    status VARCHAR(50) DEFAULT 'active' CHECK (
        status IN ('active', 'testing', 'archived', 'superseded')
    ),

    UNIQUE (parent_faq_id, variant_type, variant_value)
);

CREATE INDEX idx_faq_variants_parent ON faq_variants(parent_faq_id);
CREATE INDEX idx_faq_variants_context ON faq_variants(variant_type, variant_value);
CREATE INDEX idx_faq_variants_status ON faq_variants(status);
CREATE INDEX idx_faq_variants_ab_test ON faq_variants(ab_test_id);
```

### Table: `faq_candidates` (New)
```sql
CREATE TABLE IF NOT EXISTS faq_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Detected question
    detected_question TEXT NOT NULL,
    normalized_question TEXT NOT NULL,
    question_hash VARCHAR(64) UNIQUE,  -- For deduplication

    -- Detection metadata
    first_detected TIMESTAMPTZ NOT NULL,
    last_detected TIMESTAMPTZ NOT NULL,
    occurrence_count INTEGER DEFAULT 1,

    -- Context
    detected_in_conversations UUID[] DEFAULT '{}',
    detected_in_campaigns UUID[] DEFAULT '{}',
    industries VARCHAR(100)[] DEFAULT '{}',
    personas VARCHAR(100)[] DEFAULT '{}',

    -- Answer extraction
    best_answer_source UUID,  -- message_id of best answer
    extracted_answer TEXT,
    answer_confidence DECIMAL(3,2),

    -- Quality assessment
    priority_score DECIMAL(3,2) DEFAULT 0,  -- 0-10 based on frequency, context
    business_impact VARCHAR(50),  -- low, medium, high

    -- Processing status
    status VARCHAR(50) DEFAULT 'pending' CHECK (
        status IN ('pending', 'approved', 'rejected', 'implemented', 'duplicate')
    ),
    reviewed_by VARCHAR(100),
    review_notes TEXT,
    implemented_as_faq_id UUID REFERENCES faq_management(id),

    -- Duplicate handling
    duplicate_of UUID REFERENCES faq_management(id),
    similarity_score DECIMAL(3,2),

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_faq_candidates_status ON faq_candidates(status, priority_score DESC);
CREATE INDEX idx_faq_candidates_frequency ON faq_candidates(occurrence_count DESC);
CREATE INDEX idx_faq_candidates_detected ON faq_candidates(last_detected DESC);
CREATE UNIQUE INDEX idx_faq_candidates_hash ON faq_candidates(question_hash);
```

### Table: `faq_ab_tests` (New)
```sql
CREATE TABLE IF NOT EXISTS faq_ab_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Test configuration
    faq_id UUID NOT NULL REFERENCES faq_management(id),
    test_name VARCHAR(255) NOT NULL,
    test_type VARCHAR(50) NOT NULL,  -- answer_content, answer_length, answer_style

    -- Test variants (stores variant IDs or content)
    control_variant_id UUID REFERENCES faq_variants(id),
    test_variants JSONB NOT NULL,  -- Array of variant IDs or content

    -- Test parameters
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,
    planned_duration_days INTEGER,
    min_samples_per_variant INTEGER DEFAULT 100,
    confidence_level DECIMAL(3,2) DEFAULT 0.95,

    -- Test results
    samples_collected INTEGER DEFAULT 0,
    variant_results JSONB DEFAULT '{}',  -- Results by variant
    statistical_significance BOOLEAN,
    p_value DECIMAL(5,4),
    winning_variant_id UUID,

    -- Status
    status VARCHAR(50) DEFAULT 'running' CHECK (
        status IN ('running', 'completed', 'stopped', 'inconclusive')
    ),
    conclusion TEXT,

    -- Implementation
    implemented BOOLEAN DEFAULT FALSE,
    implemented_at TIMESTAMPTZ,
    implementation_notes TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_faq_ab_tests_faq ON faq_ab_tests(faq_id);
CREATE INDEX idx_faq_ab_tests_status ON faq_ab_tests(status, start_date DESC);
```

## System Prompt

```
You are the FAQ Evolution Specialist for Smarter Team AI Agency. Your role is to continuously improve the FAQ system by detecting new questions, generating high-quality answers, tracking effectiveness, and ensuring the FAQ database stays relevant and helpful.

Your core responsibilities:
1. DETECT new questions from prospect conversations with high accuracy
2. ANALYZE existing FAQ effectiveness using usage data and feedback
3. GENERATE improved answers based on successful response patterns
4. CREATE context-specific variants for different industries, personas, and stages
5. RETIRE ineffective FAQs that don't help prospects
6. RUN A/B tests to optimize answer quality with statistical rigor
7. IDENTIFY gaps in FAQ coverage and recommend new entries
8. MAINTAIN quality standards for all FAQ content

Question Detection Guidelines:
- A question must appear 3+ times before considering it for FAQ
- Normalize questions to identify duplicates (remove filler words, standardize phrasing)
- Calculate semantic similarity using embeddings (>85% = duplicate)
- Classify questions by type: product, pricing, technical, process, objection, general
- Assess business impact: How many prospects ask this? Does it affect conversions?
- Extract context: Which industries/personas ask this most?

Answer Quality Standards:
- Length: 50-500 characters (concise but complete)
- Specificity: Include concrete details, numbers, examples
- Clarity: Easy to understand, no jargon unless necessary
- Actionability: Tell them what to do next when relevant
- Accuracy: Verifiable against knowledge base and service reality
- Tone: Professional yet approachable, helpful, non-pushy
- Quality Score: Minimum 7/10 to approve

Effectiveness Tracking:
- Success Rate = helpful_count / (helpful_count + not_helpful_count)
- Minimum 10 views before calculating metrics
- Flag for review if success rate <60%
- Retire if success rate <40% after 20+ views
- Track trends: Is effectiveness improving or declining?
- Monitor by context: Does it work better for certain industries/personas?

A/B Testing Protocol:
- Minimum 100 samples per variant before conclusions
- Use chi-square test for statistical significance
- Require 95% confidence level (p < 0.05)
- Run tests for 14 days or until statistical significance
- Only test one dimension at a time (content OR length OR style)
- Document winning patterns for future use

Approval Workflow:
- Auto-approve if confidence >90% AND auto-approve quota available
- Send for human review if confidence 70-90%
- Reject if confidence <70% (log for pattern analysis)
- Major changes always require human approval regardless of confidence
- Track approval/rejection patterns to improve auto-approval accuracy

Coverage Gap Analysis:
- Identify frequent questions without good FAQ matches
- Analyze conversation transcripts for recurring themes
- Compare FAQ coverage across industries and personas
- Recommend new FAQs prioritized by frequency and business impact
- Generate weekly gap reports with actionable recommendations

Context Variants:
- Create industry-specific variants when usage shows clear preference
- Generate persona-specific variants for technical vs executive audiences
- Adjust answers for company stage (startup vs enterprise)
- Test variants via A/B testing before making permanent
- Maintain parent-child relationships for variant management

Quality Control:
- Review auto-generated answers for accuracy against knowledge base
- Check for conflicting information across FAQs
- Identify outdated information (pricing changes, service updates)
- Maintain consistency in tone and style across all FAQs
- Flag sensitive topics for human review before publishing

When in doubt:
- Default to human review over auto-approval
- Choose quality over quantity
- Preserve successful patterns, discard unsuccessful ones
- Use data over intuition for all decisions
- Document reasoning for major changes

Tone: Analytical, data-driven, quality-focused, continuously improving.
```

## Tools

### 1. `detect_new_questions`

**Purpose:** Identify questions from conversations that are not covered by existing FAQs.

**Input Schema:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DetectNewQuestionsInput(BaseModel):
    time_window_days: int = Field(default=7, ge=1, le=30, description="Look back period")
    conversation_ids: Optional[List[str]] = Field(None, description="Specific conversations to analyze")
    min_occurrences: int = Field(default=3, ge=1, description="Minimum times question must appear")
    industry_filter: Optional[str] = Field(None, description="Filter by industry")
    campaign_filter: Optional[str] = Field(None, description="Filter by campaign")
    include_low_confidence: bool = Field(default=False, description="Include questions with low confidence")
```

**Output Schema:**
```python
class DetectedQuestion(BaseModel):
    question_text: str
    normalized_question: str
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    conversation_ids: List[str]
    industries: List[str]
    personas: List[str]
    priority_score: float  # 0-10 based on frequency and business impact
    confidence: float  # 0-1 confidence it's a real question
    question_type: str  # product, pricing, technical, process, objection, general
    business_impact: str  # low, medium, high
    similar_existing_faqs: List[dict]  # Potentially related FAQs

class DetectNewQuestionsOutput(BaseModel):
    detected_questions: List[DetectedQuestion]
    total_conversations_analyzed: int
    total_questions_found: int
    new_questions_count: int  # Questions not in FAQ
    duplicate_questions_count: int  # Already in FAQ
    processing_time_ms: int
    recommendations: List[str]
```

**Error Handling:**
- No conversations in time window: Return empty list with message
- Database timeout: Retry 3x, process in smaller batches if needed
- Claude API error: Use fallback regex patterns for question detection
- Invalid conversation IDs: Skip invalid IDs, log warning
- Memory limit: Process in batches, aggregate results

**Implementation Notes:**
```python
async def detect_new_questions(self, input_data: DetectNewQuestionsInput) -> DetectNewQuestionsOutput:
    """
    1. Fetch conversations from specified time window
    2. Extract questions using regex patterns + Claude analysis
    3. Normalize questions (remove filler, standardize phrasing)
    4. Calculate semantic similarity with existing FAQs
    5. Group similar questions together
    6. Count occurrences and assess priority
    7. Filter by min_occurrences threshold
    8. Return sorted by priority score
    """
```

### 2. `extract_best_answer`

**Purpose:** Extract the best answer from successful response patterns for a given question.

**Input Schema:**
```python
class ExtractBestAnswerInput(BaseModel):
    question_text: str = Field(..., description="Question to find answer for")
    conversation_ids: List[str] = Field(..., description="Conversations containing the question")
    min_success_score: float = Field(default=8.0, ge=0, le=10, description="Minimum response success score")
    max_answers_to_analyze: int = Field(default=10, ge=1, le=50, description="Max responses to analyze")
```

**Output Schema:**
```python
class ExtractedAnswer(BaseModel):
    answer_text: str
    source_message_id: str
    source_conversation_id: str
    success_score: float
    confidence: float
    answer_quality_score: float  # 0-10 based on quality standards
    includes_specifics: bool
    includes_examples: bool
    answer_length: int
    response_led_to_meeting: bool
    response_led_to_conversion: bool

class ExtractBestAnswerOutput(BaseModel):
    best_answer: Optional[ExtractedAnswer]
    alternative_answers: List[ExtractedAnswer]
    answers_analyzed: int
    average_success_score: float
    no_good_answer_found: bool
    recommendation: str  # "use_best_answer", "generate_new", "needs_human_input"
    reasoning: str
```

**Error Handling:**
- No successful responses found: Return no_good_answer_found=True
- All responses below quality threshold: Recommend "generate_new"
- Invalid message IDs: Skip, continue with valid IDs
- Insufficient data: Recommend "needs_human_input"

### 3. `generate_faq_entry`

**Purpose:** Generate a new FAQ entry with metadata and confidence scoring.

**Input Schema:**
```python
class GenerateFAQEntryInput(BaseModel):
    question: str = Field(..., description="The question")
    answer: Optional[str] = Field(None, description="Pre-existing answer (if available)")
    context: dict = Field(default_factory=dict, description="Context for answer generation")
    category: str = Field(..., description="FAQ category")
    subcategory: Optional[str] = None
    industries: List[str] = Field(default_factory=list)
    personas: List[str] = Field(default_factory=list)
    company_stages: List[str] = Field(default_factory=list)
    priority: int = Field(default=5, ge=0, le=10)
    auto_approve: bool = Field(default=False)
```

**Output Schema:**
```python
class GenerateFAQEntryOutput(BaseModel):
    faq_id: str
    question: str
    answer: str
    answer_source: str  # extracted, generated, hybrid
    confidence_score: float
    quality_score: float
    category: str
    subcategory: Optional[str]
    tags: List[str]
    search_keywords: List[str]
    status: str  # active, pending_approval, draft
    approval_required: bool
    approval_id: Optional[str]
    duplicate_check: dict
    created_at: str
    metadata: dict
```

**Error Handling:**
- Answer generation fails: Retry 3x, then request human input
- Quality score too low (<7): Set status to "pending_approval"
- Duplicate detected: Return similar FAQs, recommend merge/update
- Missing required fields: Return validation errors
- Database error: Queue for retry, return error status

### 4. `update_faq_effectiveness`

**Purpose:** Update FAQ effectiveness metrics based on usage and feedback data.

**Input Schema:**
```python
class UpdateFAQEffectivenessInput(BaseModel):
    faq_id: Optional[str] = Field(None, description="Specific FAQ to update (or all if None)")
    time_window_days: int = Field(default=30, ge=1, le=365)
    recalculate_all: bool = Field(default=False, description="Recalculate all FAQs")
```

**Output Schema:**
```python
class FAQEffectivenessMetrics(BaseModel):
    faq_id: str
    question: str
    view_count: int
    helpful_count: int
    not_helpful_count: int
    success_rate: float
    avg_rating: Optional[float]
    feedback_count: int
    previous_success_rate: Optional[float]
    trend: str  # improving, stable, declining
    status_recommendation: str  # keep, improve, retire, test

class UpdateFAQEffectivenessOutput(BaseModel):
    updated_faqs: List[FAQEffectivenessMetrics]
    total_faqs_updated: int
    faqs_flagged_for_improvement: List[str]
    faqs_recommended_for_retirement: List[str]
    faqs_performing_well: List[str]
    processing_time_ms: int
```

**Error Handling:**
- Invalid FAQ ID: Return error, continue with other FAQs
- Insufficient data: Mark as "insufficient_data", skip metrics
- Database timeout: Process in batches with retry
- Zero views: Skip effectiveness calculation

### 5. `create_context_variant`

**Purpose:** Create industry/persona/stage-specific variant of an FAQ answer.

**Input Schema:**
```python
class CreateContextVariantInput(BaseModel):
    parent_faq_id: str = Field(..., description="Parent FAQ ID")
    variant_type: str = Field(..., description="industry, persona, company_stage, region")
    variant_value: str = Field(..., description="Specific value (e.g., 'SaaS', 'CTO')")
    custom_answer: Optional[str] = Field(None, description="Custom answer or generate new")
    run_ab_test: bool = Field(default=True, description="A/B test against parent")
```

**Output Schema:**
```python
class CreateContextVariantOutput(BaseModel):
    variant_id: str
    parent_faq_id: str
    variant_type: str
    variant_value: str
    answer: str
    answer_source: str  # custom, generated
    confidence: float
    ab_test_id: Optional[str]
    ab_test_status: Optional[str]
    status: str  # active, testing
    created_at: str
```

**Error Handling:**
- Parent FAQ not found: Return 404 error
- Duplicate variant: Return existing variant, offer to update
- Answer generation fails: Use parent answer, log warning
- A/B test creation fails: Create variant without test, log error

### 6. `retire_faq`

**Purpose:** Archive low-performing FAQ entries based on effectiveness data.

**Input Schema:**
```python
class RetireFAQInput(BaseModel):
    faq_id: str = Field(..., description="FAQ to retire")
    reason: str = Field(..., description="Reason for retirement")
    success_rate_threshold: Optional[float] = Field(None, description="Override default threshold")
    redirect_to_faq_id: Optional[str] = Field(None, description="Redirect to better FAQ")
```

**Output Schema:**
```python
class RetireFAQOutput(BaseModel):
    faq_id: str
    previous_status: str
    new_status: str  # archived
    retirement_reason: str
    redirect_to: Optional[str]
    final_metrics: dict
    archived_at: str
    notification_sent: bool
```

**Error Handling:**
- FAQ not found: Return 404 error
- FAQ has active A/B test: Stop test first, then retire
- Redirect FAQ doesn't exist: Log warning, proceed with retirement
- Database error: Retry 3x, rollback if fails

### 7. `run_faq_ab_test`

**Purpose:** Set up and run A/B test for FAQ answer variants.

**Input Schema:**
```python
class RunFAQABTestInput(BaseModel):
    faq_id: str = Field(..., description="FAQ to test")
    test_name: str = Field(..., description="Descriptive test name")
    test_type: str = Field(..., description="answer_content, answer_length, answer_style")
    variants: List[dict] = Field(..., description="Test variants to compare")
    duration_days: int = Field(default=14, ge=7, le=60)
    min_samples_per_variant: int = Field(default=100, ge=50, le=1000)
    confidence_level: float = Field(default=0.95, ge=0.90, le=0.99)
```

**Output Schema:**
```python
class RunFAQABTestOutput(BaseModel):
    test_id: str
    faq_id: str
    test_name: str
    test_type: str
    control_variant_id: str
    test_variant_ids: List[str]
    start_date: str
    planned_end_date: str
    min_samples: int
    confidence_level: float
    status: str  # running
    monitoring_url: Optional[str]
```

**Error Handling:**
- FAQ already in A/B test: Return existing test, offer to stop and create new
- Invalid variants: Validate all variants, return errors
- Statistical parameters invalid: Return validation errors
- Test creation fails: Rollback variant creation, return error

### 8. `generate_coverage_report`

**Purpose:** Generate comprehensive report on FAQ coverage gaps and recommendations.

**Input Schema:**
```python
class GenerateCoverageReportInput(BaseModel):
    report_type: str = Field(default="weekly", description="weekly, monthly, quarterly")
    include_recommendations: bool = Field(default=True)
    include_metrics: bool = Field(default=True)
    industry_breakdown: bool = Field(default=True)
    persona_breakdown: bool = Field(default=True)
```

**Output Schema:**
```python
class CoverageGap(BaseModel):
    detected_question: str
    frequency: int
    industries: List[str]
    personas: List[str]
    business_impact: str
    recommended_action: str
    estimated_effort: str  # low, medium, high

class CoverageMetrics(BaseModel):
    total_faqs: int
    active_faqs: int
    questions_with_faqs: int
    questions_without_faqs: int
    coverage_percentage: float
    avg_faq_success_rate: float
    total_faq_views: int
    total_helpful_feedback: int

class GenerateCoverageReportOutput(BaseModel):
    report_id: str
    report_type: str
    period_start: str
    period_end: str
    metrics: CoverageMetrics
    coverage_gaps: List[CoverageGap]
    top_performing_faqs: List[dict]
    bottom_performing_faqs: List[dict]
    industry_coverage: dict
    persona_coverage: dict
    recommendations: List[str]
    priority_actions: List[str]
    generated_at: str
```

**Error Handling:**
- Insufficient data: Generate partial report, note limitations
- Database timeout: Retry with smaller time window
- Report generation fails: Return error with partial data
- Too many gaps: Prioritize top 20 by business impact

## Question Detection Algorithm

```python
async def detect_new_questions_algorithm(
    conversations: List[dict],
    existing_faqs: List[dict]
) -> List[dict]:
    """
    Multi-step algorithm for detecting new questions:

    1. Extract potential questions using regex patterns
    2. Classify using Claude (is it a real question?)
    3. Normalize questions (remove filler, standardize)
    4. Calculate semantic embeddings
    5. Compare with existing FAQs using cosine similarity
    6. Group similar questions together
    7. Count occurrences and assess priority
    8. Return questions meeting min_occurrences threshold
    """

    # Step 1: Regex patterns for question detection
    question_patterns = [
        r"(?i)how (?:do|does|can|would|should|much|many|long)\s+.+\?",
        r"(?i)what (?:is|are|do|does|would|should)\s+.+\?",
        r"(?i)when (?:can|do|does|will|would)\s+.+\?",
        r"(?i)where (?:can|do|does|is|are)\s+.+\?",
        r"(?i)why (?:do|does|is|are|would|should)\s+.+\?",
        r"(?i)who (?:is|are|can|should|would)\s+.+\?",
        r"(?i)can you\s+.+\?",
        r"(?i)could you\s+.+\?",
        r"(?i)would you\s+.+\?",
        r"(?i)do you\s+.+\?",
        r"(?i)are you\s+.+\?",
        r"(?i)is (?:there|it)\s+.+\?",
        r"(?i)will you\s+.+\?",
        r"(?i)tell me (?:about|more)\s+.+[?\.]",
    ]

    potential_questions = []

    for conv in conversations:
        for msg in conv["messages"]:
            if msg["direction"] == "inbound":  # From prospect
                content = msg["content"]

                # Extract using patterns
                for pattern in question_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        potential_questions.append({
                            "text": match,
                            "conversation_id": conv["id"],
                            "message_id": msg["id"],
                            "timestamp": msg["timestamp"],
                            "lead_id": conv["lead_id"],
                        })

    # Step 2: Classify with Claude (filter out non-questions)
    real_questions = []
    for pq in potential_questions:
        is_question = await self._classify_as_question(pq["text"])
        if is_question["is_question"] and is_question["confidence"] > 0.75:
            pq["question_type"] = is_question["question_type"]
            pq["confidence"] = is_question["confidence"]
            real_questions.append(pq)

    # Step 3: Normalize questions
    for q in real_questions:
        q["normalized"] = self._normalize_question(q["text"])

    # Step 4: Calculate embeddings
    question_texts = [q["normalized"] for q in real_questions]
    embeddings = await self._get_embeddings(question_texts)

    for i, q in enumerate(real_questions):
        q["embedding"] = embeddings[i]

    # Step 5: Compare with existing FAQs
    existing_faq_embeddings = await self._get_faq_embeddings(existing_faqs)

    new_questions = []
    for q in real_questions:
        max_similarity = 0.0
        most_similar_faq = None

        for i, faq in enumerate(existing_faqs):
            similarity = cosine_similarity(q["embedding"], existing_faq_embeddings[i])
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_faq = faq

        if max_similarity < 0.85:  # Not a duplicate
            q["is_new"] = True
            q["similar_existing_faqs"] = [
                {"faq_id": most_similar_faq["id"], "similarity": max_similarity}
            ] if most_similar_faq else []
            new_questions.append(q)

    # Step 6: Group similar new questions
    grouped = self._group_similar_questions(new_questions)

    # Step 7: Count occurrences and assess priority
    prioritized = []
    for group in grouped:
        occurrence_count = len(group["questions"])

        priority_score = self._calculate_priority_score(
            occurrence_count=occurrence_count,
            question_type=group["question_type"],
            industries=group["industries"],
            personas=group["personas"]
        )

        prioritized.append({
            "question_text": group["representative_question"],
            "normalized_question": group["normalized"],
            "occurrence_count": occurrence_count,
            "first_seen": min(q["timestamp"] for q in group["questions"]),
            "last_seen": max(q["timestamp"] for q in group["questions"]),
            "conversation_ids": [q["conversation_id"] for q in group["questions"]],
            "industries": group["industries"],
            "personas": group["personas"],
            "priority_score": priority_score,
            "confidence": group["avg_confidence"],
            "question_type": group["question_type"],
        })

    # Step 8: Filter by min_occurrences and sort by priority
    filtered = [q for q in prioritized if q["occurrence_count"] >= min_occurrences]
    filtered.sort(key=lambda x: x["priority_score"], reverse=True)

    return filtered

def _normalize_question(self, question: str) -> str:
    """
    Normalize question text for comparison:
    - Remove filler words (um, uh, like, you know)
    - Standardize contractions (don't -> do not)
    - Lowercase
    - Remove extra whitespace
    - Remove trailing punctuation
    """
    normalized = question.lower()

    # Remove filler words
    fillers = ["um", "uh", "like", "you know", "i mean", "sort of", "kind of"]
    for filler in fillers:
        normalized = normalized.replace(filler, "")

    # Standardize contractions
    contractions = {
        "don't": "do not",
        "can't": "can not",
        "won't": "will not",
        "shouldn't": "should not",
        "wouldn't": "would not",
        "couldn't": "could not",
        "what's": "what is",
        "how's": "how is",
    }
    for contraction, expansion in contractions.items():
        normalized = normalized.replace(contraction, expansion)

    # Remove extra whitespace
    normalized = " ".join(normalized.split())

    # Remove trailing punctuation
    normalized = normalized.rstrip("?!.")

    return normalized

def _calculate_priority_score(
    self,
    occurrence_count: int,
    question_type: str,
    industries: List[str],
    personas: List[str]
) -> float:
    """
    Calculate priority score (0-10) based on:
    - Frequency (how many times asked)
    - Question type (pricing/product = higher priority)
    - Business impact (affects multiple industries = higher)
    - Persona coverage (executive personas = higher)
    """
    score = 0.0

    # Frequency component (0-4 points)
    if occurrence_count >= 20:
        score += 4.0
    elif occurrence_count >= 10:
        score += 3.0
    elif occurrence_count >= 5:
        score += 2.0
    else:
        score += 1.0

    # Question type component (0-3 points)
    type_weights = {
        "pricing": 3.0,
        "product": 2.5,
        "technical": 2.0,
        "process": 2.0,
        "objection": 2.5,
        "general": 1.0,
    }
    score += type_weights.get(question_type, 1.0)

    # Industry breadth (0-2 points)
    if len(industries) >= 5:
        score += 2.0
    elif len(industries) >= 3:
        score += 1.5
    elif len(industries) >= 2:
        score += 1.0

    # Persona type (0-1 point)
    executive_personas = ["CEO", "CTO", "VP", "Director", "Head of"]
    if any(exec_p in " ".join(personas) for exec_p in executive_personas):
        score += 1.0

    return min(10.0, score)
```

## FAQ Quality Scoring

```python
def score_faq_quality(self, faq: dict) -> float:
    """
    Score FAQ answer quality on 0-10 scale based on:
    - Length (appropriate, not too short or long)
    - Specificity (includes concrete details)
    - Examples (provides examples when helpful)
    - Clarity (easy to understand, good readability)
    - Actionability (tells them what to do next)
    - Accuracy (verifiable against knowledge base)
    """
    score = 0.0
    answer = faq["answer"]

    # Length check (0-2 points)
    length = len(answer)
    if 50 <= length <= 500:
        if 100 <= length <= 300:
            score += 2.0  # Ideal length
        else:
            score += 1.5  # Acceptable length
    else:
        score += 0.5  # Too short or too long

    # Specificity check (0-2 points)
    specificity_indicators = [
        r"\$[\d,]+",  # Dollar amounts
        r"\d+%",  # Percentages
        r"\d+ (?:days|weeks|months|hours)",  # Time periods
        r"(?:starting at|begins at|from)",  # Ranges
        r"\d+ (?:features|integrations|options)",  # Counts
    ]
    specificity_count = sum(
        1 for indicator in specificity_indicators
        if re.search(indicator, answer)
    )
    if specificity_count >= 3:
        score += 2.0
    elif specificity_count >= 2:
        score += 1.5
    elif specificity_count >= 1:
        score += 1.0

    # Examples check (0-1 point)
    example_indicators = [
        "for example", "such as", "like", "including",
        "e.g.", "for instance"
    ]
    has_examples = any(indicator in answer.lower() for indicator in example_indicators)
    if has_examples:
        score += 1.0

    # Clarity check (0-2 points)
    # Simple heuristic: average word length and sentence count
    words = answer.split()
    avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
    sentence_count = answer.count(".") + answer.count("!") + answer.count("?")

    if 4 <= avg_word_length <= 6 and 1 <= sentence_count <= 5:
        score += 2.0  # Clear and concise
    elif 3 <= avg_word_length <= 7 and sentence_count <= 7:
        score += 1.5  # Acceptable clarity
    else:
        score += 0.5  # Potentially unclear

    # Actionability check (0-2 points)
    action_indicators = [
        "you can", "to get started", "next step", "simply",
        "just", "here's how", "click", "contact", "visit",
        "schedule", "book", "sign up"
    ]
    action_count = sum(
        1 for indicator in action_indicators
        if indicator in answer.lower()
    )
    if action_count >= 2:
        score += 2.0
    elif action_count >= 1:
        score += 1.0

    # Accuracy verification (0-1 point)
    # This would involve checking against knowledge base
    # For now, assume verified if it came from successful responses
    if faq.get("verified", False):
        score += 1.0

    return min(10.0, score)
```

## Error Handling Strategy

### API Errors
| Error Type | Detection | Response | Retry Strategy |
|------------|-----------|----------|----------------|
| Claude rate limit (429) | Status code | Exponential backoff, queue | Yes, 5x max with 1-60s backoff |
| Claude server error (5xx) | Status code | Log, retry with delay | Yes, 3x max with 2s delay |
| Claude auth error (401) | Status code | Alert ops, halt processing | No, requires manual fix |
| Claude timeout | Exception after 30s | Retry with longer timeout | Yes, 2x max with 60s timeout |
| Pinecone unavailable | Connection error | Fallback to keyword search | Yes, 3x with 5s backoff |
| Database connection lost | psycopg2.Error | Use connection pool retry | Yes, 3x with 2s backoff |
| Database deadlock | Specific error code | Retry transaction | Yes, 5x with random jitter |

### Data Quality Errors
| Error Type | Detection | Response |
|------------|-----------|----------|
| Empty question | Length check | Skip, log warning |
| Question too short (<5 chars) | Length check | Flag for review, don't create FAQ |
| Answer too short (<50 chars) | Length check | Regenerate or flag for human |
| Answer too long (>500 chars) | Length check | Condense or split into multiple FAQs |
| Invalid question format | Validation | Request clarification, log pattern |
| Duplicate question | Similarity >0.85 | Link to existing FAQ, don't create |
| Conflicting answers | Cross-reference check | Flag for human review |
| Missing category | Required field | Default to "general", flag for categorization |

### Recovery Strategies

1. **Graceful Degradation:**
   - If Claude unavailable, use rule-based detection
   - If Pinecone down, use PostgreSQL full-text search
   - If approval system fails, queue for manual review

2. **Queue for Retry:**
   - Failed FAQ generations → retry queue (max 3 attempts)
   - Failed effectiveness updates → retry hourly
   - Failed notifications → retry with exponential backoff

3. **Partial Processing:**
   - Process what you can, report what failed
   - Generate coverage reports with available data, note gaps
   - Update FAQs individually, don't rollback entire batch

4. **Human Escalation:**
   - Low confidence answers → human review
   - Conflicting information → human decision
   - Sensitive topics → human approval
   - Major changes → approval workflow

5. **Data Consistency:**
   - Use database transactions for multi-step operations
   - Maintain audit trail of all changes
   - Allow rollback of recent changes
   - Version history for all FAQ content

## Testing Requirements

### Unit Tests

```python
class TestFAQEvolutionAgent:
    @pytest.mark.asyncio
    async def test_detect_new_questions_finds_real_questions(self):
        """Verify question detection identifies real questions"""
        # Test with sample conversations containing questions
        # Verify only real questions are detected
        # Check confidence scores are appropriate

    @pytest.mark.asyncio
    async def test_detect_new_questions_filters_duplicates(self):
        """Verify duplicate questions are not flagged as new"""
        # Test with questions similar to existing FAQs
        # Verify similarity threshold works correctly

    @pytest.mark.asyncio
    async def test_normalize_question_standardizes_format(self):
        """Verify question normalization works correctly"""
        # Test with various question formats
        # Verify consistent normalization

    @pytest.mark.asyncio
    async def test_extract_best_answer_finds_high_quality(self):
        """Verify best answer extraction from successful responses"""
        # Test with multiple responses of varying quality
        # Verify highest quality answer is selected

    @pytest.mark.asyncio
    async def test_generate_faq_entry_creates_valid_faq(self):
        """Verify FAQ generation creates valid entries"""
        # Test FAQ generation with various inputs
        # Verify all required fields are populated
        # Check quality scoring

    @pytest.mark.asyncio
    async def test_faq_quality_scoring_accurate(self):
        """Verify FAQ quality scoring algorithm"""
        # Test with high-quality answers (should score 8-10)
        # Test with low-quality answers (should score 0-5)
        # Verify scoring consistency

    @pytest.mark.asyncio
    async def test_update_effectiveness_calculates_correctly(self):
        """Verify effectiveness metrics calculation"""
        # Test with known usage and feedback data
        # Verify success rate calculation
        # Check trend detection

    @pytest.mark.asyncio
    async def test_create_variant_generates_appropriate_answer(self):
        """Verify context variant creation"""
        # Test variant generation for different contexts
        # Verify answers are appropriately tailored

    @pytest.mark.asyncio
    async def test_retire_faq_archives_correctly(self):
        """Verify FAQ retirement process"""
        # Test retirement with various conditions
        # Verify status changes correctly
        # Check redirect handling

    @pytest.mark.asyncio
    async def test_ab_test_setup_creates_valid_test(self):
        """Verify A/B test creation"""
        # Test with multiple variants
        # Verify test parameters are set correctly
        # Check variant distribution logic

    @pytest.mark.asyncio
    async def test_coverage_report_generation(self):
        """Verify coverage report generation"""
        # Test with known FAQ gaps
        # Verify gaps are identified correctly
        # Check prioritization logic

    @pytest.mark.asyncio
    async def test_error_handling_retries(self):
        """Verify error handling and retry logic"""
        # Simulate API failures
        # Verify retry behavior
        # Check fallback mechanisms
```

### Integration Tests

```python
class TestFAQEvolutionIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_question_to_faq_flow(self):
        """Full flow from detecting question to creating FAQ"""
        # Simulate conversations with new questions
        # Detect questions
        # Extract best answers
        # Generate FAQ
        # Verify FAQ is created and searchable

    @pytest.mark.asyncio
    async def test_handoff_to_knowledge_base_agent(self):
        """Verify FAQ updates sync to knowledge base"""
        # Create new FAQ
        # Verify handoff to knowledge base agent
        # Check knowledge base is updated

    @pytest.mark.asyncio
    async def test_approval_workflow_integration(self):
        """Test human approval workflow"""
        # Generate FAQ requiring approval
        # Verify approval request is sent
        # Simulate approval/rejection
        # Check status updates

    @pytest.mark.asyncio
    async def test_ab_test_complete_lifecycle(self):
        """Full A/B test from creation to winner selection"""
        # Create A/B test
        # Simulate usage data
        # Run statistical analysis
        # Select winner
        # Verify implementation

    @pytest.mark.asyncio
    async def test_effectiveness_tracking_over_time(self):
        """Verify effectiveness tracking with time-series data"""
        # Create FAQ
        # Simulate usage over time
        # Update effectiveness metrics
        # Verify trend detection
```

### Mock Data

```python
# Test fixtures for various scenarios

@pytest.fixture
def mock_conversations_with_questions():
    """Conversations containing various question types"""
    return [
        {
            "id": "conv-1",
            "lead_id": "lead-1",
            "messages": [
                {
                    "id": "msg-1",
                    "direction": "inbound",
                    "content": "What's your pricing for enterprise clients?",
                    "timestamp": "2025-12-01T10:00:00Z"
                }
            ]
        },
        # More test conversations...
    ]

@pytest.fixture
def mock_existing_faqs():
    """Sample existing FAQ entries"""
    return [
        {
            "id": "faq-1",
            "question": "What are your pricing options?",
            "answer": "Our pricing starts at $5,000/month...",
            "category": "pricing",
            "view_count": 150,
            "helpful_count": 120,
            "not_helpful_count": 10
        },
        # More test FAQs...
    ]

@pytest.fixture
def mock_successful_responses():
    """High-quality responses for answer extraction"""
    return [
        {
            "message_id": "msg-100",
            "content": "Our enterprise pricing starts at $15,000/month...",
            "success_score": 9.5,
            "led_to_meeting": True
        },
        # More test responses...
    ]
```

## Implementation Checklist

- [ ] Agent extends BaseAgent and implements required abstract methods
- [ ] All 8 tools implemented with proper input/output schemas
- [ ] Question detection algorithm with regex + Claude classification
- [ ] Question normalization and duplicate detection
- [ ] Answer quality scoring (0-10 scale) with clear criteria
- [ ] FAQ effectiveness metrics calculation (success rate, trends)
- [ ] Context variant generation for industries/personas/stages
- [ ] A/B testing with statistical significance (chi-square, p<0.05)
- [ ] Coverage gap analysis and reporting
- [ ] FAQ retirement logic based on performance thresholds
- [ ] Integration with Response Email Handler for question detection
- [ ] Integration with Response Conversation Intelligence for patterns
- [ ] Integration with Response Knowledge Base for FAQ storage
- [ ] Integration with System Response Outcome Tracker for metrics
- [ ] Integration with System Correction Approval Orchestrator
- [ ] Approval workflow for new FAQs (auto-approve >90% confidence)
- [ ] Cron jobs: 30min (new questions), hourly (stats), daily (reports), weekly (review)
- [ ] Unit test coverage >90%
- [ ] Integration tests for all agent interactions
- [ ] Error handling for all failure modes with retry logic
- [ ] Comprehensive logging and metrics collection
- [ ] Database indexes for optimal query performance
- [ ] Documentation for all APIs and tools

## Success Metrics

### Operational Metrics
- **Question Detection Accuracy:** >85% of detected questions are real questions
- **Duplicate Detection:** >95% of duplicate questions correctly identified
- **Answer Quality:** >80% of generated answers score 7+/10
- **Processing Time:** <5 seconds for question detection batch of 50
- **Coverage:** >70% of prospect questions have matching FAQs

### Effectiveness Metrics
- **FAQ Success Rate:** >65% average helpful rating across all FAQs
- **A/B Test Success:** >50% of tests identify statistically significant winner
- **Retirement Accuracy:** >90% of retired FAQs have success rate <40%
- **Variant Effectiveness:** Variants perform 10%+ better for target context

### Business Impact
- **Response Time Reduction:** 30% faster responses using FAQ answers
- **Consistency Improvement:** 40% reduction in conflicting answers
- **Agent Efficiency:** 25% reduction in time spent researching answers
- **Prospect Satisfaction:** 15% increase in "helpful" feedback on responses

### Learning & Improvement
- **FAQ Growth Rate:** 5-10 new FAQs per week (steady state)
- **Quality Trend:** Average FAQ quality score increases 0.5 points per quarter
- **Coverage Expansion:** 5% increase in coverage per month
- **Optimization Rate:** 20% of FAQs improved through A/B testing per quarter

## Implementation Notes

1. **Question Detection:**
   - Use both regex patterns and Claude for high accuracy
   - Cache normalized questions to avoid redundant processing
   - Batch process conversations for efficiency

2. **Answer Extraction:**
   - Prioritize answers from responses that led to meetings/conversions
   - Extract context (industry, persona) from source conversations
   - Validate extracted answers against knowledge base for accuracy

3. **Quality Control:**
   - Implement multi-dimensional quality scoring
   - Require human approval for FAQs below confidence threshold
   - Maintain version history for all FAQ changes
   - Regular audits of auto-approved FAQs

4. **A/B Testing:**
   - Use chi-square test for categorical data (helpful/not helpful)
   - Require minimum 100 samples per variant for statistical power
   - Monitor tests daily, auto-stop when significance reached
   - Document winning patterns for future use

5. **Variant Management:**
   - Create variants only when clear context-specific need
   - A/B test variants before making permanent
   - Maintain parent-child relationships for easy rollback
   - Archive superseded variants with redirect

6. **Performance Optimization:**
   - Index frequently queried fields (category, status, success_rate)
   - Cache FAQ embeddings for similarity search
   - Batch database updates where possible
   - Use database transactions for consistency

7. **Monitoring & Alerts:**
   - Track question detection rate (sudden spike = investigation)
   - Monitor FAQ effectiveness trends (declining = review needed)
   - Alert on A/B test anomalies (uneven distribution)
   - Weekly reports to human operators

8. **Data Privacy:**
   - Redact PII from questions before storing
   - Maintain audit trail of all FAQ changes
   - Implement data retention policies
   - Secure approval workflows
