# Proposal Negotiation Agent - Production Specification

## Overview

**Agent Name**: `proposal_negotiation`
**Category**: Proposal & Closing
**Phase**: Phase 3 - Closing & Proposals
**Coverage Requirement**: >85%

The Proposal Negotiation Agent autonomously handles proposal back-and-forth on pricing, scope, payment terms, and timelines. It operates within pre-approved authority limits, auto-approving common requests (discounts ≤10%, Net 30-45 terms) while escalating larger changes (discounts >10%, scope modifications, custom payment plans) to human review. This agent ensures fast response times to negotiation requests while maintaining pricing integrity and profitability.

## Architecture

### Dependencies

**Upstream Agents:**
- Response Email Handler (detects negotiation requests in emails)
- Proposal Creation Agent (provides original proposal details)
- Proposal Tracking Agent (provides engagement metrics)

**Downstream Agents:**
- Proposal Creation Agent (triggers proposal updates after negotiation)
- Payment Invoice Generation (triggers after final agreement)
- Sales Agent (escalates complex negotiations requiring human intervention)

**External Integrations:**
- PandaDoc API (updates proposals with negotiated terms)
- Slack/Telegram (routes approval requests to humans)
- Claude API (generates counter-offers and negotiation responses)
- Zep (retrieves client negotiation history and preferences)

### Database Schema

#### `negotiations` Table
```sql
CREATE TABLE negotiations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,

    -- Negotiation Status
    status VARCHAR(50) NOT NULL DEFAULT 'OPEN',
    -- Status values: OPEN, IN_PROGRESS, AWAITING_APPROVAL, APPROVED, REJECTED, ACCEPTED, CLOSED

    -- Request Classification
    request_type VARCHAR(50) NOT NULL,
    -- Types: price_discount, scope_change, payment_terms, timeline_adjustment, custom_addition, combination

    request_details JSONB NOT NULL,
    -- Structure: {
    --   "original_request": "Client's exact request text",
    --   "requested_discount_pct": 15.0,
    --   "requested_payment_terms": "Net 60",
    --   "requested_timeline_change": "+2 weeks",
    --   "requested_scope_changes": ["Remove X", "Add Y"],
    --   "justification": "Client's reasoning"
    -- }

    -- Counter-Offer Details
    counter_offer JSONB,
    -- Structure: {
    --   "discount_offered_pct": 10.0,
    --   "new_total_amount": 9000.00,
    --   "payment_terms_offered": "Net 45",
    --   "timeline_offered": "+1 week",
    --   "scope_adjustments": ["Remove X", "Partial Y"],
    --   "rationale": "Why this counter-offer is fair"
    -- }

    -- Pricing Changes
    original_total DECIMAL(10, 2) NOT NULL,
    requested_total DECIMAL(10, 2),
    final_total DECIMAL(10, 2),
    discount_percentage DECIMAL(5, 2) DEFAULT 0.00,

    -- Approval Workflow
    requires_human_approval BOOLEAN NOT NULL DEFAULT false,
    approval_status VARCHAR(50),
    -- Values: pending, approved, rejected, not_required
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    rejection_reason TEXT,

    -- Response Tracking
    response_sent_at TIMESTAMP,
    response_message TEXT,
    rounds_count INTEGER DEFAULT 1,

    -- Resolution
    resolution VARCHAR(50),
    -- Values: accepted_original, accepted_counter, accepted_modified, rejected_by_client, rejected_by_us, expired
    resolved_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_negotiations_proposal_id (proposal_id),
    INDEX idx_negotiations_client_id (client_id),
    INDEX idx_negotiations_status (status),
    INDEX idx_negotiations_approval (requires_human_approval, approval_status) WHERE requires_human_approval = true,
    INDEX idx_negotiations_created_at (created_at DESC)
);
```

#### `negotiation_history` Table
```sql
CREATE TABLE negotiation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    negotiation_id UUID NOT NULL REFERENCES negotiations(id) ON DELETE CASCADE,

    -- Event Details
    event_type VARCHAR(50) NOT NULL,
    -- Types: request_received, counter_offer_generated, approval_requested, approval_granted,
    --        approval_denied, response_sent, client_accepted, client_rejected, client_counter,
    --        proposal_updated, escalated_to_human

    actor VARCHAR(50) NOT NULL,
    -- Values: client, agent, human_approver, system

    -- Event Data
    event_data JSONB NOT NULL,
    -- Structure varies by event_type:
    -- {
    --   "action": "Generated counter-offer",
    --   "details": {...},
    --   "previous_state": {...},
    --   "new_state": {...}
    -- }

    -- Communication Content
    message_sent TEXT,
    message_received TEXT,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_negotiation_history_negotiation_id (negotiation_id),
    INDEX idx_negotiation_history_event_type (event_type),
    INDEX idx_negotiation_history_created_at (created_at DESC)
);
```

#### `approval_authority` Table
```sql
CREATE TABLE approval_authority (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Authority Rule
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    rule_type VARCHAR(50) NOT NULL,
    -- Types: discount, payment_terms, scope_change, timeline_change, custom

    -- Approval Thresholds
    auto_approve_conditions JSONB NOT NULL,
    -- Structure:
    -- For discount: {"max_percentage": 10.0, "max_amount": 5000.00}
    -- For payment_terms: {"allowed_terms": ["Net 30", "Net 45"]}
    -- For timeline: {"max_extension_weeks": 2}
    -- For scope: {"requires_approval": true}

    requires_approval_conditions JSONB NOT NULL,
    -- Structure: Conditions that trigger human approval requirement
    -- {"min_percentage": 10.0, "min_amount": 5000.00, "proposal_value_threshold": 50000.00}

    -- Approver Assignment
    default_approver_role VARCHAR(50),
    -- Values: sales_manager, finance_lead, operations_director, ceo

    escalation_approver_role VARCHAR(50),
    -- For high-value or complex cases

    -- Priority
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_approval_authority_type (rule_type),
    INDEX idx_approval_authority_active (is_active) WHERE is_active = true
);
```

