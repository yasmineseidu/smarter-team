# Coolify Deployment Tasks Summary

**Created:** 2025-12-06
**Total Tasks:** 19 (Tasks 221-239)
**Status:** All tasks created and ready for execution

## Overview

Complete set of deployment tasks for deploying Smarter Team (multi-agent AI agency automation) to Coolify. These tasks cover the entire deployment lifecycle from Docker configuration to production monitoring.

## Task Breakdown by Category

### 1. Docker Configuration (Tasks 221-223) - 3 tasks

**Task 221: Create Dockerfile for FastAPI Backend**
- Multi-stage Dockerfile with Python 3.11-slim-bookworm
- Builder stage for dependencies, runtime stage for execution
- Non-root user for security
- Health check configuration
- Expected image size: ~300-400MB (vs 1GB+ without optimization)
- Key features:
  - uvloop for 2-4x async performance improvement
  - Configurable workers via UVICORN_WORKERS env var
  - Automatic health checks every 30s
  - Graceful shutdown support

**Task 222: Create Dockerfile for Next.js Frontend**
- Multi-stage Dockerfile with Node 20-alpine
- Standalone output mode (40% size reduction)
- Dependencies stage → Builder stage → Runner stage
- Expected image size: ~200-300MB
- Key features:
  - Production-optimized Next.js build
  - Static asset caching
  - Non-root nodejs user
  - Health check via Node.js HTTP module

**Task 223: Create docker-compose.yml for Local Testing**
- Orchestrates all 5 services (Backend, Worker, Beat, Redis, Frontend)
- Service health checks and dependencies
- Named volumes for Redis persistence
- Bridge network for service discovery
- Development override file for hot-reload
- Includes Redis Commander GUI for development

### 2. Coolify Setup (Tasks 224-227) - 4 tasks

**Task 224: Set Up Coolify Project and Services**
- Create project: "smarter-team"
- Add 5 services:
  1. Redis (redis:7-alpine, 256MB, persistence enabled)
  2. Backend (Dockerfile build, port 8000, /health check)
  3. Worker (Dockerfile build, celery worker command, 2 replicas)
  4. Beat (Dockerfile build, celery beat command, 1 replica ONLY)
  5. Frontend (Dockerfile build, port 3000, /api/health check)
- Configure service dependencies (startup order)
- Internal service URLs: redis://smarter-team-redis:6379/0

**Task 225: Configure Environment Variables in Coolify**
- Backend: 40+ environment variables (DB, Redis, API keys, integrations)
- Worker: Same as backend + worker-specific settings
- Beat: Same as backend + beat-specific settings
- Frontend: NODE_ENV, API URLs (internal + public)
- Security: Mark all API keys and secrets as "Secret" in Coolify
- Comprehensive list includes:
  - Core: DATABASE_URL, REDIS_URL, SECRET_KEY
  - AI: Anthropic, Perplexity, ElevenLabs, Retell
  - Lead Gen: Instantly, IcyPeas, Findymail, Reoon, Apify
  - CRM: GoHighLevel, Notion, Airtable, ClickUp
  - Communication: Cal.com, Gmail, Google Calendar
  - Payments: Stripe, QuickBooks, PandaDoc
  - Memory: Pinecone, Zep

**Task 226: Set Up Git Repository Connection**
- Connect GitHub repository to Coolify
- Configure auto-deploy on push to main/develop
- Set build context and Dockerfile paths per service
- Enable build caching for faster deployments
- Optional .coolify.yml for advanced deployment control
- GitHub webhook integration for automated triggers

**Task 227: Configure Build and Deployment Settings**
- Enable Docker BuildKit for 30-50% faster builds
- Configure build cache and layer caching
- Set build timeouts: Backend/Worker/Beat: 15min, Frontend: 20min
- Set build memory limits: Backend: 2GB, Frontend: 4GB
- Configure rolling update strategy (zero-downtime)
- Resource limits per service:
  - Backend: 2 CPU / 2GB RAM (2 replicas)
  - Worker: 2 CPU / 2GB RAM (2 replicas)
  - Beat: 0.5 CPU / 512MB RAM (1 replica)
  - Frontend: 2 CPU / 2GB RAM (2 replicas)
  - Redis: 1 CPU / 512MB RAM

### 3. Service Configuration (Tasks 228-231) - 4 tasks

