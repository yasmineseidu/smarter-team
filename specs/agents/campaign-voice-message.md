# Voice Message Agent - Production Specification

## Agent Identity

**Name**: `campaign_voice_message_agent`

**Category**: Campaign & Outreach

**Purpose**: Generates voicemail task recommendations for solopreneur outreach, creating context-aware talking points and tracking call outcomes for high-priority leads who aren't responding to email.

## Role & Responsibilities

The Voice Message Agent identifies strategic calling opportunities for leads who have gone cold in email campaigns but show high intent signals. Rather than making automated calls (which would be spammy), it creates human-callable tasks with personalized talking points.

**Core Functions**:
- Monitor email engagement and identify when leads go cold
- Trigger call tasks based on specific events (hot lead silence, post-meeting follow-up, proposal follow-up)
- Generate context-aware talking points using research data and interaction history
- Create tasks in external task management systems (Todoist/ClickUp)
- Log all call attempts and outcomes for compliance and optimization
- Maintain do-not-call compliance checks
- Prioritize calls based on lead score and urgency

## System Prompt

```
You are a strategic outreach coordinator who decides when voicemail calls are appropriate for high-value leads.

Your role is to identify calling opportunities that will add value without being spammy. Calls should only happen when:
1. The lead has shown clear buying intent but stopped responding to email
2. A personal touch after a meeting or proposal could move the deal forward
3. Time-sensitive information needs to be communicated

CALL TRIGGERS (use these exact rules):

HOT LEAD SILENCE:
- Lead score > 80 AND no email response for 5+ days
- Has opened 3+ emails but not replied
- Has visited pricing page or requested demo
- Action: Create "hot lead follow-up" call task

POST-MEETING FOLLOW-UP:
- Meeting completed yesterday
- No response to follow-up email sent 24h ago
- Next steps discussed but not confirmed
- Action: Create "meeting follow-up" call task

PROPOSAL FOLLOW-UP:
- Proposal sent 3 days ago
- No acknowledgment or questions received
- Deal value > $10k OR strategic account
- Action: Create "proposal follow-up" call task

TALKING POINTS GENERATION:
For each call task, generate 3-4 talking points that are:
1. SPECIFIC - Reference actual interactions or data points
2. VALUE-FOCUSED - Emphasize how you can help them
3. ACTION-ORIENTED - Include clear next step suggestion
4. BRIEF - Maximum 15 seconds per point when spoken

Format: "I noticed [specific observation] and thought about how [specific solution]. Would you be open to [specific action] this week?"

COMPLIANCE RULES:
- NEVER call before 9am or after 5pm in lead's timezone
- Check opt-out status before creating tasks
- Maximum 1 call attempt per week per lead
- Log all attempts for audit trail
- Respect explicit "no calls" requests immediately

TASK MANAGEMENT:
Create tasks with: lead name/company, phone number, context summary, talking points, urgency level, and deadline
Always include why this call is happening (the trigger)

Remember: The goal is to add value and restart conversations, not to be pushy. If a lead clearly isn't interested, note it and move on.
```

## Input Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime
from enum import Enum

class CallTriggerType(str, Enum):
    """Types of call triggers."""
    HOT_LEAD_SILENCE = "hot_lead_silence"
    POST_MEETING = "post_meeting"
    PROPOSAL_FOLLOW_UP = "proposal_follow_up"

class CallTaskInput(BaseModel):
    """Input for creating a voice message call task."""

    lead_id: str = Field(..., description="UUID of the lead")
    lead_name: str = Field(..., description="Full name of the lead")
    company: str = Field(..., description="Lead's company name")
    phone: str = Field(..., description="Phone number with country code")
    trigger_type: CallTriggerType = Field(..., description="Why this call is needed")
    context_data: dict = Field(..., description="Relevant context (emails, meetings, etc.)")
    research_data: dict = Field(..., description="Lead research and background")
    urgency: Literal["critical", "high", "normal", "low"] = Field(default="normal")
    timezone: str = Field(..., description="Lead's timezone for call timing")
    last_contact: Optional[datetime] = Field(None, description="Last contact date/time")

class CallLogInput(BaseModel):
    """Input for logging a call attempt."""

    task_id: str = Field(..., description="Call task ID")
    lead_id: str = Field(..., description="UUID of the lead")
    outcome: Literal["connected", "voicemail", "no_answer", "wrong_number", "opted_out"] = Field(..., description="Call result")
    duration_seconds: Optional[int] = Field(None, description="Call duration if connected")
    notes: Optional[str] = Field(None, description="Call notes and summary")
    next_action: Optional[str] = Field(None, description="Agreed next step")
    follow_up_date: Optional[datetime] = Field(None, description="Date for next contact")
