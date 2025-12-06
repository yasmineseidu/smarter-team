# Progressive Enrichment Agent - Production Specification

## Metadata

**Agent Name:** `progressive_enrichment`
**Category:** Lead Generation & Data
**Priority:** Phase 6 - Multi-Channel & Advanced
**Dependencies:**
- Lead List Builder Agent (provides leads)
- Email Verification Agent (provides engagement context)
- Waterfall Enrichment Agent (for fallback data sources)
**Coverage Target:** >85% (agent requirement)

---

## Purpose

Fill data gaps in lead records progressively over time using multiple data enrichment APIs. Prioritizes engaged leads and high-value accounts while tracking enrichment costs to ensure positive ROI. Operates autonomously to maintain high-quality lead data for marketing campaigns.

---

## System Prompt

```
You are the Progressive Enrichment Agent for Smarter Team, an autonomous AI agency.

Your primary responsibility is to progressively enrich lead data over time, focusing on filling critical information gaps that improve campaign performance and sales effectiveness. You operate autonomously, making intelligent decisions about which leads to enrich and when.

**Core Responsibilities:**
1. Identify leads with missing or outdated data fields
2. Prioritize enrichment based on engagement level, account value, and cost-benefit analysis
3. Enrich data using multiple APIs (people data, company data, technographic, firmographic)
4. Track enrichment costs per lead and maintain budget constraints
5. Update records with new information while preserving existing valid data
6. Manage rate limits across multiple enrichment services
7. Log all enrichment activities for audit and optimization

**Enrichment Priority Framework:**
- Tier 1 (Immediate): Recently engaged leads (clicked, replied, opened) with critical gaps
- Tier 2 (High): High-value target accounts with decision-maker contacts
- Tier 3 (Normal): Cold leads with enrichment potential
- Tier 4 (Low): Leads with basic data sufficient for current campaigns

**Data Fields to Enrich (in priority order):**
1. Phone number - Critical for sales outreach
2. LinkedIn URL - Essential for social selling and research
3. Company size - Determines pricing and approach strategy
4. Industry - Vertical-specific messaging
5. Revenue range - Account prioritization
6. Tech stack - Personalization and competitive analysis
7. Recent news - Conversation starters and timing

**Cost Management:**
- Monthly enrichment budget: $500
- Cost per lead threshold: $2.50
- ROI threshold: 5x enrichment cost (estimated campaign value)
- Track cumulative spend and alert at 80% budget usage

**Quality Standards:**
- Verify new data against existing records
- Flag conflicting data for human review
- Update confidence scores for enriched fields
- Maintain data source attribution
- Respect API rate limits and implement backoff

**Error Handling:**
- Graceful degradation when APIs are unavailable
- Fallback to alternative enrichment sources
- Skip leads with insufficient identifiers
- Log all failures with context for debugging

**Handoff Protocol:**
When enrichment fails or requires human review, hand off to the Waterfall Enrichment Agent with:
- Lead ID and available identifiers
- Missing fields list
- Enrichment attempts made
- Cost constraints
- Priority tier

You work autonomously but ensure cost-effectiveness and data quality in every enrichment decision.
```

---

## Agent Implementation

### Class Definition

```python
from src.agents.base_agent import BaseAgent
from src.integrations.apify import ApifyClient
from src.integrations.serper import SerperClient
from src.integrations.icypeas import IcypeasClient
from src.config import Settings, get_agent_logger
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from enum import Enum

class EnrichmentTier(str, Enum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class EnrichmentField(str, Enum):
    PHONE = "phone"
    LINKEDIN = "linkedin_url"
    COMPANY_SIZE = "company_size"
    INDUSTRY = "industry"
    REVENUE = "revenue_range"
    TECH_STACK = "tech_stack"
    RECENT_NEWS = "recent_news"

class ProgressiveEnrichmentAgent(BaseAgent):
    """
    Progressive Enrichment Agent - Fills data gaps over time using multiple APIs.

    Prioritizes engaged leads, manages costs, and tracks enrichment ROI.
    """

    def __init__(self, settings: Settings):
        super().__init__(
            name="progressive_enrichment",
            description="Progressively enriches lead data using multiple APIs while managing costs"
        )
        self.settings = settings
        self.apify = ApifyClient(api_key=settings.APIFY_API_KEY)
        self.serper = SerperClient(api_key=settings.SERPER_API_KEY)
        self.icypeas = IcypeasClient(api_key=settings.ICYPEAS_API_KEY)

        # Cost management
        self.monthly_budget = 500.0
        self.cost_per_lead_threshold = 2.5
        self.current_month_spend = 0.0

        # Rate limiting
        self.rate_limits = {
            "apify": {"requests_per_second": 10, "current": 0},
            "serper": {"requests_per_second": 100, "current": 0},
            "icypeas": {"requests_per_second": 5, "current": 0}
        }

    @property
    def system_prompt(self) -> str:
        return """[See System Prompt section above]"""

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Process progressive enrichment task."""
        task_type = task.get("type")

        if task_type == "enrich_batch":
            return await self._enrich_batch(task)
        elif task_type == "enrich_lead":
            return await self._enrich_single_lead(task)
        elif task_type == "check_budget":
            return await self._check_budget_status()
        elif task_type == "prioritize_leads":
            return await self._prioritize_leads(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
```

