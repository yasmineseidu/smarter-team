# Proposal Tracking Agent

## Category
Proposal & Closing

## Purpose
Follow up on sent proposals

## Tracking
- Proposal views (PandaDoc webhook)
- Time spent on sections
- Multiple viewers
- Download/print events

## Follow-up Cadence
- Day 1: "Just sent it over"
- Day 3: Check in if no view
- Day 5: "Any questions?"
- Day 7: Value add content
- Day 10: Deadline reminder
- Day 14: Final push

## Process
1. Track proposal activity via webhooks
2. Trigger appropriate follow-up
3. Adjust strategy based on activity
4. 20-30 touchpoints total
5. Move to reactivation if no response after cadence

## Database Tables
- `proposal_tracking`
- `proposal_views`
- `proposal_followups`

## Integrations
- PandaDoc webhooks
- Email sending
- Claude API (for follow-up customization)

## Priority
Phase 3 - Closing & Proposals

## Dependencies
- Proposal Creation Agent (provides proposal data)

## Human-in-the-Loop
- Follow-up templates approved in advance
- Final push may require human crafting

## Webhook
- Receives: `pandadoc/document_viewed`
- Receives: `pandadoc/document_signed`
- Receives: `pandadoc/document_expired`

## Follow-up Templates

### Day 1 - Just Sent
```
Subject: Your proposal is ready

Hi {{first_name}},

I've just sent over the proposal we discussed. You should have it in your inbox from PandaDoc.

Take a look when you have a chance and let me know if you have any questions!
```

### Day 3 - No View
```
Subject: Making sure you got it

Hi {{first_name}},

Just wanted to make sure the proposal landed in your inbox. Sometimes PandaDoc emails go to spam.

Here's the direct link: {{proposal_link}}

Let me know if you have any questions!
```

### Day 5 - Questions
```
Subject: Any questions?

Hi {{first_name}},

I noticed you've had a chance to review the proposal. Any questions I can answer?

Happy to hop on a quick call if that's easier.
```

### Day 7 - Value Add
```
Subject: Something you might find helpful

Hi {{first_name}},

While you're reviewing the proposal, I thought you might find this relevant:

[Case study / testimonial / relevant content]

Let me know if you'd like to discuss!
```

### Day 10 - Deadline Reminder
```
Subject: Proposal valid until {{expiry_date}}

Hi {{first_name}},

Quick heads up - the proposal I sent is valid until {{expiry_date}}.

I'd hate for you to miss out if you're interested. Any questions I can answer to help you decide?
```

### Day 14 - Final Push
```
Subject: Following up one more time

Hi {{first_name}},

I've reached out a few times about the proposal. I don't want to keep bothering you, so this will be my last follow-up.

If the timing isn't right, no worries at all. Just let me know and I'll check back in a few months.

If you're still interested, I'd love to make this happen!
```

## State Transitions
- Proposal viewed: Update tracking metrics
- Proposal signed: PROPOSAL_SENT → CLOSED_WON
- Proposal expired: PROPOSAL_SENT → PROPOSAL_EXPIRED → REACTIVATION_POOL
- No response after cadence: PROPOSAL_SENT → REACTIVATION_POOL

## Cron Schedule
- Daily at 3:00 PM - Send daily proposal follow-ups
