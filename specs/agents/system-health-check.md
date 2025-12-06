# System Health Check Agent - Production Specification

## Overview

**Category**: System & Administration
**Priority**: Phase 7 - Polish & Scale
**Agent Name**: `system_health_check`
**Purpose**: Continuously monitor all external integrations, databases, and system services, alerting on failures and tracking uptime metrics.

---

## System Prompt

```
You are the System Health Check Agent for Smarter Team, a critical infrastructure monitoring system.

Your mission is to ensure the reliability and availability of all external integrations and system services. You proactively monitor service health, detect degradation patterns, and alert the team before failures impact operations.

**Core Responsibilities:**
1. Execute health checks for all configured integrations (APIs, databases, webhooks)
2. Analyze response times and detect performance degradation
3. Implement intelligent alerting with escalation rules (single failure = log, 2 failures = warning, 3+ = critical)
4. Track uptime metrics and calculate SLA compliance
5. Identify patterns in failures (time-based, service-specific, cascading)
6. Recommend fallback strategies when services are degraded or down

**Behavioral Guidelines:**
- Be vigilant but not alarmist - transient failures are normal
- Provide actionable context in alerts (error messages, response times, impact assessment)
- Track historical patterns to predict potential issues
- Prioritize critical services (database, Redis, Claude API) over optional integrations
- When a service recovers, send recovery notifications with downtime summary

**Decision Making:**
- Single failure: Log only, may be transient network issue
- 2 consecutive failures: Send warning alert, continue monitoring every 5 minutes
- 3+ consecutive failures: Send critical alert, mark service DOWN, activate fallback if available
- Response time >2x baseline: Mark as DEGRADED, send performance warning
- Critical services (DB, Redis, Claude): Alert immediately on first failure

**Communication Style:**
- Alerts should be concise, technical, and actionable
- Include: service name, status, error details, response time, impact, fallback status
- Use severity indicators: 🔴 CRITICAL, 🟡 WARNING, 🟢 RECOVERED
- Provide timestamp context (last healthy time, downtime duration)

You have access to tools for checking API health, database connectivity, webhook activity, and alert notifications. Use these tools systematically to maintain comprehensive system visibility.
```

---

## Agent Implementation

### Class Definition

```python
from typing import Any
from datetime import datetime, timedelta
from enum import Enum

from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger


class ServiceStatus(str, Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class HealthCheckAgent(BaseAgent):
    """
    System health check agent for monitoring integrations and infrastructure.

    Monitors all external services, databases, and webhooks with intelligent
    alerting and uptime tracking.
    """

    def __init__(self):
        super().__init__(
            name="system_health_check",
            description="Monitors system health and external integrations"
        )

        # Register tools
        self.register_tool(
            check_api_health,
            "check_api_health",
            "Check health of an external API integration"
        )
        self.register_tool(
            check_database_health,
            "check_database_health",
            "Check database connectivity and performance"
        )
        self.register_tool(
            check_webhook_activity,
            "check_webhook_activity",
            "Check if webhooks are being received"
        )
        self.register_tool(
            send_alert,
            "send_alert",
            "Send alert notification for service issues"
        )
        self.register_tool(
            get_service_metrics,
            "get_service_metrics",
            "Get historical uptime metrics for a service"
        )
        self.register_tool(
            record_health_check,
            "record_health_check",
            "Record health check result to database"
        )

    @property
    def system_prompt(self) -> str:
        # Return the system prompt from above
        return """..."""  # Full prompt from above

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process health check tasks.

        Supports:
        - run_all_checks: Run complete health check suite
        - check_service: Check specific service
        - get_status_report: Generate status page data
        """
        task_type = task.get("type")

        if task_type == "run_all_checks":
            return await self._run_all_checks(task.get("check_type", "hourly"))
        elif task_type == "check_service":
            return await self._check_specific_service(task.get("service_name"))
        elif task_type == "get_status_report":
            return await self._generate_status_report()
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _run_all_checks(self, check_type: str) -> dict[str, Any]:
        """Run all configured health checks."""
        # Implementation details
        pass

    async def _check_specific_service(self, service_name: str) -> dict[str, Any]:
        """Check a specific service."""
        # Implementation details
        pass

    async def _generate_status_report(self) -> dict[str, Any]:
        """Generate status page data."""
        # Implementation details
        pass
```

---

## Tool Definitions

### 1. check_api_health

**Purpose**: Check health of external API integrations

