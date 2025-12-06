# Campaign Deliverability Monitor - Agent Specification

**Status:** Ready to Build
**Last Updated:** 2025-12-05
**Refined From:** plan/agents/campaign-deliverability-monitor.md

## Overview

Autonomous monitoring agent that tracks email campaign deliverability metrics in real-time, maintains sender reputation health, and automatically responds to deliverability issues. Processes webhook events from Instantly, calculates health scores, triggers alerts when thresholds are exceeded, and can auto-pause at-risk campaigns to protect sender reputation.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Instantly API  │───▶│  Webhook Handler │───▶│ Deliverability  │
│   (Webhooks)    │    │   (FastAPI)      │    │    Monitor      │
└─────────────────┘    └──────────────────┘    │     Agent       │
                                                └────────┬────────┘
                                                         │
                                ┌────────────────────────┼─────────────────────────┐
                                │                        │                         │
                       ┌────────▼────────┐    ┌─────────▼─────────┐    ┌────────▼───────┐
                       │ Metrics Storage │    │ Alert Generation  │    │ Campaign Pause │
                       │ (PostgreSQL)    │    │ (Notifications)  │    │ (Instantly API) │
                       └─────────────────┘    └──────────────────┘    └────────────────┘
```

## Configuration

```python
class DeliverabilityMonitorConfig:
    """Configuration for the Deliverability Monitor agent."""

    # Agent settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower for more consistent monitoring
    max_retries: int = 3
    timeout_seconds: int = 30

    # Thresholds
    bounce_rate_warning: float = 2.0  # Percentage
    bounce_rate_critical: float = 5.0
    spam_rate_warning: float = 0.1  # Percentage
    spam_rate_critical: float = 0.3

    # Time windows for calculations (hours)
    bounce_window: int = 24
    spam_window: int = 168  # 1 week
    domain_health_window: int = 720  # 30 days

    # Alert settings
    alert_cooldown_minutes: int = 60
    max_alerts_per_campaign: int = 10
    auto_pause_enabled: bool = True

    # Report settings
    report_recipients: list[str] = ["ops@smarterteam.com"]
    report_timezone: str = "UTC"
```

## Tools

### Tool: process_bounce_webhook
**Purpose:** Process bounce events from Instantly webhooks

**Input Schema:**
```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class BounceWebhookPayload(BaseModel):
    """Webhook payload for bounce events."""

    event_id: str = Field(..., description="Unique event identifier")
    campaign_id: str = Field(..., description="Campaign UUID")
    lead_id: str = Field(..., description="Lead UUID")
    email: str = Field(..., description="Bounced email address")
    bounce_type: Literal["hard", "soft", "spam"] = Field(..., description="Type of bounce")
    bounce_reason: Optional[str] = Field(None, description="Bounce reason from ESP")
    timestamp: datetime = Field(..., description="Event timestamp")
    domain: str = Field(..., description="Sending domain")
    ip_address: Optional[str] = Field(None, description="Sending IP address")

class BounceProcessingResult(BaseModel):
    """Result of processing bounce webhook."""

    event_id: str
    processed: bool
    bounce_recorded: bool
    campaign_affected: bool
    current_bounce_rate: Optional[float] = None
    alert_triggered: bool = False
    campaign_paused: bool = False
    recommendation: str
```

**Error Handling:**
- Invalid webhook signature → Return 401, log security event
- Missing required fields → Return 400, log validation error
- Database connection error → Retry 3x with exponential backoff
- Duplicate event_id → Skip processing, log warning

**Example:**
```python
# Input
{
    "event_id": "evt_123456",
    "campaign_id": "camp_789",
    "lead_id": "lead_456",
    "email": "user@example.com",
    "bounce_type": "hard",
    "bounce_reason": "Invalid mailbox",
    "timestamp": "2025-12-05T10:30:00Z",
    "domain": "mail.smarterteam.com",
    "ip_address": "192.168.1.1"
}

# Output
{
    "event_id": "evt_123456",
    "processed": true,
    "bounce_recorded": true,
    "campaign_affected": true,
    "current_bounce_rate": 2.3,
    "alert_triggered": true,
    "campaign_paused": false,
    "recommendation": "Monitor closely, approaching warning threshold"
}
```

### Tool: calculate_deliverability_metrics
**Purpose:** Calculate deliverability metrics for a campaign or domain

**Input Schema:**
```python
class MetricsQuery(BaseModel):
    """Query for deliverability metrics."""

    campaign_id: Optional[str] = Field(None, description="Specific campaign ID")
    domain: Optional[str] = Field(None, description="Sending domain")
    time_window_hours: int = Field(default=24, description="Time window for calculation")
    include_subdomains: bool = Field(default=False, description="Include subdomains in domain metrics")

