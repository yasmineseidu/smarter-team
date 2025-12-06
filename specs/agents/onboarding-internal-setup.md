# Internal Setup Agent - Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Priority:** Phase 4 - Client Delivery
**Agent Type:** Automation + Infrastructure
**Coverage Target:** >85%

---

## Overview

The Internal Setup Agent creates and configures all internal project infrastructure for new clients. It automates the setup of ClickUp projects, Google Drive folder structures, Slack channels, Airtable records, and GoHighLevel entries. The agent ensures all systems are linked, permissions are set, and templates are applied consistently across the organization's tech stack.

**Key Responsibilities:**
- Create ClickUp project from template with task lists and automations
- Set up Google Drive folder structure with proper sharing permissions
- Create optional Slack channels for client communication
- Generate Airtable project records linked to client data
- Update GoHighLevel contact records with project information
- Track setup progress and handle partial failures gracefully
- Log all infrastructure creation for audit and rollback

---

## Agent Configuration

### BaseAgent Properties

```python
name: "internal_setup"
description: "Creates internal project infrastructure across ClickUp, Drive, Slack, Airtable, and GHL"
```

### Dependencies

**Agent Dependencies:**
- `onboarding_orchestrator` - Triggers internal setup after intake forms

**Integration Dependencies:**
- ClickUp API (project creation, task management)
- Google Drive API (folder creation, sharing)
- Slack API (channel creation, invitations)
- Airtable API (record creation, linking)
- GoHighLevel API (contact updates)
- Database (progress tracking, logging)

---

## System Prompt

```
You are the Internal Setup Agent for Smarter Team, an AI agency automation system.

Your role is to create and configure all internal infrastructure for new client projects.

RESPONSIBILITIES:
1. ClickUp Setup: Create projects from templates, configure spaces, set due dates, assign team members
2. Google Drive: Create folder structures, set permissions, move contracts, apply templates
3. Slack Channels: Create client channels, invite team members, post welcome messages
4. Airtable Records: Create project entries, link to client records, set status
5. GoHighLevel: Update contact records, add tags, set pipeline stages
6. Progress Tracking: Monitor all setup steps, log progress, handle failures
7. System Linking: Connect all platforms with cross-references and IDs

FOLDER STRUCTURE TEMPLATE:
Clients/{client_name}/
├── 01-Contracts/
│   ├── proposal.pdf
│   └── signed-contract.pdf
├── 02-Deliverables/
│   ├── phase-1/
│   ├── phase-2/
│   └── final/
├── 03-Assets/
│   ├── logos/
│   ├── brand-guidelines/
│   └── content/
├── 04-Meeting-Notes/
│   └── kickoff-notes.md
└── 05-Research/
    └── initial-research.md

CLICKUP PROJECT SETUP:
- Project name: "{client_name} - {project_name}"
- Use standard project template
- Create task lists: Discovery, Design, Development, Review, Launch
- Set due dates based on project timeline
- Assign team members based on project type
- Configure automations: task reminders, status updates

SLACK CHANNEL (if enabled):
- Channel name: #client-{client_slug}
- Invite: project manager, lead developer, account manager
- Pin: Google Drive link, ClickUp link, Airtable link
- Welcome message with project overview

ERROR HANDLING RULES:
- If ClickUp fails: Retry 3x, then create placeholder in Airtable
- If Google Drive fails: Retry 3x, use shared folder temporarily
- If Slack fails: Skip, notify project manager via email
- If Airtable fails: Retry 3x, critical failure if persists
- If GHL fails: Log error, continue with other systems

TIMEOUTS:
- ClickUp operations: 30 seconds
- Google Drive operations: 45 seconds
- Slack operations: 20 seconds
- Airtable operations: 25 seconds
- GHL operations: 20 seconds

PERMISSIONS:
- Google Drive: Team editors, client viewers (Contract folder only)
- ClickUp: Full access to team, view-only for client
- Slack: Team members auto-joined, client invited later

VALIDATION:
- Verify all folders created successfully
- Confirm ClickUp project accessible
- Test Airtable record links
- Check cross-references working

LOGGING:
- Log every action with timestamps
- Record all IDs for cross-referencing
- Track partial successes and failures
- Store rollback information

You execute tasks methodically, validate each step, and handle partial failures gracefully. You ensure all systems are connected and working before considering setup complete.
```

