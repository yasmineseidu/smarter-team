# API Rate Limit Manager Agent - Production Specification

**Status:** Ready to Build
**Last Updated:** 2025-01-15
**Refined From:** plan/agents/system-api-rate-limit.md

## Overview

**Category**: System & Administration
**Priority**: Phase 7 - Polish & Scale
**Agent Name**: `api_rate_limit_manager`
**Purpose**: Intelligent API rate limiting and usage management system that prevents throttling, optimizes request distribution, and manages cost across 40+ external integrations.

**Core Functionality:**
- Real-time API usage tracking across all services
- Dynamic throttling and request queuing based on usage patterns
- Cost-aware request routing with fallback providers
- Intelligent alerting with predictive analytics
- Automatic fallback provider switching

---

## System Prompt

```
You are the API Rate Limit Manager Agent for Smarter Team, the guardian of our API infrastructure.

Your mission is to ensure uninterrupted service by intelligently managing API usage across 40+ external services. You prevent rate limiting, optimize costs, and maintain service availability through proactive monitoring and intelligent request routing.

**Core Responsibilities:**
1. Track all API calls in real-time with token/count metrics
2. Implement adaptive throttling based on usage patterns and time-to-limit
3. Queue non-critical requests when approaching limits
4. Switch to backup providers when primary limits are exceeded
5. Predict usage trends and alert before limits are hit
6. Manage cost optimization through provider switching

**Decision Matrix:**
- **< 70% usage**: Process normally, full speed
- **70-80% usage**: Add small delays (1-2s) between requests
- **80-90% usage**: Throttle with exponential backoff (2-10s delays)
- **90-95% usage**: Queue non-essential requests, prioritize critical
- **>95% usage**: Switch to fallback providers if available
- **100% usage**: All requests queued until reset

**Priority Classification:**
- **CRITICAL**: Database operations, authentication, payment processing
- **HIGH**: Client-facing operations, active campaigns
- **NORMAL**: Batch processing, reports, data sync
- **LOW**: Analytics, cleanup, non-essential enrichment

**Behavioral Guidelines:**
- Always consider cost impact when switching providers
- Maintain audit trail of all rate limit decisions
- Provide predictive analytics ("will hit limit in 2 hours")
- Send alerts with actionable recommendations
- Learn from usage patterns to optimize future requests

**Communication Style:**
- Alerts include: current usage, time to limit, recommended action
- Metrics show: trend analysis, cost impact, provider performance
- Decisions are logged with full context and reasoning

You have comprehensive tools for usage tracking, throttling control, queue management, provider switching, and alert generation. Use these tools to maintain 99.9% API availability while optimizing costs.
```

---

## Agent Implementation

### Class Definition

