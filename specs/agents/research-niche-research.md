# Niche Research Agent - Production Specification

## Overview

**Agent Name**: `niche_research`
**Category**: Research & Intelligence
**Purpose**: Identify and score profitable niches for targeted prospecting by analyzing market dynamics, competition levels, and pain points
**Priority**: Phase 2 - Intelligence Layer
**Coverage Target**: >85% (agent testing requirement)
**Status**: Ready to Build
**Last Updated**: 2025-12-05
**Refined From**: plan/agents/research-niche-research.md

## Agent Metadata

**Dependencies**:
- None (standalone research agent)
- Database tables must exist before agent runs

**Human-in-the-Loop**:
- Niche selection requires approval before targeting (Gate 1)
- Research approach can be adjusted based on initial results

**Estimated Research Time**: 15-30 minutes per niche analysis

**Triggers**:
- Manual initiation via UI/API
- Weekly automated refresh of existing niches
- Triggered when lead quality drops below threshold

## Architecture

### Class Definition

```python
from src.agents.base_agent import BaseAgent
from src.integrations.apify import ApifyClient
from src.integrations.serper import SerperClient
from src.integrations.perplexity import PerplexityClient

class NicheResearchAgent(BaseAgent):
    """
    Researches and scores market niches for prospect targeting.

    Analyzes market size, competition intensity, pain point severity,
    and ability to pay to recommend optimal niches for outreach.
    """

    def __init__(self):
        super().__init__(
            name="niche_research",
            description="Market niche research and scoring for prospecting"
        )
        self.apify_client = ApifyClient()
        self.serper_client = SerperClient()
        self.perplexity_client = PerplexityClient()
        # Register tools after initialization
        self._register_tools()
```

### System Prompt

```
You are the Niche Research Agent for Smarter Team, an AI agency automation system.

Your mission is to identify, analyze, and score market niches to determine their viability for targeted prospecting campaigns.

**Research Framework:**

1. **Market Size Analysis**:
   - Total addressable market (TAM) estimation
   - Serviceable addressable market (SAM) calculation
   - Growth rate and market trends
   - Geographic distribution

2. **Pain Point Intensity**:
   - Identify recurring problems discussed online
   - Measure urgency and frequency of pain points
   - Assess current solution gaps
   - Evaluate willingness to pay for solutions

3. **Competition Landscape**:
   - Direct competitors analysis
   - Indirect competitors identification
   - Market saturation assessment
   - Differentiation opportunities

4. **Ability to Pay**:
   - Company size and revenue analysis
   - Budget allocation patterns
   - Decision-maker identification
   - Procurement cycle understanding

**Data Sources (in priority order):**
1. Reddit communities (r/[industry], r/[profession])
2. LinkedIn groups and job postings
3. Industry forums and communities
4. Competitor websites and pricing
5. Industry reports and market research
6. Social media discussions

**Scoring Matrix (0-100 each):**
- Market Size (0-25 points)
  - < 100 companies: 0 points
  - 100-1,000 companies: 10 points
  - 1,000-10,000 companies: 20 points
  - > 10,000 companies: 25 points

- Pain Intensity (0-30 points)
  - Rare mentions: 0-10 points
  - Regular discussions: 11-20 points
  - Urgent, frequent problems: 21-30 points

- Competition Level (0-25 points, inverted scale)
  - Highly saturated: 0-5 points
  - Moderate competition: 6-15 points
  - Low competition/blue ocean: 16-25 points

- Ability to Pay (0-20 points)
  - Small businesses: 0-5 points
  - Mid-market: 6-12 points
  - Enterprise: 13-20 points

**Quality Standards:**
- Use multiple data sources for validation
- Prioritize recent data (< 6 months)
- Verify market size with at least 2 sources
- Document all assumptions and methodologies
- Provide confidence scores for each metric

**Output Requirements:**
For each niche analyzed, provide:
1. Overall score (0-100) with category breakdowns
2. Market size estimate with sources
3. Top 3-5 pain points with evidence
4. Competitive landscape summary
5. Recommended target company size
6. Suggested messaging angles
7. Risk assessment and mitigations

**Error Handling:**
- If Reddit scraping fails, increase weight on other sources
- If insufficient data (> 50% missing), mark as "Requires Manual Review"
- If conflicting data found, document discrepancies
- Always cite sources and provide URLs

Focus on actionable insights that directly inform prospecting strategy. A well-scored niche leads to 3-5x better campaign performance.
```

