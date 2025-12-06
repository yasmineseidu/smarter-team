# Task 229: Configure Celery Worker and Beat

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure Celery worker and beat scheduler services in Coolify with proper health monitoring, graceful shutdown, and task queue management.

## Prerequisites

- [ ] Task 228 completed (FastAPI service configured)
- [ ] Redis service running
- [ ] Celery tasks implemented

## Implementation Checklist

- [ ] Configure worker service with health checks
- [ ] Configure beat service (single replica only)
- [ ] Set up graceful shutdown for workers
- [ ] Configure task routing and queues
- [ ] Test task execution and scheduling

## Configuration Details

### Worker Service (smarter-team-worker)

```yaml
Service: smarter-team-worker
Command: celery -A src.celery_app worker --loglevel=info --concurrency=4

Health Check:
  Type: exec
  Command: celery -A src.celery_app inspect ping
  Interval: 60s
  Timeout: 30s
  Retries: 3
  Start Period: 120s

Resources:
  CPU: 2.0 (limit), 1.0 (reservation)
  Memory: 2GB (limit), 1GB (reservation)

Replicas: 2
Restart: on-failure

Environment:
  CELERY_WORKER_CONCURRENCY=4
  CELERY_WORKER_PREFETCH_MULTIPLIER=4
  CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
```

### Beat Service (smarter-team-beat)

```yaml
Service: smarter-team-beat
Command: celery -A src.celery_app beat --loglevel=info

Health Check:
  Type: exec
  Command: ps aux | grep "celery beat"
  Interval: 60s
  Timeout: 10s
  Retries: 3

Resources:
  CPU: 0.5 (limit), 0.1 (reservation)
  Memory: 512MB (limit), 256MB (reservation)

Replicas: 1  # CRITICAL: Must be exactly 1
Restart: on-failure
```

## Verification

```bash
# Test worker
docker exec smarter-team-worker celery -A src.celery_app inspect active

# Test beat
docker exec smarter-team-beat celery -A src.celery_app inspect scheduled

# Send test task
curl -X POST https://api.smarter-team.com/api/tasks/test
```

## Notes

- **Worker scaling**: Can have multiple replicas
- **Beat singleton**: MUST be single replica (scheduler)
- **Graceful shutdown**: Workers finish current tasks before stopping
- **Task routing**: Configure queues in celery_app.py
