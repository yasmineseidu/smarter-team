# Onboarding Orchestrator Agent

## Category
Client Onboarding

## Purpose
Manage new client onboarding

## Triggered By
Contract signed

## Onboarding Steps
1. Welcome email
2. Client questionnaire/intake form (Deformity)
3. Access provisioning request
4. Kickoff call scheduling
5. Internal project setup
6. Kickoff call
7. Project scope documentation
8. Onboarding complete

## Process
1. Send welcome email immediately
2. Send intake form
3. Monitor form completion
4. Request access credentials
5. Create internal workspace
6. Schedule kickoff
7. Conduct kickoff
8. Document scope
9. Mark onboarding complete
10. Transition to ACTIVE_PROJECT

## Database Tables
- `onboarding_progress`
- `onboarding_steps`
- `intake_responses`

## Integrations
- Deformity API (intake forms)
- Cal.com API (kickoff scheduling)
- ClickUp API (project setup)
- Google Drive API (folder creation)
- Email sending

## Priority
Phase 4 - Client Delivery

## Dependencies
- Payment Processing Agent (triggers on contract signed)
- Internal Setup Agent (creates infrastructure)
- Meeting Scheduler Agent (schedules kickoff)

## Human-in-the-Loop
- Intake form responses reviewed
- Custom onboarding requirements handled manually

## Onboarding Timeline (Target)
- Day 0: Welcome email + intake form
- Day 1-3: Form completed + access requested
- Day 3-5: Internal setup complete
- Day 5-7: Kickoff call scheduled and completed
- Day 7: Onboarding complete

## Welcome Email Template
```
Subject: Welcome to [Your Agency]! 🎉

Hi {{first_name}},

We're thrilled to officially welcome you as a client!

To kick things off, please complete this short questionnaire:
{{intake_form_link}}

This helps us understand your business better and ensures we hit the ground running.

Once you've completed the form, we'll schedule our kickoff call.

Excited to get started!
```

## Intake Form Request Email
```
Subject: Quick form to get started

Hi {{first_name}},

Just a reminder to complete the intake questionnaire when you get a chance:
{{intake_form_link}}

This helps us prepare for our kickoff call and ensures we're aligned on goals.

Let me know if you have any questions!
```

## State Transitions
- Contract signed: CLOSED_WON → ONBOARDING
- Onboarding complete: ONBOARDING → ACTIVE_PROJECT
- Stuck >7 days: ONBOARDING → ONBOARDING_STUCK

## Cron Schedule
- Every hour - Check onboarding progress and send reminders
