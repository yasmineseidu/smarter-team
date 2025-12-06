# Technographic Data Agent - Production Specification

## Metadata

**Agent Name:** `technographic_data`
**Category:** Lead Generation & Data
**Priority:** Phase 6 - Multi-Channel & Advanced
**Dependencies:** Company Research Agent (provides company context)
**Coverage Target:** >85% (agent requirement)

---

## Purpose

Identify and analyze prospect technology stacks using multiple data sources to enable targeted sales outreach, competitive positioning, and personalization based on existing tech infrastructure.

---

## System Prompt

```
You are the Technographic Data Agent for Smarter Team, an autonomous AI agency.

Your primary responsibility is to identify, analyze, and maintain technology stack information for prospect companies. This intelligence enables targeted outreach, competitive positioning, and personalized engagement based on existing technology investments.

**Core Responsibilities:**
1. Query technology detection APIs (BuiltWith, Wappalyzer) for comprehensive tech stack analysis
2. Scrape and analyze company websites for direct technology evidence
3. Parse job postings for technology mentions and hiring trends
4. Maintain accurate, up-to-date technology stack records in the database
5. Generate and flag relevant technology signals (e.g., competitor tools, integration opportunities)
6. Cache results to optimize API usage and prevent redundant analysis
7. Track technology trends and changes over time

**Technology Categories to Detect:**
- CRM & Sales: Salesforce, HubSpot, Pipedrive, Zoho, etc.
- Marketing Automation: Marketo, Pardot, Mailchimp, Customer.io
- Website Platforms: WordPress, Shopify, Webflow, Squarespace, custom builds
- Analytics: Google Analytics, Adobe Analytics, Mixpanel, Amplitude
- Payment Processors: Stripe, Braintree, PayPal, Adyen, Square
- Communication: Slack, Microsoft Teams, Zoom, Intercom, Zendesk
- Development: React, Angular, Vue, Node.js, Python, Java, .NET
- Cloud & Infrastructure: AWS, Azure, GCP, Vercel, Netlify
- E-commerce: Magento, BigCommerce, WooCommerce, custom solutions

**Data Quality Standards:**
- Cross-reference findings across multiple sources for validation
- Assign confidence scores (0-100) for each detected technology
- Track detection source and timestamp for each technology entry
- Flag technologies detected via multiple sources as high confidence
- Refresh data quarterly or when significant changes detected

**Decision Framework:**
- High Confidence (≥80): Technology detected by 2+ sources or directly visible
- Medium Confidence (50-79): Technology detected by single reliable source
- Low Confidence (<50): Technology inferred from job postings or indirect evidence
- Stale Data (>90 days): Flag for refresh on next analysis

**API Rate Limit Management:**
- BuiltWith: 1,000 credits/month, track usage diligently
- Wappalyzer: Free tier 500 requests/month
- Implement caching with 7-day minimum for repeated lookups
- Batch requests where possible to maximize efficiency

**Signal Generation:**
Generate actionable signals when detecting:
- Competitor tools (e.g., using competing CRM)
- Integration opportunities (e.g., using compatible stack)
- Migration indicators (e.g., hiring for new technology)
- Technology gaps (e.g., missing analytics platform)
- Budget indicators (e.g., enterprise-grade tools)

**Handoff Protocol:**
When high-value signals are detected, hand off to appropriate agents:
- Lead List Builder: Update lead scoring based on tech stack
- Campaign Creation: Provide personalization data
- Sales Agents: Alert for competitive displacement opportunities

**Error Handling:**
- Gracefully handle API failures with fallback strategies
- Use website scraping when APIs are unavailable
- Log all failures for system health monitoring
- Implement exponential backoff for rate-limited requests

You work autonomously but log all decisions for data quality analytics and system optimization.
```

---

## Agent Implementation

### Class Definition

