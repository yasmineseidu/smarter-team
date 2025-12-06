# Revenue Tracking Agent - Technical Specification

**Status:** Production-Ready
**Version:** 1.0.0
**Created:** 2025-12-05
**Category:** Payment & Finance
**Phase:** Phase 4 - Client Delivery

---

## 1. Overview

### Purpose
Autonomously track, calculate, and report all financial metrics for the AI agency including MRR, ARR, revenue per client, campaign ROI, customer acquisition cost, and lifetime value. Provides real-time financial insights through automated reports and dashboard updates.

### Agent Classification
- **Type:** Analytical Agent
- **Execution Mode:** Scheduled (Celery beat) + On-demand
- **Human-in-the-Loop:** Strategic decisions based on data
- **Priority:** High (financial visibility critical)

### Dependencies
- **Upstream Agents:**
  - Invoice Generation Agent (provides payment events)
  - Payment Collection Agent (provides payment confirmations)
  - Campaign Performance Agent (provides attribution data)
- **Downstream Agents:**
  - None (data sink for financial insights)
- **External Services:**
  - Stripe API (payment and revenue data)
  - QuickBooks API (expense data)
  - Internal database (client, campaign, project data)

---

## 2. System Prompt

```
You are the Revenue Tracking Agent for Smarter Team, an AI agency automation system.

Your responsibilities:
- Track all revenue events in real-time from Stripe and internal systems
- Calculate key financial metrics (MRR, ARR, LTV, CAC, ROI)
- Generate comprehensive financial reports (weekly, monthly, ad-hoc)
- Update financial dashboard with latest metrics
- Monitor financial health and alert on anomalies
- Provide attribution analysis linking revenue to campaigns and clients

Key Metrics You Calculate:
1. MRR (Monthly Recurring Revenue): Sum of active retainers / 12
2. ARR (Annual Recurring Revenue): MRR * 12
3. Revenue per Client: Total revenue / Number of clients
4. Revenue per Campaign: Campaign revenue / Campaign cost
5. CAC (Customer Acquisition Cost): Total marketing spend / New clients
6. LTV (Lifetime Value): Avg revenue per client * Avg lifespan
7. LTV:CAC Ratio: LTV / CAC (target > 3:1)

Data Sources:
- Stripe: All payment transactions, subscriptions, invoices
- QuickBooks: Expense data for cost calculations
- Internal DB: Client data, campaign data, project data, attribution

Report Types:
1. DAILY: Revenue summary, new payments, active subscriptions
2. WEEKLY: Performance vs last week, top campaigns, client metrics
3. MONTHLY: Full financial breakdown, trends, forecasts
4. AD-HOC: Custom reports for specific queries

Calculation Rules:
- Use accrual accounting for revenue recognition
- Recognize revenue when service is delivered, not when paid
- Exclude failed payments and refunds from revenue
- Include pending payments in pipeline value
- Calculate churn rate for subscription revenue

You have access to these tools:
- fetch_stripe_revenue: Retrieve payment and subscription data
- fetch_quickbooks_expenses: Get expense data for cost calculations
- calculate_mrr_arr: Compute recurring revenue metrics
- calculate_per_client_metrics: Analyze client-level financials
- calculate_per_campaign_roi: Analyze campaign performance
- generate_financial_report: Create structured reports
- update_dashboard_metrics: Push metrics to dashboard
- detect_financial_anomalies: Identify unusual patterns
- forecast_revenue: Predict future revenue based on trends

Error Handling:
- If Stripe API fails → Use cached data, retry with backoff
- If QuickBooks fails → Estimate costs based on historical averages
- If data inconsistency → Log warning, use best available data
- If calculation error → Return last known good values, alert
- If dashboard update fails → Report still generated, queue retry

Always structure responses as JSON with:
{
  "status": "success|partial|error",
  "report_type": "daily|weekly|monthly|ad-hoc",
  "period": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD"
  },
  "metrics": {
    "mrr": 50000.00,
    "arr": 600000.00,
    "revenue_per_client": 12500.00,
    "cac": 3500.00,
    "ltv": 37500.00,
    "ltv_cac_ratio": 10.71
  },
  "insights": [
    "Revenue increased 15% vs last month",
    "Top performing campaign: SaaS lead gen (5.2x ROI)"
  ],
  "data freshness": {
    "stripe": "2025-12-05T10:30:00Z",
    "quickbooks": "2025-12-05T09:15:00Z",
    "internal": "2025-12-05T10:45:00Z"
  },
  "errors": [],
  "next_update": "2025-12-06T08:00:00Z"
}
```

---

## 3. Agent Architecture

### Class Definition

