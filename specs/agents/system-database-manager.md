# System Database Manager Agent - Production Specification

## Overview

**Category**: System & Administration
**Priority**: Phase 7 - Polish & Scale
**Agent Name**: `system_database_manager`
**Purpose**: Autonomous database maintenance agent for PostgreSQL/Supabase that ensures data integrity, optimizes performance, manages backups, and maintains long-term data health through automated maintenance tasks.

**Status**: Ready to Build
**Last Updated**: 2025-12-05
**Refined From**: plan/agents/system-database-manager.md

---

## System Prompt

```
You are the System Database Manager Agent for Smarter Team, responsible for maintaining database health, performance, and integrity.

Your mission is to proactively manage database operations that keep the system running optimally: cleaning orphaned data, optimizing indexes, verifying backups, enforcing data integrity, and archiving historical data.

**Core Responsibilities:**
1. Execute scheduled maintenance tasks (daily cleanup, weekly optimization, monthly archival)
2. Monitor database health metrics and detect performance degradation
3. Verify backup integrity and maintain recovery readiness
4. Enforce data integrity constraints and consistency checks
5. Manage storage efficiently through intelligent archival strategies
6. Coordinate maintenance windows to minimize impact on operations
7. Alert on critical database issues that require human intervention

**Behavioral Guidelines:**
- Always run operations within maintenance windows (1:00-5:00 AM UTC default)
- Use database locks sparingly and prefer non-blocking operations
- Log all maintenance activities with detailed metrics and outcomes
- Validate data changes before committing (run in dry-run mode first when possible)
- Handle partial failures gracefully and resume interrupted operations
- Coordinate with other agents to avoid conflicts during maintenance

**Decision Making:**
- Daily cleanup: Automatic unless errors > 5% of operations
- Weekly optimization: Automatic during low-traffic periods
- Monthly archival: Requires approval if > 100GB affected
- Backup failures: Immediate alert critical priority
- Data integrity issues: Alert critical, halt affected operations
- Storage > 90%: Alert critical, trigger emergency cleanup

**Safety Mechanisms:**
- All DELETE operations run as SOFT DELETE first (mark as deleted)
- Batch large operations (max 10,000 rows per transaction)
- Verify foreign key constraints before cleanup
- Create checkpoints for long-running operations
- Maintain audit trail of all data modifications

**Communication Style:**
- Maintenance reports: Clear metrics, rows affected, duration
- Error reports: Specific SQL error, context, impact assessment
- Recommendations: Data-backed suggestions with risk/benefit analysis
- Alerts: Include severity, affected tables, immediate actions needed

You have access to tools for database operations, backup verification, integrity checks, and performance monitoring. Use these tools systematically to maintain optimal database health.
```

---

## Agent Implementation

### Class Definition

```python
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger


class MaintenanceType(str, Enum):
    """Types of maintenance operations."""
    DAILY_CLEANUP = "daily_cleanup"
    WEEKLY_OPTIMIZATION = "weekly_optimization"
    MONTHLY_ARCHIVAL = "monthly_archival"
    INTEGRITY_CHECK = "integrity_check"
    BACKUP_VERIFICATION = "backup_verification"
    EMERGENCY_CLEANUP = "emergency_cleanup"


class OperationStatus(str, Enum):
    """Status of maintenance operations."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK = "rollback"


class DatabaseManagerAgent(BaseAgent):
    """
    System database manager agent for PostgreSQL/Supabase maintenance.

    Performs automated database maintenance tasks including cleanup,
    optimization, backup verification, and archival operations.
    """

    def __init__(self):
        super().__init__(
            name="system_database_manager",
            description="Automated database maintenance and health management"
        )

        # Register tools
        self.register_tool(
            execute_cleanup_query,
            "execute_cleanup_query",
            "Execute cleanup queries for orphaned or expired data"
        )
        self.register_tool(
            optimize_table_indexes,
            "optimize_table_indexes",
            "Analyze and rebuild table indexes for performance"
        )
        self.register_tool(
            verify_backup_integrity,
            "verify_backup_integrity",
            "Verify backup completion and test restore capability"
        )
        self.register_tool(
            run_integrity_checks,
            "run_integrity_checks",
            "Execute data integrity and consistency checks"
        )
        self.register_tool(
            archive_historical_data,
            "archive_historical_data",
            "Archive old records to archive tables"
        )
        self.register_tool(
            check_storage_usage,
            "check_storage_usage",
            "Check database storage usage and projections"
        )
        self.register_tool(
            send_maintenance_alert,
            "send_maintenance_alert",
            "Send alerts for maintenance issues or completion"
        )
        self.register_tool(
            record_maintenance_log,
            "record_maintenance_log",
            "Record maintenance operation details and metrics"
        )

    @property
    def system_prompt(self) -> str:
        # Return the system prompt from above
        return """..."""  # Full prompt from above

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process database maintenance tasks.

        Supports:
        - run_maintenance: Execute scheduled maintenance
        - emergency_cleanup: Handle storage emergencies
        - verify_backups: Check backup integrity
        - integrity_report: Generate data integrity report
        """
        task_type = task.get("type")

        if task_type == "run_maintenance":
            return await self._run_maintenance(task.get("maintenance_type"))
        elif task_type == "emergency_cleanup":
            return await self._emergency_cleanup(task.get("threshold_gb"))
        elif task_type == "verify_backups":
            return await self._verify_backups()
        elif task_type == "integrity_report":
            return await self._generate_integrity_report()
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _run_maintenance(self, maintenance_type: str) -> Dict[str, Any]:
        """Run scheduled maintenance operations."""
        # Implementation details
        pass

    async def _emergency_cleanup(self, threshold_gb: Optional[int]) -> Dict[str, Any]:
        """Handle emergency storage cleanup."""
        # Implementation details
        pass
```

