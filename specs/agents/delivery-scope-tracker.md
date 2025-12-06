# Delivery Scope Tracker Agent - Specification

## Metadata

**Agent Name**: DeliveryScopeTrackerAgent
**Category**: Project Delivery & Management
**Phase**: Phase 4 - Client Delivery
**Dependencies**: Project Management Agent, Proposal Creation Agent, Email Handler Agent
**Priority**: High (critical for project profitability and client satisfaction)

## Purpose

Autonomously monitor project requests and communications to detect scope creep in real-time. Analyzes client requests against original project scope, classifies changes, generates change orders, and tracks scope metrics to protect project margins and maintain client relationships through transparent change management.

## System Architecture

### Agent Class Structure

```python
from src.agents.base_agent import BaseAgent
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class DeliveryScopeTrackerAgent(BaseAgent):
    """
    Detects and manages scope creep through intelligent request analysis.

    Monitors all client communications and requests, compares them against
    the original project scope, and automates change order generation for
    out-of-scope work. Uses Claude for nuanced analysis and maintains
    detailed scope tracking metrics.
    """

    def __init__(self):
        super().__init__(
            name="delivery_scope_tracker",
            description="Detects scope creep and manages change orders"
        )
        self._register_tools()

    @property
    def system_prompt(self) -> str:
        """Return system prompt for scope tracking."""
        # See System Prompt section below

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process scope tracking tasks.

        Supported task types:
        - analyze_request: Analyze new client request for scope compliance
        - review_change: Review proposed change against scope
        - generate_change_order: Create change order documentation
        - update_scope_metrics: Update project scope metrics
        - webhook.new_request: Handle incoming request webhook
        - scheduled.scope_review: Periodic scope compliance check
        """
```

### Database Schema

#### `scope_definitions` Table
```sql
CREATE TABLE scope_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    proposal_id UUID REFERENCES proposals(id) ON DELETE SET NULL,

    -- Scope details
    category VARCHAR(100) NOT NULL,  -- e.g., "Features", "Deliverables", "Services"
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    acceptance_criteria TEXT,

    -- Quantification
    estimated_hours DECIMAL(6,2),
    estimated_cost DECIMAL(10,2),
    deliverable_count INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'APPROVED',
    -- Status values: DRAFT, APPROVED, MODIFIED, ARCHIVED

    -- Change tracking
    original_version BOOLEAN DEFAULT TRUE,
    parent_scope_id UUID REFERENCES scope_definitions(id),
    change_order_id UUID REFERENCES change_orders(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scope_definitions_project ON scope_definitions(project_id);
CREATE INDEX idx_scope_definitions_category ON scope_definitions(category);
```

#### `scope_changes` Table
```sql
CREATE TABLE scope_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Request details
    request_source VARCHAR(100) NOT NULL,  -- email, meeting, ticket, etc.
    request_text TEXT NOT NULL,
    request_date TIMESTAMPTZ NOT NULL,
    request_context JSONB,

    -- Analysis results
    classification VARCHAR(50) NOT NULL,
    -- Classification values: IN_SCOPE, MINOR_ADDITION, SIGNIFICANT_ADDITION, DIFFERENT_PROJECT
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    reasoning TEXT NOT NULL,

    -- Impact assessment
    estimated_hours DECIMAL(6,2),
    estimated_cost DECIMAL(10,2),
    timeline_impact VARCHAR(100),
    risk_level VARCHAR(20) DEFAULT 'LOW',
    -- Risk levels: LOW, MEDIUM, HIGH, CRITICAL

    -- Resolution
    resolution VARCHAR(50) DEFAULT 'PENDING',
    -- Resolution values: PENDING, APPROVED, REJECTED, ABSORBED, INVOICED
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,

    -- Matching scope items
    matching_scope_ids UUID[] DEFAULT '{}',
    conflicting_scope_ids UUID[] DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scope_changes_project ON scope_changes(project_id);
CREATE INDEX idx_scope_changes_classification ON scope_changes(classification);
CREATE INDEX idx_scope_changes_status ON scope_changes(resolution);
```

