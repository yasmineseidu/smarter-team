-- Migration 006: Functions and Triggers
-- Creates utility functions and triggers for automated behavior
-- Dependencies: 001-005 (all tables must exist)

-- Utility Functions

-- 1. Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 2. Lead status change logging
CREATE OR REPLACE FUNCTION log_lead_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log if status actually changed
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO lead_status_history (
            lead_id,
            from_status,
            to_status,
            changed_by,
            change_reason,
            metadata
        ) VALUES (
            NEW.id,
            OLD.status,
            NEW.status,
            current_setting('app.current_agent', true),
            'Status change detected',
            jsonb_build_object(
                'previous_status', OLD.status,
                'new_status', NEW.status,
                'changed_at', NOW()
            )
        );

        -- Update status_changed_at
        NEW.status_changed_at = NOW();
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- 3. Update conversation last message
CREATE OR REPLACE FUNCTION update_conversation_last_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET
        last_message_at = NEW.created_at,
        last_message_direction = NEW.direction,
        message_count = message_count + 1,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- 4. Calculate lead scores based on activity
CREATE OR REPLACE FUNCTION calculate_lead_score()
RETURNS TRIGGER AS $$
BEGIN
    -- Update engagement score based on recent activity
    IF TG_TABLE_NAME = 'messages' AND NEW.direction = 'inbound' THEN
        UPDATE leads
        SET
            engagement_score = LEAST(100, engagement_score + 5),
            updated_at = NOW()
        WHERE id = NEW.lead_id;
    END IF;

    -- Update meeting booking score
    IF TG_TABLE_NAME = 'meetings' AND NEW.status = 'scheduled' THEN
        UPDATE leads
        SET
            lead_score = LEAST(100, lead_score + 20),
            updated_at = NOW()
        WHERE id = NEW.lead_id;
    END IF;

    -- Update proposal score
    IF TG_TABLE_NAME = 'proposals' AND NEW.status = 'sent' THEN
        UPDATE leads
        SET
            lead_score = LEAST(100, lead_score + 15),
            updated_at = NOW()
        WHERE id = NEW.lead_id;
    END IF;

    -- Update conversion score
    IF TG_TABLE_NAME = 'clients' THEN
        UPDATE leads
        SET
            lead_score = LEAST(100, lead_score + 25),
            status = 'CLOSED_WON',
            updated_at = NOW()
        WHERE id = NEW.lead_id;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- 5. Update campaign performance metrics
CREATE OR REPLACE FUNCTION update_campaign_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update when new lead is added to campaign
    IF TG_TABLE_NAME = 'leads' AND NEW.current_campaign_id IS NOT NULL THEN
        UPDATE campaigns
        SET
            total_leads = total_leads + 1,
            active_leads = active_leads + 1,
            updated_at = NOW()
        WHERE id = NEW.current_campaign_id;
    END IF;

    -- Update when lead changes campaign
    IF TG_TABLE_NAME = 'leads' AND
       OLD.current_campaign_id IS NOT NULL AND
       NEW.current_campaign_id IS NOT NULL AND
       OLD.current_campaign_id != NEW.current_campaign_id THEN
        -- Remove from old campaign
        UPDATE campaigns
        SET
            active_leads = GREATEST(0, active_leads - 1),
            updated_at = NOW()
        WHERE id = OLD.current_campaign_id;

        -- Add to new campaign
        UPDATE campaigns
        SET
            active_leads = active_leads + 1,
            updated_at = NOW()
        WHERE id = NEW.current_campaign_id;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- 6. Track email performance
CREATE OR REPLACE FUNCTION track_email_performance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update email performance when sent
    IF NEW.sent_at IS NOT NULL AND OLD.sent_at IS NULL THEN
        -- Update campaign metrics
        IF NEW.campaign_id IS NOT NULL THEN
            UPDATE campaigns
            SET
                emails_sent = emails_sent + 1,
                updated_at = NOW()
            WHERE id = NEW.campaign_id;
        END IF;
    END IF;

    -- Track opens
    IF NEW.opened_at IS NOT NULL AND OLD.opened_at IS NULL THEN
        IF NEW.campaign_id IS NOT NULL THEN
            UPDATE campaigns
            SET
                opens = opens + 1,
                updated_at = NOW()
            WHERE id = NEW.campaign_id;
        END IF;
    END IF;

    -- Track replies
    IF NEW.direction = 'inbound' AND OLD.id IS NULL THEN
        IF NEW.campaign_id IS NOT NULL THEN
            UPDATE campaigns
            SET
                replies = replies + 1,
                updated_at = NOW()
            WHERE id = NEW.campaign_id;
        END IF;

        -- Check if it's a positive reply and update conversation
        IF NEW.response_type = 'positive' THEN
            IF NEW.campaign_id IS NOT NULL THEN
                UPDATE campaigns
                SET
                    positive_replies = positive_replies + 1,
                    updated_at = NOW()
                WHERE id = NEW.campaign_id;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- 7. Update client health metrics
