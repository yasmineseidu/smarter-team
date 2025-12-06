# Task 225: Configure Environment Variables in Coolify

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure all required environment variables for each service in Coolify, including API keys, database URLs, Redis connections, and service-specific settings. Implement secure secret management and environment-specific configurations.

## Prerequisites

- [ ] Task 224 completed (Coolify project and services created)
- [ ] All API keys and credentials ready
- [ ] Supabase database URL available
- [ ] Domain names configured (if using custom domains)

## Files to Create/Modify

- [ ] None (all configuration in Coolify UI)
- [ ] `.env.example` (update in repository)
- [ ] `docs/deployment/ENVIRONMENT_VARIABLES.md` (documentation)

## Implementation Checklist

### Phase 1: Configure Backend Service Variables
- [ ] Navigate to `smarter-team-backend` service
- [ ] Click "Environment Variables"
- [ ] Add all required backend variables
- [ ] Mark sensitive variables as "Secret"
- [ ] Test variable interpolation

### Phase 2: Configure Worker Service Variables
- [ ] Navigate to `smarter-team-worker` service
- [ ] Add same variables as backend (shared config)
- [ ] Verify Redis URL uses internal service name
- [ ] Test Celery connection

### Phase 3: Configure Beat Service Variables
- [ ] Navigate to `smarter-team-beat` service
- [ ] Add same variables as backend/worker
- [ ] Verify scheduler can access Redis

### Phase 4: Configure Frontend Service Variables
- [ ] Navigate to `smarter-team-frontend` service
- [ ] Add frontend-specific variables
- [ ] Set backend URL to internal service name
- [ ] Configure public API URL for browser

### Phase 5: Configure Redis (if needed)
- [ ] Redis typically needs no environment variables
- [ ] Verify persistence is enabled
- [ ] Set memory limit if needed

## Configuration Details

### Backend Environment Variables

```bash
# ============================================
# CORE CONFIGURATION
# ============================================
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-secure-random-key>
LOG_LEVEL=info

# ============================================
# DATABASE
# ============================================
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# ============================================
# REDIS (Internal Coolify Network)
# ============================================
REDIS_URL=redis://smarter-team-redis:6379/0

# ============================================
# CELERY
# ============================================
CELERY_BROKER_URL=redis://smarter-team-redis:6379/0
CELERY_RESULT_BACKEND=redis://smarter-team-redis:6379/1
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=3600
CELERY_TASK_SOFT_TIME_LIMIT=3300

# ============================================
# UVICORN
# ============================================
UVICORN_WORKERS=4
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000

# ============================================
# CORS
# ============================================
CORS_ORIGINS=https://smarter-team.com,https://www.smarter-team.com
CORS_ALLOW_CREDENTIALS=true

# ============================================
# AI SERVICES
# ============================================
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
ELEVENLABS_API_KEY=...
RETELL_API_KEY=...

# ============================================
# LEAD GENERATION & DATA
# ============================================
INSTANTLY_API_KEY=...
ICYPEAS_API_KEY=...
FINDYMAIL_API_KEY=...
REOON_API_KEY=...
APIFY_API_KEY=...
SERPER_API_KEY=...
FIRECRAWL_API_KEY=...

# ============================================
# CRM & PRODUCTIVITY
# ============================================
GOHIGHLEVEL_API_KEY=...
NOTION_API_KEY=...
AIRTABLE_API_KEY=...
CLICKUP_API_KEY=...

# ============================================
# COMMUNICATION
# ============================================
CAL_COM_API_KEY=...
GMAIL_CREDENTIALS_JSON=...
GOOGLE_CALENDAR_CREDENTIALS=...

# ============================================
# PAYMENTS & DOCUMENTS
# ============================================
STRIPE_API_KEY=sk_live_...
QUICKBOOKS_CLIENT_ID=...
QUICKBOOKS_CLIENT_SECRET=...
PANDADOC_API_KEY=...

# ============================================
# MEMORY & VECTOR DB
# ============================================
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=smarter-team-prod
ZEP_API_KEY=...
ZEP_API_URL=https://api.getzep.com

# ============================================
# MONITORING (Optional)
# ============================================
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Worker Environment Variables

```bash
# Same as backend - workers need access to all integrations
# Copy all backend environment variables
# Plus worker-specific:

CELERY_WORKER_PREFETCH_MULTIPLIER=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
CELERY_WORKER_LOG_FORMAT=[%(asctime)s: %(levelname)s/%(processName)s] %(message)s
```

### Beat Environment Variables

```bash
# Same as backend/worker - beat needs to schedule tasks
# Copy all backend environment variables
# Plus beat-specific:

CELERY_BEAT_SCHEDULE_FILENAME=/tmp/celerybeat-schedule
CELERY_BEAT_MAX_LOOP_INTERVAL=5
```

### Frontend Environment Variables

```bash
# ============================================
# NEXT.JS CONFIGURATION
# ============================================
NODE_ENV=production
PORT=3000
NEXT_TELEMETRY_DISABLED=1

