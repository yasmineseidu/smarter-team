-- Migration 008: Meeting Management System
-- Extends meeting management with comprehensive analytics, task automation, and learning integration
-- Dependencies: 004_sales_process_tables.sql, 007_learning_system.sql

-- 1. Extend existing meetings table with additional fields
ALTER TABLE meetings
ADD COLUMN IF NOT EXISTS lifecycle_stage VARCHAR(50) DEFAULT 'scheduled',
ADD COLUMN IF NOT EXISTS preparation_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS preparation_completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS engagement_score DECIMAL(3,2) CHECK (engagement_score >= 0 AND engagement_score <= 10),
ADD COLUMN IF NOT EXISTS talk_time_ratio DECIMAL(5,3) CHECK (talk_time_ratio >= 0 AND talk_time_ratio <= 1),
ADD COLUMN IF NOT EXISTS sentiment_score DECIMAL(5,3) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
ADD COLUMN IF NOT EXISTS meeting_quality_score DECIMAL(3,2) CHECK (meeting_quality_score >= 0 AND meeting_quality_score <= 10),
ADD COLUMN IF NOT EXISTS conversion_probability DECIMAL(5,3) CHECK (conversion_probability >= 0 AND conversion_probability <= 1),
ADD COLUMN IF NOT EXISTS actual_duration_minutes INTEGER CHECK (actual_duration_minutes > 0),
ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS ended_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS attendees JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS meeting_source VARCHAR(50) DEFAULT 'calendly',
ADD COLUMN IF NOT EXISTS parent_meeting_id UUID REFERENCES meetings(id),
ADD COLUMN IF NOT EXISTS follow_up_priority VARCHAR(20) DEFAULT 'normal' CHECK (follow_up_priority IN ('critical', 'high', 'normal', 'low'));

-- Add indexes for new meeting fields
CREATE INDEX IF NOT EXISTS idx_meetings_lifecycle_stage ON meetings(lifecycle_stage);
CREATE INDEX IF NOT EXISTS idx_meetings_engagement_score ON meetings(engagement_score);
CREATE INDEX IF NOT EXISTS idx_meetings_meeting_source ON meetings(meeting_source);
CREATE INDEX IF NOT EXISTS idx_meetings_parent_meeting_id ON meetings(parent_meeting_id);
CREATE INDEX IF NOT EXISTS idx_meetings_started_at ON meetings(started_at);

-- 2. Meeting Participants table (for detailed attendee tracking)
CREATE TABLE IF NOT EXISTS meeting_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Meeting association
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,

    -- Participant identification
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    contact_email VARCHAR(255),
    contact_name VARCHAR(255),
    contact_role VARCHAR(100),

    -- Participant details
    participant_type VARCHAR(50) DEFAULT 'prospect' CHECK (participant_type IN ('prospect', 'internal', 'stakeholder', 'decision_maker', 'influencer')),
    is_primary BOOLEAN DEFAULT FALSE,
    is_host BOOLEAN DEFAULT FALSE,

    -- Attendance tracking
    joined_at TIMESTAMPTZ,
    left_at TIMESTAMPTZ,
    attendance_duration_seconds INTEGER,
    attendance_status VARCHAR(50) DEFAULT 'invited' CHECK (attendance_status IN ('invited', 'confirmed', 'joined', 'left_early', 'completed', 'no_show')),

    -- Engagement metrics
    talk_time_percentage DECIMAL(5,3),
    questions_asked INTEGER DEFAULT 0,
    engagement_level VARCHAR(20) DEFAULT 'medium' CHECK (engagement_level IN ('low', 'medium', 'high')),
    sentiment_contribution DECIMAL(5,3) CHECK (sentiment_contribution >= -1 AND sentiment_contribution <= 1),

    -- Influence and decision making
    decision_influence VARCHAR(20) DEFAULT 'unknown' CHECK (decision_influence IN ('unknown', 'low', 'medium', 'high', 'primary')),
    budget_authority BOOLEAN DEFAULT FALSE,
    technical_authority BOOLEAN DEFAULT FALSE,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT meeting_participants_time_check CHECK (left_at IS NULL OR left_at >= joined_at),
    CONSTRAINT meeting_participants_unique_meeting_email UNIQUE(meeting_id, contact_email)
);

