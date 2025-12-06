#!/usr/bin/env python3
"""
Psql-based Meeting Management Migration
Uses psql command to run the migration directly
"""

import os
import subprocess
import sys
from pathlib import Path


def run_psql_migration():
    """Run migration using psql command"""
    print("🚀 Meeting Management Migration via psql (008)")
    print("=" * 50)

    # Get database URL
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        sys.exit(1)

    # Parse database URL for psql
    # Expected format: postgresql://user:pass@host:port/db
    try:
        if DATABASE_URL.startswith("postgresql://"):
            db_url = DATABASE_URL[11:]  # Remove postgresql://
            parts = db_url.split("@")
            if len(parts) != 2:
                raise ValueError("Invalid URL format")

            user_pass = parts[0].split(":")
            host_db = parts[1].split("/")

            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ""
            host_port = host_db[0].split(":")
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else "5432"
            database = host_db[1] if len(host_db) > 1 else "postgres"

            # Set PGPASSWORD environment variable for psql
            env = os.environ.copy()
            if password:
                env["PGPASSWORD"] = password

        else:
            print("❌ Invalid DATABASE_URL format")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {str(e)}")
        sys.exit(1)

    # Find migration file
    migration_path = Path("../specs/database-schema/migrations/008_meeting_management_system.sql")
    if not migration_path.exists():
        migration_path = Path("specs/database-schema/migrations/008_meeting_management_system.sql")

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        print("Looking for file in...")
        # Try to find the file
        for root, dirs, files in os.walk(".."):
            if "008_meeting_management_system.sql" in files:
                migration_path = Path(root) / "008_meeting_management_system.sql"
                print(f"Found file at: {migration_path}")
                break

    if not migration_path.exists():
        print("❌ Migration file not found anywhere")
        sys.exit(1)

    print(f"📄 Migration file: {migration_path}")
    print(f"📊 File size: {migration_path.stat().st_size:,} bytes")

    # Build psql command
    psql_cmd = [
        "psql",
        "-h",
        host,
        "-p",
        port,
        "-U",
        user,
        "-d",
        database,
        "-f",
        str(migration_path),
    ]

    print(f"🔌 Connecting to: {host}:{port}/{database}")
    print("🔨 Running psql migration...")

    try:
        # Run psql command
        result = subprocess.run(
            psql_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )

        if result.returncode == 0:
            print("✅ Migration completed successfully!")

            # Show summary of output
            output_lines = result.stdout.split("\n")
            print("\n📊 Migration Summary:")
            for line in output_lines:
                if (
                    line.startswith("CREATE TABLE")
                    or line.startswith("ALTER TABLE")
                    or line.startswith("CREATE INDEX")
                ):
                    print(f"   {line}")

                if "CREATE TRIGGER" in line or "CREATE FUNCTION" in line:
                    print(f"   {line}")

            # Check for errors
            if "ERROR" in result.stdout:
                print("\n⚠️  Warnings/Errors found in output:")
                for line in output_lines:
                    if "ERROR" in line:
                        print(f"   {line}")

            print(f"\n📄 Exit code: {result.returncode}")
            return True

        else:
            print(f"❌ Migration failed with exit code {result.returncode}")
            print("\nError output:")
            print(result.stderr)
            print("\nStdout:")
            print(result.stdout)
            return False

    except subprocess.TimeoutExpired:
        print("❌ Migration timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def check_psql_available():
    """Check if psql is available"""
    try:
        result = subprocess.run(["psql", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ psql available: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("❌ psql command not found")
        print("💡 Please install PostgreSQL client tools:")
        print("   • macOS: brew install postgresql")
        print("   • Ubuntu: sudo apt-get install postgresql-client")
        print("   • Or use Docker/Cloud SQL client")
        return False


if __name__ == "__main__":
    print("🔍 Checking prerequisites...")

    if not check_psql_available():
        sys.exit(1)

    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL not set")
        print("💡 Set DATABASE_URL in your environment or .env file")
        sys.exit(1)

    success = run_psql_migration()
    sys.exit(0 if success else 1)
