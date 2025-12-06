# Core Database Schema Specification

## Overview
This specification defines the core database schema for the Smarter Team multi-agent system. It covers all essential tables needed for MVP launch and scales to support the full sales lifecycle.

## Design Principles

1. **UUID Primary Keys**: All tables use UUID for scalability and distributed systems
2. **Timestamp Tracking**: Created/updated timestamps on all records
3. **Soft Deletes**: Status fields instead of hard deletes
4. **JSONB Flexibility**: Use JSONB for unstructured data and future-proofing
5. **Audit Ready**: Full audit trail for compliance
6. **Performance Optimized**: Strategic indexing based on query patterns

## Table Definitions

### 1. leads

**Purpose**: Central entity tracking prospects through the sales state machine

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Information
    first_name VARCHAR(100) CHECK (first_name IS NOT NULL OR source IN ('import', 'webhook')),
    last_name VARCHAR(100) CHECK (last_name IS NOT NULL OR source IN ('import', 'webhook')),
    email VARCHAR(255) UNIQUE,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_status VARCHAR(50) CHECK (email_verification_status IN ('valid', 'invalid', 'risky', 'unknown', 'unverified')),
    phone VARCHAR(50),
    linkedin_url VARCHAR(500) CHECK (linkedin_url ~ '^https://(www\.)?linkedin\.com/.*' OR linkedin_url IS NULL),

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
    CONSTRAINT leads_status_transition_check CHECK (
        previous_status IS NULL OR
        -- Add business logic for valid status transitions
        TRUE -- Will be implemented with trigger
    )
);

-- Triggers
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER log_lead_status_change
    BEFORE UPDATE ON leads
    FOR EACH ROW WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION log_status_change();
```

### 2. companies

**Purpose**: Company information and research data

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE CHECK (
        domain IS NULL OR
        domain ~* '^[a-z0-9.-]+\.[a-z]{2,}$'
    ),
    website VARCHAR(500) CHECK (
        website IS NULL OR
        website ~* '^https?://.*'
    ),
    linkedin_url VARCHAR(500) CHECK (
        linkedin_url IS NULL OR
        linkedin_url ~* '^https://(www\.)?linkedin\.com/company/.*'
    ),

    -- Company Details
    industry VARCHAR(100),
    employee_count VARCHAR(50) CHECK (
        employee_count IS NULL OR
        employee_count ~* '^([0-9]+(-[0-9]+)?|[0-9]+\+|[0-9kKmM]+)$'
    ),
    revenue_range VARCHAR(50),
    founded_year INTEGER CHECK (founded_year >= 1800 AND founded_year <= EXTRACT(YEAR FROM NOW())),
    headquarters_city VARCHAR(100),
    headquarters_country VARCHAR(2) CHECK (headquarters_country ~* '^[A-Z]{2}$'),

    -- Research Data
    description TEXT,
    last_researched_at TIMESTAMPTZ,
    company_size ENUM ('startup', 'small', 'medium', 'large', 'enterprise'),

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

-- Triggers
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3. campaigns

**Purpose**: Outreach campaign management and configuration

```sql
CREATE TYPE campaign_status AS ENUM ('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED');

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status campaign_status DEFAULT 'DRAFT',

    -- Targeting Configuration
    niche_id UUID REFERENCES niches(id) ON DELETE SET NULL,
    persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
    target_criteria JSONB DEFAULT '{}', -- Flexible targeting rules

    -- Instantly Integration
    instantly_campaign_id VARCHAR(100) UNIQUE,
    instantly_account_id VARCHAR(100),

    -- Campaign Settings
    daily_send_limit INTEGER DEFAULT 50 CHECK (daily_send_limit > 0 AND daily_send_limit <= 1000),
    sending_schedule JSONB DEFAULT '{}', -- Days/times to send
    warmup_enabled BOOLEAN DEFAULT FALSE,
    warmup_settings JSONB DEFAULT '{}',

    -- Email Sequence
    email_sequence JSONB NOT NULL DEFAULT '[]', -- Array of email steps
    sequence_length INTEGER DEFAULT 3 CHECK (sequence_length > 0 AND sequence_length <= 10),

    -- A/B Testing Configuration
    ab_test_enabled BOOLEAN DEFAULT FALSE,
    ab_test_config JSONB DEFAULT '{}',
    ab_test_winner_confidence DECIMAL(3,2) DEFAULT 0.95 CHECK (ab_test_winner_confidence > 0.5),

    -- Performance Metrics (automatically updated)
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