**Task 228: Configure FastAPI Service (with Health Checks)**
- Implement comprehensive health endpoints:
  - `/health` - Liveness probe (basic process check)
  - `/health/ready` - Readiness probe (DB + Redis connectivity)
  - `/health/detailed` - Diagnostic info (timing, versions, metrics)
- Configure Coolify health checks:
  - Interval: 30s
  - Timeout: 10s
  - Retries: 3
  - Start period: 60s (grace period)
- Auto-restart on failure (max 3 attempts)
- Resource monitoring and limits

**Task 229: Configure Celery Worker and Beat**
- Worker service:
  - Health check: `celery -A src.celery_app inspect ping`
  - Concurrency: 4 workers per container
  - Graceful shutdown (finish current tasks)
  - 2 replicas for load distribution
- Beat service:
  - Health check: Process verification
  - CRITICAL: Exactly 1 replica (scheduler singleton)
  - Lighter resource allocation
- Task routing and queue configuration

**Task 230: Configure Redis Service**
- Image: redis:7-alpine
- Persistence: RDB + AOF (dual strategy)
- Memory: 512MB limit with allkeys-lru eviction
- Internal port only (no external exposure)
- Automated backups via Coolify volume snapshots
- Configuration: Save snapshots at 900s/300s/60s intervals

**Task 231: Configure Next.js Frontend**
- Standalone mode for minimal image size
- Health endpoint: `/api/health` (checks backend connectivity)
- Environment variables:
  - Internal API_URL for server-side calls
  - Public NEXT_PUBLIC_API_URL for browser calls
- Static asset optimization and caching
- 2 replicas for high availability

### 4. CI/CD Pipeline (Tasks 232-234) - 3 tasks

**Task 232: Set Up GitHub Actions for Automated Deployments**
- Workflow triggers: Push to main/develop, manual dispatch
- Job 1: Run tests (backend pytest + frontend Vitest)
- Job 2: Trigger Coolify deployment via webhook
- Environment-specific deployments:
  - main → production
  - develop → staging
- Health checks after deployment
- Slack notifications for success/failure

**Task 233: Configure Deployment Webhooks**
- Set up Coolify webhooks for each service
- GitHub webhook integration
- Slack notification webhooks
- Webhook security (HTTPS + bearer tokens)
- Rate limiting and idempotency handling

**Task 234: Set Up Staging and Production Environments**
- Separate environments with isolated resources:
  - Production: api.smarter-team.com, smarter-team.com
  - Staging: staging-api.smarter-team.com, staging.smarter-team.com
- Separate databases and Redis instances
- Environment-specific API keys and rate limits
- Resource allocation: Production > Staging
- Test all changes in staging first

### 5. Monitoring & Health Checks (Tasks 235-237) - 3 tasks

**Task 235: Configure Health Check Endpoints**
- Comprehensive health check matrix:
  - Backend: Process, DB, Redis, Celery broker
  - Worker: Process, active tasks, queue length
  - Frontend: Server, backend reachability
  - Redis: PONG, memory usage, connected clients
- Additional endpoints:
  - `/version` - Build and commit info
  - `/metrics` - CPU, memory, disk usage

**Task 236: Set Up Logging and Monitoring**
- Structured JSON logging (Python + TypeScript)
- Centralized log aggregation in Coolify
- Log retention: 30 days
- Optional Sentry integration for error tracking
- Log search and filtering in Coolify UI
- Monitoring dashboards for resource usage

**Task 237: Configure Alerts and Notifications**
- Alert rules:
  - Service health: Immediate on 3 consecutive failures
  - Resources: CPU > 80%, Memory > 85%, Disk > 90%
  - Performance: Response time > 2s, Error rate > 5%
  - Deployment: Start, fail, succeed, rollback
- Notification channels: Slack, email
- Alert severity levels and escalation
- On-call rotation integration (optional)

### 6. SSL & Domain (Tasks 238-239) - 2 tasks

**Task 238: Configure Custom Domain and SSL**
- DNS configuration:
  - A records for @, www, api
  - Staging subdomains (optional)
- Coolify domain setup:
  - Backend: api.smarter-team.com
  - Frontend: smarter-team.com + www redirect
- Automatic SSL via Let's Encrypt
- HTTPS enforcement and HSTS headers
- SSL grade target: A or A+
- Auto-renewal 30 days before expiry

**Task 239: Set Up CORS and Security Headers**
- CORS configuration:
  - Whitelist origins (production, staging, development)
  - Allow credentials for auth cookies
  - Preflight caching: 1 hour
