# Delivery Approval Workflow Agent - Technical Specification

**Status:** Production-Ready
**Version:** 1.0.0
**Created:** 2025-12-05
**Category:** Project Delivery
**Phase:** Phase 4 - Client Delivery

---

## 1. Overview

### Purpose
Manage the complete client approval workflow for project deliverables, from submission to final sign-off. Handles review requests, revision cycles, approval tracking, and triggers subsequent project phases.

### Agent Classification
- **Type:** Workflow Management Agent
- **Execution Mode:** Event-driven (webhooks + scheduled tasks)
- **Human-in-the-Loop:** Required for revision implementation and deliverable preparation
- **Priority:** High (critical path for project completion)

### Dependencies
- **Upstream Agents:**
  - Project Management Agent (provides deliverable status, completion signals)
  - Delivery Agent (provides prepared deliverables)
- **Downstream Agents:**
  - Invoice Generation Agent (triggered on final approval)
  - Project Management Agent (updates project status)
- **External Services:**
  - Email service (Gmail/SendGrid for client communications)
  - Google Drive API (deliverable link generation and permissions)
  - ClickUp API (task status updates)

---

## 2. System Prompt

```
You are the Delivery Approval Workflow Agent for Smarter Team, an AI agency automation system.

Your responsibilities:
- Manage the end-to-end approval workflow for all client deliverables
- Send professional review requests with clear deliverable access
- Track client review status and response times
- Handle revision requests within contract limits
- Generate approval confirmations and trigger next steps
- Maintain audit trail of all approval activities

Workflow States You Manage:
1. DELIVERABLE_READY → Receive prepared deliverable from delivery team
2. REVIEW_REQUESTED → Send review request to client with access links
3. PENDING_REVIEW → Track email opens, clicks, and response times
4. REVISION_REQUESTED → Process client feedback, check limits
5. REVISION_IN_PROGRESS → Notify delivery team, track revision progress
6. RESUBMITTED → Send revised deliverable for re-review
7. APPROVED → Confirm approval, update project status, trigger invoicing
8. EXPIRED → Handle non-response, escalate if needed

Key Principles:
- ALWAYS provide clear, professional communication
- STRICTLY enforce revision limits from contract terms
- MAINTAIN complete audit trail of all approvals and revisions
- ESCALATE when revision limits are exceeded or clients don't respond
- TRACK all metrics: response times, revision cycles, approval rates
- RESPECT client preferences for communication channels

You have access to these tools:
- submit_deliverable: Register new deliverable for approval
- send_review_request: Email client with review link and checklist
- track_review_status: Monitor email opens, clicks, and response times
- process_revision_request: Handle client feedback, validate against limits
- request_revision_implementation: Notify delivery team of needed changes
- confirm_approval: Mark deliverable as approved, trigger next steps
- handle_timeout: Manage expired review periods
- update_deliverable_status: Track status changes in all systems
- generate_approval_report: Create summary of approval process

Error Handling:
- If email fails → Queue for retry, log with tracking ID
- If Google Drive link fails → Regenerate with fallback sharing method
- If ClickUp API fails → Local status tracking, sync when available
- If revision limit exceeded → Escalate to project manager, suggest change order
- If client doesn't respond → Send follow-ups, escalate after timeout

Always structure responses as JSON with:
{
  "status": "success|pending|error|escalated",
  "approval_request_id": "uuid",
  "current_state": "REVIEW_REQUESTED|PENDING_REVIEW|APPROVED|REVISION_REQUESTED",
  "actions_taken": ["sent_review_request", "updated_clickup_task"],
  "next_steps": ["await_client_response", "schedule_followup"],
  "deadlines": {"review_due": "2025-01-22T17:00:00Z"},
  "metrics": {"response_time_hours": 48, "revision_count": 1},
  "errors": []
}
```

---

## 3. Agent Architecture

### Class Definition

```python
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Literal
from enum import Enum

from src.agents.base_agent import BaseAgent
from src.integrations.email_client import EmailClient
from src.integrations.google_drive_client import GoogleDriveClient
from src.integrations.clickup_client import ClickUpClient
from src.config import get_agent_logger


class ApprovalState(Enum):
    """Deliverable approval states."""
    DELIVERABLE_READY = "deliverable_ready"
    REVIEW_REQUESTED = "review_requested"
    PENDING_REVIEW = "pending_review"
    REVISION_REQUESTED = "revision_requested"
    REVISION_IN_PROGRESS = "revision_in_progress"
    RESUBMITTED = "resubmitted"
    APPROVED = "approved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class DeliveryApprovalWorkflowAgent(BaseAgent):
    """
    Manages client approval workflow for deliverables.

    Handles review requests, revision cycles, approval tracking,
    and integrates with external systems for communication.
    """

    def __init__(self):
        super().__init__(
            name="delivery_approval_workflow",
            description="Manage client approval workflow for deliverables"
        )

        # Configuration
        self.default_review_period_days = 5
        self.max_revision_days = 14
        self.follow_up_interval_days = 2
        self.max_followups = 3

        # Integration clients (lazy loaded)
        self._email_client: EmailClient | None = None
        self._drive_client: GoogleDriveClient | None = None
        self._clickup_client: ClickUpClient | None = None

        # Register tools
        self._register_tools()

    @property
    def system_prompt(self) -> str:
        """Return system prompt from section 2."""
        return """[System prompt from section 2 above]"""

    @property
    def email_client(self) -> EmailClient:
        """Lazy load email client."""
        if self._email_client is None:
            from src.config import settings
            self._email_client = EmailClient(
                provider=settings.email_provider,
                api_key=settings.email_api_key
            )
        return self._email_client

    @property
    def drive_client(self) -> GoogleDriveClient:
        """Lazy load Google Drive client."""
        if self._drive_client is None:
            from src.config import settings
            self._drive_client = GoogleDriveClient(
                credentials=settings.google_credentials_json
            )
        return self._drive_client

    @property
    def clickup_client(self) -> ClickUpClient:
        """Lazy load ClickUp client."""
        if self._clickup_client is None:
            from src.config import settings
            self._clickup_client = ClickUpClient(
                api_token=settings.clickup_api_token
            )
        return self._clickup_client

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process approval workflow task.

        Args:
            task: {
                "action": "submit_deliverable|send_review|process_revision|confirm_approval",
                "deliverable_id": "uuid",
                "project_id": "uuid",
                "client_id": "uuid",
                "contract_id": "uuid",
                "deliverable_data": {
                    "name": "string",
                    "description": "string",
                    "drive_file_id": "string",
                    "review_checklist": ["string"],
                    "clickup_task_id": "string"
                },
                "revision_data": {  # Only for revision requests
                    "feedback": "string",
                    "requested_changes": ["string"],
                    "deadline": "2025-01-22T17:00:00Z"
                }
            }

        Returns:
            Workflow processing result with status and details
        """
        action = task.get("action")
        deliverable_id = task.get("deliverable_id")

        self.logger.info(
            f"Processing {action} for deliverable {deliverable_id}",
            extra={"project_id": task.get("project_id"), "client_id": task.get("client_id")}
        )

        try:
            if action == "submit_deliverable":
                return await self._handle_deliverable_submission(task)
            elif action == "send_review":
                return await self._handle_review_request(task)
            elif action == "process_revision":
                return await self._handle_revision_request(task)
            elif action == "confirm_approval":
                return await self._handle_approval_confirmation(task)
            elif action == "check_timeouts":
                return await self._handle_timeout_checks()
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            self.logger.error(
                f"Task processing failed: {e}",
                extra={"action": action, "deliverable_id": deliverable_id},
                exc_info=True
            )
            return {
                "status": "error",
                "error": "processing_failed",
                "message": str(e),
                "deliverable_id": deliverable_id
            }

    def _register_tools(self) -> None:
        """Register all tools available to this agent."""
        # Tools will be defined in section 4
        pass
```

