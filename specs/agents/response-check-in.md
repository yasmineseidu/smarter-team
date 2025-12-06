# Check-In Agent - Production Specification

## Overview

**Agent Name**: `check_in`
**Category**: Response Management
**Phase**: Phase 2 - Intelligence Layer
**Coverage Requirement**: >85%

### Purpose
Systematically follow up with engaged prospects who have gone silent, using an intelligent cadence system that escalates from gentle check-ins to eventual reactivation pool transition after 14 attempts.

### Key Capabilities
- Detects silent engaged leads (no response for 2+ days)
- Generates contextual check-in messages based on conversation history
- Implements strategic cadence (2, 5, 8, 12 days, then every 3-4 days)
- Automatically transitions to reactivation pool after 14 check-ins
- Tracks all check-in attempts with full audit trail
- Integrates with Conversation Intelligence for engagement signals

---

## Dependencies

### Upstream Agents (Required)
1. **Response Handler Agent** (`response_email_handler`)
   - Provides: Conversation history, last interaction timestamp, engagement status
   - Handoff trigger: Lead has gone silent (2+ days no response)

2. **Conversation Intelligence Agent** (`response_conversation_intelligence`)
   - Provides: Engagement signals, sentiment scores, topic extraction
   - Used for: Contextualizing check-in content

### Downstream Agents (Handoff Targets)
1. **Reactivation Agent** (`offboarding_reactivation`)
   - Trigger: After 14 check-ins with no response
   - Payload: Full conversation history, check-in attempts, last engagement signals

### External Dependencies
- Instantly API (email sending)
- Supabase PostgreSQL (conversation & check-in storage)
- Claude API (content generation)
- Zep (long-term memory context)

---

## System Prompt

```
You are the Check-In Agent for Smarter Team's AI agency platform.

Your role is to follow up with engaged prospects who have gone silent, using empathy and strategic timing to re-engage without being pushy.

CORE PRINCIPLES:
1. Check-ins must feel natural and human, never robotic
2. Reference specific conversation context (past topics, pain points, interests)
3. Provide value or new information when possible
4. Respect the cadence - never rush or spam
5. Know when to stop (14 check-ins = move to reactivation pool)

CHECK-IN CADENCE:
- Check-in 1: Day 2 (gentle bump)
- Check-in 2: Day 5 (value-add or question)
- Check-in 3: Day 8 (case study or insight)
- Check-in 4: Day 12 (last direct attempt)
- Check-ins 5-14: Every 3-4 days (light touches)

CONTENT STRATEGY BY CHECK-IN NUMBER:
- 1-2: "Just following up" + conversation reference
- 3-5: Value-add (case study, insight, resource)
- 6-9: Lightweight touches (relevant news, question)
- 10-14: Permission-based ("Should I stop reaching out?")

REACTIVATION TRANSITION:
After 14 check-ins with no response, you MUST:
1. Log final check-in attempt
2. Update lead status to REACTIVATION_POOL
3. Hand off to Reactivation Agent with full context
4. Log status change reason: "14_checkins_no_response"

TONE:
- Conversational, not salesy
- Respectful of their time
- Genuinely helpful
- Self-aware (acknowledge you've reached out before)

OUTPUT FORMAT:
Always return structured JSON:
{
  "subject": "Email subject line (max 60 chars)",
  "body": "Email body (max 500 chars)",
  "check_in_number": 1-14,
  "requires_approval": true/false,
  "transition_to_reactivation": true/false,
  "context_used": ["conversation_topic_1", "pain_point_2"]
}
```

---

## Tool Definitions

### 1. `get_conversation_history`
Retrieve full conversation history for a lead.

**Input Schema:**
```python
{
  "lead_id": str,              # Required: Lead UUID
  "limit": int = 10,           # Optional: Max messages to return
  "include_sentiment": bool = True  # Include sentiment scores
}
```

**Output Schema:**
```python
{
  "lead_id": str,
  "messages": [
    {
      "id": str,
      "timestamp": datetime,
      "direction": "inbound" | "outbound",
      "content": str,
      "sentiment": float,      # -1.0 to 1.0
      "topics": List[str]
    }
  ],
  "last_response_date": datetime,
  "days_since_last_response": int,
  "engagement_level": "high" | "medium" | "low"
}
```