---

## Tool Definitions

### 1. execute_cleanup_query

**Purpose**: Execute cleanup queries for orphaned or expired data

**Input Schema**:
```python
class CleanupQueryInput(BaseModel):
    query_type: str = Field(..., description="Type of cleanup: 'orphaned', 'expired', 'temp'")
    table_name: str = Field(..., description="Table to clean")
    batch_size: int = Field(default=1000, ge=100, le=10000, description="Rows per batch")
    dry_run: bool = Field(default=True, description="Preview changes without executing")
    retention_days: Optional[int] = Field(default=30, description="Retention period in days")
```

**Output Schema**:
```python
class CleanupQueryOutput(BaseModel):
    query_type: str
    table_name: str
    total_rows_processed: int
    rows_affected: int
    batches_completed: int
    execution_time_seconds: float
    space_freed_mb: float
    errors: List[str]
    warnings: List[str]
    dry_run_mode: bool
```

**Error Handling**:
- Lock timeout → Retry with smaller batch size
- Foreign key constraint → Log error, skip affected rows
- Out of memory → Reduce batch size by 50%, retry
- Connection lost → Resume from last batch checkpoint

**Implementation**:
```python
async def execute_cleanup_query(
    query_type: str,
    table_name: str,
    batch_size: int = 1000,
    dry_run: bool = True,
    retention_days: Optional[int] = 30
) -> Dict[str, Any]:
    """
    Execute cleanup queries with batching and error handling.

    Supports cleaning orphaned records, expired data, and temporary tables.
    Runs in dry-run mode by default for safety.
    """
    from sqlalchemy import text
    from src.database import get_async_session
    import time

    logger = get_agent_logger("database_manager.cleanup")
    start_time = time.time()

    # Define cleanup queries
    cleanup_queries = {
        "orphaned": {
            "lead_research": """
                DELETE FROM lead_research
                WHERE lead_id NOT IN (SELECT id FROM leads)
            """,
            "company_research": """
                DELETE FROM company_research
                WHERE company_id NOT IN (SELECT id FROM companies)
            """,
            "messages": """
                DELETE FROM messages
                WHERE conversation_id NOT IN (SELECT id FROM conversations)
            """
        },
        "expired": {
            "enrichment_attempts": f"""
                DELETE FROM enrichment_attempts
                WHERE created_at < NOW() - INTERVAL '{retention_days} days'
                AND status = 'failed'
            """,
            "temp_data": f"""
                DELETE FROM temp_uploads
                WHERE created_at < NOW() - INTERVAL '{retention_days} days'
            """
        }
    }

    if query_type not in cleanup_queries:
        raise ValueError(f"Unknown query_type: {query_type}")

    if table_name not in cleanup_queries[query_type]:
        raise ValueError(f"Table {table_name} not in {query_type} cleanup")

    query = cleanup_queries[query_type][table_name]
    total_rows = 0
    rows_affected = 0
    errors = []
    warnings = []

    try:
        async with get_async_session() as session:
            # Get count first (for dry run)
            count_query = query.replace("DELETE", "SELECT COUNT(*)")
            result = await session.execute(text(count_query))
            total_rows = result.scalar() or 0

            if dry_run:
                logger.info(f"DRY RUN: Would delete {total_rows} rows from {table_name}")
                return {
                    "query_type": query_type,
                    "table_name": table_name,
                    "total_rows_processed": total_rows,
                    "rows_affected": 0,
                    "batches_completed": 0,
                    "execution_time_seconds": time.time() - start_time,
                    "space_freed_mb": 0.0,
                    "errors": errors,
                    "warnings": warnings,
                    "dry_run_mode": True
                }

            # Execute in batches
            offset = 0
            batch_num = 0

            while True:
                batch_query = f"{query} LIMIT {batch_size}"
                result = await session.execute(text(batch_query))
                batch_affected = result.rowcount
                rows_affected += batch_affected
                batch_num += 1

                if batch_affected == 0:
                    break

                await session.commit()
                offset += batch_size

                # Log progress
                logger.info(
                    f"Cleanup batch {batch_num}: {batch_affected} rows from {table_name}",
                    extra={
                        "table": table_name,
                        "batch": batch_num,
                        "rows": batch_affected,
                        "total_so_far": rows_affected
                    }
                )

                # Check for excessive batch count
                if batch_num > 1000:
                    warnings.append(f"High batch count: {batch_num} batches")
                    break

            execution_time = time.time() - start_time

            # Estimate space freed (rough calculation)
            avg_row_size = 0.5  # KB - estimate based on schema
            space_freed_mb = (rows_affected * avg_row_size) / 1024

            logger.info(
                f"Cleanup completed: {rows_affected} rows from {table_name}",
                extra={
                    "table": table_name,
                    "rows_deleted": rows_affected,
                    "execution_time": execution_time,
                    "space_freed_mb": space_freed_mb
                }
            )

            return {
                "query_type": query_type,
                "table_name": table_name,
                "total_rows_processed": total_rows,
                "rows_affected": rows_affected,
                "batches_completed": batch_num,
                "execution_time_seconds": execution_time,
                "space_freed_mb": space_freed_mb,
                "errors": errors,
                "warnings": warnings,
                "dry_run_mode": False
            }

    except asyncio.TimeoutError:
        error_msg = f"Cleanup timeout for {table_name}"
        logger.error(error_msg)
        errors.append(error_msg)
        return {
            "query_type": query_type,
            "table_name": table_name,
            "total_rows_processed": total_rows,
            "rows_affected": rows_affected,
            "batches_completed": batch_num,
            "execution_time_seconds": time.time() - start_time,
            "space_freed_mb": 0.0,
            "errors": errors + ["Operation timeout"],
            "warnings": warnings,
            "dry_run_mode": dry_run
        }

    except Exception as e:
        error_msg = f"Cleanup failed for {table_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append(error_msg)
        return {
            "query_type": query_type,
            "table_name": table_name,
            "total_rows_processed": total_rows,
            "rows_affected": 0,
            "batches_completed": 0,
            "execution_time_seconds": time.time() - start_time,
            "space_freed_mb": 0.0,
            "errors": errors,
            "warnings": warnings,
            "dry_run_mode": dry_run
        }
```

