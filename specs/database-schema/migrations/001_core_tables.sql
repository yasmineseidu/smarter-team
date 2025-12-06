-- Migration 001: Core Tables
-- Creates the fundamental tables needed for MVP launch
-- Dependencies: None (base migration)

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types first (no dependencies)
CREATE TYPE campaign_status AS ENUM ('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED');
CREATE TYPE conversation_status AS ENUM ('active', 'resolved', 'pending_human', 'escalated');
CREATE TYPE message_direction AS ENUM ('inbound', 'outbound');
CREATE TYPE communication_channel AS ENUM ('email', 'linkedin', 'sms', 'call');
CREATE TYPE message_status AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'sent', 'delivered', 'bounced', 'failed');
CREATE TYPE approval_tier AS ENUM ('auto_send', 'approval', 'escalation');
CREATE TYPE message_type AS ENUM ('initial', 'follow_up', 'reply', 'check_in', 'notification', 'personalization');
CREATE TYPE meeting_status AS ENUM ('scheduled', 'completed', 'no_show', 'cancelled', 'rescheduled');
CREATE TYPE meeting_type AS ENUM ('discovery', 'demo', 'closing', 'follow_up', 'check_in');
CREATE TYPE meeting_outcome AS ENUM ('positive', 'negative', 'follow_up_needed', 'no_decision');
CREATE TYPE proposal_status AS ENUM ('draft', 'sent', 'viewed', 'negotiating', 'signed', 'expired', 'rejected', 'withdrawn');
CREATE TYPE contract_type AS ENUM ('one_time', 'retainer', 'milestone', 'subscription');
CREATE TYPE client_status AS ENUM ('onboarding', 'active', 'at_risk', 'paused', 'churned', 'completed');

-- Core tables with no foreign key dependencies
-- These must be created first

-- 1. companies (no dependencies)
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    website VARCHAR(500),
    linkedin_url VARCHAR(500),

    -- Company Details
    industry VARCHAR(100),
    employee_count VARCHAR(50),
    revenue_range VARCHAR(50),
    founded_year INTEGER,
    headquarters_city VARCHAR(100),
    headquarters_country VARCHAR(2),

    -- Research Data
    description TEXT,
    last_researched_at TIMESTAMPTZ,

    -- Technology Stack
    tech_stack TEXT[] DEFAULT '{}',
    primary_crm VARCHAR(100),
    primary_marketing_automation VARCHAR(100),

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    custom_fields JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT companies_founded_year_check CHECK (
        founded_year IS NULL OR
        founded_year BETWEEN 1800 AND EXTRACT(YEAR FROM NOW())
    )
);

-- 2. campaigns (no dependencies)
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status campaign_status DEFAULT 'DRAFT',

    -- Instantly Integration
    instantly_campaign_id VARCHAR(100) UNIQUE,
    instantly_account_id VARCHAR(100),

    -- Campaign Settings
    daily_send_limit INTEGER DEFAULT 50 CHECK (daily_send_limit > 0 AND daily_send_limit <= 1000),
    sending_schedule JSONB DEFAULT '{}',
    warmup_enabled BOOLEAN DEFAULT FALSE,
    warmup_settings JSONB DEFAULT '{}',

    -- Email Sequence
    email_sequence JSONB NOT NULL DEFAULT '[]',
    sequence_length INTEGER DEFAULT 3 CHECK (sequence_length > 0 AND sequence_length <= 10),

    -- A/B Testing Configuration
    ab_test_enabled BOOLEAN DEFAULT FALSE,
    ab_test_config JSONB DEFAULT '{}',
    ab_test_winner_confidence DECIMAL(3,2) DEFAULT 0.95 CHECK (ab_test_winner_confidence > 0.5),

    -- Performance Metrics
    total_leads INTEGER DEFAULT 0,
    active_leads INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    opens INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    positive_replies INTEGER DEFAULT 0,
    meetings_booked INTEGER DEFAULT 0,
    proposals_sent INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12,2) DEFAULT 0,

    -- Quality Metrics
    bounce_rate DECIMAL(5,2) DEFAULT 0,
    unsubscribe_rate DECIMAL(5,2) DEFAULT 0,
    spam_complaint_rate DECIMAL(5,2) DEFAULT 0,

    -- Calculated Metrics
    open_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN emails_sent > 0 THEN ROUND((opens::DECIMAL / emails_sent) * 100, 2) ELSE 0 END
    ) STORED,

    reply_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN emails_sent > 0 THEN ROUND((replies::DECIMAL / emails_sent) * 100, 2) ELSE 0 END
    ) STORED,

    meeting_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN emails_sent > 0 THEN ROUND((meetings_booked::DECIMAL / emails_sent) * 100, 2) ELSE 0 END
    ) STORED,

    -- Dates
    launched_at TIMESTAMPTZ,
    paused_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    custom_fields JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT campaigns_daily_send_limit_check CHECK (daily_send_limit > 0),
    CONSTRAINT campaigns_sequence_length_check CHECK (sequence_length > 0 AND sequence_length <= 10)
);

-- Create indexes for core tables
CREATE INDEX idx_companies_domain ON companies(domain) WHERE domain IS NOT NULL;
CREATE INDEX idx_companies_industry ON companies(industry) WHERE industry IS NOT NULL;
CREATE INDEX idx_companies_name ON companies(name) WHERE name IS NOT NULL;

CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_active ON campaigns(status) WHERE status = 'ACTIVE';
CREATE INDEX idx_campaigns_performance ON campaigns(status, revenue_generated DESC);
CREATE INDEX idx_campaigns_dates ON campaigns(launched_at, completed_at);

-- Add comments for documentation
COMMENT ON TABLE companies IS 'Company information and research data';
COMMENT ON TABLE campaigns IS 'Outreach campaign management and configuration';

-- Record migration
INSERT INTO schema_migrations (version, applied_at) VALUES ('001_core_tables', NOW());