-- 3. Fathom Integration tables
CREATE TABLE IF NOT EXISTS fathom_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Integration settings
    workspace_name VARCHAR(255) NOT NULL,
    workspace_id VARCHAR(255) NOT NULL,
    api_key_encrypted TEXT, -- Encrypted API key
    webhook_secret_encrypted TEXT, -- Encrypted webhook secret
    is_active BOOLEAN DEFAULT TRUE,

    -- Configuration
    auto_download_recordings BOOLEAN DEFAULT TRUE,
    auto_request_transcripts BOOLEAN DEFAULT TRUE,
    storage_location VARCHAR(500),
    recording_format VARCHAR(20) DEFAULT 'mp4' CHECK (recording_format IN ('mp4', 'webm', 'avi')),

    -- Processing settings
    processing_priority VARCHAR(20) DEFAULT 'normal' CHECK (processing_priority IN ('low', 'normal', 'high', 'critical')),
    retain_original_recording BOOLEAN DEFAULT TRUE,
    archive_after_days INTEGER DEFAULT 365,

    -- Quality requirements
    min_audio_quality VARCHAR(20) DEFAULT 'standard' CHECK (min_audio_quality IN ('basic', 'standard', 'high')),
    require_human_transcript BOOLEAN DEFAULT FALSE,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.85,

    -- Usage tracking
    total_recordings_processed INTEGER DEFAULT 0,
    total_transcripts_generated INTEGER DEFAULT 0,
    storage_used_gb DECIMAL(10,2) DEFAULT 0,
    last_sync_at TIMESTAMPTZ,

    -- Health monitoring
    is_healthy BOOLEAN DEFAULT TRUE,
    last_health_check TIMESTAMPTZ DEFAULT NOW(),
    health_check_details JSONB DEFAULT '{}',

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT fathom_integrations_workspace_unique UNIQUE(workspace_id)
);

-- Fathom recordings table
CREATE TABLE IF NOT EXISTS fathom_recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Meeting association
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES fathom_integrations(id),

    -- Fathom identifiers
    fathom_id VARCHAR(255) NOT NULL UNIQUE,
    fathom_workspace_id VARCHAR(255) NOT NULL,
    share_url VARCHAR(500),

    -- Recording details
    recording_date TIMESTAMPTZ NOT NULL,
    recording_duration_seconds INTEGER,
    participant_count INTEGER DEFAULT 1,
    recording_device VARCHAR(100),

    -- File information
    file_path VARCHAR(1000),
    file_name VARCHAR(500),
    file_size_bytes BIGINT,
    file_format VARCHAR(20) DEFAULT 'mp4',
    file_hash VARCHAR(128),
    download_url VARCHAR(1000),

    -- Processing status
    download_status VARCHAR(50) DEFAULT 'pending' CHECK (download_status IN ('pending', 'downloading', 'completed', 'failed', 'archived')),
    download_started_at TIMESTAMPTZ,
    download_completed_at TIMESTAMPTZ,
    download_attempts INTEGER DEFAULT 0,

    -- Quality metrics
    audio_quality VARCHAR(20) DEFAULT 'unknown' CHECK (audio_quality IN ('poor', 'fair', 'good', 'excellent', 'unknown')),
    video_quality VARCHAR(20) DEFAULT 'unknown' CHECK (video_quality IN ('poor', 'fair', 'good', 'excellent', 'unknown', 'audio_only')),
    background_noise_level VARCHAR(20) DEFAULT 'unknown' CHECK (background_noise_level IN ('low', 'medium', 'high', 'unknown')),
    interruptions INTEGER DEFAULT 0,

    -- Integration metadata
    integration_metadata JSONB DEFAULT '{}',
    processing_metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT fathom_recordings_duration_positive CHECK (recording_duration_seconds > 0),
    CONSTRAINT fathom_recordings_file_size_positive CHECK (file_size_bytes > 0)
);

