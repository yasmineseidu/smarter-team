# Task 231: Configure Next.js Frontend

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure Next.js frontend service in Coolify with health checks, environment variables, and static asset optimization.

## Prerequisites

- [ ] Task 222 completed (Next.js Dockerfile created)
- [ ] Backend service deployed and accessible

## Implementation Checklist

- [ ] Configure frontend service in Coolify
- [ ] Set up health check endpoint
- [ ] Configure environment variables
- [ ] Set up static asset caching
- [ ] Test frontend-backend communication

## Configuration Details

### Frontend Service Configuration

```yaml
Service: smarter-team-frontend
Build: app/frontend/Dockerfile
Port: 3000

Health Check:
  Path: /api/health
  Interval: 30s
  Timeout: 10s
  Retries: 3
  Start Period: 40s

Resources:
  CPU: 2.0 (limit), 0.5 (reservation)
  Memory: 2GB (limit), 512MB (reservation)

Replicas: 2
Restart: on-failure

Environment:
  NODE_ENV=production
  NEXT_PUBLIC_API_URL=https://api.smarter-team.com
  API_URL=http://smarter-team-backend:8000
```

### Health Check Endpoint

Create `app/frontend/app/api/health/route.ts`:

```typescript
import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Test backend connectivity
    const backendUrl = process.env.API_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/health`, {
      cache: 'no-store',
    })

    if (!response.ok) {
      return NextResponse.json(
        { status: 'unhealthy', backend: 'unreachable' },
        { status: 503 }
      )
    }

    return NextResponse.json({
      status: 'healthy',
      backend: 'connected',
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        backend: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 503 }
    )
  }
}
```

## Verification

```bash
# Test frontend health
curl https://smarter-team.com/api/health

# Test frontend can reach backend
docker exec smarter-team-frontend curl http://smarter-team-backend:8000/health

# Test in browser
open https://smarter-team.com
```

## Notes

- **Standalone mode**: Reduces image size significantly
- **Health check**: Verifies backend connectivity
- **Environment variables**: NEXT_PUBLIC_* available in browser
- **Static assets**: Served from .next/static with caching
