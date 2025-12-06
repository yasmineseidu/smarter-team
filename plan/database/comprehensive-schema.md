# Comprehensive Database Schema Plan

## Executive Summary

This document outlines the complete database architecture for the Smarter Team multi-agent system, covering 200+ tables across 13 functional domains. The schema is designed to support the entire sales lifecycle from lead generation through client delivery and retention.

## Database Architecture Overview

### Core Design Principles
1. **UUID Primary Keys**: All tables use UUID for scalability and distributed system compatibility
2. **Audit Trails**: Created/updated timestamps on all records for tracking
3. **Soft Deletes**: Status fields instead of hard deletes for data retention
4. **JSONB Flexibility**: Extensive use of JSONB for unstructured data and future-proofing
5. **Composite Indexes**: Strategic indexing for query performance optimization

### Key Entity Relationships

```
leads (core) → companies → research data
            ↓
campaigns → conversations → messages
            ↓
meetings → proposals → clients → projects → milestones → invoices
```

## Table Groupings by Domain

### 1. Core Entity Tables (Phase 1 - MVP)
- **leads**: Central entity tracking prospects through state machine
- **companies**: Company information and research data
- **campaigns**: Outreach campaigns and configuration
- **conversations**: Thread-based communication tracking
- **messages**: Individual messages within conversations

### 2. Meeting & Sales Tables (Phase 1)
- **meetings**: Scheduled and completed meetings
- **proposals**: Sales proposals and contracts
- **clients**: Converted leads with active relationships

### 3. Project Delivery Tables (Phase 2)
- **projects**: Client projects and delivery tracking
- **project_milestones**: Project phases and deliverables
- **invoices**: Financial tracking and billing
- **onboarding_progress**: Client onboarding workflow

### 4. Research & Intelligence Tables (Phase 2)
- **niches**: Market research and targeting
- **personas**: Buyer persona definitions
- **lead_research**: Individual lead research data
- **company_research**: Company intelligence
- **intent_signals**: Buying signal detection

### 5. Communication & Content Tables (Phase 2)
- **email_copy**: Campaign email templates
- **personalization_lines**: AI-generated personalization
- **knowledge_base**: FAQ and response library
- **personalization_performance**: A/B testing results

### 6. System & Operations Tables (Phase 1)
- **audit_logs**: All system actions for compliance
- **error_logs**: System error tracking
- **health_checks**: Integration monitoring
- **api_usage**: Rate limiting and cost tracking

## Database Schema by Phase

### Phase 1: MVP Foundation (First 4 weeks)
**Critical Tables for Basic Operations:**