```python
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger


class RequestPriority(str, Enum):
    """Request priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class ProviderStatus(str, Enum):
    """API provider status."""
    ACTIVE = "active"
    THROTTLED = "throttled"
    QUEUED = "queued"
    EXHAUSTED = "exhausted"
    FALLBACK = "fallback"


@dataclass
class APIUsage:
    """API usage metrics."""
    service: str
    current_usage: int
    limit: int
    period: str
    tokens_used: int
    cost_usd: float
    reset_time: datetime
    status: ProviderStatus


@dataclass
class RateLimitDecision:
    """Rate limiting decision with context."""
    action: str  # proceed, throttle, queue, fallback, reject
    delay_seconds: int
    priority: RequestPriority
    reason: str
    time_to_limit: Optional[timedelta] = None
    fallback_provider: Optional[str] = None


class APIRateLimitManagerAgent(BaseAgent):
    """
    Intelligent API rate limiting and usage management agent.

    Monitors and controls API usage across all external services,
    implementing adaptive throttling, queuing, and provider switching.
    """

    def __init__(self):
        super().__init__(
            name="api_rate_limit_manager",
            description="Manages API rate limits and usage optimization"
        )

        # Load rate limit configurations
        self._rate_limits = self._load_rate_limit_configs()
        self._fallback_providers = self._load_fallback_configs()

        # Register all tools
        self._register_tools()

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        return _SYSTEM_PROMPT

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Process incoming rate limit management tasks."""
        task_type = task.get("type")

        if task_type == "check_rate_limit":
            return await self._handle_rate_limit_check(task)
        elif task_type == "log_api_call":
            return await self._handle_log_api_call(task)
        elif task_type == "update_usage_metrics":
            return await self._handle_update_metrics(task)
        elif task_type == "check_provider_health":
            return await self._handle_provider_health_check(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _register_tools(self) -> None:
        """Register all rate limiting tools."""
        self.register_tool(
            self.check_rate_limit_status,
            "check_rate_limit_status",
            "Check current rate limit status for a service"
        )
        self.register_tool(
            self.log_api_usage,
            "log_api_usage",
            "Log API call for usage tracking"
        )
        self.register_tool(
            self.calculate_throttle_delay,
            "calculate_throttle_delay",
            "Calculate appropriate delay based on usage"
        )
        self.register_tool(
            self.queue_request,
            "queue_request",
            "Queue a request for later processing"
        )
        self.register_tool(
            self.switch_provider,
            "switch_provider",
            "Switch to fallback provider"
        )
        self.register_tool(
            self.send_rate_limit_alert,
            "send_rate_limit_alert",
            "Send rate limit alert notification"
        )
        self.register_tool(
            self.get_usage_prediction,
            "get_usage_prediction",
            "Predict when limits will be reached"
        )
        self.register_tool(
            self.get_cost_optimization,
            "get_cost_optimization",
            "Get cost optimization recommendations"
        )
        self.register_tool(
            self.update_provider_status,
            "update_provider_status",
            "Update provider status based on health checks"
        )
        self.register_tool(
            self.generate_usage_report,
            "generate_usage_report",
            "Generate comprehensive usage report"
        )
```

---

## Tools

### Tool 1: check_rate_limit_status

**Purpose:** Check current usage and determine if request should proceed

**Input Schema:**
```python
class RateLimitCheckInput(BaseModel):
    service: str = Field(..., description="API service name")
    endpoint: str = Field(..., description="API endpoint being called")
    tokens_requested: int = Field(default=0, description="Tokens for AI APIs")
    priority: RequestPriority = Field(default=RequestPriority.NORMAL)
    request_cost: float = Field(default=0.0, description="Estimated cost in USD")
```

**Output Schema:**
```python
class RateLimitCheckOutput(BaseModel):
    decision: RateLimitDecision
    current_usage: APIUsage
    queue_position: Optional[int] = None
    estimated_wait_time: Optional[int] = None
```

**Error Handling:**
- Database connection failed → Return conservative throttle (10s delay)
- Invalid service name → Log error, allow request with warning
- Missing configuration → Use default limits (1000/hour)

**Example:**
```python
# Input
{
    "service": "claude",
    "endpoint": "/v1/messages",
    "tokens_requested": 1000,
    "priority": "high",
    "request_cost": 0.03
}

# Output
{
    "decision": {
        "action": "proceed",
        "delay_seconds": 0,
        "priority": "high",
        "reason": "Usage at 45%, well within limits"
    },
    "current_usage": {
        "service": "claude",
        "current_usage": 450000,
        "limit": 1000000,
        "period": "minute",
        "status": "active"
    }
}
```

### Tool 2: log_api_usage

**Purpose:** Record API call for usage tracking and analytics

**Input Schema:**
```python
class LogUsageInput(BaseModel):
    service: str = Field(..., description="API service name")
    endpoint: str = Field(..., description="API endpoint called")
    method: str = Field(..., description="HTTP method")
    status_code: int = Field(..., description="Response status code")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    tokens_used: int = Field(default=0, description="Tokens consumed")
    request_cost: float = Field(default=0.0, description="Actual cost in USD")
    success: bool = Field(..., description="Request successful")
    error_type: Optional[str] = Field(default=None, description="Error type if failed")
```

**Output Schema:**
```python
class LogUsageOutput(BaseModel):
    logged: bool
    usage_id: str
    updated_totals: dict
```

**Error Handling:**
- Database write failed → Queue for retry, don't block request
- Invalid data → Log warning, continue with partial data
- Duplicate entry → Update existing record

### Tool 3: calculate_throttle_delay

**Purpose:** Calculate intelligent delay based on usage patterns

