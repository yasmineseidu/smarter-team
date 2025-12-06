# Campaign Send Agent - Production Specification

## Agent Identity

**Name**: `campaign_send_agent`

**Category**: Campaign & Outreach

**Purpose**: Quality control agent that reviews and validates personalization lines before sending campaigns, ensuring accuracy, tone, and relevance while logging corrections for continuous learning.

## Role & Responsibilities

The Send Agent acts as the final quality checkpoint before leads are released to email campaigns. It is the "human-in-the-loop" replacement that systematically reviews AI-generated personalization to prevent hallucinations, creepy personalization, and generic claims.

**Core Functions**:
- Review personalization lines with confidence scores <80
- Verify all claims against source research data
- Check tone for human-sounding, non-creepy language
- Validate source citations exist and are accurate
- Correct issues and log all changes for AI learning
- Approve/reject leads for campaign release
- Release approved leads to Instantly campaigns

## System Prompt

```
You are a quality control specialist reviewing AI-generated personalization lines for cold email campaigns.

Your role is to ensure every personalization line is:
1. ACCURATE - All claims match the research data exactly
2. HUMAN-SOUNDING - Conversational, not robotic or creepy
3. RELEVANT - Actually personalized, not generic praise
4. SOURCED - Has valid citation to specific source

REVIEW CRITERIA:

Accuracy:
- Check every claim against research_data
- Flag any statements not supported by sources
- Reject if confidence_score < 80 AND no research backing

Tone:
- Reject creepy personalization ("I noticed you...")
- Reject excessive flattery ("your impressive growth")
- Approve conversational mentions ("Saw your post on AI agents")
- Maximum 1 sentence, keep it brief and casual

Relevance:
- Reject generic claims without specifics ("your recent award" - which award?)
- Approve specific mentions ("your Q3 revenue increase to $2M")
- Ensure it relates to the pitch topic

Source Validation:
- Every line must have source_citation field
- Citation format: "LinkedIn post Nov 15" or "TechCrunch interview Oct 2024"
- Reject if citation is vague or missing

CORRECTION ACTIONS:

For each review, you MUST:
1. Return verdict: "approved" or "rejected"
2. If rejected, provide corrected_line (or null if unfixable)
3. List all issues found (accuracy, tone, relevance, source)
4. Provide correction_reason explaining what was wrong
5. Suggest improvement_notes for the AI to learn from

EXAMPLES:

REJECT - Generic:
Original: "I was impressed by your company's growth"
Issue: Vague, no specifics, sounds like spam
Correction: "Saw your Series A announcement last month - congrats on the $5M raise"

REJECT - Creepy:
Original: "I've been following your career trajectory and noticed you recently..."
Issue: Sounds like stalking
Correction: "Caught your podcast on SaaS metrics last week"

APPROVE - Good:
Line: "Saw your LinkedIn post about switching to async standups"
Source: "LinkedIn post Nov 15, 2024"
Reason: Specific, casual tone, verifiable source

Your corrections train the personalization AI. Be thorough but efficient - you'll review batches of 50-100 leads.
```

## Input Schema

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PersonalizationReview(BaseModel):
    """Input for reviewing a personalization line."""

    lead_id: str = Field(..., description="UUID of lead being reviewed")
    personalization_line: str = Field(..., description="AI-generated personalization line")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="AI confidence (0-100)")
    source_citation: Optional[str] = Field(None, description="Source reference for claim")
    research_data: dict = Field(..., description="Lead research data for verification")
    campaign_id: str = Field(..., description="Instantly campaign ID")

class BatchReview(BaseModel):
    """Batch of personalization lines to review."""

    batch_id: str = Field(..., description="UUID for this review batch")
    reviews: list[PersonalizationReview] = Field(..., min_items=1, max_items=100)
    priority: str = Field(default="normal", pattern="^(critical|high|normal|low)$")
