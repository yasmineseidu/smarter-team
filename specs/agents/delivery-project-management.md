# Project Management Agent - Production Specification

## Overview

**Category**: Delivery & Project Management
**Priority**: Phase 4 - Client Delivery
**Agent Name**: `delivery_project_management`
**Purpose**: Autonomous project coordination across multiple systems (ClickUp, Airtable, Todoist) with intelligent health scoring, blocker detection, and status reporting.

**Dependencies**:
- Internal Setup Agent (provides project infrastructure)
- Client Communication Agents (for notifications)

---

## System Prompt

```
You are the Project Management Agent for Smarter Team, responsible for maintaining a unified view of all client projects across multiple management systems.

Your mission is to ensure project data consistency, track progress accurately, identify potential issues before they become critical, and provide clear visibility into project health across all client engagements.

**Core Responsibilities:**
1. Synchronize project data across ClickUp, Airtable, and Todoist bi-directionally
2. Calculate project health scores based on timeline, budget, communication, and client satisfaction metrics
3. Detect and flag blockers, risks, and delays with contextual information
4. Generate comprehensive status reports with actionable insights
5. Maintain data integrity during sync operations with conflict resolution
6. Coordinate with other agents for escalations and client communications

**Sync Strategy:**
- Perform incremental syncs every 2 hours to minimize API usage
- Use last-sync timestamps to only process changes
- Resolve conflicts using "most recent update wins" with audit logging
- Batch API operations for efficiency (max 100 items per batch)
- Cache reference data (project lists, user mappings) for 1 hour

**Health Score Logic:**
- On-Time Score (40%): Percentage of tasks completed by due date
- Budget Score (30%): Budget utilization vs. actual spend
- Communication Score (20%): Response times and meeting cadence
- Client Satisfaction Score (10%): Survey feedback and sentiment

**Blocker Detection Rules:**
- Overdue tasks by > 24 hours = CRITICAL
- Milestone progress < 50% with deadline < 7 days = HIGH RISK
- No client response for > 3 business days = ACTION NEEDED
- Budget utilization > 90% with project < 80% complete = BUDGET ALERT

**Data Integrity Rules:**
- Never delete data, always archive with timestamps
- Log all sync operations with before/after values
- Validate all data against schemas before processing
- Roll back entire batch if any item fails validation

**Error Handling Philosophy:**
- Graceful degradation: If one system fails, continue with others
- Retry with exponential backoff for transient failures
- Alert after 3 consecutive failures for any integration
- Provide partial results with clear error annotations

**Communication Style:**
- Status reports should be executive-ready: concise, visual, and impactful
- Blocker alerts must include: impact, urgency, and recommended action
- Health scores need contextual explanation (why the score is what it is)
- All timestamps in recipient's timezone with clear timezone indicators

You coordinate with Client Success Agents for escalations, Finance Agents for budget concerns, and Research Agents for competitive project insights.
```

---

## Agent Implementation

### Class Definition

