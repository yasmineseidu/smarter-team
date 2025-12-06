# Task: Implement DeepSeek Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for DeepSeek extending BaseIntegrationClient with code-focused AI capabilities.

## Integration Details

**Category:** AI Services
**Base URL:** https://api.deepseek.com/v1
**Authentication:** Bearer Token (API Key)
**Documentation:** https://platform.deepseek.com/docs
**Rate Limits:** Tier-based

## Files to Create/Modify

- [ ] `app/backend/src/integrations/deepseek.py`
- [ ] `app/backend/__tests__/unit/integrations/test_deepseek.py`
- [ ] `app/backend/__tests__/fixtures/deepseek_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `DeepSeekClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `DEEPSEEK_API_KEY` environment variable
- [ ] Set base URL to `https://api.deepseek.com/v1`
- [ ] Set timeout to 60.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `chat_completion(messages: list[dict], model: str = "deepseek-chat", **kwargs) -> dict` - Chat completions
- [ ] `code_completion(prompt: str, model: str = "deepseek-coder") -> dict` - Code-specific completions
- [ ] `list_models() -> list[dict]` - List available models
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `DeepSeekAPIError` exception class
- [ ] Add `DeepSeekRateLimitError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting
- [ ] Log errors with context (model, tokens)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for chat and code completions
- [ ] Test error scenarios (401, 429, invalid request)
- [ ] Test different models
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List available models (deepseek-chat, deepseek-coder)
- [ ] Note code-specific capabilities
- [ ] Document use cases

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
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int | None = None
) -> dict[str, Any]:
    """
    Create chat completion.

    Args:
        messages: List of message dicts
        model: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens

    Returns:
        Completion response
    """

async def code_completion(
    self,
    prompt: str,
    model: str = "deepseek-coder",
    language: str | None = None
) -> dict[str, Any]:
    """
    Generate code completion.

    Args:
        prompt: Code prompt or context
        model: Code model to use
        language: Programming language hint

    Returns:
        Code completion response
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_deepseek.py -v

# Check coverage
pytest --cov=src/integrations/deepseek --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `DEEPSEEK_API_KEY`
- Primary use case: Code generation and analysis tasks
- See https://platform.deepseek.com/docs for full API reference