**Parameters**:
```python
{
    "service_name": str,          # e.g., "instantly", "stripe", "cal_com"
    "endpoint": str,              # API endpoint to check
    "method": str,                # HTTP method (GET, POST)
    "timeout": float,             # Timeout in seconds
    "expected_status": int,       # Expected HTTP status code
    "headers": dict[str, str],    # Optional custom headers
    "auth_type": str              # "bearer", "api_key", "oauth"
}
```

**Returns**:
```python
{
    "service": str,
    "status": ServiceStatus,           # HEALTHY, DEGRADED, DOWN
    "response_time_ms": float,
    "status_code": int | None,
    "error_message": str | None,
    "timestamp": datetime,
    "is_degraded": bool,               # True if >2x normal response time
    "baseline_response_time": float    # Historical average
}
```

**Implementation**:
```python
async def check_api_health(
    service_name: str,
    endpoint: str,
    method: str = "GET",
    timeout: float = 10.0,
    expected_status: int = 200,
    headers: dict[str, str] | None = None,
    auth_type: str = "bearer"
) -> dict[str, Any]:
    """
    Check health of an external API integration.

    Makes HTTP request to service endpoint and measures response time.
    Compares against historical baseline to detect degradation.
    """
    import httpx
    from time import time

    logger = get_agent_logger("health_check.api")
    start_time = time()

    try:
        # Get integration credentials from config
        from src.config import settings
        api_key = getattr(settings, f"{service_name.upper()}_API_KEY", None)

        # Build headers
        req_headers = headers or {}
        if auth_type == "bearer" and api_key:
            req_headers["Authorization"] = f"Bearer {api_key}"
        elif auth_type == "api_key" and api_key:
            req_headers["X-API-Key"] = api_key

        # Make request
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method, endpoint, headers=req_headers)

        response_time = (time() - start_time) * 1000  # Convert to ms

        # Get baseline response time from metrics
        baseline = await get_baseline_response_time(service_name)
        is_degraded = response_time > (baseline * 2) if baseline else False

        # Determine status
        status = ServiceStatus.HEALTHY
        if response.status_code != expected_status:
            status = ServiceStatus.DOWN
        elif is_degraded:
            status = ServiceStatus.DEGRADED

        return {
            "service": service_name,
            "status": status,
            "response_time_ms": response_time,
            "status_code": response.status_code,
            "error_message": None if status == ServiceStatus.HEALTHY else f"Status {response.status_code}",
            "timestamp": datetime.utcnow(),
            "is_degraded": is_degraded,
            "baseline_response_time": baseline
        }

    except httpx.TimeoutException:
        response_time = timeout * 1000
        logger.warning(f"{service_name} timeout after {timeout}s")
        return {
            "service": service_name,
            "status": ServiceStatus.DOWN,
            "response_time_ms": response_time,
            "status_code": None,
            "error_message": f"Timeout after {timeout}s",
            "timestamp": datetime.utcnow(),
            "is_degraded": False,
            "baseline_response_time": None
        }

    except Exception as e:
        logger.error(f"{service_name} check failed: {e}")
        return {
            "service": service_name,
            "status": ServiceStatus.DOWN,
            "response_time_ms": (time() - start_time) * 1000,
            "status_code": None,
            "error_message": str(e),
            "timestamp": datetime.utcnow(),
            "is_degraded": False,
            "baseline_response_time": None
        }
```

### 2. check_database_health

**Purpose**: Check database connectivity and performance

**Parameters**:
```python
{
    "database_name": str,    # "postgres_primary", "redis", "pinecone"
    "query": str | None,     # Test query (e.g., "SELECT 1")
    "timeout": float         # Timeout in seconds
}
```

**Returns**:
```python
{
    "database": str,
    "status": ServiceStatus,
    "response_time_ms": float,
    "error_message": str | None,
    "timestamp": datetime,
    "connection_pool_status": dict | None  # Pool size, active connections
}
```

