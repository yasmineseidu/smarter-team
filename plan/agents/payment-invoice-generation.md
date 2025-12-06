# Invoice Generation Agent

## Category
Payment & Financial

## Purpose
Create and send invoices

## Triggered By
- Contract signed (deposit invoice)
- Milestone completed (milestone invoice)
- Project completed (final invoice)
- Monthly retainer due

## Process
1. Pull contract/proposal details
2. Generate invoice in Stripe
3. Send invoice to client
4. Log in QuickBooks
5. Update database

## Database Tables
- `invoices`
- `invoice_items`
- `invoice_status`

## Integrations
- Stripe API
- QuickBooks API
- Email sending

## Priority
Phase 4 - Client Delivery

## Dependencies
- Proposal Creation Agent (provides contract details)
- Project Management Agent (provides milestone completion)

## Human-in-the-Loop
- Invoice amounts verified automatically against contract
- Custom invoices require approval

## Invoice Types

### Deposit Invoice
- Triggered by: Contract signed
- Amount: Typically 50% of project total
- Due: Immediate or Net 7

### Milestone Invoice
- Triggered by: Milestone marked complete
- Amount: Per milestone breakdown in contract
- Due: Per contract terms

### Final Invoice
- Triggered by: Project completion
- Amount: Remaining balance
- Due: Per contract terms

### Retainer Invoice
- Triggered by: Monthly schedule
- Amount: Fixed retainer amount
- Due: 1st of each month

## Invoice Data Structure
```json
{
  "invoice_number": "INV-2025-001",
  "client_id": "uuid",
  "project_id": "uuid",
  "type": "milestone",
  "line_items": [
    {"description": "Phase 1 completion", "amount": 5000}
  ],
  "subtotal": 5000,
  "tax": 0,
  "total": 5000,
  "due_date": "2025-02-15",
  "payment_link": "stripe_link"
}
```