**Implementation:**
```python
async def get_conversation_history(
    lead_id: str,
    limit: int = 10,
    include_sentiment: bool = True
) -> dict[str, Any]:
    """Retrieve conversation history from database."""
    # Query conversation_history table
    # Join with conversation_analysis for sentiment
    # Calculate days_since_last_response
    # Return structured data
```

---

### 2. `get_check_in_count`
Get current check-in count and last check-in date for a lead.

**Input Schema:**
```python
{
  "lead_id": str  # Required: Lead UUID
}
```

**Output Schema:**
```python
{
  "lead_id": str,
  "total_check_ins": int,           # 0-14
  "last_check_in_date": datetime | None,
  "next_scheduled_check_in": datetime | None,
  "check_in_history": [
    {
      "check_in_number": int,
      "sent_at": datetime,
      "opened": bool,
      "clicked": bool,
      "replied": bool
    }
  ]
}
```

**Implementation:**
```python
async def get_check_in_count(lead_id: str) -> dict[str, Any]:
    """Get check-in count and history from database."""
    # Query check_in_logs table
    # Count total check-ins for this lead
    # Get performance metrics (open/click/reply rates)
    # Calculate next check-in date based on cadence
```

---

### 3. `generate_check_in_message`
Generate contextual check-in message using Claude.

**Input Schema:**
```python
{
  "lead_id": str,
  "check_in_number": int,           # 1-14
  "conversation_context": dict,     # From get_conversation_history
  "engagement_signals": dict        # From Conversation Intelligence
}
```

**Output Schema:**
```python
{
  "subject": str,                   # Max 60 chars
  "body": str,                      # Max 500 chars
  "tone": "gentle" | "value-add" | "permission-based",
  "context_references": List[str],  # Topics/pain points used
  "requires_approval": bool,        # Based on check-in number
  "confidence_score": float         # 0.0-1.0
}
```

**Implementation:**
```python
async def generate_check_in_message(
    lead_id: str,
    check_in_number: int,
    conversation_context: dict[str, Any],
    engagement_signals: dict[str, Any]
) -> dict[str, Any]:
    """Generate check-in using Claude API."""
    # Build prompt with conversation context
    # Include check-in number for tone adjustment
    # Reference past topics and pain points
    # Apply character limits (500 chars max)
    # Return structured message
```

---

### 4. `send_check_in_email`
Send check-in email via Instantly API.

**Input Schema:**
```python
{
  "lead_id": str,
  "check_in_number": int,
  "subject": str,
  "body": str,
  "requires_approval": bool
}
```

**Output Schema:**
```python
{
  "check_in_log_id": str,          # UUID of created log entry
  "sent_at": datetime,
  "status": "sent" | "pending_approval" | "failed",
  "instantly_message_id": str | None,
  "next_check_in_date": datetime | None
}
```

**Implementation:**
```python
async def send_check_in_email(
    lead_id: str,
    check_in_number: int,
    subject: str,
    body: str,
    requires_approval: bool
) -> dict[str, Any]:
    """Send email via Instantly and log check-in."""
    # If requires_approval: Store draft, notify human, return pending
    # Else: Send via Instantly API
    # Create check_in_logs entry
    # Calculate next_check_in_date based on cadence
    # Return status
```

---

### 5. `transition_to_reactivation_pool`
Move lead to reactivation pool after 14 check-ins.

**Input Schema:**
```python
{
  "lead_id": str,
  "reason": str = "14_checkins_no_response",
  "final_check_in_log_id": str
}
```

**Output Schema:**
```python
{
  "lead_id": str,
  "old_status": str,
  "new_status": "REACTIVATION_POOL",
  "transitioned_at": datetime,
  "handoff_task_id": str           # Celery task ID for Reactivation Agent
}
```

**Implementation:**
```python
async def transition_to_reactivation_pool(
    lead_id: str,
    reason: str,
    final_check_in_log_id: str
) -> dict[str, Any]:
    """Update lead status and hand off to Reactivation Agent."""
    # Update leads table: status = REACTIVATION_POOL
    # Create status_change_log entry
    # Prepare handoff payload with full context
    # Hand off to Reactivation Agent
    # Return handoff task ID
```

