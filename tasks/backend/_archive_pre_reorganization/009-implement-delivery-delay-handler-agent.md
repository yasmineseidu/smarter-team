# Task: Implement Delivery Delay Handler Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/delivery-delay-handler.md
**Created:** 2025-12-05
**Estimated Effort:** 40-60 hours

## Summary

Implement the Delivery Delay Handler Agent that detects project delays, analyzes impact, drafts client communications, manages approval workflows, and updates project schedules. This agent is critical for maintaining client satisfaction through transparent delay management and proactive communication.

## Files to Create

### Core Agent Implementation
- `app/backend/src/agents/delivery_delay_handler.py` - Main agent class
- `app/backend/src/agents/tools/delay_detection.py` - Delay detection tool
- `app/backend/src/agents/tools/impact_analysis.py` - Impact calculation tool
- `app/backend/src/agents/tools/communication_drafter.py` - Communication drafting tool
- `app/backend/src/agents/tools/approval_workflow.py` - Approval management tool

### Integration Clients
- `app/backend/src/integrations/clickup.py` - ClickUp API client
- `app/backend/src/integrations/asana.py` - Asana API client
- `app/backend/src/integrations/notion.py` - Notion API client

### Database
- `app/backend/migrations/001_create_project_delays_table.sql`
- `app/backend/migrations/002_create_delay_communications_table.sql`
- `app/backend/src/models/delay.py` - SQLAlchemy models

### Tests
- `app/backend/__tests__/unit/agents/test_delivery_delay_handler.py`
- `app/backend/__tests__/unit/agents/tools/test_delay_detection.py`
- `app/backend/__tests__/unit/agents/tools/test_impact_analysis.py`
- `app/backend/__tests__/unit/agents/tools/test_communication_drafter.py`
- `app/backend/__tests__/unit/agents/tools/test_approval_workflow.py`
- `app/backend/__tests__/unit/integrations/test_clickup.py`
- `app/backend/__tests__/unit/integrations/test_asana.py`
- `app/backend/__tests__/unit/integrations/test_notion.py`
- `app/backend/__tests__/integration/test_delivery_delay_handler_integration.py`

## Implementation Checklist

### Phase 1: Setup and Database
- [ ] Create database migrations for project_delays table
- [ ] Create database migrations for delay_communications table
- [ ] Implement SQLAlchemy models for delay tracking
- [ ] Create BaseIntegrationClient subclasses for PM systems
- [ ] Set up API key management for PM integrations

### Phase 2: Core Agent Structure
- [ ] Create DeliveryDelayHandlerAgent class extending BaseAgent
- [ ] Implement system prompt property with delay handling guidelines
- [ ] Set up agent initialization and tool registration
- [ ] Implement process_task method with task type routing
- [ ] Add structured logging for all agent operations

### Phase 3: Tool Implementation
- [ ] Implement detect_delays tool for scanning overdue milestones
- [ ] Implement analyze_delay_impact tool for cascade effect calculations
- [ ] Implement draft_delay_communication tool using Claude API
- [ ] Implement submit_for_approval tool for Slack/Email notifications
- [ ] Implement send_approved_communication tool via Instantly
- [ ] Implement update_project_schedule tool for PM system updates
- [ ] Add comprehensive error handling to all tools

### Phase 4: Integration and Workflow
- [ ] Connect to ClickUp API for milestone tracking
- [ ] Connect to Asana API for task dependencies
- [ ] Connect to Notion API for project databases
- [ ] Implement approval workflow with Slack/Telegram
- [ ] Set up email sending through Instantly API
- [ ] Implement agent handoffs to QA, Client Success, and PM agents

### Phase 5: Communication Templates
- [ ] Create communication templates for each severity level
- [ ] Implement template variables and personalization
- [ ] Set up timezone handling for client communications
- [ ] Implement approval notification templates
- [ ] Create internal logging templates

### Phase 6: Testing
- [ ] Write unit tests for all tools with various scenarios
- [ ] Write integration tests for PM system APIs
- [ ] Write end-to-end tests for complete delay handling workflow
- [ ] Create mocks for all external API dependencies
- [ ] Test error handling and retry logic
- [ ] Test timezone and business hours logic
- [ ] Test approval workflow edge cases

### Phase 7: Monitoring and Metrics
- [ ] Implement structured logging with correlation IDs
- [ ] Set up metrics collection for delay patterns
- [ ] Create alerting for critical delays and workflow failures
- [ ] Implement audit logging for all communications
- [ ] Set up performance monitoring for agent execution

### Phase 8: Documentation and Deployment
- [ ] Add inline documentation for all methods
- [ ] Create configuration documentation
- [ ] Set up environment variables for API keys
- [ ] Add agent to agent registry
- [ ] Create Celery tasks for scheduled delay detection
- [ ] Set up health checks for all integrations

## Key Implementation Details

### Delay Detection Algorithm
```python
# Pseudo-code for delay detection
for project in active_projects:
    milestones = await pm_client.get_milestones(project.id)
    for milestone in milestones:
        if milestone.due_date < now and milestone.status != "complete":
            delay = calculate_delay(milestone.due_date, now)
            severity = classify_severity(delay, milestone)
            await trigger_delay_analysis(project, milestone, delay, severity)
```

