# Project Management Agent

## Category
Project Delivery

## Purpose
Track and update project progress

## Runs
Every 2 hours

## Process
1. Sync Airtable, ClickUp, Todoist
2. Check milestone progress
3. Update project status
4. Identify blockers
5. Generate status summary

## Database Tables
- `projects`
- `project_milestones`
- `project_status`

## Integrations
- Airtable API
- ClickUp API
- Todoist API

## Priority
Phase 4 - Client Delivery

## Dependencies
- Internal Setup Agent (provides project infrastructure)

## Human-in-the-Loop
- Blockers flagged for resolution
- Status changes reviewed daily

## Sync Logic

### ClickUp → Database
```
For each task in ClickUp project:
  - Update completion status
  - Update assignee
  - Update due date
  - Calculate milestone progress
```

### Airtable → Database
```
For each project record:
  - Sync current phase
  - Sync client feedback
  - Update timestamps
```

### Database → All Systems
```
For status changes:
  - Push to Airtable
  - Update ClickUp custom fields
  - Update GHL pipeline stage
```

## Project Health Score
```
health_score = (
  on_time_score * 0.4 +
  budget_score * 0.3 +
  communication_score * 0.2 +
  client_satisfaction_score * 0.1
)

on_time_score = tasks_on_time / total_tasks * 100
budget_score = (budget - actual_cost) / budget * 100
communication_score = based on response times
client_satisfaction_score = from surveys
```

## Blocker Detection
```
IF task.due_date < today AND task.status != "complete"
THEN blocker_detected = TRUE

IF milestone.progress < expected_progress AND days_until_deadline < 3
THEN at_risk = TRUE

IF no_client_response_days >= 3
THEN waiting_on_client = TRUE
```

## Status Summary Format
```
PROJECT STATUS: {{project_name}}
Client: {{client_name}}
Phase: {{current_phase}}
Health: {{health_score}}/100

MILESTONES
✅ Milestone 1 - Complete
🔄 Milestone 2 - 60% (Due: {{date}})
⏳ Milestone 3 - Not started

BLOCKERS
- {{blocker_1}}
- {{blocker_2}}

NEXT ACTIONS
- {{action_1}}
- {{action_2}}
```

## Cron Schedule
- Every 2 hours - Sync all project data
- Daily at 8:00 AM - Generate daily status summary
