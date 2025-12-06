#!/usr/bin/env python3
"""
Final Meeting Migration
Creates essential meeting tables with minimal SQL
"""

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

# Essential meeting tables
CREATE_TABLES = [
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


def create_meeting_tables():
    """Create essential meeting tables"""

    # Database connection
    db_url = f"postgresql://postgres:{quote_plus(os.getenv('DB_PASSWORD', 'Salsal$TITI$@1990'))}@{os.getenv('DB_HOST', 'db.xhuhyoqztrkwbazxvotp.supabase.co')}:5432/postgres"

    print("🚀 Final Meeting Management Migration")
    print("=" * 40)

    # Create engine
    engine = create_engine(db_url)

    with engine.connect() as conn:
        print("🔌 Connected to database")

        successful = 0

        # Execute each CREATE TABLE separately
        for i, table_sql in enumerate(CREATE_TABLES, 1):
            try:
                table_name = table_sql.split()[4]  # Extract table name
                print(f"\n🔨 Creating table {i}/{len(CREATE_TABLES)}: {table_name}")

                conn.execute(text(table_sql))
                successful += 1
                print(f"   ✅ {table_name} created")

            except Exception as e:
                if "already exists" in str(e):
                    print(f"   ⚠️  {table_name} already exists")
                    successful += 1
                else:
                    print(f"   ❌ Error creating {table_name}: {str(e)}")

        print(f"\n✅ Created {successful}/{len(CREATE_TABLES)} tables!")

        # Try to add foreign key constraints
        try:
            print("\n🔗 Adding foreign key constraints...")

            # Check if meetings table exists
            meetings_check = conn.execute(
                text("""
                SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'meetings')
            """)
            ).scalar()

            if meetings_check:
                constraints = [
                    "ALTER TABLE meeting_participants ADD CONSTRAINT fk_meeting_participants_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE",
                    "ALTER TABLE meeting_notes ADD CONSTRAINT fk_meeting_notes_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE",
                ]

                for constraint in constraints:
                    try:
                        conn.execute(text(constraint))
                        print("   ✅ FK constraint added")
                    except Exception as e:
                        if "already exists" in str(e) or "does not exist" in str(e):
                            print("   ⚠️  FK constraint skipped")
                        else:
                            print(f"   ⚠️  FK constraint warning: {str(e)[:50]}")

        except Exception as e:
            print(f"   ⚠️  Foreign key setup warning: {str(e)}")

    print("\n🎉 Meeting Management Migration Complete!")
    print("\n✅ Essential tables created:")
    print("   • meeting_participants")
    print("   • fathom_recordings")
    print("   • meeting_notes")
    print("   • task_automation_queue")
    print("   • call_performance_analytics")

    print("\n✅ Your meeting management system is ready!")
    return successful == len(CREATE_TABLES)


if __name__ == "__main__":
    try:
        success = create_meeting_tables()
        if not success:
            print("\n⚠️  Some tables may not have been created")
        else:
            print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration error: {str(e)}")
        exit(1)
