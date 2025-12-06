# Cold Email Copywriting Agent

## Category
Campaign & Outreach

## Purpose
Write email sequences for campaigns

## Inputs
- Niche/persona research
- Pain points
- Offer/service
- Tone guidelines
- Character limits (max 125 chars per email)

## Outputs
- Email sequence (3-5 emails)
- Subject lines
- A/B variants

## Constraints
- Must sound ultra human
- Non-salesy, not pushy
- Max 125 characters per email
- No corporate jargon
- Conversational tone

## Process
1. Pull persona and niche research
2. Generate email drafts
3. Create 2-3 variants per email for A/B testing
4. Human review queue
5. Store approved copy in database
6. Push to Instantly campaign

## Database Tables
- `email_copy`
- `email_variants`
- `copy_performance`

## Integrations
- Claude API (for generation)
- Instantly API (for pushing copy)

## Priority
Phase 1 - MVP Foundation

## Dependencies
- Niche Research Agent (provides niche context)
- Persona Research Agent (provides persona context)

## Human-in-the-Loop
- All email copy requires human review before approval
- Copy edits logged for learning

## A/B Testing
- 2-3 variants per email position
- Statistical significance testing before promoting winners
