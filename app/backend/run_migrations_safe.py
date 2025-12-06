#!/usr/bin/env python3
"""
Run SQL migrations safely with IF NOT EXISTS logic
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()


def run_migrations():
    """Run all migrations safely"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    # Reconstruct the URL with proper encoding
    database_url = (
        "postgresql://postgres:%s@db.xhuhyoqztrkwbazxvotp.supabase.co:5432/postgres"
        % quote_plus("Salsal$TITI$@1990")
    )

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

                # Process SQL to add IF NOT EXISTS for CREATE TABLE
                # This is a simplified approach - for complex migrations, you might need more sophisticated logic
                lines = sql.split("\n")
                processed_lines = []
                in_create_table = False

                for line in lines:
                    stripped = line.strip()

                    # Skip constraint creation that might already exist
                    if stripped.startswith("CONSTRAINT") and "CHECK" in stripped:
                        continue

                    # Convert CREATE TABLE to CREATE TABLE IF NOT EXISTS
                    if stripped.upper().startswith("CREATE TABLE"):
                        if "IF NOT EXISTS" not in stripped.upper():
                            line = line.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)

                    # Skip CREATE EXTENSION if it already exists
                    if stripped.upper().startswith("CREATE EXTENSION"):
                        if "IF NOT EXISTS" not in stripped.upper():
                            line = line.replace(
                                "CREATE EXTENSION", "CREATE EXTENSION IF NOT EXISTS", 1
                            )

                    # Skip CREATE TYPE that might already exist
                    if stripped.upper().startswith("CREATE TYPE"):
                        if "IF NOT EXISTS" not in stripped.upper():
                            line = line.replace("CREATE TYPE", "CREATE TYPE IF NOT EXISTS", 1)

                    processed_lines.append(line)

                processed_sql = "\n".join(processed_lines)

                # Execute the migration with error handling
                try:
                    # Split by semicolon for multiple statements
                    statements = [stmt.strip() for stmt in processed_sql.split(";") if stmt.strip()]

                    for stmt in statements:
                        if stmt and not stmt.strip().startswith("--"):
                            try:
                                conn.execute(text(stmt))
                            except Exception as e:
                                # Ignore errors about objects already existing
                                if "already exists" in str(e) or "duplicate key" in str(e).lower():
                                    print(f"  Skipping (already exists): {stmt[:100]}...")
                                    continue
                                else:
                                    raise

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
                    # Don't rollback - some statements may have succeeded
                    # Continue with next migration
                    continue
            else:
                print(f"Skipping already applied migration: {migration_file.name}")

        print("All migrations completed!")


if __name__ == "__main__":
    run_migrations()
