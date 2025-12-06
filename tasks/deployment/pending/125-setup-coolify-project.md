# Task 224: Set Up Coolify Project and Services

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Set up the Smarter Team project in Coolify, create all service definitions (FastAPI, Celery worker, Celery beat, Redis, Next.js), and configure the service architecture for multi-container deployment.

## Prerequisites

- [ ] Coolify instance running and accessible
- [ ] Coolify admin credentials
- [ ] Domain name configured (optional but recommended)
- [ ] GitHub repository access
- [ ] Tasks 221-223 completed (Dockerfiles and docker-compose)

## Files to Create/Modify

- [ ] None (all configuration in Coolify UI)

## Implementation Checklist

### Phase 1: Create Project
- [ ] Log into Coolify dashboard
- [ ] Navigate to Projects
- [ ] Click "Create New Project"
- [ ] Set project name: `smarter-team`
- [ ] Add description: "Multi-agent AI agency automation system"
- [ ] Create project

### Phase 2: Add Git Repository
- [ ] Click "Add Resource" → "New Service"
- [ ] Select "GitHub" as source
- [ ] Authenticate with GitHub
- [ ] Select repository: `your-username/smarter-team`
- [ ] Set default branch: `main`
- [ ] Enable "Auto Deploy" on push
- [ ] Save repository configuration

### Phase 3: Create Redis Service
- [ ] Click "Add Resource" → "Database"
- [ ] Select "Redis"
- [ ] Service name: `smarter-team-redis`
- [ ] Version: `7-alpine`
- [ ] Memory limit: `256MB`
- [ ] Enable persistence: Yes
- [ ] Volume mount: `/data`
- [ ] Internal port: `6379`
- [ ] No external port (internal only)
- [ ] Save configuration

### Phase 4: Create FastAPI Backend Service
- [ ] Click "Add Resource" → "New Service"
- [ ] Service name: `smarter-team-backend`
- [ ] Build method: "Dockerfile"
- [ ] Dockerfile path: `app/backend/Dockerfile`
- [ ] Build context: `app/backend`
- [ ] Internal port: `8000`
- [ ] External port: `8000` (or custom)
- [ ] Health check path: `/health`
- [ ] Health check interval: `30s`
- [ ] Auto-restart: Enabled
- [ ] Save configuration

### Phase 5: Create Celery Worker Service
- [ ] Click "Add Resource" → "New Service"
- [ ] Service name: `smarter-team-worker`
- [ ] Build method: "Dockerfile"
- [ ] Dockerfile path: `app/backend/Dockerfile`
- [ ] Build context: `app/backend`
- [ ] Custom start command: `celery -A src.celery_app worker --loglevel=info --concurrency=4`
- [ ] No exposed ports (internal only)
- [ ] Health check: Custom command
- [ ] Health check command: `celery -A src.celery_app inspect ping`
- [ ] Auto-restart: Enabled
- [ ] Save configuration

### Phase 6: Create Celery Beat Service
- [ ] Click "Add Resource" → "New Service"
- [ ] Service name: `smarter-team-beat`
- [ ] Build method: "Dockerfile"
- [ ] Dockerfile path: `app/backend/Dockerfile`
- [ ] Build context: `app/backend`
- [ ] Custom start command: `celery -A src.celery_app beat --loglevel=info`
- [ ] No exposed ports (internal only)
- [ ] Auto-restart: Enabled
- [ ] Save configuration

### Phase 7: Create Next.js Frontend Service
- [ ] Click "Add Resource" → "New Service"
- [ ] Service name: `smarter-team-frontend`
- [ ] Build method: "Dockerfile"
- [ ] Dockerfile path: `app/frontend/Dockerfile`
- [ ] Build context: `app/frontend`
- [ ] Internal port: `3000`
- [ ] External port: `3000` (or 80/443 with reverse proxy)
- [ ] Health check path: `/api/health`
- [ ] Health check interval: `30s`
- [ ] Auto-restart: Enabled
- [ ] Save configuration