-- Triggers
CREATE TRIGGER update_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes for campaign performance queries
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_performance ON campaigns(status, revenue_generated DESC);
CREATE INDEX idx_campaigns_dates ON campaigns(launched_at, completed_at);
```

### 4. conversations

**Purpose**: Thread-based communication tracking

```sql
CREATE TYPE conversation_status AS ENUM ('active', 'resolved', 'pending_human', 'escalated');
CREATE TYPE message_direction AS ENUM ('inbound', 'outbound');
CREATE TYPE communication_channel AS ENUM ('email', 'linkedin', 'sms', 'call');

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Association
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,

    -- Thread Management
    thread_id VARCHAR(255), -- External thread ID (Instantly, etc.)
    external_source VARCHAR(100), -- instantly, linkedin, etc.
    subject VARCHAR(500),
    channel communication_channel DEFAULT 'email',

    -- Status
    status conversation_status DEFAULT 'active',
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),

    -- Activity Tracking
    last_message_at TIMESTAMPTZ,
    last_message_direction message_direction,
    message_count INTEGER DEFAULT 0,

    -- Sentiment Analysis
    overall_sentiment VARCHAR(50), -- positive, negative, neutral
    sentiment_score INTEGER CHECK (sentiment_score >= -100 AND sentiment_score <= 100),
    sentiment_updated_at TIMESTAMPTZ,

    -- Human Review Queue
    needs_review BOOLEAN DEFAULT FALSE,
    review_reason TEXT,
    reviewed_at TIMESTAMPTZ,
    reviewed_by VARCHAR(100),

    -- Automatic Classification
    intent VARCHAR(100), -- meeting_request, question, objection, etc.
    category VARCHAR(100), -- sales, support, etc.

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT conversations_sentiment_score_check CHECK (
        sentiment_score IS NULL OR
        (sentiment_score >= -100 AND sentiment_score <= 100)
    )
);

-- Triggers
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER increment_conversation_message_count
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION increment_message_count();
```

### 5. messages

**Purpose**: Individual message tracking within conversations

```sql
CREATE TYPE message_status AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'sent', 'delivered', 'bounced', 'failed');
CREATE TYPE approval_tier AS ENUM ('auto_send', 'approval', 'escalation');
CREATE TYPE message_type AS ENUM ('initial', 'follow_up', 'reply', 'check_in', 'notification', 'personalization');

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Association
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,

    -- Message Details
    direction message_direction NOT NULL,
    channel communication_channel DEFAULT 'email',
    subject VARCHAR(500),
    body TEXT,
    html_body TEXT,

    -- Message Classification
    message_type message_type DEFAULT 'reply',
    response_type VARCHAR(50), -- positive, negative, question, objection, ooo, unsubscribe

    -- AI/Human Workflow
    tier approval_tier DEFAULT 'auto_send',
    status message_status DEFAULT 'draft',

    -- Approval Tracking
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,

    -- Draft Tracking (for learning)
    draft_body TEXT, -- Original AI-generated draft
    edited BOOLEAN DEFAULT FALSE,
    original_draft TEXT, -- For comparing with final
    edit_summary TEXT,

    -- Content Analysis
    sentiment VARCHAR(50),
    sentiment_score INTEGER CHECK (sentiment_score >= -100 AND sentiment_score <= 100),
    confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100),

    -- Delivery Tracking
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    bounced_at TIMESTAMPTZ,
    bounce_reason TEXT,

    -- External Integration
    external_id VARCHAR(255), -- Instantly message ID, etc.
    external_metadata JSONB DEFAULT '{}',

    -- Personalization Tracking
    personalization_line_id UUID REFERENCES personalization_lines(id),
    personalization_used BOOLEAN DEFAULT FALSE,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT messages_sent_after_created CHECK (
        sent_at IS NULL OR sent_at >= created_at
    ),
    CONSTRAINT messages_approval_flow CHECK (
        (tier = 'auto_send' AND status IN ('sent', 'delivered', 'bounced', 'failed')) OR
        (tier = 'approval' AND status IN ('draft', 'pending_approval', 'approved', 'rejected', 'sent', 'delivered', 'bounced', 'failed')) OR
        (tier = 'escalation' AND status IN ('draft', 'pending_approval', 'approved', 'rejected', 'sent', 'delivered', 'bounced', 'failed'))
    )
);

