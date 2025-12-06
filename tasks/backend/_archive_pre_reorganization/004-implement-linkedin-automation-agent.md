# Task: Implement LinkedIn Automation Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/campaign-linkedin-automation.md
**Created:** 2025-12-05
**Priority:** Phase 6 (Multi-Channel & Advanced)

## Summary

Implement the LinkedIn Automation Agent that handles multi-channel outreach via Heyreach API. The agent validates LinkedIn profiles, sends personalized connection requests, tracks acceptance, and sends follow-up messages while respecting rate limits and coordinating with other agents.

## Files to Create

1. `app/backend/src/agents/linkedin_automation/`
   - `__init__.py` - Package initialization
   - `agent.py` - Main agent implementation extending BaseAgent
   - `tools.py` - LinkedIn outreach tools
   - `prompts.py` - System and user prompt templates
   - `models.py` - Pydantic models for input/output

2. `app/backend/src/integrations/heyreach.py` - Heyreach API client

3. `app/backend/src/tasks/linkedin_tasks.py` - Celery background tasks

4. `app/backend/src/webhooks/heyreach_webhooks.py` - Webhook handlers

5. `app/backend/__tests__/unit/agents/`
   - `test_linkedin_automation.py` - Unit tests
   - `test_heyreach_tools.py` - Tool tests

6. `app/backend/__tests__/integration/`
   - `test_linkedin_integration.py` - Integration tests
   - `test_heyreach_webhooks.py` - Webhook tests

## Implementation Checklist

### Phase 1: Foundation
- [ ] Create agent package structure
- [ ] Implement Pydantic models (all schemas from spec)
- [ ] Create Heyreach integration client extending BaseIntegrationClient
- [ ] Set up basic agent class extending BaseAgent
- [ ] Implement system prompt and configuration

### Phase 2: Tools Implementation
- [ ] Implement `check_linkedin_profile` tool
- [ ] Implement `create_heyreach_campaign` tool
- [ ] Implement `send_connection_request` tool
- [ ] Implement `track_connection_status` tool
- [ ] Implement `send_follow_up_message` tool
- [ ] Implement `sync_outreach_activity` tool

### Phase 3: Core Agent Logic
- [ ] Implement `process_task` method for main workflow
- [ ] Add rate limiting logic with Redis
- [ ] Implement retry logic with exponential backoff
- [ ] Add daily usage tracking
- [ ] Implement handoff coordination with other agents

### Phase 4: Background Tasks
- [ ] Create Celery task for outreach processing
- [ ] Create task for connection status checking
- [ ] Create task for follow-up scheduling
- [ ] Add task for daily usage reporting

### Phase 5: Webhooks
- [ ] Implement webhook endpoint for Heyreach events
- [ ] Handle `connection_accepted` webhook
- [ ] Handle `message_received` webhook
- [ ] Add webhook signature verification

### Phase 6: Database Integration
- [ ] Create `linkedin_outreach` table schema
- [ ] Create `linkedin_connections` table schema
- [ ] Create `linkedin_messages` table schema
- [ ] Implement database sync logic

### Phase 7: Testing
- [ ] Write unit tests for all tools
- [ ] Write agent workflow tests
- [ ] Mock Heyreach API responses
- [ ] Write integration tests with mocked APIs
- [ ] Test webhook processing
- [ ] Test error handling scenarios
- [ ] Test rate limiting
- [ ] Test multi-agent coordination

### Phase 8: Monitoring & Logging
- [ ] Add structured logging throughout
- [ ] Implement metrics tracking
- [ ] Add alerting for critical errors
- [ ] Create health check endpoint

### Phase 9: Documentation
- [ ] Add inline code documentation
- [ ] Create usage examples
- [ ] Document API rate limits
- [ ] Document webhook format

## Acceptance Criteria

From spec/campaign-linkedin-automation.md:
- [ ] Agent validates LinkedIn profiles before outreach
- [ ] Respects Heyreach daily limits (configurable)
- [ ] Only contacts leads not already connected
- [ ] Sends personalized connection notes under 300 chars
- [ ] Waits 72+ hours before follow-up messages
- [ ] Syncs all activities to database
- [ ] Coordinates with other agents to avoid duplicate outreach
- [ ] Handles Heyreach API errors gracefully
- [ ] Maintains audit trail of all outreach
- [ ] Processes webhooks for connection status updates
- [ ] Generates daily usage reports
- [ ] Stops outreach if lead requests removal
- [ ] Enforces message quality standards
- [ ] Passes all unit and integration tests

## Key Implementation Details

### Heyreach API Integration
```python
class HeyreachClient(BaseIntegrationClient):
    async def create_campaign(self, name: str, leads: list[dict]) -> dict:
        return await self.post("/campaigns", json={"name": name, "leads": leads})

    async def send_connection_request(self, campaign_id: str, lead_data: dict) -> dict:
        return await self.post(f"/campaigns/{campaign_id}/requests", json=lead_data)

    async def get_request_status(self, request_ids: list[str]) -> dict:
        return await self.post("/requests/status", json={"request_ids": request_ids})
```

### Rate Limiting Pattern
```python
async def check_rate_limit(self, agent_id: str) -> bool:
    """Check if agent has reached daily connection limit."""
    key = f"linkedin:limit:{agent_id}:{date.today()}"
    count = await self.redis.get(key) or 0
    return int(count) < self.config.max_connections_per_day
```

### Error Handling Example
```python
async def handle_heyreach_error(self, error: httpx.HTTPStatusError) -> dict:
    if error.response.status_code == 429:
        # Rate limited - schedule for tomorrow
        return {"action": "reschedule", "delay": 86400}
    elif error.response.status_code == 401:
        # API key issue - alert immediately
        await self.alert_ops("Heyreach API key invalid")
        return {"action": "fail", "reason": "auth_error"}
    # ... other error types
```

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_linkedin_automation.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_linkedin_integration.py -v

# Type checking
mypy app/backend/src/agents/linkedin_automation/

# Linting
ruff check app/backend/src/agents/linkedin_automation/
ruff format app/backend/src/agents/linkedin_automation/

# Test Heyreach integration (with mock)
pytest app/backend/__tests__/unit/agents/test_heyreach_tools.py -v

# Run webhook tests
pytest app/backend/__tests__/integration/test_heyreach_webhooks.py -v

# Manual smoke test
python -c "
from app.backend.src.agents.linkedin_automation.agent import LinkedInAutomationAgent
agent = LinkedInAutomationAgent('test')
print('Agent initialized successfully')
"

# Check database migrations
alembic current
```

## Dependencies

Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
linkedin = [
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",  # For LinkedIn profile parsing
    "pydantic>=2.12.5",
]
```

## Environment Variables

```bash
# Required
HEYREACH_API_KEY=sk-heyreach-...
LINKEDIN_AGENT_ENABLED=true

# Optional with defaults
LINKEDIN_DAILY_LIMIT=25
LINKEDIN_FOLLOWUP_DELAY_HOURS=72
LINKEDIN_MESSAGE_MAX_LENGTH=300
```

## Notes

1. **Security**: Never store raw LinkedIn credentials. Use Heyreach proxy.
2. **Compliance**: Respect LinkedIn ToS - no scraping, only use Heyreach API.
3. **Quality**: Implement message quality checks to prevent spam.
4. **Coordination**: Check email agent activity before LinkedIn outreach.
5. **Monitoring**: Track acceptance rates and adjust strategy based on performance.
