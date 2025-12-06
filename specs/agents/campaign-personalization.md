# Campaign Personalization Agent - Production Specification

**Version**: 1.0
**Status**: Ready for Implementation
**Created**: 2025-12-05
**Category**: Campaign & Outreach
**Priority**: Phase 2 - Intelligence Layer

---

## Overview

The Campaign Personalization Agent generates highly personalized opening lines for cold outreach campaigns. Each line must reference specific, verifiable information from lead/company research and include source citations to prevent hallucinations.

**Key Principle**: Every personalization line must be grounded in factual research data with explicit source attribution.

---

## Agent Architecture

### Extends
- `BaseAgent` from `src.agents.base_agent`

### Name
- `campaign_personalization`

### Description
- "Generates personalized opening lines for outreach campaigns with confidence scoring and source attribution"

---

## System Prompt

```
You are the Campaign Personalization Agent for Smarter Team, an AI agency.

Your ONLY job is to create personalized opening lines for cold outreach campaigns.

CRITICAL REQUIREMENTS:
1. ONLY use facts explicitly provided in the research data
2. NEVER make assumptions or infer information not present in the data
3. ALWAYS include a source citation in the format: "Based on your [specific source]"
4. Personalization must be relevant but NOT creepy (avoid overly personal details)
5. Sound natural and human - like you spent 10 minutes researching them
6. Maximum 1 sentence for the personalization line

HALLUCINATION PREVENTION:
- If you cannot find a strong, verifiable personalization angle, return confidence: 0
- Do NOT use vague claims like "your impressive growth" without specific metrics
- Do NOT use "your recent award" without naming the specific award
- Do NOT reference events/posts without specific dates
- Do NOT invent job changes, company news, or achievements

CONFIDENCE SCORING (0-100):
- 90-100: Specific, recent (within 30 days), highly relevant to their role
- 80-89: Specific, recent (within 90 days), relevant to their industry
- 70-79: Specific but older (90+ days), or less directly relevant
- 60-69: General company information, less personalized
- 0-59: Insufficient data or low-quality personalization angle

BLACKLISTED PHRASES (auto-score 0):
- "your impressive growth" (without specific metrics)
- "your recent award" (without naming the award)
- "your success" (without specifics)
- "I noticed your company" (without specific observation)
- Any claim without a verifiable source

OUTPUT FORMAT:
{
  "personalization_line": "One sentence with specific, verifiable information",
  "source_citation": "Based on your [specific source with date if applicable]",
  "confidence": 85,
  "source_type": "linkedin_post|podcast|company_announcement|blog_post|news_article",
  "source_date": "2024-11-15",
  "reasoning": "Brief explanation of why this angle was chosen"
}

Remember: When in doubt, score lower. Low confidence triggers human review, which is better than sending hallucinated personalization.
```

---

## Input Schema

### Task Input (`process_task` receives)

```python
{
    "task_type": "generate_personalization",
    "lead_id": "uuid",
    "campaign_id": "uuid",
    "research_data": {
        "lead": {
            "name": str,
            "title": str,
            "company": str,
            "linkedin_url": str | None,
            "recent_posts": list[dict],  # [{content, date, url}]
            "recent_activity": list[dict],  # [{type, description, date}]
        },
        "company": {
            "name": str,
            "industry": str,
            "size": str,
            "recent_news": list[dict],  # [{headline, date, source, url}]
            "recent_announcements": list[dict],  # [{title, date, content}]
            "tech_stack": list[str] | None,
        },
        "personalization_angles": list[dict],  # [{angle, source, relevance_score}]
    },
    "context": {
        "offer_type": str,  # What we're selling
        "target_pain_point": str,  # Relevant pain point
    }
}
```

### Validation Requirements
- `lead_id` must be valid UUID
- `campaign_id` must be valid UUID
- `research_data.lead.name` is required
- `research_data.company.name` is required
- At least one of: `recent_posts`, `recent_activity`, `recent_news`, `recent_announcements` must be non-empty

---

## Output Schema

### Success Output

```python
{
    "status": "success",
    "lead_id": "uuid",
    "campaign_id": "uuid",
    "personalization": {
        "line": str,  # The actual personalization line
        "source_citation": str,  # Attribution for the line
        "confidence": int,  # 0-100
        "source_type": str,  # linkedin_post, podcast, etc.
        "source_date": str | None,  # ISO date or None
        "source_url": str | None,  # URL to the source
        "reasoning": str,  # Why this angle was chosen
    },
    "review_required": bool,  # True if confidence < 80
    "created_at": str,  # ISO timestamp
}
```

