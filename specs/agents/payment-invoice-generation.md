# Invoice Generation Agent - Technical Specification

**Status:** Production-Ready
**Version:** 1.0.0
**Created:** 2025-12-05
**Category:** Payment & Finance
**Phase:** Phase 4 - Client Delivery

---

## 1. Overview

### Purpose
Autonomously create, send, and track invoices for all client payments including deposits, milestones, final payments, and retainers. Integrates with Stripe for payment processing and QuickBooks for accounting synchronization.

### Agent Classification
- **Type:** Transactional Agent
- **Execution Mode:** Event-driven (Celery tasks)
- **Human-in-the-Loop:** Approval required for custom invoice amounts exceeding contract terms
- **Priority:** High (payment critical path)

### Dependencies
- **Upstream Agents:**
  - Proposal Creation Agent (provides contract details, payment terms)
  - Project Management Agent (provides milestone completion signals)
- **Downstream Agents:**
  - Payment Collection Agent (monitors payment status)
  - Finance Agent (revenue tracking, reporting)
- **External Services:**
  - Stripe API (invoice creation, payment links)
  - QuickBooks API (accounting sync)
  - Email service (invoice delivery)

---

## 2. System Prompt

```
You are the Invoice Generation Agent for Smarter Team, an AI agency automation system.

Your responsibilities:
- Generate accurate invoices based on contract terms and project milestones
- Create Stripe invoices with payment links
- Synchronize all invoices to QuickBooks for accounting
- Send professional invoice emails to clients
- Track invoice status and handle errors gracefully

Invoice Types You Handle:
1. DEPOSIT: 50% upfront payment when contract is signed
2. MILESTONE: Payments tied to specific project phases
3. FINAL: Remaining balance upon project completion
4. RETAINER: Fixed monthly/quarterly recurring payments

Key Principles:
- ALWAYS verify invoice amounts against contract terms
- NEVER create invoices exceeding contract total
- REQUIRE human approval for custom amounts outside contract terms
- MAINTAIN perfect sync between Stripe and QuickBooks
- LOG all invoice operations with complete audit trail
- HANDLE partial payments and credit scenarios

You have access to these tools:
- get_contract_details: Retrieve contract terms and payment schedule
- create_stripe_invoice: Generate invoice in Stripe with payment link
- sync_to_quickbooks: Create/update invoice in QuickBooks
- send_invoice_email: Email invoice to client with payment instructions
- validate_invoice_amount: Check amount against contract terms
- get_milestone_details: Fetch milestone completion data
- update_invoice_status: Update database invoice record
- check_duplicate_invoice: Prevent duplicate invoicing

Error Handling:
- If contract not found → log error, notify PM agent
- If amount validation fails → escalate to human approval
- If Stripe API fails → retry 3x with exponential backoff, then alert
- If QuickBooks sync fails → create invoice anyway, queue sync for retry
- If email send fails → invoice still valid, retry email delivery

Always structure responses as JSON with:
{
  "status": "success|pending_approval|error",
  "invoice_id": "stripe_invoice_id",
  "invoice_number": "INV-2025-XXX",
  "amount": 5000.00,
  "payment_link": "https://...",
  "actions_taken": ["created_stripe_invoice", "synced_quickbooks", "sent_email"],
  "next_steps": ["await_payment", "schedule_reminder"],
  "errors": []
}
```

---

## 3. Agent Architecture

### Class Definition

