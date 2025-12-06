# Task: Implement Anymailfinder Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Anymailfinder extending BaseIntegrationClient with Email address discovery and domain search.

## Integration Details

**Category:** Lead Generation & Email
**Base URL:** https://api.anymailfinder.com/v4.0
**Authentication:** Bearer Token
**Documentation:** https://anymailfinder.com/api
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/anymailfinder.py`
- [ ] `app/backend/__tests__/unit/integrations/test_anymailfinder.py`
- [ ] `app/backend/__tests__/fixtures/anymailfinder_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `AnymailfinderClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `ANYMAILFINDER_API_KEY` environment variable
- [ ] Set base URL to `https://api.anymailfinder.com/v4.0`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `find_email(full_name: str, domain: str) -> dict - Find email address`
- [ ] `search_domain(domain: str) -> dict - Find all emails at domain`
- [ ] `verify_email(email: str) -> dict - Verify email exists`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `AnymailfinderAPIError` exception class
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
pytest __tests__/unit/integrations/test_anymailfinder.py -v

# Check coverage
pytest --cov=src/integrations/anymailfinder --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `ANYMAILFINDER_API_KEY`

- Primary use case: Email address discovery and domain search
- See https://anymailfinder.com/api for full API reference
