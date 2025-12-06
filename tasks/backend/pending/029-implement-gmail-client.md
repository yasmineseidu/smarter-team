# Task: Implement Gmail Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Gmail extending BaseIntegrationClient with Email sending and inbox monitoring for campaigns.

## Integration Details

**Category:** Communication & Scheduling
**Base URL:** https://gmail.googleapis.com/gmail/v1
**Authentication:** OAuth 2.0 (Google)
**Documentation:** https://developers.google.com/gmail/api
**Special:** OAuth 2.0 with refresh tokens - requires credentials.json and token.json

## Files to Create/Modify

- [ ] `app/backend/src/integrations/gmail.py`
- [ ] `app/backend/__tests__/unit/integrations/test_gmail.py`
- [ ] `app/backend/__tests__/fixtures/gmail_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `GmailClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `GMAIL_CREDENTIALS_JSON` environment variable
- [ ] Set base URL to `https://gmail.googleapis.com/gmail/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `send_email(to: str, subject: str, body: str, **kwargs) -> dict - Send email`
- [ ] `list_messages(query: str | None = None, max_results: int = 10) -> list[dict] - List messages`
- [ ] `get_message(message_id: str) -> dict - Get message details`
- [ ] `create_draft(to: str, subject: str, body: str) -> dict - Create draft`
- [ ] `watch_mailbox(topic_name: str) -> dict - Set up push notifications`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `GmailAPIError` exception class
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
pytest __tests__/unit/integrations/test_gmail.py -v

# Check coverage
pytest --cov=src/integrations/gmail --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `GMAIL_CREDENTIALS_JSON`
- **Special**: OAuth 2.0 with refresh tokens - requires credentials.json and token.json
- Primary use case: Email sending and inbox monitoring for campaigns
- See https://developers.google.com/gmail/api for full API reference