**Input Schema:**
```python
class ThrottleDelayInput(BaseModel):
    service: str = Field(..., description="API service name")
    current_usage_pct: float = Field(..., description="Current usage percentage")
    priority: RequestPriority = Field(..., description="Request priority")
    time_until_reset: Optional[int] = Field(default=None, description="Seconds until reset")
    request_count: int = Field(default=1, description="Requests in this batch")
```

**Output Schema:**
```python
class ThrottleDelayOutput(BaseModel):
    delay_seconds: int
    reason: str
    recommended_batch_size: int
    next_check_time: datetime
```

**Logic:**
```python
def calculate_delay(usage_pct, priority, time_until_reset):
    if priority == RequestPriority.CRITICAL:
        return 0  # Never throttle critical requests

    if usage_pct < 0.7:
        return 0
    elif usage_pct < 0.8:
        return 1
    elif usage_pct < 0.9:
        return min(10, int((usage_pct - 0.8) * 100))
    else:
        return max(30, int((usage_pct - 0.9) * 300))
```

### Tool 4: queue_request

**Purpose:** Queue requests that can't be processed immediately

**Input Schema:**
```python
class QueueRequestInput(BaseModel):
    service: str = Field(..., description="API service name")
    request_data: dict = Field(..., description="Request payload")
    priority: RequestPriority = Field(..., description="Request priority")
    scheduled_for: Optional[datetime] = Field(default=None, description="Schedule for specific time")
    max_wait_time: Optional[int] = Field(default=3600, description="Max wait in seconds")
    callback_url: Optional[str] = Field(default=None, description="Callback URL when ready")
```

**Output Schema:**
```python
class QueueRequestOutput(BaseModel):
    queue_id: str
    position: int
    estimated_wait_time: int
    queue_depth: int
```

**Queue Processing:**
- Priority queues: critical, high, normal, low
- Fair share: prevent starvation of lower priority
- TTL: Auto-expire requests after max_wait_time
- Callback: Webhook or Celery task when ready

### Tool 5: switch_provider

**Purpose:** Switch to backup/fallback provider

**Input Schema:**
```python
class SwitchProviderInput(BaseModel):
    primary_service: str = Field(..., description="Primary service name")
    reason: str = Field(..., description="Reason for switching")
    duration_minutes: Optional[int] = Field(default=60, description="Duration of switch")
    force_switch: bool = Field(default=False, description="Force switch even if primary available")
```

**Output Schema:**
```python
class SwitchProviderOutput(BaseModel):
    switched: bool
    new_provider: str
    config_applied: dict
    auto_switchback_time: datetime
```

**Fallback Providers:**
```python
FALLBACK_MAP = {
    "email_verification": {
        "primary": "reoon",
        "fallbacks": ["zerobounce", "neverbounce"],
        "cost_multiplier": 1.2
    },
    "ai_llm": {
        "primary": "claude",
        "fallbacks": ["openai_gpt4", "google_gemini"],
        "cost_multiplier": 0.8
    },
    "search": {
        "primary": "serper",
        "fallbacks": ["google_custom_search", "bing_search"],
        "cost_multiplier": 1.5
    }
}
```

### Tool 6: send_rate_limit_alert

**Purpose:** Send notifications for rate limit events

**Input Schema:**
```python
class AlertInput(BaseModel):
    service: str = Field(..., description="API service name")
    alert_type: str = Field(..., description="warning, critical, recovery")
    current_usage: int = Field(..., description="Current usage value")
    limit: int = Field(..., description="Total limit")
    usage_pct: float = Field(..., description="Usage percentage")
    time_to_limit: Optional[timedelta] = Field(default=None)
    action_taken: str = Field(..., description="Action taken")
    additional_context: Optional[dict] = Field(default=None)
```

**Output Schema:**
```python
class AlertOutput(BaseModel):
    alert_id: str
    sent: bool
    channels: list[str]
    message: str
```

**Alert Channels:**
- Slack: #api-alerts channel
- Telegram: Operations group
- Email: ops@smarterteam.com
- PagerDuty: Critical alerts only

### Tool 7: get_usage_prediction

**Purpose:** Predict when limits will be reached based on trends

**Input Schema:**
```python
class PredictionInput(BaseModel):
    service: str = Field(..., description="API service name")
    prediction_window_hours: int = Field(default=24, description="Hours to predict")
    include_weekend: bool = Field(default=True, description="Include weekend patterns")
    confidence_level: float = Field(default=0.95, description="Prediction confidence")
```

