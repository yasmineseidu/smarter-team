# Task: Implement Rube MCP Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Rube MCP extending BaseIntegrationClient with Workflow automation and MCP server integration.

## Integration Details

**Category:** MCP Servers
**Base URL:** https://api.rube.ai/v1
**Authentication:** Bearer Token
**Documentation:** https://docs.rube.ai
**Special:** Requires RUBE_MCP_URL

## Files to Create/Modify

- [ ] `app/backend/src/integrations/rube_mcp.py`
- [ ] `app/backend/__tests__/unit/integrations/test_rube_mcp.py`
- [ ] `app/backend/__tests__/fixtures/rube_mcp_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `RubeMCPClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `RUBE_MCP_API_KEY` environment variable
- [ ] Set base URL to `https://api.rube.ai/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_workflow(name: str, steps: list[dict]) -> dict - Create automation workflow`
- [ ] `execute_workflow(workflow_id: str, input_data: dict) -> dict - Execute workflow`
- [ ] `get_workflow_status(execution_id: str) -> dict - Check workflow status`
- [ ] `list_workflows() -> list[dict] - List available workflows`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `RubeMCPAPIError` exception class
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
pytest __tests__/unit/integrations/test_rube_mcp.py -v

# Check coverage
pytest --cov=src/integrations/rube_mcp --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `RUBE_MCP_API_KEY`
- **Special**: Requires RUBE_MCP_URL
- Primary use case: Workflow automation and MCP server integration
- See https://docs.rube.ai for full API reference