---

## 4. Tool Definitions

### 4.1 submit_deliverable

**Purpose:** Register new deliverable for approval workflow

```python
async def submit_deliverable(
    self,
    deliverable_id: str,
    project_id: str,
    client_id: str,
    contract_id: str,
    deliverable_name: str,
    description: str,
    drive_file_id: str,
    review_checklist: list[str],
    clickup_task_id: str | None = None,
) -> dict[str, Any]:
    """
    Submit deliverable for approval workflow.

    Args:
        deliverable_id: Unique identifier for the deliverable
        project_id: Project UUID
        client_id: Client UUID
        contract_id: Contract UUID for revision limits
        deliverable_name: Human-readable name
        description: Detailed description of deliverable
        drive_file_id: Google Drive file ID
        review_checklist: Items for client to review
        clickup_task_id: Optional ClickUp task for updates

    Returns:
        {
            "status": "success",
            "approval_request_id": "uuid",
            "state": "deliverable_ready",
            "next_action": "send_review_request"
        }
    """
    # Create approval request record
    approval_request = await self._create_approval_request({
        "deliverable_id": deliverable_id,
        "project_id": project_id,
        "client_id": client_id,
        "contract_id": contract_id,
        "deliverable_name": deliverable_name,
        "description": description,
        "drive_file_id": drive_file_id,
        "review_checklist": review_checklist,
        "clickup_task_id": clickup_task_id,
        "state": ApprovalState.DELIVERABLE_READY.value,
        "created_by": "delivery_approval_workflow_agent"
    })

    self.log_action(
        "deliverable.submitted",
        {
            "deliverable_id": deliverable_id,
            "project_id": project_id,
            "approval_request_id": approval_request["id"]
        }
    )

    # Auto-trigger review request
    await self.handoff_to(
        target_agent="delivery_approval_workflow",
        payload={
            "action": "send_review",
            "deliverable_id": deliverable_id,
            "project_id": project_id,
            "client_id": client_id,
            "approval_request_id": approval_request["id"]
        },
        priority=Priority.NORMAL.value
    )

    return {
        "status": "success",
        "approval_request_id": approval_request["id"],
        "state": ApprovalState.DELIVERABLE_READY.value,
        "next_action": "send_review_request"
    }
```

### 4.2 send_review_request

**Purpose:** Send professional review request to client

```python
async def send_review_request(
    self,
    approval_request_id: str,
) -> dict[str, Any]:
    """
    Send review request email to client with deliverable access.

    Args:
        approval_request_id: Approval request UUID

    Returns:
        {
            "status": "success",
            "email_sent": true,
            "review_link": "https://drive.google.com/...",
            "due_date": "2025-01-22T17:00:00Z",
            "message_id": "email_message_id"
        }
    """
    # Get approval request details
    approval_request = await self._get_approval_request(approval_request_id)
    if not approval_request:
        raise ValueError(f"Approval request {approval_request_id} not found")

    # Get client and project details
    client = await self._get_client(approval_request["client_id"])
    project = await self._get_project(approval_request["project_id"])
    contract = await self._get_contract(approval_request["contract_id"])

    # Generate secure Google Drive link
    drive_link = await self._create_shareable_drive_link(
        file_id=approval_request["drive_file_id"],
        client_email=client["email"],
        expires_days=self.default_review_period_days
    )

    # Calculate due date
    due_date = datetime.utcnow() + timedelta(days=self.default_review_period_days)

    # Compose review request email
    email_body = await self._compose_review_email(
        client_name=client["name"],
        deliverable_name=approval_request["deliverable_name"],
        project_name=project["name"],
        drive_link=drive_link,
        review_checklist=approval_request["review_checklist"],
        due_date=due_date,
        revisions_remaining=int(contract.get("max_revisions", 3)),
        max_revisions=int(contract.get("max_revisions", 3))
    )

    # Send email
    email_result = await self.email_client.send_email(
        to=client["email"],
        subject=f"Ready for your review: {approval_request['deliverable_name']}",
        html_body=email_body,
        metadata={
            "approval_request_id": approval_request_id,
            "type": "review_request",
            "project_id": approval_request["project_id"]
        }
    )

    # Update approval request status
    await self._update_approval_request(
        approval_request_id,
        {
            "state": ApprovalState.REVIEW_REQUESTED.value,
            "review_sent_at": datetime.utcnow().isoformat(),
            "review_due_at": due_date.isoformat(),
            "drive_link": drive_link,
            "email_message_id": email_result["message_id"],
            "followups_sent": 0
        }
    )

    # Update ClickUp task if available
    if approval_request.get("clickup_task_id"):
        await self._update_clickup_task(
            task_id=approval_request["clickup_task_id"],
            status="Waiting for Client",
            description=f"Review request sent to {client['email']}. Due: {due_date.strftime('%Y-%m-%d')}"
        )

    # Schedule follow-up reminders
    await self._schedule_follow_ups(approval_request_id, due_date)

    self.log_action(
        "review_request.sent",
        {
            "approval_request_id": approval_request_id,
            "client_email": client["email"],
            "due_date": due_date.isoformat(),
            "drive_link": drive_link
        }
    )

    return {
        "status": "success",
        "email_sent": True,
        "review_link": drive_link,
        "due_date": due_date.isoformat(),
        "message_id": email_result["message_id"]
    }
```

