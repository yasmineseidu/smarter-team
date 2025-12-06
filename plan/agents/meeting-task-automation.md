# Task Automation Agent

## Category
Meeting Management

## Purpose
Automate task extraction and management across ClickUp and Todoist platforms

## Key Responsibilities
- Extract action items from meeting transcripts and notes
- Create and manage tasks in ClickUp for team collaboration
- Create and manage tasks in Todoist for personal productivity
- Track task completion and follow-up reminders
- Maintain task-linking between systems for audit trail

## Process
1. **Action Item Extraction**
   - Parse meeting transcripts for action items and decisions
   - Identify task owners, due dates, and priorities from context
   - Classify tasks by type (follow-up, research, preparation, administrative)
   - Validate task completeness and clarity

2. **Task Routing & Creation**
   - Route team tasks to ClickUp with proper space/list assignment
   - Route personal tasks to Todoist with project categorization
   - Set task priorities based on meeting outcomes and urgency
   - Assign tasks to appropriate team members

3. **Cross-Platform Synchronization**
   - Link related tasks across ClickUp and Todoist
   - Maintain bidirectional sync for status updates
   - Handle task conflicts and duplicates intelligently
   - Archive completed tasks while preserving audit trail

4. **Follow-Up Management**
   - Monitor task due dates and send reminders
   - Escalate overdue tasks to appropriate stakeholders
   - Generate task completion reports
   - Identify bottlenecks in task execution

## Database Tables
- `task_automation_queue` - Queue of tasks to be processed
- `task_mappings` - Cross-platform task relationships
- `task_templates` - Reusable task templates for common actions
- `task_completion_audit` - Completion tracking and analytics

## Key Metrics
- Task extraction accuracy
- Task creation success rate
- Cross-platform sync reliability
- Task completion rate
- Average task completion time
- Follow-up reminder effectiveness

## Triggers
- New transcript available from Fathom
- Meeting outcome recorded
- Manual task creation request
- Task due date approaching
- Task status change

## Outputs
- Created tasks in ClickUp and Todoist
- Task relationship mappings
- Completion and status reports
- Overdue task alerts
- Task productivity analytics

## Integrations
- ClickUp API (task management)
- Todoist API (personal tasks)
- Meeting Lifecycle Orchestrator (task sources)
- Fathom Integration (transcript parsing)
- Notification systems (reminders)

## Cron Schedule
- Every 5 minutes - Process new task extraction requests
- Every 15 minutes - Sync task status across platforms
- Every hour - Check for due soon tasks
- Daily - Send task completion reports
- Weekly - Analyze task patterns and optimize

## Priority
Phase 1 - Essential for meeting follow-up

## Dependencies
- ClickUp account and API access
- Todoist account and API access
- Meeting Lifecycle Orchestrator
- Fathom Integration Agent

## Human-in-the-Loop
- Review complex task assignments
- Handle task conflicts that need resolution
- Validate high-priority task routing
- Adjust task categorization rules

