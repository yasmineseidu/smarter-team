# Task 228: Configure FastAPI Service (with Health Checks)

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure the FastAPI backend service in Coolify with production-grade health checks, monitoring endpoints, resource limits, and auto-scaling capabilities.

## Prerequisites

- [ ] Task 227 completed (Build and deployment settings configured)
- [ ] Backend Dockerfile tested and working
- [ ] Health check endpoints implemented in FastAPI

## Files to Create/Modify

- [ ] `app/backend/src/main.py` (add health check endpoints)
- [ ] `app/backend/src/health.py` (detailed health checks)

## Implementation Checklist

### Phase 1: Implement Health Check Endpoints
- [ ] Create `/health` endpoint (liveness probe)
- [ ] Create `/health/ready` endpoint (readiness probe)
- [ ] Create `/health/detailed` endpoint (diagnostic info)
- [ ] Add database connectivity check
- [ ] Add Redis connectivity check

### Phase 2: Configure Service in Coolify
- [ ] Set health check path to `/health`
- [ ] Configure health check interval
- [ ] Set startup grace period
- [ ] Enable auto-restart on failure

### Phase 3: Configure Resource Limits
- [ ] Set CPU limits
- [ ] Set memory limits
- [ ] Configure auto-scaling rules (if available)

### Phase 4: Set Up Monitoring
- [ ] Enable Coolify metrics collection
- [ ] Configure log retention
- [ ] Set up alerting rules

## Configuration Details

### Health Check Endpoints Implementation

**Create `app/backend/src/health.py`:**

```python
"""Health check endpoints for service monitoring."""

import asyncio
from typing import Any

import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint (liveness probe).

    Returns 200 if service is alive.
    """
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check endpoint (readiness probe).

    Returns 200 if service is ready to accept traffic.
    Checks:
    - Database connectivity
    - Redis connectivity
    """
    checks = {}
    healthy = True

    # Check database
    try:
        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        healthy = False

    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
        healthy = False

    if not healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "checks": checks}
        )

    return {"status": "ready", "checks": checks}


@router.get("/health/detailed")
async def detailed_health() -> dict[str, Any]:
    """
    Detailed health check with diagnostic information.

    Returns comprehensive system status.
    """
    import os
    import sys
    from datetime import datetime

    checks = {}

    # System info
    checks["system"] = {
        "python_version": sys.version,
        "platform": sys.platform,
        "timestamp": datetime.utcnow().isoformat(),
        "pid": os.getpid(),
        "environment": settings.environment,
    }

    # Database check with timing
    try:
        start = asyncio.get_event_loop().time()
        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
        duration = asyncio.get_event_loop().time() - start

        checks["database"] = {
            "status": "healthy",
            "version": version,
            "response_time_ms": round(duration * 1000, 2),
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Redis check with timing
    try:
        start = asyncio.get_event_loop().time()
        r = redis.from_url(settings.redis_url)
        await r.ping()
        info = await r.info()
        await r.close()
        duration = asyncio.get_event_loop().time() - start

        checks["redis"] = {
            "status": "healthy",
            "version": info.get("redis_version"),
            "response_time_ms": round(duration * 1000, 2),
            "connected_clients": info.get("connected_clients"),
        }
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Overall status
    healthy = all(
        check.get("status") == "healthy"
        for check in checks.values()
        if isinstance(check, dict) and "status" in check
    )

    return {
        "status": "healthy" if healthy else "degraded",
        "checks": checks,
    }
```

**Update `app/backend/src/main.py`:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.health import router as health_router

app = FastAPI(
    title="Smarter Team API",
    description="Multi-agent AI agency automation",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check routes
app.include_router(health_router)

# Add other routers here
# app.include_router(leads_router, prefix="/api/leads")
# app.include_router(campaigns_router, prefix="/api/campaigns")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Smarter Team API",
        "version": "1.0.0",
        "status": "running",
    }
```

### Coolify Service Configuration

**In Coolify UI (smarter-team-backend):**

```yaml
Service Configuration:
  Name: smarter-team-backend
  Port: 8000

Health Check:
  Path: /health
  Port: 8000
  Interval: 30s
  Timeout: 10s
  Retries: 3
  Start Period: 60s

  Success Criteria:
    - HTTP Status: 200
    - Response contains: "healthy"

  Failure Actions:
    - Retry 3 times
    - If all fail: restart container
    - Log failure details

Resources:
  CPU Limit: 2.0
  CPU Reservation: 0.5
  Memory Limit: 2GB
  Memory Reservation: 512MB

Auto-Restart:
  Enabled: true
  Condition: on-failure
  Max Attempts: 3
  Delay: 5s
  Window: 120s

Scaling (optional):
  Min Replicas: 2
  Max Replicas: 5
  CPU Threshold: 70%
  Memory Threshold: 80%
```

## Verification

### Test Health Endpoints Locally

```bash
cd app/backend

# Start FastAPI locally
uvicorn src.main:app --reload

# Test liveness
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test readiness
curl http://localhost:8000/health/ready
# Expected: {"status":"ready","checks":{...}}

# Test detailed health
curl http://localhost:8000/health/detailed
# Expected: Full diagnostic info
```

### Test in Coolify

```bash
# After deployment, test external health endpoint
curl https://api.smarter-team.com/health

# Test readiness
curl https://api.smarter-team.com/health/ready

# Test detailed (should include actual DB/Redis status)
curl https://api.smarter-team.com/health/detailed
```

### Verify Auto-Restart

```bash
# SSH into Coolify server
ssh user@coolify-server

# Kill backend container
docker kill smarter-team-backend

# Watch it auto-restart (should happen within 30s)
watch docker ps | grep backend

# Check Coolify logs for restart event
```

### Monitor Resource Usage

In Coolify UI:
1. Navigate to smarter-team-backend
2. Click "Metrics" tab
3. Verify CPU and memory usage
4. Check for memory leaks (usage should be stable)

## Notes

- **Liveness vs Readiness**:
  - Liveness (`/health`): Is the process running?
  - Readiness (`/health/ready`): Can it accept traffic?
- **Startup grace period**: 60s allows for slow starts
- **Auto-restart**: Max 3 attempts prevents restart loops
- **Resource limits**: Prevent resource exhaustion

## Best Practices

1. **Keep liveness check simple** - just check process is alive
2. **Make readiness check comprehensive** - verify all dependencies
3. **Set appropriate timeouts** - balance responsiveness vs false positives
4. **Monitor restart count** - frequent restarts indicate issues
5. **Log health check failures** - for debugging

## Troubleshooting

**Health check always fails:**
- Verify endpoint returns 200 status
- Check response time < timeout
- Ensure dependencies (DB, Redis) are accessible
- Review service logs

**Service frequently restarts:**
- Check memory usage (may need increase)
- Review application logs for errors
- Verify database connection pool settings
- Check for memory leaks

**Readiness check fails but liveness passes:**
- Database or Redis connectivity issue
- Check network configuration
- Verify credentials are correct
- Test connectivity from container

## Next Steps

After configuring FastAPI service:
1. Monitor health check success rate
2. Adjust timeout/interval if needed
3. Proceed to Task 229: Configure Celery worker and beat
