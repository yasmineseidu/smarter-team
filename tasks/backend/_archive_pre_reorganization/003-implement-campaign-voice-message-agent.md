# Task: Implement Voice Message Campaign Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/campaign-voice-message.md
**Created:** 2025-12-05

## Summary
Implement an agent that creates strategic voicemail call tasks for high-value leads who have gone cold in email campaigns. The agent generates personalized talking points, creates tasks in external systems (Todoist/ClickUp), and manages compliance with do-not-call regulations.

## Files to Create
- `app/backend/src/agents/campaign/voice_message_agent.py`
- `app/backend/src/agents/campaign/tools/call_task_tools.py`
- `app/backend/src/integrations/todoist.py` (if not exists)
- `app/backend/src/integrations/clickup.py` (if not exists)
- `app/backend/__tests__/unit/agents/test_voice_message_agent.py`
- `app/backend/__tests__/integration/test_voice_message_agent_integration.py`

## Implementation Checklist
- [ ] Create agent class extending BaseAgent with ClaudeSDKClient
- [ ] Implement check_call_eligibility tool with compliance checks
- [ ] Implement generate_talking_points tool using Claude API
- [ ] Implement create_call_task tool for Todoist integration
- [ ] Implement create_call_task tool for ClickUp integration
- [ ] Implement log_call_attempt tool with lead status updates
- [ ] Implement check_opt_out_compliance tool for DNC checking
- [ ] Add comprehensive error handling for all failure modes
- [ ] Implement retry logic with exponential backoff
- [ ] Add structured logging for all operations
- [ ] Create database migrations for call_tasks and call_logs tables
- [ ] Write unit tests for all tools with mocking
- [ ] Write integration tests for end-to-end workflows
- [ ] Add compliance violation prevention tests
- [ ] Add timezone handling tests
- [ ] Verify with mypy type checking
- [ ] Verify with ruff linting

## Key Implementation Details

### Agent Class Structure
```python
class VoiceMessageAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return [system prompt from spec]

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        # Handle call task creation requests
        # Handle call result logging requests
        pass

    def _register_tools(self):
        self.register_tool(self.check_call_eligibility, "check_call_eligibility")
        self.register_tool(self.generate_talking_points, "generate_talking_points")
        # ... other tools
```

### Tool Implementation Requirements
- All I/O must be async
- Use Pydantic models for input/output validation
- Include detailed error messages for debugging
- Log all external API calls with timing
- Implement rate limiting for external APIs

### Error Handling Patterns
- Try/catch all external API calls
- Use exponential backoff for retries
- Log full context for debugging
- Return structured error responses
- Never expose sensitive data in logs

### Database Models
- Create SQLAlchemy models for call_tasks and call_logs
- Include proper indexes for performance
- Use UUID primary keys
- Add foreign key constraints
- Include audit fields (created_at, updated_at)

### Integration Client Patterns
- Extend BaseIntegrationClient for Todoist/ClickUp
- Handle API authentication securely
- Implement rate limiting headers
- Cache frequently accessed data
- Use httpx for async HTTP requests

## Acceptance Criteria
- [ ] Creates call tasks only for defined triggers (hot lead, post-meeting, proposal)
- [ ] Generates personalized talking points based on lead context
- [ ] Respects do-not-call compliance and opt-out requests
- [ ] Creates tasks in Todoist with all required information
- [ ] Creates tasks in ClickUp with all required information
- [ ] Logs all call attempts with outcomes and follow-up
- [ ] Prevents duplicate calls within 7-day window
- [ ] Handles timezones correctly for call timing
- [ ] Receives handoffs from lead research, meeting, and proposal agents
- [ ] Provides audit trail for compliance requirements
- [ ] Handles API failures gracefully with retries
- [ ] Updates lead status based on call outcomes
- [ ] Generates follow-up tasks when appropriate

## Verification Commands
```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_voice_message_agent.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_voice_message_agent_integration.py -v

# Type checking
mypy app/backend/src/agents/campaign/voice_message_agent.py

# Linting
ruff check app/backend/src/agents/campaign/

# Database migrations
make migrate

# Manual smoke test
python -c "
from app.backend.src.agents.campaign.voice_message_agent import VoiceMessageAgent
agent = VoiceMessageAgent()
print('Agent initialized successfully:', agent.name)
"
```

## Testing Requirements
- Mock all external APIs (Todoist, ClickUp, Claude)
- Test all error conditions and recovery paths
- Verify compliance checking prevents violations
- Test timezone conversion edge cases
- Include performance tests for batch operations
- Test concurrent task creation
- Validate input sanitization
- Test with malformed data

## Notes
- This agent creates tasks for human calling, not automated calls
- Compliance is critical - implement strict checking
- Store phone numbers encrypted at rest
- Log all opt-out violations immediately
- Use lead's timezone for call scheduling
- Integrate with other campaign agents for context
