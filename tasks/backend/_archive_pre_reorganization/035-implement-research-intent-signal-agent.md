# Task: Implement Intent Signal Tracking Agent

**Status:** Pending
**Domain:** Backend
**Agent:** research_intent_signal
**Spec Reference:** specs/agents/research-intent-signal.md
**Created:** 2025-12-05
**Priority:** High (Phase 6 - Multi-Channel & Advanced)

## Summary

Implement the Intent Signal Tracking Agent that monitors companies for buying signals and trigger events. The agent scans multiple data sources daily to detect intent signals, scores them using a weighted algorithm, and triggers outreach workflows for high-intent signals.

**Key Features:**
- Daily scanning of job postings, news, funding announcements, leadership changes
- Weighted scoring algorithm (1-10 scale) based on signal type and recency
- Integration with 7 external APIs (LinkedIn, News API, Crunchbase, etc.)
- Automatic handoff to Sales Agent for high-intent signals (score ≥ 8.0)
- Historical signal tracking for pattern analysis

## Files to Create

### Core Agent Implementation
- `app/backend/src/agents/research_intent_signal/agent.py` - Main agent class
- `app/backend/src/agents/research_intent_signal/__init__.py` - Package exports
- `app/backend/src/agents/research_intent_signal/tools.py` - Signal detection tools
- `app/backend/src/agents/research_intent_signal/schemas.py` - Pydantic models
- `app/backend/src/agents/research_intent_signal/prompts.py` - System prompts
- `app/backend/src/agents/research_intent_signal/exceptions.py` - Custom exceptions
- `app/backend/src/agents/research_intent_signal/scoring.py` - Scoring algorithm

### Database Models & Migrations
- `app/backend/src/models/intent_signal.py` - SQLAlchemy models
- `app/backend/migrations/versions/xxx_create_intent_signal_tables.py` - Migration

### Tasks & Background Processing
- `app/backend/src/tasks/intent_signal_tasks.py` - Celery tasks for batch processing

### Tests
- `app/backend/__tests__/unit/agents/test_research_intent_signal.py` - Unit tests
- `app/backend/__tests__/unit/agents/test_intent_signal_scoring.py` - Scoring tests
- `app/backend/__tests__/integration/test_research_intent_signal_integration.py` - Integration tests
- `app/backend/__tests__/fixtures/intent_signal_fixtures.py` - Test fixtures

### Integration Clients
- `app/backend/src/integrations/crunchbase.py` - Crunchbase API client
- `app/backend/src/integrations/linkedin_company.py` - LinkedIn Company API client

## Implementation Checklist

### Phase 1: Foundation (Day 1-2)
- [ ] Create agent directory structure and base files
- [ ] Implement IntentSignalAgent class extending BaseAgent
- [ ] Create database models (intent_signals, signal_types, lead_intent_scores)
- [ ] Write and apply database migration
- [ ] Set up basic logging and error handling

### Phase 2: Core Tools (Day 3-5)
- [ ] Implement `scan_job_postings` tool with Serper API integration
- [ ] Implement `scan_company_news` tool with News API
- [ ] Implement `check_funding_database` tool with Crunchbase
- [ ] Implement `monitor_linkedin_activity` tool
- [ ] Implement `detect_technology_changes` tool with BuiltWith
- [ ] Add comprehensive error handling for all API calls

### Phase 3: Scoring & Logic (Day 6-7)
- [ ] Implement `calculate_intent_score` tool with weighted algorithm
- [ ] Implement `update_lead_priority` tool
- [ ] Create signal deduplication logic
- [ ] Add recency factor calculations
- [ ] Test scoring accuracy against known examples

### Phase 4: Background Processing (Day 8-9)
- [ ] Create Celery task for daily batch processing
- [ ] Implement parallel processing for multiple companies
- [ ] Add rate limiting and queue management
- [ ] Set up retry logic with exponential backoff
- [ ] Configure daily cron trigger (5:00 AM)

### Phase 5: Integration & Handoffs (Day 10)
- [ ] Implement handoff to Sales Agent for high-intent signals
- [ ] Implement handoff to Campaign Personalization Agent
- [ ] Add memory integration for signal history
- [ ] Test multi-agent workflows end-to-end

