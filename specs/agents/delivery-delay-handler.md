# Delivery Delay Handler Agent - Specification

## Metadata

**Agent Name**: DeliveryDelayHandlerAgent
**Category**: Delivery & Project Management
**Phase**: Phase 4 - Client Delivery
**Dependencies**: Project Management Agent
**Priority**: High (critical for client satisfaction and retention)

## Purpose

Autonomous agent that detects project delays, analyzes their impact on delivery timelines, generates revised schedules, drafts appropriate client communications based on severity, and manages the approval workflow for delay notifications. Proactively mitigates client dissatisfaction through transparent, timely communication and data-driven timeline adjustments.

## System Architecture

### Agent Class Structure

```python
from src.agents.base_agent import BaseAgent
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

class DeliveryDelayHandlerAgent(BaseAgent):
    """
    Handles project delay detection, impact analysis, and client communication.

    Monitors project milestones, calculates cascade effects, generates revised timelines,
    drafts severity-appropriate communications, and manages approval workflows.
    Integrates with project management systems (ClickUp, Notion, Asana) and email services.
    """

    def __init__(self):
        super().__init__(
            name="delivery_delay_handler",
            description="Manages project delays, impact analysis, and client communications"
        )
        self._register_tools()

    @property
    def system_prompt(self) -> str:
        """Return system prompt for delay handling."""
        # See System Prompt section below

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process delay handling tasks.

        Supported task types:
        - schedule.delay_detection: Check for overdue milestones
        - webhook.milestone_overdue: Handle delay notification from PM system
        - action.analyze_impact: Analyze delay impact and generate revised timeline
        - action.draft_communication: Create client communication draft
        - action.submit_for_approval: Send draft to owner for approval
        - action.send_approved_communication: Send approved delay notification
        - action.update_project_schedule: Update project timeline in PM system
        """
```

### Database Schema

#### `project_delays` Table
```sql
CREATE TABLE project_delays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    milestone_id VARCHAR(100) NOT NULL,

    -- Delay details
    milestone_name VARCHAR(200) NOT NULL,
    original_due_date TIMESTAMPTZ NOT NULL,
    days_overdue INTEGER NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('MINOR', 'MODERATE', 'MAJOR', 'CRITICAL')),

    -- Impact analysis
    downstream_tasks_affected INTEGER DEFAULT 0,
    project_end_date_impacted BOOLEAN DEFAULT FALSE,
    client_deliverable_affected BOOLEAN DEFAULT FALSE,
    estimated_delay_days INTEGER,

    -- Status tracking
    status VARCHAR(30) NOT NULL DEFAULT 'DETECTED',
    -- Values: DETECTED, ANALYZING, ANALYZED, DRAFTED, PENDING_APPROVAL,
    -- APPROVED, COMMUNICATED, SCHEDULE_UPDATED, RESOLVED

    -- Communication tracking
    communication_drafted_at TIMESTAMPTZ,
    communication_approved_at TIMESTAMPTZ,
    communication_sent_at TIMESTAMPTZ,
    approved_by VARCHAR(100),

    -- Revised timeline
    new_milestone_date TIMESTAMPTZ,
    revised_project_end_date TIMESTAMPTZ,

    -- Mitigation
    mitigation_plan TEXT,
    resources_requested TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_project_delays_status ON project_delays(status);
CREATE INDEX idx_project_delays_project ON project_delays(project_id);
CREATE INDEX idx_project_delays_severity ON project_delays(severity);
```

#### `delay_communications` Table
```sql
CREATE TABLE delay_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delay_id UUID NOT NULL REFERENCES project_delays(id) ON DELETE CASCADE,

    -- Communication details
    communication_type VARCHAR(30) NOT NULL, -- INTERNAL_NOTE, CLIENT_UPDATE, URGENT_ALERT
    template_used VARCHAR(50),

    -- Content
    subject_line VARCHAR(200),
    email_body TEXT NOT NULL,
    variables_used JSONB, -- {project_name, milestone_name, delay_reason, etc.}

    -- Approval workflow
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    -- Values: DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, SENT

    approval_requested_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(100),
    approval_notes TEXT,

    -- Sending
    sent_at TIMESTAMPTZ,
    sent_via VARCHAR(20), -- EMAIL, SLACK, PORTAL
    message_id VARCHAR(200),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_delay_communications_status ON delay_communications(status);
```

