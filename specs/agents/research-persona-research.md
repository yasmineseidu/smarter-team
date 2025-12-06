# Persona Research Agent - Production Specification

## Overview

**Agent Name**: `persona_research`
**Category**: Research & Intelligence
**Purpose**: Deep understanding of target personas to inform messaging and campaign strategy
**Priority**: Phase 2 - Intelligence Layer
**Coverage Target**: >85% (agent testing requirement)

## Agent Metadata

**Dependencies**:
- Niche Research Agent (provides niche context for persona research)
- Database tables must exist before agent runs
- Apify, Serper, and Reddit API credentials configured

**Human-in-the-Loop**: Persona definitions reviewed before use in campaigns (Gate 1: Campaign setup)

**Estimated Research Time**: 5-10 minutes per persona (includes LinkedIn scraping, Reddit analysis, and web research)

## Architecture

### Class Definition

```python
from src.agents.base_agent import BaseAgent
from src.integrations.apify import ApifyClient
from src.integrations.serper import SerperClient
from src.integrations.reddit import RedditClient
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime

class PersonaResearchAgent(BaseAgent):
    """
    Researches and builds comprehensive persona profiles for target markets.

    Analyzes LinkedIn profiles, Reddit discussions, industry publications,
    and web content to create detailed persona documents for campaign teams.
    """

    def __init__(self):
        super().__init__(
            name="persona_research",
            description="Deep persona research for messaging strategy"
        )
        self.apify_client = ApifyClient()
        self.serper_client = SerperClient()
        self.reddit_client = RedditClient()
        # Register tools after initialization
        self._register_tools()
```

### Configuration

```python
class PersonaResearchConfig:
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7
    max_retries: int = 3
    timeout_seconds: int = 30

    # Research limits
    max_linkedin_profiles: int = 50
    max_reddit_posts: int = 100
    max_web_results: int = 20

    # Quality thresholds
    min_confidence_score: float = 0.7
    min_data_points: int = 10
```

### System Prompt

```
You are the Persona Research Agent for Smarter Team, an AI agency automation system.

Your mission is to build comprehensive persona profiles by analyzing real data from multiple sources. You uncover the authentic voice, challenges, and motivations of target audiences.

**Research Methodology:**
1. **LinkedIn Analysis**: Extract language patterns, career progression, and common skills from real profiles
2. **Reddit Intelligence**: Identify pain points, discussions, and genuine concerns from relevant communities
3. **Industry Publications**: Understand what content they consume and share
4. **Behavioral Synthesis**: Combine all data into actionable persona insights

**Data Quality Standards:**
- Source every insight with specific URLs/posts
- Assign confidence scores (High/Medium/Low) based on data volume and recency
- Prioritize recent data (<6 months) over historical patterns
- Identify contradictions and note edge cases
- Flag assumptions that need validation

**Output Structure:**
For each persona, provide:

1. **Day-in-the-Life Summary**
   - Typical daily routines and priorities
   - Key responsibilities and time allocation
   - Common tools and platforms used

2. **Pain Points & Challenges**
   - Top 5 frustrations (ranked by frequency/severity)
   - Problems they're actively trying to solve
   - Barriers to success in their role

3. **Goals & KPIs**
   - What they're measured on
   - Success metrics for their role
   - Career aspirations and motivations

4. **Language & Communication Style**
   - Common jargon and terminology
   - Communication preferences (email, Slack, phone)
   - Tone and formality expectations
   - Memes, references, cultural touchpoints

5. **Digital Footprint**
   - Where they spend time online (specific subreddits, LinkedIn groups, forums)
   - Publications/blogs they follow
   - Influencers they trust
   - Events they attend

6. **Buying Behavior**
   - What triggers their search for solutions
   - Decision-making process and timeline
   - Common objections and questions
   - Who influences their decisions

**Error Handling:**
- If LinkedIn scraping fails, increase Reddit/web search depth
- If insufficient data (<20 unique profiles/posts), flag as "needs manual research"
- If contradictory findings >30%, highlight for human review
- Always provide confidence levels and data sources

**Ethical Guidelines:**
- Use only publicly available information
- Don't store PII beyond what's necessary for persona building
- Respect API rate limits and terms of service
- Focus on patterns, not individuals

Your insights directly impact campaign effectiveness. Quality over speed - a well-researched persona improves conversion rates by 3-5x.
```

## Tool Definitions

