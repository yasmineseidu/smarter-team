# Campaign Warmup Monitor - Agent Specification

## Agent Identity

**Name**: `campaign_warmup_monitor`

**Category**: Campaign & Outreach

**Purpose**: Monitor and manage email warmup progress for sending domains, tracking engagement metrics, reputation progression, and providing readiness recommendations for scaling to full volume.

## Role & Responsibilities

The Warmup Monitor ensures domains are properly warmed up before high-volume sending, protecting deliverability and sender reputation. It acts as a guardian of email infrastructure health.

**Core Functions**:
- Track daily warmup email volumes and progression through stages
- Monitor engagement metrics (open rates, reply rates, spam complaints)
- Check domain reputation across major providers (Gmail, Outlook, Yahoo)
- Alert on deliverability issues and reputation threats
- Recommend when domains are ready for volume scaling
- Maintain warmup schedules and stage progression
- Generate weekly warmup health reports

## System Prompt

```
You are an email deliverability specialist monitoring domain warmup progress.

Your role is to ensure domains are properly warmed up to maintain excellent deliverability. You track metrics, identify issues, and recommend when domains are ready for scaling.

WARMUP STAGES:
- Stage 1 (Week 1-2): 10-20 emails/day, focus on engagement
- Stage 2 (Week 3-4): 30-50 emails/day, monitor reputation
- Stage 3 (Week 5-6): 75-100 emails/day, prepare for scale
- Stage 4 (Week 7+): Full volume (up to daily limit)

KEY METRICS:
- Daily sent count vs. target for current stage
- Open rate: Should be >60% for healthy warming
- Reply rate: Should be >10% for engaged sending
- Bounce rate: Must be <3% (hard bounces <1%)
- Spam complaints: Must be <0.1% (zero ideal)
- Domain reputation: Google Postmaster, Microsoft SNDS

ALERT THRESHOLDS:
CRITICAL (Immediate action):
- Spam rate >0.5%
- Hard bounce rate >3%
- Domain reputation marked "Poor" or "Low"
- 3+ consecutive days with open rate <40%

HIGH (Investigate within 24h):
- Bounce rate 2-3%
- Open rate 40-50% for 2+ days
- Reply rate <5% for 3+ days
- Sudden 50% drop in engagement

MEDIUM (Review in weekly report):
- Missing reputation data for 2+ days
- Inconsistent sending volume
- Gradual engagement decline

Your recommendations should be conservative - better to warm up slowly than damage reputation.
```

## Input Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, date
from enum import Enum

class WarmupStage(str, Enum):
    STAGE_1 = "stage_1"  # Week 1-2: 10-20/day
    STAGE_2 = "stage_2"  # Week 3-4: 30-50/day
    STAGE_3 = "stage_3"  # Week 5-6: 75-100/day
    STAGE_4 = "stage_4"  # Week 7+: Full volume

class AlertLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class WarmupMetrics(BaseModel):
    """Daily warmup metrics for a domain."""

    domain: str = Field(..., description="Domain being monitored")
    date: date = Field(..., description="Date of metrics")
    emails_sent: int = Field(..., ge=0, description="Emails sent that day")
    emails_delivered: int = Field(..., ge=0, description="Successfully delivered")
    emails_opened: int = Field(..., ge=0, description="Unique opens")
    emails_replied: int = Field(..., ge=0, description="Unique replies")
    emails_bounced: int = Field(..., ge=0, description="Total bounces")
    hard_bounces: int = Field(..., ge=0, description="Hard bounces")
    spam_complaints: int = Field(..., ge=0, description="Spam complaints")
    current_stage: WarmupStage = Field(..., description="Current warmup stage")
    stage_day: int = Field(..., ge=1, le=14, description="Day within current stage")
    daily_target: int = Field(..., description="Target emails for current stage/day")
    reputation_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Domain reputation score")