### 2. optimize_table_indexes

**Purpose**: Analyze and rebuild table indexes for performance

**Input Schema**:
```python
class OptimizeIndexesInput(BaseModel):
    table_names: List[str] = Field(..., description="List of tables to optimize")
    rebuild_threshold: float = Field(default=0.5, description="Bloat threshold for rebuild")
    analyze_only: bool = Field(default=True, description="Only run ANALYZE, not REINDEX")
    concurrent: bool = Field(default=True, description="Use CONCURRENT option")
```

**Output Schema**:
```python
class OptimizeIndexesOutput(BaseModel):
    tables_processed: List[str]
    indexes_analyzed: int
    indexes_rebuilt: int
    total_bloat_freed_mb: float
    optimization_time_seconds: float
    warnings: List[str]
    errors: List[str]
```

### 3. verify_backup_integrity

**Purpose**: Verify backup completion and test restore capability

**Input Schema**:
```python
class BackupVerificationInput(BaseModel):
    backup_type: str = Field(..., description="Type: 'daily', 'weekly', 'monthly'")
    verify_size: bool = Field(default=True, description="Check backup size consistency")
    test_restore: bool = Field(default=False, description="Test restore to staging")
    max_age_hours: int = Field(default=48, description="Maximum backup age")
```

**Output Schema**:
```python
class BackupVerificationOutput(BaseModel):
    backup_type: str
    backup_status: str
    backup_age_hours: float
    backup_size_gb: float
    size_change_percent: float
    restore_test_passed: Optional[bool]
    verification_time_seconds: float
    issues_found: List[str]
```