### 1. `scrape_linkedin_profiles`

**Purpose**: Extract profile data from LinkedIn searches using Apify actors

**Input Schema**:
```python
class LinkedInSearchParams(BaseModel):
    job_titles: List[str] = Field(..., description="List of job titles to search for")
    industry: str = Field(..., description="Industry to filter by")
    company_size: Optional[str] = Field(None, description="Company size range (e.g., '50-200', '1000+')")
    location: Optional[str] = Field(None, description="Geographic location filter")
    max_profiles: int = Field(default=50, ge=10, le=100, description="Maximum profiles to scrape")
```

**Output Schema**:
```python
class LinkedInProfile(BaseModel):
    url: str
    name: Optional[str]
    headline: Optional[str]
    summary: Optional[str]
    experience: List[Dict[str, Any]]
    skills: List[str]
    education: List[Dict[str, Any]]
    activity: Optional[List[Dict[str, Any]]]

class LinkedInResults(BaseModel):
    profiles: List[LinkedInProfile]
    total_searched: int
    successful_extractions: int
    search_date: datetime
    confidence_score: float
```

**Error Handling**:
- Apify rate limit (429) → Exponential backoff, max 3 retries
- Invalid search parameters → Return validation error
- Partial scraping success → Continue with available data, note gaps
- Complete failure → Log error, proceed with other data sources

**Example**:
```python
# Input
{
    "job_titles": ["Product Manager", "Senior Product Manager"],
    "industry": "SaaS",
    "company_size": "50-200",
    "location": "US",
    "max_profiles": 50
}

# Output
{
    "profiles": [...],
    "total_searched": 50,
    "successful_extractions": 42,
    "confidence_score": 0.84
}
```

### 2. `analyze_reddit_discussions`

**Purpose**: Extract insights from Reddit discussions in relevant communities

**Input Schema**:
```python
class RedditSearchParams(BaseModel):
    subreddits: List[str] = Field(..., description="List of subreddit names to search")
    keywords: List[str] = Field(..., description="Keywords to search for")
    time_filter: str = Field(default="year", regex="^(day|week|month|year|all)$")
    sort: str = Field(default="relevance", regex="^(relevance|hot|top|new)$")
    max_posts: int = Field(default=100, ge=10, le=500, description="Maximum posts to analyze")
```

**Output Schema**:
```python
class RedditInsight(BaseModel):
    subreddit: str
    post_title: str
    post_content: str
    comments: List[str]
    upvotes: int
    sentiment: str  # positive, negative, neutral
    themes: List[str]
    pain_points: List[str]

class RedditAnalysis(BaseModel):
    insights: List[RedditInsight]
    total_analyzed: int
    common_themes: Dict[str, int]  # theme -> frequency
    sentiment_distribution: Dict[str, float]
    top_pain_points: List[Dict[str, Any]]
    confidence_score: float
```

**Error Handling**:
- Subreddit not found → Skip, continue with others
- API rate limit → Exponential backoff
- Private/restricted subreddit → Note in logs
- Insufficient data (<10 posts) → Flag for manual review

### 3. `search_industry_content`

**Purpose**: Find industry publications, blogs, and content the persona consumes

**Input Schema**:
```python
class WebSearchParams(BaseModel):
    queries: List[str] = Field(..., description="Search queries for industry content")
    exclude_sites: Optional[List[str]] = Field(None, description="Sites to exclude from results")
    max_results: int = Field(default=20, ge=5, le=50)
    content_types: List[str] = Field(
        default=["blog", "publication", "forum", "community"],
        description="Types of content to prioritize"
    )
```

**Output Schema**:
```python
class ContentSource(BaseModel):
    url: str
    title: str
    description: str
    type: str  # blog, publication, forum, etc.
    domain: str
    estimated_audience: Optional[str]
    content_themes: List[str]

class WebContentResults(BaseModel):
    sources: List[ContentSource]
    top_domains: List[Dict[str, Any]]
    common_topics: List[str]
    recommended_following: List[str]  # influencers, publications
    content_gaps: List[str]
```

**Error Handling**:
- Serper API quota exceeded → Switch to backup search provider or use cached results
- No relevant results → Broaden search terms
- Invalid URL results → Filter out, note percentage filtered

### 4. `synthesize_persona_data`

**Purpose**: Combine all research into structured persona document

