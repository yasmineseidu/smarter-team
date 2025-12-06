-- Migration 004: Sales Process Tables
-- Creates meetings, proposals, and clients tables
-- Dependencies: 001_core_tables, 002_lead_entities

-- Meetings table (depends on leads and campaigns)
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Association
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,

    -- Meeting Details
    title VARCHAR(255) NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER DEFAULT 30 CHECK (duration_minutes > 0 AND duration_minutes <= 480),
    meeting_type meeting_type DEFAULT 'discovery',

    -- Cal.com Integration
    cal_event_id VARCHAR(255) UNIQUE,
    cal_booking_uid VARCHAR(255) UNIQUE,
    meeting_link VARCHAR(500),

    -- Status Tracking
    status meeting_status DEFAULT 'scheduled',
    outcome meeting_outcome,
    outcome_notes TEXT,

    -- Preparation (AI-generated)
    prep_sent BOOLEAN DEFAULT FALSE,
    prep_sent_at TIMESTAMPTZ,
    talking_points TEXT,
    prep_rating INTEGER CHECK (prep_rating >= 1 AND prep_rating <= 5),

    -- Recording & Transcription
    recording_url VARCHAR(500),
    transcript TEXT,
    transcript_summary TEXT,
    transcript_analyzed_at TIMESTAMPTZ,

    -- Integration Services
    fathom_recording_id VARCHAR(255),
    zoom_meeting_id VARCHAR(255),
    google_meet_id VARCHAR(255),

    -- Reminder Tracking
    reminder_24h_sent BOOLEAN DEFAULT FALSE,
    reminder_2h_sent BOOLEAN DEFAULT FALSE,
    reminder_15m_sent BOOLEAN DEFAULT FALSE,
    reminder_count INTEGER DEFAULT 0,

    -- No-show Handling
    no_show_count INTEGER DEFAULT 0,
    reschedule_count INTEGER DEFAULT 0,
    max_no_shows INTEGER DEFAULT 3,

    -- Follow-up Actions
    follow_up_required BOOLEAN DEFAULT TRUE,
    follow_up_scheduled_at TIMESTAMPTZ,
    proposal_required BOOLEAN DEFAULT FALSE,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT meetings_scheduled_future CHECK (scheduled_at >= created_at),
    CONSTRAINT meetings_duration_check CHECK (duration_minutes > 0 AND duration_minutes <= 480),
    CONSTRAINT meetings_no_show_limit CHECK (no_show_count <= max_no_shows)
);

-- Proposals table (depends on leads, will also reference meetings and clients)
CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Association
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meetings(id) ON DELETE SET NULL,
    client_id UUID, -- Will reference clients table after it's created

    -- Proposal Details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    proposal_number VARCHAR(50) UNIQUE,

    -- Pricing
    total_amount DECIMAL(12,2) NOT NULL CHECK (total_amount > 0),
    currency VARCHAR(3) DEFAULT 'USD',
    pricing_breakdown JSONB DEFAULT '{}',
    payment_terms VARCHAR(100) DEFAULT 'Net 30',
    contract_type contract_type DEFAULT 'one_time',

    -- Scope
    scope_summary TEXT,
    deliverables JSONB DEFAULT '{}',
    timeline TEXT,
    milestones JSONB DEFAULT '{}',
    assumptions TEXT[],
    exclusions TEXT[],

    -- PandaDoc Integration
    pandadoc_id VARCHAR(255) UNIQUE,
    pandadoc_status VARCHAR(50),
    document_url VARCHAR(500),
    template_id VARCHAR(100),

    -- Status Tracking
    status proposal_status DEFAULT 'draft',
    sent_at TIMESTAMPTZ,
    viewed_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,

    -- Analytics
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMPTZ,
    total_time_spent_seconds INTEGER DEFAULT 0,
    sections_viewed JSONB DEFAULT '[]',

    -- Follow-up Management
    followup_count INTEGER DEFAULT 0,
    last_followup_at TIMESTAMPTZ,
    next_followup_at TIMESTAMPTZ,
    max_followups INTEGER DEFAULT 20,

    -- Negotiation
    negotiation_count INTEGER DEFAULT 0,
    original_amount DECIMAL(12,2),
    discount_applied DECIMAL(12,2) DEFAULT 0,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    discount_reason TEXT,
    max_discount_percentage DECIMAL(5,2) DEFAULT 20,

    -- Approval
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    approval_notes TEXT,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    custom_fields JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT proposals_discount_logic CHECK (
        discount_applied >= 0 AND
        (original_amount IS NULL OR discount_applied <= original_amount) AND
        discount_percentage >= 0 AND
        discount_percentage <= max_discount_percentage
    ),
    CONSTRAINT proposals_expiry CHECK (
        expired_at IS NULL OR expired_at > sent_at
    )
);

