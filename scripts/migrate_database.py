#!/usr/bin/env python3
"""Database migration script for Smarter Team."""

import asyncio
import logging
from pathlib import Path
from typing import List

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def execute_migration_file(
    conn: asyncpg.Connection, migration_path: Path
) -> None:
    """Execute a single migration file."""
    with open(migration_path, "r") as f:
        content = f.read()

    # Split content by semicolons, handling PostgreSQL syntax properly
    statements = []
    current_statement = []

    for line in content.split("\n"):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("--"):
            continue

        current_statement.append(line)

        # If line ends with semicolon, complete the statement
        if line.endswith(";"):
            statement = "\n".join(current_statement)
            # Skip empty statements
            if statement.strip() != ";":
                statements.append(statement)
            current_statement = []

    # Add any remaining statement
    if current_statement:
        statement = "\n".join(current_statement)
        if statement.strip():
            statements.append(statement)

    # Execute each statement
    for statement in statements:
        try:
            # Skip the schema_migrations table creation if it already exists
            if "CREATE TABLE IF NOT EXISTS schema_migrations" in statement:
                pass

            await conn.execute(statement)
            logger.info(f"Executed statement from {migration_path.name}")
        except Exception as e:
            # Check if it's just a "already exists" error
            if "already exists" in str(e).lower():
                logger.warning(f"Object already exists in {migration_path.name}: {e}")
            else:
                logger.error(f"Error executing statement in {migration_path.name}: {e}")
                raise


async def get_executed_migrations(conn: asyncpg.Connection) -> set[str]:
    """Get set of already executed migration versions."""
    try:
        result = await conn.fetch("SELECT version FROM schema_migrations")
        return {row["version"] for row in result}
    except Exception:
        # Table doesn't exist yet
        return set()


async def mark_migration_executed(
    conn: asyncpg.Connection, version: str
) -> None:
    """Mark a migration as executed."""
    await conn.execute(
        """
        INSERT INTO schema_migrations (version, applied_at)
        VALUES ($1, NOW())
        ON CONFLICT (version) DO NOTHING
        """,
        version
    )


async def run_migrations(database_url: str, migrations_dir: Path) -> None:
    """Run all pending migrations."""
    conn = await asyncpg.connect(database_url)

    try:
        # Ensure schema_migrations table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(50) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                description TEXT
            )
        """)

        # Get executed migrations
        executed = await get_executed_migrations(conn)

        # Get all migration files
        migration_files: List[Path] = sorted(migrations_dir.glob("*.sql"))

        # Run pending migrations
        for migration_file in migration_files:
            version = migration_file.stem

            if version not in executed:
                logger.info(f"Running migration: {version}")
                await execute_migration_file(conn, migration_file)
                await mark_migration_executed(conn, version)
                logger.info(f"Migration {version} completed successfully")
            else:
                logger.info(f"Skipping already executed migration: {version}")

        logger.info("All migrations completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()


async def main():
    """Main migration function."""
    import os

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return

    # Path to migrations directory
    migrations_dir = Path(__file__).parent.parent / "specs" / "database-schema" / "migrations"

    if not migrations_dir.exists():
        logger.error(f"Migrations directory not found: {migrations_dir}")
        return

    # Run migrations
    await run_migrations(database_url, migrations_dir)


if __name__ == "__main__":
    asyncio.run(main())
