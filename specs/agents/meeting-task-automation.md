# Meeting Task Automation Agent - Production Specification

## Overview

**Agent Name:** `meeting_task_automation`

**Category:** Meeting Management

**Purpose:** Automatically extract action items from meeting transcripts and notes, create tasks in ClickUp (team) and Todoist (personal), maintain bidirectional synchronization, and send reminders for approaching deadlines.

**Priority:** Phase 1 - Essential for meeting follow-up

**Dependencies:**
- Meeting Fathom Integration Agent (transcript source)
- Meeting Notes Manager Agent (structured notes source)
- Delivery Project Management Agent (project task reporting)
- ClickUp API integration
- Todoist API integration
- Database: `task_automation_queue`, `task_mappings`, `task_templates`, `task_completion_audit`
- Zep memory (for context on task assignment patterns)

---

## System Prompt

```
You are the Task Automation Agent for Smarter Team, responsible for ensuring no action items fall through the cracks after meetings.

**Core Responsibilities:**
1. Extract action items from meeting transcripts using NLP with high precision
2. Identify task owners, due dates, and priorities from conversational context
3. Route tasks intelligently: team tasks to ClickUp, personal tasks to Todoist
4. Maintain bidirectional sync between platforms to prevent duplicates
5. Send timely reminders as deadlines approach
6. Generate completion analytics to track follow-through rates

**Task Extraction Logic:**
- Look for explicit commitments ("I'll send that by Friday", "Let me research...")
- Identify implicit tasks ("We need to...", "Someone should...")
- Recognize urgency signals ("ASAP", "urgent", "this week")
- Extract dependencies between tasks
- Classify task types: follow_up, research, preparation, administrative, technical

**Assignment Intelligence:**
- If person is mentioned by name, assign to them
- If "I/me/my" is used, assign to speaker
- If "we/us/our", flag for team assignment
- If "you/your", assign to other party (lead or team member)
- If ambiguous, route to meeting organizer with note for manual assignment

**Routing Rules:**
- Client-facing tasks → ClickUp (Space: Sales/Delivery based on stage)
- Internal research/prep → ClickUp (Space: Research/Operations)
- Personal todos (one person, no dependencies) → Todoist
- Multi-person tasks → ClickUp with assignees
- Tasks with subtasks → ClickUp (better hierarchy support)

**Priority Mapping:**
- "urgent", "ASAP", "today", "tomorrow" → HIGH priority
- "this week", "by Friday", explicit near-term dates → MEDIUM priority
- "eventually", "when you can", "next month" → LOW priority
- No time indicator + important client → MEDIUM (default)

**Sync Strategy:**
- Run bidirectional sync every 15 minutes
- Track status changes in both platforms
- If conflict (both changed), most recent update wins with audit log
- Handle platform-specific statuses (ClickUp: to do/in progress/done, Todoist: pending/completed)
- Archive completed tasks while preserving audit trail

**Reminder Timing:**
- 24 hours before due date → First reminder
- 4 hours before due date → Urgent reminder
- Overdue by 1 day → Escalation to manager/organizer
- Overdue by 3 days → Flag in weekly report

**Error Handling:**
- If extraction confidence < 0.7, flag for human review
- If assignee detection fails, default to meeting organizer
- If ClickUp API fails, queue tasks for retry every 5 minutes
- If Todoist API fails, continue with ClickUp and retry Todoist later
- Never lose extracted tasks: persist to database immediately

**Output Quality:**
- Task titles must be clear and actionable (start with verb)
- Include context from meeting in task description
- Link to transcript timestamp when available
- Add relevant tags: client name, meeting type, urgency
- Estimate duration based on task complexity
```

---

## Agent Architecture

### Base Class
Extends `BaseAgent` from `src/agents/base_agent.py`

### File Structure
```
src/agents/meeting_task_automation/
├── __init__.py           # Export MeetingTaskAutomationAgent
├── agent.py              # Main agent class
├── tools.py              # Tool functions for extraction and platform integration
├── prompts.py            # System prompt constants
├── schemas.py            # Pydantic models for requests/responses
├── exceptions.py         # Custom exceptions (ExtractionError, SyncConflictError, etc.)
└── utils.py              # Helper functions (priority mapping, routing logic)
```

### Class Definition

```python
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger


class TaskType(str, Enum):
    """Task classification types."""
    FOLLOW_UP = "follow_up"
    RESEARCH = "research"
    PREPARATION = "preparation"
    ADMINISTRATIVE = "administrative"
    TECHNICAL = "technical"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskPlatform(str, Enum):
    """Task management platforms."""
    CLICKUP = "clickup"
    TODOIST = "todoist"


class MeetingTaskAutomationAgent(BaseAgent):
    """
    Task automation agent for meeting action item extraction and management.

    Extracts action items from transcripts, creates tasks in ClickUp/Todoist,
    maintains sync, and sends reminders.
    """

    def __init__(self):
        super().__init__(
            name="meeting_task_automation",
            description="Automates task extraction and management from meetings"
        )

        # Register tools
        self.register_tool(
            self.extract_action_items,
            "extract_action_items",
            "Extract action items from meeting transcript using NLP"
        )
        self.register_tool(
            self.create_clickup_task,
            "create_clickup_task",
            "Create task in ClickUp with proper space and list assignment"
        )
        self.register_tool(
            self.create_todoist_task,
            "create_todoist_task",
            "Create task in Todoist with project categorization"
        )
        self.register_tool(
            self.assign_task_owner,
            "assign_task_owner",
            "Determine task assignee from conversation context"
        )
        self.register_tool(
            self.sync_task_status,
            "sync_task_status",
            "Bidirectional sync between ClickUp and Todoist"
        )
        self.register_tool(
            self.send_task_reminders,
            "send_task_reminders",
            "Notify assignees of approaching deadlines"
        )
        self.register_tool(
            self.generate_task_report,
            "generate_task_report",
            "Generate task completion analytics"
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt defined above."""
        return """You are the Task Automation Agent for Smarter Team..."""  # Full prompt

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process task automation workflows.

        Supported task types:
        - extract_tasks: Extract action items from transcript
        - sync_platforms: Run bidirectional sync between ClickUp and Todoist
        - send_reminders: Check for upcoming deadlines and send reminders
        - generate_report: Create completion analytics
        """
        task_type = task.get("type")

        if task_type == "extract_tasks":
            return await self._extract_and_create_tasks(task)
        elif task_type == "sync_platforms":
            return await self._sync_all_tasks()
        elif task_type == "send_reminders":
            return await self._check_and_send_reminders()
        elif task_type == "generate_report":
            return await self._generate_completion_report(task.get("date_range"))
        else:
            raise ValueError(f"Unknown task type: {task_type}")
```

