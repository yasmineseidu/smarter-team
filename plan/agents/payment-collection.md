# Payment Collection Agent

## Category
Payment & Financial

## Purpose
Track and collect payments

## Reminder Schedule
- Due date: Send invoice
- 3 days overdue: Gentle reminder
- 7 days overdue: Firmer reminder
- 14 days overdue: Escalation warning
- 30 days overdue: Pause work, final notice
- 60 days overdue: Collections consideration

## Process
1. Monitor invoice due dates
2. Send reminders per schedule
3. Track payment status
4. Alert on overdue
5. Escalate as needed

## Database Tables
- `payment_reminders`
- `payment_status`

## Integrations
- Stripe API (payment status)
- Email sending
- Slack/Telegram (alerts)

## Priority
Phase 4 - Client Delivery

## Dependencies
- Invoice Generation Agent (provides invoices)

## Human-in-the-Loop
- Escalation decisions (pause work, collections) require approval
- Custom payment arrangements need approval

## Reminder Templates

### 3 Days Overdue - Gentle
```
Subject: Quick reminder: Invoice {{invoice_number}}

Hi {{first_name}},

Just a friendly reminder that invoice {{invoice_number}} for {{amount}} was due on {{due_date}}.

Pay here: {{payment_link}}

Let me know if you have any questions!
```

### 7 Days Overdue - Firmer
```
Subject: Invoice {{invoice_number}} is overdue

Hi {{first_name}},

Invoice {{invoice_number}} for {{amount}} is now 7 days overdue.

Please process payment at your earliest convenience: {{payment_link}}

If there's an issue, please let me know so we can work it out.
```

### 14 Days Overdue - Warning
```
Subject: Important: Invoice {{invoice_number}} - 14 days overdue

Hi {{first_name}},

Invoice {{invoice_number}} for {{amount}} is now 14 days past due.

If payment isn't received within the next 7 days, I may need to pause work on your project.

Please pay here: {{payment_link}}

If you're experiencing difficulties, let's discuss alternative arrangements.
```

### 30 Days Overdue - Final Notice
```
Subject: Final Notice: Invoice {{invoice_number}}

Hi {{first_name}},

Invoice {{invoice_number}} for {{amount}} is now 30 days overdue.

As a result, I've paused work on your project until payment is received.

Payment link: {{payment_link}}

Please respond to this email to discuss.
```

## Cron Schedule
- Daily at 9:00 AM - Send payment reminders for due invoices