### 4.3 track_review_status

**Purpose:** Monitor client engagement with review request

```python
async def track_review_status(
    self,
    approval_request_id: str,
) -> dict[str, Any]:
    """
    Track review status based on email engagement.

    Args:
        approval_request_id: Approval request UUID

    Returns:
        {
            "status": "pending_review",
            "email_opened": true,
            "link_clicked": true,
            "last_activity": "2025-01-18T14:30:00Z",
            "response_time_hours": 24.5
        }
    """
    # Get approval request
    approval_request = await self._get_approval_request(approval_request_id)

    # Track email engagement
    email_stats = await self.email_client.get_email_stats(
        message_id=approval_request["email_message_id"]
    )

    # Track Google Drive access
    drive_stats = await self.drive_client.get_file_access_stats(
        file_id=approval_request["drive_file_id"],
        since=approval_request["review_sent_at"]
    )

    # Calculate response time
    response_time = None
    if email_stats.get("first_open"):
        sent_time = datetime.fromisoformat(approval_request["review_sent_at"])
        open_time = datetime.fromisoformat(email_stats["first_open"])
        response_time = (open_time - sent_time).total_seconds() / 3600

    # Update tracking data
    await self._update_approval_request(
        approval_request_id,
        {
            "email_opened_at": email_stats.get("first_open"),
            "email_open_count": email_stats.get("open_count", 0),
            "link_clicked_at": drive_stats.get("first_access"),
            "link_access_count": drive_stats.get("access_count", 0),
            "last_activity_at": max(
                email_stats.get("last_open"),
                drive_stats.get("last_access")
            )
        }
    )

    # Determine if follow-up is needed
    due_date = datetime.fromisoformat(approval_request["review_due_at"])
    now = datetime.utcnow()
    days_since_sent = (now - datetime.fromisoformat(approval_request["review_sent_at"])).days

    needs_followup = (
        days_since_sent >= self.follow_up_interval_days and
        approval_request.get("followups_sent", 0) < self.max_followups and
        not approval_request.get("client_responded", False)
    )

    if needs_followup:
        await self.handoff_to(
            target_agent="delivery_approval_workflow",
            payload={
                "action": "send_followup",
                "approval_request_id": approval_request_id
            },
            priority=Priority.NORMAL.value
        )

    return {
        "status": "pending_review",
        "email_opened": email_stats.get("open_count", 0) > 0,
        "link_clicked": drive_stats.get("access_count", 0) > 0,
        "last_activity": approval_request.get("last_activity_at"),
        "response_time_hours": response_time,
        "days_since_sent": days_since_sent,
        "needs_followup": needs_followup
    }
```

### 4.4 process_revision_request

**Purpose:** Handle client revision requests and validate limits

```python
async def process_revision_request(
    self,
    approval_request_id: str,
    feedback: str,
    requested_changes: list[str],
    deadline_override: str | None = None,
) -> dict[str, Any]:
    """
    Process client revision request.

    Args:
        approval_request_id: Approval request UUID
        feedback: Client's feedback message
        requested_changes: List of specific changes needed
        deadline_override: Optional new deadline for revisions

    Returns:
        {
            "status": "revision_requested" | "revision_limit_exceeded",
            "revisions_remaining": 2,
            "revision_number": 1,
            "estimated_completion": "2025-01-25T17:00:00Z",
            "change_order_required": false
        }
    """
    # Get approval request and contract
    approval_request = await self._get_approval_request(approval_request_id)
    contract = await self._get_contract(approval_request["contract_id"])

    # Check revision limits
    current_revisions = await self._count_revisions(approval_request_id)
    max_revisions = int(contract.get("max_revisions", 3))
    revisions_remaining = max_revisions - current_revisions

    if revisions_remaining <= 0:
        # Revision limit exceeded - escalate for change order
        await self._handle_revision_limit_exceeded(
            approval_request_id,
            feedback,
            requested_changes
        )

        return {
            "status": "revision_limit_exceeded",
            "revisions_remaining": 0,
            "revision_number": current_revisions,
            "change_order_required": True,
            "escalation_sent": True
        }

    # Create revision request record
    revision_request = await self._create_revision_request({
        "approval_request_id": approval_request_id,
        "revision_number": current_revisions + 1,
        "feedback": feedback,
        "requested_changes": requested_changes,
        "status": "pending",
        "created_by": "client"
    })

    # Calculate revision deadline
    revision_deadline = (
        datetime.fromisoformat(deadline_override) if deadline_override
        else datetime.utcnow() + timedelta(days=self.max_revision_days)
    )

    # Update approval request
    await self._update_approval_request(
        approval_request_id,
        {
            "state": ApprovalState.REVISION_REQUESTED.value,
            "current_revision_number": current_revisions + 1,
            "revisions_remaining": revisions_remaining - 1,
            "revision_deadline": revision_deadline.isoformat()
        }
    )

    # Notify delivery team
    await self._notify_delivery_team({
        "approval_request_id": approval_request_id,
        "deliverable_name": approval_request["deliverable_name"],
        "project_id": approval_request["project_id"],
        "revision_number": current_revisions + 1,
        "feedback": feedback,
        "requested_changes": requested_changes,
        "deadline": revision_deadline.isoformat(),
        "revisions_remaining": revisions_remaining - 1
    })

    # Update ClickUp task
    if approval_request.get("clickup_task_id"):
        await self._update_clickup_task(
            task_id=approval_request["clickup_task_id"],
            status="Revisions Requested",
            description=f"Revision #{current_revisions + 1} requested. Due: {revision_deadline.strftime('%Y-%m-%d')}"
        )

    self.log_action(
        "revision.requested",
        {
            "approval_request_id": approval_request_id,
            "revision_number": current_revisions + 1,
            "revisions_remaining": revisions_remaining - 1,
            "change_count": len(requested_changes)
        }
    )

    return {
        "status": "revision_requested",
        "revisions_remaining": revisions_remaining - 1,
        "revision_number": current_revisions + 1,
        "estimated_completion": revision_deadline.isoformat(),
        "change_order_required": False,
        "revision_request_id": revision_request["id"]
    }
```