#### Core Tables
```sql
-- Leads state machine table
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Basic Info
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_status VARCHAR(50),
    phone VARCHAR(50),
    linkedin_url VARCHAR(500),

    -- Company Info
    company_id UUID REFERENCES companies(id),
    job_title VARCHAR(200),

    -- State Machine (CRITICAL)
    status VARCHAR(50) DEFAULT 'NEW',
    previous_status VARCHAR(50),
    status_changed_at TIMESTAMPTZ,

    -- Scoring
    lead_score INTEGER DEFAULT 0,
    intent_score INTEGER DEFAULT 0,
    engagement_score INTEGER DEFAULT 0,
    fit_score INTEGER DEFAULT 0,

    -- Campaign
    current_campaign_id UUID REFERENCES campaigns(id),
    campaign_entered_at TIMESTAMPTZ,

    -- Source tracking
    source VARCHAR(100),
    source_campaign VARCHAR(100),
    import_batch_id UUID,

    -- Flags
    do_not_contact BOOLEAN DEFAULT FALSE,
    unsubscribed BOOLEAN DEFAULT FALSE,
    bounced BOOLEAN DEFAULT FALSE,

    -- Metadata
    tags TEXT[],
    custom_fields JSONB
);

-- Company information
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    website VARCHAR(500),
    linkedin_url VARCHAR(500),

    industry VARCHAR(100),
    employee_count VARCHAR(50),
    revenue_range VARCHAR(50),
    founded_year INTEGER,
    headquarters_city VARCHAR(100),
    headquarters_country VARCHAR(100),

    description TEXT,
    last_researched_at TIMESTAMPTZ,
    tech_stack TEXT[],
    tags TEXT[],
    custom_fields JSONB
);

-- Campaign management
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'DRAFT',

    -- Targeting
    niche_id UUID REFERENCES niches(id),
    persona_id UUID REFERENCES personas(id),

    -- Instantly integration
    instantly_campaign_id VARCHAR(100),

    -- Settings
    daily_send_limit INTEGER DEFAULT 50,
    sending_schedule JSONB,
    email_sequence JSONB,

    -- A/B Testing
    ab_test_enabled BOOLEAN DEFAULT FALSE,
    ab_test_config JSONB,

    -- Performance tracking
    total_leads INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    opens INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    meetings_booked INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12,2) DEFAULT 0,

    tags TEXT[],
    custom_fields JSONB
);

-- Conversation threads
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),

    -- Thread management
    thread_id VARCHAR(255), -- External thread ID (Instantly)
    subject VARCHAR(500),
    channel VARCHAR(50), -- email, linkedin, sms

    -- Status
    status VARCHAR(50),
    last_message_at TIMESTAMPTZ,
    last_message_direction VARCHAR(10),

    -- Sentiment analysis
    overall_sentiment VARCHAR(50),
    sentiment_score INTEGER,

    tags TEXT[]
);

-- Individual messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    conversation_id UUID REFERENCES conversations(id),
    lead_id UUID REFERENCES leads(id),

    -- Message details
    direction VARCHAR(10), -- inbound, outbound
    channel VARCHAR(50),
    subject VARCHAR(500),
    body TEXT,
    html_body TEXT,

    -- AI classification
    message_type VARCHAR(50),
    response_type VARCHAR(50),

    -- Human approval workflow
    tier VARCHAR(50), -- auto_send, approval, escalation
    status VARCHAR(50),
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,

    -- Draft tracking for learning
    draft_body TEXT,
    edited BOOLEAN DEFAULT FALSE,
    original_draft TEXT,

    -- Sentiment
    sentiment VARCHAR(50),
    sentiment_score INTEGER,

    -- External integration
    external_id VARCHAR(255), -- Instantly message ID
    metadata JSONB
);

-- Meeting management
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),

    -- Meeting details
    title VARCHAR(255),
    scheduled_at TIMESTAMPTZ,
    duration_minutes INTEGER DEFAULT 30,
    meeting_type VARCHAR(50),

    -- Cal.com integration
    cal_event_id VARCHAR(255),
    cal_booking_uid VARCHAR(255),
    meeting_link VARCHAR(500),

    -- Status tracking
    status VARCHAR(50),

    -- Preparation
    prep_sent BOOLEAN DEFAULT FALSE,
    prep_sent_at TIMESTAMPTZ,
    talking_points TEXT,

    -- Outcome
    outcome VARCHAR(50),
    outcome_notes TEXT,

    -- Fathom integration
    fathom_recording_id VARCHAR(255),
    transcript TEXT,
    transcript_summary TEXT,

    -- Reminder tracking
    reminder_24h_sent BOOLEAN DEFAULT FALSE,
    reminder_2h_sent BOOLEAN DEFAULT FALSE,
    reminder_15m_sent BOOLEAN DEFAULT FALSE,

    -- No-show handling
    no_show_count INTEGER DEFAULT 0,
    reschedule_count INTEGER DEFAULT 0
);

-- Proposal tracking
CREATE TABLE proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),
    meeting_id UUID REFERENCES meetings(id),

    -- Proposal details
    title VARCHAR(255),
    description TEXT,

    -- Pricing
    total_amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    pricing_breakdown JSONB,
    payment_terms VARCHAR(100),

    -- Scope
    scope_summary TEXT,
    deliverables JSONB,
    timeline TEXT,
    milestones JSONB,

    -- PandaDoc integration
    pandadoc_id VARCHAR(255),
    pandadoc_status VARCHAR(50),
    document_url VARCHAR(500),

    -- Status tracking
    status VARCHAR(50),
    sent_at TIMESTAMPTZ,
    viewed_at TIMESTAMPTZ,
    signed_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,

    -- Analytics
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMPTZ,
    time_spent_seconds INTEGER,

    -- Follow-up tracking
    followup_count INTEGER DEFAULT 0,
    last_followup_at TIMESTAMPTZ,

    -- Negotiation
    negotiation_count INTEGER DEFAULT 0,
    original_amount DECIMAL(12,2),
    discount_applied DECIMAL(12,2),
    discount_reason TEXT
);

-- Client management
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Links
    lead_id UUID REFERENCES leads(id),
    company_id UUID REFERENCES companies(id),

    -- Client info
    name VARCHAR(255),
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    primary_contact_phone VARCHAR(50),

    -- Status
    status VARCHAR(50),

    -- Contract
    contract_start_date DATE,
    contract_end_date DATE,
    contract_value DECIMAL(12,2),
    contract_type VARCHAR(50),

    -- Financial
    total_revenue DECIMAL(12,2) DEFAULT 0,
    total_paid DECIMAL(12,2) DEFAULT 0,
    outstanding_balance DECIMAL(12,2) DEFAULT 0,

    -- Health metrics
    satisfaction_score INTEGER,
    churn_risk_score INTEGER,
    last_engagement_at TIMESTAMPTZ,

    -- External IDs
    ghl_contact_id VARCHAR(255),
    airtable_record_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),

    -- Metadata
    tags TEXT[],
    custom_fields JSONB
);
```

