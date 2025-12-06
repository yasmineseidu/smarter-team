# Client Update Agent - Production Specification

**Status:** Ready to Build
**Last Updated:** 2025-12-05
**Refined From:** plan/agents/delivery-client-update.md
**Version:** 1.0.0

---

## 1. Overview

### Purpose
Autonomous agent that sends structured client progress updates including weekly summaries, milestone completions, and blocker alerts. Generates personalized emails, tracks all communications, and ensures clients are informed at optimal times.

### Agent Classification
- **Type:** Communication Agent
- **Execution Mode:** Hybrid (Scheduled cron + Event-driven)
- **Human-in-the-Loop:** Approval required for custom updates outside templates
- **Priority:** High (client retention critical)

### Dependencies
- **Upstream Agents:**
  - Project Management Agent (provides status, milestones, blockers)
  - QA Agent (provides test results for milestone completion)
- **Downstream Agents:**
  - Payment Collection Agent (triggered on milestone completion)
  - Client Success Agent (receives update logs for satisfaction tracking)
- **External Services:**
  - Email Service (Instantly.ai or Gmail API)
  - Database (client_updates, update_logs tables)

---

## 2. System Prompt

```
You are the Client Update Agent for Smarter Team, an AI agency automation system.

Your responsibilities:
- Generate personalized client progress updates based on project data
- Send weekly progress emails every Friday at 3:00 PM client time
- Send immediate milestone completion notifications within 2 hours
- Send blocker alerts within 1 hour of detection
- Log all communications for audit trail and client success tracking

Communication Principles:
- Always be clear, concise, and professional
- Focus on value delivered and progress made
- Proactively address blockers with specific action items
- Maintain consistent tone aligned with agency brand
- Respect client timezone and communication preferences

Update Types You Handle:
1. WEEKLY_PROGRESS: Scheduled comprehensive status updates
2. MILESTONE_COMPLETE: Immediate notification of milestone delivery
3. BLOCKER_ALERT: Urgent notification of issues requiring client input

Error Handling:
- If project data is missing, send placeholder with apology
- If email fails, retry with exponential backoff (max 3 attempts)
- Always log outcomes for client success team visibility

When generating updates:
- Quantify progress with specific metrics (percentages, tasks completed)
- Link deliverables to business outcomes
- Provide clear next steps and timelines
- Include relevant contact for questions

Remember: Your updates directly impact client satisfaction and retention.
```

---

## 3. Configuration

```python
class ClientUpdateConfig:
    # Claude SDK Configuration
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower for consistent formatting
    max_retries: int = 3
    timeout_seconds: int = 30

    # Scheduling Configuration
    weekly_update_day: str = "friday"
    weekly_update_time: str = "15:00"
    milestone_delay_hours: int = 2
    blocker_delay_hours: int = 1

    # Email Configuration
    email_provider: str = "instantly"  # or "gmail"
    from_email: str = "updates@smarterteam.ai"
    from_name: str = "Smarter Team Updates"
    bulk_send_batch_size: int = 50
    rate_limit_per_minute: int = 120

    # Client Preferences
    default_timezone: str = "America/New_York"
    allow_custom_updates: bool = True
    auto_approve_threshold: int = 1000  # Contract value in USD
```

---

## 4. Tools

### Tool: get_project_status
**Purpose:** Retrieve current project status from Project Management Agent

**Input Schema:**
```python
from pydantic import BaseModel, Field

class ProjectStatusInput(BaseModel):
    project_id: str = Field(..., description="Project UUID")
    client_id: str = Field(..., description="Client UUID")
    include_tasks: bool = Field(default=True, description="Include detailed task breakdown")
    timeframe: str = Field(default="week", description="Timeframe for progress (week/month/all)")
```

**Output Schema:**
```python
class ProjectStatusOutput(BaseModel):
    project_name: str
    client_name: str
    overall_progress: float  # 0.0 to 1.0
    current_milestone: dict
    completed_tasks: list[dict]
    in_progress_tasks: list[dict]
    upcoming_tasks: list[dict]
    blockers: list[dict]
    milestones_completed: list[dict]
    next_milestone: dict
    team_members: list[str]
    last_updated: datetime
```

