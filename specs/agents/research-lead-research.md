# Lead Research Agent - Production Specification

## Overview

**Agent Name**: `lead_research`
**Category**: Research & Intelligence
**Purpose**: Deep-dive research on individual leads to discover personalization angles for ultra-targeted outreach
**Priority**: Phase 2 - Intelligence Layer
**Coverage Target**: >85% (agent testing requirement)

## Agent Metadata

**Dependencies**:
- Lead List Builder Agent (provides leads to research)
- Database tables must exist before agent runs

**Human-in-the-Loop**: None (fully automated research, reviewed at personalization stage by Campaign Copywriting Agent)

**Estimated Research Time**: 2-4 minutes per lead (parallel processing via Celery)

## Architecture

### Class Definition

```python
from src.agents.base_agent import BaseAgent
from src.integrations.apify import ApifyClient
from src.integrations.serper import SerperClient
# Future: from src.integrations.perplexity import PerplexityClient

class LeadResearchAgent(BaseAgent):
    """
    Researches individual leads for personalization angles.

    Scrapes LinkedIn, searches web, identifies achievements,
    and flags best personalization opportunities.
    """

    def __init__(self):
        super().__init__(
            name="lead_research",
            description="Deep-dive lead research for personalization"
        )
        self.apify_client = ApifyClient()
        self.serper_client = SerperClient()
        # Register tools after initialization
        self._register_tools()
```

### System Prompt

```
You are the Lead Research Agent for Smarter Team, an AI agency automation system.

Your mission is to conduct deep research on individual leads to uncover compelling personalization angles for cold outreach campaigns.

**Research Priorities (in order):**
1. Recent achievements (awards, promotions, speaking engagements)
2. Published content (LinkedIn posts, articles, podcasts)
3. Shared interests (hobbies, causes, communities)
4. Career transitions (new role, company changes)
5. Company trigger events (funding, expansion, new initiatives)

**Quality Standards:**
- Verify all facts from primary sources (LinkedIn, company sites, reputable news)
- Flag confidence level for each finding (high/medium/low)
- Prioritize recency (last 3 months > last year > older)
- Identify 3-5 specific personalization angles per lead
- Avoid generic observations ("works in tech", "based in SF")

**Personalization Angle Criteria:**
A good personalization angle is:
- Specific and verifiable
- Recent (ideally <90 days)
- Relevant to the offer/service
- Uncommon (not publicly obvious)
- Conversation-worthy (creates natural dialogue)

**Output Format:**
For each lead, provide:
1. Research summary (3-5 bullet points)
2. Top 3 personalization angles (ranked by strength)
3. Source URLs for verification
4. Confidence score (1-10)
5. Recommended outreach timing (if time-sensitive trigger exists)

**Error Handling:**
- If LinkedIn scraping fails, fall back to web search + company site
- If no recent activity found, flag lead for generic outreach queue
- If insufficient data (<2 angles), mark for manual review
- Always log data sources and timestamps

Focus on quality over speed. A well-researched lead converts 3-5x better than generic outreach.
```

## Tool Definitions

### 1. `scrape_linkedin_profile`

**Purpose**: Extract LinkedIn profile data using Apify actors

**Parameters**:
```python
{
    "linkedin_url": str,  # Full LinkedIn profile URL
    "lead_id": str,       # Database lead ID for tracking
}
```

**Returns**:
```python
{
    "success": bool,
    "data": {
        "full_name": str,
        "headline": str,
        "current_position": str,
        "current_company": str,
        "recent_posts": list[dict],  # Last 10 posts with text, likes, date
        "recent_activity": list[dict],  # Shares, comments, engagement
        "experience": list[dict],        # Job history
        "education": list[dict],
        "skills": list[str],
        "recommendations_count": int,
        "connections_count": int,
    },
    "scraped_at": str,  # ISO timestamp
    "error": str | None,
}
```

**Error Handling**:
- LinkedIn login required → Use Apify actor with auth
- Profile privacy settings → Fallback to public search
- Rate limit hit → Queue for retry with exponential backoff
- Invalid URL → Log error, mark lead for manual review