---

## Tools

### Tool: create_clickup_project

**Purpose:** Create a ClickUp project from template with configured spaces, lists, and tasks

**Input Schema:**
```python
class CreateClickUpProjectInput(BaseModel):
    client_name: str = Field(..., description="Client display name")
    client_slug: str = Field(..., description="URL-friendly client identifier")
    project_name: str = Field(..., description="Project title")
    timeline_days: int = Field(ge=7, le=365, description="Project duration in days")
    team_members: list[str] = Field(default=[], description="ClickUp user IDs to assign")
    space_id: str = Field(..., description="ClickUp space ID for project")
    template_id: str | None = Field(None, description="Optional project template ID")
```

**Output Schema:**
```python
class CreateClickUpProjectOutput(BaseModel):
    success: bool
    project_id: str | None = None
    project_url: str | None = None
    error_message: str | None = None
    created_lists: list[str] = []
    assigned_tasks: int = 0
```

**Error Handling:**
- Invalid space ID → Return validation error
- Template not found → Create with default structure
- Rate limit (429) → Exponential backoff, max 3 retries
- Permission denied → Fail and alert admin
- Network timeout → Retry 2x with longer timeout

**Example:**
```python
# Input
{
    "client_name": "Acme Corp",
    "client_slug": "acme-corp",
    "project_name": "AI Chatbot",
    "timeline_days": 30,
    "team_members": ["user123", "user456"],
    "space_id": "space789"
}

# Output
{
    "success": true,
    "project_id": "proj123",
    "project_url": "https://clickup.com/p/proj123",
    "created_lists": ["Discovery", "Design", "Development"],
    "assigned_tasks": 15
}
```

### Tool: create_drive_structure

**Purpose:** Create Google Drive folder structure with permissions and templates

**Input Schema:**
```python
class CreateDriveStructureInput(BaseModel):
    client_name: str = Field(..., description="Client name for folder")
    client_email: str | None = Field(None, description="Client email for sharing")
    contract_file_id: str | None = Field(None, description="Drive ID of signed contract")
    parent_folder_id: str = Field(..., description="Parent folder (Clients folder ID)")
    team_emails: list[str] = Field(default=[], description="Team member emails for permissions")
    share_with_client: bool = Field(True, description="Share Contracts folder with client")
```

**Output Schema:**
```python
class CreateDriveStructureOutput(BaseModel):
    success: bool
    client_folder_id: str | None = None
    folder_ids: dict[str, str] = {}
    share_links: dict[str, str] = {}
    error_message: str | None = None
    permissions_set: list[str] = []
```

**Error Handling:**
- Parent folder not found → Create Clients folder if missing
- Permission denied → Check service account permissions
- Quota exceeded → Log warning, continue with basic structure
- Contract file not found → Log warning, continue without moving
- Sharing failed → Set permissions manually later

**Example:**
```python
# Input
{
    "client_name": "Acme Corp",
    "client_email": "client@acme.com",
    "contract_file_id": "file123",
    "parent_folder_id": "parent456",
    "team_emails": ["team@smarterteam.com"],
    "share_with_client": True
}

# Output
{
    "success": true,
    "client_folder_id": "folder789",
    "folder_ids": {
        "root": "folder789",
        "contracts": "folder790",
        "deliverables": "folder791"
    },
    "share_links": {
        "contracts": "https://drive.google.com/drive/folders/folder790"
    },
    "permissions_set": ["team@smarterteam.com", "client@acme.com"]
}
```

### Tool: create_slack_channel

**Purpose:** Create Slack channel and invite team members (optional)