**Error Handling:**
- Project not found → Return empty status with error message
- Agent unavailable → Retry 2x, then use cached status if <24h old
- Invalid UUID → Return validation error
- Timeout → Return last known status with warning

---

### Tool: generate_update_content
**Purpose:** Generate personalized update content based on project status and update type

**Input Schema:**
```python
class UpdateContentInput(BaseModel):
    update_type: str = Field(..., description="WEEKLY_PROGRESS|MILESTONE_COMPLETE|BLOCKER_ALERT")
    project_status: dict
    client_data: dict
    custom_message: Optional[str] = Field(None, description="Custom message for special updates")
    urgency_level: Optional[str] = Field("normal", description="low|normal|high|urgent")
```

**Output Schema:**
```python
class UpdateContentOutput(BaseModel):
    subject_line: str
    email_body: str
    summary_points: list[str]
    action_items: list[str]
    business_impact: str
    next_steps: str
    estimated_completion: Optional[str]
    attachments: list[dict]  # Deliverables, reports, etc.
```

**Error Handling:**
- Invalid update_type → Return error with supported types
- Missing required data → Use defaults and note missing info
- Content generation failure → Retry once with simplified template
- Personalization errors → Fall back to generic template

---

### Tool: send_email_update
**Purpose:** Send update email via configured email provider

**Input Schema:**
```python
class EmailUpdateInput(BaseModel):
    to_email: str = Field(..., description="Recipient email address")
    to_name: str = Field(..., description="Recipient full name")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="HTML email body")
    attachments: Optional[list[str]] = Field(None, description="List of attachment URLs")
    priority: Optional[str] = Field("normal", description="email priority header")
    send_at: Optional[datetime] = Field(None, description="Schedule send time")
```

**Output Schema:**
```python
class EmailUpdateOutput(BaseModel):
    email_id: str  # Provider's email ID
    status: str  # sent|scheduled|failed
    sent_at: datetime
    delivery_estimate: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
```

**Error Handling:**
- Rate limit (429) → Exponential backoff: 1min, 5min, 15min
- Invalid email → Log error, notify admin
- Authentication error → Fail immediately, alert ops
- Timeout → Retry 2x with longer timeout
- Content too large → Compress images or split message
- Provider outage → Switch to backup provider if configured

---

### Tool: log_client_update
**Purpose:** Record all client communications for audit trail and analytics

**Input Schema:**
```python
class LogUpdateInput(BaseModel):
    client_id: str
    project_id: str
    update_type: str
    email_id: Optional[str]
    content_summary: str
    sent_at: datetime
    status: str
    metadata: dict = Field(default_factory=dict)
```

**Output Schema:**
```python
class LogUpdateOutput(BaseModel):
    log_id: str
    created_at: datetime
    success: bool
    duplicate: bool  # True if similar update recently sent
```

**Error Handling:**
- Database connection → Retry 3x, queue for later
- Schema validation → Log error, continue with update
- Duplicate detection → Log warning but allow send
- Storage quota → Purge old logs, retry

---

## 5. Database Schema

### client_updates table
```sql
CREATE TABLE client_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    update_type VARCHAR(50) NOT NULL,  -- WEEKLY_PROGRESS, MILESTONE_COMPLETE, BLOCKER_ALERT
    email_id VARCHAR(255),  -- Provider's email ID
    subject VARCHAR(500),
    content_summary TEXT,
    status VARCHAR(50) NOT NULL,  -- sent, scheduled, failed, draft
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',

    CONSTRAINT valid_update_type CHECK (update_type IN ('WEEKLY_PROGRESS', 'MILESTONE_COMPLETE', 'BLOCKER_ALERT', 'CUSTOM')),
    CONSTRAINT valid_status CHECK (status IN ('sent', 'scheduled', 'failed', 'draft', 'cancelled'))
);

CREATE INDEX idx_client_updates_client_id ON client_updates(client_id);
CREATE INDEX idx_client_updates_project_id ON client_updates(project_id);
CREATE INDEX idx_client_updates_sent_at ON client_updates(sent_at DESC);
CREATE INDEX idx_client_updates_type ON client_updates(update_type);
```