### Error Output

```python
{
    "status": "error",
    "lead_id": "uuid",
    "campaign_id": "uuid",
    "error_code": str,  # INSUFFICIENT_DATA, VALIDATION_ERROR, etc.
    "error_message": str,
    "created_at": str,
}
```

---

## Tools

### 1. `fetch_research_data`

Retrieves research data for a lead from the database.

**Parameters:**
```python
lead_id: str  # UUID of the lead
```

**Returns:**
```python
{
    "lead": dict,  # Lead research data
    "company": dict,  # Company research data
    "personalization_angles": list[dict],  # Pre-identified angles
}
```

**Raises:**
- `LeadNotFoundError`: If lead doesn't exist
- `DatabaseError`: If database query fails

**Implementation Location:** `src/agents/campaign_personalization/tools.py`

---

### 2. `rank_personalization_angles`

Ranks available personalization angles by quality and relevance.

**Parameters:**
```python
angles: list[dict]  # List of personalization angles
context: dict  # Campaign context (offer, pain point)
```

**Returns:**
```python
list[dict]  # Angles sorted by score, each with:
    {
        "angle": str,
        "source": str,
        "source_type": str,
        "source_date": str | None,
        "source_url": str | None,
        "relevance_score": float,  # 0.0-1.0
        "recency_score": float,  # 0.0-1.0
        "specificity_score": float,  # 0.0-1.0
        "combined_score": float,  # 0.0-1.0
    }
```

**Scoring Logic:**
- Recency: Exponential decay (100% at 0 days, 50% at 30 days, 10% at 90 days)
- Specificity: Has metrics/dates/names (1.0) vs vague (0.3)
- Relevance: Matches campaign context (1.0) vs generic (0.5)
- Combined: `(recency * 0.3) + (specificity * 0.4) + (relevance * 0.3)`

**Implementation Location:** `src/agents/campaign_personalization/tools.py`

---

### 3. `validate_personalization_line`

Validates personalization line against hallucination rules.

**Parameters:**
```python
line: str  # The personalization line
source_citation: str  # The source attribution
research_data: dict  # Original research data
```

**Returns:**
```python
{
    "is_valid": bool,
    "validation_errors": list[str],  # Reasons if invalid
    "blacklist_matches": list[str],  # Blacklisted phrases found
    "source_verified": bool,  # Citation matches research data
}
```

**Validation Checks:**
1. No blacklisted phrases
2. Source citation matches research data
3. Specific claims have supporting evidence
4. Dates in citation match source dates
5. No vague adjectives without metrics

**Implementation Location:** `src/agents/campaign_personalization/tools.py`

---

### 4. `calculate_confidence_score`

Calculates confidence score for the generated personalization.

**Parameters:**
```python
personalization: dict  # Generated personalization
angle: dict  # The angle used
validation_result: dict  # Result from validate_personalization_line
```

**Returns:**
```python
int  # Confidence score 0-100
```

**Scoring Algorithm:**
```python
base_score = angle["combined_score"] * 100

# Penalties
if not validation_result["source_verified"]:
    base_score = 0
if validation_result["blacklist_matches"]:
    base_score = 0
if not validation_result["is_valid"]:
    base_score = min(base_score, 60)

# Recency bonuses
if source_date within 30 days:
    base_score = min(base_score * 1.1, 100)
elif source_date within 90 days:
    base_score = base_score * 1.0
else:
    base_score = base_score * 0.9

return int(base_score)
```

**Implementation Location:** `src/agents/campaign_personalization/tools.py`

---

### 5. `store_personalization`

Stores the personalization line in the database.

**Parameters:**
```python
lead_id: str
campaign_id: str
personalization: dict
review_required: bool
```

**Returns:**
```python
str  # UUID of created personalization record
```

**Side Effects:**
- Inserts into `personalization_lines` table
- Links to `personalization_sources` table
- If `review_required=True`, adds to review queue

**Implementation Location:** `src/agents/campaign_personalization/tools.py`

---

### 6. `sync_to_instantly`

Syncs personalization line to Instantly campaign variable.

**Parameters:**
```python
lead_id: str
campaign_id: str
personalization_line: str
```