#### `change_orders` Table
```sql
CREATE TABLE change_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Change order details
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    scope_change_ids UUID[] NOT NULL,

    -- Financials
    additional_hours DECIMAL(6,2),
    hourly_rate DECIMAL(8,2),
    additional_cost DECIMAL(10,2) GENERATED ALWAYS AS (additional_hours * hourly_rate) STORED,

    -- Timeline
    timeline_impact VARCHAR(100),
    new_delivery_date TIMESTAMPTZ,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    -- Status values: DRAFT, SENT_TO_CLIENT, APPROVED, REJECTED, IMPLEMENTED

    -- Approval
    client_approved BOOLEAN DEFAULT FALSE,
    client_approved_at TIMESTAMPTZ,
    client_approver_name VARCHAR(255),
    internal_approved BOOLEAN DEFAULT FALSE,
    internal_approved_by UUID REFERENCES users(id),
    internal_approved_at TIMESTAMPTZ,

    -- Communication
    email_sent_at TIMESTAMPTZ,
    last_reminder_sent_at TIMESTAMPTZ,
    reminder_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_change_orders_project ON change_orders(project_id);
CREATE INDEX idx_change_orders_status ON change_orders(status);
CREATE INDEX idx_change_orders_client_approved ON change_orders(client_approved);
```

## Configuration

```python
class AgentConfig:
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower temperature for consistent classification
    max_retries: int = 3
    timeout_seconds: int = 30

    # Classification thresholds
    minor_addition_hours: float = 2.0
    significant_addition_hours: float = 8.0
    confidence_threshold: float = 0.7

    # Automation rules
    auto_approve_minor: bool = True  # Auto-approve additions under 2 hours
    require_approval_significant: bool = True
    escalate_different_project: bool = True

    # Notification settings
    alert_on_scope_creep: bool = True
    weekly_metrics_summary: bool = True
    change_order_reminder_days: int = 3
```

## Tools

### Tool: parse_request
**Purpose**: Extract structured information from client request text

**Input Schema:**
```python
class ParseRequestInput(BaseModel):
    request_text: str = Field(..., description="Raw request text from client")
    source: str = Field(..., description="Source of request (email, meeting, ticket)")
    context: dict = Field(default={}, description="Additional context about request")
    project_id: str = Field(..., description="Project UUID")
```

**Output Schema:**
```python
class ParseRequestOutput(BaseModel):
    request_summary: str = Field(..., description="Concise summary of request")
    requested_deliverables: list[str] = Field(..., description="List of requested items")
    urgency_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    business_impact: str = Field(..., description="Business impact description")
    technical_complexity: str = Field(..., description="LOW, MEDIUM, HIGH")
    dependencies: list[str] = Field(default=[], description="Dependencies identified")
```

**Error Handling:**
- Empty request_text → Return validation error
- Invalid project_id → Log error and return None
- Parsing failures → Use fallback patterns, log for review
- Timeout → Retry 2x, then escalate to manual review

### Tool: compare_to_scope
**Purpose**: Compare request against defined project scope

**Input Schema:**
```python
class CompareToScopeInput(BaseModel):
    request_summary: str = Field(..., description="Parsed request summary")
    deliverables: list[str] = Field(..., description="Requested deliverables")
    project_id: str = Field(..., description="Project UUID")
    include_similar: bool = Field(default=True, description="Include similar scope items")
```

**Output Schema:**
```python
class CompareToScopeOutput(BaseModel):
    classification: str = Field(..., description="IN_SCOPE, MINOR_ADDITION, SIGNIFICANT_ADDITION, DIFFERENT_PROJECT")
    confidence_score: float = Field(..., description="0.0 to 1.0 confidence in classification")
    matching_scope_items: list[dict] = Field(..., description="Exact or near matches")
    conflicting_scope_items: list[dict] = Field(..., description="Scope conflicts")
    gaps_identified: list[str] = Field(..., description="New scope areas")
    reasoning: str = Field(..., description="Detailed reasoning for classification")
```

