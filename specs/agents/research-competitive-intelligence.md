# Competitive Intelligence Agent - Production Specification

**Agent Name:** `competitive_intelligence`

**Category:** Research & Intelligence

**Status:** Ready for Implementation

**Coverage Requirement:** >85% (agents)

**Generated:** 2025-12-05

---

## Overview

The Competitive Intelligence Agent analyzes prospect communications (emails, call transcripts, proposal feedback) to extract and categorize competitor mentions, pricing intelligence, feature comparisons, and win/loss reasons. This agent provides strategic insights for competitive positioning and tracks market trends over time.

**Input:** Conversation data (emails, transcripts), proposal feedback
**Output:** Structured competitive intelligence with mention logs, pricing insights, and recommendations
**Trigger:** Handoff from Response Handler Agent, Call Transcript Processor, or weekly cron job

---

## System Prompt

```
You are the Competitive Intelligence Agent for Smarter Team, an autonomous AI agency.

Your mission is to analyze prospect communications for competitive intelligence that informs our sales strategy and positioning.

**Core Responsibilities:**
1. Parse all prospect communications for competitor name mentions
2. Extract contextual information around each mention
3. Categorize mentions by type: pricing, features, reputation, relationship
4. Track pricing intelligence and feature comparisons
5. Identify win/loss reasons by competitor
6. Generate weekly competitive intelligence reports

**Competitor Detection Logic:**
- Direct mentions: "CompetitorX", "Competitor X", "CompetitorX Corp"
- Alternative names: "CX", "Competitor", "that other company"
- Product references: "CompetitorX's product", "their platform"
- Context clues: "the solution we used before", "your competitor"

**Mention Categories:**
- PRICING: Discount amounts, contract terms, licensing models, total contract value
- FEATURES: Specific capabilities mentioned, feature gaps, comparisons
- REPUTATION: Market perception, reliability concerns, satisfaction levels
- RELATIONSHIP: History with competitor, decision maker connections, switching costs

**Pricing Intelligence Extraction:**
- Exact prices mentioned (validate with $ symbol or currency)
- Percentage discounts (e.g., "15% discount")
- Contract terms (monthly, annual, multi-year)
- Licensing models (per-seat, usage-based, enterprise)
- Implementation/hidden costs mentioned

**Win/Loss Reason Classification:**
- PRICE: Higher/lower pricing, discount differences, value perception
- FEATURE: Missing capabilities, superior features, integration gaps
- SERVICE: Support quality, implementation timeline, customer success
- RELATIONSHIP: Existing vendor relationship, decision maker preferences
- TECHNICAL: Integration complexity, migration effort, security concerns

**Error Handling:**
- If conversation data is malformed, log and skip to next record
- If competitor detection is uncertain, mark as "unknown_competitor"
- If database write fails, queue for retry with exponential backoff
- If no mentions found, log as "no_intelligence" for tracking

**Quality Standards:**
- All extracted prices must include currency/period for validation
- Feature comparisons must be specific and actionable
- Win/loss reasons must include direct quote evidence when possible
- Confidence scores (0.0-1.0) for all extracted intelligence

Always prioritize accuracy and context over volume of mentions.
```

---

## Agent Architecture

### Inheritance
```python
from src.agents.base_agent import BaseAgent

class CompetitiveIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="competitive_intelligence",
            description="Extracts and analyzes competitive intelligence from prospect communications"
        )
```

### Dependencies
- **Upstream:** Response Handler Agent, Call Transcript Processor, Proposal Tracking Agent
- **Downstream:** Campaign Creation Agent (for competitive positioning)
- **Integrations:** Internal database (conversations, transcripts), Supabase for storage

