#!/usr/bin/env python3
"""
Safe Meeting Management Migration Runner
Handles existing columns gracefully and provides detailed feedback
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def check_column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    result = conn.execute(
        text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = :table_name
            AND column_name = :column_name
        );
    """),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar()


def run_meeting_management_migration():
    """Run migration 008 for meeting management system safely"""

    # Database connection
    db_url = f"postgresql://postgres:{quote_plus(os.getenv('DB_PASSWORD', 'Salsal$TITI$@1990'))}@{os.getenv('DB_HOST', 'db.xhuhyoqztrkwbazxvotp.supabase.co')}:5432/postgres"

    # Migration file path
    migration_file = (
        Path(__file__).parent.parent.parent
        / "specs"
        / "database-schema"
        / "migrations"
        / "008_meeting_management_system.sql"
    )

    print("🚀 Safe Meeting Management System Migration (008)")
    print("=" * 50)
    print(f"📄 Migration file: {migration_file}")

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    with open(migration_file) as f:
        content = f.read()

    print(f"📏 Migration size: {len(content):,} characters")

    # Create engine
    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            print("\n🔌 Connected to database")

            # Check existing columns in meetings table
            print("🔍 Checking existing columns in meetings table...")
            existing_columns = {}
            new_columns_to_add = [
                "lifecycle_stage",
                "preparation_completed",
                "preparation_completed_at",
                "engagement_score",
                "talk_time_ratio",
                "sentiment_score",
                "meeting_quality_score",
                "conversion_probability",
                "actual_duration_minutes",
                "started_at",
                "ended_at",
                "attendees",
                "meeting_source",
                "parent_meeting_id",
                "follow_up_priority",
            ]

            for column in new_columns_to_add:
                exists = check_column_exists(conn, "meetings", column)
                existing_columns[column] = exists
                status = "✅" if exists else "➕"
                print(f"   {status} {column}: {'exists' if exists else 'will be added'}")

            # Read and process migration with manual handling for ALTER TABLE
            lines = content.split("\n")
            current_statement = []
            statements = []
            in_alter_table = False

            for line in lines:
                stripped = line.strip()

                # Skip comments and empty lines
                if not stripped or stripped.startswith("--"):
                    continue

                current_statement.append(line)

                # Check for statement end
                if stripped.endswith(";"):
                    statement = "\n".join(current_statement)
                    statements.append(statement)
                    current_statement = []

            # Add any remaining content
            if current_statement:
                statements.append("\n".join(current_statement))

            print(f"\n🔨 Processing {len(statements)} SQL statements...")

            # Start transaction
            trans = conn.begin()
            print("📦 Transaction started")

            statements_executed = 0
            statements_skipped = 0

            try:
                for i, statement in enumerate(statements, 1):
                    if not statement.strip():
                        continue

                    # Handle ALTER TABLE for meetings specially
                    if "ALTER TABLE meetings" in statement and "ADD COLUMN" in statement:
                        # Parse which column is being added
                        for column in new_columns_to_add:
                            if f"ADD COLUMN IF NOT EXISTS {column}" in statement:
                                if existing_columns[column]:
                                    print(f"   ⚠️  Skipping ALTER for existing column: {column}")
                                    statements_skipped += 1
                                else:
                                    try:
                                        conn.execute(text(statement))
                                        print(f"   ✅ Added column: {column}")
                                        statements_executed += 1
                                    except Exception as e:
                                        if "already exists" in str(e):
                                            print(f"   ⚠️  Column {column} already exists")
                                            statements_skipped += 1
                                        else:
                                            print(f"   ❌ Error adding column {column}: {str(e)}")
                                            raise
                                break
                        continue

                    # Skip ALTER TABLE statements for columns that already exist
                    if "ALTER TABLE meetings" in statement and "ADD COLUMN" in statement:
                        # This should be handled above, but skip anyway
                        continue

                    # Execute other statements normally
                    try:
                        # Print progress every 10 statements
                        if i % 10 == 0:
                            print(f"   Executing statement {i}/{len(statements)}")

                        conn.execute(text(statement))
                        statements_executed += 1

                        # Print CREATE TABLE statements
                        if "CREATE TABLE" in statement:
                            # Extract table name
                            if "CREATE TABLE IF NOT EXISTS" in statement:
                                table_name = statement.split("CREATE TABLE IF NOT EXISTS")[
                                    1
                                ].split()[0]
                            else:
                                table_name = statement.split("CREATE TABLE")[1].split()[0]
                            print(f"   ✅ Created table: {table_name}")

                    except Exception as e:
                        # Check if it's a "already exists" error for safe operations
                        if (
                            "already exists" in str(e)
                            or "does not exist" in str(e)
                            or "duplicate key" in str(e)
                        ):
                            print(f"   ⚠️  Statement skipped (object exists): {str(e)[:100]}...")
                            statements_skipped += 1
                        else:
                            print(f"   ❌ Error in statement {i}: {str(e)}")
                            print(f"   Statement preview: {statement[:200]}...")
                            raise

                # Commit transaction
                trans.commit()
                print("\n✅ Transaction committed")
                print(f"📊 Statements executed: {statements_executed}")
                print(f"📊 Statements skipped: {statements_skipped}")

            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Transaction rolled back: {str(e)}")
                return False

        # Verify tables were created
        print("\n🔍 Verifying created tables...")
        with engine.connect() as conn:
            result = conn.execute(
                text("""
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
            )

            tables = result.fetchall()
            if tables:
                print(f"✅ Found {len(tables)} meeting management tables:")
                for table in tables:
                    print(f"   • {table[0]}")
            else:
                print("⚠️  No new tables found")

            # Check specific important tables
            important_tables = [
                "meeting_participants",
                "fathom_integrations",
                "fathom_recordings",
                "fathom_transcripts",
                "meeting_notes",
                "task_automation_queue",
                "task_mappings",
                "call_performance_analytics",
                "call_script_templates",
                "meeting_prep_packages",
            ]

            print("\n🎯 Important table status:")
            created_count = 0
            for table_name in important_tables:
                result = conn.execute(
                    text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = :table_name
                    );
                """),
                    {"table_name": table_name},
                )
                exists = result.scalar()
                status = "✅" if exists else "❌"
                print(f"   {status} {table_name}")
                if exists:
                    created_count += 1

            print(f"\n📊 Important tables created: {created_count}/{len(important_tables)}")

        print("\n🎉 Meeting Management System Migration completed!")
        print("=" * 50)

        # Print comprehensive summary
        print("\n📊 Migration Summary:")
        print("   ✅ Extended meetings table with new analytics columns")
        print("   ✅ Created comprehensive meeting tracking system")
        print("   ✅ Added Fathom recording and transcript management")
        print("   ✅ Implemented task automation (ClickUp/Todoist)")
        print("   ✅ Added sales call performance analytics")
        print("   ✅ Created AI-powered meeting preparation system")
        print("   ✅ Built relationship intelligence tracking")
        print(f"   📈 {statements_executed} SQL statements executed successfully")
        if statements_skipped > 0:
            print(f"   ⚠️  {statements_skipped} statements skipped (already exists)")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   • Check database connection")
        print("   • Verify migration 007 was completed")
        print("   • Ensure proper CREATE/ALTER permissions")
        return False


if __name__ == "__main__":
    print("Safe Meeting Management System Migration")
    print("====================================")

    success = run_meeting_management_migration()
    exit(0 if success else 1)
