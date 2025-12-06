# Task 226: Set Up Git Repository Connection

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure Git repository integration with Coolify for automated deployments on push, set up branch-based deployment strategies, and configure build triggers for the Smarter Team multi-service application.

## Prerequisites

- [ ] Task 224 completed (Coolify project created)
- [ ] Task 225 completed (Environment variables configured)
- [ ] GitHub repository accessible
- [ ] SSH keys or GitHub App configured in Coolify

## Files to Create/Modify

- [ ] `.coolify.yml` (optional deployment configuration)
- [ ] `.github/workflows/deploy.yml` (CI/CD integration)

## Implementation Checklist

### Phase 1: Configure Git Source
- [ ] Navigate to Coolify → Settings → Sources
- [ ] Add GitHub as source (if not already added)
- [ ] Authenticate with GitHub (OAuth or SSH)
- [ ] Grant repository access
- [ ] Test connection

### Phase 2: Connect Repository to Services
- [ ] For each service (backend, worker, beat, frontend):
  - [ ] Navigate to service settings
  - [ ] Click "Source" section
  - [ ] Select repository
  - [ ] Set branch (main for production, develop for staging)
  - [ ] Set build context path
  - [ ] Set Dockerfile path
  - [ ] Enable "Auto Deploy on Push"

### Phase 3: Configure Build Settings
- [ ] Set build arguments (if needed)
- [ ] Configure build timeout (increase for large builds)
- [ ] Set up build caching
- [ ] Test manual deployment

### Phase 4: Set Up Deployment Branches
- [ ] Configure `main` branch for production
- [ ] Configure `develop` branch for staging (if applicable)
- [ ] Set up preview deployments for PRs (optional)

## Configuration Details

### Git Source Configuration

**In Coolify UI:**

1. **Settings → Sources → Add Source**
   - Source type: GitHub
   - Authentication: GitHub App (recommended) or OAuth
   - Name: `github-smarter-team`

2. **Grant Repository Access**
   - Select `your-username/smarter-team`
   - Grant read access to repository
   - Grant webhook permissions

### Service-Specific Git Configuration

**Backend Service (`smarter-team-backend`):**
```yaml
Repository: your-username/smarter-team
Branch: main
Build Context: ./app/backend
Dockerfile: ./app/backend/Dockerfile
Auto Deploy: Enabled
Deploy on Push: true
```

**Worker Service (`smarter-team-worker`):**
```yaml
Repository: your-username/smarter-team
Branch: main
Build Context: ./app/backend
Dockerfile: ./app/backend/Dockerfile
Start Command: celery -A src.celery_app worker --loglevel=info --concurrency=4
Auto Deploy: Enabled
Deploy on Push: true
```

**Beat Service (`smarter-team-beat`):**
```yaml
Repository: your-username/smarter-team
Branch: main
Build Context: ./app/backend
Dockerfile: ./app/backend/Dockerfile
Start Command: celery -A src.celery_app beat --loglevel=info
Auto Deploy: Enabled
Deploy on Push: true
```

**Frontend Service (`smarter-team-frontend`):**
```yaml
Repository: your-username/smarter-team
Branch: main
Build Context: ./app/frontend
Dockerfile: ./app/frontend/Dockerfile
Auto Deploy: Enabled
Deploy on Push: true
```

### Optional: .coolify.yml Configuration

Create `.coolify.yml` in repository root for advanced deployment control:

```yaml
version: '1.0'

services:
  backend:
    build:
      context: ./app/backend
      dockerfile: Dockerfile
    deploy:
      restart_policy: unless-stopped
      replicas: 2
      health_check:
        path: /health
        interval: 30s
        timeout: 10s
    environment:
      - ENVIRONMENT=production

  worker:
    build:
      context: ./app/backend
      dockerfile: Dockerfile
    command: celery -A src.celery_app worker --loglevel=info --concurrency=4
    deploy:
      restart_policy: unless-stopped
      replicas: 2

  beat:
    build:
      context: ./app/backend
      dockerfile: Dockerfile
    command: celery -A src.celery_app beat --loglevel=info
    deploy:
      restart_policy: unless-stopped
      replicas: 1  # Only one beat instance

  frontend:
    build:
      context: ./app/frontend
      dockerfile: Dockerfile
    deploy:
      restart_policy: unless-stopped
      replicas: 2
      health_check:
        path: /api/health
        interval: 30s
        timeout: 10s

deployment:
  branches:
    main:
      environment: production
      auto_deploy: true
    develop:
      environment: staging
      auto_deploy: true

  pre_deploy:
    - echo "Running pre-deployment checks..."
    - echo "DATABASE_URL is configured: ${DATABASE_URL:0:10}..."

  post_deploy:
    - echo "Deployment completed successfully"
    - echo "Services restarted"
```