**Implementation**:
```python
async def check_database_health(
    database_name: str,
    query: str | None = None,
    timeout: float = 5.0
) -> dict[str, Any]:
    """
    Check database connectivity and performance.

    Tests connection, executes simple query, measures response time.
    """
    from time import time
    from src.config import settings

    start_time = time()

    try:
        if database_name == "postgres_primary":
            # SQLAlchemy async check
            from sqlalchemy.ext.asyncio import create_async_engine
            engine = create_async_engine(settings.DATABASE_URL)

            async with engine.connect() as conn:
                result = await conn.execute(text(query or "SELECT 1"))
                await result.fetchone()

            response_time = (time() - start_time) * 1000

            return {
                "database": database_name,
                "status": ServiceStatus.HEALTHY,
                "response_time_ms": response_time,
                "error_message": None,
                "timestamp": datetime.utcnow(),
                "connection_pool_status": {
                    "pool_size": engine.pool.size(),
                    "checked_out": engine.pool.checked_out()
                }
            }

        elif database_name == "redis":
            # Redis check
            import redis.asyncio as redis
            client = redis.from_url(settings.REDIS_URL)

            await client.ping()
            response_time = (time() - start_time) * 1000

            info = await client.info()

            return {
                "database": database_name,
                "status": ServiceStatus.HEALTHY,
                "response_time_ms": response_time,
                "error_message": None,
                "timestamp": datetime.utcnow(),
                "connection_pool_status": {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown")
                }
            }

        elif database_name == "pinecone":
            # Pinecone check
            from pinecone import Pinecone
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)

            index = pc.Index(settings.PINECONE_INDEX_NAME)
            stats = index.describe_index_stats()

            response_time = (time() - start_time) * 1000

            return {
                "database": database_name,
                "status": ServiceStatus.HEALTHY,
                "response_time_ms": response_time,
                "error_message": None,
                "timestamp": datetime.utcnow(),
                "connection_pool_status": {
                    "total_vector_count": stats.total_vector_count,
                    "dimension": stats.dimension
                }
            }

    except Exception as e:
        response_time = (time() - start_time) * 1000
        return {
            "database": database_name,
            "status": ServiceStatus.DOWN,
            "response_time_ms": response_time,
            "error_message": str(e),
            "timestamp": datetime.utcnow(),
            "connection_pool_status": None
        }
```

### 3. check_webhook_activity

**Purpose**: Check if webhooks are being received within expected timeframe

**Parameters**:
```python
{
    "webhook_type": str,                # e.g., "instantly_reply", "fathom_recording"
    "last_received_threshold": int      # Alert if no webhook in N seconds
}
```

**Returns**:
```python
{
    "webhook_type": str,
    "status": ServiceStatus,
    "last_received_at": datetime | None,
    "time_since_last": float,           # Seconds since last webhook
    "threshold": int,
    "error_message": str | None
}
```

**Implementation**:
```python
async def check_webhook_activity(
    webhook_type: str,
    last_received_threshold: int
) -> dict[str, Any]:
    """
    Check if webhooks are being received within expected timeframe.

    Queries database for last received webhook of given type.
    """
    from sqlalchemy import select, func
    from src.database import get_async_session
    from src.models import WebhookLog  # Assuming webhook logging model

    async with get_async_session() as session:
        # Get last webhook received time
        stmt = select(WebhookLog.received_at).where(
            WebhookLog.webhook_type == webhook_type
        ).order_by(WebhookLog.received_at.desc()).limit(1)

        result = await session.execute(stmt)
        last_received = result.scalar_one_or_none()

        if not last_received:
            return {
                "webhook_type": webhook_type,
                "status": ServiceStatus.DOWN,
                "last_received_at": None,
                "time_since_last": float('inf'),
                "threshold": last_received_threshold,
                "error_message": "No webhooks ever received"
            }

        time_since = (datetime.utcnow() - last_received).total_seconds()

        status = ServiceStatus.HEALTHY
        error_message = None

        if time_since > last_received_threshold:
            status = ServiceStatus.DOWN
            error_message = f"No webhook in {time_since:.0f}s (threshold: {last_received_threshold}s)"

        return {
            "webhook_type": webhook_type,
            "status": status,
            "last_received_at": last_received,
            "time_since_last": time_since,
            "threshold": last_received_threshold,
            "error_message": error_message
        }
```

### 4. send_alert

**Purpose**: Send alert notification for service issues

**Parameters**:
```python
{
    "service": str,
    "status": ServiceStatus,
    "severity": str,                    # "warning", "critical", "recovery"
    "error_message": str,
    "response_time_ms": float | None,
    "consecutive_failures": int,
    "last_healthy_at": datetime | None,
    "affected_workflows": list[str],
    "fallback_status": str | None
}
```

**Returns**:
```python
{
    "alert_sent": bool,
    "alert_id": str,
    "channels": list[str],              # ["slack", "email"]
    "timestamp": datetime
}
```

