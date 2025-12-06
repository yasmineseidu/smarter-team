# Task: Implement Airtable Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Airtable extending BaseIntegrationClient with Flexible database for leads, campaigns, and tracking.

## Integration Details

**Category:** CRM & Project Management
**Base URL:** https://api.airtable.com/v0
**Authentication:** Bearer Token
**Documentation:** https://airtable.com/developers/web/api
**Special:** Requires AIRTABLE_BASE_ID for operations

## Files to Create/Modify

- [ ] `app/backend/src/integrations/airtable.py`
- [ ] `app/backend/__tests__/unit/integrations/test_airtable.py`
- [ ] `app/backend/__tests__/fixtures/airtable_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `AirtableClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `AIRTABLE_API_KEY` environment variable
- [ ] Set base URL to `https://api.airtable.com/v0`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `list_records(table_name: str, **kwargs) -> dict - List table records`
- [ ] `create_record(table_name: str, fields: dict) -> dict - Create record`
- [ ] `update_record(table_name: str, record_id: str, fields: dict) -> dict - Update record`
- [ ] `delete_record(table_name: str, record_id: str) -> dict - Delete record`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `AirtableAPIError` exception class
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
pytest __tests__/unit/integrations/test_airtable.py -v

# Check coverage
pytest --cov=src/integrations/airtable --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `AIRTABLE_API_KEY`
- **Special**: Requires AIRTABLE_BASE_ID for operations
- Primary use case: Flexible database for leads, campaigns, and tracking
- See https://airtable.com/developers/web/api for full API reference
