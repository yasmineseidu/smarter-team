# Payment Processing Agent - Technical Specification

**Status:** Production-Ready
**Version:** 1.0.0
**Created:** 2025-12-05
**Category:** Payment & Finance
**Phase:** Phase 4 - Client Delivery
**Refined From:** plan/agents/payment-processing.md

---

## 1. Overview

### Purpose
Autonomously process Stripe payment events through webhook handlers, updating invoices, client balances, and triggering downstream workflows. Handles payment successes, failures, retries, and disputes with comprehensive error handling and audit trails.

### Agent Classification
- **Type:** Event-Driven Transactional Agent
- **Execution Mode:** Webhook-triggered via FastAPI → Celery tasks
- **Human-in-the-Loop:** Dispute events require immediate human notification
- **Priority:** Critical (payment infrastructure)

### Dependencies
- **Upstream Agents:**
  - Invoice Generation Agent (provides invoice context)
- **Downstream Agents:**
  - Onboarding Orchestrator (triggered by successful deposit payments)
  - Project Management Agent (milestone payment notifications)
  - Client Success Agent (payment failure follow-ups)
- **External Services:**
  - Stripe API (webhook event verification, payment data)
  - QuickBooks API (payment recording)
  - Email service (client notifications)
  - Slack/Telegram (urgent alerts)

---

## 2. System Prompt

```
You are the Payment Processing Agent for Smarter Team, an AI agency automation system.

Your responsibilities:
- Process Stripe webhook events securely with signature verification
- Update payment records and client balances in the database
- Synchronize payment data to QuickBooks for accounting
- Send appropriate notifications to clients and internal teams
- Handle payment failures with retry logic and client notifications
- Immediately escalate disputes to human review with project pausing
- Maintain perfect audit trails for all payment operations

Webhook Events You Handle:
1. PAYMENT_SUCCEEDED: Invoice paid, update status, sync to QB, send thank you
2. PAYMENT_FAILED: Log failure, notify client, track retry attempts
3. CHARGE_DISPUTED: Pause work, alert owner, gather evidence, track resolution

Security & Compliance:
- ALWAYS verify webhook signatures before processing
- NEVER process duplicate events (check event ID)
- MAINTAIN idempotency for all operations
- LOG every payment action with complete audit trail
- HANDLE webhook timeouts gracefully (return 200 immediately, process async)
- VALIDATE all payment amounts against invoice totals

Key Principles:
- Process webhooks asynchronously (Celery) for reliability
- Use database transactions for consistency
- Implement exponential backoff for external API failures
- Send human-readable notifications with clear action items
- Track all payment state changes in audit logs
- Handle partial payments and overpayments correctly
- Comply with PCI DSS through Stripe integration

You have access to these tools:
- verify_webhook_signature: Validate Stripe webhook signature
- check_event_processed: Prevent duplicate event processing
- get_payment_details: Retrieve payment and invoice information
- update_payment_status: Update database payment records
- update_client_balance: Adjust client outstanding balance
- sync_to_quickbooks: Record payment in QuickBooks
- send_payment_notification: Send emails to clients
- send_urgent_alert: Notify team of critical issues
- pause_project_work: Suspend project for disputes
- get_dispute_evidence: Gather documentation for dispute response
- log_payment_event: Comprehensive audit logging
- calculate_retry_timing: Determine next retry attempt
- validate_payment_amount: Check against invoice totals

Error Handling:
- Invalid webhook signature → Reject with 401, log security alert
- Duplicate event → Return 200 success, skip processing
- Database errors → Retry 3x with exponential backoff
- Stripe API timeout → Process asynchronously, retry later
- QuickBooks sync failure → Queue for retry, don't block payment
- Email send failure → Retry 3x, log for manual follow-up
- Dispute evidence missing → Alert ops team immediately

Always structure responses as JSON with:
{
  "status": "processed|duplicate|error|requires_action",
  "event_id": "evt_xxx",
  "event_type": "payment_succeeded|payment_failed|charge_disputed",
  "payment_id": "pi_xxx",
  "invoice_id": "in_xxx",
  "amount": 5000.00,
  "currency": "usd",
  "actions_taken": ["updated_database", "synced_quickbooks", "sent_email"],
  "next_steps": ["trigger_onboarding", "schedule_reminder"],
  "errors": [],
  "retry_scheduled": null,
  "human_notification_required": false
}
```

---

## 3. Agent Architecture

### Class Definition

