# Task: Implement Persona Research Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/research-persona-research.md
**Created:** 2025-01-05
**Priority:** Phase 2 - Intelligence Layer

## Summary

Implement the Persona Research Agent that conducts comprehensive research on target personas by analyzing LinkedIn profiles, Reddit discussions, and industry publications. This agent creates detailed persona documents including pain points, language patterns, buying behavior, and digital footprints to inform campaign messaging.

## Files to Create

1. **Agent Implementation:**
   - `app/backend/src/agents/persona_research/__init__.py`
   - `app/backend/src/agents/persona_research/agent.py`
   - `app/backend/src/agents/persona_research/tools.py`
   - `app/backend/src/agents/persona_research/prompts.py`
   - `app/backend/src/agents/persona_research/schemas.py`
   - `app/backend/src/agents/persona_research/exceptions.py`

2. **Database & Tasks:**
   - Database migrations for persona tables (if not already existing)
   - `app/backend/src/tasks/persona_research_tasks.py`

3. **Tests:**
   - `app/backend/__tests__/unit/agents/test_persona_research.py`
   - `app/backend/__tests__/integration/test_persona_research_integration.py`
   - Test fixtures for mock data

## Implementation Checklist

### Phase 1: Foundation Setup
- [ ] Create persona_research directory structure
- [ ] Implement all Pydantic schemas (LinkedInResults, RedditAnalysis, etc.)
- [ ] Create custom exception classes for PersonaResearchError, InsufficientDataError
- [ ] Set up database models if tables don't exist

### Phase 2: Tool Implementation
- [ ] Implement `scrape_linkedin_profiles` tool with Apify integration
- [ ] Implement `analyze_reddit_discussions` tool with Reddit API
- [ ] Implement `search_industry_content` tool with Serper
- [ ] Implement `synthesize_persona_data` tool for data aggregation
- [ ] Add input validation for all tools
- [ ] Implement retry logic with exponential backoff

### Phase 3: Agent Core
- [ ] Create PersonaResearchAgent class extending BaseAgent
- [ ] Register all tools in `_register_tools()` method
- [ ] Implement system prompt in prompts.py
- [ ] Create user prompt templates for different research scenarios
- [ ] Add context management for research sessions

### Phase 4: Error Handling & Reliability
- [ ] Implement comprehensive error handling matrix
- [ ] Add graceful degradation when data sources fail
- [ ] Implement confidence scoring algorithm
- [ ] Add data validation and sanitization
- [ ] Log all API calls and results with structured logging

### Phase 5: Integration & Orchestration
- [ ] Create Celery tasks for async persona research
- [ ] Implement handoff to Campaign Copywriting Agent
- [ ] Add support for batch processing multiple personas
- [ ] Implement caching for research results

### Phase 6: Testing
- [ ] Write unit tests for all tools (mock external APIs)
- [ ] Write integration tests for end-to-end workflow
- [ ] Create test fixtures for LinkedIn, Reddit, and web data
- [ ] Test error scenarios and recovery strategies
- [ ] Verify agent handoff payload format

### Phase 7: Performance & Monitoring
- [ ] Implement performance metrics and logging
- [ ] Add rate limiting for API calls
- [ ] Optimize for parallel processing where possible
- [ ] Set up alerts for failure thresholds

## Implementation Details

### Key Integration Points:

1. **Apify Integration (LinkedIn Scraping):**
   ```python
   # Use: apify-client-python
   # Actor: linkedin-profile-scraper or custom
   # Input: job titles, industry, filters
   # Output: Structured profile data
   ```

2. **Reddit API Integration:**
   ```python
   # Use: praw (Python Reddit API Wrapper)
   # Authentication: OAuth2 with app credentials
   # Data: Posts, comments, upvotes, timestamps
   ```

3. **Serper Integration:**
   ```python
   # Use: serper-dev-python-sdk
   # Purpose: Industry content and publication search
   # Features: Site filtering, result ranking
   ```

### Data Processing Requirements:

1. **Language Pattern Extraction:**
   - Identify common jargon and industry terms
   - Extract frequently asked questions
   - Analyze sentiment and tone preferences
   - Detect objection patterns

2. **Behavioral Analysis:**
   - Identify peak activity times
   - Determine preferred content formats
   - Map decision-making processes
   - Extract buying triggers

3. **Quality Assurance:**
   - Minimum 50 LinkedIn profiles for statistical significance
   - Minimum 100 Reddit posts across 3+ subreddits
   - Cross-validate insights across sources
   - Flag conflicting data for review

### Performance Targets:

- **Persona Creation Time:** <10 minutes
- **API Response Time:** <30 seconds average
- **Success Rate:** >95% for complete personas
- **Data Quality Score:** >0.7 average confidence

## Acceptance Criteria

- [ ] Agent successfully creates persona documents from LinkedIn, Reddit, and web data
- [ ] All tools handle rate limits and API failures gracefully
- [ ] Persona documents include all required sections with confidence scores
- [ ] Integration with Campaign Copywriting Agent works seamlessly
- [ ] Unit test coverage >85%
- [ ] Integration tests pass with mocked APIs
- [ ] Performance meets specified targets
- [ ] All data is validated and sanitized
- [ ] Error scenarios are properly logged and handled
- [ ] Agent handoffs include correct payload structure

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_persona_research.py -v --cov=app/backend/src/agents/persona_research

# Run integration tests
pytest app/backend/__tests__/integration/test_persona_research_integration.py -v

# Type checking
mypy app/backend/src/agents/persona_research/ --strict

# Linting
ruff check app/backend/src/agents/persona_research/

# Manual test (requires API keys)
python -c "
from app.backend.src.agents.persona_research import PersonaResearchAgent
import asyncio

async def test():
    agent = PersonaResearchAgent()
    result = await agent.process_task({
        'type': 'research_persona',
        'job_titles': ['Product Manager'],
        'industry': 'SaaS',
        'company_size': '50-200'
    })
    print(result)

asyncio.run(test())
"
```

## Dependencies

### External APIs Required:
- `APIFY_API_TOKEN` - For LinkedIn scraping
- `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` - Reddit API access
- `REDDIT_USER_AGENT` - Reddit client identification
- `SERPER_API_KEY` - Web search capabilities

### Python Packages:
```text
apify-client>=1.0.0
praw>=7.7.0
google-search-results>=2.4.2
pydantic>=2.0.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.28.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
```

## Notes

1. This agent is critical for the intelligence layer - ensure data quality and accuracy
2. Implement robust error handling as external APIs can be unreliable
3. Consider implementing a queue system for batch persona research
4. Add monitoring for API quota usage to prevent service disruptions
5. Document any assumptions or limitations in the agent's capabilities
