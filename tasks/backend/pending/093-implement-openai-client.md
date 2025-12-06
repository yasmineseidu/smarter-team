# Task: Implement OpenAI Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for OpenAI extending BaseIntegrationClient with GPT models, embeddings, and completions.

## Integration Details

**Category:** AI Services
**Base URL:** https://api.openai.com/v1
**Authentication:** Bearer Token (API Key)
**Documentation:** https://platform.openai.com/docs/api-reference
**Rate Limits:** Tier-based (RPM and TPM limits)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/openai.py`
- [ ] `app/backend/__tests__/unit/integrations/test_openai.py`
- [ ] `app/backend/__tests__/fixtures/openai_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `OpenAIClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `OPENAI_API_KEY` environment variable
- [ ] Set base URL to `https://api.openai.com/v1`
- [ ] Set timeout to 60.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `chat_completion(messages: list[dict], model: str = "gpt-4o", **kwargs) -> dict` - Chat completions
- [ ] `create_embedding(text: str | list[str], model: str = "text-embedding-3-small") -> dict` - Generate embeddings
- [ ] `create_moderation(text: str) -> dict` - Content moderation
- [ ] `list_models() -> list[dict]` - List available models
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `OpenAIAPIError` exception class
- [ ] Add `OpenAIRateLimitError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting with exponential backoff
- [ ] Log errors with context (model, tokens, error_type)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for chat, embeddings, moderation
- [ ] Test error scenarios (401, 429, invalid request)
- [ ] Test different models and parameters
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List available models (gpt-4o, gpt-4-turbo, gpt-3.5-turbo)
- [ ] Note rate limits by tier
- [ ] Document token counting best practices

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## API Methods to Implement

```python
async def chat_completion(
    self,
    messages: list[dict[str, str]],
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int | None = None,
    response_format: dict[str, str] | None = None
) -> dict[str, Any]:
    """
    Create chat completion.

    Args:
        messages: List of message dicts with role and content
        model: Model to use
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens in response
        response_format: Force JSON output

    Returns:
        Completion response with choices
    """

async def create_embedding(
    self,
    text: str | list[str],
    model: str = "text-embedding-3-small"
) -> dict[str, Any]:
    """
    Generate embeddings for text.

    Args:
        text: Text string or list of strings
        model: Embedding model to use

    Returns:
        Embedding vectors
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_openai.py -v

# Check coverage
pytest --cov=src/integrations/openai --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `OPENAI_API_KEY`
- Primary use case: Fallback AI model when Claude is rate-limited
- See https://platform.openai.com/docs for full API reference
