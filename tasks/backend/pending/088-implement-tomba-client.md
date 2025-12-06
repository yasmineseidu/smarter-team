# Task: Implement Tomba Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Tomba extending BaseIntegrationClient with Email finding and verification service.

## Integration Details

**Category:** Lead Generation & Email
**Base URL:** https://api.tomba.io/v1
**Authentication:** API Key header (X-Tomba-Key)
**Documentation:** https://developer.tomba.io
**Special:** Uses X-Tomba-Key header instead of Authorization

## Files to Create/Modify

- [ ] `app/backend/src/integrations/tomba.py`
- [ ] `app/backend/__tests__/unit/integrations/test_tomba.py`
- [ ] `app/backend/__tests__/fixtures/tomba_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `TombaClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `TOMBA_API_KEY` environment variable
- [ ] Set base URL to `https://api.tomba.io/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `email_finder(first_name: str, last_name: str, domain: str) -> dict - Find email`
- [ ] `email_verifier(email: str) -> dict - Verify email`
- [ ] `domain_search(domain: str) -> dict - Search all emails at domain`
- [ ] `email_count(domain: str) -> dict - Count emails at domain`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `TombaAPIError` exception class
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
pytest __tests__/unit/integrations/test_tomba.py -v

# Check coverage
pytest --cov=src/integrations/tomba --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `TOMBA_API_KEY`
- **Special**: Uses X-Tomba-Key header instead of Authorization
- Primary use case: Email finding and verification service
- See https://developer.tomba.io for full API reference
