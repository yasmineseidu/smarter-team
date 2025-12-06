# Payment Collection Agent - Technical Specification

**Status:** Production-Ready
**Version:** 1.0.0
**Created:** 2025-12-05
**Category:** Payment & Finance
**Phase:** Phase 4 - Client Delivery
**Refined From:** plan/agents/payment-collection.md

---

## 1. Overview

### Purpose
Autonomous payment collection agent that monitors invoice due dates, sends escalating reminders, tracks payment status, and manages collection workflows for all client invoices. Integrates with Stripe for payment status tracking and multiple communication channels for reminders.

### Agent Classification
- **Type:** Monitoring & Collection Agent
- **Execution Mode:** Scheduled (Cron) + Event-driven (Stripe webhooks)
- **Human-in-the-Loop:** Required for work pauses, collections escalation, and payment arrangements
- **Priority:** High (revenue critical path)

### Dependencies
- **Upstream Agents:**
  - Invoice Generation Agent (provides invoice data via handoff)
- **Downstream Agents:**
  - Project Management Agent (work pause notifications)
  - Finance Agent (revenue reporting, write-offs)
- **External Services:**
  - Stripe API (payment status, payment links)
  - Email Service (reminder delivery)
  - Slack/Telegram (internal alerts)

---

## 2. System Prompt

```
You are the Payment Collection Agent for Smarter Team, an AI agency automation system.

Your responsibilities:
- Monitor all invoices for due dates and payment status
- Send escalating reminders according to configured schedules
- Track partial payments and payment arrangements
- Alert internal teams on overdue accounts requiring attention
- Coordinate work pauses for severely overdue invoices
- Maintain audit trail of all collection activities

Reminder Schedule You Manage:
1. DUE DATE (Day 0): Send initial invoice reminder
2. 3 DAYS OVERDUE: Gentle reminder email
3. 7 DAYS OVERDUE: Firmer reminder with urgency
4. 14 DAYS OVERDUE: Warning about potential work pause
5. 30 DAYS OVERDUE: Final notice with work pause implementation
6. 60 DAYS OVERDUE: Collections consideration and escalation

Key Principles:
- ALWAYS verify payment status with Stripe before sending reminders
- RESPECT configured grace periods and business hours
- DOCUMENT all collection activities with complete audit trail
- ESCALATE to human approval for work pauses and collections
- ACCOMMODATE reasonable payment arrangements when requested
- MAINTAIN professional yet firm communication tone
- AVOID reminder spam on weekends/holidays unless critically overdue

You have access to these tools:
- get_overdue_invoices: Fetch invoices requiring attention
- check_stripe_payment_status: Verify payment via Stripe API
- send_payment_reminder: Send email reminder with template
- send_internal_alert: Notify team via Slack/Telegram
- update_collection_status: Track collection actions in database
- request_payment_arrangement: Handle client payment plan requests
- pause_project_work: Coordinate project work pause with PM agent
- escalate_to_collections: Prepare case for collections agency

Error Handling:
- If Stripe API is down → Use cached status, queue for retry
- If email send fails → Try alternative channel, log for retry
- If payment amount mismatch → Flag for manual review
- If client requests arrangement → Escalate to human approval
- If work pause approved → Coordinate with Project Management

Always structure responses as JSON with:
{
  "status": "success|pending_approval|error",
  "invoices_processed": 5,
  "reminders_sent": 3,
  "alerts_triggered": 1,
  "payment_arrangements": 0,
  "work_pauses": 0,
  "next_actions": ["send_reminders", "monitor_status"],
  "errors": []
}
```

---

## 3. Agent Architecture

### Class Definition

```python
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Literal

from src.agents.base_agent import BaseAgent
from src.integrations.stripe_client import StripeClient
from src.integrations.email_client import EmailClient
from src.integrations.slack_client import SlackClient
from src.config import get_agent_logger


CollectionStatus = Literal["monitoring", "reminder_sent", "payment_arranged", "work_paused", "collections"]
ReminderLevel = Literal["due_date", "gentle", "firm", "warning", "final", "escalation"]


class PaymentCollectionAgent(BaseAgent):
    """
    Autonomous payment collection and monitoring agent.

    Manages invoice reminders, payment status tracking, and collection workflows.
    Integrates with Stripe, email, and internal communication channels.
    """

    def __init__(self):
        super().__init__(
            name="payment_collection",
            description="Monitor invoices and manage payment collection workflows"
        )

        # Integration clients (lazy loaded)
        self._stripe_client: StripeClient | None = None
        self._email_client: EmailClient | None = None
        self._slack_client: SlackClient | None = None

        # Configuration
        self.reminder_schedule = {
            "due_date": 0,
            "gentle": 3,
            "firm": 7,
            "warning": 14,
            "final": 30,
            "escalation": 60,
        }
        self.business_hours = {"start": 9, "end": 17, "timezone": "America/New_York"}
        self.pause_threshold_days = 30
        self.collections_threshold_days = 60

        # Register tools
        self._register_tools()

    @property
    def system_prompt(self) -> str:
        """Return system prompt from section 2."""
        return """[System prompt from section 2 above]"""

    @property
    def stripe_client(self) -> StripeClient:
        """Lazy load Stripe client."""
        if self._stripe_client is None:
            from src.config import settings
            self._stripe_client = StripeClient(api_key=settings.stripe_api_key)
        return self._stripe_client

    @property
    def email_client(self) -> EmailClient:
        """Lazy load email client."""
        if self._email_client is None:
            self._email_client = EmailClient()
        return self._email_client

    @property
    def slack_client(self) -> SlackClient:
        """Lazy load Slack client."""
        if self._slack_client is None:
            from src.config import settings
            self._slack_client = SlackClient(webhook_url=settings.slack_webhook_url)
        return self._slack_client

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process payment collection task.

        Args:
            task: {
                "type": "daily_check|webhook_payment|manual_reminder",
                "invoice_id": "uuid|null",
                "force_send": false,
                "dry_run": false
            }

        Returns:
            Collection activity results with detailed metrics
        """
        task_type = task.get("type", "daily_check")

        self.logger.info(
            f"Processing {task_type} collection task",
            extra={"invoice_id": task.get("invoice_id")}
        )

        try:
            if task_type == "daily_check":
                return await self._process_daily_collection_check(task)
            elif task_type == "webhook_payment":
                return await self._process_payment_webhook(task)
            elif task_type == "manual_reminder":
                return await self._process_manual_reminder(task)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

        except Exception as e:
            self.logger.error(f"Collection task failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": "task_failed",
                "message": str(e),
                "invoices_processed": 0,
            }

    def _register_tools(self) -> None:
        """Register all tools available to this agent."""
        # Tools will be defined in section 4
        pass
```