## Configuration

```python
from pydantic import BaseModel, Field
from typing import Optional

class NicheResearchConfig(BaseModel):
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower for consistent scoring
    max_retries: int = 3
    timeout_seconds: int = 60
    min_sources_required: int = 3
    cache_days: int = 30  # Refresh niche data monthly

    # Scoring weights
    market_size_weight: float = 0.25
    pain_intensity_weight: float = 0.30
    competition_weight: float = 0.25
    ability_to_pay_weight: float = 0.20

    # Data collection limits
    max_reddit_posts: int = 100
    max_linkedin_jobs: int = 50
    max_competitors: int = 20
```

## Tool Definitions

### 1. `search_reddit_discussions`

**Purpose**: Analyze Reddit discussions for pain points and market insights

**Input Schema**:
```python
from pydantic import BaseModel, Field
from typing import List

class RedditSearchInput(BaseModel):
    subreddit: str = Field(..., description="Target subreddit (e.g., 'SaaS', 'sysadmin')")
    keywords: List[str] = Field(..., description="Search keywords for pain points")
    time_filter: str = Field(default="year", description="Time period: day, week, month, year, all")
    sort: str = Field(default="relevance", description="Sort by: relevance, hot, top, new")
    limit: int = Field(default=100, ge=10, le=1000, description="Max posts to analyze")

class RedditSearchOutput(BaseModel):
    success: bool
    data: Optional[dict] = None
    pain_points: List[dict] = Field(default_factory=list)
    sentiment_analysis: dict = Field(default_factory=dict)
    common_themes: List[str] = Field(default_factory=list)
    post_count: int = 0
    analyzed_at: str
    error: Optional[str] = None
```

**Error Handling**:
- Subreddit not found → Return empty with warning
- Rate limit hit → Exponential backoff, max 3 retries
- Private subreddit → Log and skip
- No relevant posts → Return empty, flag as low activity

**Implementation Notes**:
- Use Apify actor: `apify/reddit-scraper`
- Extract: title, content, comments, upvotes, post date
- Sentiment analysis on comments
- Identify recurring keywords and themes
- Cache results for 7 days

---

### 2. `analyze_linkedin_job_postings`

**Purpose**: Analyze job postings to understand market needs and company growth

**Input Schema**:
```python
class LinkedInJobsInput(BaseModel):
    keywords: List[str] = Field(..., description="Industry/job keywords")
    company_size: Optional[str] = Field(None, description="Filter: 1-10, 11-50, 51-200, 201-500, 501-1000, 1000+")
    location: Optional[str] = Field(None, description="Geographic filter")
    job_type: Optional[str] = Field(None, description="full-time, part-time, contract, etc.")
    limit: int = Field(default=50, ge=10, le=100)

class LinkedInJobsOutput(BaseModel):
    success: bool
    data: Optional[dict] = None
    job_postings: List[dict] = Field(default_factory=list)
    common_requirements: List[str] = Field(default_factory=list)
    growth_indicators: dict = Field(default_factory=dict)
    salary_ranges: List[dict] = Field(default_factory=list)
    hiring_velocity: float = 0.0  # Jobs posted per week
    analyzed_at: str
    error: Optional[str] = None
```

**Error Handling**:
- LinkedIn auth required → Use Apify actor with provided credentials
- Insufficient results → Expand search criteria
- Salary data missing → Flag as unknown
- API quota exceeded → Queue for retry

**Implementation Notes**:
- Use Apify actor: `apify/linkedin-jobs-scraper`
- Track posting frequency over time
- Extract requirements and responsibilities
- Identify pain points from "what you'll do" sections
- Group by company size for segment analysis

---

### 3. `analyze_competitor_landscape`

**Purpose**: Research competitors and identify market positioning opportunities

**Input Schema**:
```python
class CompetitorAnalysisInput(BaseModel):
    niche_keywords: List[str] = Field(..., description="Core niche keywords")
    exclude_domains: List[str] = Field(default_factory=list, description="Domains to exclude")
    include_pricing: bool = Field(default=True, description="Extract pricing info")
    max_competitors: int = Field(default=20, ge=5, le=50)

class CompetitorAnalysisOutput(BaseModel):
    success: bool
    data: Optional[dict] = None
    competitors: List[dict] = Field(default_factory=list)
    market_saturation: str  # low, medium, high
    price_ranges: List[dict] = Field(default_factory=list)
    common_features: List[str] = Field(default_factory=list)
    gaps_identified: List[str] = Field(default_factory=list)
    differentiation_opportunities: List[str] = Field(default_factory=list)
    analyzed_at: str
    error: Optional[str] = None
```

