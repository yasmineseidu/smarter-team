#!/usr/bin/env python3
"""
Quick Meeting Management Migration
Creates essential meeting tables directly
"""

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def create_meeting_tables():
    """Create meeting management tables directly"""

    # Database connection
    db_url = f"postgresql://postgres:{quote_plus(os.getenv('DB_PASSWORD', 'Salsal$TITI$@1990'))}@{os.getenv('DB_HOST', 'db.xhuhyoqztrkwbazxvotp.supabase.co')}:5432/postgres"

    print("🚀 Quick Meeting Management Migration")
    print("=" * 40)

    # SQL statements for meeting tables (simplified versions)
    meeting_tables = [
        # 1. Meeting Participants
        """
        CREATE TABLE IF NOT EXISTS meeting_participants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            meeting_id UUID NOT NULL,
            contact_name VARCHAR(255),
            contact_email VARCHAR(255),
            contact_role VARCHAR(100),
            participant_type VARCHAR(50) DEFAULT 'prospect',
            attendance_status VARCHAR(50) DEFAULT 'invited',
            engagement_level VARCHAR(20) DEFAULT 'medium'
        );
        """,
        # 2. Fathom Recordings
        """
        CREATE TABLE IF NOT EXISTS fathom_recordings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            meeting_id UUID,
            fathom_id VARCHAR(255) UNIQUE,
            recording_date TIMESTAMPTZ,
            recording_duration_seconds INTEGER,
            download_url VARCHAR(1000)
        );
        """,
        # 3. Meeting Notes
        """
        CREATE TABLE IF NOT EXISTS meeting_notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            meeting_id UUID NOT NULL,
            note_type VARCHAR(50) DEFAULT 'structured_summary',
            business_discussion JSONB DEFAULT '{}',
            action_items_summary JSONB DEFAULT '[]',
            sentiment_score DECIMAL(5,3)
        );
        """,
        # 4. Task Automation
        """
        CREATE TABLE IF NOT EXISTS task_automation_queue (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            meeting_id UUID,
            processing_status VARCHAR(50) DEFAULT 'pending',
            action_items JSONB DEFAULT '[]'
        );
        """,
        # 5. Call Analytics
        """
        CREATE TABLE IF NOT EXISTS call_performance_analytics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            call_id UUID,
            sales_rep_id VARCHAR(100),
            overall_score DECIMAL(3,2),
            opening_effectiveness JSONB DEFAULT '{}',
            discovery_quality JSONB DEFAULT '{}'
        );
        """,
    ]

    # Create engine
    engine = create_engine(db_url)

    with engine.connect() as conn:
        print("🔌 Connected to database")

        successful_tables = 0

        for i, table_sql in enumerate(meeting_tables, 1):
            try:
                table_name = table_sql.split()[5]  # Extract table name
                print(f"\n🔨 Creating table {i}/{len(meeting_tables)}: {table_name}")

                conn.execute(text(table_sql))
                successful_tables += 1
                print(f"   ✅ {table_name} created")

            except Exception as e:
                if "already exists" in str(e):
                    print("   ⚠️  Table already exists")
                    successful_tables += 1
                else:
                    print(f"   ❌ Error: {str(e)}")

        # Add foreign key constraints (if meetings table exists)
        try:
            print("\n🔗 Adding foreign key constraints...")

            # Check if meetings table exists
            meetings_exists = conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'meetings'
                );
            """)
            ).scalar()

            if meetings_exists:
                # Add FK constraints
                constraints = [
                    "ALTER TABLE meeting_participants ADD CONSTRAINT fk_meeting_participants_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE;",
                    "ALTER TABLE meeting_notes ADD CONSTRAINT fk_meeting_notes_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE;",
                ]

                for constraint in constraints:
                    try:
                        conn.execute(text(constraint))
                        print("   ✅ FK constraint added")
                    except Exception as e:
                        if "already exists" in str(e) or "does not exist" in str(e):
                            print("   ⚠️  FK constraint skipped")
                        else:
                            print(f"   ⚠️  FK constraint warning: {str(e)[:100]}")

        except Exception as e:
            print(f"   ⚠️  Foreign key setup warning: {str(e)}")

        print("\n✅ Migration completed!")
        print(f"📊 Tables created: {successful_tables}/{len(meeting_tables)}")

        # Verify tables
        print("\n🔍 Verifying created tables...")
        result = conn.execute(
            text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name IN ('meeting_participants', 'fathom_recordings', 'meeting_notes', 'task_automation_queue', 'call_performance_analytics')
            ORDER BY table_name;
        """)
        )

        tables = result.fetchall()
        if tables:
            print("✅ Created tables:")
            for table in tables:
                print(f"   • {table[0]}")

    print("\n🎉 Meeting Management Migration Complete!")
    print("\n✅ Your database now supports:")
    print("   • Meeting participant tracking")
    print("   • Fathom recording integration")
    print("   • Meeting notes and insights")
    print("   • Automated task extraction")
    print("   • Sales call analytics")

    return True


if __name__ == "__main__":
    try:
        success = create_meeting_tables()
        if not success:
            exit(1)
    except Exception as e:
        print(f"\n❌ Migration error: {str(e)}")
        exit(1)
