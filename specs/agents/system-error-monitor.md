# System Error Monitor Agent - Technical Specification

## Agent Metadata

**Category**: System & Administration
**Priority**: Phase 7 - Polish & Scale
**Dependencies**: All system components (receives errors from all agents)
**Coverage Requirement**: >85% (agent standard)

## Purpose

Continuously monitor system health, classify and triage errors, detect patterns, auto-resolve transient failures, and alert humans on critical issues. Serves as the observability backbone for the multi-agent system.

## Architecture

### Agent Class

```python
from src.agents.base_agent import BaseAgent
from typing import Any, Literal

class SystemErrorMonitorAgent(BaseAgent):
    """
    Monitors system errors, classifies severity, detects patterns,
    auto-resolves transient failures, and generates alerts/reports.
    """

    def __init__(
        self,
        sentry_dsn: str | None = None,
        slack_webhook: str | None = None,
        telegram_bot_token: str | None = None,
        telegram_chat_id: str | None = None,
        pagerduty_integration_key: str | None = None,
    ):
        super().__init__(
            name="system_error_monitor",
            description="System error monitoring, classification, and alerting"
        )
        self.sentry_client = SentryClient(dsn=sentry_dsn) if sentry_dsn else None
        self.slack_client = SlackClient(webhook_url=slack_webhook) if slack_webhook else None
        self.telegram_client = TelegramClient(
            bot_token=telegram_bot_token,
            chat_id=telegram_chat_id
        ) if telegram_bot_token and telegram_chat_id else None
        self.pagerduty_client = PagerDutyClient(
            integration_key=pagerduty_integration_key
        ) if pagerduty_integration_key else None

        # Register tools
        self.register_tool(self._log_error, "log_error", "Log and classify an error")
        self.register_tool(self._detect_patterns, "detect_patterns", "Detect error patterns")
        self.register_tool(self._generate_report, "generate_report", "Generate daily error report")
        self.register_tool(self._resolve_error, "resolve_error", "Mark error as resolved")
        self.register_tool(self._check_health, "check_health", "Check system health status")
```

### System Prompt

```python
@property
def system_prompt(self) -> str:
    return """You are the System Error Monitor Agent for Smarter Team.

Your responsibilities:
1. Log and classify all system errors by severity (CRITICAL, HIGH, MEDIUM, LOW)
2. Detect error patterns (spikes, recurring issues, cascade failures, time-based)
3. Auto-resolve transient errors (rate limits, network issues)
4. Alert humans on critical/high severity errors
5. Generate daily error reports with insights and recommendations

Severity Classification Rules:

CRITICAL (immediate alert, wake human if needed):
- Database connection lost
- Payment processing failure
- Authentication system down
- Data corruption detected
- Multiple systems failing simultaneously (cascade)

HIGH (urgent alert, fix within 1 hour):
- Agent completely failed
- External API down (non-transient)
- Webhook delivery failed 3+ times
- Email delivery blocked
- Single system failure affecting operations

MEDIUM (alert, fix within 24 hours):
- Agent partial failure (some tasks succeed)
- API rate limit hit (if not auto-resolved)
- Slow response times (>5s)
- Non-critical integration issue

LOW (log only, review in daily report):
- Validation errors (expected user input issues)
- Expected failures (invalid email format)
- Minor integration hiccups (auto-resolved)
- Transient network errors (successfully retried)

Auto-Resolution Strategies:

API Rate Limit:
- Queue the request with exponential backoff
- Retry after rate limit window
- Mark resolved if succeeds within 3 retries

Temporary Network Issue:
- Auto-retry with exponential backoff (1s, 2s, 4s)
- Mark resolved if succeeds within 3 retries
- Escalate to MEDIUM if all retries fail

Invalid Data:
- Log the validation error with context
- Skip the record and continue processing
- Mark as expected failure (LOW severity)

Pattern Detection:

Spike Pattern:
- >10 errors from same source in 5 minutes
- Alert immediately as HIGH severity
- Likely indicates systemic issue

Recurring Pattern:
- Same error >5 times in 1 hour
- Flag for investigation
- May indicate underlying bug

Cascade Failure:
- Multiple agents/systems failing within 5 minutes
- Escalate to CRITICAL
- Likely root cause affecting dependencies

Time-Based Pattern:
- Errors occurring at specific times/intervals
- Flag as potential scheduled job issue
- Include in daily report for review

Always provide:
- Clear, actionable error messages
- Relevant context and stack traces
- Suggested remediation steps
- Links to error dashboard/Sentry

Be concise, professional, and focus on actionability."""
```