**Error Handling**:
- Web search fails → Retry with different keywords
- Competitor websites blocked → Note and continue
- Pricing info not public → Mark as "private"
- Too many results → Narrow keywords

**Implementation Notes**:
- Use Serper API for initial search
- Extract: pricing, features, target audience, positioning
- Calculate market density (competitors per 1000 companies)
- Identify feature gaps and underserved segments
- Note pricing patterns and models

---

### 4. `estimate_market_size`

**Purpose**: Calculate TAM/SAM using multiple data sources and methods

**Input Schema**:
```python
class MarketSizeInput(BaseModel):
    niche: str = Field(..., description="Niche description")
    keywords: List[str] = Field(..., description="Search terms")
    geographic_scope: str = Field(default="global", description="global, US, EU, specific country")
    company_size_focus: Optional[str] = Field(None, description="Filter by employee count")
    methodologies: List[str] = Field(default=["top-down", "bottom-up"], description="Estimation methods")

class MarketSizeOutput(BaseModel):
    success: bool
    data: Optional[dict] = None
    tam_usd: float = 0.0  # Total Addressable Market
    sam_usd: float = 0.0  # Serviceable Addressable Market
    som_usd: float = 0.0  # Serviceable Obtainable Market
    company_count: int = 0
    growth_rate: float = 0.0  # Annual CAGR
    methodology_notes: List[str] = Field(default_factory=list)
    confidence_level: str  # high, medium, low
    sources: List[dict] = Field(default_factory=list)
    calculated_at: str
    error: Optional[str] = None
```

**Error Handling**:
- Insufficient data → Use industry averages
- Conflicting estimates → Report range
- No growth data → Assume 0% growth
- Currency conversion fails → Use USD

**Implementation Notes**:
- Combine multiple estimation methods
- Cross-reference with industry reports
- Adjust for geographic scope
- Factor in market growth trends
- Document all assumptions

---

### 5. `calculate_niche_score`

**Purpose**: Apply scoring matrix to generate final niche recommendation

**Input Schema**:
```python
class NicheScoreInput(BaseModel):
    niche_id: str = Field(..., description="Unique niche identifier")
    market_size_score: float = Field(..., ge=0, le=25)
    pain_intensity_score: float = Field(..., ge=0, le=30)
    competition_score: float = Field(..., ge=0, le=25)
    ability_to_pay_score: float = Field(..., ge=0, le=20)
    qualitative_factors: dict = Field(default_factory=dict)
    risk_factors: List[str] = Field(default_factory=list)

class NicheScoreOutput(BaseModel):
    success: bool
    niche_id: str
    overall_score: float = Field(..., ge=0, le=100)
    category_scores: dict = Field(default_factory=dict)
    recommendation: str  # "High Priority", "Consider", "Avoid"
    confidence_level: str  # "High", "Medium", "Low"
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggested_approach: Optional[str] = None
    calculated_at: str
    error: Optional[str] = None
```

**Error Handling**:
- Invalid scores → Return validation error
- Missing categories → Use defaults (0)
- Tie scores → Prioritize by market size
- All scores low → Recommend avoiding niche

**Implementation Notes**:
- Apply configurable weights
- Include qualitative adjustments
- Generate tiered recommendations
- Suggest specific strategies based on score breakdown

---

### 6. `generate_niche_report`

**Purpose**: Create comprehensive niche research report with recommendations

**Input Schema**:
```python
class ReportInput(BaseModel):
    niche_id: str = Field(..., description="Unique niche identifier")
    include_raw_data: bool = Field(default=False, description="Include source data")
    report_format: str = Field(default="detailed", description="brief, standard, detailed")
    target_audience: str = Field(default="internal", description="internal, client, executive")

class ReportOutput(BaseModel):
    success: bool
    report_html: Optional[str] = None
    report_markdown: Optional[str] = None
    summary_metrics: dict = Field(default_factory=dict)
    key_insights: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    appendices: List[dict] = Field(default_factory=list)
    generated_at: str
    error: Optional[str] = None
```

**Error Handling**:
- Missing data → Generate partial report with gaps noted
- HTML generation fails → Fallback to markdown
- Report too long → Offer summary version
- Data inconsistency → Include warnings