### 4. run_integrity_checks

**Purpose**: Execute data integrity and consistency checks

**Input Schema**:
```python
class IntegrityCheckInput(BaseModel):
    check_types: List[str] = Field(..., description="Types: 'foreign_keys', 'data_consistency', 'required_fields'")
    sample_rate: float = Field(default=1.0, description="Sample rate for large tables")
    max_errors_per_check: int = Field(default=100, description="Stop after N errors")
```

**Output Schema**:
```python
class IntegrityCheckOutput(BaseModel):
    checks_completed: List[str]
    total_errors: int
    errors_by_type: Dict[str, int]
    sample_size: int
    check_time_seconds: float
    critical_issues: List[Dict]
```

### 5. archive_historical_data

**Purpose**: Archive old records to archive tables

**Input Schema**:
```python
class ArchiveDataInput(BaseModel):
    tables_to_archive: List[str] = Field(..., description="Tables to archive")
    archive_date: datetime = Field(..., description="Cutoff date for archival")
    batch_size: int = Field(default=1000, description="Rows per batch")
    create_backup: bool = Field(default=True, description="Create table backup before archival")
    verify_archive: bool = Field(default=True, description="Verify archived data integrity")
```

**Output Schema**:
```python
class ArchiveDataOutput(BaseModel):
    tables_archived: List[str]
    total_rows_archived: int
    archive_size_gb: float
    compression_ratio: float
    verification_passed: bool
    archive_time_seconds: float
    errors: List[str]
```

### 6. check_storage_usage

**Purpose**: Check database storage usage and projections

**Input Schema**:
```python
class StorageCheckInput(BaseModel):
    include_projections: bool = Field(default=True, description="Calculate 30-day projections")
    table_details: bool = Field(default=True, description="Include per-table breakdown")
    alert_threshold: float = Field(default=0.9, description="Alert if usage > threshold")
```

**Output Schema**:
```python
class StorageCheckOutput(BaseModel):
    total_size_gb: float
    used_size_gb: float
    usage_percentage: float
    projected_usage_30d_gb: Optional[float]
    table_sizes: Optional[Dict[str, float]]
    growth_rate_daily_gb: float
    alerts: List[str]
    recommendations: List[str]
```

### 7. send_maintenance_alert

**Purpose**: Send alerts for maintenance issues or completion

**Input Schema**:
```python
class MaintenanceAlertInput(BaseModel):
    alert_type: str = Field(..., description="Type: 'info', 'warning', 'critical'")
    operation: str = Field(..., description="Operation that triggered alert")
    message: str = Field(..., description="Alert message")
    details: Dict[str, Any] = Field(default={}, description="Additional context")
    requires_action: bool = Field(default=False, description="Human action required")
```

**Output Schema**:
```python
class MaintenanceAlertOutput(BaseModel):
    alert_id: str
    alert_sent: bool
    channels: List[str]
    timestamp: datetime
    escalation_required: bool
```

### 8. record_maintenance_log

**Purpose**: Record maintenance operation details and metrics

**Input Schema**:
```python
class MaintenanceLogInput(BaseModel):
    operation: str = Field(..., description="Maintenance operation type")
    status: str = Field(..., description="Operation status")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: datetime = Field(..., description="Completion timestamp")
    metrics: Dict[str, Any] = Field(..., description="Operation metrics")
    error_details: Optional[str] = Field(None, description="Error details if failed")
```

**Output Schema**:
```python
class MaintenanceLogOutput(BaseModel):
    log_id: str
    recorded: bool
    timestamp: datetime
```

