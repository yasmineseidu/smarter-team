# Payment Processing Agent

## Category
Payment & Financial

## Purpose
Handle Stripe payments

## Triggered By
Stripe webhooks

## Events
- Payment successful → Update invoice, notify, proceed
- Payment failed → Retry logic, notify client
- Dispute/chargeback → Alert, pause work, investigate

## Database Tables
- `payments`
- `payment_failures`
- `disputes`

## Integrations
- Stripe webhooks
- QuickBooks API (for recording)
- Email sending
- Slack/Telegram (alerts)

## Priority
Phase 4 - Client Delivery

## Dependencies
- Invoice Generation Agent (provides invoice context)

## Human-in-the-Loop
- Payment success: No approval needed
- Payment failure: Auto-retry, then alert
- Dispute: Immediate human notification

## Webhook Events

### `stripe/payment_succeeded`
```
1. Mark invoice as PAID
2. Update client outstanding_balance
3. Record in QuickBooks
4. Send thank you email
5. If deposit: Trigger onboarding start
6. If milestone: Unlock next milestone
```

### `stripe/payment_failed`
```
1. Log failure reason
2. Send failure notification to client
3. Stripe auto-retries per settings
4. If 3 failures: Alert for manual follow-up
```

### `stripe/charge_disputed`
```
1. Immediately pause project work
2. Send urgent alert to owner
3. Log dispute details
4. Gather evidence for response
5. Track dispute resolution
```

## Payment Success Email
```
Subject: Payment received - Thank you!

Hi {{first_name}},

Thank you! We've received your payment of {{amount}} for invoice {{invoice_number}}.

Receipt: {{receipt_link}}

We appreciate your business!
```

## Payment Failed Email
```
Subject: Payment issue - action needed

Hi {{first_name}},

We tried to process your payment of {{amount}} for invoice {{invoice_number}}, but it was declined.

Please update your payment method and try again: {{payment_link}}

If you have any questions, just reply to this email.
```
