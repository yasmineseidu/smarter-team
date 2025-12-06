# Task: Implement Niche Research Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/research-niche-research.md
**Created:** 2025-12-05
**Estimated Effort:** 2-3 days

## Summary

Implement the Niche Research Agent that identifies and scores profitable market niches for targeted prospecting. The agent analyzes Reddit discussions, LinkedIn job postings, competitor landscapes, and market size data to generate comprehensive niche recommendations with confidence scores.

This agent extends BaseAgent and integrates with Apify (Reddit scraping), Serper (web search), and Perplexity (AI analysis) APIs to collect and analyze market intelligence.

## Files to Create

- `app/backend/src/agents/niche_research/agent.py`
- `app/backend/src/agents/niche_research/tools.py`
- `app/backend/src/agents/niche_research/prompts.py`
- `app/backend/src/agents/niche_research/schemas.py`
- `app/backend/src/agents/niche_research/__init__.py`
- `app/backend/__tests__/unit/agents/test_niche_research.py`
- `app/backend/__tests__/integration/test_niche_research_integration.py`
- `app/backend/src/tasks/niche_research_tasks.py`

## Implementation Checklist

### Agent Implementation
- [ ] Create NicheResearchAgent class extending BaseAgent
- [ ] Initialize integration clients (Apify, Serper, Perplexity)
- [ ] Register all 6 tools with proper schemas
- [ ] Implement system prompt with detailed instructions
- [ ] Add configuration management with scoring weights

### Tool Implementation (tools.py)
- [ ] `search_reddit_discussions` - Reddit pain point analysis
- [ ] `analyze_linkedin_job_postings` - Job market insights
- [ ] `analyze_competitor_landscape` - Competition analysis
- [ ] `estimate_market_size` - TAM/SAM/SOM calculation
- [ ] `calculate_niche_score` - Scoring matrix application
- [ ] `generate_niche_report` - Comprehensive report generation

### Database Integration
- [ ] Create Pydantic models for database tables
- [ ] Implement async SQLAlchemy operations
- [ ] Add proper indexes and constraints
- [ ] Handle foreign key relationships
- [ ] Implement soft delete for research data

### Error Handling & Resilience
- [ ] Exponential backoff for rate limits (max 3 retries)
- [ ] Graceful degradation when sources fail
- [ ] Partial report generation with warnings
- [ ] Comprehensive logging with structured context
- [ ] Timeout handling for all API calls

### Caching Strategy
- [ ] Implement Redis caching for API responses
- [ ] Cache Reddit posts for 7 days
- [ ] Cache LinkedIn jobs for 3 days
- [ ] Cache competitor data for 14 days
- [ ] Cache market reports for 30 days

### Testing Implementation
- [ ] Unit tests for all 6 tools (mock external APIs)
- [ ] Test error scenarios and recovery strategies
- [ ] Integration tests for end-to-end workflow
- [ ] Database operation tests with fixtures
- [ ] Performance tests for concurrent processing

### Documentation & Type Safety
- [ ] Full type hints using Python 3.11+ syntax
- [ ] Docstrings for all public methods
- [ ] Example usage in README
- [ ] API rate limit documentation

## Acceptance Criteria

### Functional Requirements
- [ ] Successfully analyze niches using all 3 data sources
- [ ] Generate accurate market size estimates (within ±20%)
- [ ] Score niches using 4-category matrix (0-100 scale)
- [ ] Produce HTML and Markdown reports with sources
- [ ] Store all research data with proper relationships
- [ ] Handle partial data gracefully with warnings

### Quality Requirements
- [ ] Unit test coverage >90%
- [ ] Integration test coverage >85%
- [ ] All tools properly validate inputs
- [ ] Error scenarios handled with recovery
- [ ] Processing time <30 minutes per niche
- [ ] Type checking passes with MyPy