---

## Tool Definitions

### 1. `extract_action_items`

**Description:** Extract action items from meeting transcript using Claude API with NLP.

**Parameters:**
```python
from pydantic import BaseModel, Field

class ExtractActionItemsParams(BaseModel):
    transcript_text: str = Field(..., description="Full meeting transcript text")
    meeting_context: dict[str, Any] = Field(..., description="Meeting metadata")
    meeting_id: str = Field(..., description="UUID of meeting in database")
    attendees: list[dict[str, str]] = Field(..., description="List of attendees with names and emails")
```

**Returns:**
```python
class ActionItem(BaseModel):
    id: str  # Generated UUID
    description: str  # Clear, actionable task description
    assignee: dict[str, str] | None  # {"name": "...", "email": "...", "role": "..."}
    due_date: datetime | None  # Extracted or inferred due date
    priority: TaskPriority  # HIGH, MEDIUM, LOW, CRITICAL
    task_type: TaskType  # follow_up, research, preparation, etc.
    context: dict[str, Any]  # Meeting context, client info, timestamp in transcript
    dependencies: list[str]  # IDs of tasks that must complete first
    estimated_duration_minutes: int | None  # Estimated completion time
    confidence_score: float  # 0.0-1.0 extraction confidence
    task_notes: str | None  # Additional context from transcript
    transcript_timestamp: int | None  # Seconds into transcript where mentioned

class ExtractActionItemsResponse(BaseModel):
    action_items: list[ActionItem]
    total_extracted: int
    high_confidence_count: int  # confidence >= 0.8
    needs_review: list[ActionItem]  # confidence < 0.7
    extraction_metadata: dict[str, Any]
```

**Implementation:**
```python
async def extract_action_items(
    self,
    params: ExtractActionItemsParams
) -> ExtractActionItemsResponse:
    """
    Extract action items from transcript using Claude API.

    Process:
    1. Construct extraction prompt with meeting context
    2. Call Claude API with structured output format
    3. Parse and validate action items
    4. Assign confidence scores based on clarity
    5. Identify dependencies between tasks
    6. Return structured action items

    NLP Prompt Structure:
    - Include meeting type, attendees, client name
    - Provide example action items for consistency
    - Request JSON output with specific fields
    - Ask Claude to identify task owner, due date, priority
    - Request confidence score for each extraction
    """
    extraction_prompt = f"""
    Analyze this meeting transcript and extract all action items.

    Meeting Context:
    - Client: {params.meeting_context.get('client_name')}
    - Meeting Type: {params.meeting_context.get('meeting_type')}
    - Date: {params.meeting_context.get('meeting_date')}
    - Attendees: {', '.join([a['name'] for a in params.attendees])}

    Transcript:
    {params.transcript_text}

    Extract action items with:
    1. Clear task description (start with verb: "Send...", "Research...", "Schedule...")
    2. Assigned person (if mentioned explicitly or implied by "I/me/my")
    3. Due date (if stated or implied - "by Friday", "this week", etc.)
    4. Priority level (urgent/ASAP = HIGH, this week = MEDIUM, eventually = LOW)
    5. Task type (follow_up, research, preparation, administrative, technical)
    6. Dependencies (if task depends on another task completing first)
    7. Estimated duration in minutes
    8. Confidence score (0.0-1.0) for how certain you are this is an action item
    9. Transcript timestamp in seconds (if you can identify when it was mentioned)

    Format as JSON array of action items matching this structure:
    {{
      "description": "Send technical demo to Acme Corp",
      "assignee": {{"name": "Sarah Johnson", "email": "sarah@smarterteam.ai"}},
      "due_date": "2024-01-17T17:00:00Z",
      "priority": "high",
      "type": "follow_up",
      "estimated_duration_minutes": 30,
      "confidence_score": 0.95,
      "notes": "Focus on integration capabilities as mentioned by client"
    }}

    Only extract items that are actual commitments or tasks, not general discussion points.
    """

    # Use Claude API for extraction
    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240229",
        max_tokens=4000,
        messages=[{"role": "user", "content": extraction_prompt}]
    )

    # Parse and validate action items
    action_items = self._parse_and_validate_action_items(
        response.content,
        params.meeting_context,
        params.attendees
    )

    # Categorize by confidence
    high_confidence = [item for item in action_items if item.confidence_score >= 0.8]
    needs_review = [item for item in action_items if item.confidence_score < 0.7]

    self.logger.info(
        "Action items extracted",
        extra={
            "meeting_id": params.meeting_id,
            "total": len(action_items),
            "high_confidence": len(high_confidence),
            "needs_review": len(needs_review)
        }
    )

    return ExtractActionItemsResponse(
        action_items=action_items,
        total_extracted=len(action_items),
        high_confidence_count=len(high_confidence),
        needs_review=needs_review,
        extraction_metadata={
            "model": "claude-3-5-sonnet",
            "transcript_length": len(params.transcript_text),
            "extraction_timestamp": datetime.utcnow().isoformat()
        }
    )
```

**Error Handling:**
- `ExtractionError`: Claude API call fails (retry with exponential backoff, max 3 times)
- `ValidationError`: Parsed data doesn't match schema (log and skip invalid items)
- `TimeoutError`: API timeout (increase timeout to 60s and retry once)

---

### 2. `create_clickup_task`

**Description:** Create task in ClickUp with proper space and list assignment based on task type.

**Parameters:**
```python
class CreateClickUpTaskParams(BaseModel):
    action_item: ActionItem
    meeting_context: dict[str, Any]
    space_mapping: dict[str, str] | None = None  # Override default space mapping
```

**Returns:**
```python
class CreateClickUpTaskResponse(BaseModel):
    clickup_task_id: str  # ClickUp task ID
    clickup_url: str  # Direct URL to task
    space_id: str
    list_id: str
    status: str  # "created" or "failed"
    created_at: datetime
```

