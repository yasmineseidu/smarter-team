# Company Research Agent - Production Specification

**Agent Name:** `company_research`

**Category:** Research & Intelligence

**Status:** Ready for Implementation

**Coverage Requirement:** >85% (agents)

**Generated:** 2025-12-05

---

## Overview

The Company Research Agent autonomously researches companies to identify trigger events, growth signals, pain points, and contextual intelligence. This agent provides actionable insights for sales and outreach personalization by analyzing news, job postings, tech stack, LinkedIn activity, and competitive positioning.

**Input:** Company name, website, LinkedIn URL
**Output:** Comprehensive company brief with trigger events and growth/pain signals
**Trigger:** Handoff from Lead List Builder Agent or manual API call

---

## System Prompt

```
You are the Company Research Agent for Smarter Team, an autonomous AI agency.

Your mission is to research companies thoroughly and identify actionable trigger events for sales outreach.

**Core Responsibilities:**
1. Gather recent company news (funding, acquisitions, leadership changes, expansions)
2. Analyze job postings to identify growth signals and pain points
3. Detect tech stack and technology trends
4. Review LinkedIn activity and press releases
5. Assess competitive positioning
6. Identify and prioritize trigger events

**Trigger Event Categories (priority order):**
- CRITICAL: Recent funding rounds, acquisitions, executive changes, major product launches
- HIGH: Rapid hiring, new market expansion, technology migrations, competitive wins
- MEDIUM: Product updates, partnership announcements, award wins
- LOW: General growth, routine hiring, blog posts

**Decision Criteria:**
- News must be within last 90 days to be considered "recent"
- Job postings indicating >20% headcount growth = strong growth signal
- Tech stack migrations (detected via BuiltWith changes) = pain point opportunity
- LinkedIn posts from C-suite = high-priority insights
- Competitive moves mentioned in news = positioning opportunity

**Output Format:**
- Structured JSON with categorized insights
- Trigger events ranked by priority and recency
- Actionable insights for sales personalization
- Confidence scores for each finding (0.0-1.0)

**Error Handling:**
- If company name is ambiguous, request clarification
- If no recent news found, flag as "low-intent" company
- If API rate limits hit, queue for retry with exponential backoff
- If website unreachable, log warning and continue with available data

Always prioritize actionable, recent, and verifiable insights over volume.
```

---

## Agent Architecture

### Inheritance
```python
from src.agents.base_agent import BaseAgent

class CompanyResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="company_research",
            description="Research companies for trigger events and growth signals"
        )
```

### Dependencies
- **Upstream:** Lead List Builder Agent (`lead_list_builder`)
- **Downstream:** Campaign Personalization Agent (`campaign_personalization`)
- **Integrations:** Apify, Serper, BuiltWith, News API, Firecrawl, Perplexity

---

## Tools & Methods

### 1. `search_company_news`

**Purpose:** Search for recent company news using Serper and News API

**Parameters:**
```python
{
    "company_name": str,              # Full company name
    "domain": str | None,             # Company domain (optional)
    "lookback_days": int = 90,        # How far back to search (default 90)
    "max_results": int = 20           # Maximum news articles
}
```

**Returns:**
```python
{
    "articles": [
        {
            "title": str,
            "url": str,
            "source": str,
            "published_date": str,        # ISO 8601 format
            "snippet": str,
            "relevance_score": float,     # 0.0-1.0
            "trigger_category": str | None  # "funding", "acquisition", etc.
        }
    ],
    "total_found": int,
    "sources_used": list[str],            # ["serper", "newsapi"]
    "cache_hit": bool
}
```

**Error Handling:**
- `HTTPStatusError`: Log and retry with exponential backoff (max 3 retries)
- `RateLimitError`: Queue for later processing, return cached results if available
- `ValidationError`: Log and return empty results with error flag

**Implementation Notes:**
- Search query: `"{company_name}" AND (funding OR acquisition OR CEO OR expansion OR product launch)`
- Filter results to last `lookback_days`
- Deduplicate by URL and title similarity (>80% match)
- Cache results for 24 hours (Redis)

---

### 2. `scrape_linkedin_company`

**Purpose:** Scrape company LinkedIn page for recent posts and employee count

**Parameters:**
```python
{
    "linkedin_url": str,              # LinkedIn company page URL
    "include_posts": bool = True,     # Fetch recent posts
    "max_posts": int = 10             # Maximum posts to retrieve
}
```

