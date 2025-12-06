#!/usr/bin/env python3
"""
Create learning and improvement system tables for agents
This includes knowledge base, response tracking, FAQ, and agent learning tables
"""

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def create_learning_system_tables():
    """Create all learning system tables"""

    # Database connection
    db_url = (
        "postgresql://postgres:%s@db.xhuhyoqztrkwbazxvotp.supabase.co:5432/postgres"
        % quote_plus("Salsal$TITI$@1990")
    )

    engine = create_engine(db_url)

    print("Creating Learning & Improvement System Tables...")

    with engine.connect() as conn:
        # 1. Knowledge Base Table
        print("\n1. Creating knowledge_base table...")
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                created_by VARCHAR(100), -- agent or user who created it

                -- Content
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                content_type VARCHAR(50) DEFAULT 'text', -- text, markdown, html, code

                -- Categorization
                category VARCHAR(100),
                subcategory VARCHAR(100),
                tags TEXT[] DEFAULT '{}',

                -- Usage & Effectiveness
                usage_count INTEGER DEFAULT 0,
                success_rate DECIMAL(5,2), -- Percentage of successful uses
                last_used_at TIMESTAMPTZ,
                effectiveness_score DECIMAL(3,2) DEFAULT 0, -- 0-10 rating

                -- Context & Scope
                industry VARCHAR(100),
                company_size VARCHAR(50),
                persona VARCHAR(100), -- target persona for this knowledge
                use_cases TEXT[] DEFAULT '{}',

                -- Validation
                verified BOOLEAN DEFAULT FALSE,
                verified_by VARCHAR(100),
                verified_at TIMESTAMPTZ,
                confidence_score DECIMAL(3,2) DEFAULT 0, -- AI confidence in accuracy

                -- Relationships
                parent_id UUID REFERENCES knowledge_base(id), -- for knowledge hierarchies
                related_ids UUID[] DEFAULT '{}',
                sources TEXT[] DEFAULT '{}', -- source URLs or references

                -- Metadata
                metadata JSONB DEFAULT '{}',
                -- embedding_vector VECTOR(1536), -- For semantic search (requires pgvector extension)
                search_keywords TEXT[] DEFAULT '{}',

                -- Status
                status VARCHAR(50) DEFAULT 'active' CHECK (
                    status IN ('active', 'archived', 'draft', 'deprecated')
                )
            )
        """)
        )
        conn.commit()
        print("   ✅ knowledge_base created")

        # 2. Response Tracking Table
        print("\n2. Creating response_tracking table...")
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS response_tracking (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),

                -- Response Details
                message_id UUID REFERENCES messages(id),
                campaign_id UUID REFERENCES campaigns(id),
                lead_id UUID REFERENCES leads(id),

                -- Agent Information
                agent_name VARCHAR(100) NOT NULL,
                agent_version VARCHAR(50),
                agent_type VARCHAR(100), -- copywriter, researcher, scheduler etc.

                -- Original Response
                original_content TEXT NOT NULL,
                original_subject VARCHAR(500),
                generated_at TIMESTAMPTZ,
                generation_time_ms INTEGER,
                prompt_used TEXT,

                -- Human Corrections
                corrected_content TEXT,
                corrected_subject VARCHAR(500),
                corrected_by VARCHAR(100),
                corrected_at TIMESTAMPTZ,
                correction_reason TEXT,

                -- Performance Metrics
                opened BOOLEAN DEFAULT FALSE,
                opened_at TIMESTAMPTZ,
                clicked BOOLEAN DEFAULT FALSE,
                clicked_at TIMESTAMPTZ,
                replied BOOLEAN DEFAULT FALSE,
                replied_at TIMESTAMPTZ,
                replied_content TEXT,

                -- Sentiment Analysis
                sentiment VARCHAR(50), -- positive, negative, neutral
                sentiment_score DECIMAL(3,2), -- -1 to 1
                sentiment_analyzed_at TIMESTAMPTZ,

                -- Learning Data
                success_score DECIMAL(3,2) DEFAULT 0, -- 0-10 based on outcomes
                key_factors JSONB DEFAULT '{}', -- What made it successful/not
                lessons_learned TEXT,

                -- A/B Testing
                ab_test_group VARCHAR(10), -- A, B, control
                ab_test_id UUID,
                is_winner BOOLEAN,

                -- Metadata
                metadata JSONB DEFAULT '{}',
                tags TEXT[] DEFAULT '{}',

                -- Status
                status VARCHAR(50) DEFAULT 'sent' CHECK (
                    status IN ('draft', 'sent', 'corrected', 'analyzed', 'archived')
                )
            )
        """)
        )
        conn.commit()
        print("   ✅ response_tracking created")

        # 3. FAQ Management Table
        print("\n3. Creating faq_management table...")
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS faq_management (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                created_by VARCHAR(100),

                -- Question & Answer
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                question_type VARCHAR(50), -- product, pricing, technical, general

                -- Categorization
                category VARCHAR(100),
                subcategory VARCHAR(100),
                priority INTEGER DEFAULT 0, -- 0-10, higher = more important
                tags TEXT[] DEFAULT '{}',

                -- Usage Statistics
                view_count INTEGER DEFAULT 0,
                helpful_count INTEGER DEFAULT 0,
                not_helpful_count INTEGER DEFAULT 0,
                last_viewed_at TIMESTAMPTZ,

                -- Context
                applies_to VARCHAR(100)[], -- which agents/roles this applies to
                industry VARCHAR(100),
                company_stage VARCHAR(50), -- startup, growth, enterprise

                -- Effectiveness
                success_rate DECIMAL(5,2), -- helpful / total views
                avg_rating DECIMAL(3,2), -- if users can rate
                feedback_count INTEGER DEFAULT 0,

                -- Related Information
                related_faqs UUID[] DEFAULT '{}',
                related_kb_articles UUID[] DEFAULT '{}', -- References to knowledge_base.id (enforced at application level)

                -- AI Enhancement
                suggested_improvements TEXT,
                auto_generated BOOLEAN DEFAULT FALSE,
                confidence_score DECIMAL(3,2) DEFAULT 0,

                -- Metadata
                metadata JSONB DEFAULT '{}',
                search_keywords TEXT[] DEFAULT '{}',

                -- Status
                status VARCHAR(50) DEFAULT 'active' CHECK (
                    status IN ('active', 'draft', 'archived', 'needs_review')
                )
            )
        """)
        )
        conn.commit()
        print("   ✅ faq_management created")

        # 4. Agent Learning & Corrections Table
        print("\n4. Creating agent_learning table...")
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS agent_learning (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),

                -- Agent Information
                agent_name VARCHAR(100) NOT NULL,
                agent_type VARCHAR(100),
                agent_version VARCHAR(50),

                -- Learning Event
                event_type VARCHAR(100) NOT NULL, -- mistake, correction, improvement, insight
                event_category VARCHAR(100), -- copywriting, timing, targeting, personalization

                -- Original Action (What went wrong/right)
                original_action TEXT,
                original_context JSONB DEFAULT '{}',
                original_parameters JSONB DEFAULT '{}',
                original_outcome JSONB DEFAULT '{}',

                -- Correction/Improvement
                corrected_action TEXT,
                correction_reason TEXT,
                correction_source VARCHAR(100), -- human_feedback, auto_analysis, pattern_recognition

                -- Learning Details
                lesson_learned TEXT NOT NULL,
                confidence_level DECIMAL(3,2) DEFAULT 0, -- How confident are we in this learning
                applicability_score DECIMAL(3,2) DEFAULT 0, -- How broadly applicable
                impact_potential DECIMAL(3,2) DEFAULT 0, -- Potential impact on performance

                -- Pattern Recognition
                pattern_detected BOOLEAN DEFAULT FALSE,
                pattern_description TEXT,
                similar_cases UUID[] DEFAULT '{}', -- References to similar learning events

                -- Implementation
                implemented_at TIMESTAMPTZ,
                implementation_method VARCHAR(100), -- prompt_update, rule_change, model_fine_tune
                implementation_status VARCHAR(50) DEFAULT 'pending',

                -- Validation
                validated BOOLEAN DEFAULT FALSE,
                validation_method VARCHAR(100), -- a_b_test, performance_metrics, human_review
                validation_results JSONB DEFAULT '{}',
                validated_at TIMESTAMPTZ,
                validated_by VARCHAR(100),

                -- Performance Impact
                baseline_performance DECIMAL(5,2),
                improved_performance DECIMAL(5,2),
                performance_change DECIMAL(5,2), -- percentage change
                measurement_period VARCHAR(50), -- 1_week, 1_month, etc.

                -- Knowledge Integration
                kb_article_id UUID REFERENCES knowledge_base(id),
                rule_created BOOLEAN DEFAULT FALSE,
                rule_description TEXT,

                -- Metadata
                metadata JSONB DEFAULT '{}',
                tags TEXT[] DEFAULT '{}',
                sources TEXT[] DEFAULT '{}',

                -- Status
                status VARCHAR(50) DEFAULT 'new' CHECK (
                    status IN ('new', 'learning', 'implementing', 'validated', 'integrated', 'rejected')
                )
            )
        """)
        )
        conn.commit()
        print("   ✅ agent_learning created")

        # 5. Agent Performance Analytics Table
        print("\n5. Creating agent_performance_analytics table...")
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS agent_performance_analytics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),

                -- Agent Information
                agent_name VARCHAR(100) NOT NULL,
                agent_type VARCHAR(100),
                agent_version VARCHAR(50),

                -- Time Period
                period_start TIMESTAMPTZ NOT NULL,
                period_end TIMESTAMPTZ NOT NULL,
                period_type VARCHAR(20) DEFAULT 'day', -- hour, day, week, month

                -- Key Metrics
                total_tasks INTEGER DEFAULT 0,
                successful_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                success_rate DECIMAL(5,2),

                -- Performance Metrics
                avg_response_time_ms INTEGER,
                avg_task_completion_time_ms INTEGER,
                accuracy_score DECIMAL(5,2), -- 0-100%
                quality_score DECIMAL(5,2), -- Human-rated quality

                -- Learning Metrics
                corrections_count INTEGER DEFAULT 0,
                improvements_count INTEGER DEFAULT 0,
                new_insights_count INTEGER DEFAULT 0,
                learning_velocity DECIMAL(5,2), -- Rate of improvement

                -- Business Impact
                leads_generated INTEGER DEFAULT 0,
                meetings_booked INTEGER DEFAULT 0,
                conversion_rate DECIMAL(5,2),
                revenue_impact DECIMAL(12,2),

                -- Context
                campaigns_worked_on INTEGER DEFAULT 0,
                leads_handled INTEGER DEFAULT 0,
                messages_sent INTEGER DEFAULT 0,

                -- Detailed Breakdown
                performance_breakdown JSONB DEFAULT '{}', -- Detailed metrics by category
                error_breakdown JSONB DEFAULT '{}', -- Types of errors and frequencies
                success_factors JSONB DEFAULT '{}', -- What contributed to success

                -- Trends
                performance_trend VARCHAR(20), -- improving, stable, declining
                trend_strength DECIMAL(3,2), -- How strong is the trend

                -- Metadata
                metadata JSONB DEFAULT '{}',
                notes TEXT,

                -- Status
                status VARCHAR(50) DEFAULT 'calculated'
            )
        """)
        )
        conn.commit()
        print("   ✅ agent_performance_analytics created")

        # 6. Correction Approval Workflow Table
        print("\n6. Creating correction_approval_workflow table...")
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS correction_approval_workflow (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),

                -- Reference to learning/correction
                agent_learning_id UUID REFERENCES agent_learning(id),
                response_tracking_id UUID REFERENCES response_tracking(id),

                -- Correction Details
                correction_type VARCHAR(100), -- content_edit, parameter_adjustment, rule_change
                proposed_correction TEXT NOT NULL,
                original_value TEXT,
                reasoning TEXT NOT NULL,

                -- Workflow
                status VARCHAR(50) DEFAULT 'pending' CHECK (
                    status IN ('pending', 'under_review', 'approved', 'rejected', 'implemented')
                ),
                priority INTEGER DEFAULT 0, -- 0-10

                -- Approval Process
                requested_by VARCHAR(100),
                reviewed_by VARCHAR(100),
                approved_by VARCHAR(100),

                review_date TIMESTAMPTZ,
                approval_date TIMESTAMPTZ,
                implementation_date TIMESTAMPTZ,

                -- Review Details
                review_notes TEXT,
                approval_conditions TEXT,
                rejection_reason TEXT,

                -- Impact Assessment
                estimated_impact VARCHAR(50), -- low, medium, high, critical
                impact_description TEXT,
                risk_level VARCHAR(50), -- low, medium, high

                -- Auto-Approval Logic
                auto_approve BOOLEAN DEFAULT FALSE,
                auto_approve_conditions JSONB DEFAULT '{}',
                confidence_threshold DECIMAL(3,2) DEFAULT 0.8,

                -- Implementation
                implemented BOOLEAN DEFAULT FALSE,
                implementation_details JSONB DEFAULT '{}',
                rollback_available BOOLEAN DEFAULT FALSE,
                rollback_procedure TEXT,

                -- Results
                post_implementation_metrics JSONB DEFAULT '{}',
                success_criteria TEXT,
                actual_impact JSONB DEFAULT '{}',

                -- Metadata
                metadata JSONB DEFAULT '{}',
                tags TEXT[] DEFAULT '{}',

                -- Status History
                status_history JSONB DEFAULT '[]' -- Array of status changes with timestamps
            )
        """)
        )
        conn.commit()
        print("   ✅ correction_approval_workflow created")

        # Create indexes for performance
        print("\nCreating indexes...")
        indexes = [
            # Knowledge Base indexes
            "CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category, subcategory)",
            "CREATE INDEX IF NOT EXISTS idx_kb_tags ON knowledge_base USING GIN(tags)",
            "CREATE INDEX IF NOT EXISTS idx_kb_effectiveness ON knowledge_base(effectiveness_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_kb_usage ON knowledge_base(usage_count DESC)",
            # Response Tracking indexes
            "CREATE INDEX IF NOT EXISTS idx_rt_agent ON response_tracking(agent_name, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_rt_campaign ON response_tracking(campaign_id, success_score)",
            "CREATE INDEX IF NOT EXISTS idx_rt_ab_test ON response_tracking(ab_test_id, is_winner)",
            "CREATE INDEX IF NOT EXISTS idx_rt_performance ON response_tracking(success_score DESC)",
            # FAQ Management indexes
            "CREATE INDEX IF NOT EXISTS idx_faq_category ON faq_management(category, subcategory)",
            "CREATE INDEX IF NOT EXISTS idx_faq_priority ON faq_management(priority DESC)",
            "CREATE INDEX IF NOT EXISTS idx_faq_success ON faq_management(success_rate DESC)",
            "CREATE INDEX IF NOT EXISTS idx_faq_tags ON faq_management USING GIN(tags)",
            # Agent Learning indexes
            "CREATE INDEX IF NOT EXISTS idx_al_agent ON agent_learning(agent_name, event_type)",
            "CREATE INDEX IF NOT EXISTS idx_al_status ON agent_learning(status, confidence_level)",
            "CREATE INDEX IF NOT EXISTS idx_al_pattern ON agent_learning(pattern_detected, applicability_score)",
            "CREATE INDEX IF NOT EXISTS idx_al_impact ON agent_learning(impact_potential DESC)",
            # Agent Performance Analytics indexes
            "CREATE INDEX IF NOT EXISTS idx_apa_agent_period ON agent_performance_analytics(agent_name, period_start)",
            "CREATE INDEX IF NOT EXISTS idx_apa_success ON agent_performance_analytics(success_rate DESC)",
            "CREATE INDEX IF NOT EXISTS idx_apa_trend ON agent_performance_analytics(performance_trend, trend_strength)",
            # Correction Workflow indexes
            "CREATE INDEX IF NOT EXISTS idx_caw_status ON correction_approval_workflow(status, priority DESC)",
            "CREATE INDEX IF NOT EXISTS idx_caw_type ON correction_approval_workflow(correction_type, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_caw_agent ON correction_approval_workflow(agent_learning_id)",
        ]

        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"   ⚠ Index warning: {e}")
                conn.rollback()

        print("\n✅ All Learning & Improvement System tables created successfully!")
        print("\nTables created:")
        print("  • knowledge_base - Central repository of agent knowledge")
        print("  • response_tracking - Track every response and its outcomes")
        print("  • faq_management - Dynamic FAQ system with usage tracking")
        print("  • agent_learning - Agent mistakes, corrections, and improvements")
        print("  • agent_performance_analytics - Performance metrics over time")
        print("  • correction_approval_workflow - Workflow for approving corrections")


if __name__ == "__main__":
    create_learning_system_tables()