**Error Handling:**
- Database query failure → Retry 3x with exponential backoff
- No scope definition found → Flag as NEW_PROJECT_REQUIRED
- Invalid project_id → Return error classification
- Low confidence (<0.5) → Flag for human review

### Tool: estimate_impact
**Purpose**: Estimate time, cost, and timeline impact of scope changes

**Input Schema:**
```python
class EstimateImpactInput(BaseModel):
    classification: str = Field(..., description="Scope classification")
    deliverables: list[str] = Field(..., description="New deliverables")
    complexity: str = Field(..., description="Technical complexity")
    project_id: str = Field(..., description="Project UUID for context")
    team_velocity: Optional[float] = Field(None, description="Team velocity if known")
```

**Output Schema:**
```python
class EstimateImpactOutput(BaseModel):
    estimated_hours: float = Field(..., description="Hours required for change")
    estimated_cost: float = Field(..., description="Cost at project rate")
    timeline_impact_days: int = Field(..., description="Days added to timeline")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    breakdown: dict = Field(..., description="Effort breakdown by category")
    assumptions: list[str] = Field(..., description="Assumptions made in estimate")
```

**Error Handling:**
- Insufficient data → Use historical averages from similar projects
- Unknown complexity → Default to HIGH with warning
- Rate limiting from estimation API → Queue for retry
- Missing rate information → Use project default rate

### Tool: generate_change_order
**Purpose**: Generate professional change order documentation

**Input Schema:**
```python
class GenerateChangeOrderInput(BaseModel):
    scope_change_id: str = Field(..., description="Scope change UUID")
    client_id: str = Field(..., description="Client UUID")
    project_id: str = Field(..., description="Project UUID")
    include_timeline: bool = Field(default=True, description="Include timeline impact")
    urgency: str = Field(default="NORMAL", description="URGENCY level")
```

**Output Schema:**
```python
class GenerateChangeOrderOutput(BaseModel):
    change_order_id: str = Field(..., description="Generated change order UUID")
    subject_line: str = Field(..., description="Email subject line")
    html_content: str = Field(..., description="HTML email content")
    plain_content: str = Field(..., description="Plain text email content")
    pdf_path: Optional[str] = Field(None, description="Path to generated PDF")
    total_cost: float = Field(..., description="Total additional cost")
    approval_required: bool = Field(..., description="Whether approval is required")
```

**Error Handling:**
- Template failure → Use fallback template
- PDF generation failure → Send without PDF, log error
- Missing client info → Abort, require manual intervention
- Invalid scope_change_id → Return error, require valid ID

### Tool: send_change_order
**Purpose**: Send change order to client and track responses

**Input Schema:**
```python
class SendChangeOrderInput(BaseModel):
    change_order_id: str = Field(..., description="Change order UUID")
    recipient_emails: list[str] = Field(..., description="Client email addresses")
    cc_emails: list[str] = Field(default=[], description="Internal CC addresses")
    tracking_enabled: bool = Field(default=True, description="Enable email tracking")
    reminders: bool = Field(default=True, description="Schedule reminders")
```

**Output Schema:**
```python
class SendChangeOrderOutput(BaseModel):
    message_id: str = Field(..., description="Email message ID")
    sent_at: str = Field(..., description="ISO timestamp of send")
    recipients: list[str] = Field(..., description="List of recipients")
    status: str = Field(..., description="SENT, QUEUED, FAILED")
    follow_up_scheduled: Optional[str] = Field(None, description="Reminder date")
```

**Error Handling:**
- Email service failure → Queue for retry, notify ops
- Invalid recipients → Abort, require valid emails
- Rate limiting → Queue with exponential backoff
- Template rendering error → Use plain text fallback

