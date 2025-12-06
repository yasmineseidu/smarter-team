# Intent Signal Tracking Agent - Production Specification

**Agent Name:** `research_intent_signal`

**Category:** Research & Intelligence

**Status:** Ready for Implementation

**Coverage Requirement:** >85% (agents)

**Generated:** 2025-12-05

**Refined From:** plan/agents/research-intent-signal.md

---

## Overview

The Intent Signal Tracking Agent continuously monitors tracked companies for buying signals and trigger events. This agent scans multiple data sources daily to detect changes in company behavior that indicate purchase intent, then scores and prioritizes these signals to trigger timely outreach.

**Primary Data Sources:**
- Job board postings (hiring patterns)
- News feeds and press releases
- Funding announcements
- Leadership changes
- Technology stack updates
- LinkedIn activity monitoring
- Competitor mentions
- Content engagement patterns

**Input:** List of companies to monitor (from Company Research Agent)
**Output:** Scored intent signals with recommended actions
**Trigger:** Daily cron job at 5:00 AM or manual API call

---

## System Prompt

```
You are the Intent Signal Tracking Agent for Smarter Team, an autonomous AI agency.

Your mission is to detect, analyze, and score buying signals from monitored companies to identify optimal timing for sales outreach.

**Core Responsibilities:**
1. Scan tracked companies daily across multiple signal sources
2. Detect and categorize intent signals based on predefined patterns
3. Score signal strength using weighted algorithm (1-10 scale)
4. Update lead priority scores based on new signals
5. Trigger outreach workflows for high-intent signals
6. Maintain historical signal data for pattern analysis

**Signal Categories & Weights:**
- HIRING_GROWTH (weight: 0.25): New job postings, especially in relevant departments
- FUNDING_EVENT (weight: 0.30): New funding rounds, acquisitions, IPOs
- LEADERSHIP_CHANGE (weight: 0.20): New executives, especially in buying roles
- EXPANSION_NEWS (weight: 0.15): New offices, markets, product launches
- TECHNOLOGY_CHANGE (weight: 0.20): New tools, migrations, deprecations
- COMPETITOR_ACTIVITY (weight: 0.10): Competitor wins, mentions, evaluations
- CONTENT_ENGAGEMENT (weight: 0.05): Engaging with relevant content

**Scoring Algorithm:**
Base Score = Σ(signal_value × category_weight × recency_factor)

- Recency Factor: 1.0 (last 7 days), 0.7 (8-30 days), 0.3 (31-90 days)
- Signal Value: 1-5 based on signal strength
- Final Score: Normalized to 1-10 scale

**High-Intent Thresholds:**
- Score ≥ 8.0: Immediate outreach trigger (critical)
- Score ≥ 6.5: Add to priority campaign queue (high)
- Score ≥ 4.0: Monitor for additional signals (medium)
- Score < 4.0: Log for pattern analysis (low)

**Decision Rules:**
- Multiple signals in 30 days = +2.0 score bonus
- Signals in target company size range = +1.0 bonus
- Signals in relevant industry = +1.5 bonus
- Previous outreach = -0.5 penalty per attempt

**Error Handling:**
- API rate limits: Implement exponential backoff, queue failed requests
- Inaccessible data: Log and continue with available sources
- Ambiguous company names: Use domain name as primary identifier
- Duplicate signals: Merge, keeping highest confidence score

**Output Format:**
```json
{
  "company_id": "uuid",
  "signals": [
    {
      "type": "HIRING_GROWTH",
      "description": "Hiring 5 Sales Engineers",
      "source": "linkedin_jobs",
      "detected_at": "2025-12-05T10:00:00Z",
      "confidence": 0.85,
      "raw_data": {...}
    }
  ],
  "intent_score": 8.5,
  "recommendation": "IMMEDIATE_OUTREACH",
  "previous_signals": 3,
  "last_updated": "2025-12-05T10:30:00Z"
}
```

Always prioritize recent, verifiable signals with clear business impact over speculative indicators.
```

---

## Agent Architecture