```python
from src.agents.base_agent import BaseAgent
from src.integrations.builtwith import BuiltWithClient
from src.integrations.wappalyzer import WappalyzerClient
from src.integrations.firecrawl import FirecrawlClient
from src.config import Settings, get_agent_logger
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

class ConfidenceLevel(Enum):
    HIGH = "high"      # ≥80 confidence
    MEDIUM = "medium"  # 50-79 confidence
    LOW = "low"        # <50 confidence

@dataclass
class TechnologyDetection:
    technology: str
    category: str
    confidence: int
    source: str
    detected_at: datetime
    url_evidence: Optional[str] = None
    job_posting_id: Optional[str] = None

class TechnographicDataAgent(BaseAgent):
    """
    Technographic Data Agent - Identifies and analyzes technology stacks.

    Uses multiple data sources to detect, validate, and maintain technology
    intelligence for prospect companies.
    """

    def __init__(self, settings: Settings):
        super().__init__(
            name="technographic_data",
            description="Analyzes company technology stacks using multiple data sources"
        )
        self.settings = settings
        self.builtwith = BuiltWithClient(api_key=settings.BUILTWITH_API_KEY)
        self.wappalyzer = WappalyzerClient(api_key=settings.WAPPALYZER_API_KEY)
        self.firecrawl = FirecrawlClient(api_key=settings.FIRECRAWL_API_KEY)

        # Rate limit tracking
        self.builtwith_credits_used = 0
        self.wappalyzer_requests_used = 0
        self.monthly_reset_day = 1  # Reset counters on first day of month

    @property
    def system_prompt(self) -> str:
        return """[See System Prompt section above]"""

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Process technographic analysis task."""
        task_type = task.get("type")

        if task_type == "analyze_company":
            return await self._analyze_company(task)
        elif task_type == "refresh_tech_stack":
            return await self._refresh_tech_stack(task)
        elif task_type == "batch_analyze":
            return await self._batch_analyze(task)
        elif task_type == "detect_signals":
            return await self._detect_signals(task)
        elif task_type == "update_usage_stats":
            return await self._update_usage_stats()
        else:
            raise ValueError(f"Unknown task type: {task_type}")
```

---

## Tools

### 1. `query_builtwith_api`

**Purpose:** Query BuiltWith API for comprehensive technology analysis

**Parameters:**
```python
{
    "domain": str,                    # Company domain to analyze
    "lookup_type": str = "standard",  # "standard" or "premium" lookup
    "include_metadata": bool = True   # Include technology metadata
}
```

**Returns:**
```python
{
    "technologies": List[TechnologyDetection],
    "api_credits_used": int,
    "total_available": int,
    "technologies_by_category": Dict[str, List[TechnologyDetection]],
    "domain_info": {
        "rank": Optional[int],
        "first_detected": Optional[datetime],
        "last_updated": datetime
    }
}
```

**Error Handling:**
- Rate limit (429): Implement exponential backoff, max 5 retries
- Invalid domain: Return error with specific validation message
- API error: Log and fallback to other detection methods
- Credits exhausted: Mark for next monthly reset

### 2. `query_wappalyzer_api`

**Purpose:** Query Wappalyzer API for quick technology detection

**Parameters:**
```python
{
    "urls": List[str],               # URLs to analyze (max 10 per request)
    "include_subdomains": bool = False
}
```

**Returns:**
```python
{
    "results": Dict[str, List[TechnologyDetection]],
    "requests_used": int,
    "total_available": int,
    "failed_urls": List[str]
}
```

**Error Handling:**
- Rate limit: Exponential backoff, check free tier limits
- Invalid URLs: Filter and continue with valid URLs
- Timeout: Retry once with longer timeout
- Parsing errors: Log and continue

### 3. `scrape_website_tech`

**Purpose:** Directly scrape website for technology evidence

**Parameters:**
```python
{
    "url": str,
    "analyze_js": bool = True,
    "analyze_headers": bool = True,
    "analyze_source": bool = True
}
```

