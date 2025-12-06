# Task: Implement Notion Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Notion extending BaseIntegrationClient with Knowledge base management and documentation.

## Integration Details

**Category:** CRM & Project Management
**Base URL:** https://api.notion.com/v1
**Authentication:** Bearer Token (with Notion-Version header)
**Documentation:** https://developers.notion.com
**Special:** Requires Notion-Version: 2022-06-28 header

## Files to Create/Modify

- [ ] `app/backend/src/integrations/notion.py`
- [ ] `app/backend/__tests__/unit/integrations/test_notion.py`
- [ ] `app/backend/__tests__/fixtures/notion_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `NotionClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `NOTION_API_KEY` environment variable
- [ ] Set base URL to `https://api.notion.com/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `query_database(database_id: str, filter: dict | None = None) -> dict - Query database`
- [ ] `create_page(parent: dict, properties: dict) -> dict - Create page`
- [ ] `update_page(page_id: str, properties: dict) -> dict - Update page`
- [ ] `append_blocks(block_id: str, children: list[dict]) -> dict - Add content blocks`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `NotionAPIError` exception class
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
pytest __tests__/unit/integrations/test_notion.py -v

# Check coverage
pytest --cov=src/integrations/notion --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `NOTION_API_KEY`
- **Special**: Requires Notion-Version: 2022-06-28 header
- Primary use case: Knowledge base management and documentation
- See https://developers.notion.com for full API reference