## Tool Definitions

### 1. log_error

**Purpose**: Log an error, classify severity, attempt auto-resolution, and alert if needed.

**Signature**:
```python
async def _log_error(
    self,
    agent_name: str,
    error_type: str,
    error_message: str,
    stack_trace: str,
    context: dict[str, Any],
    retry_count: int = 0,
) -> dict[str, Any]:
    """
    Log an error to database and Sentry, classify severity,
    attempt auto-resolution, and send alerts.

    Args:
        agent_name: Name of the agent that encountered the error
        error_type: Type of error (api_error, database_error, validation_error, etc.)
        error_message: Human-readable error message
        stack_trace: Full stack trace
        context: Additional context (lead_id, request_id, etc.)
        retry_count: Number of retry attempts (for auto-resolution)

    Returns:
        {
            "error_id": "uuid",
            "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
            "auto_resolved": bool,
            "alerts_sent": ["slack", "pagerduty"],
            "pattern_detected": "spike" | "recurring" | "cascade" | "time_based" | None
        }
    """
```

**Implementation Flow**:
1. Generate error ID (UUID)
2. Classify severity based on error type and context
3. Check if error can be auto-resolved (rate limits, network issues)
4. Log to database (`error_logs` table)
5. Send to Sentry (if configured)
6. Detect patterns (check recent errors)
7. Send alerts based on severity:
   - CRITICAL: Slack + Telegram + PagerDuty (if configured)
   - HIGH: Slack + Telegram
   - MEDIUM: Slack only
   - LOW: No immediate alert
8. Return error metadata

### 2. detect_patterns

**Purpose**: Analyze recent errors for patterns (spikes, recurring, cascade, time-based).

**Signature**:
```python
async def _detect_patterns(
    self,
    lookback_minutes: int = 60,
) -> dict[str, Any]:
    """
    Analyze recent errors for patterns.

    Args:
        lookback_minutes: How far back to analyze (default 60 minutes)

    Returns:
        {
            "patterns": [
                {
                    "type": "spike" | "recurring" | "cascade" | "time_based",
                    "description": "10+ errors from lead_list_builder in 5 minutes",
                    "severity": "HIGH",
                    "affected_agents": ["lead_list_builder"],
                    "error_count": 12,
                    "first_occurrence": "2025-12-05T10:00:00Z",
                    "last_occurrence": "2025-12-05T10:05:00Z"
                }
            ],
            "total_errors": 45,
            "critical_count": 2,
            "high_count": 5,
            "medium_count": 15,
            "low_count": 23
        }
    """
```

**Implementation Flow**:
1. Query `error_logs` for errors in last N minutes
2. Group by agent, error type, and time windows
3. Apply pattern detection rules:
   - **Spike**: >10 errors from same source in 5 minutes
   - **Recurring**: Same error >5 times in 1 hour
   - **Cascade**: >3 different agents failing in 5 minutes
   - **Time-based**: Errors at regular intervals (using modulo time analysis)
4. Return detected patterns with metadata

### 3. generate_report

**Purpose**: Generate comprehensive daily error report.

**Signature**:
```python
async def _generate_report(
    self,
    date: str,  # YYYY-MM-DD format
    send_alerts: bool = True,
) -> dict[str, Any]:
    """
    Generate daily error report.

    Args:
        date: Date for report (default: yesterday)
        send_alerts: Whether to send report via Slack/Telegram

    Returns:
        {
            "report_id": "uuid",
            "date": "2025-12-05",
            "summary": {
                "total_errors": 124,
                "critical_count": 3,
                "high_count": 12,
                "medium_count": 45,
                "low_count": 64,
                "auto_resolved_count": 52,
                "unresolved_critical_count": 1
            },
            "top_errors": [
                {
                    "rank": 1,
                    "error_type": "api_rate_limit",
                    "count": 35,
                    "agent": "lead_list_builder",
                    "last_occurrence": "2025-12-05T18:30:00Z"
                }
            ],
            "patterns": [...],
            "recommendations": [
                "Increase rate limit handling for lead_list_builder",
                "Investigate recurring database timeout in sales agent"
            ],
            "report_text": "📊 DAILY ERROR REPORT - 2025-12-05\n\n..."
        }
    """
```

