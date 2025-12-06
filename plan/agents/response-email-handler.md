# Email Response Handler Agent

## Category
Response Handling

## Purpose
Process and respond to email replies

## Triggered By
Webhook from Instantly on reply

## Response Tiers

| Tier | Type | Action |
|------|------|--------|
| Auto-Send | Meeting confirmations, thank you, simple calendar links | Send immediately |
| Approval | Questions, objections, pricing discussions | Draft → Slack/Telegram → Wait for approval |
| Escalation | Complaints, complex technical, custom requests | Immediate notification + human handle |

## Process
1. Receive reply webhook
2. Classify response type (positive, negative, question, objection, out-of-office)
3. Check knowledge base and FAQ for relevant info
4. Draft response based on tier
5. For Approval tier: Send to Slack/Telegram
6. Wait for human approval/edit
7. Send approved response
8. Log everything in conversation history

## Special Handling
- Out-of-office: Parse return date, schedule follow-up
- Unsubscribe: Remove from campaigns, update status
- Referral: Create new lead from referral
- "Not the right person": Request correct contact

## Database Tables
- `email_responses`
- `response_drafts`
- `response_approvals`
- `conversation_history`

## Integrations
- Instantly webhooks
- Slack/Telegram (for approvals)
- Claude API (for classification and drafting)

## Priority
Phase 1 - MVP Foundation

## Dependencies
- Knowledge Base Agent (provides FAQ answers)
- Campaign metrics (provides conversation context)

## Human-in-the-Loop
- Approval tier: All require human approval
- Escalation tier: Human handles directly
- Auto-send tier: No approval needed

## Webhook
- Receives: `instantly/email_replied`