```python
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Literal, Optional
import asyncio

from src.agents.base_agent import BaseAgent
from src.integrations.stripe_client import StripeClient
from src.integrations.quickbooks_client import QuickBooksClient
from src.integrations.email_client import EmailClient
from src.config import get_agent_logger
from src.database.models import Payment, Invoice, Client, Dispute, PaymentEvent

WebhookEventType = Literal[
    "payment_succeeded",
    "payment_failed",
    "charge_disputed"
]

PaymentStatus = Literal[
    "pending",
    "processing",
    "succeeded",
    "failed",
    "partially_refunded",
    "refunded",
    "disputed"
]


class PaymentProcessingAgent(BaseAgent):
    """
    Stripe webhook processing agent for payment events.

    Handles secure webhook verification, payment processing,
    and downstream workflow triggers with full audit trails.
    """

    def __init__(self):
        super().__init__(
            name="payment_processing",
            description="Process Stripe payment webhooks with secure verification"
        )

        # Integration clients (lazy loaded)
        self._stripe_client: StripeClient | None = None
        self._quickbooks_client: QuickBooksClient | None = None
        self._email_client: EmailClient | None = None

        # Configuration
        self.max_retries = 3
        self.retry_backoff_base = 2.0  # seconds
        self.webhook_timeout = 30.0  # seconds
        self.signature_tolerance = 300  # seconds (5 min)

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
    def quickbooks_client(self) -> QuickBooksClient:
        """Lazy load QuickBooks client."""
        if self._quickbooks_client is None:
            from src.config import settings
            self._quickbooks_client = QuickBooksClient(
                client_id=settings.quickbooks_client_id,
                client_secret=settings.quickbooks_client_secret
            )
        return self._quickbooks_client

    @property
    def email_client(self) -> EmailClient:
        """Lazy load email client."""
        if self._email_client is None:
            from src.config import settings
            self._email_client = EmailClient(
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password
            )
        return self._email_client

    async def process_webhook_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process incoming Stripe webhook event.

        This is the main entry point for webhook processing.
        Verifies signatures, prevents duplicates, and routes to appropriate handlers.
        """
        start_time = datetime.utcnow()
        event_id = event_data.get("id")
        event_type = event_data.get("type")

        try:
            # Security: Verify webhook signature first
            if not await self.verify_webhook_signature(event_data):
                self.logger.warning(
                    "Invalid webhook signature",
                    extra={"event_id": event_id, "ip": event_data.get("ip")}
                )
                return {
                    "status": "error",
                    "error": "Invalid signature",
                    "code": "SECURITY_VIOLATION"
                }

            # Idempotency: Check if already processed
            if await self.check_event_processed(event_id):
                self.logger.info(
                    "Duplicate webhook event",
                    extra={"event_id": event_id, "event_type": event_type}
                )
                return {
                    "status": "duplicate",
                    "event_id": event_id,
                    "message": "Event already processed"
                }

            # Mark as processing to prevent race conditions
            await self.log_payment_event(event_id, event_type, "processing")

            # Route to appropriate handler
            handler_map = {
                "payment_succeeded": self._handle_payment_succeeded,
                "payment_failed": self._handle_payment_failed,
                "charge_disputed": self._handle_charge_disputed
            }

            handler = handler_map.get(event_type)
            if not handler:
                self.logger.warning(
                    "Unhandled webhook event type",
                    extra={"event_type": event_type, "event_id": event_id}
                )
                await self.log_payment_event(event_id, event_type, "skipped")
                return {
                    "status": "skipped",
                    "event_id": event_id,
                    "message": f"Event type {event_type} not handled"
                }

            # Process the event
            result = await handler(event_data)

            # Mark as completed
            await self.log_payment_event(
                event_id,
                event_type,
                "completed",
                result
            )

            # Log processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                f"Webhook processed successfully",
                extra={
                    "event_id": event_id,
                    "event_type": event_type,
                    "processing_time_seconds": processing_time
                }
            )

            return result

        except Exception as e:
            self.logger.error(
                "Webhook processing failed",
                extra={
                    "event_id": event_id,
                    "event_type": event_type,
                    "error": str(e),
                    "processing_time": (datetime.utcnow() - start_time).total_seconds()
                },
                exc_info=True
            )

            # Mark as failed
            await self.log_payment_event(event_id, event_type, "failed", {"error": str(e)})

            return {
                "status": "error",
                "event_id": event_id,
                "error": str(e),
                "code": "PROCESSING_ERROR"
            }

    async def _handle_payment_succeeded(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Handle successful payment webhook."""
        payment_intent = event_data["data"]["object"]
        payment_id = payment_intent["id"]
        amount = Decimal(payment_intent["amount"]) / Decimal(100)  # Convert from cents
        currency = payment_intent["currency"]
        invoice_id = payment_intent.get("metadata", {}).get("invoice_id")

        # Get payment and invoice details
        payment_details = await self.get_payment_details(payment_id)
        if not payment_details:
            # Create new payment record
            payment_details = await self.create_payment_record(
                payment_intent=payment_intent,
                status="succeeded"
            )

        # Update payment status
        await self.update_payment_status(payment_id, "succeeded")

        # Update invoice status
        if invoice_id:
            await self.update_invoice_status(invoice_id, "paid")

            # Update client balance
            invoice = await self.get_invoice_details(invoice_id)
            if invoice:
                await self.update_client_balance(
                    invoice["client_id"],
                    -amount  # Reduce outstanding balance
                )

        # Sync to QuickBooks
        quickbooks_result = await self.sync_to_quickbooks({
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "invoice_id": invoice_id,
            "date": datetime.fromtimestamp(payment_intent["created"])
        })

        # Send thank you email
        if invoice_id:
            await self.send_payment_notification({
                "type": "payment_success",
                "client_email": invoice["client_email"],
                "amount": amount,
                "invoice_number": invoice["invoice_number"],
                "receipt_link": payment_intent.get("charges", {}).get("data", [{}])[0].get("receipt_url")
            })

        # Trigger downstream workflows
        next_steps = []

        # If this is a deposit payment, trigger onboarding
        if invoice_id and await self.is_deposit_invoice(invoice_id):
            await self.handoff_to(
                target_agent="onboarding_orchestrator",
                payload={
                    "client_id": invoice["client_id"],
                    "payment_id": payment_id,
                    "deposit_paid": True
                },
                priority="high"
            )
            next_steps.append("triggered_onboarding")

        # If this is a milestone payment, notify project management
        if invoice_id and await self.is_milestone_invoice(invoice_id):
            await self.handoff_to(
                target_agent="project_management",
                payload={
                    "invoice_id": invoice_id,
                    "milestone_paid": True,
                    "next_milestone_unlocked": True
                },
                priority="normal"
            )
            next_steps.append("unlocked_next_milestone")

        return {
            "status": "processed",
            "event_id": event_data["id"],
            "event_type": "payment_succeeded",
            "payment_id": payment_id,
            "invoice_id": invoice_id,
            "amount": float(amount),
            "currency": currency,
            "actions_taken": [
                "updated_payment_status",
                "updated_client_balance",
                "synced_quickbooks",
                "sent_email"
            ],
            "next_steps": next_steps,
            "errors": [],
            "quickbooks_sync": quickbooks_result
        }

    async def _handle_payment_failed(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Handle failed payment webhook."""
        payment_intent = event_data["data"]["object"]
        payment_id = payment_intent["id"]
        amount = Decimal(payment_intent["amount"]) / Decimal(100)
        last_payment_error = payment_intent.get("last_payment_error", {})
        invoice_id = payment_intent.get("metadata", {}).get("invoice_id")

        # Check if this is the final failure (Stripe retries automatically)
        failure_count = await self.get_payment_failure_count(payment_id)
        is_final_failure = failure_count >= 3  # Stripe's default retry count

        # Update payment status
        await self.update_payment_status(payment_id, "failed")

        # Log payment failure
        await self.log_payment_failure({
            "payment_id": payment_id,
            "failure_reason": last_payment_error.get("message", "Unknown"),
            "failure_code": last_payment_error.get("code", "unknown"),
            "failure_count": failure_count + 1,
            "is_final": is_final_failure,
            "invoice_id": invoice_id
        })

        # Send failure notification
        if invoice_id:
            invoice = await self.get_invoice_details(invoice_id)
            if invoice:
                await self.send_payment_notification({
                    "type": "payment_failed",
                    "client_email": invoice["client_email"],
                    "amount": amount,
                    "invoice_number": invoice["invoice_number"],
                    "failure_reason": last_payment_error.get("message", "Payment declined"),
                    "payment_link": invoice["payment_link"],
                    "is_final": is_final_failure
                })

        next_steps = []
        if is_final_failure:
            # Escalate to human for manual follow-up
            await self.send_urgent_alert({
                "type": "payment_failure_escalation",
                "payment_id": payment_id,
                "invoice_id": invoice_id,
                "client_email": invoice["client_email"] if invoice else None,
                "amount": float(amount),
                "failure_count": failure_count + 1
            })
            next_steps.append("escalated_to_human")
        else:
            # Calculate next retry timing (Stripe handles this automatically)
            next_retry = await self.calculate_retry_timing(failure_count)
            next_steps.append(f"stripe_retry_scheduled_{next_retry}")

        return {
            "status": "processed",
            "event_id": event_data["id"],
            "event_type": "payment_failed",
            "payment_id": payment_id,
            "invoice_id": invoice_id,
            "amount": float(amount),
            "currency": payment_intent["currency"],
            "actions_taken": [
                "updated_payment_status",
                "logged_failure",
                "sent_email"
            ],
            "next_steps": next_steps,
            "errors": [last_payment_error.get("message", "Unknown failure")],
            "failure_count": failure_count + 1,
            "is_final_failure": is_final_failure
        }

    async def _handle_charge_disputed(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Handle chargeback/dispute webhook."""
        charge = event_data["data"]["object"]
        dispute_id = charge.get("dispute")
        payment_id = charge.get("payment_intent")
        amount = Decimal(charge["amount"]) / Decimal(100)

        # Get dispute details from Stripe
        dispute_details = await self.stripe_client.get_dispute(dispute_id)

        # Find associated invoice and client
        invoice_id = None
        client_id = None
        if payment_id:
            payment_record = await self.get_payment_by_stripe_id(payment_id)
            if payment_record:
                invoice_id = payment_record.get("invoice_id")
                client_id = payment_record.get("client_id")

        # Create dispute record
        await self.create_dispute_record({
            "dispute_id": dispute_id,
            "payment_id": payment_id,
            "invoice_id": invoice_id,
            "client_id": client_id,
            "amount": amount,
            "currency": charge["currency"],
            "reason": dispute_details.get("reason"),
            "status": "needs_response",
            "evidence_due": datetime.fromtimestamp(dispute_details.get("evidence_details", {}).get("due_by", 0))
        })

        # Pause project work immediately
        if client_id:
            await self.pause_project_work({
                "client_id": client_id,
                "reason": "payment_dispute",
                "dispute_id": dispute_id,
                "amount": float(amount)
            })

        # Send urgent alert to owner
        await self.send_urgent_alert({
            "type": "payment_dispute",
            "dispute_id": dispute_id,
            "payment_id": payment_id,
            "client_id": client_id,
            "amount": float(amount),
            "reason": dispute_details.get("reason"),
            "evidence_due": dispute_details.get("evidence_details", {}).get("due_by"),
            "urgency": "critical"
        })

        # Gather preliminary evidence
        await self.gather_dispute_evidence({
            "dispute_id": dispute_id,
            "invoice_id": invoice_id,
            "client_id": client_id
        })

        # Notify client success team for follow-up
        await self.handoff_to(
            target_agent="client_success",
            payload={
                "type": "dispute_notification",
                "client_id": client_id,
                "dispute_id": dispute_id,
                "amount": float(amount),
                "requires_immediate_action": True
            },
            priority="critical"
        )

        return {
            "status": "requires_action",
            "event_id": event_data["id"],
            "event_type": "charge_disputed",
            "payment_id": payment_id,
            "invoice_id": invoice_id,
            "dispute_id": dispute_id,
            "amount": float(amount),
            "currency": charge["currency"],
            "actions_taken": [
                "created_dispute_record",
                "paused_project_work",
                "sent_urgent_alert",
                "gathered_evidence",
                "notified_client_success"
            ],
            "next_steps": ["human_review_required", "evidence_submission"],
            "errors": [],
            "human_notification_required": True,
            "urgency": "critical"
        }

    def _register_tools(self) -> None:
        """Register all available tools for the agent."""
        self.register_tool(self.verify_webhook_signature, "verify_webhook_signature")
        self.register_tool(self.check_event_processed, "check_event_processed")
        self.register_tool(self.get_payment_details, "get_payment_details")
        self.register_tool(self.update_payment_status, "update_payment_status")
        self.register_tool(self.update_client_balance, "update_client_balance")
        self.register_tool(self.sync_to_quickbooks, "sync_to_quickbooks")
        self.register_tool(self.send_payment_notification, "send_payment_notification")
        self.register_tool(self.send_urgent_alert, "send_urgent_alert")
        self.register_tool(self.pause_project_work, "pause_project_work")
        self.register_tool(self.get_dispute_evidence, "get_dispute_evidence")
        self.register_tool(self.log_payment_event, "log_payment_event")
        self.register_tool(self.calculate_retry_timing, "calculate_retry_timing")
        self.register_tool(self.validate_payment_amount, "validate_payment_amount")
```

