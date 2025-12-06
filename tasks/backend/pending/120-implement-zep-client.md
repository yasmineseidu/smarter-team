# Task: Implement Zep Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Zep extending BaseIntegrationClient with Long-term agent memory and conversation context.

## Integration Details

**Category:** Vector & Memory
**Base URL:** https://api.getzep.com
**Authentication:** Bearer Token
**Documentation:** https://docs.getzep.com
**Special:** Requires ZEP_API_URL

## Files to Create/Modify

- [ ] `app/backend/src/integrations/zep.py`
- [ ] `app/backend/__tests__/unit/integrations/test_zep.py`
- [ ] `app/backend/__tests__/fixtures/zep_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `ZepClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `ZEP_API_KEY` environment variable
- [ ] Set base URL to `https://api.getzep.com`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `add_memory(session_id: str, messages: list[dict]) -> dict - Add conversation memory`
- [ ] `get_memory(session_id: str) -> dict - Retrieve session memory`
- [ ] `search_memory(session_id: str, query: str, **kwargs) -> dict - Search memories`
- [ ] `delete_memory(session_id: str) -> dict - Delete session memory`
- [ ] `add_session(session_id: str, metadata: dict | None = None) -> dict - Create session`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `ZepAPIError` exception class
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
pytest __tests__/unit/integrations/test_zep.py -v

# Check coverage
pytest --cov=src/integrations/zep --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `ZEP_API_KEY`
- **Special**: Requires ZEP_API_URL
- Primary use case: Long-term agent memory and conversation context
- See https://docs.getzep.com for full API reference