### Inheritance
```python
from src.agents.base_agent import BaseAgent

class IntentSignalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="research_intent_signal",
            description="Detect and score buying signals from monitored companies"
        )
```

### Dependencies
- **Upstream:** Company Research Agent (`company_research`), Lead List Builder Agent (`leadgen_lead_list_builder`)
- **Downstream:** Campaign Personalization Agent (`campaign_personalization`), Sales Agent
- **Database:** `intent_signals`, `signal_types`, `lead_intent_scores`, `companies`
- **Integrations:** Serper, News API, LinkedIn API, Crunchbase, BuiltWith, Firecrawl

---

## Tools & Methods

### 1. `scan_job_postings`

**Purpose:** Scan job boards for new postings that indicate growth or pain points

**Input Schema:**
```python
{
    "company_domain": str,         # Company's website domain
    "keywords": list[str],         # Relevant keywords (e.g., "sales engineer")
    "departments": list[str],      # Target departments
    "lookback_days": int = 30      # Days to look back for new posts
}
```

**Output Schema:**
```python
{
    "postings": list[dict],
    "hiring_growth_score": float,
    "department_breakdown": dict,
    "seniority_distribution": dict
}
```

**Error Handling:**
- Rate limit (429) → Exponential backoff, max 5 retries
- Auth error (401) → Fail immediately, log alert
- Partial data → Return available postings with warning

### 2. `scan_company_news`

**Purpose:** Search news feeds for company announcements and press releases

**Input Schema:**
```python
{
    "company_name": str,
    "company_domain": str,
    "keywords": list[str] = ["funding", "acquisition", "expansion", "launch"],
    "lookback_days": int = 90
}
```

**Output Schema:**
```python
{
    "articles": list[dict],
    "funding_events": list[dict],
    "acquisition_news": list[dict],
    "expansion_news": list[dict],
    "leadership_changes": list[dict]
}
```

**Error Handling:**
- API quota exceeded → Switch to backup source, log warning
- No results → Return empty arrays, not error
- Malformed response → Log error, continue with other sources

### 3. `check_funding_database`

**Purpose:** Query funding databases for recent investment rounds

**Input Schema:**
```python
{
    "company_name": str,
    "company_domain": str,
    "include_acquisitions": bool = True
}
```

**Output Schema:**
```python
{
    "funding_rounds": list[dict],
    "total_raised": float,
    "latest_round": dict,
    "investors": list[str],
    "acquisition_details": dict
}
```

**Error Handling:**
- Database timeout → Retry 3x with increasing timeout
- Company not found → Return empty result, not error
- Rate limit → Queue for retry with exponential backoff

### 4. `monitor_linkedin_activity`

**Purpose:** Track LinkedIn posts, job changes, and company updates

**Input Schema:**
```python
{
    "company_name": str,
    "linkedin_url": str,
    "track_executives": bool = True,
    "track_company_page": bool = True
}
```

**Output Schema:**
```python
{
    "recent_posts": list[dict],
    "new_hires": list[dict],
    "executive_changes": list[dict],
    "engagement_metrics": dict
}
```

**Error Handling:**
- LinkedIn API limits → Respect X-RateLimit headers
- Private profiles → Skip silently, don't fail
- Temporary outages → Queue for retry later

### 5. `detect_technology_changes`

**Purpose:** Monitor tech stack for new adoptions, migrations, or deprecations

**Input Schema:**
```python
{
    "domain": str,
    "previous_tech_stack": list[str] = [],
    "focus_areas": list[str] = ["crm", "analytics", "devops", "collaboration"]
}
```

**Output Schema:**
```python
{
    "new_technologies": list[dict],
    "removed_technologies": list[str],
    "migration_signals": list[dict],
    "tech_stack_score": float
}
```

**Error Handling:**
- BuiltWith limits → Use cached data if available
- Site inaccessible → Return last known state with warning
- Inconsistent data → Flag for manual review

### 6. `calculate_intent_score`

**Purpose:** Aggregate all signals into a single intent score

**Input Schema:**
```python
{
    "company_id": str,
    "signals": list[dict],
    "previous_signals": list[dict] = [],
    "company_profile": dict = {}
}
```

