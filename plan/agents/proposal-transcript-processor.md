# Call Transcript Processor Agent

## Category
Proposal & Closing

## Purpose
Extract insights from meeting recordings

## Triggered By
Fathom webhook after call

## Outputs
- Call summary
- Key points discussed
- Pain points identified
- Budget/timeline mentioned
- Decision makers identified
- Objections raised
- Next steps agreed
- Action items (auto-created in Todoist/ClickUp)

## Process
1. Receive transcript from Fathom
2. Parse and analyze with AI
3. Extract structured data
4. Create action items in task management
5. Update lead record with insights
6. Generate call summary
7. Feed insights to proposal creation

## Database Tables
- `call_transcripts`
- `call_insights`
- `call_action_items`

## Integrations
- Fathom webhooks
- Todoist/ClickUp API
- Claude API (for analysis)

## Priority
Phase 3 - Closing & Proposals

## Dependencies
- Meeting Scheduler Agent (provides meeting context)

## Human-in-the-Loop
- Call summary reviewed for accuracy
- Action items may be edited before distribution

## Webhook
- Receives: `fathom/recording_ready`

## Extracted Data Structure
```json
{
  "summary": "Brief 2-3 sentence overview",
  "key_points": ["point1", "point2"],
  "pain_points": [
    {"pain": "description", "severity": "high/medium/low"}
  ],
  "budget": {"mentioned": true, "range": "$X-$Y", "timeline": "Q1 2025"},
  "decision_makers": [
    {"name": "John", "role": "CTO", "influence": "high"}
  ],
  "objections": [
    {"objection": "text", "response_given": "text", "resolved": true}
  ],
  "next_steps": ["step1", "step2"],
  "action_items": [
    {"task": "description", "owner": "us/them", "due": "date"}
  ],
  "sentiment": "positive/neutral/negative",
  "likelihood_to_close": 0.75
}
```