---

## 4. Tools Specification

### Tool: verify_webhook_signature
**Purpose:** Securely verify Stripe webhook signature

**Input Schema:**
```python
class WebhookSignatureInput(BaseModel):
    payload: bytes = Field(..., description="Raw webhook request body")
    signature_header: str = Field(..., description="Stripe-Signature header")
    webhook_secret: str = Field(..., description="Webhook signing secret")
    tolerance: int = Field(default=300, description="Signature tolerance in seconds")
```

**Output Schema:**
```python
class WebhookSignatureOutput(BaseModel):
    valid: bool = Field(..., description="Whether signature is valid")
    event_id: str | None = Field(None, description="Extracted event ID if valid")
    error: str | None = Field(None, description="Error message if invalid")
```

**Error Handling:**
- Missing signature → Return error
- Invalid signature → Log security alert, return False
- Expired timestamp → Return error with timestamp mismatch

**Implementation:**
```python
async def verify_webhook_signature(self, payload: bytes, signature_header: str) -> bool:
    """Verify Stripe webhook signature using their official method."""
    try:
        import stripe
        from src.config import settings

        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature_header,
            secret=settings.stripe_webhook_secret,
            tolerance=self.signature_tolerance
        )
        return True, event.get("id")
    except stripe.error.SignatureVerificationError as e:
        self.logger.warning(
            "Webhook signature verification failed",
            extra={"error": str(e), "signature": signature_header[:50] + "..."}
        )
        return False, None
    except Exception as e:
        self.logger.error(
            "Webhook signature verification error",
            extra={"error": str(e)},
            exc_info=True
        )
        return False, None
```

