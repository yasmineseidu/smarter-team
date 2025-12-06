# Task: Implement ClickUp Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for ClickUp extending BaseIntegrationClient with Project management and task tracking for client deliveries.

## Integration Details

**Category:** CRM & Project Management
**Base URL:** https://api.clickup.com/api/v2
**Authentication:** Bearer Token
**Documentation:** https://clickup.com/api
**Special:** Webhook support for task events

## Files to Create/Modify

- [ ] `app/backend/src/integrations/clickup.py`
- [ ] `app/backend/__tests__/unit/integrations/test_clickup.py`
- [ ] `app/backend/__tests__/fixtures/clickup_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `ClickUpClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `CLICKUP_API_KEY` environment variable
- [ ] Set base URL to `https://api.clickup.com/api/v2`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_task(list_id: str, name: str, **kwargs) -> dict - Create task`
- [ ] `update_task(task_id: str, **kwargs) -> dict - Update task`
- [ ] `get_task(task_id: str) -> dict - Get task details`
- [ ] `create_checklist(task_id: str, name: str) -> dict - Add checklist`
- [ ] `add_comment(task_id: str, comment: str) -> dict - Add task comment`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `ClickUpAPIError` exception class
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
pytest __tests__/unit/integrations/test_clickup.py -v

# Check coverage
pytest --cov=src/integrations/clickup --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `CLICKUP_API_KEY`
- **Special**: Webhook support for task events
- Primary use case: Project management and task tracking for client deliveries
- See https://clickup.com/api for full API reference