**Output Schema:**
```python
{
    "intent_score": float,
    "score_breakdown": dict,
    "recommendation": str,
    "confidence_level": float,
    "signal_count": int,
    "high_value_signals": list[dict]
}
```

**Error Handling:**
- Missing signals → Return score of 0 with explanation
- Invalid input → Return validation error
- Calculation error → Log full context, return default score

### 7. `update_lead_priority`

**Purpose:** Update lead records with new intent scores

**Input Schema:**
```python
{
    "lead_id": str,
    "intent_score": float,
    "signals": list[dict],
    "recommendation": str
}
```

**Output Schema:**
```python
{
    "lead_id": str,
    "previous_score": float,
    "new_score": float,
    "priority_level": str,
    "updated_at": str
}
```

**Error Handling:**
- Lead not found → Create new lead record
- Database constraint → Log error, continue with update
- Concurrent update → Use last update wins strategy

---

## Database Schema

### Tables

#### `intent_signals`
```sql
CREATE TABLE intent_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    signal_type VARCHAR(50) NOT NULL REFERENCES signal_types(name),
    description TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    raw_data JSONB,
    score_value DECIMAL(3,1) CHECK (score_value >= 1 AND score_value <= 10),
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_intent_signals_company (company_id),
    INDEX idx_intent_signals_type (signal_type),
    INDEX idx_intent_signals_detected (detected_at),
    INDEX idx_intent_signals_score (score_value DESC)
);
```

#### `signal_types`
```sql
CREATE TABLE signal_types (
    name VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    weight DECIMAL(3,2) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed data
INSERT INTO signal_types (name, display_name, weight) VALUES
('HIRING_GROWTH', 'Hiring Growth', 0.25),
('FUNDING_EVENT', 'Funding Event', 0.30),
('LEADERSHIP_CHANGE', 'Leadership Change', 0.20),
('EXPANSION_NEWS', 'Expansion News', 0.15),
('TECHNOLOGY_CHANGE', 'Technology Change', 0.20),
('COMPETITOR_ACTIVITY', 'Competitor Activity', 0.10),
('CONTENT_ENGAGEMENT', 'Content Engagement', 0.05);
```

#### `lead_intent_scores`
```sql
CREATE TABLE lead_intent_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    current_score DECIMAL(3,1) NOT NULL CHECK (current_score >= 1 AND current_score <= 10),
    previous_score DECIMAL(3,1),
    signal_count INTEGER NOT NULL DEFAULT 0,
    last_signal_at TIMESTAMP WITH TIME ZONE,
    recommendation VARCHAR(50),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(lead_id),
    INDEX idx_lead_intent_scores_score (current_score DESC),
    INDEX idx_lead_intent_scores_updated (updated_at)
);
```

---

## Error Handling Matrix

| Component | Error Type | Detection | Response | Retry |
|-----------|------------|-----------|----------|-------|
| Job scanner | Rate limit | HTTP 429 | Exponential backoff | Yes, 5x |
| News API | Quota exceeded | API response | Switch to backup | No |
| LinkedIn | Auth error | HTTP 401 | Refresh token | Yes, 1x |
| Funding DB | Timeout | Exception | Increase timeout | Yes, 3x |
| Tech stack | Site down | HTTP 5xx | Use cached data | No |
| Scoring | Invalid data | Validation | Log error, skip | No |
| Database | Constraint | SQL error | Log full context | No |

### Recovery Strategies
1. **Partial Failure:** Continue processing other companies, queue failed ones
2. **API Degradation:** Fall back to cached or alternative data sources
3. **Database Issues:** Use in-memory processing, persist when available
4. **Cascading Failures:** Implement circuit breaker pattern

---

## Testing Strategy

### Unit Tests
```python
# test_intent_signal_agent.py
class TestIntentSignalAgent:
    @pytest.mark.asyncio
    async def test_scan_job_postings_success(self):
        """Verify job posting detection and scoring"""

    @pytest.mark.asyncio
    async def test_calculate_intent_score_accuracy(self):
        """Verify scoring algorithm produces expected results"""

    @pytest.mark.asyncio
    async def test_signal_deduplication(self):
        """Verify duplicate signals are merged correctly"""

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Verify exponential backoff on rate limits"""

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Verify graceful handling of API failures"""
```

