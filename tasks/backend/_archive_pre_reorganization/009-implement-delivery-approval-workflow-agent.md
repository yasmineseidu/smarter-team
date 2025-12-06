# Task: Implement Delivery Approval Workflow Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/delivery-approval-workflow.md
**Created:** 2025-12-05
**Priority:** High

## Summary
Implement the Delivery Approval Workflow Agent that manages client approval processes for project deliverables, including review requests, revision handling, approval tracking, and integration with email, Google Drive, and ClickUp systems.

## Files to Create
- `app/backend/src/agents/delivery_approval_workflow/`
  - `__init__.py`
  - `agent.py` - Main agent implementation
  - `tools.py` - All tool functions
  - `schemas.py` - Pydantic models for validation
  - `exceptions.py` - Custom exceptions
  - `email_templates.py` - Email template generators
- `app/backend/src/tasks/delivery_tasks.py` - Celery tasks for async operations
- `app/backend/__tests__/unit/agents/test_delivery_approval_workflow_agent.py`
- `app/backend/__tests__/integration/test_delivery_approval_integration.py`
- Database migrations:
  - `migrations/versions/XXX_create_approval_tables.py`

## Implementation Checklist

### Core Agent Implementation
- [ ] Create agent class extending BaseAgent
- [ ] Implement system prompt property
- [ ] Set up lazy-loaded integration clients (Email, Google Drive, ClickUp)
- [ ] Implement process_task() method with action routing
- [ ] Register all tools in _register_tools()

### Tool Implementation
- [ ] `submit_deliverable` - Register new deliverable for approval
- [ ] `send_review_request` - Send professional review email
- [ ] `track_review_status` - Monitor client engagement
- [ ] `process_revision_request` - Handle client feedback
- [ ] `confirm_approval` - Mark as approved and trigger next steps
- [ ] `handle_timeout` - Manage expired review periods
- [ ] `update_deliverable_status` - Track status in all systems
- [ ] `generate_approval_report` - Create process summary

### Database Models & Migrations
- [ ] Create `approval_requests` table with all fields
- [ ] Create `revision_requests` table
- [ ] Create `approvals` table
- [ ] Create `approval_events` table for audit trail
- [ ] Add all indexes for performance
- [ ] Create SQLAlchemy models

### Integration Clients
- [ ] Google Drive client integration
  - Create shareable links with expiration
  - Track file access statistics
  - Manage permissions (viewer only)
- [ ] Email client integration
  - Send templated emails
  - Track open/click statistics
  - Handle bounces and failures
- [ ] ClickUp client integration
  - Update task statuses
  - Add comments and attachments
  - Handle API rate limits

### Celery Tasks
- [ ] `send_followup_reminder` - Automated follow-ups
- [ ] `check_review_timeouts` - Daily timeout check
- [ ] `sync_approval_status` - Sync to external systems
- [ ] `generate_daily_report` - Approval metrics

### Error Handling & Edge Cases
- [ ] Retry logic for external API failures
- [ ] Handle revision limit exceeded scenarios
- [ ] Manage client non-response with escalation
- [ ] Handle email delivery failures
- [ ] Manage Google Drive permission errors

### Testing
- [ ] Unit tests for all tools (>90% coverage)
- [ ] Unit tests for agent orchestration
- [ ] Integration tests with database
- [ ] Mock external service integrations
- [ ] Test error scenarios and recovery
- [ ] Test timeout handling and escalation

### Email Templates
- [ ] Review request template
- [ ] Revision notification template
- [ ] Approval confirmation template
- [ ] Follow-up reminder template
- [ ] Escalation notification template

### Configuration & Settings
- [ ] Add environment variables for integrations
- [ ] Configure default timing (review period, follow-up interval)
- [ ] Set up logging and monitoring
- [ ] Define escalation rules and thresholds

## Acceptance Criteria

1. **Functional Requirements:**
   - Successfully submit deliverables for approval
   - Send review requests with secure Google Drive links
   - Track client engagement (email opens, link clicks)
   - Process revision requests within contract limits
   - Confirm approvals and trigger invoice generation
   - Handle timeouts with proper escalation

2. **Integration Requirements:**
   - Send emails through configured provider
   - Create/manage Google Drive sharing links
   - Update ClickUp tasks with status changes
   - Handoff to other agents (invoice_generation, project_management)

3. **Performance Requirements:**
   - Process approval requests in < 5 seconds
   - Handle 100+ concurrent approval workflows
   - Email delivery within 30 seconds
   - Database queries optimized with proper indexes

4. **Quality Requirements:**
   - >90% unit test coverage
   - >85% integration test coverage
   - All error scenarios handled gracefully
   - Complete audit trail for all actions
   - Structured logging for monitoring

5. **Security Requirements:**
   - Secure Google Drive links with expiration
   - Email sent only to verified contacts
   - Input validation for all parameters
   - Rate limiting for external APIs
   - Audit logging for compliance

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_delivery_approval_workflow_agent.py -v --cov=src/agents/delivery_approval_workflow

# Run integration tests
pytest app/backend/__tests__/integration/test_delivery_approval_integration.py -v

# Type checking
mypy app/backend/src/agents/delivery_approval_workflow/

# Linting
ruff check app/backend/src/agents/delivery_approval_workflow/

# Test database migrations
alembic upgrade head

# Manual test workflow
python -c "
from src.agents.delivery_approval_workflow import DeliveryApprovalWorkflowAgent
agent = DeliveryApprovalWorkflowAgent()
print(f'Agent: {agent.name}, Tools: {len(agent.tools)}')
"
```

## Dependencies

### Required Environment Variables
```bash
# Email service
EMAIL_PROVIDER=sendgrid|gmail|ses
EMAIL_API_KEY=your_email_api_key

# Google Drive
GOOGLE_CREDENTIALS_JSON=path/to/service-account.json
GOOGLE_DRIVE_FOLDER_ID=deliverables_folder_id

# ClickUp
CLICKUP_API_TOKEN=your_clickup_token
CLICKUP_SPACE_ID=space_id
CLICKUP_LIST_ID=deliverables_list_id

# Timing Configuration
DEFAULT_REVIEW_PERIOD_DAYS=5
MAX_REVISION_DAYS=14
FOLLOWUP_INTERVAL_DAYS=2
MAX_FOLLOWUPS=3
```

### Python Dependencies
```python
# Already in dependencies - ensure available:
# - fastapi
# - sqlalchemy
# - pydantic
# - httpx (for API clients)
# - tenacity (for retry logic)
# - celery (for background tasks)
# - google-api-python-client
# - google-auth-oauthlib
```

## Notes

- Follow existing patterns from other agent implementations
- Use BaseAgent and BaseIntegrationClient classes
- Ensure all I/O operations are async
- Implement proper error handling with structured logging
- Test all edge cases, especially revision limit handling
- Monitor performance with appropriate metrics
- Document any deviations from the spec