---

## 4. Tool Definitions

### 4.1 get_overdue_invoices

**Purpose:** Fetch invoices requiring collection attention

```python
async def get_overdue_invoices(
    self,
    include_paid: bool = False,
    days_overdue_min: int = 0,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Retrieve overdue invoices from database.

    Args:
        include_paid: Include recently paid invoices for final status update
        days_overdue_min: Minimum days overdue to filter
        limit: Maximum number of invoices to return

    Returns:
        {
            "invoices": [
                {
                    "id": "uuid",
                    "invoice_number": "INV-2025-001",
                    "client": {"id": "uuid", "name": "Client Name", "email": "client@example.com"},
                    "amount_total": "5000.00",
                    "amount_paid": "0.00",
                    "amount_due": "5000.00",
                    "due_date": "2025-01-15",
                    "days_overdue": 5,
                    "status": "sent|overdue|paid",
                    "last_reminder": "2025-01-12",
                    "reminder_level": "gentle",
                    "stripe_invoice_id": "in_123",
                    "project_id": "uuid",
                    "payment_arrangements": []
                }
            ],
            "total_count": 15,
            "query_time_ms": 45.2
        }
    """
    from src.database import get_async_session
    from sqlalchemy import select, and_, func
    from src.models import Invoice, Client

    async with get_async_session() as session:
        # Calculate overdue date threshold
        overdue_threshold = date.today() - timedelta(days=days_overdue_min)

        query = (
            select(
                Invoice,
                Client,
                func.datediff(date.today(), Invoice.due_date).label("days_overdue")
            )
            .join(Client, Invoice.client_id == Client.id)
            .where(
                and_(
                    Invoice.due_date <= overdue_threshold,
                    Invoice.status.in_(["sent", "overdue"] if not include_paid else ["sent", "overdue", "paid"])
                )
            )
            .order_by(func.datediff(date.today(), Invoice.due_date).desc())
            .limit(limit)
        )

        result = await session.execute(query)
        invoices = []

        for row in result:
            invoice, client, days_overdue = row

            invoices.append({
                "id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "client": {
                    "id": str(client.id),
                    "name": client.name,
                    "email": client.email,
                },
                "amount_total": str(invoice.total),
                "amount_paid": str(invoice.amount_paid),
                "amount_due": str(invoice.amount_due),
                "due_date": invoice.due_date.isoformat(),
                "days_overdue": days_overdue or 0,
                "status": invoice.status,
                "last_reminder": invoice.last_reminder.isoformat() if invoice.last_reminder else None,
                "reminder_level": invoice.reminder_level,
                "stripe_invoice_id": invoice.stripe_invoice_id,
                "project_id": str(invoice.project_id),
                "payment_arrangements": [],  # Load from payment_arrangements table
            })

        return {
            "invoices": invoices,
            "total_count": len(invoices),
            "query_time_ms": 0.0,  # TODO: Track query time
        }
```

### 4.2 check_stripe_payment_status

**Purpose:** Verify current payment status via Stripe API

```python
async def check_stripe_payment_status(
    self,
    stripe_invoice_id: str,
) -> dict[str, Any]:
    """
    Check payment status from Stripe API.

    Args:
        stripe_invoice_id: Stripe invoice identifier

    Returns:
        {
            "status": "draft|open|paid|uncollectible|void",
            "amount_due": 5000,
            "amount_paid": 2500,
            "amount_remaining": 2500,
            "paid_at": "2025-01-15T10:30:00Z|null",
            "payment_attempts": 1,
            "next_payment_attempt": "2025-01-22T10:30:00Z|null",
            "metadata": {}
        }
    """
    try:
        invoice = await self.stripe_client.get_invoice(stripe_invoice_id)

        return {
            "status": invoice["status"],
            "amount_due": invoice["amount_due"] / 100,  # Convert from cents
            "amount_paid": invoice["amount_paid"] / 100,
            "amount_remaining": invoice["amount_remaining"] / 100,
            "paid_at": invoice.get("paid_at"),
            "payment_attempts": invoice.get("payment_attempts", 0),
            "next_payment_attempt": invoice.get("next_payment_attempt"),
            "metadata": invoice.get("metadata", {}),
        }

    except Exception as e:
        self.logger.error(f"Stripe API error for {stripe_invoice_id}: {e}")
        return {
            "status": "unknown",
            "error": str(e),
        }
```

### 4.3 send_payment_reminder

**Purpose:** Send email reminder with appropriate template

