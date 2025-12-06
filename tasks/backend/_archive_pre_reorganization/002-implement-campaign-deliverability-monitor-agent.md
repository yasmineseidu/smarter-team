# Task: Implement Campaign Deliverability Monitor Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/campaign-deliverability-monitor.md
**Created:** 2025-12-05

## Summary

Implement an autonomous email deliverability monitoring agent that processes bounce webhooks from Instantly, calculates domain health scores, triggers alerts when thresholds are exceeded, and can auto-pause at-risk campaigns to protect sender reputation.

## Files to Create

- `app/backend/src/agents/deliverability_monitor.py`
- `app/backend/src/agents/deliverability_tools.py`
- `app/backend/src/integrations/instantly.py`
- `app/backend/src/webhooks/instantly_webhooks.py`
- `app/backend/__tests__/unit/agents/test_deliverability_monitor.py`
- `app/backend/__tests__/unit/agents/test_deliverability_tools.py`
- `app/backend/__tests__/integration/test_deliverability_monitor_integration.py`
- `app/backend/src/models/deliverability.py`

## Implementation Checklist

### Agent Implementation
- [ ] Create `CampaignDeliverabilityMonitor` class extending BaseAgent
- [ ] Implement system prompt with detailed monitoring responsibilities
- [ ] Create Pydantic models for all inputs/outputs (BounceWebhookPayload, DeliverabilityMetrics, etc.)
- [ ] Implement configuration class with thresholds and settings

### Tools Implementation
- [ ] Implement `process_bounce_webhook` tool with webhook validation
- [ ] Implement `calculate_deliverability_metrics` with time window queries
- [ ] Implement `check_thresholds_and_alert` with alert cooldown logic
- [ ] Implement `pause_campaign` tool with Instantly API integration
- [ ] Implement `generate_weekly_report` with multiple format support
- [ ] Implement `update_domain_health_score` with weighted algorithm
- [ ] Add comprehensive error handling for all tools

### Database Schema
- [ ] Create `deliverability_metrics` table schema
- [ ] Create `domain_health` table schema
- [ ] Create `deliverability_alerts` table schema
- [ ] Add indexes for time-based queries
- [ ] Create database migration files

### Integration Components
- [ ] Create Instantly API client extending BaseIntegrationClient
- [ ] Implement webhook signature validation
- [ ] Create FastAPI webhook endpoint at `/webhooks/instantly/deliverability`
- [ ] Add rate limiting and security middleware
- [ ] Implement proper authentication/authorization

### Error Handling & Resilience
- [ ] Add retry logic with exponential backoff for API calls
- [ ] Implement circuit breaker for repeated failures
- [ ] Add graceful degradation for partial data scenarios
- [ ] Create fallback values for missing metrics
- [ ] Implement alert queuing for service outages

### Testing
- [ ] Write unit tests for all tools (mock external APIs)
- [ ] Write unit tests for webhook validation
- [ ] Write integration tests for end-to-end flows
- [ ] Add performance tests for high-volume webhook processing
- [ ] Test auto-pause functionality with mock Instantly API
- [ ] Test domain health score calculation accuracy

### Monitoring & Observability
- [ ] Add structured logging with appropriate levels
- [ ] Implement Prometheus metrics for business KPIs
- [ ] Add health check endpoints
- [ ] Create audit logging for all automated actions
- [ ] Add alerting for system failures

## Database Schema

```sql
-- deliverability_metrics table
CREATE TABLE deliverability_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    domain VARCHAR(255) NOT NULL,
    metric_date DATE NOT NULL,
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_bounces INTEGER DEFAULT 0,
    hard_bounces INTEGER DEFAULT 0,
    soft_bounces INTEGER DEFAULT 0,
    spam_complaints INTEGER DEFAULT 0,
    bounce_rate DECIMAL(5,2),
    spam_rate DECIMAL(5,2),
    delivery_rate DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- domain_health table
CREATE TABLE domain_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) UNIQUE NOT NULL,
    overall_score DECIMAL(5,2) CHECK (overall_score >= 0 AND overall_score <= 100),
    bounce_rate_score DECIMAL(5,2),
    spam_rate_score DECIMAL(5,2),
    consistency_score DECIMAL(5,2),
    reputation_score DECIMAL(5,2),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    score_trend VARCHAR(10) CHECK (score_trend IN ('up', 'stable', 'down')),
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical'))
);

-- deliverability_alerts table
CREATE TABLE deliverability_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    domain VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('info', 'warning', 'critical')),
    metric_name VARCHAR(100),
    current_value DECIMAL(10,4),
    threshold_value DECIMAL(10,4),
    message TEXT NOT NULL,
    recommendations JSONB,
    action_taken VARCHAR(100),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- bounce_events table (for detailed tracking)
CREATE TABLE bounce_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    campaign_id UUID REFERENCES campaigns(id),
    lead_id UUID REFERENCES leads(id),
    email VARCHAR(255) NOT NULL,
    bounce_type VARCHAR(20) CHECK (bounce_type IN ('hard', 'soft', 'spam')),
    bounce_reason TEXT,
    domain VARCHAR(255) NOT NULL,
    ip_address INET,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_deliverability_metrics_campaign_date ON deliverability_metrics(campaign_id, metric_date);
CREATE INDEX idx_deliverability_metrics_domain_date ON deliverability_metrics(domain, metric_date);
CREATE INDEX idx_bounce_events_campaign_created ON bounce_events(campaign_id, created_at);
CREATE INDEX idx_deliverability_alerts_campaign_severity ON deliverability_alerts(campaign_id, severity);
```

## Acceptance Criteria

From spec/agents/campaign-deliverability-monitor.md:

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

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_deliverability_monitor.py -v
pytest app/backend/__tests__/unit/agents/test_deliverability_tools.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_deliverability_monitor_integration.py -v

# Type checking
mypy app/backend/src/agents/deliverability_monitor.py
mypy app/backend/src/agents/deliverability_tools.py

# Linting
ruff check app/backend/src/agents/deliverability_monitor.py
ruff check app/backend/src/agents/deliverability_tools.py

# Database migration
make migrate

# Manual test - webhook endpoint
curl -X POST http://localhost:8000/webhooks/instantly/deliverability \
  -H "Content-Type: application/json" \
  -H "X-Instantly-Signature: test" \
  -d '{"event_id":"test","campaign_id":"test","email":"test@example.com","bounce_type":"hard"}'

# Manual test - agent instantiation
python -c "from app.backend.src.agents.deliverability_monitor import CampaignDeliverabilityMonitor; print('Agent loaded successfully')"
```

## Dependencies

- Instantly API key (`INSTANTLY_API_KEY`)
- Database schema migrations applied
- Campaign Creation Agent deployed (for handoffs)
- System Health Monitor deployed (for error notifications)
- Webhook signature secret configured

## Notes

- Follow existing patterns in `app/backend/src/agents/base_agent.py`
- Use structured logging via `get_agent_logger("deliverability_monitor")`
- All I/O operations must be async
- Handle webhook deduplication using event_id
- Implement proper rate limiting for monitoring endpoints
- Cache frequent queries to improve performance
- Document all automated actions in audit trail
