#!/usr/bin/env python3
"""
Run SQL migrations directly
"""

import asyncio
import os
from pathlib import Path

import asyncpg  # type: ignore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def run_migration(connection, migration_file: Path):
    """Run a single migration file"""
    print(f"Running migration: {migration_file.name}")

    with open(migration_file) as f:
        sql = f.read()

    # Split SQL by semicolons and execute each statement
    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]

    for stmt in statements:
        if stmt:
            try:
                await connection.execute(stmt)
            except Exception as e:
                print(f"Error executing statement: {stmt[:100]}...")
                print(f"Error: {e}")
                raise

    print(f"Completed migration: {migration_file.name}")


async def main():
    """Run all migrations"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    # Parse database URL for asyncpg
    # asyncpg expects: postgres://user:password@host:port/database
    db_url = database_url.replace("postgresql://", "postgres://")

    migrations_dir = Path(__file__).parent.parent / "specs" / "database-schema" / "migrations"

    # Get all SQL migration files sorted by name
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("No migration files found!")
        return

    print(f"Found {len(migration_files)} migration files")

    # Connect to database and run migrations
    conn = await asyncpg.connect(db_url)

    try:
        # Create migrations table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        for migration_file in migration_files:
            # Check if migration already applied
            applied = await conn.fetchval(
                "SELECT filename FROM schema_migrations WHERE filename = $1", migration_file.name
            )

            if not applied:
                await run_migration(conn, migration_file)
                # Record migration
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)", migration_file.name
                )
            else:
                print(f"Skipping already applied migration: {migration_file.name}")

        print("All migrations completed successfully!")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
