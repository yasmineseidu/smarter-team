# Task: Implement Apify Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Apify extending BaseIntegrationClient with Web scraping and lead list building automation.

## Integration Details

**Category:** Lead Generation & Email
**Base URL:** https://api.apify.com/v2
**Authentication:** Bearer Token
**Documentation:** https://docs.apify.com/api/v2
**Special:** Async actor runs - requires polling

## Files to Create/Modify

- [ ] `app/backend/src/integrations/apify.py`
- [ ] `app/backend/__tests__/unit/integrations/test_apify.py`
- [ ] `app/backend/__tests__/fixtures/apify_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `ApifyClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `APIFY_API_KEY` environment variable
- [ ] Set base URL to `https://api.apify.com/v2`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `run_actor(actor_id: str, input_data: dict) -> dict - Start actor run`
- [ ] `get_run_status(run_id: str) -> dict - Check run status`
- [ ] `get_dataset_items(dataset_id: str) -> list[dict] - Get scraped data`
- [ ] `list_actors() -> list[dict] - List available actors`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `ApifyAPIError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting
- [ ] Log errors with context

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses
- [ ] Test error scenarios (401, 429, invalid requests)
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List key features and capabilities
- [ ] Note rate limits and best practices

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_apify.py -v

# Check coverage
pytest --cov=src/integrations/apify --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `APIFY_API_KEY`
- **Special**: Async actor runs - requires polling
- Primary use case: Web scraping and lead list building automation
- See https://docs.apify.com/api/v2 for full API reference