**Implementation Notes**:
- Structured report with executive summary
- Visual charts for scores and comparisons
- Actionable recommendations
- Source citations throughout
- Appendices for detailed data

---

## Database Schema

### Table: `niches`

```sql
CREATE TABLE niches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    keywords JSONB,
    status VARCHAR(50) DEFAULT 'researching', -- researching, scored, approved, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    -- Metadata
    research_date TIMESTAMP WITH TIME ZONE,
    refresh_frequency INTERVAL DEFAULT '30 days',
    last_refreshed TIMESTAMP WITH TIME ZONE,

    -- Constraints
    UNIQUE(name)
);

CREATE INDEX idx_niches_status ON niches(status);
CREATE INDEX idx_niches_keywords ON niches USING GIN(keywords);
```

### Table: `niche_scores`

```sql
CREATE TABLE niche_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    niche_id UUID NOT NULL REFERENCES niches(id) ON DELETE CASCADE,

    -- Category scores
    market_size_score DECIMAL(5,2) CHECK (market_size_score >= 0 AND market_size_score <= 25),
    pain_intensity_score DECIMAL(5,2) CHECK (pain_intensity_score >= 0 AND pain_intensity_score <= 30),
    competition_score DECIMAL(5,2) CHECK (competition_score >= 0 AND competition_score <= 25),
    ability_to_pay_score DECIMAL(5,2) CHECK (ability_to_pay_score >= 0 AND ability_to_pay_score <= 20),

    -- Overall
    overall_score DECIMAL(5,2) CHECK (overall_score >= 0 AND overall_score <= 100),
    recommendation VARCHAR(20) CHECK (recommendation IN ('High Priority', 'Consider', 'Avoid')),
    confidence_level VARCHAR(10) CHECK (confidence_level IN ('High', 'Medium', 'Low')),

    -- Metadata
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    calculation_method JSONB,
    qualitative_factors JSONB,

    -- Constraints
    UNIQUE(niche_id)
);

CREATE INDEX idx_niche_scores_overall ON niche_scores(overall_score DESC);
CREATE INDEX idx_niche_scores_recommendation ON niche_scores(recommendation);
```

### Table: `niche_research_sources`

```sql
CREATE TABLE niche_research_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    niche_id UUID NOT NULL REFERENCES niches(id) ON DELETE CASCADE,

    -- Source details
    source_type VARCHAR(50) NOT NULL, -- reddit, linkedin, web_search, report
    source_url TEXT,
    source_name VARCHAR(255),

    -- Data extracted
    data_extracted JSONB,
    pain_points JSONB,
    sentiment_scores JSONB,

    -- Quality metrics
    reliability_score DECIMAL(3,2) CHECK (reliability_score >= 0 AND reliability_score <= 1),
    recency_score DECIMAL(3,2) CHECK (recency_score >= 0 AND recency_score <= 1),

    -- Metadata
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    extraction_method VARCHAR(100),

    -- Constraints
    CHECK (source_url IS NOT NULL OR source_name IS NOT NULL)
);

CREATE INDEX idx_niche_sources_type ON niche_research_sources(source_type);
CREATE INDEX idx_niche_sources_niche ON niche_research_sources(niche_id);
```

### Table: `niche_market_metrics`

```sql
CREATE TABLE niche_market_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    niche_id UUID NOT NULL REFERENCES niches(id) ON DELETE CASCADE,

    -- Market size metrics
    tam_usd DECIMAL(15,2),
    sam_usd DECIMAL(15,2),
    som_usd DECIMAL(15,2),
    company_count INTEGER,

    -- Market dynamics
    growth_rate DECIMAL(5,2), -- Percentage
    market_saturation VARCHAR(20),
    competitor_count INTEGER,

    -- Geographic breakdown
    geographic_scope JSONB,
    regional_distribution JSONB,

    -- Company size breakdown
    company_size_distribution JSONB,

    -- Metadata
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    methodology JSONB,
    confidence_interval JSONB,

    -- Constraints
    UNIQUE(niche_id)
);
```

## Error Handling Matrix