-- Triggers
CREATE TRIGGER update_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversation_last_message
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION update_conversation_last_message();
```

## Additional Core Tables

### 6. meetings

```sql
CREATE TYPE meeting_status AS ENUM ('scheduled', 'completed', 'no_show', 'cancelled', 'rescheduled');
CREATE TYPE meeting_type AS ENUM ('discovery', 'demo', 'closing', 'follow_up', 'check_in');
CREATE TYPE meeting_outcome AS ENUM ('positive', 'negative', 'follow_up_needed', 'no_decision');

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
```

### 7. proposals

```sql
CREATE TYPE proposal_status AS ENUM ('draft', 'sent', 'viewed', 'negotiating', 'signed', 'expired', 'rejected', 'withdrawn');
CREATE TYPE contract_type AS ENUM ('one_time', 'retainer', 'milestone', 'subscription');

CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Association
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meetings(id) ON DELETE SET NULL,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,

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
    CONSTRAINT proposals_positive_amount CHECK (total_amount > 0),
    CONSTRAINT proposals_discount_logic CHECK (
        discount_applied >= 0 AND
        discount_applied <= original_amount AND
        discount_percentage >= 0 AND
        discount_percentage <= max_discount_percentage
    ),
    CONSTRAINT proposals_expiry CHECK (
        expired_at IS NULL OR expired_at > sent_at
    )
);
```

### 8. clients

```sql
CREATE TYPE client_status AS ENUM ('onboarding', 'active', 'at_risk', 'paused', 'churned', 'completed');

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
```

## Indexes

### Core Performance Indexes
```sql
-- Lead lookup indexes
CREATE INDEX idx_leads_email ON leads(email) WHERE email IS NOT NULL;
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_company ON leads(company_id) WHERE company_id IS NOT NULL;
CREATE INDEX idx_leads_campaign ON leads(current_campaign_id) WHERE current_campaign_id IS NOT NULL;
CREATE INDEX idx_leads_score ON leads(lead_score DESC) WHERE status NOT IN ('DEAD_LEAD', 'INVALID_EMAIL');
CREATE INDEX idx_leads_source ON leads(source, created_at);

-- Company lookup indexes
CREATE INDEX idx_companies_domain ON companies(domain) WHERE domain IS NOT NULL;
CREATE INDEX idx_companies_industry ON companies(industry) WHERE industry IS NOT NULL;
CREATE INDEX idx_companies_size ON companies(employee_count) WHERE employee_count IS NOT NULL;

-- Campaign indexes
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_active ON campaigns(status) WHERE status = 'ACTIVE';
CREATE INDEX idx_campaigns_performance ON campaigns(status, revenue_generated DESC);
CREATE INDEX idx_campaigns_dates ON campaigns(launched_at, completed_at);

