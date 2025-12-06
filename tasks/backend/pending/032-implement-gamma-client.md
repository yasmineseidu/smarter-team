# Task: Implement Gamma Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Gamma extending BaseIntegrationClient with presentation generation capabilities.

## Integration Details

**Category:** AI Services
**Base URL:** https://api.gamma.app/v1
**Authentication:** Bearer Token (API Key)
**Documentation:** https://gamma.app/docs/api
**Rate Limits:** Contact-based

## Files to Create/Modify

- [ ] `app/backend/src/integrations/gamma.py`
- [ ] `app/backend/__tests__/unit/integrations/test_gamma.py`
- [ ] `app/backend/__tests__/fixtures/gamma_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `GammaClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `GAMMA_API_KEY` environment variable
- [ ] Set base URL to `https://api.gamma.app/v1`
- [ ] Set timeout to 90.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_presentation(title: str, outline: str | list[str], theme: str = "default") -> dict` - Create presentation from outline
- [ ] `get_presentation(presentation_id: str) -> dict` - Get presentation details
- [ ] `update_presentation(presentation_id: str, **kwargs) -> dict` - Update presentation content
- [ ] `export_presentation(presentation_id: str, format: str = "pdf") -> bytes` - Export as PDF/PPTX
- [ ] `list_presentations(limit: int = 50) -> list[dict]` - List user presentations
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `GammaAPIError` exception class
- [ ] Add `GammaGenerationError` exception class for failed generations
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle generation timeouts
- [ ] Log errors with context (presentation_id, title, theme)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for create, get, export
- [ ] Test error scenarios (invalid outline, export failed)
- [ ] Test different themes and formats
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List available themes
- [ ] Note export formats (PDF, PPTX)
- [ ] Document outline structure requirements

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## API Methods to Implement

```python
async def create_presentation(
    self,
    title: str,
    outline: str | list[str],
    theme: str = "default",
    auto_design: bool = True
) -> dict[str, Any]:
    """
    Create presentation from outline.

    Args:
        title: Presentation title
        outline: Text outline or list of slide topics
        theme: Visual theme to apply
        auto_design: Enable AI design suggestions

    Returns:
        Presentation object with id and url
    """

async def export_presentation(
    self,
    presentation_id: str,
    format: str = "pdf"
) -> bytes:
    """
    Export presentation as PDF or PPTX.

    Args:
        presentation_id: Presentation ID
        format: Export format (pdf, pptx)

    Returns:
        File bytes
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_gamma.py -v

# Check coverage
pytest --cov=src/integrations/gamma --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `GAMMA_API_KEY`
- Primary use case: Meeting Prep Agent - generate slide decks 1 hour before meetings
- See https://gamma.app/docs for full API reference
