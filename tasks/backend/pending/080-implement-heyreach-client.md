# Task: Implement HeyReach Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for HeyReach extending BaseIntegrationClient with LinkedIn automation and outreach campaigns.

## Integration Details

**Category:** Lead Generation & Email
**Base URL:** https://api.heyreach.io/v1
**Authentication:** Bearer Token
**Documentation:** https://docs.heyreach.io
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/heyreach.py`
- [ ] `app/backend/__tests__/unit/integrations/test_heyreach.py`
- [ ] `app/backend/__tests__/fixtures/heyreach_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `HeyReachClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `HEYREACH_API_KEY` environment variable
- [ ] Set base URL to `https://api.heyreach.io/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_campaign(name: str, target_url: str, **kwargs) -> dict - Create LinkedIn campaign`
- [ ] `add_prospects(campaign_id: str, profiles: list[str]) -> dict - Add LinkedIn profiles`
- [ ] `get_campaign_results(campaign_id: str) -> dict - Get campaign metrics`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `HeyReachAPIError` exception class
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
pytest __tests__/unit/integrations/test_heyreach.py -v

# Check coverage
pytest --cov=src/integrations/heyreach --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `HEYREACH_API_KEY`

- Primary use case: LinkedIn automation and outreach campaigns
- See https://docs.heyreach.io for full API reference