### Tool: check_event_processed
**Purpose:** Prevent duplicate webhook event processing

**Input Schema:**
```python
class EventProcessedInput(BaseModel):
    event_id: str = Field(..., description="Stripe event ID")
```

**Output Schema:**
```python
class EventProcessedOutput(BaseModel):
    processed: bool = Field(..., description="Whether event was already processed")
    processed_at: datetime | None = Field(None, description="When it was processed")
    processing_time_ms: float = Field(..., description="Check execution time")
```

**Implementation:**
```python
async def check_event_processed(self, event_id: str) -> bool:
    """Check if webhook event has already been processed."""
    start_time = time.time()

    try:
        # Check database for processed event
        processed_event = await self.db.get_processed_event(event_id)
        processed = processed_event is not None

        self.logger.info(
            f"Event duplicate check",
            extra={
                "event_id": event_id,
                "is_duplicate": processed,
                "check_time_ms": (time.time() - start_time) * 1000
            }
        )

        return processed
    except Exception as e:
        self.logger.error(
            "Failed to check event processed status",
            extra={"event_id": event_id, "error": str(e)},
            exc_info=True
        )
        # On error, assume not processed to avoid missing events
        return False
```

### Tool: sync_to_quickbooks
**Purpose:** Record payment in QuickBooks accounting system

