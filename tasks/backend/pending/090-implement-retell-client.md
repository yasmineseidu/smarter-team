# Task: Implement Retell AI Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Retell AI extending BaseIntegrationClient with voice call automation capabilities.

## Integration Details

**Category:** AI Services
**Base URL:** https://api.retellai.com/v1
**Authentication:** Bearer Token (API Key)
**Documentation:** https://docs.retellai.com
**Rate Limits:** Contact-based (no public rate limits)

## Files to Create/Modify

- [ ] `app/backend/src/integrations/retell.py`
- [ ] `app/backend/__tests__/unit/integrations/test_retell.py`
- [ ] `app/backend/__tests__/fixtures/retell_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `RetellClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `RETELL_API_KEY` environment variable
- [ ] Set base URL to `https://api.retellai.com/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_call(phone_number: str, agent_id: str, metadata: dict | None = None) -> dict` - Create outbound call
- [ ] `get_call(call_id: str) -> dict` - Get call details
- [ ] `list_calls(limit: int = 100, offset: int = 0) -> dict` - List recent calls
- [ ] `create_agent(name: str, voice_id: str, prompt: str, **kwargs) -> dict` - Create AI agent
- [ ] `update_agent(agent_id: str, **kwargs) -> dict` - Update agent configuration
- [ ] `get_agent(agent_id: str) -> dict` - Get agent details
- [ ] `delete_agent(agent_id: str) -> dict` - Delete agent
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `RetellAPIError` exception class
- [ ] Add `RetellCallError` exception class for call failures
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle call failures with detailed error messages
- [ ] Log errors with context (call_id, agent_id, phone_number)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for calls, agents
- [ ] Test error scenarios (invalid phone, agent not found, call failed)
- [ ] Test pagination for list_calls
- [ ] Test agent CRUD operations
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List call statuses (queued, ringing, in-progress, completed, failed)
- [ ] Document agent configuration options (voice, prompt, interruptions)
- [ ] Note webhook integration for call events

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test call if safe)

## API Methods to Implement

```python
async def create_call(
    self,
    phone_number: str,
    agent_id: str,
    metadata: dict[str, Any] | None = None,
    from_number: str | None = None
) -> dict[str, Any]:
    """
    Create an outbound voice call.

    Args:
        phone_number: Destination phone number (E.164 format)
        agent_id: AI agent ID to handle the call
        metadata: Custom metadata for the call
        from_number: Optional caller ID number

    Returns:
        Call object with call_id and status
    """

async def get_call(self, call_id: str) -> dict[str, Any]:
    """
    Get call details and status.

    Args:
        call_id: Call ID

    Returns:
        Call object with transcript, duration, status
    """

async def create_agent(
    self,
    name: str,
    voice_id: str,
    prompt: str,
    first_message: str | None = None,
    enable_backchannel: bool = True,
    interruption_sensitivity: int = 1
) -> dict[str, Any]:
    """
    Create a new AI agent for calls.

    Args:
        name: Agent name
        voice_id: Voice ID to use (ElevenLabs, PlayHT, etc.)
        prompt: System prompt for agent behavior
        first_message: First message agent says
        enable_backchannel: Enable "uh-huh" backchanneling
        interruption_sensitivity: 0 (never) to 3 (very sensitive)

    Returns:
        Agent object with agent_id
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_retell.py -v

# Check coverage
pytest --cov=src/integrations/retell --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `RETELL_API_KEY`
- See https://docs.retellai.com for full API reference
- Primary use case: Automated voice calls for follow-ups and outreach
- Phone numbers must be in E.164 format (+1234567890)
- Supports webhooks for call events (call.started, call.ended, call.analyzed)