#### `negotiation_approvals` Table
```sql
CREATE TABLE negotiation_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    negotiation_id UUID NOT NULL REFERENCES negotiations(id) ON DELETE CASCADE,

    -- Approval Request
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    requested_by VARCHAR(50) DEFAULT 'agent',

    -- Assigned Approver
    approver_user_id UUID REFERENCES users(id),
    approver_role VARCHAR(50) NOT NULL,

    -- Request Details
    approval_type VARCHAR(50) NOT NULL,
    request_summary TEXT NOT NULL,
    request_details JSONB NOT NULL,

    -- Response
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Values: pending, approved, rejected, expired

    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    decision_notes TEXT,

    -- Notification Tracking
    notification_sent_at TIMESTAMP,
    notification_channel VARCHAR(50),
    -- Values: slack, email, telegram, sms

    reminder_sent_at TIMESTAMP,
    reminder_count INTEGER DEFAULT 0,

    -- SLA Tracking
    sla_deadline TIMESTAMP,
    sla_breached BOOLEAN DEFAULT false,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_negotiation_approvals_negotiation_id (negotiation_id),
    INDEX idx_negotiation_approvals_status (status),
    INDEX idx_negotiation_approvals_approver (approver_user_id, status),
    INDEX idx_negotiation_approvals_sla (sla_deadline) WHERE status = 'pending'
);
```

## System Prompt

```
You are the Proposal Negotiation Agent for Smarter Team, an AI agency automation system.

Your role is to handle proposal negotiations professionally and strategically, maximizing close rates while protecting profitability and maintaining client relationships.

# Your Capabilities

1. **Request Classification**: Categorize negotiation requests (pricing, scope, terms, timeline)
2. **Authority Assessment**: Determine if request is within auto-approve limits or requires human approval
3. **Counter-Offer Generation**: Create strategic counter-proposals that balance client needs with business goals
4. **Approval Routing**: Escalate complex negotiations to appropriate human approvers via Slack
5. **Proposal Updates**: Modify PandaDoc proposals with negotiated terms once agreed
6. **History Tracking**: Log all negotiation events for learning and compliance
7. **Pattern Recognition**: Learn from past negotiations to improve counter-offer strategies

# Workflow

1. **Receive Negotiation Request** from Response Email Handler
   - Extract: Client request, specific asks (discount, scope, terms, timeline)
   - Context: Original proposal details, client history, engagement metrics

2. **Classify Request Type**
   - Price discount (percentage or dollar amount)
   - Scope changes (additions, reductions, modifications)
   - Payment terms (Net 30/45/60, payment plans, milestone adjustments)
   - Timeline adjustments (extensions, accelerations)
   - Combination requests (multiple changes)

3. **Check Approval Authority**
   Query `approval_authority` table for applicable rules:

   **AUTO-APPROVE** (respond immediately):
   - Discounts ≤10% AND ≤$5,000
   - Net 30 or Net 45 payment terms
   - Timeline extensions ≤2 weeks
   - Minor clarifications (no financial impact)

   **REQUIRES APPROVAL** (escalate to human):
   - Discounts >10% OR >$5,000
   - Net 60+ payment terms or custom payment plans
   - Any scope changes (additions or reductions)
   - Timeline extensions >2 weeks
   - Proposals valued >$50,000 (any changes)
   - Combination requests affecting multiple terms

4. **Generate Counter-Offer** (for auto-approve cases)
   - Calculate: New pricing, adjusted terms, modified timeline
   - Ensure: Counter-offer is fair, profitable, and strategic
   - Principles:
     * Never go below minimum margin (30% gross margin)
     * Offer less than requested when reasonable (e.g., requested 15% → offer 10%)
     * Bundle concessions (if discount, tighten timeline or terms)
     * Emphasize value and ROI, not just price
     * Maintain professional, collaborative tone

5. **Route for Approval** (for cases requiring human review)
   - Create approval request in `negotiation_approvals` table
   - Determine approver: sales_manager (<$25k), finance_lead ($25k-$50k), ceo (>$50k or scope changes)
   - Send notification via Slack with:
     * Client name and proposal value
     * Specific request and justification
     * Recommended counter-offer (agent's suggestion)
     * Engagement metrics (proposal views, interest signals)
     * Approval deadline (4 hours for <$25k, 8 hours for >$25k)
   - Track: SLA adherence, send reminders if no response

6. **Update Proposal in PandaDoc**
   Once negotiation is accepted (auto-approved or human-approved):
   - Modify proposal document with new terms
   - Update pricing tables, payment schedule, timeline
   - Add note: "Updated terms per agreement on [date]"
   - Preserve version history
   - Send updated proposal to client
   - Update `proposals` table with new amounts

7. **Track All Negotiation Events**
   - Log every action in `negotiation_history` table
   - Record: Request, counter-offers, approvals, client responses
   - Track: Resolution (accepted, rejected), final terms
   - Learn: Patterns for future negotiations (acceptance rate by discount %, client segment preferences)

8. **Handoff After Agreement**
   - If accepted: Handoff to `payment_invoice_generation` agent
   - If rejected: Handoff to `sales_agent` for human follow-up
   - Update lead status: NEGOTIATING → CLOSED_WON or back to PROPOSAL_SENT

# Negotiation Strategy Guidelines

**Discount Requests:**
- Understand WHY they're asking (budget constraints, competitive quote, perceived value gap)
- Counter with lower discount + additional value (extended support, faster timeline, bonus service)
- Emphasize ROI and outcomes, not just cost
- Example: "I can offer 8% off, bringing total to $9,200. At this rate, you'll still see 5x ROI within 6 months based on your goals."

**Scope Changes:**
- Clearly outline impact on timeline and pricing
- Offer alternatives (phased approach, MVP vs full scope)
- Protect against scope creep with precise definitions
- Example: "We can reduce the scope to core features for $8,000, delivering in 6 weeks. Advanced features can be Phase 2 for $3,000."

**Payment Terms:**
- Default to Net 30 (fastest payment)
- Net 45 acceptable for established businesses
- Net 60+ or payment plans require approval (cash flow impact)
- Offer incentive for faster payment (2% discount for Net 15)
- Example: "We typically work with Net 30 terms. If you need Net 45, we can accommodate that."

**Timeline Adjustments:**
- Small extensions (≤2 weeks) usually acceptable if justified
- Accelerations require resource check (may need additional cost)
- Be honest about feasibility
- Example: "We can extend the timeline by 1 week to accommodate your review schedule. New delivery: June 15th."

**Combination Requests:**
- Prioritize which concession to grant (prefer timeline flexibility over price)
- Bundle trade-offs (e.g., "We can do Net 45 if you approve scope by Friday")
- Maintain profitability and project quality

# Approval Routing Rules

**Sales Manager** (auto-assign for):
- Discounts 10-15%
- Net 60 terms
- Timeline extensions 2-4 weeks
- Proposal value <$25,000

**Finance Lead** (auto-assign for):
- Discounts 15-20%
- Custom payment plans
- Proposal value $25,000-$50,000

**Operations Director** (auto-assign for):
- Scope additions (resource impact)
- Timeline accelerations (team capacity)

**CEO** (auto-assign for):
- Discounts >20%
- Proposal value >$50,000
- Scope reductions (strategic decision)
- Non-standard terms

# Response Templates

Use these as starting points, personalize with Claude:

**Auto-Approved Discount:**
```
Thanks for reaching out! I appreciate you asking.

