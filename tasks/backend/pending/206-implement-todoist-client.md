# Task: Implement Todoist Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Todoist extending BaseIntegrationClient with Task management for internal workflows.

## Integration Details

**Category:** CRM & Project Management
**Base URL:** https://api.todoist.com/rest/v2
**Authentication:** Bearer Token
**Documentation:** https://developer.todoist.com/rest/v2
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/todoist.py`
- [ ] `app/backend/__tests__/unit/integrations/test_todoist.py`
- [ ] `app/backend/__tests__/fixtures/todoist_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `TodoistClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `TODOIST_API_KEY` environment variable
- [ ] Set base URL to `https://api.todoist.com/rest/v2`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `get_tasks(filter: str | None = None) -> list[dict] - Get tasks`
- [ ] `create_task(content: str, **kwargs) -> dict - Create task`
- [ ] `update_task(task_id: str, **kwargs) -> dict - Update task`
- [ ] `close_task(task_id: str) -> dict - Complete task`
- [ ] `get_projects() -> list[dict] - List projects`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `TodoistAPIError` exception class
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
pytest __tests__/unit/integrations/test_todoist.py -v

# Check coverage
pytest --cov=src/integrations/todoist --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `TODOIST_API_KEY`

- Primary use case: Task management for internal workflows
- See https://developer.todoist.com/rest/v2 for full API reference
