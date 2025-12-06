# Campaign Creation Agent

## Category
Campaign & Outreach

## Purpose
Set up campaigns in Instantly

## Inputs
- Campaign name
- Target niche/persona
- Email sequence
- Sending schedule
- Daily send limits

## Outputs
- Campaign ID
- Configuration confirmation

## Process
1. Create campaign in Instantly via API
2. Configure sending settings
3. Set up warmup parameters
4. Link tracking domain
5. Store campaign ID and config in database

## Database Tables
- `campaigns`
- `campaign_configs`

## Integrations
- Instantly API

## Priority
Phase 1 - MVP Foundation

## Dependencies
- Data Validation Agent (provides validated leads)
- Copywriting Agent (provides email sequence)

## Human-in-the-Loop
- Campaign launch requires approval (Gate 1)
- Review: niche/persona fit, email copy, personalization strategy, sending schedule, target list

## Approval Flow
1. AI generates campaign config
2. Draft sent to Slack with preview
3. Human reviews and approves/rejects
4. If approved, campaign launches
5. If rejected, revision notes sent back to AI
