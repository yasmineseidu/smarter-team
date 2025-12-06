# Task: Implement Signaturely Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Signaturely extending BaseIntegrationClient with E-signature and contract management.

## Integration Details

**Category:** Documents & Storage
**Base URL:** https://api.signaturely.com/v1
**Authentication:** Bearer Token
**Documentation:** https://docs.signaturely.com
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/signaturely.py`
- [ ] `app/backend/__tests__/unit/integrations/test_signaturely.py`
- [ ] `app/backend/__tests__/fixtures/signaturely_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `SignaturelyClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `SIGNATURELY_API_KEY` environment variable
- [ ] Set base URL to `https://api.signaturely.com/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_contract(title: str, file_url: str, signers: list[dict]) -> dict - Create contract`
- [ ] `send_contract(contract_id: str) -> dict - Send contract for signing`
- [ ] `get_contract(contract_id: str) -> dict - Get contract status`
- [ ] `download_signed_contract(contract_id: str) -> bytes - Download signed contract`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `SignaturelyAPIError` exception class
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
pytest __tests__/unit/integrations/test_signaturely.py -v

# Check coverage
pytest --cov=src/integrations/signaturely --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `SIGNATURELY_API_KEY`

- Primary use case: E-signature and contract management
- See https://docs.signaturely.com for full API reference
