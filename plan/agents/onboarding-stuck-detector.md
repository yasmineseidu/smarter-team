# Onboarding Stuck Detector Agent

## Category
Client Onboarding

## Purpose
Catch stalled onboardings

## Triggers
- Intake form not completed in 3 days
- No response to access requests in 2 days
- Kickoff call not scheduled in 5 days
- No communication in 5 days

## Process
1. Check onboarding progress daily
2. Identify stuck onboardings
3. Send reminder to client
4. Alert you after 2 reminders
5. Escalate if no progress in 7 days

## Database Tables
- `onboarding_alerts`
- `stuck_onboardings`

## Integrations
- Slack/Telegram (owner alerts)
- Email sending (client reminders)

## Priority
Phase 4 - Client Delivery

## Dependencies
- Onboarding Orchestrator Agent (provides onboarding status)

## Human-in-the-Loop
- Escalations require human intervention
- May need phone call or alternative approach

## Stuck Detection Rules

### Intake Form Stuck
```
IF intake_form_sent = TRUE
AND intake_form_completed = FALSE
AND days_since_sent >= 3
THEN stuck = TRUE, reason = "intake_form"
```

### Access Request Stuck
```
IF access_requested = TRUE
AND access_received = FALSE
AND days_since_requested >= 2
THEN stuck = TRUE, reason = "access"
```

### Kickoff Stuck
```
IF onboarding_started_days >= 5
AND kickoff_scheduled = FALSE
THEN stuck = TRUE, reason = "kickoff"
```

### Communication Stuck
```
IF last_communication_days >= 5
THEN stuck = TRUE, reason = "communication"
```

## Reminder Templates

### Intake Form Reminder
```
Subject: Quick reminder: Intake form

Hi {{first_name}},

Just checking in - I noticed the intake form is still pending. Here's the link again:
{{intake_form_link}}

This helps us prepare for your kickoff call. Let me know if you have any questions!
```

### Access Request Reminder
```
Subject: Access request follow-up

Hi {{first_name}},

Following up on the access credentials I requested. We need these to begin work:
{{access_list}}

Please let me know if there are any blockers or if you need help.
```

### General Check-In
```
Subject: Checking in on onboarding

Hi {{first_name}},

I wanted to check in - it's been a few days since we connected about your onboarding.

Is everything okay? Let me know if there's anything I can help with to move things forward.
```

## Escalation Flow
1. Day 3: First reminder sent
2. Day 5: Second reminder sent
3. Day 7: Owner alerted via Slack/Telegram
4. Day 10: Status changed to ONBOARDING_STUCK, requires human intervention

## Cron Schedule
- Every hour - Check for stuck onboardings