### 4.5 confirm_approval

**Purpose:** Mark deliverable as approved and trigger next steps

```python
async def confirm_approval(
    self,
    approval_request_id: str,
    approver_email: str,
    approval_notes: str | None = None,
) -> dict[str, Any]:
    """
    Confirm client approval and complete workflow.

    Args:
        approval_request_id: Approval request UUID
        approver_email: Email of person who approved
        approval_notes: Optional notes from approver

    Returns:
        {
            "status": "approved",
            "approved_at": "2025-01-20T10:30:00Z",
            "total_revision_cycles": 2,
            "next_steps": ["invoice_generation", "project_update"],
            "invoice_triggered": true
        }
    """
    # Get approval request
    approval_request = await self._get_approval_request(approval_request_id)

    # Create approval record
    approval = await self._create_approval({
        "approval_request_id": approval_request_id,
        "approver_email": approver_email,
        "approved_at": datetime.utcnow().isoformat(),
        "approval_notes": approval_notes,
        "total_revision_cycles": approval_request.get("current_revision_number", 0),
        "approval_method": "email"
    })

    # Update approval request
    await self._update_approval_request(
        approval_request_id,
        {
            "state": ApprovalState.APPROVED.value,
            "approved_at": datetime.utcnow().isoformat(),
            "approver_email": approver_email,
            "approval_notes": approval_notes
        }
    )

    # Send approval confirmation email
    await self._send_approval_confirmation(
        approval_request_id,
        approver_email,
        approval_notes
    )

    # Update ClickUp task
    if approval_request.get("clickup_task_id"):
        await self._update_clickup_task(
            task_id=approval_request["clickup_task_id"],
            status="Approved",
            description=f"Approved by {approver_email} on {datetime.utcnow().strftime('%Y-%m-%d')}"
        )

    # Check if this is final deliverable
    project = await self._get_project(approval_request["project_id"])
    is_final_deliverable = await self._is_final_deliverable(
        approval_request["deliverable_id"],
        approval_request["project_id"]
    )

    # Trigger invoice generation
    await self.handoff_to(
        target_agent="invoice_generation",
        payload={
            "type": "milestone" if not is_final_deliverable else "final",
            "contract_id": approval_request["contract_id"],
            "project_id": approval_request["project_id"],
            "client_id": approval_request["client_id"],
            "deliverable_id": approval_request["deliverable_id"],
            "milestone_id": approval_request.get("milestone_id"),
            "approval_id": approval["id"]
        },
        priority=Priority.HIGH.value
    )

    # Update project status if final deliverable
    if is_final_deliverable:
        await self.handoff_to(
            target_agent="project_management",
            payload={
                "action": "complete_project",
                "project_id": approval_request["project_id"],
                "completion_reason": "final_deliverable_approved"
            },
            priority=Priority.HIGH.value
        )

    # Generate approval report
    report = await self._generate_approval_report(approval_request_id)

    self.log_action(
        "deliverable.approved",
        {
            "approval_request_id": approval_request_id,
            "approver_email": approver_email,
            "revision_cycles": approval_request.get("current_revision_number", 0),
            "is_final_deliverable": is_final_deliverable,
            "approval_id": approval["id"]
        }
    )

    return {
        "status": "approved",
        "approved_at": approval["approved_at"],
        "total_revision_cycles": approval_request.get("current_revision_number", 0),
        "next_steps": (
            ["invoice_generation", "project_completion"]
            if is_final_deliverable
            else ["invoice_generation", "next_phase"]
        ),
        "invoice_triggered": True,
        "project_updated": is_final_deliverable,
        "approval_report": report
    }
```

### 4.6 handle_timeout

**Purpose:** Manage expired review periods and client non-response

```python
async def handle_timeout(
    self,
    approval_request_id: str,
    escalation_level: int = 1,
) -> dict[str, Any]:
    """
    Handle expired review period with escalation.

    Args:
        approval_request_id: Approval request UUID
        escalation_level: Current escalation level (1-3)

    Returns:
        {
            "status": "escalated" | "auto_approved" | "extended",
            "escalation_level": 2,
            "new_due_date": "2025-01-27T17:00:00Z",
            "project_manager_notified": true
        }
    """
    # Get approval request and client
    approval_request = await self._get_approval_request(approval_request_id)
    client = await self._get_client(approval_request["client_id"])
    project = await self._get_project(approval_request["project_id"])

    due_date = datetime.fromisoformat(approval_request["review_due_at"])
    days_overdue = (datetime.utcnow() - due_date).days

    if escalation_level == 1:
        # First escalation: Send follow-up email
        await self._send_timeout_followup(
            approval_request_id,
            client,
            days_overdue
        )

        # Extend deadline by 3 days
        new_due_date = datetime.utcnow() + timedelta(days=3)

        await self._update_approval_request(
            approval_request_id,
            {
                "review_due_at": new_due_date.isoformat(),
                "escalation_level": escalation_level,
                "last_escalation_at": datetime.utcnow().isoformat()
            }
        )

        return {
            "status": "extended",
            "escalation_level": escalation_level,
            "new_due_date": new_due_date.isoformat(),
            "followup_sent": True
        }

    elif escalation_level == 2:
        # Second escalation: Notify project manager
        pm = await self._get_project_manager(approval_request["project_id"])

        await self._notify_project_manager({
            "type": "client_non_response",
            "approval_request_id": approval_request_id,
            "project_name": project["name"],
            "client_name": client["name"],
            "days_overdue": days_overdue,
            "deliverable": approval_request["deliverable_name"]
        })

        # Final extension of 2 days
        new_due_date = datetime.utcnow() + timedelta(days=2)

        await self._update_approval_request(
            approval_request_id,
            {
                "review_due_at": new_due_date.isoformat(),
                "escalation_level": escalation_level,
                "pm_notified": True,
                "last_escalation_at": datetime.utcnow().isoformat()
            }
        )

        return {
            "status": "escalated",
            "escalation_level": escalation_level,
            "new_due_date": new_due_date.isoformat(),
            "project_manager_notified": True
        }

    else:
        # Final escalation: Auto-approve with notice
        await self._auto_approve_deliverable(
            approval_request_id,
            reason="client_non_response",
            days_overdue=days_overdue
        )

        return {
            "status": "auto_approved",
            "escalation_level": escalation_level,
            "auto_approve_reason": "client_non_response",
            "days_overdue": days_overdue
        }
```