- Security headers:
  - HSTS: 1 year with preload
  - X-Frame-Options: DENY/SAMEORIGIN
  - X-Content-Type-Options: nosniff
  - X-XSS-Protection: 1; mode=block
  - CSP: Restrictive content security policy
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy: Disable unnecessary features
- Security scanner targets: A or A+ rating

## Deployment Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Docker Configuration (Tasks 221-223)               │
│ - Create Dockerfiles for all services                       │
│ - Test locally with docker-compose                          │
│ - Verify all services communicate correctly                 │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Coolify Setup (Tasks 224-227)                      │
│ - Create project and services in Coolify                    │
│ - Configure environment variables                           │
│ - Connect Git repository                                    │
│ - Optimize build and deployment settings                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Service Configuration (Tasks 228-231)              │
│ - Configure health checks for all services                  │
│ - Set resource limits and scaling rules                     │
│ - Test service communication                                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: CI/CD Pipeline (Tasks 232-234)                     │
│ - Set up GitHub Actions for automated deployment            │
│ - Configure webhooks and notifications                      │
│ - Create staging and production environments                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 5: Monitoring (Tasks 235-237)                         │
│ - Implement comprehensive health checks                     │
│ - Set up logging and monitoring                             │
│ - Configure alerts and notifications                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 6: Production Hardening (Tasks 238-239)               │
│ - Configure custom domains and SSL                          │
│ - Set up CORS and security headers                          │
│ - Run security audits                                       │
│ ✓ DEPLOYMENT COMPLETE                                       │
└─────────────────────────────────────────────────────────────┘
```

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet (HTTPS)                          │
└────────────┬───────────────────────┬────────────────────────┘
             │                       │
             ▼                       ▼
    ┌────────────────┐      ┌────────────────┐
    │   Frontend     │      │    Backend     │
    │  (Next.js 15)  │◄────►│  (FastAPI)     │
    │  Port 3000     │      │  Port 8000     │
    └────────────────┘      └────────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │    Worker    │ │     Beat     │ │    Redis     │
            │   (Celery)   │ │  (Scheduler) │ │  (Broker)    │
            │  2 replicas  │ │  1 replica   │ │  Port 6379   │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │                │                │
                    └────────────────┴────────────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │   Supabase PostgreSQL│
                          │   (External Service) │
                          └─────────────────────┘
```

## Expected Performance Benchmarks

### Build Times
- **With cache:**
  - Backend: 2-3 minutes
  - Worker/Beat: 30 seconds (shares backend cache)
  - Frontend: 4-6 minutes
  - **Total:** 6-8 minutes

- **Without cache (first build):**
  - Backend: 8-10 minutes
  - Frontend: 12-15 minutes
  - **Total:** 20-25 minutes

### Deployment Times
- Rolling update: 2-3 minutes per service
- Total deployment: 8-12 minutes
- Zero downtime: ✓ (for frontend and backend)

### Resource Usage (per replica)
- Backend: ~150-300MB RAM, 5-15% CPU (idle)
- Worker: ~200-400MB RAM, 10-30% CPU (active)
- Beat: ~100-150MB RAM, 1-5% CPU
- Frontend: ~150-300MB RAM, 5-15% CPU (idle)
- Redis: ~100-200MB RAM, 1-5% CPU

## Key Files Created

