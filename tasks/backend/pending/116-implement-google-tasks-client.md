# Task: Implement Google Tasks Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Google Tasks extending BaseIntegrationClient with Task management and to-do lists.

## Integration Details

**Category:** Communication & Scheduling
**Base URL:** https://tasks.googleapis.com/tasks/v1
**Authentication:** OAuth 2.0 (Google)
**Documentation:** https://developers.google.com/tasks
**Special:** OAuth 2.0 with refresh tokens

## Files to Create/Modify

- [ ] `app/backend/src/integrations/google_tasks.py`
- [ ] `app/backend/__tests__/unit/integrations/test_google_tasks.py`
- [ ] `app/backend/__tests__/fixtures/google_tasks_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `GoogleTasksClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `GOOGLE_TASKS_CREDENTIALS_JSON` environment variable
- [ ] Set base URL to `https://tasks.googleapis.com/tasks/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `list_tasks(tasklist_id: str = '@default') -> list[dict] - List tasks`
- [ ] `create_task(tasklist_id: str, title: str, **kwargs) -> dict - Create task`
- [ ] `update_task(tasklist_id: str, task_id: str, **kwargs) -> dict - Update task`
- [ ] `delete_task(tasklist_id: str, task_id: str) -> dict - Delete task`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `GoogleTasksAPIError` exception class
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
pytest __tests__/unit/integrations/test_google_tasks.py -v

# Check coverage
pytest --cov=src/integrations/google_tasks --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `GOOGLE_TASKS_CREDENTIALS_JSON`
- **Special**: OAuth 2.0 with refresh tokens
- Primary use case: Task management and to-do lists
- See https://developers.google.com/tasks for full API reference
