# Onboarding Orchestrator Agent - Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Priority:** Phase 4 - Client Delivery
**Agent Type:** Orchestration + Automation
**Coverage Target:** >85%

---

## Overview

The Onboarding Orchestrator Agent manages the complete new client onboarding lifecycle from contract signing to project activation. It automates the 8-step onboarding process, coordinates with internal systems (Deformity, Cal.com, ClickUp, Google Drive), tracks progress, sends automated communications, and ensures smooth handoffs to the Internal Setup Agent and project delivery teams.

**Key Responsibilities:**
- Trigger onboarding workflow on contract signed event
- Send welcome emails and intake forms (Deformity)
- Monitor form completion and access provisioning
- Schedule kickoff calls (Cal.com)
- Coordinate internal setup with Internal Setup Agent
- Track onboarding state transitions
- Handle stuck detection escalations
- Complete onboarding and transition to ACTIVE_PROJECT

---

## Agent Configuration

### BaseAgent Properties

```python
name: "onboarding_orchestrator"
description: "Manages new client onboarding from contract to project activation"
```

### Dependencies

**Agent Dependencies:**
- `internal_setup` - Creates internal infrastructure (ClickUp, Drive, Airtable, GHL)
- `onboarding_stuck_detector` - Monitors and escalates stalled onboardings
- `payment_processing` - Triggers onboarding on contract signed event

**Integration Dependencies:**
- Deformity API (intake forms)
- Cal.com API (kickoff scheduling)
- Email service (welcome/reminder emails)
- Database (onboarding state tracking)

---

## System Prompt

```
You are the Onboarding Orchestrator Agent for Smarter Team, an AI agency automation system.

Your role is to manage the complete client onboarding process from contract signing to project activation.

RESPONSIBILITIES:
1. Welcome Communication: Send personalized welcome emails immediately upon contract signing
2. Intake Form Management: Deploy Deformity intake forms and monitor completion
3. Access Provisioning: Request and track client access credentials
4. Kickoff Scheduling: Coordinate kickoff calls via Cal.com within 5-7 days
5. Internal Setup: Handoff to Internal Setup Agent for infrastructure creation
6. Progress Tracking: Monitor all onboarding steps and maintain state
7. Transition Management: Move clients from CLOSED_WON → ONBOARDING → ACTIVE_PROJECT
8. Documentation: Ensure all onboarding data is captured and accessible

ONBOARDING STEPS (8-step checklist):
1. ✅ Welcome email sent
2. ✅ Intake form deployed and link sent
3. ✅ Intake form completed by client
4. ✅ Access credentials requested
5. ✅ Internal setup triggered (handoff to Internal Setup Agent)
6. ✅ Kickoff call scheduled (Cal.com)
7. ✅ Kickoff call completed
8. ✅ Project scope documented and onboarding complete

TIMELINE TARGETS:
- Day 0: Welcome email + intake form sent
- Day 1-3: Form completed + access requested
- Day 3-5: Internal setup complete (via Internal Setup Agent)
- Day 5-7: Kickoff call scheduled and completed
- Day 7: Onboarding complete → ACTIVE_PROJECT

STATE TRANSITIONS:
- Contract signed: CLOSED_WON → ONBOARDING
- Onboarding complete: ONBOARDING → ACTIVE_PROJECT
- Stuck >7 days: ONBOARDING → ONBOARDING_STUCK (escalate to human)

ESCALATION RULES:
- If intake form not completed in 3 days: Alert Stuck Detector Agent
- If no communication in 5 days: Alert Stuck Detector Agent
- If onboarding exceeds 10 days: Escalate to human via Slack/Telegram

COMMUNICATION TONE:
- Warm, professional, and welcoming
- Action-oriented with clear next steps
- Use client's first name
- Provide links and resources proactively
- Set clear expectations on timelines

TOOLS AVAILABLE:
- send_email: Send welcome/reminder emails with templates
- create_intake_form: Generate Deformity intake forms
- check_form_status: Query intake form completion status
- schedule_kickoff: Book Cal.com meeting slots
- update_onboarding_status: Update onboarding progress in database
- handoff_to_internal_setup: Trigger Internal Setup Agent
- log_onboarding_event: Track all onboarding events for audit

ERROR HANDLING:
- Retry failed API calls 3x with exponential backoff
- Log all errors with context (client_id, step, error_details)
- Escalate to human if critical step fails after retries
- Never proceed to next step if previous step incomplete

You work autonomously but escalate when uncertain or when human approval is needed.
```

---

## Tool Definitions

### 1. send_email

**Purpose:** Send templated emails (welcome, intake form, reminders)

**Function Signature:**
```python
async def send_email(
    client_id: str,
    template_name: str,
    context: dict[str, Any],
    priority: str = "normal"
) -> dict[str, Any]:
    """
    Send email using predefined templates.

    Args:
        client_id: Client UUID
        template_name: Template identifier (welcome, intake_form, reminder)
        context: Template variables (first_name, intake_form_link, etc.)
        priority: Email priority (critical, high, normal, low)

    Returns:
        {
            "email_id": str,
            "sent_at": str (ISO 8601),
            "status": str (sent, failed, queued),
            "error": Optional[str]
        }

    Raises:
        ValueError: Invalid template_name or missing required context
        EmailServiceError: Email service failure after retries
    """
```