```python
async def send_payment_reminder(
    self,
    invoice_data: dict[str, Any],
    reminder_level: ReminderLevel,
    custom_message: str | None = None,
) -> dict[str, Any]:
    """
    Send payment reminder email to client.

    Args:
        invoice_data: Invoice details from get_overdue_invoices
        reminder_level: Type of reminder to send
        custom_message: Optional custom message override

    Returns:
        {
            "success": true,
            "message_id": "email_message_id",
            "template_used": "gentle_reminder",
            "sent_at": "2025-01-18T10:00:00Z"
        }
    """
    # Select template based on reminder level
    templates = {
        "due_date": self._get_due_date_template(),
        "gentle": self._get_gentle_reminder_template(),
        "firm": self._get_firm_reminder_template(),
        "warning": self._get_warning_template(),
        "final": self._get_final_notice_template(),
        "escalation": self._get_escalation_template(),
    }

    template = templates.get(reminder_level, templates["gentle"])

    # Prepare template variables
    template_vars = {
        "first_name": invoice_data["client"]["name"].split()[0],
        "invoice_number": invoice_data["invoice_number"],
        "amount": float(invoice_data["amount_due"]),
        "due_date": datetime.fromisoformat(invoice_data["due_date"]).strftime("%B %d, %Y"),
        "days_overdue": invoice_data["days_overdue"],
        "payment_link": await self._get_payment_link(invoice_data["stripe_invoice_id"]),
        "custom_message": custom_message or "",
    }

    # Render template
    subject = template["subject"].format(**template_vars)
    html_body = template["html_body"].format(**template_vars)
    text_body = template["text_body"].format(**template_vars)

    try:
        result = await self.email_client.send_email(
            to=invoice_data["client"]["email"],
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            metadata={
                "invoice_id": invoice_data["id"],
                "invoice_number": invoice_data["invoice_number"],
                "reminder_level": reminder_level,
                "type": "payment_reminder",
            }
        )

        return {
            "success": True,
            "message_id": result["message_id"],
            "template_used": reminder_level,
            "sent_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        self.logger.error(f"Failed to send reminder for {invoice_data['invoice_number']}: {e}")
        return {
            "success": False,
            "error": str(e),
            "template_used": reminder_level,
        }

def _get_gentle_reminder_template(self) -> dict[str, str]:
    """Gentle reminder template (3 days overdue)."""
    return {
        "subject": "Quick reminder: Invoice {invoice_number}",
        "html_body": """
        <p>Hi {first_name},</p>
        <p>Just a friendly reminder that invoice {invoice_number} for ${amount:,.2f} was due on {due_date}.</p>
        <p>You can pay securely here: <a href="{payment_link}">Pay Invoice</a></p>
        <p>Let me know if you have any questions or need any assistance!</p>
        <p>Best regards,<br>Smarter Team</p>
        """,
        "text_body": """
        Hi {first_name},

        Just a friendly reminder that invoice {invoice_number} for ${amount:,.2f} was due on {due_date}.

        Pay here: {payment_link}

        Let me know if you have any questions!

        Best regards,
        Smarter Team
        """
    }

def _get_firm_reminder_template(self) -> dict[str, str]:
    """Firm reminder template (7 days overdue)."""
    return {
        "subject": "Invoice {invoice_number} is overdue",
        "html_body": """
        <p>Hi {first_name},</p>
        <p>Invoice {invoice_number} for ${amount:,.2f} is now {days_overdue} days overdue.</p>
        <p>Please process payment at your earliest convenience: <a href="{payment_link}">Pay Invoice</a></p>
        <p>If there's an issue with the invoice or payment, please let me know so we can work it out.</p>
        <p>Best regards,<br>Smarter Team</p>
        """,
        "text_body": """
        Hi {first_name},

        Invoice {invoice_number} for ${amount:,.2f} is now {days_overdue} days overdue.

        Please process payment at your earliest convenience: {payment_link}

        If there's an issue with the invoice or payment, please let me know so we can work it out.

        Best regards,
        Smarter Team
        """
    }

def _get_warning_template(self) -> dict[str, str]:
    """Warning template (14 days overdue)."""
    return {
        "subject": "Important: Invoice {invoice_number} - 14 days overdue",
        "html_body": """
        <p>Hi {first_name},</p>
        <p>Invoice {invoice_number} for ${amount:,.2f} is now 14 days past due.</p>
        <p><strong>If payment isn't received within the next 7 days, we may need to pause work on your project.</strong></p>
        <p>Please pay here: <a href="{payment_link}">Pay Invoice</a></p>
        <p>If you're experiencing difficulties, let's discuss alternative arrangements.</p>
        <p>Best regards,<br>Smarter Team</p>
        """,
        "text_body": """
        Hi {first_name},

        Invoice {invoice_number} for ${amount:,.2f} is now 14 days past due.

        If payment isn't received within the next 7 days, we may need to pause work on your project.

        Please pay here: {payment_link}

        If you're experiencing difficulties, let's discuss alternative arrangements.

        Best regards,
        Smarter Team
        """
    }

def _get_final_notice_template(self) -> dict[str, str]:
    """Final notice template (30 days overdue)."""
    return {
        "subject": "Final Notice: Invoice {invoice_number}",
        "html_body": """
        <p>Hi {first_name},</p>
        <p>Invoice {invoice_number} for ${amount:,.2f} is now 30 days overdue.</p>
        <p><strong>As a result, we've paused work on your project until payment is received.</strong></p>
        <p>Payment link: <a href="{payment_link}">Pay Invoice</a></p>
        <p>Please respond to this email to discuss payment arrangements.</p>
        <p>Best regards,<br>Smarter Team</p>
        """,
        "text_body": """
        Hi {first_name},

        Invoice {invoice_number} for ${amount:,.2f} is now 30 days overdue.

        As a result, we've paused work on your project until payment is received.

        Payment link: {payment_link}

        Please respond to this email to discuss payment arrangements.

        Best regards,
        Smarter Team
        """
    }
```

### 4.4 send_internal_alert

**Purpose:** Notify internal team about collection issues

```python
async def send_internal_alert(
    self,
    alert_type: Literal["overdue_30", "overdue_60", "payment_arrangement", "collections"],
    invoice_data: dict[str, Any],
    message: str | None = None,
) -> dict[str, Any]:
    """
    Send alert to internal team via Slack.

    Args:
        alert_type: Type of alert to send
        invoice_data: Invoice details
        message: Optional custom message

    Returns:
        {
            "success": true,
            "message_id": "slack_message_ts",
            "channel": "#finance-alerts"
        }
    """
    # Format alert message based on type
    if alert_type == "overdue_30":
        title = f"🟡 Invoice 30 Days Overdue"
        color = "warning"
    elif alert_type == "overdue_60":
        title = f"🔴 Invoice 60 Days Overdue"
        color = "danger"
    elif alert_type == "payment_arrangement":
        title = f"📋 Payment Arrangement Requested"
        color = "good"
    elif alert_type == "collections":
        title = f"⚖️ Ready for Collections"
        color = "danger"
    else:
        title = f"ℹ️ Collection Alert"
        color = "#808080"

    # Build Slack message
    slack_message = {
        "attachments": [{
            "color": color,
            "title": title,
            "fields": [
                {"title": "Invoice", "value": invoice_data["invoice_number"], "short": True},
                {"title": "Client", "value": invoice_data["client"]["name"], "short": True},
                {"title": "Amount", "value": f"${float(invoice_data['amount_due']):,.2f}", "short": True},
                {"title": "Days Overdue", "value": str(invoice_data["days_overdue"]), "short": True},
            ],
            "actions": [
                {
                    "type": "button",
                    "text": "View Invoice",
                    "url": f"https://dashboard.stripe.com/invoices/{invoice_data['stripe_invoice_id']}"
                }
            ],
            "footer": "Payment Collection Agent",
            "ts": int(datetime.utcnow().timestamp())
        }]
    }

    if message:
        slack_message["text"] = message

    try:
        result = await self.slack_client.send_message(slack_message)

        return {
            "success": True,
            "message_id": result["ts"],
            "channel": result.get("channel", "#finance-alerts"),
        }

    except Exception as e:
        self.logger.error(f"Failed to send Slack alert: {e}")
        return {
            "success": False,
            "error": str(e),
        }
```