**Implementation Flow**:
1. Query all errors for specified date
2. Group and aggregate by severity, type, agent
3. Detect patterns
4. Identify top errors (by count)
5. Generate recommendations using Claude (analyze patterns)
6. Format report using template
7. Send via Slack/Telegram if `send_alerts=True`
8. Store report in database (`error_reports` table)

### 4. resolve_error

**Purpose**: Mark error as resolved with notes.

**Signature**:
```python
async def _resolve_error(
    self,
    error_id: str,
    resolution_notes: str,
    auto_resolved: bool = False,
) -> dict[str, Any]:
    """
    Mark an error as resolved.

    Args:
        error_id: UUID of the error
        resolution_notes: How the error was resolved
        auto_resolved: Whether this was auto-resolved

    Returns:
        {
            "error_id": "uuid",
            "resolved": true,
            "resolved_at": "2025-12-05T10:15:00Z",
            "resolution_notes": "Auto-resolved after successful retry"
        }
    """
```

**Implementation Flow**:
1. Validate error exists
2. Update `error_logs` table:
   - `resolved = true`
   - `resolved_at = now()`
   - `resolution_notes = notes`
3. Log resolution action
4. Return confirmation

### 5. check_health

**Purpose**: Check overall system health based on recent errors.

**Signature**:
```python
async def _check_health(
    self,
    lookback_minutes: int = 15,
) -> dict[str, Any]:
    """
    Check system health status.

    Args:
        lookback_minutes: Time window to analyze

    Returns:
        {
            "status": "healthy" | "degraded" | "critical",
            "score": 95.5,  # 0-100 health score
            "critical_errors": 0,
            "high_errors": 2,
            "degraded_agents": [],
            "failing_agents": [],
            "message": "System is healthy. 2 high-severity errors in last 15 minutes."
        }
    """
```

**Implementation Flow**:
1. Query errors in last N minutes
2. Calculate health score:
   - Start at 100
   - Deduct 20 per CRITICAL error
   - Deduct 10 per HIGH error
   - Deduct 2 per MEDIUM error
   - Deduct 0.5 per LOW error
3. Determine status:
   - `healthy`: score >= 90, no CRITICAL
   - `degraded`: score >= 70, no CRITICAL
   - `critical`: score < 70 or any CRITICAL
4. Identify degraded/failing agents
5. Return health report

## Database Schema

### error_logs Table

```sql
CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Error source
    agent_name VARCHAR(255) NOT NULL,
    error_type VARCHAR(100) NOT NULL,  -- api_error, database_error, validation_error, etc.

    -- Error details
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    severity VARCHAR(20) NOT NULL,  -- CRITICAL, HIGH, MEDIUM, LOW

    -- Context
    context JSONB DEFAULT '{}',  -- lead_id, request_id, retry_count, etc.

    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    auto_resolved BOOLEAN DEFAULT FALSE,

    -- Indexes for fast queries
    INDEX idx_error_logs_created_at ON error_logs(created_at DESC),
    INDEX idx_error_logs_agent_name ON error_logs(agent_name),
    INDEX idx_error_logs_severity ON error_logs(severity),
    INDEX idx_error_logs_resolved ON error_logs(resolved),
    INDEX idx_error_logs_error_type ON error_logs(error_type)
);
```

### error_alerts Table

```sql
CREATE TABLE error_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Alert details
    error_id UUID REFERENCES error_logs(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,  -- slack, telegram, pagerduty

    -- Message
    message TEXT NOT NULL,

    -- Delivery status
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMPTZ,
    delivery_status VARCHAR(50),  -- pending, sent, failed
    error_message TEXT,

    INDEX idx_error_alerts_error_id ON error_alerts(error_id),
    INDEX idx_error_alerts_created_at ON error_alerts(created_at DESC)
);
```

### error_reports Table

```sql
CREATE TABLE error_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Report metadata
    report_date DATE NOT NULL UNIQUE,

    -- Summary stats
    total_errors INT NOT NULL,
    critical_count INT NOT NULL,
    high_count INT NOT NULL,
    medium_count INT NOT NULL,
    low_count INT NOT NULL,
    auto_resolved_count INT NOT NULL,
    unresolved_critical_count INT NOT NULL,

    -- Report content
    top_errors JSONB NOT NULL,  -- Array of top errors
    patterns JSONB NOT NULL,    -- Detected patterns
    recommendations JSONB NOT NULL,  -- AI-generated recommendations
    report_text TEXT NOT NULL,  -- Formatted report

    INDEX idx_error_reports_date ON error_reports(report_date DESC)
);
```

