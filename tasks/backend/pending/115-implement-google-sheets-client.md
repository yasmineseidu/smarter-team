# Task: Implement Google Sheets Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Google Sheets extending BaseIntegrationClient with Spreadsheet data management and reporting.

## Integration Details

**Category:** Communication & Scheduling
**Base URL:** https://sheets.googleapis.com/v4
**Authentication:** OAuth 2.0 (Google)
**Documentation:** https://developers.google.com/sheets/api
**Special:** OAuth 2.0 with refresh tokens

## Files to Create/Modify

- [ ] `app/backend/src/integrations/google_sheets.py`
- [ ] `app/backend/__tests__/unit/integrations/test_google_sheets.py`
- [ ] `app/backend/__tests__/fixtures/google_sheets_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `GoogleSheetsClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `GOOGLE_SHEETS_CREDENTIALS_JSON` environment variable
- [ ] Set base URL to `https://sheets.googleapis.com/v4`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `get_values(spreadsheet_id: str, range: str) -> dict - Get cell values`
- [ ] `update_values(spreadsheet_id: str, range: str, values: list[list]) -> dict - Update cells`
- [ ] `append_values(spreadsheet_id: str, range: str, values: list[list]) -> dict - Append rows`
- [ ] `create_spreadsheet(title: str) -> dict - Create new spreadsheet`
- [ ] `batch_update(spreadsheet_id: str, requests: list[dict]) -> dict - Batch operations`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `GoogleSheetsAPIError` exception class
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
pytest __tests__/unit/integrations/test_google_sheets.py -v

# Check coverage
pytest --cov=src/integrations/google_sheets --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `GOOGLE_SHEETS_CREDENTIALS_JSON`
- **Special**: OAuth 2.0 with refresh tokens
- Primary use case: Spreadsheet data management and reporting
- See https://developers.google.com/sheets/api for full API reference
