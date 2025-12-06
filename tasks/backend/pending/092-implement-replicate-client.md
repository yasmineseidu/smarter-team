# Task: Implement Replicate Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Replicate extending BaseIntegrationClient with ML model inference capabilities.

## Integration Details

**Category:** AI Services
**Base URL:** https://api.replicate.com/v1
**Authentication:** Bearer Token (API Key)
**Documentation:** https://replicate.com/docs/reference/http
**Rate Limits:** 5000 requests/hour (free tier)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/replicate.py`
- [ ] `app/backend/__tests__/unit/integrations/test_replicate.py`
- [ ] `app/backend/__tests__/fixtures/replicate_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `ReplicateClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `REPLICATE_API_KEY` environment variable
- [ ] Set base URL to `https://api.replicate.com/v1`
- [ ] Set timeout to 120.0 seconds (longer for model inference)
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `run_prediction(model: str, input_data: dict, version: str | None = None) -> dict` - Run model prediction
- [ ] `get_prediction(prediction_id: str) -> dict` - Get prediction status
- [ ] `cancel_prediction(prediction_id: str) -> dict` - Cancel running prediction
- [ ] `list_predictions(limit: int = 100) -> list[dict]` - List recent predictions
- [ ] `get_model(owner: str, name: str) -> dict` - Get model details
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `ReplicateAPIError` exception class
- [ ] Add `ReplicatePredictionError` exception class for failed predictions
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle long-running predictions with polling
- [ ] Log errors with context (model, prediction_id, input)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for predictions, models
- [ ] Test error scenarios (invalid model, prediction failed, timeout)
- [ ] Test polling for async predictions
- [ ] Test different model types (image, text, audio)
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List popular models (SDXL, Whisper, LLaMA, etc.)
- [ ] Note prediction statuses (starting, processing, succeeded, failed)
- [ ] Document webhook support for async predictions

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test with simple model)

## API Methods to Implement

```python
async def run_prediction(
    self,
    model: str,
    input_data: dict[str, Any],
    version: str | None = None,
    webhook: str | None = None
) -> dict[str, Any]:
    """
    Run a model prediction.

    Args:
        model: Model identifier (owner/name or owner/name:version)
        input_data: Input parameters for the model
        version: Specific model version (optional)
        webhook: Webhook URL for async completion

    Returns:
        Prediction object with id and status
    """

async def get_prediction(self, prediction_id: str) -> dict[str, Any]:
    """
    Get prediction status and output.

    Args:
        prediction_id: Prediction ID

    Returns:
        Prediction object with status, output, error
    """

async def wait_for_prediction(
    self,
    prediction_id: str,
    max_wait: int = 300,
    poll_interval: int = 1
) -> dict[str, Any]:
    """
    Wait for prediction to complete.

    Args:
        prediction_id: Prediction ID
        max_wait: Maximum wait time in seconds
        poll_interval: Seconds between status checks

    Returns:
        Completed prediction object

    Raises:
        TimeoutError: If prediction doesn't complete in time
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_replicate.py -v

# Check coverage
pytest --cov=src/integrations/replicate --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `REPLICATE_API_KEY`
- See https://replicate.com/docs for full API reference
- Primary use case: Run various ML models (image gen, transcription, embeddings)
- Predictions are async - poll status or use webhooks
- Popular models: stability-ai/sdxl, openai/whisper, meta/llama-2
