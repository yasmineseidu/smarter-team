# Task: Implement Progressive Enrichment Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/leadgen-progressive-enrichment.md
**Created:** 2025-01-05
**Estimated Effort:** 16-24 hours

## Summary

Implement the Progressive Enrichment Agent that fills data gaps in lead records over time using multiple APIs (Apify, Serper, Icypeas). The agent prioritizes engaged leads, manages enrichment costs, and tracks ROI to ensure cost-effective data enhancement.

## Files to Create

- `app/backend/src/agents/progressive_enrichment/__init__.py`
- `app/backend/src/agents/progressive_enrichment/agent.py`
- `app/backend/src/agents/progressive_enrichment/tools.py`
- `app/backend/src/agents/progressive_enrichment/prompts.py`
- `app/backend/src/agents/progressive_enrichment/schemas.py`
- `app/backend/src/agents/progressive_enrichment/exceptions.py`
- `app/backend/__tests__/unit/agents/test_progressive_enrichment.py`
- `app/backend/__tests__/integration/test_progressive_enrichment_integration.py`
- `app/backend/src/tasks/enrichment_tasks.py`
- Database migrations for enrichment tables

## Implementation Checklist

### 1. Agent Structure Setup
- [ ] Create ProgressiveEnrichmentAgent class extending BaseAgent
- [ ] Implement constructor with API clients and budget tracking
- [ ] Set up rate limiting for each integration
- [ ] Create enums for EnrichmentTier and EnrichmentField
- [ ] Initialize logging and metrics collection

### 2. Tool Implementation
- [ ] Implement `identify_enrichment_candidates` tool
  - Query leads with missing fields
  - Calculate priority tiers based on engagement
  - Estimate enrichment costs
  - Return candidate list with recommendations
- [ ] Implement `enrich_lead_profile` tool
  - Orchestrate multiple API calls
  - Merge data from different sources
  - Apply confidence scores
  - Track costs and update records
- [ ] Implement `enrich_company_data` tool
  - Call Apify/Serper for company information
  - Include technology stack detection
  - Validate and normalize data
- [ ] Implement `find_contact_information` tool
  - Search for phone numbers and social profiles
  - Verify matches using multiple data points
  - Return confidence scores
- [ ] Implement `get_recent_news_signals` tool
  - Search news APIs and company announcements
  - Extract conversation starters
  - Provide timing recommendations
- [ ] Implement `calculate_enrichment_roi` tool
  - Use historical data for campaign lift
  - Calculate cost-benefit analysis
  - Recommend enrichment actions

### 3. Error Handling & Resilience
- [ ] Implement rate limit handling with exponential backoff
- [ ] Add fallback strategies when APIs fail
- [ ] Implement retry logic with maximum attempts
- [ ] Add graceful degradation for partial failures
- [ ] Create custom exceptions for enrichment errors

### 4. Database Integration
- [ ] Create enrichment_queue table for tracking jobs
- [ ] Create enrichment_history table for audit trail
- [ ] Create enrichment_budget table for cost tracking
- [ ] Implement CRUD operations for queue management
- [ ] Add database indexes for performance

### 5. API Integration
- [ ] Implement ApifyClient for people/company data
- [ ] Implement SerperClient for company research
- [ ] Implement IcypeasClient for social profile lookup
- [ ] Add request/response logging
- [ ] Implement response validation

### 6. Testing
- [ ] Write unit tests for all tools (mock APIs)
- [ ] Test rate limiting and backoff logic
- [ ] Test budget management and ROI calculation
- [ ] Write integration tests with mocked external APIs
- [ ] Test agent handoffs to Waterfall Enrichment
- [ ] Test database operations
- [ ] Achieve >85% test coverage

### 7. Performance & Caching
- [ ] Implement Redis caching for enrichment results
- [ ] Add cache invalidation logic
- [ ] Optimize batch processing
- [ ] Implement background task queuing
- [ ] Add performance metrics

### 8. Configuration & Security
- [ ] Add environment variables for API keys
- [ ] Implement budget configuration
- [ ] Add input validation with Pydantic
- [ ] Secure logging (no PII in logs)
- [ ] Add API rate limit configuration

### 9. Documentation
- [ ] Add inline docstrings for all methods
- [ ] Document API integration patterns
- [ ] Create troubleshooting guide
- [ ] Document configuration options

## Acceptance Criteria

From specs/agents/leadgen-progressive-enrichment.md:

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

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_progressive_enrichment.py -v --cov=app/backend/src/agents/progressive_enrichment

# Run integration tests
pytest app/backend/__tests__/integration/test_progressive_enrichment_integration.py -v

# Type checking
mypy app/backend/src/agents/progressive_enrichment/

# Linting
ruff check app/backend/src/agents/progressive_enrichment/

# Format check
ruff format --check app/backend/src/agents/progressive_enrichment/

# Manual test
python -c "
from app.backend.src.agents.progressive_enrichment.agent import ProgressiveEnrichmentAgent
from app.backend.src.config import Settings
agent = ProgressiveEnrichmentAgent(Settings())
print(f'Agent initialized: {agent.name}')
"

# Check database tables
psql $DATABASE_URL -c "\d enrichment_queue;"
psql $DATABASE_URL -c "\d enrichment_history;"
psql $DATABASE_URL -c "\d enrichment_budget;"
```

## Dependencies

### Prerequisites
- [ ] BaseAgent class implemented
- [ ] Integration clients for Apify, Serper, Icypeas
- [ ] Database migrations system in place
- [ ] Redis for caching configured
- [ ] Celery for background tasks configured

### API Keys Required
- [ ] APIFY_API_KEY in environment
- [ ] SERPER_API_KEY in environment
- [ ] ICYPEAS_API_KEY in environment

### Feature Dependencies
- [ ] Lead List Builder Agent (provides leads)
- [ ] Email Verification Agent (provides engagement data)
- [ ] Waterfall Enrichment Agent (for fallback)

## Notes

1. **Cost Management**: Implement strict budget controls from day one. Track costs per field and per lead to ensure ROI targets are met.

2. **Rate Limiting**: All APIs have different rate limits. Implement a unified rate limiter that queues requests appropriately.

3. **Data Quality**: Implement confidence scoring for all enriched data. Low-confidence data should be flagged for review.

4. **Performance**: Use batching and parallel processing where possible, but respect API limits.

5. **Monitoring**: Set up alerts for budget thresholds, API failures, and low enrichment success rates.

## Follow-up Tasks

Once this agent is complete:
1. Create dashboard for enrichment metrics
2. Set up automated budget alerts
3. Implement A/B testing for enrichment effectiveness
4. Add more data sources based on performance
5. Create enrichment quality review workflow