#### System Tables (Phase 1)
```sql
-- Audit logging (CRITICAL for compliance)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    actor VARCHAR(100), -- agent name or user id
    action VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id UUID,

    old_values JSONB,
    new_values JSONB,

    ip_address VARCHAR(50),
    user_agent TEXT
);

-- Error tracking
CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    agent_name VARCHAR(100),
    error_type VARCHAR(100),
    error_message TEXT,
    stack_trace TEXT,

    severity VARCHAR(50),

    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,

    metadata JSONB
);

-- Health monitoring
CREATE TABLE health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    service VARCHAR(100),
    endpoint VARCHAR(255),

    status VARCHAR(50),
    response_time_ms INTEGER,

    error_message TEXT
);

-- API usage tracking
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    service VARCHAR(100),
    endpoint VARCHAR(255),

    request_count INTEGER DEFAULT 1,
    tokens_used INTEGER,

    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,

    cost_usd DECIMAL(10,4)
);
```

### Phase 2: Intelligence & Delivery (Next 4 weeks)

#### Research Tables
```sql
-- Niche research
CREATE TABLE niches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    name VARCHAR(255),
    description TEXT,
    industry VARCHAR(100),

    -- AI scoring
    market_size_score INTEGER,
    pain_intensity_score INTEGER,
    ability_to_pay_score INTEGER,
    competition_score INTEGER,
    overall_score INTEGER,

    -- Research data
    pain_points TEXT[],
    common_objections TEXT[],
    buying_triggers TEXT[],
    recommended_messaging TEXT,

    -- Performance tracking
    leads_generated INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12,2) DEFAULT 0,

    status VARCHAR(50)
);

-- Persona definitions
CREATE TABLE personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    niche_id UUID REFERENCES niches(id),

    name VARCHAR(255),
    job_titles TEXT[],

    -- Profile
    day_in_life TEXT,
    goals TEXT[],
    kpis TEXT[],
    frustrations TEXT[],

    -- Communication
    language_patterns TEXT[],
    jargon TEXT[],
    preferred_channels TEXT[],

    -- Behavior
    where_they_hang_out TEXT[],
    what_they_read TEXT[],
    influencers TEXT[],

    -- Buying
    buying_triggers TEXT[],
    objection_patterns TEXT[],
    decision_criteria TEXT[],

    -- Performance
    leads_generated INTEGER DEFAULT 0,
    deals_won INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12,2) DEFAULT 0
);

-- Lead research data
CREATE TABLE lead_research (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),

    -- LinkedIn data
    linkedin_headline TEXT,
    linkedin_summary TEXT,
    linkedin_recent_posts JSONB,
    linkedin_activity_summary TEXT,

    -- Career history
    career_history JSONB,
    education JSONB,
    skills TEXT[],

    -- Media mentions
    news_mentions JSONB,
    podcast_appearances JSONB,
    speaking_engagements JSONB,
    awards JSONB,

    -- Social media
    twitter_handle VARCHAR(100),
    twitter_recent_posts JSONB,

    -- AI personalization
    personalization_angles JSONB,
    recommended_angle TEXT,

    -- Metadata
    research_sources TEXT[],
    last_updated_at TIMESTAMPTZ
);

-- Company research data
CREATE TABLE company_research (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    company_id UUID REFERENCES companies(id),

    -- Recent events
    recent_news JSONB,
    funding_history JSONB,
    acquisitions JSONB,
    leadership_changes JSONB,

    -- LinkedIn data
    linkedin_recent_posts JSONB,
    linkedin_follower_count INTEGER,
    linkedin_employee_count INTEGER,

    -- Job market signals
    current_job_postings JSONB,
    hiring_trends TEXT,

    -- AI analysis
    growth_signals TEXT[],
    pain_signals TEXT[],
    trigger_events JSONB,

    -- Metadata
    research_sources TEXT[],
    last_updated_at TIMESTAMPTZ
);

-- Intent signal tracking
CREATE TABLE intent_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),
    company_id UUID REFERENCES companies(id),

    -- Signal details
    signal_type VARCHAR(100),
    signal_description TEXT,
    signal_strength INTEGER, -- 1-10
    signal_source VARCHAR(100),

    -- Context
    raw_data JSONB,

    -- Action taken
    action_taken VARCHAR(100),
    action_taken_at TIMESTAMPTZ
);
```

