#!/usr/bin/env python3
"""
Verify that all tables were created successfully
"""

from urllib.parse import quote_plus

from sqlalchemy import create_engine, inspect, text


def verify_migrations():
    """Check if all expected tables exist"""

    # Database connection
    db_url = (
        "postgresql://postgres:%s@db.xhuhyoqztrkwbazxvotp.supabase.co:5432/postgres"
        % quote_plus("Salsal$TITI$@1990")
    )

    engine = create_engine(db_url)

    # Expected tables from the migrations
    expected_tables = [
        # Core tables
        "companies",
        "campaigns",
        # Lead entities
        "leads",
        "lead_status_history",
        # Communication
        "conversations",
        "messages",
        "message_approvals",
        # Sales process
        "meetings",
        "proposals",
        "contracts",
        "invoices",
        "payments",
        # System tables
        "audit_logs",
        "error_logs",
        "health_checks",
        "system_metrics",
        "api_usage",
        "performance_analytics",
        "webhook_events",
        "background_jobs",
        # Migration tracking
        "schema_migrations",
    ]

    print("Checking database tables...")

    with engine.connect() as conn:
        # Get inspector
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        print(f"\nFound {len(existing_tables)} tables in database")

        # Check each expected table
        created_tables = []
        missing_tables = []

        for table in expected_tables:
            if table in existing_tables:
                created_tables.append(table)
                print(f"✅ {table}")
            else:
                missing_tables.append(table)
                print(f"❌ {table} - NOT FOUND")

        # Show all tables that exist
        print("\nAll existing tables:")
        for table in sorted(existing_tables):
            if table not in expected_tables:
                print(f"  • {table} (additional)")

        # Summary
        print("\n" + "=" * 50)
        print("Migration Summary:")
        print(f"Expected: {len(expected_tables)}")
        print(f"Created:  {len(created_tables)}")
        print(f"Missing:  {len(missing_tables)}")

        if missing_tables:
            print(f"\nMissing tables: {', '.join(missing_tables)}")
        else:
            print("\n✅ All expected tables created successfully!")

        # Check some key tables have data
        print("\n" + "=" * 50)
        print("Table Row Counts:")

        for table in ["companies", "campaigns", "leads", "schema_migrations"]:
            if table in existing_tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  {table}: {count} rows")
                except Exception as e:
                    print(f"  {table}: Error - {e}")


if __name__ == "__main__":
    verify_migrations()
