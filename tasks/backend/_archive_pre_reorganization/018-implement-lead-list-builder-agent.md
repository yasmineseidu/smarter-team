# Task: Implement Lead List Builder Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/leadgen-lead-list-builder.md
**Created:** 2025-12-05

## Summary

Implement the Lead List Builder Agent - an entry point agent that scrapes lead data from Apify actors (LinkedIn Sales Navigator, Apollo.io, etc.), normalizes the data, performs deduplication, assesses quality, and imports verified leads into the database. This agent is critical for the lead generation pipeline and must handle large datasets efficiently.

## Files to Create

### Core Agent
- `app/backend/src/agents/lead_list_builder/agent.py` - Main agent class
- `app/backend/src/agents/lead_list_builder/__init__.py` - Exports
- `app/backend/src/agents/lead_list_builder/schemas.py` - Pydantic models
- `app/backend/src/agents/lead_list_builder/exceptions.py` - Custom exceptions

### Integration
- `app/backend/src/integrations/apify.py` - Apify API client

### Database
- `app/backend/src/models/lead_list_builder.py` - SQLAlchemy models
- `app/backend/migrations/versions/add_lead_list_builder_tables.py` - Migration

### Webhook
- `app/backend/src/webhooks/apify.py` - Apify webhook handler

### Tests
- `app/backend/__tests__/unit/agents/test_lead_list_builder.py`
- `app/backend/__tests__/unit/integrations/test_apify.py`
- `app/backend/__tests__/unit/webhooks/test_apify_webhook.py`
- `app/backend/__tests__/integration/test_lead_list_builder_integration.py`
- `app/backend/__tests__/fixtures/lead_list_builder_fixtures.py`

## Implementation Checklist

### Phase 1: Foundation (Day 1-2)
- [ ] Create agent directory structure
- [ ] Implement `LeadListBuilderAgent` class extending `BaseAgent`
- [ ] Define system prompt with all responsibilities
- [ ] Implement basic `process_task()` method with routing
- [ ] Create ApifyClient integration extending `BaseIntegrationClient`
- [ ] Add Apify webhook configuration to `config/webhooks.py`
- [ ] Write initial unit tests for agent initialization
- [ ] Run `make check` - ensure quality gates pass

### Phase 2: Database Schema (Day 2-3)
- [ ] Create database migration with all required tables:
  - `lead_sources` - Source configurations
  - `scrape_tasks` - Apify task tracking
  - `import_logs` - Import statistics
- [ ] Add columns to existing `leads` table
- [ ] Create all necessary indexes for performance
- [ ] Apply migration and verify schema
- [ ] Write schema validation tests

### Phase 3: Apify Integration (Day 3-4)
- [ ] Implement core ApifyClient methods:
  - `run_actor()` - Start scraping tasks
  - `get_run_status()` - Monitor progress
  - `get_dataset_items()` - Retrieve results
  - `create_webhook()` - Set up notifications
  - `get_user_info()` - Check usage/budget
- [ ] Add comprehensive error handling
- [ ] Implement retry logic for transient failures
- [ ] Write integration tests with real API (if key available)

### Phase 4: Core Tools - Scraping (Day 4-5)
- [ ] Implement `launch_apify_scrape()` tool:
  - Validate search criteria
  - Check budget limits before launch
  - Configure webhooks for completion
  - Store task tracking in database
- [ ] Implement webhook handler for scrape completion
- [ ] Implement dataset retrieval and chunking
- [ ] Register all tools in agent initialization
- [ ] Write comprehensive unit tests (>90% coverage)

### Phase 5: Data Processing (Day 5-6)
- [ ] Implement `normalize_lead_data()` tool:
  - Field mapping for LinkedIn, Apollo, other sources
  - Data type conversion and validation
  - Required field enforcement
  - Field coverage statistics
- [ ] Implement `detect_duplicates()` tool:
  - Exact email matching
  - Fuzzy name/company matching using Levenshtein
  - Merge conflict resolution strategy
- [ ] Implement `assess_lead_quality()` tool:
  - Email validation and format checking
  - Data completeness scoring
  - Source reliability scoring
- [ ] Write tests for data processing edge cases

### Phase 6: Database Integration (Day 6-7)
- [ ] Implement `import_leads_to_db()` tool:
  - Batch processing for large datasets (500+ records)
  - Transaction handling and rollback on failure
  - Duplicate record updates
  - Import statistics tracking
- [ ] Implement `generate_import_report()` tool:
  - Quality metrics calculation
  - Cost analysis and recommendations
  - Performance insights
- [ ] Implement `check_budget_usage()` tool:
  - Usage tracking and forecasting
  - Alert threshold checking
  - Budget optimization suggestions
- [ ] Write database integration tests

### Phase 7: Error Handling & Quality (Day 7-8)
- [ ] Add error handling for all scenarios:
  - Apify API failures (rate limits, auth, timeouts)
  - Webhook delivery failures
  - Data corruption issues
  - Database constraint violations
- [ ] Implement retry logic with exponential backoff
- [ ] Add webhook signature verification
- [ ] Implement budget monitoring and alerting
- [ ] Add comprehensive logging with structured data
- [ ] Write error scenario tests

### Phase 8: Performance & Monitoring (Day 8-9)
- [ ] Optimize for 10,000+ lead batches:
  - Stream processing to minimize memory
  - Batch database writes
  - Parallel processing where possible