```

## Output Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class ReviewVerdict(BaseModel):
    """Result of reviewing a single personalization line."""

    lead_id: str
    verdict: Literal["approved", "rejected"] = Field(..., description="Approval decision")
    corrected_line: Optional[str] = Field(None, description="Corrected version if rejected")
    issues_found: list[str] = Field(default_factory=list, description="List of issues: accuracy, tone, relevance, source")
    correction_reason: Optional[str] = Field(None, description="Why it was corrected")
    improvement_notes: Optional[str] = Field(None, description="Learning notes for AI")
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)

class BatchReviewResult(BaseModel):
    """Results from batch review."""

    batch_id: str
    approved_count: int
    rejected_count: int
    corrected_count: int
    verdicts: list[ReviewVerdict]
    processed_at: datetime = Field(default_factory=datetime.utcnow)
```

## Tools

### 1. `verify_research_claim`

**Purpose**: Check if a claim in the personalization line is supported by research data.

**Parameters**:
```python
claim: str  # The claim to verify (e.g., "raised $5M Series A")
research_data: dict  # Lead research data with sources
```

**Returns**:
```python
{
    "is_verified": bool,
    "confidence": float,  # 0.0 - 1.0
    "supporting_source": Optional[str],  # Source that backs the claim
    "discrepancies": list[str]  # Any conflicts found
}
```

**Implementation**:
- Extract key facts from claim (entities, dates, numbers)
- Search research_data for matching information
- Compare for exact matches vs. close matches
- Return confidence score based on match quality
- Flag discrepancies (e.g., wrong date, wrong amount)

### 2. `validate_tone`

**Purpose**: Analyze tone of personalization line for human-sounding quality.

**Parameters**:
```python
personalization_line: str  # Line to analyze
```

**Returns**:
```python
{
    "is_acceptable": bool,
    "tone_score": float,  # 0.0 - 1.0 (higher = more human)
    "issues": list[str],  # Specific tone problems
    "suggestions": list[str]  # How to improve
}
```

**Implementation**:
- Check for creepy patterns ("I noticed you...", "I've been following...")
- Detect excessive flattery ("impressive", "amazing", "revolutionary")
- Validate brevity (max 1-2 sentences, <125 chars ideal)
- Check for natural language vs. robotic phrasing
- Return specific issues and suggestions

### 3. `check_source_citation`

**Purpose**: Validate that source citation exists and is specific enough.

**Parameters**:
```python
source_citation: Optional[str]  # Citation to validate
research_data: dict  # Available sources
```

**Returns**:
```python
{
    "is_valid": bool,
    "citation_quality": float,  # 0.0 - 1.0
    "issues": list[str],
    "source_exists": bool,  # Is the source in research_data?
    "specificity": str  # "specific", "vague", or "missing"
}
```

**Implementation**:
- Check if citation is provided
- Validate format (e.g., "LinkedIn post Nov 15" vs. "social media")
- Verify source exists in research_data
- Check specificity (date, platform, event name)
- Return quality score and issues

### 4. `log_correction`

**Purpose**: Store correction in database for AI learning feedback loop.

**Parameters**:
```python
lead_id: str
original_line: str
corrected_line: Optional[str]
issues: list[str]
correction_reason: str
improvement_notes: str
confidence_score: float
```

**Returns**:
```python
{
    "correction_id": str,
    "logged_at": datetime,
    "status": "success"
}
```

**Implementation**:
- Write to `correction_logs` table with all metadata
- Link to personalization_lines table via lead_id
- Tag with issue categories for analytics
- Store improvement_notes for periodic AI retraining
- Return confirmation with correction ID

### 5. `release_to_campaign`

**Purpose**: Release approved leads to Instantly campaign.

**Parameters**:
```python
lead_ids: list[str]  # Approved lead IDs
campaign_id: str  # Instantly campaign ID
```

**Returns**:
```python
{
    "released_count": int,
    "failed_count": int,
    "instantly_response": dict,
    "errors": list[dict]  # Any failures with reasons
}
```

**Implementation**:
- Call Instantly API to add leads to campaign
- Map personalization_line to {{personalization}} variable
- Handle Instantly API errors gracefully
- Update lead status to "in_campaign" in database
- Log release event for audit trail
- Return summary with any failures

### 6. `batch_review`

**Purpose**: Process a batch of personalization lines efficiently.

**Parameters**:
```python
batch: BatchReview  # Batch of reviews to process
```

**Returns**:
```python
{
    "batch_id": str,
    "results": BatchReviewResult,
    "processing_time": float,  # seconds
    "approval_rate": float  # percentage
}
```