## Task Automation Schema
```json
{
  "id": "uuid",
  "created_at": "2024-01-15T16:00:00Z",
  "updated_at": "2024-01-15T16:30:00Z",
  "meeting_id": "meeting_123",
  "transcript_id": "trans_456",
  "extraction_source": "fathom_transcript",
  "extraction_confidence": 0.92,

  "action_items": [
    {
      "id": "task_001",
      "description": "Send technical demo to Acme Corp",
      "assignee": {
        "name": "Sarah Johnson",
        "email": "sarah@smarterteam.ai",
        "role": "sales_engineer"
      },
      "due_date": "2024-01-17T17:00:00Z",
      "priority": "high",
      "type": "follow_up",
      "context": {
        "client": "Acme Corp",
        "meeting_date": "2024-01-16T14:00:00Z",
        "referenced_in_transcript": true,
        "timestamp_seconds": 1845
      },
      "dependencies": [],
      "estimated_duration_minutes": 30,
      "task_notes": "Prepare demo focusing on integration capabilities"
    },
    {
      "id": "task_002",
      "description": "Research competitor pricing models",
      "assignee": {
        "name": "Mike Chen",
        "email": "mike@smarterteam.ai",
        "role": "market_researcher"
      },
      "due_date": "2024-01-19T17:00:00Z",
      "priority": "medium",
      "type": "research",
      "context": {
        "client": "Acme Corp",
        "competitors_mentioned": ["CompetitorA", "CompetitorB"],
        "pricing_tier": "enterprise"
      },
      "dependencies": ["task_001"],
      "estimated_duration_minutes": 120
    }
  ],

  "platform_tasks": {
    "clickup_tasks": [
      {
        "task_id": "clickup_789",
        "action_item_id": "task_001",
        "space_id": "space_sales",
        "list_id": "list_followups",
        "status": "in_progress",
        "created_at": "2024-01-15T16:05:00Z",
        "updated_at": "2024-01-15T16:30:00Z",
        "clickup_url": "https://clickup.com/t/clickup_789"
      }
    ],
    "todoist_tasks": [
      {
        "task_id": "todoist_456",
        "action_item_id": "task_002",
        "project_id": "project_research",
        "parent_task_id": null,
        "status": "pending",
        "created_at": "2024-01-15T16:10:00Z",
        "todoist_url": "https://todoist.com/showTask?id=456"
      }
    ]
  },

  "sync_status": {
    "last_sync_at": "2024-01-15T16:30:00Z",
    "sync_errors": [],
    "pending_updates": 0,
    "conflict_resolution": {
      "has_conflicts": false,
      "resolved_count": 0,
      "manual_resolution_needed": 0
    }
  },

  "analytics": {
    "total_tasks_extracted": 2,
    "tasks_created_clickup": 1,
    "tasks_created_todoist": 1,
    "average_confidence_score": 0.92,
    "extraction_processing_time_seconds": 12,
    "task_distribution": {
      "follow_up": 1,
      "research": 1,
      "preparation": 0,
      "administrative": 0
    }
  }
}
```

## Task Extraction Logic
```python
async def extract_action_items(transcript_text: str, meeting_context: dict):
    """
    Extract action items from meeting transcript using NLP
    """
    extraction_prompt = f"""
    Analyze this meeting transcript and extract action items:

    Meeting Context:
    - Client: {meeting_context.get('client_name')}
    - Meeting Type: {meeting_context.get('meeting_type')}
    - Attendees: {meeting_context.get('attendees')}

    Transcript:
    {transcript_text}

    Extract action items with:
    1. Clear task description
    2. Assigned person (if mentioned)
    3. Due date (if implied or stated)
    4. Priority level (based on context)
    5. Task type (follow_up, research, preparation, administrative)
    6. Dependencies on other tasks
    7. Estimated duration

    Format as JSON array of action items.
    """

    # Use Claude API for extraction
    response = await anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": extraction_prompt
        }]
    )

    # Parse and validate action items
    action_items = parse_action_items(response.content)
    validated_items = await validate_action_items(action_items, meeting_context)

    return validated_items
```

## ClickUp Integration
```python
async def create_clickup_task(action_item: dict, meeting_context: dict):
    """
    Create task in ClickUp with proper space and list assignment
    """
    # Determine space and list based on task type
    space_mapping = {
        'follow_up': 'space_sales',
        'research': 'space_research',
        'preparation': 'space_delivery',
        'administrative': 'space_operations'
    }

    # Build ClickUp task payload
    clickup_payload = {
        "name": action_item['description'],
        "description": build_task_description(action_item, meeting_context),
        "priority": map_priority_to_clickup(action_item['priority']),
        "due_date": convert_to_timestamp(action_item['due_date']),
        "assignees": [get_clickup_user_id(action_item['assignee']['email'])],
        "status": "to do",
        "custom_fields": [
            {
                "id": "meeting_id_field",
                "value": meeting_context['meeting_id']
            },
            {
                "id": "client_field",
                "value": meeting_context['client_name']
            },
            {
                "id": "task_type_field",
                "value": action_item['type']
            }
        ]
    }

    # Create task in ClickUp
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.clickup.com/api/v2/list/{get_list_id(action_item)}/task",
            headers={"Authorization": f"Bearer {CLICKUP_API_KEY}"},
            json=clickup_payload
        )

        if response.status_code == 200:
            task_data = response.json()
            return {
                "clickup_task_id": task_data['id'],
                "clickup_url": task_data['url'],
                "status": "created"
            }
        else:
            raise Exception(f"ClickUp task creation failed: {response.text}")
```

