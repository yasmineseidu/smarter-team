# Task: Implement Internal Setup Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/onboarding-internal-setup.md
**Created:** 2025-01-15
**Priority:** High (Phase 4 - Client Delivery)

## Summary

Implement the Internal Setup Agent that creates and configures all internal project infrastructure for new clients. The agent automates setup across ClickUp, Google Drive, Slack, Airtable, and GoHighLevel, ensuring all systems are linked and permissions are properly configured.

## Files to Create

### Core Agent
- `app/backend/src/agents/onboarding/internal_setup.py` - Main agent implementation
- `app/backend/src/agents/tools/clickup_setup.py` - ClickUp integration tool
- `app/backend/src/agents/tools/drive_structure.py` - Google Drive tool
- `app/backend/src/agents/tools/slack_setup.py` - Slack channel tool
- `app/backend/src/agents/tools/airtable_setup.py` - Airtable record tool
- `app/backend/src/agents/tools/ghl_setup.py` - GoHighLevel tool
- `app/backend/src/agents/tools/verify_setup.py` - Setup verification tool

### Integration Clients
- `app/backend/src/integrations/clickup.py` - ClickUp API client
- `app/backend/src/integrations/google_drive.py` - Google Drive API client
- `app/backend/src/integrations/slack.py` - Slack API client
- `app/backend/src/integrations/airtable.py` - Airtable API client
- `app/backend/src/integrations/ghl.py` - GoHighLevel API client

### Database
- `app/backend/src/models/project_infrastructure.py` - Data model for tracking infrastructure
- `app/backend/src/models/setup_logs.py` - Audit log for setup actions

### Tests
- `app/backend/__tests__/unit/agents/test_internal_setup.py` - Unit tests
- `app/backend/__tests__/unit/agents/tools/test_clickup_setup.py` - Tool tests
- `app/backend/__tests__/integration/test_internal_setup_integration.py` - Integration tests

## Implementation Checklist

### Phase 1: Integration Clients (Day 1)
- [ ] Create ClickUp client extending BaseIntegrationClient
  - [ ] Implement create_project() method
  - [ ] Implement create_list() method
  - [ ] Implement assign_task() method
  - [ ] Add error handling and retries
- [ ] Create Google Drive client extending BaseIntegrationClient
  - [ ] Implement create_folder() method
  - [ ] Implement share_folder() method
  - [ ] Implement move_file() method
  - [ ] Add batch folder creation
- [ ] Create Slack client (optional dependency)
  - [ ] Implement create_channel() method
  - [ ] Implement invite_users() method
  - [ ] Handle Slack not configured gracefully
- [ ] Create Airtable client extending BaseIntegrationClient
  - [ ] Implement create_record() method
  - [ ] Implement update_record() method
  - [ ] Implement link_records() method
- [ ] Create GHL client extending BaseIntegrationClient
  - [ ] Implement get_contact() method
  - [ ] Implement update_contact() method
  - [ ] Implement move_pipeline_stage() method

### Phase 2: Tools Implementation (Day 2-3)
- [ ] Implement create_clickup_project tool
  - [ ] Input validation with Pydantic
  - [ ] Call ClickUp API with proper parameters
  - [ ] Handle template application
  - [ ] Return structured output
- [ ] Implement create_drive_structure tool
  - [ ] Create folder hierarchy
  - [ ] Set permissions correctly
  - [ ] Move contract file if provided
  - [ ] Generate share links
- [ ] Implement create_slack_channel tool
  - [ ] Handle missing Slack config
  - [ ] Create private/public channels
  - [ ] Invite team members
  - [ ] Post welcome message
- [ ] Implement create_airtable_record tool
  - [ ] Link to client record
  - [ ] Set all project fields
  - [ ] Store cross-reference IDs
- [ ] Implement update_ghl_contact tool
  - [ ] Update contact with project info
  - [ ] Apply correct tags
  - [ ] Move to pipeline stage
- [ ] Implement verify_setup_complete tool
  - [ ] Check each system is accessible
  - [ ] Verify links work
  - [ ] Report status for each

### Phase 3: Agent Core (Day 4)
- [ ] Create InternalSetupAgent class extending BaseAgent
  - [ ] Implement system prompt property
  - [ ] Register all tools
  - [ ] Implement process_task method
- [ ] Add error handling and retry logic
  - [ ] Exponential backoff for rate limits
  - [ ] Partial failure handling
  - [ ] Rollback procedures if needed
- [ ] Implement state management
  - [ ] Track setup progress
  - [ ] Store infrastructure IDs
  - [ ] Log all actions
- [ ] Add handoff support
  - [ ] Receive from onboarding_orchestrator
  - [ ] Report completion back
  - [ ] Handle escalations

### Phase 4: Database Models (Day 5)
- [ ] Create ProjectInfrastructure model
  - [ ] Fields for all system IDs
  - [ ] Status tracking
  - [ ] Links to client/project
- [ ] Create SetupLog model
  - [ ] Timestamps for all actions
  - [ ] Error logs
  - [ ] Success confirmations
- [ ] Add database operations
  - [ ] Insert/update infrastructure
  - [ ] Query setup status
  - [ ] Audit trail queries

### Phase 5: Testing (Day 6-7)
- [ ] Write unit tests for agent
  - [ ] Test initialization
  - [ ] Test process_task with valid input
  - [ ] Test error scenarios
  - [ ] Test tool registration