```python
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger


class ProjectStatus(str, Enum):
    """Project lifecycle statuses."""
    PLANNING = "planning"
    ACTIVE = "active"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BlockerSeverity(str, Enum):
    """Blocker severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectManagementAgent(BaseAgent):
    """
    Project management agent for multi-system synchronization and monitoring.

    Maintains consistency across ClickUp, Airtable, and Todoist while providing
    intelligent insights into project health and potential issues.
    """

    def __init__(self):
        super().__init__(
            name="delivery_project_management",
            description="Synchronizes project data and monitors health across all management systems"
        )

        # Initialize sync state
        self._last_sync: Optional[datetime] = None
        self._sync_lock = asyncio.Lock()

        # Register tools
        self.register_tool(
            self.sync_clickup_to_db,
            "sync_clickup_to_db",
            "Sync tasks and milestones from ClickUp to database"
        )
        self.register_tool(
            self.sync_airtable_to_db,
            "sync_airtable_to_db",
            "Sync project records from Airtable to database"
        )
        self.register_tool(
            self.sync_todoist_to_db,
            "sync_todoist_to_db",
            "Sync tasks from Todoist to database"
        )
        self.register_tool(
            self.calculate_health_scores,
            "calculate_health_scores",
            "Calculate health scores for all active projects"
        )
        self.register_tool(
            self.detect_blockers,
            "detect_blockers",
            "Identify and categorize project blockers"
        )
        self.register_tool(
            self.generate_status_report,
            "generate_status_report",
            "Generate comprehensive status report"
        )
        self.register_tool(
            self.resolve_sync_conflicts,
            "resolve_sync_conflicts",
            "Resolve data conflicts between systems"
        )
        self.register_tool(
            self.broadcast_updates,
            "broadcast_updates",
            "Push status changes to all connected systems"
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt defined above."""
        return """You are the Project Management Agent for Smarter Team..."""  # Full prompt

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process project management tasks.

        Supported task types:
        - sync_all: Perform bidirectional sync across all systems
        - sync_service: Sync specific service (clickup, airtable, todoist)
        - calculate_health: Update health scores for projects
        - detect_blockers: Run blocker detection across projects
        - generate_report: Create status report for date range
        - resolve_conflict: Handle specific data conflict
        """
        task_type = task.get("type")

        if task_type == "sync_all":
            return await self._sync_all_systems()
        elif task_type == "sync_service":
            return await self._sync_single_service(task.get("service"))
        elif task_type == "calculate_health":
            return await self._calculate_health_scores(task.get("project_ids"))
        elif task_type == "detect_blockers":
            return await self._detect_blockers(task.get("project_ids"))
        elif task_type == "generate_report":
            return await self._generate_report(task.get("report_type"), task.get("date_range"))
        elif task_type == "resolve_conflict":
            return await self._resolve_conflict(task.get("conflict_id"))
        else:
            raise ValueError(f"Unknown task type: {task_type}")
```

---

## Tools

### 1. sync_clickup_to_db

**Purpose**: Fetch and sync tasks, milestones, and custom fields from ClickUp projects.

**Input Schema**:
```python
class ClickUpSyncInput(BaseModel):
    space_id: Optional[str] = Field(None, description="ClickUp space ID (optional)")
    team_id: Optional[str] = Field(None, description="ClickUp team ID (optional)")
    since: Optional[datetime] = Field(None, description="Sync changes since this time")
    batch_size: int = Field(default=100, ge=1, le=100, description="Items per batch")
```

**Output Schema**:
```python
class ClickUpSyncOutput(BaseModel):
    synced_tasks: List[Dict[str, Any]]
    synced_milestones: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    total_processed: int
    sync_timestamp: datetime
```

**Implementation Details**:
```python
async def sync_clickup_to_db(self, args: ClickUpSyncInput) -> ClickUpSyncOutput:
    """
    Sync ClickUp data to local database.

    Process:
    1. Query tasks modified since last sync (or all if first sync)
    2. Fetch custom fields, comments, and attachments
    3. Convert to normalized schema
    4. Check for conflicts with existing data
    5. Batch upsert to database
    6. Log all changes for audit trail

    Error Handling:
    - Rate limit (429): Exponential backoff, max 5 retries
    - Auth error (401): Fail immediately, alert ops
    - Timeout: Retry with longer timeout, max 3 attempts
    - Partial failure: Continue with other tasks, log errors
    """
```

**Error Handling Matrix**:
| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Rate limit (429) | Status code | Wait with backoff | Yes, 5x |
| Auth error (401/403) | Status code | Fail immediately | No |
| Timeout | Exception | Increase timeout | Yes, 3x |
| Invalid data | Validation | Skip with log | No |
| Partial batch failure | Response | Continue with next | No |

### 2. sync_airtable_to_db

**Purpose**: Sync project records, phases, and client feedback from Airtable bases.

**Input Schema**:
```python
class AirtableSyncInput(BaseModel):
    base_id: Optional[str] = Field(None, description="Airtable base ID")
    table_names: List[str] = Field(default=["Projects", "Milestones", "Feedback"])
    since: Optional[datetime] = Field(None, description="Sync changes since")
```

**Output Schema**:
```python
class AirtableSyncOutput(BaseModel):
    synced_records: Dict[str, List[Dict]]  # Table name -> records
    updated_fields: List[str]
    conflicts: List[Dict[str, Any]]
    errors: List[str]
    total_records: int
```

