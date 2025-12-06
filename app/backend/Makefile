.PHONY: install dev test lint format typecheck clean run worker beat

# Install production dependencies
install:
	pip install -e .

# Install development dependencies
dev:
	pip install -e ".[dev]"
	pre-commit install

# Run tests
test:
	pytest --cov=src --cov-report=term-missing

# Run tests with HTML coverage report
test-html:
	pytest --cov=src --cov-report=html
	open htmlcov/index.html

# Lint code
lint:
	ruff check src/ __tests__/

# Fix linting issues
lint-fix:
	ruff check --fix src/ __tests__/

# Format code
format:
	ruff format src/ __tests__/

# Check formatting
format-check:
	ruff format --check src/ __tests__/

# Type check
typecheck:
	mypy src/

# Run all quality checks
check: lint format-check typecheck test

# Clean build artifacts
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run FastAPI development server
run:
	uvicorn src.main:app --reload --port 8000

# Run Celery worker
worker:
	celery -A config.celery worker --loglevel=info

# Run Celery beat scheduler
beat:
	celery -A config.celery beat --loglevel=info

# Run both worker and beat
worker-beat:
	celery -A config.celery worker --beat --loglevel=info

# Database migrations
migrate:
	alembic upgrade head

# Create new migration
migration:
	alembic revision --autogenerate -m "$(name)"