**Returns:**
```python
{
    "synced": bool,
    "instantly_variable": str,  # Variable name (e.g., "{{personalization}}")
    "campaign_updated": str,  # ISO timestamp
}
```

**Instantly API:**
- Endpoint: `PATCH /campaigns/{campaign_id}/leads/{lead_id}`
- Payload: `{"custom_variables": {"personalization": "line"}}`

**Error Handling:**
- Retries 3x on rate limit (exponential backoff)
- Logs failures but doesn't block (async sync)

**Implementation Location:** `src/agents/campaign_personalization/tools.py`

---

## Database Schema

### Table: `personalization_lines`

```sql
CREATE TABLE personalization_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,

    -- Personalization data
    personalization_line TEXT NOT NULL,
    source_citation TEXT NOT NULL,
    confidence_score INTEGER NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),
    source_type VARCHAR(50) NOT NULL,  -- linkedin_post, podcast, news_article, etc.
    source_date DATE,
    source_url TEXT,
    reasoning TEXT,

    -- Review workflow
    review_required BOOLEAN NOT NULL DEFAULT false,
    reviewed_at TIMESTAMPTZ,
    reviewed_by VARCHAR(100),  -- Human reviewer ID
    review_status VARCHAR(20),  -- pending, approved, rejected, edited
    review_notes TEXT,
    edited_line TEXT,  -- If human edited the line

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    instantly_synced_at TIMESTAMPTZ,  -- When synced to Instantly

    -- Indexes
    INDEX idx_lead_id (lead_id),
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_review_required (review_required) WHERE review_required = true,
    INDEX idx_confidence_score (confidence_score),
    INDEX idx_created_at (created_at DESC),

    -- Constraints
    UNIQUE(lead_id, campaign_id)  -- One personalization per lead per campaign
);
```

### Table: `personalization_sources`

Tracks which sources were used for personalization.

```sql
CREATE TABLE personalization_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    personalization_id UUID NOT NULL REFERENCES personalization_lines(id) ON DELETE CASCADE,

    -- Source details
    source_type VARCHAR(50) NOT NULL,
    source_content TEXT NOT NULL,  -- Original content from source
    source_date DATE,
    source_url TEXT,
    source_metadata JSONB,  -- Additional data (author, platform, etc.)

    -- Scoring
    relevance_score DECIMAL(3,2),  -- 0.00-1.00
    recency_score DECIMAL(3,2),
    specificity_score DECIMAL(3,2),
    combined_score DECIMAL(3,2),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    INDEX idx_personalization_id (personalization_id),
    INDEX idx_source_type (source_type)
);
```

### Table: `personalization_performance`

Tracks performance metrics for personalization lines.

```sql
CREATE TABLE personalization_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    personalization_id UUID NOT NULL REFERENCES personalization_lines(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,

    -- Email performance
    emails_sent INTEGER NOT NULL DEFAULT 0,
    emails_opened INTEGER NOT NULL DEFAULT 0,
    emails_clicked INTEGER NOT NULL DEFAULT 0,
    emails_replied INTEGER NOT NULL DEFAULT 0,

    -- Conversion metrics
    meetings_booked INTEGER NOT NULL DEFAULT 0,
    deals_closed INTEGER NOT NULL DEFAULT 0,

    -- Rates (calculated)
    open_rate DECIMAL(5,2),  -- Percentage
    click_rate DECIMAL(5,2),
    reply_rate DECIMAL(5,2),
    meeting_rate DECIMAL(5,2),

    -- Metadata
    first_sent_at TIMESTAMPTZ,
    last_sent_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    INDEX idx_personalization_id (personalization_id),
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_reply_rate (reply_rate DESC),

    UNIQUE(personalization_id)
);
```

### Migration File

Location: `specs/database-schema/migrations/003_personalization_tables.sql`

---

## Confidence Scoring System

### Score Ranges

| Range | Meaning | Action |
|-------|---------|--------|
| 90-100 | Excellent: Specific, recent, highly relevant | Auto-approve, immediate sync |
| 80-89 | Good: Specific, recent, relevant | Auto-approve, immediate sync |
| 70-79 | Fair: Specific but older, or less relevant | Human review required |
| 60-69 | Weak: Generic company info | Human review required |
| 0-59 | Poor: Insufficient data or blacklisted | Block, human review required |

### Human Review Workflow