I can offer a {{discount_pct}}% discount, bringing the total to ${{new_total}}. This is our best rate for this scope, and you'll still see {{roi_metric}} within {{timeframe}}.

I've updated the proposal with these new terms: [PandaDoc link]

Let me know if you're ready to move forward!
```

**Auto-Approved Payment Terms:**
```
Absolutely, we can work with {{terms}} payment terms.

I've updated the proposal to reflect this: [PandaDoc link]

Everything else remains the same. Let me know if you have any other questions!
```

**Requires Approval - Acknowledging Request:**
```
Thanks for the message! I appreciate you sharing your budget constraints.

Let me discuss this with our team and get back to you within {{timeframe}} with options.

I'll follow up shortly!
```

**Counter-Offer (Strategic):**
```
I hear you on the budget. Here's what I can do:

Instead of {{requested_discount}}%, I can offer {{counter_discount}}% off, bringing the total to ${{new_total}}. To make this work, we'd need to {{trade_off}} (e.g., "start within 2 weeks" or "finalize scope by Friday").

This still gives you {{value_prop}} and keeps us on track for your {{goal}}.

Thoughts?
```

**Scope Change Counter-Offer:**
```
Great question! Here's how we can adjust the scope:

**Option 1**: Reduced scope for ${{reduced_price}} (core features, {{timeline_1}})
**Option 2**: Full scope with phased delivery: Phase 1 (${{phase1_price}}, {{timeline_1}}), Phase 2 (${{phase2_price}}, {{timeline_2}})

Both options deliver the core outcomes you need. Which approach works better for you?
```

**Escalated to Approval:**
```
Thanks for this! I'm reviewing your request with our team to see what we can do.

I'll have an answer for you by {{deadline}}.

Appreciate your patience!
```

# Tone & Voice

- **Professional but warm**: Not robotic, genuinely helpful
- **Collaborative, not adversarial**: "Let's find what works for both of us"
- **Confident in value**: Justify pricing with ROI and outcomes
- **Empathetic**: Acknowledge budget constraints without devaluing our work
- **Solution-oriented**: Always offer options, not just yes/no
- **Concise**: Keep responses under 150 words (respect their time)

# Error Handling

- **Client request unclear**: Ask clarifying questions before responding
- **Approval timeout** (>SLA deadline): Escalate to next level approver + notify sales manager
- **PandaDoc API failure**: Save negotiation locally, send manual proposal link as fallback
- **Conflicting requests** (e.g., "lower price AND add features"): Explain trade-offs, offer options
- **Client becomes aggressive/hostile**: Escalate to human sales agent immediately

# Quality Standards

- **Response time**:
  - Auto-approve cases: <30 minutes
  - Approval-required cases: <4 hours (pending human approval)
- **Acceptance rate**: Target >60% of negotiations result in CLOSED_WON
- **Profitability**: Never approve deals below 30% gross margin without explicit CEO approval
- **Client satisfaction**: Maintain professional, respectful tone even if rejecting unreasonable requests

# Learning & Improvement

After each negotiation:
- Log: Request type, counter-offer, resolution
- Analyze: Acceptance rate by discount %, client segment, request type
- Identify: Patterns (e.g., "SaaS companies usually accept 8% discount, agencies want Net 45")
- Optimize: Adjust counter-offer strategies based on data

Be strategic, empathetic, and data-driven. Every negotiation is an opportunity to close a deal AND build a relationship.
```

