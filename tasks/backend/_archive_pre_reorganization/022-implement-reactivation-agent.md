# Task: Implement Reactivation Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/offboarding-reactivation.md
**Created:** 2025-12-05
**Priority:** Phase 6 - Multi-Channel & Advanced

## Summary
Implement the Reactivation Agent that monitors cold leads for trigger events (job changes, funding rounds, company growth, leadership changes, competitor mentions, industry events) and generates personalized reactivation outreach at optimal times.

## Files to Create
- `app/backend/src/agents/reactivation/`
  - `__init__.py` - Agent exports
  - `agent.py` - Main ReactivationAgent class
  - `tools.py` - All 5 trigger monitoring and content generation tools
  - `prompts.py` - System and user prompt templates
  - `schemas.py` - Pydantic models for all inputs/outputs
  - `exceptions.py` - Custom exceptions
- `app/backend/src/integrations/linkedin.py` - LinkedIn monitoring client
- `app/backend/src/integrations/news_api.py` - News API client
- `app/backend/src/tasks/reactivation_tasks.py` - Celery tasks
- `app/backend/__tests__/unit/agents/test_reactivation.py` - Unit tests
- `app/backend/__tests__/integration/test_reactivation_integration.py` - Integration tests
- `specs/database-schema/migrations/` - SQL migration files for 4 tables

## Implementation Checklist

### Database Schema
- [ ] Create `reactivation_pools` table with proper indexes
- [ ] Create `reactivation_triggers` table with JSONB fields and indexes
- [ ] Create `reactivation_campaigns` table with conversion tracking
- [ ] Create `reactivation_monitoring` table for source configuration
- [ ] Add foreign key relationships where appropriate
- [ ] Create necessary indexes for performance
- [ ] Write migration files

### Agent Implementation
- [ ] Create ReactivationAgent class extending BaseAgent
- [ ] Implement system prompt with reactivation guidelines
- [ ] Set up configuration with timing rules and limits

### Tools Implementation
- [ ] Implement `monitor_linkedin_changes` with rate limit handling
- [ ] Implement `scan_news_sources` with multiple source support
- [ ] Implement `analyze_job_postings` with growth signal detection
- [ ] Implement `generate_reactivation_content` with personalization
- [ ] Implement `schedule_reactivation` with campaign coordination
- [ ] Add comprehensive error handling for all tools
- [ ] Include retry logic with exponential backoff

### Integrations
- [ ] Create LinkedIn client for job change monitoring
- [ ] Create News API client for funding/leadership events
- [ ] Implement job board scraping for growth signals
- [ ] Add proper authentication and rate limiting
- [ ] Handle API quotas and fallback strategies

### Multi-Agent Coordination
- [ ] Implement handoff to Long-Term Nurture Agent
- [ ] Integrate with Company Research Agent for validation
- [ ] Coordinate with Campaign agents for execution
- [ ] Sync with Intent Signal Agent for prioritization
- [ ] Handle incoming handoffs from other agents

### Celery Tasks
- [ ] Create periodic task for trigger scanning
- [ ] Implement batch processing of detected triggers
- [ ] Add task for reactivation campaign scheduling
- [ ] Include error handling and retry logic
- [ ] Set up proper task routing and priorities

### Testing
- [ ] Write unit tests for all 5 tools
- [ ] Test trigger detection accuracy
- [ ] Test timing calculation logic
- [ ] Test content generation quality
- [ ] Write integration tests for end-to-end flows
- [ ] Test error handling and recovery
- [ ] Mock external API responses
- [ ] Test rate limit handling
- [ ] Verify multi-agent handoffs

### Performance & Reliability
- [ ] Implement batch processing for large datasets
- [ ] Add database query optimization
- [ ] Include comprehensive logging
- [ ] Add metrics collection
- [ ] Implement circuit breakers for external APIs
- [ ] Add daily limits and queue management

## Acceptance Criteria

### Functional Requirements
- [ ] Successfully detect all 6 trigger types with >90% accuracy
- [ ] Calculate optimal contact timing based on trigger type
- [ ] Generate personalized reactivation content for each trigger
- [ ] Schedule and execute reactivation campaigns
- [ ] Track all reactivation metrics and outcomes
- [ ] Achieve >15% response rate on reactivated leads
- [ ] Generate positive ROI on reactivation efforts

### Technical Requirements
- [ ] All I/O operations must be async
- [ ] Full type hints with MyPy compliance
- [ ] All tests pass (unit + integration)
- [ ] Code coverage >85% for agent logic
- [ ] Handle all error scenarios gracefully
- [ ] Respect API rate limits and quotas
- [ ] Comply with privacy regulations

### Integration Requirements
- [ ] Seamless handoff with Long-Term Nurture Agent
- [ ] Validation through Company Research Agent
- [ ] Campaign execution through Campaign agents
- [ ] Intent data integration with Intent Signal Agent

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_reactivation.py -v --cov=src.agents.reactivation

# Run integration tests
pytest app/backend/__tests__/integration/test_reactivation_integration.py -v

# Type checking
mypy app/backend/src/agents/reactivation/

# Linting and formatting
ruff check app/backend/src/agents/reactivation/
ruff format app/backend/src/agents/reactivation/

# Database migration
cd app/backend && alembic upgrade head

# Manual test - trigger detection
python -c "
from src.agents.reactivation import ReactivationAgent
import asyncio

async def test():
    agent = ReactivationAgent()
    result = await agent.monitor_linkedin_changes({
        'contact_ids': ['test123'],
        'max_results': 10
    })
    print(result)

asyncio.run(test())
"
```

## Dependencies

### Required Environment Variables
```bash
LINKEDIN_API_KEY=your_linkedin_api_key
NEWS_API_KEY=your_news_api_key
CRUNCHBASE_API_KEY=your_crunchbase_key
SERPER_API_KEY=your_serper_key  # For job searches
```

### Python Dependencies (add to pyproject.toml)
- `linkedin-api` - LinkedIn API client
- `newsapi-python` - News API client
- `crunchbase-api` - Crunchbase integration
- `beautifulsoup4` - Job board scraping
- `newspaper3k` - Article content extraction

## Notes
- This is a Phase 6 agent, should be implemented after core campaign agents
- Requires careful attention to rate limits and API costs
- Personalization is key to reactivation success
- Must integrate smoothly with existing nurture workflows