## Integration Clients

### 1. SentryClient

```python
from src.integrations.base import BaseIntegrationClient
import sentry_sdk

class SentryClient:
    """Sentry error tracking integration."""

    def __init__(self, dsn: str | None):
        if dsn:
            sentry_sdk.init(
                dsn=dsn,
                traces_sample_rate=0.1,  # 10% performance monitoring
                profiles_sample_rate=0.1,
            )
        self.enabled = bool(dsn)

    def capture_error(
        self,
        error_message: str,
        error_type: str,
        stack_trace: str,
        context: dict[str, Any],
        severity: str,
    ) -> str | None:
        """Capture error in Sentry. Returns event ID."""
        if not self.enabled:
            return None

        with sentry_sdk.push_scope() as scope:
            scope.set_level(self._map_severity(severity))
            scope.set_context("error_details", context)
            scope.set_tag("agent_name", context.get("agent_name", "unknown"))
            scope.set_tag("error_type", error_type)

            event_id = sentry_sdk.capture_message(
                error_message,
                level=self._map_severity(severity),
            )
            return event_id

    def _map_severity(self, severity: str) -> str:
        """Map our severity to Sentry levels."""
        mapping = {
            "CRITICAL": "fatal",
            "HIGH": "error",
            "MEDIUM": "warning",
            "LOW": "info",
        }
        return mapping.get(severity, "error")
```

### 2. SlackClient

```python
from src.integrations.base import BaseIntegrationClient

class SlackClient(BaseIntegrationClient):
    """Slack webhook integration for alerts."""

    def __init__(self, webhook_url: str | None):
        if webhook_url:
            super().__init__(
                name="slack",
                base_url=webhook_url,
                api_key=None,  # Webhook URL is the auth
                timeout=10.0
            )
        self.enabled = bool(webhook_url)

    async def send_alert(
        self,
        message: str,
        severity: str,
        color: str | None = None,
    ) -> bool:
        """Send alert to Slack."""
        if not self.enabled:
            return False

        color = color or self._severity_color(severity)

        payload = {
            "attachments": [
                {
                    "color": color,
                    "text": message,
                    "mrkdwn_in": ["text"],
                }
            ]
        }

        try:
            await self._request("POST", "", json=payload)
            return True
        except Exception:
            return False

    def _severity_color(self, severity: str) -> str:
        """Map severity to Slack color."""
        colors = {
            "CRITICAL": "danger",
            "HIGH": "warning",
            "MEDIUM": "#ffa500",  # Orange
            "LOW": "good",
        }
        return colors.get(severity, "good")
```

### 3. TelegramClient

```python
from src.integrations.base import BaseIntegrationClient

class TelegramClient(BaseIntegrationClient):
    """Telegram bot integration for alerts."""

    def __init__(self, bot_token: str | None, chat_id: str | None):
        if bot_token and chat_id:
            super().__init__(
                name="telegram",
                base_url=f"https://api.telegram.org/bot{bot_token}",
                api_key=None,
                timeout=10.0
            )
            self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)

    async def send_alert(self, message: str) -> bool:
        """Send alert to Telegram."""
        if not self.enabled:
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            await self._request("POST", "/sendMessage", json=payload)
            return True
        except Exception:
            return False
```

### 4. PagerDutyClient

```python
from src.integrations.base import BaseIntegrationClient

class PagerDutyClient(BaseIntegrationClient):
    """PagerDuty integration for critical alerts."""

    def __init__(self, integration_key: str | None):
        if integration_key:
            super().__init__(
                name="pagerduty",
                base_url="https://events.pagerduty.com/v2",
                api_key=integration_key,
                timeout=10.0
            )
        self.enabled = bool(integration_key)

    async def trigger_incident(
        self,
        error_id: str,
        summary: str,
        severity: str,
        details: dict[str, Any],
    ) -> bool:
        """Trigger PagerDuty incident."""
        if not self.enabled:
            return False

        payload = {
            "routing_key": self.api_key,
            "event_action": "trigger",
            "dedup_key": error_id,
            "payload": {
                "summary": summary,
                "severity": severity.lower(),
                "source": "smarter-team",
                "custom_details": details,
            },
        }

        try:
            await self._request("POST", "/enqueue", json=payload)
            return True
        except Exception:
            return False
```

