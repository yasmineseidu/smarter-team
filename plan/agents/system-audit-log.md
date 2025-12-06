# Audit Log Agent

## Category
System & Administration

## Purpose
Track all automated actions

## Logged Actions
- Lead status changes
- Emails sent
- Proposals sent
- Database modifications
- API calls
- Human approvals
- System configuration changes

## Process
1. Log every significant action
2. Include timestamp, actor, details
3. Retain for compliance period
4. Enable audit queries

## Database Tables
- `audit_logs`

## Integrations
- All system components (receive events)
- Compliance/reporting tools

## Priority
Phase 7 - Polish & Scale

## Dependencies
- All agents and system components

## Human-in-the-Loop
- Audit logs are read-only
- Compliance queries handled by human

## Audit Log Schema
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Who
    actor VARCHAR(100) NOT NULL,  -- agent name, user id, or 'system'
    actor_type VARCHAR(50),       -- agent, user, system, webhook

    -- What
    action VARCHAR(100) NOT NULL,  -- e.g., 'lead.status_changed'
    resource_type VARCHAR(100),    -- e.g., 'lead', 'campaign', 'proposal'
    resource_id UUID,

    -- Details
    old_values JSONB,
    new_values JSONB,
    metadata JSONB,

    -- Context
    request_id VARCHAR(100),       -- For tracing related actions
    ip_address VARCHAR(50),
    user_agent TEXT,

    -- Indexing
    INDEX idx_audit_created (created_at),
    INDEX idx_audit_actor (actor),
    INDEX idx_audit_action (action),
    INDEX idx_audit_resource (resource_type, resource_id)
);
```

## Action Categories

### Lead Actions
```
lead.created
lead.updated
lead.status_changed
lead.assigned_to_campaign
lead.removed_from_campaign
lead.enrichment_completed
lead.merged
lead.deleted
```

### Campaign Actions
```
campaign.created
campaign.updated
campaign.launched
campaign.paused
campaign.completed
campaign.leads_added
campaign.leads_removed
```

### Communication Actions
```
email.sent
email.received
email.opened
email.clicked
email.bounced
email.unsubscribed
sms.sent
linkedin.connection_sent
linkedin.message_sent
```

### Proposal Actions
```
proposal.created
proposal.sent
proposal.viewed
proposal.signed
proposal.expired
proposal.negotiation_started
proposal.negotiation_completed
```

### Financial Actions
```
invoice.created
invoice.sent
payment.received
payment.failed
payment.refunded
```

### System Actions
```
config.changed
api_key.rotated
user.logged_in
user.logged_out
permission.changed
integration.connected
integration.disconnected
```

## Logging Function
```python
async def log_audit(
    actor: str,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    old_values: dict = None,
    new_values: dict = None,
    metadata: dict = None
):
    await db.execute("""
        INSERT INTO audit_logs
        (actor, action, resource_type, resource_id, old_values, new_values, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, actor, action, resource_type, resource_id,
        json.dumps(old_values), json.dumps(new_values), json.dumps(metadata))
```

## Common Queries

### Lead History
```sql
SELECT * FROM audit_logs
WHERE resource_type = 'lead' AND resource_id = $1
ORDER BY created_at DESC;
```

### Actions by Agent
```sql
SELECT action, COUNT(*) as count
FROM audit_logs
WHERE actor = 'response_handler_agent'
AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY action
ORDER BY count DESC;
```

### Status Change Timeline
```sql
SELECT
    created_at,
    old_values->>'status' as from_status,
    new_values->>'status' as to_status,
    actor
FROM audit_logs
WHERE resource_type = 'lead'
AND resource_id = $1
AND action = 'lead.status_changed'
ORDER BY created_at;
```

### Daily Activity Report
```sql
SELECT
    DATE(created_at) as date,
    action,
    COUNT(*) as count
FROM audit_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), action
ORDER BY date DESC, count DESC;
```

## Retention Policy
```
Standard retention: 2 years
Financial records: 7 years
Compliance records: As required by regulation

Archival process:
- Monthly: Archive logs >2 years old
- Yearly: Purge archived logs >7 years old
```

## Compliance Reports
```
Available reports:
- Lead data access log
- Email communication history
- Financial transaction history
- User access history
- Configuration change history
```