## Tool Definitions

### 1. `classify_negotiation_request`
**Purpose**: Categorize negotiation request type and extract specific asks

**Input Schema**:
```python
{
    "proposal_id": str,  # UUID of proposal
    "client_id": str,  # UUID of client
    "request_message": str,  # Client's negotiation request text
    "engagement_metrics": dict | None  # Optional proposal tracking data
}
```

**Output Schema**:
```python
{
    "negotiation_id": str,  # UUID created for this negotiation
    "request_type": str,  # price_discount, scope_change, payment_terms, timeline_adjustment, combination
    "request_details": {
        "original_request": str,  # Client's exact text
        "requested_discount_pct": float | None,  # e.g., 15.0
        "requested_discount_amount": float | None,  # e.g., 2000.00
        "requested_payment_terms": str | None,  # e.g., "Net 60"
        "requested_timeline_change": str | None,  # e.g., "+2 weeks"
        "requested_scope_changes": list[str] | None,  # ["Remove X", "Add Y"]
        "justification": str  # Client's reasoning extracted
    },
    "urgency": str,  # low, medium, high (based on client language)
    "sentiment": str  # positive, neutral, frustrated (tone detection)
}
```

**Implementation**: Use Claude to parse client message, extract specific requests, detect tone/urgency

---

### 2. `check_approval_authority`
**Purpose**: Determine if request can be auto-approved or requires human approval

**Input Schema**:
```python
{
    "negotiation_id": str,  # UUID of negotiation
    "request_type": str,
    "request_details": dict,  # From classify_negotiation_request
    "original_proposal_value": float
}
```

**Output Schema**:
```python
{
    "requires_approval": bool,
    "approval_reason": str | None,  # Why human approval needed
    "applicable_rules": list[dict],  # Rules from approval_authority table
    "auto_approve_eligible": bool,
    "recommended_approver": str | None,  # sales_manager, finance_lead, ceo
    "authority_limits": {
        "max_discount_pct": float,
        "max_discount_amount": float,
        "allowed_payment_terms": list[str],
        "max_timeline_extension_weeks": int
    }
}
```

**Implementation**: Query `approval_authority` table, match request against rules, determine approval path

---

### 3. `calculate_counter_offer`
**Purpose**: Generate strategic counter-proposal within approved bounds

**Input Schema**:
```python
{
    "negotiation_id": str,
    "request_details": dict,
    "original_proposal": dict,  # Pricing, scope, terms from proposals table
    "client_history": dict,  # Past negotiations, acceptance patterns
    "authority_limits": dict  # From check_approval_authority
}
```

**Output Schema**:
```python
{
    "counter_offer": {
        "discount_offered_pct": float,  # e.g., 8.0 (if requested 15%)
        "new_total_amount": float,
        "new_subtotal": float,
        "discount_amount": float,
        "payment_terms_offered": str,  # e.g., "Net 45"
        "timeline_offered": str,  # e.g., "+1 week"
        "scope_adjustments": list[str],  # Changes to deliverables
        "trade_offs": list[str],  # Conditions for counter-offer
        "rationale": str  # Why this counter-offer is fair
    },
    "roi_metrics": {
        "estimated_roi": str,  # e.g., "5x within 6 months"
        "value_delivered": str,  # e.g., "$50k in new revenue"
        "timeframe": str  # e.g., "6 months"
    },
    "gross_margin_pct": float,  # Ensure profitability (min 30%)
    "acceptance_probability": float  # 0-1, based on historical data
}
```

**Implementation**: Business logic for counter-offer calculation, Claude for rationale generation

---

### 4. `update_proposal_pandadoc`
**Purpose**: Modify proposal in PandaDoc with negotiated terms

**Input Schema**:
```python
{
    "negotiation_id": str,
    "proposal_id": str,
    "pandadoc_document_id": str,
    "updated_terms": dict  # From counter_offer or approved modification
}
```

**Output Schema**:
```python
{
    "pandadoc_document_id": str,
    "pandadoc_url": str,  # Updated proposal link
    "version_number": int,  # Incremented version
    "changes_applied": list[str],  # ["Updated pricing to $9,200", "Changed terms to Net 45"]
    "updated_at": str,  # ISO 8601 timestamp
    "success": bool
}
```

**Implementation**: PandaDoc API to update document, create new version snapshot

---

### 5. `route_for_approval`
**Purpose**: Send negotiation request to appropriate human approver via Slack

**Input Schema**:
```python
{
    "negotiation_id": str,
    "approval_type": str,  # discount, payment_terms, scope_change, etc.
    "approver_role": str,  # sales_manager, finance_lead, ceo
    "request_summary": str,
    "request_details": dict,
    "recommended_counter_offer": dict | None,  # Agent's suggestion
    "sla_hours": int  # 4 or 8 hours
}
```

**Output Schema**:
```python
{
    "approval_id": str,  # UUID of negotiation_approvals record
    "approver_notified": bool,
    "notification_channel": str,  # slack, email
    "notification_sent_at": str,  # ISO 8601
    "sla_deadline": str,  # ISO 8601 (now + sla_hours)
    "approval_url": str  # Link to approval interface/Slack message
}
```

**Implementation**: Create `negotiation_approvals` record, send Slack notification with approval buttons

---

### 6. `track_negotiation_history`
**Purpose**: Log all negotiation events for compliance and learning

**Input Schema**:
```python
{
    "negotiation_id": str,
    "event_type": str,  # request_received, counter_offer_generated, approval_requested, etc.
    "actor": str,  # client, agent, human_approver, system
    "event_data": dict,  # Event-specific data
    "message_sent": str | None,
    "message_received": str | None
}
```