**Implementation**:
- Iterate through all reviews in batch
- For each: verify claim, validate tone, check citation
- Use Claude to make approval decision based on criteria
- Generate corrected_line for rejected items
- Collect all verdicts
- Return batch results with statistics

## Database Schema

### `send_agent_reviews`

```sql
CREATE TABLE send_agent_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    batch_id UUID NOT NULL,
    personalization_line TEXT NOT NULL,
    confidence_score NUMERIC(5,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),
    source_citation TEXT,
    verdict VARCHAR(20) NOT NULL CHECK (verdict IN ('approved', 'rejected')),
    corrected_line TEXT,
    issues_found TEXT[], -- array of issue types
    correction_reason TEXT,
    improvement_notes TEXT,
    reviewed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    reviewer_agent VARCHAR(50) NOT NULL DEFAULT 'campaign_send_agent',

    -- Analytics
    review_duration_ms INTEGER,

    -- Indexes
    INDEX idx_lead_id (lead_id),
    INDEX idx_batch_id (batch_id),
    INDEX idx_verdict (verdict),
    INDEX idx_reviewed_at (reviewed_at)
);
```

### `correction_logs`

```sql
CREATE TABLE correction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    review_id UUID NOT NULL REFERENCES send_agent_reviews(id),

    -- Original vs. corrected
    original_line TEXT NOT NULL,
    corrected_line TEXT,
    original_confidence NUMERIC(5,2),

    -- Issue classification
    issue_categories TEXT[] NOT NULL, -- ['accuracy', 'tone', 'relevance', 'source']
    correction_reason TEXT NOT NULL,
    improvement_notes TEXT NOT NULL,

    -- Learning metadata
    correction_type VARCHAR(50), -- 'hallucination', 'tone_improvement', 'specificity', etc.
    severity VARCHAR(20) CHECK (severity IN ('critical', 'major', 'minor')),

    -- Timestamps
    logged_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- AI feedback loop
    applied_to_training BOOLEAN DEFAULT FALSE,
    training_applied_at TIMESTAMP,

    -- Indexes
    INDEX idx_lead_id (lead_id),
    INDEX idx_issue_categories USING GIN (issue_categories),
    INDEX idx_correction_type (correction_type),
    INDEX idx_logged_at (logged_at),
    INDEX idx_training_status (applied_to_training, training_applied_at)
);
```

### `campaign_releases`

```sql
CREATE TABLE campaign_releases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL,
    lead_id UUID NOT NULL REFERENCES leads(id),
    campaign_id VARCHAR(100) NOT NULL, -- Instantly campaign ID

    -- Release details
    personalization_line TEXT NOT NULL,
    released_at TIMESTAMP NOT NULL DEFAULT NOW(),
    release_status VARCHAR(20) NOT NULL CHECK (release_status IN ('success', 'failed')),

    -- Instantly response
    instantly_lead_id VARCHAR(100),
    instantly_response JSONB,
    error_message TEXT,

    -- Indexes
    INDEX idx_batch_id (batch_id),
    INDEX idx_lead_id (lead_id),
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_release_status (release_status),
    INDEX idx_released_at (released_at)
);
```

## Integration: Instantly API

### Client Implementation

```python
from src.integrations.base import BaseIntegrationClient
from typing import Any

class InstantlyClient(BaseIntegrationClient):
    """Client for Instantly.ai campaign API."""

    def __init__(self, api_key: str):
        super().__init__(
            name="instantly",
            base_url="https://api.instantly.ai/api/v1",
            api_key=api_key,
            timeout=30.0
        )

    async def add_leads_to_campaign(
        self,
        campaign_id: str,
        leads: list[dict],
    ) -> dict[str, Any]:
        """
        Add leads to Instantly campaign with personalization variables.

        Args:
            campaign_id: Instantly campaign ID
            leads: List of lead dicts with email, personalization, etc.

        Returns:
            API response with success/failure counts
        """
        payload = {
            "campaign_id": campaign_id,
            "leads": leads
        }

        return await self.post(
            "/campaigns/leads/add",
            json=payload
        )

    async def get_campaign_status(self, campaign_id: str) -> dict[str, Any]:
        """Get campaign status and stats."""
        return await self.get(f"/campaigns/{campaign_id}")
```

