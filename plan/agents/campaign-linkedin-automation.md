# LinkedIn Automation Agent

## Category
Campaign & Outreach

## Purpose
Multi-channel outreach via Heyreach

## Triggers
- Hot lead (high intent score)
- No email response after sequence
- High-value target accounts

## Actions
- Connection request with note
- Follow-up message after connection
- Profile view (awareness)

## Process
1. Identify leads for LinkedIn outreach
2. Check if already connected
3. Send connection request via Heyreach
4. Track connection acceptance
5. Send follow-up message
6. Sync activity back to lead record

## Database Tables
- `linkedin_outreach`
- `linkedin_connections`
- `linkedin_messages`

## Integrations
- Heyreach API

## Priority
Phase 6 - Multi-Channel & Advanced

## Dependencies
- Lead List Builder Agent (provides LinkedIn URLs)
- Intent Signal Agent (provides intent scores)
- Campaign metrics (provides email response data)

## Human-in-the-Loop
- Connection request messages reviewed
- Follow-up messages may require approval

## Webhook
- Receives: `heyreach/connection_accepted`
- Receives: `heyreach/message_received`

## Rate Limits
- Connection requests: 20-30/day per account
- Messages: 50-100/day per account