## Todoist Integration
```python
async def create_todoist_task(action_item: dict, meeting_context: dict):
    """
    Create task in Todoist with project categorization
    """
    # Determine project based on task type
    project_mapping = {
        'follow_up': 'project_sales_followups',
        'research': 'project_market_research',
        'preparation': 'project_meeting_prep',
        'administrative': 'project_admin_tasks'
    }

    # Build Todoist task payload
    todoist_payload = {
        "content": action_item['description'],
        "description": build_task_description(action_item, meeting_context),
        "project_id": get_todoist_project_id(action_item['type']),
        "priority": map_priority_to_todoist(action_item['priority']),
        "due_string": format_due_date_todoist(action_item['due_date']),
        "labels": [
            action_item['type'],
            meeting_context['client_name'],
            "from_meeting"
        ]
    }

    # Create task in Todoist
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.todoist.com/rest/v2/tasks",
            headers={
                "Authorization": f"Bearer {TODOIST_API_KEY}",
                "Content-Type": "application/json"
            },
            json=todoist_payload
        )

        if response.status_code == 200:
            task_data = response.json()
            return {
                "todoist_task_id": task_data['id'],
                "todoist_url": task_data['url'],
                "status": "created"
            }
        else:
            raise Exception(f"Todoist task creation failed: {response.text}")
```

## Task Synchronization
```python
async def sync_task_status():
    """
    Synchronize task status between ClickUp and Todoist
    """
    # Get all active task mappings
    active_mappings = await get_active_task_mappings()

    for mapping in active_mappings:
        try:
            # Get ClickUp task status
            clickup_status = await get_clickup_task_status(mapping['clickup_task_id'])

            # Get Todoist task status
            todoist_status = await get_todoist_task_status(mapping['todoist_task_id'])

            # Check if sync needed
            if clickup_status['updated_at'] > mapping['last_sync_at']:
                await update_todoist_task_status(mapping['todoist_task_id'], clickup_status)
                await update_mapping_sync_time(mapping['id'])

            elif todoist_status['updated_at'] > mapping['last_sync_at']:
                await update_clickup_task_status(mapping['clickup_task_id'], todoist_status)
                await update_mapping_sync_time(mapping['id'])

        except Exception as e:
            await log_sync_error(mapping['id'], e)
            continue
```

## Follow-Up Reminders
```python
async def check_due_tasks():
    """
    Check for tasks due soon and send reminders
    """
    # Get tasks due in next 24 hours
    soon_tasks = await get_tasks_due_in_hours(24)

    for task in soon_tasks:
        # Determine reminder recipients
        recipients = await get_task_reminder_recipients(task)

        # Build reminder message
        reminder_message = build_reminder_message(task)

        # Send reminders via appropriate channels
        for recipient in recipients:
            if recipient['preferred_channel'] == 'email':
                await send_email_reminder(recipient['email'], reminder_message)
            elif recipient['preferred_channel'] == 'slack':
                await send_slack_reminder(recipient['slack_id'], reminder_message)

        # Log reminder sent
        await log_reminder_sent(task['id'], recipients)
```

## Task Analytics
```sql
-- Task completion by type
SELECT
    task_type,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as completion_rate,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) as avg_completion_hours
FROM task_automation_queue
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY task_type;

-- Cross-platform sync performance
SELECT
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as tasks_created,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) * 100.0 / COUNT(*) as sync_success_rate,
    AVG(sync_latency_seconds) as avg_sync_latency
FROM task_mappings
WHERE created_at >= NOW() - INTERVAL '12 weeks'
GROUP BY week;

-- Task extraction accuracy
SELECT
    DATE(created_at) as date,
    AVG(extraction_confidence) as avg_confidence,
    COUNT(*) as tasks_extracted,
    COUNT(CASE WHEN validated = true THEN 1 END) * 100.0 / COUNT(*) as validation_rate
FROM task_automation_queue
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY date
ORDER BY date;
```

## API Endpoints
- `POST /api/tasks/extract` - Extract tasks from transcript
- `POST /api/tasks/clickup` - Create ClickUp task
- `POST /api/tasks/todoist` - Create Todoist task
- `GET /api/tasks/sync` - Force sync between platforms
- `GET /api/tasks/due-soon` - Get tasks due soon
- `GET /api/tasks/analytics` - Task performance analytics