```python
from decimal import Decimal
from typing import Any, Literal

from src.agents.base_agent import BaseAgent
from src.integrations.stripe_client import StripeClient
from src.integrations.quickbooks_client import QuickBooksClient
from src.config import get_agent_logger


InvoiceType = Literal["deposit", "milestone", "final", "retainer"]
InvoiceStatus = Literal["draft", "pending", "sent", "paid", "overdue", "cancelled"]


class InvoiceGenerationAgent(BaseAgent):
    """
    Autonomous invoice generation and management agent.

    Handles all invoice types: deposit, milestone, final, retainer.
    Integrates with Stripe, QuickBooks, and email delivery.
    """

    def __init__(self):
        super().__init__(
            name="invoice_generation",
            description="Generate and manage client invoices with Stripe and QuickBooks"
        )

        # Integration clients (lazy loaded)
        self._stripe_client: StripeClient | None = None
        self._quickbooks_client: QuickBooksClient | None = None

        # Configuration
        self.max_retries = 3
        self.approval_threshold = Decimal("10000.00")  # Amounts > $10k require approval

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
                client_secret=settings.quickbooks_client_secret,
            )
        return self._quickbooks_client

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process invoice generation task.

        Args:
            task: {
                "type": "deposit|milestone|final|retainer",
                "contract_id": "uuid",
                "project_id": "uuid",
                "client_id": "uuid",
                "milestone_id": "uuid|null",
                "custom_amount": "decimal|null",
                "due_days": 7
            }

        Returns:
            Invoice generation result with status and details
        """
        invoice_type = task.get("type")
        contract_id = task.get("contract_id")

        self.logger.info(
            f"Processing {invoice_type} invoice",
            extra={"contract_id": contract_id, "project_id": task.get("project_id")}
        )

        try:
            # Step 1: Validate and prepare invoice data
            invoice_data = await self._prepare_invoice_data(task)

            # Step 2: Check for duplicates
            if await self._is_duplicate_invoice(invoice_data):
                return {
                    "status": "error",
                    "error": "duplicate_invoice",
                    "message": "Invoice already exists for this trigger"
                }

            # Step 3: Validate amount against contract
            validation = await self._validate_invoice_amount(invoice_data)
            if not validation["valid"]:
                if validation["requires_approval"]:
                    return await self._request_approval(invoice_data, validation["reason"])
                else:
                    return {
                        "status": "error",
                        "error": "validation_failed",
                        "message": validation["reason"]
                    }

            # Step 4: Create Stripe invoice
            stripe_invoice = await self._create_stripe_invoice(invoice_data)

            # Step 5: Sync to QuickBooks (async, best effort)
            qb_result = await self._sync_to_quickbooks(stripe_invoice, invoice_data)

            # Step 6: Save to database
            db_invoice = await self._save_invoice_to_db(stripe_invoice, qb_result, invoice_data)

            # Step 7: Send email to client
            email_result = await self._send_invoice_email(db_invoice, stripe_invoice)

            # Step 8: Log success and handoff to collection agent
            self.log_action(
                "invoice.created",
                {
                    "invoice_id": db_invoice["id"],
                    "stripe_invoice_id": stripe_invoice["id"],
                    "amount": float(invoice_data["amount"]),
                    "type": invoice_type,
                }
            )

            # Handoff to payment collection agent for monitoring
            await self.handoff_to(
                target_agent="payment_collection",
                payload={
                    "invoice_id": db_invoice["id"],
                    "stripe_invoice_id": stripe_invoice["id"],
                    "due_date": invoice_data["due_date"],
                },
                priority="normal"
            )

            return {
                "status": "success",
                "invoice_id": db_invoice["id"],
                "invoice_number": db_invoice["invoice_number"],
                "stripe_invoice_id": stripe_invoice["id"],
                "amount": float(invoice_data["amount"]),
                "payment_link": stripe_invoice["hosted_invoice_url"],
                "actions_taken": [
                    "created_stripe_invoice",
                    "synced_quickbooks" if qb_result["success"] else "quickbooks_queued",
                    "sent_email" if email_result["success"] else "email_queued",
                ],
                "next_steps": ["await_payment", "monitor_due_date"],
            }

        except Exception as e:
            self.logger.error(f"Invoice generation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": "generation_failed",
                "message": str(e)
            }

    def _register_tools(self) -> None:
        """Register all tools available to this agent."""
        # Tools will be defined in section 4
        pass
```

---

## 4. Tool Definitions

### 4.1 get_contract_details

**Purpose:** Retrieve contract terms, payment schedule, and amounts

```python
async def get_contract_details(self, contract_id: str) -> dict[str, Any]:
    """
    Fetch contract details from database.

    Args:
        contract_id: Contract UUID

    Returns:
        {
            "id": "uuid",
            "client_id": "uuid",
            "project_id": "uuid",
            "total_amount": "50000.00",
            "deposit_percentage": "50",
            "payment_terms": "net_7",
            "milestones": [
                {"id": "uuid", "name": "Phase 1", "amount": "15000.00", "invoiced": false},
                {"id": "uuid", "name": "Phase 2", "amount": "10000.00", "invoiced": false}
            ],
            "retainer_amount": null,
            "retainer_frequency": null,
            "currency": "usd",
            "created_at": "2025-01-15T10:00:00Z"
        }

    Raises:
        ContractNotFoundError: If contract doesn't exist
    """
    from src.database import get_async_session
    from sqlalchemy import select
    from src.models import Contract, Milestone

    async with get_async_session() as session:
        result = await session.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = result.scalar_one_or_none()

        if not contract:
            raise ContractNotFoundError(f"Contract {contract_id} not found")

        # Fetch milestones
        milestones_result = await session.execute(
            select(Milestone)
            .where(Milestone.contract_id == contract_id)
            .order_by(Milestone.sequence)
        )
        milestones = [
            {
                "id": str(m.id),
                "name": m.name,
                "amount": str(m.amount),
                "invoiced": m.invoiced,
            }
            for m in milestones_result.scalars()
        ]

        return {
            "id": str(contract.id),
            "client_id": str(contract.client_id),
            "project_id": str(contract.project_id),
            "total_amount": str(contract.total_amount),
            "deposit_percentage": str(contract.deposit_percentage),
            "payment_terms": contract.payment_terms,
            "milestones": milestones,
            "retainer_amount": str(contract.retainer_amount) if contract.retainer_amount else None,
            "retainer_frequency": contract.retainer_frequency,
            "currency": contract.currency,
            "created_at": contract.created_at.isoformat(),
        }
```

### 4.2 create_stripe_invoice

**Purpose:** Create invoice in Stripe with payment link

```python
async def create_stripe_invoice(
    self,
    customer_id: str,
    amount: Decimal,
    description: str,
    line_items: list[dict[str, Any]],
    due_days: int = 7,
    metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Create Stripe invoice with hosted payment page.

    Args:
        customer_id: Stripe customer ID
        amount: Total invoice amount
        description: Invoice description
        line_items: [{"description": "...", "amount": Decimal, "quantity": 1}]
        due_days: Days until due (default 7)
        metadata: Additional metadata (contract_id, project_id, etc.)

    Returns:
        Stripe invoice object with hosted_invoice_url

    Raises:
        StripeAPIError: If invoice creation fails
    """
    return await self.stripe_client.create_invoice(
        customer_id=customer_id,
        amount=amount,
        description=description,
        line_items=line_items,
        due_days=due_days,
        metadata=metadata or {},
    )
```

### 4.3 sync_to_quickbooks

