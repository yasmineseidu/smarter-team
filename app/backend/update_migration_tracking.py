#!/usr/bin/env python3
"""
Update migration tracking to reflect all completed migrations
"""

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def update_migration_tracking():
    """Update schema_migrations table with all migration files"""

    # Database connection
    db_url = (
        "postgresql://postgres:%s@db.xhuhyoqztrkwbazxvotp.supabase.co:5432/postgres"
        % quote_plus("Salsal$TITI$@1990")
    )

    engine = create_engine(db_url)

    print("Updating migration tracking...")

    with engine.connect() as conn:
        # All migration files that should be marked as applied
        all_migrations = [
            "001_core_tables.sql",
            "002_lead_entities.sql",
            "003_communication_tables.sql",
            "004_sales_process_tables.sql",
            "005_system_tables.sql",
            "006_functions_and_triggers.sql",
        ]

        for migration in all_migrations:
            result = conn.execute(
                text("SELECT filename FROM schema_migrations WHERE filename = :filename"),
                {"filename": migration},
            )
            if not result.fetchone():
                conn.execute(
                    text("INSERT INTO schema_migrations (filename) VALUES (:filename)"),
                    {"filename": migration},
                )
                print(f"✅ Added: {migration}")
            else:
                print(f"✅ Already tracked: {migration}")

        conn.commit()
        print("\n✅ Migration tracking updated!")

        # Show summary
        result = conn.execute(text("SELECT COUNT(*) FROM schema_migrations"))
        count = result.scalar()
        print(f"\nTotal migrations tracked: {count}")

        print("\nAll migration files:")
        result = conn.execute(
            text("SELECT filename, applied_at FROM schema_migrations ORDER BY filename")
        )
        for row in result.fetchall():
            print(f"  • {row[0]} (applied: {row[1]})")


if __name__ == "__main__":
    update_migration_tracking()
