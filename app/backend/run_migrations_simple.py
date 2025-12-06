#!/usr/bin/env python3
"""
Run SQL migrations directly using SQLAlchemy
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()


def run_migrations():
    """Run all migrations"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Try to get it from parent directory
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    # Fix URL encoding for password if needed
    # The password has special characters that need encoding
    print(f"Original URL: {database_url}")

    # Reconstruct the URL with proper encoding
    database_url = (
        "postgresql://postgres:%s@db.xhuhyoqztrkwbazxvotp.supabase.co:5432/postgres"
        % quote_plus("Salsal$TITI$@1990")
    )
    print(f"Fixed URL: {database_url}")

    migrations_dir = (
        Path(__file__).parent.parent.parent / "specs" / "database-schema" / "migrations"
    )

    # Get all SQL migration files sorted by name
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("No migration files found!")
        return

    print(f"Found {len(migration_files)} migration files")

    # Create engine
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Create migrations table if not exists
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        )
        conn.commit()

        for migration_file in migration_files:
            # Check if migration already applied
            result = conn.execute(
                text("SELECT filename FROM schema_migrations WHERE filename = :filename"),
                {"filename": migration_file.name},
            )

            applied = result.fetchone()

            if not applied:
                print(f"Running migration: {migration_file.name}")

                with open(migration_file) as f:
                    sql = f.read()

                # Execute the migration
                try:
                    # Split by semicolon for multiple statements
                    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]

                    for stmt in statements:
                        if stmt:
                            conn.execute(text(stmt))

                    conn.commit()

                    # Record migration
                    conn.execute(
                        text("INSERT INTO schema_migrations (filename) VALUES (:filename)"),
                        {"filename": migration_file.name},
                    )
                    conn.commit()

                    print(f"Completed migration: {migration_file.name}")

                except Exception as e:
                    print(f"Error running migration {migration_file.name}: {e}")
                    print(f"SQL: {sql[:200]}...")
                    conn.rollback()
                    raise
            else:
                print(f"Skipping already applied migration: {migration_file.name}")

        print("All migrations completed successfully!")


if __name__ == "__main__":
    run_migrations()