## Alert Templates

### Critical Alert Template

```python
def format_critical_alert(
    system_name: str,
    error_message: str,
    timestamp: str,
    context: dict[str, Any],
    stack_trace_summary: str,
    error_dashboard_link: str,
) -> str:
    return f"""🚨 CRITICAL ERROR

System: {system_name}
Error: {error_message}
Time: {timestamp}

IMMEDIATE ACTION REQUIRED

Context:
{_format_context(context)}

Stack trace:
{stack_trace_summary}

Dashboard: {error_dashboard_link}"""
```

### High Severity Alert Template

```python
def format_high_alert(
    agent_name: str,
    error_type: str,
    error_message: str,
    timestamp: str,
    count: int,
    context: dict[str, Any],
) -> str:
    return f"""⚠️ HIGH SEVERITY ERROR

Agent: {agent_name}
Error: {error_type}
Message: {error_message}
Time: {timestamp}

Action needed within 1 hour.

Occurrences in last hour: {count}

Context:
{_format_context(context)}"""
```

### Daily Report Template

```python
def format_daily_report(
    date: str,
    summary: dict[str, int],
    top_errors: list[dict],
    patterns: list[dict],
    resolved_count: int,
    unresolved_critical_count: int,
) -> str:
    report = f"""📊 DAILY ERROR REPORT - {date}

SUMMARY
- Critical: {summary['critical_count']}
- High: {summary['high_count']}
- Medium: {summary['medium_count']}
- Low: {summary['low_count']}
- Total: {summary['total_errors']}

TOP ERRORS
"""

    for i, error in enumerate(top_errors[:10], 1):
        report += f"""{i}. {error['error_type']} ({error['count']}x)
   Agent: {error['agent']}
   Last: {error['last_occurrence']}

"""

    if patterns:
        report += "PATTERNS DETECTED\n"
        for pattern in patterns:
            report += f"- {pattern['description']}\n"
        report += "\n"

    report += f"""RESOLVED TODAY
{resolved_count} errors resolved

NEEDS ATTENTION
{unresolved_critical_count} critical errors unresolved"""

    return report
```

## Celery Tasks

### Monitor Errors Task (Continuous)

```python
from src.celery_app import celery_app

@celery_app.task(bind=True, max_retries=0)
def monitor_errors_continuously(self):
    """
    Continuous error monitoring (runs every 5 minutes).
    Checks for error spikes and patterns.
    """
    from src.agents.system_error_monitor.agent import SystemErrorMonitorAgent

    agent = SystemErrorMonitorAgent()

    # Detect patterns in last 60 minutes
    patterns = await agent._detect_patterns(lookback_minutes=60)

    # Alert on detected patterns
    for pattern in patterns.get("patterns", []):
        if pattern["severity"] in ["CRITICAL", "HIGH"]:
            # Send alerts
            await agent._send_pattern_alert(pattern)

    return {"status": "completed", "patterns_detected": len(patterns.get("patterns", []))}
```

### Generate Daily Report Task

```python
@celery_app.task(bind=True, max_retries=3)
def generate_daily_error_report(self, date: str | None = None):
    """
    Generate and send daily error report (runs daily at 8:00 AM).
    """
    from src.agents.system_error_monitor.agent import SystemErrorMonitorAgent
    from datetime import date as date_module, timedelta

    agent = SystemErrorMonitorAgent()

    # Default to yesterday
    if not date:
        yesterday = date_module.today() - timedelta(days=1)
        date = yesterday.strftime("%Y-%m-%d")

    report = await agent._generate_report(date=date, send_alerts=True)

    return {"status": "completed", "report_id": report["report_id"]}
```

### Check System Health Task

```python
@celery_app.task(bind=True, max_retries=0)
def check_system_health(self):
    """
    Check system health status (runs every 5 minutes).
    """
    from src.agents.system_error_monitor.agent import SystemErrorMonitorAgent

    agent = SystemErrorMonitorAgent()

    health = await agent._check_health(lookback_minutes=15)

    # Alert if system is critical
    if health["status"] == "critical":
        await agent._send_health_alert(health)

    return health
```