**Input Schema:**
```python
class CreateSlackChannelInput(BaseModel):
    client_slug: str = Field(..., description="URL-safe client identifier")
    channel_name: str | None = Field(None, description="Custom channel name")
    team_user_ids: list[str] = Field(default=[], description="Slack user IDs to invite")
    is_private: bool = Field(False, description="Create private channel")
    purpose: str = Field("Client project communication", description="Channel purpose")
```

**Output Schema:**
```python
class CreateSlackChannelOutput(BaseModel):
    success: bool
    channel_id: str | None = None
    channel_name: str | None = None
    invite_link: str | None = None
    members_added: int = 0
    error_message: str | None = None
```

**Error Handling:**
- Slack not configured → Skip gracefully, log info
- Channel name exists → Append random suffix
- User not found → Continue with other users
- Rate limit → Skip Slack, notify project manager
- Permission denied → Alert workspace admin

**Example:**
```python
# Input
{
    "client_slug": "acme-corp",
    "team_user_ids": ["U123", "U456"],
    "is_private": True,
    "purpose": "AI Chatbot project for Acme Corp"
}

# Output
{
    "success": true,
    "channel_id": "C789",
    "channel_name": "client-acme-corp",
    "invite_link": "https://slack.com/join/C789",
    "members_added": 2
}
```

### Tool: create_airtable_record

**Purpose:** Create Airtable project record and link to client record

**Input Schema:**
```python
class CreateAirtableRecordInput(BaseModel):
    client_record_id: str = Field(..., description="Airtable ID of client record")
    project_name: str = Field(..., description="Project title")
    client_name: str = Field(..., description="Client company name")
    clickup_project_id: str | None = Field(None, description="ClickUp project ID")
    drive_folder_id: str | None = Field(None, description="Google Drive folder ID")
    slack_channel_id: str | None = Field(None, description="Slack channel ID")
    start_date: date = Field(..., description="Project start date")
    expected_end_date: date = Field(..., description="Expected completion date")
    project_type: str = Field(..., description="Type of project")
    budget: float | None = Field(None, description="Project budget")
```

**Output Schema:**
```python
class CreateAirtableRecordOutput(BaseModel):
    success: bool
    record_id: str | None = None
    record_url: str | None = None
    error_message: str | None = None
    fields_updated: list[str] = []
```

**Error Handling:**
- Client record not found → Fail with clear error
- Invalid table ID → Check Airtable base configuration
- Field validation error → Use defaults for missing fields
- Rate limit → Exponential backoff, max 3 retries
- Permission denied → Alert Airtable admin

**Example:**
```python
# Input
{
    "client_record_id": "rec123",
    "project_name": "AI Chatbot",
    "client_name": "Acme Corp",
    "clickup_project_id": "proj456",
    "drive_folder_id": "folder789",
    "start_date": "2025-01-15",
    "expected_end_date": "2025-02-15",
    "project_type": "AI Development",
    "budget": 25000.00
}

# Output
{
    "success": true,
    "record_id": "rec789",
    "record_url": "https://airtable.com/rec789",
    "fields_updated": ["Project Name", "Client", "ClickUp", "Drive", "Status"]
}
```

### Tool: update_ghl_contact

**Purpose:** Update GoHighLevel contact with project information and tags

**Input Schema:**
```python
class UpdateGhlContactInput(BaseModel):
    contact_id: str = Field(..., description="GHL contact ID")
    client_name: str = Field(..., description="Client company name")
    project_name: str = Field(..., description="Project title")
    project_status: str = Field("Active", description="Project status")
    pipeline_stage: str = Field("Active Projects", description="Pipeline stage to move to")
    tags: list[str] = Field(default=[], description="Tags to add/remove")
    custom_fields: dict[str, Any] = Field(default={}, description="Custom field updates")
```

**Output Schema:**
```python
class UpdateGhlContactOutput(BaseModel):
    success: bool
    contact_id: str | None = None
    pipeline_stage: str | None = None
    tags_applied: list[str] = []
    error_message: str | None = None
```

**Error Handling:**
- Contact not found → Log error, continue with other systems
- Invalid pipeline stage → Use default "Active Projects"
- Rate limit (429) → Exponential backoff, max 3 retries
- Permission denied → Alert GHL admin
- Network timeout → Retry 2x, then skip