| Stage | Error Type | Detection | Recovery | Retry |
|-------|------------|-----------|----------|-------|
| Reddit Search | Rate limit (429) | HTTP status | Exponential backoff | Yes, 3x |
| Reddit Search | Subreddit not found | API response | Skip, log warning | No |
| Reddit Search | Private subreddit | API response | Skip, note in report | No |
| LinkedIn Jobs | Auth failure | API response | Use alternative actor | Yes, 1x |
| LinkedIn Jobs | Insufficient results | Result count | Expand search terms | Yes |
| Competitor Analysis | Search errors | HTTP status | Try alternative keywords | Yes, 2x |
| Market Size | Data conflicts | Cross-reference | Use range estimate | No |
| Market Size | Currency errors | Exception | Default to USD | No |
| Scoring | Invalid inputs | Validation | Return error | No |
| Report Generation | Template errors | Exception | Use fallback format | No |
| Database | Connection timeout | Exception | Retry with backoff | Yes, 3x |
| Database | Constraint violation | Error response | Log and skip | No |

### Recovery Strategies

1. **Graceful Degradation**:
   - Reddit fails → Increase weight on LinkedIn and web search
   - Salary data missing → Use industry averages
   - Competitor pricing private → Note in report
   - Market size unclear → Provide range

2. **Fallback Behavior**:
   - All primary sources fail → Mark as "Requires Manual Review"
   - Insufficient data points → Generate partial report with disclaimers
   - Scoring conflicts → Document and provide both perspectives

3. **User Notification**:
   - Data quality warnings in reports
   - Confidence level indicators
   - Missing data callouts
   - Manual review recommendations

## Multi-Agent Integration

**Current: Standalone Agent**
- No dependencies on other agents
- Provides input for Lead List Builder Agent
- Results used by Campaign Creation Agent

**Future Integrations**:
- **Persona Research Agent**: Share pain point insights
- **Lead List Builder**: Receive approved niches as input
- **Campaign Copywriting**: Get niche-specific messaging angles
- **Competitive Intelligence**: Share competitor analysis

**Handoff Opportunities**:
```python
# After niche approval
await self.handoff_to(
    target_agent="lead_list_builder",
    payload={
        "niche_id": niche.id,
        "target_criteria": niche.target_company_profile,
        "recommended_approach": niche.suggested_approach
    },
    priority="high"
)
```

## Testing Strategy

### Unit Tests (Target: 90% coverage)

```python
# Test tool inputs/outputs
async def test_reddit_search_validation():
    """Validate input schema and error handling"""

async def test_linkedin_job_parsing():
    """Verify job posting data extraction"""

async def test_competitor_analysis_scoring():
    """Test competition density calculation"""

async def test_market_size_estimation():
    """Verify TAM/SAM calculation logic"""

async def test_niche_scoring_matrix():
    """Test weighted score calculation"""

# Test error scenarios
async def test_reddit_rate_limit_handling():
    """Verify exponential backoff"""

async def test_insufficient_data_handling():
    """Check partial report generation"""

async def test_database_constraint_handling():
    """Test unique constraints and foreign keys"""
```

### Integration Tests (Target: 85% coverage)

```python
# End-to-end workflow
async def test_complete_niche_analysis():
    """Full pipeline with mocked APIs"""

async def test_concurrent_niche_research():
    """Verify parallel processing works"""

async def test_report_generation_accuracy():
    """Validate report data consistency"""

# API integrations
async def test_apify_reddit_integration():
    """Mocked Apify client calls"""

async def test_serper_search_integration():
    """Mocked Serper API calls"""

async def test_perplexity_analysis_integration():
    """Mocked Perplexity API calls"""

# Database operations
async def test_niche_crud_operations():
    """Create, read, update, delete niches"""

async def test_score_calculation_storage():
    """Verify score persistence"""

async def test_source_data_tracking():
    """Test research source logging"""
```

### Mocking Strategy

```python
@pytest.fixture
def mock_reddit_data():
    """Mock Reddit scraper responses"""
    return {
        "posts": [
            {
                "title": "Struggling with X problem",
                "content": "We can't find good solutions...",
                "comments": [
                    {"text": "Have you tried Y?", "sentiment": 0.8},
                    {"text": "We have same issue", "sentiment": -0.5}
                ],
                "upvotes": 45,
                "created_at": "2025-11-01T00:00:00Z"
            }
        ]
    }

@pytest.fixture
def mock_linkedin_jobs():
    """Mock LinkedIn job responses"""
    return {
        "jobs": [
            {
                "title": "Senior Role in Industry",
                "company": "TechCorp",
                "requirements": ["5+ years experience", "Skill X", "Tool Y"],
                "salary_range": "$120k-$180k",
                "posted_date": "2025-11-15T00:00:00Z"
            }
        ]
    }

@pytest.fixture
def mock_competitor_data():
    """Mock competitor analysis results"""
    return {
        "competitors": [
            {
                "name": "CompetitorA",
                "pricing": "$299/month",
                "features": ["Feature 1", "Feature 2"],
                "target_market": "Enterprise"
            }
        ],
        "market_saturation": "medium"
    }
```