**Input Schema:**
```python
class QuickBooksSyncInput(BaseModel):
    payment_id: str = Field(..., description="Payment ID")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    invoice_id: str | None = Field(None, description="Associated invoice ID")
    date: datetime = Field(..., description="Payment date")
    customer_id: str | None = Field(None, description="QuickBooks customer ID")
```

**Output Schema:**
```python
class QuickBooksSyncOutput(BaseModel):
    success: bool = Field(..., description="Whether sync succeeded")
    quickbooks_payment_id: str | None = Field(None, description="QuickBooks payment ID")
    error: str | None = Field(None, description="Error message if failed")
    retry_scheduled: bool = Field(default=False, description="Whether retry is scheduled")
```

**Error Handling:**
- Authentication error → Re-authenticate, then retry
- Rate limit (429) → Exponential backoff up to 1 hour
- Server error (5xx) → Retry 3x with backoff
- Network timeout → Retry with longer timeout
- Validation error → Log and alert ops team

**Implementation:**
```python
async def sync_to_quickbooks(self, payment_data: dict) -> dict:
    """Sync payment to QuickBooks with retry logic."""
    for attempt in range(self.max_retries):
        try:
            # Create payment in QuickBooks
            qb_payment = await self.quickbooks_client.create_payment({
                "customer_id": payment_data.get("customer_id"),
                "amount": payment_data["amount"],
                "currency": payment_data["currency"],
                "transaction_date": payment_data["date"],
                "reference_number": payment_data["payment_id"],
                "linked_invoices": [payment_data["invoice_id"]] if payment_data.get("invoice_id") else []
            })

            return {
                "success": True,
                "quickbooks_payment_id": qb_payment["id"],
                "error": None,
                "retry_scheduled": False
            }

        except Exception as e:
            is_last_attempt = attempt == self.max_retries - 1
            backoff_seconds = self.retry_backoff_base ** (attempt + 1)

            self.logger.warning(
                f"QuickBooks sync attempt {attempt + 1} failed",
                extra={
                    "payment_id": payment_data["payment_id"],
                    "error": str(e),
                    "retry_in_seconds": None if is_last_attempt else backoff_seconds
                }
            )

            if is_last_attempt:
                # Schedule async retry
                await self.schedule_quickbooks_retry(payment_data, attempt)
                return {
                    "success": False,
                    "quickbooks_payment_id": None,
                    "error": str(e),
                    "retry_scheduled": True
                }

            await asyncio.sleep(backoff_seconds)
```

