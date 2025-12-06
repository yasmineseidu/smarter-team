# Task: Implement Client Update Agent

**Status:** Pending
**Domain:** Backend
**Agent:** Client Update Agent
**Spec Reference:** specs/agents/delivery-client-update.md
**Created:** 2025-12-05
**Priority:** High

## Summary

Implement the Client Update Agent that sends personalized project progress updates to clients including weekly summaries, milestone completions, and blocker alerts. The agent must handle scheduling, email generation, delivery tracking, and comprehensive error handling.

## Files to Create

```
app/backend/src/agents/client_update/
├── __init__.py
├── agent.py                    # Main ClientUpdateAgent class extending BaseAgent
├── schemas.py                  # Pydantic models for all data contracts
├── exceptions.py               # Custom exceptions
├── tools/
│   ├── __init__.py
│   ├── project_status.py       # get_project_status tool implementation
│   ├── content_gen.py          # generate_update_content tool implementation
│   ├── email_sender.py         # send_email_update tool implementation
│   └── logger.py               # log_client_update tool implementation
├── templates/
│   ├── weekly_progress.html    # Weekly update email template
│   ├── milestone_complete.html # Milestone completion template
│   └── blocker_alert.html      # Blocker alert template
└── config.py                   # Agent configuration

app/backend/src/tasks/client_update_tasks.py  # Celery tasks for scheduling

app/backend/__tests__/
├── unit/agents/test_client_update.py         # Unit tests
└── integration/test_client_update_integration.py # Integration tests

Database migrations:
- migrations/001_create_client_updates_table.sql
- migrations/002_create_update_logs_table.sql
```

## Implementation Checklist

### Phase 1: Core Agent Structure
- [ ] Create `ClientUpdateAgent` class extending `BaseAgent`
- [ ] Implement system prompt property
- [ ] Set up agent configuration
- [ ] Register all tools with proper descriptions
- [ ] Implement `process_task` async method

### Phase 2: Database Schema
- [ ] Create migration for `client_updates` table
- [ ] Create migration for `update_logs` table
- [ ] Add necessary indexes for performance
- [ ] Add foreign key constraints
- [ ] Create SQLAlchemy models

### Phase 3: Tools Implementation
- [ ] **project_status.py:**
  - Implement `get_project_status` tool
  - Add input/output Pydantic schemas
  - Handle API calls to Project Management Agent
  - Add comprehensive error handling
  - Add caching for 15-minute TTL

- [ ] **content_gen.py:**
  - Implement `generate_update_content` tool
  - Create HTML template rendering logic
  - Add personalization based on client preferences
  - Handle all update types (weekly, milestone, blocker)
  - Add fallback content generation

- [ ] **email_sender.py:**
  - Implement `send_email_update` tool
  - Integrate with Instantly.ai/Gmail API
  - Add rate limiting logic
  - Implement exponential backoff retry
  - Add provider failover capability

- [ ] **logger.py:**
  - Implement `log_client_update` tool
  - Write to database with proper schema
  - Add duplicate detection
  - Include all metadata for analytics
  - Handle database connection issues

### Phase 4: Email Templates
- [ ] Create responsive HTML templates
- [ ] Add support for dynamic content blocks
- [ ] Include inline CSS for email client compatibility
- [ ] Add placeholders for all variables
- [ ] Test rendering with various data scenarios

### Phase 5: Scheduling & Triggers
- [ ] Create Celery task for weekly updates (Friday 3 PM)
- [ ] Create webhook handler for milestone completions
- [ ] Create webhook handler for blocker detection
- [ ] Add timezone handling for client locations
- [ ] Implement bulk send processing with rate limiting

### Phase 6: Error Handling
- [ ] Implement circuit breaker for email providers
- [ ] Add dead letter queue for failed sends
- [ ] Create alerting for critical failures
- [ ] Add graceful degradation scenarios
- [ ] Implement comprehensive logging