class DeliverabilityMetrics(BaseModel):
    """Calculated deliverability metrics."""

    total_sent: int
    total_delivered: int
    total_bounces: int
    hard_bounces: int
    soft_bounces: int
    spam_complaints: int
    bounce_rate: float
    spam_rate: float
    delivery_rate: float
    domain_health_score: float
    trend_direction: Literal["improving", "stable", "declining"]
    confidence_level: float
```

**Error Handling:**
- No data in time window → Return zeros with appropriate message
- Invalid time window → Default to 24 hours, log warning
- Campaign not found → Return error with campaign list
- Database timeout → Retry 2x, then return cached metrics if available

### Tool: check_thresholds_and_alert
**Purpose:** Evaluate metrics against thresholds and trigger alerts

**Input Schema:**
```python
class ThresholdCheck(BaseModel):
    """Threshold check request."""

    metrics: DeliverabilityMetrics
    campaign_id: Optional[str] = None
    domain: str
    auto_pause: bool = Field(default=True, description="Allow automatic campaign pause")
    cooldown_active: bool = Field(default=False, description="Check if alert cooldown is active")

class AlertAction(BaseModel):
    """Alert action recommendation."""

    action: Literal["none", "warning", "critical", "pause_campaign"]
    message: str
    metrics_triggered: list[str]
    recommended_actions: list[str]
    escalation_level: Literal["info", "warning", "critical"]
    requires_human_approval: bool
```

**Error Handling:**
- Missing threshold config → Use defaults, log configuration error
- Alert service unavailable → Queue alert for retry
- Invalid campaign ID for pause → Log error, continue with alert
- Rate limiting on notifications → Batch alerts, send later

### Tool: pause_campaign
**Purpose:** Pause a campaign to protect sender reputation

**Input Schema:**
```python
class CampaignPause(BaseModel):
    """Campaign pause request."""

    campaign_id: str = Field(..., description="Campaign to pause")
    reason: str = Field(..., description="Reason for pausing")
    trigger_metric: str = Field(..., description="Metric that triggered pause")
    current_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Threshold exceeded")
    auto_pause: bool = Field(default=True, description="Automatic vs manual pause")

class PauseResult(BaseModel):
    """Result of campaign pause operation."""

    campaign_id: str
    paused: bool
    paused_at: datetime
    reason: str
    affected_leads: int
    recovery_recommendations: list[str]
    next_check_time: datetime
```

**Error Handling:**
- Campaign already paused → Return status, no action needed
- Instantly API error → Retry 3x, alert ops team
- Insufficient permissions → Log security error, escalate
- Campaign not found → Log error, update monitoring list

### Tool: generate_weekly_report
**Purpose:** Generate comprehensive deliverability report

**Input Schema:**
```python
class ReportRequest(BaseModel):
    """Weekly report generation request."""

    domain: str = Field(..., description="Primary domain to report on")
    include_campaigns: bool = Field(default=True, description="Include campaign breakdown")
    include_trends: bool = Field(default=True, description="Include trend analysis")
    include_recommendations: bool = Field(default=True, description="Include AI recommendations")
    report_format: Literal["markdown", "html", "json"] = Field(default="markdown")

class WeeklyReport(BaseModel):
    """Generated weekly deliverability report."""

    report_id: str
    domain: str
    report_period: str
    summary_metrics: dict
    campaign_breakdown: list[dict]
    trends_analysis: dict
    domain_health_trend: float
    issues_identified: list[dict]
    recommendations: list[str]
    generated_at: datetime
```

**Error Handling:**
- Insufficient data for report → Generate partial report, note limitations
- Report generation timeout → Return cached report from previous period
- Delivery failures → Retry with different recipients
- Template errors → Use fallback template

### Tool: update_domain_health_score
**Purpose:** Calculate and update domain health score

**Input Schema:**
```python
class DomainHealthUpdate(BaseModel):
    """Domain health score update."""

    domain: str = Field(..., description="Domain to update")
    include_history: bool = Field(default=True, description="Include historical data")
    weight_factors: Optional[dict] = Field(None, description="Custom weight factors")

class DomainHealthScore(BaseModel):
    """Calculated domain health score."""

    domain: str
    overall_score: float  # 0-100
    bounce_rate_score: float
    spam_rate_score: float
    consistency_score: float
    reputation_score: float
    last_updated: datetime
    score_trend: Literal["up", "stable", "down"]
    risk_level: Literal["low", "medium", "high", "critical"]
```

**Algorithm:**
```
Overall Score = (
    Bounce Rate Score * 0.35 +
    Spam Rate Score * 0.35 +
    Consistency Score * 0.15 +
    Reputation Score * 0.15
)