### Performance Requirements
- [ ] Can process 5 niches concurrently
- [ ] API calls optimized with caching
- [ ] Memory usage stable during processing
- [ ] Database queries properly indexed
- [ ] No memory leaks in long-running tasks

## Implementation Details

### Key Patterns to Follow

1. **Agent Structure**:
```python
class NicheResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="niche_research", description="...")
        self.apify_client = ApifyClient()
        self.serper_client = SerperClient()
        self.perplexity_client = PerplexityClient()
        self._register_tools()
```

2. **Tool Registration**:
```python
from src.agents.base_agent import tool

@tool(
    name="search_reddit_discussions",
    description="Search Reddit for pain points and market insights",
    parameters=RedditSearchInput.model_json_schema()
)
async def search_reddit_discussions(args: dict) -> dict:
    # Implementation
```

3. **Error Handling**:
```python
try:
    result = await api_call()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        # Exponential backoff
        await asyncio.sleep(2 ** attempt)
        retry = True
```

4. **Database Operations**:
```python
async with async_session() as session:
    niche = Niche(
        name=niche_name,
        keywords=keywords,
        status="researching"
    )
    session.add(niche)
    await session.commit()
```

### Dependencies to Install
```bash
# Already in pyproject.toml
# anthropic>=0.75.0
# httpx>=0.27.0
# pydantic>=2.12.5
# sqlalchemy>=2.0.44
# asyncpg>=0.31.0
# redis>=6.4.0
```

### Environment Variables Needed
```bash
# Existing
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0

# New
APIFY_API_TOKEN=...
SERPER_API_KEY=...
PERPLEXITY_API_KEY=...
```

## Verification

### Run Tests
```bash
# Unit tests
pytest app/backend/__tests__/unit/agents/test_niche_research.py -v --cov=app/backend/src/agents/niche_research

# Integration tests
pytest app/backend/__tests__/integration/test_niche_research_integration.py -v

# All agent tests
pytest app/backend/__tests__/unit/agents/ -k "niche" -v
```

### Type Checking
```bash
mypy app/backend/src/agents/niche_research/
mypy app/backend/src/tasks/niche_research_tasks.py
```

### Linting & Formatting
```bash
ruff check app/backend/src/agents/niche_research/
ruff format app/backend/src/agents/niche_research/
```

### Manual Testing
```python
# Test agent instantiation
python -c "
from app.backend.src.agents.niche_research.agent import NicheResearchAgent
agent = NicheResearchAgent()
print(f'Agent created: {agent.name}')
print(f'Tools registered: {len(agent.tools)}')
"

# Test individual tools
python -c "
from app.backend.src.agents.niche_research.tools import search_reddit_discussions
import asyncio
result = asyncio.run(search_reddit_discussions({
    'subreddit': 'SaaS',
    'keywords': ['automation', 'efficiency'],
    'limit': 10
}))
print(f'Tool result: {result}')
"
```

### Database Validation
```bash
# Check tables exist
psql $DATABASE_URL -c "\dt niches*"

# Verify constraints
psql $DATABASE_URL -c "\d niche_scores"
```

## Notes

1. **Rate Limiting**: All external API calls must respect rate limits. Use the BaseIntegrationClient's rate limiting features.

2. **Data Privacy**: Reddit posts must be sanitized to remove PII before storage.

3. **Cost Control**: Monitor API usage and implement quotas to prevent unexpected costs.

4. **Human Review**: Generated niche scores require human approval before campaign activation.

5. **Refresh Strategy**: Implement a background task to refresh niche data monthly to keep insights current.

## Related Tasks

This implementation enables:
- Lead List Builder Agent (uses approved niches)
- Campaign Creation Agent (gets niche insights)
- Persona Research Agent (shares pain point data)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limits | Medium | Implement caching, exponential backoff |
| Inaccurate market sizing | High | Cross-reference multiple sources |
| Competitor data missing | Medium | Use alternative research methods |
| Reddit API changes | Low | Multiple data source fallbacks |