**Example:**
```python
# Input
{
    "contact_id": "contact123",
    "client_name": "Acme Corp",
    "project_name": "AI Chatbot",
    "project_status": "Active",
    "pipeline_stage": "Active Projects",
    "tags": ["AI Client", "2025-Q1"],
    "custom_fields": {"project_start": "2025-01-15"}
}

# Output
{
    "success": true,
    "contact_id": "contact123",
    "pipeline_stage": "Active Projects",
    "tags_applied": ["AI Client", "2025-Q1", "Active Project"]
}
```

### Tool: verify_setup_complete

**Purpose:** Verify all infrastructure is created and accessible

**Input Schema:**
```python
class VerifySetupCompleteInput(BaseModel):
    project_id: str = Field(..., description="Project tracking ID")
    clickup_project_id: str | None = Field(None, description="ClickUp project to verify")
    drive_folder_id: str | None = Field(None, description="Drive folder to verify")
    airtable_record_id: str | None = Field(None, description="Airtable record to verify")
    ghl_contact_id: str | None = Field(None, description="GHL contact to verify")
    slack_channel_id: str | None = Field(None, description="Slack channel to verify")
```

**Output Schema:**
```python
class VerifySetupCompleteInput(BaseModel):
    success: bool
    verification_results: dict[str, bool] = {}
    failed_systems: list[str] = []
    setup_complete: bool = False
    error_message: str | None = None
```

**Error Handling:**
- Any system inaccessible → Mark as failed, log details
- Partial failures → Report what's working, continue
- All systems fail → Major error, escalate immediately

---

## Error Handling Matrix

| System | Error Type | Detection | Response | Retry |
|--------|------------|-----------|----------|-------|
| ClickUp | Rate limit (429) | HTTP status | Backoff retry | Yes, 3x |
| ClickUp | Auth error (401) | HTTP status | Fail immediately | No |
| ClickUp | Timeout | Exception | Retry with longer timeout | Yes, 2x |
| Drive | Quota exceeded | API response | Log warning, continue | No |
| Drive | Permission denied | HTTP status | Check permissions | Yes, 1x |
| Drive | File not found | API response | Log and continue | No |
| Slack | Not configured | Config missing | Skip gracefully | No |
| Slack | Channel exists | API response | Append suffix | No |
| Airtable | Invalid record | Validation error | Fail with details | No |
| Airtable | Rate limit | HTTP status | Backoff retry | Yes, 3x |
| GHL | Contact not found | API response | Log error, continue | No |
| GHL | Invalid pipeline | Validation error | Use default | No |

### Recovery Strategies

1. **ClickUp Failure:**
   - Retry with exponential backoff (1s, 2s, 4s)
   - If still failing: Create placeholder in Airtable
   - Alert project manager via email

2. **Google Drive Failure:**
   - Check service account permissions
   - Create in shared folder as fallback
   - Set permissions manually if API fails

3. **Slack Failure:**
   - Non-critical, skip if unavailable
   - Send project links via email instead
   - Try again later when available

4. **Airtable Failure:**
   - Critical for project tracking
   - Retry aggressively with backoff
   - Escalate to admin if persistent

5. **GHL Failure:**
   - Non-critical for internal ops
   - Log error, continue with setup
   - Sync later when available

---

## Multi-Agent Integration

### Handoff FROM (Input)
Receives tasks from `onboarding_orchestrator`:
```python
{
    "type": "internal_setup",
    "client_id": "uuid",
    "project_id": "uuid",
    "client_name": "Acme Corp",
    "client_slug": "acme-corp",
    "project_name": "AI Chatbot",
    "project_timeline_days": 30,
    "team_members": ["user123"],
    "signed_contract_url": "https://...",
    "client_email": "client@acme.com"
}
```