-- Fathom transcripts table
CREATE TABLE IF NOT EXISTS fathom_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Recording association
    recording_id UUID NOT NULL REFERENCES fathom_recordings(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,

    -- Fathom identifiers
    fathom_transcript_id VARCHAR(255) UNIQUE,

    -- Transcript content
    full_transcript TEXT,
    clean_transcript TEXT,
    summarized_transcript TEXT,

    -- Transcript metadata
    transcript_type VARCHAR(50) DEFAULT 'automated' CHECK (transcript_type IN ('automated', 'human', 'hybrid')),
    language VARCHAR(10) DEFAULT 'en-US',
    word_count INTEGER,
    speaker_count INTEGER DEFAULT 1,

    -- Quality metrics
    accuracy_score DECIMAL(3,2) CHECK (accuracy_score >= 0 AND accuracy_score <= 1),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    processing_time_seconds INTEGER,
    human_review_available BOOLEAN DEFAULT FALSE,
    human_review_requested BOOLEAN DEFAULT FALSE,

    -- Speaker identification
    speakers_identified BOOLEAN DEFAULT FALSE,
    speaker_labels JSONB DEFAULT '[]'::jsonb,
    speaker_confidence DECIMAL(3,2) CHECK (speaker_confidence >= 0 AND speaker_confidence <= 1),

    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed', 'enhanced')),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    last_enhanced_at TIMESTAMPTZ,

    -- Analysis data
    sentiment_analysis JSONB DEFAULT '{}',
    key_topics TEXT[] DEFAULT '{}',
    action_items_detected INTEGER DEFAULT 0,
    questions_asked INTEGER DEFAULT 0,
    mentions_competitors BOOLEAN DEFAULT FALSE,

    -- Custom vocabulary
    custom_vocabulary_used BOOLEAN DEFAULT FALSE,
    custom_vocabulary_terms TEXT[] DEFAULT '{}',

    -- Enhancement tracking
    enhancement_count INTEGER DEFAULT 0,
    last_enhancement_type VARCHAR(100),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT fathom_transcripts_word_count_positive CHECK (word_count > 0),
    CONSTRAINT fathom_transcripts_accuracy_valid CHECK (accuracy_score >= 0 AND accuracy_score <= 1)
);

-- 4. Meeting Notes Manager tables
CREATE TABLE IF NOT EXISTS meeting_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Meeting association
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    prospect_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    transcript_id UUID REFERENCES fathom_transcripts(id) ON DELETE SET NULL,

    -- Note details
    note_type VARCHAR(50) DEFAULT 'structured_summary' CHECK (note_type IN ('structured_summary', 'key_points', 'action_items', 'relationship_notes', 'follow_up')),
    author VARCHAR(100) DEFAULT 'system_generated',
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Structured content
    business_discussion JSONB DEFAULT '{}'::jsonb,
    technical_discussion JSONB DEFAULT '{}'::jsonb,
    relationship_indicators JSONB DEFAULT '{}'::jsonb,
    action_items_summary JSONB DEFAULT '[]'::jsonb,
    decisions_made JSONB DEFAULT '[]'::jsonb,
    concerns_raised JSONB DEFAULT '[]'::jsonb,
    commitments_offered JSONB DEFAULT '[]'::jsonb,

    -- Sentiment analysis
    overall_sentiment VARCHAR(50) CHECK (overall_sentiment IN ('positive', 'neutral', 'negative', 'mixed')),
    sentiment_score DECIMAL(5,3) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    emotional_indicators JSONB DEFAULT '{}'::jsonb,
    sentiment_trend VARCHAR(20) CHECK (sentiment_trend IN ('improving', 'stable', 'declining', 'unknown')),

    -- Relationship intelligence
    relationship_level VARCHAR(50) DEFAULT 'initial' CHECK (relationship_level IN ('initial', 'exploratory', 'qualified', 'trusted_advisor', 'partner')),
    trust_score DECIMAL(3,2) CHECK (trust_score >= 0 AND trust_score <= 10),
    urgency_level VARCHAR(20) DEFAULT 'medium' CHECK (urgency_level IN ('low', 'medium', 'high', 'critical')),
    buying_signals JSONB DEFAULT '[]'::jsonb,
    engagement_cues JSONB DEFAULT '[]'::jsonb,

    -- Tags and categorization
    tags TEXT[] DEFAULT '{}',
    categories TEXT[] DEFAULT '{}',
    importance_level VARCHAR(20) DEFAULT 'medium' CHECK (importance_level IN ('low', 'medium', 'high', 'critical')),

    -- CRM synchronization
    crm_sync_status VARCHAR(50) DEFAULT 'pending' CHECK (crm_sync_status IN ('pending', 'syncing', 'completed', 'failed')),
    crm_systems TEXT[] DEFAULT '{}',
    synced_at TIMESTAMPTZ,
    sync_errors JSONB DEFAULT '[]'::jsonb,
    record_updates JSONB DEFAULT '{}'::jsonb,

    -- Search optimization
    searchable_content TEXT,
    note_hash VARCHAR(128),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT meeting_notes_confidence_valid CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- 5. Task Automation tables