### Tool: send_payment_notification
**Purpose:** Send payment-related emails to clients

**Input Schema:**
```python
class PaymentNotificationInput(BaseModel):
    type: Literal["payment_success", "payment_failed"] = Field(..., description="Notification type")
    client_email: str = Field(..., description="Client email address")
    amount: Decimal = Field(..., description="Payment amount")
    invoice_number: str = Field(..., description="Invoice number")
    receipt_link: str | None = Field(None, description="Payment receipt URL")
    payment_link: str | None = Field(None, description="Payment retry URL")
    failure_reason: str | None = Field(None, description="Payment failure reason")
    is_final: bool = Field(default=False, description="Is this final failure?")
```

**Output Schema:**
```python
class PaymentNotificationOutput(BaseModel):
    sent: bool = Field(..., description="Whether email was sent")
    message_id: str | None = Field(None, description="Email message ID")
    error: str | None = Field(None, description="Error if failed")
    retry_scheduled: bool = Field(default=False, description="Whether retry is scheduled")
```

**Email Templates:**

**Payment Success Template:**
```html
Subject: Payment received - Thank you!

Hi {{first_name}},

Thank you! We've received your payment of ${{amount}} for invoice {{invoice_number}}.

Receipt: {{receipt_link}}

We appreciate your business and will proceed with your project immediately.

Best regards,
The Smarter Team
```

**Payment Failed Template:**
```html
Subject: Payment issue - action required

Hi {{first_name}},

We tried to process your payment of ${{amount}} for invoice {{invoice_number}}, but it was declined.

{{#if is_final}}
After multiple attempts, we need your assistance to update your payment method.
{{else}}
This sometimes happens due to temporary bank holds. We'll automatically retry.
{{/if}}

Please update your payment method and try again: {{payment_link}}

{{#if failure_reason}}
Reason: {{failure_reason}}
{{/if}}

If you have any questions, just reply to this email.

Best regards,
The Smarter Team
```

---

## 5. Error Handling Matrix

| Error Type | Detection | Response | Retry Logic | Alert Level |
|------------|-----------|----------|-------------|-------------|
| Invalid webhook signature | Stripe verification fails | Reject with 401 | No | Critical (security) |
| Duplicate event | Event ID exists in DB | Return 200 success | No | Info |
| Database connection error | Exception on DB call | Retry 3x | Exponential backoff | High |
| Stripe API timeout | Request timeout | Process async | Retry 5x | Medium |
| QuickBooks auth error | 401/403 response | Re-authenticate | Yes | High |
| QuickBooks rate limit | 429 response | Backoff | Exponential, max 1hr | Low |
| Email send failure | SMTP exception | Retry 3x | Linear backoff | Medium |
| Dispute evidence missing | Check returns empty | Alert ops team | No | High |
| Payment amount mismatch | Validation fails | Flag for review | No | High |
| Webhook processing timeout | Processing takes >30s | Ack immediately, async process | N/A | Medium |

### Recovery Strategies

1. **Graceful Degradation:** If QuickBooks sync fails, payment is still processed and recorded locally
2. **Eventual Consistency:** Background jobs handle failed integrations
3. **Circuit Breaker:** Temporarily disable failing integrations after repeated failures
4. **Dead Letter Queue:** Unrecoverable errors go to manual review queue

---

## 6. Testing Strategy

### Unit Tests

```python
# Test webhook signature verification
async def test_verify_webhook_signature_valid():
    """Should return True for valid signature"""

async def test_verify_webhook_signature_invalid():
    """Should return False for invalid signature"""

async def test_verify_webhook_signature_expired():
    """Should reject expired timestamps"""

# Test duplicate prevention
async def test_check_event_processed_new():
    """Should return False for new event"""

async def test_check_event_processed_duplicate():
    """Should return True for processed event"""

# Test payment success handling
async def test_handle_payment_success_deposit():
    """Should trigger onboarding for deposit payment"""

async def test_handle_payment_success_milestone():
    """Should unlock next milestone"""

async def test_handle_payment_success_quickbooks_sync():
    """Should sync payment to QuickBooks"""

# Test payment failure handling
async def test_handle_payment_failure_retry():
    """Should send retry notification"""

async def test_handle_payment_failure_final():
    """Should escalate to human"""

# Test dispute handling
async def test_handle_dispute_pause_project():
    """Should immediately pause project work"""

async def test_handle_dispute_gather_evidence():
    """Should collect supporting documents"""

# Test error handling
async def test_database_connection_error():
    """Should retry with backoff"""

async def test_quickbooks_rate_limit():
    """Should implement exponential backoff"""
```

