# Task: Implement PandaDoc Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for PandaDoc extending BaseIntegrationClient with Proposal and contract generation with e-signatures.

## Integration Details

**Category:** Documents & Storage
**Base URL:** https://api.pandadoc.com/public/v1
**Authentication:** Bearer Token
**Documentation:** https://developers.pandadoc.com
**Special:** Webhook support for document events (PANDADOC_WEBHOOK_KEY)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/pandadoc.py`
- [ ] `app/backend/__tests__/unit/integrations/test_pandadoc.py`
- [ ] `app/backend/__tests__/fixtures/pandadoc_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `PandaDocClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `PANDADOC_API_KEY` environment variable
- [ ] Set base URL to `https://api.pandadoc.com/public/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_document(template_id: str, recipients: list[dict], **kwargs) -> dict - Create document`
- [ ] `send_document(document_id: str) -> dict - Send document for signature`
- [ ] `get_document(document_id: str) -> dict - Get document status`
- [ ] `download_document(document_id: str) -> bytes - Download signed document`
- [ ] `list_templates() -> list[dict] - List available templates`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `PandaDocAPIError` exception class
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
pytest __tests__/unit/integrations/test_pandadoc.py -v

# Check coverage
pytest --cov=src/integrations/pandadoc --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `PANDADOC_API_KEY`
- **Special**: Webhook support for document events (PANDADOC_WEBHOOK_KEY)
- Primary use case: Proposal and contract generation with e-signatures
- See https://developers.pandadoc.com for full API reference