**Returns:**
```python
{
    "company_info": {
        "name": str,
        "follower_count": int,
        "employee_count_range": str,  # e.g., "501-1000"
        "industry": str,
        "headquarters": str,
        "specialties": list[str]
    },
    "recent_posts": [
        {
            "text": str,
            "posted_date": str,           # ISO 8601
            "likes": int,
            "comments": int,
            "author": str,                # Name and title
            "is_executive": bool          # C-suite author
        }
    ],
    "scrape_timestamp": str
}
```

**Error Handling:**
- `ApifyError`: Log and continue without LinkedIn data
- `InvalidURLError`: Validate and attempt to fix URL, else skip
- `PrivateProfileError`: Log and return partial data

**Implementation Notes:**
- Use Apify's LinkedIn Scraper actor (`apify/linkedin-company-scraper`)
- Extract executive posts separately (filter by title: CEO, CTO, CMO, etc.)
- Cache for 7 days (less frequently changing)

---

### 3. `search_job_postings`

**Purpose:** Search job boards for company postings to identify growth/pain signals

**Parameters:**
```python
{
    "company_name": str,
    "domain": str | None,
    "location": str | None = None,    # Optional location filter
    "max_results": int = 50
}
```

**Returns:**
```python
{
    "jobs": [
        {
            "title": str,
            "location": str,
            "posted_date": str,
            "job_board": str,             # "linkedin", "indeed", etc.
            "seniority": str,             # "entry", "mid", "senior", "executive"
            "department": str,            # "engineering", "sales", etc.
            "url": str
        }
    ],
    "total_count": int,
    "growth_signals": {
        "rapid_hiring": bool,             # >20% of workforce in 90 days
        "new_departments": list[str],     # Recently created teams
        "executive_hires": int,           # C-suite openings
        "technical_roles": int,           # Engineering/dev roles
        "sales_roles": int                # Sales/BD roles
    },
    "analysis_timestamp": str
}
```

**Error Handling:**
- `JobBoardError`: Fallback to next job board, log failure
- `ParsingError`: Skip malformed job listings, continue
- `NoResultsError`: Return empty with flag, not failure

**Implementation Notes:**
- Use Apify's LinkedIn Job Scraper + Indeed Scraper
- Detect "rapid hiring" by comparing against industry benchmarks
- Flag departments that didn't exist 6 months ago
- Cache for 3 days

---

### 4. `analyze_tech_stack`

**Purpose:** Detect company's technology stack and recent changes

**Parameters:**
```python
{
    "domain": str,                    # Primary domain
    "include_history": bool = True    # Include historical changes
}
```

**Returns:**
```python
{
    "technologies": {
        "frontend": list[str],
        "backend": list[str],
        "infrastructure": list[str],
        "analytics": list[str],
        "marketing": list[str],
        "payments": list[str]
    },
    "recent_changes": [
        {
            "technology": str,
            "change_type": str,           # "added", "removed", "updated"
            "detected_date": str,
            "category": str
        }
    ],
    "migration_signals": [
        {
            "from_tech": str,
            "to_tech": str,
            "confidence": float,          # 0.0-1.0
            "implications": str           # Pain point description
        }
    ],
    "last_scan_date": str
}
```

**Error Handling:**
- `BuiltWithError`: Log and return limited data from Wappalyzer fallback
- `DomainNotFoundError`: Return empty, flag for manual review
- `APIQuotaError`: Use cached data, schedule retry

**Implementation Notes:**
- Primary: BuiltWith API (`/v21/api.json`)
- Fallback: Wappalyzer (self-hosted detection)
- Compare current stack to 90-day-old snapshot for changes
- Cache for 14 days

---

### 5. `scrape_company_website`

**Purpose:** Extract press releases, blog posts, and company updates

**Parameters:**
```python
{
    "domain": str,
    "pages_to_scrape": list[str] = ["/blog", "/press", "/news", "/about"],
    "max_pages": int = 20
}
```

**Returns:**
```python
{
    "content": [
        {
            "title": str,
            "url": str,
            "published_date": str | None,
            "content_type": str,          # "blog", "press", "about"
            "summary": str,               # 200 char summary
            "key_topics": list[str],
            "relevance_score": float
        }
    ],
    "website_health": {
        "accessible": bool,
        "https_enabled": bool,
        "response_time_ms": int,
        "last_updated": str | None        # From copyright/meta
    }
}
```