**Output Schema:**
```python
class PredictionOutput(BaseModel):
    service: str
    current_usage: int
    predicted_usage: int
    time_to_limit: timedelta
    confidence: float
    recommendation: str
    trend_analysis: dict
```

### Tool 8: get_cost_optimization

**Purpose:** Analyze usage patterns for cost optimization opportunities

**Input Schema:**
```python
class CostOptimizationInput(BaseModel):
    services: Optional[list[str]] = Field(default=None, description="Services to analyze")
    period_days: int = Field(default=30, description="Analysis period")
    include_suggestions: bool = Field(default=True, description="Include optimization suggestions")
```

**Output Schema:**
```python
class CostOptimizationOutput(BaseModel):
    total_cost: float
    cost_by_service: dict
    optimization_opportunities: list
    potential_savings: float
    recommendations: list[str]
```

### Tool 9: update_provider_status

**Purpose:** Update provider health status based on metrics

**Input Schema:**
```python
class ProviderStatusInput(BaseModel):
    service: str = Field(..., description="API service name")
    status: ProviderStatus = Field(..., description="New status")
    error_rate: Optional[float] = Field(default=None, description="Current error rate")
    avg_response_time: Optional[int] = Field(default=None, description="Average response time")
    last_error: Optional[str] = Field(default=None, description="Last error message")
    metrics: Optional[dict] = Field(default=None, description="Additional metrics")
```

**Output Schema:**
```python
class ProviderStatusOutput(BaseModel):
    updated: bool
    previous_status: ProviderStatus
    new_status: ProviderStatus
    status_changed_at: datetime
    actions_taken: list[str]
```

### Tool 10: generate_usage_report

**Purpose:** Generate comprehensive usage and cost reports

**Input Schema:**
```python
class UsageReportInput(BaseModel):
    report_type: str = Field(..., description="daily, weekly, monthly, custom")
    start_date: Optional[datetime] = Field(default=None, description="Custom start date")
    end_date: Optional[datetime] = Field(default=None, description="Custom end date")
    services: Optional[list[str]] = Field(default=None, description="Specific services")
    include_predictions: bool = Field(default=True, description="Include future predictions")
    format: str = Field(default="json", description="json, csv, html")
```

**Output Schema:**
```python
class UsageReportOutput(BaseModel):
    report_id: str
    report_url: Optional[str] = None
    summary: dict
    detailed_usage: dict
    cost_analysis: dict
    recommendations: list
    generated_at: datetime
```

---

## Database Schema

### api_usage table
```sql
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    request_cost DECIMAL(10,4) DEFAULT 0,
    success BOOLEAN NOT NULL,
    error_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    agent_id VARCHAR(50),
    request_id VARCHAR(100),

    INDEX idx_api_usage_service_created (service, created_at),
    INDEX idx_api_usage_created_at (created_at),
    INDEX idx_api_usage_endpoint (endpoint)
);
```

### api_limits table
```sql
CREATE TABLE api_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(50) UNIQUE NOT NULL,
    limit_type VARCHAR(20) NOT NULL, -- requests, tokens, cost
    limit_value INTEGER NOT NULL,
    period VARCHAR(20) NOT NULL, -- minute, hour, day, month
    throttle_threshold DECIMAL(3,2) DEFAULT 0.9,
    queue_threshold DECIMAL(3,2) DEFAULT 0.95,
    fallback_service VARCHAR(50),
    cost_per_request DECIMAL(10,4) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### api_rate_limit_queue table
```sql
CREATE TABLE api_rate_limit_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(50) NOT NULL,
    request_data JSONB NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    status VARCHAR(20) NOT NULL DEFAULT 'queued', -- queued, processing, completed, failed
    scheduled_for TIMESTAMP WITH TIME ZONE,
    max_wait_time INTEGER DEFAULT 3600,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    attempts INTEGER DEFAULT 0,
    callback_url VARCHAR(255),

    INDEX idx_queue_service_priority (service, priority, status),
    INDEX idx_queue_scheduled_for (scheduled_for, status),
    INDEX idx_queue_created_at (created_at)
);
```

### api_alerts table
```sql
CREATE TABLE api_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(50) NOT NULL,
    alert_type VARCHAR(20) NOT NULL, -- warning, critical, recovery
    current_usage INTEGER NOT NULL,
    limit_value INTEGER NOT NULL,
    usage_pct DECIMAL(5,2) NOT NULL,
    action_taken VARCHAR(100),
    message TEXT,
    channels_sent JSONB,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Multi-Agent Integration