CREATE OR REPLACE FUNCTION update_client_health()
RETURNS TRIGGER AS $$
BEGIN
    -- Update last engagement
    IF TG_TABLE_NAME = 'conversations' THEN
        UPDATE clients
        SET
            last_engagement_at = NEW.created_at,
            updated_at = NOW()
        WHERE lead_id = NEW.lead_id;
    END IF;

    -- Update satisfaction score from surveys (if table exists)
    IF TG_TABLE_NAME = 'satisfaction_surveys' AND NEW.score IS NOT NULL THEN
        UPDATE clients
        SET
            satisfaction_score = NEW.score,
            health_score = GREATEST(0, LEAST(100,
                (health_score * 0.7) + (NEW.score * 10 * 0.3) -- Weight new survey 30%
            )),
            updated_at = NOW()
        WHERE id = NEW.client_id;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- 8. Cleanup old webhook events
CREATE OR REPLACE FUNCTION cleanup_old_webhook_events()
RETURNS void AS $$
BEGIN
    -- Delete webhook events older than 30 days that are completed
    DELETE FROM webhook_events
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND status = 'completed';

    -- Log the cleanup
    INSERT INTO audit_logs (
        actor,
        action,
        resource_type,
        metadata
    ) VALUES (
        'system',
        'cleanup',
        'webhook_events',
        jsonb_build_object(
            'deleted_count', ROW_COUNT,
            'cleanup_date', NOW()
        )
    );
END;
$$ language 'plpgsql';

-- Create Triggers

-- Update timestamp triggers
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meetings_updated_at
    BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_proposals_updated_at
    BEFORE UPDATE ON proposals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Business logic triggers
CREATE TRIGGER log_lead_status_change
    BEFORE UPDATE ON leads
    FOR EACH ROW WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION log_lead_status_change();

CREATE TRIGGER update_conversation_last_message
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION update_conversation_last_message();

CREATE TRIGGER calculate_lead_score_from_messages
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION calculate_lead_score();

CREATE TRIGGER calculate_lead_score_from_meetings
    AFTER INSERT OR UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION calculate_lead_score();

CREATE TRIGGER calculate_lead_score_from_proposals
    AFTER INSERT ON proposals
    FOR EACH ROW EXECUTE FUNCTION calculate_lead_score();

CREATE TRIGGER calculate_lead_score_from_conversion
    AFTER INSERT ON clients
    FOR EACH ROW EXECUTE FUNCTION calculate_lead_score();

CREATE TRIGGER update_campaign_metrics_on_lead
    AFTER INSERT OR UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_campaign_metrics();

CREATE TRIGGER track_email_performance_metrics
    AFTER INSERT OR UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION track_email_performance();

CREATE TRIGGER update_client_health_metrics
    AFTER INSERT ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_client_health();

-- Validation Functions