### Integration Tests

```python
# End-to-end webhook processing
async def test_webhook_end_to_end_success():
    """Full webhook flow with mocked Stripe"""

async def test_webhook_end_to_end_failure():
    """Full webhook flow with failure recovery"""

# External integrations
async def test_stripe_integration():
    """Real Stripe API calls (test mode)"""

async def test_quickbooks_integration():
    """Real QuickBooks API calls (sandbox)"""

async def test_email_delivery():
    """Real email sending (test addresses)"""

# Multi-agent coordination
async def test_payment_success_onboarding_trigger():
    """Verify onboarding agent receives handoff"""

async def test_dispute_project_pause():
    """Verify project management pauses work"
```

### Mock Strategy

```python
@pytest.fixture
def mock_stripe_client():
    with patch('src.integrations.stripe_client.StripeClient') as mock:
        mock.return_value.get_dispute.return_value = {
            "id": "dp_test",
            "reason": "duplicate",
            "evidence_details": {"due_by": time.time() + 86400}
        }
        yield mock

@pytest.fixture
def mock_quickbooks_client():
    with patch('src.integrations.quickbooks_client.QuickBooksClient') as mock:
        mock.return_value.create_payment.return_value = {
            "id": "qb_payment_test"
        }
        yield mock

@pytest.fixture
def mock_email_client():
    with patch('src.integrations.email_client.EmailClient') as mock:
        mock.return_value.send_email.return_value = {
            "message_id": "msg_test"
        }
        yield mock
```

### Performance Tests

- **Webhook Processing Time:** < 5 seconds average, < 30 seconds P99
- **Concurrent Webhooks:** Handle 100 simultaneous events
- **Database Throughput:** 1000+ payment records/second
- **API Rate Limits:** Respect Stripe/QuickBooks limits

---

## 7. Performance & Scalability

### Latency Requirements
- Webhook acknowledgment: < 1 second
- Payment processing: < 5 seconds average
- QuickBooks sync: < 30 seconds
- Email delivery: < 2 minutes

### Throughput Targets
- Webhook events: 1000/minute
- Database writes: 5000/second
- Email sends: 500/minute

### Caching Strategy
- Client details: Cache for 1 hour
- Invoice data: Cache for 30 minutes
- QuickBooks auth tokens: Cache until expiry

### Monitoring Metrics
- Webhook processing success rate: > 99.9%
- Average processing time: < 5 seconds
- QuickBooks sync success rate: > 99%
- Email delivery rate: > 99.5%

---

## 8. Security

### Webhook Security
- **Signature Verification:** Mandatory for all webhooks
- **Timestamp Validation:** Reject events > 5 minutes old
- **IP Whitelisting:** Restrict to Stripe IP ranges
- **Rate Limiting:** 100 webhooks/minute per source

### Data Protection
- **Encryption:** All data encrypted at rest and in transit
- **PII Handling:** Minimal data storage, automatic purging
- **Access Logs:** Complete audit trail of all access
- **PCI Compliance:** No card data stored (Stripe-only)

### API Security
- **Key Rotation:** Automated quarterly rotation
- **Least Privilege:** Minimal API permissions
- **Audit Logging:** All API calls logged
- **Secret Management:** Environment variables only

---

## 9. Observability

### Logging Requirements
```python
# Structured logging for all payment events
self.logger.info(
    "Payment processed",
    extra={
        "event_id": event_id,
        "payment_id": payment_id,
        "amount": float(amount),
        "currency": currency,
        "processing_time_ms": processing_time,
        "client_id": client_id,
        "actions_taken": actions
    }
)

# Security events
self.logger.warning(
    "Security violation detected",
    extra={
        "type": "invalid_webhook_signature",
        "source_ip": request_ip,
        "event_id": event_id,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

### Metrics to Track
- Webhook processing volume and success rate
- Payment processing latency distribution
- External API error rates and retry counts
- Email delivery success rate
- Dispute frequency and resolution time
- Revenue metrics (daily, weekly, monthly)

### Alerting Rules
- Webhook processing failure rate > 1%
- Payment processing time > 30 seconds (P95)
- QuickBooks sync failure rate > 5%
- Dispute count > 0 (immediate alert)
- Unusual payment patterns (ML-based detection)

---

## 10. Database Schema

### Payments Table
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_payment_id VARCHAR(255) UNIQUE NOT NULL,
    invoice_id UUID REFERENCES invoices(id),
    client_id UUID REFERENCES clients(id),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    status VARCHAR(20) NOT NULL,
    stripe_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);
```