---

### 6. `get_check_in_template`
Retrieve pre-approved check-in template (optional for auto-send).

**Input Schema:**
```python
{
  "check_in_number": int,
  "template_category": "generic" | "value_add" | "permission_based"
}
```

**Output Schema:**
```python
{
  "template_id": str,
  "subject_template": str,         # With {{variable}} placeholders
  "body_template": str,
  "approval_required": bool,
  "max_uses_per_lead": int | None
}
```

**Implementation:**
```python
async def get_check_in_template(
    check_in_number: int,
    template_category: str
) -> dict[str, Any]:
    """Get pre-approved template from database."""
    # Query check_in_templates table
    # Filter by check_in_number range and category
    # Return template with placeholders
```

---

## Check-In Cadence Logic

### Cadence Schedule
| Check-In # | Days Since Last Response | Tone | Approval Required |
|------------|-------------------------|------|-------------------|
| 1 | 2 | Gentle bump | No |
| 2 | 5 | Value-add question | No |
| 3 | 8 | Case study/insight | No |
| 4 | 12 | Last direct attempt | Yes |
| 5 | 15 | Light touch | Yes |
| 6 | 19 | Light touch | Yes |
| 7 | 23 | Light touch | Yes |
| 8 | 27 | Permission-based | Yes |
| 9 | 31 | Light touch | Yes |
| 10 | 35 | Permission-based | Yes |
| 11 | 39 | Light touch | Yes |
| 12 | 43 | Permission-based | Yes |
| 13 | 47 | Light touch | Yes |
| 14 | 51 | Final permission-based | Yes |

### Cadence Calculation Logic
```python
def calculate_next_check_in_date(
    last_response_date: datetime,
    check_in_number: int
) -> datetime:
    """Calculate when next check-in should be sent."""
    if check_in_number == 1:
        days_to_add = 2
    elif check_in_number == 2:
        days_to_add = 5
    elif check_in_number == 3:
        days_to_add = 8
    elif check_in_number == 4:
        days_to_add = 12
    elif check_in_number >= 5:
        # Every 3-4 days: 15, 19, 23, 27, 31, 35, 39, 43, 47, 51
        days_to_add = 12 + ((check_in_number - 4) * 4) - 1

    return last_response_date + timedelta(days=days_to_add)
```

### Reactivation Transition Rules
```python
async def should_transition_to_reactivation(
    lead_id: str,
    check_in_count: int
) -> bool:
    """Determine if lead should move to reactivation pool."""
    # Rule 1: After 14 check-ins
    if check_in_count >= 14:
        return True

    # Rule 2: If lead explicitly unsubscribed
    lead_status = await get_lead_status(lead_id)
    if lead_status == "UNSUBSCRIBED":
        return True

    # Rule 3: If lead responded (handled elsewhere)
    # This function only called when no response

    return False
```

---

## Database Schema

### Table: `check_in_logs`
```sql
CREATE TABLE check_in_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    check_in_number INT NOT NULL CHECK (check_in_number BETWEEN 1 AND 14),
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    requires_approval BOOLEAN NOT NULL DEFAULT false,
    approval_status TEXT CHECK (approval_status IN ('pending', 'approved', 'rejected', 'auto_sent')),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    instantly_message_id TEXT,
    opened BOOLEAN DEFAULT false,
    opened_at TIMESTAMPTZ,
    clicked BOOLEAN DEFAULT false,
    clicked_at TIMESTAMPTZ,
    replied BOOLEAN DEFAULT false,
    replied_at TIMESTAMPTZ,
    reply_content TEXT,
    next_check_in_date TIMESTAMPTZ,
    context_used JSONB,  -- Topics/pain points referenced
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    INDEX idx_check_in_logs_lead_id (lead_id),
    INDEX idx_check_in_logs_sent_at (sent_at),
    INDEX idx_check_in_logs_next_check_in (next_check_in_date),
    INDEX idx_check_in_logs_approval_status (approval_status)
);
```