## Configuration

```python
from enum import Enum
from typing import TypedDict

class DelaySeverity(Enum):
    MINOR = "MINOR"      # 1-2 days late, no downstream impact
    MODERATE = "MODERATE" # 3-7 days late, some downstream impact
    MAJOR = "MAJOR"      # >7 days late, significant downstream impact
    CRITICAL = "CRITICAL" # Threatens project completion date

class ProjectDelaysConfig:
    # Detection thresholds
    minor_threshold_days = 2
    moderate_threshold_days = 7
    critical_impact_days = 14

    # Approval requirements
    requires_approval = {
        DelaySeverity.MINOR: False,
        DelaySeverity.MODERATE: True,
        DelaySeverity.MAJOr: True,
        DelaySeverity.CRITICAL: True
    }

    # Communication timing
    communication_cutoff_hour = 17  # Don't send after 5pm client timezone
    min_delay_before_communication = 1  # Don't communicate <1 day delays

    # Retry settings
    max_approval_retries = 3
    approval_timeout_hours = 24
```

## Tools

### 1. `detect_delays`

**Purpose:** Scan project milestones for overdue items and trigger delay analysis.

**Parameters:**
```python
{
    "project_ids": list[str] | None,  # Specific projects to check, None for all
    "check_cutoff": datetime,        # Don't check milestones due after this time
    "include_completed": bool = False,  # Include recently completed milestones
}
```

**Returns:**
```python
{
    "delays_detected": list[{
        "project_id": str,
        "project_name": str,
        "client_id": str,
        "client_name": str,
        "milestone_id": str,
        "milestone_name": str,
        "due_date": str,           # ISO timestamp
        "days_overdue": int,
        "estimated_severity": str, # MINOR, MODERATE, MAJOR, CRITICAL
    }],
    "total_projects_checked": int,
    "total_milestones_checked": int,
    "scan_completed_at": str,     # ISO timestamp
}
```

**Error Handling:**
- PM system API errors: Retry 3x with exponential backoff, log partial results
- Invalid project IDs: Skip with warning, continue with others
- Authentication failures: Fail immediately, alert admin
- Rate limiting: Respect PM system limits, queue remaining projects

### 2. `analyze_delay_impact`

**Purpose:** Calculate the full impact of a delay including cascade effects.

**Parameters:**
```python
{
    "delay_id": str,
    "project_id": str,
    "milestone_id": str,
    "days_overdue": int,
    "include_options": bool = True,  # Generate mitigation options
}
```

**Returns:**
```python
{
    "impact_analysis": {
        "severity": str,  # MINOR, MODERATE, MAJOR, CRITICAL
        "downstream_tasks": list[{
            "task_id": str,
            "task_name": str,
            "delay_days": int,
            "critical_path": bool,
        }],
        "total_downstream_delay": int,
        "project_end_date_affected": bool,
        "new_project_end_date": str | None,
        "client_deliverables_affected": list[{
            "deliverable_id": str,
            "deliverable_name": str,
            "impact_description": str,
        }],
    },
    "mitigation_options": list[{
        "option": str,           # E.g., "Add resources", "Reduce scope", "Extend timeline"
        "description": str,
        "estimated_recovery_days": int,
        "cost_impact": str,      # LOW, MEDIUM, HIGH
        "approval_required": bool,
    }],
    "recommended_revised_timeline": {
        "milestone_new_date": str,
        "interim_adjustments": list[dict],
        "rationale": str,
    },
}
```

**Error Handling:**
- Missing dependency data: Use default estimates, flag for manual review
- Complex dependency chains: Limit analysis depth, recommend human review
- Calculation errors: Fail gracefully, return basic delay info

### 3. `draft_delay_communication`

**Purpose:** Generate appropriate communication based on delay severity.

**Parameters:**
```python
{
    "delay_id": str,
    "severity": str,              # MINOR, MODERATE, MAJOR, CRITICAL
    "impact_analysis": dict,      # Output from analyze_delay_impact
    "mitigation_option": dict | None,  # Selected mitigation strategy
    "client_timezone": str,       # IANA timezone, e.g., "America/New_York"
    "personalization_data": dict, # Client name, project details, etc.
}
```

