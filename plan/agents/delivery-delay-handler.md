# Project Delay Handler Agent

## Category
Project Delivery

## Purpose
Manage and communicate delays

## Triggered By
Milestone overdue

## Process
1. Detect delay
2. Assess impact
3. Generate revised timeline
4. Draft client communication
5. Send after approval
6. Update project schedule

## Database Tables
- `project_delays`
- `delay_communications`

## Integrations
- Project Management systems
- Email sending
- Claude API (for communication drafting)

## Priority
Phase 4 - Client Delivery

## Dependencies
- Project Management Agent (detects overdue milestones)

## Human-in-the-Loop
- Delay communication requires approval before sending
- Timeline revision requires approval

## Delay Detection

### Automatic Detection
```
IF milestone.due_date < today
AND milestone.status != "complete"
THEN delay_detected = TRUE
```

### Severity Assessment
```
MINOR: 1-2 days late, no downstream impact
MODERATE: 3-7 days late, some downstream impact
MAJOR: >7 days late, significant downstream impact
CRITICAL: Threatens project completion date
```

## Impact Analysis
```
For each delayed milestone:
  - Calculate days late
  - Identify dependent tasks
  - Calculate cascade effect
  - Determine if end date affected
  - Flag if client deliverable impacted
```

## Communication Templates

### Minor Delay (Internal Note)
```
No client communication needed.
Log delay internally.
Adjust internal schedule.
```

### Moderate Delay
```
Subject: Quick update on {{project_name}} timeline

Hi {{first_name}},

I wanted to give you a heads up - {{milestone_name}} is taking a bit longer than expected.

WHAT HAPPENED
{{delay_reason}}

NEW TIMELINE
- {{milestone_name}}: {{new_date}} (was {{original_date}})
- Impact on final delivery: {{impact}}

This {{does/doesn't}} affect your final delivery date.

I'll keep you posted on progress. Let me know if you have any questions!
```

### Major Delay
```
Subject: Important: {{project_name}} timeline update

Hi {{first_name}},

I need to share an important update about our timeline.

CURRENT STATUS
{{status_summary}}

DELAY REASON
{{delay_reason}}

REVISED TIMELINE
| Milestone | Original | New Date |
|-----------|----------|----------|
{{timeline_table}}

IMPACT
{{impact_description}}

WHAT WE'RE DOING
{{mitigation_steps}}

I apologize for any inconvenience. Let me know if you'd like to discuss.
```

### Critical Delay
```
Subject: Urgent: Need to discuss {{project_name}} timeline

Hi {{first_name}},

I need to have an honest conversation about our project timeline.

{{situation_explanation}}

I'd like to schedule a call to discuss options and find the best path forward.

Are you available {{suggested_times}}?
```

## Mitigation Options
- Add resources to catch up
- Reduce scope (with approval)
- Extend timeline (with approval)
- Parallel track work

## Alert Flow
1. Delay detected → Generate impact analysis
2. Draft communication based on severity
3. Send to owner for approval
4. Owner edits/approves
5. Send to client
6. Update project schedule
7. Log delay for future analysis