**Input Schema**:
```python
class PersonaSynthesisParams(BaseModel):
    linkedin_data: Optional[LinkedInResults]
    reddit_data: Optional[RedditAnalysis]
    web_content: Optional[WebContentResults]
    persona_title: str = Field(..., description="Title for the persona")
    target_industry: str = Field(..., description="Primary industry")
    niche_context: Optional[str] = Field(None, description="Additional context from niche research")
```

**Output Schema**:
```python
class PersonaDocument(BaseModel):
    title: str
    industry: str
    research_date: datetime
    data_sources: List[str]
    confidence_score: float
    sample_size: Dict[str, int]  # linkedin: 50, reddit: 100, etc.

    # Core persona sections
    day_in_life: Dict[str, Any]
    pain_points: List[Dict[str, Any]]
    goals_kpis: List[Dict[str, Any]]
    language_style: Dict[str, Any]
    digital_footprint: Dict[str, Any]
    buying_behavior: Dict[str, Any]

    # Meta information
    assumptions: List[str]
    data_gaps: List[str]
    recommended_research: List[str]
    validation_needed: List[str]
```

**Error Handling**:
- Insufficient total data points → Flag for manual research
- Contradictory insights >30% → Highlight contradictions
- Low confidence score (<0.7) → Mark as draft, requires validation

## Error Handling Matrix

| Component | Error Type | Detection | Response | Retry |
|-----------|------------|-----------|----------|-------|
| LinkedIn | Rate limit (429) | Apify response | Exponential backoff | Yes, 3x |
| LinkedIn | Invalid search | Validation error | Return detailed message | No |
| LinkedIn | Partial failure | Success rate < 80% | Continue with data | No |
| Reddit | Subreddit not found | 403/404 | Log, skip subreddit | No |
| Reddit | Rate limit (429) | HTTP 429 | Backoff retry | Yes, 3x |
| Reddit | Insufficient data | <10 posts | Flag for manual review | No |
| Web Search | Quota exceeded | API response | Use cached data | Yes, 1x |
| Web Search | No results | Empty results | Broaden queries | Yes, 1x |
| Synthesis | Low confidence | Score < 0.7 | Mark as draft | No |
| Synthesis | Contradictions | Theme overlap >30% | Flag for review | No |

## Database Schema

### Table: `personas`
```sql
CREATE TABLE personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100), -- agent name
    status VARCHAR(20) DEFAULT 'draft', -- draft, reviewed, active, archived
    confidence_score DECIMAL(3,2),
    sample_size JSONB,
    data_sources TEXT[],
    metadata JSONB
);
```

### Table: `persona_research_data`
```sql
CREATE TABLE persona_research_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id UUID REFERENCES personas(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL, -- linkedin, reddit, web
    source_url TEXT,
    raw_data JSONB,
    extracted_insights JSONB,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Table: `persona_language_patterns`
```sql
CREATE TABLE persona_language_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id UUID REFERENCES personas(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50), -- jargon, phrases, questions, objections
    pattern_text TEXT NOT NULL,
    frequency INTEGER,
    confidence_score DECIMAL(3,2),
    examples TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Multi-Agent Integration

### Handoffs To:
- **Campaign Copywriting Agent**: Provides persona insights for personalized messaging
- **Campaign Creation Agent**: Supplies audience understanding for campaign strategy

### Receives From:
- **Niche Research Agent**: Provides market context to focus persona research
- **Lead List Builder Agent**: May trigger persona research for new markets

### Handoff Payload:
```python
{
    "persona_id": str,
    "persona_title": str,
    "key_insights": {
        "primary_pain_points": List[str],
        "language_style": Dict[str, Any],
        "buying_triggers": List[str],
        "objections": List[str]
    },
    "confidence_score": float,
    "data_sources": List[str]
}
```

## Testing Strategy

### Unit Tests
```python
class TestPersonaResearchAgent:
    @pytest.mark.asyncio
    async def test_linkedin_scraping_success(self):
        """Verify LinkedIn data extraction and validation"""

    @pytest.mark.asyncio
    async def test_reddit_analysis_sentiment(self):
        """Verify sentiment analysis and theme extraction"""

    @pytest.mark.asyncio
    async def test_synthesis_low_confidence(self):
        """Verify handling of insufficient data"""

    def test_input_validation(self):
        """Verify schema validation for all tools"""

    def test_error_handling_rate_limit(self):
        """Verify exponential backoff on rate limits"
```