---

## Database Schema

### maintenance_logs Table

```sql
CREATE TABLE maintenance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Operation details
    operation VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds NUMERIC(10, 3) NOT NULL,

    -- Metrics and results
    rows_affected INTEGER DEFAULT 0,
    space_freed_mb NUMERIC(12, 2) DEFAULT 0,
    tables_processed TEXT[],
    metrics JSONB,

    -- Error handling
    error_details TEXT,
    warnings TEXT[],

    -- Indexes
    INDEX idx_operation_created (operation, created_at DESC),
    INDEX idx_status_created (status, created_at DESC)
);
```

### backup_verification_logs Table

```sql
CREATE TABLE backup_verification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Backup details
    backup_type VARCHAR(50) NOT NULL,
    backup_date DATE NOT NULL,
    backup_status VARCHAR(50) NOT NULL,
    backup_size_gb NUMERIC(10, 2),

    -- Verification results
    verification_status VARCHAR(50) NOT NULL,
    restore_test_passed BOOLEAN,
    size_change_percent NUMERIC(5, 2),
    issues_found TEXT[],

    -- Metadata
    verification_time_seconds NUMERIC(10, 3),

    UNIQUE(backup_type, backup_date)
);
```

### data_integrity_results Table

```sql
CREATE TABLE data_integrity_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Check details
    check_type VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    check_status VARCHAR(50) NOT NULL,

    -- Results
    errors_found INTEGER DEFAULT 0,
    sample_size INTEGER DEFAULT 0,
    error_details JSONB,

    -- Check metadata
    check_time_seconds NUMERIC(10, 3),
    threshold_exceeded BOOLEAN DEFAULT FALSE,

    -- Indexes
    INDEX idx_check_type_created (check_type, created_at DESC),
    INDEX idx_status_created (check_status, created_at DESC)
);
```

---

## Error Handling Strategy

### Database Error Categories

1. **Connection Errors**
   - Action: Retry with exponential backoff (max 3 attempts)
   - Examples: Connection timeout, network issues
   - Recovery: Automatic, alert if all retries fail

2. **Lock Timeout Errors**
   - Action: Reduce batch size, retry with shorter timeout
   - Examples: Table locks, row locks
   - Recovery: Automatic, log warning

3. **Constraint Violation Errors**
   - Action: Log error, skip offending records
   - Examples: Foreign key constraints, unique violations
   - Recovery: Continue with valid records

4. **Disk Space Errors**
   - Action: Immediate critical alert, trigger emergency cleanup
   - Examples: No space left on device
   - Recovery: Manual intervention required

5. **Memory Errors**
   - Action: Reduce batch size, add memory monitoring
   - Examples: Out of memory, query too large
   - Recovery: Automatic with smaller batches

### Error Recovery Patterns

```python
ERROR_RECOVERY = {
    "connection_timeout": {
        "max_retries": 3,
        "backoff_seconds": [5, 15, 30],
        "alert_after": 3
    },
    "lock_timeout": {
        "action": "reduce_batch_size",
        "reduction_factor": 0.5,
        "max_reductions": 3
    },
    "constraint_violation": {
        "action": "skip_record",
        "log_level": "warning",
        "continue": True
    },
    "disk_full": {
        "action": "emergency_cleanup",
        "alert_level": "critical",
        "halt_operations": True
    }
}
```

---

## Performance Considerations

### Operation Limits

- **Batch Size**: Default 1,000 rows, configurable 100-10,000
- **Timeout**: Default 30 minutes per operation
- **Lock Wait**: Default 5 seconds, then retry
- **Memory Limit**: Monitor and alert at 80% of available memory

### Scheduling Strategy

```python
MAINTENANCE_SCHEDULE = {
    "daily_cleanup": {
        "time": "01:00 UTC",
        "max_duration": "2 hours",
        "priority": "normal"
    },
    "weekly_optimization": {
        "day": "sunday",
        "time": "02:00 UTC",
        "max_duration": "4 hours",
        "priority": "low"
    },
    "monthly_archival": {
        "day": 1,  # First day of month
        "time": "03:00 UTC",
        "max_duration": "8 hours",
        "priority": "low",
        "requires_approval": True
    }
}
```

### Resource Monitoring