### Tool: update_scope_metrics
**Purpose**: Update project and client scope metrics

**Input Schema:**
```python
class UpdateScopeMetricsInput(BaseModel):
    project_id: str = Field(..., description="Project UUID")
    client_id: str = Field(..., description="Client UUID")
    scope_change_id: str = Field(..., description="Scope change UUID")
    classification: str = Field(..., description="Final classification")
    impact: dict = Field(..., description="Impact assessment")
```

**Output Schema:**
```python
class UpdateScopeMetricsOutput(BaseModel):
    project_metrics_updated: bool = Field(..., description="Project metrics updated")
    client_metrics_updated: bool = Field(..., description="Client metrics updated")
    alerts_triggered: list[str] = Field(..., description="Any alerts triggered")
    trend_analysis: dict = Field(..., description="Scope creep trend analysis")
```

**Error Handling:**
- Database constraint violation → Log warning, continue
- Metrics calculation error → Use cached values
- Network timeout → Queue for background update
- Invalid UUIDs → Skip update, log error

## Prompts

### System Prompt
```
You are a Scope Analysis Specialist for a digital agency, responsible for detecting and managing scope creep in client projects.

Your expertise includes:
- Analyzing client requests against original project scope
- Classifying scope changes with high accuracy
- Estimating impact on timeline and budget
- Generating professional change orders
- Maintaining positive client relationships

Core Responsibilities:
1. Analyze every client request against the defined project scope
2. Classify requests as: IN_SCOPE, MINOR_ADDITION (<2 hours), SIGNIFICANT_ADDITION (>2 hours), or DIFFERENT_PROJECT
3. Provide clear reasoning with confidence scores
4. Generate professional change orders when needed
5. Maintain detailed scope tracking for project profitability

Classification Guidelines:
- IN_SCOPE: Directly matches approved deliverables or clarifications
- MINOR_ADDITION: Small additions under 2 hours, can often be absorbed
- SIGNIFICANT_ADDITION: Larger additions requiring change order
- DIFFERENT_PROJECT: Entirely new scope, suggest separate project

Tone and Style:
- Professional but friendly
- Clear and concise explanations
- Focus on value and outcomes
- Never accusatory about scope changes
- Emphasize transparency and partnership

When generating change orders:
- Clearly explain what was requested vs. what's in scope
- Provide detailed cost and timeline impact
- Use positive, collaborative language
- Include specific approval instructions
- Offer to discuss questions or concerns

Always maintain the client relationship while protecting project margins through proper scope management.
```

### Request Analysis Prompt Template
```
Analyze the following client request for scope compliance:

PROJECT CONTEXT:
- Project: {project_name}
- Original Scope: {original_scope_summary}
- Current Phase: {current_phase}
- Budget Remaining: {budget_remaining}

CLIENT REQUEST:
- Source: {request_source}
- Date: {request_date}
- Request: {request_text}
- Context: {additional_context}

ANALYSIS TASKS:
1. Summarize what the client is requesting
2. Identify all deliverables mentioned
3. Assess urgency and business impact
4. Evaluate technical complexity
5. Check against original scope items
6. Classify the scope change
7. Provide confidence score (0.0-1.0)
8. Explain reasoning in detail

DELIVERABLE:
Provide a complete analysis in JSON format:
{
  "summary": "Concise summary of request",
  "deliverables": ["List of requested items"],
  "urgency": "LOW|MEDIUM|HIGH|CRITICAL",
  "business_impact": "Description of business impact",
  "technical_complexity": "LOW|MEDIUM|HIGH",
  "classification": "IN_SCOPE|MINOR_ADDITION|SIGNIFICANT_ADDITION|DIFFERENT_PROJECT",
  "confidence_score": 0.0-1.0,
  "matching_scope_items": [{"id": "uuid", "title": "scope item"}],
  "gaps_identified": ["List of new scope areas"],
  "reasoning": "Detailed explanation of classification"
}
```