-- Conversation indexes
CREATE INDEX idx_conversations_lead ON conversations(lead_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
CREATE INDEX idx_conversations_needs_review ON conversations(needs_review) WHERE needs_review = TRUE;

-- Message indexes
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_created ON messages(created_at DESC);
CREATE INDEX idx_messages_status ON messages(status) WHERE status IN ('pending_approval', 'approved');
CREATE INDEX idx_messages_approval ON messages(tier, status) WHERE tier = 'approval';

-- Meeting indexes
CREATE INDEX idx_meetings_scheduled ON meetings(scheduled_at) WHERE status = 'scheduled';
CREATE INDEX idx_meetings_lead ON meetings(lead_id);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_today ON meetings(scheduled_at) WHERE scheduled_at >= NOW()::date AND scheduled_at < NOW()::date + 1;

-- Proposal indexes
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_lead ON proposals(lead_id);
CREATE INDEX idx_proposals_amount ON proposals(total_amount DESC);
CREATE INDEX idx_proposals_followup ON proposals(status, next_followup_at) WHERE status IN ('sent', 'viewed');

-- Client indexes
CREATE INDEX idx_clients_status ON clients(status);
CREATE INDEX idx_clients_health ON clients(churn_risk_score DESC) WHERE status = 'active';
CREATE INDEX idx_clients_revenue ON clients(total_revenue DESC);

-- Time-based indexes for analytics
CREATE INDEX idx_leads_created_month ON leads(date_trunc('month', created_at));
CREATE INDEX idx_conversations_created_week ON conversations(date_trunc('week', created_at));
CREATE INDEX idx_meetings_created_day ON meetings(date_trunc('day', created_at));
```

## Functions and Triggers

### Utility Functions
```sql
-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Status change logging
CREATE OR REPLACE FUNCTION log_status_change()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO lead_status_history (lead_id, from_status, to_status, changed_by, change_reason)
    VALUES (
        NEW.id,
        OLD.status,
        NEW.status,
        current_setting('app.current_agent', true),
        'Status change detected'
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Update conversation last message
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

-- Increment message count
CREATE OR REPLACE FUNCTION increment_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET message_count = message_count + 1
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

## Row Level Security (RLS)

### Security Policies
```sql
-- Enable RLS on all tables
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

-- Agent-specific policies
CREATE POLICY agents_read_leads ON leads
    FOR SELECT USING (
        current_setting('app.agent_role', true) IN ('admin', 'manager', 'sales', 'support')
    );

CREATE POLICY agents_write_leads ON leads
    FOR INSERT WITH CHECK (
        current_setting('app.agent_role', true) IN ('admin', 'manager', 'sales', 'list_builder')
    );

-- System-wide admin access
CREATE POLICY admin_full_access ON leads
    FOR ALL USING (current_setting('app.agent_role', true) = 'admin')
    WITH CHECK (current_setting('app.agent_role', true) = 'admin');
```

## Migration Order

1. **Core tables** (no dependencies):
   - companies
   - campaigns

2. **Primary entities** (depend on core):
   - leads (depends on companies, campaigns)
   - conversations (depends on leads, campaigns)
   - messages (depends on conversations, leads, campaigns)

3. **Sales process tables**:
   - meetings (depends on leads, campaigns)
   - proposals (depends on leads, meetings)
   - clients (depends on leads, companies, proposals)

4. **Supporting tables**:
   - lead_status_history
   - All indexes
   - All triggers
   - RLS policies

## Performance Considerations

1. **Partitioning**: Consider partitioning high-volume tables (messages, audit_logs) by date
2. **Connection Pooling**: Use PgBouncer for managing connections
3. **Read Replicas**: Set up read replicas for analytics queries
4. **Monitoring**: Track slow queries and index usage
5. **Vacuuming**: Regular VACUUM and ANALYZE operations

## Next Steps

1. Review this specification with the team
2. Create migration scripts
3. Set up database in Supabase
4. Test with sample data
5. Monitor performance in production