- **CPU Usage**: Alert if > 80% during maintenance
- **Memory Usage**: Alert if > 85% sustained
- **Disk I/O**: Monitor for excessive writes during archival
- **Lock Duration**: Alert if locks held > 10 minutes

---

## Celery Task Configuration

### Periodic Maintenance Tasks

```python
# In src/tasks/database_maintenance_tasks.py

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "daily-database-cleanup": {
        "task": "src.tasks.database_maintenance_tasks.daily_cleanup",
        "schedule": crontab(hour=1, minute=0),  # 01:00 UTC daily
        "args": ()
    },
    "weekly-database-optimization": {
        "task": "src.tasks.database_maintenance_tasks.weekly_optimization",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday 02:00 UTC
        "args": ()
    },
    "backup-verification": {
        "task": "src.tasks.database_maintenance_tasks.verify_backups",
        "schedule": crontab(hour=3, minute=0),  # 03:00 UTC daily
        "args": ()
    },
    "storage-monitoring": {
        "task": "src.tasks.database_maintenance_tasks.monitor_storage",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
        "args": ()
    }
}
```

### Task Implementation

```python
@celery_app.task(bind=True, max_retries=3)
def daily_cleanup(self: Task) -> Dict[str, Any]:
    """
    Execute daily database cleanup operations.

    Removes orphaned records, expired data, and temporary tables.
    """
    from src.agents.system_database_manager import DatabaseManagerAgent

    agent = DatabaseManagerAgent()

    result = await agent.process_task({
        "type": "run_maintenance",
        "maintenance_type": "daily_cleanup"
    })

    return result


@celery_app.task(bind=True, max_retries=1)
def weekly_optimization(self: Task) -> Dict[str, Any]:
    """
    Execute weekly database optimization.

    Analyzes tables, rebuilds indexes, updates statistics.
    """
    from src.agents.system_database_manager import DatabaseManagerAgent

    agent = DatabaseManagerAgent()

    result = await agent.process_task({
        "type": "run_maintenance",
        "maintenance_type": "weekly_optimization"
    })

    return result
```

---

## Testing Requirements

### Unit Tests (>90% coverage required)

**Test file**: `__tests__/unit/agents/test_database_manager_agent.py`

```python
class TestDatabaseManagerAgentInitialization:
    def test_agent_initialization()
    def test_tools_registered()
    def test_system_prompt_defined()

class TestExecuteCleanupQuery:
    @pytest.mark.asyncio
    async def test_orphaned_cleanup_dry_run()
    async def test_expired_cleanup_with_deletion()
    async def test_cleanup_batch_processing()
    async def test_cleanup_foreign_key_error_handling()
    async def test_cleanup_timeout_recovery()

class TestOptimizeTableIndexes:
    @pytest.mark.asyncio
    async def test_analyze_only_mode()
    async def test_index_rebuild_with_bloat()
    async def test_concurrent_index_operations()
    async def test_optimization_error_handling()

class TestVerifyBackupIntegrity:
    @pytest.mark.asyncio
    async def test_successful_backup_verification()
    async def test_backup_size_anomaly_detection()
    async def test_restore_test_execution()
    async def test_missing_backup_handling()

class TestRunIntegrityChecks:
    @pytest.mark.asyncio
    async def test_foreign_key_consistency_check()
    async def test_data_validation_check()
    async def test_required_fields_validation()
    async def test_integrity_error_reporting()

class TestArchiveHistoricalData:
    @pytest.mark.asyncio
    async def test_successful_archival()
    async def test_archive_verification()
    async def test_large_table_archival()
    async def test_archive_rollback_on_error()

class TestStorageMonitoring:
    @pytest.mark.asyncio
    async def test_storage_usage_calculation()
    async def test_growth_projections()
    async def test_storage_alert_thresholds()
    async def test_table_size_breakdown()

class TestMaintenanceAlerts:
    @pytest.mark.asyncio
    async def test_info_alert_sending()
    async def test_critical_alert_escalation()
    async def test_alert_context_inclusion()
    async def test_multiple_channel_notifications()
```

### Integration Tests

**Test file**: `__tests__/integration/test_database_manager_integration.py`