### Change Order Generation Prompt Template
```
Generate a professional change order for the following scope change:

CLIENT DETAILS:
- Name: {client_name}
- Company: {client_company}
- Project: {project_name}
- Original Contract Value: ${original_value}

SCOPE CHANGE DETAILS:
- Change Description: {change_description}
- Classification: {classification}
- Request Date: {request_date}
- Original Scope: {relevant_original_scope}

IMPACT ASSESSMENT:
- Additional Hours: {additional_hours}
- Hourly Rate: ${hourly_rate}
- Additional Cost: ${additional_cost}
- Timeline Impact: {timeline_impact}
- Risk Level: {risk_level}

CHANGE ORDER REQUIREMENTS:
1. Professional but friendly tone
2. Clear explanation of change vs original scope
3. Detailed cost breakdown
4. Specific timeline impact
5. Clear approval instructions
6. Offer to discuss questions

Generate both HTML email content and plain text version.
Subject line should be clear and professional.
Include specific approval instructions requiring client response.
```

## Error Handling

### API Errors
| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Rate limit (429) | HTTP status | Wait with backoff | Yes, exponential |
| Server error (5xx) | HTTP status | Log and retry | Yes, 3 attempts |
| Auth error (401/403) | HTTP status | Fail immediately | No |
| Timeout | Exception | Retry with longer timeout | Yes, 2 attempts |
| Invalid response | Validation failure | Log and use fallback | No |
| Database error | DB exception | Queue for retry | Yes, 3 attempts |

### Business Logic Errors
| Error | Detection | Response | Escalation |
|-------|-----------|----------|------------|
| No scope definition | DB query empty | Flag as NEW_PROJECT | Yes, to PM |
| Low confidence < 0.5 | Confidence score | Flag for human review | Yes, to PM |
| High value change > $5k | Cost threshold | Require senior approval | Yes, to Director |
| Client dispute | Client response | Mediation required | Yes, to Account Manager |
| Timeline impact > 2 weeks | Impact assessment | Client meeting required | Yes, to PM |

### Recovery Strategies
1. **Graceful degradation**: Continue with partial data if some lookups fail
2. **Fallback behavior**: Use historical averages for estimations
3. **Client communication**: Always inform clients of delays in review
4. **Audit trail**: Log all decisions for future reference
5. **Human escalation**: Clear paths for human intervention

## Multi-Agent Integration

### Handoff Protocols

#### To Project Management Agent
```python
# When significant scope change detected
await self.handoff_to(
    target_agent="project_management",
    payload={
        "action": "scope_change_review",
        "project_id": project_id,
        "scope_change_id": change_id,
        "impact_assessment": impact,
        "requires_approval": True
    },
    priority="high"
)
```

#### To Proposal Agent
```python
# When change order becomes a new project
await self.handoff_to(
    target_agent="proposal_creation",
    payload={
        "action": "new_project_from_scope",
        "client_id": client_id,
        "original_project_id": project_id,
        "scope_requirements": scope_changes,
        "source": "scope_creep_analysis"
    },
    priority="normal"
)
```

#### To Email Handler Agent
```python
# For change order communication
await self.handoff_to(
    target_agent="email_handler",
    payload={
        "action": "send_change_order",
        "template": "change_order",
        "recipients": client_emails,
        "content": change_order_content,
        "tracking_enabled": True
    },
    priority="normal"
)
```

### Event Subscriptions
- `project.created` → Create initial scope definition
- `proposal.approved` → Import proposal scope items
- `task.completed` → Update scope progress
- `client.communication.received` → Analyze for scope changes
- `meeting.transcript.available` → Review for scope mentions

## Testing