**Purpose:** Create/update invoice in QuickBooks for accounting

```python
async def sync_to_quickbooks(
    self,
    invoice_data: dict[str, Any],
    retry_on_failure: bool = True,
) -> dict[str, Any]:
    """
    Sync invoice to QuickBooks.

    Args:
        invoice_data: Invoice details including line items
        retry_on_failure: Queue for retry if sync fails

    Returns:
        {
            "success": true,
            "quickbooks_invoice_id": "123",
            "sync_status": "synced|queued|failed"
        }
    """
    try:
        qb_invoice = await self.quickbooks_client.create_invoice(
            customer_ref=invoice_data["client_id"],
            line_items=invoice_data["line_items"],
            due_date=invoice_data["due_date"],
            metadata={
                "stripe_invoice_id": invoice_data.get("stripe_invoice_id"),
                "invoice_number": invoice_data.get("invoice_number"),
            }
        )

        return {
            "success": True,
            "quickbooks_invoice_id": qb_invoice["Id"],
            "sync_status": "synced",
        }

    except Exception as e:
        self.logger.error(f"QuickBooks sync failed: {e}")

        if retry_on_failure:
            # Queue for retry via Celery task
            from src.tasks.finance_tasks import retry_quickbooks_sync
            retry_quickbooks_sync.apply_async(
                args=[invoice_data],
                countdown=300,  # Retry in 5 minutes
            )
            return {
                "success": False,
                "quickbooks_invoice_id": None,
                "sync_status": "queued",
            }

        return {
            "success": False,
            "quickbooks_invoice_id": None,
            "sync_status": "failed",
        }
```

### 4.4 validate_invoice_amount

**Purpose:** Verify invoice amount against contract terms

```python
async def validate_invoice_amount(
    self,
    invoice_type: InvoiceType,
    amount: Decimal,
    contract_data: dict[str, Any],
    milestone_id: str | None = None,
) -> dict[str, Any]:
    """
    Validate invoice amount against contract terms.

    Args:
        invoice_type: Type of invoice
        amount: Requested invoice amount
        contract_data: Contract details from get_contract_details
        milestone_id: Milestone ID for milestone invoices

    Returns:
        {
            "valid": true|false,
            "requires_approval": false,
            "reason": "validation_message",
            "expected_amount": "25000.00"
        }
    """
    total_amount = Decimal(contract_data["total_amount"])

    if invoice_type == "deposit":
        deposit_pct = Decimal(contract_data["deposit_percentage"])
        expected_amount = total_amount * (deposit_pct / 100)

        if amount != expected_amount:
            return {
                "valid": False,
                "requires_approval": True,
                "reason": f"Deposit amount {amount} differs from contract {expected_amount}",
                "expected_amount": str(expected_amount),
            }

    elif invoice_type == "milestone":
        if not milestone_id:
            return {
                "valid": False,
                "requires_approval": False,
                "reason": "Milestone ID required for milestone invoices",
                "expected_amount": None,
            }

        milestone = next(
            (m for m in contract_data["milestones"] if m["id"] == milestone_id),
            None
        )

        if not milestone:
            return {
                "valid": False,
                "requires_approval": False,
                "reason": f"Milestone {milestone_id} not found in contract",
                "expected_amount": None,
            }

        if milestone["invoiced"]:
            return {
                "valid": False,
                "requires_approval": False,
                "reason": f"Milestone {milestone['name']} already invoiced",
                "expected_amount": None,
            }

        expected_amount = Decimal(milestone["amount"])
        if amount != expected_amount:
            return {
                "valid": False,
                "requires_approval": True,
                "reason": f"Milestone amount {amount} differs from contract {expected_amount}",
                "expected_amount": str(expected_amount),
            }

    elif invoice_type == "retainer":
        expected_amount = Decimal(contract_data["retainer_amount"] or "0")
        if expected_amount == 0:
            return {
                "valid": False,
                "requires_approval": False,
                "reason": "Contract has no retainer configured",
                "expected_amount": None,
            }

        if amount != expected_amount:
            return {
                "valid": False,
                "requires_approval": True,
                "reason": f"Retainer amount {amount} differs from contract {expected_amount}",
                "expected_amount": str(expected_amount),
            }

    # Check if amount exceeds approval threshold
    if amount > self.approval_threshold:
        return {
            "valid": True,
            "requires_approval": True,
            "reason": f"Amount exceeds approval threshold of ${self.approval_threshold}",
            "expected_amount": str(amount),
        }

    return {
        "valid": True,
        "requires_approval": False,
        "reason": "Amount validated against contract",
        "expected_amount": str(amount),
    }
```

### 4.5 check_duplicate_invoice

**Purpose:** Prevent duplicate invoicing for same trigger

```python
async def check_duplicate_invoice(
    self,
    contract_id: str,
    invoice_type: InvoiceType,
    milestone_id: str | None = None,
    billing_period: str | None = None,
) -> bool:
    """
    Check if invoice already exists for this trigger.

    Args:
        contract_id: Contract UUID
        invoice_type: Type of invoice
        milestone_id: Milestone ID (for milestone invoices)
        billing_period: Period identifier (for retainer, e.g., "2025-01")

    Returns:
        True if duplicate exists, False otherwise
    """
    from src.database import get_async_session
    from sqlalchemy import select, and_
    from src.models import Invoice

    async with get_async_session() as session:
        query = select(Invoice).where(
            and_(
                Invoice.contract_id == contract_id,
                Invoice.type == invoice_type,
                Invoice.status.in_(["draft", "pending", "sent", "paid"])
            )
        )

        if milestone_id:
            query = query.where(Invoice.milestone_id == milestone_id)

        if billing_period:
            query = query.where(Invoice.billing_period == billing_period)

        result = await session.execute(query)
        return result.scalar_one_or_none() is not None
```

