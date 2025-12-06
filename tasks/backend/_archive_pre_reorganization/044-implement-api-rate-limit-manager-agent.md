# Task: Implement API Rate Limit Manager Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/system-api-rate-limit.md
**Created:** 2025-01-15

## Summary

Implement a comprehensive API rate limiting and usage management system that monitors 40+ external integrations, prevents throttling through intelligent throttling and queuing, manages costs with provider switching, and provides predictive analytics for usage patterns.

## Files to Create

### Core Agent
- `app/backend/src/agents/api_rate_limit_manager/__init__.py`
- `app/backend/src/agents/api_rate_limit_manager/agent.py`
- `app/backend/src/agents/api_rate_limit_manager/tools.py`
- `app/backend/src/agents/api_rate_limit_manager/schemas.py`
- `app/backend/src/agents/api_rate_limit_manager/prompts.py`
- `app/backend/src/agents/api_rate_limit_manager/exceptions.py`

### Database
- `app/backend/src/agents/api_rate_limit_manager/models.py`
- `app/backend/migrations/versions/xxx_add_api_rate_limit_tables.py`

### Tasks
- `app/backend/src/tasks/api_rate_limit_tasks.py`

### Tests
- `app/backend/__tests__/unit/agents/test_api_rate_limit_manager.py`
- `app/backend/__tests__/integration/test_api_rate_limit_integration.py`
- `app/backend/__tests__/performance/test_api_rate_limit_performance.py`

## Implementation Checklist

### Phase 1: Foundation (Day 1-2)
- [ ] Create agent directory structure
- [ ] Implement base agent class extending BaseAgent
- [ ] Define all Pydantic schemas (inputs/outputs)
- [ ] Create database models for api_usage, api_limits, queue, alerts
- [ ] Write and run database migration
- [ ] Set up basic agent registration in main app

### Phase 2: Tools Implementation (Day 3-4)
- [ ] Implement `check_rate_limit_status` tool with real-time checking
- [ ] Implement `log_api_usage` tool with async batching
- [ ] Implement `calculate_throttle_delay` tool with intelligent algorithms
- [ ] Implement `queue_request` tool with priority queues
- [ ] Implement `switch_provider` tool with fallback configuration
- [ ] Implement `send_rate_limit_alert` tool with multiple channels
- [ ] Add error handling and retry logic to all tools

### Phase 3: Advanced Features (Day 5-6)
- [ ] Implement `get_usage_prediction` with trend analysis
- [ ] Implement `get_cost_optimization` with ML recommendations
- [ ] Implement `update_provider_status` with health monitoring
- [ ] Implement `generate_usage_report` with multiple formats
- [ ] Add circuit breaker pattern for provider failures
- [ ] Implement caching layer for high-frequency checks

### Phase 4: Integration (Day 7)
- [ ] Create Celery tasks for background processing
- [ ] Set up event handlers for API call tracking
- [ ] Configure cron schedules for periodic tasks
- [ ] Implement agent handoffs for provider switching
- [ ] Add metrics and observability (Prometheus)
- [ ] Configure logging with structured format

### Phase 5: Testing (Day 8-9)
- [ ] Write unit tests for all tools (target: 95% coverage)
- [ ] Write integration tests for end-to-end flows
- [ ] Write performance tests for load handling
- [ ] Mock all external APIs in tests
- [ ] Test database transactions and rollbacks
- [ ] Verify Celery task execution and retries

### Phase 6: Production Setup (Day 10)
- [ ] Add environment configuration for all 40+ services
- [ ] Set up monitoring dashboard
- [ ] Create runbooks for common scenarios
- [ ] Configure alert thresholds and escalation
- [ ] Implement graceful shutdown handling
- [ ] Add health check endpoints

## Acceptance Criteria

### Functional Requirements
- [ ] Real-time rate limit checks complete in <50ms
- [ ] All 40+ external APIs configured with limits
- [ ] Queue handles 1M+ requests without performance degradation
- [ ] Provider switching completes in <10 seconds
- [ ] Usage predictions accurate within 10% margin
- [ ] Cost optimization achieves minimum 15% savings

### Non-Functional Requirements
- [ ] 99.9% uptime for rate limiting service
- [ ] Memory usage <500MB under normal load
- [ ] All API calls tracked with <100ms overhead
- [ ] Zero data loss during outages (queue persistence)
- [ ] Security audit passes with no critical findings
- [ ] Documentation complete with runbooks

### Integration Requirements
- [ ] Seamless handoff to Campaign, Research, Finance agents
- [ ] Event-driven updates to System Health Check agent
- [ ] Celery tasks for background processing
- [ ] Prometheus metrics exported
- [ ] Dashboard displays real-time metrics
- [ ] Alerts sent via Slack, Telegram, email