## Celery Beat Schedule

```python
# In src/celery_app.py or config

from celery.schedules import crontab

beat_schedule = {
    "monitor-error-patterns": {
        "task": "src.tasks.error_monitoring_tasks.monitor_errors_continuously",
        "schedule": 300.0,  # Every 5 minutes
    },
    "check-system-health": {
        "task": "src.tasks.error_monitoring_tasks.check_system_health",
        "schedule": 300.0,  # Every 5 minutes
    },
    "generate-daily-error-report": {
        "task": "src.tasks.error_monitoring_tasks.generate_daily_error_report",
        "schedule": crontab(hour=8, minute=0),  # Daily at 8:00 AM
    },
}
```

## Testing Requirements

Coverage requirement: **>85%** (agent standard)

### Unit Tests

**File**: `__tests__/unit/agents/test_system_error_monitor.py`

**Test Cases**:
1. **Error Classification**
   - Test CRITICAL classification (database connection lost, payment failure)
   - Test HIGH classification (agent failure, API down)
   - Test MEDIUM classification (rate limits, slow responses)
   - Test LOW classification (validation errors, expected failures)

2. **Pattern Detection**
   - Test spike detection (>10 errors in 5 minutes)
   - Test recurring error detection (same error >5 times in 1 hour)
   - Test cascade failure detection (multiple agents failing)
   - Test time-based pattern detection

3. **Auto-Resolution**
   - Test rate limit auto-resolution (queue and retry)
   - Test network error auto-resolution (retry with backoff)
   - Test invalid data handling (log and skip)
   - Test failed auto-resolution escalation

4. **Alert Formatting**
   - Test critical alert template formatting
   - Test high severity alert template
   - Test daily report template
   - Test health status messages

5. **Health Score Calculation**
   - Test healthy status (score >= 90, no CRITICAL)
   - Test degraded status (score >= 70, no CRITICAL)
   - Test critical status (score < 70 or any CRITICAL)
   - Test score deductions per severity level

6. **Tool Methods**
   - Test `_log_error` with various error types
   - Test `_detect_patterns` with different time windows
   - Test `_generate_report` for specific dates
   - Test `_resolve_error` with valid/invalid IDs
   - Test `_check_health` with different error scenarios

### Integration Tests

**File**: `__tests__/integration/test_error_monitor_integration.py`

**Test Cases**:
1. **End-to-End Error Flow**
   - Log error → classify → detect pattern → send alert
   - Test database persistence
   - Test Sentry integration (mocked)
   - Test Slack/Telegram alerts (mocked)

2. **Daily Report Generation**
   - Insert errors for test date
   - Generate report
   - Verify summary statistics
   - Verify top errors ranking
   - Verify report delivery

3. **Pattern Detection Integration**
   - Insert spike pattern errors
   - Run pattern detection
   - Verify pattern identified
   - Verify alert sent

4. **Auto-Resolution Flow**
   - Log rate limit error
   - Trigger auto-resolution
   - Verify retry logic
   - Verify resolution marked in database

5. **Health Check Integration**
   - Insert various severity errors
   - Run health check
   - Verify status calculation
   - Verify degraded agents list

### Fixtures

**File**: `__tests__/fixtures/error_monitor_fixtures.py`

```python
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

@pytest.fixture
def sample_critical_error():
    return {
        "agent_name": "payment_processor",
        "error_type": "payment_failure",
        "error_message": "Stripe API returned 500: Internal Server Error",
        "stack_trace": "Traceback (most recent call last)...",
        "context": {
            "payment_id": str(uuid4()),
            "amount": 5000,
            "customer_id": str(uuid4()),
        },
        "retry_count": 0,
    }

@pytest.fixture
def sample_rate_limit_error():
    return {
        "agent_name": "lead_list_builder",
        "error_type": "api_rate_limit",
        "error_message": "Apify API rate limit exceeded",
        "stack_trace": "Traceback (most recent call last)...",
        "context": {
            "lead_id": str(uuid4()),
            "request_id": str(uuid4()),
        },
        "retry_count": 1,
    }

@pytest.fixture
def error_spike_data():
    """12 errors from same agent in 3 minutes (spike pattern)."""
    base_time = datetime.utcnow()
    errors = []
    for i in range(12):
        errors.append({
            "agent_name": "sales",
            "error_type": "api_error",
            "error_message": f"API call failed #{i}",
            "stack_trace": "...",
            "context": {},
            "created_at": base_time + timedelta(seconds=i * 15),
        })
    return errors

@pytest.fixture
def mock_sentry_client(mocker):
    return mocker.patch("src.agents.system_error_monitor.integrations.SentryClient")

@pytest.fixture
def mock_slack_client(mocker):
    return mocker.patch("src.agents.system_error_monitor.integrations.SlackClient")
```

