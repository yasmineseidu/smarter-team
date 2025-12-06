# Task: Implement System Database Manager Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/system-database-manager.md
**Created:** 2025-12-05

## Summary

Implement the System Database Manager Agent - an autonomous PostgreSQL/Supabase maintenance agent responsible for database cleanup, optimization, backup verification, data integrity checks, and archival operations. This critical infrastructure agent ensures database health, performance, and long-term data sustainability.

## Files to Create
- `app/backend/src/agents/system_database_manager.py`
- `app/backend/src/agents/tools/database_cleanup.py`
- `app/backend/src/agents/tools/database_optimization.py`
- `app/backend/src/agents/tools/backup_verification.py`
- `app/backend/src/agents/tools/integrity_checks.py`
- `app/backend/src/agents/tools/data_archival.py`
- `app/backend/__tests__/unit/agents/test_database_manager_agent.py`
- `app/backend/__tests__/unit/agents/test_database_tools.py`
- `app/backend/__tests__/integration/test_database_manager_integration.py`
- `app/backend/src/tasks/database_maintenance_tasks.py`

## Implementation Checklist

### Phase 1: Core Agent Structure
- [ ] Create `DatabaseManagerAgent` class extending `BaseAgent`
- [ ] Register all 8 tools in agent initialization
- [ ] Implement system prompt with detailed behavioral guidelines
- [ ] Create `process_task` method supporting all task types
- [ ] Implement maintenance scheduling logic
- [ ] Add structured logging for all operations

### Phase 2: Database Tools Implementation
- [ ] Implement `execute_cleanup_query` with batching and error handling
- [ ] Implement `optimize_table_indexes` with bloat detection
- [ ] Implement `check_storage_usage` with growth projections
- [ ] Implement `send_maintenance_alert` with escalation rules
- [ ] Implement `record_maintenance_log` with metrics tracking
- [ ] Add comprehensive error handling for all database operations
- [ ] Implement retry logic with exponential backoff

### Phase 3: Backup & Integrity Tools
- [ ] Implement `verify_backup_integrity` with size analysis
- [ ] Implement `run_integrity_checks` for foreign key consistency
- [ ] Add integration with Supabase backup API
- [ ] Implement restore testing functionality
- [ ] Create detailed integrity violation reporting
- [ ] Add sample-based checking for large tables

### Phase 4: Data Archival Tools
- [ ] Implement `archive_historical_data` with verification
- [ ] Create archive table schemas
- [ ] Implement batch archival with checkpoints
- [ ] Add compression and space optimization
- [ ] Create archival rollback procedures
- [ ] Implement approval workflow for large operations

### Phase 5: Database Schema
- [ ] Create `maintenance_logs` table migration
- [ ] Create `backup_verification_logs` table migration
- [ ] Create `data_integrity_results` table migration
- [ ] Add proper indexes for performance
- [ ] Implement data retention for log tables
- [ ] Create foreign key constraints where needed

### Phase 6: Celery Task Integration
- [ ] Create `daily_cleanup` Celery task
- [ ] Create `weekly_optimization` Celery task
- [ ] Create `backup_verification` Celery task
- [ ] Create `monitor_storage` Celery task
- [ ] Configure Celery Beat schedules for all tasks
- [ ] Implement task failure retry logic
- [ ] Add task monitoring and alerting

### Phase 7: Testing Suite
- [ ] Write unit tests for all tools (>90% coverage)
- [ ] Write unit tests for agent initialization and task processing
- [ ] Create integration tests for maintenance workflows
- [ ] Write tests for error handling and recovery
- [ ] Create performance tests for large datasets
- [ ] Add database transaction testing
- [ ] Implement test fixtures and mocks

### Phase 8: Configuration & Security
- [ ] Add configuration for maintenance windows
- [ ] Implement database permission restrictions
- [ ] Add soft-delete mechanisms for safety
- [ ] Create approval workflows for critical operations
- [ ] Implement audit logging for all modifications
- [ ] Add rate limiting for operations

### Phase 9: Monitoring & Observability
- [ ] Implement detailed logging with structured data
- [ ] Create metrics for operation performance
- [ ] Add storage monitoring and alerting
- [ ] Implement health check endpoints
- [ ] Create maintenance dashboards
- [ ] Add alert integration with system monitoring

## Acceptance Criteria

### Functional Requirements
- [ ] Daily cleanup removes orphaned records and expired data
- [ ] Weekly optimization improves query performance by >20%
- [ ] Backup verification checks age, size, and restore capability
- [ ] Integrity checks detect and report data violations
- [ ] Archival reduces storage usage while maintaining data access
- [ ] All operations run within maintenance windows (1:00-5:00 AM UTC)
- [ ] Emergency cleanup triggers when storage >90% full