**Output Schema**:
```python
{
    "history_id": str,  # UUID of history record
    "created_at": str,  # ISO 8601
    "success": bool
}
```

**Implementation**: Insert into `negotiation_history` table

---

### 7. `generate_negotiation_summary`
**Purpose**: Create summary of negotiation for closing and handoff

**Input Schema**:
```python
{
    "negotiation_id": str
}
```

**Output Schema**:
```python
{
    "negotiation_id": str,
    "summary": {
        "original_request": str,
        "rounds_count": int,
        "final_terms": dict,
        "resolution": str,  # accepted_original, accepted_counter, rejected_by_client, etc.
        "price_change": {
            "original": float,
            "final": float,
            "discount_pct": float
        },
        "timeline": {
            "started_at": str,
            "resolved_at": str,
            "duration_hours": int
        },
        "key_events": list[dict],  # Major milestones
        "lessons_learned": str  # Pattern for future negotiations
    }
}
```

**Implementation**: Query `negotiations` and `negotiation_history`, generate Claude summary

---

## Approval Authority Matrix

This matrix defines auto-approve vs. requires-approval rules. Populate `approval_authority` table with these rules:

### 1. Price Discounts

| Discount Range | Proposal Value | Auto-Approve | Approver Required | SLA |
|----------------|----------------|--------------|-------------------|-----|
| ≤5% | Any | ✓ | - | Immediate |
| 5-10% | <$25k | ✓ | - | Immediate |
| 5-10% | ≥$25k | - | Sales Manager | 4 hours |
| 10-15% | <$25k | - | Sales Manager | 4 hours |
| 10-15% | ≥$25k | - | Finance Lead | 8 hours |
| 15-20% | Any | - | Finance Lead + Sales Manager | 8 hours |
| >20% | Any | - | CEO | 24 hours |

### 2. Payment Terms

| Terms Requested | Auto-Approve | Approver Required | SLA |
|-----------------|--------------|-------------------|-----|
| Net 30 | ✓ | - | Immediate |
| Net 45 | ✓ | - | Immediate |
| Net 60 | - | Sales Manager | 4 hours |
| Net 75+ | - | Finance Lead | 8 hours |
| Payment Plan (50/50) | - | Finance Lead | 8 hours |
| Payment Plan (Custom) | - | Finance Lead + CEO | 24 hours |
| Deferred Payment | - | CEO | 24 hours |

### 3. Timeline Adjustments

| Timeline Change | Auto-Approve | Approver Required | SLA |
|-----------------|--------------|-------------------|-----|
| Extension ≤1 week | ✓ | - | Immediate |
| Extension 1-2 weeks | ✓ | - | Immediate |
| Extension 2-4 weeks | - | Sales Manager | 4 hours |
| Extension >4 weeks | - | Operations Director | 8 hours |
| Acceleration (faster) | - | Operations Director | 8 hours |

### 4. Scope Changes

| Scope Change | Auto-Approve | Approver Required | SLA |
|--------------|--------------|-------------------|-----|
| Clarifications (no $$ impact) | ✓ | - | Immediate |
| Scope Addition | - | Sales Manager + Operations | 8 hours |
| Scope Reduction (<10% value) | - | Sales Manager | 4 hours |
| Scope Reduction (≥10% value) | - | CEO | 24 hours |
| Scope Swap (equal value) | - | Operations Director | 8 hours |

### 5. Combination Requests

| Combination Type | Auto-Approve | Approver Required | SLA |
|------------------|--------------|-------------------|-----|
| Discount ≤10% + Net 45 | ✓ | - | Immediate |
| Discount ≤10% + Timeline ≤2 weeks | ✓ | - | Immediate |
| Discount >10% + Any other change | - | Finance Lead | 8 hours |
| Any scope change + Other changes | - | CEO | 24 hours |

### 6. High-Value Override

**Automatic Escalation to CEO** (regardless of change):
- Proposal value >$50,000 AND any modification
- Strategic client (enterprise, referral partner)
- Competitive situation (client mentions competitor quote)

---

## Response Templates

### 1. Auto-Approved Discount (≤10%)

```
Hi {{client_name}},

Thanks for reaching out! I appreciate you asking.

I can offer a {{discount_pct}}% discount, bringing the total to ${{new_total}}. This is our best rate for this scope of work, and you'll still see {{roi_metric}} within {{timeframe}} based on your goals.

I've updated the proposal with the new pricing: {{pandadoc_url}}

Let me know if you're ready to move forward, or if you have any questions!

Best,
[Agent Signature]
```

### 2. Auto-Approved Payment Terms (Net 30/45)

```
Hi {{client_name}},

Absolutely, we can work with {{payment_terms}} payment terms.

I've updated the proposal to reflect this: {{pandadoc_url}}

Everything else remains the same. Ready to get started?

Best,
[Agent Signature]
```

### 3. Auto-Approved Timeline Extension (≤2 weeks)

```
Hi {{client_name}},

No problem! We can extend the timeline by {{extension_duration}} to accommodate your {{reason}}.

Updated delivery date: {{new_end_date}}

I've updated the proposal: {{pandadoc_url}}

Let me know if this works for you!

Best,
[Agent Signature]
```

### 4. Requires Approval - Acknowledgment

```
Hi {{client_name}},

Thanks for the message! I appreciate you sharing {{reason}}.

Let me discuss this with our team and get back to you by {{deadline}} with options that work for both of us.

I'll follow up shortly!

Best,
[Agent Signature]
```

### 5. Strategic Counter-Offer (Discount)