### Table: `check_in_templates`
```sql
CREATE TABLE check_in_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    check_in_number_min INT NOT NULL,
    check_in_number_max INT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('generic', 'value_add', 'permission_based')),
    subject_template TEXT NOT NULL,  -- With {{variable}} placeholders
    body_template TEXT NOT NULL,
    approval_required BOOLEAN NOT NULL DEFAULT false,
    max_uses_per_lead INT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    INDEX idx_check_in_templates_category (category),
    INDEX idx_check_in_templates_active (active)
);
```

### Table Updates: `leads`
Add columns to track check-in state:
```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS total_check_ins INT DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_check_in_date TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS next_check_in_date TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_leads_next_check_in ON leads(next_check_in_date)
WHERE next_check_in_date IS NOT NULL;
```

---

## Agent Implementation

### Class Structure
```python
from typing import Any
from datetime import datetime, timedelta
from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger

class CheckInAgent(BaseAgent):
    """
    Follow up with silent prospects using intelligent cadence.

    Implements 14-check-in system with automatic reactivation pool
    transition after final attempt.
    """

    def __init__(self):
        super().__init__(
            name="check_in",
            description="Follow up with silent engaged prospects"
        )
        self.max_check_ins = 14

        # Register tools
        self.register_tool(
            self.get_conversation_history,
            name="get_conversation_history",
            description="Retrieve conversation history for context"
        )
        self.register_tool(
            self.get_check_in_count,
            name="get_check_in_count",
            description="Get current check-in count and history"
        )
        self.register_tool(
            self.generate_check_in_message,
            name="generate_check_in_message",
            description="Generate contextual check-in using Claude"
        )
        self.register_tool(
            self.send_check_in_email,
            name="send_check_in_email",
            description="Send check-in via Instantly API"
        )
        self.register_tool(
            self.transition_to_reactivation_pool,
            name="transition_to_reactivation_pool",
            description="Move lead to reactivation pool after 14 check-ins"
        )
        self.register_tool(
            self.get_check_in_template,
            name="get_check_in_template",
            description="Get pre-approved template"
        )

    @property
    def system_prompt(self) -> str:
        """Return system prompt (see System Prompt section above)."""
        # Full prompt from System Prompt section

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process check-in task for a silent lead.

        Args:
            task: {
                "type": "check_in",
                "lead_id": str,
                "triggered_by": "cron" | "manual",
                "force_send": bool (optional)
            }

        Returns:
            {
                "status": "sent" | "pending_approval" | "transitioned_to_reactivation",
                "check_in_number": int,
                "check_in_log_id": str,
                "next_check_in_date": datetime | None
            }
        """
        lead_id = task["lead_id"]

        # Step 1: Get current check-in count
        check_in_data = await self.get_check_in_count(lead_id)
        check_in_number = check_in_data["total_check_ins"] + 1

        # Step 2: Check if should transition to reactivation
        if check_in_number > self.max_check_ins:
            self.logger.info(
                "Transitioning to reactivation pool",
                extra={"lead_id": lead_id, "check_in_count": check_in_number - 1}
            )
            return await self._handle_reactivation_transition(lead_id)

        # Step 3: Get conversation context
        conversation = await self.get_conversation_history(lead_id)

        # Step 4: Get engagement signals from Conversation Intelligence
        engagement_signals = await self._get_engagement_signals(lead_id)

        # Step 5: Generate check-in message
        message = await self.generate_check_in_message(
            lead_id=lead_id,
            check_in_number=check_in_number,
            conversation_context=conversation,
            engagement_signals=engagement_signals
        )

        # Step 6: Send check-in (or queue for approval)
        result = await self.send_check_in_email(
            lead_id=lead_id,
            check_in_number=check_in_number,
            subject=message["subject"],
            body=message["body"],
            requires_approval=message["requires_approval"]
        )

        self.log_action(
            "check_in.sent" if result["status"] == "sent" else "check_in.pending_approval",
            details={
                "lead_id": lead_id,
                "check_in_number": check_in_number,
                "next_check_in_date": result["next_check_in_date"]
            }
        )

        return {
            "status": result["status"],
            "check_in_number": check_in_number,
            "check_in_log_id": result["check_in_log_id"],
            "next_check_in_date": result["next_check_in_date"]
        }

    async def _handle_reactivation_transition(
        self,
        lead_id: str
    ) -> dict[str, Any]:
        """Handle transition to reactivation pool."""
        # Get final check-in log
        final_log = await self._get_final_check_in_log(lead_id)

        # Transition to reactivation pool
        transition_result = await self.transition_to_reactivation_pool(
            lead_id=lead_id,
            reason="14_checkins_no_response",
            final_check_in_log_id=final_log["id"]
        )

        return {
            "status": "transitioned_to_reactivation",
            "handoff_task_id": transition_result["handoff_task_id"],
            "check_in_number": 14,
            "next_check_in_date": None
        }

    async def _get_engagement_signals(self, lead_id: str) -> dict[str, Any]:
        """Get engagement signals from Conversation Intelligence agent."""
        # Hand off to conversation_intelligence agent for analysis
        # Or query conversation_analysis table directly
        pass

    async def _get_final_check_in_log(self, lead_id: str) -> dict[str, Any]:
        """Get the 14th check-in log entry."""
        # Query check_in_logs for check_in_number = 14
        pass
```

