# Task 236: Set Up Logging and Monitoring

**Status:** Pending
**Domain:** deployment
**Source:** Coolify deployment requirements
**Created:** 2025-12-06

## Summary

Configure centralized logging, monitoring dashboards, and alerting for all services in Coolify using built-in tools and optional integrations (Sentry, Grafana).

## Prerequisites

- [ ] All services deployed and healthy
- [ ] Coolify logging enabled
- [ ] (Optional) Sentry account for error tracking

## Implementation Checklist

- [ ] Configure structured logging in all services
- [ ] Set up log aggregation in Coolify
- [ ] Configure log retention policies
- [ ] (Optional) Integrate Sentry for error tracking
- [ ] Set up monitoring dashboards
- [ ] Configure log search and filtering

## Configuration Details

### Structured Logging Configuration

**Backend (Python):**

```python
# src/config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(level: str = "INFO"):
    """Configure structured JSON logging."""
    logger = logging.getLogger()
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        timestamp=True
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

**Frontend (Next.js):**

```typescript
// lib/logger.ts
export const logger = {
  info: (message: string, data?: object) => {
    console.log(JSON.stringify({ level: 'info', message, ...data, timestamp: new Date().toISOString() }))
  },
  error: (message: string, error?: Error, data?: object) => {
    console.error(JSON.stringify({
      level: 'error',
      message,
      error: error?.message,
      stack: error?.stack,
      ...data,
      timestamp: new Date().toISOString()
    }))
  },
}
```

### Coolify Logging Configuration

**In Coolify UI:**

1. Navigate to service → Logs
2. Enable log collection
3. Set retention: 30 days
4. Configure log rotation: 100MB
5. Enable log streaming

### Sentry Integration (Optional)

```bash
# Environment variables
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

```python
# src/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
        integrations=[FastApiIntegration()],
    )
```

## Verification

```bash
# View logs in Coolify
# Navigate to service → Logs

# Search logs
# Use Coolify search: "error", "level:ERROR", etc.

# Test error reporting
curl -X POST https://api.smarter-team.com/api/test-error
# Check Sentry dashboard for error
```

## Notes

- **JSON logging**: Easy parsing and filtering
- **Log retention**: Balance storage vs history
- **Sentry**: Captures errors automatically
- **Coolify logs**: Accessible via UI and API