**Implementation:**
```python
async def create_clickup_task(
    self,
    params: CreateClickUpTaskParams
) -> CreateClickUpTaskResponse:
    """
    Create task in ClickUp with intelligent routing.

    Space Mapping (default):
    - follow_up → Sales Follow-ups (space_sales)
    - research → Market Research (space_research)
    - preparation → Meeting Prep (space_delivery)
    - administrative → Operations (space_operations)
    - technical → Engineering (space_engineering)

    Custom Fields:
    - meeting_id: Link back to source meeting
    - client_name: For filtering by client
    - task_type: For analytics
    - extracted_from: "meeting_transcript"
    - confidence_score: Extraction confidence
    """
    # Determine space and list based on task type
    space_id = self._get_space_id(params.action_item.task_type, params.space_mapping)
    list_id = self._get_list_id(space_id, params.action_item.priority)

    # Build ClickUp task payload
    clickup_payload = {
        "name": params.action_item.description,
        "description": self._build_task_description(
            params.action_item,
            params.meeting_context
        ),
        "priority": self._map_priority_to_clickup(params.action_item.priority),
        "due_date": int(params.action_item.due_date.timestamp() * 1000) if params.action_item.due_date else None,
        "assignees": [self._get_clickup_user_id(params.action_item.assignee["email"])] if params.action_item.assignee else [],
        "status": "to do",
        "tags": [
            params.meeting_context.get("client_name"),
            params.action_item.task_type,
            "from_meeting"
        ],
        "custom_fields": [
            {"id": "meeting_id_field", "value": params.meeting_context["meeting_id"]},
            {"id": "client_field", "value": params.meeting_context["client_name"]},
            {"id": "task_type_field", "value": params.action_item.task_type},
            {"id": "confidence_field", "value": params.action_item.confidence_score}
        ]
    }

    # Create task in ClickUp
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.clickup.com/api/v2/list/{list_id}/task",
            headers={
                "Authorization": settings.CLICKUP_API_KEY,
                "Content-Type": "application/json"
            },
            json=clickup_payload,
            timeout=30.0
        )

        if response.status_code == 200:
            task_data = response.json()

            self.logger.info(
                "ClickUp task created",
                extra={
                    "task_id": task_data["id"],
                    "action_item_id": params.action_item.id,
                    "space": space_id,
                    "assignee": params.action_item.assignee.get("email") if params.action_item.assignee else None
                }
            )

            return CreateClickUpTaskResponse(
                clickup_task_id=task_data["id"],
                clickup_url=task_data["url"],
                space_id=space_id,
                list_id=list_id,
                status="created",
                created_at=datetime.utcnow()
            )
        else:
            self.logger.error(
                "ClickUp task creation failed",
                extra={
                    "status_code": response.status_code,
                    "error": response.text,
                    "action_item_id": params.action_item.id
                }
            )
            raise ClickUpAPIError(f"Failed to create task: {response.text}")
```

**Error Handling:**
- `ClickUpAPIError`: API call fails (retry with backoff, max 3 times)
- `UserNotFoundError`: Assignee email not found in ClickUp (assign to default user)
- `SpaceNotFoundError`: Invalid space ID (use default space)

**Priority Mapping:**
```python
def _map_priority_to_clickup(self, priority: TaskPriority) -> int:
    """Map internal priority to ClickUp priority."""
    return {
        TaskPriority.CRITICAL: 1,  # Urgent
        TaskPriority.HIGH: 2,      # High
        TaskPriority.MEDIUM: 3,    # Normal
        TaskPriority.LOW: 4        # Low
    }[priority]
```

---

### 3. `create_todoist_task`

**Description:** Create task in Todoist with project categorization for personal tasks.

**Parameters:**
```python
class CreateTodoistTaskParams(BaseModel):
    action_item: ActionItem
    meeting_context: dict[str, Any]
    project_mapping: dict[str, str] | None = None
```

**Returns:**
```python
class CreateTodoistTaskResponse(BaseModel):
    todoist_task_id: str
    todoist_url: str
    project_id: str
    status: str
    created_at: datetime
```

**Implementation:**
```python
async def create_todoist_task(
    self,
    params: CreateTodoistTaskParams
) -> CreateTodoistTaskResponse:
    """
    Create task in Todoist for personal task management.

    Project Mapping:
    - follow_up → Sales Follow-ups (project_sales)
    - research → Market Research (project_research)
    - preparation → Meeting Prep (project_meetings)
    - administrative → Admin Tasks (project_admin)

    Labels:
    - Task type (follow_up, research, etc.)
    - Client name
    - Priority level
    - from_meeting (special label)
    """
    project_id = self._get_todoist_project_id(
        params.action_item.task_type,
        params.project_mapping
    )

    # Build Todoist task payload
    todoist_payload = {
        "content": params.action_item.description,
        "description": self._build_task_description(
            params.action_item,
            params.meeting_context
        ),
        "project_id": project_id,
        "priority": self._map_priority_to_todoist(params.action_item.priority),
        "due_string": self._format_due_date_todoist(params.action_item.due_date) if params.action_item.due_date else None,
        "labels": [
            params.action_item.task_type,
            params.meeting_context.get("client_name"),
            f"priority_{params.action_item.priority.lower()}",
            "from_meeting"
        ]
    }

    # Create task in Todoist
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.todoist.com/rest/v2/tasks",
            headers={
                "Authorization": f"Bearer {settings.TODOIST_API_KEY}",
                "Content-Type": "application/json"
            },
            json=todoist_payload,
            timeout=30.0
        )

        if response.status_code == 200:
            task_data = response.json()

            self.logger.info(
                "Todoist task created",
                extra={
                    "task_id": task_data["id"],
                    "action_item_id": params.action_item.id,
                    "project": project_id
                }
            )

            return CreateTodoistTaskResponse(
                todoist_task_id=task_data["id"],
                todoist_url=task_data["url"],
                project_id=project_id,
                status="created",
                created_at=datetime.utcnow()
            )
        else:
            self.logger.error(
                "Todoist task creation failed",
                extra={
                    "status_code": response.status_code,
                    "error": response.text
                }
            )
            raise TodoistAPIError(f"Failed to create task: {response.text}")
```

**Priority Mapping:**
```python
def _map_priority_to_todoist(self, priority: TaskPriority) -> int:
    """Map internal priority to Todoist priority."""
    return {
        TaskPriority.CRITICAL: 4,  # p1 in Todoist
        TaskPriority.HIGH: 3,      # p2
        TaskPriority.MEDIUM: 2,    # p3
        TaskPriority.LOW: 1        # p4
    }[priority]
```

---

### 4. `assign_task_owner`

**Description:** Determine task assignee from conversation context using NLP patterns.

**Parameters:**
```python
class AssignTaskOwnerParams(BaseModel):
    task_description: str
    transcript_context: str  # Surrounding text from transcript
    attendees: list[dict[str, str]]
    meeting_organizer: dict[str, str]
```

