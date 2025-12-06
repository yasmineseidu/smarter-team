# Task 221: Create Dockerfile for FastAPI Backend

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Create a multi-stage Dockerfile for the FastAPI backend that builds a production-ready image with Python 3.11, includes all dependencies, and optimizes for small image size and fast startup times.

## Prerequisites

- [ ] Coolify instance running and accessible
- [ ] Docker installed locally for testing
- [ ] Backend dependencies finalized in pyproject.toml
- [ ] Environment variables documented in .env.example

## Files to Create/Modify

- [ ] `app/backend/Dockerfile`
- [ ] `app/backend/.dockerignore`
- [ ] `app/backend/docker-entrypoint.sh`

## Implementation Checklist

### Phase 1: Create .dockerignore
- [ ] Create `.dockerignore` to exclude unnecessary files
- [ ] Exclude `__pycache__`, `*.pyc`, `*.pyo`, `*.pyd`
- [ ] Exclude `.pytest_cache`, `.coverage`, `.mypy_cache`, `.ruff_cache`
- [ ] Exclude `__tests__`, `*.md`, `.env`, `.git`

### Phase 2: Create Multi-Stage Dockerfile
- [ ] Stage 1: Builder stage for dependencies
- [ ] Use `python:3.11-slim-bookworm` as base
- [ ] Install build dependencies (gcc, postgresql-dev)
- [ ] Install Python dependencies from pyproject.toml
- [ ] Stage 2: Runtime stage
- [ ] Copy only necessary files from builder
- [ ] Create non-root user for security
- [ ] Set up health check endpoint

### Phase 3: Create Entrypoint Script
- [ ] Create `docker-entrypoint.sh` for startup tasks
- [ ] Run database migrations (if needed)
- [ ] Start uvicorn with proper settings
- [ ] Make script executable

## Configuration Details

### Dockerfile Content

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim-bookworm AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY src ./src

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[prod]"

# Stage 2: Runtime
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder --chown=appuser:appuser /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder --chown=appuser:appuser /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser docker-entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
```

### .dockerignore Content

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Testing
__tests__/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Environment
.env
.env.*
!.env.example

# Git
.git/
.gitignore

# Documentation
*.md
docs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
```

### docker-entrypoint.sh Content

```bash
#!/bin/bash
set -e

echo "Starting FastAPI application..."

# Wait for database to be ready (if needed)
# python -c "import time; from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); time.sleep(2); engine.connect()"

# Run migrations (optional - usually handled separately)
# alembic upgrade head

# Start uvicorn
exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-4}" \
    --loop uvloop \
    --log-level info
```

## Verification

```bash
# Build the Docker image locally
cd app/backend
docker build -t smarter-team-backend:test .

# Check image size
docker images smarter-team-backend:test

# Run container locally
docker run -d \
    -p 8000:8000 \
    --env-file .env \
    --name backend-test \
    smarter-team-backend:test

# Test health endpoint
curl http://localhost:8000/health

# Check logs
docker logs backend-test

# Test API endpoint
curl http://localhost:8000/api/health

# Cleanup
docker stop backend-test
docker rm backend-test
```

## Notes

- **Multi-stage builds** reduce final image size by ~60%
- **Non-root user** improves security (Coolify best practice)
- **Health checks** enable Coolify to monitor service health
- **uvloop** improves async performance by 2-4x
- **Workers**: Set via `UVICORN_WORKERS` env var (default: 4)
- **Base image**: `python:3.11-slim-bookworm` is Debian-based, smaller than full Python image
- **Dependencies**: Only runtime dependencies in final stage (no gcc, build-essential)
- **Migrations**: Can be run in entrypoint or separate init container
- **Expected image size**: ~300-400MB (vs 1GB+ without multi-stage)

## Coolify Integration

Once deployed to Coolify:
1. Coolify will build this Dockerfile on each git push
2. Health check will be monitored automatically
3. Service will auto-restart on failures
4. Logs available in Coolify dashboard
5. Can scale to multiple replicas if needed