### Integration Tests
```python
# test_intent_signal_integration.py
class TestIntentSignalIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_signal_detection(self):
        """Full pipeline from scan to score to database"""

    @pytest.mark.asyncio
    async def test_multi_source_signal_aggregation(self):
        """Verify signals from multiple sources are combined"""

    @pytest.mark.asyncio
    async def test_database_transaction_handling(self):
        """Verify atomic updates on concurrent access"""
```

### Mock Strategy
```python
# fixtures/intent_signal_fixtures.py
@pytest.fixture
def mock_job_postings():
    return {
        "results": [
            {"title": "Sales Engineer", "department": "Sales", "level": "Mid"},
            {"title": "VP of Sales", "department": "Sales", "level": "Executive"}
        ]
    }

@pytest.fixture
def mock_funding_data():
    return {
        "rounds": [
            {"amount": 5000000, "stage": "Series A", "date": "2025-11-15"}
        ],
        "total": 5000000
    }
```

---

## Performance & Scalability

### Batch Processing
- Process companies in batches of 50 to limit memory usage
- Parallel processing across signal types (job news, funding, etc.)
- Implement rate limiting per API endpoint

### Caching Strategy
- Cache company profiles for 24 hours
- Cache job postings for 6 hours
- Cache tech stack data for 7 days
- Use Redis for distributed cache

### Storage Optimization
- Compress raw_data JSONB column
- Implement partitioning by detected_at date
- Archive signals older than 2 years

### Monitoring Metrics
- Signals detected per company
- Processing latency per signal type
- API quota utilization
- Database query performance

---

## Multi-Agent Integration

### Handoff Triggers
```python
# High-intent signal detected
if intent_score >= 8.0:
    await self.handoff_to(
        target_agent="sales",
        payload={
            "lead_id": lead_id,
            "intent_score": intent_score,
            "signals": signals,
            "urgency": "high"
        },
        priority="critical"
    )

# New signals for campaign targeting
if new_signals and intent_score >= 6.5:
    await self.handoff_to(
        target_agent="campaign_personalization",
        payload={
            "lead_id": lead_id,
            "signals": signals,
            "recommended_angle": extract_primary_signal(signals)
        },
        priority="high"
    )
```

### Context Sharing
- Pass full signal history with handoffs
- Include company research context
- Maintain signal confidence scores

---

## Security & Privacy

### Data Handling
- Redact PII from signal descriptions
- Encrypt sensitive company data at rest
- Implement data retention policies

### API Security
- Rotate API keys monthly
- Use IP whitelisting where available
- Monitor for unusual API usage

### Compliance
- GDPR compliance for EU companies
- CCPA compliance for California residents
- Respect robots.txt and rate limits

---

## Acceptance Criteria

- [ ] Agent successfully scans all tracked companies daily
- [ ] Detects signals from all 7 categories with >90% accuracy
- [ ] Intent scores correlate with actual sales outcomes (R² > 0.6)
- [ ] High-intent signals (score ≥ 8) trigger outreach within 1 hour
- [ ] Processes 1000+ companies within daily batch window
- [ ] Maintains 99.9% uptime during processing windows
- [ ] All API failures handled gracefully with retry logic
- [ ] Database transactions maintain ACID compliance
- [ ] Historical signal data enables trend analysis
- [ ] Performance metrics available via monitoring dashboard

---

## Implementation Checklist

- [ ] Create IntentSignalAgent class extending BaseAgent
- [ ] Implement all 7 tools with proper error handling
- [ ] Create database models with proper indexing
- [ ] Implement signal scoring algorithm
- [ ] Add comprehensive logging and metrics
- [ ] Write unit tests for each tool
- [ ] Write integration tests for full pipeline
- [ ] Set up daily Celery task for batch processing
- [ ] Configure monitoring and alerting
- [ ] Document API rate limits and quotas