-- Validate email format
CREATE OR REPLACE FUNCTION validate_email_format(email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
END;
$$ language 'plpgsql';

-- Validate lead status transitions
CREATE OR REPLACE FUNCTION validate_lead_status_transition(
    from_status TEXT,
    to_status TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    -- Define valid transitions (this can be expanded)
    CASE
        WHEN from_status IS NULL THEN RETURN TRUE; -- New lead
        WHEN from_status = 'NEW' AND to_status IN ('ENRICHING', 'DEAD_LEAD') THEN RETURN TRUE;
        WHEN from_status = 'ENRICHING' AND to_status IN ('VERIFIED', 'INVALID_EMAIL', 'DEAD_LEAD') THEN RETURN TRUE;
        WHEN from_status = 'VERIFIED' AND to_status IN ('IN_CAMPAIGN', 'DEAD_LEAD') THEN RETURN TRUE;
        WHEN from_status = 'IN_CAMPAIGN' AND to_status IN ('ENGAGED', 'BOUNCED', 'UNSUBSCRIBED', 'REACTIVATION_POOL') THEN RETURN TRUE;
        WHEN from_status = 'ENGAGED' AND to_status IN ('MEETING_BOOKED', 'CLOSED_LOST', 'REACTIVATION_POOL') THEN RETURN TRUE;
        WHEN from_status = 'MEETING_BOOKED' AND to_status IN ('MEETING_COMPLETED', 'MEETING_NO_SHOW') THEN RETURN TRUE;
        WHEN from_status = 'MEETING_COMPLETED' AND to_status IN ('PROPOSAL_SENT', 'CLOSED_LOST') THEN RETURN TRUE;
        WHEN from_status = 'PROPOSAL_SENT' AND to_status IN ('NEGOTIATING', 'CLOSED_WON', 'CLOSED_LOST', 'PROPOSAL_EXPIRED') THEN RETURN TRUE;
        WHEN from_status = 'NEGOTIATING' AND to_status IN ('CLOSED_WON', 'CLOSED_LOST') THEN RETURN TRUE;
        WHEN from_status = 'CLOSED_WON' AND to_status = 'ONBOARDING' THEN RETURN TRUE;
        ELSE RETURN FALSE;
    END CASE;
END;
$$ language 'plpgsql';

-- Create Views for Common Queries

-- Lead pipeline view
CREATE OR REPLACE VIEW lead_pipeline AS
SELECT
    status,
    COUNT(*) as count,
    AVG(lead_score) as avg_score,
    COUNT(DISTINCT company_id) as unique_companies,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as new_this_week,
    COUNT(CASE WHEN status_changed_at >= NOW() - INTERVAL '7 days' THEN 1 END) as changed_this_week
FROM leads
WHERE status != 'DEAD_LEAD'
GROUP BY status
ORDER BY
    CASE status
        WHEN 'NEW' THEN 1
        WHEN 'ENRICHING' THEN 2
        WHEN 'VERIFIED' THEN 3
        WHEN 'IN_CAMPAIGN' THEN 4
        WHEN 'ENGAGED' THEN 5
        WHEN 'MEETING_BOOKED' THEN 6
        WHEN 'MEETING_COMPLETED' THEN 7
        WHEN 'PROPOSAL_SENT' THEN 8
        WHEN 'NEGOTIATING' THEN 9
        WHEN 'CLOSED_WON' THEN 10
        WHEN 'CLOSED_LOST' THEN 11
        ELSE 12
    END;

-- Campaign performance view
CREATE OR REPLACE VIEW campaign_performance AS
SELECT
    c.id,
    c.name,
    c.status,
    c.total_leads,
    c.emails_sent,
    c.open_rate,
    c.reply_rate,
    c.meeting_rate,
    c.revenue_generated,
    c.created_at,
    c.launched_at,
    CASE
        WHEN c.status = 'ACTIVE' THEN 'Running'
        WHEN c.status = 'DRAFT' THEN 'Draft'
        WHEN c.status = 'COMPLETED' THEN 'Completed'
        WHEN c.status = 'PAUSED' THEN 'Paused'
        ELSE c.status
    END as status_display
FROM campaigns c
ORDER BY c.revenue_generated DESC NULLS LAST;

-- Create scheduled job for cleanup (requires pg_cron extension)
-- Uncomment if pg_cron is available
/*
SELECT cron.schedule(
    'cleanup-webhook-events',
    '0 2 * * *', -- 2 AM daily
    'SELECT cleanup_old_webhook_events();'
);
*/

-- Comments for documentation
COMMENT ON FUNCTION update_updated_at_column() IS 'Automatically updates updated_at timestamp on row updates';
COMMENT ON FUNCTION log_lead_status_change() IS 'Logs all lead status changes to history table';
COMMENT ON FUNCTION calculate_lead_score() IS 'Updates lead scores based on activities';
COMMENT ON FUNCTION validate_lead_status_transition() IS 'Validates lead follows proper state machine transitions';
COMMENT ON VIEW lead_pipeline IS 'Aggregated view of lead pipeline by status';
COMMENT ON VIEW campaign_performance IS 'Campaign performance metrics view';

-- Record migration
INSERT INTO schema_migrations (version, applied_at, description)
VALUES ('006_functions_and_triggers', NOW(), 'Database functions, triggers, and views');