```
Hi {{client_name}},

I hear you on the budget. Here's what I can do:

Instead of {{requested_discount}}%, I can offer {{counter_discount}}% off, bringing the total to ${{new_total}}. This is our best rate while maintaining the quality and outcomes you need.

At this price, you'll still see {{roi_metric}} and {{value_delivered}}.

To make this work, we'd need to {{trade_off}} (e.g., "start within 2 weeks" or "finalize scope by Friday").

Thoughts? I'm happy to discuss on a quick call if helpful.

Best,
[Agent Signature]
```

### 6. Scope Change Counter-Offer

```
Hi {{client_name}},

Great question! Here's how we can adjust the scope:

**Option 1: Reduced Scope**
- Core features: {{core_features}}
- Price: ${{reduced_price}}
- Timeline: {{timeline_1}}

**Option 2: Phased Delivery**
- Phase 1: {{phase1_scope}} (${{phase1_price}}, {{timeline_1}})
- Phase 2: {{phase2_scope}} (${{phase2_price}}, {{timeline_2}})

Both options deliver {{core_outcome}} you need. Which approach works better for you?

Happy to jump on a call to discuss!

Best,
[Agent Signature]
```

### 7. Escalated - Awaiting Approval

```
Hi {{client_name}},

Thanks for this! I'm reviewing your request with our {{approver_role}} to see what we can do.

I'll have an answer for you by {{deadline}}.

Appreciate your patience!

Best,
[Agent Signature]
```

### 8. Approval Granted - Sending Counter-Offer

```
Hi {{client_name}},

Good news! We can make this work.

Here's what we can offer:

{{counter_offer_details}}

I've updated the proposal with these terms: {{pandadoc_url}}

This keeps us aligned on {{value_prop}} while working within your constraints.

Ready to move forward?

Best,
[Agent Signature]
```

### 9. Approval Denied - Alternative Offered

```
Hi {{client_name}},

I discussed this with our team. Unfortunately, we can't accommodate {{rejected_request}} while maintaining the quality and outcomes you need.

However, here's what we CAN do:

{{alternative_offer}}

This still delivers {{core_value}} and keeps us on track for your goals.

Would this work for you? I'm happy to discuss alternatives on a call.

Best,
[Agent Signature]
```

### 10. Final Agreement Confirmation

```
Hi {{client_name}},

Perfect! Here's the updated proposal with our agreed terms:

{{pandadoc_url}}

**Summary of Changes:**
{{changes_list}}

Once you sign, we'll kick things off on {{start_date}}.

Excited to work together!

Best,
[Agent Signature]
```

---

## Error Handling Strategy

### 1. Ambiguous Client Request

**Scenario**: Client message is unclear (e.g., "Can we adjust pricing?")

**Action**:
- Send clarifying questions via email
- Example: "Happy to help! Are you looking for a discount, different payment terms, or a scope adjustment? Let me know what would work best for you."
- Do NOT generate counter-offer without clarity

### 2. Unrealistic Request

**Scenario**: Client requests 50% discount or unreasonable terms

**Action**:
- Politely explain value and constraints
- Offer realistic alternative
- Example: "I understand budget is a concern. Unfortunately, a 50% discount isn't feasible while maintaining quality. I can offer 10% off ($9,000 total) or we can discuss a phased approach. Would either work?"
- Escalate to human if client insists

### 3. Approval Timeout (>SLA)

**Scenario**: Human approver hasn't responded within SLA deadline

**Action**:
- Send reminder notification (1 hour before deadline)
- If deadline passed:
  - Escalate to next-level approver (sales_manager → finance_lead → ceo)
  - Notify client of delay: "Still reviewing your request with our team. Will update you by [new deadline]."
- Log SLA breach in `negotiation_approvals` table

### 4. PandaDoc API Failure

**Scenario**: Cannot update proposal document in PandaDoc

**Action**:
- Retry up to 3 times with exponential backoff (1s, 2s, 4s)
- If all retries fail:
  - Save negotiated terms in `negotiations` table
  - Send client manual proposal update via email (PDF or plain text)
  - Log error for Error Monitoring Agent
  - Notify operations team to manually update PandaDoc

### 5. Conflicting Client Requests

**Scenario**: Client asks to "reduce price AND add features"

**Action**:
- Explain trade-offs transparently
- Example: "I'd love to help with both! Typically, adding features increases the scope. I can either reduce the price for the current scope, or add features at the current price. Which is more important for you?"
- Offer clear options, not vague compromises

### 6. Hostile or Aggressive Client

**Scenario**: Client becomes rude, demanding, or threatening

**Action**:
- Immediately escalate to human sales agent
- Mark negotiation status: "escalated_to_human"
- Notify sales manager via Slack (high priority)
- Do NOT engage in arguments
- Example handoff note: "Client expressed frustration with pricing. Human follow-up recommended for relationship management."

### 7. Multiple Negotiation Rounds

**Scenario**: Client rejects counter-offer and submits new request (round 2, 3, etc.)

**Action**:
- Track rounds in `negotiations.rounds_count`
- If rounds_count > 3:
  - Suggest phone call: "It seems we're going back and forth via email. Would a quick 15-min call help us align? I can walk through options in real-time."
  - Escalate to human if rounds_count > 5 (likely needs personal touch)

### 8. Competitor Mentioned

**Scenario**: Client says "Competitor X quoted $5,000 for similar work"

**Action**:
- Acknowledge competitor without disparaging
- Emphasize unique value proposition and differentiators
- Example: "I appreciate you sharing that! Our pricing reflects [unique value: speed/quality/expertise]. We've delivered [outcome] for similar clients. That said, I can offer [counter-offer] to make this work. How does that compare?"
- Flag negotiation for sales manager review (competitive intelligence)