### 4.5 update_collection_status

**Purpose:** Track collection actions in database

```python
async def update_collection_status(
    self,
    invoice_id: str,
    action: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Update collection status and log action.

    Args:
        invoice_id: Invoice UUID
        action: Action taken (sent_reminder, paused_work, etc.)
        details: Additional details about the action

    Returns:
        {
            "success": true,
            "status_updated": "reminder_sent",
            "reminder_count": 2,
            "last_action": "2025-01-18T10:00:00Z"
        }
    """
    from src.database import get_async_session
    from sqlalchemy import select, update
    from src.models import Invoice, CollectionEvent

    async with get_async_session() as session:
        try:
            # Update invoice status
            update_data = {
                "updated_at": datetime.utcnow(),
            }

            if action == "sent_reminder":
                update_data["last_reminder"] = datetime.utcnow()
                # Update reminder level based on days overdue
                # TODO: Implement reminder level progression

            elif action == "paused_work":
                update_data["status"] = "work_paused"

            elif action == "payment_arranged":
                update_data["status"] = "payment_arranged"

            await session.execute(
                update(Invoice)
                .where(Invoice.id == invoice_id)
                .values(**update_data)
            )

            # Log collection event
            event = CollectionEvent(
                invoice_id=invoice_id,
                event_type=action,
                event_source="payment_collection_agent",
                description=details.get("description") if details else None,
                metadata=details or {},
                created_by="payment_collection_agent",
            )

            session.add(event)
            await session.commit()

            return {
                "success": True,
                "status_updated": update_data.get("status", "reminder_sent"),
                "event_id": str(event.id),
                "last_action": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            await session.rollback()
            self.logger.error(f"Failed to update collection status: {e}")
            return {
                "success": False,
                "error": str(e),
            }
```

### 4.6 request_payment_arrangement

**Purpose:** Handle client payment plan requests

```python
async def request_payment_arrangement(
    self,
    invoice_id: str,
    proposed_terms: dict[str, Any],
    client_notes: str | None = None,
) -> dict[str, Any]:
    """
    Process payment arrangement request from client.

    Args:
        invoice_id: Invoice UUID
        proposed_terms: {
            "total_amount": "2500.00",
            "monthly_payment": "500.00",
            "start_date": "2025-02-01",
            "duration_months": 5
        }
        client_notes: Optional notes from client

    Returns:
        {
            "status": "pending_approval",
            "arrangement_id": "uuid",
            "requires_human_approval": true,
            "approval_url": "https://dashboard.app/approve/..."
        }
    """
    from src.database import get_async_session
    from src.models import PaymentArrangement

    async with get_async_session() as session:
        try:
            # Create payment arrangement record
            arrangement = PaymentArrangement(
                invoice_id=invoice_id,
                proposed_terms=proposed_terms,
                client_notes=client_notes,
                status="pending_approval",
                created_at=datetime.utcnow(),
            )

            session.add(arrangement)
            await session.commit()

            # Send internal alert for approval
            await self.send_internal_alert(
                alert_type="payment_arrangement",
                invoice_data=await self._get_invoice_details(invoice_id),
                message=f"Client requested payment arrangement: ${proposed_terms['monthly_payment']}/month for {proposed_terms.get('duration_months', 'unknown')} months"
            )

            return {
                "status": "pending_approval",
                "arrangement_id": str(arrangement.id),
                "requires_human_approval": True,
                "message": "Payment arrangement request received and pending approval",
            }

        except Exception as e:
            await session.rollback()
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to process payment arrangement request",
            }
```

### 4.7 pause_project_work

**Purpose:** Coordinate project work pause with PM agent

```python
async def pause_project_work(
    self,
    invoice_id: str,
    project_id: str,
    reason: str = "Invoice overdue 30+ days",
) -> dict[str, Any]:
    """
    Request project work pause via PM agent.

    Args:
        invoice_id: Invoice UUID causing pause
        project_id: Project UUID to pause
        reason: Reason for work pause

    Returns:
        {
            "success": true,
            "pause_id": "task_id",
            "status": "pause_requested",
            "effective_date": "2025-01-18"
        }
    """
    try:
        # Handoff to Project Management agent
        task_id = await self.handoff_to(
            target_agent="project_management",
            payload={
                "action": "pause_project",
                "project_id": project_id,
                "reason": reason,
                "triggering_invoice": invoice_id,
                "resume_condition": "payment_received",
            },
            priority="high"
        )

        return {
            "success": True,
            "pause_id": task_id,
            "status": "pause_requested",
            "message": "Project work pause requested from PM agent",
        }

    except Exception as e:
        self.logger.error(f"Failed to request project pause: {e}")
        return {
            "success": False,
            "error": str(e),
        }
```

---

## 5. Database Schema

### 5.1 invoices Table (Additions)

```sql
-- Add collection-specific columns to existing invoices table
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS last_reminder TIMESTAMP WITH TIME ZONE;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS reminder_level VARCHAR(20);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS collection_status VARCHAR(30) DEFAULT 'monitoring';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS work_paused_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_arrangement_id UUID;

-- Add constraints
ALTER TABLE invoices ADD CONSTRAINT valid_reminder_level
CHECK (reminder_level IN ('due_date', 'gentle', 'firm', 'warning', 'final', 'escalation'));

ALTER TABLE invoices ADD CONSTRAINT valid_collection_status
CHECK (collection_status IN ('monitoring', 'reminder_sent', 'payment_arranged', 'work_paused', 'collections'));
```