**Implementation**:
```python
async def send_alert(
    service: str,
    status: ServiceStatus,
    severity: str,
    error_message: str,
    response_time_ms: float | None,
    consecutive_failures: int,
    last_healthy_at: datetime | None,
    affected_workflows: list[str],
    fallback_status: str | None
) -> dict[str, Any]:
    """
    Send alert notification via configured channels.

    Formats alert message and sends to Slack/email/PagerDuty.
    """
    from src.integrations.slack import send_slack_message
    from src.config import settings

    # Format alert message
    severity_emoji = {
        "critical": "🔴",
        "warning": "🟡",
        "recovery": "🟢"
    }

    emoji = severity_emoji.get(severity, "⚪")

    # Calculate downtime
    downtime = ""
    if last_healthy_at:
        duration = datetime.utcnow() - last_healthy_at
        downtime = f"\nDowntime: {duration.total_seconds():.0f}s"

    # Format message
    message = f"""
{emoji} SERVICE {severity.upper()}

Service: {service}
Status: {status}
Failures: {consecutive_failures}
{downtime}

Error: {error_message}
Response time: {response_time_ms:.0f}ms

Impact:
{chr(10).join(f"- {wf}" for wf in affected_workflows) if affected_workflows else "- No workflows affected"}

Fallback: {fallback_status or "None available"}
""".strip()

    # Send to configured channels
    channels_used = []

    if settings.SLACK_WEBHOOK_URL:
        await send_slack_message(message, channel="#alerts")
        channels_used.append("slack")

    # TODO: Add email, PagerDuty integrations

    # Log alert
    alert_id = f"alert_{service}_{int(datetime.utcnow().timestamp())}"

    return {
        "alert_sent": True,
        "alert_id": alert_id,
        "channels": channels_used,
        "timestamp": datetime.utcnow()
    }
```

### 5. get_service_metrics

**Purpose**: Get historical uptime metrics for a service

**Parameters**:
```python
{
    "service_name": str,
    "time_period": str,     # "24h", "7d", "30d"
    "metric_type": str      # "uptime", "response_time", "failure_rate"
}
```

**Returns**:
```python
{
    "service": str,
    "period": str,
    "uptime_percentage": float,
    "avg_response_time_ms": float,
    "max_response_time_ms": float,
    "total_checks": int,
    "failed_checks": int,
    "degraded_checks": int,
    "time_series": list[dict]  # [{timestamp, value}, ...]
}
```

### 6. record_health_check

**Purpose**: Record health check result to database

**Parameters**:
```python
{
    "service": str,
    "status": ServiceStatus,
    "response_time_ms": float,
    "error_message": str | None,
    "check_type": str,          # "api", "database", "webhook"
    "metadata": dict[str, Any]
}
```

**Returns**:
```python
{
    "id": str,                  # UUID
    "recorded": bool,
    "timestamp": datetime
}
```

---

## Database Schema

### health_checks Table

```sql
CREATE TABLE health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Service identification
    service VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,  -- 'api', 'database', 'webhook'
    endpoint VARCHAR(500),

    -- Health status
    status VARCHAR(20) NOT NULL,  -- 'healthy', 'degraded', 'down'
    response_time_ms NUMERIC(10, 2),
    status_code INTEGER,
    error_message TEXT,

    -- Context
    metadata JSONB,

    -- Indexes
    INDEX idx_service_created (service, created_at DESC),
    INDEX idx_status_created (status, created_at DESC),
    INDEX idx_service_status (service, status)
);
```

### service_failure_tracking Table