---

## Testing Requirements

### Unit Tests (>90% coverage for tools)

**Test File**: `app/backend/__tests__/unit/agents/test_proposal_negotiation_agent.py`

Required tests:
1. `test_agent_initialization` - Agent name, description, tools registered
2. `test_classify_negotiation_request_discount` - Classify discount request
3. `test_classify_negotiation_request_payment_terms` - Classify payment terms request
4. `test_classify_negotiation_request_scope_change` - Classify scope change
5. `test_classify_negotiation_request_combination` - Classify multiple changes
6. `test_check_approval_authority_auto_approve_discount_5pct` - 5% discount auto-approved
7. `test_check_approval_authority_auto_approve_discount_10pct` - 10% discount auto-approved
8. `test_check_approval_authority_requires_approval_15pct` - 15% requires approval
9. `test_check_approval_authority_high_value_override` - >$50k requires CEO approval
10. `test_check_approval_authority_payment_terms_net30` - Net 30 auto-approved
11. `test_check_approval_authority_payment_terms_net60` - Net 60 requires approval
12. `test_calculate_counter_offer_discount_request` - Generate discount counter-offer
13. `test_calculate_counter_offer_maintains_margin` - Ensure 30% min margin
14. `test_calculate_counter_offer_with_tradeoffs` - Bundle concessions (discount + timeline)
15. `test_update_proposal_pandadoc_success` - PandaDoc update success
16. `test_update_proposal_pandadoc_api_error` - Retry logic on API failure
17. `test_route_for_approval_sales_manager` - Route to sales manager
18. `test_route_for_approval_finance_lead` - Route to finance lead
19. `test_route_for_approval_ceo` - Route to CEO for high-value
20. `test_route_for_approval_sla_tracking` - SLA deadline calculation
21. `test_track_negotiation_history_all_events` - Log all event types
22. `test_generate_negotiation_summary_accepted` - Summary for accepted deal
23. `test_generate_negotiation_summary_rejected` - Summary for rejected deal

### Integration Tests (>85% coverage for agent workflow)

**Test File**: `app/backend/__tests__/integration/test_proposal_negotiation_workflow.py`

Required tests:
1. `test_full_workflow_auto_approve_discount` - End-to-end auto-approve discount
2. `test_full_workflow_requires_approval_discount` - End-to-end approval-required discount
3. `test_full_workflow_payment_terms_change` - Payment terms negotiation
4. `test_full_workflow_scope_change` - Scope modification workflow
5. `test_full_workflow_combination_request` - Multiple changes negotiation
6. `test_approval_notification_slack` - Slack notification sent to approver
7. `test_approval_granted_updates_proposal` - Approved request updates PandaDoc
8. `test_approval_denied_sends_alternative` - Denied request sends alternative offer
9. `test_approval_timeout_escalation` - SLA breach escalates to next approver
10. `test_multiple_negotiation_rounds` - Client rejects counter-offer, round 2
11. `test_pandadoc_integration_real_api` - Actual PandaDoc API calls (mocked in CI)
12. `test_database_transactions_rollback` - Proper rollback on failure
13. `test_handoff_to_payment_after_acceptance` - Handoff after deal accepted
14. `test_handoff_to_sales_after_rejection` - Handoff after deal rejected

### Fixtures

**Test File**: `app/backend/__tests__/fixtures/negotiation_fixtures.py`

Required fixtures:
- `mock_negotiation_request_discount` - Sample discount request
- `mock_negotiation_request_payment_terms` - Sample payment terms request
- `mock_negotiation_request_scope_change` - Sample scope change request
- `mock_negotiation_request_combination` - Sample combination request
- `mock_approval_authority_rules` - Sample approval rules
- `mock_counter_offer` - Sample counter-offer response
- `mock_pandadoc_update_success` - PandaDoc success response
- `mock_pandadoc_update_error` - PandaDoc error response
- `mock_slack_notification_payload` - Slack approval notification
- `mock_client_history` - Sample client negotiation history

---

## Environment Configuration

Add to `.env`:
```bash
# PandaDoc (Required)
PANDADOC_API_KEY=your_api_key_here
PANDADOC_WEBHOOK_KEY=your_webhook_secret_here
PANDADOC_ENVIRONMENT=sandbox  # or production

# Slack (Required for approval routing)
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APPROVALS_CHANNEL_ID=C01234567  # Channel for approval notifications

# Negotiation Settings (Optional overrides)
NEGOTIATION_AUTO_APPROVE_MAX_DISCOUNT_PCT=10.0
NEGOTIATION_AUTO_APPROVE_MAX_DISCOUNT_AMOUNT=5000.00
NEGOTIATION_MIN_GROSS_MARGIN_PCT=30.0
NEGOTIATION_SLA_HOURS_DEFAULT=4
```

---

## Implementation Checklist

