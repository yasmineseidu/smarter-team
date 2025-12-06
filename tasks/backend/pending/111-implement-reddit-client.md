# Task: Implement Reddit Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Reddit extending BaseIntegrationClient with subreddit and post research capabilities.

## Integration Details

**Category:** Search & Research
**Base URL:** https://oauth.reddit.com
**Authentication:** OAuth 2.0 (Client Credentials)
**Documentation:** https://www.reddit.com/dev/api
**Rate Limits:** 60 requests/minute

## Files to Create/Modify

- [ ] `app/backend/src/integrations/reddit.py`
- [ ] `app/backend/__tests__/unit/integrations/test_reddit.py`
- [ ] `app/backend/__tests__/fixtures/reddit_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `RedditClient` class extending `BaseIntegrationClient`
- [ ] Initialize with credentials from `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`
- [ ] Set base URL to `https://oauth.reddit.com`
- [ ] Implement OAuth 2.0 client credentials flow
- [ ] Add access token management with auto-refresh
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `search_posts(query: str, subreddit: str | None = None, **kwargs) -> dict` - Search posts
- [ ] `get_subreddit_posts(subreddit: str, sort: str = "hot", **kwargs) -> dict` - Get subreddit posts
- [ ] `get_post_comments(post_id: str, sort: str = "best") -> dict` - Get post comments
- [ ] `search_subreddits(query: str) -> dict` - Search subreddits
- [ ] `get_subreddit_info(subreddit: str) -> dict` - Get subreddit details
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `RedditAPIError` exception class
- [ ] Add `RedditAuthError` exception class for OAuth failures
- [ ] Add `RedditRateLimitError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting (60 requests/minute)
- [ ] Auto-refresh access tokens on expiry
- [ ] Log errors with context (subreddit, query, post_id)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock OAuth token flow
- [ ] Mock API responses for posts, comments, subreddits
- [ ] Test error scenarios (401, 429, invalid subreddit)
- [ ] Test token refresh logic
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document OAuth setup process
- [ ] List sort options (hot, new, top, rising, controversial)
- [ ] Note rate limits (60 req/min)
- [ ] Document user agent requirements

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## API Methods to Implement

```python
async def authenticate(self) -> str:
    """
    Obtain OAuth access token using client credentials.

    Returns:
        Access token string
    """

async def search_posts(
    self,
    query: str,
    subreddit: str | None = None,
    time_filter: str = "all",
    sort: str = "relevance",
    limit: int = 25
) -> dict[str, Any]:
    """
    Search Reddit posts.

    Args:
        query: Search query
        subreddit: Limit to specific subreddit
        time_filter: Time filter (hour, day, week, month, year, all)
        sort: Sort order (relevance, hot, top, new)
        limit: Number of results (max 100)

    Returns:
        Matching posts with metadata
    """

async def get_subreddit_posts(
    self,
    subreddit: str,
    sort: str = "hot",
    time_filter: str = "day",
    limit: int = 25
) -> dict[str, Any]:
    """
    Get posts from subreddit.

    Args:
        subreddit: Subreddit name (without r/)
        sort: Sort order (hot, new, top, rising)
        time_filter: Time filter (for top sort)
        limit: Number of posts

    Returns:
        Subreddit posts
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_reddit.py -v

# Check coverage
pytest --cov=src/integrations/reddit --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- Credentials loaded from environment: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`
- **Special**: Requires OAuth 2.0 client credentials flow
- **Special**: Requires unique User-Agent header
- Primary use case: Pain point research, niche discovery
- See https://www.reddit.com/dev/api for full API reference