**Returns:**
```python
class AssignTaskOwnerResponse(BaseModel):
    assignee: dict[str, str] | None  # {"name": "...", "email": "...", "role": "..."}
    confidence: float  # 0.0-1.0
    reasoning: str  # Why this person was assigned
    needs_manual_review: bool
```

**Implementation:**
```python
async def assign_task_owner(
    self,
    params: AssignTaskOwnerParams
) -> AssignTaskOwnerResponse:
    """
    Identify task assignee using NLP patterns.

    Pattern Matching:
    - "I'll..." → Speaker (requires speaker identification)
    - "You should..." → Other party
    - "[Name] will..." → Explicit assignment
    - "We need to..." → Team task (assign to organizer)
    - Ambiguous → Assign to organizer with manual review flag
    """
    # Use Claude to identify assignee from context
    assignment_prompt = f"""
    Identify who should be assigned this task based on the conversation context.

    Task: {params.task_description}

    Context from transcript:
    {params.transcript_context}

    Meeting attendees:
    {json.dumps(params.attendees, indent=2)}

    Meeting organizer:
    {json.dumps(params.meeting_organizer, indent=2)}

    Determine:
    1. Who should be assigned this task
    2. Confidence level (0.0-1.0)
    3. Reasoning for the assignment

    Return JSON format:
    {{
      "assignee_email": "email@example.com",
      "confidence": 0.9,
      "reasoning": "Person explicitly said 'I'll handle that'"
    }}

    If assignment is unclear, return:
    {{
      "assignee_email": "{params.meeting_organizer['email']}",
      "confidence": 0.4,
      "reasoning": "Ambiguous assignment, defaulting to organizer"
    }}
    """

    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240229",
        max_tokens=500,
        messages=[{"role": "user", "content": assignment_prompt}]
    )

    assignment_data = json.loads(response.content[0].text)

    # Find full attendee info from email
    assignee = next(
        (a for a in params.attendees if a["email"] == assignment_data["assignee_email"]),
        params.meeting_organizer
    )

    needs_review = assignment_data["confidence"] < 0.7

    return AssignTaskOwnerResponse(
        assignee=assignee,
        confidence=assignment_data["confidence"],
        reasoning=assignment_data["reasoning"],
        needs_manual_review=needs_review
    )
```

---

### 5. `sync_task_status`

**Description:** Bidirectional synchronization between ClickUp and Todoist to keep statuses aligned.

**Parameters:**
```python
class SyncTaskStatusParams(BaseModel):
    sync_window_hours: int = 24  # Only sync tasks updated in last N hours
    resolve_conflicts: bool = True  # Auto-resolve conflicts with "most recent wins"
```

**Returns:**
```python
class SyncTaskStatusResponse(BaseModel):
    synced_count: int
    conflicts_resolved: int
    conflicts_pending: int
    errors: list[dict[str, Any]]
    sync_timestamp: datetime
```

**Implementation:**
```python
async def sync_task_status(
    self,
    params: SyncTaskStatusParams
) -> SyncTaskStatusResponse:
    """
    Sync task status between ClickUp and Todoist.

    Process:
    1. Get all active task mappings from database
    2. Fetch updated tasks from ClickUp (modified in last N hours)
    3. Fetch updated tasks from Todoist (modified in last N hours)
    4. Compare timestamps to detect conflicts
    5. Resolve conflicts (most recent update wins)
    6. Push status updates to both platforms
    7. Update database with sync timestamp

    Status Mapping:
    ClickUp → Todoist:
    - to do → pending
    - in progress → pending
    - complete → completed
    - closed → completed

    Todoist → ClickUp:
    - pending → to do (if not started)
    - completed → complete
    """
    # Get active task mappings
    mappings = await self._get_active_task_mappings(params.sync_window_hours)

    synced = 0
    conflicts_resolved = 0
    conflicts_pending = 0
    errors = []

    for mapping in mappings:
        try:
            # Fetch current status from both platforms
            clickup_task = await self._get_clickup_task(mapping["clickup_task_id"])
            todoist_task = await self._get_todoist_task(mapping["todoist_task_id"])

            # Check for status mismatch
            if self._needs_sync(clickup_task, todoist_task, mapping):
                # Determine which platform has newer update
                if clickup_task["updated_at"] > todoist_task["updated_at"]:
                    # ClickUp is newer, update Todoist
                    await self._update_todoist_status(
                        mapping["todoist_task_id"],
                        clickup_task["status"]
                    )
                    synced += 1
                elif todoist_task["updated_at"] > clickup_task["updated_at"]:
                    # Todoist is newer, update ClickUp
                    await self._update_clickup_status(
                        mapping["clickup_task_id"],
                        todoist_task["status"]
                    )
                    synced += 1
                else:
                    # Same timestamp, log conflict
                    if params.resolve_conflicts:
                        # Default to ClickUp (team system takes precedence)
                        await self._update_todoist_status(
                            mapping["todoist_task_id"],
                            clickup_task["status"]
                        )
                        conflicts_resolved += 1
                    else:
                        conflicts_pending += 1

                # Update sync timestamp in database
                await self._update_mapping_sync_time(mapping["id"])

        except Exception as e:
            self.logger.error(
                "Sync error for task mapping",
                extra={"mapping_id": mapping["id"], "error": str(e)}
            )
            errors.append({
                "mapping_id": mapping["id"],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })

    return SyncTaskStatusResponse(
        synced_count=synced,
        conflicts_resolved=conflicts_resolved,
        conflicts_pending=conflicts_pending,
        errors=errors,
        sync_timestamp=datetime.utcnow()
    )
```

---

### 6. `send_task_reminders`

**Description:** Check for tasks with approaching deadlines and send reminders to assignees.

**Parameters:**
```python
class SendTaskRemindersParams(BaseModel):
    reminder_window_hours: int = 24  # Remind for tasks due in next N hours
    include_overdue: bool = True
```

**Returns:**
```python
class SendTaskRemindersResponse(BaseModel):
    reminders_sent: int
    overdue_escalations: int
    notification_failures: int
    reminder_details: list[dict[str, Any]]
```

