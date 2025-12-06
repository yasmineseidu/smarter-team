# Task: Implement Perplexity Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Perplexity AI extending BaseIntegrationClient with research and search capabilities.

## Integration Details

**Category:** AI Services
**Base URL:** https://api.perplexity.ai
**Authentication:** Bearer Token (API Key)
**Documentation:** https://docs.perplexity.ai
**Rate Limits:** Varies by plan (typically 50 requests/minute)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/perplexity.py`
- [ ] `app/backend/__tests__/unit/integrations/test_perplexity.py`
- [ ] `app/backend/__tests__/fixtures/perplexity_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `PerplexityClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `PERPLEXITY_API_KEY` environment variable
- [ ] Set base URL to `https://api.perplexity.ai`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging via `get_agent_logger("integration.perplexity")`

### Phase 2: Core Methods
- [ ] `search(query: str, search_domain: str = "web") -> dict` - Perform research search
- [ ] `ask(question: str, context: str | None = None) -> dict` - Ask question with optional context
- [ ] `chat_completion(messages: list[dict], model: str = "sonar-medium-online") -> dict` - Chat-based completion
- [ ] `streaming_search(query: str) -> AsyncIterator[dict]` - Streaming search responses
- [ ] Add request/response type hints
- [ ] Include docstrings with examples
- [ ] Handle pagination for multi-page results

### Phase 3: Error Handling
- [ ] Add `PerplexityAPIError` exception class
- [ ] Add `PerplexityRateLimitError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting with exponential backoff
- [ ] Log errors with context (query, model, status code)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for search, ask, chat_completion
- [ ] Test error scenarios (401, 429, 500)
- [ ] Test rate limiting behavior
- [ ] Test streaming responses
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List all available models (sonar-small, sonar-medium, sonar-large)
- [ ] Note rate limits and best practices
- [ ] Document streaming vs non-streaming usage

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test with sample query)

## API Methods to Implement

```python
async def search(
    self,
    query: str,
    search_domain: str = "web",
    return_related_questions: bool = False
) -> dict[str, Any]:
    """
    Perform a research search query.

    Args:
        query: Search query string
        search_domain: Domain to search (web, news, academic)
        return_related_questions: Include related questions in response

    Returns:
        Search results with citations
    """

async def ask(
    self,
    question: str,
    context: str | None = None,
    model: str = "sonar-medium-online"
) -> dict[str, Any]:
    """
    Ask a question with optional context.

    Args:
        question: Question to ask
        context: Additional context for the question
        model: Model to use for response

    Returns:
        Answer with citations
    """

async def chat_completion(
    self,
    messages: list[dict[str, str]],
    model: str = "sonar-medium-online",
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> dict[str, Any]:
    """
    Chat-based completion with message history.

    Args:
        messages: List of message dicts with "role" and "content"
        model: Model to use
        temperature: Response randomness (0-1)
        max_tokens: Maximum tokens in response

    Returns:
        Completion response
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_perplexity.py -v

# Check coverage
pytest --cov=src/integrations/perplexity --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `PERPLEXITY_API_KEY`
- See https://docs.perplexity.ai for full API reference
- Primary use case: Research Agent for market/competitor intelligence
- Supports online and offline models (online for real-time data)