```python
class TestMaintenanceWorkflows:
    @pytest.mark.asyncio
    async def test_full_daily_cleanup_workflow()
    async def test_weekly_optimization_workflow()
    async def test_backup_verification_workflow()
    async def test_emergency_cleanup_workflow()

class TestDatabaseTransactions:
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error()
    async def test_concurrent_operation_handling()
    async def test_large_dataset_processing()
    async def test_lock_timeout_scenarios()

class TestCeleryTaskIntegration:
    @pytest.mark.asyncio
    async def test_daily_cleanup_task_execution()
    async def test_weekly_optimization_task()
    async def test_task_retry_mechanism()
    async def test_task_failure_alerting()
```

### Fixtures

**Test file**: `__tests__/fixtures/database_manager_fixtures.py`

```python
@pytest.fixture
async def sample_database():
    """Create test database with sample data."""
    # Setup test database with tables and data
    pass

@pytest.fixture
def mock_database_manager_agent():
    """Return mock DatabaseManagerAgent instance."""
    pass

@pytest.fixture
def sample_orphaned_data():
    """Return sample data with orphaned records."""
    pass

@pytest.fixture
def sample_maintenance_logs():
    """Return sample maintenance log entries."""
    pass
```

---

## Security Considerations

### Access Control

- **Database Permissions**: Limited to DELETE, SELECT, and maintenance operations
- **Table Restrictions**: No access to sensitive authentication tables
- **Operation Logging**: All modifications recorded with audit trail
- **Approval Required**: Large archival operations need human approval

### Data Protection

- **PII Handling**: Never archive or delete PII without approval
- **Backup Encryption**: Ensure all backups are encrypted at rest
- **Archive Security**: Archived data inherits original security policies
- **Retention Policies**: Enforce data retention compliance automatically

### Safety Mechanisms

- **Soft Deletes**: Mark records before physical deletion
- **Verification**: Always verify foreign key relationships
- **Rollback**: Maintain rollback capability for all operations
- **Isolation**: Run test operations in isolated transactions

---

## Observability Requirements

### Logging Strategy

```python
LOGGING_LEVELS = {
    "cleanup_operation": "info",
    "cleanup_error": "error",
    "optimization_start": "info",
    "optimization_complete": "info",
    "backup_verification": "info",
    "backup_failure": "critical",
    "integrity_check": "info",
    "integrity_violation": "critical",
    "archival_operation": "info",
    "archival_error": "error",
    "storage_alert": "warning"
}
```

### Metrics to Track

- **Database Performance**: Query execution times, index efficiency
- **Storage Metrics**: Usage trends, growth rates, archival success
- **Operation Metrics**: Rows processed, execution times, error rates
- **Backup Metrics**: Success rates, restore test results, size trends
- **Alert Metrics**: Frequency, resolution times, false positive rate

### Health Checks

- Database connection health
- Sufficient disk space (>20% free)
- Backup age verification (<24 hours)
- Archive storage availability
- Maintenance task execution status

---

## Configuration

### Environment Variables

```bash
# Database Maintenance Settings
DATABASE_MAINTENANCE_ENABLED=true
MAINTENANCE_WINDOW_START=01:00
MAINTENANCE_WINDOW_END=05:00
CLEANUP_BATCH_SIZE=1000
MAX_ARCHIVAL_SIZE_GB=100

# Backup Settings
BACKUP_RETENTION_DAYS=30
BACKUP_VERIFICATION_ENABLED=true
BACKUP_RESTORE_TEST_ENABLED=false

# Alerting
DATABASE_ALERT_EMAIL=admin@smarterteam.ai
DATABASE_ALERT_SLACK_WEBHOOK=${SLACK_WEBHOOK_URL}
STORAGE_ALERT_THRESHOLD=0.9

# Safety
REQUIRE_ARCHIVAL_APPROVAL=true
DRY_RUN_MODE_DEFAULT=true
MAX_OPERATION_DURATION_MINUTES=120
```

---

## Implementation Checklist

### Phase 1: Core Database Operations
- [ ] Implement `DatabaseManagerAgent` class extending `BaseAgent`
- [ ] Implement `execute_cleanup_query` tool with batching
- [ ] Implement `optimize_table_indexes` tool
- [ ] Implement `check_storage_usage` tool
- [ ] Create database tables for logging
- [ ] Write comprehensive unit tests (>90% coverage)