---

## 5. Database Schema

### 5.1 approval_requests Table

```sql
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    deliverable_id UUID NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id),
    client_id UUID NOT NULL REFERENCES clients(id),
    contract_id UUID NOT NULL REFERENCES contracts(id),
    milestone_id UUID REFERENCES milestones(id),  -- Optional

    -- Deliverable details
    deliverable_name VARCHAR(255) NOT NULL,
    description TEXT,
    drive_file_id VARCHAR(255) NOT NULL,
    drive_link TEXT,
    review_checklist TEXT[],  -- PostgreSQL array

    -- State tracking
    state VARCHAR(50) NOT NULL DEFAULT 'deliverable_ready',
    current_revision_number INTEGER DEFAULT 0,
    revisions_remaining INTEGER DEFAULT 3,

    -- Dates
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    review_sent_at TIMESTAMP WITH TIME ZONE,
    review_due_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    revision_deadline TIMESTAMP WITH TIME ZONE,

    -- Email tracking
    email_message_id VARCHAR(255),
    email_opened_at TIMESTAMP WITH TIME ZONE,
    email_open_count INTEGER DEFAULT 0,
    link_clicked_at TIMESTAMP WITH TIME ZONE,
    link_access_count INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP WITH TIME ZONE,

    -- Escalation
    escalation_level INTEGER DEFAULT 0,
    pm_notified BOOLEAN DEFAULT FALSE,
    auto_approved BOOLEAN DEFAULT FALSE,
    last_escalation_at TIMESTAMP WITH TIME ZONE,
    followups_sent INTEGER DEFAULT 0,

    -- Approval details
    approver_email VARCHAR(255),
    approval_notes TEXT,

    -- ClickUp integration
    clickup_task_id VARCHAR(255),

    -- Metadata
    created_by VARCHAR(100) DEFAULT 'delivery_approval_workflow_agent',
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_state CHECK (state IN (
        'deliverable_ready', 'review_requested', 'pending_review',
        'revision_requested', 'revision_in_progress', 'resubmitted',
        'approved', 'expired', 'cancelled'
    )),
    CONSTRAINT valid_revision_number CHECK (current_revision_number >= 0),
    CONSTRAINT valid_revisions_remaining CHECK (revisions_remaining >= 0),
    CONSTRAINT valid_escalation_level CHECK (escalation_level >= 0 AND escalation_level <= 3)
);

-- Indexes
CREATE INDEX idx_approval_requests_deliverable_id ON approval_requests(deliverable_id);
CREATE INDEX idx_approval_requests_project_id ON approval_requests(project_id);
CREATE INDEX idx_approval_requests_client_id ON approval_requests(client_id);
CREATE INDEX idx_approval_requests_state ON approval_requests(state);
CREATE INDEX idx_approval_requests_review_due ON approval_requests(review_due_at);
CREATE INDEX idx_approval_requests_created_at ON approval_requests(created_at);
```

### 5.2 revision_requests Table

```sql
CREATE TABLE revision_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    approval_request_id UUID NOT NULL REFERENCES approval_requests(id),

    -- Revision details
    revision_number INTEGER NOT NULL,
    feedback TEXT NOT NULL,
    requested_changes TEXT[],  -- PostgreSQL array
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed

    -- Dates
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_at TIMESTAMP WITH TIME ZONE,

    -- Implementation details
    implemented_by VARCHAR(100),  -- Team member who implemented
    implementation_notes TEXT,

    -- Metadata
    created_by VARCHAR(100) DEFAULT 'client',
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_revision_status CHECK (status IN ('pending', 'in_progress', 'completed')),
    CONSTRAINT unique_revision_per_request UNIQUE (approval_request_id, revision_number)
);

-- Indexes
CREATE INDEX idx_revision_requests_approval_request_id ON revision_requests(approval_request_id);
CREATE INDEX idx_revision_requests_status ON revision_requests(status);
CREATE INDEX idx_revision_requests_due_at ON revision_requests(due_at);
```

### 5.3 approvals Table

```sql
CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    approval_request_id UUID NOT NULL REFERENCES approval_requests(id),

    -- Approval details
    approver_email VARCHAR(255) NOT NULL,
    approved_at TIMESTAMP WITH TIME ZONE NOT NULL,
    approval_method VARCHAR(50) DEFAULT 'email',  -- email, portal, verbal
    approval_notes TEXT,
    total_revision_cycles INTEGER DEFAULT 0,

    -- Delivery confirmation
    deliverable_final_link TEXT,
    delivered_to_client_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_approval_method CHECK (approval_method IN ('email', 'portal', 'verbal', 'auto'))
);

-- Indexes
CREATE INDEX idx_approvals_approval_request_id ON approvals(approval_request_id);
CREATE INDEX idx_approvals_approved_at ON approvals(approved_at);
CREATE INDEX idx_approvals_approver_email ON approvals(approver_email);
```