1. **First 20 Lines**: 100% human review (regardless of confidence)
   - Purpose: Calibrate system, build training data
   - Reviewer provides feedback on quality

2. **After Calibration**: Confidence-based review
   - Confidence >= 80: Auto-approve
   - Confidence < 80: Human review queue
   - 10% random sampling for quality assurance

3. **Review Queue Priority**:
   - High value leads (score > 80) reviewed first
   - FIFO within same priority tier
   - SLA: 24 hours for review

4. **Feedback Loop**:
   - Human edits stored in `edited_line` field
   - `review_notes` captured for learning
   - Weekly analysis of rejections to improve prompts

---

## Hallucination Prevention Strategies

### 1. Grounding in Research Data
- **Pre-validation**: All research data validated before reaching agent
- **Fact Extraction**: Only use explicitly stated facts
- **No Inference**: Agent cannot infer or assume information

### 2. Source Attribution Required
- **Mandatory Citation**: Every line must include source
- **Source Verification**: Citation checked against research data
- **URL Linking**: Original source URL stored for auditing

### 3. Blacklist System
- **Vague Claims**: "impressive growth", "recent award" (without specifics)
- **Unverifiable Statements**: Claims without supporting data
- **Date Violations**: "recent" without specific date
- **Auto-Rejection**: Any blacklisted phrase → confidence = 0

### 4. Confidence Scoring
- **Conservative Default**: When in doubt, score lower
- **Multiple Factors**: Recency, specificity, relevance combined
- **Penalty System**: Validation failures heavily penalized

### 5. Human Review Gates
- **Low Confidence**: < 80 triggers review
- **First N Lines**: Initial calibration period
- **Random Sampling**: Continuous quality monitoring

### 6. Audit Trail
- **Full Provenance**: Source data stored with each line
- **Review History**: All human edits logged
- **Performance Tracking**: Success/failure metrics tracked

---

## Error Handling

### Error Codes

| Code | Description | Recovery |
|------|-------------|----------|
| `LEAD_NOT_FOUND` | Lead ID doesn't exist | Return error, log |
| `INSUFFICIENT_DATA` | Not enough research data | Score 0, human review |
| `VALIDATION_FAILED` | Line failed validation checks | Score 0, human review |
| `BLACKLIST_MATCH` | Blacklisted phrase detected | Score 0, reject |
| `DATABASE_ERROR` | Database operation failed | Retry 3x, then fail |
| `INSTANTLY_SYNC_FAILED` | Instantly API error | Log, retry async |
| `CLAUDE_API_ERROR` | Claude API failure | Retry 3x with backoff |

### Retry Logic

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
async def call_claude_api(...):
    ...
```

### Graceful Degradation

- If Claude API fails: Queue for later processing
- If Instantly sync fails: Continue, sync async
- If validation fails: Default to human review, don't block

---

## Integrations

### 1. Claude API (Anthropic)

**Purpose**: Generate personalization lines

**Model**: `claude-3-5-sonnet-20241022` (default)

**Configuration**:
```python
{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 500,
    "temperature": 0.7,  # Balanced creativity/consistency
}
```

**Rate Limits**:
- 50 requests/minute (tier 2)
- Handled via `tenacity` retry logic

---

### 2. Instantly API

**Purpose**: Sync personalization to campaign variables

**Base URL**: `https://api.instantly.ai/api/v1`

**Authentication**: API key via header

**Endpoints Used**:
- `PATCH /campaigns/{id}/leads/{id}` - Update lead variables

**Variable Mapping**:
```python
{
    "custom_variables": {
        "personalization": personalization_line
    }
}
```

**Rate Limits**:
- 120 requests/minute
- Exponential backoff on 429

---

### 3. Database (PostgreSQL)

**Purpose**: Store personalization lines, sources, performance

**Connection**: Via SQLAlchemy async engine

**Tables**:
- `personalization_lines`
- `personalization_sources`
- `personalization_performance`

---

## Testing Requirements

### Coverage Targets
- **Agent**: >85% code coverage
- **Tools**: >90% code coverage
- **Overall**: >85% code coverage

### Unit Tests

**Location**: `app/backend/__tests__/unit/agents/campaign_personalization/`

**Test Files**:

1. `test_agent.py` - Agent core functionality
   - Initialization
   - System prompt validation
   - Task processing flow
   - Error handling

