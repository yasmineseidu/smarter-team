# Task 230: Configure Redis Service

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure Redis service in Coolify with persistence, memory limits, and backup strategies for Celery broker and application caching.

## Prerequisites

- [ ] Task 224 completed (Coolify project created)

## Implementation Checklist

- [ ] Create Redis database service in Coolify
- [ ] Enable persistence (RDB or AOF)
- [ ] Configure memory limits and eviction policy
- [ ] Set up periodic backups
- [ ] Test connectivity from other services

## Configuration Details

### Redis Service Configuration

```yaml
Service: smarter-team-redis
Image: redis:7-alpine
Port: 6379 (internal only)

Persistence:
  Type: RDB + AOF
  Volume: /data
  Save: "900 1 300 10 60 10000"

Memory:
  Limit: 512MB
  Policy: allkeys-lru

Resources:
  CPU: 1.0 (limit), 0.25 (reservation)
  Memory: 512MB (limit), 256MB (reservation)

Health Check:
  Command: redis-cli ping
  Interval: 10s
  Timeout: 5s
  Retries: 5
```

### Redis Configuration (redis.conf)

```conf
# Memory
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300
```

## Verification

```bash
# Test Redis from backend
docker exec smarter-team-backend python -c "
import redis
r = redis.from_url('redis://smarter-team-redis:6379/0')
print('Ping:', r.ping())
r.set('test', 'hello')
print('Get:', r.get('test'))
"

# Check Redis info
docker exec smarter-team-redis redis-cli info memory
docker exec smarter-team-redis redis-cli info persistence
```

## Notes

- **Internal only**: No external port exposure
- **Persistence**: Both RDB (snapshots) and AOF (append-only file)
- **Eviction**: LRU policy prevents OOM
- **Backups**: Automated via Coolify volume snapshots
