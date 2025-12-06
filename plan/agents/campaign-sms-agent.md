# SMS Agent

## Category
Campaign & Outreach

## Purpose
Text message follow-ups for hot leads

## Triggers
- Phone number available
- High intent score (70+)
- Meeting no-show
- Proposal expiring

## Process
1. Verify phone number validity
2. Check SMS consent
3. Send SMS via API
4. Track delivery and response
5. Log in conversation history

## Database Tables
- `sms_messages`
- `sms_consent`

## Integrations
- SMS provider API (Twilio, etc.)

## Priority
Phase 6 - Multi-Channel & Advanced

## Dependencies
- Lead List Builder Agent (provides phone numbers)
- Intent Signal Agent (provides intent scores)
- Meeting Management (provides no-show events)
- Proposal Tracking (provides expiring proposals)

## Human-in-the-Loop
- SMS content templates approved in advance
- Individual SMS may require approval for complex situations

## Compliance
- TCPA compliance required
- Consent tracking mandatory
- Opt-out handling
