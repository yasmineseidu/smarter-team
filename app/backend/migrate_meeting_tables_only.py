#!/usr/bin/env python3
"""
Migrate Meeting Tables Only
Creates new meeting management tables without altering existing ones
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def extract_new_tables():
    """Extract only CREATE TABLE statements for new tables"""
    migration_file = (
        Path(__file__).parent.parent.parent
        / "specs"
        / "database-schema"
        / "migrations"
        / "008_meeting_management_system.sql"
    )

    with open(migration_file) as f:
        content = f.read()

    # Split content by CREATE TABLE statements
    statements = []
    current_statement = []
    capture = False

    for line in content.split("\n"):
        if line.strip().startswith("CREATE TABLE IF NOT EXISTS"):
            capture = True
            current_statement = []

        if capture:
            current_statement.append(line)

            # End statement when we reach semicolon
            if line.strip().endswith(";"):
                statements.append("\n".join(current_statement))
                capture = False
                current_statement = []

        # Skip other statements
        if not capture and not line.strip().startswith("CREATE TABLE IF NOT EXISTS"):
            if line.strip().startswith("--") or not line.strip():
                continue
            # Stop at CREATE INDEX section
            if "CREATE INDEX" in line:
                break

    return statements


def run_migration():
    """Run migration for new tables only"""

    # Database connection
    db_url = f"postgresql://postgres:{quote_plus(os.getenv('DB_PASSWORD', 'Salsal$TITI$@1990'))}@{os.getenv('DB_HOST', 'db.xhuhyoqztrkwbazxvotp.supabase.co')}:5432/postgres"

    print("🚀 Meeting Tables Migration")
    print("=" * 40)

    # Extract CREATE TABLE statements
    create_statements = extract_new_tables()

    if not create_statements:
        print("❌ No CREATE TABLE statements found")
        return False

    print(f"📋 Found {len(create_statements)} tables to create:")

    # List table names
    for stmt in create_statements:
        table_name = stmt.split()[
            4
        ]  # Extract table name from "CREATE TABLE IF NOT EXISTS table_name"
        print(f"   • {table_name}")

    # Create engine
    engine = create_engine(db_url)

    with engine.connect() as conn:
        print("\n🔌 Connected to database")

        # Execute each CREATE TABLE statement
        successful = 0
        for i, statement in enumerate(create_statements, 1):
            try:
                print(f"\n🔨 Creating table {i}/{len(create_statements)}...")
                conn.execute(text(statement))
                successful += 1
                print("   ✅ Success")

            except Exception as e:
                if "already exists" in str(e):
                    print("   ⚠️  Table already exists")
                else:
                    print(f"   ❌ Error: {str(e)}")
                    return False

        print(f"\n✅ Successfully created {successful} tables!")

        # Verify tables were created
        print("\n🔍 Verifying created tables...")
        verification_query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (
                table_name LIKE 'meeting_%' OR
                table_name LIKE 'fathom_%' OR
                table_name LIKE 'task_%' OR
                table_name LIKE 'call_%' OR
                table_name = 'meeting_analytics'
            )
            ORDER BY table_name;
        """)

        tables = conn.execute(verification_query).fetchall()

        if tables:
            print(f"✅ Found {len(tables)} meeting management tables:")
            for table in tables:
                print(f"   • {table[0]}")
        else:
            print("⚠️  No tables found")

        # Create indexes separately
        print("\n🔨 Creating indexes...")
        try:
            # Basic indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting_id ON meeting_participants(meeting_id);",
                "CREATE INDEX IF NOT EXISTS idx_fathom_recordings_meeting_id ON fathom_recordings(meeting_id);",
                "CREATE INDEX IF NOT EXISTS idx_fathom_transcripts_meeting_id ON fathom_transcripts(meeting_id);",
                "CREATE INDEX IF NOT EXISTS idx_meeting_notes_meeting_id ON meeting_notes(meeting_id);",
                "CREATE INDEX IF NOT EXISTS idx_task_automation_queue_meeting_id ON task_automation_queue(meeting_id);",
                "CREATE INDEX IF NOT EXISTS idx_call_performance_analytics_call_id ON call_performance_analytics(call_id);",
                "CREATE INDEX IF NOT EXISTS idx_meeting_prep_packages_meeting_id ON meeting_prep_packages(meeting_id);",
            ]

            for index in indexes:
                try:
                    conn.execute(text(index))
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"   ⚠️  Index creation warning: {str(e)[:100]}")

            print("   ✅ Indexes created")

        except Exception as e:
            print(f"   ⚠️  Index creation warnings: {str(e)}")

    print("\n🎉 Migration completed successfully!")
    print("\n✅ Your database now has:")
    print("   • Meeting participants tracking")
    print("   • Fathom recording management")
    print("   • Transcript processing")
    print("   • Meeting notes system")
    print("   • Task automation")
    print("   • Sales call analytics")
    print("   • Meeting preparation")

    return True


if __name__ == "__main__":
    try:
        success = run_migration()
        if not success:
            print("\n❌ Migration failed")
            exit(1)
    except Exception as e:
        print(f"\n❌ Migration error: {str(e)}")
        exit(1)