```sql
CREATE TABLE service_failure_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(100) NOT NULL UNIQUE,

    -- Failure tracking
    consecutive_failures INTEGER DEFAULT 0,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    last_healthy_at TIMESTAMP WITH TIME ZONE,
    current_status VARCHAR(20) DEFAULT 'healthy',

    -- Alert tracking
    last_alert_sent_at TIMESTAMP WITH TIME ZONE,
    alert_level VARCHAR(20),  -- 'warning', 'critical'

    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### uptime_metrics Table

```sql
CREATE TABLE uptime_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(100) NOT NULL,
    date DATE NOT NULL,

    -- Daily metrics
    total_checks INTEGER DEFAULT 0,
    successful_checks INTEGER DEFAULT 0,
    degraded_checks INTEGER DEFAULT 0,
    failed_checks INTEGER DEFAULT 0,

    -- Response time stats
    avg_response_time_ms NUMERIC(10, 2),
    max_response_time_ms NUMERIC(10, 2),
    min_response_time_ms NUMERIC(10, 2),

    -- Calculated metrics
    uptime_percentage NUMERIC(5, 2),

    UNIQUE(service, date),
    INDEX idx_service_date (service, date DESC)
);
```

---

## Health Check Configurations

### API Health Checks

```python
API_HEALTH_CHECKS = {
    # Lead Generation
    "instantly": {
        "endpoint": "https://api.instantly.ai/api/v1/account/status",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200,
        "check_interval": "hourly",
        "critical": False,
        "affected_workflows": ["cold_email_campaigns", "reply_handling"]
    },
    "reoon": {
        "endpoint": "https://api.reoon.com/api/v1/status",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200,
        "check_interval": "hourly",
        "critical": False,
        "affected_workflows": ["email_verification"]
    },
    "apify": {
        "endpoint": "https://api.apify.com/v2/acts",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200,
        "check_interval": "hourly",
        "critical": False,
        "affected_workflows": ["lead_scraping", "linkedin_enrichment"]
    },

    # Communication
    "cal_com": {
        "endpoint": "https://api.cal.com/v1/me",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200,
        "check_interval": "hourly",
        "critical": True,
        "affected_workflows": ["meeting_scheduling", "calendar_sync"]
    },

    # Payments
    "stripe": {
        "endpoint": "https://api.stripe.com/v1/balance",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200,
        "check_interval": "hourly",
        "critical": True,
        "affected_workflows": ["payment_processing", "invoice_collection"]
    },

    # Documents
    "pandadoc": {
        "endpoint": "https://api.pandadoc.com/public/v1/documents",
        "method": "GET",
        "timeout": 10,
        "expected_status": 200,
        "check_interval": "hourly",
        "critical": True,
        "affected_workflows": ["proposal_creation", "contract_signing"]
    },

    # AI Services
    "anthropic": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "method": "POST",
        "timeout": 30,
        "expected_status": 200,
        "check_interval": "5min",
        "critical": True,
        "affected_workflows": ["all_ai_agents"]
    },
    "perplexity": {
        "endpoint": "https://api.perplexity.ai/chat/completions",
        "method": "POST",
        "timeout": 30,
        "expected_status": 200,
        "check_interval": "hourly",
        "critical": False,
        "affected_workflows": ["research_agent"]
    }
}
```

### Database Health Checks

```python
DATABASE_HEALTH_CHECKS = {
    "postgres_primary": {
        "type": "postgres",
        "query": "SELECT 1",
        "timeout": 5,
        "check_interval": "5min",
        "critical": True,
        "affected_workflows": ["all_data_operations"]
    },
    "redis": {
        "type": "redis",
        "command": "PING",
        "timeout": 5,
        "check_interval": "5min",
        "critical": True,
        "affected_workflows": ["celery_tasks", "caching", "rate_limiting"]
    },
    "pinecone": {
        "type": "vector_db",
        "method": "describe_index_stats",
        "timeout": 10,
        "check_interval": "hourly",
        "critical": False,
        "affected_workflows": ["semantic_search", "vector_storage"]
    }
}
```

### Webhook Activity Checks

```python
WEBHOOK_ACTIVITY_CHECKS = {
    "instantly_reply": {
        "webhook_type": "instantly_reply",
        "threshold_seconds": 3600,  # 1 hour
        "check_interval": "hourly",
        "critical": False,
        "affected_workflows": ["email_response_handling"]
    },
    "fathom_recording": {
        "webhook_type": "fathom_recording",
        "threshold_seconds": 86400,  # 24 hours
        "check_interval": "hourly",
        "critical": False,
        "affected_workflows": ["call_transcript_processing"]
    },
    "stripe_payment": {
        "webhook_type": "stripe_payment",
        "threshold_seconds": 86400,  # 24 hours
        "check_interval": "hourly",
        "critical": True,
        "affected_workflows": ["payment_notifications"]
    },
    "cal_com_booking": {
        "webhook_type": "cal_com_booking",
        "threshold_seconds": 86400,  # 24 hours
        "check_interval": "hourly",
        "critical": True,
        "affected_workflows": ["meeting_notifications"]
    }
}
```

---

## Alert Rules & Escalation

### Alert Thresholds

```python
ALERT_RULES = {
    "single_failure": {
        "action": "log_only",
        "description": "May be transient network issue",
        "alert_sent": False
    },
    "two_consecutive_failures": {
        "action": "send_warning",
        "description": "Persistent issue detected",
        "alert_sent": True,
        "severity": "warning",
        "check_frequency": "5min"  # Increase check frequency
    },
    "three_plus_consecutive_failures": {
        "action": "send_critical",
        "description": "Service confirmed DOWN",
        "alert_sent": True,
        "severity": "critical",
        "mark_service_down": True,
        "activate_fallback": True
    },
    "degraded_performance": {
        "action": "send_warning",
        "description": "Response time >2x baseline",
        "alert_sent": True,
        "severity": "warning",
        "threshold_multiplier": 2.0
    },
    "critical_service_first_failure": {
        "action": "send_critical",
        "description": "Critical service failure requires immediate attention",
        "alert_sent": True,
        "severity": "critical",
        "applies_to": ["postgres_primary", "redis", "anthropic", "cal_com", "stripe"]
    }
}
```

### Escalation Chain

```python
ESCALATION_CHAIN = {
    "warning": {
        "channels": ["slack"],
        "recipients": ["#engineering-alerts"],
        "retry_interval": "15min"
    },
    "critical": {
        "channels": ["slack", "email", "sms"],
        "recipients": ["#engineering-alerts", "oncall@smarterteam.ai"],
        "retry_interval": "5min",
        "escalate_after": "30min"  # Escalate to leadership if unresolved
    },
    "recovery": {
        "channels": ["slack"],
        "recipients": ["#engineering-alerts"],
        "include_downtime_summary": True
    }
}
```

---

## Celery Task Configuration

### Periodic Health Check Tasks

```python
# In src/celery_app.py or src/tasks/health_check_tasks.py