## Workflow

### Phase 1: Batch Collection

```python
# Triggered by Celery task or API endpoint
# Input: Leads with personalization lines ready for review

1. Query database for personalization_lines where:
   - confidence_score < 80 OR
   - never_reviewed = true OR
   - random_sample (10% of high-confidence)

2. Group into batches of 50-100 leads
3. Create batch_id for tracking
4. Load research_data for each lead
5. Pass to process_task()
```

### Phase 2: Review Process

```python
async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
    """Process batch review task."""

    # 1. Parse input
    batch = BatchReview(**task)

    # 2. Review each personalization line
    verdicts = []
    for review in batch.reviews:
        # Verify claim against research
        claim_check = await self.verify_research_claim(
            claim=review.personalization_line,
            research_data=review.research_data
        )

        # Validate tone
        tone_check = await self.validate_tone(
            personalization_line=review.personalization_line
        )

        # Check source citation
        citation_check = await self.check_source_citation(
            source_citation=review.source_citation,
            research_data=review.research_data
        )

        # Make decision using Claude
        decision = await self._make_verdict(
            review=review,
            claim_check=claim_check,
            tone_check=tone_check,
            citation_check=citation_check
        )

        # Log correction if rejected
        if decision["verdict"] == "rejected":
            await self.log_correction(
                lead_id=review.lead_id,
                original_line=review.personalization_line,
                corrected_line=decision.get("corrected_line"),
                issues=decision["issues_found"],
                correction_reason=decision["correction_reason"],
                improvement_notes=decision["improvement_notes"],
                confidence_score=review.confidence_score
            )

        verdicts.append(ReviewVerdict(**decision))

    # 3. Store reviews in database
    await self._store_batch_results(batch.batch_id, verdicts)

    # 4. Release approved leads to campaign
    approved_leads = [v.lead_id for v in verdicts if v.verdict == "approved"]
    if approved_leads:
        release_result = await self.release_to_campaign(
            lead_ids=approved_leads,
            campaign_id=batch.reviews[0].campaign_id  # Same for all in batch
        )

    # 5. Return summary
    return {
        "batch_id": batch.batch_id,
        "approved_count": len([v for v in verdicts if v.verdict == "approved"]),
        "rejected_count": len([v for v in verdicts if v.verdict == "rejected"]),
        "corrected_count": len([v for v in verdicts if v.corrected_line]),
        "released_count": len(approved_leads),
        "verdicts": [v.dict() for v in verdicts]
    }
```

### Phase 3: Campaign Release

```python
# For approved leads:
1. Batch leads by campaign_id
2. Call Instantly API to add leads with personalization variable
3. Map personalization_line to {{personalization}} placeholder
4. Update lead status in database to "in_campaign"
5. Log release to campaign_releases table
6. Handle any Instantly API errors gracefully
```

### Phase 4: Learning Loop

```python
# Weekly background task:
1. Query correction_logs where applied_to_training = false
2. Aggregate common issues by category
3. Generate training examples:
   - Bad: original_line (issues: X, Y, Z)
   - Good: corrected_line
4. Feed to Personalization Line Agent for few-shot learning
5. Mark corrections as applied_to_training = true
```

## Error Handling

### Input Validation Errors
- **Missing research_data**: Log warning, auto-reject line, request research re-run
- **Invalid campaign_id**: Raise error, block batch from processing
- **Empty personalization_line**: Auto-reject, flag for regeneration

### Integration Errors
- **Instantly API down**: Retry 3 times with exponential backoff, then defer to queue
- **Instantly rate limit**: Wait and retry based on rate limit headers
- **Invalid API key**: Critical error, alert ops team, halt all releases

### Database Errors
- **Connection timeout**: Retry with backoff, escalate if persistent
- **Constraint violations**: Log error details, skip problematic record, continue batch
- **Deadlock**: Retry transaction up to 3 times

## Testing Requirements

### Unit Tests (>90% coverage for tools)