### Database Schema
```sql
-- Competitors registry
CREATE TABLE competitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    aliases JSONB,                    -- Alternative names and spellings
    website VARCHAR(500),
    industry VARCHAR(100),
    tier VARCHAR(20),                 -- tier1, tier2, tier3
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Competitor mentions from conversations
CREATE TABLE competitor_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    conversation_type VARCHAR(50) NOT NULL,    -- email, call, proposal
    competitor_id UUID REFERENCES competitors(id),
    competitor_name VARCHAR(255),              -- For unknown competitors
    mention_category VARCHAR(50),              -- pricing, features, reputation, relationship
    context_extract TEXT,                      -- Full context around mention
    direct_quote TEXT,                         -- Exact quote if available
    sentiment VARCHAR(20),                     -- positive, negative, neutral
    confidence_score FLOAT DEFAULT 0.0,
    metadata JSONB,                            -- Additional extracted data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX (conversation_id),
    INDEX (competitor_id),
    INDEX (mention_category),
    INDEX (created_at)
);

-- Pricing intelligence
CREATE TABLE competitive_pricing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mention_id UUID REFERENCES competitor_mentions(id),
    competitor_id UUID REFERENCES competitors(id),
    price_amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    pricing_model VARCHAR(50),                 -- per_seat, usage_based, enterprise
    billing_period VARCHAR(20),                -- monthly, annual, onetime
    discount_percentage DECIMAL(5,2),
    contract_term_months INTEGER,
    additional_costs JSONB,                    -- Implementation, training, etc.
    confidence_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX (competitor_id),
    INDEX (price_amount),
    INDEX (created_at)
);

-- Feature comparisons
CREATE TABLE competitive_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mention_id UUID REFERENCES competitor_mentions(id),
    competitor_id UUID REFERENCES competitors(id),
    feature_name VARCHAR(255) NOT NULL,
    comparison_type VARCHAR(20),               -- superior, inferior, equivalent, missing
    our_advantage BOOLEAN DEFAULT FALSE,
    their_advantage BOOLEAN DEFAULT FALSE,
    details TEXT,                              -- Specific comparison details
    impact_level VARCHAR(20),                  -- critical, important, minor
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX (competitor_id),
    INDEX (feature_name),
    INDEX (comparison_type)
);

-- Win/loss analysis
CREATE TABLE competitive_win_loss (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id UUID,                              -- From deals table
    competitor_id UUID REFERENCES competitors(id),
    outcome VARCHAR(20),                       -- win, loss, no_decision
    primary_reason VARCHAR(100),               -- Main loss/winfactor
    secondary_reasons JSONB,                   -- Additional factors
    deal_value DECIMAL(12,2),
    confidence_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX (competitor_id),
    INDEX (outcome),
    INDEX (primary_reason),
    INDEX (created_at)
);
```

---

## Tools & Methods

### 1. `parse_conversation_for_mentions`

**Purpose:** Extract competitor mentions from conversation text

**Parameters:**
```python
{
    "conversation_id": str,         # Unique identifier
    "conversation_type": str,       -- "email", "call", "proposal"
    "text_content": str,           # Full conversation text
    "metadata": dict | None        # Additional context (speaker roles, timeline)
}
```

**Returns:**
```python
{
    "conversation_id": str,
    "mentions_found": int,
    "competitor_mentions": [
        {
            "competitor_name": str,
            "aliases_detected": list[str],
            "mention_count": int,
            "mentions": [
                {
                    "text": str,            # Full sentence with mention
                    "context": str,         # Paragraph around mention
                    "quote": str | None,    # Direct quote if available
                    "position": int,        # Character position in text
                    "speaker": str | None   # Who said it (for calls)
                }
            ]
        }
    ],
    "processing_time_ms": float,
    "confidence_score": float
}
```

**Error Handling:**
- Empty/null text: Return empty results, log warning
- Malformed conversation ID: Log error, return empty with error flag
- Text too long (>100k chars): Process in chunks, aggregate results
- Unicode issues: Clean text, log character encoding issues

**Implementation Notes:**
- Use fuzzy string matching for competitor name detection
- Maintain alias mapping for competitor name variations
- Exclude false positives (e.g., "competitive" as adjective)
- Track mention frequency for relevance scoring

---

### 2. `categorize_mentions`

**Purpose:** Categorize extracted mentions and extract specific intelligence

**Parameters:**
```python
{
    "conversation_id": str,
    "competitor_mentions": list[dict],  # Output from parse_conversation_for_mentions
    "context_hints": dict | None       # Deal stage, prospect industry, etc.
}
```

**Returns:**
```python
{
    "categorized_mentions": [
        {
            "mention_id": str,
            "competitor_name": str,
            "category": str,                    -- pricing, features, reputation, relationship
            "sentiment": str,                   -- positive, negative, neutral
            "confidence_score": float,
            "extracted_intelligence": {
                "pricing": {
                    "amount": float | None,
                    "currency": str | None,
                    "model": str | None,
                    "period": str | None
                } | None,
                "features": [
                    {
                        "name": str,
                        "comparison": str,
                        "advantage": str,
                        "impact": str
                    }
                ] | None,
                "sentiment_indicators": list[str],
                "relationship_context": str | None
            }
        }
    ],
    "uncertain_mentions": list[dict],    -- Low confidence mentions for review
    "total_processing_time_ms": float
}
```