from celery import Celery
from celery.schedules import crontab

celery_app = Celery("smarter_team")

# Schedule critical service checks every 5 minutes
celery_app.conf.beat_schedule = {
    "check-critical-services": {
        "task": "src.tasks.health_check_tasks.check_critical_services",
        "schedule": crontab(minute="*/5"),
        "args": ()
    },
    "check-all-services-hourly": {
        "task": "src.tasks.health_check_tasks.check_all_services",
        "schedule": crontab(minute=0),  # Every hour
        "args": ()
    },
    "calculate-daily-uptime-metrics": {
        "task": "src.tasks.health_check_tasks.calculate_daily_metrics",
        "schedule": crontab(hour=0, minute=5),  # Daily at 00:05
        "args": ()
    }
}
```

### Health Check Task Implementation

```python
from celery import Task
from src.celery_app import celery_app
from src.agents.system_health_check import HealthCheckAgent

@celery_app.task(bind=True, max_retries=3)
def check_critical_services(self: Task) -> dict[str, Any]:
    """
    Run health checks on critical services every 5 minutes.

    Critical services: postgres, redis, claude, cal.com, stripe
    """
    agent = HealthCheckAgent()

    result = await agent.process_task({
        "type": "run_all_checks",
        "check_type": "critical_only"
    })

    return result


@celery_app.task(bind=True, max_retries=3)
def check_all_services(self: Task) -> dict[str, Any]:
    """
    Run comprehensive health checks on all services hourly.
    """
    agent = HealthCheckAgent()

    result = await agent.process_task({
        "type": "run_all_checks",
        "check_type": "hourly"
    })

    return result


@celery_app.task(bind=True)
def calculate_daily_metrics(self: Task) -> dict[str, Any]:
    """
    Calculate and store daily uptime metrics.

    Runs at 00:05 UTC to aggregate previous day's data.
    """
    from src.services.health_metrics import calculate_uptime_metrics

    result = await calculate_uptime_metrics(days=1)
    return result
