# Task: Implement Findymail Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Findymail extending BaseIntegrationClient with Email discovery and contact enrichment.

## Integration Details

**Category:** Lead Generation & Email
**Base URL:** https://app.findymail.com/api/v1
**Authentication:** Bearer Token
**Documentation:** https://docs.findymail.com
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/findymail.py`
- [ ] `app/backend/__tests__/unit/integrations/test_findymail.py`
- [ ] `app/backend/__tests__/fixtures/findymail_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `FindymailClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `FINDYMAIL_API_KEY` environment variable
- [ ] Set base URL to `https://app.findymail.com/api/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `search_email(name: str, domain: str) -> dict - Find email by name and domain`
- [ ] `enrich_contact(linkedin_url: str) -> dict - Enrich from LinkedIn`
- [ ] `verify_email(email: str) -> dict - Verify email deliverability`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `FindymailAPIError` exception class
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
pytest __tests__/unit/integrations/test_findymail.py -v

# Check coverage
pytest --cov=src/integrations/findymail --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `FINDYMAIL_API_KEY`

- Primary use case: Email discovery and contact enrichment
- See https://docs.findymail.com for full API reference