**Implementation:**
```python
async def send_task_reminders(
    self,
    params: SendTaskRemindersParams
) -> SendTaskRemindersResponse:
    """
    Send reminders for upcoming and overdue tasks.

    Reminder Tiers:
    - 24 hours before: Email reminder (standard)
    - 4 hours before: Urgent email + Slack notification
    - Overdue by 1 day: Escalation to manager
    - Overdue by 3 days: Weekly report flag

    Notification Channels:
    - Email (always)
    - Slack (if urgent or overdue)
    - SMS (if critical priority only)
    """
    now = datetime.utcnow()
    reminder_cutoff = now + timedelta(hours=params.reminder_window_hours)

    # Get tasks due soon
    upcoming_tasks = await self._get_tasks_due_between(now, reminder_cutoff)

    # Get overdue tasks
    overdue_tasks = await self._get_overdue_tasks() if params.include_overdue else []

    reminders_sent = 0
    overdue_escalations = 0
    failures = 0
    details = []

    # Process upcoming tasks
    for task in upcoming_tasks:
        try:
            hours_until_due = (task["due_date"] - now).total_seconds() / 3600

            if hours_until_due <= 4:
                # Urgent reminder
                await self._send_urgent_reminder(task)
                details.append({
                    "task_id": task["id"],
                    "type": "urgent",
                    "hours_until_due": round(hours_until_due, 1)
                })
            else:
                # Standard reminder
                await self._send_standard_reminder(task)
                details.append({
                    "task_id": task["id"],
                    "type": "standard",
                    "hours_until_due": round(hours_until_due, 1)
                })

            reminders_sent += 1

        except Exception as e:
            self.logger.error(
                "Reminder send failed",
                extra={"task_id": task["id"], "error": str(e)}
            )
            failures += 1

    # Process overdue tasks
    for task in overdue_tasks:
        try:
            days_overdue = (now - task["due_date"]).days

            if days_overdue >= 3:
                # Escalate to weekly report
                await self._flag_for_weekly_report(task)
            elif days_overdue >= 1:
                # Escalate to manager
                await self._escalate_to_manager(task)

            overdue_escalations += 1
            details.append({
                "task_id": task["id"],
                "type": "overdue_escalation",
                "days_overdue": days_overdue
            })

        except Exception as e:
            self.logger.error(
                "Overdue escalation failed",
                extra={"task_id": task["id"], "error": str(e)}
            )
            failures += 1

    return SendTaskRemindersResponse(
        reminders_sent=reminders_sent,
        overdue_escalations=overdue_escalations,
        notification_failures=failures,
        reminder_details=details
    )
```

---

### 7. `generate_task_report`

**Description:** Generate analytics on task completion rates, average time to complete, and bottlenecks.

**Parameters:**
```python
class GenerateTaskReportParams(BaseModel):
    date_range: tuple[datetime, datetime]
    group_by: str = "task_type"  # "task_type", "assignee", "client", "priority"
    include_charts: bool = False
```

**Returns:**
```python
class GenerateTaskReportResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    completion_rate: float  # Percentage
    average_completion_time_hours: float
    overdue_tasks: int
    tasks_by_category: dict[str, dict[str, Any]]
    bottlenecks: list[dict[str, Any]]
    report_url: str | None  # If saved to file storage
```

**Implementation:**
```python
async def generate_task_report(
    self,
    params: GenerateTaskReportParams
) -> GenerateTaskReportResponse:
    """
    Generate comprehensive task completion analytics.

    Metrics Tracked:
    - Total tasks created in period
    - Completion rate (%)
    - Average time from creation to completion
    - Overdue task count
    - Breakdown by category (type, assignee, client, priority)
    - Bottleneck identification (tasks stuck in progress)
    """
    start_date, end_date = params.date_range

    # Query task data
    tasks = await self._get_tasks_in_range(start_date, end_date)

    # Calculate metrics
    total = len(tasks)
    completed = len([t for t in tasks if t["status"] == "completed"])
    completion_rate = (completed / total * 100) if total > 0 else 0.0

    # Average completion time (only for completed tasks)
    completed_tasks = [t for t in tasks if t["status"] == "completed"]
    avg_completion_hours = (
        sum([
            (t["completed_at"] - t["created_at"]).total_seconds() / 3600
            for t in completed_tasks
        ]) / len(completed_tasks)
    ) if completed_tasks else 0.0

    # Overdue tasks
    now = datetime.utcnow()
    overdue = len([
        t for t in tasks
        if t["due_date"] and t["due_date"] < now and t["status"] != "completed"
    ])

    # Group by category
    tasks_by_category = self._group_tasks(tasks, params.group_by)

    # Identify bottlenecks (tasks in progress > 7 days)
    bottlenecks = [
        {
            "task_id": t["id"],
            "description": t["description"],
            "assignee": t["assignee"],
            "days_in_progress": (now - t["started_at"]).days
        }
        for t in tasks
        if t["status"] == "in_progress" and (now - t["started_at"]).days > 7
    ]

    return GenerateTaskReportResponse(
        total_tasks=total,
        completed_tasks=completed,
        completion_rate=round(completion_rate, 2),
        average_completion_time_hours=round(avg_completion_hours, 2),
        overdue_tasks=overdue,
        tasks_by_category=tasks_by_category,
        bottlenecks=bottlenecks,
        report_url=None  # Future: save to S3 or similar
    )
```

---

## Database Schema

### Table: `task_automation_queue`

Stores all extracted action items before platform creation.

```sql
CREATE TABLE task_automation_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id),
    transcript_id UUID REFERENCES meeting_transcripts(id),
    extraction_source TEXT NOT NULL,  -- 'fathom_transcript', 'meeting_notes', 'manual'
    extraction_confidence DECIMAL(3, 2) NOT NULL CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),

    -- Action item details
    description TEXT NOT NULL,
    assignee_name TEXT,
    assignee_email TEXT,
    assignee_role TEXT,
    due_date TIMESTAMPTZ,
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    task_type TEXT NOT NULL CHECK (task_type IN ('follow_up', 'research', 'preparation', 'administrative', 'technical')),
    estimated_duration_minutes INTEGER,
    task_notes TEXT,
    transcript_timestamp INTEGER,  -- Seconds into transcript

    -- Context
    meeting_context JSONB NOT NULL,
    dependencies JSONB,  -- Array of task IDs

    -- Platform routing
    target_platform TEXT CHECK (target_platform IN ('clickup', 'todoist', 'both')),
    needs_manual_review BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,

    -- Indexes
    CONSTRAINT fk_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE INDEX idx_task_queue_meeting_id ON task_automation_queue(meeting_id);
CREATE INDEX idx_task_queue_processed ON task_automation_queue(processed_at) WHERE processed_at IS NULL;
CREATE INDEX idx_task_queue_confidence ON task_automation_queue(extraction_confidence);
CREATE INDEX idx_task_queue_assignee ON task_automation_queue(assignee_email);
```

