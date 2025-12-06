# Task: Implement OpenRouter Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for OpenRouter extending BaseIntegrationClient with multi-model gateway access.

## Integration Details

**Category:** AI Services
**Base URL:** https://openrouter.ai/api/v1
**Authentication:** Bearer Token (API Key)
**Documentation:** https://openrouter.ai/docs
**Rate Limits:** Model-dependent

## Files to Create/Modify

- [ ] `app/backend/src/integrations/openrouter.py`
- [ ] `app/backend/__tests__/unit/integrations/test_openrouter.py`
- [ ] `app/backend/__tests__/fixtures/openrouter_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `OpenRouterClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `OPENROUTER_API_KEY` environment variable
- [ ] Set base URL to `https://openrouter.ai/api/v1`
- [ ] Add `HTTP-Referer` and `X-Title` headers for app identification
- [ ] Set timeout to 60.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `chat_completion(messages: list[dict], model: str, **kwargs) -> dict` - Chat completions with any model
- [ ] `list_models() -> list[dict]` - List available models across providers
- [ ] `get_model(model_id: str) -> dict` - Get model details and pricing
- [ ] `get_usage() -> dict` - Get API usage and credits
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `OpenRouterAPIError` exception class
- [ ] Add `OpenRouterModelError` exception class for unsupported models
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle model-specific rate limits
- [ ] Log errors with context (model, provider, cost)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for chat completions, models
- [ ] Test error scenarios (model not found, insufficient credits)
- [ ] Test different providers (Anthropic, OpenAI, Google, etc.)
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List popular models (claude-3, gpt-4, llama-3, etc.)
- [ ] Note pricing varies by model/provider
- [ ] Document provider fallback capabilities

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
    model: str,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    provider: str | None = None
) -> dict[str, Any]:
    """
    Create chat completion with any model.

    Args:
        messages: List of message dicts
        model: Model ID (e.g., anthropic/claude-3-opus)
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        provider: Specific provider to use

    Returns:
        Completion response with usage/cost info
    """

async def list_models(
    self,
    supported_parameters: list[str] | None = None
) -> list[dict[str, Any]]:
    """
    List available models across providers.

    Args:
        supported_parameters: Filter by supported params

    Returns:
        List of models with pricing and capabilities
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_openrouter.py -v

# Check coverage
pytest --cov=src/integrations/openrouter --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `OPENROUTER_API_KEY`
- **Special**: Requires `HTTP-Referer` and `X-Title` headers for app identification
- Primary use case: Access multiple AI providers through single API
- See https://openrouter.ai/docs for full API reference
