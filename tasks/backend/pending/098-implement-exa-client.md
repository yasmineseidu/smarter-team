# Task: Implement Exa Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Exa extending BaseIntegrationClient with AI-powered search capabilities.

## Integration Details

**Category:** Search & Research
**Base URL:** https://api.exa.ai
**Authentication:** Bearer Token (API Key)
**Documentation:** https://docs.exa.ai
**Rate Limits:** 1000 searches/month (free tier)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/exa.py`
- [ ] `app/backend/__tests__/unit/integrations/test_exa.py`
- [ ] `app/backend/__tests__/fixtures/exa_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `ExaClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `EXA_API_KEY` environment variable
- [ ] Set base URL to `https://api.exa.ai`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `search(query: str, use_autoprompt: bool = True, **kwargs) -> dict` - AI-powered search
- [ ] `find_similar(url: str, num_results: int = 10) -> dict` - Find similar pages
- [ ] `get_contents(ids: list[str]) -> dict` - Get full page contents
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `ExaAPIError` exception class
- [ ] Add `ExaQuotaError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle quota limits
- [ ] Log errors with context (query, num_results)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for search, find_similar, get_contents
- [ ] Test error scenarios (401, 429, quota exceeded)
- [ ] Test autoprompt vs manual queries
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] Explain autoprompt feature
- [ ] Note rate limits and quota
- [ ] Document use cases (research, similar content discovery)

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## API Methods to Implement

```python
async def search(
    self,
    query: str,
    use_autoprompt: bool = True,
    num_results: int = 10,
    start_published_date: str | None = None,
    category: str | None = None
) -> dict[str, Any]:
    """
    AI-powered semantic search.

    Args:
        query: Search query (natural language)
        use_autoprompt: Let Exa optimize the query
        num_results: Number of results (max 100)
        start_published_date: Filter by publication date (YYYY-MM-DD)
        category: Filter by category (news, research, etc.)

    Returns:
        Search results with relevance scores, summaries
    """

async def find_similar(
    self,
    url: str,
    num_results: int = 10,
    exclude_source_domain: bool = False
) -> dict[str, Any]:
    """
    Find similar pages to a URL.

    Args:
        url: Reference URL
        num_results: Number of similar results
        exclude_source_domain: Exclude pages from same domain

    Returns:
        Similar pages with similarity scores
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_exa.py -v

# Check coverage
pytest --cov=src/integrations/exa --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `EXA_API_KEY`
- Primary use case: Deep research, competitive intelligence
- See https://docs.exa.ai for full API reference