CREATE TABLE IF NOT EXISTS task_automation_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Source information
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    transcript_id UUID REFERENCES fathom_transcripts(id) ON DELETE SET NULL,
    extraction_source VARCHAR(50) DEFAULT 'fathom_transcript' CHECK (extraction_source IN ('fathom_transcript', 'meeting_notes', 'manual', 'crm')),
    extraction_confidence DECIMAL(3,2) CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),

    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed', 'partial')),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    processing_error TEXT,

    -- Action items extracted
    action_items JSONB DEFAULT '[]'::jsonb,
    total_tasks_extracted INTEGER DEFAULT 0,
    high_priority_tasks INTEGER DEFAULT 0,

    -- Platform distribution
    tasks_created_clickup INTEGER DEFAULT 0,
    tasks_created_todoist INTEGER DEFAULT 0,
    tasks_created_other INTEGER DEFAULT 0,

    -- Quality metrics
    extraction_accuracy_score DECIMAL(3,2),
    validation_status VARCHAR(50) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'needs_review', 'rejected')),
    validated_by VARCHAR(100),
    validated_at TIMESTAMPTZ,

    -- Analytics
    task_distribution JSONB DEFAULT '{}'::jsonb,
    average_confidence_score DECIMAL(3,2),
    processing_latency_seconds INTEGER,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS task_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Source task information
    source_meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    source_action_item_id VARCHAR(255),

    -- ClickUp integration
    clickup_task_id VARCHAR(255),
    clickup_space_id VARCHAR(255),
    clickup_list_id VARCHAR(255),
    clickup_status VARCHAR(100),
    clickup_url VARCHAR(500),
    clickup_created_at TIMESTAMPTZ,
    clickup_updated_at TIMESTAMPTZ,

    -- Todoist integration
    todoist_task_id VARCHAR(255),
    todoist_project_id VARCHAR(255),
    todoist_parent_task_id VARCHAR(255),
    todoist_status VARCHAR(100),
    todoist_url VARCHAR(500),
    todoist_created_at TIMESTAMPTZ,
    todoist_updated_at TIMESTAMPTZ,

    -- Synchronization status
    sync_status VARCHAR(50) DEFAULT 'created' CHECK (sync_status IN ('created', 'synced', 'conflict', 'failed')),
    last_sync_at TIMESTAMPTZ,
    sync_latency_seconds INTEGER,
    sync_errors JSONB DEFAULT '[]'::jsonb,

    -- Conflict resolution
    has_conflicts BOOLEAN DEFAULT FALSE,
    conflict_resolution VARCHAR(100),
    conflict_resolved_at TIMESTAMPTZ,
    manual_resolution_needed BOOLEAN DEFAULT FALSE,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT task_mappings_at_least_one_platform CHECK (
        clickup_task_id IS NOT NULL OR todoist_task_id IS NOT NULL
    )
);