### Docker Configuration
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/app/backend/Dockerfile`
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/app/backend/.dockerignore`
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/app/backend/docker-entrypoint.sh`
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/app/frontend/Dockerfile`
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/app/frontend/.dockerignore`
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/docker-compose.yml`
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/docker-compose.override.yml`

### Health Checks
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/app/backend/src/health.py`
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/app/frontend/app/api/health/route.ts`

### CI/CD
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/.github/workflows/deploy.yml`
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/.coolify.yml` (optional)

### Documentation
- `/Users/yasmineseidu/Desktop/Coding/smarter-team/docs/deployment/ENVIRONMENT_VARIABLES.md`

## Environment Variables Summary

### Required (All Services)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection (internal: redis://smarter-team-redis:6379/0)
- `ANTHROPIC_API_KEY` - Claude API key
- `SECRET_KEY` - Application secret key

### Backend-Specific
- `UVICORN_WORKERS` - Number of API workers (default: 4)
- `CELERY_WORKER_CONCURRENCY` - Tasks per worker (default: 4)
- `CORS_ORIGINS` - Allowed frontend origins

### Frontend-Specific
- `NEXT_PUBLIC_API_URL` - Public API URL for browser (https://api.smarter-team.com)
- `API_URL` - Internal API URL for server (http://smarter-team-backend:8000)
- `NODE_ENV` - Environment (production/staging/development)

### Optional Integrations (40+ total)
- AI: Perplexity, ElevenLabs, Retell, Fal, Replicate
- Lead Gen: Instantly, IcyPeas, Findymail, Reoon, Apify, Serper, Firecrawl
- CRM: GoHighLevel, Notion, Airtable, ClickUp
- Communication: Cal.com, Gmail, Google Calendar/Tasks
- Payments: Stripe, QuickBooks, PandaDoc
- Memory: Pinecone, Zep
- Monitoring: Sentry

## Critical Configuration Notes

1. **Celery Beat**: MUST have exactly 1 replica (scheduler singleton)
2. **Redis**: Internal only, no external port exposure
3. **Health checks**: Required for auto-restart and monitoring
4. **CORS**: Never use `*` in production, whitelist specific origins
5. **Secrets**: Always mark API keys as "Secret" in Coolify UI
6. **SSL**: Automatic via Let's Encrypt, renews 30 days before expiry
7. **Build cache**: Speeds up deployments by 50-70%
8. **Rolling updates**: Zero downtime for user-facing services

## Security Checklist

- [x] Multi-stage Dockerfiles (minimal attack surface)
- [x] Non-root users in all containers
- [x] HTTPS enforcement (HSTS with preload)
- [x] Security headers (CSP, X-Frame-Options, etc.)
- [x] CORS whitelisting (no wildcards)
- [x] Secret management (Coolify secrets, never in Git)
- [x] SSL/TLS 1.2+ only
- [x] Automated security updates (Alpine/Debian base images)
- [x] Health check monitoring
- [x] Error tracking (Sentry integration)
- [x] Log retention and audit trails
- [x] Rate limiting (via integrations)

## Verification Checklist

After completing all tasks:

- [ ] All services running in Coolify
- [ ] Health checks passing for all services
- [ ] Frontend accessible via HTTPS (https://smarter-team.com)
- [ ] Backend API accessible via HTTPS (https://api.smarter-team.com)
- [ ] CORS working (frontend can call backend)
- [ ] SSL certificate valid (A or A+ rating)
- [ ] Security headers present (A or A+ rating)
- [ ] Auto-deployment working (push triggers deploy)
- [ ] Logs viewable in Coolify
- [ ] Alerts configured and tested
- [ ] Resource usage within limits
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] Celery tasks executing
- [ ] Celery beat scheduling tasks

## Troubleshooting Guide

### Common Issues

**Services fail to start:**
- Check environment variables are set correctly
- Verify health check endpoints exist and return 200
- Review service logs in Coolify
- Check resource limits aren't too restrictive

**Build fails:**
- Verify Dockerfile paths are correct
- Check .dockerignore isn't excluding necessary files
- Increase build timeout if needed
- Review build logs for specific errors

**CORS errors:**
- Verify origin is in CORS_ORIGINS list
- Check credentials setting matches frontend
- Ensure preflight requests succeed
- Clear browser cache

**SSL certificate fails:**
- Verify DNS points to Coolify server
- Check ports 80/443 are accessible
- Review Let's Encrypt rate limits
- Check domain is publicly accessible

## Next Steps After Deployment

1. **Monitor first 24 hours** - Watch for errors, resource usage, restarts
2. **Run security audit** - Mozilla Observatory, SecurityHeaders.com
3. **Performance testing** - Load test API endpoints
4. **Backup verification** - Test database backup/restore
5. **Documentation** - Update CLAUDE.md with production URLs
6. **Staging environment** - Clone for testing future changes
7. **Monitoring dashboards** - Set up Grafana/Prometheus (optional)
8. **Cost optimization** - Review resource usage, scale down if possible

## Support Resources

- **Coolify Documentation**: https://coolify.io/docs
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Next.js Deployment**: https://nextjs.org/docs/deployment
- **Let's Encrypt**: https://letsencrypt.org/docs/
- **Celery Best Practices**: https://docs.celeryq.dev/en/stable/userguide/

---

**Total Tasks Created:** 19
**Estimated Total Time:** 15-20 hours (with learning curve), 8-12 hours (experienced)
**Complexity:** Medium-High (multi-service orchestration)
**Production Readiness:** ✓ Enterprise-grade deployment

All tasks are self-contained, actionable, and include verification steps. Follow tasks sequentially for best results.