### Phase 2: Backup & Integrity
- [ ] Implement `verify_backup_integrity` tool
- [ ] Implement `run_integrity_checks` tool
- [ ] Implement `send_maintenance_alert` tool
- [ ] Integrate with backup service API
- [ ] Create backup verification schedules
- [ ] Write tests for backup and integrity checks

### Phase 3: Archival System
- [ ] Implement `archive_historical_data` tool
- [ ] Create archive table schemas
- [ ] Implement archival verification
- [ ] Add approval workflow for large operations
- [ ] Create archival rollback procedures
- [ ] Write tests for archival operations

### Phase 4: Monitoring & Alerting
- [ ] Implement `record_maintenance_log` tool
- [ ] Create storage monitoring dashboards
- [ ] Set up alert escalation rules
- [ ] Create maintenance report generation
- [ ] Integrate with system health monitoring
- [ ] Write tests for monitoring and alerting

### Phase 5: Celery Integration
- [ ] Create daily cleanup Celery task
- [ ] Create weekly optimization Celery task
- [ ] Create backup verification Celery task
- [ ] Create storage monitoring Celery task
- [ ] Configure Celery Beat schedules
- [ ] Write integration tests for all tasks

### Phase 6: Security & Safety
- [ ] Implement database permission restrictions
- [ ] Add soft-delete mechanisms
- [ ] Create approval workflows for critical operations
- [ ] Implement audit logging
- [ ] Add data protection measures
- [ ] Security review and testing

### Phase 7: Performance & Optimization
- [ ] Optimize query performance for large tables
- [ ] Implement connection pooling
- [ ] Add operation timeouts and retries
- [ ] Create performance monitoring
- [ ] Load testing with production-scale data
- [ ] Performance tuning and optimization

### Phase 8: Documentation & Deployment
- [ ] Create operation runbooks
- [ ] Document emergency procedures
- [ ] Create maintenance schedules
- [ ] Write troubleshooting guides
- [ ] Deploy to staging environment
- [ ] Production deployment with monitoring

---

## Dependencies

### Python Packages
- `sqlalchemy>=2.0.44` - Database ORM (already installed)
- `asyncpg>=0.31.0` - PostgreSQL async driver (already installed)
- `psycopg2-binary` - Backup operations
- `alembic` - Database migrations (already installed)

### External Services
- Database: PostgreSQL (Supabase)
- Backup Service: Supabase Backups
- Monitoring: System Health Check Agent
- Notifications: Slack, Email (via existing integrations)

### Agent Dependencies
- **system_health_check**: Notify of critical database issues
- **system_error_monitor**: Report critical errors and failures

---

## Human-in-the-Loop

### Approval Gates
1. **Monthly Archival**: Requires approval if > 100GB affected
2. **Schema Changes**: Always requires approval
3. **Backup Configuration Changes**: Requires approval
4. **Emergency Operations**: May require immediate approval

### Manual Interventions
1. **Storage Emergencies**: Manual cleanup may be required
2. **Backup Failures**: Manual investigation and restoration
3. **Data Corruption**: Manual recovery procedures
4. **Performance Issues**: Manual optimization may be needed

### Monitoring Dashboard
- Real-time storage usage
- Maintenance operation status
- Backup verification results
- Data integrity check results
- Recent maintenance logs

---

## Success Metrics

- **Uptime Maintenance**: 99.9%+ database availability during maintenance
- **Storage Efficiency**: >20% storage savings from archival
- **Performance Improvement**: >30% query speed improvement from optimization
- **Backup Reliability**: 100% successful daily backups
- **Data Integrity**: 0 critical integrity violations
- **Test Coverage**: >90% code coverage
- **Operation Success**: >95% maintenance operations succeed without intervention
- **Alert Accuracy**: <5% false positive alert rate

---

## Related Agents

- **system_health_check**: Monitors database health metrics
- **system_error_monitor**: Receives critical error notifications
- **All Agents**: Benefit from optimized database performance

---

## Future Enhancements

1. **Predictive Maintenance**: ML-based prediction of optimization needs
2. **Auto-Scaling**: Automatic resource scaling based on load
3. **Multi-Region Support**: Cross-region database replication and failover
4. **Advanced Analytics**: Query performance analysis and recommendations
5. **Self-Healing**: Automatic resolution of common database issues
6. **Compliance Automation**: Automated GDPR and other compliance reporting
7. **Cost Optimization**: Cloud database cost monitoring and optimization
