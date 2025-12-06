-- Migration 005: System and Monitoring Tables
-- Creates audit logs, error tracking, and system monitoring tables
-- Dependencies: None (can run independently)

-- Audit logging table for compliance
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    actor VARCHAR(100) NOT NULL, -- agent name or user id
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,

    old_values JSONB DEFAULT '{}',
    new_values JSONB DEFAULT '{}',

    ip_address VARCHAR(50),
    user_agent TEXT,

    -- Additional context
    session_id VARCHAR(255),
    request_id VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

-- Error tracking table
CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,

    agent_name VARCHAR(100),
    error_type VARCHAR(100),
    error_code VARCHAR(50),
    error_message TEXT NOT NULL,
    stack_trace TEXT,

    severity VARCHAR(50) DEFAULT 'medium' CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    ),

    resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(100),
    resolution_notes TEXT,

    -- Context
    context JSONB DEFAULT '{}',
    environment VARCHAR(50) DEFAULT 'production',
    version VARCHAR(50),

    -- Occurrence tracking
    occurrence_count INTEGER DEFAULT 1,
    first_occurred_at TIMESTAMPTZ DEFAULT NOW(),
    last_occurred_at TIMESTAMPTZ DEFAULT NOW()
);

-- Health check monitoring table
CREATE TABLE health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    service VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255),
    check_type VARCHAR(50) DEFAULT 'http', -- http, api, database, queue

    status VARCHAR(50) NOT NULL CHECK (
        status IN ('healthy', 'degraded', 'down', 'unknown')
    ),
    response_time_ms INTEGER,

    error_message TEXT,
    error_details JSONB DEFAULT '{}',

    -- Additional metrics
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    disk_usage DECIMAL(5,2),

    metadata JSONB DEFAULT '{}'
);

-- API usage tracking for rate limiting and cost management
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    service VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255),
    method VARCHAR(10) DEFAULT 'GET',

    request_count INTEGER DEFAULT 1,
    tokens_used INTEGER,
    cost_usd DECIMAL(10,4),

    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    period_type VARCHAR(20) DEFAULT 'hour', -- minute, hour, day, month

    limits JSONB DEFAULT '{}',
    quotas JSONB DEFAULT '{}',

    metadata JSONB DEFAULT '{}'
);

-- System metrics table for performance monitoring
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(50), -- count, percentage, milliseconds, bytes, etc.

    tags JSONB DEFAULT '{}',
    source VARCHAR(100), -- application, database, external_service

    context JSONB DEFAULT '{}'
);

-- Performance analytics table
CREATE TABLE performance_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    date DATE NOT NULL,

    entity_type VARCHAR(50) NOT NULL, -- campaign, agent, user
    entity_id UUID NOT NULL,

    metrics JSONB DEFAULT '{}', -- Flexible metrics storage
    computed_metrics JSONB DEFAULT '{}', -- Derived metrics

    period VARCHAR(20) DEFAULT 'day', -- hour, day, week, month
    source VARCHAR(100),

    metadata JSONB DEFAULT '{}',

    UNIQUE(date, entity_type, entity_id, period)
);

-- Webhook events table for tracking incoming/outgoing webhooks
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,

    webhook_type VARCHAR(100) NOT NULL, -- instantly_reply, pandadoc_signed, stripe_payment
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('incoming', 'outgoing')),

    source VARCHAR(100) NOT NULL, -- instantly, pandadoc, cal_com, etc.
    event_type VARCHAR(100) NOT NULL,

    payload JSONB NOT NULL,
    response_code INTEGER,
    response_body TEXT,
    processing_error TEXT,

    status VARCHAR(50) DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'completed', 'failed', 'retrying')
    ),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Correlation
    correlation_id VARCHAR(255),
    related_entity_type VARCHAR(100),
    related_entity_id UUID,

    metadata JSONB DEFAULT '{}'
);