```python
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Literal

from src.agents.base_agent import BaseAgent
from src.integrations.stripe_client import StripeClient
from src.integrations.quickbooks_client import QuickBooksClient
from src.config import get_agent_logger

ReportType = Literal["daily", "weekly", "monthly", "ad-hoc"]
MetricType = Literal["mrr", "arr", "revenue_per_client", "cac", "ltv", "roi"]

class RevenueTrackingAgent(BaseAgent):
    """
    Autonomous financial metrics tracking and reporting agent.

    Calculates and reports on all key financial metrics for the agency.
    Integrates with Stripe, QuickBooks, and internal data sources.
    """

    def __init__(self):
        super().__init__(
            name="revenue_tracking",
            description="Track and report financial metrics and KPIs"
        )

        # Integration clients (lazy loaded)
        self._stripe_client: StripeClient | None = None
        self._quickbooks_client: QuickBooksClient | None = None

        # Configuration
        self.max_retries = 3
        self.cache_ttl_minutes = 60
        self.anomaly_threshold = Decimal("0.15")  # 15% variance

        # Register tools
        self._register_tools()

    @property
    def system_prompt(self) -> str:
        """Return system prompt from section 2."""
        return """[System prompt from section 2 above]"""
```

### Tool Specifications

#### Tool: fetch_stripe_revenue
**Purpose:** Retrieve revenue data from Stripe API

**Input Schema:**
```python
class FetchStripeRevenueInput(BaseModel):
    start_date: datetime = Field(..., description="Start date for revenue data")
    end_date: datetime = Field(..., description="End date for revenue data")
    include_pending: bool = Field(default=True, description="Include pending payments")
    subscription_status: list[str] = Field(
        default=["active", "trialing"],
        description="Subscription statuses to include"
    )
```

**Output Schema:**
```python
class StripeRevenueData(BaseModel):
    total_revenue: Decimal
    recurring_revenue: Decimal
    one_time_revenue: Decimal
    refunds: Decimal
    failed_payments: Decimal
    new_customers: int
    churned_customers: int
    active_subscriptions: int
    transactions: list[dict]
    last_updated: datetime
```

**Error Handling:**
- Rate limit (429) → Exponential backoff, max 5 retries
- Auth error (401) → Fail immediately, alert ops
- Timeout → Retry 2x with longer timeout
- Partial data → Return what's available, note gaps

---

## 4. Database Schema

### Tables

#### revenue_events
```sql
CREATE TABLE revenue_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,  -- 'payment', 'refund', 'subscription'
    source VARCHAR(20) NOT NULL,      -- 'stripe', 'quickbooks', 'internal'
    source_id VARCHAR(100) NOT NULL,  -- External ID
    client_id UUID REFERENCES clients(id),
    campaign_id UUID REFERENCES campaigns(id),
    project_id UUID REFERENCES projects(id),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    event_date TIMESTAMP WITH TIME ZONE NOT NULL,
    recognized_date TIMESTAMP WITH TIME ZONE,  -- When revenue is recognized
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source, source_id)
);
```

#### revenue_metrics
```sql
CREATE TABLE revenue_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(50) NOT NULL,  -- 'mrr', 'arr', 'cac', 'ltv', etc.
    metric_date DATE NOT NULL,
    value DECIMAL(12,2) NOT NULL,
    dimensions JSONB,  -- e.g., {"client_id": "xxx", "campaign_id": "yyy"}
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(metric_type, metric_date, (dimensions::text))
);
```

#### financial_reports
```sql
CREATE TABLE financial_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(20) NOT NULL,  -- 'daily', 'weekly', 'monthly'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    report_data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(report_type, period_start, period_end)
);
```

### Indexes
```sql
CREATE INDEX idx_revenue_events_date ON revenue_events(event_date);
CREATE INDEX idx_revenue_events_client ON revenue_events(client_id);
CREATE INDEX idx_revenue_events_campaign ON revenue_events(campaign_id);
CREATE INDEX idx_revenue_metrics_date ON revenue_metrics(metric_date);
CREATE INDEX idx_revenue_metrics_type ON revenue_metrics(metric_type);
```

---

## 5. Error Handling Matrix

| Component | Error Type | Detection | Response | Retry |
|-----------|------------|-----------|----------|-------|
| Stripe API | Rate limit (429) | HTTP status | Backoff retry | Yes, 5x |
| Stripe API | Auth error (401) | HTTP status | Fail, alert | No |
| Stripe API | Timeout | Exception | Retry with longer timeout | Yes, 2x |
| QuickBooks API | Any error | HTTP status | Use cached expenses | No |
| Database | Connection error | Exception | Retry 3x | Yes |
| Database | Constraint violation | Exception | Log and skip | No |
| Calculation | Invalid data | Validation | Use fallback value | No |
| Calculation | Division by zero | Exception | Return 0 with note | No |
| Dashboard | Update failure | HTTP status | Queue for retry | Yes |
| Report generation | Memory error | Exception | Generate partial report | No |

### Recovery Strategies
1. **Graceful degradation:** Return partial metrics if some data sources fail
2. **Fallback values:** Use historical averages for missing data
3. **Caching:** Cache successful results for 1 hour to serve during outages
4. **Alerting:** Immediate alerts for critical failures (auth, data corruption)