- [ ] Create database tables: `negotiations`, `negotiation_history`, `approval_authority`, `negotiation_approvals`
- [ ] Implement `ProposalNegotiationAgent` class extending `BaseAgent`
- [ ] Implement all 7 tool functions with full error handling
- [ ] Create PandaDoc client methods for proposal updates
- [ ] Create Slack integration for approval notifications
- [ ] Populate `approval_authority` table with rules from matrix
- [ ] Write all response templates with personalization variables
- [ ] Implement Claude prompts for counter-offer generation
- [ ] Create counter-offer calculation logic (pricing, margin checks)
- [ ] Implement approval routing logic (determine approver by rule)
- [ ] Create SLA tracking and reminder system
- [ ] Write webhook handler for PandaDoc status updates (optional for this agent)
- [ ] Implement handoff to `payment_invoice_generation` on acceptance
- [ ] Implement handoff to `sales_agent` on rejection/escalation
- [ ] Write unit tests (>90% coverage for tools)
- [ ] Write integration tests (>85% coverage for workflow)
- [ ] Create test fixtures for all scenarios
- [ ] Test PandaDoc API integration (sandbox environment)
- [ ] Test Slack approval notifications
- [ ] Test approval timeout and escalation logic
- [ ] Test multi-round negotiation handling
- [ ] Document all approval rules in internal wiki
- [ ] Train sales team on approval interface
- [ ] Set up monitoring and alerts for SLA breaches
- [ ] Performance test: 100 concurrent negotiation requests

---

## Success Metrics

**Key Metrics:**
- Negotiation acceptance rate (target: >60% result in CLOSED_WON)
- Auto-approval rate (target: >40% of requests auto-approved)
- Response time for auto-approve (target: <30 minutes)
- Response time for approval-required (target: <4 hours)
- SLA adherence (target: >95% approvals within deadline)
- Client satisfaction with negotiation process (target: >4.5/5 survey rating)
- Gross margin protection (target: 0% deals below 30% margin without CEO approval)
- Escalation rate (target: <10% of negotiations escalate to human takeover)

**Alerts:**
- SLA breach (approval not received within deadline)
- High rejection rate (>50% of negotiations rejected by client in 7-day period)
- Low margin deal pending (deal below 30% margin requires immediate attention)
- Multiple negotiation rounds (>5 rounds, suggest human intervention)
- Hostile client detected (escalate to sales manager immediately)

---

## Performance Targets

- **Classification Time**: <5 seconds to classify request and extract details
- **Counter-Offer Generation**: <10 seconds to generate strategic counter-offer
- **Approval Routing**: <3 seconds to route to approver and send notification
- **PandaDoc Update**: <15 seconds to update proposal document
- **Database Write**: <2 seconds to save negotiation records
- **End-to-End Auto-Approve**: <30 minutes from request to response sent

---

## Dependencies Installation

Add to `app/backend/pyproject.toml`:
```toml
[project.optional-dependencies]
negotiation = [
    "httpx>=0.27.0",  # Already included (PandaDoc, Slack APIs)
]
```

---

## Migration Files

**Location**: `specs/database-schema/migrations/`

Required migrations (create after database schema review):
1. `007_create_negotiations_table.sql`
2. `008_create_negotiation_history_table.sql`
3. `009_create_approval_authority_table.sql`
4. `010_create_negotiation_approvals_table.sql`
5. `011_populate_approval_authority_rules.sql` (seed default rules)

---

## Security Considerations

1. **API Key Protection**: Store PandaDoc, Slack API keys in environment variables
2. **Approval Authority**: Enforce approval rules at database level (triggers/constraints)
3. **Data Privacy**: Redact client financial details in logs
4. **Access Control**: Only authorized users can approve high-value deals
5. **Audit Logging**: Log all negotiation events, approvals, rejections
6. **Rate Limiting**: Implement rate limits on PandaDoc API calls
7. **Input Validation**: Sanitize client negotiation requests (prevent injection attacks)
8. **Margin Protection**: Hard block deals below 30% margin without explicit CEO approval

---

## Future Enhancements

1. **ML-Based Counter-Offers**: Use ML to predict optimal counter-offer based on client segment, historical acceptance rates
2. **A/B Testing Negotiation Strategies**: Test different counter-offer approaches and measure acceptance rates
3. **Negotiation Playbooks**: Create industry-specific negotiation templates (SaaS vs agency vs enterprise)
4. **Video Negotiation**: Integrate Loom for video responses to high-value negotiations
5. **Real-Time Chat**: Offer live chat for complex negotiations instead of async email
6. **Competitor Intelligence**: Automatically fetch competitor pricing when mentioned
7. **Dynamic Margin Optimization**: Adjust margin requirements based on sales pipeline health
8. **Multi-Language Support**: Negotiate in client's preferred language

---

## Summary of Gaps Identified

### Critical Gaps in Original Plan
1. **No tool definitions** - Added 7 detailed tool schemas with input/output
2. **No system prompt** - Created comprehensive 1000+ word prompt with strategy guidelines
3. **No approval matrix** - Built detailed 6-table approval authority matrix
4. **No counter-offer logic** - Defined calculation rules, margin protection, trade-off bundling
5. **No response templates** - Created 10 templates for all scenarios
6. **No database schema** - Created 4 tables with full relationships and indexes
7. **No error handling** - Added 8 error scenarios with recovery strategies
8. **No testing requirements** - Defined >85% coverage with 23 unit + 14 integration tests
9. **No approval routing** - Built SLA-tracked approval workflow with escalation
10. **No PandaDoc integration** - Defined proposal update methods
11. **No Slack integration** - Created approval notification system
12. **No metrics/monitoring** - Added 8 KPIs and 5 alert conditions
13. **No security considerations** - Added 8 security requirements
14. **No negotiation strategy** - Created strategic guidelines for discounts, scope, terms, timeline
15. **No learning system** - Added pattern tracking for future optimization

### Added Specifications
- Complete database schema with 4 tables
- 7 detailed tool definitions with schemas
- Comprehensive system prompt (1000+ words)
- Approval authority matrix with 6 rule categories
- 10 response templates with personalization
- Approval routing with SLA tracking
- Error handling for 8 scenarios
- Testing plan with 37 tests
- Performance targets and monitoring
- Security and compliance requirements

This specification is now production-ready and provides all details needed for implementation.
