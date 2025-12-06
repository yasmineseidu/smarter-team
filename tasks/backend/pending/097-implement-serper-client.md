# Task: Implement Serper Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Serper extending BaseIntegrationClient with Google Search API capabilities.

## Integration Details

**Category:** Search & Research
**Base URL:** https://google.serper.dev
**Authentication:** API Key (X-API-KEY header)
**Documentation:** https://serper.dev/docs
**Rate Limits:** 2500 searches/month (free tier), 1 req/sec

## Files to Create/Modify

- [ ] `app/backend/src/integrations/serper.py`
- [ ] `app/backend/__tests__/unit/integrations/test_serper.py`
- [ ] `app/backend/__tests__/fixtures/serper_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `SerperClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `SERPER_API_KEY` environment variable
- [ ] Set base URL to `https://google.serper.dev`
- [ ] Override `client` property to use `X-API-KEY` header instead of `Authorization`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `search(query: str, search_type: str = "search", **kwargs) -> dict` - General search
- [ ] `news_search(query: str, **kwargs) -> dict` - News-specific search
- [ ] `image_search(query: str, **kwargs) -> dict` - Image search
- [ ] `places_search(query: str, **kwargs) -> dict` - Google Places search
- [ ] `shopping_search(query: str, **kwargs) -> dict` - Shopping results
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `SerperAPIError` exception class
- [ ] Add `SerperQuotaError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting (1 req/sec)
- [ ] Log errors with context (query, search_type)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for different search types
- [ ] Test error scenarios (401, 429, quota exceeded)
- [ ] Test pagination
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup (X-API-KEY header)
- [ ] List search types (search, news, images, places, shopping)
- [ ] Note rate limits and quota
- [ ] Document result structure

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
    search_type: str = "search",
    num_results: int = 10,
    location: str | None = None,
    gl: str = "us"
) -> dict[str, Any]:
    """
    Perform Google search.

    Args:
        query: Search query
        search_type: Type of search (search, news, images, places, shopping)
        num_results: Number of results (max 100)
        location: Geographic location
        gl: Country code

    Returns:
        Search results with organic, knowledge graph, related searches
    """

async def news_search(
    self,
    query: str,
    num_results: int = 10
) -> dict[str, Any]:
    """
    Search Google News.

    Args:
        query: News query
        num_results: Number of results

    Returns:
        News articles with titles, links, snippets, dates
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_serper.py -v

# Check coverage
pytest --cov=src/integrations/serper --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `SERPER_API_KEY`
- **Special**: Uses `X-API-KEY` header instead of `Authorization: Bearer`
- Primary use case: Company research, competitor analysis
- See https://serper.dev/docs for full API reference