---

## Tools

### 1. `identify_enrichment_candidates`

**Purpose:** Identify leads requiring enrichment based on data gaps and engagement

**Parameters:**
```python
{
    "campaign_id": Optional[UUID],     # Filter by campaign
    "engagement_min_hours": int = 24,  # Minimum hours since last engagement
    "missing_fields": List[str],       # Fields to check (optional, defaults to all)
    "limit": int = 100,                # Maximum leads to return
    "tier_filter": Optional[str]       # Filter by priority tier
}
```

**Returns:**
```python
{
    "candidates": List[Dict],          # Lead data with missing fields
    "tier_counts": Dict[str, int],     # Count per priority tier
    "estimated_cost": float,           # Total estimated enrichment cost
    "budget_remaining": float,         # Remaining budget for the month
    "recommendation": str              # Action recommendation
}
```

**Implementation:**
```python
async def identify_enrichment_candidates(
    self,
    campaign_id: Optional[UUID] = None,
    engagement_min_hours: int = 24,
    missing_fields: Optional[List[str]] = None,
    limit: int = 100,
    tier_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Identify leads that need data enrichment.

    Prioritizes based on engagement, account value, and data gaps.
    Returns leads grouped by enrichment priority tier.
    """
```

### 2. `enrich_lead_profile`

**Purpose:** Enrich a single lead with missing data using multiple APIs

**Parameters:**
```python
{
    "lead_id": UUID,                   # Lead identifier
    "fields_to_enrich": List[str],     # Specific fields to focus on
    "max_cost_per_lead": float = 2.5,  # Maximum spend for this lead
    "skip_existing": bool = True,      # Skip fields that already have data
    "sources": List[str] = ["apify", "serper", "icypeas"]  # Data sources to use
}
```

**Returns:**
```python
{
    "lead_id": UUID,
    "enriched_fields": Dict[str, Any], # New data found
    "field_confidence": Dict[str, float], # Confidence scores (0-1)
    "sources_used": List[str],         # Which APIs provided data
    "cost_incurred": float,            # Actual cost for this enrichment
    "errors": List[Dict],              # Any errors encountered
    "recommendations": List[str]       # Follow-up actions
}
```

**Implementation:**
```python
async def enrich_lead_profile(
    self,
    lead_id: UUID,
    fields_to_enrich: List[str],
    max_cost_per_lead: float = 2.5,
    skip_existing: bool = True,
    sources: List[str] = ["apify", "serper", "icypeas"]
) -> Dict[str, Any]:
    """
    Enrich a single lead's profile using multiple data sources.

    Attempts to fill specified fields within cost constraints.
    Returns new data with confidence scores and source attribution.
    """
```

### 3. `enrich_company_data`

**Purpose:** Enrich company-level information (size, revenue, industry, tech stack)

**Parameters:**
```python
{
    "company_domain": str,             # Company website
    "company_name": str,               # Company name
    "fields": List[str],               # Company fields to find
    "include_technology": bool = True, # Include tech stack lookup
    "max_cost": float = 1.0           # Maximum spend for company data
}
```

**Returns:**
```python
{
    "company_data": Dict[str, Any],    # Company information found
    "technologies": List[Dict],        # Technology stack if requested
    "confidence_scores": Dict[str, float],
    "sources": List[str],              # Data sources used
    "cost": float,                     # API credits consumed
    "completeness": float              # Percentage of requested fields found
}
```

**Implementation:**
```python
async def enrich_company_data(
    self,
    company_domain: str,
    company_name: str,
    fields: List[str],
    include_technology: bool = True,
    max_cost: float = 1.0
) -> Dict[str, Any]:
    """
    Enrich company-level data using multiple sources.

    Combines data from company APIs and technology detection services.
    Provides confidence scores for each field.
    """
```

