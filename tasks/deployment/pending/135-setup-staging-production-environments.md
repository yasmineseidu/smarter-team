# Task 234: Set Up Staging and Production Environments

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure separate staging and production environments in Coolify with isolated databases, different resource allocations, and environment-specific configurations.

## Prerequisites

- [ ] Tasks 224-233 completed (Coolify project fully configured)
- [ ] Separate databases for staging and production
- [ ] Domain names for both environments

## Implementation Checklist

- [ ] Clone production services for staging
- [ ] Configure staging-specific environment variables
- [ ] Set up staging database and Redis
- [ ] Configure domain routing
- [ ] Test both environments independently

## Configuration Details

### Environment Structure

```
Production (main branch):
  - api.smarter-team.com → smarter-team-backend
  - smarter-team.com → smarter-team-frontend
  - Database: production
  - Redis: production instance

Staging (develop branch):
  - staging-api.smarter-team.com → smarter-team-backend-staging
  - staging.smarter-team.com → smarter-team-frontend-staging
  - Database: staging
  - Redis: staging instance
```

### Staging Environment Variables

```bash
# Staging-specific overrides
ENVIRONMENT=staging
DEBUG=true
LOG_LEVEL=debug

# Separate database
DATABASE_URL=postgresql://staging-user:pass@host/staging-db

# Separate Redis
REDIS_URL=redis://smarter-team-redis-staging:6379/0

# Staging API keys (lower rate limits)
ANTHROPIC_API_KEY=sk-ant-staging-...

# Frontend URLs
NEXT_PUBLIC_API_URL=https://staging-api.smarter-team.com
```

## Verification

```bash
# Test staging
curl https://staging-api.smarter-team.com/health
curl https://staging.smarter-team.com/api/health

# Test production
curl https://api.smarter-team.com/health
curl https://smarter-team.com/api/health

# Verify separate databases
# (staging changes should not affect production)
```

## Notes

- **Isolation**: Staging and production completely separate
- **Resource allocation**: Staging uses fewer resources
- **Testing ground**: Test all changes in staging first
- **Data**: Staging uses synthetic/test data only