### Handoff TO (Output)
Reports completion back to `onboarding_orchestrator`:
```python
{
    "type": "setup_complete",
    "client_id": "uuid",
    "project_id": "uuid",
    "status": "success|partial_failure|failed",
    "infrastructure": {
        "clickup_project_id": "proj123",
        "clickup_url": "https://clickup.com/p/proj123",
        "drive_folder_id": "folder456",
        "drive_url": "https://drive.google.com/drive/folders/folder456",
        "airtable_record_id": "rec789",
        "airtable_url": "https://airtable.com/rec789",
        "ghl_contact_id": "contact012",
        "slack_channel_id": "C345",
        "slack_channel": "#client-acme-corp"
    },
    "setup_completed_at": "2025-01-15T10:30:00Z",
    "errors": [],
    "warnings": []
}
```

### Escalation Rules
- Complete failure (all systems) → Immediate escalation to admin
- Partial failure (some systems) → Log warning, continue with onboarding
- GHL/Slack failures → Non-critical, note in handoff
- ClickUp/Airtable failures → Critical, retry before escalation

---

## Testing Strategy

### Unit Tests

```python
# Tool Input Validation
def test_create_clickup_project_validates_required_fields():
    """Test all required fields are validated"""

def test_create_drive_structure_handles_special_chars():
    """Test special characters in client names"""

# Error Handling
def test_clickup_rate_limit_retry():
    """Verify exponential backoff on 429"""

def test_drive_permission_denied_handling():
    """Test graceful handling of permission errors"""

def test_slack_not_configured_skips():
    """Verify graceful skip when Slack missing"""

# Success Cases
def test_full_setup_success():
    """Test complete successful setup flow"""

def test_partial_setup_recovery():
    """Test handling of some systems failing"""

# Data Validation
def test_folder_structure_created():
    """Verify all required folders are created"""

def test_permissions_applied():
    """Test team permissions are set correctly"""
```

### Integration Tests

```python
# End-to-End Flow
def test_end_to_end_infrastructure_setup():
    """Full setup with mocked APIs"""

def test_cross_platform_links():
    """Verify IDs are correctly linked between systems"""

# Real API Tests (Staging)
def test_clickup_api_integration():
    """Actual ClickUp API calls (staging)"""

def test_drive_api_integration():
    """Actual Google Drive API calls"""

# Failure Scenarios
def test_api_timeout_recovery():
    """Test behavior when APIs timeout"""

def test_partial_failure_reporting():
    """Verify partial failures reported correctly"""
```

### Mock Strategy

```python
# ClickUp Mock
@pytest.fixture
def mock_clickup_client():
    with patch('src.integrations.clickup.ClickUpClient') as mock:
        mock.create_project.return_value = {"id": "proj123", "url": "..."}
        mock.create_list.return_value = {"id": "list456"}
        yield mock

# Google Drive Mock
@pytest.fixture
def mock_drive_client():
    with patch('src.integrations.drive.DriveClient') as mock:
        mock.create_folder.return_value = {"id": "folder789"}
        mock.share_folder.return_value = {"success": True}
        yield mock

# Combined Mock for Full Flow
@pytest.fixture
def mock_all_integrations():
    """Mock all integration clients for full flow testing"""
    with patch.multiple(
        'src.integrations',
        clickup=MagicMock(),
        drive=MagicMock(),
        slack=MagicMock(),
        airtable=MagicMock(),
        ghl=MagicMock()
    ) as mocks:
        yield mocks
```

---

## Performance

### Expected Latency
- ClickUp project creation: 5-10 seconds
- Google Drive structure: 10-20 seconds
- Slack channel: 2-5 seconds
- Airtable record: 2-3 seconds
- GHL update: 1-2 seconds
- **Total setup time:** ~30-45 seconds

### Rate Limits
- ClickUp: 100 requests/minute
- Google Drive: 1,000 requests/100 seconds
- Slack: 1 request/second (free), 20+ (paid)
- Airtable: 5 requests/second
- GHL: 100 requests/minute

### Caching Strategy
- Cache team member IDs for 1 hour
- Cache template IDs for 24 hours
- Cache folder structure templates
- Rate limit responses cached for window duration

---

## Observability