### 4. `find_contact_information`

**Purpose:** Find additional contact methods (phone, LinkedIn, social profiles)

**Parameters:**
```python
{
    "email": str,                      # Known email address
    "full_name": str,                  # Contact's full name
    "company": str,                    # Company name
    "search_depth": str = "standard",  # "basic", "standard", "deep"
    "include_social": bool = True      # Include social media profiles
}
```

**Returns:**
```python
{
    "phone": Optional[str],            # Phone number found
    "linkedin_url": Optional[str],     # LinkedIn profile
    "social_profiles": Dict[str, str], # Other social media
    "confidence": float,               # Overall confidence in matches
    "sources": List[str],              # Sources that provided matches
    "verification_status": str,        # "verified", "likely", "possible"
    "cost": float                      # API credits consumed
}
```

**Implementation:**
```python
async def find_contact_information(
    self,
    email: str,
    full_name: str,
    company: str,
    search_depth: str = "standard",
    include_social: bool = True
) -> Dict[str, Any]:
    """
    Find additional contact information for a lead.

    Searches multiple people data APIs to find phone numbers,
    LinkedIn profiles, and social media accounts.
    """
```

### 5. `get_recent_news_signals`

**Purpose:** Find recent news and signals about the company or contact

**Parameters:**
```python
{
    "company_name": str,               # Company to search for
    "contact_name": Optional[str],     # Specific contact (optional)
    "days_back": int = 30,             # How many days to look back
    "news_types": List[str] = ["funding", "hiring", "launch", "award"],
    "max_results": int = 10            # Maximum news items to return
}
```

**Returns:**
```python
{
    "news_items": List[Dict],          # News articles and signals
    "signal_strength": float,          # Overall signal strength (0-1)
    "conversation_starters": List[str], # Suggested conversation topics
    "timing_recommendations": List[str], # Best times to reach out
    "sources": List[str],              # News sources found
    "cost": float                      # Search cost in credits
}
```

**Implementation:**
```python
async def get_recent_news_signals(
    self,
    company_name: str,
    contact_name: Optional[str] = None,
    days_back: int = 30,
    news_types: List[str] = ["funding", "hiring", "launch", "award"],
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Find recent news and signals for timely outreach.

    Searches news APIs and company announcements to find
    conversation starters and optimal timing.
    """
```

### 6. `calculate_enrichment_roi`

**Purpose:** Calculate ROI and prioritize enrichment efforts

**Parameters:**
```python
{
    "lead_id": UUID,                   # Lead to analyze
    "fields_needed": List[str],        # Fields that would add value
    "estimated_campaign_value": float, # Potential value if enriched
    "enrichment_cost": float          # Cost to enrich this lead
}
```

**Returns:**
```python
{
    "roi_score": float,                # ROI multiplier (enrichment value / cost)
    "recommendation": str,             # "enrich", "skip", "partial_enrich"
    "priority_fields": List[str],      # Fields with highest ROI
    "estimated_lift": float,           # Expected campaign improvement
    "confidence": float,               # Confidence in ROI calculation
    "budget_impact": Dict[str, Any]    # Impact on monthly budget
}
```

**Implementation:**
```python
async def calculate_enrichment_roi(
    self,
    lead_id: UUID,
    fields_needed: List[str],
    estimated_campaign_value: float,
    enrichment_cost: float
) -> Dict[str, Any]:
    """
    Calculate ROI for lead enrichment.

    Uses historical data to estimate campaign improvement
    from enriched fields and recommends actions.
    """
```

---

## Error Handling

### API Errors
| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Rate limit (429) | Status code or header | Exponential backoff, try alternative source | Yes, 3 attempts |
| Insufficient credits | API response | Skip to next source, log budget warning | No |
| No results found | Empty response | Try alternative search terms | Yes, 1 attempt |
| Invalid format | Response validation | Log error, skip to next source | No |
| Timeout | Exception | Retry with longer timeout | Yes, 2 attempts |
| Authentication error | Status 401/403 | Fail immediately, alert ops | No |

### Recovery Strategies
1. **Source Fallback:** If Apify fails, try Icypeas, then Serper
2. **Partial Enrichment:** Return whatever data was successfully found
3. **Budget Management:** Skip enrichment if remaining budget < cost threshold
4. **Queue Management:** Re-queue failed enrichments for later retry
5. **Graceful Degradation:** Continue with available data if enrichment fails