### 5.2 collection_events Table

```sql
CREATE TABLE collection_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,

    -- Event details
    event_type VARCHAR(50) NOT NULL,  -- sent_reminder, payment_arranged, work_paused, escalated
    event_source VARCHAR(50),  -- payment_collection_agent, stripe_webhook, manual

    -- Event data
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    -- Indexes
    INDEX idx_collection_events_invoice_id (invoice_id),
    INDEX idx_collection_events_type (event_type),
    INDEX idx_collection_events_created_at (created_at)
);
```

### 5.3 payment_arrangements Table

```sql
CREATE TABLE payment_arrangements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,

    -- Arrangement details
    status VARCHAR(30) NOT NULL DEFAULT 'pending_approval',  -- pending_approval, active, completed, cancelled
    proposed_terms JSONB NOT NULL,  -- {"total_amount": "2500.00", "monthly_payment": "500.00", ...}
    approved_terms JSONB,  -- Final approved arrangement

    -- Schedule
    start_date DATE,
    end_date DATE,
    next_payment_date DATE,

    -- Tracking
    total_amount NUMERIC(10, 2) NOT NULL,
    amount_paid NUMERIC(10, 2) DEFAULT 0.00,
    payments_made INTEGER DEFAULT 0,

    -- Notes and audit
    client_notes TEXT,
    internal_notes TEXT,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'payment_collection_agent',

    -- Constraints
    CONSTRAINT valid_arrangement_status CHECK (status IN ('pending_approval', 'active', 'completed', 'cancelled', 'defaulted')),
    CONSTRAINT valid_amounts CHECK (total_amount >= 0 AND amount_paid >= 0 AND amount_paid <= total_amount)
);

-- Indexes
CREATE INDEX idx_payment_arrangements_invoice_id ON payment_arrangements(invoice_id);
CREATE INDEX idx_payment_arrangements_status ON payment_arrangements(status);
CREATE INDEX idx_payment_arrangements_next_payment ON payment_arrangements(next_payment_date) WHERE status = 'active';
```

### 5.4 reminder_templates Table

```sql
CREATE TABLE reminder_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Template identification
    reminder_level VARCHAR(20) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,

    -- Template content
    subject_template TEXT NOT NULL,
    html_template TEXT NOT NULL,
    text_template TEXT NOT NULL,

    -- Configuration
    send_after_days INTEGER NOT NULL,  -- Days after due date
    max_sends INTEGER DEFAULT 1,  -- Maximum times to send this template

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE (reminder_level, language),
    CONSTRAINT valid_reminder_level_template CHECK (reminder_level IN ('due_date', 'gentle', 'firm', 'warning', 'final', 'escalation'))
);

-- Insert default templates
INSERT INTO reminder_templates (reminder_level, subject_template, html_template, text_template, send_after_days) VALUES
('due_date', 'Invoice {invoice_number} is due today', 'Your invoice {invoice_number} for ${amount} is due today.', 'Invoice {invoice_number} due: ${amount}', 0),
('gentle', 'Quick reminder: Invoice {invoice_number}', 'Gentle reminder about overdue invoice {invoice_number}', 'Reminder: Invoice {invoice_number}', 3),
('firm', 'Invoice {invoice_number} is overdue', 'Your invoice {invoice_number} is {days_overdue} days overdue', 'Overdue: Invoice {invoice_number}', 7),
('warning', 'Important: Invoice {invoice_number} - Work may pause', 'Invoice {invoice_number} is 14 days overdue. Work may pause.', 'Warning: Invoice {invoice_number} overdue', 14),
('final', 'Final Notice: Invoice {invoice_number}', 'Final notice: Invoice {invoice_number} is 30 days overdue. Work paused.', 'Final Notice: Invoice {invoice_number}', 30),
('escalation', 'Collections: Invoice {invoice_number}', 'Invoice {invoice_number} escalated to collections after 60 days.', 'Collections: Invoice {invoice_number}', 60);
```

---

## 6. Error Handling & Edge Cases

### 6.1 Error Scenarios

| Error | Detection | Handling | Recovery |
|-------|-----------|----------|----------|
| Stripe API unavailable | Connection timeout, 5xx errors | Use cached status, queue for retry | Retry every 15 minutes for 2 hours |
| Email delivery failure | SMTP error, bounce message | Try alternative channel (SMS) | Queue for retry in 4 hours |
| Invoice already paid | Stripe status = paid | Update DB, stop reminders | Mark as complete, send receipt |
| Partial payment received | Amount paid < total due | Update remaining amount, continue reminders | Adjust reminder tone based on effort |
| Client disputes charge | Stripe dispute notification | Pause collection, notify finance | Handoff to human resolution |
| Payment arrangement request | Client responds with arrangement terms | Create arrangement record, request approval | Pause reminders until approved |
| Weekends/Holidays | Calendar check | Delay reminders until business day | Schedule for next business day |
| B2B payment delays | Large corporate clients | Extend reminder intervals | Configure per-client terms |

### 6.2 Retry Logic

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def check_stripe_payment_status_with_retry(self, stripe_invoice_id: str):
    """Retry Stripe API calls on transient failures."""
    return await self.check_stripe_payment_status(stripe_invoice_id)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=5, max=30),
)
async def send_reminder_with_retry(self, invoice_data: dict, reminder_level: str):
    """Retry email sending on temporary failures."""
    return await self.send_payment_reminder(invoice_data, reminder_level)
```

### 6.3 Edge Cases

1. **Partial Payments**:
   - Update `amount_due` and continue reminders for remaining balance
   - Adjust reminder tone to acknowledge partial payment
   - Track payment history for audit

2. **Payment Disputes**:
   - Immediately pause all collection activities
   - Alert finance team via high-priority Slack
   - Handoff to human for dispute resolution

3. **Bankruptcy/Legal Issues**:
   - Mark account as do-not-contact
   - Escalate to legal/finance team
   - Comply with all legal requirements

4. **Client Communication Preferences**:
   - Respect unsubscribes from reminder emails
   - Offer alternative communication channels
   - Document client preferences

5. **Currency Conversion Issues**:
   - Handle multi-currency invoices (future)
   - Use real-time exchange rates for conversions
   - Display amounts in client's preferred currency

---

## 7. Testing Requirements

### 7.1 Unit Tests (Target: >90%)

**File:** `app/backend/__tests__/unit/agents/test_payment_collection_agent.py`

```python
"""Unit tests for PaymentCollectionAgent."""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.payment_collection import PaymentCollectionAgent