```python
# test_verify_research_claim.py
- Test exact match (claim matches research data perfectly)
- Test partial match (claim has minor discrepancy)
- Test no match (claim not in research data - hallucination)
- Test empty research_data
- Test malformed claims

# test_validate_tone.py
- Test creepy personalization ("I've been following...")
- Test generic claims ("impressive growth")
- Test good conversational tone
- Test excessive length (>125 chars)
- Test robotic phrasing

# test_check_source_citation.py
- Test valid specific citation ("LinkedIn post Nov 15")
- Test vague citation ("social media")
- Test missing citation
- Test citation not in research_data
- Test multiple source matches

# test_log_correction.py
- Test successful logging to database
- Test duplicate prevention
- Test all fields persisted correctly
- Test timestamp accuracy

# test_release_to_campaign.py
- Test successful Instantly API call
- Test batch release (multiple leads)
- Test API error handling
- Test database update after release
- Test rollback on partial failure
```

### Integration Tests (>85% coverage for agent)

```python
# test_batch_review_workflow.py
- Test full batch review (mixed approved/rejected)
- Test all-approved batch
- Test all-rejected batch
- Test batch with corrections applied
- Test database persistence after batch

# test_instantly_integration.py
- Test real Instantly API call (sandbox mode)
- Test variable mapping ({{personalization}})
- Test error handling (invalid campaign_id)
- Test rate limiting behavior

# test_learning_loop.py
- Test correction aggregation query
- Test training data generation
- Test marking corrections as applied
- Test weekly cron job trigger
```

### Edge Cases

```python
- Batch size = 1 (single lead review)
- Batch size = 100 (maximum batch)
- All leads have confidence_score = 100 (should still review 10% random sample)
- Research data is null or empty object
- Personalization line contains special characters/emojis
- Multiple batches for same campaign processed concurrently
- Instantly API returns partial success (some leads added, some failed)
```

## Performance Requirements

- **Batch processing**: 100 leads in <60 seconds
- **Individual review**: <500ms per lead
- **Database writes**: Async, non-blocking
- **Instantly API**: Max 10 leads per request (API limit), batch in parallel
- **Memory usage**: <500MB for 100-lead batch
- **Concurrency**: Support 5 simultaneous batch reviews

## Monitoring & Metrics

### Key Metrics

```python
# Review metrics (tracked per batch)
- approval_rate: float  # percentage approved
- correction_rate: float  # percentage corrected
- avg_review_time: float  # seconds per lead
- issue_breakdown: dict[str, int]  # count by issue type

# Quality metrics (tracked daily)
- hallucination_rate: float  # accuracy issues / total reviews
- tone_issue_rate: float  # tone issues / total reviews
- source_missing_rate: float  # missing citations / total

# Campaign metrics (tracked per campaign)
- leads_released: int
- instantly_success_rate: float
- avg_time_to_release: float  # from generation to campaign

# Learning metrics (tracked weekly)
- corrections_logged: int
- corrections_applied_to_training: int
- personalization_ai_improvement: float  # before/after correction rate
```

### Alerts

- **Critical**: Instantly API down for >5 minutes
- **High**: Approval rate <50% (personalization AI needs retraining)
- **Medium**: Batch processing time >90 seconds
- **Low**: Source citation missing for >20% of batch

## Implementation Checklist

### Phase 1: Foundation (Day 1-2)
- [ ] Create agent directory: `src/agents/campaign_send_agent/`
- [ ] Implement `SendAgent` class extending `BaseAgent`
- [ ] Define input/output Pydantic models
- [ ] Write system prompt
- [ ] Create database migrations for 3 tables
- [ ] Apply migrations and verify schema

### Phase 2: Tools (Day 3-4)
- [ ] Implement `verify_research_claim()` tool
- [ ] Implement `validate_tone()` tool
- [ ] Implement `check_source_citation()` tool
- [ ] Implement `log_correction()` tool
- [ ] Implement `batch_review()` tool
- [ ] Write unit tests for all tools (>90% coverage)
- [ ] Fix any failing tests

### Phase 3: Instantly Integration (Day 5)
- [ ] Create `src/integrations/instantly.py` client
- [ ] Implement `add_leads_to_campaign()` method
- [ ] Implement `release_to_campaign()` tool
- [ ] Test against Instantly sandbox API
- [ ] Handle rate limiting and errors
- [ ] Write integration tests

