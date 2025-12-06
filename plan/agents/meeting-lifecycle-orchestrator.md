# Meeting Lifecycle Orchestrator

## Category
Meeting Management

## Purpose
Orchestrate and track the complete lifecycle of meetings from booking through follow-up

## Key Responsibilities
- Track all scheduled meetings across the system
- Coordinate meeting preparation and follow-up
- Monitor meeting outcomes and conversions
- Maintain complete meeting audit trail
- Generate meeting performance analytics

## Process
1. **Meeting Ingestion**
   - Capture all meetings from all sources
   - Deduplicate and consolidate meeting records
   - Link meetings to leads, campaigns, and opportunities
   - Establish meeting hierarchy and relationships

2. **Preparation Coordination**
   - Trigger meeting prep one hour before
   - Ensure all necessary materials are ready
   - Send reminder notifications
   - Check attendee readiness

3. **Execution Tracking**
   - Monitor meeting attendance
   - Track meeting duration and outcomes
   - Record key decisions and action items
   - Update meeting status in real-time

4. **Post-Meeting Actions**
   - Distribute meeting notes and recordings
   - Create follow-up tasks and reminders
   - Update CRM with meeting outcomes
   - Trigger next steps in sales process

## Database Tables
- `meetings` - Master meeting table
- `meeting_participants` - Attendee tracking
- `meeting_outcomes` - Results and decisions
- `meeting_analytics` - Performance metrics
- `meeting_timeline` - Complete audit trail

## Key Metrics
- Meeting book rate (from conversations)
- Meeting show rate
- Average meeting duration
- Conversion rate (meeting → next step)
- Meeting quality score
- Follow-up completion rate
- Revenue per meeting

## Triggers
- New meeting booked
- Meeting time approaching (1 hour)
- Meeting started
- Meeting ended
- Recording available
- Follow-up actions needed

## Outputs
- Comprehensive meeting dashboard
- Meeting performance reports
- Follow-up task lists
- Analytics on meeting effectiveness
- Calendar integration updates

## Integrations
- Cal.com (booking data)
- Zoom/Teams (attendance tracking)
- Fathom (recordings)
- ClickUp (task creation)
- Todoist (action items)
- CRM systems (outcome tracking)
- Email systems (notifications)

## Cron Schedule
- Every 5 minutes - Sync meeting data
- Every hour - Check upcoming meetings
- Real-time - Update meeting status
- Daily - Generate daily reports
- Weekly - Performance analysis

## Priority
Phase 1 - Critical for sales process

## Dependencies
- Meeting Scheduler (booking)
- Meeting Prep (preparation)
- Fathom Integration (recordings)
- Task Automation (follow-up)
- All communication channels

## Human-in-the-Loop
- Review high-value meeting outcomes
- Approve major follow-up actions
- Validate meeting quality scores
- Adjust meeting strategies

