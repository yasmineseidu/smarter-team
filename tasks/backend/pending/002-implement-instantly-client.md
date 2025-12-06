# Task: Implement Instantly.ai Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Instantly.ai extending BaseIntegrationClient with cold email campaign automation.

## Integration Details

**Category:** Lead Generation & Email
**Base URL:** https://api.instantly.ai/api/v1
**Authentication:** Bearer Token (API Key)
**Documentation:** https://developer.instantly.ai
**Rate Limits:** Varies by plan
**Webhooks:** Campaign events, reply handling

## Files to Create/Modify

- [ ] `app/backend/src/integrations/instantly.py`
- [ ] `app/backend/__tests__/unit/integrations/test_instantly.py`
- [ ] `app/backend/__tests__/fixtures/instantly_fixtures.py`
- [ ] `app/backend/src/webhooks/instantly_webhook.py` - Webhook handler
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `InstantlyClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `INSTANTLY_API_KEY` environment variable
- [ ] Set base URL to `https://api.instantly.ai/api/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_campaign(name: str, **kwargs) -> dict` - Create email campaign
- [ ] `get_campaign(campaign_id: str) -> dict` - Get campaign details
- [ ] `list_campaigns() -> list[dict]` - List all campaigns
- [ ] `add_leads_to_campaign(campaign_id: str, leads: list[dict]) -> dict` - Add leads
- [ ] `send_campaign(campaign_id: str) -> dict` - Launch campaign
- [ ] `pause_campaign(campaign_id: str) -> dict` - Pause campaign
- [ ] `get_campaign_stats(campaign_id: str) -> dict` - Get performance stats
- [ ] `verify_webhook_signature(payload: bytes, signature: str) -> bool` - Webhook verification
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Webhook Handler
- [ ] Create `InstantlyWebhookHandler` class in `src/webhooks/instantly_webhook.py`
- [ ] Handle reply events (store in conversations table)
- [ ] Handle bounce events (update lead status)
- [ ] Handle unsubscribe events (update lead status)
- [ ] Verify webhook signatures using `INSTANTLY_WEBHOOK_SECRET`
- [ ] Add structured logging for all events

### Phase 4: Error Handling
- [ ] Add `InstantlyAPIError` exception class
- [ ] Add `InstantlyWebhookError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting
- [ ] Log errors with context (campaign_id, lead_count)

### Phase 5: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for campaigns, leads, stats
- [ ] Test webhook signature verification
- [ ] Test webhook event handling
- [ ] Test error scenarios (invalid campaign, duplicate leads)
- [ ] Achieve >90% coverage

### Phase 6: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List webhook event types
- [ ] Note campaign limits
- [ ] Document best practices (warmup, sending limits)

### Phase 7: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## API Methods to Implement

```python
async def create_campaign(
    self,
    name: str,
    from_name: str,
    from_email: str,
    subject: str,
    body: str,
    schedule: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Create email campaign.

    Args:
        name: Campaign name
        from_name: Sender name
        from_email: Sender email address
        subject: Email subject line
        body: Email body (supports variables)
        schedule: Sending schedule config

    Returns:
        Campaign object with campaign_id
    """

async def add_leads_to_campaign(
    self,
    campaign_id: str,
    leads: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Add leads to campaign.

    Args:
        campaign_id: Campaign ID
        leads: List of lead dicts with email, first_name, etc.

    Returns:
        Result with added/skipped counts
    """

async def get_campaign_stats(
    self,
    campaign_id: str
) -> dict[str, Any]:
    """
    Get campaign performance stats.

    Args:
        campaign_id: Campaign ID

    Returns:
        Stats with sent, opened, clicked, replied, bounced
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_instantly.py -v
pytest __tests__/unit/webhooks/test_instantly_webhook.py -v

# Check coverage
pytest --cov=src/integrations/instantly --cov=src/webhooks/instantly_webhook --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `INSTANTLY_API_KEY`
- Webhook secret: `INSTANTLY_WEBHOOK_SECRET`
- **Special**: Requires webhook handler for reply processing
- Primary use case: Cold email campaign automation, reply handling
- See https://developer.instantly.ai for full API reference