Where:
- Bounce Rate Score = max(0, 100 - (bounce_rate * 20))
- Spam Rate Score = max(0, 100 - (spam_rate * 300))
- Consistency Score = Based on volume stability over time
- Reputation Score = Based on external reputation data if available
```

## Prompts

### System Prompt
```
You are an Email Deliverability Monitor, an autonomous agent responsible for maintaining optimal sender reputation and campaign health.

Your core responsibilities:
1. Monitor bounce rates, spam complaints, and delivery metrics in real-time
2. Calculate domain health scores using weighted algorithms
3. Trigger alerts when thresholds are exceeded
4. Automatically pause at-risk campaigns to protect sender reputation
5. Generate weekly deliverability reports with actionable insights

Your decision-making framework:
- Always prioritize sender reputation protection
- Use data-driven thresholds (bounce >2% warning, >5% critical; spam >0.1% warning, >0.3% critical)
- Consider campaign context (new vs established, industry, volume)
- Provide clear, actionable recommendations with each alert
- Document all decisions for audit trail and learning

Key principles:
- Be proactive but not overly cautious - protect reputation without unnecessary pauses
- Provide context for all metrics (compare to historical averages, industry benchmarks)
- Escalate quickly when critical thresholds are breached
- Learn from each incident to improve monitoring accuracy

You have access to tools for processing webhooks, calculating metrics, checking thresholds, pausing campaigns, generating reports, and updating domain health scores. Use them systematically to maintain deliverability excellence.
```

### User Prompt Templates

#### Webhook Processing Template
```
Process bounce webhook:
- Campaign: {campaign_id}
- Email: {email}
- Bounce Type: {bounce_type}
- Reason: {bounce_reason}
- Domain: {domain}
- Timestamp: {timestamp}

Please process this event and determine if any alerts or actions are needed based on current campaign metrics.
```

#### Metrics Check Template
```
Check deliverability health:
- Domain: {domain}
- Campaign: {campaign_id or "all campaigns"}
- Time Window: {time_window_hours} hours
- Current Metrics: {current_metrics}

Evaluate against thresholds and recommend appropriate actions if needed.
```

#### Weekly Report Template
```
Generate weekly deliverability report for:
- Domain: {domain}
- Period: {start_date} to {end_date}
- Include: {campaign_breakdown}, {trends}, {recommendations}

Provide comprehensive analysis with actionable insights for improvement.
```

## Error Handling

### Error Matrix

| Component | Error Type | Detection | Response | Retry |
|-----------|------------|-----------|----------|-------|
| Webhook Handler | Invalid signature | HTTP 401 | Reject with security log | No |
| Webhook Handler | Missing fields | Validation error | Return 400 with details | No |
| Database | Connection timeout | Exception | Retry 3x, backoff | Yes |
| Database | Constraint violation | DB error | Log, continue with partial | No |
| Instantly API | Rate limit (429) | Status code | Exponential backoff | Yes |
| Instantly API | Auth error (401) | Status code | Fail immediately, alert | No |
| Instantly API | Server error (5xx) | Status code | Retry 3x, fallback | Yes |
| Metrics Calculation | No data | Query result | Return zeros, log warning | No |
| Alert System | Service down | HTTP error | Queue for retry | Yes |
| Report Generation | Template error | Exception | Use fallback template | No |

### Recovery Strategies

1. **Graceful Degradation**: If partial data unavailable, use available data and note limitations
2. **Fallback Values**: Use last known good values for missing metrics
3. **Queued Processing**: Queue failed operations for retry when systems recover
4. **Manual Escalation**: Auto-escalate to ops team after 3 failed retries
5. **Circuit Breaker**: Temporarily disable auto-pause if API failures persist

### Data Validation

```python
def validate_webhook_signature(payload: dict, signature: str) -> bool:
    """Validate Instantly webhook signature."""

def sanitize_email(email: str) -> str:
    """Clean and validate email addresses."""

def validate_campaign_id(campaign_id: str) -> bool:
    """Ensure campaign ID exists and is active."""

def check_rate_limits(domain: str) -> bool:
    """Prevent API abuse for monitoring endpoints."""
```

## Multi-Agent Integration

### Handoff Scenarios

1. **To Campaign Creation Agent**:
   - Trigger: Persistent deliverability issues with specific campaign type
   - Payload: `{"issue_type": "deliverability", "metrics": {...}, "recommendations": [...]}`

2. **To System Health Monitor**:
   - Trigger: Database errors, API failures, system-wide issues
   - Payload: `{"system": "deliverability_monitor", "error": "...", "impact": "high"}`

3. **To Response Email Handler**:
   - Trigger: Need to communicate with clients about campaign issues
   - Payload: `{"campaign_id": "...", "issue": "...", "client_notification": true}`

### Dependencies

- **Campaign Creation Agent**: Provides campaign metadata and active campaigns list
- **Database Manager**: Stores/retrieves metrics and historical data
- **System Error Monitor**: Receives system health notifications

## Testing

### Unit Tests

```python
def test_process_bounce_webhook_hard_bounce():
    """Test hard bounce processing and threshold checking."""