2. `test_tools.py` - Individual tool functions
   - `fetch_research_data`: Valid/invalid lead_id
   - `rank_personalization_angles`: Scoring algorithm
   - `validate_personalization_line`: Blacklist detection
   - `calculate_confidence_score`: Edge cases
   - `store_personalization`: Database operations
   - `sync_to_instantly`: API calls, retries

3. `test_confidence_scoring.py` - Confidence algorithm
   - Score ranges (0-100)
   - Recency penalties/bonuses
   - Validation impacts
   - Edge cases (null dates, etc.)

4. `test_hallucination_prevention.py` - Hallucination checks
   - Blacklist phrase detection
   - Source verification
   - Vague claim detection
   - Citation validation

### Integration Tests

**Location**: `app/backend/__tests__/integration/agents/`

**Test Files**:

1. `test_personalization_flow.py` - End-to-end flow
   - Fetch research → Generate → Validate → Store → Sync
   - Human review queue workflow
   - Performance tracking updates

2. `test_instantly_integration.py` - Instantly API
   - Successful sync
   - Rate limit handling
   - Error recovery

3. `test_database_operations.py` - Database
   - Insert personalization lines
   - Query review queue
   - Update performance metrics
   - Cascade deletes

### Fixtures

**Location**: `app/backend/__tests__/fixtures/personalization_fixtures.py`

```python
@pytest.fixture
def mock_research_data():
    return {
        "lead": {
            "name": "John Doe",
            "title": "VP of Engineering",
            "company": "TechCorp",
            "recent_posts": [
                {
                    "content": "Excited to announce our team shipped...",
                    "date": "2024-11-20",
                    "url": "https://linkedin.com/posts/...",
                }
            ],
        },
        "company": {
            "name": "TechCorp",
            "industry": "SaaS",
            "recent_news": [
                {
                    "headline": "TechCorp raises $50M Series B",
                    "date": "2024-11-15",
                    "source": "TechCrunch",
                }
            ],
        },
    }

@pytest.fixture
def mock_personalization_angles():
    return [
        {
            "angle": "Recent LinkedIn post about shipping new feature",
            "source": "LinkedIn",
            "source_date": "2024-11-20",
            "relevance_score": 0.9,
        }
    ]

@pytest.fixture
def mock_claude_response():
    return {
        "personalization_line": "Saw your team shipped the new analytics dashboard last week",
        "source_citation": "Based on your LinkedIn post from Nov 20",
        "confidence": 92,
        "source_type": "linkedin_post",
        "source_date": "2024-11-20",
        "reasoning": "Recent, specific, relevant to engineering leader",
    }
```

### Test Scenarios

1. **Happy Path**: Valid research → High confidence → Auto-approve
2. **Low Confidence**: Insufficient data → Low score → Human review
3. **Blacklist Hit**: Vague claim → Score 0 → Reject
4. **API Failure**: Claude timeout → Retry → Success
5. **Instantly Failure**: Rate limit → Backoff → Success
6. **First 20 Lines**: Auto-route to review regardless of confidence
7. **Source Mismatch**: Citation doesn't match data → Score 0

---

## Performance Requirements

### Latency
- **Target**: < 3 seconds per personalization line
- **Max**: 10 seconds (including Claude API call)

### Throughput
- **Target**: 100 leads/hour single worker
- **Scale**: 500+ leads/hour with 5 workers

### Accuracy
- **Target**: >90% human approval rate (confidence >= 80)
- **Monitoring**: Weekly review of rejection reasons

---

## Monitoring & Observability

### Metrics to Track

1. **Generation Metrics**:
   - Lines generated per hour
   - Average confidence score
   - Confidence score distribution
   - Generation latency (p50, p95, p99)

2. **Quality Metrics**:
   - Human approval rate
   - Rejection reasons (categorized)
   - Blacklist hit rate
   - Source verification failures

3. **Performance Metrics**:
   - Open rate by confidence tier
   - Reply rate by confidence tier
   - Meeting rate by confidence tier
   - ROI per confidence tier

4. **Integration Metrics**:
   - Claude API latency
   - Instantly sync success rate
   - Database query latency
   - Error rate by type

### Logging

**Structured Logging** via `get_agent_logger`:

```python
logger.info(
    "Personalization generated",
    extra={
        "lead_id": lead_id,
        "campaign_id": campaign_id,
        "confidence": confidence,
        "source_type": source_type,
        "review_required": review_required,
    },
)
```

