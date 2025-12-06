-- Migration 002: Lead and Related Entities
-- Creates the lead state machine and related tables
-- Dependencies: 001_core_tables (companies, campaigns)

-- Lead state machine table (depends on companies and campaigns)
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_status VARCHAR(50) CHECK (
        email_verification_status IN ('valid', 'invalid', 'risky', 'unknown', 'unverified')
    ),
    phone VARCHAR(50),
    linkedin_url VARCHAR(500),

    -- Company Association
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    job_title VARCHAR(200),

    -- State Machine (CRITICAL for lead flow)
    status VARCHAR(50) DEFAULT 'NEW' CHECK (
        status IN ('NEW', 'ENRICHING', 'VERIFIED', 'IN_CAMPAIGN', 'ENGAGED', 'MEETING_BOOKED',
                  'MEETING_COMPLETED', 'PROPOSAL_SENT', 'NEGOTIATING', 'CLOSED_WON', 'CLOSED_LOST',
                  'ONBOARDING', 'ACTIVE_PROJECT', 'PROJECT_COMPLETED', 'MAINTENANCE',
                  'NURTURE_POOL', 'REACTIVATION_POOL', 'LONG_TERM_NURTURE', 'DEAD_LEAD',
                  'INVALID_EMAIL', 'BOUNCED', 'UNSUBSCRIBED', 'MEETING_NO_SHOW',
                  'PROPOSAL_EXPIRED', 'ONBOARDING_STUCK', 'PROJECT_PAUSED', 'PROJECT_CANCELLED')
    ),
    previous_status VARCHAR(50),
    status_changed_at TIMESTAMPTZ,

    -- Lead Scoring (0-100 scale)
    lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100),
    intent_score INTEGER DEFAULT 0 CHECK (intent_score >= 0 AND intent_score <= 100),
    engagement_score INTEGER DEFAULT 0 CHECK (engagement_score >= 0 AND engagement_score <= 100),
    fit_score INTEGER DEFAULT 0 CHECK (fit_score >= 0 AND fit_score <= 100),

    -- Campaign Association
    current_campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    campaign_entered_at TIMESTAMPTZ,

    -- Source Tracking
    source VARCHAR(100) NOT NULL,
    source_campaign VARCHAR(100),
    import_batch_id UUID,

    -- Data Quality
    enrichment_complete BOOLEAN DEFAULT FALSE,
    last_enriched_at TIMESTAMPTZ,
    data_quality_score INTEGER DEFAULT 0 CHECK (data_quality_score >= 0 AND data_quality_score <= 100),

    -- Personalization (AI-generated)
    personalization_line TEXT,
    personalization_confidence INTEGER CHECK (personalization_confidence >= 0 AND personalization_confidence <= 100),
    personalization_source TEXT,

    -- Communication Preferences
    timezone VARCHAR(50) DEFAULT 'UTC',
    optimal_send_time TIME,

    -- Compliance Flags
    do_not_contact BOOLEAN DEFAULT FALSE,
    unsubscribed BOOLEAN DEFAULT FALSE,
    bounced BOOLEAN DEFAULT FALSE,
    gdpr_consent_given BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMPTZ,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    custom_fields JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT leads_email_check CHECK (
        email IS NULL OR
        email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    ),
    CONSTRAINT leads_linkedin_check CHECK (
        linkedin_url IS NULL OR
        linkedin_url ~* '^https://(www\.)?linkedin\.com/.*'
    )
);

-- Lead status history for tracking state changes
CREATE TABLE lead_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,

    changed_by VARCHAR(100), -- agent name or 'human'
    change_reason TEXT,

    metadata JSONB DEFAULT '{}'
);

-- Indexes for leads table
CREATE INDEX idx_leads_email ON leads(email) WHERE email IS NOT NULL;
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_company ON leads(company_id) WHERE company_id IS NOT NULL;
CREATE INDEX idx_leads_campaign ON leads(current_campaign_id) WHERE current_campaign_id IS NOT NULL;
CREATE INDEX idx_leads_score ON leads(lead_score DESC) WHERE status NOT IN ('DEAD_LEAD', 'INVALID_EMAIL');
CREATE INDEX idx_leads_source ON leads(source, created_at);
CREATE INDEX idx_leads_status_changed ON leads(status_changed_at DESC);
CREATE INDEX idx_leads_unsubscribed ON leads(do_not_contact, unsubscribed) WHERE do_not_contact = TRUE OR unsubscribed = TRUE;
CREATE INDEX idx_leads_active_campaign ON leads(current_campaign_id, status) WHERE current_campaign_id IS NOT NULL;

-- Indexes for lead_status_history
CREATE INDEX idx_lead_status_history_lead ON lead_status_history(lead_id);
CREATE INDEX idx_lead_status_history_created ON lead_status_history(created_at DESC);
CREATE INDEX idx_lead_status_history_transition ON lead_status_history(from_status, to_status);

-- Comments for documentation
COMMENT ON TABLE leads IS 'Central entity tracking prospects through the sales state machine';
COMMENT ON TABLE lead_status_history IS 'Audit trail of all lead status transitions';

-- Record migration
INSERT INTO schema_migrations (version, applied_at) VALUES ('002_lead_entities', NOW());