**Error Handling:**
- Invalid mention structure: Skip mention, log error
- Category ambiguity: Mark as "multiple_categories", flag for review
- Missing context: Use default neutral sentiment, lower confidence
- Parsing failures: Log error, continue with next mention

**Implementation Notes:**
- Use keyword-based classification with ML model fallback
- Look for pricing indicators: "$", "discount", "deal", "contract"
- Feature keywords: "feature", "capability", "integration", "limitation"
- Sentiment analysis: Use VADER or similar for quick classification
- Context analysis: Consider speaker role and conversation flow

---

### 3. `store_competitive_intelligence`

**Purpose:** Persist categorized intelligence to database

**Parameters:**
```python
{
    "conversation_id": str,
    "conversation_type": str,
    "categorized_mentions": list[dict],  # Output from categorize_mentions
    "deal_id": str | None,              # If associated with specific deal
    "metadata": dict | None
}
```

**Returns:**
```python
{
    "mentions_stored": int,
    "pricing_records": int,
    "feature_records": int,
    "new_competitors": list[str],       -- Discovered competitors
    "errors": list[dict],
    "processing_time_ms": float
}
```

**Error Handling:**
- Database connection failure: Queue for retry, exponential backoff
- Constraint violation: Log duplicate, update existing record
- Invalid foreign key: Create placeholder competitor record
- Transaction failure: Rollback, retry entire batch once

**Implementation Notes:**
- Use upsert for competitor records to handle new discoveries
- Batch insert mentions for performance (max 100 per batch)
- Link mentions to deals when available for win/loss analysis
- Maintain referential integrity with proper foreign keys

---

### 4. `generate_weekly_report`

**Purpose:** Generate comprehensive competitive intelligence report

**Parameters:**
```python
{
    "report_period": str,               -- "last_7_days", "last_30_days"
    "competitors": list[str] | None,   -- Specific competitors to include
    "include_sections": list[str] | None  -- pricing, features, trends, recommendations
}
```

**Returns:**
```python
{
    "report_period": str,
    "generated_at": str,               -- ISO 8601 timestamp
    "executive_summary": {
        "total_mentions": int,
        "unique_competitors": int,
        "key_insights": list[str],
        "trending_topics": list[str]
    },
    "competitor_analysis": [
        {
            "competitor_name": str,
            "mention_frequency": int,
            "win_rate": float | None,
            "pricing_position": str,    -- premium, competitive, discount
            "strengths": list[str],
            "weaknesses": list[str],
            "recent_deals": list[dict]
        }
    ],
    "pricing_intelligence": {
        "average_discounts": dict,     -- By competitor
        "pricing_trends": list[dict],
        "deal_size_comparison": dict
    },
    "feature_battlefield": {
        "our_advantages": list[str],
        "their_advantages": list[str],
        "feature_gaps": list[str],
        "common_comparison_points": list[str]
    },
    "recommendations": [
        {
            "category": str,            -- positioning, pricing, features
            "priority": str,            -- high, medium, low
            "action": str,
            "rationale": str,
            "estimated_impact": str
        }
    ],
    "appendix": {
        "raw_mentions_by_competitor": dict,
        "data_quality_metrics": dict
    }
}
```

**Error Handling:**
- No data for period: Return empty report with message
- Aggregation query timeout: Use cached partial results
- Invalid date range: Default to last 7 days, log warning
- Rendering issues: Return raw data structure

**Implementation Notes:**
- Run via cron every Monday at 9:00 AM
- Cache report results for 24 hours
- Include data freshness indicators
- Provide drill-down capabilities for key insights
- Track report viewership for ROI measurement

---

## Error Handling Matrix

| Component | Error Type | Detection | Response | Retry |
|-----------|------------|-----------|----------|-------|
| Text Parsing | Empty content | Length check | Log warning, return empty | No |
| Text Parsing | Unicode error | Exception | Clean text, continue | No |
| NLP Processing | Timeout | Duration check | Use cached results | Yes, 1x |
| Database | Connection failed | Exception | Queue for retry | Yes, 3x |
| Database | Constraint error | SQLSTATE | Update existing | No |
| External API | Rate limit | HTTP 429 | Exponential backoff | Yes, 5x |
| External API | Auth error | HTTP 401/403 | Fail immediately | No |
| Report Generation | Query timeout | Duration | Use partial data | Yes, 1x |
| Report Generation | Memory error | Exception | Reduce scope, retry | Yes, 1x |

---