### 5.4 approval_events Table

```sql
CREATE TABLE approval_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    approval_request_id UUID NOT NULL REFERENCES approval_requests(id),

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(50) DEFAULT 'agent',  -- agent, client, system, pm
    description TEXT,

    -- Event data
    event_data JSONB DEFAULT '{}'::jsonb,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_approval_events_approval_request_id ON approval_events(approval_request_id);
CREATE INDEX idx_approval_events_type ON approval_events(event_type);
CREATE INDEX idx_approval_events_created_at ON approval_events(created_at);
```

---

## 6. Error Handling & Edge Cases

### 6.1 Error Scenarios

| Error | Detection | Handling | Recovery |
|-------|-----------|----------|----------|
| Email send failure | SMTP/API error | Queue for retry | Retry 3x with backoff |
| Google Drive permission error | API 403 | Regenerate link | Use different sharing method |
| ClickUp API unavailable | HTTP 5xx | Local tracking | Sync when available |
| Revision limit exceeded | Count > contract max | Escalate to PM | Change order required |
| Client email bounces | Delivery failure | Notify PM | Update contact info |
| Duplicate approval request | Unique constraint | Return existing | Skip creation |
| File not in Drive | API 404 | Notify delivery team | Request new file |
| Invalid contract terms | Validation error | Use defaults | Escalate for review |

### 6.2 Retry Logic

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def send_email_with_retry(self, to: str, subject: str, body: str):
    """Retry email sending on transient failures."""
    return await self.email_client.send_email(to=to, subject=subject, html_body=body)

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
)
async def update_clickup_with_retry(self, task_id: str, updates: dict):
    """Retry ClickUp updates on transient failures."""
    return await self.clickup_client.update_task(task_id, updates)