**Log Levels**:
- `INFO`: Successful generations, reviews, syncs
- `WARNING`: Low confidence, validation failures, retries
- `ERROR`: API failures, database errors, unrecoverable issues

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)

- [ ] Create agent directory structure: `src/agents/campaign_personalization/`
- [ ] Implement `BaseAgent` extension in `agent.py`
- [ ] Define system prompt in `prompts.py`
- [ ] Create Pydantic schemas in `schemas.py`
- [ ] Define custom exceptions in `exceptions.py`
- [ ] Set up agent logger

### Phase 2: Tools (Week 1-2)

- [ ] Implement `fetch_research_data` tool
- [ ] Implement `rank_personalization_angles` tool
- [ ] Implement `validate_personalization_line` tool
- [ ] Implement `calculate_confidence_score` tool
- [ ] Implement `store_personalization` tool
- [ ] Implement `sync_to_instantly` tool
- [ ] Write unit tests for each tool (>90% coverage)

### Phase 3: Database (Week 2)

- [ ] Create migration: `003_personalization_tables.sql`
- [ ] Add SQLAlchemy models for tables
- [ ] Test migrations up/down
- [ ] Add database indexes
- [ ] Test cascade deletes
- [ ] Write integration tests for DB operations

### Phase 4: Integrations (Week 2-3)

- [ ] Create Instantly client extending `BaseIntegrationClient`
- [ ] Implement Claude API integration
- [ ] Add retry logic with `tenacity`
- [ ] Test rate limit handling
- [ ] Test error recovery
- [ ] Write integration tests for APIs

### Phase 5: Agent Logic (Week 3)

- [ ] Implement `process_task` method
- [ ] Integrate all tools
- [ ] Add hallucination prevention logic
- [ ] Implement confidence scoring
- [ ] Add review queue routing
- [ ] Test end-to-end flow

### Phase 6: Testing (Week 3-4)

- [ ] Write unit tests for agent (>85% coverage)
- [ ] Write integration tests for full flow
- [ ] Test hallucination prevention scenarios
- [ ] Test confidence scoring edge cases
- [ ] Test human review workflow
- [ ] Load test (100 leads/hour)

### Phase 7: Human Review UI (Week 4)

- [ ] Design review queue interface
- [ ] Implement approve/reject actions
- [ ] Add edit functionality
- [ ] Track review feedback
- [ ] Calculate approval metrics
- [ ] Test review workflow

### Phase 8: Monitoring (Week 4)

- [ ] Add performance metrics
- [ ] Set up logging dashboard
- [ ] Create alerts for failures
- [ ] Track confidence distribution
- [ ] Monitor approval rates
- [ ] Set up weekly reports

### Phase 9: Documentation (Week 4)

- [ ] API documentation
- [ ] Tool documentation
- [ ] Human review guide
- [ ] Runbook for common issues
- [ ] Update CLAUDE.md
- [ ] Create training materials

### Phase 10: Deployment (Week 5)

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Celery tasks registered
- [ ] Monitoring dashboards live
- [ ] Run smoke tests
- [ ] Deploy to production

---

## Success Criteria

### Launch Criteria (Must Pass)

1. **Quality**:
   - [ ] >85% test coverage
   - [ ] All tests passing
   - [ ] No linting errors
   - [ ] No type errors

2. **Functionality**:
   - [ ] Generates personalization lines
   - [ ] Confidence scoring works
   - [ ] Human review queue functional
   - [ ] Instantly sync operational

3. **Performance**:
   - [ ] < 5s average latency
   - [ ] 100 leads/hour throughput
   - [ ] Zero data loss

4. **Safety**:
   - [ ] Blacklist system active
   - [ ] Source verification working
   - [ ] First 20 lines → review

### Post-Launch Metrics (Week 1-4)

1. **Adoption**:
   - [ ] 100+ personalization lines generated
   - [ ] Human review process validated
   - [ ] Instantly integration stable

2. **Quality**:
   - [ ] >90% approval rate (confidence >= 80)
   - [ ] < 5% blacklist hit rate
   - [ ] < 10% source verification failures

3. **Performance**:
   - [ ] Open rate >= campaign baseline
   - [ ] Reply rate >= campaign baseline
   - [ ] Meeting rate >= campaign baseline

---

## Dependencies

### Upstream (Provides Data)

1. **Lead Research Agent**:
   - Provides: Lead research data
   - Required fields: `recent_posts`, `recent_activity`