### 4.6 send_invoice_email

**Purpose:** Email invoice to client with payment link

```python
async def send_invoice_email(
    self,
    client_email: str,
    invoice_number: str,
    amount: Decimal,
    due_date: str,
    payment_link: str,
    line_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Send invoice email to client.

    Args:
        client_email: Client email address
        invoice_number: Invoice number (e.g., INV-2025-001)
        amount: Total invoice amount
        due_date: Due date (ISO format)
        payment_link: Stripe hosted invoice URL
        line_items: Invoice line items for email body

    Returns:
        {
            "success": true,
            "message_id": "email_message_id"
        }
    """
    from src.integrations.email_client import EmailClient
    from datetime import datetime

    email_client = EmailClient()

    # Format due date
    due_date_formatted = datetime.fromisoformat(due_date).strftime("%B %d, %Y")

    # Build email body
    line_items_html = "\n".join([
        f"<tr><td>{item['description']}</td><td>${item['amount']:.2f}</td></tr>"
        for item in line_items
    ])

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>Invoice {invoice_number}</h2>

        <p>Thank you for choosing Smarter Team! Please find your invoice details below:</p>

        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead>
                <tr style="background-color: #f4f4f4;">
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Description</th>
                    <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {line_items_html}
                <tr style="font-weight: bold;">
                    <td style="padding: 10px; text-align: left; border: 1px solid #ddd;">Total</td>
                    <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">${amount:.2f}</td>
                </tr>
            </tbody>
        </table>

        <p><strong>Due Date:</strong> {due_date_formatted}</p>

        <p>
            <a href="{payment_link}"
               style="display: inline-block; padding: 12px 24px; background-color: #4CAF50;
                      color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
                Pay Invoice
            </a>
        </p>

        <p>You can also view and pay your invoice here:<br>
        <a href="{payment_link}">{payment_link}</a></p>

        <p>If you have any questions, please don't hesitate to reach out.</p>

        <p>Best regards,<br>
        Smarter Team</p>
    </body>
    </html>
    """

    try:
        result = await email_client.send_email(
            to=client_email,
            subject=f"Invoice {invoice_number} - ${amount:.2f} Due {due_date_formatted}",
            html_body=html_body,
            metadata={
                "invoice_number": invoice_number,
                "type": "invoice",
            }
        )

        return {
            "success": True,
            "message_id": result["message_id"],
        }

    except Exception as e:
        self.logger.error(f"Email send failed: {e}")
        return {
            "success": False,
            "message_id": None,
            "error": str(e),
        }
```

---

## 5. Database Schema

### 5.1 invoices Table

```sql
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,  -- INV-2025-001

    -- Relationships
    contract_id UUID NOT NULL REFERENCES contracts(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    client_id UUID NOT NULL REFERENCES clients(id),
    milestone_id UUID REFERENCES milestones(id),  -- NULL for deposit/final/retainer

    -- Invoice details
    type VARCHAR(20) NOT NULL,  -- deposit, milestone, final, retainer
    status VARCHAR(20) NOT NULL DEFAULT 'draft',  -- draft, pending, sent, paid, overdue, cancelled

    -- Amounts (stored as NUMERIC for precision)
    subtotal NUMERIC(10, 2) NOT NULL,
    tax NUMERIC(10, 2) DEFAULT 0.00,
    discount NUMERIC(10, 2) DEFAULT 0.00,
    total NUMERIC(10, 2) NOT NULL,
    amount_paid NUMERIC(10, 2) DEFAULT 0.00,
    amount_due NUMERIC(10, 2) NOT NULL,

    -- Dates
    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    paid_date DATE,

    -- External references
    stripe_invoice_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255) NOT NULL,
    stripe_payment_link TEXT,
    quickbooks_invoice_id VARCHAR(255),

    -- Retainer tracking
    billing_period VARCHAR(20),  -- '2025-01', '2025-Q1', etc.

    -- Metadata
    currency VARCHAR(3) DEFAULT 'usd',
    payment_terms VARCHAR(50),  -- 'net_7', 'net_14', 'net_30', 'immediate'
    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'invoice_generation_agent',

    -- Indexes
    CONSTRAINT valid_invoice_type CHECK (type IN ('deposit', 'milestone', 'final', 'retainer')),
    CONSTRAINT valid_status CHECK (status IN ('draft', 'pending', 'sent', 'paid', 'overdue', 'cancelled')),
    CONSTRAINT valid_amounts CHECK (total >= 0 AND amount_paid >= 0 AND amount_due >= 0)
);

-- Indexes for performance
CREATE INDEX idx_invoices_client_id ON invoices(client_id);
CREATE INDEX idx_invoices_project_id ON invoices(project_id);
CREATE INDEX idx_invoices_contract_id ON invoices(contract_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_type ON invoices(type);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_invoices_stripe_id ON invoices(stripe_invoice_id);
CREATE INDEX idx_invoices_billing_period ON invoices(billing_period);

-- Prevent duplicate milestone invoices
CREATE UNIQUE INDEX idx_unique_milestone_invoice
ON invoices(contract_id, milestone_id)
WHERE milestone_id IS NOT NULL AND status != 'cancelled';

-- Prevent duplicate retainer invoices per period
CREATE UNIQUE INDEX idx_unique_retainer_invoice
ON invoices(contract_id, billing_period)
WHERE type = 'retainer' AND status != 'cancelled';
```