-- Background job tracking
CREATE TABLE background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    job_type VARCHAR(100) NOT NULL,
    job_name VARCHAR(255),
    queue_name VARCHAR(100) DEFAULT 'default',

    status VARCHAR(50) DEFAULT 'pending' CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'cancelled')
    ),

    priority INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    retry_after TIMESTAMPTZ,

    -- Job details
    parameters JSONB DEFAULT '{}',
    result JSONB DEFAULT '{}',
    error_message TEXT,

    -- Performance
    duration_ms INTEGER,
    memory_usage_mb DECIMAL(8,2),

    -- Scheduling
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    timeout_at TIMESTAMPTZ,

    worker_id VARCHAR(100),

    metadata JSONB DEFAULT '{}'
);

-- Schema migrations tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT,
    checksum VARCHAR(64),
    execution_time_ms INTEGER
);

-- Indexes for audit_logs
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor, created_at DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);

-- Indexes for error_logs
CREATE INDEX idx_error_logs_created ON error_logs(created_at DESC);
CREATE INDEX idx_error_logs_agent ON error_logs(agent_name, created_at DESC);
CREATE INDEX idx_error_logs_severity ON error_logs(severity, created_at DESC);
CREATE INDEX idx_error_logs_unresolved ON error_logs(resolved) WHERE resolved = FALSE;
CREATE INDEX idx_error_logs_first_occurred ON error_logs(first_occurred_at DESC);

-- Indexes for health_checks
CREATE INDEX idx_health_checks_created ON health_checks(created_at DESC);
CREATE INDEX idx_health_checks_service ON health_checks(service, created_at DESC);
CREATE INDEX idx_health_checks_status ON health_checks(status, created_at DESC);

-- Indexes for api_usage
CREATE INDEX idx_api_usage_service_period ON api_usage(service, period_start, period_end);
CREATE INDEX idx_api_usage_created ON api_usage(created_at DESC);
CREATE INDEX idx_api_usage_cost ON api_usage(cost_usd DESC);

-- Indexes for system_metrics
CREATE INDEX idx_system_metrics_name_time ON system_metrics(metric_name, created_at DESC);
CREATE INDEX idx_system_metrics_source ON system_metrics(source, created_at DESC);

-- Indexes for performance_analytics
CREATE INDEX idx_performance_analytics_date_entity ON performance_analytics(date, entity_type, entity_id);
CREATE INDEX idx_performance_analytics_period ON performance_analytics(period, date DESC);

-- Indexes for webhook_events
CREATE INDEX idx_webhook_events_created ON webhook_events(created_at DESC);
CREATE INDEX idx_webhook_events_status ON webhook_events(status, created_at DESC);
CREATE INDEX idx_webhook_events_type ON webhook_events(webhook_type, created_at DESC);
CREATE INDEX idx_webhook_events_correlation ON webhook_events(correlation_id) WHERE correlation_id IS NOT NULL;

-- Indexes for background_jobs
CREATE INDEX idx_background_jobs_status ON background_jobs(status, created_at);
CREATE INDEX idx_background_jobs_queue ON background_jobs(queue_name, status);
CREATE INDEX idx_background_jobs_type ON background_jobs(job_type, created_at DESC);
CREATE INDEX idx_background_jobs_retry ON background_jobs(retry_after, status) WHERE status IN ('failed', 'retrying');
CREATE INDEX idx_background_jobs_worker ON background_jobs(worker_id, status) WHERE worker_id IS NOT NULL;

-- Partition audit_logs for better performance (optional, uncomment if needed)
-- This requires PostgreSQL 10+
/*
CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
*/

-- Comments for documentation
COMMENT ON TABLE audit_logs IS 'Audit trail for all system actions (compliance)';
COMMENT ON TABLE error_logs IS 'System error tracking and resolution';
COMMENT ON TABLE health_checks IS 'Integration and service health monitoring';
COMMENT ON TABLE api_usage IS 'API rate limiting and cost tracking';
COMMENT ON TABLE system_metrics IS 'Performance and operational metrics';
COMMENT ON TABLE performance_analytics IS 'Business intelligence and analytics data';
COMMENT ON TABLE webhook_events IS 'Incoming and outgoing webhook tracking';
COMMENT ON TABLE background_jobs IS 'Asynchronous job queue tracking';

-- Record migration
INSERT INTO schema_migrations (version, applied_at, description)
VALUES ('005_system_tables', NOW(), 'System monitoring and audit tables');
