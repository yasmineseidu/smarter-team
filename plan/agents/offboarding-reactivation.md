# Trigger-Based Reactivation Agent

## Category
Offboarding & Nurture

## Purpose
Re-engage cold leads based on triggers

## Triggers
- Job change (new role = new budget/authority)
- Funding round (company has money)
- Company growth (hiring, expansion)
- Leadership change (new decision maker)
- Competitor mentioned (shopping again)
- Industry event (relevant timing)

## Process
1. Monitor all leads in reactivation/nurture pools
2. Detect trigger events
3. Generate relevant outreach
4. Move back to campaign
5. Track reactivation results

## Database Tables
- `reactivation_triggers`
- `reactivation_campaigns`

## Integrations
- LinkedIn monitoring (job changes)
- News APIs (funding, leadership)
- Job board APIs (hiring signals)
- Intent data providers

## Priority
Phase 6 - Multi-Channel & Advanced

## Dependencies
- Long-Term Nurture Agent (provides pool of contacts)
- Company Research Agent (provides signal detection)
- Intent Signal Agent (provides intent data)

## Human-in-the-Loop
- High-value reactivation opportunities reviewed
- Outreach content may require approval

## Trigger Detection

### Job Change
```
Source: LinkedIn monitoring
Signal: Contact changed jobs
Action:
  - If same company, new role: Budget/authority change
  - If new company: Fresh opportunity
Outreach timing: 30-60 days after start
```

### Funding Round
```
Source: News APIs, Crunchbase
Signal: Company announced funding
Action: Budget available, likely hiring
Outreach timing: 2-4 weeks after announcement
```

### Company Growth
```
Source: Job postings, LinkedIn
Signal: Multiple new hires, new locations
Action: Expansion = new needs
Outreach timing: During growth phase
```

### Leadership Change
```
Source: News, LinkedIn
Signal: New C-suite or VP
Action: New decision maker, fresh slate
Outreach timing: 60-90 days after start
```

### Competitor Mentioned
```
Source: Conversation intelligence, news
Signal: Prospect mentions competitor
Action: May be shopping again
Outreach timing: Immediate (within 48 hours)
```

## Reactivation Templates

### Job Change - Same Company
```
Subject: Congrats on the new role!

Hi {{first_name}},

Congratulations on becoming {{new_title}} at {{company}}!

We chatted {{timeframe}} ago about {{topic}}. With your new role, I thought it might be worth reconnecting.

Would you be open to a quick chat about how we might help {{company}} with {{value_prop}}?
```

### Job Change - New Company
```
Subject: Congrats on {{new_company}}!

Hi {{first_name}},

I saw you joined {{new_company}} as {{new_title}} - congratulations!

We worked together at {{old_company}} on {{project/topic}}. I'd love to help {{new_company}} with similar challenges.

Would you have 15 minutes to catch up?
```

### Funding Round
```
Subject: Congrats on the funding!

Hi {{first_name}},

Congrats on {{company}}'s {{funding_amount}} {{round_type}} round! Exciting times.

With growth ahead, I thought it might be a good time to revisit {{our_service}}.

Would you be open to a quick chat about how we could support your expansion?
```

### Company Growth
```
Subject: {{company}} is growing fast!

Hi {{first_name}},

I've noticed {{company}} is expanding - {{specific_evidence}}. That's great to see!

Growing teams often need {{our_service}} to {{benefit}}.

Would it make sense to chat about how we could help?
```

### Leadership Change
```
Subject: Intro from [Your Name]

Hi {{first_name}},

Welcome to {{company}}! I'm [Your Name] - I help companies like yours with {{service}}.

I worked with {{company}} previously and thought you might be interested in {{relevant_context}}.

Would you have 15 minutes for a quick intro?
```

## Reactivation Metrics
- Reactivation attempt rate
- Reactivation success rate (moved to active pipeline)
- Revenue from reactivated leads
- Best performing triggers
- Time from trigger to conversion

## Cron Schedule
- Sunday at 8:00 PM - Scan for reactivation opportunities
- Daily - Process detected triggers
