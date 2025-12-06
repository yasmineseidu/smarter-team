# Task: Implement Fathom Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Fathom extending BaseIntegrationClient with Call recording, transcription, and analysis.

## Integration Details

**Category:** Communication & Scheduling
**Base URL:** https://api.fathom.video/v1
**Authentication:** Bearer Token
**Documentation:** https://docs.fathom.video
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/fathom.py`
- [ ] `app/backend/__tests__/unit/integrations/test_fathom.py`
- [ ] `app/backend/__tests__/fixtures/fathom_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `FathomClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `FATHOM_API_KEY` environment variable
- [ ] Set base URL to `https://api.fathom.video/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `list_recordings(**kwargs) -> list[dict] - List call recordings`
- [ ] `get_recording(recording_id: str) -> dict - Get recording details`
- [ ] `get_transcript(recording_id: str) -> dict - Get call transcript`
- [ ] `get_summary(recording_id: str) -> dict - Get AI-generated summary`
- [ ] `search_recordings(query: str) -> list[dict] - Search recordings`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `FathomAPIError` exception class
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
pytest __tests__/unit/integrations/test_fathom.py -v

# Check coverage
pytest --cov=src/integrations/fathom --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `FATHOM_API_KEY`

- Primary use case: Call recording, transcription, and analysis
- See https://docs.fathom.video for full API reference