## Meeting Lifecycle Schema
```json
{
  "id": "uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T15:45:00Z",

  "meeting_details": {
    "title": "Discovery Call - Acme Corp",
    "description": "Initial discovery call to understand needs",
    "meeting_type": "discovery",
    "duration_minutes": 45,
    "scheduled_at": "2024-01-16T14:00:00Z",
    "timezone": "America/New_York",
    "meeting_link": "https://calendly.com/demo/meeting",
    "location": "Virtual (Zoom)"
  },

  "participants": [
    {
      "lead_id": "lead_123",
      "name": "John Smith",
      "email": "john@acme.com",
      "role": "decision_maker",
      "status": "confirmed",
      "joined_at": "2024-01-16T14:02:00Z",
      "left_at": "2024-01-16T14:45:00Z"
    },
    {
      "lead_id": "internal_rep_1",
      "name": "Sarah Johnson",
      "email": "sarah@smarterteam.ai",
      "role": "sales_rep",
      "status": "host",
      "joined_at": "2024-01-16T14:00:00Z",
      "left_at": "2024-01-16T14:47:00Z"
    }
  ],

  "lead_context": {
    "lead_id": "lead_123",
    "company": "Acme Corp",
    "industry": "SaaS",
    "deal_value": 50000,
    "stage": "qualified",
    "campaign_id": "camp_456"
  },

  "outcomes": {
    "status": "completed",
    "outcome": "positive",
    "next_step": "proposal_requested",
    "decisions": ["Budget confirmed", "Decision timeline: Q1"],
    "action_items": [
      "Send technical demo",
      "Schedule demo with technical team",
      "Prepare pricing proposal"
    ],
    "key_insights": [
      "Budget: $50k - $100k",
      "Timeline: Decision by end of Q1",
      "Key stakeholders: John (CEO), Lisa (CTO)"
    ]
  },

  "engagement_metrics": {
    "prep_completed": true,
    "prep_sent_at": "2024-01-16T13:00:00Z",
    "show_rate": 100,
    "participation_score": 0.95,
    "engagement_level": "high"
  },

  "recording": {
    "fathom_id": "fathom_789",
    "recording_url": "https://fathom.app/share/abc123",
    "transcript_available": true,
    "transcript_id": "trans_456"
  },

  "follow_up": {
    "status": "active",
    "next_action": "proposal",
    "next_action_date": "2024-01-17T10:00:00Z",
    "automated_tasks_created": 3,
    "manual_tasks_created": 1
  },

  "analytics": {
    "prep_time_minutes": 45,
    "talk_time_ratio": 0.4,
    "questions_asked": 12,
    "insights_generated": 8,
    "quality_score": 8.5
  },

  "status_history": [
    {
      "status": "scheduled",
      "timestamp": "2024-01-15T10:30:00Z",
      "changed_by": "system"
    },
    {
      "status": "preparing",
      "timestamp": "2024-01-16T13:00:00Z",
      "changed_by": "system"
    },
    {
      "status": "in_progress",
      "timestamp": "2024-01-16T14:00:00Z",
      "changed_by": "system"
    },
    {
      "status": "completed",
      "timestamp": "2024-01-16T14:47:00Z",
      "changed_by": "system"
    }
  ]
}
```

## Meeting Sources and Integration
```python
class MeetingSource(Enum):
    CALENDLY = "calendly"
    MANUAL = "manual"
    AI_SUGGESTED = "ai_suggested"
    REPLY_BOOKED = "reply_booked"
    INSTANTLY = "instantly"
    LINKEDIN = "linkedin"

async def ingest_meetings():
    """Collect meetings from all sources"""
    sources = [
        sync_calendly_meetings,
        sync_manual_meetings,
        detect_reply_booked_meetings,
        sync_ai_suggested_meetings
    ]

    all_meetings = []
    for source_func in sources:
        meetings = await source_func()
        all_meetings.extend(meetings)

    # Deduplicate and process
    processed_meetings = await deduplicate_meetings(all_meetings)

    for meeting in processed_meetings:
        await create_or_update_meeting(meeting)
        await trigger_meeting_workflow(meeting)
```

## Preparation Workflow
```python
async def prepare_meeting(meeting_id):
    """Coordinate all meeting preparation"""
    meeting = await get_meeting(meeting_id)

    # Generate prep materials
    prep_data = {
        'lead_research': await get_lead_research(meeting.lead_id),
        'company_research': await get_company_research(meeting.company_id),
        'conversation_history': await get_conversation_history(meeting.lead_id),
        'previous_meetings': await get_previous_meetings(meeting.lead_id),
        'talking_points': await generate_talking_points(meeting),
        'custom_content': await gather_custom_content(meeting)
    }

    # Create meeting prep package
    prep_package = await create_prep_package(meeting, prep_data)

    # Send to attendees
    await send_prep_package(meeting, prep_package)

    # Update meeting record
    await update_meeting(meeting_id, {
        'prep_completed': True,
        'prep_sent_at': datetime.utcnow(),
        'prep_package_id': prep_package.id
    })
```

