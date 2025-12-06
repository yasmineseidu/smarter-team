-- Migration 003: Communication Tables
-- Creates conversation and message tracking
-- Dependencies: 001_core_tables, 002_lead_entities

-- Conversations table (depends on leads and campaigns)
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

-- Messages table (depends on conversations, leads, campaigns)
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
    personalization_line_id UUID, -- Will reference personalization_lines table later
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

-- Indexes for conversations
CREATE INDEX idx_conversations_lead ON conversations(lead_id);
CREATE INDEX idx_conversations_campaign ON conversations(campaign_id) WHERE campaign_id IS NOT NULL;
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
CREATE INDEX idx_conversations_needs_review ON conversations(needs_review) WHERE needs_review = TRUE;
CREATE INDEX idx_conversations_active ON conversations(status, last_message_at DESC) WHERE status = 'active';
CREATE INDEX idx_conversations_thread_id ON conversations(thread_id) WHERE thread_id IS NOT NULL;

-- Indexes for messages
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_lead ON messages(lead_id);
CREATE INDEX idx_messages_created ON messages(created_at DESC);
CREATE INDEX idx_messages_status ON messages(status) WHERE status IN ('pending_approval', 'approved');
CREATE INDEX idx_messages_approval ON messages(tier, status) WHERE tier = 'approval';
CREATE INDEX idx_messages_external_id ON messages(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX idx_messages_sent ON messages(sent_at) WHERE sent_at IS NOT NULL;
CREATE INDEX idx_messages_direction ON messages(direction, created_at);

-- Composite indexes for common queries
CREATE INDEX idx_messages_conversation_sent ON messages(conversation_id, sent_at DESC);
CREATE INDEX idx_messages_lead_status ON messages(lead_id, status);

-- Comments for documentation
COMMENT ON TABLE conversations IS 'Thread-based communication tracking';
COMMENT ON TABLE messages IS 'Individual message tracking within conversations';

-- Record migration
INSERT INTO schema_migrations (version, applied_at) VALUES ('003_communication_tables', NOW());
