#!/usr/bin/env python3
"""
Run SQL migrations directly using psql command
"""

import os
import subprocess
from pathlib import Path


def run_migrations():
    """Run all migrations using psql"""
    # Database connection info
    db_host = "db.xhuhyoqztrkwbazxvotp.supabase.co"
    db_port = "5432"
    db_name = "postgres"
    db_user = "postgres"
    db_password = "Salsal$TITI$@1990"

    # Export password for psql
    os.environ["PGPASSWORD"] = db_password

    migrations_dir = (
        Path(__file__).parent.parent.parent / "specs" / "database-schema" / "migrations"
    )

    # Get all SQL migration files sorted by name
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("No migration files found!")
        return

    print(f"Found {len(migration_files)} migration files")

    # Track migrations in a simple way
    applied_migrations = set()

    for migration_file in migration_files:
        print(f"Running migration: {migration_file.name}")

        # Use psql to run the migration
        cmd = [
            "psql",
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "-d",
            db_name,
            "-f",
            str(migration_file),
            "-v",
            "ON_ERROR_STOP=0",  # Continue on errors
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✓ Completed migration: {migration_file.name}")
                applied_migrations.add(migration_file.name)
            else:
                print(f"⚠ Migration {migration_file.name} had issues:")
                # Print only the first few lines of error output
                error_lines = result.stderr.split("\n")[:5]
                for line in error_lines:
                    if line.strip():
                        print(f"  {line}")
                print("  ... continuing with next migration")
                # Still mark as applied to avoid retrying
                applied_migrations.add(migration_file.name)

        except Exception as e:
            print(f"Error running migration {migration_file.name}: {e}")
            print("Continuing with next migration...")

    # Clean up
    if "PGPASSWORD" in os.environ:
        del os.environ["PGPASSWORD"]

    print("\nMigration Summary:")
    print(f"Total files: {len(migration_files)}")
    print(f"Processed: {len(applied_migrations)}")
    print("\nAll migrations processed!")


if __name__ == "__main__":
    # Check if psql is available
    result = subprocess.run(["which", "psql"], capture_output=True)
    if result.returncode != 0:
        print("Error: psql is not installed or not in PATH")
        print("Please install PostgreSQL client tools")
        exit(1)

    run_migrations()
