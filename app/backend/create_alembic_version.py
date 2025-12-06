#!/usr/bin/env python3
"""
Create Alembic version table and mark current state as version 001
"""

import uuid
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def create_alembic_version():
    """Create alembic version table and mark initial migration"""

    # Database connection
    db_url = (
        "postgresql://postgres:%s@db.xhuhyoqztrkwbazxvotp.supabase.co:5432/postgres"
        % quote_plus("Salsal$TITI$@1990")
    )

    engine = create_engine(db_url)

    print("Setting up Alembic version tracking...")

    with engine.connect() as conn:
        # Create alembic_version table if not exists
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        )
        conn.commit()

        # Check if there's already a version
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        existing = result.fetchone()

        if existing:
            print(f"Current Alembic version: {existing[0]}")
        else:
            # Insert initial version
            version = str(uuid.uuid4()).replace("-", "")[:12]
            conn.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:version)"),
                {"version": version},
            )
            conn.commit()
            print(f"Created initial Alembic version: {version}")

        # Also create/update schema_migrations table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        )
        conn.commit()

        # Mark migrations as applied
        migrations = [
            "001_core_tables.sql",
            "002_lead_entities.sql",
            "003_communication_tables.sql",
            "004_sales_process_tables.sql",
            "005_system_tables.sql",
            "006_functions_and_triggers.sql",
        ]

        for migration in migrations:
            result = conn.execute(
                text("SELECT filename FROM schema_migrations WHERE filename = :filename"),
                {"filename": migration},
            )
            if not result.fetchone():
                conn.execute(
                    text("INSERT INTO schema_migrations (filename) VALUES (:filename)"),
                    {"filename": migration},
                )
                print(f"✅ Marked migration as applied: {migration}")

        conn.commit()
        print("\n✅ Alembic setup complete!")


if __name__ == "__main__":
    create_alembic_version()