### Table: `task_mappings`

Cross-platform task relationships and sync status.

```sql
CREATE TABLE task_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source action item
    action_item_id UUID NOT NULL REFERENCES task_automation_queue(id),

    -- Platform task IDs
    clickup_task_id TEXT,
    clickup_url TEXT,
    todoist_task_id TEXT,
    todoist_url TEXT,

    -- Sync status
    sync_status TEXT NOT NULL DEFAULT 'synced' CHECK (sync_status IN ('synced', 'conflict', 'error')),
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    sync_latency_seconds INTEGER,

    -- Conflict resolution
    conflict_details JSONB,
    conflict_resolved_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT at_least_one_platform CHECK (
        clickup_task_id IS NOT NULL OR todoist_task_id IS NOT NULL
    )
);

CREATE INDEX idx_task_mappings_action_item ON task_mappings(action_item_id);
CREATE INDEX idx_task_mappings_clickup ON task_mappings(clickup_task_id) WHERE clickup_task_id IS NOT NULL;
CREATE INDEX idx_task_mappings_todoist ON task_mappings(todoist_task_id) WHERE todoist_task_id IS NOT NULL;
CREATE INDEX idx_task_mappings_sync_status ON task_mappings(sync_status) WHERE sync_status != 'synced';
```

### Table: `task_templates`

Reusable task templates for common meeting action items.

```sql
CREATE TABLE task_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Template details
    template_name TEXT NOT NULL,
    description_template TEXT NOT NULL,  -- Can include variables like {{client_name}}
    task_type TEXT NOT NULL CHECK (task_type IN ('follow_up', 'research', 'preparation', 'administrative', 'technical')),
    default_priority TEXT NOT NULL CHECK (default_priority IN ('low', 'medium', 'high', 'critical')),
    default_duration_minutes INTEGER,

    -- Assignment rules
    default_assignee_role TEXT,  -- 'sales', 'engineer', 'manager'
    target_platform TEXT NOT NULL CHECK (target_platform IN ('clickup', 'todoist', 'both')),

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_template_name UNIQUE (template_name)
);

CREATE INDEX idx_task_templates_type ON task_templates(task_type);
CREATE INDEX idx_task_templates_usage ON task_templates(usage_count DESC);
```

### Table: `task_completion_audit`

Audit trail for task completion and timing analytics.

```sql
CREATE TABLE task_completion_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task reference
    action_item_id UUID NOT NULL REFERENCES task_automation_queue(id),
    task_mapping_id UUID REFERENCES task_mappings(id),

    -- Completion details
    completed_platform TEXT NOT NULL CHECK (completed_platform IN ('clickup', 'todoist')),
    completed_at TIMESTAMPTZ NOT NULL,
    completed_by_email TEXT,

    -- Timing metrics
    time_to_complete_hours DECIMAL(10, 2),  -- created_at to completed_at
    was_overdue BOOLEAN DEFAULT FALSE,
    days_overdue INTEGER,

    -- Context
    meeting_type TEXT,
    client_name TEXT,
    task_type TEXT,
    priority TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_completion_audit_action_item ON task_completion_audit(action_item_id);
CREATE INDEX idx_completion_audit_completed_at ON task_completion_audit(completed_at);
CREATE INDEX idx_completion_audit_overdue ON task_completion_audit(was_overdue) WHERE was_overdue = TRUE;
CREATE INDEX idx_completion_audit_client ON task_completion_audit(client_name);
```

---

## Task Routing Logic

### Decision Tree

```
Extract Action Item
    ↓
Is it team-facing or multi-person?
    ├─ YES → Route to ClickUp
    │         ├─ Client-facing → Space: Sales/Delivery
    │         ├─ Internal research → Space: Research
    │         ├─ Technical work → Space: Engineering
    │         └─ Administrative → Space: Operations
    │
    └─ NO → Is it complex with subtasks?
              ├─ YES → Route to ClickUp (better hierarchy)
              │
              └─ NO → Route to Todoist (personal task)
                        ├─ Follow-up → Project: Sales Follow-ups
                        ├─ Research → Project: Market Research
                        ├─ Prep → Project: Meeting Prep
                        └─ Admin → Project: Admin Tasks
```

### Routing Rules Implementation

```python
def determine_platform_routing(
    action_item: ActionItem,
    meeting_context: dict[str, Any]
) -> TaskPlatform:
    """
    Determine whether task should go to ClickUp or Todoist.

    ClickUp Criteria:
    - Multiple assignees
    - Client-facing task
    - Has dependencies
    - Complex workflow required

    Todoist Criteria:
    - Single assignee
    - Personal task
    - No dependencies
    - Simple completion
    """
    # Multi-assignee tasks always go to ClickUp
    if action_item.assignee and "," in action_item.assignee.get("name", ""):
        return TaskPlatform.CLICKUP

    # Client-facing tasks go to ClickUp
    if meeting_context.get("is_client_meeting"):
        return TaskPlatform.CLICKUP

    # Tasks with dependencies go to ClickUp
    if action_item.dependencies and len(action_item.dependencies) > 0:
        return TaskPlatform.CLICKUP

    # High-priority or critical tasks go to ClickUp (team visibility)
    if action_item.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL]:
        return TaskPlatform.CLICKUP

    # Technical tasks go to ClickUp
    if action_item.task_type == TaskType.TECHNICAL:
        return TaskPlatform.CLICKUP

    # Everything else goes to Todoist (personal productivity)
    return TaskPlatform.TODOIST
```

---

## Error Handling Strategy

### Error Categories

1. **Extraction Errors**
   - Low confidence (<0.7): Flag for human review, still create task
   - Claude API failure: Retry 3 times with backoff, escalate on failure
   - Malformed response: Log error, attempt to salvage partial data

2. **Platform API Errors**
   - ClickUp rate limit (429): Queue tasks, retry after rate limit reset
   - Todoist auth error (401): Alert ops team, fail task creation
   - Network timeout: Retry with increased timeout (60s), max 3 attempts
   - Task creation conflict: Check if task already exists, skip duplicate

3. **Sync Conflicts**
   - Both platforms updated: Most recent update wins, log conflict
   - Status mismatch without clear timestamp: Default to ClickUp (team system)
   - Sync deadlock: Manual intervention required, create task for ops

4. **Assignment Errors**
   - Assignee not found: Default to meeting organizer, flag for review
   - Ambiguous assignment: Assign to organizer with manual review flag
   - Missing email: Skip email-based assignment, use name matching

