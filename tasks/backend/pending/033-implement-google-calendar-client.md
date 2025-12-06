# Task: Implement Google Calendar Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Google Calendar extending BaseIntegrationClient with Meeting scheduling and calendar management.

## Integration Details

**Category:** Communication & Scheduling
**Base URL:** https://www.googleapis.com/calendar/v3
**Authentication:** OAuth 2.0 (Google)
**Documentation:** https://developers.google.com/calendar/api
**Special:** OAuth 2.0 with refresh tokens

## Files to Create/Modify

- [ ] `app/backend/src/integrations/google_calendar.py`
- [ ] `app/backend/__tests__/unit/integrations/test_google_calendar.py`
- [ ] `app/backend/__tests__/fixtures/google_calendar_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `GoogleCalendarClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `GOOGLE_CALENDAR_CREDENTIALS_JSON` environment variable
- [ ] Set base URL to `https://www.googleapis.com/calendar/v3`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `list_events(calendar_id: str = 'primary', **kwargs) -> list[dict] - List events`
- [ ] `create_event(summary: str, start: dict, end: dict, **kwargs) -> dict - Create event`
- [ ] `update_event(event_id: str, **kwargs) -> dict - Update event`
- [ ] `delete_event(event_id: str) -> dict - Delete event`
- [ ] `quick_add(text: str) -> dict - Quick add event from text`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `GoogleCalendarAPIError` exception class
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
pytest __tests__/unit/integrations/test_google_calendar.py -v

# Check coverage
pytest --cov=src/integrations/google_calendar --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `GOOGLE_CALENDAR_CREDENTIALS_JSON`
- **Special**: OAuth 2.0 with refresh tokens
- Primary use case: Meeting scheduling and calendar management
- See https://developers.google.com/calendar/api for full API reference