### GitHub Actions Integration (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Coolify

on:
  push:
    branches:
      - main
      - develop
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Trigger Coolify Deployment
        run: |
          curl -X POST \
            "${{ secrets.COOLIFY_WEBHOOK_URL }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_TOKEN }}"

      - name: Wait for deployment
        run: sleep 60

      - name: Health check
        run: |
          curl -f https://api.smarter-team.com/health || exit 1
          curl -f https://smarter-team.com || exit 1
```

## Webhook Configuration

### Coolify Webhook Setup

1. **Navigate to service → Webhooks**
2. **Copy webhook URL**
3. **Add to GitHub:**
   - Go to repository → Settings → Webhooks
   - Add webhook URL
   - Content type: `application/json`
   - Events: Push events
   - Active: ✓

### Test Webhook

```bash
# Trigger deployment manually
curl -X POST https://coolify.your-domain.com/webhooks/deploy/service-id

# Check deployment status
# (View in Coolify UI → Deployments)
```

## Verification

### Test Auto-Deployment

```bash
# Make a small change
echo "# Test deployment" >> README.md
git add README.md
git commit -m "test: trigger Coolify deployment"
git push origin main

# Monitor in Coolify:
# 1. Check Deployments tab
# 2. Verify build starts automatically
# 3. Watch build logs
# 4. Confirm services restart
```

### Check Deployment Logs

In Coolify UI:
1. Navigate to project
2. Click "Deployments" tab
3. View latest deployment
4. Check build logs for each service
5. Verify all services restarted successfully

### Verify Services Updated

```bash
# Check backend version (add version endpoint)
curl https://api.smarter-team.com/version

# Check frontend version
curl https://smarter-team.com/api/version

# Check all services running
# (In Coolify UI → Services → Status)
```

## Branch Strategy

### Production (main branch)
```
main → Coolify Production Environment
  ├── smarter-team-backend (production)
  ├── smarter-team-worker (production)
  ├── smarter-team-beat (production)
  └── smarter-team-frontend (production)
```

### Staging (develop branch)
```
develop → Coolify Staging Environment
  ├── smarter-team-backend-staging
  ├── smarter-team-worker-staging
  ├── smarter-team-beat-staging
  └── smarter-team-frontend-staging
```

### Feature Branches
```
feature/* → Manual deployment or preview environments
```

## Deployment Flow

```
Developer pushes to GitHub
    ↓
GitHub webhook triggers Coolify
    ↓
Coolify pulls latest code
    ↓
Coolify builds Docker images
    ↓
Coolify runs health checks
    ↓
Coolify stops old containers
    ↓
Coolify starts new containers
    ↓
Coolify verifies health checks pass
    ↓
Deployment complete ✓
```

## Notes

- **Auto-deploy**: Recommended for staging, optional for production
- **Manual approval**: Can require manual trigger for production
- **Build caching**: Speeds up subsequent deployments by 50-70%
- **Parallel builds**: Coolify can build multiple services simultaneously
- **Rollback**: Previous versions kept for easy rollback

## Best Practices

1. **Always test in staging** before deploying to production
2. **Use semantic versioning** for releases
3. **Tag production releases** in Git
4. **Monitor deployment logs** for errors
5. **Set up alerts** for failed deployments
6. **Keep deployment history** for auditing

## Troubleshooting

**Webhook not triggering:**
- Verify webhook URL is correct
- Check GitHub webhook delivery logs
- Ensure webhook is active
- Test with manual trigger

**Build fails:**
- Check build logs in Coolify
- Verify Dockerfile paths are correct
- Check environment variables are set
- Ensure all dependencies are available

**Deployment succeeds but services fail:**
- Check health check endpoints
- Verify environment variables
- Check service dependencies
- Review service logs

**Old version still running:**
- Check deployment completed successfully
- Verify health checks passed
- Manually restart services if needed
- Check for stuck containers

## Rollback Procedure

**In Coolify UI:**
1. Navigate to service
2. Click "Deployments" tab
3. Find previous working version
4. Click "Redeploy"
5. Verify services restart with old version

**Via CLI:**
```bash
# SSH into Coolify server
ssh user@coolify-server

# List recent deployments
docker images | grep smarter-team

# Rollback to previous image
docker tag smarter-team-backend:previous smarter-team-backend:latest
docker restart smarter-team-backend
```

## Next Steps

After completing this task:
1. Test auto-deployment with small change
2. Monitor deployment logs
3. Set up staging environment (if needed)
4. Configure deployment notifications
5. Proceed to Task 227: Configure build and deployment settings