---

## Error Handling

### Expected Errors
1. **Lead Not Found**: Return error, log warning
2. **Instantly API Failure**: Retry 3 times, then queue for manual send
3. **Template Not Found**: Fall back to generic template
4. **Database Connection Error**: Retry with exponential backoff
5. **Check-in Already Sent Today**: Skip, log info

### Error Response Format
```python
{
    "error": {
        "code": "CHECK_IN_FAILED",
        "message": "Failed to send check-in email",
        "details": {
            "lead_id": "...",
            "check_in_number": 5,
            "reason": "instantly_api_timeout"
        }
    },
    "retry_scheduled": true,
    "retry_at": "2025-01-15T14:30:00Z"
}
```

---

## Testing Requirements

### Unit Tests (Target: >90%)
**File**: `app/backend/__tests__/unit/agents/test_check_in_agent.py`

```python
# Test cases (minimum):
1. test_check_in_agent_initialization
2. test_system_prompt_returns_string
3. test_get_conversation_history_success
4. test_get_conversation_history_no_messages
5. test_get_check_in_count_zero
6. test_get_check_in_count_multiple
7. test_calculate_next_check_in_date_check_in_1
8. test_calculate_next_check_in_date_check_in_4
9. test_calculate_next_check_in_date_check_in_14
10. test_generate_check_in_message_gentle_tone
11. test_generate_check_in_message_value_add
12. test_generate_check_in_message_permission_based
13. test_send_check_in_email_auto_send
14. test_send_check_in_email_requires_approval
15. test_transition_to_reactivation_pool_after_14
16. test_transition_does_not_occur_before_14
17. test_process_task_first_check_in
18. test_process_task_final_check_in_transitions
19. test_error_handling_instantly_api_failure
20. test_error_handling_missing_template
```

### Integration Tests (Target: >85%)
**File**: `app/backend/__tests__/integration/test_check_in_workflow.py`

```python
# Test cases (minimum):
1. test_full_check_in_workflow_auto_send
2. test_full_check_in_workflow_requires_approval
3. test_14_check_ins_transition_to_reactivation
4. test_check_in_cadence_timing_accuracy
5. test_handoff_to_reactivation_agent
6. test_conversation_intelligence_integration
7. test_instantly_api_integration
8. test_database_logging_complete
9. test_duplicate_check_in_prevention
10. test_response_resets_check_in_count
```

### Fixtures Needed
**File**: `app/backend/__tests__/fixtures/check_in_fixtures.py`

```python
@pytest.fixture
def mock_check_in_agent():
    """Mock CheckInAgent instance."""
    pass

@pytest.fixture
def sample_conversation_history():
    """Sample conversation with 3 messages."""
    pass

@pytest.fixture
def sample_check_in_templates():
    """Pre-approved check-in templates."""
    pass

@pytest.fixture
def mock_instantly_client():
    """Mock Instantly API client."""
    pass
```

---

## Celery Task (Cron Automation)

**File**: `app/backend/src/tasks/check_in_tasks.py`