# ============================================
# API CONFIGURATION
# ============================================
# Internal (server-side)
API_URL=http://smarter-team-backend:8000

# Public (browser-side)
NEXT_PUBLIC_API_URL=https://api.smarter-team.com

# ============================================
# FEATURE FLAGS (Optional)
# ============================================
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_CHAT=true
```

## Coolify-Specific Configuration

### Setting Variables in Coolify UI

1. **Navigate to service** (e.g., `smarter-team-backend`)
2. **Click "Environment Variables"** tab
3. **Add variables** using one of these methods:

   **Method 1: Individual Entry**
   - Click "+ Add Variable"
   - Key: `ANTHROPIC_API_KEY`
   - Value: `sk-ant-...`
   - Toggle "Secret" (hides value in UI)
   - Click "Save"

   **Method 2: Bulk Import**
   - Click "Bulk Edit"
   - Paste all variables (KEY=VALUE format)
   - Click "Save"

4. **Mark sensitive variables as secrets**:
   - API keys
   - Database passwords
   - SECRET_KEY
   - OAuth credentials

### Variable Precedence

Coolify environment variables override Dockerfile ENV:
1. Coolify UI variables (highest priority)
2. .env file in repository (if present)
3. Dockerfile ENV statements (lowest priority)

## Verification

### Test Backend Variables

```bash
# SSH into Coolify server
ssh user@coolify-server

# Check backend container environment
docker exec -it smarter-team-backend env | grep ANTHROPIC_API_KEY
docker exec -it smarter-team-backend env | grep DATABASE_URL
docker exec -it smarter-team-backend env | grep REDIS_URL

# Test database connection
docker exec -it smarter-team-backend python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.environ['DATABASE_URL'])
print('Database connected:', engine.connect())
"

# Test Redis connection
docker exec -it smarter-team-backend python -c "
import redis
import os
r = redis.from_url(os.environ['REDIS_URL'])
print('Redis ping:', r.ping())
"

# Test Anthropic API
docker exec -it smarter-team-backend python -c "
import os
from anthropic import Anthropic
client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
print('Anthropic client initialized')
"
```

### Test Worker Variables

```bash
# Check worker can connect to Redis
docker exec -it smarter-team-worker celery -A src.celery_app inspect ping

# Check worker sees environment
docker exec -it smarter-team-worker env | grep CELERY_
```

### Test Frontend Variables

```bash
# Check Next.js environment
docker exec -it smarter-team-frontend env | grep NEXT_PUBLIC_

# Test frontend can reach backend
docker exec -it smarter-team-frontend curl http://smarter-team-backend:8000/health
```

## Security Best Practices

1. **Never commit real secrets** to repository
2. **Use Coolify's secret management** for sensitive values
3. **Rotate secrets regularly** (quarterly)
4. **Use different keys** for staging and production
5. **Limit variable visibility** to necessary services
6. **Audit access logs** for environment variable views

## Documentation

Create `docs/deployment/ENVIRONMENT_VARIABLES.md`:

```markdown
# Environment Variables Reference

## Required Variables

### All Environments
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ANTHROPIC_API_KEY`: Claude API key
- `SECRET_KEY`: Application secret key

### Production Only
- `SENTRY_DSN`: Error tracking
- `STRIPE_API_KEY`: Payment processing

## Optional Variables

### Feature Flags
- `ENABLE_ANALYTICS`: Enable user analytics (default: false)
- `ENABLE_CHAT`: Enable chat features (default: true)

## Setting Variables

### Local Development
Copy `.env.example` to `.env` and fill in values.

### Coolify Deployment
Set in Coolify UI under service → Environment Variables.

## Variable Naming

- `NEXT_PUBLIC_*`: Exposed to browser (Next.js)
- `*_API_KEY`: Third-party API credentials
- `*_URL`: Service URLs and endpoints
```

## Notes

- **Internal URLs**: Use service names (e.g., `smarter-team-redis:6379`)
- **External URLs**: Use public domains (e.g., `https://api.smarter-team.com`)
- **Secrets**: Always mark as "Secret" in Coolify
- **CORS**: Must include all frontend domains
- **Database**: Use connection pooling for multi-worker setup

## Common Issues

**Backend can't connect to Redis:**
- Verify `REDIS_URL=redis://smarter-team-redis:6379/0`
- Check Redis service is running
- Verify both services are in same network

**Frontend can't reach backend:**
- Internal: Use `http://smarter-team-backend:8000`
- Browser: Use `NEXT_PUBLIC_API_URL=https://api.smarter-team.com`

**Variables not updating:**
- Restart service after changing variables
- Check Coolify logs for build errors
- Verify variable syntax (no spaces around =)

**Secrets visible in logs:**
- Never log sensitive variables
- Use Coolify's secret management
- Redact secrets in Sentry/monitoring