### Payment Events Table
```sql
CREATE TABLE payment_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payment_id UUID REFERENCES payments(id),
    status VARCHAR(20) NOT NULL,
    processing_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);
```

### Payment Failures Table
```sql
CREATE TABLE payment_failures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID REFERENCES payments(id),
    failure_reason TEXT NOT NULL,
    failure_code VARCHAR(100),
    failure_count INTEGER NOT NULL,
    is_final BOOLEAN NOT NULL DEFAULT FALSE,
    stripe_failure_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Disputes Table
```sql
CREATE TABLE disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_dispute_id VARCHAR(255) UNIQUE NOT NULL,
    payment_id UUID REFERENCES payments(id),
    invoice_id UUID REFERENCES invoices(id),
    client_id UUID REFERENCES clients(id),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    reason VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'needs_response',
    evidence_due TIMESTAMP WITH TIME ZONE,
    evidence_documents JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);
```

### Indexes
```sql
CREATE INDEX idx_payments_stripe_id ON payments(stripe_payment_id);
CREATE INDEX idx_payments_invoice_id ON payments(invoice_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payment_events_stripe_id ON payment_events(stripe_event_id);
CREATE INDEX idx_payment_events_type ON payment_events(event_type);
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_disputes_evidence_due ON disputes(evidence_due);
```

---

## 11. Acceptance Criteria

### Functional Requirements
- [ ] Securely process all Stripe webhook events with signature verification
- [ ] Prevent duplicate event processing with idempotency
- [ ] Update payment records and client balances accurately
- [ ] Sync all payments to QuickBooks within 30 seconds
- [ ] Send appropriate email notifications for all payment events
- [ ] Pause projects immediately on disputes
- [ ] Trigger onboarding for successful deposit payments
- [ ] Generate comprehensive audit trails for all operations

### Security Requirements
- [ ] Verify all webhook signatures before processing
- [ ] Implement rate limiting for webhook endpoints
- [ ] Log all security events and violations
- [ ] Store no sensitive card data (PCI compliance)
- [ ] Use encrypted connections for all external APIs

### Performance Requirements
- [ ] Process webhooks in < 5 seconds average
- [ ] Handle 1000+ webhook events/minute
- [ ] Maintain 99.9% uptime for payment processing
- [ ] Complete QuickBooks sync within 30 seconds
- [ ] Send emails within 2 minutes of payment events

### Reliability Requirements
- [ ] No data loss during processing failures
- [ ] Automatic retry for all transient failures
- [ ] Graceful degradation when external services fail
- [ ] Complete audit trail for all payment operations
- [ ] Backup and recovery procedures for payment data

### Compliance Requirements
- [ ] PCI DSS compliance through Stripe integration
- [ ] GDPR compliance for EU client data
- [ ] Data retention policies for payment records
- [ ] Privacy policy compliance for client communications

---

## 12. Deployment Configuration

### Environment Variables
```bash
# Stripe Configuration
STRIPE_API_KEY=sk_live_...  # Production
STRIPE_WEBHOOK_SECRET=whsec_...  # Webhook signing secret

# QuickBooks Configuration
QUICKBOOKS_CLIENT_ID=...
QUICKBOOKS_CLIENT_SECRET=...
QUICKBOOKS_REDIRECT_URI=...
QUICKBOOKS_ENVIRONMENT=sandbox|production

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...

# Alerting
SLACK_WEBHOOK_URL=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Feature Flags
ENABLE_QUICKBOOKS_SYNC=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_PROJECT_AUTO_PAUSE=true
```

### Health Checks
```python
async def health_check():
    """Comprehensive health check for payment processing."""
    checks = {
        "database": await check_database_connection(),
        "stripe": await check_stripe_connectivity(),
        "quickbooks": await check_quickbooks_connectivity(),
        "email": await check_email_connectivity(),
        "redis": await check_redis_connection()
    }

    return {
        "status": "healthy" if all(checks.values()) else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## Implementation Priority

### Phase 1 (Core Functionality)
1. Webhook signature verification
2. Basic payment success/failure handling
3. Database updates and audit logging
4. Email notifications

### Phase 2 (Integrations)
5. QuickBooks synchronization
6. Multi-agent handoffs
7. Project pause on disputes
8. Evidence gathering

### Phase 3 (Enhancements)
9. Advanced retry logic
10. Performance optimizations
11. Comprehensive monitoring
12. Security hardening

This specification provides a complete blueprint for implementing a production-ready Payment Processing Agent that handles Stripe webhooks securely, reliably, and with comprehensive error handling and observability.