### Agent Handoffs

1. **To Campaign Agents:**
   - When email service rate limited → Handoff with alternative provider config
   - Payload: `{"service": "instantly", "fallback": "mailgun", "config": {...}}`

2. **To Research Agents:**
   - When enrichment APIs limited → Handoff with queued processing
   - Payload: `{"queue_id": "xxx", "estimated_wait": 300, "alternative_sources": [...]}`

3. **To System Health Check:**
   - When provider consistently failing → Alert for health investigation
   - Payload: `{"service": "reoon", "error_rate": 0.15, "status": "degraded"}`

4. **To Finance Agent:**
   - When costs exceed budget → Request approval for overages
   - Payload: `{"current_spend": 1250.50, "budget": 1000, "overage": 250.50}`

### Event Subscription

```python
# Subscribe to API call events
@event_handler("api.call.completed")
async def handle_api_call_completed(event):
    await agent.log_api_usage(event.data)

# Subscribe to rate limit events
@event_handler("api.rate_limit.warning")
async def handle_rate_limit_warning(event):
    await agent.send_rate_limit_alert({
        "service": event.service,
        "alert_type": "warning",
        ...
    })
```

---

## Celery Tasks

### Background Tasks
```python
# tasks/api_rate_limit_tasks.py

@celery_app.task(bind=True, max_retries=3)
def process_queued_requests(self, service: str):
    """Process queued requests for a specific service."""
    pass

@celery_app.task
def check_all_rate_limits():
    """Check rate limits for all services and send alerts."""
    pass

@celery_app.task
def generate_daily_usage_report():
    """Generate daily usage and cost report."""
    pass

@celery_app.task
def cleanup_old_queue_items():
    """Remove expired items from queue."""
    pass

@celery_app.task
def update_provider_health_metrics():
    """Update health metrics for all providers."""
    pass
```

### Cron Schedule
```python
# Celery Beat schedule
CELERY_BEAT_SCHEDULE = {
    'check-rate-limits': {
        'task': 'tasks.api_rate_limit_tasks.check_all_rate_limits',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'daily-usage-report': {
        'task': 'tasks.api_rate_limit_tasks.generate_daily_usage_report',
        'schedule': crontab(hour=23, minute=55),  # 11:55 PM daily
    },
    'cleanup-queue': {
        'task': 'tasks.api_rate_limit_tasks.cleanup_old_queue_items',
        'schedule': crontab(minute=0),  # Every hour
    },
    'update-health-metrics': {
        'task': 'tasks.api_rate_limit_tasks.update_provider_health_metrics',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
}
```

---

## Error Handling

### Error Types and Recovery

| Error Type | Detection | Response | Retry | Alert |
|------------|-----------|----------|-------|-------|
| Database connection | Exception on write | Use Redis cache, queue writes | Yes, 3x | Critical |
| Invalid service config | Config validation | Use defaults, log error | No | Warning |
| Queue full | Queue depth check | Drop lowest priority, alert | No | Critical |
| Provider switch failed | Health check | Try next fallback | Yes, 2x | High |
| Cost calculation error | Exception in calculation | Use estimate, flag for review | No | Normal |

### Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise
```

---

## Testing

### Unit Tests

```python
# __tests__/unit/agents/test_api_rate_limit_manager.py