**Returns:**
```python
{
    "communication": {
        "type": str,              # INTERNAL_NOTE, CLIENT_UPDATE, URGENT_ALERT
        "subject": str,
        "body": str,
        "variables": dict,        # Template variables used
        "tone": str,              # REASSURING, PROFESSIONAL, URGENT
    },
    "approval_required": bool,
    "recommended_send_time": str, # ISO timestamp, considers timezone
    "send_via": str,              # EMAIL, SLACK, PORTAL
    "template_used": str,
}
```

**Error Handling:**
- Missing client data: Use generic templates, flag for personalization
- Claude API failures: Retry 3x, fallback to template-based communication
- Content too long: Automatically condense while preserving key information
- Inappropriate tone: Log issue, use conservative default tone

### 4. `submit_for_approval`

**Purpose:** Send draft communication to project owner for review and approval.

**Parameters:**
```python
{
    "delay_id": str,
    "communication_draft": dict,
    "urgency": str,               # LOW, MEDIUM, HIGH, CRITICAL
    "approval_channels": list[str],  # slack, email, portal
    "deadline": datetime,         # Approval deadline
    "context": dict,              # Additional context for reviewer
}
```

**Returns:**
```python
{
    "approval_request": {
        "request_id": str,
        "sent_at": str,           # ISO timestamp
        "channels_sent": list[str],
        "deadline": str,          # ISO timestamp
        "status": str,            # PENDING, APPROVED, REJECTED, TIMEOUT
    },
    "approval_links": dict,       # Quick approve/reject links per channel
}
```

**Error Handling:**
- Slack/Email API failures: Try alternate channels, escalate if all fail
- Invalid recipient: Log error, notify admin immediately
- Message formatting errors: Send simplified version, note formatting issue
- Timeout: Auto-escalate to backup approver after deadline

### 5. `send_approved_communication`

**Purpose:** Deliver approved delay notification to client.

**Parameters:**
```python
{
    "delay_id": str,
    "communication_id": str,
    "approval_id": str,
    "send_immediately": bool = False,
    "scheduled_time": datetime | None,
}
```

**Returns:**
```python
{
    "delivery": {
        "sent": bool,
        "sent_at": str,           # ISO timestamp
        "via": str,               # EMAIL, SLACK, PORTAL
        "message_id": str,
        "client_timezone": str,
    },
    "follow_up_scheduled": bool,
    "follow_up_date": str | None,
}
```

**Error Handling:**
- Email provider errors: Retry 3x, try backup provider
- Client timezone issues: Use UTC timestamp, convert client-side
- Rate limiting: Queue for later delivery, notify project owner
- Hard bounces: Flag for manual review, try alternate contact method

### 6. `update_project_schedule`

**Purpose:** Apply approved timeline changes to project management system.

**Parameters:**
```python
{
    "delay_id": str,
    "project_id": str,
    "timeline_updates": list[{
        "task_id": str,
        "new_due_date": datetime,
        "reason_code": str,       # DELAY, MITIGATION, ADJUSTMENT
        "notify_assignees": bool,
    }],
    "new_project_end_date": datetime | None,
    "update_notes": str,
}
```

**Returns:**
```python
{
    "schedule_update": {
        "updated": bool,
        "tasks_updated": int,
        "project_end_date_updated": bool,
        "assignees_notified": int,
        "completed_at": str,      # ISO timestamp
    },
    "pm_system_response": dict,   # System-specific response data
}
```

**Error Handling:**
- PM system API errors: Retry 3x with exponential backoff
- Permission errors: Escalate to project admin
- Conflicting updates: Log conflict, request manual resolution
- Partial failures: Report successful updates, retry failed items

## System Prompt