- [ ] Write unit tests for tools
  - [ ] Test input validation
  - [ ] Test error handling
  - [ ] Test success responses
  - [ ] Mock external APIs
- [ ] Write integration tests
  - [ ] Test full setup flow
  - [ ] Test partial failures
  - [ ] Test cross-platform linking
  - [ ] Test handoff communication
- [ ] Add test fixtures
  - [ ] Mock API responses
  - [ ] Test data factories
  - [ ] Common test utilities

### Phase 6: Documentation & Finalization (Day 8)
- [ ] Add comprehensive docstrings
- [ ] Update API documentation
- [ ] Add monitoring and metrics
- [ ] Performance optimization
- [ ] Security review

## Acceptance Criteria

### Functional Requirements
- [ ] Successfully creates ClickUp project from template
- [ ] Creates complete Google Drive folder structure
- [ ] Sets up Slack channel when configured
- [ ] Creates Airtable project record with links
- [ ] Updates GHL contact with project info
- [ ] Handles partial failures gracefully
- [ ] Reports completion status accurately
- [ ] All IDs cross-referenced between systems

### Non-Functional Requirements
- [ ] All API calls include proper error handling
- [ ] Rate limits respected with backoff
- [ ] Sensitive data never logged
- [ ] All actions audited with timestamps
- [ ] Setup completes within 60 seconds
- [ ] 99% success rate for typical setup
- [ ] Unit test coverage >85%
- [ ] Integration tests for all tools

### Integration Requirements
- [ ] Receives tasks from onboarding_orchestrator
- [ ] Reports completion with full infrastructure details
- [ ] Handles missing optional integrations (Slack)
- [ ] Escalates critical failures appropriately
- [ ] Uses BaseAgent patterns correctly
- [ ] Follows existing code conventions

## Database Schema

### project_infrastructure Table
```sql
CREATE TABLE project_infrastructure (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    client_id UUID NOT NULL REFERENCES clients(id),

    -- System IDs
    clickup_project_id VARCHAR(50),
    clickup_url TEXT,
    clickup_space_id VARCHAR(50),

    drive_folder_id VARCHAR(100),
    drive_folder_url TEXT,
    contract_folder_id VARCHAR(100),

    slack_channel_id VARCHAR(20),
    slack_channel_name VARCHAR(100),

    airtable_record_id VARCHAR(50),
    airtable_record_url TEXT,

    ghl_contact_id VARCHAR(50),
    ghl_pipeline_stage VARCHAR(100),

    -- Status tracking
    clickup_status VARCHAR(20) DEFAULT 'pending',
    drive_status VARCHAR(20) DEFAULT 'pending',
    slack_status VARCHAR(20) DEFAULT 'pending',
    airtable_status VARCHAR(20) DEFAULT 'pending',
    ghl_status VARCHAR(20) DEFAULT 'pending',

    -- Metadata
    setup_started_at TIMESTAMP WITH TIME ZONE,
    setup_completed_at TIMESTAMP WITH TIME ZONE,
    setup_duration_seconds INTEGER,
    setup_status VARCHAR(20) DEFAULT 'in_progress',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### setup_logs Table
```sql
CREATE TABLE setup_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_infrastructure_id UUID REFERENCES project_infrastructure(id),

    action VARCHAR(50) NOT NULL,
    system VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,

    details JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    duration_ms INTEGER,
    api_call_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_setup_logs_project ON setup_logs(project_infrastructure_id);
CREATE INDEX idx_setup_logs_system ON setup_logs(system);
CREATE INDEX idx_setup_logs_created ON setup_logs(created_at);
```

## Environment Variables Required

```bash
# ClickUp
CLICKUP_API_KEY=sk_...
CLICKUP_TEAM_ID=...
CLICKUP_SPACE_ID=...
CLICKUP_TEMPLATE_ID=...

# Google Drive
GOOGLE_SERVICE_ACCOUNT_KEY='...'
GOOGLE_DRIVE_PARENT_FOLDER_ID=...
GOOGLE_DOMAIN=...

# Slack (Optional)
SLACK_BOT_TOKEN=...
SLACK_TEAM_ID=...
SLACK_ENABLED=true

# Airtable
AIRTABLE_API_KEY=...
AIRTABLE_BASE_ID=...
AIRTABLE_PROJECTS_TABLE=...

# GoHighLevel
GHL_API_KEY=...
GHL_LOCATION_ID=...
```

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_internal_setup.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_internal_setup_integration.py -v

# Type checking
mypy app/backend/src/agents/onboarding/internal_setup.py

# Linting
ruff check app/backend/src/agents/onboarding/

# Test all tools
pytest app/backend/__tests__/unit/agents/tools/ -v

# Manual test
python -c "
from app.backend.src.agents.onboarding.internal_setup import InternalSetupAgent
agent = InternalSetupAgent()
print(agent.name)
print(agent.system_prompt[:100] + '...')
"

# Test integration clients
pytest app/backend/__tests__/unit/integrations/ -v
```

## Dependencies to Add

```toml
[tool.poetry.dependencies]
google-api-python-client = "^2.100.0"
google-auth = "^2.25.2"
google-auth-oauthlib = "^1.2.0"
google-auth-httplib2 = "^0.2.0"
slack-sdk = "^3.26.0"
pyairtable = "^2.3.0"

[tool.poetry.group.dev.dependencies]
pytest-mock = "^3.12.0"
responses = "^0.24.0"
```
