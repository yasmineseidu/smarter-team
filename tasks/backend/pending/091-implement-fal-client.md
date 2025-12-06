# Task: Implement Fal AI Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Fal AI extending BaseIntegrationClient with image and video generation capabilities.

## Integration Details

**Category:** AI Services
**Base URL:** https://fal.run
**Authentication:** API Key (Key header)
**Documentation:** https://fal.ai/docs
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/fal_ai.py`
- [ ] `app/backend/__tests__/unit/integrations/test_fal_ai.py`
- [ ] `app/backend/__tests__/fixtures/fal_ai_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `FalAIClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `FAL_API_KEY` environment variable
- [ ] Set base URL to `https://fal.run`
- [ ] Set timeout to 120.0 seconds (longer for image/video generation)
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `generate_image(prompt: str, model: str = "fal-ai/flux/schnell", **kwargs) -> dict` - Generate image
- [ ] `generate_video(prompt: str, model: str = "fal-ai/stable-video", **kwargs) -> dict` - Generate video
- [ ] `upscale_image(image_url: str, scale: int = 2) -> dict` - Upscale image
- [ ] `get_status(request_id: str) -> dict` - Check generation status
- [ ] `get_result(request_id: str) -> dict` - Get completed result
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `FalAIError` exception class
- [ ] Add `FalAIGenerationError` exception class for failed generations
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle long-running generation with polling
- [ ] Log errors with context (prompt, model, request_id)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for image/video generation
- [ ] Test error scenarios (invalid prompt, timeout, quota exceeded)
- [ ] Test polling for long-running generations
- [ ] Test different models
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List available models (FLUX, Stable Video, etc.)
- [ ] Note generation time estimates
- [ ] Document image/video format options

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test with simple prompt)

## API Methods to Implement

```python
async def generate_image(
    self,
    prompt: str,
    model: str = "fal-ai/flux/schnell",
    width: int = 1024,
    height: int = 1024,
    num_images: int = 1,
    seed: int | None = None
) -> dict[str, Any]:
    """
    Generate image from text prompt.

    Args:
        prompt: Text description of image
        model: Model to use (flux/schnell, flux/dev, stable-diffusion)
        width: Image width in pixels
        height: Image height in pixels
        num_images: Number of images to generate
        seed: Random seed for reproducibility

    Returns:
        Result with image URLs
    """

async def generate_video(
    self,
    prompt: str,
    model: str = "fal-ai/stable-video",
    duration: int = 3,
    fps: int = 24
) -> dict[str, Any]:
    """
    Generate video from text prompt.

    Args:
        prompt: Text description of video
        model: Model to use
        duration: Video duration in seconds
        fps: Frames per second

    Returns:
        Result with video URL
    """

async def get_status(self, request_id: str) -> dict[str, Any]:
    """
    Check generation status.

    Args:
        request_id: Request ID from generation call

    Returns:
        Status object (queued, processing, completed, failed)
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_fal_ai.py -v

# Check coverage
pytest --cov=src/integrations/fal_ai --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `FAL_API_KEY`
- See https://fal.ai/docs for full API reference
- Primary use case: Generate visuals for presentations and marketing materials
- Generation is async - use polling to check status
- Image formats: PNG, JPEG, WebP