## Post-Meeting Automation
```python
async def process_meeting_outcome(meeting_id):
    """Process meeting outcomes and trigger follow-ups"""
    meeting = await get_meeting(meeting_id)

    # Analyze meeting if transcript available
    if meeting.recording.get('transcript_id'):
        insights = await analyze_meeting_transcript(meeting)
        await update_meeting(meeting_id, {'insights': insights})

    # Create follow-up tasks
    follow_up_tasks = []

    if meeting.outcomes.get('action_items'):
        for item in meeting.outcomes['action_items']:
            if item.get('assignee') == 'sales':
                task = await create_clickup_task(item)
                follow_up_tasks.append(task)
            elif item.get('assignee') == 'personal':
                task = await create_todoist_task(item)
                follow_up_tasks.append(task)

    # Update lead status based on outcome
    await update_lead_status_from_meeting(meeting)

    # Schedule next steps
    if meeting.outcomes.get('next_step'):
        await schedule_next_step(meeting, meeting.outcomes['next_step'])

    # Send follow-up emails
    await send_follow_up_communications(meeting)

    # Update CRM systems
    await sync_to_all_crm_systems(meeting)
```

## Analytics and Reporting
```sql
-- Meeting performance by type
SELECT
    meeting_type,
    COUNT(*) as total_meetings,
    COUNT(CASE WHEN outcome = 'positive' THEN 1 END) * 100.0 / COUNT(*) as success_rate,
    AVG(engagement_metrics->>'participation_score') as avg_engagement,
    AVG(analytics->>'quality_score') as avg_quality,
    AVG(duration_minutes) as avg_duration
FROM meetings
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY meeting_type;

-- Meeting conversion funnel
SELECT
    stage,
    COUNT(*) as count,
    COUNT(*) * 100.0 / LAG(COUNT(*)) OVER (ORDER BY stage) as conversion_rate
FROM (
    SELECT
        CASE
            WHEN status = 'scheduled' THEN 'Scheduled'
            WHEN status = 'in_progress' THEN 'Attended'
            WHEN status = 'completed' AND outcome = 'positive' THEN 'Converted'
            WHEN status = 'completed' AND outcome = 'negative' THEN 'Lost'
            ELSE 'Other'
        END as stage,
        COUNT(*) as count
    FROM meetings
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY status, outcome
) AS meeting_funnel
GROUP BY stage
ORDER BY CASE stage
    WHEN 'Scheduled' THEN 1
    WHEN 'Attended' THEN 2
    WHEN 'Converted' THEN 3
    WHEN 'Lost' THEN 4
    ELSE 5
END;

-- Follow-up completion rate
SELECT
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as meetings_completed,
    COUNT(CASE WHEN follow_up->>'status' = 'completed' THEN 1 END) * 100.0 / COUNT(*) as completion_rate
FROM meetings
WHERE status = 'completed'
    AND created_at >= NOW() - INTERVAL '12 weeks'
GROUP BY week
ORDER BY week;
```

## Notification Templates
```python
# Meeting reminder
meeting_reminder_template = """
Meeting Reminder: {title}

Time: {time}
Link: {link}
Attendees: {attendees}

Prep materials: {prep_link}
""",

# Meeting summary
meeting_summary_template = """
Meeting Completed: {title}

Date: {date}
Duration: {duration_minutes} minutes
Outcome: {outcome}

Key Decisions:
{decisions}

Next Steps:
{next_steps}

Recording: {recording_link}
Transcript: {transcript_link}
""",

# Follow-up notification
follow_up_template = """
Follow-up Required: {title}

Deadline: {deadline}
Priority: {priority}

Task: {task_description}
"""

# Analytics alert
performance_alert_template = """
Meeting Performance Alert

Issue: {alert_type}
Details: {details}
Meeting ID: {meeting_id}
Recommendation: {recommendation}
"""
```

## API Endpoints
- `GET /api/meetings` - List all meetings
- `POST /api/meetings` - Create new meeting
- `GET /api/meetings/{id}` - Get meeting details
- `PUT /api/meetings/{id}` - Update meeting
- `POST /api/meetings/{id}/prep` - Trigger preparation
- `GET /api/meetings/analytics` - Meeting analytics
- `POST /api/meetings/{id}/outcome` - Record outcome