-- 6. Sales Call Analytics tables
CREATE TABLE IF NOT EXISTS call_performance_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Call association
    call_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    transcript_id UUID REFERENCES fathom_transcripts(id) ON DELETE SET NULL,
    sales_rep_id VARCHAR(100),
    prospect_id UUID REFERENCES leads(id) ON DELETE CASCADE,

    -- Call context
    call_type VARCHAR(50) DEFAULT 'discovery' CHECK (call_type IN ('discovery', 'demo', 'proposal', 'negotiation', 'follow_up', 'check_in')),
    call_outcome VARCHAR(50) CHECK (call_outcome IN ('positive', 'negative', 'neutral', 'needs_follow_up')),
    analysis_confidence DECIMAL(3,2) CHECK (analysis_confidence >= 0 AND analysis_confidence <= 1),

    -- Performance scores
    overall_score DECIMAL(3,2) CHECK (overall_score >= 0 AND overall_score <= 10),
    opening_effectiveness JSONB DEFAULT '{}'::jsonb,
    discovery_quality JSONB DEFAULT '{}'::jsonb,
    presentation_clarity JSONB DEFAULT '{}'::jsonb,
    objection_handling JSONB DEFAULT '{}'::jsonb,
    closing_effectiveness JSONB DEFAULT '{}'::jsonb,

    -- Conversation metrics
    talk_time_analysis JSONB DEFAULT '{}'::jsonb,
    question_metrics JSONB DEFAULT '{}'::jsonb,
    engagement_indicators JSONB DEFAULT '{}'::jsonb,
    content_analysis JSONB DEFAULT '{}'::jsonb,

    -- Skill assessment
    communication_skills JSONB DEFAULT '{}'::jsonb,
    sales_techniques JSONB DEFAULT '{}'::jsonb,
    product_knowledge JSONB DEFAULT '{}'::jsonb,

    -- Comparative analysis
    team_ranking JSONB DEFAULT '{}'::jsonb,
    performance_vs_similar_calls JSONB DEFAULT '{}'::jsonb,
    performance_comparison VARCHAR(50) DEFAULT 'unknown' CHECK (performance_comparison IN ('above_average', 'average', 'below_average', 'excellent', 'needs_improvement', 'unknown')),

    -- Improvement recommendations
    improvement_recommendations JSONB DEFAULT '[]'::jsonb,
    best_practice_identified JSONB DEFAULT '{}'::jsonb,
    coaching_summary JSONB DEFAULT '{}'::jsonb,

    -- Development tracking
    skill_improvement_areas JSONB DEFAULT '[]'::jsonb,
    strengths_to_reinforce JSONB DEFAULT '[]'::jsonb,
    priority_improvements JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT call_performance_analytics_overall_score_valid CHECK (overall_score >= 0 AND overall_score <= 10),
    CONSTRAINT call_performance_analytics_confidence_valid CHECK (analysis_confidence >= 0 AND analysis_confidence <= 1)
);

CREATE TABLE IF NOT EXISTS call_script_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Template information
    template_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) DEFAULT 'discovery' CHECK (template_type IN ('discovery', 'demo', 'proposal', 'negotiation', 'follow_up')),
    industry VARCHAR(100),
    company_size VARCHAR(50),
    persona VARCHAR(100),

    -- Script content
    opening_section JSONB DEFAULT '{}'::jsonb,
    discovery_section JSONB DEFAULT '{}'::jsonb,
    presentation_section JSONB DEFAULT '{}'::jsonb,
    objection_section JSONB DEFAULT '{}'::jsonb,
    closing_section JSONB DEFAULT '{}'::jsonb,

    -- Performance metrics
    success_rate DECIMAL(5,3) CHECK (success_rate >= 0 AND success_rate <= 1),
    usage_count INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,3) CHECK (conversion_rate >= 0 AND conversion_rate <= 1),
    average_engagement_score DECIMAL(3,2) CHECK (average_engagement_score >= 0 AND average_engagement_score <= 10),

    -- Optimization data
    last_optimized_at TIMESTAMPTZ,
    optimization_version INTEGER DEFAULT 1,
    ab_test_results JSONB DEFAULT '{}'::jsonb,
    feedback_score DECIMAL(3,2) CHECK (feedback_score >= 0 AND feedback_score <= 10),

    -- Effectiveness tracking
    prospect_industries TEXT[] DEFAULT '{}',
    successful_cases JSONB DEFAULT '[]'::jsonb,
    failure_patterns JSONB DEFAULT '[]'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_approved BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT call_script_templates_unique_name UNIQUE(template_name, template_type, industry, company_size),
    CONSTRAINT call_script_templates_success_rate_valid CHECK (success_rate >= 0 AND success_rate <= 1),
    CONSTRAINT call_script_templates_conversion_rate_valid CHECK (conversion_rate >= 0 AND conversion_rate <= 1)
);

