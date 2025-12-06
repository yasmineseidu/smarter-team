# Contract Renewal Agent

## Category
Client Success & Retention

## Purpose
Manage retainer renewals

## Reminders
- 90 days before: Internal alert
- 60 days before: Client touchpoint
- 30 days before: Renewal proposal
- 14 days before: Final reminder

## Process
1. Track contract end dates
2. Send reminders per schedule
3. Generate renewal proposal
4. Handle negotiations
5. Process renewal or offboarding

## Database Tables
- `contract_renewals`
- `renewal_reminders`

## Integrations
- Contract/proposal system
- Email sending
- Calendar (for renewal dates)

## Priority
Phase 5 - Retention & Growth

## Dependencies
- Client data (provides contract end dates)
- Proposal Creation Agent (generates renewal proposal)

## Human-in-the-Loop
- Renewal proposal terms reviewed before sending
- Negotiation requires human involvement
- Decision to not renew requires human approval

## Renewal Timeline

### 90 Days Before (Internal)
```
ALERT: CONTRACT RENEWAL UPCOMING

Client: {{client_name}}
Contract ends: {{end_date}}
Contract value: ${{value}}
Renewal type: {{monthly/annual}}

ACTION NEEDED
Prepare renewal strategy by {{strategy_deadline}}.
Consider: pricing changes, scope adjustments, upsell opportunities.
```

### 60 Days Before (Client Touchpoint)
```
Subject: Thinking about our partnership

Hi {{first_name}},

Can you believe it's been {{duration}} since we started working together?

I wanted to check in ahead of your contract renewal in {{days}} days.

How are things going? Anything you'd like to adjust or improve for the next period?

Let me know if you'd like to hop on a quick call to discuss.
```

### 30 Days Before (Renewal Proposal)
```
Subject: Your renewal proposal

Hi {{first_name}},

Your current contract is up for renewal on {{end_date}}.

I've put together a renewal proposal for you: {{proposal_link}}

{{if_changes}}
Based on our conversations, I've included the following adjustments:
{{change_list}}
{{/if_changes}}

{{if_same}}
We'd love to continue our work together under the same terms.
{{/if_same}}

Let me know if you have any questions!
```

### 14 Days Before (Final Reminder)
```
Subject: Quick reminder: Renewal due {{end_date}}

Hi {{first_name}},

Just a reminder that your contract renewal is due in 2 weeks.

Renewal proposal: {{proposal_link}}

Please let me know if you'd like to proceed, make changes, or discuss.

If I don't hear back, I'll reach out next week to confirm.
```

### 7 Days Before (Final Check)
```
Subject: Contract ending soon - need your decision

Hi {{first_name}},

Your current contract ends on {{end_date}} - just 7 days away.

I haven't heard back about renewal. Could you let me know your plans?

Options:
1. Renew as proposed: {{proposal_link}}
2. Discuss changes: Reply to schedule a call
3. Not renewing: Let me know so I can plan accordingly

Looking forward to hearing from you!
```

## Renewal Scenarios

### Standard Renewal
- Same terms
- Auto-generate proposal from template
- Simple approval process

### Renewal with Changes
- Price adjustment (market rate, scope change)
- Scope modification
- Term length change
- Requires human review

### Non-Renewal
- Client declines
- Trigger offboarding process
- Exit survey
- Maintain relationship for future

## Pricing Guidance
```
Standard increase: 3-5% annually
Value-based increase: Based on demonstrated ROI
Loyalty discount: Consider for 2+ year clients
Market adjustment: Match competitive rates
```

## Cron Schedule
- Monthly on 1st at 10:00 AM - Identify upcoming renewals
- Weekly - Send scheduled renewal reminders