@pytest.fixture
def agent():
    """Create agent instance."""
    return PaymentCollectionAgent()


@pytest.fixture
def overdue_invoices():
    """Sample overdue invoice data."""
    return [
        {
            "id": "inv-1",
            "invoice_number": "INV-2025-001",
            "client": {"id": "client-1", "name": "Test Client", "email": "test@example.com"},
            "amount_total": "5000.00",
            "amount_paid": "0.00",
            "amount_due": "5000.00",
            "due_date": "2025-01-10",
            "days_overdue": 8,
            "status": "overdue",
            "last_reminder": "2025-01-15",
            "reminder_level": "gentle",
            "stripe_invoice_id": "in_123",
            "project_id": "proj-1",
        },
        {
            "id": "inv-2",
            "invoice_number": "INV-2025-002",
            "client": {"id": "client-2", "name": "Another Client", "email": "another@example.com"},
            "amount_total": "10000.00",
            "amount_paid": "2500.00",
            "amount_due": "7500.00",
            "due_date": "2024-12-01",
            "days_overdue": 48,
            "status": "overdue",
            "last_reminder": "2025-01-01",
            "reminder_level": "final",
            "stripe_invoice_id": "in_456",
            "project_id": "proj-2",
        }
    ]


class TestPaymentCollectionAgent:
    """Test suite for PaymentCollectionAgent."""

    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "payment_collection"
        assert agent.pause_threshold_days == 30
        assert agent.collections_threshold_days == 60
        assert "gentle" in agent.reminder_schedule

    async def test_get_overdue_invoices_success(self, agent):
        """Test fetching overdue invoices."""
        with patch("src.agents.payment_collection.get_async_session") as mock_session:
            # Mock database response
            mock_result = MagicMock()
            mock_result.__iter__ = MagicMock(return_value=iter([]))

            mock_session.return_value.__aenter__.return_value.execute = AsyncMock(
                return_value=mock_result
            )

            result = await agent.get_overdue_invoices()

            assert "invoices" in result
            assert "total_count" in result
            assert isinstance(result["invoices"], list)

    async def test_check_stripe_payment_status_success(self, agent):
        """Test Stripe payment status check."""
        with patch.object(agent, 'stripe_client') as mock_stripe:
            mock_stripe.get_invoice = AsyncMock(return_value={
                "status": "open",
                "amount_due": 500000,  # cents
                "amount_paid": 0,
                "amount_remaining": 500000,
                "payment_attempts": 1,
            })

            result = await agent.check_stripe_payment_status("in_123")

            assert result["status"] == "open"
            assert result["amount_due"] == 5000.00
            assert result["amount_paid"] == 0.00

    async def test_send_payment_reminder_gentle(self, agent):
        """Test sending gentle reminder."""
        invoice_data = {
            "client": {"name": "John Doe", "email": "john@example.com"},
            "invoice_number": "INV-2025-001",
            "amount_due": "1000.00",
            "due_date": "2025-01-10",
            "days_overdue": 5,
            "stripe_invoice_id": "in_123",
        }

        with patch.object(agent, 'email_client') as mock_email:
            mock_email.send_email = AsyncMock(return_value={"message_id": "msg-123"})
            with patch.object(agent, '_get_payment_link', return_value="https://pay.stripe.com/123"):

                result = await agent.send_payment_reminder(invoice_data, "gentle")

                assert result["success"] is True
                assert result["template_used"] == "gentle"
                mock_email.send_email.assert_called_once()

    async def test_send_payment_reminder_final(self, agent):
        """Test sending final notice."""
        invoice_data = {
            "client": {"name": "Jane Smith", "email": "jane@example.com"},
            "invoice_number": "INV-2025-002",
            "amount_due": "5000.00",
            "due_date": "2024-12-01",
            "days_overdue": 45,
            "stripe_invoice_id": "in_456",
        }

        with patch.object(agent, 'email_client') as mock_email:
            mock_email.send_email = AsyncMock(return_value={"message_id": "msg-456"})
            with patch.object(agent, '_get_payment_link', return_value="https://pay.stripe.com/456"):

                result = await agent.send_payment_reminder(invoice_data, "final")

                assert result["success"] is True
                assert result["template_used"] == "final"
                # Verify final notice includes work pause warning
                call_args = mock_email.send_email.call_args
                email_body = call_args[1]["html_body"]
                assert "paused work" in email_body.lower()

    async def test_send_internal_alert_overdue_60(self, agent):
        """Test sending 60-day overdue alert."""
        invoice_data = {
            "invoice_number": "INV-2025-003",
            "client": {"name": "Company XYZ"},
            "amount_due": "15000.00",
            "days_overdue": 65,
            "stripe_invoice_id": "in_789",
        }

        with patch.object(agent, 'slack_client') as mock_slack:
            mock_slack.send_message = AsyncMock(return_value={"ts": "1234567890.123456"})

            result = await agent.send_internal_alert("overdue_60", invoice_data)

            assert result["success"] is True
            mock_slack.send_message.assert_called_once()

            # Verify alert content
            call_args = mock_slack.send_message.call_args[0][0]
            attachments = call_args["attachments"][0]
            assert "🔴" in attachments["title"]
            assert "60 Days Overdue" in attachments["title"]
            assert attachments["color"] == "danger"

    async def test_request_payment_arrangement(self, agent):
        """Test processing payment arrangement request."""
        with patch("src.agents.payment_collection.get_async_session") as mock_session:
            # Mock database save
            mock_session.return_value.__aenter__.return_value.add = MagicMock()
            mock_session.return_value.__aenter__.return_value.commit = AsyncMock()

            with patch.object(agent, '_get_invoice_details', return_value={}):
                with patch.object(agent, 'send_internal_alert', return_value={"success": True}):

                    result = await agent.request_payment_arrangement(
                        invoice_id="inv-123",
                        proposed_terms={
                            "total_amount": "5000.00",
                            "monthly_payment": "1000.00",
                            "start_date": "2025-02-01",
                            "duration_months": 5,
                        },
                        client_notes="Client experiencing cash flow issues"
                    )

                    assert result["status"] == "pending_approval"
                    assert result["requires_human_approval"] is True

    async def test_pause_project_work(self, agent):
        """Test requesting project work pause."""
        with patch.object(agent, 'handoff_to', return_value="task-123") as mock_handoff:

            result = await agent.pause_project_work(
                invoice_id="inv-123",
                project_id="proj-456",
                reason="Invoice 45 days overdue"
            )

            assert result["success"] is True
            assert result["pause_id"] == "task-123"
            mock_handoff.assert_called_once_with(
                target_agent="project_management",
                payload={
                    "action": "pause_project",
                    "project_id": "proj-456",
                    "reason": "Invoice 45 days overdue",
                    "triggering_invoice": "inv-123",
                    "resume_condition": "payment_received",
                },
                priority="high"
            )

    async def test_process_daily_collection_check(self, agent):
        """Test daily collection check workflow."""
        task = {"type": "daily_check", "dry_run": False}

        # Mock all dependencies
        with patch.object(agent, 'get_overdue_invoices', return_value={"invoices": []}), \
             patch.object(agent, 'check_stripe_payment_status', return_value={"status": "open"}), \
             patch.object(agent, 'send_payment_reminder', return_value={"success": True}), \
             patch.object(agent, 'update_collection_status', return_value={"success": True}):

            result = await agent.process_task(task)

            assert result["status"] == "success"
            assert "invoices_processed" in result

    async def test_process_payment_webhook(self, agent):
        """Test processing payment webhook."""
        task = {
            "type": "webhook_payment",
            "stripe_invoice_id": "in_123",
            "payment_status": "paid"
        }

        with patch.object(agent, 'check_stripe_payment_status', return_value={"status": "paid"}), \
             patch.object(agent, 'update_collection_status', return_value={"success": True}):

            result = await agent.process_task(task)

            assert result["status"] == "success"

    def test_reminder_templates(self, agent):
        """Test reminder template generation."""
        gentle_template = agent._get_gentle_reminder_template()
        assert "{invoice_number}" in gentle_template["subject"]
        assert "friendly reminder" in gentle_template["html_body"].lower()

        firm_template = agent._get_firm_reminder_template()
        assert "overdue" in firm_template["subject"].lower()
        assert "overdue" in firm_template["html_body"].lower()

        warning_template = agent._get_warning_template()
        assert "important" in warning_template["subject"].lower()
        assert "pause work" in warning_template["html_body"].lower()

        final_template = agent._get_final_notice_template()
        assert "final notice" in final_template["subject"].lower()
        assert "paused work" in final_template["html_body"].lower()
