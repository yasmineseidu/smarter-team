# Task: Implement News API Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for News API extending BaseIntegrationClient with news article search capabilities.

## Integration Details

**Category:** Search & Research
**Base URL:** https://newsapi.org/v2
**Authentication:** API Key (X-Api-Key header or apiKey param)
**Documentation:** https://newsapi.org/docs
**Rate Limits:** 100 requests/day (developer tier)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/newsapi.py`
- [ ] `app/backend/__tests__/unit/integrations/test_newsapi.py`
- [ ] `app/backend/__tests__/fixtures/newsapi_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `NewsAPIClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `NEWS_API_KEY` environment variable
- [ ] Set base URL to `https://newsapi.org/v2`
- [ ] Override `client` property to use `X-Api-Key` header
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `get_top_headlines(country: str = "us", category: str | None = None, **kwargs) -> dict` - Top headlines
- [ ] `search_everything(query: str, **kwargs) -> dict` - Search all articles
- [ ] `get_sources(category: str | None = None, language: str = "en") -> dict` - Get news sources
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `NewsAPIError` exception class
- [ ] Add `NewsAPIRateLimitError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting (100 requests/day)
- [ ] Log errors with context (query, country, category)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for headlines, search, sources
- [ ] Test error scenarios (401, 429, invalid parameters)
- [ ] Test pagination
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup (X-Api-Key header)
- [ ] List available categories (business, entertainment, health, science, sports, technology)
- [ ] Note rate limits (100 req/day developer, unlimited with paid)
- [ ] Document date range filtering

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## API Methods to Implement

```python
async def get_top_headlines(
    self,
    country: str = "us",
    category: str | None = None,
    query: str | None = None,
    page_size: int = 20
) -> dict[str, Any]:
    """
    Get top headlines.

    Args:
        country: Country code (us, gb, etc.)
        category: News category (business, tech, etc.)
        query: Search query within headlines
        page_size: Number of results (max 100)

    Returns:
        Top headlines with articles
    """

async def search_everything(
    self,
    query: str,
    from_date: str | None = None,
    to_date: str | None = None,
    language: str = "en",
    sort_by: str = "relevancy",
    page_size: int = 20
) -> dict[str, Any]:
    """
    Search all news articles.

    Args:
        query: Search keywords
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        language: Language code
        sort_by: Sort order (relevancy, popularity, publishedAt)
        page_size: Number of results

    Returns:
        Matching articles with metadata
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_newsapi.py -v

# Check coverage
pytest --cov=src/integrations/newsapi --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `NEWS_API_KEY`
- **Special**: Uses `X-Api-Key` header instead of `Authorization: Bearer`
- Primary use case: Industry news monitoring, trend detection
- See https://newsapi.org/docs for full API reference