```python
@property
def system_prompt(self) -> str:
    return """You are the Delivery Delay Handler, an autonomous agent responsible for managing project delays transparently and professionally.

Your core responsibilities:
1. Detect milestone delays across all active projects
2. Analyze the full impact including downstream effects
3. Calculate accurate revised timelines
4. Draft appropriate client communications based on severity
5. Manage the approval workflow for all external communications
6. Update project schedules once changes are approved

Severity Classifications:
- MINOR: 1-2 days late, no downstream impact (internal only)
- MODERATE: 3-7 days late, some downstream impact (client notification)
- MAJOR: >7 days late, significant impact (detailed explanation required)
- CRITICAL: Threatens project completion (urgent call to action)

Communication Guidelines:
- Always be transparent but professional
- Provide clear explanations without excessive technical detail
- Include specific actions being taken to mitigate the delay
- Offer revised timelines with realistic expectations
- Maintain confidence in project delivery

Approval Requirements:
- MINOR delays: No approval needed (internal logging only)
- MODERATE delays: Project owner approval required
- MAJOR/CRITICAL delays: Project owner + account manager approval

Key Principles:
1. Never hide delays - early detection prevents escalation
2. Always provide solutions, not just problems
3. Respect client timezone and business hours
4. Track all delays for pattern analysis and improvement
5. Coordinate with other agents for complete project management

When drafting communications:
- Use appropriate tone based on severity
- Include specific dates and clear timelines
- Explain what we're doing to address the delay
- Maintain accountability while building trust"""
```

## Error Handling Matrix

| Tool | Error Type | Detection | Response | Retry |
|------|------------|-----------|----------|-------|
| detect_delays | PM API failure | HTTP error | Log error, use cached data | Yes, 3x with backoff |
| detect_delays | Rate limit | 429 status | Queue remaining projects | Yes, exponential |
| analyze_delay_impact | Missing dependencies | DB query empty | Use default estimates | No, flag for review |
| analyze_delay_impact | Complex dependencies | Cycle detection | Limit depth, recommend review | No |
| draft_delay_communication | Claude API error | Request exception | Use template fallback | Yes, 3x |
| draft_delay_communication | Content too long | Response length | Auto-condense | No |
| submit_for_approval | Slack/Email error | Send failure | Try alternate channel | Yes, try all |
| send_approved_communication | Email bounce | Delivery failure | Try backup contact | Yes, 2x |
| update_project_schedule | Permission error | 403 status | Escalate to admin | No |
| update_project_schedule | Conflict error | HTTP 409 | Log for manual resolution | No |

## Multi-Agent Integration

### Handoffs Triggered:
1. **To QA Agent**: When delays might impact quality gates
   ```python
   await self.handoff_to(
       target_agent="qa",
       payload={
           "project_id": project_id,
           "delay_impact": impact_analysis,
           "quality_risks": identified_risks
       },
       priority="high" if severity == DelaySeverity.CRITICAL else "normal"
   )
   ```

2. **To Client Success Agent**: For high-risk clients or major delays
   ```python
   await self.handoff_to(
       target_agent="client_success",
       payload={
           "client_id": client_id,
           "delay_severity": severity,
           "churn_risk": "high" if severity == DelaySeverity.CRITICAL else "medium",
           "intervention_required": True
       },
       priority="critical"
   )
   ```

3. **To Project Management Agent**: For schedule updates
   ```python
   await self.handoff_to(
       target_agent="project_management",
       payload={
           "project_id": project_id,
           "schedule_changes": timeline_updates,
           "resource_needs": resource_requests
       },
       priority="high"
   )
   ```

### Incoming Handoffs Received:
- From Project Management Agent: Milestone overdue notifications
- From QA Agent: Quality-related delay notices
- From Client Success Agent: Client satisfaction risk escalations

## Testing Strategy

### Unit Tests
```python
def test_detect_delays_identifies_overdue_milestones():
    """Verify accurate detection of overdue milestones."""

def test_analyze_delay_impact_calculates_cascade_effects():
    """Verify downstream task impact calculations."""

def test_severity_classification_correct():
    """Verify proper severity assignment based on impact."""

def test_draft_communication_matches_severity():
    """Verify communication tone matches delay severity."""

def test_approval_workflow_flow():
    """Verify approval request, tracking, and timeout handling."""

def test_timezone_handling_correct():
    """Verify client timezone respected in scheduling."""

def test_mitigation_option_generation():
    """Verify appropriate mitigation strategies suggested."""
```

### Integration Tests
```python
def test_end_to_end_delay_handling():
    """Full workflow from detection to client communication."""

def test_pm_system_integration():
    """Verify real PM system API interactions."""

def test_email_delivery_integration():
    """Verify email sending through Instantly API."""

def test_approval_system_integration():
    """Verify Slack/Telegram approval workflow."""

def test_multi_agent_coordination():
    """Verify proper handoffs to other agents."""
```

