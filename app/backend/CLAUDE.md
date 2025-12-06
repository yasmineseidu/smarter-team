# Backend - Claude Instructions

<!-- AUTO-MANAGED: overview -->
## Overview

Python backend for Smarter Team multi-agent system. FastAPI + Claude Agent SDK + Celery.

**Stack**: Python 3.11+, FastAPI 0.123.10, Celery 5.6.0, SQLAlchemy 2.0, Redis 6.4.0
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: commands -->
## Commands

```bash
# Development
make run                  # FastAPI on port 8000
make worker               # Celery worker
make beat                 # Celery beat scheduler
make worker-beat          # Worker + beat together

# Quality
make lint                 # Ruff linter
make lint-fix             # Auto-fix linting
make format               # Ruff formatter
make typecheck            # MyPy type checking
make test                 # Pytest with coverage
make check                # All quality checks

# Database
make migrate              # Apply migrations
make migration name="x"   # Create new migration
python create_missing_tables.py     # Create missing tables individually
python migrate_remaining_tables.py  # Run remaining migrations (002-006)
python update_migration_tracking.py # Update migration tracking table
python create_learning_system_tables.py  # Create learning & improvement system tables (007)
# Meeting Management (008) - COMPLETED
python final_meeting_migration.py          # Creates 5 meeting tables (successful)
python verify_meeting_migration.py         # Verify meeting tables were created
python migrate_meeting_tables_only.py      # Alternative: Create only new tables
python quick_meeting_migration.py          # Simplified migration approach
python run_meeting_migration_direct.py     # Direct SQL execution from migration file

# Setup
pip install -e ".[dev]"   # Install with dev deps
pre-commit install        # Git hooks
```
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: structure -->
## Structure

```
src/
├── agents/               # Claude Agent SDK implementations
│   ├── base_agent.py     # BaseAgent ABC (handoff, logging)
│   └── [agent_name]/     # Individual agents
├── integrations/         # Third-party API clients
│   └── base.py           # BaseIntegrationClient
├── tasks/                # Celery background tasks
├── webhooks/             # Webhook handlers
├── config.py             # Settings, get_agent_logger()
└── main.py               # FastAPI app

Database utilities:
├── create_missing_tables.py         # Create individual missing tables
├── migrate_remaining_tables.py      # Run remaining migrations with error handling
├── update_migration_tracking.py     # Update schema_migrations table
├── create_learning_system_tables.py # Create learning & improvement system tables (007)
├── final_meeting_migration.py       # ✅ Creates 5 meeting tables (successful)
├── verify_meeting_migration.py      # Verify meeting tables were created
├── migrate_meeting_tables_only.py   # Alternative: Create only new tables
├── quick_meeting_migration.py       # Simplified migration approach
├── run_meeting_migration_direct.py  # Direct SQL execution from migration file
├── create_meeting_management_tables.py  # Advanced meeting migration (008)
├── run_meeting_management_migration.py  # SQLAlchemy-based migration
├── run_meeting_migration_safe.py        # Safe migration with error handling
└── psql_meeting_migration.py            # PostgreSQL-specific migration runner

__tests__/
├── fixtures/             # Test fixtures
├── unit/                 # Unit tests
└── integration/          # Integration tests
```
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: conventions -->
## Conventions

- Full type hints (`mypy --strict`)
- Line length: 100 chars
- Double quotes for strings
- All I/O must be async
- Naming: `snake_case` files/functions, `PascalCase` classes
- Agents extend `BaseAgent`, clients extend `BaseIntegrationClient`
- Celery tasks use `@celery_app.task(bind=True, max_retries=3)`
- Structured logging via `get_agent_logger(name)`

**Database Migration Patterns:**
- Migration scripts: `create_[system]_tables.py` or `run_[system]_migration.py`
- Use SQLAlchemy `create_engine()` with `postgresql://` connection string
- Password encode with `quote_plus()` for special characters
- Table creation: `CREATE TABLE IF NOT EXISTS` with UUID primary keys
- Add `created_at` and `updated_at` TIMESTAMPTZ columns to all tables
- Use `gen_random_uuid()` for default UUID values
- Handle "already exists" errors gracefully
- Verification scripts: `verify_[system]_migration.py`
<!-- END AUTO-MANAGED -->

<!-- MANUAL -->
## Notes

- See root CLAUDE.md for full architecture and patterns
- Agent plans in `plan/agents/` (51 agents across 9 categories)
- Task workflow: `tasks/[domain]/pending/` → `_in-progress/` → `_completed/`
<!-- END MANUAL -->