**Returns:**
```python
{
    "technologies": List[TechnologyDetection],
    "evidence": Dict[str, List[str]],  # Evidence for each detection
    "scripts_found": List[str],
    "meta_tags": Dict[str, str],
    "headers": Dict[str, str],
    "scrape_success": bool
}
```

**Error Handling:**
- Blocked by robots.txt: Respect and log blocking
- JavaScript-heavy sites: Note limitation, rely on headers/meta
- Network timeout: Retry with different approach
- SSL errors: Log and mark as inaccessible

### 4. `analyze_job_postings`

**Purpose:** Extract technology mentions from job postings

**Parameters:**
```python
{
    "company_id": UUID,
    "keywords": List[str] = ["engineer", "developer", "technical"],  # Job titles to search
    "days_back": int = 30,           # How many days back to search
    "min_mentions": int = 2          # Minimum mentions to count as evidence
}
```

**Returns:**
```python
{
    "technologies": List[TechnologyDetection],
    "postings_analyzed": int,
    "technology_mentions": Dict[str, int],
    "hiring_trends": Dict[str, str],  # "expanding", "maintaining", "declining"
    "confidence_adjustments": Dict[str, int]
}
```

**Error Handling:**
- Job board API limits: Implement rate limiting across all boards
- No job postings found: Return empty results, log for analytics
- Parsing errors: Continue with successfully parsed postings
- Duplicate postings: Deduplicate based on content hash

### 5. `update_company_tech_stack`

**Purpose:** Update database with new technology detections

**Parameters:**
```python
{
    "company_id": UUID,
    "technologies": List[TechnologyDetection],
    "merge_strategy": str = "merge",  # "merge", "replace", "append"
    "confidence_threshold": int = 50
}
```

**Returns:**
```python
{
    "updated_count": int,
    "new_technologies": int,
    "updated_technologies": int,
    "removed_technologies": int,     # If merge_strategy is "replace"
    "tech_stack_id": UUID,
    "last_updated": datetime
}
```

**Error Handling:**
- Database constraint violations: Log and continue with valid records
- Invalid confidence values: Use default threshold
- Missing company: Create new tech stack record
- Concurrent updates: Use optimistic locking with retry

### 6. `generate_tech_signals`

**Purpose:** Generate actionable signals from technology analysis

**Parameters:**
```python
{
    "company_id": UUID,
    "tech_stack": List[TechnologyDetection],
    "analysis_type": str = "all"      # "competitive", "integration", "gap"
}
```

**Returns:**
```python
{
    "signals": List[Dict[str, Any]],
    "competitive_signals": List[Dict],  # Using competitor tools
    "integration_opportunities": List[Dict],  # Compatible tech
    "technology_gaps": List[Dict],     # Missing categories
    "priority_score": int,            # 0-100 based on signal quality
    "recommendations": List[str]
}
```

**Signal Types:**
- **Competitive**: Using competitor's tool
- **Integration Opportunity**: Using compatible technology
- **Migration Signal**: Hiring for new technology
- **Gap Analysis**: Missing technology in key category
- **Budget Indicator**: Enterprise-level tools detected

---

## Database Schema

### Table: `company_tech_stack`

```sql
CREATE TABLE company_tech_stack (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    technology VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    source VARCHAR(50) NOT NULL,  -- 'builtwith', 'wappalyzer', 'scrape', 'jobs'
    url_evidence TEXT,
    job_posting_id UUID REFERENCES job_postings(id),
    first_detected TIMESTAMP WITH TIME ZONE NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    UNIQUE(company_id, technology, source)
);

CREATE INDEX idx_tech_stack_company ON company_tech_stack(company_id);
CREATE INDEX idx_tech_stack_technology ON company_tech_stack(technology);
CREATE INDEX idx_tech_stack_category ON company_tech_stack(category);
CREATE INDEX idx_tech_stack_confidence ON company_tech_stack(confidence);
CREATE INDEX idx_tech_stack_updated ON company_tech_stack(last_updated);
```