```

---

## Error Handling Strategy

### Failure Categories

1. **Transient Network Errors**
   - Action: Log, retry once, no alert
   - Examples: Connection reset, timeout on first attempt
   - Recovery: Automatic on next check

2. **Persistent Service Degradation**
   - Action: Log, send warning alert, increase check frequency
   - Examples: High latency, intermittent failures
   - Recovery: Monitor until resolved or escalated

3. **Complete Service Failure**
   - Action: Log, send critical alert, mark DOWN, activate fallback
   - Examples: 3+ consecutive failures, connection refused
   - Recovery: Manual investigation required

4. **Authentication/Authorization Errors**
   - Action: Send critical alert immediately
   - Examples: Invalid API key, expired token
   - Recovery: Manual credential update required

5. **Rate Limit Exceeded**
   - Action: Log, send warning, temporarily skip checks
   - Examples: 429 Too Many Requests
   - Recovery: Resume checks after rate limit reset

### Error Response Patterns

```python
ERROR_PATTERNS = {
    "network_timeout": {
        "indicators": ["timeout", "timed out", "no response"],
        "severity": "transient",
        "retry": True,
        "alert_threshold": 2
    },
    "authentication_failure": {
        "indicators": ["unauthorized", "invalid api key", "401", "403"],
        "severity": "critical",
        "retry": False,
        "alert_immediately": True
    },
    "rate_limit": {
        "indicators": ["rate limit", "429", "too many requests"],
        "severity": "warning",
        "retry": False,
        "backoff_minutes": 60
    },
    "service_unavailable": {
        "indicators": ["503", "502", "500", "service unavailable"],
        "severity": "critical",
        "retry": True,
        "alert_threshold": 3
    }
}
```

---

## Status Page Data Structure

### Public Status Page Response

```json
{
  "overall_status": "operational",
  "last_updated": "2025-12-05T19:30:00Z",
  "services": [
    {
      "name": "Email Campaigns",
      "category": "Lead Generation",
      "status": "operational",
      "uptime_30d": 99.9,
      "avg_response_time_ms": 145,
      "dependencies": ["instantly", "reoon"]
    },
    {
      "name": "Calendar Integration",
      "category": "Communication",
      "status": "operational",
      "uptime_30d": 99.8,
      "avg_response_time_ms": 320,
      "dependencies": ["cal_com"]
    },
    {
      "name": "Payment Processing",
      "category": "Finance",
      "status": "operational",
      "uptime_30d": 100.0,
      "avg_response_time_ms": 210,
      "dependencies": ["stripe"]
    },
    {
      "name": "AI Services",
      "category": "Core",
      "status": "degraded",
      "uptime_30d": 98.5,
      "avg_response_time_ms": 2450,
      "dependencies": ["anthropic", "perplexity"],
      "degradation_reason": "High response times on anthropic API"
    },
    {
      "name": "Database",
      "category": "Infrastructure",
      "status": "operational",
      "uptime_30d": 99.99,
      "avg_response_time_ms": 12,
      "dependencies": ["postgres_primary", "redis"]
    }
  ],
  "incidents": [
    {
      "id": "inc_2025_12_05_001",
      "title": "Anthropic API Degraded Performance",
      "status": "monitoring",
      "severity": "minor",
      "started_at": "2025-12-05T17:45:00Z",
      "updates": [
        {
          "timestamp": "2025-12-05T19:30:00Z",
          "message": "Monitoring elevated response times. Service remains functional."
        }
      ]
    }
  ],
  "uptime_summary": {
    "24h": 99.8,
    "7d": 99.5,
    "30d": 99.2
  }
}
```

---

## Testing Requirements

### Unit Tests (>85% coverage required)

**Test file**: `__tests__/unit/agents/test_health_check_agent.py`

```python
class TestHealthCheckAgentInitialization:
    def test_agent_initialization()
    def test_tools_registered()
    def test_system_prompt_defined()

class TestCheckAPIHealth:
    @pytest.mark.asyncio
    async def test_healthy_api_check()
    async def test_api_check_timeout()
    async def test_api_check_wrong_status_code()
    async def test_api_check_degraded_performance()
    async def test_api_check_authentication_error()

class TestCheckDatabaseHealth:
    @pytest.mark.asyncio
    async def test_postgres_health_check()
    async def test_redis_health_check()
    async def test_pinecone_health_check()
    async def test_database_connection_failure()

class TestCheckWebhookActivity:
    @pytest.mark.asyncio
    async def test_webhook_activity_healthy()
    async def test_webhook_activity_stale()
    async def test_webhook_never_received()

class TestSendAlert:
    @pytest.mark.asyncio
    async def test_send_warning_alert()
    async def test_send_critical_alert()
    async def test_send_recovery_alert()
    async def test_alert_formatting()
    async def test_multiple_channels()

class TestServiceMetrics:
    @pytest.mark.asyncio
    async def test_get_uptime_metrics()
    async def test_calculate_uptime_percentage()
    async def test_response_time_statistics()

class TestRecordHealthCheck:
    @pytest.mark.asyncio
    async def test_record_success()
    async def test_record_failure()
    async def test_database_persistence()

class TestAlertEscalation:
    @pytest.mark.asyncio
    async def test_single_failure_no_alert()
    async def test_two_failures_warning()
    async def test_three_failures_critical()
    async def test_critical_service_immediate_alert()
    async def test_degraded_performance_alert()
```

### Integration Tests

**Test file**: `__tests__/integration/test_health_check_integration.py`

```python
class TestHealthCheckIntegration:
    @pytest.mark.asyncio
    async def test_full_health_check_cycle()
    async def test_failure_detection_and_recovery()
    async def test_uptime_metrics_calculation()
    async def test_alert_delivery()
    async def test_status_page_generation()

class TestCeleryTasks:
    @pytest.mark.asyncio
    async def test_critical_services_check_task()
    async def test_hourly_check_task()
    async def test_daily_metrics_task()
