# Task: Implement Reoon Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Reoon extending BaseIntegrationClient with Email verification and validation.

## Integration Details

**Category:** Lead Generation & Email
**Base URL:** https://api.reoon.com/v1
**Authentication:** Bearer Token
**Documentation:** https://docs.reoon.com
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/reoon.py`
- [ ] `app/backend/__tests__/unit/integrations/test_reoon.py`
- [ ] `app/backend/__tests__/fixtures/reoon_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `ReoonClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `REOON_API_KEY` environment variable
- [ ] Set base URL to `https://api.reoon.com/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `verify_email(email: str) -> dict - Verify single email`
- [ ] `bulk_verify(emails: list[str]) -> dict - Bulk email verification`
- [ ] `get_verification_status(job_id: str) -> dict - Check bulk job status`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `ReoonAPIError` exception class
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
pytest __tests__/unit/integrations/test_reoon.py -v

# Check coverage
pytest --cov=src/integrations/reoon --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `REOON_API_KEY`

- Primary use case: Email verification and validation
- See https://docs.reoon.com for full API reference
