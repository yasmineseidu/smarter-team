#!/usr/bin/env python3
"""
Create tables with proper transaction handling
"""

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def create_tables():
    """Create all required tables"""

    # Database connection
    db_url = (
        "postgresql://postgres:%s@db.xhuhyoqztrkwbazxvotp.supabase.co:5432/postgres"
        % quote_plus("Salsal$TITI$@1990")
    )

    engine = create_engine(db_url)

    print("Creating database tables...")

    with engine.connect() as conn:
        # Enable UUID extension
        try:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            conn.commit()
            print("✅ UUID extension enabled")
        except Exception as e:
            print(f"  Warning: {e}")
            conn.rollback()

        # Create ENUM types
        enums = [
            "CREATE TYPE campaign_status AS ENUM ('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED')",
            "CREATE TYPE conversation_status AS ENUM ('active', 'resolved', 'pending_human', 'escalated')",
            "CREATE TYPE message_direction AS ENUM ('inbound', 'outbound')",
            "CREATE TYPE communication_channel AS ENUM ('email', 'linkedin', 'sms', 'call')",
            "CREATE TYPE message_status AS ENUM ('draft', 'pending_approval', 'approved', 'rejected', 'sent', 'delivered', 'bounced', 'failed')",
            "CREATE TYPE approval_tier AS ENUM ('auto_send', 'approval', 'escalation')",
            "CREATE TYPE message_type AS ENUM ('initial', 'follow_up', 'reply', 'check_in', 'notification', 'personalization')",
            "CREATE TYPE meeting_status AS ENUM ('scheduled', 'completed', 'no_show', 'cancelled', 'rescheduled')",
            "CREATE TYPE meeting_type AS ENUM ('discovery', 'demo', 'closing', 'follow_up', 'check_in')",
            "CREATE TYPE meeting_outcome AS ENUM ('positive', 'negative', 'follow_up_needed', 'no_decision')",
            "CREATE TYPE proposal_status AS ENUM ('draft', 'sent', 'viewed', 'negotiating', 'signed', 'expired', 'rejected', 'withdrawn')",
            "CREATE TYPE contract_type AS ENUM ('one_time', 'retainer', 'milestone', 'subscription')",
            "CREATE TYPE client_status AS ENUM ('onboarding', 'active', 'at_risk', 'paused', 'churned', 'completed')",
        ]

        print("\nCreating ENUM types...")
        for enum_sql in enums:
            try:
                conn.execute(text(enum_sql))
                conn.commit()
                print(f"✅ {enum_sql.split('AS ENUM')[0].strip()}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"✅ {enum_sql.split('AS ENUM')[0].strip()} (already exists)")
                else:
                    print(f"❌ Error: {e}")
                    conn.rollback()

        # Core tables
        tables = [
            # Companies table
            """
            CREATE TABLE IF NOT EXISTS companies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                name VARCHAR(255) NOT NULL,
                domain VARCHAR(255) UNIQUE,
                website VARCHAR(500),
                linkedin_url VARCHAR(500),
                industry VARCHAR(100),
                employee_count VARCHAR(50),
                revenue_range VARCHAR(50),
                founded_year INTEGER,
                headquarters_city VARCHAR(100),
                headquarters_country VARCHAR(2),
                description TEXT,
                last_researched_at TIMESTAMPTZ,
                technology_stack TEXT[],
                company_size VARCHAR(50),
                business_model VARCHAR(100),
                target_market VARCHAR(255),
                competitors TEXT[],
                funding_stage VARCHAR(50),
                total_funding DECIMAL(15,2),
                annual_revenue DECIMAL(15,2),
                growth_rate DECIMAL(5,2),
                notes TEXT,
                is_active BOOLEAN DEFAULT true,
                data_source VARCHAR(50) DEFAULT 'manual',
                raw_data JSONB,
                custom_fields JSONB DEFAULT '{}',
                tags TEXT[] DEFAULT '{}'
            )
            """,
            # Campaigns table
            """
            CREATE TABLE IF NOT EXISTS campaigns (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                status campaign_status DEFAULT 'DRAFT',
                instantly_campaign_id VARCHAR(100) UNIQUE,
                instantly_account_id VARCHAR(100),
                daily_send_limit INTEGER DEFAULT 50,
                sending_schedule JSONB DEFAULT '{}',
                warmup_enabled BOOLEAN DEFAULT false,
                warmup_settings JSONB DEFAULT '{}',
                email_sequence JSONB NOT NULL DEFAULT '[]',
                sequence_length INTEGER DEFAULT 3,
                ab_test_enabled BOOLEAN DEFAULT false,
                ab_test_config JSONB DEFAULT '{}',
                ab_test_winner_confidence DECIMAL(3,2) DEFAULT 0.95,
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
                bounce_rate DECIMAL(5,2) DEFAULT 0,
                unsubscribe_rate DECIMAL(5,2) DEFAULT 0,
                spam_complaint_rate DECIMAL(5,2) DEFAULT 0,
                open_rate DECIMAL(5,2) GENERATED ALWAYS AS (
                    CASE WHEN emails_sent > 0 THEN ROUND((opens::DECIMAL / emails_sent) * 100, 2) ELSE 0 END
                ) STORED,
                reply_rate DECIMAL(5,2) GENERATED ALWAYS AS (
                    CASE WHEN emails_sent > 0 THEN ROUND((replies::DECIMAL / emails_sent) * 100, 2) ELSE 0 END
                ) STORED,
                meeting_rate DECIMAL(5,2) GENERATED ALWAYS AS (
                    CASE WHEN emails_sent > 0 THEN ROUND((meetings_booked::DECIMAL / emails_sent) * 100, 2) ELSE 0 END
                ) STORED,
                launched_at TIMESTAMPTZ,
                paused_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                tags TEXT[] DEFAULT '{}',
                custom_fields JSONB DEFAULT '{}'
            )
            """,
            # Leads table
            """
            CREATE TABLE IF NOT EXISTS leads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(255) UNIQUE,
                email_normalized VARCHAR(255) UNIQUE,
                phone VARCHAR(50),
                linkedin_url VARCHAR(500),
                title VARCHAR(255),
                seniority_level VARCHAR(50),
                department VARCHAR(100),
                company_id UUID REFERENCES companies(id),
                company_name VARCHAR(255),
                industry VARCHAR(100),
                company_size VARCHAR(50),
                location_city VARCHAR(100),
                location_state VARCHAR(100),
                location_country VARCHAR(2),
                timezone VARCHAR(50),
                lead_source VARCHAR(100),
                source_campaign_id UUID REFERENCES campaigns(id),
                source_specific VARCHAR(255),
                current_campaign_id UUID REFERENCES campaigns(id),
                status VARCHAR(50) DEFAULT 'new',
                sub_status VARCHAR(50),
                lead_score INTEGER DEFAULT 0,
                last_contacted_at TIMESTAMPTZ,
                next_follow_up_at TIMESTAMPTZ,
                do_not_contact BOOLEAN DEFAULT false,
                unsubscribed BOOLEAN DEFAULT false,
                unsubscribe_reason TEXT,
                bounce_count INTEGER DEFAULT 0,
                last_bounced_at TIMESTAMPTZ,
                email_validity VARCHAR(20) DEFAULT 'unknown',
            persona_tags TEXT[] DEFAULT '{}',
            technographics TEXT[],
            firmographics JSONB DEFAULT '{}',
            psychographics JSONB DEFAULT '{}',
            contact_history JSONB DEFAULT '[]',
            notes TEXT,
            is_active BOOLEAN DEFAULT true,
            data_quality_score DECIMAL(3,2) DEFAULT 1.0,
            enrichment_sources TEXT[] DEFAULT '{}',
            custom_fields JSONB DEFAULT '{}',
            tags TEXT[] DEFAULT '{}'
            )
            """,
            # Conversations table
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                lead_id UUID REFERENCES leads(id),
                campaign_id UUID REFERENCES campaigns(id),
                thread_id VARCHAR(255),
                platform VARCHAR(50),
                status conversation_status DEFAULT 'active',
                subject VARCHAR(500),
                summary TEXT,
                ai_assigned BOOLEAN DEFAULT false,
                needs_review BOOLEAN DEFAULT false,
                last_message_at TIMESTAMPTZ,
                message_count INTEGER DEFAULT 0,
                sentiment VARCHAR(50),
                intent_detected VARCHAR(100),
                next_action_required VARCHAR(100),
                metadata JSONB DEFAULT '{}'
            )
            """,
            # Messages table
            """
            CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                conversation_id UUID REFERENCES conversations(id),
                lead_id UUID REFERENCES leads(id),
                campaign_id UUID REFERENCES campaigns(id),
                parent_message_id UUID REFERENCES messages(id),
                external_id VARCHAR(255),
                direction message_direction NOT NULL,
                channel communication_channel DEFAULT 'email',
                message_type message_type DEFAULT 'reply',
                tier approval_tier DEFAULT 'auto_send',
                status message_status DEFAULT 'draft',
                subject VARCHAR(500),
                content TEXT NOT NULL,
                html_content TEXT,
                from_email VARCHAR(255),
                from_name VARCHAR(255),
                to_emails TEXT[] NOT NULL,
                cc_emails TEXT[] DEFAULT '{}',
                bcc_emails TEXT[] DEFAULT '{}',
                attachments JSONB DEFAULT '[]',
                personalization_data JSONB DEFAULT '{}',
            ab_test_variant VARCHAR(10),
            send_after INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            retry_count INTEGER DEFAULT 0,
            scheduled_at TIMESTAMPTZ,
            sent_at TIMESTAMPTZ,
            delivered_at TIMESTAMPTZ,
            opened_at TIMESTAMPTZ,
            clicked_at TIMESTAMPTZ,
            replied_at TIMESTAMPTZ,
            bounced_at TIMESTAMPTZ,
            bounce_reason TEXT,
            unsubscribe_at TIMESTAMPTZ,
            ai_generated BOOLEAN DEFAULT false,
            ai_confidence DECIMAL(3,2),
            human_reviewed BOOLEAN DEFAULT false,
            reviewed_by VARCHAR(100),
            review_notes TEXT,
            metadata JSONB DEFAULT '{}',
            external_metadata JSONB DEFAULT '{}'
            )
            """,
        ]

        print("\nCreating tables...")
        for table_sql in tables:
            try:
                conn.execute(text(table_sql))
                conn.commit()
                # Extract table name from SQL
                table_name = table_sql.split("CREATE TABLE IF NOT EXISTS ")[1].split(" ")[0].strip()
                print(f"✅ {table_name}")
            except Exception as e:
                print(f"❌ Error creating table: {e}")
                conn.rollback()

        print("\n✅ Database tables creation completed!")


if __name__ == "__main__":
    create_tables()