**Implementation Notes**:
- Use Apify actor: `apify/linkedin-profile-scraper`
- Cache results for 7 days (profiles don't change frequently)
- Respect Apify rate limits (track via BaseIntegrationClient)

---

### 2. `search_web_mentions`

**Purpose**: Find news articles, podcast appearances, speaking engagements

**Parameters**:
```python
{
    "lead_name": str,          # Full name
    "company_name": str,       # Current company (helps disambiguate)
    "search_type": str,        # "news" | "podcasts" | "speaking" | "awards"
    "date_filter": str,        # "3m" | "6m" | "1y" (months/years)
}
```

**Returns**:
```python
{
    "success": bool,
    "results": list[{
        "title": str,
        "url": str,
        "source": str,          # Publisher/platform
        "published_date": str,  # ISO date
        "snippet": str,         # Excerpt mentioning the lead
        "relevance_score": float,  # 0-1 (how relevant to personalization)
    }],
    "total_results": int,
    "error": str | None,
}
```

**Error Handling**:
- No results found → Try variations (nicknames, middle initials)
- Common name collision → Add company context to query
- API quota exceeded → Log and schedule retry
- Stale results → Filter by date_filter parameter

**Implementation Notes**:
- Use Serper API for Google search
- Query format: `"{lead_name}" "{company_name}" {search_type}`
- Future: Add Perplexity API for AI-summarized results

---

### 3. `extract_personalization_angles`

**Purpose**: Analyze research data and identify top personalization opportunities

**Parameters**:
```python
{
    "linkedin_data": dict,      # From scrape_linkedin_profile
    "web_mentions": dict,       # From search_web_mentions
    "company_context": dict,    # Company research if available
}
```

**Returns**:
```python
{
    "angles": list[{
        "angle_type": str,       # "achievement" | "content" | "transition" | "interest"
        "description": str,      # Human-readable angle
        "source_url": str,       # Verification link
        "recency_days": int,     # Days since event/post
        "confidence": str,       # "high" | "medium" | "low"
        "usage_suggestion": str, # How to use in outreach
        "priority_score": float, # 0-10 ranking
    }],
    "recommended_angle": dict,   # Top-ranked angle
    "fallback_angles": list[dict],  # Backup options
}
```

**Error Handling**:
- Insufficient data → Return generic angles with low confidence
- Conflicting information → Flag for manual review
- All low-confidence → Recommend lead for generic queue

**Implementation Notes**:
- Use Claude API to analyze research data (leverage LLM reasoning)
- Apply recency weighting: <30 days (2x), 30-90 days (1.5x), >90 days (1x)
- Score based on specificity, verifiability, relevance

---

### 4. `store_research_results`

**Purpose**: Persist research findings to database

**Parameters**:
```python
{
    "lead_id": str,
    "research_summary": str,
    "personalization_angles": list[dict],
    "sources": list[dict],
    "confidence_score": float,
    "research_metadata": dict,
}
```

**Returns**:
```python
{
    "success": bool,
    "research_id": str,       # UUID of created research record
    "angles_stored": int,     # Count of angles saved
    "error": str | None,
}
```

**Error Handling**:
- Database connection failed → Retry 3x with backoff
- Duplicate research → Update existing record
- Invalid lead_id → Raise ValueError

**Implementation Notes**:
- Use SQLAlchemy async ORM
- Transaction: research record + angles + sources (atomic)
- Update lead status to "researched"

---

### 5. `check_research_cache`

**Purpose**: Avoid re-researching leads within freshness window

**Parameters**:
```python
{
    "lead_id": str,
    "max_age_days": int,  # Default: 30
}
```

**Returns**:
```python
{
    "cached": bool,
    "research": dict | None,  # Cached research if found
    "age_days": int,
    "needs_refresh": bool,
}
```

**Error Handling**:
- Lead not found → Return `{"cached": false}`
- Stale cache → Return with `needs_refresh: true`

**Implementation Notes**:
- Query `lead_research` table with timestamp filter
- Consider refresh triggers: job change, company news

## Process Flow

### Task Input Schema

```python
{
    "task_type": "research_lead",
    "lead_id": str,           # Required
    "lead_name": str,         # Required
    "company_name": str,      # Required
    "linkedin_url": str,      # Required
    "email": str,             # Optional
    "force_refresh": bool,    # Default: False
    "priority": str,          # "critical" | "high" | "normal" | "low"
}
```

### Execution Steps

1. **Validate Input**
   - Check required fields present
   - Validate LinkedIn URL format
   - Log research start

2. **Check Cache**
   - Query `check_research_cache(lead_id, max_age_days=30)`
   - If cached and not force_refresh, return cached data
   - If needs_refresh, proceed with research

3. **LinkedIn Scraping** (Primary Source)
   - Call `scrape_linkedin_profile(linkedin_url, lead_id)`
   - Handle errors gracefully (log, continue with limited data)
   - Store raw data in `lead_research_sources`

4. **Web Search** (Secondary Source)
   - Parallel searches:
     - News mentions (3 months)
     - Podcast appearances (6 months)
     - Speaking engagements (1 year)
     - Awards/recognition (1 year)
   - Aggregate results, deduplicate URLs

5. **Angle Extraction**
   - Call `extract_personalization_angles()` with all data
   - Rank angles by priority_score
   - Flag top 3 for immediate use

6. **Database Storage**
   - Call `store_research_results()` in transaction
   - Update lead status to "researched"
   - Log completion

7. **Handoff Decision**
   - If high-quality angles found (confidence > 7/10):
     - Handoff to Campaign Copywriting Agent
   - If medium quality (4-7/10):
     - Queue for human review
   - If low quality (<4/10):
     - Add to generic outreach queue

### Task Output Schema

```python
{
    "status": "completed" | "failed" | "partial",
    "research_id": str,
    "lead_id": str,
    "summary": {
        "angles_found": int,
        "top_angle": dict,
        "confidence_score": float,
        "sources_count": int,
    },
    "next_action": str,  # "personalize_outreach" | "manual_review" | "generic_queue"
    "errors": list[str],
}
```

## Database Schema

### Table: `lead_research`

Primary research record per lead.

```sql
CREATE TABLE lead_research (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Research metadata
    research_summary TEXT NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 10),

    -- Quality metrics
    angles_found INTEGER DEFAULT 0,
    sources_count INTEGER DEFAULT 0,

    -- Timestamps
    researched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- When to refresh research

    -- Processing status
    status VARCHAR(50) DEFAULT 'pending',  -- pending | completed | failed
    error_message TEXT,

    -- Indexes
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(lead_id)  -- One active research per lead
);

CREATE INDEX idx_lead_research_lead_id ON lead_research(lead_id);
CREATE INDEX idx_lead_research_status ON lead_research(status);
CREATE INDEX idx_lead_research_expires_at ON lead_research(expires_at);
```

---

### Table: `personalization_angles`

Individual personalization opportunities discovered.

```sql
CREATE TABLE personalization_angles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_id UUID NOT NULL REFERENCES lead_research(id) ON DELETE CASCADE,

    -- Angle details
    angle_type VARCHAR(50) NOT NULL,  -- achievement | content | transition | interest
    description TEXT NOT NULL,
    usage_suggestion TEXT,

    -- Scoring
    priority_score DECIMAL(4,2) CHECK (priority_score >= 0 AND priority_score <= 10),
    confidence VARCHAR(20) NOT NULL,  -- high | medium | low

    -- Metadata
    source_url TEXT,
    recency_days INTEGER,

    -- Usage tracking
    used_in_campaign_id UUID,  -- References campaigns table (future)
    used_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_personalization_angles_research_id ON personalization_angles(research_id);
CREATE INDEX idx_personalization_angles_priority ON personalization_angles(priority_score DESC);
CREATE INDEX idx_personalization_angles_type ON personalization_angles(angle_type);
```

---

### Table: `lead_research_sources`

Raw data sources for audit trail and re-analysis.

```sql
CREATE TABLE lead_research_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_id UUID NOT NULL REFERENCES lead_research(id) ON DELETE CASCADE,

    -- Source details
    source_type VARCHAR(50) NOT NULL,  -- linkedin | news | podcast | speaking | awards
    source_url TEXT,
    source_data JSONB NOT NULL,  -- Raw API response

    -- Quality
    reliability_score DECIMAL(3,2),  -- 0-1 (source trustworthiness)

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lead_research_sources_research_id ON lead_research_sources(research_id);
CREATE INDEX idx_lead_research_sources_type ON lead_research_sources(source_type);
CREATE INDEX idx_lead_research_sources_data ON lead_research_sources USING gin(source_data);
```

## Integration Details

### Apify (LinkedIn Scraping)

**Actor**: `apify/linkedin-profile-scraper`

**Configuration**:
```python
{
    "startUrls": [{"url": linkedin_url}],
    "maxResults": 1,
    "proxyConfiguration": {
        "useApifyProxy": true,
        "apifyProxyGroups": ["RESIDENTIAL"]
    }
}
```

**Rate Limits**:
- Free tier: 10 runs/month
- Paid: Unlimited (charged per compute unit)
- Recommended: Cache results for 7 days

**Error Codes**:
- `PROXY_ERROR` → Retry with different proxy
- `LOGIN_REQUIRED` → Enable authentication in settings
- `RATE_LIMIT` → Exponential backoff (1min, 5min, 15min)

---

### Serper (Web Search)

**API**: `https://google.serper.dev/search`

**Query Templates**:
```python
news_query = f'"{lead_name}" "{company_name}" (news OR press OR article)'
podcast_query = f'"{lead_name}" (podcast OR interview OR "speaking on")'
speaking_query = f'"{lead_name}" (conference OR speaker OR keynote)'
awards_query = f'"{lead_name}" (award OR recognition OR "named to")'
```

**Rate Limits**:
- Free tier: 2,500 searches/month
- Paid: 100,000+ searches/month
- Track via `rate_limit_remaining` in BaseIntegrationClient

**Response Handling**:
```python
# Filter by date
results = [r for r in response["organic"] if is_recent(r["date"])]

# Score relevance
for result in results:
    result["relevance_score"] = calculate_relevance(
        result["snippet"],
        lead_name
    )
```

---

### Perplexity (Future Enhancement)

**Use Case**: AI-powered research summaries

**Prompt Template**:
```
Research {lead_name} at {company_name}. Find:
1. Recent achievements (awards, promotions, speaking)
2. Published content (articles, posts, podcasts)
3. Career transitions
4. Unique interests or affiliations

Focus on last 6 months. Provide sources for all claims.
```

**Benefits**:
- Faster than scraping + searching
- Contextual understanding
- Automatic source verification

**When to Use**: High-value leads (>$50k deal size)

## Error Handling Strategy

### Error Categories

1. **Transient Errors** (Retry with backoff)
   - Network timeouts
   - Rate limits
   - Service unavailable (503)

2. **Input Errors** (Fail fast, log)
   - Invalid LinkedIn URL
   - Missing required fields
   - Lead not found in database

3. **Data Quality Errors** (Degrade gracefully)
   - No LinkedIn activity found
   - Name collision (common names)
   - Insufficient public information

4. **Integration Errors** (Fallback to alternatives)
   - Apify quota exceeded → Use web search only
   - Serper down → Skip web mentions, use LinkedIn only
   - Database write failed → Queue for retry

### Error Response Format

```python
{
    "error_type": str,       # "transient" | "input" | "data_quality" | "integration"
    "error_code": str,       # Specific error identifier
    "error_message": str,    # Human-readable description
    "retry_recommended": bool,
    "fallback_action": str,  # What the agent did instead
    "timestamp": str,
}
```

### Retry Logic

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    autoretry_for=(httpx.RequestError, httpx.HTTPStatusError),
    retry_backoff=True,
    retry_backoff_max=600,  # 10 minutes
    retry_jitter=True,
)
async def research_lead_task(self, task_data: dict):
    """Celery task with built-in retry logic."""
    agent = LeadResearchAgent()
    return await agent.process_task(task_data)