### Retry Configuration

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ClickUpAPIError, TodoistAPIError)),
    reraise=True
)
async def create_task_with_retry(platform: TaskPlatform, params: Any) -> Any:
    """Create task with automatic retry on transient failures."""
    if platform == TaskPlatform.CLICKUP:
        return await self.create_clickup_task(params)
    else:
        return await self.create_todoist_task(params)
```

### Error Escalation

**Escalate to human when:**
- Extraction confidence < 0.5 for critical meetings
- Task creation fails 3+ times across both platforms
- Sync conflict persists for > 24 hours
- 5+ tasks from same meeting need manual review
- Assignee detection fails for high-priority tasks

---

## Testing Requirements

### Unit Tests (>90% coverage for tools)

**File:** `__tests__/unit/agents/test_meeting_task_automation.py`

**Test Cases:**
1. `test_extract_action_items_high_confidence` - Claude API returns well-structured items
2. `test_extract_action_items_low_confidence` - Flags items needing review
3. `test_extract_action_items_api_failure` - Handles Claude API errors
4. `test_create_clickup_task_success` - Successfully creates ClickUp task
5. `test_create_clickup_task_assignee_not_found` - Falls back to default assignee
6. `test_create_todoist_task_success` - Successfully creates Todoist task
7. `test_assign_task_owner_explicit` - Identifies explicitly named assignee
8. `test_assign_task_owner_implicit` - Detects "I'll..." pattern
9. `test_assign_task_owner_ambiguous` - Defaults to organizer
10. `test_sync_task_status_no_conflicts` - Syncs without issues
11. `test_sync_task_status_with_conflicts` - Resolves conflicts correctly
12. `test_send_task_reminders_upcoming` - Sends standard reminders
13. `test_send_task_reminders_urgent` - Sends urgent reminders (< 4 hours)
14. `test_send_task_reminders_overdue` - Escalates overdue tasks
15. `test_generate_task_report` - Calculates metrics correctly
16. `test_platform_routing_clickup` - Routes team tasks to ClickUp
17. `test_platform_routing_todoist` - Routes personal tasks to Todoist

### Integration Tests (>85% coverage for agent)

**File:** `__tests__/integration/test_meeting_task_automation.py`

**Test Cases:**
1. `test_full_extraction_to_creation_flow` - End-to-end from transcript to platform tasks
2. `test_bidirectional_sync` - Status updates sync correctly between platforms
3. `test_reminder_workflow` - Reminders sent at correct times
4. `test_task_completion_audit` - Completion tracked in database
5. `test_celery_task_execution` - Scheduled tasks execute correctly
6. `test_handoff_from_fathom` - Receives transcript and extracts tasks
7. `test_handoff_to_project_management` - Reports project tasks correctly
8. `test_sync_conflict_resolution` - Handles real sync conflicts
9. `test_template_usage` - Uses task templates correctly

### Mock Data Fixtures

**File:** `__tests__/fixtures/task_automation_fixtures.py`

```python
@pytest.fixture
def mock_transcript():
    return """
    Sarah: "I'll send the technical demo to Acme Corp by Friday."
    John: "Can you research their current tech stack? I need it before our next call."
    Sarah: "Sure, I'll have that ready by Wednesday."
    Client: "We need a proposal by end of next week."
    Sarah: "Noted, I'll prepare that for you."
    """

@pytest.fixture
def mock_meeting_context():
    return {
        "meeting_id": "meeting-123",
        "client_name": "Acme Corp",
        "meeting_type": "discovery",
        "meeting_date": "2025-12-05T14:00:00Z",
        "is_client_meeting": True,
        "organizer": {
            "name": "Sarah Johnson",
            "email": "sarah@smarterteam.ai",
            "role": "sales_engineer"
        }
    }

@pytest.fixture
def mock_attendees():
    return [
        {"name": "Sarah Johnson", "email": "sarah@smarterteam.ai", "role": "sales_engineer"},
        {"name": "John Smith", "email": "john@smarterteam.ai", "role": "sales_rep"},
        {"name": "Jane Doe", "email": "jane@acmecorp.com", "role": "client"}
    ]

@pytest.fixture
def mock_action_items():
    return [
        {
            "description": "Send technical demo to Acme Corp",
            "assignee": {"name": "Sarah Johnson", "email": "sarah@smarterteam.ai"},
            "due_date": "2025-12-08T17:00:00Z",
            "priority": "high",
            "task_type": "follow_up",
            "confidence_score": 0.95
        },
        {
            "description": "Research Acme Corp tech stack",
            "assignee": {"name": "Sarah Johnson", "email": "sarah@smarterteam.ai"},
            "due_date": "2025-12-07T17:00:00Z",
            "priority": "medium",
            "task_type": "research",
            "confidence_score": 0.88
        }
    ]

@pytest.fixture
def mock_clickup_response():
    return {
        "id": "clickup-task-123",
        "url": "https://clickup.com/t/clickup-task-123",
        "name": "Send technical demo to Acme Corp",
        "status": {"status": "to do"},
        "date_created": "1701788400000"
    }

@pytest.fixture
def mock_todoist_response():
    return {
        "id": "todoist-task-456",
        "url": "https://todoist.com/showTask?id=456",
        "content": "Research Acme Corp tech stack",
        "created_at": "2025-12-05T14:30:00Z"
    }