```python
try:
    from src.celery_app import celery_app
except ImportError:
    from unittest.mock import MagicMock
    celery_app = MagicMock()
    celery_app.task = lambda *_args, **_kwargs: lambda f: f

from src.config import get_agent_logger
from src.agents.check_in.agent import CheckInAgent

logger = get_agent_logger("check_in_tasks")

@celery_app.task(bind=True, max_retries=3)
def process_daily_check_ins(self):
    """
    Daily cron job to send check-ins to silent engaged leads.

    Runs daily at 2:00 PM EST.
    """
    logger.info("Starting daily check-in processing")

    # Query leads with next_check_in_date <= NOW
    # For each lead:
    #   - Instantiate CheckInAgent
    #   - Call process_task({"type": "check_in", "lead_id": lead.id})
    #   - Log results

    logger.info("Daily check-in processing complete")

@celery_app.task(bind=True, max_retries=3)
def process_single_check_in(self, lead_id: str, force_send: bool = False):
    """
    Process check-in for a single lead.

    Args:
        lead_id: UUID of lead
        force_send: Skip approval requirement if True
    """
    agent = CheckInAgent()
    result = await agent.process_task({
        "type": "check_in",
        "lead_id": lead_id,
        "triggered_by": "manual",
        "force_send": force_send
    })
    return result
```

### Celery Beat Schedule
**File**: `app/backend/src/celery_app.py`

```python
celery_app.conf.beat_schedule = {
    'daily-check-ins': {
        'task': 'src.tasks.check_in_tasks.process_daily_check_ins',
        'schedule': crontab(hour=14, minute=0),  # Daily at 2:00 PM
    },
}
```

---

## Human-in-the-Loop

### Approval Gates
- **Check-ins 1-3**: Auto-send (no approval required)
- **Check-ins 4-14**: Require human approval

### Approval Workflow
1. Check-in drafted by agent
2. Stored in `check_in_logs` with `approval_status = 'pending'`
3. Notification sent to Slack/Telegram with:
   - Lead name & company
   - Check-in number
   - Draft subject & body
   - Conversation context
   - Approve/Reject/Edit buttons
4. On approval: Send via Instantly, update `approval_status = 'approved'`
5. On rejection: Update `approval_status = 'rejected'`, optionally reschedule
6. On edit: Human edits content, then approves

### Notification Format (Slack)
```
🔔 Check-in #5 Ready for Approval

Lead: John Doe @ Acme Corp
Last Response: 15 days ago
Engagement: Medium

Subject: Quick thought about scaling your ops

Body:
Hi John,

I was thinking about our conversation on scaling operations. We just published a case study on how TechCo reduced onboarding time by 60% - thought you'd find it relevant.

Would you like me to send it over?

[Approve] [Edit] [Reject]
```

---

## Metrics & Monitoring

### Key Metrics
- Check-in send rate (daily)
- Check-in open rate (by check-in number)
- Check-in reply rate (by check-in number)
- Reactivation pool transition rate
- Average check-ins before response
- Average check-ins before reactivation
- Template performance (if templates used)

### Logging
All actions logged with structured data:
```python
self.logger.info(
    "Check-in sent",
    extra={
        "lead_id": "...",
        "check_in_number": 5,
        "requires_approval": False,
        "next_check_in_date": "2025-01-20"
    }
)
```

---

## Deployment Checklist

- [ ] Database migrations created and tested
- [ ] Check-in templates seeded
- [ ] Instantly API credentials configured
- [ ] Celery beat schedule configured
- [ ] Slack/Telegram webhook configured for approvals
- [ ] All unit tests pass (>90% coverage)
- [ ] All integration tests pass (>85% coverage)
- [ ] Pre-commit hooks pass (Ruff, MyPy)
- [ ] Documentation updated
- [ ] Task moved to `_completed/`
- [ ] `TASK-LOG.md` updated

---

## Future Enhancements (Phase 3+)

1. **A/B Testing**: Test different check-in cadences
2. **Personalization Variables**: Dynamic content based on lead attributes
3. **Multi-Channel Check-Ins**: SMS, LinkedIn, voice after email failures
4. **ML-Based Cadence**: Predict optimal check-in timing per lead
5. **Auto-Pause**: Detect out-of-office, pause check-ins automatically
6. **Sentiment Analysis**: Skip check-ins if last sentiment was negative
7. **Team Collaboration**: Assign check-ins to specific sales reps
