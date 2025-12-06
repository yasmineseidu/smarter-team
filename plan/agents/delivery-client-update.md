# Client Update Agent

## Category
Project Delivery

## Purpose
Send progress updates to clients

## Schedule
- Weekly progress email
- Milestone completion notifications
- Blocker alerts

## Process
1. Generate progress summary
2. Create update email
3. Send to client
4. Log communication

## Database Tables
- `client_updates`
- `update_logs`

## Integrations
- Email sending
- Project Management data

## Priority
Phase 4 - Client Delivery

## Dependencies
- Project Management Agent (provides status data)

## Human-in-the-Loop
- Weekly updates auto-sent (templates pre-approved)
- Custom updates require approval

## Update Types

### Weekly Progress Update
```
Subject: Weekly Update: {{project_name}}

Hi {{first_name}},

Here's your weekly progress update:

COMPLETED THIS WEEK
✅ {{task_1}}
✅ {{task_2}}
✅ {{task_3}}

IN PROGRESS
🔄 {{task_4}} - {{progress}}%
🔄 {{task_5}} - {{progress}}%

NEXT WEEK'S FOCUS
- {{upcoming_1}}
- {{upcoming_2}}

Overall Progress: {{overall_progress}}%

Let me know if you have any questions!
```

### Milestone Completion
```
Subject: 🎉 Milestone Complete: {{milestone_name}}

Hi {{first_name}},

Great news - we've completed {{milestone_name}}!

WHAT WE DELIVERED
{{deliverable_summary}}

NEXT STEPS
{{next_milestone}} begins now. You can expect:
{{next_milestone_description}}

{{if_approval_needed}}
Please review and let me know if you'd like any adjustments.
{{/if_approval_needed}}

Thanks!
```

### Blocker Alert
```
Subject: Heads up: Need your input on {{project_name}}

Hi {{first_name}},

Quick heads up - we've hit a point where we need your input to continue:

WHAT WE NEED
{{blocker_description}}

IMPACT
{{impact_description}}

Can you provide this by {{requested_date}}? This helps us stay on track for {{milestone_name}}.

Thanks!
```

## Sending Rules
- Weekly update: Every Friday at 3:00 PM
- Milestone completion: Within 2 hours of completion
- Blocker alert: Within 1 hour of detection

## Cron Schedule
- Friday at 3:00 PM - Send weekly client progress updates
