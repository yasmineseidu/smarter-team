# Task: Implement Technographic Data Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/leadgen-technographic-data.md
**Created:** 2025-01-05
**Estimated Effort:** 3-4 days

## Summary

Implement the Technographic Data Agent to identify and analyze prospect technology stacks using multiple data sources (BuiltWith API, Wappalyzer, website scraping, job posting analysis). The agent maintains technology intelligence, generates competitive signals, and enables targeted sales outreach.

## Files to Create

### Core Implementation
- `app/backend/src/agents/technographic_data.py` - Main agent implementation
- `app/backend/src/integrations/builtwith.py` - BuiltWith API client
- `app/backend/src/integrations/wappalyzer.py` - Wappalyzer API client
- `app/backend/src/tools/tech_detection.py` - Technology detection utilities

### Database Migrations
- `app/backend/src/alembic/versions/XXX_create_company_tech_stack.py` - Tech stack table
- `app/backend/src/alembic/versions/XXX_create_tech_signals.py` - Signals table

### Tests
- `app/backend/__tests__/unit/agents/test_technographic_data.py` - Unit tests
- `app/backend/__tests__/integration/test_technographic_data_integration.py` - Integration tests
- `app/backend/__tests__/fixtures/tech_fixtures.py` - Test fixtures for tech data

## Implementation Checklist

### Phase 1: Core Infrastructure (Day 1)
- [ ] Create BuiltWith integration client extending BaseIntegrationClient
- [ ] Create Wappalyzer integration client extending BaseIntegrationClient
- [ ] Implement rate limiting and usage tracking for both APIs
- [ ] Add API key validation and error handling
- [ ] Create database migration for `company_tech_stack` table
- [ ] Create database migration for `tech_signals` table

### Phase 2: Agent Core Logic (Day 1-2)
- [ ] Implement TechnographicDataAgent class extending BaseAgent
- [ ] Add system prompt and initialization logic
- [ ] Implement `_analyze_company` method for single company analysis
- [ ] Implement `_batch_analyze` method for bulk processing
- [ ] Create TechnologyDetection dataclass with validation
- [ ] Add confidence scoring algorithm across sources

### Phase 3: Technology Detection Tools (Day 2)
- [ ] Implement `query_builtwith_api` tool with retry logic
- [ ] Implement `query_wappalyzer_api` tool with batch support
- [ ] Implement `scrape_website_tech` tool with Firecrawl integration
- [ ] Implement `analyze_job_postings` tool for job board parsing
- [ ] Add cross-validation logic across multiple sources
- [ ] Implement caching strategy with TTL for each source

### Phase 4: Database & Signal Generation (Day 2-3)
- [ ] Implement `update_company_tech_stack` tool with merge strategies
- [ ] Implement `generate_tech_signals` tool for actionable insights
- [ ] Create SQLAlchemy models for tech stack and signals
- [ ] Add database operations with proper error handling
- [ ] Implement data freshness tracking and update scheduling
- [ ] Add competitive signal detection logic

### Phase 5: Handoffs & Integration (Day 3)
- [ ] Implement handoff to Lead List Builder with tech stack data
- [ ] Implement handoff to Campaign Creation with competitive signals
- [ ] Implement handoff to Sales agents with opportunities
- [ ] Add Celery task for background processing
- [ ] Create task queue for batch technology analysis
- [ ] Add webhook for real-time signal alerts

### Phase 6: Testing (Day 3-4)
- [ ] Write unit tests for all tools and methods
- [ ] Mock external API responses (BuiltWith, Wappalyzer, Firecrawl)
- [ ] Test rate limiting and error handling scenarios
- [ ] Write integration tests for end-to-end workflows
- [ ] Test database operations and migrations
- [ ] Test agent handoffs and task processing
- [ ] Achieve >85% code coverage

### Phase 7: Performance & Monitoring (Day 4)
- [ ] Implement caching with Redis for API responses
- [ ] Add structured logging with correlation IDs
- [ ] Create metrics for API usage, cache hits, processing time
- [ ] Add health checks for all integrations
- [ ] Implement background job for quarterly data refresh
- [ ] Add alerting for rate limit thresholds

## Acceptance Criteria