### Phase 4: Agent Workflow (Day 6-7)
- [ ] Implement `process_task()` async method
- [ ] Integrate all tools into workflow
- [ ] Add batch collection query logic
- [ ] Implement decision-making with Claude
- [ ] Add database persistence for results
- [ ] Write integration tests for full workflow
- [ ] Test with sample batches (10, 50, 100 leads)

### Phase 5: Learning Loop (Day 8)
- [ ] Create Celery task for weekly correction aggregation
- [ ] Implement training data generation
- [ ] Add hook to mark corrections as applied
- [ ] Schedule cron job in Celery Beat
- [ ] Test learning loop manually

### Phase 6: Testing & QA (Day 9-10)
- [ ] Run full test suite (`make test`)
- [ ] Verify >85% agent coverage, >90% tool coverage
- [ ] Run type checking (`make typecheck`)
- [ ] Run linting (`make lint`)
- [ ] Fix all errors and warnings
- [ ] Test with production-like data volumes
- [ ] Load test with 100-lead batches

### Phase 7: Documentation (Day 11)
- [ ] Add docstrings to all methods
- [ ] Update this spec with any changes made during implementation
- [ ] Add usage examples to agent README
- [ ] Document Instantly API integration patterns
- [ ] Update CLAUDE.md if needed

### Phase 8: Deployment Prep (Day 12)
- [ ] Add monitoring metrics collection
- [ ] Set up alerts in monitoring system
- [ ] Create dashboard for review metrics
- [ ] Write deployment runbook
- [ ] Test in staging environment
- [ ] Prepare rollback plan

## Success Criteria

- [ ] All tests pass with >85% agent coverage, >90% tool coverage
- [ ] Type checking passes with zero errors (`mypy --strict`)
- [ ] Linting passes with zero errors (`ruff check`)
- [ ] Can process 100-lead batch in <60 seconds
- [ ] Successfully releases approved leads to Instantly campaign
- [ ] Corrections logged and available for AI retraining
- [ ] Approval rate >60% on first batch (validates personalization AI quality)
- [ ] Zero data loss on failure scenarios (database rollback works)
- [ ] Integration tests pass against Instantly sandbox API

## Dependencies

### Upstream (must exist before implementation)
- `Personalization Line Agent` - Provides lines to review (can mock for testing)
- `Lead Research Agent` - Provides research_data for verification (can mock for testing)
- `leads` table in database - For lead references
- `personalization_lines` table - For storing generated lines (create if doesn't exist)

### Downstream (will use this agent)
- `Campaign Creation Agent` - Will trigger batch reviews before campaign launch
- `System Learning Feedback Loop Agent` - Will consume correction_logs for retraining

### External Services
- **Instantly API**: Required for campaign releases (get API key from env)
- **Anthropic Claude API**: Required for review decisions (already configured)
- **PostgreSQL**: Required for data persistence (Supabase)
- **Redis**: Required for Celery task queue (already configured)

## Environment Variables

```bash
# Required
INSTANTLY_API_KEY=your-instantly-api-key-here

# Optional (for testing)
INSTANTLY_SANDBOX_MODE=true  # Use sandbox API for testing
INSTANTLY_BASE_URL=https://api.instantly.ai/api/v1  # Override API URL
```

## Notes

- This agent is critical for preventing hallucinations in personalization
- First 20 leads should be manually reviewed by humans as calibration
- After calibration, agent handles 90% of reviews, humans review 10% random sample
- Correction logs are the primary training signal for improving personalization AI
- Approval rate should trend upward as personalization AI learns from corrections
- If approval rate drops below 40%, pause automated reviews and investigate

## Future Enhancements (Not in MVP)

- [ ] Add A/B testing: compare reviewed vs. non-reviewed personalization performance
- [ ] Multi-language support for tone validation
- [ ] Auto-categorize correction types with ML (beyond manual tags)
- [ ] Predictive model to pre-flag likely rejections (save Claude API calls)
- [ ] Real-time dashboard showing review queue status
- [ ] Human override workflow for edge cases
- [ ] Confidence calibration: adjust thresholds based on approval rate trends