- [ ] Add performance metrics tracking:
  - Processing speed (records/sec)
  - Memory usage
  - API response times
- [ ] Implement rate limiting for concurrent scrapes
- [ ] Profile and optimize bottlenecks
- [ ] Test with large synthetic datasets

### Phase 9: Integration & End-to-End Testing (Day 9-10)
- [ ] Write end-to-end integration tests:
  - Complete workflow from scrape to import
  - Webhook delivery simulation
  - Budget management testing
  - Cross-source deduplication
- [ ] Test with multiple data sources
- [ ] Verify performance with large datasets
- [ ] Run full test suite and achieve >85% coverage
- [ ] Generate coverage report for review

### Phase 10: Documentation & Final Quality (Day 10)
- [ ] Update all docstrings with examples
- [ ] Add inline comments for complex algorithms
- [ ] Create troubleshooting guide for common issues
- [ ] Update project documentation
- [ ] Final code quality checks:
  - `make check` - all quality gates pass
  - `make lint-fix` - apply formatting fixes
  - `mypy --strict` - zero type errors
- [ ] Review logging completeness
- [ ] Final acceptance testing

## Acceptance Criteria

### Functional Requirements
- [ ] Successfully launch Apify scraping tasks with various actors
- [ ] Process webhook notifications for scrape completion
- [ ] Normalize data from LinkedIn, Apollo, and other sources
- [ ] Detect duplicates with >95% accuracy
- [ ] Score lead quality consistently (0-100 scale)
- [ ] Import 10,000+ leads in under 5 minutes
- [ ] Generate comprehensive import reports
- [ ] Monitor and alert on budget usage at 80% threshold

### Performance Requirements
- [ ] Scrape launch: <2 seconds
- [ ] Data normalization: <100ms per record
- [ ] Duplicate detection: <50ms per record
- [ ] Quality scoring: <20ms per record
- [ ] Database import: <10ms per record (batched)
- [ ] Memory usage: <512MB for 10k records
- [ ] Support up to 10 concurrent scrape tasks

### Quality Requirements
- [ ] Unit test coverage: >85%
- [ ] Tool test coverage: >90%
- [ ] Zero type errors (`mypy --strict`)
- [ ] Zero linting errors (`ruff check`)
- [ ] All error scenarios handled gracefully
- [ ] Structured logging throughout
- [ ] Webhook security verified

### Integration Requirements
- [ ] Clean integration with BaseAgent pattern
- [ ] Proper handoff to Email Verification Agent
- [ ] Database transactions with rollback
- [ ] Celery task integration for async processing
- [ ] Webhook endpoint properly registered

## Verification Commands

```bash
# Run all tests
pytest app/backend/__tests__/unit/agents/test_lead_list_builder* -v
pytest app/backend/__tests__/integration/test_lead_list_builder* -v

# Coverage check
pytest --cov=app/backend/src/agents/lead_list_builder --cov-report=html

# Type checking
mypy app/backend/src/agents/lead_list_builder/

# Linting and formatting
ruff check app/backend/src/agents/lead_list_builder/
ruff format app/backend/src/agents/lead_list_builder/

# Database migration
make migrate

# Manual test with example scrape
python -c "
from app.backend.src.agents.lead_list_builder import LeadListBuilderAgent
from app.backend.src.config import Settings
import asyncio

async def test():
    agent = LeadListBuilderAgent(Settings())
    result = await agent.launch_apify_scrape(
        actor_id='clockwork/free-linkedin-scraper',
        search_criteria={'keywords': 'CEO', 'location': 'US'},
        max_results=10
    )
    print(f'Launched scrape: {result}')

asyncio.run(test())
"
```

## Dependencies

### Required Environment Variables
- `APIFY_API_KEY` - Apify API key for scraping
- `APIFY_WEBHOOK_SECRET` - Webhook signature verification

### Python Dependencies
- No new packages required (httpx already available)
- Consider `recordlinkage` package for advanced deduplication (Phase 2+)

### Database Changes
- New tables: `lead_sources`, `scrape_tasks`, `import_logs`
- New columns on `leads` table
- New indexes for performance

## Related Tasks

- Task 015: Implement Email Verification Agent (downstream)
- Task 019: Implement Data Validation Agent (downstream)
- Task 004: Implement LinkedIn Automation Agent (potential integration)

## Notes

1. **Budget Management**: Monitor Apify compute unit usage carefully - costs can escalate quickly with large scrapes
2. **Data Privacy**: Ensure compliance with GDPR/CCPA when scraping personal data
3. **Rate Limiting**: Be respectful of source APIs to avoid being blocked
4. **Scalability**: Design for processing 10k+ leads efficiently
5. **Error Recovery**: Implement robust error handling - scraping can fail for many reasons
6. **Testing**: Mock Apify API in unit tests, use real API in integration tests sparingly

## Success Metrics

- Import success rate >90%
- Duplicate detection accuracy >95%
- Average quality score >70
- Cost per lead <$0.50
- Processing speed >100 records/second
- Zero critical errors in production

---

**Specification Version:** 1.0
**Last Updated:** 2025-12-05
**Estimated Duration:** 10 days
**Priority:** High (Phase 1 MVP)