**Templates:**
- `welcome`: Welcome email with intake form link
- `intake_form_reminder`: Reminder to complete intake form
- `access_request`: Request for client access credentials
- `kickoff_scheduled`: Kickoff call confirmation

**Implementation Notes:**
- Use environment variable `SMTP_*` config or email integration client
- Log all sent emails to `email_logs` table
- Retry failed sends 3x with exponential backoff (5s, 15s, 45s)
- Track open/click rates if available

---

### 2. create_intake_form

**Purpose:** Generate Deformity intake form for client

**Function Signature:**
```python
async def create_intake_form(
    client_id: str,
    project_type: str,
    custom_questions: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """
    Create customized intake form via Deformity API.

    Args:
        client_id: Client UUID
        project_type: Project category (web_app, ai_solution, integration, etc.)
        custom_questions: Additional questions beyond default template

    Returns:
        {
            "form_id": str,
            "form_url": str,
            "expires_at": str (ISO 8601),
            "question_count": int
        }

    Raises:
        DeformityAPIError: API failure after retries
        ValidationError: Invalid project_type or question format
    """
```

**Default Questions (all project types):**
1. Business name and website
2. Primary contact (name, email, phone)
3. Project goals and success metrics
4. Target launch date
5. Budget expectations (if not finalized)
6. Technical requirements/constraints
7. Brand guidelines and assets
8. Access credentials needed (list)
9. Preferred communication channels
10. Availability for kickoff call

**Implementation Notes:**
- Use Deformity API client (BaseIntegrationClient)
- Store form_id in `onboarding_progress` table
- Set form expiration to 7 days
- Include webhook for form completion notification

---

### 3. check_form_status

**Purpose:** Query intake form completion status

**Function Signature:**
```python
async def check_form_status(
    form_id: str
) -> dict[str, Any]:
    """
    Check if intake form has been completed.

    Args:
        form_id: Deformity form identifier

    Returns:
        {
            "completed": bool,
            "completed_at": Optional[str] (ISO 8601),
            "response_count": int,
            "responses": dict[str, Any] (if completed),
            "last_updated": str (ISO 8601)
        }

    Raises:
        DeformityAPIError: API failure after retries
    """
```

**Implementation Notes:**
- Cache results for 5 minutes to avoid rate limiting
- Store responses in `intake_responses` table when completed
- Trigger webhook handler if form just completed

---

### 4. schedule_kickoff

**Purpose:** Schedule kickoff call via Cal.com

**Function Signature:**
```python
async def schedule_kickoff(
    client_id: str,
    attendees: list[str],
    duration_minutes: int = 60,
    preferred_times: list[str] | None = None
) -> dict[str, Any]:
    """
    Schedule kickoff call using Cal.com API.

    Args:
        client_id: Client UUID
        attendees: Email addresses of attendees
        duration_minutes: Meeting duration (default 60)
        preferred_times: Client preferred time slots (ISO 8601)

    Returns:
        {
            "booking_id": str,
            "meeting_url": str,
            "scheduled_time": str (ISO 8601),
            "calendar_invite_sent": bool,
            "reschedule_url": str
        }

    Raises:
        CalComAPIError: API failure after retries
        NoAvailabilityError: No available slots found
    """
```

**Implementation Notes:**
- Use Cal.com API client (extends BaseIntegrationClient)
- Link to Cal.com event type for "Client Kickoff"
- Send calendar invites automatically
- Store booking_id in `onboarding_progress` table
- Set reminder 24 hours before call

---

### 5. update_onboarding_status

**Purpose:** Update onboarding progress and state

**Function Signature:**
```python
async def update_onboarding_status(
    client_id: str,
    step: str,
    status: str,
    metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Update onboarding step status in database.

    Args:
        client_id: Client UUID
        step: Onboarding step identifier (welcome_sent, form_completed, etc.)
        status: Step status (pending, in_progress, completed, failed)
        metadata: Additional step-specific data

    Returns:
        {
            "progress_id": str,
            "updated_at": str (ISO 8601),
            "completion_percentage": int,
            "next_step": str
        }

    Raises:
        DatabaseError: Database operation failure
        ValidationError: Invalid step or status value
    """
```

**Valid Steps:**
- `welcome_sent`
- `form_sent`
- `form_completed`
- `access_requested`
- `internal_setup_triggered`
- `kickoff_scheduled`
- `kickoff_completed`
- `scope_documented`

**Valid Statuses:**
- `pending`: Not started
- `in_progress`: Currently working on
- `completed`: Successfully finished
- `failed`: Failed after retries
- `skipped`: Intentionally skipped

**Implementation Notes:**
- Use async SQLAlchemy ORM
- Update `onboarding_progress` table
- Calculate completion percentage automatically
- Trigger state transition webhooks