#### Content & Communication Tables
```sql
-- Email copy management
CREATE TABLE email_copy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    campaign_id UUID REFERENCES campaigns(id),

    -- Copy details
    sequence_position INTEGER,
    subject VARCHAR(255),
    body TEXT,

    -- A/B testing
    variant_name VARCHAR(50),
    is_control BOOLEAN DEFAULT FALSE,

    -- Approval workflow
    status VARCHAR(50),
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,

    -- Performance tracking
    sends INTEGER DEFAULT 0,
    opens INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    positive_replies INTEGER DEFAULT 0
);

-- Personalization lines
CREATE TABLE personalization_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    lead_id UUID REFERENCES leads(id),

    -- Content
    line TEXT,
    source_citation TEXT,
    confidence_score INTEGER,

    -- Review workflow
    status VARCHAR(50),
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,

    -- Learning tracking
    original_line TEXT,
    edited BOOLEAN DEFAULT FALSE,
    edit_reason TEXT,

    -- Performance
    email_sent BOOLEAN DEFAULT FALSE,
    response_received BOOLEAN DEFAULT FALSE,
    response_type VARCHAR(50)
);

-- Knowledge base
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Content
    category VARCHAR(100),
    question TEXT,
    answer TEXT,

    -- Usage analytics
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,

    -- Status
    status VARCHAR(50),
    source VARCHAR(100) -- manual, learned
);
```

#### Project Delivery Tables
```sql
-- Project management
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    client_id UUID REFERENCES clients(id),
    proposal_id UUID REFERENCES proposals(id),

    -- Project info
    name VARCHAR(255),
    description TEXT,
    project_type VARCHAR(100),

    -- Status
    status VARCHAR(50),

    -- Timeline
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,

    -- Scope
    original_scope TEXT,
    current_scope TEXT,
    scope_changes_count INTEGER DEFAULT 0,

    -- Progress
    progress_percentage INTEGER DEFAULT 0,
    current_phase VARCHAR(100),

    -- Financial
    budget DECIMAL(12,2),
    actual_cost DECIMAL(12,2),

    -- External IDs
    clickup_project_id VARCHAR(255),
    airtable_record_id VARCHAR(255),
    drive_folder_id VARCHAR(255),

    -- Metadata
    tags TEXT[]
);

-- Project milestones
CREATE TABLE project_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    project_id UUID REFERENCES projects(id),

    -- Milestone info
    name VARCHAR(255),
    description TEXT,
    sequence_order INTEGER,

    -- Timeline
    target_date DATE,
    actual_completion_date DATE,

    -- Status
    status VARCHAR(50),

    -- Approval
    requires_client_approval BOOLEAN DEFAULT TRUE,
    approved_by VARCHAR(255),
    approved_at TIMESTAMPTZ,

    -- Revision tracking
    revision_count INTEGER DEFAULT 0,
    max_revisions INTEGER DEFAULT 3,

    -- Payment trigger
    payment_trigger BOOLEAN DEFAULT FALSE,
    payment_amount DECIMAL(12,2),
    payment_status VARCHAR(50)
);

-- Invoice management
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    client_id UUID REFERENCES clients(id),
    project_id UUID REFERENCES projects(id),
    milestone_id UUID REFERENCES project_milestones(id),

    -- Invoice info
    invoice_number VARCHAR(50) UNIQUE,
    description TEXT,

    -- Amounts
    subtotal DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    discount_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',

    -- Dates
    issue_date DATE,
    due_date DATE,
    paid_date DATE,

    -- Status
    status VARCHAR(50),

    -- Stripe integration
    stripe_invoice_id VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),

    -- Reminders
    reminder_count INTEGER DEFAULT 0,
    last_reminder_at TIMESTAMPTZ,

    -- Line items
    line_items JSONB
);

-- Onboarding progress
CREATE TABLE onboarding_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    client_id UUID REFERENCES clients(id),

    -- Overall status
    status VARCHAR(50),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Step tracking
    welcome_email_sent BOOLEAN DEFAULT FALSE,
    welcome_email_sent_at TIMESTAMPTZ,

    intake_form_sent BOOLEAN DEFAULT FALSE,
    intake_form_sent_at TIMESTAMPTZ,
    intake_form_completed BOOLEAN DEFAULT FALSE,
    intake_form_completed_at TIMESTAMPTZ,

    access_requested BOOLEAN DEFAULT FALSE,
    access_requested_at TIMESTAMPTZ,
    access_received BOOLEAN DEFAULT FALSE,
    access_received_at TIMESTAMPTZ,

    kickoff_scheduled BOOLEAN DEFAULT FALSE,
    kickoff_scheduled_at TIMESTAMPTZ,
    kickoff_meeting_id UUID REFERENCES meetings(id),
    kickoff_completed BOOLEAN DEFAULT FALSE,
    kickoff_completed_at TIMESTAMPTZ,

    internal_setup_complete BOOLEAN DEFAULT FALSE,
    internal_setup_at TIMESTAMPTZ,

    scope_documented BOOLEAN DEFAULT FALSE,
    scope_documented_at TIMESTAMPTZ,

    -- Stuck detection
    stuck_alert_sent BOOLEAN DEFAULT FALSE,
    stuck_alert_sent_at TIMESTAMPTZ,
    stuck_reminder_count INTEGER DEFAULT 0
);
```

