# Task: Implement Revenue Tracking Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/payment-revenue-tracking.md
**Created:** 2025-12-05

## Summary
Implement the Revenue Tracking Agent that monitors, calculates, and reports on all financial metrics for the AI agency including MRR, ARR, revenue per client, campaign ROI, CAC, and LTV. Integrates with Stripe, QuickBooks, and internal database for comprehensive financial insights.

## Files to Create
- `app/backend/src/agents/revenue_tracking/revenue_tracking_agent.py`
- `app/backend/src/agents/revenue_tracking/tools/`
  - `stripe_tools.py` - Stripe revenue data fetching
  - `quickbooks_tools.py` - Expense data retrieval
  - `calculation_tools.py` - Metric calculations
  - `report_tools.py` - Report generation
- `app/backend/src/models/revenue.py` - Database models
- `app/backend/__tests__/unit/agents/test_revenue_tracking.py`
- `app/backend/__tests__/integration/test_revenue_tracking_integration.py`
- `app/backend/migrations/versions/xxx_add_revenue_tables.py` - Database migration

## Implementation Checklist

### Core Agent Implementation
- [ ] Create `RevenueTrackingAgent` class extending `BaseAgent`
- [ ] Implement system prompt with all capabilities and rules
- [ ] Set up lazy-loaded integration clients (Stripe, QuickBooks)
- [ ] Register all tools with proper descriptions
- [ ] Implement `process_task()` method with task routing

### Tools Implementation
- [ ] **fetch_stripe_revenue**: Retrieve payments, subscriptions, refunds
  - Handle pagination for large datasets
  - Include error handling for rate limits
  - Cache results for 5 minutes
- [ ] **fetch_quickbooks_expenses**: Get marketing and operational expenses
  - Categorize expenses for CAC calculation
  - Handle partial data gracefully
- [ ] **calculate_mrr_arr**: Compute recurring revenue from subscriptions
  - Handle different billing frequencies (monthly, quarterly, annual)
  - Exclude churned subscriptions
- [ ] **calculate_per_client_metrics**: Analyze client-level financials
  - Calculate revenue per client
  - Track client lifetime value
  - Identify top/bottom performing clients
- [ ] **calculate_per_campaign_roi**: Analyze campaign performance
  - Link revenue to specific campaigns
  - Calculate ROI including campaign costs
  - Rank campaigns by performance
- [ ] **calculate_cac_ltv**: Compute customer acquisition metrics
  - Include all marketing and sales expenses
  - Calculate average client lifespan
  - Compute LTV:CAC ratio with alerts
- [ ] **generate_financial_report**: Create structured reports
  - Support daily, weekly, monthly, ad-hoc formats
  - Include all calculated metrics
  - Add insights and trends
- [ ] **detect_anomalies**: Identify unusual patterns
  - Detect revenue spikes/drops >15%
  - Alert on subscription churn
  - Flag calculation errors

### Database Implementation
- [ ] Create `revenue_events` table for tracking all financial events
- [ ] Create `revenue_metrics` table for storing calculated metrics
- [ ] Create `financial_reports` table for generated reports
- [ ] Add proper indexes for query performance
- [ ] Create database migration

### Integration & Testing
- [ ] Implement comprehensive unit tests for all calculations
  - Test MRR/ARR with various subscription mixes
  - Test CAC with different expense allocations
  - Test LTV:CAC ratio calculations
- [ ] Write integration tests with mocked APIs
  - Test end-to-end report generation
  - Test error handling and fallbacks
  - Test data reconciliation
- [ ] Add performance tests for large datasets
  - Test with 10k+ revenue events
  - Verify report generation timing
- [ ] Test anomaly detection accuracy
  - Create test scenarios with outliers
  - Verify alert thresholds

### Deployment & Monitoring
- [ ] Schedule Celery tasks for automated reports
  - Daily: 8:00 AM summary
  - Weekly: Monday 8:00 AM detailed
  - Monthly: 1st of month 8:00 AM comprehensive
- [ ] Add structured logging for all operations
  - Log report generation metrics
  - Track API call performance
  - Record data freshness
- [ ] Implement health checks
  - Verify API connectivity
  - Check database performance
  - Monitor task queue backlog
- [ ] Add configuration management
  - Set anomaly thresholds
  - Configure cache TTLs
  - Manage retry parameters

### Acceptance Criteria
- [ ] Successfully fetches real revenue data from Stripe
- [ ] Integrates with QuickBooks for expense data
- [ ] Accurately calculates all specified metrics
- [ ] Generates all report types with correct format
- [ ] Updates dashboard with real-time metrics
- [ ] Handles API failures gracefully
- [ ] Detects and alerts on financial anomalies
- [ ] Provides accurate revenue attribution
- [ ] Meets performance requirements
- [ ] Passes all tests
- [ ] Implements proper security practices

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_revenue_tracking.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_revenue_tracking_integration.py -v

# Type checking
mypy app/backend/src/agents/revenue_tracking/

# Linting
ruff check app/backend/src/agents/revenue_tracking/

# Run database migration
cd app/backend && make migrate

# Test Celery task execution
make worker
celery -A src.celery_app call revenue_tracking.generate_daily_report

# Manual agent test
python -c "
from src.agents.revenue_tracking.revenue_tracking_agent import RevenueTrackingAgent
import asyncio

async def test():
    agent = RevenueTrackingAgent()
    result = await agent.process_task({
        'type': 'monthly',
        'period': '2025-11'
    })
    print(result)

asyncio.run(test())
"
```

## Dependencies
- Stripe API key configured in environment
- QuickBooks OAuth credentials set up
- Database connection established
- Redis for Celery task queue
- S3/s3-compatible storage for report exports (optional)

## Notes
- Agent should be idempotent - safe to retry tasks
- All currency values should use Decimal for precision
- Consider implementing data archiving for old revenue events
- Add webhooks for real-time payment event processing