**Implementation Details**:
```python
async def sync_airtable_to_db(self, args: AirtableSyncInput) -> AirtableSyncOutput:
    """
    Sync Airtable base with project management data.

    Key tables:
    - Projects: Master project records with phases and status
    - Milestones: Major deliverables with dates and owners
    - Feedback: Client feedback and satisfaction data
    - Budgets: Financial tracking and projections

    Features:
    - Formula field evaluation (health scores, status calculations)
    - Attachment handling (link storage, not file sync)
    - Linked record resolution across tables
    - Field type conversion (select, multi-select, currency, etc.)
    """
```

### 3. calculate_health_scores

**Purpose**: Calculate comprehensive health scores for all active projects.

**Input Schema**:
```python
class HealthScoreInput(BaseModel):
    project_ids: Optional[List[str]] = Field(None, description="Specific projects to score")
    include_trends: bool = Field(default=True, description="Calculate historical trends")
    benchmark_period: int = Field(default=30, description="Days for trend calculation")
```

**Output Schema**:
```python
class HealthScoreOutput(BaseModel):
    project_scores: List[Dict[str, Any]]
    benchmarks: Dict[str, float]
    alerts: List[Dict[str, Any]]
    calculated_at: datetime
```

**Score Calculation Logic**:
```python
def calculate_project_health(project_id: str) -> Dict[str, Any]:
    """
    Calculate weighted health score:

    On-Time Score (40%):
    - tasks_completed_on_time / total_tasks_due

    Budget Score (30%):
    - (budget - actual_spend) / budget * 100

    Communication Score (20%):
    - Based on response times, meeting attendance
    - Deductions for missed check-ins

    Client Satisfaction (10%):
    - Latest survey score (0-10)
    - Recent sentiment analysis
    """

    scores = {
        "on_time": calculate_on_time_score(project_id),
        "budget": calculate_budget_score(project_id),
        "communication": calculate_communication_score(project_id),
        "satisfaction": calculate_satisfaction_score(project_id)
    }

    weights = {"on_time": 0.4, "budget": 0.3, "communication": 0.2, "satisfaction": 0.1}

    overall = sum(scores[key] * weights[key] for key in scores)

    return {
        "overall": round(overall, 1),
        "breakdown": scores,
        "grade": get_health_grade(overall),  # A, B, C, D, F
        "trend": calculate_trend(project_id)
    }
```

### 4. detect_blockers

**Purpose**: Identify and categorize project blockers with recommended actions.

**Input Schema**:
```python
class BlockerDetectionInput(BaseModel):
    project_ids: Optional[List[str]] = Field(None)
    include_resolved: bool = Field(default=False, description="Include resolved blockers")
    severity_filter: Optional[List[BlockerSeverity]] = Field(None)
```

**Output Schema**:
```python
class BlockerDetectionOutput(BaseModel):
    blockers: List[Dict[str, Any]]
    new_blockers: List[Dict[str, Any]]
    escalated_blockers: List[Dict[str, Any]]
    summary: Dict[str, int]  # Count by severity
```

**Blocker Detection Rules**:
```python
def detect_blockers(project_id: str) -> List[Dict[str, Any]]:
    """
    Apply business rules to identify blockers:

    Schedule Blockers:
    - Task overdue > 24h = CRITICAL
    - Task overdue > 72h = ESCALATE to management
    - Milestone at risk if progress < 70% with deadline < 7 days

    Budget Blockers:
    - Spend rate > 125% of planned = HIGH
    - Unexpected costs > 10% of budget = MEDIUM

    Communication Blockers:
    - No client response > 3 business days = MEDIUM
    - No team response > 24 hours = HIGH
    - Missed status meeting = MEDIUM

    Resource Blockers:
    - Unassigned tasks > 5 = MEDIUM
    - Team member with > 150% allocation = HIGH
    """
```

### 5. generate_status_report

**Purpose**: Generate comprehensive status reports with visualizations and insights.

**Input Schema**:
```python
class StatusReportInput(BaseModel):
    report_type: str = Field(..., description="daily, weekly, monthly, executive")
    date_range: Dict[str, datetime] = Field(..., description="start_date, end_date")
    client_ids: Optional[List[str]] = Field(None, description="Filter by clients")
    include_charts: bool = Field(default=True, description="Generate chart data")
    format: str = Field(default="markdown", description="Output format")
```

**Output Schema**:
```python
class StatusReportOutput(BaseModel):
    report_content: str
    chart_data: Optional[List[Dict[str, Any]]]
    executive_summary: Dict[str, Any]
    action_items: List[Dict[str, Any]]
    generated_at: datetime
    metadata: Dict[str, Any]
```