```

---

## Implementation Checklist

### Phase 1: Setup & Foundation
- [ ] Create agent directory: `src/agents/meeting_task_automation/`
- [ ] Create agent file: `agent.py` with `MeetingTaskAutomationAgent` class
- [ ] Create tools file: `tools.py` with all 7 tool functions
- [ ] Create prompts file: `prompts.py` with system prompt constant
- [ ] Create schemas file: `schemas.py` with Pydantic models
- [ ] Create exceptions file: `exceptions.py` (ExtractionError, ClickUpAPIError, TodoistAPIError, SyncConflictError)
- [ ] Create utils file: `utils.py` (priority mapping, routing logic)

### Phase 2: Integrations
- [ ] Create ClickUp integration: `src/integrations/clickup.py` extending `BaseIntegrationClient`
- [ ] Create Todoist integration: `src/integrations/todoist.py` extending `BaseIntegrationClient`
- [ ] Add ClickUp API configuration to `.env.example`
- [ ] Add Todoist API configuration to `.env.example`
- [ ] Test ClickUp API connection and authentication
- [ ] Test Todoist API connection and authentication

### Phase 3: Database
- [ ] Create migration: `specs/database-schema/migrations/007_task_automation_tables.sql`
- [ ] Add `task_automation_queue` table
- [ ] Add `task_mappings` table
- [ ] Add `task_templates` table
- [ ] Add `task_completion_audit` table
- [ ] Add indexes for performance
- [ ] Run migration on dev database
- [ ] Verify foreign key constraints

### Phase 4: Core Implementation
- [ ] Implement `extract_action_items` tool with Claude API
- [ ] Implement `create_clickup_task` tool with space/list routing
- [ ] Implement `create_todoist_task` tool with project routing
- [ ] Implement `assign_task_owner` tool with NLP assignment logic
- [ ] Implement `sync_task_status` tool with conflict resolution
- [ ] Implement `send_task_reminders` tool with multi-tier reminders
- [ ] Implement `generate_task_report` tool with analytics
- [ ] Implement helper functions (platform routing, priority mapping)

### Phase 5: Agent Logic
- [ ] Implement `system_prompt` property
- [ ] Implement `process_task` method with workflow routing
- [ ] Add error handling for all edge cases
- [ ] Add logging at each step
- [ ] Add timing metrics
- [ ] Test manual agent invocation

### Phase 6: Celery Integration
- [ ] Create Celery tasks: `src/tasks/task_automation_tasks.py`
- [ ] Implement `extract_tasks_from_transcript` task (triggered by Fathom agent)
- [ ] Implement `sync_task_platforms` periodic task (every 15 minutes)
- [ ] Implement `check_task_reminders` periodic task (hourly)
- [ ] Add Celery beat schedule configuration
- [ ] Test task execution locally

### Phase 7: Testing
- [ ] Create test fixtures: `__tests__/fixtures/task_automation_fixtures.py`
- [ ] Write unit tests for all 7 tools (>90% coverage)
- [ ] Write unit tests for helper functions
- [ ] Write integration test for full extraction-to-creation flow
- [ ] Write integration test for bidirectional sync
- [ ] Write integration test for reminder workflow
- [ ] Run `make test` and verify >85% agent coverage
- [ ] Fix any failing tests

### Phase 8: Quality Assurance
- [ ] Run `make lint` and fix all linting errors
- [ ] Run `make typecheck` and fix all type errors
- [ ] Run `make format` to format code
- [ ] Run `make check` to verify all quality gates pass
- [ ] Manual testing with real ClickUp and Todoist accounts
- [ ] Test extraction with various transcript formats
- [ ] Test sync conflict resolution
- [ ] Test reminder delivery

### Phase 9: Documentation & Deployment
- [ ] Update root `CLAUDE.md` with agent overview
- [ ] Document environment variables in `.env.example`
- [ ] Create runbook for monitoring task creation rate
- [ ] Move task to `tasks/backend/_completed/`
- [ ] Update `tasks/TASK-LOG.md` with completion notes
- [ ] Create PR with all changes

### Phase 10: Monitoring & Optimization
- [ ] Set up alerts for extraction failures
- [ ] Monitor ClickUp/Todoist API rate limits
- [ ] Track task completion rates
- [ ] Monitor sync latency
- [ ] Collect feedback on extraction accuracy
- [ ] Iterate on Claude extraction prompt based on false positives/negatives

---

## Success Metrics

- **Extraction Accuracy:** >85% of extracted action items are valid (measured via human review sampling)
- **Task Creation Success Rate:** >98% (tasks successfully created in target platform)
- **Sync Reliability:** >99% (status updates propagated within 15 minutes)
- **Reminder Delivery Rate:** >99% (reminders sent on time)
- **Average Extraction Confidence:** >0.80
- **Task Completion Rate:** >70% (percentage of extracted tasks actually completed)
- **Time to Creation:** <2 minutes from transcript receipt to platform task creation
- **Sync Conflict Rate:** <2% of synced tasks

---

## Cron Schedule

**Celery Beat Configuration:**

```python
# In src/celery_app.py beat_schedule
{
    "sync-task-platforms": {
        "task": "src.tasks.task_automation_tasks.sync_task_platforms",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "check-task-reminders": {
        "task": "src.tasks.task_automation_tasks.check_task_reminders",
        "schedule": crontab(minute="0"),  # Every hour
    },
    "generate-weekly-task-report": {
        "task": "src.tasks.task_automation_tasks.generate_weekly_report",
        "schedule": crontab(day_of_week="1", hour="9", minute="0"),  # Monday 9 AM
    },
}
```

---

## Integration Points

### Upstream (Receives From)
- **Meeting Fathom Integration Agent:** Transcript text + meeting metadata
- **Meeting Notes Manager Agent:** Structured notes with action items
- **Manual Input:** API endpoint for manual task creation

### Downstream (Sends To)
- **Delivery Project Management Agent:** Project-related tasks for tracking
- **Response Handler Agent:** Task reminder emails
- **Notification System:** Slack/SMS for urgent reminders

---

## Future Enhancements (Post-MVP)

1. **Smart Templates:** Learn common action item patterns and suggest templates
2. **Task Prioritization AI:** Use ML to predict true priority based on context
3. **Automatic Subtask Creation:** Break complex tasks into subtasks automatically
4. **Voice Task Creation:** Extract tasks from voice memos/calls
5. **Task Dependency Visualization:** Generate dependency graphs for complex projects
6. **Predictive Completion Dates:** Estimate completion based on historical data
7. **Integration with GitHub:** Create GitHub issues for technical tasks
8. **Slack Bot Interface:** Create tasks via Slack commands
9. **Mobile App:** Push notifications for reminders
10. **Task Impact Scoring:** Prioritize by business impact, not just urgency

---

## Dependencies (Python Packages)

```toml
# Already installed in pyproject.toml
anthropic = ">=0.75.0"
httpx = ">=0.27.0"
pydantic = ">=2.12.5"
celery = ">=5.6.0"
redis = ">=6.4.0"

# May need to add
tenacity = ">=8.2.0"  # For retry logic
```

---

## References

### API Documentation
- [ClickUp API v2](https://clickup.com/api)
- [Todoist REST API v2](https://developer.todoist.com/rest/v2/)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)

### Internal Documentation
- BaseAgent: `app/backend/src/agents/base_agent.py`
- BaseIntegrationClient: `app/backend/src/integrations/base.py`
- Project conventions: `.project/CONVENTIONS.md`
- Testing patterns: `app/backend/__tests__/`

---

**Last Updated:** 2025-12-05
**Spec Version:** 1.0.0
**Status:** Ready for Implementation