```

### 7.2 Integration Tests

**File:** `app/backend/__tests__/integration/test_payment_collection_integration.py`

```python
"""Integration tests for payment collection flow."""

import pytest
from datetime import date, timedelta

from src.agents.payment_collection import PaymentCollectionAgent
from src.database import get_async_session
from src.models import Invoice, Client, Project, CollectionEvent


@pytest.mark.integration
class TestPaymentCollectionIntegration:
    """Integration tests with database and external services."""

    async def test_full_collection_workflow(self, db_session):
        """Test complete collection workflow from overdue to paid."""
        # Setup: Create overdue invoice
        client = Client(
            name="Test Client",
            email="test@example.com",
        )
        project = Project(name="Test Project", client=client)
        invoice = Invoice(
            client=client,
            project=project,
            invoice_number="INV-2025-001",
            total=5000.00,
            amount_due=5000.00,
            due_date=date.today() - timedelta(days=10),
            status="sent",
            stripe_invoice_id="in_123",
        )

        db_session.add_all([client, project, invoice])
        await db_session.commit()

        # Execute: Process collection
        agent = PaymentCollectionAgent()

        # Check overdue invoices
        overdue = await agent.get_overdue_invoices()
        assert len(overdue["invoices"]) == 1
        assert overdue["invoices"][0]["days_overdue"] == 10

        # Send gentle reminder
        reminder_result = await agent.send_payment_reminder(
            overdue["invoices"][0],
            "gentle"
        )
        assert reminder_result["success"] is True

        # Update collection status
        status_result = await agent.update_collection_status(
            str(invoice.id),
            "sent_reminder",
            {"reminder_level": "gentle", "message_id": reminder_result["message_id"]}
        )
        assert status_result["success"] is True

        # Verify: Collection event logged
        events = await db_session.execute(
            select(CollectionEvent).where(CollectionEvent.invoice_id == invoice.id)
        )
        event = events.scalar_one()
        assert event.event_type == "sent_reminder"
        assert event.event_source == "payment_collection_agent"

    async def test_payment_arrangement_flow(self, db_session):
        """Test payment arrangement request and approval flow."""
        # Setup: Create severely overdue invoice
        # ... similar setup as above but 45 days overdue ...

        # Execute: Client requests payment arrangement
        agent = PaymentCollectionAgent()

        arrangement_result = await agent.request_payment_arrangement(
            invoice_id="inv-123",
            proposed_terms={
                "total_amount": "5000.00",
                "monthly_payment": "1000.00",
                "start_date": "2025-02-01",
                "duration_months": 5,
            },
            client_notes="Experiencing temporary cash flow issues"
        )

        assert arrangement_result["status"] == "pending_approval"
        assert arrangement_result["requires_human_approval"] is True

    async def test_work_pause_escalation(self, db_session):
        """Test work pause for 30+ day overdue invoice."""
        # Setup: Create 35-day overdue invoice
        # ... setup code ...

        # Execute: Process final notice and pause
        agent = PaymentCollectionAgent()

        # Send final notice
        final_result = await agent.send_payment_reminder(
            invoice_data,
            "final"
        )
        assert final_result["success"] is True

        # Pause project work
        pause_result = await agent.pause_project_work(
            invoice_id="inv-123",
            project_id="proj-456"
        )
        assert pause_result["success"] is True
        assert pause_result["status"] == "pause_requested"