---

### 6. handoff_to_internal_setup

**Purpose:** Handoff to Internal Setup Agent for infrastructure creation

**Function Signature:**
```python
async def handoff_to_internal_setup(
    client_id: str,
    project_details: dict[str, Any],
    priority: str = "normal"
) -> str:
    """
    Handoff to Internal Setup Agent via BaseAgent.handoff_to().

    Args:
        client_id: Client UUID
        project_details: Client and project information from intake form
        priority: Task priority (critical, high, normal, low)

    Returns:
        task_id: Celery task ID for tracking

    Raises:
        HandoffError: Handoff failure
    """
```

**Project Details Payload:**
```python
{
    "client_id": str,
    "client_name": str,
    "project_name": str,
    "project_type": str,
    "team_members": list[str],
    "drive_folder_template": str,
    "clickup_template_id": str,
    "airtable_base_id": str,
    "slack_channel_required": bool
}
```

**Implementation Notes:**
- Use `self.handoff_to()` from BaseAgent
- Wait for Internal Setup Agent completion (poll task status)
- Store returned task_id in `onboarding_progress`
- Set timeout of 30 minutes for setup completion

---

### 7. log_onboarding_event

**Purpose:** Log all onboarding events for audit trail

**Function Signature:**
```python
async def log_onboarding_event(
    client_id: str,
    event_type: str,
    event_data: dict[str, Any],
    severity: str = "info"
) -> None:
    """
    Log onboarding event to audit trail.

    Args:
        client_id: Client UUID
        event_type: Event category (email_sent, form_created, handoff, etc.)
        event_data: Event-specific details
        severity: Log level (debug, info, warning, error, critical)

    Returns:
        None

    Raises:
        DatabaseError: Logging failure (non-blocking)
    """
```

**Event Types:**
- `onboarding_started`
- `email_sent`
- `form_created`
- `form_completed`
- `access_requested`
- `setup_handoff`
- `kickoff_scheduled`
- `kickoff_completed`
- `onboarding_completed`
- `error_occurred`