**Error Handling:**
- `FirecrawlError`: Fallback to basic HTTP scraping with BeautifulSoup
- `TimeoutError`: Reduce max_pages, retry
- `404Error`: Log and skip page, continue others

**Implementation Notes:**
- Use Firecrawl API for intelligent scraping
- Extract dates from meta tags, URLs, content
- Summarize using Claude Haiku for efficiency
- Cache for 7 days

---

### 6. `identify_trigger_events`

**Purpose:** Analyze all research data and identify prioritized trigger events

**Parameters:**
```python
{
    "company_data": {
        "news": dict,
        "linkedin": dict,
        "jobs": dict,
        "tech_stack": dict,
        "website": dict
    },
    "min_confidence": float = 0.6     # Minimum confidence threshold
}
```

**Returns:**
```python
{
    "trigger_events": [
        {
            "event_type": str,            # "funding", "hiring", "migration", etc.
            "priority": str,              # "critical", "high", "medium", "low"
            "confidence": float,          # 0.0-1.0
            "description": str,
            "source": str,                # Data source
            "detected_date": str,
            "recency_days": int,
            "actionable_insight": str,    # For sales personalization
            "evidence": list[str]         # Supporting data points
        }
    ],
    "overall_intent_score": float,        # 0.0-1.0
    "recommended_action": str,            # "engage_now", "nurture", "skip"
    "analysis_timestamp": str
}
```

**Error Handling:**
- `InsufficientDataError`: Return low-confidence results with warning
- `AnalysisError`: Log, use rule-based fallback

**Implementation Notes:**
- Use Claude Opus 4.5 for nuanced analysis
- Weight events by recency (exponential decay: 0.5^(days/30))
- Cross-reference events across sources for validation
- Trigger event types: funding, acquisition, expansion, leadership_change, product_launch, rapid_hiring, tech_migration, competitive_move, award, partnership

---

### 7. `generate_company_brief`

**Purpose:** Synthesize all research into actionable company brief

**Parameters:**
```python
{
    "company_name": str,
    "all_research_data": dict,
    "trigger_events": list[dict],
    "format": str = "full"            # "full" or "summary"
}
```

**Returns:**
```python
{
    "company_name": str,
    "domain": str,
    "brief": {
        "executive_summary": str,     # 3-4 sentences
        "key_insights": list[str],    # Top 5 bullet points
        "trigger_events": list[dict], # Prioritized events
        "growth_signals": {
            "hiring_velocity": str,
            "funding_status": str,
            "market_expansion": bool,
            "tech_investment": str
        },
        "pain_points": list[str],     # Inferred pain points
        "competitive_landscape": str,
        "recommended_approach": str,  # Sales angle
        "confidence_score": float
    },
    "data_freshness": {
        "news_age_days": int,
        "jobs_age_days": int,
        "linkedin_age_days": int
    },
    "generated_at": str,
    "research_id": str                # Unique ID for this research
}
```

**Error Handling:**
- `GenerationError`: Use template-based fallback
- `MissingDataError`: Generate partial brief, flag gaps

**Implementation Notes:**
- Use Claude Opus 4.5 for synthesis
- Include confidence scores for transparency
- Store brief in PostgreSQL (`company_research` table)
- Generate unique research_id (UUID)

---

## Database Schema

### `company_research` Table
```sql
CREATE TABLE company_research (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    linkedin_url VARCHAR(500),
    research_data JSONB NOT NULL,        -- All research results
    trigger_events JSONB NOT NULL,       -- Array of trigger events
    brief JSONB NOT NULL,                -- Generated brief
    overall_intent_score FLOAT,
    data_freshness JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- Auto-expire old research
    lead_id UUID REFERENCES leads(id),   -- Link to lead
    UNIQUE(domain, created_at::DATE)     -- One research per domain per day
);

CREATE INDEX idx_company_research_domain ON company_research(domain);
CREATE INDEX idx_company_research_created_at ON company_research(created_at);
CREATE INDEX idx_company_research_intent_score ON company_research(overall_intent_score);
CREATE INDEX idx_company_research_expires_at ON company_research(expires_at);
```

### `company_news` Table
```sql
CREATE TABLE company_news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_research_id UUID REFERENCES company_research(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(100),
    published_date TIMESTAMP WITH TIME ZONE,
    snippet TEXT,
    relevance_score FLOAT,
    trigger_category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_company_news_research_id ON company_news(company_research_id);
CREATE INDEX idx_company_news_published_date ON company_news(published_date);
```

