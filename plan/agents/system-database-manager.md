# Database Manager Agent

## Category
System & Administration

## Purpose
Maintain database health

## Tasks
- Daily cleanup of orphaned records
- Index optimization
- Backup verification
- Data integrity checks
- Archive old records

## Database Tables
- `maintenance_logs`
- `backup_status`

## Integrations
- PostgreSQL/Supabase
- Backup service

## Priority
Phase 7 - Polish & Scale

## Dependencies
- None (core infrastructure agent)

## Human-in-the-Loop
- Critical operations require approval
- Alerts on data integrity issues

## Maintenance Tasks

### Daily Cleanup
```sql
-- Remove orphaned records
DELETE FROM lead_research WHERE lead_id NOT IN (SELECT id FROM leads);
DELETE FROM company_research WHERE company_id NOT IN (SELECT id FROM companies);
DELETE FROM messages WHERE conversation_id NOT IN (SELECT id FROM conversations);

-- Clean up old temporary data
DELETE FROM enrichment_attempts WHERE created_at < NOW() - INTERVAL '30 days' AND status = 'failed';
```

### Weekly Optimization
```sql
-- Analyze tables for query optimization
ANALYZE leads;
ANALYZE companies;
ANALYZE campaigns;
ANALYZE conversations;
ANALYZE messages;

-- Reindex heavily-used tables
REINDEX TABLE leads;
REINDEX TABLE messages;
```

### Monthly Archival
```sql
-- Archive old completed projects
INSERT INTO projects_archive
SELECT * FROM projects
WHERE status = 'COMPLETED'
AND completed_at < NOW() - INTERVAL '1 year';

-- Archive old conversations
INSERT INTO conversations_archive
SELECT * FROM conversations
WHERE last_message_at < NOW() - INTERVAL '1 year';
```

## Data Integrity Checks
```
Check 1: Foreign key consistency
- All lead_id references exist in leads table
- All company_id references exist in companies table
- All campaign_id references exist in campaigns table

Check 2: Status consistency
- No leads with invalid status values
- No stuck leads (same status > threshold)

Check 3: Required fields
- All active leads have email
- All campaigns have at least one email in sequence

Check 4: Duplicate detection
- Flag duplicate emails across leads
- Flag duplicate company domains
```

## Backup Verification
```
Daily backup check:
1. Verify backup completed
2. Check backup size (should not be 0)
3. Compare to previous backup size
4. Alert on significant size changes (>20%)
5. Monthly: Test restore to staging
```

## Alert Conditions
```
CRITICAL:
- Backup failed
- Data integrity check failed
- Storage >90% full
- Replication lag >5 minutes

WARNING:
- Slow queries detected
- Table bloat >50%
- Backup size changed >20%
- Orphaned records found
```

## Maintenance Log Format
```json
{
  "task": "daily_cleanup",
  "started_at": "2025-01-15T01:00:00Z",
  "completed_at": "2025-01-15T01:05:32Z",
  "status": "success",
  "records_affected": {
    "orphaned_removed": 15,
    "temp_cleaned": 230
  },
  "duration_seconds": 332,
  "notes": null
}
```

## Cron Schedule
- Daily at 1:00 AM - Data hygiene and cleanup
- Daily at 2:00 AM - Full database backup
- Weekly - Index optimization
- Monthly - Archive old records