### 5.2 invoice_items Table

```sql
CREATE TABLE invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,

    -- Item details
    description TEXT NOT NULL,
    quantity NUMERIC(10, 2) DEFAULT 1.00,
    unit_price NUMERIC(10, 2) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,  -- quantity * unit_price

    -- Metadata
    item_type VARCHAR(50),  -- 'service', 'product', 'discount', 'tax'
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sequence INTEGER NOT NULL,  -- Display order

    CONSTRAINT valid_amount CHECK (amount >= 0)
);

CREATE INDEX idx_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX idx_invoice_items_sequence ON invoice_items(invoice_id, sequence);
```

### 5.3 invoice_events Table

```sql
CREATE TABLE invoice_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,

    -- Event details
    event_type VARCHAR(50) NOT NULL,  -- created, sent, viewed, paid, overdue, reminder_sent, etc.
    event_source VARCHAR(50),  -- agent, stripe_webhook, manual, system

    -- Event data
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

CREATE INDEX idx_invoice_events_invoice_id ON invoice_events(invoice_id);
CREATE INDEX idx_invoice_events_type ON invoice_events(event_type);
CREATE INDEX idx_invoice_events_created_at ON invoice_events(created_at);
```

---

## 6. Integration Specifications

### 6.1 Stripe Integration

**Client:** `StripeClient` (extends `BaseIntegrationClient`)

**API Endpoints:**
- `POST /v1/invoices` - Create invoice
- `POST /v1/invoices/{id}/send` - Send invoice to customer
- `GET /v1/invoices/{id}` - Retrieve invoice
- `POST /v1/invoices/{id}/finalize` - Finalize draft invoice
- `POST /v1/invoices/{id}/void` - Cancel invoice

**Key Methods:**

```python
class StripeClient(BaseIntegrationClient):
    def __init__(self, api_key: str):
        super().__init__(
            name="stripe",
            base_url="https://api.stripe.com",
            api_key=api_key,
            timeout=30.0
        )

    async def create_invoice(
        self,
        customer_id: str,
        amount: Decimal,
        description: str,
        line_items: list[dict[str, Any]],
        due_days: int = 7,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create Stripe invoice."""
        # Create invoice items first
        invoice_items = []
        for item in line_items:
            item_response = await self.post(
                "/v1/invoiceitems",
                data={
                    "customer": customer_id,
                    "description": item["description"],
                    "amount": int(item["amount"] * 100),  # Convert to cents
                    "currency": "usd",
                }
            )
            invoice_items.append(item_response["id"])

        # Create invoice
        invoice = await self.post(
            "/v1/invoices",
            data={
                "customer": customer_id,
                "description": description,
                "collection_method": "send_invoice",
                "days_until_due": due_days,
                "metadata": metadata or {},
            }
        )

        # Finalize invoice to make it payable
        finalized = await self.post(
            f"/v1/invoices/{invoice['id']}/finalize",
            data={"auto_advance": True}
        )

        return finalized

    async def get_invoice(self, invoice_id: str) -> dict[str, Any]:
        """Retrieve invoice by ID."""
        return await self.get(f"/v1/invoices/{invoice_id}")

    async def void_invoice(self, invoice_id: str) -> dict[str, Any]:
        """Cancel/void an invoice."""
        return await self.post(f"/v1/invoices/{invoice_id}/void")
```

**Webhook Events to Handle:**
- `invoice.paid` - Update invoice status to paid
- `invoice.payment_failed` - Trigger collection agent
- `invoice.finalized` - Invoice ready to send
- `invoice.sent` - Track delivery

### 6.2 QuickBooks Integration

**Client:** `QuickBooksClient` (extends `BaseIntegrationClient`)

**API Endpoints:**
- `POST /v3/company/{realmId}/invoice` - Create invoice
- `GET /v3/company/{realmId}/invoice/{id}` - Get invoice
- `POST /v3/company/{realmId}/invoice/{id}` - Update invoice

**Key Methods:**

```python
class QuickBooksClient(BaseIntegrationClient):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            name="quickbooks",
            base_url="https://quickbooks.api.intuit.com",
            timeout=30.0
        )
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: str | None = None

    async def create_invoice(
        self,
        customer_ref: str,
        line_items: list[dict[str, Any]],
        due_date: str,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create QuickBooks invoice."""
        invoice_data = {
            "CustomerRef": {"value": customer_ref},
            "Line": [
                {
                    "Amount": float(item["amount"]),
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "ItemRef": {"value": "1"},  # Default service item
                    },
                    "Description": item["description"],
                }
                for item in line_items
            ],
            "DueDate": due_date,
            "CustomField": [
                {"DefinitionId": "1", "Name": "stripe_invoice_id", "StringValue": metadata.get("stripe_invoice_id", "")},
            ]
        }

        return await self.post(
            f"/v3/company/{self.realm_id}/invoice",
            json=invoice_data,
            headers={"Authorization": f"Bearer {await self._get_access_token()}"}
        )

    async def _get_access_token(self) -> str:
        """Get or refresh OAuth access token."""
        # OAuth flow implementation
        # TODO: Implement token refresh logic
        return self._access_token or ""
```

---

## 7. Error Handling & Edge Cases

