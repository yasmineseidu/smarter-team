# Upsell Detector Agent

## Category
Client Success & Retention

## Purpose
Identify expansion opportunities

## Signals
- Client asks about other services
- High satisfaction scores
- Successful project delivery
- Mentions other pain points
- Company growth signals

## Process
1. Monitor for upsell signals
2. Score opportunity
3. Generate upsell recommendation
4. Create outreach task

## Database Tables
- `upsell_opportunities`
- `upsell_signals`

## Integrations
- Conversation analysis
- Survey responses
- Company research

## Priority
Phase 5 - Retention & Growth

## Dependencies
- Conversation Intelligence (provides conversation analysis)
- Satisfaction Survey Agent (provides scores)
- Company Research Agent (provides growth signals)

## Human-in-the-Loop
- Upsell opportunities flagged for human action
- Human decides timing and approach

## Signal Detection

### Explicit Signals (High Value)
```
Keywords/phrases in conversations:
- "Do you also do..."
- "What about..."
- "We're also looking for..."
- "Another project we're considering..."
- "Our [other department] needs..."
```

### Implicit Signals (Medium Value)
```
- High satisfaction score (9-10)
- Project delivered early/under budget
- Multiple positive interactions
- Referral provided
- Testimonial given
```

### Company Signals (Context)
```
From Company Research:
- Funding round announced
- New leadership (new decision makers)
- Expansion/hiring signals
- Competitor mentioned in market
- Industry growth trends
```

## Opportunity Scoring
```
explicit_signal = 40 points (max)
satisfaction_high = 20 points
project_success = 15 points
company_growth = 15 points
relationship_tenure = 10 points

total_opportunity_score = sum (max 100)
```

## Opportunity Alert
```
💰 UPSELL OPPORTUNITY

Client: {{client_name}}
Current Project: {{project_name}}
Opportunity Score: {{score}}/100

SIGNALS DETECTED
{{for signal in signals}}
- {{signal.type}}: "{{signal.evidence}}"
{{/for}}

POTENTIAL SERVICES
Based on signals, consider:
1. {{service_1}} - {{relevance_reason}}
2. {{service_2}} - {{relevance_reason}}

RECOMMENDED APPROACH
{{approach_recommendation}}

TIMING
{{timing_recommendation}}
```

## Upsell Approach Templates

### Service Inquiry Follow-Up
```
Subject: Re: Your question about {{service}}

Hi {{first_name}},

You mentioned being interested in {{service}}. I'd love to tell you more about how we approach this.

Would you have 15 minutes this week for a quick chat?
```

### High Satisfaction Outreach
```
Subject: Thank you + a thought

Hi {{first_name}},

Thank you again for the kind feedback on {{project_name}}!

I was thinking - based on what we accomplished together, {{service}} might be a natural next step for {{company}}.

Would you be open to exploring this?
```

### Post-Project Value Add
```
Subject: Idea for {{company}}

Hi {{first_name}},

Now that {{project_name}} is complete, I've been thinking about what would complement it well.

{{service}} could help you {{benefit}}.

Interested in learning more?
```

## Tracking
- Track upsell conversion rate
- Track revenue from upsells
- Track which signals convert best