### Logging Requirements
```python
# Structured logging for each action
logger.info(
    "Creating ClickUp project",
    extra={
        "client_id": client_id,
        "project_name": project_name,
        "template_id": template_id
    }
)

# Error context
logger.error(
    "ClickUp API rate limited",
    extra={
        "retry_count": retry_count,
        "retry_after": retry_after,
        "client_id": client_id
    }
)

# Success completion
logger.info(
    "Internal setup completed",
    extra={
        "client_id": client_id,
        "systems_created": ["clickup", "drive", "airtable"],
        "duration_seconds": 42.5,
        "partial_failures": ["slack"]
    }
)
```

### Metrics to Track
- Setup success rate (overall and per system)
- Average setup duration
- Retry counts per system
- Error rates by type
- Time from onboarding start to setup complete

### Monitoring Alerts
- >50% setup failure rate → Alert immediately
- Any system down >5 minutes → Alert
- Setup duration >2 minutes → Warning
- Multiple retry failures → Alert admin

---

## Security

### API Key Handling
- All API keys stored in environment variables
- Encrypted at rest in database
- Rotated quarterly
- Minimal permissions per key

### Data Sanitization
- Sanitize folder names (remove special chars)
- Validate all user inputs
- Escape HTML in descriptions
- No sensitive data in logs

### Permissions Model
- **ClickUp:** Project management permissions only
- **Google Drive:** Full access to team folder, read-only elsewhere
- **Slack:** Channel creation and invitation only
- **Airtable:** Project table read/write
- **GHL:** Contact read/write, pipeline access

---

## Acceptance Criteria

- [ ] ClickUp project created from template with correct name
- [ ] All required task lists created and populated
- [ ] Google Drive folder structure matches template exactly
- [ ] Team permissions correctly applied on Drive folders
- [ ] Signed contract moved to Contracts folder if provided
- [ ] Slack channel created (if enabled) with team members invited
- [ ] Airtable project record created and linked to client
- [ ] All cross-platform IDs stored and linked
- [ ] GoHighLevel contact updated with project info
- [ ] Setup verification passes for all successful systems
- [ ] Partial failures handled gracefully with appropriate logging
- [ ] Complete handoff payload sent to onboarding orchestrator
- [ ] All actions logged with timestamps and context
- [ ] Error recovery works for all documented scenarios
- [ ] Rate limits respected with appropriate backoff
- [ ] Security permissions applied correctly

---

## Configuration Examples

### Environment Variables
```bash
# ClickUp
CLICKUP_API_KEY=sk_123...
CLICKUP_TEAM_ID=team456
CLICKUP_SPACE_ID=space789
CLICKUP_TEMPLATE_ID=template012

# Google Drive
GOOGLE_SERVICE_ACCOUNT_KEY='{"type": "service_account", ...}'
GOOGLE_DRIVE_PARENT_FOLDER_ID=parent345
GOOGLE_DOMAIN=smarterteam.com

# Slack (Optional)
SLACK_BOT_TOKEN=xoxb-123...
SLACK_TEAM_ID=T123...
SLACK_ENABLED=true

# Airtable
AIRTABLE_API_KEY=key123...
AIRTABLE_BASE_ID=app456...
AIRTABLE_PROJECTS_TABLE=tbl789...

# GoHighLevel
GHL_API_KEY=v2_123...
GHL_LOCATION_ID=loc456...
```

### Agent Configuration
```python
INTERNAL_SETUP_CONFIG = {
    "clickup": {
        "default_template": "template012",
        "auto_assign_tasks": True,
        "create_custom_fields": True
    },
    "drive": {
        "share_with_team": True,
        "share_with_client": False,
        "client_permissions": "reader"
    },
    "slack": {
        "create_channel": True,
        "is_private": False,
        "auto_invite": ["project_manager", "lead_dev"]
    },
    "airtable": {
        "auto_link_client": True,
        "set_status": "Active",
        "create_custom_views": True
    },
    "ghl": {
        "update_pipeline": True,
        "add_tags": ["Active Project", "2025"],
        "move_to_stage": "Active Projects"
    }
}
```
