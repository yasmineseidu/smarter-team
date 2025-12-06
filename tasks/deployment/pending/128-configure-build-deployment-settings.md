# Task 227: Configure Build and Deployment Settings

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Optimize build and deployment settings in Coolify for faster builds, efficient resource usage, and reliable deployments across all services (FastAPI, Celery, Next.js).

## Prerequisites

- [ ] Tasks 224-226 completed (Coolify project, environment variables, Git repository)
- [ ] Services successfully deployed at least once
- [ ] Build logs reviewed for optimization opportunities

## Files to Create/Modify

- [ ] `app/backend/.dockerignore` (optimize if needed)
- [ ] `app/frontend/.dockerignore` (optimize if needed)
- [ ] `.github/workflows/ci.yml` (update for Coolify integration)

## Implementation Checklist

### Phase 1: Configure Build Cache
- [ ] Enable Docker layer caching for all services
- [ ] Configure BuildKit for faster builds
- [ ] Set appropriate cache expiration
- [ ] Test cache effectiveness

### Phase 2: Optimize Build Resources
- [ ] Set build timeout limits per service
- [ ] Configure build memory limits
- [ ] Set concurrent build limits
- [ ] Allocate CPU resources for builds

### Phase 3: Configure Deployment Strategy
- [ ] Set rolling update strategy
- [ ] Configure zero-downtime deployments
- [ ] Set deployment timeout
- [ ] Configure rollback on failure

### Phase 4: Set Up Health Check Requirements
- [ ] Define health check success criteria
- [ ] Set appropriate timeout values
- [ ] Configure retry attempts
- [ ] Set grace period for startup

## Configuration Details

### Build Cache Settings

**In Coolify UI (per service):**

```yaml
Backend Service (smarter-team-backend):
  Build Settings:
    - Enable cache: true
    - Cache layers: true
    - BuildKit: enabled
    - Build timeout: 15 minutes
    - Build memory limit: 2GB

Worker Service (smarter-team-worker):
  Build Settings:
    - Enable cache: true
    - Cache layers: true
    - BuildKit: enabled
    - Build timeout: 15 minutes (shares cache with backend)
    - Build memory limit: 2GB

Beat Service (smarter-team-beat):
  Build Settings:
    - Enable cache: true
    - Cache layers: true
    - BuildKit: enabled
    - Build timeout: 15 minutes (shares cache with backend)
    - Build memory limit: 2GB

Frontend Service (smarter-team-frontend):
  Build Settings:
    - Enable cache: true
    - Cache layers: true
    - BuildKit: enabled
    - Build timeout: 20 minutes (Next.js builds can be slower)
    - Build memory limit: 4GB
    - Node memory: 4096
```

### Deployment Strategy Settings

```yaml
All Services:
  Deployment:
    strategy: rolling
    max_surge: 1
    max_unavailable: 0

    health_check:
      enabled: true
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

    rollback:
      on_failure: true
      max_retries: 2

    timeout:
      deployment: 10 minutes
      shutdown: 30s
```

### Service-Specific Deployment Settings

**Backend (smarter-team-backend):**
```yaml
deployment:
  replicas: 2
  update_config:
    parallelism: 1
    delay: 10s
    order: start-first  # Zero downtime
  rollback_config:
    parallelism: 1
    delay: 5s
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3
    window: 120s
```

**Worker (smarter-team-worker):**
```yaml
deployment:
  replicas: 2
  update_config:
    parallelism: 1
    delay: 30s  # Let tasks finish
    order: stop-first  # Prevent duplicate task processing
  rollback_config:
    parallelism: 1
    delay: 5s
  restart_policy:
    condition: on-failure
    delay: 10s
    max_attempts: 3
    window: 120s
```

**Beat (smarter-team-beat):**
```yaml
deployment:
  replicas: 1  # MUST be 1 (scheduler singleton)
  update_config:
    parallelism: 1
    delay: 10s
    order: start-first
  rollback_config:
    parallelism: 1
    delay: 5s
  restart_policy:
    condition: on-failure
    delay: 10s
    max_attempts: 3
    window: 120s
```

**Frontend (smarter-team-frontend):**
```yaml
deployment:
  replicas: 2
  update_config:
    parallelism: 1
    delay: 5s
    order: start-first  # Zero downtime
  rollback_config:
    parallelism: 1
    delay: 5s
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3
    window: 120s
```

### Build Optimization

**Enable BuildKit in Dockerfiles:**

Add to all Dockerfiles:
```dockerfile
# syntax=docker/dockerfile:1.4

# Use BuildKit features
FROM python:3.11-slim-bookworm AS builder

# Enable BuildKit cache mounts
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -e ".[prod]"
```

**Optimize .dockerignore:**