### Impact Analysis Logic
```python
# Pseudo-code for impact analysis
def calculate_cascade_impact(milestone_id, days_delayed):
    downstream = get_downstream_tasks(milestone_id)
    total_impact = days_delayed
    critical_path_affected = False

    for task in downstream:
        task_delay = days_delayed + task.buffer
        if task.is_critical_path:
            critical_path_affected = True
        total_impact = max(total_impact, task_delay)

    return {
        "downstream_tasks": len(downstream),
        "total_delay": total_impact,
        "critical_path_affected": critical_path_affected
    }
```

### Communication Templates Storage
- Store templates in database for easy updates
- Support variable substitution with validation
- Maintain version history of template changes
- Support A/B testing of communication effectiveness

## Acceptance Criteria

### Core Functionality
- [ ] Detects delays within 1 hour of milestone due date
- [ ] Accurately calculates downstream impact across dependency chains
- [ ] Generates revised timelines with realistic buffer estimates
- [ ] Drafts severity-appropriate communications (MINOR to CRITICAL)
- [ ] Manages approval workflow for all external communications
- [ ] Updates project schedules in connected PM systems

### Quality Gates
- [ ] All tests pass with >90% coverage
- [ ] No linting or type checking errors
- [ ] All API integrations have retry logic and error handling
- [ ] Client timezone and business hours respected
- [ ] All external communications approved before sending
- [ ] Audit trail maintained for all delay events

### Performance Requirements
- [ ] Processes all active projects within 5 minutes
- [ ] Communication generated within 15 seconds of impact analysis
- [ ] Approval requests sent within 2 minutes of draft completion
- [ ] Schedule updates completed within 30 seconds
- [ ] Zero data loss in delay tracking

### Integration Requirements
- [ ] Successfully connects to ClickUp, Asana, and Notion
- [ ] Sends emails through Instantly with >98% deliverability
- [ ] Posts approval requests to Slack/Telegram
- [ ] Hands off to other agents with proper payload format
- [ ] Handles API rate limits and quotas gracefully

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_delivery_delay_handler.py -v

# Run tool-specific tests
pytest app/backend/__tests__/unit/agents/tools/ -v

# Run integration tests
pytest app/backend/__tests__/integration/test_delivery_delay_handler_integration.py -v

# Type checking
mypy app/backend/src/agents/delivery_delay_handler.py

# Linting
ruff check app/backend/src/agents/delivery_delay_handler.py
ruff format app/backend/src/agents/delivery_delay_handler.py

# Test PM integrations
pytest app/backend/__tests__/unit/integrations/test_clickup.py -v
pytest app/backend/__tests__/unit/integrations/test_asana.py -v
pytest app/backend/__tests__/unit/integrations/test_notion.py -v

# Manual agent test
python -c "
from app.backend.src.agents.delivery_delay_handler import DeliveryDelayHandlerAgent
agent = DeliveryDelayHandlerAgent()
print(f'Agent initialized: {agent.name}')
print(f'System prompt length: {len(agent.system_prompt)}')
print(f'Tools registered: {[t[\"name\"] for t in agent.tools]}')
"

# Test delay detection
python -c "
import asyncio
from app.backend.src.agents.delivery_delay_handler import DeliveryDelayHandlerAgent

async def test_detection():
    agent = DeliveryDelayHandlerAgent()
    result = await agent.detect_delays({})
    print(f'Delays detected: {len(result[\"delays_detected\"])}')

asyncio.run(test_detection())
"
```

## Dependencies

### Required Environment Variables
```bash
# Project Management Systems
CLICKUP_API_KEY=your_clickup_api_key
CLICKUP_TEAM_ID=your_team_id
ASANA_API_KEY=your_asana_api_key
ASANA_WORKSPACE_ID=your_workspace_id
NOTION_API_KEY=your_notion_api_key

# Communication
INSTANTLY_API_KEY=your_instantly_api_key
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_APPROVAL_CHANNEL=delay-approvals
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_APPROVAL_CHAT_ID=your_chat_id

# AI Services
ANTHROPIC_API_KEY=your_anthropic_api_key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/smarter_team
```

### Python Dependencies (add to pyproject.toml)
```toml
[project.optional-dependencies]
delivery-delay-handler = [
    "clickup-client>=2.0.0",
    "asana>=3.0.0",
    "notion-client>=2.0.0",
    "slack-sdk>=3.21.0",
    "python-telegram-bot>=20.0",
    "python-dateutil>=2.8.0",
    "pytz>=2023.3",
    "jinja2>=3.1.0",
]
```

## Risk Mitigation

### Technical Risks
- **PM API Rate Limits**: Implement intelligent batching and caching
- **Claude API Failures**: Maintain template-based fallback communications
- **Email Deliverability**: Monitor bounce rates, maintain backup providers
- **Timezone Errors**: Validate all timezone calculations, use UTC internally

### Business Risks
- **Communication Delays**: Set up escalation paths for approval timeouts
- **Incorrect Analysis**: Implement human review triggers for complex cases
- **Client Dissatisfaction**: Ensure transparent, proactive communication
- **Data Privacy**: Sanitize all client data before external API calls
