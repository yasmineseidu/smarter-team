# Task: Implement ElevenLabs Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for ElevenLabs extending BaseIntegrationClient with voice synthesis and text-to-speech capabilities.

## Integration Details

**Category:** AI Services
**Base URL:** https://api.elevenlabs.io/v1
**Authentication:** API Key (xi-api-key header)
**Documentation:** https://docs.elevenlabs.io
**Rate Limits:** Varies by plan (character limits per month)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/elevenlabs.py`
- [ ] `app/backend/__tests__/unit/integrations/test_elevenlabs.py`
- [ ] `app/backend/__tests__/fixtures/elevenlabs_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `ElevenLabsClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `ELEVENLABS_API_KEY` environment variable
- [ ] Set base URL to `https://api.elevenlabs.io/v1`
- [ ] Override `client` property to use `xi-api-key` header instead of `Authorization`
- [ ] Set timeout to 60.0 seconds (longer for audio generation)
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `text_to_speech(text: str, voice_id: str, model_id: str = "eleven_monolingual_v1") -> bytes` - Generate speech audio
- [ ] `get_voices() -> list[dict]` - List available voices
- [ ] `get_voice(voice_id: str) -> dict` - Get voice details
- [ ] `stream_text_to_speech(text: str, voice_id: str) -> AsyncIterator[bytes]` - Streaming audio generation
- [ ] `get_models() -> list[dict]` - List available TTS models
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `ElevenLabsAPIError` exception class
- [ ] Add `ElevenLabsQuotaError` exception class for character limit exceeded
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle quota/rate limiting errors specifically
- [ ] Log errors with context (text length, voice_id, model)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for TTS, voices, models
- [ ] Test error scenarios (401, 403 quota exceeded, 500)
- [ ] Test streaming audio generation
- [ ] Test different voice IDs and models
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup (xi-api-key header)
- [ ] List popular voice IDs
- [ ] Note character limits by plan tier
- [ ] Document audio format (MP3, PCM, etc.)

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test with sample text)

## API Methods to Implement

```python
async def text_to_speech(
    self,
    text: str,
    voice_id: str,
    model_id: str = "eleven_monolingual_v1",
    stability: float = 0.5,
    similarity_boost: float = 0.75
) -> bytes:
    """
    Convert text to speech audio.

    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use
        model_id: TTS model ID
        stability: Voice stability (0-1)
        similarity_boost: Voice similarity boost (0-1)

    Returns:
        Audio bytes (MP3 format)
    """

async def get_voices(self) -> list[dict[str, Any]]:
    """
    Get list of available voices.

    Returns:
        List of voice objects with id, name, preview_url
    """

async def stream_text_to_speech(
    self,
    text: str,
    voice_id: str,
    model_id: str = "eleven_monolingual_v1"
) -> AsyncIterator[bytes]:
    """
    Stream text-to-speech audio generation.

    Args:
        text: Text to convert
        voice_id: Voice ID
        model_id: TTS model

    Yields:
        Audio chunks as bytes
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_elevenlabs.py -v

# Check coverage
pytest --cov=src/integrations/elevenlabs --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `ELEVENLABS_API_KEY`
- **Special**: Uses `xi-api-key` header instead of standard `Authorization: Bearer`
- See https://docs.elevenlabs.io for full API reference
- Primary use case: Voice call synthesis for outbound campaigns
- Audio format: MP3 by default, supports PCM for real-time streaming