### Non-Functional Requirements
- [ ] >90% test coverage for all code
- [ ] All database operations use proper transaction management
- [ ] Error handling covers all failure scenarios
- [ ] Operations are idempotent and resumable
- [ ] Comprehensive audit trail maintained
- [ ] Performance: cleanup completes within 2 hours for 1M records
- [ ] Zero data loss during archival operations

### Integration Requirements
- [ ] Integrates with Supabase PostgreSQL
- [ ] Coordinates with system-health-check agent
- [ ] Sends alerts to system-error-monitor agent
- [ ] Uses existing Celery task infrastructure
- [ ] Follows project logging patterns
- [ ] Uses existing notification channels (Slack/email)

## Verification

### Manual Testing
```bash
# Run agent with test maintenance tasks
cd app/backend
python -c "
from src.agents.system_database_manager import DatabaseManagerAgent
import asyncio

async def test():
    agent = DatabaseManagerAgent()
    result = await agent.process_task({
        'type': 'run_maintenance',
        'maintenance_type': 'daily_cleanup'
    })
    print(result)

asyncio.run(test())
"

# Test cleanup in dry-run mode
python -c "
from src.agents.tools.database_cleanup import execute_cleanup_query
import asyncio

asyncio.run(execute_cleanup_query(
    query_type='orphaned',
    table_name='lead_research',
    dry_run=True
))
"
```

### Automated Testing
```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_database_manager_agent.py -v --cov=src.agents.system_database_manager

# Run integration tests
pytest app/backend/__tests__/integration/test_database_manager_integration.py -v

# Run all database manager tests
pytest app/backend/__tests__/ -k "database_manager" -v --cov=src.agents.system_database_manager

# Type checking
mypy app/backend/src/agents/system_database_manager.py

# Linting
ruff check app/backend/src/agents/system_database_manager.py
```

### Database Testing
```bash
# Create test database with sample data
psql $DATABASE_URL -c "
-- Create test tables with orphaned records
CREATE TABLE IF NOT EXISTS test_leads (id SERIAL PRIMARY KEY, email VARCHAR);
CREATE TABLE IF NOT EXISTS test_lead_research (id SERIAL PRIMARY KEY, lead_id INTEGER, data JSON);
INSERT INTO test_lead_research (lead_id, data) VALUES (999, '{}'); -- Orphaned record
"

# Run cleanup test
python -c "
from src.agents.tools.database_cleanup import execute_cleanup_query
import asyncio

asyncio.run(execute_cleanup_query(
    query_type='orphaned',
    table_name='test_lead_research',
    dry_run=False
))
"

# Verify cleanup
psql $DATABASE_URL -c "SELECT COUNT(*) FROM test_lead_research WHERE lead_id = 999;"
```

### Performance Testing
```bash
# Generate test data (1M records)
python scripts/generate_test_data.py --count 1000000 --table test_messages

# Measure cleanup performance
time python -c "
from src.agents.tools.database_cleanup import execute_cleanup_query
import asyncio

result = asyncio.run(execute_cleanup_query(
    query_type='expired',
    table_name='test_messages',
    batch_size=1000,
    dry_run=False
))
print(f'Processed {result[\"rows_affected\"]} records in {result[\"execution_time_seconds\"]} seconds')
"
```

## Important Notes

### Safety First
- Always run cleanup operations in dry-run mode first
- Use soft deletes before physical deletion when possible
- Verify foreign key constraints before cleanup
- Create checkpoints for long-running operations
- Implement proper transaction rollback on errors

### Performance Considerations
- Use batching for operations on large tables
- Implement connection pooling
- Monitor memory usage during operations
- Use CONCURRENT option for index operations
- Schedule resource-intensive operations during low-traffic periods

### Coordination with Other Systems
- Check for active agent operations before maintenance
- Coordinate with backup schedules
- Notify dependent systems of planned maintenance
- Implement graceful degradation during maintenance windows

### Monitoring Requirements
- Log all maintenance operations with detailed metrics
- Alert on operation failures or timeouts
- Monitor storage trends and growth projections
- Track backup verification results
- Create dashboards for maintenance visibility

## Definition of Done

1. **Code Complete**: All tools implemented with error handling and logging
2. **Tests Passing**: >90% coverage, all unit and integration tests pass
3. **Documentation**: Code documented, API docs updated
4. **Performance**: Operations complete within specified time limits
5. **Security**: Proper permissions, audit logging, safety mechanisms in place
6. **Integration**: Works with existing systems and follows project patterns
7. **Monitoring**: Alerts, dashboards, and health checks implemented
8. **Production Ready**: Deployed to staging, tested, and approved for production