### `company_jobs` Table
```sql
CREATE TABLE company_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_research_id UUID REFERENCES company_research(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    location VARCHAR(200),
    posted_date TIMESTAMP WITH TIME ZONE,
    job_board VARCHAR(50),
    seniority VARCHAR(50),
    department VARCHAR(100),
    url VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_company_jobs_research_id ON company_jobs(company_research_id);
CREATE INDEX idx_company_jobs_department ON company_jobs(department);
```

### `company_tech_stack` Table
```sql
CREATE TABLE company_tech_stack (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_research_id UUID REFERENCES company_research(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    technologies JSONB NOT NULL,         -- Categorized technologies
    recent_changes JSONB,                -- Array of changes
    migration_signals JSONB,             -- Array of migrations
    last_scan_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_company_tech_stack_research_id ON company_tech_stack(company_research_id);
CREATE INDEX idx_company_tech_stack_domain ON company_tech_stack(domain);
```

### `trigger_events` Table
```sql
CREATE TABLE trigger_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_research_id UUID REFERENCES company_research(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    priority VARCHAR(20) NOT NULL,      -- critical, high, medium, low
    confidence FLOAT NOT NULL,
    description TEXT NOT NULL,
    source VARCHAR(100),
    detected_date TIMESTAMP WITH TIME ZONE,
    recency_days INT,
    actionable_insight TEXT,
    evidence JSONB,                     -- Array of evidence
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_trigger_events_research_id ON trigger_events(company_research_id);
CREATE INDEX idx_trigger_events_priority ON trigger_events(priority);
CREATE INDEX idx_trigger_events_confidence ON trigger_events(confidence);
```

---

## Integration Clients

### 1. SerperClient
```python
from src.integrations.base import BaseIntegrationClient

class SerperClient(BaseIntegrationClient):
    def __init__(self, api_key: str):
        super().__init__(
            name="serper",
            base_url="https://google.serper.dev",
            api_key=api_key,
            timeout=30.0
        )

    async def search_news(
        self,
        query: str,
        num: int = 20,
        tbs: str | None = None  # Time filter (e.g., "qdr:m3" for last 3 months)
    ) -> dict[str, Any]:
        """Search Google News via Serper API."""
        payload = {
            "q": query,
            "num": num,
            "type": "news"
        }
        if tbs:
            payload["tbs"] = tbs

        return await self.post("/search", json=payload)
```

### 2. ApifyClient
```python
class ApifyClient(BaseIntegrationClient):
    def __init__(self, api_key: str):
        super().__init__(
            name="apify",
            base_url="https://api.apify.com/v2",
            api_key=api_key,
            timeout=120.0  # Longer timeout for scraping
        )

    async def scrape_linkedin_company(
        self,
        linkedin_url: str,
        max_posts: int = 10
    ) -> dict[str, Any]:
        """Run LinkedIn company scraper actor."""
        actor_id = "apify/linkedin-company-scraper"
        run_input = {
            "companyUrls": [linkedin_url],
            "maxPosts": max_posts
        }

        # Start actor run
        run = await self.post(
            f"/acts/{actor_id}/runs",
            json=run_input,
            params={"token": self.api_key}
        )

        # Wait for completion and get results
        # (Implementation: poll run status, fetch dataset)
        return run
```

### 3. BuiltWithClient
```python
class BuiltWithClient(BaseIntegrationClient):
    def __init__(self, api_key: str):
        super().__init__(
            name="builtwith",
            base_url="https://api.builtwith.com",
            api_key=api_key,
            timeout=30.0
        )

    async def get_tech_stack(
        self,
        domain: str,
        include_history: bool = True
    ) -> dict[str, Any]:
        """Get technology profile for domain."""
        return await self.get(
            f"/v21/api.json",
            params={
                "KEY": self.api_key,
                "LOOKUP": domain,
                "HISTORY": "1" if include_history else "0"
            }
        )
```

