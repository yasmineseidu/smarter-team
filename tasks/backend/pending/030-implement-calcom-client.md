# Task: Implement Cal.com Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Cal.com extending BaseIntegrationClient with Meeting scheduling automation with Cal.com.

## Integration Details

**Category:** Communication & Scheduling
**Base URL:** https://api.cal.com/v1
**Authentication:** Bearer Token
**Documentation:** https://cal.com/docs/api
**Special:** Webhook support for booking events

## Files to Create/Modify

- [ ] `app/backend/src/integrations/calcom.py`
- [ ] `app/backend/__tests__/unit/integrations/test_calcom.py`
- [ ] `app/backend/__tests__/fixtures/calcom_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `Cal.comClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `CAL_COM_API_KEY` environment variable
- [ ] Set base URL to `https://api.cal.com/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `get_bookings(**kwargs) -> list[dict] - List bookings`
- [ ] `get_availability(username: str, date_from: str, date_to: str) -> dict - Check availability`
- [ ] `create_event_type(title: str, length: int, **kwargs) -> dict - Create event type`
- [ ] `reschedule_booking(booking_id: str, start_time: str) -> dict - Reschedule booking`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `Cal.comAPIError` exception class
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
pytest __tests__/unit/integrations/test_calcom.py -v

# Check coverage
pytest --cov=src/integrations/calcom --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `CAL_COM_API_KEY`
- **Special**: Webhook support for booking events
- Primary use case: Meeting scheduling automation with Cal.com
- See https://cal.com/docs/api for full API reference