class TestAPIRateLimitManager:
    @pytest.mark.asyncio
    async def test_check_rate_limit_normal_usage(self, agent):
        """Test normal usage returns proceed."""
        result = await agent.check_rate_limit_status({
            "service": "claude",
            "endpoint": "/v1/messages",
            "tokens_requested": 1000,
            "priority": "normal"
        })
        assert result.decision.action == "proceed"
        assert result.decision.delay_seconds == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_throttle_required(self, agent, mock_high_usage):
        """Test high usage triggers throttling."""
        result = await agent.check_rate_limit_status({
            "service": "claude",
            "endpoint": "/v1/messages",
            "tokens_requested": 1000,
            "priority": "normal"
        })
        assert result.decision.action == "throttle"
        assert result.decision.delay_seconds > 0

    @pytest.mark.asyncio
    async def test_critical_request_never_throttled(self, agent, max_usage_mock):
        """Test critical requests always proceed."""
        result = await agent.check_rate_limit_status({
            "service": "claude",
            "endpoint": "/v1/messages",
            "tokens_requested": 1000,
            "priority": "critical"
        })
        assert result.decision.action in ["proceed", "fallback"]

    @pytest.mark.asyncio
    async def test_queue_request_with_priority(self, agent):
        """Test request queuing respects priority."""
        result = await agent.queue_request({
            "service": "instantly",
            "request_data": {"to": "test@example.com"},
            "priority": "high"
        })
        assert result.position == 1  # High priority at front
        assert result.queue_depth >= 1

    @pytest.mark.asyncio
    async def test_switch_provider_fallback(self, agent):
        """Test provider switching to fallback."""
        result = await agent.switch_provider({
            "primary_service": "reoon",
            "reason": "Rate limit exceeded",
            "duration_minutes": 60
        })
        assert result.switched is True
        assert result.new_provider in ["zerobounce", "neverbounce"]

    @pytest.mark.asyncio
    async def test_usage_prediction_accuracy(self, agent):
        """Test usage prediction accuracy."""
        result = await agent.get_usage_prediction({
            "service": "claude",
            "prediction_window_hours": 24
        })
        assert result.time_to_limit is not None
        assert 0 <= result.confidence <= 1
        assert result.recommendation is not None

    @pytest.mark.asyncio
    async def test_cost_optimization_suggestions(self, agent):
        """Test cost optimization provides actionable suggestions."""
        result = await agent.get_cost_optimization({
            "services": ["claude", "openai"],
            "period_days": 30
        })
        assert result.total_cost > 0
        assert len(result.recommendations) > 0
        assert result.potential_savings >= 0
```

### Integration Tests

```python
# __tests__/integration/test_api_rate_limit_integration.py

class TestAPIRateLimitIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_rate_limit_flow(self, agent, mock_database):
        """Test complete flow from check to queue to process."""
        # 1. Check rate limit (returns queue)
        check_result = await agent.check_rate_limit_status({
            "service": "reoon",
            "endpoint": "/api/verify",
            "priority": "normal"
        })
        assert check_result.decision.action == "queue"

        # 2. Queue request
        queue_result = await agent.queue_request({
            "service": "reoon",
            "request_data": {"email": "test@example.com"},
            "priority": "normal"
        })

        # 3. Simulate queue processing
        process_task = process_queued_requests.delay("reoon")
        assert process_task.status == "PENDING"

    @pytest.mark.asyncio
    async def test_provider_switch_with_cascade(self, agent):
        """Test provider switch cascades to dependent agents."""
        # Switch provider
        await agent.switch_provider({
            "primary_service": "reoon",
            "reason": "Service degraded"
        })

        # Verify handoff to email verification agent
        handoffs = await agent.get_recent_handoffs()
        assert any("email_verification" in h["target"] for h in handoffs)

    @pytest.mark.asyncio
    async def test_alert_escalation(self, agent):
        """Test alert escalation to critical level."""
        # Send multiple warnings
        for i in range(3):
            await agent.send_rate_limit_alert({
                "service": "claude",
                "alert_type": "warning",
                "usage_pct": 0.85 + i * 0.05
            })

        # Verify critical alert sent
        alerts = await agent.get_recent_alerts("claude")
        critical_alerts = [a for a in alerts if a["alert_type"] == "critical"]
        assert len(critical_alerts) > 0
```

### Performance Tests

```python
# __tests__/performance/test_api_rate_limit_performance.py

class TestAPIRateLimitPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_rate_limit_checks(self, agent):
        """Test 1000 concurrent checks complete in <5 seconds."""
        start_time = time.time()

        tasks = [
            agent.check_rate_limit_status({
                "service": "claude",
                "endpoint": "/v1/messages",
                "tokens_requested": 1000,
                "priority": "normal"
            })
            for _ in range(1000)
        ]

        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        assert duration < 5.0
        assert len(results) == 1000
        assert all(r.decision.action in ["proceed", "throttle", "queue"] for r in results)

    @pytest.mark.asyncio
    async def test_queue_processing_throughput(self, agent):
        """Test queue processes 10000 items in <10 minutes."""
        # Add 10000 items to queue
        for i in range(10000):
            await agent.queue_request({
                "service": "instantly",
                "request_data": {"id": i},
                "priority": "normal"
            })

        # Process queue
        start_time = time.time()
        await process_queued_requests("instantly")
        duration = time.time() - start_time

        assert duration < 600  # 10 minutes
```

---

## Performance Requirements

### Response Times
- Rate limit check: <50ms (p95)
- Usage logging: <100ms (p95)
- Queue operation: <200ms (p95)
- Alert sending: <500ms (p95)
- Report generation: <5 seconds

### Throughput
- Handle 10,000 concurrent rate limit checks
- Process 100,000 API usage logs per minute
- Queue capacity: 1 million requests
- 100% uptime for rate limiting service

### Resource Limits
- Memory usage: <500MB
- CPU usage: <20% average
- Database connections: <50
- Redis memory: <1GB for queue

---

## Observability

### Metrics to Track
```python
# Custom metrics
RATE_LIMIT_CHECKS_TOTAL = Counter('rate_limit_checks_total', ['service', 'action'])
RATE_LIMIT_CHECK_DURATION = Histogram('rate_limit_check_duration_seconds')
API_USAGE_LOGGED = Counter('api_usage_logged_total', ['service', 'status'])
QUEUE_DEPTH = Gauge('queue_depth', ['service', 'priority'])
ACTIVE_PROVIDERS = Gauge('active_providers_total', ['service'])
COST_TRACKING = Counter('api_cost_usd_total', ['service'])
ALERTS_SENT = Counter('api_alerts_sent_total', ['service', 'type'])
```

### Logging
```python
# Structured logging format
logger.info(
    "Rate limit decision made",
    extra={
        "service": "claude",
        "action": "throttle",
        "delay_seconds": 5,
        "usage_pct": 0.85,
        "request_id": "req_123",
        "agent": "api_rate_limit_manager"
    }
)
```

### Tracing
- OpenTelemetry integration for distributed tracing
- Trace rate limit decisions through the system
- Track queue processing latency
- Monitor provider switch cascades

---

## Security

### API Key Management
- Encrypted storage of provider API keys
- Rotation every 90 days
- Separate keys for production/staging
- Audit trail of key access

### Data Protection
- PII scrubbing from logs
- GDPR compliance for EU data
- Data retention: 90 days for usage logs
- Secure deletion of expired queue items

### Access Control
- Role-based access to rate limit dashboard
- API access requires authentication
- Rate limit changes require approval
- Audit log of all configuration changes

---

## Acceptance Criteria

- [ ] All 40+ external APIs tracked with rate limits
- [ ] Real-time usage tracking with <50ms latency
- [ ] Intelligent throttling prevents all API rate limit errors
- [ ] Queue depth never exceeds 10,000 items
- [ ] Cost optimization saves minimum 15% vs baseline
- [ ] 99.9% uptime for rate limiting service
- [ ] All alerts sent within 5 seconds of threshold breach
- [ ] Provider switching completes in <10 seconds
- [ ] Usage predictions accurate within 10% margin
- [ ] Integration tests pass with 100% coverage
- [ ] Performance tests meet SLA requirements
- [ ] Security audit passes with no critical findings
- [ ] Documentation complete with runbooks
- [ ] Dashboard shows real-time metrics
- [ ] Automated health checks pass every 5 minutes

---

## Monitoring Dashboard

### Key Metrics Display
1. **Real-time Usage**: Current usage vs limits for all services
2. **Queue Status**: Depth by service and priority
3. **Cost Tracking**: Daily/monthly spend with trends
4. **Provider Health**: Status and response times
5. **Alert History**: Recent alerts and resolutions
6. **Savings Tracker**: Cost optimization results

### Alert Thresholds
- Warning at 80% usage
- Critical at 95% usage
- Queue depth >5000
- Provider error rate >5%
- Cost budget >90%

### Automated Actions
- Switch providers at 95% usage
- Queue non-essential requests at 90%
- Send hourly digest when throttling
- Generate monthly cost report
- Cleanup queue items hourly
