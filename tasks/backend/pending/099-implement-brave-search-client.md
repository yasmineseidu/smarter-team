# Task: Implement Brave Search Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Brave Search extending BaseIntegrationClient with privacy-focused search capabilities.

## Integration Details

**Category:** Search & Research
**Base URL:** https://api.search.brave.com/res/v1
**Authentication:** API Key (X-Subscription-Token header)
**Documentation:** https://brave.com/search/api/
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/brave_search.py`
- [ ] `app/backend/__tests__/unit/integrations/test_brave_search.py`
- [ ] `app/backend/__tests__/fixtures/brave_search_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `BraveSearchClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `BRAVE_API_KEY` environment variable
- [ ] Set base URL to `https://api.search.brave.com/res/v1`
- [ ] Override `client` property to use `X-Subscription-Token` header
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `web_search(query: str, **kwargs) -> dict` - Web search
- [ ] `news_search(query: str, **kwargs) -> dict` - News search
- [ ] `image_search(query: str, **kwargs) -> dict` - Image search
- [ ] `video_search(query: str, **kwargs) -> dict` - Video search
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `BraveSearchAPIError` exception class
- [ ] Add `BraveSearchRateLimitError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting
- [ ] Log errors with context (query, search_type)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for different search types
- [ ] Test error scenarios (401, 429, invalid query)
- [ ] Test pagination
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup (X-Subscription-Token header)
- [ ] List search types (web, news, images, videos)
- [ ] Note rate limits by plan
- [ ] Document privacy features

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## API Methods to Implement

```python
async def web_search(
    self,
    query: str,
    count: int = 10,
    offset: int = 0,
    country: str = "us",
    freshness: str | None = None
) -> dict[str, Any]:
    """
    Perform web search.

    Args:
        query: Search query
        count: Number of results (max 20)
        offset: Pagination offset
        country: Country code
        freshness: Time filter (day, week, month, year)

    Returns:
        Web search results
    """

async def news_search(
    self,
    query: str,
    count: int = 10,
    freshness: str | None = None
) -> dict[str, Any]:
    """
    Search news articles.

    Args:
        query: News query
        count: Number of results
        freshness: Time filter

    Returns:
        News articles with metadata
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_brave_search.py -v

# Check coverage
pytest --cov=src/integrations/brave_search --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `BRAVE_API_KEY`
- **Special**: Uses `X-Subscription-Token` header instead of `Authorization: Bearer`
- Primary use case: Privacy-focused search alternative
- See https://brave.com/search/api/ for full API reference
