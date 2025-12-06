# Check-In Agent

## Category
Response Handling

## Purpose
Follow up with silent prospects

## Triggers
- No response in 2 days from last conversation
- Engaged but went silent

## Process
1. Check conversation history
2. Identify last interaction
3. Draft check-in email
4. Send if auto-approved
5. Track check-in count
6. After 14 check-ins → Move to reactivation pool

## Database Tables
- `check_in_logs`
- `check_in_templates`

## Integrations
- Instantly API (for sending)
- Internal conversation database

## Priority
Phase 2 - Intelligence Layer

## Dependencies
- Response Handler Agent (provides conversation context)
- Conversation Intelligence (provides engagement signals)

## Human-in-the-Loop
- Check-in templates approved in advance
- Individual check-ins may be auto-sent or require approval based on config

## Check-In Cadence
- Day 2: First check-in
- Day 5: Second check-in
- Day 8: Third check-in
- Day 12: Fourth check-in
- Continue every 3-4 days up to 14 total

## Reactivation Rule
- After 14 check-ins with no response → Move to REACTIVATION_POOL
- Status change logged with reason

## Cron Schedule
- Daily at 2:00 PM - Send check-ins to silent engaged leads