def test_calculate_metrics_with_no_data():
    """Test graceful handling of empty time windows."""

def test_spam_threshold_critical():
    """Test critical spam rate triggers auto-pause."""

def test_domain_health_score_calculation():
    """Verify weighted scoring algorithm."""

def test_alert_cooldown():
    """Ensure alerts respect cooldown period."""

def test_duplicate_webhook_event():
    """Test duplicate event_id handling."""
```

### Integration Tests

```python
def test_end_to_end_webhook_to_pause():
    """Full flow: webhook → metrics → threshold → pause."""

def test_weekly_report_generation():
    """Test report generation with real data."""

def test_multi_campaign_domain_impact():
    """Verify domain issues affect all campaigns."""

def test_instantly_api_pause_integration():
    """Test actual campaign pause via Instantly API."""
```

### Mock Strategy

```python
@pytest.fixture
def mock_instantly_client():
    with patch('src.integrations.instantly.InstantlyClient') as mock:
        mock.return_value.pause_campaign.return_value = {"status": "paused"}
        yield mock

@pytest.fixture
def mock_webhook_payload():
    return {
        "event_id": "test_123",
        "campaign_id": "camp_test",
        "email": "test@example.com",
        "bounce_type": "hard",
        "timestamp": datetime.utcnow(),
        "domain": "test.example.com"
    }
```

## Performance

### Expected Latency
- Webhook processing: <200ms (99th percentile)
- Metrics calculation: <500ms for 30-day window
- Alert generation: <100ms
- Report generation: <2s for weekly report

### Throughput Requirements
- Webhooks: Handle 1000 events/minute during peak sends
- Concurrent campaigns: Monitor 100+ active campaigns
- API rate limits: Respect Instantly limits (100 requests/minute)

### Caching Strategy
```python
# Cache frequent queries
- Campaign metadata: 5 minutes
- Domain health scores: 15 minutes
- Recent metrics: 1 minute
- Threshold configurations: 30 minutes
```

## Observability

### Logging Levels
- **DEBUG**: Raw webhook data, calculation steps
- **INFO**: Normal operations, metric updates, report generation
- **WARN**: Threshold warnings, API retries, missing data
- **ERROR**: Failed operations, API errors, auto-pause actions
- **CRITICAL**: System failures, security issues

### Metrics to Track
```python
# Business metrics
bounce_rates_by_campaign = Gauge(...)
spam_complaint_rates = Gauge(...)
domain_health_scores = Gauge(...)
campaign_auto_pauses = Counter(...)
alerts_generated = Counter(...)

# Technical metrics
webhook_processing_latency = Histogram(...)
api_request_duration = Histogram(...)
database_query_time = Histogram(...)
error_rates_by_type = Counter(...)
```

### Alerting
- PagerDuty alerts for critical failures
- Slack notifications for threshold warnings
- Email reports for weekly summaries

## Security

### API Security
- Validate all webhook signatures using Instantly secret
- Sanitize all email addresses and domains
- Rate limit monitoring endpoints
- Audit log all campaign pause actions

### Data Protection
- Hash personal email addresses in logs
- Encrypt sensitive configuration
- Use read-only database credentials where possible
- Regular rotation of API keys

### Permissions
```python
required_permissions = {
    "webhooks": ["read", "write"],
    "deliverability_metrics": ["read", "write"],
    "campaigns": ["read", "update:pause"],
    "reports": ["read", "write"]
}
```

## Acceptance Criteria

- [ ] Processes 1000 webhook events/minute with <200ms latency
- [ ] Automatically pauses campaigns when bounce rate >5% or spam rate >0.3%
- [ ] Generates accurate domain health scores using weighted algorithm
- [ ] Sends alert notifications within 30 seconds of threshold breach
- [ ] Produces weekly reports with comprehensive analysis
- [ ] Maintains 99.9% uptime with graceful error handling
- [ ] Passes all security scans and penetration tests
- [ ] Achieves >90% test coverage with comprehensive scenarios
- [ ] Integrates seamlessly with Campaign Creation and System Health agents
- [ ] Provides clear audit trail for all automated actions

## Implementation Notes

1. **Use existing BaseAgent pattern** from `src/agents/base_agent.py`
2. **Extend BaseIntegrationClient** for Instantly API integration
3. **Leverage Celery** for async report generation and batch processing
4. **Follow existing logging patterns** with structured logging via `get_agent_logger()`
5. **Use Pydantic models** for all input/output validation
6. **Implement proper error handling** with retries and fallbacks
7. **Write comprehensive tests** following existing patterns in `__tests__/`