### Error Metrics to Track
- API failure rate per service
- Enrichment success rate by field type
- Cost per successful enrichment
- Average attempts per successful enrichment
- Budget utilization efficiency

---

## Multi-Agent Integration

### Handoffs FROM this Agent:
- **Waterfall Enrichment Agent**: When primary APIs fail or require alternative sources
  - Payload: lead_id, missing_fields, attempts_made, cost_remaining
  - Priority: Based on lead's tier
- **Campaign Personalization Agent**: When significant new data is found
  - Payload: lead_id, enriched_fields, personalization_opportunities
  - Priority: High for engaged leads

### Handoffs TO this Agent:
- **Email Verification Agent**: Provides verified emails and engagement data
  - Trigger: New leads verified or engagement detected
  - Payload: lead_ids, engagement_scores, verification_results
- **Lead List Builder Agent**: Provides new leads requiring initial enrichment
  - Trigger: New lead lists generated
  - Payload: campaign_id, lead_ids, data_sources_used

### Coordination Patterns:
1. **Batch Processing**: Process leads in batches to optimize API usage
2. **Priority Queue**: Use Celery priorities for urgent enrichments
3. **State Sharing**: Store enrichment progress in database for coordination
4. **Event Triggers**: Enrich on engagement events (email open, click, reply)

---

## Testing Strategy

### Unit Tests
```python
class TestProgressiveEnrichmentAgent:
    @pytest.mark.asyncio
    async def test_identify_enrichment_candidates(self):
        """Test lead prioritization and gap analysis"""

    @pytest.mark.asyncio
    async def test_enrich_lead_profile_success(self):
        """Test successful enrichment with mock APIs"""

    @pytest.mark.asyncio
    async def test_enrich_lead_handles_rate_limit(self):
        """Test rate limit handling and fallback"""

    @pytest.mark.asyncio
    async def test_calculate_roi_accuracy(self):
        """Test ROI calculation with historical data"""

    def test_budget_management(self):
        """Test budget tracking and limits"""

    @pytest.mark.asyncio
    async def test_enrichment_priority_tiers(self):
        """Test correct tier assignment"""
```

### Integration Tests
```python
class TestEnrichmentIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_enrichment_flow(self):
        """Test complete enrichment with mocked external APIs"""

    @pytest.mark.asyncio
    async def test_multi_source_data_merging(self):
        """Test combining data from multiple APIs"""

    @pytest.mark.asyncio
    async def test_agent_handoff_workflow(self):
        """Test handoff to Waterfall Enrichment Agent"""

    @pytest.mark.asyncio
    async def test_campaign_integration(self):
        """Test integration with campaign workflows"""
```

### Mocking Strategy
```python
@pytest.fixture
def mock_enrichment_apis():
    """Mock all enrichment API clients"""
    with patch('src.integrations.apify.ApifyClient') as apify, \
         patch('src.integrations.serper.SerperClient') as serper, \
         patch('src.integrations.icypeas.IcypeasClient') as icypeas:
        # Configure mock responses
        yield apify, serper, icypeas

@pytest.fixture
def sample_lead_data():
    """Sample lead record for testing"""
    return {
        "id": uuid4(),
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "TechCorp",
        "phone": None,
        "linkedin_url": None,
        "company_size": None,
        "industry": None
    }
```

---

## Performance

### Expected Performance
- **Throughput**: 50 leads/hour (average 5 fields per lead)
- **Latency**: 2-5 seconds per field (depending on source)
- **Cost**: $0.10-0.50 per field (varies by data source)
- **Success Rate**: 65-80% (depends on data availability)
- **Cache Hit Rate**: 30% (for repeat lookups)

### Caching Strategy
- **Redis Cache**: Cache results for 7 days
- **Cache Keys**: enrichment:{source}:{field}:{identifier}
- **Cache Invalidation**: Manual invalidation for data updates
- **Fallback Cache**: Local cache for API outages

### Rate Limiting
- **Apify**: 10 requests/second, 1000/hour
- **Serper**: 100 requests/second, 10,000/hour
- **Icypeas**: 5 requests/second, 500/hour
- **Backoff Strategy**: Exponential with jitter (1s, 2s, 4s, 8s)

---

## Observability

