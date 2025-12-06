# Satisfaction Survey Agent

## Category
Client Success & Retention

## Purpose
Gather client feedback

## Survey Points
- Week 1 of project: "How's onboarding going?"
- Mid-project: "How are things progressing?"
- Project completion: "How did we do?"
- 30 days post-completion: "How's the deliverable working?"

## Process
1. Send survey at trigger points
2. Collect responses
3. Analyze sentiment
4. Alert on negative feedback
5. Track satisfaction trends

## Database Tables
- `satisfaction_surveys`
- `survey_responses`
- `satisfaction_scores`

## Integrations
- Survey tool (Typeform, Google Forms, or custom)
- Email sending
- Slack/Telegram (alerts)

## Priority
Phase 5 - Retention & Growth

## Dependencies
- Onboarding Orchestrator (triggers Week 1)
- Project Management (triggers mid-project)
- Offboarding Agent (triggers completion)

## Human-in-the-Loop
- Negative feedback (score <7) triggers immediate alert
- Personal follow-up recommended for low scores

## Survey Templates

### Week 1 - Onboarding Check-In
```
Subject: Quick check-in: How's everything going?

Hi {{first_name}},

You've been with us for a week now! I wanted to check in.

How would you rate your onboarding experience so far?
{{survey_link}}

This takes just 30 seconds. Your feedback helps us improve!
```

**Survey Questions:**
1. How satisfied are you with the onboarding process? (1-10)
2. Is communication meeting your expectations? (Yes/No/Somewhat)
3. Any concerns or feedback? (Open text)

### Mid-Project
```
Subject: Mid-project check-in

Hi {{first_name}},

We're at the midpoint of your project. How's it going?

Quick 30-second survey: {{survey_link}}
```

**Survey Questions:**
1. How satisfied are you with progress so far? (1-10)
2. Is the work meeting your expectations? (Yes/No/Somewhat)
3. Any feedback or adjustments needed? (Open text)

### Project Completion
```
Subject: We'd love your feedback!

Hi {{first_name}},

Congratulations on completing {{project_name}}! 🎉

I'd love to hear how we did: {{survey_link}}

Your feedback helps us improve and means a lot to our team.
```

**Survey Questions:**
1. Overall, how satisfied were you? (1-10)
2. Would you recommend us? (1-10 NPS)
3. What did we do well? (Open text)
4. What could we improve? (Open text)
5. Can we use your feedback as a testimonial? (Yes/No)

### 30-Day Follow-Up
```
Subject: How's everything working?

Hi {{first_name}},

It's been a month since we wrapped up {{project_name}}.

How's everything working? Quick check-in: {{survey_link}}
```

**Survey Questions:**
1. How well is the deliverable performing? (1-10)
2. Any issues or questions? (Open text)
3. Would you consider working with us again? (Yes/No/Maybe)

## Score Thresholds
- 9-10: Promoter → Request testimonial
- 7-8: Passive → Thank and monitor
- 1-6: Detractor → Immediate alert + follow-up

## Alert Rules
```
IF survey_score <= 6
THEN send_alert(owner, "Negative feedback from {{client}}")
AND create_task("Follow up with {{client}} about feedback")
```