### 4. NewsAPIClient
```python
class NewsAPIClient(BaseIntegrationClient):
    def __init__(self, api_key: str):
        super().__init__(
            name="newsapi",
            base_url="https://newsapi.org/v2",
            api_key=api_key,
            timeout=30.0
        )

    async def search_everything(
        self,
        query: str,
        from_date: str | None = None,
        language: str = "en",
        page_size: int = 20
    ) -> dict[str, Any]:
        """Search all news articles."""
        params = {
            "q": query,
            "language": language,
            "pageSize": page_size,
            "apiKey": self.api_key
        }
        if from_date:
            params["from"] = from_date

        return await self.get("/everything", params=params)
```

### 5. FirecrawlClient
```python
class FirecrawlClient(BaseIntegrationClient):
    def __init__(self, api_key: str):
        super().__init__(
            name="firecrawl",
            base_url="https://api.firecrawl.dev",
            api_key=api_key,
            timeout=60.0
        )

    async def scrape_url(
        self,
        url: str,
        extract_schema: dict | None = None
    ) -> dict[str, Any]:
        """Scrape URL with optional schema extraction."""
        payload = {"url": url}
        if extract_schema:
            payload["extractSchema"] = extract_schema

        return await self.post("/v1/scrape", json=payload)

    async def crawl_website(
        self,
        domain: str,
        max_pages: int = 20,
        allowed_paths: list[str] | None = None
    ) -> dict[str, Any]:
        """Crawl entire website."""
        payload = {
            "url": domain,
            "maxPages": max_pages
        }
        if allowed_paths:
            payload["allowedPaths"] = allowed_paths

        return await self.post("/v1/crawl", json=payload)
```

---

## Error Handling Strategy

### Error Categories

1. **Transient Errors** (retry with exponential backoff)
   - Rate limiting (429)
   - Timeouts (408, 504)
   - Server errors (500, 502, 503)
   - Network errors

2. **Client Errors** (log and skip)
   - Invalid domain (400)
   - Not found (404)
   - Unauthorized (401, 403)

3. **Data Errors** (log and continue with partial data)
   - Parsing failures
   - Missing required fields
   - Invalid dates

4. **Critical Errors** (fail task, alert admin)
   - Database connection failures
   - Missing API keys
   - Corrupted data

### Retry Logic
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import httpx

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def resilient_api_call(func, *args, **kwargs):
    """Wrapper for API calls with retry logic."""
    return await func(*args, **kwargs)