```

### 6.3 Edge Cases

1. **Multiple approvers**: Support approval from any authorized contact
2. **Conditional approval**: Approve with minor changes requested
3. **Partial approval**: Approve some deliverables, request revisions on others
4. **Client wants more revisions**: Handle change order process
5. **Deliverable format issues**: Client can't access file
6. **Language barriers**: Non-English feedback
7. **Time zone differences**: Calculate due dates in client timezone
8. **Batch approvals**: Multiple deliverables approved together

---

## 7. Testing Requirements

### 7.1 Unit Tests (Target: >90%)

**File:** `app/backend/__tests__/unit/agents/test_delivery_approval_workflow_agent.py`

```python
"""Unit tests for DeliveryApprovalWorkflowAgent."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.delivery_approval_workflow import (
    DeliveryApprovalWorkflowAgent,
    ApprovalState,
    Priority
)


@pytest.fixture
def agent():
    """Create agent instance."""
    return DeliveryApprovalWorkflowAgent()


@pytest.fixture
def sample_approval_request():
    """Sample approval request data."""
    return {
        "id": "ar-123",
        "deliverable_id": "del-456",
        "project_id": "proj-789",
        "client_id": "client-001",
        "contract_id": "contract-123",
        "deliverable_name": "Website Design",
        "description": "Homepage and landing page designs",
        "drive_file_id": "file-google-drive-id",
        "review_checklist": ["Color scheme", "Typography", "Layout", "Mobile responsiveness"],
        "state": ApprovalState.DELIVERABLE_READY.value,
        "revisions_remaining": 3,
        "current_revision_number": 0
    }


class TestDeliveryApprovalWorkflowAgent:
    """Test suite for DeliveryApprovalWorkflowAgent."""

    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "delivery_approval_workflow"
        assert agent.default_review_period_days == 5
        assert agent.max_revision_days == 14
        assert agent.follow_up_interval_days == 2
        assert agent.max_followups == 3

    async def test_submit_deliverable_success(self, agent, sample_approval_request):
        """Test deliverable submission - success."""
        with patch.object(agent, '_create_approval_request') as mock_create:
            mock_create.return_value = {"id": "ar-123"}

            with patch.object(agent, 'handoff_to') as mock_handoff:
                result = await agent.submit_deliverable(
                    deliverable_id=sample_approval_request["deliverable_id"],
                    project_id=sample_approval_request["project_id"],
                    client_id=sample_approval_request["client_id"],
                    contract_id=sample_approval_request["contract_id"],
                    deliverable_name=sample_approval_request["deliverable_name"],
                    description=sample_approval_request["description"],
                    drive_file_id=sample_approval_request["drive_file_id"],
                    review_checklist=sample_approval_request["review_checklist"]
                )

                assert result["status"] == "success"
                assert result["approval_request_id"] == "ar-123"
                assert result["state"] == ApprovalState.DELIVERABLE_READY.value
                mock_handoff.assert_called_once()

    async def test_send_review_request_success(self, agent, sample_approval_request):
        """Test sending review request - success."""
        with patch.object(agent, '_get_approval_request') as mock_get:
            mock_get.return_value = sample_approval_request

            with patch.object(agent, '_get_client') as mock_client:
                mock_client.return_value = {
                    "id": "client-001",
                    "name": "Test Client",
                    "email": "client@example.com"
                }

                with patch.object(agent, 'email_client') as mock_email:
                    mock_email.send_email = AsyncMock(return_value={
                        "message_id": "email-123"
                    })

                    with patch.object(agent, '_create_shareable_drive_link') as mock_link:
                        mock_link.return_value = "https://drive.google.com/link"

                        result = await agent.send_review_request("ar-123")

                        assert result["status"] == "success"
                        assert result["email_sent"] is True
                        assert result["review_link"] == "https://drive.google.com/link"
                        assert "due_date" in result

    async def test_process_revision_request_within_limit(self, agent, sample_approval_request):
        """Test processing revision request - within limit."""
        with patch.object(agent, '_get_approval_request') as mock_get:
            sample_approval_request["current_revision_number"] = 1
            mock_get.return_value = sample_approval_request

            with patch.object(agent, '_get_contract') as mock_contract:
                mock_contract.return_value = {"max_revisions": 3}

                with patch.object(agent, '_count_revisions') as mock_count:
                    mock_count.return_value = 1

                    with patch.object(agent, '_create_revision_request') as mock_create:
                        mock_create.return_value = {"id": "rev-123"}

                        with patch.object(agent, 'handoff_to') as mock_handoff:
                            result = await agent.process_revision_request(
                                approval_request_id="ar-123",
                                feedback="Please update the colors",
                                requested_changes=["Change header to blue", "Update button styles"]
                            )

                            assert result["status"] == "revision_requested"
                            assert result["revisions_remaining"] == 1
                            assert result["revision_number"] == 2
                            assert result["change_order_required"] is False

    async def test_process_revision_request_limit_exceeded(self, agent, sample_approval_request):
        """Test processing revision request - limit exceeded."""
        with patch.object(agent, '_get_approval_request') as mock_get:
            mock_get.return_value = sample_approval_request

            with patch.object(agent, '_get_contract') as mock_contract:
                mock_contract.return_value = {"max_revisions": 2}

                with patch.object(agent, '_count_revisions') as mock_count:
                    mock_count.return_value = 2

                    with patch.object(agent, '_handle_revision_limit_exceeded') as mock_handle:
                        result = await agent.process_revision_request(
                            approval_request_id="ar-123",
                            feedback="Another revision needed",
                            requested_changes=["More changes"]
                        )

                        assert result["status"] == "revision_limit_exceeded"
                        assert result["revisions_remaining"] == 0
                        assert result["change_order_required"] is True

    async def test_confirm_approval_final_deliverable(self, agent, sample_approval_request):
        """Test confirming approval - final deliverable."""
        with patch.object(agent, '_get_approval_request') as mock_get:
            mock_get.return_value = sample_approval_request

            with patch.object(agent, '_create_approval') as mock_create:
                mock_create.return_value = {"id": "approval-123"}

                with patch.object(agent, '_is_final_deliverable') as mock_final:
                    mock_final.return_value = True

                    with patch.object(agent, 'handoff_to') as mock_handoff:
                        result = await agent.confirm_approval(
                            approval_request_id="ar-123",
                            approver_email="client@example.com",
                            approval_notes="Looks great!"
                        )

                        assert result["status"] == "approved"
                        assert result["project_updated"] is True
                        assert "invoice_generation" in result["next_steps"]
                        assert "project_completion" in result["next_steps"]

    async def test_handle_timeout_first_escalation(self, agent, sample_approval_request):
        """Test handling timeout - first escalation."""
        sample_approval_request["review_due_at"] = (
            datetime.utcnow() - timedelta(days=1)
        ).isoformat()

        with patch.object(agent, '_get_approval_request') as mock_get:
            mock_get.return_value = sample_approval_request

            with patch.object(agent, '_get_client') as mock_client:
                mock_client.return_value = {"name": "Test Client", "email": "client@example.com"}

                with patch.object(agent, '_send_timeout_followup') as mock_followup:
                    with patch.object(agent, '_update_approval_request') as mock_update:
                        result = await agent.handle_timeout("ar-123", escalation_level=1)

                        assert result["status"] == "extended"
                        assert result["escalation_level"] == 1
                        assert "new_due_date" in result
                        assert result["followup_sent"] is True

    async def test_track_review_status_engagement(self, agent, sample_approval_request):
        """Test tracking review status with client engagement."""
        sample_approval_request["email_message_id"] = "email-123"
        sample_approval_request["review_sent_at"] = (
            datetime.utcnow() - timedelta(hours=24)
        ).isoformat()

        with patch.object(agent, '_get_approval_request') as mock_get:
            mock_get.return_value = sample_approval_request

            with patch.object(agent, 'email_client') as mock_email:
                mock_email.get_email_stats = AsyncMock(return_value={
                    "first_open": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
                    "last_open": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "open_count": 3
                })

                with patch.object(agent, 'drive_client') as mock_drive:
                    mock_drive.get_file_access_stats = AsyncMock(return_value={
                        "first_access": (datetime.utcnow() - timedelta(hours=10)).isoformat(),
                        "last_access": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                        "access_count": 2
                    })

                    result = await agent.track_review_status("ar-123")

                    assert result["status"] == "pending_review"
                    assert result["email_opened"] is True
                    assert result["link_clicked"] is True
                    assert result["response_time_hours"] == 12.0
```

### 7.2 Integration Tests

**File:** `app/backend/__tests__/integration/test_delivery_approval_integration.py`

```python
"""Integration tests for delivery approval workflow."""

import pytest
from datetime import datetime, timedelta

from src.agents.delivery_approval_workflow import DeliveryApprovalWorkflowAgent
from src.database import get_async_session
from src.models import ApprovalRequest, RevisionRequest, Approval


@pytest.mark.integration
class TestDeliveryApprovalIntegration:
    """Integration tests with database."""

    async def test_full_approval_workflow_success(self, db_session):
        """Test complete approval workflow from submission to approval."""
        # Setup: Create client, project, contract
        # ... setup code ...

        # Execute: Submit deliverable
        agent = DeliveryApprovalWorkflowAgent()

        # Step 1: Submit deliverable
        submit_result = await agent.submit_deliverable(
            deliverable_id="del-001",
            project_id="proj-001",
            client_id="client-001",
            contract_id="contract-001",
            deliverable_name="Logo Design",
            description="Company logo variations",
            drive_file_id="file-123",
            review_checklist=["Colors", "Typography", "Scalability"]
        )

        assert submit_result["status"] == "success"

        # Step 2: Send review request (mocked email)
        with patch.object(agent, 'email_client') as mock_email:
            mock_email.send_email = AsyncMock(return_value={"message_id": "email-123"})

            review_result = await agent.send_review_request(
                approval_request_id=submit_result["approval_request_id"]
            )

            assert review_result["status"] == "success"

        # Step 3: Confirm approval
        approval_result = await agent.confirm_approval(
            approval_request_id=submit_result["approval_request_id"],
            approver_email="client@example.com",
            approval_notes="Perfect design!"
        )

        assert approval_result["status"] == "approved"

        # Verify: Database records created
        approval_request = await db_session.get(
            ApprovalRequest,
            submit_result["approval_request_id"]
        )
        assert approval_request.state == "approved"

        approval = await db_session.execute(
            select(Approval).where(
                Approval.approval_request_id == submit_result["approval_request_id"]
            )
        )
        assert approval.scalar_one_or_none() is not None

    async def test_revision_cycle_workflow(self, db_session):
        """Test workflow with revision cycle."""
        # Setup: Create approval request
        # ... setup code ...

        # Execute: Request revision
        agent = DeliveryApprovalWorkflowAgent()

        revision_result = await agent.process_revision_request(
            approval_request_id="ar-001",
            feedback="Need color changes",
            requested_changes=["Change blue to green", "Make text darker"]
        )

        assert revision_result["status"] == "revision_requested"
        assert revision_result["revisions_remaining"] == 2

        # Verify: Revision request created
        revision = await db_session.execute(
            select(RevisionRequest).where(
                RevisionRequest.approval_request_id == "ar-001"
            )
        )
        revision_record = revision.scalar_one()
        assert revision_record.feedback == "Need color changes"
        assert len(revision_record.requested_changes) == 2
```

### 7.3 Test Coverage Targets

- **Unit tests:** >90% coverage
- **Integration tests:** >85% coverage
- **Critical paths:** 100% coverage (submission, review, revision, approval)

---

## 8. Performance & Scalability

### 8.1 Optimizations

1. **Batch Processing:**
   - Process multiple review requests in parallel
   - Batch email sends for efficiency
   - Bulk updates to ClickUp tasks

2. **Caching:**
   - Cache client contact information
   - Cache contract terms for revision limits
   - Cache frequently accessed deliverable links

3. **Async Operations:**
   - All I/O operations must be async
   - Parallel email and Drive operations
   - Background processing for non-critical updates

4. **Rate Limiting:**
   - Respect email provider limits
   - Implement ClickUp API rate limiting
   - Queue non-urgent operations

### 8.2 Monitoring

```python
# Prometheus metrics
approval_requests_total = Counter(
    "approval_requests_total",
    "Total approval requests",
    ["state", "project_type"]
)

approval_duration = Histogram(
    "approval_duration_hours",
    "Time from request to approval"
)

revision_cycles = Histogram(
    "revision_cycles_count",
    "Number of revision cycles per deliverable"
)

client_response_time = Histogram(
    "client_response_time_hours",
    "Time to client response"
)
```

---

## 9. Security Considerations

### 9.1 Data Protection

- **Secure Google Drive sharing:** Use expiring links with specific permissions
- **Email encryption:** TLS for all email communications
- **Audit logging:** Complete trail of all approval activities
- **Access control:** Only authorized contacts can approve deliverables

### 9.2 Input Validation

```python
from pydantic import BaseModel, Field, validator

class DeliverableSubmission(BaseModel):
    """Schema for deliverable submission."""
    deliverable_name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=2000)
    drive_file_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    review_checklist: list[str] = Field(..., min_items=1, max_items=20)

    @validator('review_checklist')
    def validate_checklist_items(cls, v):
        """Ensure checklist items are reasonable length."""
        for item in v:
            if len(item) > 200:
                raise ValueError("Checklist item too long")
        return v
```

### 9.3 Permission Management

- **Drive permissions:** Viewer access only, expires after approval
- **ClickUp access:** Limited to specific tasks
- **Email restrictions:** Only send to verified client contacts

---

## 10. Deployment Checklist

- [ ] Database migrations applied (all tables)
- [ ] Google Drive service account configured
- [ ] Email service provider configured
- [ ] ClickUp API token configured
- [ ] Celery tasks registered for follow-ups
- [ ] Webhook handlers for client emails
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing (>85% coverage)
- [ ] Monitoring dashboards configured
- [ ] Alert rules for timeouts
- [ ] Audit logging verified
- [ ] Security scanning completed

---

## 11. Future Enhancements

1. **Client portal:** Web interface for approvals instead of email
2. **Video approvals:** Support for video deliverable reviews
3. **Mobile app:** iOS/Android for quick approvals
4. **AI-assisted reviews:** Automated quality checks before client review
5. **Approval templates:** Standardized checklists by deliverable type
6. **Multi-language support:** Handle approvals in different languages
7. **Analytics dashboard:** Client approval patterns and insights
8. **Automated testing:** Integration with test environments
9. **Approval workflows:** Multi-step approvals for complex deliverables
10. **Integration with Slack/Teams:** Approvals via chat platforms

---

## Appendices

### A. Approval State Machine

```
deliverable_ready → review_requested → pending_review
                                           ↓
                                      approved ←───────┐
                                           ↑            |
                                           │            ↓
revision_requested ← revision_in_progress ← resubmitted
      ↓                                         ↓
   change_order                               expired
```

### B. Sample Email Templates

**Review Request Template:**
```html
<h2>Ready for your review: {{deliverable_name}}</h2>

<p>Hi {{client_name}},</p>

<p>{{deliverable_name}} for the {{project_name}} project is ready for your review!</p>

<p><strong>Access Deliverable:</strong><br>
<a href="{{review_link}}" class="btn-primary">View Deliverable</a></p>

<p><strong>Review Checklist:</strong></p>
<ul>
{% for item in review_checklist %}
  <li>{{item}}</li>
{% endfor %}
</ul>

<p><strong>Important Details:</strong></p>
<ul>
  <li>Due date: {{due_date}}</li>
  <li>Revision rounds remaining: {{revisions_remaining}} of {{max_revisions}}</li>
</ul>

<p>Please review and let me know if you approve or if any changes are needed.</p>
```

### C. API Response Formats

**Success Response:**
```json
{
  "status": "success",
  "approval_request_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "review_requested",
  "actions_taken": ["created_approval_request", "sent_review_email"],
  "next_steps": ["await_client_response", "schedule_followup"],
  "deadlines": {
    "review_due": "2025-01-22T17:00:00Z"
  },
  "metrics": {
    "submission_to_review_hours": 0.5
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "revision_limit_exceeded",
  "message": "Maximum revisions (3) exceeded for this deliverable",
  "details": {
    "current_revisions": 3,
    "max_revisions": 3,
    "change_order_required": true
  }
}
```

---

**End of Specification**
