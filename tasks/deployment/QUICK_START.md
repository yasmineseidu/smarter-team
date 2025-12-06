# Coolify Deployment Quick Start Guide

**For:** Smarter Team Multi-Agent System
**Target:** Coolify Self-Hosted PaaS
**Total Tasks:** 19 (221-239)

## Prerequisites

Before starting:
- [ ] Coolify instance installed and accessible
- [ ] Domain name registered (e.g., smarter-team.com)
- [ ] DNS access for domain configuration
- [ ] GitHub repository ready
- [ ] All API keys ready (Anthropic, Supabase, etc.)

## Quick Deployment Path

### Phase 1: Local Docker Testing (1-2 hours)
```bash
# Tasks 221-223
1. Create app/backend/Dockerfile (Task 221)
2. Create app/frontend/Dockerfile (Task 222)
3. Create docker-compose.yml (Task 223)
4. Test locally: docker-compose up -d
5. Verify all services healthy
```

### Phase 2: Coolify Configuration (2-3 hours)
```bash
# Tasks 224-227
1. Create Coolify project "smarter-team" (Task 224)
2. Add all 5 services (Backend, Worker, Beat, Redis, Frontend)
3. Configure environment variables (Task 225)
4. Connect Git repository (Task 226)
5. Optimize build settings (Task 227)
```

### Phase 3: Service Setup (2-3 hours)
```bash
# Tasks 228-231
1. Configure FastAPI with health checks (Task 228)
2. Configure Celery worker and beat (Task 229)
3. Configure Redis service (Task 230)
4. Configure Next.js frontend (Task 231)
5. Deploy and verify all services
```

### Phase 4: Automation (1-2 hours)
```bash
# Tasks 232-234
1. Set up GitHub Actions (Task 232)
2. Configure webhooks (Task 233)
3. Create staging environment (Task 234)
4. Test auto-deployment
```

### Phase 5: Production Ready (2-3 hours)
```bash
# Tasks 235-237
1. Implement health endpoints (Task 235)
2. Set up logging/monitoring (Task 236)
3. Configure alerts (Task 237)
```

### Phase 6: Go Live (1-2 hours)
```bash
# Tasks 238-239
1. Configure domain and SSL (Task 238)
2. Set up CORS and security (Task 239)
3. Run security audit
4. ✓ PRODUCTION READY
```

## Critical Commands

### Build and Test Locally
```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Test health checks
curl http://localhost:8000/health
curl http://localhost:3000/api/health

# Stop all services
docker-compose down
```

### Coolify Deployment
```bash
# Trigger manual deployment
curl -X POST https://coolify.your-domain.com/webhooks/deploy/service-id

# Check service status (in Coolify UI)
# Navigate to: Project → Services → Status

# View logs (in Coolify UI)
# Navigate to: Service → Logs
```

### Health Checks
```bash
# Production endpoints
curl https://api.smarter-team.com/health
curl https://api.smarter-team.com/health/ready
curl https://api.smarter-team.com/health/detailed
curl https://smarter-team.com/api/health
```

### Troubleshooting
```bash
# SSH into Coolify server
ssh user@coolify-server

# Check running containers
docker ps

# View container logs
docker logs smarter-team-backend
docker logs smarter-team-worker
docker logs smarter-team-frontend

# Restart service
docker restart smarter-team-backend

# Check resource usage
docker stats

# Clean up old images
docker image prune -a
```

## Service URLs

### Internal (Docker Network)
```
Backend:  http://smarter-team-backend:8000
Frontend: http://smarter-team-frontend:3000
Redis:    redis://smarter-team-redis:6379/0
```

### External (Production)
```
Frontend: https://smarter-team.com
Backend:  https://api.smarter-team.com
API Docs: https://api.smarter-team.com/docs (staging only)
```

## Environment Variables Quick Reference

### Minimal Setup (Required)
```bash
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://smarter-team-redis:6379/0
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://smarter-team.com
NEXT_PUBLIC_API_URL=https://api.smarter-team.com
```

### Full Setup (See Task 225)
40+ environment variables for all integrations

## Service Configuration Summary

| Service | Replicas | CPU | Memory | Port | Health Check |
|---------|----------|-----|--------|------|--------------|
| Backend | 2 | 2.0 | 2GB | 8000 | /health |
| Worker | 2 | 2.0 | 2GB | - | celery inspect |
| Beat | 1* | 0.5 | 512MB | - | process check |
| Frontend | 2 | 2.0 | 2GB | 3000 | /api/health |
| Redis | 1 | 1.0 | 512MB | 6379 | redis-cli ping |

*CRITICAL: Beat must be exactly 1 replica (scheduler singleton)

## Deployment Checklist

### Pre-Deployment
- [ ] All tasks 221-223 completed (Docker configs)
- [ ] Local docker-compose test successful
- [ ] All API keys ready
- [ ] Domain DNS configured

### During Deployment
- [ ] Coolify project created (Task 224)
- [ ] Environment variables configured (Task 225)
- [ ] Git repository connected (Task 226)
- [ ] All services deployed and healthy
- [ ] Health checks passing

### Post-Deployment
- [ ] Frontend accessible via HTTPS
- [ ] Backend API responding
- [ ] CORS working
- [ ] SSL certificate valid (A+ rating)
- [ ] Security headers present (A+ rating)
- [ ] Alerts configured
- [ ] Monitoring active

## Common Pitfalls

1. **Beat replicas > 1**: Will cause duplicate scheduled tasks
2. **Missing CORS origins**: Frontend can't call backend
3. **Wrong Redis URL**: Use internal service name, not localhost
4. **Secrets in Git**: Use Coolify secret management
5. **Health check timeout**: Increase grace period for slow starts
6. **Build timeout**: Increase for large projects
7. **Resource limits too low**: Services crash or restart frequently

## Emergency Rollback

```bash
# In Coolify UI
1. Navigate to service
2. Click "Deployments" tab
3. Find previous working version
4. Click "Redeploy"

# Via CLI (on Coolify server)
docker tag smarter-team-backend:previous smarter-team-backend:latest
docker restart smarter-team-backend
```

## Support

**Task Files Location:**
`/Users/yasmineseidu/Desktop/Coding/smarter-team/tasks/deployment/pending/task-*.md`

**Summary Document:**
`/Users/yasmineseidu/Desktop/Coding/smarter-team/tasks/deployment/DEPLOYMENT_TASKS_SUMMARY.md`

**Next Task:** Start with Task 221 (Create FastAPI Dockerfile)

---

**Estimated Total Time:** 10-15 hours
**Difficulty:** Medium-High
**Production Ready:** Yes

Follow tasks sequentially for best results. Each task includes detailed implementation steps, verification commands, and troubleshooting guides.