### Functional Requirements
- [ ] Successfully detects technologies from BuiltWith API with 95% accuracy
- [ ] Cross-validates findings across BuiltWith, Wappalyzer, and scraping
- [ ] Maintains technology stack with confidence scores (0-100)
- [ ] Generates competitive signals (using competitor tools)
- [ ] Identifies integration opportunities (compatible tech stacks)
- [ ] Processes batch analysis of 100+ companies under 5 minutes
- [ ] Operates within API rate limits (BuiltWith: 1k/mo, Wappalyzer: 500/mo)
- [ ] Caches results to prevent redundant API calls (7-day TTL)
- [ ] Handles API failures with graceful degradation

### Technical Requirements
- [ ] All async operations with proper error handling
- [ ] Type hints on all methods and properties
- [ ] Database operations use SQLAlchemy 2.0 async patterns
- [ ] Implements exponential backoff for rate limits
- [ ] Uses structured logging with correlation IDs
- [ ] Validates all inputs using Pydantic models
- [ ] Implements proper cleanup in __aexit__ methods

### Integration Requirements
- [ ] Extends BaseAgent following project patterns
- [ ] Integrations extend BaseIntegrationClient
- [ ] Uses Celery for background task processing
- [ ] Handoffs work with existing agent orchestration
- [ ] Follows existing naming conventions (snake_case)
- [ ] Compatible with existing database schema patterns

### Testing Requirements
- [ ] Unit tests for all tools with >90% coverage
- [ ] Integration tests for end-to-end workflows
- [ ] Mock all external API dependencies
- [ ] Tests cover error scenarios and edge cases
- [ ] Performance tests validate batch processing
- [ ] All tests pass in CI environment

## Environment Variables Required

```bash
# Primary APIs
BUILTWITH_API_KEY=                    # BuiltWith API key (1,000 credits/mo)
WAPPALYZER_API_KEY=                   # Wappalyzer API key (500 req/mo free)
FIRECRAWL_API_KEY=                    # Firecrawl API for website scraping

# Optional Job Board APIs
LINKEDIN_API_KEY=                     # For job posting analysis
INDEED_API_KEY=                       # Alternative job source

# Caching & Performance
REDIS_URL=                            # For caching API responses
CACHE_TTL_TECH_STACK=604800           # 7 days in seconds
```

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_technographic_data.py -v --cov=app/backend/src/agents/technographic_data

# Run integration tests
pytest app/backend/__tests__/integration/test_technographic_data_integration.py -v

# Type checking
mypy app/backend/src/agents/technographic_data.py

# Linting and formatting
ruff check app/backend/src/agents/technographic_data.py
ruff format app/backend/src/agents/technographic_data.py

# Database migrations
alembic upgrade head  # Apply new migrations

# Manual test (with API keys)
python -c "
from src.agents.technographic_data import TechnographicDataAgent
from src.config import Settings
import asyncio

async def test():
    agent = TechnographicDataAgent(Settings())
    result = await agent.process_task({
        'type': 'analyze_company',
        'domain': 'example.com',
        'company_id': 'test-id'
    })
    print(result)

asyncio.run(test())
"
```

## Dependencies to Add

```bash
# API clients (if not already installed)
pip install httpx>=0.27.0           # HTTP client
pip install beautifulsoup4>=4.12.0 # HTML parsing
pip install python-dotenv>=1.0.0   # Environment variables

# Database (if new patterns needed)
pip install alembic>=1.13.0        # Database migrations
pip install asyncpg>=0.31.0        # PostgreSQL async driver
```

## Notes & Considerations

1. **API Cost Management**: BuiltWith has limited credits, implement intelligent caching and batch requests
2. **Data Freshness**: Technology stacks change; implement quarterly refresh logic
3. **False Positives**: Cross-reference across sources to minimize incorrect detections
4. **Rate Limiting**: Coordinated rate limiting across all APIs to prevent blocking
5. **Privacy**: Respect robots.txt and only analyze publicly available information
6. **Scalability**: Design for processing thousands of companies efficiently
7. **Signal Quality**: Focus on high-value, actionable signals for sales team

## Success Metrics

- 95% accuracy in technology detection (validated against known stacks)
- <5 second response time for single company analysis (with cache)
- 90% cache hit rate for repeat domain lookups
- Generate at least 3 actionable signals per 100 companies analyzed
- Zero API rate limit violations in production
- <1% error rate in technology stack updates