### Logging Requirements
```python
# Structured logging examples
logger.info(
    "Enrichment started",
    extra={
        "lead_id": str(lead_id),
        "fields_requested": fields,
        "tier": tier.value,
        "estimated_cost": cost
    }
)

logger.info(
    "API call made",
    extra={
        "source": "apify",
        "endpoint": "person-enrichment",
        "cost": 0.25,
        "response_time_ms": 1200
    }
)

logger.warning(
    "Rate limit hit",
    extra={
        "source": "icypeas",
        "retry_after": 60,
        "queue_size": 150
    }
)
```

### Metrics to Track
1. **Enrichment Metrics**
   - Enrichment success rate by field
   - Cost per successful enrichment
   - Average fields enriched per lead
   - Time to enrich batch

2. **API Metrics**
   - API response times by service
   - Rate limit hit frequency
   - API error rates
   - Credit consumption

3. **Business Metrics**
   - Enriched lead conversion rate
   - ROI on enrichment spend
   - Campaign improvement from enriched data
   - Budget utilization

### Dashboards
- **Real-time**: Current enrichment queue, API status, budget remaining
- **Daily**: Enrichment success rates, cost breakdown, field coverage
- **Weekly**: ROI trends, source performance, quality metrics

---

## Security

### API Key Management
- Store API keys in environment variables
- Rotate keys quarterly
- Monitor API key usage for anomalies
- Use separate keys for development/staging

### Data Privacy
- Do not store PII in logs
- Encrypt sensitive data at rest
- Respect data processing agreements
- Implement data retention policies

### Input Validation
```python
from pydantic import BaseModel, validator

class EnrichmentRequest(BaseModel):
    lead_id: UUID
    fields: List[str]
    max_cost: float

    @validator('fields')
    def validate_fields(cls, v):
        allowed_fields = [field.value for field in EnrichmentField]
        for field in v:
            if field not in allowed_fields:
                raise ValueError(f"Invalid field: {field}")
        return v

    @validator('max_cost')
    def validate_cost(cls, v):
        if v < 0 or v > 10.0:
            raise ValueError("Cost must be between 0 and 10")
        return v
```

---

## Acceptance Criteria

- [ ] Agent can identify leads requiring enrichment based on data gaps
- [ ] Prioritization logic correctly tiers leads by engagement and value
- [ ] Successfully enriches at least 65% of targeted fields across all leads
- [ ] Maintains enrichment costs below $2.50 per lead on average
- [ ] Respects API rate limits for all integrated services
- [ ] Handles API failures gracefully with fallback strategies
- [ ] Tracks enrichment costs and stays within monthly budget
- [ ] Logs all enrichment activities for audit and optimization
- [ ] Handoffs failed enrichments to Waterfall Enrichment Agent
- [ ] Updates lead records with confidence scores and source attribution
- [ ] Provides ROI calculations for enrichment decisions
- [ ] All unit and integration tests pass with >85% coverage
- [ ] Performance meets or exceeds stated targets
- [ ] Security requirements are fully implemented

---

## Implementation Dependencies

### Required Integrations
1. **Apify** (`APIFY_API_KEY`) - People and company data enrichment
2. **Serper** (`SERPER_API_KEY`) - Company research and news
3. **Icypeas** (`ICYPEAS_API_KEY`) - Email to social profile lookup

### Database Tables
```sql
-- Track enrichment queue and status
CREATE TABLE enrichment_queue (
    id UUID PRIMARY KEY,
    lead_id UUID NOT NULL REFERENCES leads(id),
    fields_needed TEXT[],
    tier VARCHAR(20) NOT NULL,
    priority INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    scheduled_at TIMESTAMP DEFAULT NOW()
);

-- Track enrichment history and costs
CREATE TABLE enrichment_history (
    id UUID PRIMARY KEY,
    lead_id UUID NOT NULL REFERENCES leads(id),
    field_name VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    source VARCHAR(50) NOT NULL,
    confidence FLOAT,
    cost DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Track monthly budget and spend
CREATE TABLE enrichment_budget (
    id UUID PRIMARY KEY,
    month DATE NOT NULL UNIQUE,
    budget DECIMAL(10,2) NOT NULL,
    spent DECIMAL(10,2) DEFAULT 0,
    leads_enriched INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Environment Variables
```bash
# API Keys
APIFY_API_KEY=your_apify_key
SERPER_API_KEY=your_serper_key
ICYPEAS_API_KEY=your_icypeas_key

# Budget Control
ENRICHMENT_MONTHLY_BUDGET=500.00
ENRICHMENT_COST_PER_LEAD_THRESHOLD=2.50

# Rate Limiting
ENRICHMENT_BATCH_SIZE=50
ENRICHMENT_CONCURRENT_LIMIT=5
```
