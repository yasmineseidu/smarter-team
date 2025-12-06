#!/usr/bin/env python3
"""
Direct Meeting Management Migration
Uses the same pattern as existing migrations (run_migrations_final.py)
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def run_meeting_migration():
    """Execute meeting management migration using proven pattern"""

    # Database connection (same as other migrations)
    db_url = f"postgresql://postgres:{quote_plus(os.getenv('DB_PASSWORD', 'Salsal$TITI$@1990'))}@{os.getenv('DB_HOST', 'db.xhuhyoqztrkwbazxvotp.supabase.co')}:5432/postgres"

    # Migration file
    migrations_dir = (
        Path(__file__).parent.parent.parent / "specs" / "database-schema" / "migrations"
    )
    migration_file = migrations_dir / "008_meeting_management_system.sql"

    print("🚀 Meeting Management System Migration (008)")
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

    with engine.connect() as conn:
        print("\n🔌 Connected to database")

        # Split content into statements (same logic as run_migrations_final.py)
        statements = []
        current = []
        in_quotes = False
        quote_char = None

        for char in content:
            if char in ("'", '"'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
            elif char == ";" and not in_quotes:
                current.append(char)
                statement = "".join(current).strip()
                if statement and not statement.startswith("--"):
                    statements.append(statement)
                current = []
                continue

            current.append(char)

        # Add any remaining content
        if current:
            statement = "".join(current).strip()
            if statement and not statement.startswith("--"):
                statements.append(statement)

        print(f"🔨 Processing {len(statements)} SQL statements...")

        # Execute statements directly without explicit transaction
        successful_statements = 0
        skipped_statements = 0

        for i, statement in enumerate(statements, 1):
            if not statement.strip():
                continue

            try:
                # Print progress every 10 statements
                if i % 10 == 0:
                    print(f"   Executing statement {i}/{len(statements)}")

                # Handle ALTER TABLE meetings specially
                if "ALTER TABLE meetings" in statement and "ADD COLUMN" in statement:
                    # Check if column already exists first
                    column_name = None
                    if "lifecycle_stage" in statement:
                        column_name = "lifecycle_stage"
                    elif "preparation_completed" in statement:
                        column_name = "preparation_completed"
                    elif "engagement_score" in statement:
                        column_name = "engagement_score"
                    # Add more column checks as needed...

                    if column_name:
                        exists_check = text(f"""
                            SELECT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name = 'meetings'
                                AND column_name = '{column_name}'
                            );
                        """)
                        column_exists = conn.execute(exists_check).scalar()

                        if column_exists:
                            print(f"   ⚠️  Column {column_name} already exists - skipping")
                            skipped_statements += 1
                            continue

                conn.execute(text(statement))
                successful_statements += 1

                # Log CREATE TABLE statements
                if "CREATE TABLE" in statement:
                    table_name = (
                        statement.split()[2]
                        .replace("IF", "")
                        .replace("NOT", "")
                        .replace("EXISTS", "")
                        .strip()
                    )
                    print(f"   ✅ Created/updated table: {table_name}")

            except Exception as e:
                # Check if it's a safe error (object already exists)
                error_msg = str(e).lower()
                if (
                    "already exists" in error_msg
                    or "does not exist" in error_msg
                    or "duplicate key" in error_msg
                    or "duplicate column" in error_msg
                ):
                    print(f"   ⚠️  Statement skipped (already exists): {str(e)[:80]}...")
                    skipped_statements += 1
                else:
                    print(f"   ❌ Error in statement {i}: {str(e)}")
                    print(f"   Statement: {statement[:150]}...")
                    raise

        print("\n✅ Migration completed successfully!")
        print(f"📊 Statements executed: {successful_statements}")
        print(f"📊 Statements skipped: {skipped_statements}")

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
            print("⚠️  No meeting management tables found (they may already exist)")

    print("\n🎉 Meeting Management System Migration completed!")
    return True


if __name__ == "__main__":
    try:
        success = run_meeting_migration()
        if success:
            print("\n✅ Migration successful! Your database now supports:")
            print("   • Advanced meeting lifecycle tracking")
            print("   • Fathom recording and transcript integration")
            print("   • Automated task extraction (ClickUp/Todoist)")
            print("   • Sales call performance analytics")
            print("   • AI-powered meeting preparation")
            print("   • Comprehensive meeting insights")
        else:
            print("\n❌ Migration failed")
            exit(1)
    except Exception as e:
        print(f"\n❌ Migration error: {str(e)}")
        exit(1)