### update_logs table
```sql
CREATE TABLE update_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    update_id UUID REFERENCES client_updates(id),
    event_type VARCHAR(50) NOT NULL,  -- created, sent, failed, retried, opened, clicked
    event_data JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_event_type CHECK (event_type IN ('created', 'sent', 'failed', 'retried', 'opened', 'clicked', 'bounced', 'complained'))
);

CREATE INDEX idx_update_logs_update_id ON update_logs(update_id);
CREATE INDEX idx_update_logs_timestamp ON update_logs(timestamp DESC);
CREATE INDEX idx_update_logs_event_type ON update_logs(event_type);
```

---

## 6. Email Templates

### Weekly Progress Template
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Weekly Update: {{project_name}}</title>
</head>
<body style="font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #374151;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1f2937; border-bottom: 2px solid #10b981; padding-bottom: 10px;">
            Weekly Update: {{project_name}}
        </h2>

        <p style="font-size: 16px;">Hi {{first_name}},</p>

        <p style="font-size: 16px;">Here's your weekly progress update for {{project_name}}:</p>

        <!-- Completed Section -->
        <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #166534; margin-top: 0;">✅ Completed This Week</h3>
            {{#each completed_tasks}}
            <div style="margin: 8px 0;">
                <strong>{{this.name}}</strong>
                {{#if this.deliverable}}
                <br><small style="color: #6b7280;">Deliverable: {{this.deliverable}}</small>
                {{/if}}
            </div>
            {{/each}}
        </div>

        <!-- In Progress Section -->
        {{#if in_progress_tasks}}
        <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #92400e; margin-top: 0;">🔄 In Progress</h3>
            {{#each in_progress_tasks}}
            <div style="margin: 8px 0;">
                <strong>{{this.name}}</strong> - {{this.progress}}%
                <div style="background: #e5e7eb; height: 4px; border-radius: 2px; margin: 4px 0;">
                    <div style="background: #f59e0b; height: 100%; width: {{this.progress}}%; border-radius: 2px;"></div>
                </div>
            </div>
            {{/each}}
        </div>
        {{/if}}

        <!-- Next Week Section -->
        <div style="background: #eff6ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #1e40af; margin-top: 0;">📋 Next Week's Focus</h3>
            <ul style="margin: 0; padding-left: 20px;">
                {{#each upcoming_tasks}}
                <li>{{this.name}}</li>
                {{/each}}
            </ul>
        </div>

        <!-- Overall Progress -->
        <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <strong>Overall Progress:</strong>
                <span style="font-size: 24px; color: #10b981;">{{overall_progress}}%</span>
            </div>
        </div>

        <!-- Blockers (if any) -->
        {{#if blockers}}
        <div style="background: #fef2f2; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ef4444;">
            <h3 style="color: #991b1b; margin-top: 0;">⚠️ Blockers Needing Your Input</h3>
            {{#each blockers}}
            <div style="margin: 10px 0;">
                <strong>{{this.title}}</strong>
                <p>{{this.description}}</p>
                <p><small>Needed by: {{this.needed_by}}</small></p>
            </div>
            {{/each}}
        </div>
        {{/if}}

        <p style="margin-top: 30px;">Let me know if you have any questions or would like to discuss the project in detail.</p>

        <p style="margin-top: 20px;">Best regards,<br>Smarter Team</p>

        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
        <p style="font-size: 12px; color: #6b7280;">
            This is an automated update. Reply to this email or schedule a call anytime.
        </p>
    </div>
</body>
</html>
```

---

## 7. Error Handling Matrix

| Error Type | Detection | Response | Retry | Alert |
|------------|-----------|----------|-------|-------|
| **API Rate Limit** | HTTP 429 | Exponential backoff (1min, 5min, 15min) | Yes, 3 attempts | No |
| **Provider Outage** | HTTP 5xx or timeout | Switch to backup provider | Yes, 2 attempts | Yes (after fails) |
| **Invalid Email** | Validation failure | Log error, skip send | No | Yes (daily digest) |
| **Auth Failure** | HTTP 401/403 | Fail immediately | No | Yes (immediate) |
| **Database Error** | DB exception | Queue for retry | Yes, 3 attempts | Yes (if persists) |
| **Missing Project Data** | Empty response | Send apology email | No | No |
| **Template Error** | Template exception | Use fallback template | Yes, 1 attempt | Yes (log error) |
| **Attachment Error** | Upload failure | Send without attachment | Yes, 1 attempt | No |

### Recovery Strategies

1. **Graceful Degradation:**
   - Missing project data → Send placeholder update
   - Template failure → Use plain text fallback
   - Attachments missing → Send update with note

2. **Circuit Breaker:**
   - Provider fails 5x in row → Temporarily switch providers
   - Email bounces >10% → Pause sends, investigate
   - Multiple failures to same client → Flag for review

3. **Queue Management:**
   - Failed sends → Dead letter queue after 3 retries
   - Scheduled sends → Requeue if provider unavailable
   - Bulk sends → Process in batches, track progress

---

## 8. Multi-Agent Integration

### Data Contract with Project Management Agent
```python
# Request payload for project status
{
    "project_id": "uuid",
    "client_id": "uuid",
    "timeframe": "week|month|all",
    "include_details": true,
    "include_blockers": true
}

# Response structure
{
    "project": {
        "name": "string",
        "status": "active|on_hold|completed",
        "progress": 0.85,
        "current_milestone": {...}
    },
    "tasks": {
        "completed": [...],
        "in_progress": [...],
        "upcoming": [...],
        "blocked": [...]
    },
    "milestones": {
        "current": {...},
        "completed": [...],
        "next": {...}
    },
    "blockers": [...],
    "team": [...],
    "last_updated": "2025-12-05T10:00:00Z"
}
```

### Handoff Triggers
1. **To QA Agent:** When milestone marked complete → "verify-milestone-completion"
2. **To Payment Agent:** When milestone verified → "generate-milestone-invoice"
3. **To Client Success:** When update sent → "log-client-touchpoint"
4. **To Project Management:** When blocker reported → "escalate-blocker"

### Priority Matrix
| Update Type | Priority | Max Delay | SLA |
|-------------|----------|-----------|-----|
| Blocker Alert | Critical | 1 hour | 99.5% |
| Milestone Complete | High | 2 hours | 99% |
| Weekly Progress | Normal | 4 hours | 95% |
| Custom Update | Low | 24 hours | 90% |

---

## 9. Testing Strategy

### Unit Tests
```python
class TestClientUpdateAgent:
    @pytest.mark.asyncio
    async def test_generate_weekly_update_success(self):
        """Verify weekly update generation with complete project data"""

    @pytest.mark.asyncio
    async def test_handle_missing_project_data(self):
        """Verify graceful handling of missing project information"""

    @pytest.mark.asyncio
    async def test_email_template_rendering(self):
        """Verify template variables are properly substituted"""

    @pytest.mark.asyncio
    async def test_timezone_handling(self):
        """Verify emails respect client timezone"""

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Verify rate limiting is respected"""

    @pytest.mark.asyncio
    async def test_duplicate_detection(self):
        """Verify duplicate updates are detected and handled"""
```

### Integration Tests
```python
class TestClientUpdateIntegration:
    @pytest.mark.asyncio
    async def test_full_weekly_update_flow(self):
        """End-to-end weekly update with mocked Project Management Agent"""

    @pytest.mark.asyncio
    async def test_milestone_completion_notification(self):
        """Verify milestone triggers immediate notification"""

    @pytest.mark.asyncio
    async def test_blocker_alert_escalation(self):
        """Verify blockers are properly escalated"""

    @pytest.mark.asyncio
    async def test_email_provider_failover(self):
        """Verify backup provider is used on primary failure"""
```

### Mock Strategy
```python
@pytest.fixture
def mock_project_management_agent():
    with patch('src.agents.project_management.ProjectManagementAgent') as mock:
        mock.return_value.get_project_status.return_value = {
            "project_name": "Test Project",
            "overall_progress": 0.75,
            "completed_tasks": [...],
            "in_progress_tasks": [...],
            "blockers": []
        }
        yield mock

@pytest.fixture
def mock_email_provider():
    with patch('src.integrations.email.EmailClient') as mock:
        mock.return_value.send_email.return_value = {
            "email_id": "email_123",
            "status": "sent",
            "sent_at": datetime.utcnow()
        }
        yield mock
```

---

## 10. Performance & Scaling

### Expected Volume
- Weekly updates: ~200 clients per week
- Milestone notifications: ~50 per week
- Blocker alerts: ~20 per week
- Total emails: ~270 per week (40 per day average)

### Rate Limiting
```python
class RateLimiter:
    # Instantly.ai limits: 120 emails/minute
    instant_limit = 120/minute

    # Gmail API limits: 1000 emails/day
    gmail_limit = 1000/day

    # Custom limits for smooth operation
    operation_limit = 60/minute  # Conservative buffer
    batch_size = 50  # Process in batches
```

### Caching Strategy
- Project status: Cache for 15 minutes
- Client preferences: Cache for 1 hour
- Email templates: Cache permanently (memory)
- Rate limit status: Cache for 1 minute

### Monitoring Metrics
- Delivery success rate: >99%
- Average delivery time: <5 minutes
- Template render time: <500ms
- API response time: <2 seconds
- Queue depth: <100 items

---

## 11. Observability

### Logging Strategy
```python
# Structured logging with correlation IDs
logger.info(
    "Client update sent",
    extra={
        "client_id": "uuid",
        "project_id": "uuid",
        "update_type": "WEEKLY_PROGRESS",
        "email_id": "email_123",
        "correlation_id": "req_abc123",
        "duration_ms": 2340,
        "template_used": "weekly_v2"
    }
)

# Error logging with full context
logger.error(
    "Failed to send client update",
    extra={
        "error": str(e),
        "client_id": client_id,
        "project_id": project_id,
        "retry_count": 2,
        "provider": "instantly",
        "error_code": "RATE_LIMIT"
    },
    exc_info=True
)
```

### Metrics to Track
1. **Delivery Metrics:**
   - Success/failure rate by provider
   - Open rate and click-through rate
   - Bounce and complaint rates
   - Delivery latency distribution

2. **Business Metrics:**
   - Client satisfaction scores (correlate with update frequency)
   - Time to resolve blockers
   - Client response rate to updates
   - Churn rate vs update frequency

3. **Technical Metrics:**
   - API response times
   - Rate limit utilization
   - Template rendering performance
   - Queue processing time

### Alerts
- Delivery success rate <95% for 1 hour
- Queue depth >500 items
- Provider API error rate >10%
- Template rendering failures >5/min
- Database connection failures

---

## 12. Security & Compliance

### Data Protection
- Encrypt email content at rest
- Mask PII in logs
- Respect unsubscribe requests
- GDPR compliance for EU clients

### Access Controls
- Role-based access to update logs
- Audit trail for all communications
- Secure API key management
- IP allowlist for admin access

### Privacy Features
- Client opt-out preferences
- Data retention policies (2 years for logs)
- Right to deletion requests
- Automated PII redaction

---

## 13. Acceptance Criteria

- [ ] Agent generates all three update types correctly
- [ ] Weekly updates sent every Friday at 3 PM client time
- [ ] Milestone notifications sent within 2 hours
- [ ] Blocker alerts sent within 1 hour
- [ ] All emails use correct templates with personalization
- [ ] Error handling covers all failure scenarios
- [ ] Rate limiting respected for all providers
- [ ] All communications logged in database
- [ ] Unit test coverage >90%
- [ ] Integration tests cover all workflows
- [ ] Performance meets specified SLAs
- [ ] Security requirements implemented
- [ ] Documentation complete

---

## 14. Implementation Files

```
app/backend/src/agents/client_update/
├── __init__.py
├── agent.py              # Main ClientUpdateAgent class
├── tools/
│   ├── __init__.py
│   ├── project_status.py # get_project_status tool
│   ├── content_gen.py    # generate_update_content tool
│   ├── email_sender.py   # send_email_update tool
│   └── logger.py         # log_client_update tool
├── templates/
│   ├── weekly_progress.html
│   ├── milestone_complete.html
│   └── blocker_alert.html
├── schemas.py            # Pydantic models
└── exceptions.py         # Custom exceptions

app/backend/__tests__/unit/agents/test_client_update.py
app/backend/__tests__/integration/test_client_update_integration.py

Database migrations:
- migrations/001_create_client_updates_table.sql
- migrations/002_create_update_logs_table.sql
```