```

## Testing Requirements

### Unit Tests (>90% coverage for tools)

**File**: `__tests__/unit/agents/test_lead_research_agent.py`

Test scenarios:
1. `test_agent_initialization` - Agent setup with integrations
2. `test_scrape_linkedin_success` - Happy path scraping
3. `test_scrape_linkedin_privacy_error` - Handle private profiles
4. `test_search_web_mentions_news` - News search results
5. `test_search_web_mentions_no_results` - Empty results handling
6. `test_extract_angles_high_quality` - Strong personalization data
7. `test_extract_angles_low_quality` - Weak data fallback
8. `test_store_research_results` - Database writes
9. `test_check_research_cache_hit` - Cache retrieval
10. `test_check_research_cache_miss` - No cached data

**Mocking Strategy**:
```python
@pytest.fixture
def mock_apify_client(mocker):
    mock = mocker.patch("src.integrations.apify.ApifyClient")
    mock.return_value.scrape_profile.return_value = {
        "success": True,
        "data": {...}  # Sample LinkedIn data
    }
    return mock
```

---

### Integration Tests (>85% coverage)

**File**: `__tests__/integration/test_lead_research_integration.py`

Test scenarios:
1. `test_full_research_flow` - End-to-end with real DB
2. `test_research_with_cache` - Cache hit scenario
3. `test_research_with_apify_failure` - Fallback to web search
4. `test_parallel_lead_research` - Multiple leads concurrently
5. `test_handoff_to_copywriting` - Agent handoff on success
6. `test_database_transaction_rollback` - Error handling

**Setup**:
```python
@pytest.fixture
async def test_db():
    """Create test database with schema."""
    # Apply migrations to test DB
    # Yield connection
    # Cleanup after test