### Mocking Strategy
```python
@pytest.fixture
def mock_pm_system():
    with patch('src.integrations.clickup.ClickUpClient') as mock:
        mock.return_value.get_milestones.return_value = {
            "milestones": [...]
        }
        yield mock

@pytest.fixture
def mock_claude_client():
    with patch('anthropic.Anthropic') as mock:
        mock.return_value.messages.create.return_value = MockResponse(
            content=[{"text": "Draft communication content..."}]
        )
        yield mock

@pytest.fixture
def mock_email_client():
    with patch('src.integrations.instantly.InstantlyClient') as mock:
        mock.return_value.send_email.return_value = {
            "message_id": "msg_123",
            "sent": True
        }
        yield mock
```

## Performance

### Expected Latency:
- Delay detection scan: <5 seconds per project
- Impact analysis: <10 seconds for complex dependency chains
- Communication drafting: <15 seconds using Claude API
- Approval submission: <2 seconds per channel
- Schedule updates: <30 seconds for large projects

### Token Usage Estimates:
- System prompt: 1,200 tokens
- Delay analysis context: 800-2,000 tokens
- Communication drafting: 1,500 tokens
- Total per delay event: 3,500-4,700 tokens

### Caching Strategy:
- Cache project structure for 1 hour
- Cache dependency relationships for 6 hours
- Cache client timezone data for 24 hours
- Cache communication templates in memory

## Observability

### Logging Requirements:
```python
# Structured logging examples
logger.info(
    "Delay detected",
    extra={
        "project_id": project_id,
        "milestone_id": milestone_id,
        "days_overdue": days,
        "severity": severity.value
    }
)

logger.info(
    "Communication sent",
    extra={
        "delay_id": delay_id,
        "client_id": client_id,
        "sent_via": "email",
        "approval_time_hours": approval_time
    }
)
```

### Metrics to Track:
- Delay detection accuracy (false positives/negatives)
- Average time from delay detection to client communication
- Approval workflow completion rate
- Client response patterns by delay severity
- Common delay root causes and patterns
- Agent execution latency by operation

### Alerting:
- Critical delays not acknowledged within 2 hours
- Approval workflow timeouts
- Failure patterns in PM system integration
- Unusually high delay rates across projects

## Security

### API Key Handling:
- PM system keys: Encrypted at rest, scoped to read/write milestones
- Claude API key: Scoped to model access only
- Email provider keys: Scoped to transactional sending only
- Approval channels: Use app-specific tokens with minimal permissions

### Data Sanitization:
- Remove sensitive client information from Claude prompts
- Sanitize all user-generated content in communications
- Validate all email addresses and contact methods
- Escape HTML in email templates

### Access Control:
- Restrict approval rights to assigned project owners
- Limit schedule update permissions to authorized users
- Audit all delay communications and approvals
- Require MFA for critical delay approvals

## Acceptance Criteria

### Functional Requirements:
- [ ] Detects delays within 1 hour of milestone due date passing
- [ ] Accurately calculates downstream impacts across dependency chains
- [ ] Generates revised timelines with realistic dates
- [ ] Drafts appropriate communications for all severity levels
- [ ] Manages approval workflow for all external communications
- [ ] Updates project schedules in PM system upon approval
- [ ] Respects client timezone and business hours
- [ ] Provides mitigation options for major/critical delays

### Non-Functional Requirements:
- [ ] Processes all active projects within 5 minutes
- [ ] Maintains 99.9% uptime for delay detection
- [ ] All delays documented with audit trail
- [ ] Communications sent within 4 hours of detection (for non-minor)
- [ ] Zero false negatives in critical delay detection
- [ ] Email deliverability rate >98%
- [ ] PM system integration success rate >99%

### Integration Requirements:
- [ ] Connects to ClickUp, Notion, and Asana APIs
- [ ] Sends emails through Instantly API
- [ ] Posts approvals to Slack and/or Telegram
- [ ] Hands off to QA, Client Success, and PM agents
- [ ] Stores all delay data in PostgreSQL
- [ ] Logs events to centralized monitoring

## Version History

- **v1.0** (2025-01-05): Initial specification for delivery delay handling