-- 7. Enhanced Meeting Prep tables
CREATE TABLE IF NOT EXISTS meeting_prep_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Meeting association
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    prospect_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    sales_rep_id VARCHAR(100),

    -- Package details
    prep_type VARCHAR(50) DEFAULT 'discovery_call' CHECK (prep_type IN ('discovery_call', 'demo', 'proposal', 'negotiation', 'follow_up')),
    prep_confidence DECIMAL(3,2) CHECK (prep_confidence >= 0 AND prep_confidence <= 1),

    -- Research insights
    research_insights JSONB DEFAULT '{}'::jsonb,
    lead_summary JSONB DEFAULT '{}'::jsonb,
    company_summary JSONB DEFAULT '{}'::jsonb,
    contextual_factors JSONB DEFAULT '{}'::jsonb,

    -- Learning integration
    learning_integration JSONB DEFAULT '{}'::jsonb,
    similar_successful_calls JSONB DEFAULT '[]'::jsonb,
    effective_opening_techniques JSONB DEFAULT '[]'::jsonb,
    proven_value_propositions JSONB DEFAULT '[]'::jsonb,

    -- Optimized script
    optimized_script JSONB DEFAULT '{}'::jsonb,
    key_talking_points JSONB DEFAULT '[]'::jsonb,
    high_impact_questions JSONB DEFAULT '[]'::jsonb,
    objection_preparation JSONB DEFAULT '{}'::jsonb,

    -- Presentation materials
    presentation_materials JSONB DEFAULT '{}'::jsonb,
    supporting_materials JSONB DEFAULT '[]'::jsonb,
    gamma_deck_id VARCHAR(255),
    slides_created INTEGER DEFAULT 0,
    customization_level VARCHAR(50) DEFAULT 'medium' CHECK (customization_level IN ('low', 'medium', 'high')),

    -- Delivery tracking
    delivery_method VARCHAR(50) DEFAULT 'email' CHECK (delivery_method IN ('email', 'slack', 'portal', 'sms')),
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    materials_used JSONB DEFAULT '[]'::jsonb,

    -- Feedback and effectiveness
    feedback_collected BOOLEAN DEFAULT FALSE,
    feedback_rating INTEGER CHECK (feedback_rating >= 1 AND feedback_rating <= 5),
    effectiveness_score DECIMAL(3,2) CHECK (effectiveness_score >= 0 AND effectiveness_score <= 10),
    prep_usage_analytics JSONB DEFAULT '{}'::jsonb,

    -- Learning contribution
    learning_contribution JSONB DEFAULT '{}'::jsonb,
    script_sections_used JSONB DEFAULT '[]'::jsonb,
    talking_points_effectiveness JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT meeting_prep_packages_confidence_valid CHECK (prep_confidence >= 0 AND prep_confidence <= 1),
    CONSTRAINT meeting_prep_packages_effectiveness_valid CHECK (effectiveness_score >= 0 AND effectiveness_score <= 10)
);