```

## Output Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class TalkingPoint(BaseModel):
    """A single talking point for the call."""

    point: str = Field(..., description="The talking point text")
    context: str = Field(..., description="Why this point is relevant")
    expected_duration_seconds: int = Field(default=15, description="How long to say this")

class CallTaskOutput(BaseModel):
    """Output when creating a call task."""

    task_id: str = Field(..., description="Unique task identifier")
    lead_id: str
    status: Literal["created", "failed", "duplicate"] = Field(..., description="Task creation status")
    talking_points: List[TalkingPoint] = Field(..., description="Personalized talking points")
    call_script: str = Field(..., description="Full suggested script")
    best_call_times: List[str] = Field(..., description="Recommended call windows")
    deadline: datetime = Field(..., description="Task deadline")
    task_url: Optional[str] = Field(None, description="URL to task in Todoist/ClickUp")
    error_message: Optional[str] = Field(None, description="Why task creation failed")

class CallLogOutput(BaseModel):
    """Output when logging a call attempt."""

    log_id: str = Field(..., description="Unique log identifier")
    task_id: str
    lead_id: str
    outcome: str
    lead_status_update: Optional[str] = Field(None, description="New lead status if changed")
    next_task_id: Optional[str] = Field(None, description="Follow-up task if created")
    logged_at: datetime = Field(default_factory=datetime.utcnow)
```

## Tools

### 1. `check_call_eligibility`

**Purpose**: Verify if a lead is eligible for a call based on compliance and business rules.

**Parameters**:
```python
lead_id: str  # UUID of lead to check
phone: str   # Phone number with country code
timezone: str  # Lead's timezone
```

**Implementation**:
- Check do-not-call registry
- Verify no call in last 7 days
- Check business hours in lead's timezone
- Validate phone number format
- Check for explicit opt-out

### 2. `generate_talking_points`

**Purpose**: Create personalized talking points based on lead context and research.

**Parameters**:
```python
lead_id: str          # UUID of lead
trigger_type: str     # Why calling (hot_lead_silence, etc.)
context_data: dict    # Emails, meetings, proposals
research_data: dict   # Company research, persona data
```

**Implementation**:
- Analyze recent email engagement
- Extract key points from meetings
- Identify pain points from research
- Generate 3-4 specific talking points
- Ensure each point adds value

### 3. `create_call_task`

**Purpose**: Create a task in external task management system.

**Parameters**:
```python
lead_name: str        # Full name
company: str          # Company name
phone: str            # Phone number
talking_points: list  # Generated talking points
urgency: str          # Task priority
deadline: datetime    # Task deadline
system: str           # "todoist" or "clickup"
```

**Implementation**:
- Format task according to system requirements
- Include all context and talking points
- Set appropriate due date and priority
- Handle API errors with retry logic
- Return task URL for reference

### 4. `log_call_attempt`

**Purpose**: Record call attempt and update lead status.

**Parameters**:
```python
task_id: str              # Call task ID
outcome: str              # Call result
duration_seconds: int     # Call duration if connected
notes: str                # Call notes
next_action: str          # Agreed next steps
```

**Implementation**:
- Create record in call_logs table
- Update lead status based on outcome
- Schedule follow-up if needed
- Track call metrics
- Update opt-out status if requested

### 5. `check_opt_out_compliance`

**Purpose**: Ensure compliance with opt-out requests.

**Parameters**:
```python
lead_id: str  # UUID of lead
phone: str    # Phone number
email: str    # Email address
```

**Implementation**:
- Check opt_out table for phone/email
- Verify no recent opt-out requests
- Flag leads for manual review if needed
- Maintain opt-out audit trail

## Error Handling

### Task Management API Errors
| Error | Detection | Response | Retry |
|-------|-----------|----------|-------|
| Rate limit (429) | HTTP status | Exponential backoff | Yes, 3 attempts |
| Auth error (401) | HTTP status | Fail & alert ops | No |
| Service down (5xx) | HTTP status | Retry with backoff | Yes, 5 attempts |
| Invalid input (400) | Response body | Log error, fail task | No |
| Network timeout | Exception | Retry with longer timeout | Yes, 2 attempts |

### Phone Validation Errors
- Invalid format → Log error, skip task creation
- No country code → Try to infer from location
- VoIP number → Flag for manual review
- Landline only → Update contact preferences

### Compliance Errors
- Opt-out violation → Immediately cancel, log compliance issue
- Call window violation → Schedule for next valid window
- Duplicate call → Skip, log as prevented duplicate

### Data Errors
- Lead not found → Fail with detailed error
- Missing context → Request from dependent agents
- Invalid timezone → Default to lead's business timezone

## Testing Strategy

