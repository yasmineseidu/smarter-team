# Task: Implement Autobound Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Autobound extending BaseIntegrationClient with AI-powered email personalization for cold outreach.

## Integration Details

**Category:** Lead Generation & Email
**Base URL:** https://api.autobound.ai/v1
**Authentication:** Bearer Token
**Documentation:** https://docs.autobound.ai
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/autobound.py`
- [ ] `app/backend/__tests__/unit/integrations/test_autobound.py`
- [ ] `app/backend/__tests__/fixtures/autobound_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `AutoboundClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `AUTOBOUND_API_KEY` environment variable
- [ ] Set base URL to `https://api.autobound.ai/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `personalize_email(lead_data: dict, template: str) -> dict - Generate personalized email`
- [ ] `get_insights(company_domain: str) -> dict - Get personalization insights`
- [ ] `batch_personalize(leads: list[dict]) -> list[dict] - Batch personalization`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `AutoboundAPIError` exception class
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
pytest __tests__/unit/integrations/test_autobound.py -v

# Check coverage
pytest --cov=src/integrations/autobound --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `AUTOBOUND_API_KEY`

- Primary use case: AI-powered email personalization for cold outreach
- See https://docs.autobound.ai for full API reference