### Phase 8: Configure Service Dependencies
- [ ] Set backend to depend on Redis
- [ ] Set worker to depend on Redis and Backend
- [ ] Set beat to depend on Redis and Backend
- [ ] Set frontend to depend on Backend
- [ ] Verify startup order in deployment logs

## Service Configuration Summary

```yaml
# Service Architecture (for reference)
smarter-team-project/
├── smarter-team-redis (Database)
│   ├── Image: redis:7-alpine
│   ├── Internal Port: 6379
│   ├── Persistence: Enabled
│   └── Memory: 256MB
│
├── smarter-team-backend (API)
│   ├── Build: app/backend/Dockerfile
│   ├── Port: 8000
│   ├── Health: /health
│   └── Depends: redis
│
├── smarter-team-worker (Background Tasks)
│   ├── Build: app/backend/Dockerfile
│   ├── Command: celery worker
│   ├── No external port
│   └── Depends: redis, backend
│
├── smarter-team-beat (Scheduler)
│   ├── Build: app/backend/Dockerfile
│   ├── Command: celery beat
│   ├── No external port
│   └── Depends: redis, backend
│
└── smarter-team-frontend (Web UI)
    ├── Build: app/frontend/Dockerfile
    ├── Port: 3000
    ├── Health: /api/health
    └── Depends: backend
```

## Service URLs (Internal Coolify Network)

```bash
# Internal service discovery
REDIS_URL=redis://smarter-team-redis:6379/0
BACKEND_URL=http://smarter-team-backend:8000
FRONTEND_URL=http://smarter-team-frontend:3000

# External access (after domain setup)
https://api.smarter-team.com  # Backend
https://smarter-team.com      # Frontend
```

## Verification

### In Coolify Dashboard:

1. **Check all services are created:**
   - Navigate to project "smarter-team"
   - Verify 5 services listed
   - Verify Redis shows as "Database" type

2. **Check service status:**
   - All services should show "Stopped" (not yet deployed)
   - No errors in service configuration
   - Dependencies visible in service details

3. **Verify build settings:**
   - Backend: Dockerfile path correct
   - Worker: Custom command set
   - Beat: Custom command set
   - Frontend: Dockerfile path correct

4. **Check health check configuration:**
   - Backend: `/health` endpoint
   - Frontend: `/api/health` endpoint
   - Worker: Celery inspect command

## Notes

- **Service naming**: Use consistent prefix `smarter-team-*` for clarity
- **Dependencies**: Coolify handles startup order automatically
- **Internal networking**: Services communicate via service names
- **Health checks**: Enable Coolify to monitor and auto-restart
- **Auto-deploy**: Enabled for CI/CD workflow
- **Resource limits**: Set on per-service basis (task 231)

## Best Practices

1. **Use service names** for internal URLs (not localhost or IP)
2. **Enable health checks** for all user-facing services
3. **Set resource limits** to prevent memory/CPU exhaustion
4. **Use persistent volumes** for Redis and databases
5. **Enable auto-restart** for resilience
6. **Configure logging** for debugging

## Next Steps

After completing this task:
1. Proceed to Task 225: Configure environment variables
2. Then Task 226: Set up Git repository connection
3. Then deploy and test services

## Coolify Dashboard Screenshots Needed

For documentation:
- [ ] Project overview page
- [ ] Service list view
- [ ] Individual service configuration
- [ ] Service dependency graph (if available)

## Common Issues

**Services don't start in order:**
- Solution: Configure dependencies in service settings
- Coolify will wait for dependencies to be healthy

**Cannot access services internally:**
- Solution: Use service names, not localhost
- Example: `redis://smarter-team-redis:6379/0`

**Build fails:**
- Solution: Verify Dockerfile paths are correct
- Check build context is set properly

**Health check fails:**
- Solution: Verify endpoint exists and returns 200
- Check service is actually listening on configured port
