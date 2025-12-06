# Proposal Negotiation Agent

## Category
Proposal & Closing

## Purpose
Handle proposal back-and-forth

## Common Scenarios
- Price negotiation
- Scope changes
- Payment term requests
- Timeline adjustments
- Custom additions

## Process
1. Receive negotiation request
2. Classify request type
3. Check approval authority (pre-approved discounts, etc.)
4. Generate counter-proposal or acceptance
5. Route to human for approval if needed
6. Update proposal
7. Track all changes

## Database Tables
- `negotiations`
- `negotiation_history`
- `approval_authority`

## Integrations
- PandaDoc API (for proposal updates)
- Slack/Telegram (for approvals)
- Claude API (for response drafting)

## Priority
Phase 3 - Closing & Proposals

## Dependencies
- Proposal Creation Agent (provides initial proposal)

## Human-in-the-Loop
- Auto-approved: Discounts ≤10%, standard payment terms
- Requires approval: Discounts >10%, custom terms, scope changes

## Approval Authority Matrix

| Request Type | Auto-Approve | Needs Approval |
|--------------|--------------|----------------|
| Discount ≤5% | ✓ | |
| Discount 5-10% | ✓ | |
| Discount >10% | | ✓ |
| Net 30 terms | ✓ | |
| Net 45 terms | ✓ | |
| Net 60+ terms | | ✓ |
| Payment plan | | ✓ |
| Scope reduction | | ✓ |
| Scope addition | | ✓ |
| Timeline change ≤2 weeks | ✓ | |
| Timeline change >2 weeks | | ✓ |

## Negotiation Response Templates

### Discount Request
```
I appreciate you asking! I can offer a {{discount}}% discount, bringing the total to {{new_price}}.

This brings us to our best possible rate for this scope of work.
```

### Payment Terms Request
```
Absolutely, we can work with {{terms}} payment terms.

I'll update the proposal to reflect this.
```

### Scope Change Request
```
I'd be happy to adjust the scope. Based on your request, here's the updated breakdown:

[Updated scope and pricing]

Let me know if this works for you!
```