## Error Handling & Edge Cases

### Edge Cases to Handle

1. **Database Unavailable**
   - Fallback to local logging (file-based)
   - Queue errors in Redis for later processing
   - Alert via Sentry/Slack without database

2. **Alert Service Down**
   - Log failed alert attempt
   - Retry with exponential backoff
   - Fallback to alternative service (Slack → Telegram)

3. **Circular Error Logging**
   - Prevent error monitor from logging its own errors infinitely
   - Use circuit breaker pattern
   - Track error logging depth

4. **Error Flood**
   - Rate limit error logging (max 100 errors/minute)
   - Aggregate duplicate errors
   - Send single "error storm detected" alert

5. **Missing Context**
   - Handle errors with incomplete context gracefully
   - Provide default values for required fields
   - Log warning about missing data

## Performance Considerations

1. **Database Indexes**
   - Index on `created_at` for time-based queries
   - Index on `agent_name` for agent-specific queries
   - Index on `severity` for filtering
   - Composite index on `(resolved, severity, created_at)`

2. **Query Optimization**
   - Use time-windowed queries (last 60 minutes, not all-time)
   - Implement pagination for large result sets
   - Cache pattern detection results (5-minute TTL)

3. **Alert Throttling**
   - Prevent duplicate alerts for same error within 5 minutes
   - Batch LOW severity errors into hourly digest
   - Use deduplication key for PagerDuty

4. **Async Processing**
   - All integration calls must be async
   - Use concurrent alert sending (asyncio.gather)
   - Non-blocking database writes

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0

# Optional - Error Tracking
SENTRY_DSN=https://...@sentry.io/...

# Optional - Alerts (at least one recommended)
SLACK_ERROR_WEBHOOK_URL=https://hooks.slack.com/services/...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
PAGERDUTY_INTEGRATION_KEY=...  # For critical alerts only
```

## Dependencies

Add to `app/backend/pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies
    "sentry-sdk>=2.0.0",  # Error tracking
]
```

## Implementation Checklist

- [ ] Create agent class extending BaseAgent
- [ ] Implement system prompt with severity rules
- [ ] Implement `_log_error` tool with classification logic
- [ ] Implement `_detect_patterns` tool with all pattern types
- [ ] Implement `_generate_report` tool with Claude-powered insights
- [ ] Implement `_resolve_error` tool
- [ ] Implement `_check_health` tool with scoring
- [ ] Create integration clients (Sentry, Slack, Telegram, PagerDuty)
- [ ] Create database models (error_logs, error_alerts, error_reports)
- [ ] Create database migration
- [ ] Implement Celery tasks (monitor, health check, daily report)
- [ ] Configure Celery beat schedule
- [ ] Write unit tests (>85% coverage)
- [ ] Write integration tests
- [ ] Create test fixtures
- [ ] Add environment variables to `.env.example`
- [ ] Update CLAUDE.md with agent documentation
- [ ] Test alert delivery (Slack, Telegram, PagerDuty)
- [ ] Test auto-resolution logic
- [ ] Test pattern detection with real data
- [ ] Verify daily report generation

## Future Enhancements

1. **Machine Learning**
   - Train model to predict error severity
   - Auto-classify error types using embeddings
   - Anomaly detection for unusual error patterns

2. **Root Cause Analysis**
   - Use Claude to analyze error chains
   - Suggest likely root causes
   - Recommend preventive measures

3. **Incident Management**
   - Track incident lifecycle (detected → acknowledged → resolved)
   - Post-mortem report generation
   - Incident timeline visualization

4. **Proactive Monitoring**
   - Predict errors before they occur
   - Monitor system metrics (CPU, memory, latency)
   - Alert on degrading trends

5. **Error Replay**
   - Store request context for reproduction
   - Automated error reproduction in test environment
   - Integration with debugging tools
