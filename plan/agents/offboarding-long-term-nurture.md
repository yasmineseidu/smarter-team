# Long-Term Nurture Agent

## Category
Offboarding & Nurture

## Purpose
Stay in touch with past clients/prospects

## Nurture Content
- Newsletter/updates
- Value-add content
- Holiday greetings
- Industry news
- Case studies

## Process
1. Segment nurture list
2. Send appropriate content
3. Track engagement
4. Watch for re-engagement signals
5. Route back to active pipeline when ready

## Database Tables
- `nurture_list`
- `nurture_sends`
- `nurture_engagement`

## Integrations
- Email marketing platform
- Content library
- CRM for segmentation

## Priority
Phase 5 - Retention & Growth

## Dependencies
- Client Offboarding Agent (adds completed clients)
- Closed Lost pipeline (adds lost deals)

## Human-in-the-Loop
- Nurture content created/approved by human
- Re-engagement signals reviewed before outreach

## Nurture Segments

### Past Clients
```
Source: Completed projects
Cadence: Monthly
Content: Value-add, updates, case studies
Goal: Repeat business, referrals
```

### Lost Deals - Timing
```
Source: Closed lost (timing/budget reason)
Cadence: Quarterly
Content: Industry news, value content
Goal: Re-engagement when timing is right
```

### Lost Deals - Competitor
```
Source: Closed lost (chose competitor)
Cadence: Quarterly
Content: Differentiating content, case studies
Goal: Second chance if competitor fails
```

### Reactivation Pool
```
Source: No response after outreach
Cadence: Quarterly
Content: Trigger-based outreach
Goal: Re-engage based on signals
```

## Content Calendar

### Monthly (Past Clients)
- Week 1: Industry insight/tip
- Week 2: Case study or success story
- Week 3: Helpful resource
- Week 4: Check-in/availability

### Quarterly (Lost Deals)
- Month 1: Industry report/insights
- Month 2: Success story
- Month 3: Soft check-in

### Holidays
- New Year: Year in review + wishes
- Q2: Mid-year check-in
- Q4: Holiday greetings

## Nurture Email Templates

### Monthly Value Email
```
Subject: {{Insight topic}} - thought you'd find this useful

Hi {{first_name}},

I came across this and thought of you:

{{insight_summary}}

{{if_content_link}}
Full article: {{link}}
{{/if_content_link}}

Hope things are going well at {{company}}!
```

### Quarterly Check-In
```
Subject: Checking in from [Your Name]

Hi {{first_name}},

It's been a while! I wanted to check in and see how things are going.

{{if_past_client}}
How's {{deliverable}} working out?
{{/if_past_client}}

{{if_lost_deal}}
Hope everything is going well with {{mention_their_choice_if_known}}.
{{/if_lost_deal}}

If there's ever anything I can help with, just reply.

Best,
```

### Case Study Share
```
Subject: How {{similar_company}} achieved {{result}}

Hi {{first_name}},

Thought you might find this interesting:

We recently helped {{similar_company}} {{achievement}}.

{{case_study_summary}}

Full case study: {{link}}

Let me know if you'd like to chat about something similar!
```

## Re-Engagement Triggers
```
Trigger → Action:

Email opened 3+ times → Flag for personal follow-up
Link clicked → Send related content
Reply received → Route to active pipeline
Company news detected → Personalized outreach
Job change detected → Congratulations + soft pitch
```

## State Transitions
- Engagement detected: LONG_TERM_NURTURE → ENGAGED
- Re-engagement successful: Move back to appropriate pipeline stage
