# Task 235: Configure Health Check Endpoints

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Implement comprehensive health check endpoints across all services with database connectivity, Redis status, and dependency checks.

## Prerequisites

- [ ] Task 228 completed (FastAPI service configured)
- [ ] All services deployed

## Implementation Checklist

- [ ] Implement liveness probes (basic health)
- [ ] Implement readiness probes (dependency checks)
- [ ] Add version and build info endpoints
- [ ] Configure health check intervals
- [ ] Test all health endpoints

## Configuration Details

### Health Check Matrix

```yaml
Backend (/health):
  - Process alive: ✓
  - Database connectivity: ✓
  - Redis connectivity: ✓
  - Celery broker: ✓
  - Response time: < 200ms

Worker (celery inspect):
  - Worker process alive: ✓
  - Active tasks count: ✓
  - Queue length: ✓
  - Connection to Redis: ✓

Frontend (/api/health):
  - Next.js server alive: ✓
  - Backend reachability: ✓
  - Response time: < 100ms

Redis (redis-cli ping):
  - PONG response: ✓
  - Memory usage: < 80%
  - Connected clients: > 0
```

### Additional Endpoints

```python
# Add to src/main.py

@app.get("/version")
async def version():
    """Version and build information."""
    return {
        "version": "1.0.0",
        "build": os.getenv("BUILD_ID", "local"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "deployed_at": os.getenv("DEPLOY_TIME", "unknown"),
    }

@app.get("/metrics")
async def metrics():
    """Basic metrics for monitoring."""
    import psutil

    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }
```

## Verification

```bash
# Test all health endpoints
for service in backend worker frontend; do
  echo "Testing $service..."
  curl https://api.smarter-team.com/health
done

# Monitor health check success rate in Coolify
```

## Notes

- **Liveness**: Basic process check (fast)
- **Readiness**: Full dependency check (slower)
- **Metrics**: Optional performance data
- **Version**: Useful for deployment verification