## Indexing Strategy

### Critical Indexes for Performance
```sql
-- Core lookups
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_company ON leads(company_id);
CREATE INDEX idx_leads_campaign ON leads(current_campaign_id);
CREATE INDEX idx_companies_domain ON companies(domain);

-- Conversation queries
CREATE INDEX idx_conversations_lead ON conversations(lead_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- Meeting scheduling
CREATE INDEX idx_meetings_scheduled ON meetings(scheduled_at);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_lead ON meetings(lead_id);

-- Proposals tracking
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_lead ON proposals(lead_id);

-- Time-based queries
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_error_logs_created ON error_logs(created_at);
CREATE INDEX idx_health_checks_created ON health_checks(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_leads_status_score ON leads(status, lead_score DESC);
CREATE INDEX idx_campaigns_status_performance ON campaigns(status, created_at);
CREATE INDEX idx_conversations_lead_last ON conversations(lead_id, last_message_at DESC);
```

## Migration Strategy

### Phase 1 Migration (Week 1)
1. Create core entity tables (leads, companies, campaigns, conversations, messages)
2. Create system tables (audit_logs, error_logs, health_checks, api_usage)
3. Add critical indexes
4. Set up foreign key constraints
5. Create triggers for updated_at timestamps

### Phase 2 Migration (Week 5)
1. Create research tables (niches, personas, lead_research, company_research)
2. Create content tables (email_copy, personalization_lines, knowledge_base)
3. Create delivery tables (projects, milestones, invoices, onboarding_progress)
4. Add remaining indexes
5. Set up RLS (Row Level Security) policies

## Data Retention & Archival

### Retention Policies
- **audit_logs**: 7 years (compliance)
- **error_logs**: 1 year
- **conversation_history**: 5 years
- **email_tracking**: 2 years
- **research_data**: 3 years

### Archival Strategy
- Partition large tables by date
- Move old data to cold storage
- Maintain active indexes for recent data only

## Security Considerations

### Row Level Security (RLS)
- Enable RLS on all tables
- Agent-specific access policies
- Human-in-the-loop approval visibility

### Encryption
- Encrypt sensitive fields (PII, financial data)
- Use PostgreSQL pgcrypto extension
- Key management through Supabase

### Compliance
- GDPR compliance with data deletion
- CCPA compliance with data export
- Audit trail for all modifications

## Performance Optimization

### Query Optimization
- Materialized views for dashboards
- Common table expressions for complex queries
- Proper join ordering

### Caching Strategy
- Redis cache for frequent lookups
- Application-level caching
- Database connection pooling

### Scaling Considerations
- Read replicas for analytics
- Partitioning for high-volume tables
- Connection pooling (PgBouncer)

## Monitoring & Maintenance

### Health Checks
- Table size monitoring
- Index usage statistics
- Query performance analysis
- Connection pool monitoring

### Maintenance Tasks
- Daily VACUUM and ANALYZE
- Weekly index rebuilds
- Monthly statistics updates
- Quarterly archival processes

## Next Steps

1. **Review and approve** this schema plan
2. **Create migration files** for each phase
3. **Set up Supabase project** with proper configuration
4. **Execute Phase 1 migration** for MVP functionality
5. **Test with sample data** before production use
6. **Monitor performance** and adjust as needed