**Implementation Notes:**
- Write to `onboarding_events` table
- Include agent name and timestamp
- Non-blocking (log failures shouldn't halt onboarding)
- Use structured logging via `get_agent_logger()`

---

## Database Schema

### Table: onboarding_progress

**Purpose:** Track onboarding state and progress

```sql
CREATE TABLE onboarding_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- State tracking
    current_state VARCHAR(50) NOT NULL DEFAULT 'ONBOARDING',
    current_step VARCHAR(50) NOT NULL DEFAULT 'welcome_sent',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Step statuses
    welcome_sent BOOLEAN DEFAULT FALSE,
    form_sent BOOLEAN DEFAULT FALSE,
    form_completed BOOLEAN DEFAULT FALSE,
    access_requested BOOLEAN DEFAULT FALSE,
    internal_setup_triggered BOOLEAN DEFAULT FALSE,
    kickoff_scheduled BOOLEAN DEFAULT FALSE,
    kickoff_completed BOOLEAN DEFAULT FALSE,
    scope_documented BOOLEAN DEFAULT FALSE,

    -- External IDs
    form_id VARCHAR(255),
    form_url TEXT,
    kickoff_booking_id VARCHAR(255),
    setup_task_id VARCHAR(255),

    -- Metrics
    completion_percentage INT DEFAULT 0,
    days_in_onboarding INT GENERATED ALWAYS AS (
        EXTRACT(DAY FROM (COALESCE(completed_at, NOW()) - started_at))
    ) STORED,
    stuck BOOLEAN DEFAULT FALSE,
    stuck_reason VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes
    CONSTRAINT valid_state CHECK (current_state IN (
        'CLOSED_WON', 'ONBOARDING', 'ONBOARDING_STUCK', 'ACTIVE_PROJECT'
    )),
    CONSTRAINT valid_step CHECK (current_step IN (
        'welcome_sent', 'form_sent', 'form_completed', 'access_requested',
        'internal_setup_triggered', 'kickoff_scheduled', 'kickoff_completed',
        'scope_documented'
    ))
);

CREATE INDEX idx_onboarding_client ON onboarding_progress(client_id);
CREATE INDEX idx_onboarding_state ON onboarding_progress(current_state);
CREATE INDEX idx_onboarding_stuck ON onboarding_progress(stuck) WHERE stuck = TRUE;
CREATE INDEX idx_onboarding_active ON onboarding_progress(current_state)
    WHERE current_state = 'ONBOARDING';
```

### Table: onboarding_steps

**Purpose:** Detailed step-by-step tracking with timestamps

```sql
CREATE TABLE onboarding_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    progress_id UUID NOT NULL REFERENCES onboarding_progress(id) ON DELETE CASCADE,

    step_name VARCHAR(50) NOT NULL,
    step_order INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,

    error_message TEXT,
    retry_count INT DEFAULT 0,
    metadata JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'in_progress', 'completed', 'failed', 'skipped'
    )),
    UNIQUE(progress_id, step_name)
);

CREATE INDEX idx_steps_progress ON onboarding_steps(progress_id);
CREATE INDEX idx_steps_status ON onboarding_steps(status);
```

### Table: intake_responses

**Purpose:** Store Deformity intake form responses

```sql
CREATE TABLE intake_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    form_id VARCHAR(255) NOT NULL,

    -- Form data
    responses JSONB NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL,

    -- Extracted fields (for easy querying)
    business_name VARCHAR(255),
    primary_contact JSONB,
    project_goals TEXT,
    target_launch_date DATE,
    budget_expectations VARCHAR(100),
    access_credentials JSONB,
    preferred_communication VARCHAR(50),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(form_id)
);

CREATE INDEX idx_intake_client ON intake_responses(client_id);
CREATE INDEX idx_intake_form ON intake_responses(form_id);
```

### Table: onboarding_events

**Purpose:** Audit trail for all onboarding events

```sql
CREATE TABLE onboarding_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    progress_id UUID REFERENCES onboarding_progress(id) ON DELETE SET NULL,

    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',

    agent_name VARCHAR(50),
    event_data JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_severity CHECK (severity IN (
        'debug', 'info', 'warning', 'error', 'critical'
    ))
);

CREATE INDEX idx_events_client ON onboarding_events(client_id);
CREATE INDEX idx_events_type ON onboarding_events(event_type);
CREATE INDEX idx_events_created ON onboarding_events(created_at DESC);
```

---

## Integration Clients

### DeformityClient

**Purpose:** Interact with Deformity API for intake forms

**File:** `app/backend/src/integrations/deformity.py`

```python
from src.integrations.base import BaseIntegrationClient

class DeformityClient(BaseIntegrationClient):
    """
    Deformity API client for creating and managing intake forms.

    Docs: https://deformity.com/api/docs (placeholder)
    """

    def __init__(self, api_key: str):
        super().__init__(
            name="deformity",
            base_url="https://api.deformity.com/v1",
            api_key=api_key,
            timeout=30.0
        )

    async def create_form(
        self,
        title: str,
        questions: list[dict[str, Any]],
        webhook_url: str | None = None,
        expires_in_days: int = 7
    ) -> dict[str, Any]:
        """Create a new intake form."""
        payload = {
            "title": title,
            "questions": questions,
            "webhook_url": webhook_url,
            "expires_in_days": expires_in_days
        }
        return await self.post("/forms", json=payload)

    async def get_form_status(self, form_id: str) -> dict[str, Any]:
        """Get form completion status."""
        return await self.get(f"/forms/{form_id}")

    async def get_form_responses(self, form_id: str) -> dict[str, Any]:
        """Get form responses."""
        return await self.get(f"/forms/{form_id}/responses")
```

**Environment Variable:**
- `DEFORMITY_API_KEY` (add to .env.example)

---

### CalComClient

**Purpose:** Interact with Cal.com API for scheduling

**File:** `app/backend/src/integrations/calcom.py`

```python
from src.integrations.base import BaseIntegrationClient

class CalComClient(BaseIntegrationClient):
    """
    Cal.com API client for scheduling kickoff calls.

    Docs: https://cal.com/docs/api-reference
    """

    def __init__(self, api_key: str):
        super().__init__(
            name="calcom",
            base_url="https://api.cal.com/v1",
            api_key=api_key,
            timeout=30.0
        )

    async def create_booking(
        self,
        event_type_id: int,
        attendees: list[dict[str, str]],
        start_time: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create a new booking."""
        payload = {
            "eventTypeId": event_type_id,
            "attendees": attendees,
            "start": start_time,
            "metadata": metadata or {}
        }
        return await self.post("/bookings", json=payload)

    async def get_availability(
        self,
        event_type_id: int,
        date_from: str,
        date_to: str
    ) -> dict[str, Any]:
        """Get available time slots."""
        params = {
            "eventTypeId": event_type_id,
            "dateFrom": date_from,
            "dateTo": date_to
        }
        return await self.get("/availability", params=params)

    async def cancel_booking(self, booking_id: str, reason: str) -> dict[str, Any]:
        """Cancel a booking."""
        payload = {"reason": reason}
        return await self.delete(f"/bookings/{booking_id}", json=payload)
```

**Environment Variable:**
- `CAL_COM_API_KEY` (already in .env.example)

---

## Email Templates

### Template: welcome

**Subject:** Welcome to Smarter Team! 🎉

**Body:**
```html
Hi {{first_name}},

We're thrilled to officially welcome you as a client!

To kick things off, please complete this short questionnaire:
{{intake_form_link}}

This helps us understand your business better and ensures we hit the ground running.

Once you've completed the form, we'll schedule our kickoff call within the next few days.

Excited to get started!

Best regards,
Smarter Team
```

### Template: intake_form_reminder

**Subject:** Quick reminder: Intake form

**Body:**
```html
Hi {{first_name}},

Just checking in - I noticed the intake form is still pending. Here's the link again:
{{intake_form_link}}

This helps us prepare for your kickoff call and ensures we're aligned on goals.

Let me know if you have any questions!

Best regards,
Smarter Team
```

### Template: access_request

**Subject:** Access credentials needed

**Body:**
```html
Hi {{first_name}},

Thanks for completing the intake form!

To begin work, we'll need access to the following:
{{access_list}}

Please send these credentials at your earliest convenience. We'll keep them secure.

Let me know if you have any questions or concerns.

Best regards,
Smarter Team
```

### Template: kickoff_scheduled

**Subject:** Kickoff call scheduled - {{scheduled_time}}

**Body:**
```html
Hi {{first_name}},

Great news! Your kickoff call is scheduled for:

📅 {{scheduled_time}}
🔗 {{meeting_url}}

We'll use this call to:
- Review your project goals
- Discuss timeline and milestones
- Answer any questions you have
- Finalize project scope

Calendar invite attached. See you then!

Best regards,
Smarter Team
```

---

## Process Flow

### 1. Contract Signed Event (Trigger)

```python
# Webhook: POST /webhooks/contract-signed
# Triggered by Payment Processing Agent

async def handle_contract_signed(event: dict[str, Any]) -> None:
    """
    Handle contract signed webhook.

    Event payload:
    {
        "client_id": str,
        "contract_id": str,
        "signed_at": str,
        "client_name": str,
        "client_email": str,
        "project_type": str
    }
    """
    # 1. Create onboarding progress record
    progress = await create_onboarding_progress(event["client_id"])

    # 2. Send welcome email
    await send_email(
        client_id=event["client_id"],
        template_name="welcome",
        context={
            "first_name": extract_first_name(event["client_name"]),
            "intake_form_link": "{{ form_url }}"  # Populated after form creation
        }
    )

    # 3. Create intake form
    form = await create_intake_form(
        client_id=event["client_id"],
        project_type=event["project_type"]
    )

    # 4. Send intake form email
    await send_email(
        client_id=event["client_id"],
        template_name="intake_form",
        context={
            "first_name": extract_first_name(event["client_name"]),
            "intake_form_link": form["form_url"]
        }
    )

    # 5. Update progress
    await update_onboarding_status(
        client_id=event["client_id"],
        step="form_sent",
        status="completed",
        metadata={"form_id": form["form_id"], "form_url": form["form_url"]}
    )

    # 6. Log event
    await log_onboarding_event(
        client_id=event["client_id"],
        event_type="onboarding_started",
        event_data={"trigger": "contract_signed", "contract_id": event["contract_id"]}
    )
```

### 2. Form Completion Event (Webhook)

```python
# Webhook: POST /webhooks/deformity/form-completed

async def handle_form_completed(event: dict[str, Any]) -> None:
    """
    Handle Deformity form completion webhook.

    Event payload:
    {
        "form_id": str,
        "completed_at": str,
        "responses": dict
    }
    """
    # 1. Get client_id from form_id
    progress = await get_progress_by_form_id(event["form_id"])

    # 2. Store responses
    await store_intake_responses(
        client_id=progress.client_id,
        form_id=event["form_id"],
        responses=event["responses"],
        completed_at=event["completed_at"]
    )

    # 3. Update progress
    await update_onboarding_status(
        client_id=progress.client_id,
        step="form_completed",
        status="completed"
    )

    # 4. Request access credentials (if needed)
    access_list = extract_access_requirements(event["responses"])
    if access_list:
        await send_email(
            client_id=progress.client_id,
            template_name="access_request",
            context={
                "first_name": event["responses"]["primary_contact"]["first_name"],
                "access_list": format_access_list(access_list)
            }
        )

    # 5. Handoff to Internal Setup Agent
    setup_task_id = await handoff_to_internal_setup(
        client_id=progress.client_id,
        project_details={
            "client_id": progress.client_id,
            "client_name": event["responses"]["business_name"],
            "project_name": event["responses"]["project_name"],
            "project_type": event["responses"]["project_type"],
            "team_members": extract_team_members(event["responses"]),
            "slack_channel_required": event["responses"].get("slack_required", False)
        },
        priority="high"
    )

    # 6. Update progress with setup task ID
    await update_onboarding_status(
        client_id=progress.client_id,
        step="internal_setup_triggered",
        status="completed",
        metadata={"setup_task_id": setup_task_id}
    )
```

### 3. Internal Setup Complete (Callback)

```python
# Called by Internal Setup Agent upon completion

async def handle_setup_complete(task_result: dict[str, Any]) -> None:
    """
    Handle internal setup completion callback.

    Task result:
    {
        "client_id": str,
        "infrastructure": {
            "clickup_project_id": str,
            "drive_folder_id": str,
            "airtable_record_id": str,
            "ghl_contact_id": str,
            "slack_channel_id": str
        },
        "setup_completed_at": str
    }
    """
    # 1. Get availability for next 7 days
    availability = await get_cal_com_availability(
        date_from=tomorrow(),
        date_to=seven_days_from_now()
    )

    # 2. Schedule kickoff call
    booking = await schedule_kickoff(
        client_id=task_result["client_id"],
        attendees=[get_client_email(task_result["client_id"])],
        duration_minutes=60,
        preferred_times=availability["slots"][:5]  # Top 5 slots
    )

    # 3. Send kickoff confirmation email
    await send_email(
        client_id=task_result["client_id"],
        template_name="kickoff_scheduled",
        context={
            "first_name": get_client_first_name(task_result["client_id"]),
            "scheduled_time": format_datetime(booking["scheduled_time"]),
            "meeting_url": booking["meeting_url"]
        }
    )

    # 4. Update progress
    await update_onboarding_status(
        client_id=task_result["client_id"],
        step="kickoff_scheduled",
        status="completed",
        metadata={
            "booking_id": booking["booking_id"],
            "scheduled_time": booking["scheduled_time"]
        }
    )
```

### 4. Kickoff Call Complete (Manual Trigger)

```python
# Triggered manually or via Cal.com webhook

async def handle_kickoff_complete(event: dict[str, Any]) -> None:
    """
    Handle kickoff call completion.

    Event payload:
    {
        "client_id": str,
        "booking_id": str,
        "completed_at": str,
        "meeting_notes": Optional[str],
        "scope_documented": bool
    }
    """
    # 1. Update kickoff step
    await update_onboarding_status(
        client_id=event["client_id"],
        step="kickoff_completed",
        status="completed",
        metadata={
            "completed_at": event["completed_at"],
            "meeting_notes": event.get("meeting_notes")
        }
    )

    # 2. Check if scope documented
    if event.get("scope_documented"):
        await complete_onboarding(event["client_id"])
    else:
        # Escalate to PM or human to document scope
        await escalate_scope_documentation(event["client_id"])
```

### 5. Complete Onboarding (Final Step)

```python
async def complete_onboarding(client_id: str) -> None:
    """
    Complete onboarding and transition to ACTIVE_PROJECT.
    """
    # 1. Update final step
    await update_onboarding_status(
        client_id=client_id,
        step="scope_documented",
        status="completed"
    )

    # 2. Mark progress as complete
    await mark_progress_complete(client_id)

    # 3. Transition state to ACTIVE_PROJECT
    await transition_state(
        client_id=client_id,
        from_state="ONBOARDING",
        to_state="ACTIVE_PROJECT"
    )

    # 4. Handoff to Project Manager Agent
    await handoff_to(
        target_agent="project_manager",
        payload={
            "client_id": client_id,
            "onboarding_completed_at": datetime.now().isoformat(),
            "infrastructure": get_infrastructure_details(client_id),
            "intake_responses": get_intake_responses(client_id)
        },
        priority="high"
    )

    # 5. Log completion
    await log_onboarding_event(
        client_id=client_id,
        event_type="onboarding_completed",
        event_data={"duration_days": get_onboarding_duration(client_id)}
    )
```

---

## State Transitions

```
CLOSED_WON
    |
    | (contract signed)
    v
ONBOARDING
    |
    +-- (form not completed in 3 days) --> Alert Stuck Detector
    |
    +-- (no communication in 5 days) --> Alert Stuck Detector
    |
    +-- (>7 days total) --> ONBOARDING_STUCK (escalate)
    |
    | (all steps complete)
    v
ACTIVE_PROJECT
```

**State Machine Rules:**
1. Only transition to ONBOARDING after contract signed event
2. Only transition to ACTIVE_PROJECT after all 8 steps complete
3. ONBOARDING_STUCK requires human intervention to resume
4. No backwards transitions (except manual override)

---

## Error Handling

### Retry Strategy

**All external API calls:**
- Retry count: 3
- Backoff: Exponential (5s, 15s, 45s)
- Timeout: 30s per request
- Circuit breaker: Open after 5 consecutive failures

**Critical failures (escalate after retries):**
- Email send failures
- Deformity API errors
- Cal.com booking failures
- Database write failures

**Non-critical failures (log but continue):**
- Audit log write failures
- Analytics tracking errors
- Notification delivery failures

### Error Scenarios

#### 1. Deformity API Down
```python
try:
    form = await create_intake_form(client_id, project_type)
except DeformityAPIError as e:
    # Retry 3x with exponential backoff
    if retries_exhausted:
        # Escalate to human
        await notify_slack("Deformity API down - manual intervention needed")
        await update_onboarding_status(
            client_id=client_id,
            step="form_sent",
            status="failed",
            metadata={"error": str(e)}
        )
```

#### 2. Client Not Responding
```python
# Handled by Stuck Detector Agent
# Onboarding Orchestrator just logs events
if days_since_form_sent >= 3 and not form_completed:
    await trigger_stuck_detector(client_id, reason="intake_form_timeout")
```

#### 3. Cal.com No Availability
```python
try:
    booking = await schedule_kickoff(client_id, attendees)
except NoAvailabilityError:
    # Escalate to human to manually schedule
    await notify_slack(f"No Cal.com availability for {client_id}")
    await send_email(
        client_id=client_id,
        template_name="manual_scheduling_required",
        context={"calendly_link": get_backup_scheduling_link()}
    )
```

---

## Testing Requirements

**Coverage Target:** >85%

### Unit Tests

**File:** `app/backend/__tests__/unit/agents/test_onboarding_orchestrator.py`

**Test Cases:**

1. **Agent Initialization**
   - ✅ Test agent name and description set correctly
   - ✅ Test system prompt is non-empty string
   - ✅ Test logger initialized properly

2. **Tool Registration**
   - ✅ Test all 7 tools registered on init
   - ✅ Test tool names and descriptions correct

3. **send_email Tool**
   - ✅ Test welcome email sent with correct template
   - ✅ Test template variable substitution
   - ✅ Test invalid template name raises ValueError
   - ✅ Test retry logic on failure (3 retries)
   - ✅ Test email logged to database

4. **create_intake_form Tool**
   - ✅ Test form created via Deformity API
   - ✅ Test custom questions merged with defaults
   - ✅ Test form expiration set to 7 days
   - ✅ Test webhook URL included
   - ✅ Test API error handling and retries

5. **check_form_status Tool**
   - ✅ Test status check returns correct data
   - ✅ Test caching (5 minute TTL)
   - ✅ Test completed form stores responses

6. **schedule_kickoff Tool**
   - ✅ Test booking created via Cal.com
   - ✅ Test calendar invites sent
   - ✅ Test no availability error handling
   - ✅ Test preferred times respected

7. **update_onboarding_status Tool**
   - ✅ Test progress record updated
   - ✅ Test completion percentage calculated
   - ✅ Test invalid step raises ValueError
   - ✅ Test database rollback on error

8. **handoff_to_internal_setup Tool**
   - ✅ Test handoff task created via Celery
   - ✅ Test task ID returned and stored
   - ✅ Test payload structure validated
   - ✅ Test priority levels work

9. **log_onboarding_event Tool**
   - ✅ Test event logged to database
   - ✅ Test non-blocking behavior (no exception on failure)
   - ✅ Test severity levels
   - ✅ Test structured logging

### Integration Tests

**File:** `app/backend/__tests__/integration/test_onboarding_flow.py`

**Test Cases:**

1. **Full Onboarding Flow (Happy Path)**
   - ✅ Contract signed → welcome email sent
   - ✅ Intake form created and sent
   - ✅ Form completion → internal setup triggered
   - ✅ Setup complete → kickoff scheduled
   - ✅ Kickoff complete → transition to ACTIVE_PROJECT
   - ✅ All database records created correctly
   - ✅ All handoffs successful

2. **Form Not Completed (Stuck Detection)**
   - ✅ Form sent but not completed in 3 days
   - ✅ Stuck Detector Agent notified
   - ✅ Reminder emails sent
   - ✅ Escalation after 7 days

3. **API Failure Recovery**
   - ✅ Deformity API down → retry → escalate
   - ✅ Cal.com API down → fallback scheduling
   - ✅ Database failure → transaction rollback

4. **State Transition Validation**
   - ✅ Cannot transition to ACTIVE_PROJECT without all steps
   - ✅ State transitions logged to events table
   - ✅ Backward transitions prevented

5. **Concurrent Onboardings**
   - ✅ Multiple clients onboarding simultaneously
   - ✅ No race conditions on database writes
   - ✅ Celery task queue handles load

### Fixtures

**File:** `app/backend/__tests__/fixtures/onboarding_fixtures.py`

```python
import pytest
from datetime import datetime, timedelta

@pytest.fixture
def mock_contract_signed_event():
    return {
        "client_id": "client-123",
        "contract_id": "contract-456",
        "signed_at": datetime.now().isoformat(),
        "client_name": "John Doe",
        "client_email": "john@example.com",
        "project_type": "web_app"
    }

@pytest.fixture
def mock_deformity_client():
    # Mock DeformityClient
    pass

@pytest.fixture
def mock_calcom_client():
    # Mock CalComClient
    pass

@pytest.fixture
def mock_onboarding_progress():
    # Mock database record
    pass
```

---

## Monitoring & Observability

### Metrics to Track

1. **Onboarding Duration**
   - Average time to complete onboarding
   - Breakdown by step
   - Target: <7 days

2. **Step Completion Rates**
   - % clients completing intake form
   - % clients attending kickoff
   - Bottleneck identification

3. **Stuck Onboardings**
   - Count of ONBOARDING_STUCK states
   - Stuck reasons breakdown
   - Escalation frequency

4. **API Health**
   - Deformity API uptime
   - Cal.com API uptime
   - Error rates by integration

### Logging Standards

```python
# Log all key events with structured data
self.logger.info(
    "Onboarding step completed",
    extra={
        "client_id": client_id,
        "step": "form_sent",
        "duration_ms": 1234,
        "form_id": form_id
    }
)
```

### Alerts

1. **Critical Alerts (Slack/Telegram)**
   - Onboarding stuck >10 days
   - API down after 3 retries
   - Database write failures

2. **Warning Alerts (Email)**
   - Form not completed in 5 days
   - Kickoff not scheduled in 7 days
   - Setup handoff timeout

---

## Dependencies & Environment

### Python Dependencies

```toml
# Add to app/backend/pyproject.toml

[project.dependencies]
# Already included:
# fastapi, sqlalchemy, celery, redis, httpx, pydantic

# No new dependencies required
```

### Environment Variables

```bash
# Add to .env.example

# Deformity API (intake forms)
DEFORMITY_API_KEY=...
DEFORMITY_WEBHOOK_SECRET=...

# Cal.com API (already exists)
CAL_COM_API_KEY=cal_...
CALCOM_WEBHOOK_SECRET=...
CAL_COM_EVENT_TYPE_ID=123456  # Kickoff call event type

# Email configuration (if not using existing)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=hello@smarterteam.ai
```

---

## Migration Plan

### Phase 1: Database Setup (Day 1)

1. Create migration file: `specs/database-schema/migrations/004_onboarding_tables.sql`
2. Run migration: `make migrate`
3. Verify tables created: `onboarding_progress`, `onboarding_steps`, `intake_responses`, `onboarding_events`

### Phase 2: Integration Clients (Day 2)

1. Implement `DeformityClient` in `app/backend/src/integrations/deformity.py`
2. Implement `CalComClient` in `app/backend/src/integrations/calcom.py`
3. Write unit tests for both clients (>90% coverage)

### Phase 3: Agent Implementation (Day 3-4)

1. Create `app/backend/src/agents/onboarding_orchestrator/`
2. Implement `OnboardingOrchestratorAgent` extending `BaseAgent`
3. Implement all 7 tools
4. Write unit tests (>85% coverage)

### Phase 4: Webhooks & Tasks (Day 5)

1. Implement webhook handlers in `app/backend/src/webhooks/onboarding.py`
2. Create Celery tasks in `app/backend/src/tasks/onboarding_tasks.py`
3. Configure webhook routes in FastAPI

### Phase 5: Integration Testing (Day 6)

1. Write integration tests for full onboarding flow
2. Test with mock clients and integrations
3. Test error scenarios and retries

### Phase 6: Production Readiness (Day 7)

1. Add monitoring and alerting
2. Configure Celery beat schedule for stuck detection
3. Deploy to staging environment
4. Run smoke tests

---

## Success Criteria

✅ **Functional Requirements:**
- [ ] Contract signed event triggers onboarding
- [ ] Welcome email and intake form sent automatically
- [ ] Form completion triggers internal setup handoff
- [ ] Kickoff call scheduled within 7 days
- [ ] State transitions work correctly
- [ ] Stuck detection alerts after 7 days

✅ **Quality Requirements:**
- [ ] >85% test coverage
- [ ] All tests passing (unit + integration)
- [ ] No linting errors (Ruff)
- [ ] No type errors (MyPy)
- [ ] All database migrations applied

✅ **Performance Requirements:**
- [ ] Webhook responses <5 seconds
- [ ] Email sent within 1 minute of trigger
- [ ] Form creation <10 seconds
- [ ] Kickoff scheduling <15 seconds

✅ **Reliability Requirements:**
- [ ] Retries work for API failures
- [ ] Circuit breaker prevents cascading failures
- [ ] Database transactions rollback on error
- [ ] No data loss on failures

---

## Open Questions

1. **Email Service:** Use existing SMTP config or integrate with SendGrid/Postmark?
   - **Recommendation:** Start with SMTP, migrate to SendGrid if volume grows

2. **Deformity Alternative:** Deformity API may not exist - use Typeform/Google Forms?
   - **Recommendation:** Use Typeform API (better documented)

3. **Kickoff Call Recording:** Integrate with Fathom for automatic transcripts?
   - **Recommendation:** Phase 2 feature

4. **Access Credentials:** How to securely store client-provided credentials?
   - **Recommendation:** Encrypt in database, store in 1Password vault

5. **Multi-Project Clients:** Can one client have multiple concurrent onboardings?
   - **Recommendation:** Yes, use `(client_id, project_id)` composite key

---

## Related Specifications

- **Onboarding Stuck Detector Agent:** `specs/agents/onboarding-stuck-detector.md` (to be created)
- **Internal Setup Agent:** `specs/agents/onboarding-internal-setup.md` (to be created)
- **Payment Processing Agent:** `specs/agents/payment-processing.md` (to be created)
- **Database Schema:** `specs/database-schema/migrations/004_onboarding_tables.sql` (to be created)

---

**Specification Status:** ✅ Ready for Implementation

**Estimated Implementation Time:** 5-7 days (1 developer)

**Blocking Dependencies:** None (all integrations have fallbacks)

**Next Steps:**
1. Review and approve specification
2. Create task file: `tasks/backend/pending/019-implement-onboarding-orchestrator-agent.md`
3. Create database migration file
4. Begin Phase 1 implementation