### Table: `tech_signals`

```sql
CREATE TABLE tech_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    signal_type VARCHAR(50) NOT NULL,  -- 'competitive', 'integration', 'gap', 'migration'
    technology VARCHAR(255),
    description TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK (priority >= 0 AND priority <= 100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by UUID REFERENCES users(id)
);

CREATE INDEX idx_tech_signals_company ON tech_signals(company_id);
CREATE INDEX idx_tech_signals_type ON tech_signals(signal_type);
CREATE INDEX idx_tech_signals_priority ON tech_signals(priority);
CREATE INDEX idx_tech_signals_unacknowledged ON tech_signals(acknowledged_at) WHERE acknowledged_at IS NULL;
```

---

## Error Handling Matrix

| Component | Error Type | Detection | Response | Retry |
|-----------|------------|-----------|----------|-------|
| BuiltWith API | Rate Limit (429) | Response status | Exponential backoff (max 5) | Yes |
| BuiltWith API | Credits Exhausted | Response message | Log, wait for monthly reset | No |
| Wappalyzer API | Rate Limit | Response status | Exponential backoff (max 3) | Yes |
| Website Scrape | Blocked (403) | Response status | Log, continue with other sources | No |
| Website Scrape | Timeout | Exception | Retry once with 60s timeout | Yes |
| Website Scrape | SSL Error | Exception | Log as inaccessible | No |
| Job Board API | Rate Limit | Response status | Implement request throttling | Yes |
| Database | Connection Error | Exception | Retry 3x with backoff | Yes |
| Database | Constraint Violation | Exception | Log and skip record | No |
| JSON Parsing | Invalid Response | Validation error | Log, continue with valid data | No |

---

## Multi-Agent Integration

### Handoffs FROM this Agent:

1. **To Lead List Builder:**
   - Trigger: New technology stack analysis complete
   - Payload: Company ID, tech stack summary, personalization data
   - Purpose: Update lead scoring based on technology compatibility

2. **To Campaign Creation:**
   - Trigger: High-value competitive signals detected
   - Payload: Company ID, competitive opportunities, talking points
   - Purpose: Enable targeted competitive messaging

3. **To Sales Agents:**
   - Trigger: Migration indicators or integration opportunities
   - Payload: Company ID, specific opportunities, contact timing
   - Priority: High (time-sensitive opportunities)

### Handoffs TO this Agent:

1. **From Company Research Agent:**
   - Trigger: New company profile created
   - Payload: Company ID, domain, company size, industry
   - Purpose: Initial technology stack analysis

2. **From Lead List Builder:**
   - Trigger: Batch of new leads ready for enrichment
   - Payload: List of company IDs and domains
   - Purpose: Bulk technology analysis

---

## Testing Strategy

### Unit Tests

```python
# Test file: app/backend/__tests__/unit/agents/test_technographic_data.py

def test_query_builtwith_success():
    """Test successful BuiltWith API query"""

def test_query_builtwith_rate_limit():
    """Test rate limit handling with exponential backoff"""

def test_scrape_website_technologies():
    """Test website scraping for technology detection"""

def test_analyze_job_postings_tech_mentions():
    """Test job posting analysis for technology keywords"""

def test_update_tech_stack_merge():
    """Test database update with merge strategy"""

def test_generate_competitive_signals():
    """Test competitive signal generation"""

def test_confidence_scoring():
    """Test confidence score calculation across sources"""

def test_cache_hit_prevents_api_call():
    """Test that cached results prevent redundant API calls"""
```

### Integration Tests

```python
# Test file: app/backend/__tests__/integration/test_technographic_data_integration.py

def test_end_to_end_company_analysis():
    """Test complete flow from company domain to tech stack"""

def test_multi_source_validation():
    """Test cross-validation across BuiltWith, Wappalyzer, and scraping"""

def test_handoff_to_campaign_creation():
    """Test handoff protocol to Campaign Creation agent"""

def test_batch_processing_performance():
    """Test batch analysis of 100 companies"""

def test_rate_limit_across_apis():
    """Test coordinated rate limiting across all APIs"""
```

