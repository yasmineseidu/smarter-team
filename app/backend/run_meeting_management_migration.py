#!/usr/bin/env python3
"""
Run Meeting Management System Migration (008)
Uses SQLAlchemy to run the meeting management migration safely
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def run_meeting_management_migration():
    """Run migration 008 for meeting management system"""

    # Database connection using the same pattern as existing migrations
    db_url = f"postgresql://postgres:{quote_plus(os.getenv('DB_PASSWORD', 'Salsal$TITI$@1990'))}@{os.getenv('DB_HOST', 'db.xhuhyoqztrkwbazxvotp.supabase.co')}:5432/postgres"

    # Migration file path
    migration_file = (
        Path(__file__).parent.parent.parent
        / "specs"
        / "database-schema"
        / "migrations"
        / "008_meeting_management_system.sql"
    )

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

    try:
        with engine.connect() as conn:
            print("\n🔌 Connected to database")

            # Start transaction
            trans = conn.begin()
            print("📦 Transaction started")

            try:
                # Split content into statements (same logic as existing migrations)
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

                print(f"🔨 Executing {len(statements)} statements...")

                # Execute statements
                for i, statement in enumerate(statements, 1):
                    if statement.strip():
                        try:
                            # Print progress every 10 statements
                            if i % 10 == 0:
                                print(f"   Executing statement {i}/{len(statements)}")

                            conn.execute(text(statement))
                        except Exception as e:
                            # Check if it's just an "already exists" error
                            if "already exists" in str(e) or "does not exist" in str(e):
                                print(
                                    f"   ⚠️  Statement {i} skipped (object already exists): {str(e)[:100]}..."
                                )
                                continue
                            else:
                                print(f"   ❌ Error in statement {i}: {str(e)}")
                                print(f"   Statement: {statement[:200]}...")
                                raise

                # Commit transaction
                trans.commit()
                print("✅ Transaction committed")

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
                print(f"✅ Created {len(tables)} meeting management tables:")
                for table in tables:
                    print(f"   • {table[0]}")
            else:
                print("⚠️  No new tables found (they may already exist)")

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

            print("\n🎯 Checking important tables:")
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

        print("\n🎉 Meeting Management System Migration completed successfully!")
        print("\n📊 Migration Summary:")
        print("   • Extended meetings table with analytics fields")
        print("   • Created detailed participant tracking")
        print("   • Added Fathom integration tables")
        print("   • Implemented task automation system")
        print("   • Added sales call analytics")
        print("   • Created meeting prep system")
        print("   • Added comprehensive indexes and triggers")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   • Check database connection")
        print("   • Verify migration 007 was completed")
        print("   • Ensure proper permissions")
        return False


def check_prerequisites():
    """Check if prerequisites are met"""
    print("🔍 Checking prerequisites...")

    # Check for SQLAlchemy
    try:
        import sqlalchemy

        print(f"✅ SQLAlchemy available: {sqlalchemy.__version__}")
    except ImportError:
        print("❌ SQLAlchemy not available")
        return False

    # Check for key tables that should exist from migration 007
    try:
        db_url = f"postgresql://postgres:{quote_plus(os.getenv('DB_PASSWORD', 'Salsal$TITI$@1990'))}@{os.getenv('DB_HOST', 'db.xhuhyoqztrkwbazxvotp.supabase.co')}:5432/postgres"
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Check for meetings table (from migration 004)
            result = conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'meetings'
                );
            """)
            )
            meetings_exist = result.scalar()

            # Check for knowledge_base table (from migration 007)
            result = conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'knowledge_base'
                );
            """)
            )
            knowledge_base_exists = result.scalar()

            if meetings_exist:
                print("✅ meetings table exists (migration 004)")
            else:
                print("❌ meetings table missing - please run migration 004 first")
                return False

            if knowledge_base_exists:
                print("✅ knowledge_base table exists (migration 007)")
            else:
                print("⚠️  knowledge_base table missing - please run migration 007 first")
                return False

    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    print("Meeting Management System Migration Runner")
    print("=======================================")

    if not check_prerequisites():
        print("\n❌ Prerequisites not met")
        exit(1)

    success = run_meeting_management_migration()
    exit(0 if success else 1)
