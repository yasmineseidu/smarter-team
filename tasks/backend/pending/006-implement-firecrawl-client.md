# Task: Implement Firecrawl Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Firecrawl extending BaseIntegrationClient with web scraping and crawling capabilities.

## Integration Details

**Category:** Search & Research
**Base URL:** https://api.firecrawl.dev/v1
**Authentication:** Bearer Token (API Key)
**Documentation:** https://docs.firecrawl.dev
**Rate Limits:** 500 pages/month (free tier)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/firecrawl.py`
- [ ] `app/backend/__tests__/unit/integrations/test_firecrawl.py`
- [ ] `app/backend/__tests__/fixtures/firecrawl_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `FirecrawlClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `FIRECRAWL_API_KEY` environment variable
- [ ] Set base URL to `https://api.firecrawl.dev/v1`
- [ ] Set timeout to 60.0 seconds (longer for crawling)
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `scrape_url(url: str, formats: list[str] = ["markdown"], **kwargs) -> dict` - Scrape single page
- [ ] `crawl_website(url: str, max_depth: int = 2, **kwargs) -> dict` - Crawl entire website
- [ ] `get_crawl_status(job_id: str) -> dict` - Check crawl job status
- [ ] `map_website(url: str) -> dict` - Get sitemap structure
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `FirecrawlAPIError` exception class
- [ ] Add `FirecrawlQuotaError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle long-running crawl jobs with polling
- [ ] Log errors with context (url, job_id)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for scrape, crawl, status
- [ ] Test error scenarios (invalid URL, quota exceeded, timeout)
- [ ] Test different output formats (markdown, html, structured)
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List output formats (markdown, html, structured, screenshot)
- [ ] Note rate limits and quota
- [ ] Document crawling best practices

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test with simple URL)

## API Methods to Implement

```python
async def scrape_url(
    self,
    url: str,
    formats: list[str] = ["markdown"],
    include_tags: list[str] | None = None,
    exclude_tags: list[str] | None = None,
    wait_for: int | None = None
) -> dict[str, Any]:
    """
    Scrape a single URL.

    Args:
        url: URL to scrape
        formats: Output formats (markdown, html, structured, screenshot)
        include_tags: HTML tags to include
        exclude_tags: HTML tags to exclude
        wait_for: Milliseconds to wait for JS rendering

    Returns:
        Scraped content in requested formats
    """

async def crawl_website(
    self,
    url: str,
    max_depth: int = 2,
    limit: int = 100,
    formats: list[str] = ["markdown"]
) -> dict[str, Any]:
    """
    Crawl entire website.

    Args:
        url: Starting URL
        max_depth: Maximum crawl depth
        limit: Maximum number of pages
        formats: Output formats

    Returns:
        Crawl job with job_id for status tracking
    """

async def get_crawl_status(self, job_id: str) -> dict[str, Any]:
    """
    Check crawl job status.

    Args:
        job_id: Crawl job ID

    Returns:
        Job status (queued, processing, completed, failed)
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_firecrawl.py -v

# Check coverage
pytest --cov=src/integrations/firecrawl --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `FIRECRAWL_API_KEY`
- Primary use case: Scrape competitor websites, extract company info
- See https://docs.firecrawl.dev for full API reference
- Crawling is async - use polling to check job status