class DomainReputation(BaseModel):
    """Reputation data from providers."""

    domain: str
    provider: Literal["google", "microsoft", "yahoo", "others"]
    reputation_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    reputation_level: Optional[Literal["Very High", "High", "Medium", "Low", "Poor"]] = None
    spam_rate: Optional[float] = Field(None, ge=0.0)
    complaint_rate: Optional[float] = Field(None, ge=0.0)
    domain_age_days: Optional[int] = Field(None, ge=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class WarmupReviewRequest(BaseModel):
    """Request for warmup progress review."""

    domain: str = Field(..., description="Domain to review")
    review_period_days: int = Field(default=7, ge=1, le=30, description="Days to review")
    include_recommendations: bool = Field(default=True, description="Include scaling recommendations")
    force_report: bool = Field(default=False, description="Generate report even if recently done")

class WeeklyReportRequest(BaseModel):
    """Request for weekly warmup report."""

    domains: Optional[list[str]] = Field(None, description="Specific domains (null = all)")
    include_charts: bool = Field(default=True, description="Include chart data")
    send_to_email: Optional[str] = Field(None, description="Email to send report to")
```

## Output Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class WarmupAlert(BaseModel):
    """Alert for warmup issue."""

    alert_id: str
    domain: str
    level: AlertLevel
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold_value: float
    recommendation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class ScalingReadiness(BaseModel):
    """Assessment of readiness for volume scaling."""

    domain: str
    current_stage: WarmupStage
    ready_for_next_stage: bool
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    blocking_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    estimated_ready_date: Optional[date] = None
    safe_daily_limit: int

class WarmupReviewResult(BaseModel):
    """Result of warmup progress review."""

    domain: str
    review_period_days: int
    current_stage: WarmupStage
    days_in_stage: int

    # Metrics
    avg_daily_sent: float
    avg_open_rate: float
    avg_reply_rate: float
    avg_bounce_rate: float
    total_complaints: int

    # Health assessment
    overall_health: Literal["excellent", "good", "concerning", "critical"]
    trend_direction: Literal["improving", "stable", "declining"]

    # Alerts and recommendations
    active_alerts: List[WarmupAlert] = Field(default_factory=list)
    scaling_readiness: ScalingReadiness

    reviewed_at: datetime = Field(default_factory=datetime.utcnow)

class WeeklyReport(BaseModel):
    """Weekly warmup performance report."""

    report_id: str
    week_start: date
    week_end: date
    domains: List[str]

    # Summary metrics
    total_emails_sent: int
    avg_open_rate: float
    avg_reply_rate: float
    total_bounces: int
    total_complaints: int

    # Domain breakdown
    domain_performance: Dict[str, Dict[str, Any]]

    # Alerts summary
    new_alerts_count: int
    resolved_alerts_count: int
    critical_alerts: List[WarmupAlert]

    # Recommendations
    top_recommendations: List[str]

    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ChartData(BaseModel):
    """Data for visualizations."""

    dates: List[date]
    datasets: Dict[str, List[float]]  # e.g., {"open_rate": [60, 65, 62], "reply_rate": [8, 12, 10]}
```

## Tools

### 1. `track_daily_metrics`

**Purpose**: Record daily warmup metrics for a domain.

**Parameters**:
```python
metrics: WarmupMetrics
```

**Returns**:
```python
{
    "metrics_id": str,
    "status": "recorded",
    "trend_analysis": {
        "open_rate_trend": "up|down|stable",
        "bounce_rate_trend": "up|down|stable",
        "volume_consistency": float  # 0-1 score
    }
}
```

**Implementation**:
- Write to `warmup_metrics` table
- Calculate 7-day moving averages
- Detect anomalies in sending patterns
- Update trend indicators
- Check against stage targets

### 2. `check_domain_reputation`

**Purpose**: Fetch current reputation data from major providers.

**Parameters**:
```python
domain: str
providers: Optional[List[Literal["google", "microsoft", "yahoo"]]] = None
```

**Returns**:
```python
{
    "domain": str,
    "reputation_data": List[DomainReputation],
    "overall_risk": "low|medium|high",
    "last_checked": datetime,
    "data_gaps": List[str]  # Providers with no data
}
```

**Implementation**:
- Query Google Postmaster API (if configured)
- Check Microsoft SNDS (if available)
- Use third-party reputation services (e.g., Talos, SenderScore)
- Cache results for 24 hours
- Alert on significant reputation drops

### 3. `analyze_engagement_health`

**Purpose**: Analyze engagement metrics and identify issues.

**Parameters**:
```python
domain: str
days: int = 7  # Analysis period
```

**Returns**:
```python
{
    "domain": str,
    "health_score": float,  # 0-100
    "metrics": {
        "open_rate": float,
        "reply_rate": float,
        "bounce_rate": float,
        "spam_rate": float,
        "volume_consistency": float
    },
    "issues": List[str],
    "improvements": List[str]
}
```

**Implementation**:
- Compare against industry benchmarks
- Check for sudden drops in engagement
- Identify patterns in bounce types
- Analyze sending volume consistency
- Generate actionable insights

### 4. `generate_alerts`

**Purpose**: Create alerts for threshold breaches.

**Parameters**:
```python
domain: str
metrics: Optional[WarmupMetrics] = None  # If None, check latest
```

**Returns**:
```python
{
    "alerts_created": List[WarmupAlert],
    "alerts_resolved": List[WarmupAlert],
    "summary": {
        "critical": int,
        "high": int,
        "medium": int,
        "low": int
    }
}
```

**Implementation**:
- Check all metrics against alert thresholds
- Avoid duplicate alerts (same issue, same day)
- Auto-resolve alerts when metrics normalize
- Group related alerts to reduce noise
- Prioritize by business impact

### 5. `assess_scaling_readiness`

**Purpose**: Determine if domain is ready for next warmup stage.

**Parameters**:
```python
domain: str
target_stage: Optional[WarmupStage] = None
```

**Returns**:
```python
{
    "scaling_readiness": ScalingReadiness,
    "stage_progress": {
        "days_completed": int,
        "total_days": int,
        "targets_met": float  # percentage
    },
    "blockers": List[str],
    "confidence_factors": Dict[str, float]  # Factors affecting confidence
}
```

**Implementation**:
- Check minimum days in current stage
- Verify all metrics are healthy thresholds
- Consider recent trends, not just averages
- Factor in reputation data
- Provide specific reasons for decisions

### 6. `create_weekly_report`

**Purpose**: Generate comprehensive weekly report.

**Parameters**:
```python
request: WeeklyReportRequest
```

**Returns**:
```python
{
    "report": WeeklyReport,
    "chart_data": Optional[ChartData],
    "sent": bool,  # If email was sent
    "delivery_status": Optional[str]
}
```

**Implementation**:
- Aggregate metrics across all domains
- Generate insights and trends
- Create visualizations data
- Send email report if requested
- Store report for historical reference

### 7. `update_warmup_schedule`

**Purpose**: Adjust warmup schedule based on performance.

**Parameters**:
```python
domain: str
action: Literal["pause", "resume", "extend_stage", "promote_stage"]
reason: str
days: Optional[int] = None  # For extend/promote
```

**Returns**:
```python
{
    "schedule_updated": bool,
    "new_stage": Optional[WarmupStage],
    "estimated_completion": Optional[date],
    "reason_log": str
}
```

**Implementation**:
- Update `domain_warmup` table
- Log reason for change
- Recalculate daily targets
- Notify relevant agents (Campaign Send Agent)
- Ensure smooth transitions

## Database Schema

### `domain_warmup`

```sql
CREATE TABLE domain_warmup (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) UNIQUE NOT NULL,

    -- Current status
    current_stage VARCHAR(20) NOT NULL CHECK (current_stage IN ('stage_1', 'stage_2', 'stage_3', 'stage_4')),
    stage_start_date DATE NOT NULL,
    days_in_stage INTEGER NOT NULL DEFAULT 0,

    -- Schedule
    daily_target INTEGER NOT NULL,
    max_daily_limit INTEGER NOT NULL DEFAULT 500,
    paused BOOLEAN DEFAULT FALSE,
    pause_reason TEXT,

    -- Readiness
    ready_for_scaling BOOLEAN DEFAULT FALSE,
    last_scaling_check TIMESTAMP,
    scaling_confidence NUMERIC(5,2) DEFAULT 0.0,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'campaign_warmup_monitor',

    -- Indexes
    INDEX idx_domain (domain),
    INDEX idx_current_stage (current_stage),
    INDEX idx_ready_for_scaling (ready_for_scaling),
    INDEX idx_updated_at (updated_at)
);
```

### `warmup_metrics`

```sql
CREATE TABLE warmup_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) NOT NULL REFERENCES domain_warmup(domain),
    metric_date DATE NOT NULL,

    -- Volume metrics
    emails_sent INTEGER NOT NULL DEFAULT 0,
    emails_delivered INTEGER NOT NULL DEFAULT 0,
    emails_opened INTEGER NOT NULL DEFAULT 0,
    emails_replied INTEGER NOT NULL DEFAULT 0,

    -- Quality metrics
    emails_bounced INTEGER NOT NULL DEFAULT 0,
    hard_bounces INTEGER NOT NULL DEFAULT 0,
    soft_bounces INTEGER NOT NULL DEFAULT 0,
    spam_complaints INTEGER NOT NULL DEFAULT 0,

    -- Calculated rates (stored for quick querying)
    open_rate NUMERIC(5,2),  -- percentage
    reply_rate NUMERIC(5,2),  -- percentage
    bounce_rate NUMERIC(5,2),  -- percentage
    spam_rate NUMERIC(5,2),    -- percentage

    -- Stage context
    current_stage VARCHAR(20) NOT NULL,
    daily_target INTEGER NOT NULL,
    target_compliance BOOLEAN,  -- Met daily target?

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    UNIQUE(domain, metric_date),

    -- Indexes
    INDEX idx_domain_date (domain, metric_date),
    INDEX idx_metric_date (metric_date),
    INDEX idx_current_stage (current_stage),
    INDEX idx_created_at (created_at)
);
```

### `domain_reputation`

```sql
CREATE TABLE domain_reputation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) NOT NULL REFERENCES domain_warmup(domain),
    provider VARCHAR(50) NOT NULL,  -- google, microsoft, yahoo, etc.

    -- Reputation data
    reputation_score NUMERIC(5,2),  -- 0-100
    reputation_level VARCHAR(20),   -- Very High, High, Medium, Low, Poor
    spam_rate NUMERIC(5,2),         -- percentage
    complaint_rate NUMERIC(5,2),    -- percentage

    -- Additional data
    domain_age_days INTEGER,
    ip_reputation NUMERIC(5,2),
    volume_score NUMERIC(5,2),

    -- Metadata
    checked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    raw_data JSONB,  -- Full response from provider

    -- Constraints
    UNIQUE(domain, provider, checked_at),

    -- Indexes
    INDEX idx_domain_provider (domain, provider),
    INDEX idx_checked_at (checked_at),
    INDEX idx_reputation_score (reputation_score)
);
```

### `warmup_alerts`

```sql
CREATE TABLE warmup_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) NOT NULL REFERENCES domain_warmup(domain),
    alert_type VARCHAR(100) NOT NULL,  -- high_spam_rate, low_engagement, etc.

    -- Alert details
    level VARCHAR(20) NOT NULL CHECK (level IN ('critical', 'high', 'medium', 'low')),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,

    -- Metrics that triggered alert
    metric_name VARCHAR(100) NOT NULL,
    current_value NUMERIC(10,2),
    threshold_value NUMERIC(10,2),

    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolution_note TEXT,

    -- Actions taken
    auto_paused BOOLEAN DEFAULT FALSE,
    human_notified BOOLEAN DEFAULT FALSE,
    recommendation TEXT,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_domain_resolved (domain, resolved),
    INDEX idx_level_created (level, created_at),
    INDEX idx_alert_type (alert_type),
    INDEX idx_created_at (created_at)
);
```

### `warmup_reports`

```sql
CREATE TABLE warmup_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(50) NOT NULL,  -- daily, weekly, monthly

    -- Report period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Content
    report_data JSONB NOT NULL,
    chart_data JSONB,
    summary TEXT,

    -- Delivery
    sent_via_email BOOLEAN DEFAULT FALSE,
    email_recipients TEXT[],
    delivery_status VARCHAR(50),  -- sent, failed, pending

    -- Metadata
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    generated_by VARCHAR(100) DEFAULT 'campaign_warmup_monitor',
    file_path VARCHAR(500),  -- If saved to file

    -- Indexes
    INDEX idx_report_type_period (report_type, period_start),
    INDEX idx_generated_at (generated_at)
);
```

## Integration: External Reputation Services

### Google Postmaster Client

```python
from src.integrations.base import BaseIntegrationClient

class GooglePostmasterClient(BaseIntegrationClient):
    """Client for Google Postmaster Tools API."""

    def __init__(self, api_key: str):
        super().__init__(
            name="google_postmaster",
            base_url="https://postmaster.google.com",
            api_key=api_key,
            timeout=30.0
        )

    async def get_domain_reputation(self, domain: str) -> dict:
        """Fetch reputation data from Google Postmaster."""
        return await self.get(f"/api/v1/domains/{domain}/reputation")

    async def get_traffic_stats(self, domain: str, days: int = 7) -> dict:
        """Get traffic statistics for domain."""
        return await self.get(f"/api/v1/domains/{domain}/traffic?days={days}")
```

### SenderScore Client

```python
class SenderScoreClient(BaseIntegrationClient):
    """Client for Return Path SenderScore."""

    def __init__(self, api_key: str):
        super().__init__(
            name="senderscore",
            base_url="https://api.senderscore.org",
            api_key=api_key,
            timeout=30.0
        )

    async def get_score(self, domain: str) -> dict:
        """Get SenderScore for domain."""
        return await self.get(f"/v1/score?domain={domain}")
```

## Workflow

### Daily Monitoring Workflow (Scheduled at 2 AM UTC)

```python
async def daily_monitoring():
    """Run daily checks for all active warmup domains."""

    # 1. Get all active domains
    domains = await get_active_warmup_domains()

    for domain in domains:
        # 2. Fetch yesterday's metrics from Instantly API
        metrics = await fetch_instantly_metrics(domain, yesterday)

        # 3. Store metrics
        await track_daily_metrics(metrics)

        # 4. Check reputation (every 3 days)
        if should_check_reputation(domain):
            reputation = await check_domain_reputation(domain)
            await store_reputation_data(reputation)

        # 5. Analyze health
        health = await analyze_engagement_health(domain)

        # 6. Generate alerts
        alerts = await generate_alerts(domain, metrics)

        # 7. Check for auto-pause conditions
        if health["health_score"] < 30 or any(a.level == "critical" for a in alerts):
            await update_warmup_schedule(domain, "pause", "Auto-pause due to critical issues")

        # 8. Check for stage progression
        readiness = await assess_scaling_readiness(domain)
        if readiness.ready_for_next_stage:
            await update_warmup_schedule(domain, "promote_stage", "Met all criteria")
```

### Weekly Reporting (Sundays at 9 AM UTC)

```python
async def weekly_reporting():
    """Generate and send weekly warmup reports."""

    request = WeeklyReportRequest(
        domains=None,  # All domains
        include_charts=True,
        send_to_email="deliverability@company.com"
    )

    result = await create_weekly_report(request)

    # Store report
    await log_report_generation(result["report"])

    # If critical issues found, notify ops
    if result["report"].critical_alerts:
        await notify_ops_team(result["report"].critical_alerts)
```

### Alert Processing

```python
async def process_alerts():
    """Background task to process and escalate alerts."""

    # 1. Get unnotified critical/high alerts
    alerts = await get_pending_alerts(min_level="high")

    # 2. Group by domain
    by_domain = group_alerts_by_domain(alerts)

    # 3. Send notifications
    for domain, domain_alerts in by_domain.items():
        if any(a.level == "critical" for a in domain_alerts):
            # Immediate Slack/Email for critical
            await send_critical_alert(domain, domain_alerts)
        else:
            # Batch high alerts in hourly digest
            await queue_hourly_digest(domain, domain_alerts)

    # 4. Mark as notified
    await mark_alerts_notified([a.id for a in alerts])
```

## Error Handling

### API Integration Errors

| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Instantly API down | HTTP 5xx | Log warning, use cached data | Yes, 3 times |
| Rate limit (429) | HTTP 429 | Exponential backoff | Yes, respect retry-after |
| Invalid API key | HTTP 401 | Critical alert, halt checks | No |
| Timeout | Request >30s | Retry with longer timeout | Yes, 2 times |

### Data Issues

| Issue | Detection | Response |
|-------|-----------|----------|
| Missing metrics | No data for 24h | Alert, mark as suspicious |
| Implausible values | Open rate >100% | Flag for manual review |
| Stage mismatch | Metrics don't match stage | Recalculate stage |
| Duplicate entries | Same domain/date | Skip, log warning |

### Database Errors

| Error | Recovery |
|-------|----------|
| Connection timeout | Retry with backoff |
| Constraint violation | Skip record, log error |
| Deadlock | Retry transaction up to 3 times |
| Disk full | Critical alert, halt writes |

## Testing Requirements

### Unit Tests (>90% coverage for tools)

```python
# test_track_daily_metrics.py
- Test normal metric recording
- Test stage validation
- Test trend calculation
- Test anomaly detection
- Test duplicate handling

# test_check_domain_reputation.py
- Test Google Postmaster integration
- Test reputation score parsing
- Test cache expiry
- Test provider failures
- Test data aggregation

# test_analyze_engagement_health.py
- Test healthy domain scoring
- Test declining trend detection
- Test benchmark comparison
- Test volume consistency
- Test improvement suggestions

# test_generate_alerts.py
- Test all alert thresholds
- Test duplicate prevention
- Test auto-resolution
- Test alert grouping
- Test escalation logic

# test_assess_scaling_readiness.py
- Test stage progression criteria
- Test confidence calculation
- Test blocker identification
- Test conservative decisions
- Test edge cases
```

### Integration Tests (>85% coverage for agent)

```python
# test_daily_workflow.py
- Test full daily monitoring cycle
- Test multi-domain processing
- Test alert generation cascade
- Test auto-pause functionality
- Test data persistence

# test_reputation_integration.py
- Test real Google Postmaster API
- Test SenderScore integration
- Test reputation change detection
- Test multi-provider aggregation

# test_weekly_report.py
- Test report generation
- Test chart data creation
- Test email delivery
- Test historical data accuracy
```

### Edge Cases

```python
- Domain with 1 day of history
- Sudden 100% drop in open rate
- Perfect metrics (100% open rate)
- Missing reputation for all providers
- Multiple alerts same domain same day
- Stage 4 requesting further scaling
- Holiday period (no sending)
```

## Performance Requirements

- **Daily monitoring**: 100 domains in <10 minutes
- **Reputation checks**: 10 domains/second (API limited)
- **Alert processing**: <100ms per alert
- **Report generation**: <30 seconds for weekly report
- **Database queries**: All indexes for <100ms response
- **Concurrent monitoring**: Support 10 parallel domain checks

## Monitoring & Metrics

### Key Metrics

```python
# Daily metrics
- domains_monitored: int
- alerts_generated: int (by level)
- auto_pauses: int
- stage_progressions: int

# Health metrics
- avg_open_rate: float (across all domains)
- avg_reply_rate: float
- avg_bounce_rate: float
- reputation_score_avg: float

# Performance metrics
- monitoring_duration: float (per domain)
- api_call_success_rate: float
- report_generation_time: float
- database_query_time: float
```

### Alerts

- **Critical**: Domain auto-paused, reputation crash
- **High**: Multiple threshold breaches, API down
- **Medium**: Missing data, gradual decline
- **Low**: Volume inconsistency, approaching thresholds

## Implementation Checklist

### Phase 1: Foundation (Day 1-2)
- [ ] Create agent directory: `src/agents/campaign_warmup_monitor/`
- [ ] Implement `WarmupMonitorAgent` class extending `BaseAgent`
- [ ] Define all Pydantic models for input/output
- [ ] Create database migrations for 5 tables
- [ ] Apply migrations and verify schema
- [ ] Write system prompt

### Phase 2: Core Tools (Day 3-4)
- [ ] Implement `track_daily_metrics()` tool
- [ ] Implement `analyze_engagement_health()` tool
- [ ] Implement `generate_alerts()` tool
- [ ] Implement `assess_scaling_readiness()` tool
- [ ] Write unit tests for all tools (>90% coverage)

### Phase 3: Reputation Integration (Day 5)
- [ ] Create `src/integrations/google_postmaster.py`
- [ ] Create `src/integrations/senderscore.py`
- [ ] Implement `check_domain_reputation()` tool
- [ ] Test with sandbox/demo accounts
- [ ] Write integration tests

### Phase 4: Reporting (Day 6)
- [ ] Implement `create_weekly_report()` tool
- [ ] Add chart data generation
- [ ] Implement email delivery for reports
- [ ] Test report templates
- [ ] Write tests for report generation

### Phase 5: Scheduling & Automation (Day 7)
- [ ] Create Celery task for daily monitoring
- [ ] Create Celery task for weekly reports
- [ ] Configure cron schedules in Celery Beat
- [ ] Implement alert notification system
- [ ] Test automation end-to-end

### Phase 6: Agent Workflow (Day 8-9)
- [ ] Implement `process_task()` async method
- [ ] Integrate all tools into cohesive workflow
- [ ] Add error handling and recovery
- [ ] Implement state management for domains
- [ ] Write integration tests for full workflow

### Phase 7: Testing & QA (Day 10-11)
- [ ] Run full test suite (`make test`)
- [ ] Verify >85% agent coverage, >90% tool coverage
- [ ] Run type checking (`make typecheck`)
- [ ] Run linting (`make lint`)
- [ ] Load test with 100 domains
- [ ] Test failure scenarios

### Phase 8: Documentation & Deployment (Day 12)
- [ ] Add comprehensive docstrings
- [ ] Create monitoring dashboard
- [ ] Set up alerts in monitoring system
- [ ] Write deployment runbook
- [ ] Test in staging environment
- [ ] Update this spec with any changes

## Success Criteria

- [ ] All tests pass with >85% agent coverage, >90% tool coverage
- [ ] Type checking passes with zero errors (`mypy --strict`)
- [ ] Linting passes with zero errors (`ruff check`)
- [ ] Can monitor 100 domains in <10 minutes
- [ ] Accurately detects deliverability issues
- [ ] Generates actionable recommendations
- [ ] Successfully integrates with reputation APIs
- [ ] Auto-pauses domains when critical issues detected
- [ ] Weekly reports delivered on schedule

## Dependencies

### Upstream
- `Campaign Creation Agent` - Provides new domains to monitor
- `Campaign Send Agent` - Provides daily sending metrics
- Instantly API - Source of truth for sending data

### Downstream
- `Campaign Send Agent` - Receives pause/resume commands
- `System Error Monitor` - Receives critical alerts
- Human ops team - Receives notifications and reports

### External Services
- **Google Postmaster Tools** - Reputation data (API key required)
- **SenderScore** - Additional reputation data (API key required)
- **Instantly API** - Sending metrics (already integrated)
- **Email service** - For report delivery (SendGrid/SES)

## Environment Variables

```bash
# Required
INSTANTLY_API_KEY=your-instantly-api-key

# Optional but recommended
GOOGLE_POSTMASTER_API_KEY=your-google-api-key
SENDERScore_API_KEY=your-senderscore-api-key

# Configuration
WARMUP_MONITOR_SCHEDULE=0 2 * * *  # Daily at 2 AM UTC
WEEKLY_REPORT_SCHEDULE=0 9 * * 0  # Sundays at 9 AM UTC
WARMUP_ALERT_EMAIL=alerts@company.com
```

## Notes

- Warmup is critical for deliverability - be conservative in recommendations
- Always err on the side of caution when in doubt
- Reputation data may have delays - account for 24-48 hour lag
- Auto-pause is a safety net - human review should still happen
- Weekly reports help identify trends before they become problems
- Integration with Campaign Send Agent ensures coordinated scaling

## Future Enhancements (Not in MVP)

- [ ] Machine learning model to predict deliverability issues
- [ ] A/B testing for warmup schedules
- [ ] Integration with more reputation providers
- [ ] Real-time dashboard with live metrics
- [ ] Automated recommendation implementation
- [ ] Historical performance benchmarks by industry
- [ ] Warmup template library for different domain types
- [ ] Advanced analytics for engagement patterns