@pytest.fixture
async def sample_lead():
    """Create test lead in database."""
    return await create_lead({
        "name": "Jane Doe",
        "company": "TechCorp",
        "linkedin_url": "https://linkedin.com/in/janedoe",
        "email": "jane@techcorp.com"
    })
```

---

### Performance Tests

**File**: `__tests__/performance/test_lead_research_performance.py`

Test scenarios:
1. `test_single_lead_research_time` - Should complete in <4 minutes
2. `test_batch_research_throughput` - 100 leads in <30 minutes (parallel)
3. `test_cache_lookup_speed` - Cache check <100ms
4. `test_database_write_performance` - Bulk inserts <1s per 100 records

**Benchmarks**:
- Single lead: 2-4 minutes target
- Cache hit: <100ms
- Database write: <500ms
- Apify scrape: 30-90 seconds
- Web search: 1-3 seconds per query

## Implementation Checklist

### Phase 1: Foundation (Week 1)

- [ ] Create agent file: `src/agents/lead_research/agent.py`
- [ ] Implement BaseAgent extension with system_prompt
- [ ] Create Apify integration: `src/integrations/apify.py`
- [ ] Create Serper integration: `src/integrations/serper.py`
- [ ] Write unit tests for integrations (>90% coverage)
- [ ] Create database migration for 3 tables
- [ ] Apply migration to dev database
- [ ] Verify tables created correctly

### Phase 2: Core Tools (Week 2)

- [ ] Implement `scrape_linkedin_profile` tool
- [ ] Implement `search_web_mentions` tool
- [ ] Implement `extract_personalization_angles` tool
- [ ] Implement `store_research_results` tool
- [ ] Implement `check_research_cache` tool
- [ ] Write unit tests for each tool (>90% coverage)
- [ ] Test tools with mock data
- [ ] Handle all error scenarios

### Phase 3: Process Flow (Week 2-3)

- [ ] Implement `process_task` method with full flow
- [ ] Add input validation and logging
- [ ] Implement cache checking logic
- [ ] Add parallel web search execution
- [ ] Implement handoff decision logic
- [ ] Write integration tests (>85% coverage)
- [ ] Test with real Apify/Serper (sandbox mode)
- [ ] Verify database transactions work correctly

### Phase 4: Error Handling (Week 3)

- [ ] Implement retry logic for transient errors
- [ ] Add graceful degradation for missing data
- [ ] Create fallback paths for integration failures
- [ ] Add comprehensive error logging
- [ ] Test all error scenarios
- [ ] Document error codes and resolutions

### Phase 5: Quality & Performance (Week 4)

- [ ] Run full test suite (`make test`)
- [ ] Verify >85% coverage for agent
- [ ] Verify >90% coverage for tools
- [ ] Run performance benchmarks
- [ ] Optimize slow queries (if any)
- [ ] Add monitoring/alerting hooks
- [ ] Load test with 100 leads
- [ ] Review and refactor code

### Phase 6: Integration & Deployment (Week 4)

- [ ] Create Celery task wrapper
- [ ] Test agent handoff from Lead List Builder
- [ ] Test handoff to Campaign Copywriting
- [ ] Create API endpoint: `POST /api/research/lead`
- [ ] Write API integration tests
- [ ] Update CLAUDE.md with agent patterns
- [ ] Create runbook for troubleshooting
- [ ] Deploy to staging environment

### Phase 7: Documentation (Week 4)

- [ ] Write inline docstrings (all methods)
- [ ] Generate API documentation
- [ ] Create troubleshooting guide
- [ ] Document rate limits and costs
- [ ] Add examples to README
- [ ] Update TASK-LOG.md
- [ ] Move task to _completed/

## Success Metrics

**Quality Metrics**:
- Test coverage: >85% for agent, >90% for tools
- No MyPy type errors
- Ruff linting passes
- All pre-commit hooks pass

**Performance Metrics**:
- Single lead research: <4 minutes
- Cache lookup: <100ms
- Database write: <500ms
- Batch throughput: >3 leads/minute

**Business Metrics**:
- Personalization angle discovery rate: >70% of leads
- High-confidence angles: >40% of leads
- Research freshness: <30 days for 90% of leads
- Source verification rate: 100%

## Future Enhancements

1. **Perplexity Integration** (Phase 3)
   - Replace scraping + searching with AI research
   - Faster, more contextual results
   - Automatic fact-checking

2. **Mutual Connections** (Phase 3)
   - LinkedIn Sales Navigator integration
   - Identify warm intro paths
   - Track relationship strength

3. **Social Listening** (Phase 4)
   - Monitor Twitter/X mentions
   - Track Reddit discussions
   - GitHub activity for technical leads

4. **Automated Refresh** (Phase 2)
   - Cron job to refresh stale research
   - Trigger refresh on job change detection
   - Prioritize leads in active campaigns

5. **Research Quality Scoring** (Phase 3)
   - ML model to predict angle effectiveness
   - A/B test angles in campaigns
   - Feedback loop from response rates

6. **Cost Optimization** (Ongoing)
   - Smart caching strategy
   - Rate limit pooling across agents
   - Bulk scraping for efficiency

## Appendix: Example Research Output

```json
{
    "research_id": "550e8400-e29b-41d4-a716-446655440000",
    "lead_id": "123e4567-e89b-12d3-a456-426614174000",
    "research_summary": "Jane Doe recently promoted to VP Engineering at TechCorp (2 months ago). Published article on AI ethics in Forbes (1 month ago). Speaking at DevOps Summit next month. Active on LinkedIn with weekly posts about engineering leadership.",
    "confidence_score": 8.5,
    "personalization_angles": [
        {
            "angle_type": "achievement",
            "description": "Recent promotion to VP Engineering at TechCorp",
            "source_url": "https://linkedin.com/posts/janedoe/promotion-announcement",
            "recency_days": 45,
            "confidence": "high",
            "usage_suggestion": "Congratulate on promotion, tie into leadership scaling challenges",
            "priority_score": 9.2
        },
        {
            "angle_type": "content",
            "description": "Published Forbes article on ethical AI implementation",
            "source_url": "https://forbes.com/sites/janedoe/ethical-ai-2024",
            "recency_days": 30,
            "confidence": "high",
            "usage_suggestion": "Reference article, offer perspective on AI governance frameworks",
            "priority_score": 8.8
        },
        {
            "angle_type": "interest",
            "description": "Speaking at DevOps Summit on 'Scaling Engineering Teams'",
            "source_url": "https://devopssummit.com/speakers/jane-doe",
            "recency_days": -15,  # 15 days in future
            "confidence": "high",
            "usage_suggestion": "Offer to share case study for talk, attend session",
            "priority_score": 8.3
        }
    ],
    "next_action": "personalize_outreach",
    "sources_count": 7,
    "researched_at": "2025-12-05T19:30:00Z"
}
```

## Notes

- This agent is CPU-bound (web scraping, API calls), ideal for Celery async tasks
- Consider dedicated worker pool for research tasks to avoid blocking other agents
- Apify costs: ~$0.10-0.50 per profile scrape (use caching aggressively)
- Serper costs: ~$0.001 per search (negligible at scale)
- Expected research cost per lead: $0.20-0.75 (mostly Apify)
