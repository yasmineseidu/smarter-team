# Task: Implement GoHighLevel Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for GoHighLevel extending BaseIntegrationClient with CRM contact and pipeline management.

## Integration Details

**Category:** CRM & Project Management
**Base URL:** https://rest.gohighlevel.com/v1
**Authentication:** Bearer Token
**Documentation:** https://highlevel.stoplight.io
**Special:** Webhook support for CRM events

## Files to Create/Modify

- [ ] `app/backend/src/integrations/gohighlevel.py`
- [ ] `app/backend/__tests__/unit/integrations/test_gohighlevel.py`
- [ ] `app/backend/__tests__/fixtures/gohighlevel_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `GoHighLevelClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `GOHIGHLEVEL_API_KEY` environment variable
- [ ] Set base URL to `https://rest.gohighlevel.com/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_contact(email: str, name: str, **kwargs) -> dict - Create CRM contact`
- [ ] `update_contact(contact_id: str, **kwargs) -> dict - Update contact`
- [ ] `add_tag(contact_id: str, tag: str) -> dict - Add tag to contact`
- [ ] `create_opportunity(contact_id: str, **kwargs) -> dict - Create sales opportunity`
- [ ] `send_sms(contact_id: str, message: str) -> dict - Send SMS`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `GoHighLevelAPIError` exception class
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
pytest __tests__/unit/integrations/test_gohighlevel.py -v

# Check coverage
pytest --cov=src/integrations/gohighlevel --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `GOHIGHLEVEL_API_KEY`
- **Special**: Webhook support for CRM events
- Primary use case: CRM contact and pipeline management
- See https://highlevel.stoplight.io for full API reference