```

### Fixtures

**Test file**: `__tests__/fixtures/health_check_fixtures.py`

```python
@pytest.fixture
def mock_health_check_agent():
    """Return mock HealthCheckAgent instance."""
    pass

@pytest.fixture
def mock_api_responses():
    """Return mock HTTP responses for various services."""
    pass

@pytest.fixture
def mock_database_connections():
    """Return mock database connections."""
    pass

@pytest.fixture
def sample_health_check_results():
    """Return sample health check results."""
    pass
```

---

## Implementation Checklist

### Phase 1: Core Health Checking
- [ ] Implement `HealthCheckAgent` class extending `BaseAgent`
- [ ] Implement `check_api_health` tool
- [ ] Implement `check_database_health` tool
- [ ] Implement `check_webhook_activity` tool
- [ ] Create database tables (`health_checks`, `service_failure_tracking`, `uptime_metrics`)
- [ ] Write unit tests for all health check tools (>85% coverage)

### Phase 2: Alert System
- [ ] Implement `send_alert` tool
- [ ] Implement failure tracking logic (consecutive failures)
- [ ] Implement alert escalation rules
- [ ] Integrate Slack notifications
- [ ] Integrate email notifications (optional)
- [ ] Write unit tests for alert system

### Phase 3: Metrics & Monitoring
- [ ] Implement `get_service_metrics` tool
- [ ] Implement `record_health_check` tool
- [ ] Create uptime calculation logic
- [ ] Implement daily metrics aggregation
- [ ] Create status page data generator
- [ ] Write unit tests for metrics

### Phase 4: Celery Integration
- [ ] Create `check_critical_services` Celery task
- [ ] Create `check_all_services` Celery task
- [ ] Create `calculate_daily_metrics` Celery task
- [ ] Configure Celery Beat schedules
- [ ] Write integration tests for Celery tasks

### Phase 5: Service Configuration
- [ ] Define all API health check configurations
- [ ] Define all database health check configurations
- [ ] Define all webhook activity check configurations
- [ ] Document fallback strategies for each service
- [ ] Create configuration loader

### Phase 6: Testing & Validation
- [ ] Achieve >85% test coverage
- [ ] Run integration tests with real services (dev environment)
- [ ] Test alert delivery to all channels
- [ ] Validate uptime calculations accuracy
- [ ] Test failure scenarios (timeouts, errors, degradation)

### Phase 7: Documentation & Deployment
- [ ] Update API documentation
- [ ] Create runbook for handling alerts
- [ ] Document escalation procedures
- [ ] Create status page endpoint
- [ ] Deploy to production with monitoring

---

## Dependencies

### Python Packages
- `httpx>=0.27.0` - HTTP client for API checks (already installed)
- `redis>=6.4.0` - Redis health checks (already installed)
- `sqlalchemy>=2.0.44` - Database health checks (already installed)
- `pinecone-client>=6.0.0` - Pinecone health checks (already installed)

### External Services
- Database: PostgreSQL (Supabase)
- Cache: Redis (Upstash)
- Vector DB: Pinecone
- Notifications: Slack (webhook), Email (optional)

### Agent Dependencies
None - this is an infrastructure agent with no dependencies on other agents.

---

## Human-in-the-Loop

### Approval Gates
None - fully automated monitoring agent.

### Manual Interventions
1. **Critical Service Down**: Requires investigation and resolution
2. **Prolonged Outages**: May require manual failover or vendor contact
3. **False Positives**: May require tuning of alert thresholds
4. **Credential Updates**: Manual update of API keys when expired

---

## Success Metrics

- **Uptime Tracking**: 99%+ accuracy in uptime calculations
- **Alert Precision**: <5% false positive rate
- **Detection Speed**: Critical failures detected within 5 minutes
- **Recovery Notification**: Recovery alerts sent within 1 minute
- **Coverage**: 100% of critical services monitored
- **Test Coverage**: >85% code coverage
- **Performance**: Health checks complete in <30s total

---

## Related Agents

This agent enables monitoring for all other agents by ensuring their dependencies are operational.

---

## Future Enhancements

1. **Predictive Failure Detection**: ML-based anomaly detection
2. **Auto-Remediation**: Automatic service restarts for known issues
3. **Cost Tracking**: Monitor API usage and costs
4. **Performance Benchmarking**: Compare services against SLA commitments
5. **Incident Management**: Auto-create incidents in PagerDuty
6. **Custom Health Check Logic**: Service-specific validation beyond HTTP checks
7. **Distributed Tracing**: Correlate health issues with request traces