```

### Fallback Strategy
- Serper fails → Use NewsAPI
- Apify fails → Skip LinkedIn data, continue
- BuiltWith fails → Use basic tech detection, lower confidence
- Firecrawl fails → Use httpx + BeautifulSoup
- All news sources fail → Return cached data if available

### Logging
```python
self.logger.error(
    "API call failed",
    extra={
        "integration": "serper",
        "endpoint": "/search",
        "error": str(e),
        "retry_count": retry_count,
        "company": company_name
    },
    exc_info=True
)
```

---

## Celery Tasks

### 1. `research_company_task`
```python
from celery import Task
from src.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3, time_limit=600)
async def research_company_task(
    self: Task,
    company_name: str,
    domain: str | None,
    linkedin_url: str | None,
    lead_id: str | None = None
) -> dict[str, Any]:
    """
    Background task to research a company.

    Time limit: 10 minutes
    Max retries: 3
    """
    agent = CompanyResearchAgent()

    task_payload = {
        "type": "research_company",
        "company_name": company_name,
        "domain": domain,
        "linkedin_url": linkedin_url,
        "lead_id": lead_id
    }

    try:
        result = await agent.process_task(task_payload)
        return result
    except Exception as e:
        agent.logger.error(f"Research failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

### 2. `refresh_stale_research_task`
```python
@celery_app.task(bind=True)
async def refresh_stale_research_task(self: Task, max_age_days: int = 30) -> dict:
    """
    Cron task to refresh stale company research.

    Runs daily at 2 AM.
    """
    from datetime import datetime, timedelta
    from src.database import get_db

    cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

    # Query stale research with high intent scores
    # Re-run research for active leads
    # Update database

    return {"refreshed_count": 0, "skipped_count": 0}
```

---

## Testing Requirements

### Unit Tests (>85% coverage)

**File:** `app/backend/__tests__/unit/agents/test_company_research.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.agents.company_research import CompanyResearchAgent

class TestCompanyResearchAgent:
    @pytest.fixture
    def agent(self):
        return CompanyResearchAgent()

    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "company_research"
        assert agent.description != ""
        assert len(agent.system_prompt) > 100

    @pytest.mark.asyncio
    async def test_search_company_news_success(self, agent):
        """Test news search with valid company."""
        with patch.object(agent.serper_client, 'search_news', new_callable=AsyncMock) as mock:
            mock.return_value = {
                "news": [{"title": "Test News", "url": "https://example.com"}]
            }

            result = await agent.search_company_news(
                company_name="Acme Corp",
                domain="acme.com"
            )

            assert "articles" in result
            assert result["total_found"] >= 0
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_company_news_rate_limit(self, agent):
        """Test news search handles rate limiting."""
        # Test rate limit error handling
        # Verify exponential backoff
        # Verify cache fallback
        pass

    @pytest.mark.asyncio
    async def test_scrape_linkedin_invalid_url(self, agent):
        """Test LinkedIn scrape with invalid URL."""
        result = await agent.scrape_linkedin_company(
            linkedin_url="invalid-url"
        )

        assert result.get("error") is not None
        assert result.get("company_info") is None

    @pytest.mark.asyncio
    async def test_identify_trigger_events_funding(self, agent):
        """Test trigger event identification for funding news."""
        company_data = {
            "news": {
                "articles": [{
                    "title": "Acme Corp raises $50M Series B",
                    "published_date": "2025-11-15T00:00:00Z",
                    "snippet": "Leading AI company secures funding"
                }]
            },
            "linkedin": {},
            "jobs": {"growth_signals": {}},
            "tech_stack": {},
            "website": {}
        }

        result = await agent.identify_trigger_events(company_data)

        assert len(result["trigger_events"]) > 0
        funding_event = next(
            (e for e in result["trigger_events"] if e["event_type"] == "funding"),
            None
        )
        assert funding_event is not None
        assert funding_event["priority"] in ["critical", "high"]

    @pytest.mark.asyncio
    async def test_generate_company_brief_complete(self, agent):
        """Test brief generation with complete data."""
        # Full research data fixture
        # Verify all sections present
        # Check confidence scores
        pass

    @pytest.mark.asyncio
    async def test_process_task_end_to_end(self, agent):
        """Test complete research workflow."""
        task = {
            "type": "research_company",
            "company_name": "Test Corp",
            "domain": "test.com",
            "linkedin_url": "https://linkedin.com/company/test-corp"
        }

        with patch.multiple(
            agent,
            search_company_news=AsyncMock(return_value={"articles": []}),
            scrape_linkedin_company=AsyncMock(return_value={"company_info": {}}),
            search_job_postings=AsyncMock(return_value={"jobs": []}),
            analyze_tech_stack=AsyncMock(return_value={"technologies": {}}),
            scrape_company_website=AsyncMock(return_value={"content": []})
        ):
            result = await agent.process_task(task)

            assert result["status"] == "completed"
            assert "research_id" in result
            assert "brief" in result
```

### Integration Tests

**File:** `app/backend/__tests__/integration/test_company_research_integration.py`

```python
import pytest
from src.agents.company_research import CompanyResearchAgent
from src.integrations.serper import SerperClient

class TestCompanyResearchIntegration:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_serper_api_real_request(self):
        """Test real Serper API request."""
        client = SerperClient(api_key=os.getenv("SERPER_API_KEY"))

        result = await client.search_news(
            query="Anthropic AI",
            num=5
        )

        assert "news" in result or "organic" in result
        await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_research_workflow_real_company(self):
        """Test full research on real company (cached)."""
        agent = CompanyResearchAgent()

        result = await agent.process_task({
            "type": "research_company",
            "company_name": "Anthropic",
            "domain": "anthropic.com",
            "linkedin_url": "https://www.linkedin.com/company/anthropic-ai"
        })

        assert result["status"] == "completed"
        assert len(result["brief"]["trigger_events"]) > 0
```

### Fixtures

**File:** `app/backend/__tests__/fixtures/company_research_fixtures.py`

```python
import pytest
from datetime import datetime, timedelta

@pytest.fixture
def mock_company_news():
    return {
        "articles": [
            {
                "title": "Company raises $100M Series C",
                "url": "https://techcrunch.com/...",
                "source": "TechCrunch",
                "published_date": (datetime.utcnow() - timedelta(days=10)).isoformat(),
                "snippet": "Leading AI company secures funding",
                "relevance_score": 0.95,
                "trigger_category": "funding"
            },
            {
                "title": "New CEO appointed",
                "url": "https://bloomberg.com/...",
                "source": "Bloomberg",
                "published_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                "snippet": "Former Google exec joins as CEO",
                "relevance_score": 0.88,
                "trigger_category": "leadership_change"
            }
        ],
        "total_found": 2,
        "sources_used": ["serper", "newsapi"],
        "cache_hit": False
    }

@pytest.fixture
def mock_linkedin_data():
    return {
        "company_info": {
            "name": "Acme Corporation",
            "follower_count": 125000,
            "employee_count_range": "501-1000",
            "industry": "Software Development",
            "headquarters": "San Francisco, CA",
            "specialties": ["AI", "Machine Learning", "SaaS"]
        },
        "recent_posts": [
            {
                "text": "Excited to announce our new AI platform!",
                "posted_date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "likes": 450,
                "comments": 32,
                "author": "Jane Smith, CEO",
                "is_executive": True
            }
        ],
        "scrape_timestamp": datetime.utcnow().isoformat()
    }

@pytest.fixture
def mock_job_postings():
    return {
        "jobs": [
            {
                "title": "Senior Machine Learning Engineer",
                "location": "San Francisco, CA",
                "posted_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "job_board": "linkedin",
                "seniority": "senior",
                "department": "engineering",
                "url": "https://linkedin.com/jobs/..."
            }
        ],
        "total_count": 15,
        "growth_signals": {
            "rapid_hiring": True,
            "new_departments": ["AI Research"],
            "executive_hires": 2,
            "technical_roles": 10,
            "sales_roles": 3
        },
        "analysis_timestamp": datetime.utcnow().isoformat()
    }
```

---

## Performance Requirements

- **Task Completion Time:** < 2 minutes (median), < 5 minutes (p95)
- **API Call Limits:**
  - Serper: 50/day (free tier), handle gracefully
  - News API: 100/day (free tier)
  - Apify: Based on credits
  - BuiltWith: Based on plan
- **Cache Hit Rate:** > 40% (reduce API costs)
- **Concurrent Research:** Support 5 simultaneous company researches
- **Database Growth:** ~500 KB per company research (compressed JSONB)

---

## Monitoring & Observability

### Metrics to Track
```python
# Prometheus metrics
research_duration_seconds = Histogram(
    "company_research_duration_seconds",
    "Time to complete company research",
    ["success"]
)

api_calls_total = Counter(
    "company_research_api_calls_total",
    "Total API calls by integration",
    ["integration", "endpoint", "status"]
)

trigger_events_detected = Counter(
    "trigger_events_detected_total",
    "Trigger events detected by type",
    ["event_type", "priority"]
)

cache_hits_total = Counter(
    "company_research_cache_hits_total",
    "Cache hits by data type",
    ["data_type"]
)
```

### Logging
- **INFO:** Research started, completed, trigger events found
- **WARNING:** Partial data, API fallbacks, low confidence results
- **ERROR:** API failures, parsing errors, database errors
- **DEBUG:** Individual tool calls, cache hits, data transformations

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Create `CompanyResearchAgent` class extending `BaseAgent`
- [ ] Implement system prompt and basic structure
- [ ] Create integration clients: `SerperClient`, `NewsAPIClient`
- [ ] Set up database schema (5 tables)
- [ ] Write unit tests for agent initialization

### Phase 2: Core Tools (Week 1-2)
- [ ] Implement `search_company_news` with Serper + News API
- [ ] Implement `scrape_linkedin_company` with Apify
- [ ] Implement `search_job_postings` with Apify
- [ ] Implement `analyze_tech_stack` with BuiltWith
- [ ] Implement `scrape_company_website` with Firecrawl
- [ ] Write unit tests for each tool (>85% coverage)

### Phase 3: Intelligence Layer (Week 2)
- [ ] Implement `identify_trigger_events` with Claude Opus 4.5
- [ ] Implement `generate_company_brief` with synthesis logic
- [ ] Add caching layer (Redis) for all API calls
- [ ] Implement retry logic and error handling
- [ ] Write integration tests with real APIs (cached)

### Phase 4: Database & Persistence (Week 2-3)
- [ ] Create Alembic migration for all 5 tables
- [ ] Implement database write operations in agent
- [ ] Add data expiration logic (30-day TTL)
- [ ] Test database operations (CRUD)
- [ ] Add database indexes for performance

### Phase 5: Celery Tasks (Week 3)
- [ ] Create `research_company_task` with time limits
- [ ] Create `refresh_stale_research_task` cron job
- [ ] Test task execution and retries
- [ ] Add task monitoring and logging
- [ ] Configure Celery beat schedule

### Phase 6: Testing & Quality (Week 3-4)
- [ ] Achieve >85% test coverage (unit + integration)
- [ ] Add fixtures for all data types
- [ ] Test error handling for all failure modes
- [ ] Performance testing (2-5 min completion time)
- [ ] Load testing (5 concurrent researches)

### Phase 7: Integration & Handoffs (Week 4)
- [ ] Test handoff from Lead List Builder Agent
- [ ] Test handoff to Campaign Personalization Agent
- [ ] Add API endpoints: `POST /api/research/company`
- [ ] Document API in OpenAPI spec
- [ ] End-to-end integration test

### Phase 8: Production Readiness (Week 4)
- [ ] Add Prometheus metrics
- [ ] Configure logging (structured JSON)
- [ ] Set up alerting for failures
- [ ] Create runbook for operations
- [ ] Documentation review and finalization

---

## API Endpoints

### `POST /api/research/company`

**Purpose:** Trigger company research (async via Celery)

**Request:**
```json
{
  "company_name": "Acme Corporation",
  "domain": "acme.com",
  "linkedin_url": "https://linkedin.com/company/acme",
  "lead_id": "uuid-here",
  "priority": "high"
}
```

**Response:**
```json
{
  "task_id": "celery-task-uuid",
  "status": "queued",
  "estimated_completion_seconds": 120
}
```

### `GET /api/research/company/{research_id}`

**Purpose:** Retrieve completed research

**Response:**
```json
{
  "data": {
    "research_id": "uuid",
    "company_name": "Acme Corporation",
    "brief": { ... },
    "trigger_events": [ ... ],
    "data_freshness": { ... },
    "generated_at": "2025-12-05T10:30:00Z"
  },
  "meta": {
    "cache_hit": false
  }
}
```

---

## Dependencies

**New Python Packages:**
```toml
# Add to pyproject.toml [project.dependencies]
tenacity = ">=9.0.0"          # Retry logic
beautifulsoup4 = ">=4.12.0"   # HTML parsing (fallback)
lxml = ">=5.0.0"              # Fast XML/HTML parsing
python-dateutil = ">=2.8.0"   # Date parsing
```

**Environment Variables:**
```bash
SERPER_API_KEY=...
NEWS_API_KEY=...
BUILTWITH_API_KEY=...  # Need to obtain
APIFY_API_KEY=...
FIRECRAWL_API_KEY=...
```

---

## Future Enhancements

### Phase 2 Features (Post-MVP)
- [ ] Sentiment analysis on news articles
- [ ] Glassdoor review scraping for culture insights
- [ ] GitHub activity tracking for tech companies
- [ ] Patent filing detection via USPTO API
- [ ] Social media monitoring (Twitter, Reddit)
- [ ] Podcast appearance tracking
- [ ] Conference speaking detection
- [ ] Press release prediction (using historical patterns)

### Phase 3 Features
- [ ] Real-time alerts for trigger events (webhook-based)
- [ ] Competitive intelligence dashboard
- [ ] Intent signal scoring across portfolio
- [ ] Automated research reports (weekly digests)
- [ ] ML model for trigger event prediction

---

## Success Metrics

**Operational:**
- [ ] >85% test coverage
- [ ] <5 minute p95 research completion time
- [ ] >95% API success rate (with retries)
- [ ] >40% cache hit rate

**Quality:**
- [ ] >80% trigger event accuracy (human validation)
- [ ] >0.7 average confidence score
- [ ] <5% false positive rate on critical triggers
- [ ] >90% data freshness (< 30 days old)

**Business Impact:**
- [ ] 3x increase in personalized outreach quality (sales team feedback)
- [ ] 50% reduction in manual research time
- [ ] 2x improvement in lead qualification accuracy

---

**Specification Status:** Ready for Implementation
**Estimated Effort:** 4 weeks (1 developer)
**Priority:** Phase 2 - Intelligence Layer
**Approval Required:** Technical Lead review

---

**Next Steps:**
1. Review specification with technical lead
2. Obtain BuiltWith API key (not yet in .env.example)
3. Create task file: `tasks/backend/pending/012-implement-company-research-agent.md`
4. Begin Phase 1 implementation