-- 8. Analytics and tracking tables
CREATE TABLE IF NOT EXISTS meeting_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Analytics period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    period_type VARCHAR(20) DEFAULT 'day' CHECK (period_type IN ('hour', 'day', 'week', 'month', 'quarter')),

    -- Meeting metrics
    total_meetings INTEGER DEFAULT 0,
    completed_meetings INTEGER DEFAULT 0,
    cancelled_meetings INTEGER DEFAULT 0,
    no_show_meetings INTEGER DEFAULT 0,

    -- Performance metrics
    average_meeting_duration DECIMAL(8,2),
    average_engagement_score DECIMAL(3,2),
    average_conversion_probability DECIMAL(5,3),
    show_rate DECIMAL(5,3),

    -- By meeting type
    meeting_type_breakdown JSONB DEFAULT '{}'::jsonb,

    -- Source analytics
    meeting_source_breakdown JSONB DEFAULT '{}'::jsonb,

    -- Quality metrics
    prep_effectiveness_average DECIMAL(3,2),
    transcript_quality_average DECIMAL(3,2),
    follow_up_completion_rate DECIMAL(5,3),

    -- Business impact
    total_pipeline_generated DECIMAL(15,2),
    total_deals_closed INTEGER DEFAULT 0,
    total_revenue_impact DECIMAL(15,2),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT meeting_analytics_period_check CHECK (period_end > period_start),
    CONSTRAINT meeting_analytics_unique_period UNIQUE(period_start, period_end, period_type)
);