### Mock Strategy

```python
@pytest.fixture
def mock_builtwith_client():
    with patch('src.integrations.builtwith.BuiltWithClient') as mock:
        mock.return_value.lookup_domain.return_value = {
            "technologies": [
                {"name": "Google Analytics", "category": "Analytics", "confidence": 90}
            ],
            "credits_used": 10
        }
        yield mock

@pytest.fixture
def mock_wappalyzer_client():
    with patch('src.integrations.wappalyzer.WappalyzerClient') as mock:
        mock.return_value.analyze_urls.return_value = {
            "results": {
                "example.com": [
                    {"name": "React", "category": "JavaScript Framework", "confidence": 85}
                ]
            }
        }
        yield mock

@pytest.fixture
def mock_firecrawl_client():
    with patch('src.integrations.firecrawl.FirecrawlClient') as mock:
        mock.return_value.scrape_url.return_value = {
            "content": "<html>...</html>",
            "metadata": {"title": "Example Site"}
        }
        yield mock
```

---

## Performance

### Expected Latency
- Single company analysis: 2-5 seconds (with cache)
- Batch analysis (100 companies): 2-5 minutes
- API-only lookup: 500ms-1s
- Full analysis with scraping: 3-7s

### Token Usage
- System prompt: ~3,000 tokens
- Analysis context: 500-2,000 tokens per company
- Signal generation: 200-500 tokens

### Caching Strategy
- BuiltWith results: 7 days (per domain)
- Wappalyzer results: 7 days (per URL)
- Website scrape: 3 days (per URL)
- Technology signals: 24 hours (per company)
- Job posting analysis: 30 days (per company)

---

## Observability

### Logging
```python
# Structured logging examples
self.logger.info(
    "Technology analysis complete",
    extra={
        "company_id": company_id,
        "domain": domain,
        "technologies_found": len(technologies),
        "api_credits_used": credits,
        "processing_time_ms": processing_time,
        "sources_used": sources
    }
)

self.logger.warning(
    "Rate limit approaching",
    extra={
        "api": "builtwith",
        "credits_used": self.builtwith_credits_used,
        "credits_total": 1000,
        "percentage_used": percentage
    }
)
```

### Metrics to Track
- API usage by service (BuiltWith, Wappalyzer, Firecrawl)
- Cache hit/miss ratios
- Detection accuracy (when validated)
- Processing time per company
- Signal generation rate
- Error rates by type

### Health Checks
- API key validity check
- Rate limit status
- Database connectivity
- Cache backend health
- Background job queue status

---

## Security

### API Key Handling
- All API keys stored in environment variables
- API keys logged at debug level only
- Rate limit tracking to prevent abuse
- Request signing for BuiltWith where applicable

### Data Sanitization
- Sanitize scraped HTML before processing
- Validate all domains before API calls
- Escape special characters in database queries
- Redact sensitive information from logs

### Permissions
- Read access to company and lead tables
- Write access to tech_stack and signals tables
- No access to financial or PII data
- Network access limited to required domains

---

## Acceptance Criteria

- [ ] Successfully detects technologies from BuiltWith API with 95% accuracy
- [ ] Cross-validates findings across multiple sources
- [ ] Maintains technology stack database with confidence scores
- [ ] Generates actionable competitive signals
- [ ] Operates within API rate limits (BuiltWith: 1,000/month, Wappalyzer: 500/month)
- [ ] Caches results to minimize redundant API calls
- [ ] Handles API failures gracefully with fallback strategies
- [ ] Updates technology data quarterly or on significant changes
- [ ] Provides handoff data to Lead List Builder and Campaign agents
- [ ] Processes batch analysis of 100+ companies efficiently
- [ ] Passes all unit and integration tests with >85% coverage
- [ ] Logs all decisions for audit trail and optimization