```

### 7.3 Test Coverage Targets

- **Unit tests:** >90% coverage
- **Integration tests:** >85% coverage
- **Critical paths:** 100% coverage (reminder sending, payment status checking, status updates)
- **Template rendering:** 100% coverage (all reminder templates)
- **Edge cases:** 100% coverage (partial payments, disputes, arrangements)

---

## 8. Monitoring & Observability

### 8.1 Metrics to Track

```python
# Prometheus metrics
collection_reminders_sent = Counter(
    "collection_reminders_sent_total",
    "Total reminders sent",
    ["reminder_level", "status"]
)

collection_alerts_triggered = Counter(
    "collection_alerts_triggered_total",
    "Internal alerts triggered",
    ["alert_type"]
)

payment_arrangements_requested = Counter(
    "payment_arrangements_requested_total",
    "Payment arrangement requests received"
)

projects_paused = Counter(
    "projects_paused_total",
    "Projects paused due to non-payment"
)

stripe_api_errors = Counter(
    "stripe_api_errors_total",
    "Stripe API failures",
    ["endpoint", "error_type"]
)

collection_processing_duration = Histogram(
    "collection_processing_duration_seconds",
    "Time to process daily collection check"
)

overdue_invoices_count = Gauge(
    "overdue_invoices_count",
    "Number of currently overdue invoices",
    ["age_bucket"]  # 0-7, 8-30, 31-60, 60+ days
)
```

### 8.2 Logging

```python
# Structured logging for all collection activities
self.logger.info(
    "Payment reminder sent",
    extra={
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "client_id": invoice.client_id,
        "reminder_level": "gentle",
        "days_overdue": days_overdue,
        "message_id": result["message_id"],
        "duration_ms": duration_ms,
    }
)

self.logger.warning(
    "Invoice escalated to work pause",
    extra={
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "client_name": invoice.client.name,
        "amount_due": float(invoice.amount_due),
        "days_overdue": days_overdue,
        "project_id": invoice.project_id,
    }
)

self.logger.error(
    "Stripe API error checking payment status",
    extra={
        "stripe_invoice_id": stripe_invoice_id,
        "error_type": type(e).__name__,
        "error_message": str(e),
        "retry_count": retry_count,
    }
)
```

### 8.3 Alerting

- **Stripe API error rate** > 5% for 5 minutes
- **Email delivery failure rate** > 10% for 1 hour
- **Invoices > 60 days overdue** > 5
- **Daily reminders not sent** for >2 hours
- **Collection workflow stall** (no updates for 24 hours)
- **Payment arrangement requests** pending > 24 hours

---

## 9. Security & Compliance

### 9.1 PCI Compliance

- Never store full credit card numbers
- Use Stripe Elements for hosted payment pages
- All payment data flows through Stripe only
- Implement strong access controls for payment arrangement data

### 9.2 Data Privacy

- Anonymize PII in logs and metrics
- Secure email transmission (TLS)
- Comply with GDPR/CCPA data requests
- Implement data retention policies

### 9.3 Access Controls

```python
# Role-based access for payment arrangement approvals
PAYMENT_ARRANGEMENT_LIMITS = {
    "account_manager": {"max_amount": 5000.00, "requires_approval": False},
    "finance_manager": {"max_amount": 25000.00, "requires_approval": False},
    "director": {"max_amount": 100000.00, "requires_approval": False},
    "cfo": {"max_amount": float("inf"), "requires_approval": False},
}
```

---

## 10. Deployment Checklist

- [ ] Database migrations applied (collection_events, payment_arrangements, reminder_templates)
- [ ] Stripe API credentials configured with proper permissions
- [ ] Email service templates configured and tested
- [ ] Slack webhook configured for internal alerts
- [ ] Celery beat scheduled for daily 9 AM collection checks
- [ ] Stripe webhook handlers configured (invoice.paid, invoice.payment_failed)
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing (>85% coverage)
- [ ] Monitoring dashboards configured (Grafana panels)
- [ ] Alert rules configured (PagerDuty/Slack)
- [ ] Business hours calendar configured for reminder scheduling
- [ ] Payment arrangement approval workflow tested
- [ ] Project pause integration tested with PM agent
- [ ] Error handling tested (Stripe down, email failures)
- [ ] Documentation updated and team trained

---

## 11. Future Enhancements

1. **Multi-channel reminders** - SMS, WhatsApp, in-app notifications
2. **Dynamic reminder scheduling** - ML model to optimize send times
3. **Payment analytics** - Predict payment delays, optimize terms
4. **Automated settlement offers** - AI-negotiated payment plans
5. **Integration with accounting systems** - QuickBooks, Xero sync
6. **Customer portal** - Self-service payment arrangements
7. **Advanced reporting** - DSO metrics, aging reports, forecasts
8. **ACH/direct debit support** - Automated bank payments
9. **International collections** - Multi-language, multi-currency
10. **Legal compliance automation** - Local regulations, statutes of limitations

---

## Appendices

### A. Collection State Machine

```
monitoring → reminder_sent → payment_arranged → completed
    ↓           ↓              ↓
reminder_sent  → work_paused → collections
    ↓              ↓
payment_arranged → completed
```

### B. Sample Collection Event

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "invoice_id": "inv-123",
  "event_type": "sent_reminder",
  "event_source": "payment_collection_agent",
  "description": "Gentle reminder sent - 3 days overdue",
  "metadata": {
    "reminder_level": "gentle",
    "message_id": "msg-123456",
    "template_used": "gentle_reminder",
    "days_overdue": 3
  },
  "created_at": "2025-01-18T10:00:00Z",
  "created_by": "payment_collection_agent"
}
```

### C. API Response Formats

**Daily Check Success:**
```json
{
  "status": "success",
  "invoices_processed": 12,
  "reminders_sent": 8,
  "alerts_triggered": 2,
  "payment_arrangements": 1,
  "work_pauses": 0,
  "processing_time_ms": 2340,
  "next_actions": ["monitor_responses", "process_arrangements"],
  "errors": []
}
```

**Reminder Send Success:**
```json
{
  "success": true,
  "message_id": "msg-123456",
  "template_used": "gentle",
  "sent_at": "2025-01-18T10:00:00Z",
  "next_reminder_date": "2025-01-22"
}
```

---

**End of Specification**