2. **Company Research Agent**:
   - Provides: Company research data
   - Required fields: `recent_news`, `recent_announcements`

### Downstream (Consumes Output)

1. **Campaign Send Agent**:
   - Consumes: Personalization lines
   - Via: Instantly campaign variables

2. **A/B Testing Agent**:
   - Consumes: Performance metrics
   - Via: `personalization_performance` table

### Integrations

1. **Claude API**: Text generation
2. **Instantly API**: Campaign variable sync
3. **PostgreSQL**: Data storage
4. **Redis**: Celery task queue

---

## Future Enhancements

### Phase 3+ (Post-MVP)

1. **AI Learning Loop**:
   - Analyze approved vs rejected lines
   - Fine-tune prompts based on feedback
   - Auto-improve confidence calibration

2. **Multi-variant Testing**:
   - Generate 2-3 personalization variants
   - A/B test which performs best
   - Learn best-performing patterns

3. **Industry-Specific Prompts**:
   - Customize system prompt by industry
   - Tech vs healthcare vs finance tones
   - Improve relevance scores

4. **Advanced Source Types**:
   - Podcast transcripts
   - GitHub activity
   - Conference speaking
   - Patent filings

5. **Sentiment Analysis**:
   - Analyze source sentiment
   - Match tone to lead's communication style
   - Avoid overly cheerful for serious topics

---

## Appendix

### Example Personalization Lines

#### Excellent (Confidence: 95)
```
Line: "Saw your team shipped the real-time analytics dashboard last week - impressive
3-day sprint from your LinkedIn post"
Citation: "Based on your LinkedIn post from Nov 20, 2024"
Source: https://linkedin.com/posts/johndoe/analytics-launch
```

#### Good (Confidence: 85)
```
Line: "Congrats on TechCorp's $50M Series B announced last month on TechCrunch"
Citation: "Based on TechCrunch article from Nov 15, 2024"
Source: https://techcrunch.com/2024/11/15/techcorp-raises-50m
```

#### Fair (Confidence: 72) - Triggers Review
```
Line: "Noticed TechCorp is expanding your engineering team according to recent job posts"
Citation: "Based on LinkedIn job postings from October 2024"
Source: https://linkedin.com/jobs/techcorp
```

#### Poor (Confidence: 0) - Blacklisted
```
Line: "Impressed by your company's recent growth and success"
Citation: "Based on general industry trends"
Reason: Vague claim without specifics, blacklisted phrase "recent growth"
```

### Sample Research Data

```json
{
  "lead": {
    "name": "Sarah Chen",
    "title": "Director of Marketing",
    "company": "GrowthCo",
    "recent_posts": [
      {
        "content": "Just launched our new podcast 'Marketing Mavericks' - first episode drops Monday with guest CMO from Stripe!",
        "date": "2024-11-18",
        "url": "https://linkedin.com/posts/sarahchen/podcast-launch",
        "platform": "LinkedIn"
      }
    ],
    "recent_activity": [
      {
        "type": "article",
        "description": "Published article on MarTech Today about AI in email marketing",
        "date": "2024-11-10",
        "url": "https://martechtoday.com/ai-email-marketing-chen"
      }
    ]
  },
  "company": {
    "name": "GrowthCo",
    "industry": "Marketing SaaS",
    "size": "50-100",
    "recent_news": [
      {
        "headline": "GrowthCo integrates with HubSpot for seamless CRM sync",
        "date": "2024-11-05",
        "source": "Product Hunt",
        "url": "https://producthunt.com/posts/growthco-hubspot"
      }
    ]
  }
}
```

### Blacklist Phrases (Auto-Reject)

```python
BLACKLIST_PHRASES = [
    # Vague growth claims
    "impressive growth",
    "recent growth",
    "rapid expansion",
    "scaling quickly",

    # Vague success claims
    "your success",
    "impressive success",
    "recent success",

    # Vague awards
    "recent award",
    "recent recognition",
    "industry recognition",

    # Generic observations
    "I noticed your company",
    "I saw that you",
    "came across your",

    # Empty compliments
    "impressive work",
    "great job",
    "amazing team",

    # Unspecific time references
    "recently launched" (without date),
    "just announced" (without date),
    "new initiative" (without specifics),
]
```

---

**End of Specification**

**Next Steps**: Implement according to checklist, targeting 4-5 week timeline for production readiness.