Ensure these are excluded:
```
# Build artifacts
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
node_modules/
.next/

# Git
.git/
.github/

# Documentation
*.md
docs/

# Large files
*.log
*.sqlite
*.db
```

## Coolify-Specific Settings

### Enable Advanced Features

1. **Navigate to Coolify → Settings → Advanced**
2. **Enable BuildKit:**
   ```bash
   DOCKER_BUILDKIT=1
   COMPOSE_DOCKER_CLI_BUILD=1
   ```

3. **Configure Docker daemon:**
   ```json
   {
     "experimental": true,
     "features": {
       "buildkit": true
     },
     "max-concurrent-builds": 3,
     "builder": {
       "gc": {
         "enabled": true,
         "defaultKeepStorage": "20GB"
       }
     }
   }
   ```

### Set Resource Limits

**In Coolify UI (per service):**

```yaml
Backend:
  resources:
    limits:
      cpus: '2.0'
      memory: 2GB
    reservations:
      cpus: '0.5'
      memory: 512MB

Worker:
  resources:
    limits:
      cpus: '2.0'
      memory: 2GB
    reservations:
      cpus: '1.0'
      memory: 1GB

Beat:
  resources:
    limits:
      cpus: '0.5'
      memory: 512MB
    reservations:
      cpus: '0.1'
      memory: 256MB

Frontend:
  resources:
    limits:
      cpus: '2.0'
      memory: 2GB
    reservations:
      cpus: '0.5'
      memory: 512MB

Redis:
  resources:
    limits:
      cpus: '1.0'
      memory: 512MB
    reservations:
      cpus: '0.25'
      memory: 256MB
```

## Verification

### Test Build Performance

```bash
# Build with timing
time docker build -t test-backend ./app/backend

# Check cache usage
docker build --no-cache -t test-backend ./app/backend  # Without cache
docker build -t test-backend ./app/backend             # With cache

# Compare build times
```

### Monitor Deployment

```bash
# Watch deployment in real-time (Coolify UI)
# Deployments → Latest → View Logs

# Check deployment time
# Should complete in 3-5 minutes with cache
# First build: 10-15 minutes without cache
```

### Verify Zero-Downtime

```bash
# Monitor health endpoint during deployment
while true; do
  curl -s https://api.smarter-team.com/health || echo "DOWN"
  sleep 1
done

# Should never show "DOWN" during rolling update
```

### Check Resource Usage

```bash
# SSH into Coolify server
ssh user@coolify-server

# Monitor resources during build
docker stats

# Check build cache size
docker system df

# View build history
docker images | grep smarter-team
```

## Performance Benchmarks

**Expected Build Times (with cache):**
- Backend: 2-3 minutes
- Worker: 30 seconds (shares backend cache)
- Beat: 30 seconds (shares backend cache)
- Frontend: 4-6 minutes
- Total: 6-8 minutes for all services

**Expected Build Times (without cache):**
- Backend: 8-10 minutes
- Worker: 30 seconds (uses backend image)
- Beat: 30 seconds (uses backend image)
- Frontend: 12-15 minutes
- Total: 20-25 minutes for all services

**Deployment Times:**
- Rolling update: 2-3 minutes per service
- Total deployment: 8-12 minutes
- Zero downtime: ✓

## Notes

- **Cache sharing**: Worker and Beat share backend build cache
- **BuildKit**: Reduces build time by 30-50%
- **Rolling updates**: Ensure zero downtime for user-facing services
- **Resource limits**: Prevent resource exhaustion
- **Automatic rollback**: Triggered if health checks fail

## Best Practices

1. **Use multi-stage builds** to minimize final image size
2. **Enable BuildKit** for parallel layer builds
3. **Cache pip/npm installs** separately from code changes
4. **Set appropriate timeouts** based on service complexity
5. **Monitor build performance** and adjust limits accordingly
6. **Keep build logs** for troubleshooting

## Troubleshooting

**Builds timing out:**
- Increase build timeout
- Verify network connectivity
- Check Docker daemon resources
- Review build logs for bottlenecks

**Cache not working:**
- Verify BuildKit is enabled
- Check .dockerignore excludes build artifacts
- Ensure Dockerfile layers are ordered correctly
- Review Coolify cache settings

**Deployments failing:**
- Check health check endpoints
- Verify environment variables
- Review service dependencies
- Check resource limits

**Out of disk space:**
- Clean old images: `docker image prune -a`
- Reduce cache retention: `docker builder prune`
- Monitor disk usage: `docker system df`

## Next Steps

After optimizing build and deployment settings:
1. Monitor first deployment with new settings
2. Measure and record build times
3. Adjust resource limits if needed
4. Proceed to Task 228: Configure FastAPI service specifics
