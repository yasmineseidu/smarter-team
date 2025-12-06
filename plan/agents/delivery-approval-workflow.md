# Client Approval Workflow Agent

## Category
Project Delivery

## Purpose
Get client sign-off on deliverables

## Process
1. Submit deliverable for review
2. Send review request to client
3. Track review status
4. Handle revision requests
5. Get final approval
6. Mark deliverable complete

## Database Tables
- `approval_requests`
- `revision_requests`
- `approvals`

## Integrations
- Email sending
- Google Drive (deliverable links)
- ClickUp (task status updates)

## Priority
Phase 4 - Client Delivery

## Dependencies
- Project Management Agent (provides deliverable status)

## Human-in-the-Loop
- Deliverables prepared by human before submission
- Revision requests handled by human

## Approval Flow

```
DELIVERABLE READY
       │
       ▼
SEND REVIEW REQUEST
       │
       ▼
┌──────────────────┐
│ WAITING FOR      │
│ CLIENT REVIEW    │
│ (Track: opened,  │
│  time spent)     │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
APPROVED   REVISIONS
    │      REQUESTED
    │         │
    │         ▼
    │    HANDLE REVISIONS
    │         │
    │         ▼
    │    RESUBMIT
    │         │
    └────┬────┘
         │
         ▼
   MARK COMPLETE
         │
         ▼
  TRIGGER NEXT STEP
  (invoice, next phase)
```

## Review Request Email
```
Subject: Ready for your review: {{deliverable_name}}

Hi {{first_name}},

{{deliverable_name}} is ready for your review!

VIEW DELIVERABLE
{{deliverable_link}}

WHAT TO REVIEW
{{review_checklist}}

Please review and either approve or let me know what changes you'd like.

Revision rounds remaining: {{revisions_remaining}} of {{max_revisions}}

Thanks!
```

## Revision Request Handling
```
Subject: Re: Ready for your review: {{deliverable_name}}

Hi {{first_name}},

Thanks for the feedback! I've noted your revision requests:

{{revision_list}}

I'll have the updated version to you by {{estimated_date}}.

Revision rounds remaining after this: {{revisions_remaining}}
```

## Approval Confirmation
```
Subject: ✅ Approved: {{deliverable_name}}

Hi {{first_name}},

Thank you for approving {{deliverable_name}}!

WHAT'S NEXT
{{next_step}}

{{if_invoice_triggered}}
You'll receive an invoice for this milestone shortly.
{{/if_invoice_triggered}}

Thanks for your partnership!
```

## Revision Limits
- Default max revisions: 3
- Beyond limit: Change order required
- Track revision reasons for learning