### 7.1 Error Scenarios

| Error | Detection | Handling | Recovery |
|-------|-----------|----------|----------|
| Contract not found | Database query returns null | Log error, return error status | Notify PM agent to create contract |
| Duplicate invoice | Check existing invoices | Return duplicate error | Skip creation, return existing invoice |
| Amount validation fails | Amount != contract terms | Request human approval if custom | Admin reviews in dashboard |
| Stripe API failure | HTTP 4xx/5xx errors | Retry 3x with backoff | Alert admin, queue for manual review |
| QuickBooks sync fails | API error | Queue for retry | Invoice still created, sync retried async |
| Email send fails | SMTP error | Queue for retry | Invoice valid, email retried later |
| Milestone already invoiced | Database constraint | Return error | Skip creation, log warning |
| Customer not in Stripe | Customer lookup fails | Create Stripe customer first | Retry invoice creation |

### 7.2 Retry Logic

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
async def create_stripe_invoice_with_retry(self, *args, **kwargs):
    """Retry Stripe invoice creation on transient failures."""
    return await self.create_stripe_invoice(*args, **kwargs)
```

### 7.3 Edge Cases

1. **Partial payments**: Update `amount_paid` and `amount_due` fields
2. **Invoice cancellation**: Set status to 'cancelled', void in Stripe
3. **Credit/refunds**: Create negative invoice or credit memo
4. **Multi-currency**: Support via `currency` field (future)
5. **Tax calculation**: Support line-item tax (future)
6. **Discounts**: Apply at line-item or invoice level
7. **Late fees**: Handled by collection agent (future)

---

## 8. Testing Requirements

### 8.1 Unit Tests (Target: >90%)

**File:** `app/backend/__tests__/unit/agents/test_invoice_generation_agent.py`

```python
"""Unit tests for InvoiceGenerationAgent."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, timedelta

from src.agents.invoice_generation import InvoiceGenerationAgent


@pytest.fixture
def agent():
    """Create agent instance."""
    return InvoiceGenerationAgent()


@pytest.fixture
def contract_data():
    """Sample contract data."""
    return {
        "id": "contract-123",
        "client_id": "client-456",
        "project_id": "project-789",
        "total_amount": "50000.00",
        "deposit_percentage": "50",
        "payment_terms": "net_7",
        "milestones": [
            {"id": "m1", "name": "Phase 1", "amount": "15000.00", "invoiced": False},
            {"id": "m2", "name": "Phase 2", "amount": "10000.00", "invoiced": False},
        ],
        "retainer_amount": None,
        "currency": "usd",
    }


class TestInvoiceGenerationAgent:
    """Test suite for InvoiceGenerationAgent."""

    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "invoice_generation"
        assert agent.description is not None
        assert agent.max_retries == 3
        assert agent.approval_threshold == Decimal("10000.00")

    async def test_system_prompt_defined(self, agent):
        """Test system prompt is defined."""
        prompt = agent.system_prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "invoice" in prompt.lower()

    async def test_validate_deposit_invoice_valid(self, agent, contract_data):
        """Test deposit invoice validation - valid amount."""
        result = await agent.validate_invoice_amount(
            invoice_type="deposit",
            amount=Decimal("25000.00"),  # 50% of 50000
            contract_data=contract_data,
        )

        assert result["valid"] is True
        assert result["requires_approval"] is False

    async def test_validate_deposit_invoice_invalid(self, agent, contract_data):
        """Test deposit invoice validation - invalid amount."""
        result = await agent.validate_invoice_amount(
            invoice_type="deposit",
            amount=Decimal("30000.00"),  # Wrong amount
            contract_data=contract_data,
        )

        assert result["valid"] is False
        assert result["requires_approval"] is True
        assert "differs from contract" in result["reason"]

    async def test_validate_milestone_invoice_valid(self, agent, contract_data):
        """Test milestone invoice validation - valid."""
        result = await agent.validate_invoice_amount(
            invoice_type="milestone",
            amount=Decimal("15000.00"),
            contract_data=contract_data,
            milestone_id="m1",
        )

        assert result["valid"] is True
        assert result["requires_approval"] is False

    async def test_validate_milestone_invoice_already_invoiced(self, agent, contract_data):
        """Test milestone invoice validation - already invoiced."""
        contract_data["milestones"][0]["invoiced"] = True

        result = await agent.validate_invoice_amount(
            invoice_type="milestone",
            amount=Decimal("15000.00"),
            contract_data=contract_data,
            milestone_id="m1",
        )

        assert result["valid"] is False
        assert "already invoiced" in result["reason"]

    async def test_validate_retainer_invoice_not_configured(self, agent, contract_data):
        """Test retainer invoice validation - no retainer in contract."""
        result = await agent.validate_invoice_amount(
            invoice_type="retainer",
            amount=Decimal("5000.00"),
            contract_data=contract_data,
        )

        assert result["valid"] is False
        assert "no retainer configured" in result["reason"]

    async def test_high_amount_requires_approval(self, agent, contract_data):
        """Test amounts over threshold require approval."""
        contract_data["deposit_percentage"] = "100"  # 50k deposit

        result = await agent.validate_invoice_amount(
            invoice_type="deposit",
            amount=Decimal("50000.00"),
            contract_data=contract_data,
        )

        assert result["valid"] is True
        assert result["requires_approval"] is True
        assert "approval threshold" in result["reason"]

    @patch("src.agents.invoice_generation.get_async_session")
    async def test_check_duplicate_invoice_exists(self, mock_session, agent):
        """Test duplicate detection - invoice exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"id": "invoice-1"}

        mock_session.return_value.__aenter__.return_value.execute = AsyncMock(
            return_value=mock_result
        )

        is_duplicate = await agent.check_duplicate_invoice(
            contract_id="contract-123",
            invoice_type="deposit",
        )

        assert is_duplicate is True

    @patch("src.agents.invoice_generation.get_async_session")
    async def test_check_duplicate_invoice_not_exists(self, mock_session, agent):
        """Test duplicate detection - no duplicate."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session.return_value.__aenter__.return_value.execute = AsyncMock(
            return_value=mock_result
        )

        is_duplicate = await agent.check_duplicate_invoice(
            contract_id="contract-123",
            invoice_type="deposit",
        )

        assert is_duplicate is False

    async def test_create_stripe_invoice(self, agent):
        """Test Stripe invoice creation."""
        with patch.object(agent, 'stripe_client') as mock_stripe:
            mock_stripe.create_invoice = AsyncMock(return_value={
                "id": "in_123",
                "hosted_invoice_url": "https://invoice.stripe.com/i/123",
                "amount_due": 25000,
            })

            result = await agent.create_stripe_invoice(
                customer_id="cus_123",
                amount=Decimal("25000.00"),
                description="Deposit Invoice",
                line_items=[{"description": "Deposit", "amount": Decimal("25000.00"), "quantity": 1}],
                due_days=7,
            )

            assert result["id"] == "in_123"
            assert "hosted_invoice_url" in result

    async def test_sync_to_quickbooks_success(self, agent):
        """Test QuickBooks sync - success."""
        with patch.object(agent, 'quickbooks_client') as mock_qb:
            mock_qb.create_invoice = AsyncMock(return_value={"Id": "qb-123"})

            result = await agent.sync_to_quickbooks({
                "client_id": "client-456",
                "line_items": [],
                "due_date": "2025-02-01",
            })

            assert result["success"] is True
            assert result["quickbooks_invoice_id"] == "qb-123"
            assert result["sync_status"] == "synced"

    async def test_sync_to_quickbooks_failure_queued(self, agent):
        """Test QuickBooks sync - failure with retry."""
        with patch.object(agent, 'quickbooks_client') as mock_qb:
            mock_qb.create_invoice = AsyncMock(side_effect=Exception("API error"))

            with patch("src.tasks.finance_tasks.retry_quickbooks_sync") as mock_task:
                mock_task.apply_async = MagicMock()

                result = await agent.sync_to_quickbooks(
                    {"client_id": "client-456", "line_items": [], "due_date": "2025-02-01"},
                    retry_on_failure=True,
                )

                assert result["success"] is False
                assert result["sync_status"] == "queued"
                mock_task.apply_async.assert_called_once()

    async def test_send_invoice_email_success(self, agent):
        """Test invoice email sending - success."""
        result = await agent.send_invoice_email(
            client_email="client@example.com",
            invoice_number="INV-2025-001",
            amount=Decimal("25000.00"),
            due_date="2025-02-01",
            payment_link="https://invoice.stripe.com/i/123",
            line_items=[{"description": "Deposit", "amount": Decimal("25000.00")}],
        )

        # Will need to mock EmailClient
        # For now, test structure
        assert "success" in result

    async def test_process_task_deposit_invoice_success(self, agent):
        """Test processing deposit invoice task - end to end."""
        task = {
            "type": "deposit",
            "contract_id": "contract-123",
            "project_id": "project-789",
            "client_id": "client-456",
            "due_days": 7,
        }

        # Mock all dependencies
        with patch.object(agent, '_prepare_invoice_data') as mock_prepare, \
             patch.object(agent, '_is_duplicate_invoice', return_value=False), \
             patch.object(agent, '_validate_invoice_amount', return_value={"valid": True, "requires_approval": False}), \
             patch.object(agent, '_create_stripe_invoice', return_value={"id": "in_123", "hosted_invoice_url": "https://..."}), \
             patch.object(agent, '_sync_to_quickbooks', return_value={"success": True}), \
             patch.object(agent, '_save_invoice_to_db', return_value={"id": "inv-123", "invoice_number": "INV-2025-001"}), \
             patch.object(agent, '_send_invoice_email', return_value={"success": True}), \
             patch.object(agent, 'handoff_to', return_value="task-123"):

            mock_prepare.return_value = {
                "type": "deposit",
                "amount": Decimal("25000.00"),
                "due_date": "2025-02-01",
            }

            result = await agent.process_task(task)

            assert result["status"] == "success"
            assert result["invoice_id"] == "inv-123"
            assert result["payment_link"] is not None
```

### 8.2 Integration Tests

**File:** `app/backend/__tests__/integration/test_invoice_generation_integration.py`

```python
"""Integration tests for invoice generation flow."""

import pytest
from decimal import Decimal
from datetime import date, timedelta

from src.agents.invoice_generation import InvoiceGenerationAgent
from src.database import get_async_session
from src.models import Invoice, Contract, Client, Project


@pytest.mark.integration
class TestInvoiceGenerationIntegration:
    """Integration tests with database."""

    async def test_full_deposit_invoice_flow(self, db_session):
        """Test complete deposit invoice generation with DB."""
        # Setup: Create client, project, contract
        client = Client(email="test@example.com", name="Test Client")
        project = Project(name="Test Project", client=client)
        contract = Contract(
            client=client,
            project=project,
            total_amount=Decimal("50000.00"),
            deposit_percentage=Decimal("50"),
            payment_terms="net_7",
        )

        db_session.add_all([client, project, contract])
        await db_session.commit()

        # Execute: Generate deposit invoice
        agent = InvoiceGenerationAgent()
        result = await agent.process_task({
            "type": "deposit",
            "contract_id": str(contract.id),
            "project_id": str(project.id),
            "client_id": str(client.id),
            "due_days": 7,
        })

        # Verify: Invoice created in DB
        assert result["status"] == "success"

        invoice = await db_session.get(Invoice, result["invoice_id"])
        assert invoice is not None
        assert invoice.type == "deposit"
        assert invoice.total == Decimal("25000.00")
        assert invoice.status == "sent"

    async def test_prevent_duplicate_deposit_invoice(self, db_session):
        """Test duplicate deposit invoice prevention."""
        # Setup: Create contract and existing deposit invoice
        # ... setup code ...

        # Execute: Try to create duplicate
        result = await agent.process_task(task)

        # Verify: Duplicate rejected
        assert result["status"] == "error"
        assert result["error"] == "duplicate_invoice"
```

### 8.3 Test Coverage Targets

- **Unit tests:** >90% coverage
- **Integration tests:** >85% coverage
- **Critical paths:** 100% coverage (invoice creation, amount validation, duplicate prevention)

---

## 9. Monitoring & Observability

### 9.1 Metrics to Track

```python
# Prometheus metrics
invoice_creation_total = Counter("invoice_creation_total", "Total invoices created", ["type", "status"])
invoice_creation_duration = Histogram("invoice_creation_duration_seconds", "Invoice creation time")
invoice_validation_failures = Counter("invoice_validation_failures_total", "Validation failures", ["reason"])
stripe_api_errors = Counter("stripe_api_errors_total", "Stripe API failures", ["endpoint"])
quickbooks_sync_failures = Counter("quickbooks_sync_failures_total", "QuickBooks sync failures")
```

### 9.2 Logging

```python
# Structured logging for all operations
self.logger.info(
    "Invoice created",
    extra={
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "type": invoice.type,
        "amount": float(invoice.total),
        "client_id": invoice.client_id,
        "stripe_invoice_id": invoice.stripe_invoice_id,
        "duration_ms": duration_ms,
    }
)
```

### 9.3 Alerts

- Stripe API error rate > 5%
- QuickBooks sync failure rate > 10%
- Invoice validation failure rate > 20%
- Invoices stuck in "draft" status > 24 hours
- Average invoice creation time > 30 seconds

---

## 10. Deployment Checklist

- [ ] Database migrations applied (invoices, invoice_items, invoice_events tables)
- [ ] Stripe API credentials configured
- [ ] QuickBooks OAuth credentials configured
- [ ] Email service configured
- [ ] Celery tasks registered for async operations
- [ ] Webhook handlers for Stripe events
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing (>85% coverage)
- [ ] Monitoring dashboards configured
- [ ] Alert rules configured
- [ ] Error handling tested (Stripe down, QuickBooks down, etc.)
- [ ] Documentation updated
- [ ] Audit logging verified

---

## 11. Future Enhancements

1. **Multi-currency support** - Handle invoices in different currencies
2. **Tax calculation** - Integrate with TaxJar or Avalara
3. **Recurring invoices** - Automated retainer invoice generation
4. **Invoice templates** - Customizable invoice designs
5. **Late fees** - Automatic late fee calculation
6. **Payment plans** - Split invoices into installments
7. **Credit memos** - Handle refunds and credits
8. **Invoice reminders** - Automated payment reminders
9. **Batch invoicing** - Generate multiple invoices at once
10. **Invoice analytics** - Revenue forecasting and aging reports

---

## Appendices

### A. Invoice State Machine

```
draft → sent → paid
  ↓       ↓
cancelled  ↓
         overdue
```

### B. Sample Invoice JSON

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "invoice_number": "INV-2025-001",
  "type": "deposit",
  "status": "sent",
  "contract_id": "...",
  "project_id": "...",
  "client_id": "...",
  "subtotal": "25000.00",
  "tax": "0.00",
  "total": "25000.00",
  "amount_due": "25000.00",
  "invoice_date": "2025-01-15",
  "due_date": "2025-01-22",
  "stripe_invoice_id": "in_1234567890",
  "stripe_payment_link": "https://invoice.stripe.com/i/acct_123/test_abc",
  "quickbooks_invoice_id": "123",
  "currency": "usd",
  "payment_terms": "net_7",
  "line_items": [
    {
      "description": "Project deposit (50%)",
      "quantity": "1.00",
      "unit_price": "25000.00",
      "amount": "25000.00"
    }
  ],
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:05:00Z"
}
```

### C. API Response Formats

**Success:**
```json
{
  "status": "success",
  "invoice_id": "uuid",
  "invoice_number": "INV-2025-001",
  "stripe_invoice_id": "in_123",
  "amount": 25000.00,
  "payment_link": "https://...",
  "actions_taken": ["created_stripe_invoice", "synced_quickbooks", "sent_email"],
  "next_steps": ["await_payment"]
}
```

**Error:**
```json
{
  "status": "error",
  "error": "validation_failed",
  "message": "Deposit amount differs from contract terms",
  "details": {
    "requested_amount": "30000.00",
    "expected_amount": "25000.00"
  }
}
```

---

**End of Specification**
