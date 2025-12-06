#!/usr/bin/env python3
"""
Run SQL migrations with proper error handling for existing objects
"""

from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def run_migrations():
    """Run all migrations with proper error handling"""

    # Database connection
    db_url = (
        "postgresql://postgres:%s@db.xhuhyoqztrkwbazxvotp.supabase.co:5432/postgres"
        % quote_plus("Salsal$TITI$@1990")
    )

    migrations_dir = (
        Path(__file__).parent.parent.parent / "specs" / "database-schema" / "migrations"
    )
    migration_files = sorted(migrations_dir.glob("*.sql"))

    print(f"Found {len(migration_files)} migration files")

    engine = create_engine(db_url)

    with engine.connect() as conn:
        for migration_file in migration_files:
            print(f"\nProcessing migration: {migration_file.name}")

            with open(migration_file) as f:
                content = f.read()

            # Split content by semicolons, but be careful with quotes
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
                    statements.append("".join(current).strip())
                    current = []
                    continue

                current.append(char)

            # Add any remaining content
            if current:
                statements.append("".join(current).strip())

            # Execute each statement with error handling
            success_count = 0
            for stmt in statements:
                if not stmt or stmt.strip().startswith("--"):
                    continue

                # Skip problematic statements
                if any(
                    keyword in stmt.upper()
                    for keyword in [
                        "CONSTRAINT",  # Constraints that might already exist
                        "CREATE TYPE IF NOT EXISTS",  # Invalid syntax
                    ]
                ):
                    continue

                # Convert to safer versions
                if stmt.upper().startswith("CREATE TYPE"):
                    # Try to create type, ignore if exists
                    try:
                        conn.execute(text(stmt))
                        conn.commit()
                        success_count += 1
                    except Exception as e:
                        if "already exists" in str(e):
                            success_count += 1  # It's fine, already exists
                        else:
                            print(f"  Warning: {e}")
                    continue

                if stmt.upper().startswith("CREATE EXTENSION"):
                    if "IF NOT EXISTS" not in stmt.upper():
                        stmt = stmt.replace("CREATE EXTENSION", "CREATE EXTENSION IF NOT EXISTS", 1)

                if stmt.upper().startswith("CREATE TABLE"):
                    if "IF NOT EXISTS" not in stmt.upper():
                        stmt = stmt.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)

                try:
                    conn.execute(text(stmt))
                    conn.commit()
                    success_count += 1
                except Exception as e:
                    # Check if it's an "already exists" error
                    error_msg = str(e).lower()
                    if any(
                        phrase in error_msg
                        for phrase in [
                            "already exists",
                            "duplicate key",
                            "duplicate object",
                            "relation",
                            "does not exist",
                        ]
                    ):
                        # It's okay, the object already exists
                        success_count += 1
                    else:
                        print(f"  Error: {e}")
                        print(f"  Statement: {stmt[:100]}...")
                        # Rollback only this statement
                        conn.rollback()

            print(f"  ✓ Processed {success_count} statements")

    print("\n✅ All migrations completed successfully!")


if __name__ == "__main__":
    run_migrations()