## Configuration Requirements

### Environment Variables
```bash
# Rate Limit Manager Settings
RATE_LIMIT_CHECK_INTERVAL=5  # seconds
RATE_LIMIT_QUEUE_MAX_SIZE=1000000
RATE_LIMIT_CACHE_TTL=60  # seconds
RATE_LIMIT_PREDICTION_HORIZON=24  # hours

# Alert Channels
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
PAGERDUTY_INTEGRATION_KEY=...

# Cost Tracking
COST_TRACKING_ENABLED=true
COST_BUDGET_MONTHLY=10000.00
COST_ALERT_THRESHOLD=0.9

# Provider Configs
FALLBACK_PROVIDERS_CONFIG=/app/config/fallback_providers.json
RATE_LIMITS_CONFIG=/app/config/rate_limits.json
```

### Rate Limit Configuration
```json
{
  "claude": {
    "limit_tokens": 1000000,
    "limit_requests": 1000,
    "period": "minute",
    "throttle_at": 0.8,
    "queue_at": 0.9,
    "cost_per_token": 0.00003
  },
  "instantly": {
    "limit_requests": 50000,
    "period": "day",
    "throttle_at": 0.9,
    "queue_at": 0.95,
    "cost_per_request": 0.001
  },
  "...": "Continue for all 40+ services"
}
```

### Fallback Providers
```json
{
  "email_verification": {
    "primary": "reoon",
    "fallbacks": ["zerobounce", "neverbounce"],
    "cost_multipliers": {"zerobounce": 1.2, "neverbounce": 1.1}
  },
  "ai_llm": {
    "primary": "claude",
    "fallbacks": ["openai_gpt4", "google_gemini"],
    "cost_multipliers": {"openai_gpt4": 0.8, "google_gemini": 0.7}
  }
}
```

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_api_rate_limit_manager.py -v --cov=app/backend/src/agents/api_rate_limit_manager

# Run integration tests
pytest app/backend/__tests__/integration/test_api_rate_limit_integration.py -v

# Run performance tests
pytest app/backend/__tests__/performance/test_api_rate_limit_performance.py -v

# Type checking
mypy app/backend/src/agents/api_rate_limit_manager/

# Linting
ruff check app/backend/src/agents/api_rate_limit_manager/

# Database migration
alembic upgrade head

# Load rate limit configs
python -c "
from src.agents.api_rate_limit_manager.agent import APIRateLimitManagerAgent
agent = APIRateLimitManagerAgent()
print('Agent initialized successfully')
"

# Test Celery tasks
celery -A src.celery_app worker -l info -Q rate_limit

# Test health check
curl http://localhost:8000/health/agents/api_rate_limit_manager
```

## Dependencies to Add

```toml
# Add to pyproject.toml dependencies
redis-py-cluster>=2.1.0  # For distributed rate limiting
prometheus-client>=0.19.0  # For metrics
circuitbreaker>=2.0.0  # For circuit breaker pattern
apscheduler>=3.10.0  # For scheduled tasks
pytz>=2023.3  # For timezone handling
numpy>=1.24.0  # For prediction calculations
scikit-learn>=1.3.0  # For cost optimization ML
aiohttp>=3.9.0  # For async HTTP in tests
aiosmtplib>=3.0.0  # For email alerts
aioredis>=2.0.0  # For Redis async
```

## Success Metrics

1. **Zero rate limit errors** in production for 30 days
2. **Cost savings** of 15%+ vs baseline through optimization
3. **Response time** <50ms for 99.9% of rate limit checks
4. **Queue processing** <10 second average wait time
5. **Uptime** 99.9% for the rate limiting service
6. **Prediction accuracy** within 10% for 95% of services

## Rollout Plan

1. **Phase 1**: Deploy to staging with 10% of traffic
2. **Phase 2**: Monitor metrics, adjust thresholds
3. **Phase 3**: Deploy to production with shadow mode (logging only)
4. **Phase 4**: Gradually enable throttling for non-critical services
5. **Phase 5**: Enable full rate limiting for all services
6. **Phase 6**: Add cost optimization features

## Runbook Items

### High Queue Depth
1. Check if service is rate limited
2. Verify worker processes are running
3. Check for database connectivity
4. Consider increasing worker count

### Provider Switching
1. Verify API keys for fallback providers
2. Test fallback provider connectivity
3. Monitor costs after switch
4. Plan switchback time

### Cost Overruns
1. Identify high-cost services
2. Check for unusual usage patterns
3. Review optimization recommendations
4. Consider temporary throttling

### Alerts Not Sending
1. Verify webhook URLs and tokens
2. Check rate limits on alert channels
3. Test alert configuration
4. Fallback to email if needed