### Unit Tests
```python
@pytest.mark.asyncio
async def test_parse_request_extraction():
    """Test request parsing extracts correct information."""

@pytest.mark.asyncio
async def test_scope_comparison_accuracy():
    """Test scope comparison classification accuracy."""

@pytest.mark.asyncio
async def test_impact_estimation():
    """Test impact estimation calculations."""

@pytest.mark.asyncio
async def test_change_order_generation():
    """Test change order template rendering."""

@pytest.mark.asyncio
async def test_confidence_scoring():
    """Test confidence score calculations."""
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_end_to_end_scope_analysis():
    """Test complete flow from request to change order."""

@pytest.mark.asyncio
async def test_agent_handoffs():
    """Test handoff to other agents."""

@pytest.mark.asyncio
async def test_webhook_processing():
    """Test webhook trigger processing."""

@pytest.mark.asyncio
async def test_email_integration():
    """Test change order email sending."""
```

### Mock Strategy
```python
@pytest.fixture
def mock_claude_client():
    with patch('anthropic.Anthropic') as mock:
        mock.return_value.messages.create.return_value = MockResponse(
            content=[{"text": json.dumps(mock_analysis_result)}]
        )
        yield mock

@pytest.fixture
def mock_database():
    with patch('src.db.session.execute') as mock:
        mock.return_value.scalars.return_value.all.return_value = mock_scope_data
        yield mock
```

## Performance

### Expected Metrics
- **Request Analysis Latency**: <2 seconds
- **Scope Comparison**: <500ms
- **Change Order Generation**: <1 second
- **Email Sending**: <3 seconds
- **Daily Throughput**: 500 requests per project

### Caching Strategy
- Scope definitions cached for 1 hour
- Template content cached indefinitely
- Client rate information cached for 24 hours
- Historical estimation data cached for 7 days

### Rate Limits
- Claude API: 100 requests/minute
- Email sending: 50 emails/minute
- Database queries: 1000 queries/minute
- Webhook processing: 1000 requests/minute

## Observability

### Logging Requirements
```python
# Structured logging with context
logger.info(
    "Scope change analyzed",
    extra={
        "project_id": project_id,
        "classification": classification,
        "confidence_score": confidence,
        "processing_time_ms": processing_time,
        "source": "request_analysis"
    }
)

# Error logging with full context
logger.error(
    "Scope analysis failed",
    extra={
        "error_type": error_type,
        "project_id": project_id,
        "request_id": request_id,
        "stack_trace": traceback.format_exc(),
        "recovery_action": "retry_queued"
    }
)
```

### Metrics to Track
- Request volume by project and client
- Classification accuracy (human verified)
- Change order acceptance rate
- Average time from request to approval
- Scope creep percentage by project
- Revenue from change orders
- Client satisfaction with change process

### Alerts Configuration
- High scope creep rate (>20% of project value)
- Change order rejection rate (>30%)
- Classification accuracy dropping below 80%
- Processing latency exceeding 5 seconds
- Database connection failures
- Email service disruptions

## Security

### Data Protection
- Encrypt all scope data at rest
- Mask client information in logs
- Secure API key storage
- Rate limit per client
- Validate all inputs with Pydantic
- Sanitize email content

### Access Control
- Role-based access to scope data
- Audit trail for all changes
- IP whitelisting for admin access
- Secure webhook signature verification
- Time-based access tokens
- Minimum privilege principle

## Acceptance Criteria

- [ ] Correctly classifies scope changes with >85% accuracy
- [ ] Generates professional change orders in <2 minutes
- [ ] Maintains complete audit trail of all scope changes
- [ ] Integrates seamlessly with Project Management Agent
- [ ] Sends change orders with email tracking enabled
- [ ] Updates scope metrics in real-time
- [ ] Alerts on scope creep patterns within 24 hours
- [ ] Handles 100+ concurrent requests without degradation
- [ ] Maintains 99.9% uptime
- [ ] All unit tests pass with >90% coverage
- [ ] All integration tests validate agent handoffs
- [ ] Performance benchmarks met under load
- [ ] Security scan passes with no critical issues