-- Clients table (depends on leads, companies, proposals)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Links to Original Records
    lead_id UUID UNIQUE REFERENCES leads(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    proposal_id UUID REFERENCES proposals(id) ON DELETE SET NULL,

    -- Client Information
    client_name VARCHAR(255),
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    primary_contact_phone VARCHAR(50),

    -- Account Management
    account_manager VARCHAR(100),
    client_success_manager VARCHAR(100),

    -- Status
    status client_status DEFAULT 'onboarding',

    -- Contract Details
    contract_start_date DATE,
    contract_end_date DATE,
    contract_value DECIMAL(12,2) NOT NULL,
    contract_type contract_type DEFAULT 'one_time',
    billing_frequency VARCHAR(50), -- monthly, quarterly, annually

    -- Financial Tracking
    total_revenue DECIMAL(12,2) DEFAULT 0,
    total_paid DECIMAL(12,2) DEFAULT 0,
    outstanding_balance DECIMAL(12,2) DEFAULT 0,
    average_monthly_revenue DECIMAL(12,2),

    -- Health Metrics
    satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 10),
    churn_risk_score INTEGER DEFAULT 0 CHECK (churn_risk_score >= 0 AND churn_risk_score <= 100),
    health_score INTEGER DEFAULT 80 CHECK (health_score >= 0 AND health_score <= 100),
    last_engagement_at TIMESTAMPTZ,

    -- Integration IDs
    ghl_contact_id VARCHAR(255),
    airtable_record_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    quickbooks_customer_id VARCHAR(255),

    -- Communication Preferences
    preferred_contact_method VARCHAR(50) DEFAULT 'email',
    communication_frequency VARCHAR(50) DEFAULT 'weekly',

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    custom_fields JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT clients_contract_dates CHECK (
        contract_end_date IS NULL OR
        contract_end_date > contract_start_date
    ),
    CONSTRAINT clients_positive_value CHECK (contract_value > 0)
);

-- Add foreign key constraint for proposals.client_id after clients table is created
ALTER TABLE proposals
ADD CONSTRAINT fk_proposals_client
FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL;

-- Indexes for meetings
CREATE INDEX idx_meetings_scheduled ON meetings(scheduled_at) WHERE status = 'scheduled';
CREATE INDEX idx_meetings_lead ON meetings(lead_id);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_today ON meetings(scheduled_at)
WHERE scheduled_at >= NOW()::date AND scheduled_at < NOW()::date + 1;
CREATE INDEX idx_meetings_upcoming ON meetings(scheduled_at) WHERE status = 'scheduled';
CREATE INDEX idx_meetings_cal_event ON meetings(cal_event_id) WHERE cal_event_id IS NOT NULL;

-- Indexes for proposals
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_lead ON proposals(lead_id);
CREATE INDEX idx_proposal_meeting ON proposals(meeting_id) WHERE meeting_id IS NOT NULL;
CREATE INDEX idx_proposals_client ON proposals(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX idx_proposals_amount ON proposals(total_amount DESC);
CREATE INDEX idx_proposals_followup ON proposals(status, next_followup_at)
WHERE status IN ('sent', 'viewed');
CREATE INDEX idx_proposals_pandadoc ON proposals(pandadoc_id) WHERE pandadoc_id IS NOT NULL;

-- Indexes for clients
CREATE INDEX idx_clients_status ON clients(status);
CREATE INDEX idx_clients_health ON clients(churn_risk_score DESC) WHERE status = 'active';
CREATE INDEX idx_clients_revenue ON clients(total_revenue DESC);
CREATE INDEX idx_clients_account_manager ON clients(account_manager) WHERE account_manager IS NOT NULL;
CREATE INDEX idx_clients_contract_end ON clients(contract_end_date) WHERE contract_end_date IS NOT NULL;

-- Comments for documentation
COMMENT ON TABLE meetings IS 'Meeting scheduling and tracking';
COMMENT ON TABLE proposals IS 'Sales proposal and contract management';
COMMENT ON TABLE clients IS 'Converted leads with active relationships';

-- Record migration
INSERT INTO schema_migrations (version, applied_at) VALUES ('004_sales_process_tables', NOW());
