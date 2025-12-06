# Task: Implement Google Gemini Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Google Gemini extending BaseIntegrationClient with multimodal AI capabilities.

## Integration Details

**Category:** AI Services
**Base URL:** https://generativelanguage.googleapis.com/v1beta
**Authentication:** API Key (query parameter)
**Documentation:** https://ai.google.dev/docs
**Rate Limits:** 60 requests/minute (free tier)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/gemini.py`
- [ ] `app/backend/__tests__/unit/integrations/test_gemini.py`
- [ ] `app/backend/__tests__/fixtures/gemini_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `GeminiClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `GEMINI_API_KEY` environment variable
- [ ] Set base URL to `https://generativelanguage.googleapis.com/v1beta`
- [ ] Override `_request` to add API key as query parameter
- [ ] Set timeout to 60.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `generate_content(prompt: str, model: str = "gemini-1.5-pro", **kwargs) -> dict` - Generate text content
- [ ] `chat(messages: list[dict], model: str = "gemini-1.5-pro") -> dict` - Chat completions
- [ ] `count_tokens(text: str, model: str = "gemini-1.5-pro") -> dict` - Count tokens
- [ ] `list_models() -> list[dict]` - List available models
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `GeminiAPIError` exception class
- [ ] Add `GeminiRateLimitError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting (60 RPM)
- [ ] Log errors with context (model, prompt_length)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for content generation, chat
- [ ] Test error scenarios (401, 429, invalid request)
- [ ] Test different models
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup (API key in query param)
- [ ] List available models (gemini-1.5-pro, gemini-1.5-flash)
- [ ] Note rate limits
- [ ] Document multimodal capabilities (text, image, video)

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## API Methods to Implement

```python
async def generate_content(
    self,
    prompt: str,
    model: str = "gemini-1.5-pro",
    temperature: float = 0.7,
    max_tokens: int | None = None
) -> dict[str, Any]:
    """
    Generate content from prompt.

    Args:
        prompt: Text prompt
        model: Model to use
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response

    Returns:
        Generated content response
    """

async def chat(
    self,
    messages: list[dict[str, str]],
    model: str = "gemini-1.5-pro"
) -> dict[str, Any]:
    """
    Chat with message history.

    Args:
        messages: List of message dicts
        model: Model to use

    Returns:
        Chat response
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_gemini.py -v

# Check coverage
pytest --cov=src/integrations/gemini --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `GEMINI_API_KEY`
- **Special**: API key passed as query parameter `?key=...` instead of header
- Primary use case: Alternative AI model for specific use cases
- See https://ai.google.dev/docs for full API reference