### Phase 6: Testing (Day 11-12)
- [ ] Write comprehensive unit tests (target: 90% coverage)
- [ ] Write integration tests with mocked APIs
- [ ] Create test fixtures for all signal types
- [ ] Test error scenarios and recovery
- [ ] Performance test with 1000+ companies

### Phase 7: Production Readiness (Day 13)
- [ ] Add monitoring and metrics collection
- [ ] Implement caching for API responses
- [ ] Add database query optimization
- [ ] Document API rate limits and quotas
- [ ] Create operational runbook

## Database Schema Key Points

```sql
-- Core tables to implement:
CREATE TABLE intent_signals (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    confidence DECIMAL(3,2),
    score_value DECIMAL(3,1),
    raw_data JSONB
);

CREATE TABLE signal_types (
    name VARCHAR(50) PRIMARY KEY,
    weight DECIMAL(3,2) NOT NULL
);

CREATE TABLE lead_intent_scores (
    lead_id UUID PRIMARY KEY,
    current_score DECIMAL(3,1) NOT NULL,
    signal_count INTEGER NOT NULL
);
```

## Key Algorithms to Implement

### Intent Score Calculation
```
Base Score = Σ(signal_value × category_weight × recency_factor)

Where:
- signal_value: 1-5 based on signal strength
- category_weight: 0.05-0.30 per signal type
- recency_factor: 1.0 (7 days), 0.7 (30 days), 0.3 (90 days)

Final Score: Normalized to 1-10 scale
```

### Signal Deduplication
- Group by company_id + signal_type + description_hash
- Keep highest confidence score
- Merge within 7-day window

## Acceptance Criteria

- [ ] Agent scans all tracked companies daily within 4-hour window
- [ ] Detects signals from all 7 categories with >90% accuracy
- [ ] Intent scores correlate with actual sales outcomes (R² > 0.6)
- [ ] High-intent signals (score ≥ 8) trigger outreach within 1 hour
- [ ] Processes 1000+ companies without performance degradation
- [ ] All API failures handled gracefully with proper logging
- [ ] Database transactions maintain ACID compliance
- [ ] Unit test coverage >90%, integration test coverage >80%
- [ ] No memory leaks in long-running batch processes

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_research_intent_signal.py -v --cov=src.agents.research_intent_signal

# Run integration tests
pytest app/backend/__tests__/integration/test_research_intent_signal_integration.py -v

# Type checking
mypy app/backend/src/agents/research_intent_signal/

# Linting
ruff check app/backend/src/agents/research_intent_signal/
ruff format app/backend/src/agents/research_intent_signal/

# Manual test with single company
python -c "
from src.agents.research_intent_signal import IntentSignalAgent
import asyncio

async def test():
    agent = IntentSignalAgent()
    result = await agent.process_task({
        'type': 'scan_company',
        'company_domain': 'example.com',
        'company_name': 'Example Corp'
    })
    print(result)

asyncio.run(test())
"

# Database migration test
alembic upgrade head
# Verify tables created
psql $DATABASE_URL -c "\dt intent_*"
```

## Dependencies Required

```python
# Add to pyproject.toml
"crunchbase-api>=1.0.0",
"linkedin-api>=2.0.0",
"builtwith>=1.0.0",
"newsapi>=2.0.0",
"serper>=1.0.0",
```

## Environment Variables

```bash
# Add to .env.example
CRUNCHBASE_API_KEY=your_crunchbase_key
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_secret
NEWS_API_KEY=your_news_api_key
BUILTWITH_API_KEY=your_builtwith_key
SERPER_API_KEY=your_serper_key
```

## Risk Mitigation

1. **API Rate Limits:** Implement exponential backoff, circuit breakers
2. **Data Quality:** Cross-reference signals from multiple sources
3. **False Positives:** Require minimum confidence before triggering outreach
4. **Performance:** Process in batches, use connection pooling
5. **Cost:** Monitor API usage, implement caching where possible

## Rollback Plan

If critical issues discovered:
1. Stop daily Celery task
2. Revert database migration if needed
3. Disable handoffs to other agents
4. Continue monitoring existing signals (read-only mode)

## Next Steps After Implementation

1. Deploy to staging environment
2. Run parallel processing with existing workflow
3. Compare intent scores with actual sales outcomes
4. Fine-tune scoring algorithm based on results
5. Enable automated handoffs to sales team
6. Monitor performance and optimize as needed