---

## 6. Testing Strategy

### Unit Tests
```python
def test_mrr_calculation_with_active_subscriptions():
    """Verify MRR calculation with mixed subscription tiers."""

def test_cac_calculation_with_marketing_expenses():
    """Verify CAC includes all marketing and sales costs."""

def test_ltv_cac_ratio_calculation():
    """Verify LTV:CAC ratio calculation and threshold alerts."""

def test_revenue_attribution_per_campaign():
    """Verify accurate revenue attribution to campaigns."""

def test_anomaly_detection_for_revenue_spikes():
    """Verify anomaly detection flags unusual revenue changes."""

def test_forecast_accuracy_with_historical_data():
    """Verify revenue forecast based on historical trends."""
```

### Integration Tests
```python
def test_end_to_end_monthly_report_generation():
    """Full monthly report with mocked Stripe/QuickBooks."""

def test_real_time_dashboard_update_flow():
    """Dashboard update after new payment event."""

def test_cross_data_source_reconciliation():
    """Verify Stripe revenue matches internal records."""

def test_graceful_degradation_with_stripe_down():
    """Report generation continues with cached data."""
```

### Mock Strategy
```python
@pytest.fixture
def mock_stripe_client():
    with patch('src.integrations.stripe_client.StripeClient') as mock:
        mock.return_value.get_balance_transactions.return_value = {
            "data": mock_stripe_transactions
        }
        yield mock

@pytest.fixture
def mock_quickbooks_client():
    with patch('src.integrations.quickbooks_client.QuickBooksClient') as mock:
        mock.return_value.get_expenses.return_value = mock_expenses
        yield mock
```

---

## 7. Performance Requirements

### Latency
- Daily report generation: < 30 seconds
- Weekly report generation: < 2 minutes
- Monthly report generation: < 5 minutes
- Real-time metric calculation: < 5 seconds

### Throughput
- Handle 10,000+ revenue events per month
- Process 100+ concurrent report requests
- Support dashboard refresh rate of 1 minute

### Caching
- Stripe data: Cache for 5 minutes
- QuickBooks data: Cache for 1 hour
- Calculated metrics: Cache for 15 minutes
- Reports: Store permanently, regenerate on demand

---

## 8. Observability

### Logging
```python
# Structured logging examples
logger.info(
    "Generated monthly revenue report",
    extra={
        "report_type": "monthly",
        "period": "2025-11-01 to 2025-11-30",
        "mrr": 125000.00,
        "growth_rate": 0.15,
        "data_sources": ["stripe", "quickbooks", "internal"]
    }
)

logger.error(
    "Failed to fetch Stripe data",
    extra={
        "error_type": "rate_limit",
        "retry_count": 3,
        "backoff_seconds": 300
    }
)
```

### Metrics to Track
- Report generation time and success rate
- Data freshness for each source
- API call counts and error rates
- Cache hit/miss ratios
- Anomaly detection accuracy
- Dashboard update latency

### Health Checks
- Stripe API connectivity
- QuickBooks API connectivity
- Database query performance
- Memory usage during report generation
- Celery task queue backlog

---

## 9. Security

### Data Protection
- Encrypt sensitive financial data at rest
- Use HTTPS for all API communications
- Implement API key rotation for Stripe/QuickBooks
- Log all data access for audit trail

### Access Control
- Restrict financial report access to authorized users
- Implement role-based viewing permissions
- Mask sensitive client data in logs

### Compliance
- Follow PCI DSS for payment data handling
- Maintain audit logs for financial transactions
- Implement data retention policies

---

## 10. Acceptance Criteria

- [ ] Successfully fetches revenue data from Stripe API
- [ ] Integrates with QuickBooks for expense data
- [ ] Calculates all specified metrics accurately
- [ ] Generates daily, weekly, and monthly reports
- [ ] Updates dashboard with real-time metrics
- [ ] Handles API failures gracefully with fallbacks
- [ ] Detects and alerts on financial anomalies
- [ ] Provides revenue attribution by client and campaign
- [ ] Maintains data consistency across sources
- [ ] Meets performance requirements for all report types
- [ ] Passes all unit and integration tests
- [ ] Implements proper error handling and logging
- [ ] Follows security best practices for financial data

---

## 11. Implementation Tasks

1. Create agent class inheriting from BaseAgent
2. Implement all tools with proper input/output schemas
3. Add database models and migrations
4. Create Stripe and QuickBooks integration methods
5. Implement metric calculation algorithms
6. Build report generation templates
7. Add dashboard update mechanisms
8. Implement caching layer
9. Add comprehensive error handling
10. Write unit tests for all calculations
11. Write integration tests for external APIs
12. Add logging and monitoring
13. Schedule Celery tasks for automated reports
14. Document API endpoints for dashboard integration
