# Task: Implement Client Offboarding Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/offboarding-client-offboarding.md
**Created:** 2025-12-05
**Priority:** Phase 5 - Retention & Growth

## Summary

Implement the Client Offboarding Agent that orchestrates complete client project offboarding with checklist-driven process. This agent ensures smooth transition from active project to long-term nurture while maintaining professionalism and collecting valuable feedback. The agent handles final deliverable handoffs, payment verification, access revocation, project archiving, and client transition to nurture sequences.

## Files to Create

- `app/backend/src/agents/client_offboarding/__init__.py`
- `app/backend/src/agents/client_offboarding/agent.py`
- `app/backend/src/agents/client_offboarding/tools.py`
- `app/backend/src/agents/client_offboarding/prompts.py`
- `app/backend/src/agents/client_offboarding/schemas.py`
- `app/backend/src/agents/client_offboarding/exceptions.py`
- `app/backend/__tests__/unit/agents/test_client_offboarding.py`
- `app/backend/__tests__/integration/test_client_offboarding_integration.py`
- `app/backend/__tests__/fixtures/offboarding_fixtures.py`

## Database Schema Updates

Create the following tables (add to migration):

```sql
-- Offboarding checklist tracking
CREATE TABLE offboarding_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    client_id UUID NOT NULL REFERENCES clients(id),
    status VARCHAR(20) NOT NULL DEFAULT 'NOT_STARTED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id)
);

-- Checklist items
CREATE TABLE offboarding_checklist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    progress_id UUID NOT NULL REFERENCES offboarding_progress(id),
    item_id VARCHAR(100) NOT NULL,
    section VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    evidence JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(progress_id, item_id)
);

-- Archive tracking
CREATE TABLE project_archives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    archive_id VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    data_size_gb DECIMAL(10,2),
    files_count INTEGER,
    retention_policy JSONB,
    completion_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Implementation Checklist

### Core Agent Implementation
- [ ] Create `ClientOffboardingAgent` class extending `BaseAgent`
- [ ] Implement `system_prompt` property with comprehensive offboarding instructions
- [ ] Implement `process_task` method with state management
- [ ] Register all 8 tools with proper schemas
- [ ] Add error handling and retry logic for all operations

### Tools Implementation
- [ ] `get_offboarding_checklist` - Query checklist status, create if needed
- [ ] `update_checklist_item` - Mark items complete, add notes and evidence
- [ ] `prepare_deliverable_handoff` - Google Drive integration for file sharing
- [ ] `verify_final_payment` - Stripe integration for payment verification
- [ ] `revoke_access_credentials` - Multi-system access revocation
- [ ] `archive_project_data` - Project archival with retention policy
- [ ] `send_feedback_request` - Email templates for survey/testimonial
- [ ] `transition_to_nurture` - Long-term nurture handoff

### Integration Clients
- [ ] Extend `BaseIntegrationClient` for Stripe payment verification
- [ ] Extend `BaseIntegrationClient` for Google Drive file operations
- [ ] Extend `BaseIntegrationClient` for email sending (Instantly/SendGrid)
- [ ] Add rate limiting and retry logic for all integrations

### Error Handling & Resilience
- [ ] Implement exponential backoff for transient failures
- [ ] Add dead-letter queue for persistent failures
- [ ] Create custom exceptions for offboarding-specific errors
- [ ] Add graceful degradation for partial failures
- [ ] Implement timeout handling for all external calls

### Database Operations
- [ ] Create async SQLAlchemy models for all tables
- [ ] Implement CRUD operations for checklist management
- [ ] Add database transactions for multi-step operations
- [ ] Create migration for schema changes

### Testing Suite
- [ ] Unit tests for each tool with mocked external APIs
- [ ] Integration tests for complete offboarding flows
- [ ] Error scenario tests (payment failures, API errors)
- [ ] Performance tests for batch operations
- [ ] Mock fixtures for all external services

### Configuration & Deployment
- [ ] Add environment variables for all API keys
- [ ] Update `.env.example` with new integrations
- [ ] Add agent to agent registry
- [ ] Create Celery tasks for background operations
- [ ] Add monitoring and alerting rules

## Acceptance Criteria

### Functional Requirements
- [ ] Agent can create and manage offboarding checklists for any project
- [ ] All 8 tools work independently and as part of complete workflow
- [ ] File handoff works with Google Drive API (folder creation, sharing)
- [ ] Payment verification correctly detects paid/unpaid/overdue status
- [ ] Access revocation logs all changes and handles failures gracefully
- [ ] Project archival follows retention policy and stores metadata
- [ ] Feedback requests send proper email templates
- [ ] Nurture transition updates CRM with correct tags

### Non-Functional Requirements
- [ ] All external API calls have proper timeout and retry logic
- [ ] Error messages are logged with full context for debugging
- [ ] Agent maintains state across multiple steps and interruptions
- [ ] Performance meets specifications (offboarding < 15 minutes)
- [ ] Security requirements implemented (encryption, audit trail)
- [ ] Unit test coverage > 90% for all tools
- [ ] Integration tests cover all success and failure paths

### Integration Requirements
- [ ] Agent handoffs work correctly with Project Management and Invoice agents
- [ ] Stripe integration handles all payment statuses correctly
- [ ] Google Drive integration manages permissions and sharing properly
- [ ] Email sending respects rate limits and handles bounces
- [ ] Database operations are properly transactional

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_client_offboarding.py -v --cov=src.agents.client_offboarding

# Run integration tests
pytest app/backend/__tests__/integration/test_client_offboarding_integration.py -v

# Type checking
mypy app/backend/src/agents/client_offboarding/

# Linting
ruff check app/backend/src/agents/client_offboarding/

# Database migration
make migrate

# Manual test
python -c "
from src.agents.client_offboarding import ClientOffboardingAgent
import asyncio

async def test():
    agent = ClientOffboardingAgent()
    checklist = await agent.get_offboarding_checklist(
        project_id='test-123',
        client_id='client-456'
    )
    print(checklist)

asyncio.run(test())
"
```

## Dependencies

- Project Management Agent (for project completion status)
- Invoice Generation Agent (for final invoice details)
- Testimonial Request Agent (for testimonial collection)
- Stripe API (payment verification)
- Google Drive API (file sharing)
- Email Service API (notifications)
- PostgreSQL (checklist and archive storage)
- Redis (task queue and caching)

## Risks & Mitigations

- **Risk:** Stripe API rate limiting during payment verification
  **Mitigation:** Implement queue-based verification with exponential backoff

- **Risk:** Google Drive permission errors during file sharing
  **Mitigation:** Pre-create folder structure, use service account with proper scopes

- **Risk:** Client non-response to feedback requests
  **Mitigation:** Automated follow-ups, multiple contact methods

- **Risk:** Incomplete access revocation leading to security issues
  **Mitigation:** Mandatory verification steps, audit trail, periodic access audits

- **Risk:** Archive storage running out of space
  **Mitigation:** Pre-flight checks, multiple storage locations, cleanup procedures