**Report Template**:
```python
def generate_executive_summary() -> Dict[str, Any]:
    """
    Generate C-suite ready summary:

    Key Metrics:
    - Total active projects
    - Average health score
    - Blockers requiring escalation
    - Budget variance across portfolio

    Traffic Light System:
    🟢 Green: 80-100 health score
    🟡 Yellow: 60-79 health score
    🔴 Red: < 60 health score

    Top Concerns:
    - Projects at risk
    - Budget overruns
    - Resource constraints
    - Client satisfaction issues
    """
```

### 6. resolve_sync_conflicts

**Purpose**: Intelligent conflict resolution for data discrepancies between systems.

**Input Schema**:
```python
class ConflictResolutionInput(BaseModel):
    conflict_id: str = Field(..., description="Unique conflict identifier")
    resolution_strategy: str = Field(..., description="auto, manual, priority, timestamp")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
```

**Conflict Resolution Strategies**:
1. **Timestamp Priority**: "Last update wins" with full audit trail
2. **System Priority**: ClickUp > Airtable > Todoist (configurable)
3. **Manual Review**: Queue for human resolution
4. **Merge**: Combine non-conflicting fields from both sources

---

## Error Handling

### Global Error Handling

```python
class SyncError(Exception):
    """Base class for sync-related errors."""
    pass

class RateLimitError(SyncError):
    """Raised when API rate limit exceeded."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after

class AuthenticationError(SyncError):
    """Raised when API credentials are invalid."""
    pass

class DataValidationError(SyncError):
    """Raised when data fails validation."""
    def __init__(self, field: str, value: Any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
```

### Retry Logic Implementation

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitError, TimeoutError))
)
async def api_call_with_retry(url: str, **kwargs):
    """Make API call with intelligent retry logic."""
    pass
```

### Fallback Strategies

1. **Service Unavailable**:
   - Queue sync requests for retry
   - Serve cached data with "stale" indicator
   - Notify monitoring system

2. **Partial Data Loss**:
   - Re-fetch from other systems
   - Mark as incomplete in UI
   - Schedule full re-sync

3. **Conflict Resolution Failure**:
   - Preserve both versions
   - Flag for manual review
   - Continue with other items

---

## Multi-Agent Integration

### Handoff Protocols

```python
# Escalate critical blockers to Client Success Agent
await self.handoff_to(
    target_agent="client_success",
    payload={
        "type": "critical_blocker",
        "project_id": project.id,
        "blocker": blocker,
        "impact": impact_assessment,
        "recommended_actions": actions
    },
    priority="high"
)

# Notify Finance Agent of budget concerns
await self.handoff_to(
    target_agent="finance",
    payload={
        "type": "budget_alert",
        "project_id": project.id,
        "budget_variance": variance,
        "forecast": projection
    },
    priority="normal"
)
```

### Event Publishing

```python
# Publish project status changes
await self.publish_event(
    event_type="project.status_changed",
    data={
        "project_id": project.id,
        "old_status": old_status,
        "new_status": new_status,
        "changed_by": "project_management_agent",
        "timestamp": datetime.utcnow()
    }
)
```

---

## Testing Strategy

### Unit Tests

```python
class TestProjectManagementAgent:
    """Unit test suite for Project Management Agent."""

    @pytest.mark.asyncio
    async def test_sync_clickup_success(self, mock_clickup_client):
        """Test successful ClickUp sync."""
        # Setup mock responses
        mock_clickup_client.get_tasks.return_value = {
            "tasks": [...],
            "has_more": False
        }

        agent = ProjectManagementAgent()
        result = await agent.sync_clickup_to_db({
            "since": datetime.utcnow() - timedelta(hours=2)
        })

        assert result.synced_tasks is not None
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_health_score_calculation(self, test_projects):
        """Test health score calculation logic."""
        agent = ProjectManagementAgent()
        result = await agent.calculate_health_scores({
            "project_ids": [p.id for p in test_projects]
        })

        assert all(0 <= score["overall"] <= 100 for score in result.project_scores)
        assert all("grade" in score for score in result.project_scores)

    @pytest.mark.asyncio
    async def test_blocker_detection(self, test_project_with_overdue_tasks):
        """Test blocker detection rules."""
        agent = ProjectManagementAgent()
        result = await agent.detect_blockers({
            "project_ids": [test_project_with_overdue_tasks.id]
        })

        blockers = result.blockers
        assert any(b["severity"] == "critical" for b in blockers)
        assert all("recommended_action" in b for b in blockers)