## Testing Strategy

### Unit Tests
```python
def test_competitor_name_detection():
    """Verify accurate detection of competitor mentions"""
    # Test direct mentions, aliases, and false positives

def test_pricing_extraction():
    """Verify pricing intelligence extraction"""
    # Test various price formats and currencies

def test_categorization_accuracy():
    """Verify mention categorization"""
    # Test category assignment with edge cases

def test_sentiment_analysis():
    """Verify sentiment scoring for mentions"""
    # Test positive, negative, and neutral mentions
```

### Integration Tests
```python
def test_end_to_end_processing():
    """Full pipeline from conversation to storage"""
    # Test with mock email, call, and proposal data

def test_database_operations():
    """Verify database writes and queries"""
    # Test with actual test database

def test_weekly_report_generation():
    """Verify report creation with sample data"""
    # Test all report sections and aggregations
```

### Mock Data Fixtures
```python
@pytest.fixture
def sample_email_conversation():
    return {
        "id": "email-001",
        "type": "email",
        "text": "We were using CompetitorX but their pricing was too high...",
        "metadata": {"from": "prospect@company.com", "date": "2025-01-15"}
    }

@pytest.fixture
def sample_call_transcript():
    return {
        "id": "call-001",
        "type": "call",
        "text": "Speaker1: How does your pricing compare to CompetitorY?\nSpeaker2: We're more flexible...",
        "metadata": {"speakers": ["prospect", "sales"], "duration": 1800}
    }
```

---

## Performance Requirements

### Latency Expectations
- Single conversation processing: <2 seconds
- Batch processing (100 conversations): <30 seconds
- Weekly report generation: <10 seconds
- Database queries: <500ms for typical queries

### Throughput Targets
- 1,000 conversations per hour sustained
- 10,000 database writes per hour sustained
- Concurrent report generation: 5 reports

### Caching Strategy
- Competitor name mappings: 24 hours TTL
- Recent mentions: 1 hour TTL
- Weekly reports: 24 hours TTL
- Pricing intelligence: 6 hours TTL

---

## Observability

### Logging Requirements
```python
# Structured logging with context
logger.info(
    "Processed conversation for competitive intelligence",
    extra={
        "conversation_id": conv_id,
        "mentions_found": len(mentions),
        "competitors": [m["competitor_name"] for m in mentions],
        "processing_time_ms": duration,
        "confidence_score": avg_confidence
    }
)

# Error logging with full context
logger.error(
    "Failed to store competitive intelligence",
    extra={
        "conversation_id": conv_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "batch_size": len(mentions),
        "retry_count": retry_count
    }
)
```

### Metrics to Track
- Conversation processing rate (per hour)
- Competitor mention frequency (by competitor)
- Categorization accuracy (manual sampling)
- Database write latency
- Report generation performance
- Error rates by component

### Alerting Rules
- Processing queue depth >1,000
- Error rate >5% (1-hour window)
- Database connection failures
- Report generation failures
- Competitor mention spike (3x baseline)

---

## Security Considerations

### Data Privacy
- PII redaction from conversation text
- Encrypted storage of sensitive pricing data
- Access controls for competitive intelligence
- Audit trail for data access

### Data Sanitization
- Remove email addresses and phone numbers
- Sanitize financial details in logs
- Anonymize customer names in reports
- Filter out proprietary information

---

## Acceptance Criteria

- [ ] Agent processes emails, calls, and proposal feedback accurately
- [ ] Competitor mentions detected with >95% precision
- [ ] Mentions categorized correctly >90% of the time
- [ ] Pricing intelligence extracted with currency/period validation
- [ ] Win/loss reasons tracked with evidence quotes
- [ ] Weekly reports generated automatically with actionable insights
- [ ] All database writes properly indexed and queryable
- [ ] Error handling covers all failure modes
- [ ] Unit test coverage >85%
- [ ] Integration tests cover end-to-end flows
- [ ] Performance targets met under load testing
- [ ] Security and privacy requirements implemented
- [ ] Monitoring and alerting configured

---

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_competitive_intelligence.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_competitive_intelligence.py -v

# Type checking
mypy app/backend/src/agents/competitive_intelligence.py

# Linting
ruff check app/backend/src/agents/competitive_intelligence.py

# Performance test (load testing)
python -m pytest app/backend/__tests__/performance/test_competitive_intelligence_perf.py

# Manual smoke test
python -c "from src.agents.competitive_intelligence import CompetitiveIntelligenceAgent; print('Agent imports successfully')"
```