### Integration Tests
```python
class TestPersonaResearchIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_persona_research(self):
        """Full persona creation workflow with mocked APIs"""

    @pytest.mark.asyncio
    async def test_partial_data_handling(self):
        """Verify graceful degradation when some sources fail"""

    @pytest.mark.asyncio
    async def test_agent_handoff_to_copywriting(self):
        """Verify data format matches expectations of downstream agents"""
```

### Mocking Strategy
```python
@pytest.fixture
def mock_linkedin_data():
    """Mock LinkedIn profile data"""
    return {
        "profiles": [
            {
                "name": "John Doe",
                "headline": "Senior Product Manager at TechCorp",
                "summary": "Building products that matter...",
                "skills": ["Product Management", "Agile", "SQL"],
                "experience": [...]
            }
        ],
        "confidence_score": 0.85
    }

@pytest.fixture
def mock_reddit_data():
    """Mock Reddit discussion data"""
    return {
        "insights": [
            {
                "subreddit": "productmanagement",
                "post_title": "Biggest challenges in PM role?",
                "sentiment": "neutral",
                "pain_points": ["stakeholder alignment", "resource constraints"]
            }
        ],
        "top_pain_points": [...]
    }
```

## Performance Requirements

### Latency Targets:
- LinkedIn scraping: <2 minutes per 10 profiles
- Reddit analysis: <1 minute per subreddit
- Web search: <30 seconds per query
- Total persona creation: <10 minutes

### Resource Limits:
- Max concurrent API calls: 5
- Memory usage: <500MB per persona
- Database storage: ~1MB per persona (with all source data)

### Caching Strategy:
- Cache LinkedIn search results for 24 hours
- Cache Reddit analysis for 1 week
- Cache web search results for 3 days
- Cache final personas for 30 days

## Observability

### Metrics to Track:
- Persona creation success rate
- Average data points per persona
- Confidence score distribution
- API call latency and errors
- Source data quality scores

### Logging Requirements:
```python
# Structured logging examples
logger.info(
    "Starting persona research",
    extra={
        "persona_title": persona_title,
        "industry": industry,
        "job_titles": job_titles,
        "search_params": search_params
    }
)

logger.info(
    "LinkedIn scraping completed",
    extra={
        "profiles_found": len(profiles),
        "success_rate": success_rate,
        "confidence_score": confidence_score
    }
)

logger.warning(
    "Insufficient data from Reddit",
    extra={
        "subreddits_searched": len(subreddits),
        "total_posts": total_posts,
        "threshold": 10
    }
)
```

### Alerts:
- Persona creation failure rate >10%
- Average confidence score <0.7
- API quota exhaustion
- Data source failures >50%

## Security

### API Key Management:
- All API keys stored in environment variables
- Keys rotated quarterly
- Rate limiting enforced at application level

### Data Privacy:
- No PII stored beyond what's necessary
- Raw LinkedIn profiles deleted after 30 days
- Persona data accessible only to authorized campaigns

### Compliance:
- GDPR compliant (anonymized data only)
- Respect robots.txt and API terms
- No scraping of private communities

## Acceptance Criteria

- [ ] Successfully scrapes and analyzes LinkedIn profiles for given job titles/industry
- [ ] Extracts meaningful insights from at least 3 relevant subreddits
- [ ] Generates persona document with all required sections
- [ ] Confidence scoring accurately reflects data quality
- [ ] Handles API failures gracefully without losing all data
- [ ] Integrates properly with Campaign Copywriting Agent
- [ ] All unit tests pass with >85% coverage
- [ ] Integration tests verify end-to-end workflow
- [ ] Persona creation completes within 10 minutes
- [ ] Data is properly validated and sanitized
- [ ] Error scenarios are logged appropriately
- [ ] Performance metrics meet specified targets

## File Structure to Create

```
app/backend/src/agents/persona_research/
├── __init__.py
├── agent.py              # PersonaResearchAgent class
├── tools.py              # Tool implementations
├── prompts.py            # Prompt templates
├── schemas.py            # Pydantic models
└── exceptions.py         # Custom exceptions

app/backend/src/tasks/persona_research_tasks.py
app/backend/__tests__/unit/agents/test_persona_research.py
app/backend/__tests__/integration/test_persona_research_integration.py
```

This specification provides a complete blueprint for implementing the Persona Research Agent with comprehensive error handling, testing, and integration patterns.