```

### Integration Tests

```python
class TestProjectSyncIntegration:
    """Integration tests for full sync workflows."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_sync_cycle(self, docker_compose_env):
        """Test complete sync across all systems."""
        # Setup: Create test data in all three systems
        # Execute: Run full sync
        # Verify: Data consistency across systems
        pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_conflict_resolution(self, conflicting_data_setup):
        """Test conflict resolution with real data conflicts."""
        pass
```

### Performance Tests

```python
@pytest.mark.performance
async def test_sync_performance_large_dataset():
    """Test sync performance with 10,000+ tasks."""
    start_time = time.time()

    agent = ProjectManagementAgent()
    result = await agent.sync_clickup_to_db({
        "batch_size": 100
    })

    duration = time.time() - start_time
    assert duration < 300  # 5 minutes max
    assert result.total_processed > 10000
```

### Mock Strategy

```python
@pytest.fixture
def mock_integrations():
    """Mock all external integrations."""
    with patch('src.integrations.clickup.ClickUpClient') as mock_clickup, \
         patch('src.integrations.airtable.AirtableClient') as mock_airtable, \
         patch('src.integrations.todoist.TodoistClient') as mock_todoist:

        # Configure mock responses
        mock_clickup.return_value.get_tasks.return_value = {
            "tasks": generate_mock_tasks(100),
            "has_more": False
        }

        yield {
            "clickup": mock_clickup,
            "airtable": mock_airtable,
            "todoist": mock_todoist
        }
```

---

## Performance

### Expected Performance Metrics

| Operation | Target Latency | Throughput | Resources |
|-----------|----------------|------------|-----------|
| Incremental sync (2h) | < 30 seconds | 1000 items/min | 512 MB RAM |
| Full initial sync | < 10 minutes | 5000 items/min | 1 GB RAM |
| Health score calc | < 5 seconds | 200 projects/sec | 256 MB RAM |
| Blocker detection | < 10 seconds | 500 projects/sec | 256 MB RAM |
| Report generation | < 15 seconds | 50 reports/min | 512 MB RAM |

### Caching Strategy

```python
# Reference data cache (1 hour TTL)
await cache.set("clickup:users", users, ttl=3600)
await cache.set("airtable:fields", fields, ttl=3600)

# Sync state cache (15 minutes TTL)
await cache.set(f"sync:last_sync:{service}", timestamp, ttl=900)

# Health score cache (5 minutes TTL)
await cache.set(f"health:{project_id}", score, ttl=300)
```

### Batch Processing

```python
# Process ClickUp tasks in batches of 100
async for batch in chunked(tasks, 100):
    await process_batch(batch)
    await asyncio.sleep(0.1)  # Rate limiting
```

---

## Observability

### Logging Strategy

```python
# Structured logging with context
logger.info(
    "Sync operation completed",
    extra={
        "operation": "clickup_sync",
        "items_processed": len(tasks),
        "errors": len(errors),
        "duration_ms": duration,
        "service": "clickup"
    }
)

# Performance metrics
logger.info(
    "Health scores calculated",
    extra={
        "projects_count": len(projects),
        "avg_score": avg_score,
        "calculation_time_ms": calc_time
    }
)
```

### Metrics Collection

```python
# Prometheus metrics
sync_duration_histogram = Histogram('sync_duration_seconds', 'Sync operation duration')
sync_errors_counter = Counter('sync_errors_total', 'Total sync errors')
health_score_gauge = Gauge('project_health_score', 'Project health score', ['project_id'])

# Track success rates
success_rate = (successful_syncs / total_syncs) * 100
```

### Distributed Tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("sync_clickup") as span:
    span.set_attribute("service.name", "clickup")
    span.set_attribute("sync.items_count", len(tasks))
    # Sync logic here
```

---

## Security

### Data Handling

1. **Sensitive Data Redaction**:
   - Never log API keys or tokens
   - Mask email addresses in logs
   - Sanitize client data in error messages

2. **Input Validation**:
   - Validate all data against Pydantic schemas
   - Sanitize HTML content in descriptions
   - Limit field lengths to prevent overflow

3. **Access Control**:
   - Use least-privilege API tokens
   - Restrict to required scopes only
   - Rotate credentials regularly

### Audit Trail

```python
# Log every data modification
await audit_log.create({
    "action": "task_updated",
    "entity_type": "task",
    "entity_id": task.id,
    "old_values": old_values,
    "new_values": new_values,
    "changed_by": "project_management_agent",
    "source_system": "clickup",
    "timestamp": datetime.utcnow()
})
```

---

## Acceptance Criteria

### Functional Requirements

- [ ] **Sync Accuracy**: 99.9% data consistency across all systems
- [ ] **Sync Frequency**: Incremental syncs every 2 hours ± 5 minutes
- [ ] **Error Recovery**: Automatic retry with exponential backoff
- [ ] **Conflict Resolution**: All conflicts resolved with audit trail
- [ ] **Health Score Accuracy**: Scores match manual calculations within 5%
- [ ] **Blocker Detection**: 95% accuracy on known blocker scenarios
- [ ] **Report Generation**: Complete reports in < 15 seconds

### Non-Functional Requirements

- [ ] **Availability**: 99.9% uptime (excluding maintenance)
- [ ] **Performance**: All operations within specified latency targets
- [ ] **Scalability**: Handle 10,000 concurrent tasks without degradation
- [ ] **Security**: No credential leakage, all data encrypted in transit
- [ ] **Observability**: Complete traceability for all operations
- [ ] **Documentation**: All APIs documented with examples

### Integration Requirements

- [ ] **ClickUp API**: Support for tasks, milestones, custom fields, comments
- [ ] **Airtable API**: Support for bases, tables, linked records, formulas
- [ ] **Todoist API**: Support for tasks, projects, labels, due dates
- [ ] **Database**: PostgreSQL with connection pooling and transactions
- [ ] **Redis**: Caching and job queue support
- [ ] **Agent Handoffs**: Seamless integration with other Smarter Team agents

---

## Configuration

### Environment Variables

```bash
# ClickUp Integration
CLICKUP_API_KEY=sk-...
CLICKUP_TEAM_ID=team_123
CLICKUP_SPACE_IDS=space_456,space_789

# Airtable Integration
AIRTABLE_API_KEY=key_123
AIRTABLE_BASE_ID=app_456
AIRTABLE_TABLE_MAPPING={"Projects":"tbl_master", "Milestones":"tbl_milestones"}

# Todoist Integration
TODOIST_API_TOKEN=token_789
TODOIST_PROJECT_IDS=111,222,333

# Sync Configuration
SYNC_BATCH_SIZE=100
SYNC_INTERVAL_MINUTES=120
MAX_RETRY_ATTEMPTS=5
RATE_LIMIT_DELAY_MS=1000

# Health Score Configuration
HEALTH_SCORE_WEIGHTS={"on_time":0.4,"budget":0.3,"communication":0.2,"satisfaction":0.1}
ALERT_THRESHOLDS={"critical":40,"warning":60}
```

### Database Schema

```sql
-- Projects table (master record)
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255), -- ClickUp/Airtable ID
    source_system VARCHAR(50), -- clickup, airtable, manual
    name VARCHAR(500) NOT NULL,
    client_id UUID REFERENCES clients(id),
    status project_status DEFAULT 'planning',
    health_score INTEGER CHECK (health_score >= 0 AND health_score <= 100),
    budget_cents INTEGER,
    actual_spend_cents INTEGER,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(external_id, source_system)
);

-- Project milestones
CREATE TABLE project_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    external_id VARCHAR(255),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    due_date TIMESTAMP,
    status milestone_status DEFAULT 'pending',
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sync audit log
CREATE TABLE sync_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system VARCHAR(50) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    conflict_resolution VARCHAR(100),
    sync_batch_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Project blockers
CREATE TABLE project_blockers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    type blocker_type NOT NULL,
    severity blocker_severity NOT NULL,
    description TEXT NOT NULL,
    impact_assessment TEXT,
    recommended_action TEXT,
    status blocker_status DEFAULT 'active',
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

**Status**: Ready to Build
**Last Updated**: 2025-12-05
**Refined From**: plan/agents/delivery-project-management.md