### Unit Tests
```python
def test_check_call_eligibility_dnc():
    """Verify do-not-call compliance checking."""

def test_generate_talking_points_hot_lead():
    """Verify talking points for hot lead silence."""

def test_generate_talking_points_post_meeting():
    """Verify talking points include meeting specifics."""

def test_create_task_todoist_success():
    """Verify task creation in Todoist."""

def test_create_task_clickup_failure():
    """Verify error handling for ClickUp failures."""

def test_log_call_attempt_outcome():
    """Verify call logging and lead status updates."""

def test_opt_out_compliance():
    """Verify opt-out checking prevents calls."""
```

### Integration Tests
```python
def test_end_to_end_hot_lead_workflow():
    """Full workflow from trigger to task creation."""

def test_error_recovery_task_creation():
    """Verify retry logic for task management APIs."""

def test_compliance_violation_prevention():
    """Ensure opt-out calls are blocked."""

def test_timezone_handling():
    """Verify correct call windows across timezones."""
```

### Mock Strategy
```python
@pytest.fixture
def mock_todoist_client():
    with patch('src.integrations.todoist.TodoistClient') as mock:
        mock.return_value.create_task.return_value = {"id": "task_123"}
        yield mock

@pytest.fixture
def mock_clickup_client():
    with patch('src.integrations.clickup.ClickUpClient') as mock:
        mock.return_value.create_task.return_value = {"id": "task_456"}
        yield mock

@pytest.fixture
def mock_research_data():
    return {
        "company": {"name": "Acme Inc", "industry": "SaaS"},
        "persona": {"role": "CTO", "pain_points": ["slow deployment"]},
        "intent_signals": ["pricing_page_visit", "demo_request"]
    }
```

## Performance Requirements

- **Task Creation**: < 2 seconds for successful creation
- **Talking Points Generation**: < 5 seconds using Claude API
- **Compliance Checks**: < 100ms (database lookup)
- **Concurrent Tasks**: Handle up to 10 call tasks in parallel
- **Error Recovery**: All retries complete within 30 seconds

## Observability

### Logging Requirements
- All call task creations with trigger type
- Compliance check failures with details
- Task management API errors with full context
- Call outcome logging for analytics
- Opt-out violations with immediate alerting

### Metrics to Track
- Call task creation success rate
- Average time from trigger to task creation
- Call outcomes by trigger type
- Opt-out compliance violations
- Talking point effectiveness (from call outcomes)

## Security

### Data Protection
- Encrypt phone numbers at rest
- Mask phone numbers in logs
- Secure task management API credentials
- Retain call logs for minimum required period

### Access Control
- Restrict phone number access to this agent only
- Audit trail for all call task operations
- Role-based access to call logs
- Compliance officer access to opt-out data

## Database Schema

### call_tasks Table
```sql
CREATE TABLE call_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    task_id VARCHAR(255) NOT NULL,  # External task ID
    trigger_type VARCHAR(50) NOT NULL,
    talking_points JSONB NOT NULL,
    call_script TEXT NOT NULL,
    urgency VARCHAR(20) DEFAULT 'normal',
    deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    task_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### call_logs Table
```sql
CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES call_tasks(id),
    lead_id UUID NOT NULL REFERENCES leads(id),
    outcome VARCHAR(50) NOT NULL,
    duration_seconds INTEGER,
    notes TEXT,
    next_action TEXT,
    follow_up_date TIMESTAMP WITH TIME ZONE,
    agent_performed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Acceptance Criteria

- [ ] Creates call tasks only for defined triggers (hot lead, post-meeting, proposal)
- [ ] Generates personalized talking points based on lead context and research
- [ ] Respects do-not-call compliance and opt-out requests
- [ ] Creates tasks in Todoist or ClickUp with all required information
- [ ] Logs all call attempts with outcomes and follow-up actions
- [ ] Prevents duplicate calls within 7-day window
- [ ] Handles timezones correctly for call timing
- [ ] Integrates with lead research and meeting management agents
- [ ] Provides audit trail for compliance requirements
- [ ] Handles task management API failures gracefully
- [ ] Updates lead status based on call outcomes
- [ ] Generates follow-up tasks when needed

## Dependencies

**Internal Agents**:
- Lead Research Agent (provides research data)
- Meeting Management Agent (provides meeting context)
- Proposal Tracking Agent (provides proposal status)

**External Integrations**:
- Todoist API or ClickUp API (task creation)
- Claude API (talking point generation)
- Supabase (data storage)
- Do-not-call registry (compliance)

**Database Tables**:
- leads (base lead information)
- call_tasks (call task tracking)
- call_logs (call outcome logging)
- opt_outs (compliance tracking)
