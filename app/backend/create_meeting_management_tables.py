#!/usr/bin/env python3
"""
Create Meeting Management System Tables
Runs migration 008 to create comprehensive meeting management system
"""

import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)


async def create_meeting_management_tables():
    """Execute the meeting management system migration"""
    print("🚀 Starting Meeting Management System Migration (008)")
    print("=" * 60)

    # Parse database URL
    parsed_url = urlparse(DATABASE_URL)
    db_config = {
        "host": parsed_url.hostname,
        "port": parsed_url.port or 5432,
        "user": parsed_url.username,
        "password": parsed_url.password,
        "database": parsed_url.lstrip("/") or "postgres",
    }

    # Read the migration file
    migration_path = Path("specs/database-schema/migrations/008_meeting_management_system.sql")
    if not migration_path.exists():
        print(f"❌ ERROR: Migration file not found: {migration_path}")
        sys.exit(1)

    with open(migration_path) as f:
        migration_sql = f.read()

    print(f"📄 Migration file loaded: {migration_path}")
    print(f"📏 Migration size: {len(migration_sql):,} characters")

    try:
        # Connect to database
        print("\n🔌 Connecting to PostgreSQL...")
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected successfully")

        # Start transaction
        print("\n📦 Starting transaction...")
        async with conn.transaction():
            # Check if migration was already run
            check_sql = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'meeting_participants'
                );
            """
            tables_exist = await conn.fetchval(check_sql)

            if tables_exist:
                print("⚠️  Meeting management tables already exist")
                response = input("Do you want to continue anyway? (y/N): ").strip().lower()
                if response != "y":
                    print("❌ Migration cancelled")
                    return

            print("🔨 Executing migration...")

            # Execute migration in chunks
            statements = migration_sql.split(";")
            statements = [
                s.strip() for s in statements if s.strip() and not s.strip().startswith("--")
            ]

            for i, statement in enumerate(statements, 1):
                if statement:
                    try:
                        await conn.execute(statement)
                        if i % 10 == 0:
                            print(f"   Executed {i}/{len(statements)} statements...")
                    except Exception as e:
                        print(f"❌ Error executing statement {i}: {str(e)}")
                        print(f"Statement: {statement[:200]}...")
                        raise

            print(f"✅ Migration completed: {len(statements)} statements executed")

        # Verify tables were created
        print("\n🔍 Verifying table creation...")
        verification_query = """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'current_schema()'
            AND (
                table_name LIKE 'meeting_%' OR
                table_name LIKE 'fathom_%' OR
                table_name LIKE 'task_%' OR
                table_name LIKE 'call_%' OR
                table_name = 'meeting_analytics'
            )
            ORDER BY table_name;
        """

        created_tables = await conn.fetch(verification_query)

        if created_tables:
            print(f"✅ Found {len(created_tables)} meeting management tables:")
            for table in created_tables:
                print(f"   • {table['table_name']} ({table['table_type']})")
        else:
            print("⚠️  No meeting management tables found - this may indicate an issue")

        # Check indexes
        index_query = """
            SELECT indexname, tablename
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND (
                tablename LIKE 'meeting_%' OR
                tablename LIKE 'fathom_%' OR
                tablename LIKE 'task_%' OR
                tablename LIKE 'call_%' OR
                tablename = 'meeting_analytics'
            )
            ORDER BY tablename, indexname;
        """

        created_indexes = await conn.fetch(index_query)
        print(f"✅ Created {len(created_indexes)} indexes for meeting management tables")

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
            check_query = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = $1
                );
            """
            exists = await conn.fetchval(check_query, table_name)
            status = "✅" if exists else "❌"
            print(f"   {status} {table_name}")

        await conn.close()
        print("\n🎉 Meeting Management System Migration completed successfully!")
        print("=" * 60)

        # Print table summary
        print("\n📊 Created Tables Summary:")
        print("   • Meeting Extensions: Enhanced meetings table with analytics")
        print("   • meeting_participants: Detailed attendee tracking")
        print("   • Fathom Integration: fathom_integrations, fathom_recordings, fathom_transcripts")
        print("   • Notes Management: meeting_notes with relationship intelligence")
        print("   • Task Automation: task_automation_queue, task_mappings")
        print("   • Call Analytics: call_performance_analytics, call_script_templates")
        print("   • Meeting Prep: meeting_prep_packages with learning integration")
        print("   • Analytics: meeting_analytics for aggregated metrics")
        print(f"   • Total indexes created: {len(created_indexes)}")

    except Exception as e:
        print(f"\n❌ ERROR: Migration failed: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   • Check database connection")
        print("   • Verify you have CREATE TABLE permissions")
        print("   • Ensure migration 007 (learning system) was completed")
        print("   • Check for conflicting table names")
        sys.exit(1)


async def check_dependencies():
    """Check if required dependencies exist"""
    print("🔍 Checking migration dependencies...")

    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME", "smarter_team"),
    }

    try:
        conn = await asyncpg.connect(**db_config)

        # Check for required tables from migration 007
        required_tables = ["knowledge_base", "response_tracking", "agent_learning", "meetings"]

        for table in required_tables:
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = $1
                );
            """,
                table,
            )

            if not exists:
                print(f"❌ Required table '{table}' not found. Please run migration 007 first.")
                return False

        await conn.close()
        print("✅ Dependencies check passed")
        return True

    except Exception as e:
        print(f"❌ Dependency check failed: {str(e)}")
        return False


async def rollback_migration():
    """Rollback the meeting management migration"""
    print("🔄 Rolling back Meeting Management System Migration...")

    # Tables to drop in order (respecting dependencies)
    tables_to_drop = [
        # Analytics
        "meeting_analytics",
        # Meeting Prep
        "meeting_prep_packages",
        # Call Analytics
        "call_script_templates",
        "call_performance_analytics",
        # Task Automation
        "task_mappings",
        "task_automation_queue",
        # Notes
        "meeting_notes",
        # Fathom
        "fathom_transcripts",
        "fathom_recordings",
        "fathom_integrations",
        # Participants
        "meeting_participants",
    ]

    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME", "smarter_team"),
    }

    try:
        conn = await asyncpg.connect(**db_config)

        async with conn.transaction():
            for table in tables_to_drop:
                drop_sql = f"DROP TABLE IF EXISTS {table} CASCADE;"
                await conn.execute(drop_sql)
                print(f"   Dropped table: {table}")

        await conn.close()
        print("✅ Rollback completed successfully")

    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    import os
    from urllib.parse import urlparse

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            # Run dependency check
            success = asyncio.run(check_dependencies())
            sys.exit(0 if success else 1)

        elif sys.argv[1] == "rollback":
            # Rollback migration
            success = asyncio.run(rollback_migration())
            sys.exit(0 if success else 1)

        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Usage: python create_meeting_management_tables.py [check|rollback]")
            sys.exit(1)

    # Run dependency check first
    print("🔍 Running dependency check...")
    dependencies_ok = asyncio.run(check_dependencies())

    if not dependencies_ok:
        print("\n❌ Dependency check failed. Please resolve issues before running migration.")
        sys.exit(1)

    # Run migration
    try:
        asyncio.run(create_meeting_management_tables())
    except KeyboardInterrupt:
        print("\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)
