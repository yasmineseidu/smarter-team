# Voice Message Agent

## Category
Campaign & Outreach

## Purpose
Voicemail drops for solopreneur outreach

## Triggers
- Hot lead not responding to email
- Post-meeting follow-up
- Proposal follow-up

## Process
1. Generate call task for you
2. Provide talking points
3. Log call attempt
4. Track outcome
5. Update lead status

## Database Tables
- `call_tasks`
- `call_logs`

## Integrations
- Task management (Todoist/ClickUp)
- Optional: AI voice generation (ElevenLabs)

## Priority
Phase 6 - Multi-Channel & Advanced

## Dependencies
- Lead Research Agent (provides talking points context)
- Meeting Management (provides meeting context)
- Proposal Tracking (provides proposal context)

## Human-in-the-Loop
- Calls are manual (this agent creates tasks, not automated calls)
- Talking points reviewed before call

## Output Format
```
CALL TASK: [Lead Name] at [Company]
PHONE: [Number]
CONTEXT: [Why calling - hot lead / follow-up / proposal]
TALKING POINTS:
- Point 1
- Point 2
- Point 3
DUE: [Time window]
```