### Phase 7: Testing
- [ ] **Unit Tests:**
  - Test all tools with various inputs
  - Test template rendering edge cases
  - Test error handling scenarios
  - Test rate limiting logic
  - Test database operations

- [ ] **Integration Tests:**
  - End-to-end weekly update flow
  - Milestone notification trigger
  - Blocker alert escalation
  - Provider failover testing
  - Bulk send processing

### Phase 8: Performance & Monitoring
- [ ] Add structured logging with correlation IDs
- [ ] Implement metrics tracking
- [ ] Add performance monitoring
- [ ] Create health check endpoints
- [ ] Set up alerting rules

## Data Models (Key Fields)

```python
# ClientUpdate model
class ClientUpdate:
    id: UUID
    client_id: UUID
    project_id: UUID
    update_type: str  # WEEKLY_PROGRESS, MILESTONE_COMPLETE, BLOCKER_ALERT
    email_id: Optional[str]
    subject: str
    content_summary: str
    status: str  # sent, scheduled, failed, draft
    sent_at: Optional[datetime]
    created_at: datetime
    metadata: dict

# UpdateLog model
class UpdateLog:
    id: UUID
    update_id: UUID
    event_type: str  # created, sent, failed, opened, clicked
    event_data: dict
    timestamp: datetime
```

## Integration Points

### External APIs:
- **Instantly.ai:** Primary email provider
- **Gmail API:** Backup email provider
- **Project Management Agent:** Status data source

### Internal Systems:
- **Database:** PostgreSQL via SQLAlchemy
- **Task Queue:** Celery with Redis
- **Logging:** Structured logging via get_agent_logger
- **Monitoring:** Custom metrics and health checks

## Configuration Requirements

```python
# Environment variables needed
CLIENT_UPDATE_FROM_EMAIL=updates@smarterteam.ai
CLIENT_UPDATE_FROM_NAME=Smarter Team Updates
INSTANTLY_API_KEY=sk-...
GMAIL_CREDENTIALS_JSON=...
CLIENT_UPDATE_TIMEZONE_DEFAULT=America/New_York
CLIENT_UPDATE_WEEKLY_DAY=friday
CLIENT_UPDATE_WEEKLY_TIME=15:00
CLIENT_UPDATE_RATE_LIMIT=120
```

## Acceptance Criteria

- [ ] All three update types (weekly, milestone, blocker) work correctly
- [ ] Weekly updates sent every Friday at 3 PM client time
- [ ] Milestone notifications sent within 2 hours of completion
- [ ] Blocker alerts sent within 1 hour of detection
- [ ] Email templates render correctly in all major email clients
- [ ] Rate limiting respected for both email providers
- [ ] Failover to backup provider works automatically
- [ ] All communications logged with proper metadata
- [ ] Error handling covers all specified scenarios
- [ ] Unit test coverage >90%
- [ ] Integration tests pass for all workflows
- [ ] Performance meets SLA requirements
- [ ] Security requirements implemented (PII masking, encryption)
- [ ] Documentation complete with examples

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_client_update.py -v --cov=src.agents.client_update

# Run integration tests
pytest app/backend/__tests__/integration/test_client_update_integration.py -v

# Type checking
mypy app/backend/src/agents/client_update/

# Linting and formatting
ruff check app/backend/src/agents/client_update/
ruff format app/backend/src/agents/client_update/

# Database migrations
alembic upgrade head

# Manual test
python -c "
from src.agents.client_update.agent import ClientUpdateAgent
agent = ClientUpdateAgent()
print('Agent initialized successfully')
"

# Load test (bulk sends)
python scripts/test_bulk_sends.py --clients 100 --batch-size 10
```

## Notes

1. **Timezone Handling:** All timestamps should be stored in UTC, but sent at client local time
2. **Rate Limiting:** Implement per-provider limits with conservative buffers
3. **Security:** Mask PII in logs, encrypt sensitive data at rest
4. **Performance:** Cache project status for 15 minutes to reduce API calls
5. **Monitoring:** Track delivery rates, open rates, and response times
6. **Back-compatibility:** Template versioning for future updates