-- 9. Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting_id ON meeting_participants(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_lead_id ON meeting_participants(lead_id);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_email ON meeting_participants(contact_email);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_role ON meeting_participants(contact_role);

CREATE INDEX IF NOT EXISTS idx_fathom_recordings_meeting_id ON fathom_recordings(meeting_id);
CREATE INDEX IF NOT EXISTS idx_fathom_recordings_fathom_id ON fathom_recordings(fathom_id);
CREATE INDEX IF NOT EXISTS idx_fathom_recordings_download_status ON fathom_recordings(download_status);
CREATE INDEX IF NOT EXISTS idx_fathom_recordings_recording_date ON fathom_recordings(recording_date);

CREATE INDEX IF NOT EXISTS idx_fathom_transcripts_recording_id ON fathom_transcripts(recording_id);
CREATE INDEX IF NOT EXISTS idx_fathom_transcripts_meeting_id ON fathom_transcripts(meeting_id);
CREATE INDEX IF NOT EXISTS idx_fathom_transcripts_processing_status ON fathom_transcripts(processing_status);
CREATE INDEX IF NOT EXISTS idx_fathom_transcripts_accuracy_score ON fathom_transcripts(accuracy_score);

CREATE INDEX IF NOT EXISTS idx_meeting_notes_meeting_id ON meeting_notes(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_notes_prospect_id ON meeting_notes(prospect_id);
CREATE INDEX IF NOT EXISTS idx_meeting_notes_note_type ON meeting_notes(note_type);
CREATE INDEX IF NOT EXISTS idx_meeting_notes_relationship_level ON meeting_notes(relationship_level);
CREATE INDEX IF NOT EXISTS idx_meeting_notes_sentiment_score ON meeting_notes(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_meeting_notes_crm_sync_status ON meeting_notes(crm_sync_status);

CREATE INDEX IF NOT EXISTS idx_task_automation_queue_meeting_id ON task_automation_queue(meeting_id);
CREATE INDEX IF NOT EXISTS idx_task_automation_queue_processing_status ON task_automation_queue(processing_status);
CREATE INDEX IF NOT EXISTS idx_task_automation_queue_extraction_source ON task_automation_queue(extraction_source);

CREATE INDEX IF NOT EXISTS idx_task_mappings_source_meeting ON task_mappings(source_meeting_id);
CREATE INDEX IF NOT EXISTS idx_task_mappings_clickup_task ON task_mappings(clickup_task_id);
CREATE INDEX IF NOT EXISTS idx_task_mappings_todoist_task ON task_mappings(todoist_task_id);
CREATE INDEX IF NOT EXISTS idx_task_mappings_sync_status ON task_mappings(sync_status);

CREATE INDEX IF NOT EXISTS idx_call_performance_analytics_call_id ON call_performance_analytics(call_id);
CREATE INDEX IF NOT EXISTS idx_call_performance_analytics_sales_rep ON call_performance_analytics(sales_rep_id);
CREATE INDEX IF NOT EXISTS idx_call_performance_analytics_call_type ON call_performance_analytics(call_type);
CREATE INDEX IF NOT EXISTS idx_call_performance_analytics_overall_score ON call_performance_analytics(overall_score);

CREATE INDEX IF NOT EXISTS idx_call_script_templates_type ON call_script_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_call_script_templates_industry ON call_script_templates(industry);
CREATE INDEX IF NOT EXISTS idx_call_script_templates_success_rate ON call_script_templates(success_rate);

CREATE INDEX IF NOT EXISTS idx_meeting_prep_packages_meeting_id ON meeting_prep_packages(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_prep_packages_prospect_id ON meeting_prep_packages(prospect_id);
CREATE INDEX IF NOT EXISTS idx_meeting_prep_packages_prep_type ON meeting_prep_packages(prep_type);
CREATE INDEX IF NOT EXISTS idx_meeting_prep_packages_effectiveness ON meeting_prep_packages(effectiveness_score);

-- 10. Add helpful functions
CREATE OR REPLACE FUNCTION update_meeting_engagement_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update meeting metrics when participants are added
    UPDATE meetings
    SET
        engagement_score = COALESCE(
            (SELECT AVG(engagement_level_score)
             FROM (
                 SELECT CASE
                     WHEN engagement_level = 'low' THEN 3
                     WHEN engagement_level = 'medium' THEN 6
                     WHEN engagement_level = 'high' THEN 9
                     ELSE 5
                 END as engagement_level_score
                 FROM meeting_participants
                 WHERE meeting_id = NEW.meeting_id
                 AND attendance_status = 'completed'
             ) scores),
            5
        ),
        actual_duration_minutes = CASE
            WHEN (SELECT MAX(EXTRACT(EPOCH FROM (left_at - joined_at))/60)
                 FROM meeting_participants
                 WHERE meeting_id = NEW.meeting_id
                 AND left_at IS NOT NULL
                 AND joined_at IS NOT NULL) > 0
            THEN (SELECT MAX(EXTRACT(EPOCH FROM (left_at - joined_at))/60)
                 FROM meeting_participants
                 WHERE meeting_id = NEW.meeting_id
                 AND left_at IS NOT NULL
                 AND joined_at IS NOT NULL)
            ELSE actual_duration_minutes
        END
    WHERE id = NEW.meeting_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update meeting metrics when participants change
DROP TRIGGER IF EXISTS trigger_update_meeting_engagement ON meeting_participants;
CREATE TRIGGER trigger_update_meeting_engagement
    AFTER INSERT OR UPDATE ON meeting_participants
    FOR EACH ROW
    EXECUTE FUNCTION update_meeting_engagement_metrics();

-- 11. Add comments for documentation
COMMENT ON TABLE meeting_participants IS 'Detailed tracking of all meeting attendees with engagement metrics and influence assessment';
COMMENT ON TABLE fathom_integrations IS 'Configuration and health monitoring for Fathom recording integrations';
COMMENT ON TABLE fathom_recordings IS 'Individual recording instances from Fathom with download and quality tracking';
COMMENT ON TABLE fathom_transcripts IS 'Transcript data with speaker identification, quality metrics, and analysis';
COMMENT ON TABLE meeting_notes IS 'Structured meeting notes with sentiment analysis and relationship intelligence';
COMMENT ON TABLE task_automation_queue IS 'Queue for processing action items from meetings into task systems';
COMMENT ON TABLE task_mappings IS 'Cross-platform task mappings between ClickUp, Todoist, and other systems';
COMMENT ON TABLE call_performance_analytics IS 'Detailed sales call performance analysis with comparative metrics';
COMMENT ON TABLE call_script_templates IS 'AI-optimized call scripts with performance tracking and A/B testing';
COMMENT ON TABLE meeting_prep_packages IS 'AI-generated meeting preparation packages with learning integration';
COMMENT ON TABLE meeting_analytics IS 'Aggregated meeting analytics for performance monitoring and business intelligence';