### Performance Tests

```python
# Load testing
async def test_large_dataset_processing():
    """Process 100+ Reddit posts efficiently"""

async def test_concurrent_api_calls():
    """Handle multiple API calls without rate limiting"""

# Memory usage
async def test_memory_cleanup():
    """Verify proper resource cleanup after processing"""
```

## Performance

### Expected Metrics
- **Per niche analysis**: 15-30 minutes total
  - Reddit search: 3-5 minutes
  - LinkedIn analysis: 2-4 minutes
  - Competitor research: 5-10 minutes
  - Market sizing: 3-6 minutes
  - Scoring & report: 2-5 minutes

- **API call budget**: ~50-100 calls per niche
  - Serper: 20-30 searches
  - Apify: 10-15 scraper runs
  - Perplexity: 5-10 analysis requests

- **Concurrent processing**: Up to 5 niches in parallel
- **Cache hit ratio**: >60% for repeated queries

### Caching Strategy
```python
# Cache levels
1. Reddit posts: 7 days (posts don't change frequently)
2. LinkedIn jobs: 3 days (job market active)
3. Competitor data: 14 days (pricing/features stable)
4. Market reports: 30 days (industry reports static)
5. Score calculations: Until data refresh
```

## Observability

### Logging Strategy
```python
# Structured logging with context
logger.info(
    "Starting niche analysis",
    extra={
        "niche_id": niche.id,
        "niche_name": niche.name,
        "user_id": user.id,
        "data_sources": len(sources)
    }
)

# Track API usage
logger.info(
    "API quota usage",
    extra={
        "service": "apify",
        "calls_made": calls_today,
        "quota_remaining": quota_left,
        "reset_time": quota_reset
    }
)

# Error context
logger.error(
    "Reddit scraping failed",
    extra={
        "niche_id": niche.id,
        "subreddit": subreddit,
        "error_code": "RATE_LIMIT",
        "retry_attempt": attempt,
        "will_retry": True
    }
)
```

### Metrics to Track
- Agent performance (execution time, success rate)
- API usage and costs
- Data quality metrics
- Niche score distribution
- User adoption and satisfaction

### Monitoring Alerts
- API quota > 80% used
- Failure rate > 10%
- Average processing time > 45 minutes
- Database connection issues
- Missing data in reports

## Security

### API Key Management
- All API keys stored in environment variables
- Per-service rate limiting implemented
- API usage tracking and alerts
- Key rotation support

### Data Sanitization
- Remove PII from Reddit posts
- Sanitize company names
- Anonymize user mentions
- Validate all inputs

### Access Control
- Niche research restricted to authenticated users
- Approval workflow for niche activation
- Audit trail for all modifications
- Data retention policies

## Acceptance Criteria

### Functional Requirements
- [ ] Successfully analyze niches using Reddit, LinkedIn, and web search
- [ ] Generate accurate market size estimates (within ±20%)
- [ ] Score niches using defined matrix (0-100 scale)
- [ ] Produce detailed reports with sources and methodology
- [ ] Handle partial data gracefully with warnings
- [ ] Store all research data in database with proper relationships

### Quality Requirements
- [ ] Unit test coverage >90%
- [ ] Integration test coverage >85%
- [ ] All error scenarios handled with recovery
- [ ] Processing time <30 minutes per niche
- [ ] Data validation prevents invalid scores
- [ ] Reports pass content validation

### Integration Requirements
- [ ] Apify Reddit scraper integration functional
- [ ] Serper search API working with proper rate limits
- [ ] Perplexity analysis API connected
- [ ] Database operations use proper async SQLAlchemy
- [ ] Celery task queue for background processing

### Performance Requirements
- [ ] Can process 5 niches concurrently
- [ ] API calls optimized with caching
- [ ] Memory usage stable during processing
- [ ] Database queries properly indexed
- [ ] Error recovery doesn't cause memory leaks

### Security Requirements
- [ ] All API calls use secure authentication
- [ ] No sensitive data logged
- [ ] Input validation prevents injection
- [ ] Rate limiting prevents abuse
- [ ] Proper access controls enforced
