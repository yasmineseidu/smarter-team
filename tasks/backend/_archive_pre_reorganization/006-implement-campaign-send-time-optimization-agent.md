# Task: Implement Campaign Send Time Optimization Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/campaign-send-time-optimization.md
**Created:** 2025-12-05

## Summary

Implement the Campaign Send Time Optimization Agent that maximizes email engagement by determining optimal send times for each lead. The agent combines timezone detection, engagement pattern analysis, cohort intelligence, and A/B testing to continuously optimize send times.

The implementation spans 4 phases:
1. **Basic** - Timezone detection + business hours
2. **Individual** - Personal engagement patterns
3. **Cohort** - Industry/role-based patterns
4. **Full** - A/B testing with statistical analysis

## Files to Create

- `app/backend/src/agents/campaign_send_time_optimization/`
  - `__init__.py` - Exports
  - `agent.py` - Main agent class extending BaseAgent
  - `tools.py` - 7 tool functions for optimization
  - `prompts.py` - System prompt constants
  - `schemas.py` - Pydantic models for inputs/outputs
  - `exceptions.py` - Custom exception classes
- `app/backend/src/integrations/nominatim.py` - OpenStreetMap geocoding client
- `app/backend/src/integrations/ipinfo.py` - Optional IP geolocation client
- `app/backend/__tests__/unit/agents/test_campaign_send_time_optimization.py`
- `app/backend/__tests__/integration/test_send_time_optimization_integration.py`
- Database migrations for 5 tables

## Implementation Checklist

### Phase 1: Foundation (Day 1-2)
- [ ] Create agent directory structure with all files
- [ ] Implement `SendTimeOptimizationAgent` class extending `BaseAgent`
- [ ] Define all Pydantic models in `schemas.py`
- [ ] Write comprehensive system prompt in `prompts.py`
- [ ] Create database migrations for all 5 tables
- [ ] Apply migrations and verify schema with psql
- [ ] Add custom exception classes in `exceptions.py`

### Phase 2: Timezone Detection (Days 3-4)
- [ ] Implement `detect_timezone()` tool with confidence scoring
- [ ] Create `NominatimClient` integration for geocoding
- [ ] Implement IP-based geolocation fallback (optional)
- [ ] Add Redis caching with 7-day TTL
- [ ] Implement timezone validation with pytz
- [ ] Write unit tests for all detection paths
- [ ] Verify accuracy with known location test data

### Phase 3: Pattern Analysis (Days 5-6)
- [ ] Implement `analyze_engagement_patterns()` tool
- [ ] Apply exponential decay for recent engagement weighting
- [ ] Implement `get_cohort_patterns()` tool with fuzzy matching
- [ ] Create confidence interval calculation logic
- [ ] Add pattern strength classification (weak/strong/very_strong)
- [ ] Implement minimum sample size enforcement
- [ ] Write tests covering edge cases and data quality scenarios

### Phase 4: Optimization Engine (Days 7-8)
- [ ] Implement `get_business_hours()` with industry/role adjustments
- [ ] Add holiday detection and avoidance logic
- [ ] Implement `calculate_optimal_send_time()` combining all sources
- [ ] Create priority algorithm: individual > cohort > basic
- [ ] Add timezone conversion and validation
- [ ] Implement business hour constraint enforcement
- [ ] Write comprehensive optimization logic tests

### Phase 5: A/B Testing Framework (Days 9-10)
- [ ] Implement `schedule_ab_test()` tool with random assignment
- [ ] Add chi-square statistical analysis functions
- [ ] Create test tracking and winner determination
- [ ] Implement confidence level calculations (95% default)
- [ ] Add automatic pattern updates from test results
- [ ] Create test completion monitoring
- [ ] Write A/B test suite with statistical validation

### Phase 6: Instantly Integration (Day 11)
- [ ] Implement `schedule_with_instantly()` tool
- [ ] Handle Instantly API rate limiting (10 req/s)
- [ ] Add batch scheduling optimization
- [ ] Implement proper timezone conversion for API
- [ ] Add comprehensive error handling and retry logic
- [ ] Test with Instantly sandbox environment
- [ ] Verify send time accuracy end-to-end

### Phase 7: Agent Workflow & Learning (Day 12)
- [ ] Implement `process_task()` method handling all 4 optimization levels
- [ ] Add batch processing logic for up to 500 leads
- [ ] Implement weekly learning loop Celery task
- [ ] Create cohort pattern recalculation logic
- [ ] Add optimization summary report generation
- [ ] Implement comprehensive logging with structured data
- [ ] Write integration tests for full workflow

### Phase 8: Testing & Quality Assurance (Days 13-14)
- [ ] Complete all unit tests (target: >90% coverage for tools)
- [ ] Complete all integration tests (target: >85% coverage for agent)
- [ ] Run performance tests with 100-lead batches (<30s)
- [ ] Test memory usage stays under 200MB
- [ ] Verify error handling for all failure modes
- [ ] Run full quality check suite (`make check`)
- [ ] Fix any failing tests or type errors

### Phase 9: Monitoring & Deployment (Day 15)
- [ ] Add monitoring metrics for all key KPIs
- [ ] Set up alerts for critical metrics (<80% timezone confidence)
- [ ] Create optimization dashboard with visualizations
- [ ] Write deployment documentation and runbook
- [ ] Test in staging environment with production data
- [ ] Prepare rollback procedures for failures
- [ ] Document integration points and dependencies

## Acceptance Criteria

From spec - all must be satisfied:

- [ ] All timezone detections complete with >80% confidence
- [ ] Individual patterns created for leads with >5 engagements
- [ ] Cohort patterns maintained for all industry/role combos with >50 samples
- [ ] A/B tests run automatically when sufficient sample size available
- [ ] Patterns updated weekly based on recent performance data
- [ ] All sends respect business hours and avoid national holidays
- [ ] Instantly API integration successfully schedules optimized sends
- [ ] Processing time: <30 seconds for batch of 100 leads
- [ ] Test coverage: >90% for tools, >85% for agent
- [ ] Zero timezone-related send failures in production testing

## Verification Commands

```bash
# Run all tests
pytest app/backend/__tests__/unit/agents/test_campaign_send_time_optimization.py -v
pytest app/backend/__tests__/integration/test_send_time_optimization_integration.py -v

# Type checking
mypy app/backend/src/agents/campaign_send_time_optimization/

# Linting
ruff check app/backend/src/agents/campaign_send_time_optimization/
ruff format app/backend/src/agents/campaign_send_time_optimization/

# Database verification
psql $DATABASE_URL -c "\d lead_timezones"
psql $DATABASE_URL -c "\d engagement_patterns"
psql $DATABASE_URL -c "\d cohort_patterns"
psql $DATABASE_URL -c "\d send_time_optimization"
psql $DATABASE_URL -c "\d ab_tests"

# Manual test
python -c "from app.backend.src.agents.campaign_send_time_optimization import SendTimeOptimizationAgent; print('Agent imports successfully')"

# Performance test
time python -c "import asyncio; from app.backend.src.agents.campaign_send_time_optimization import SendTimeOptimizationAgent; asyncio.run(SendTimeOptimizationAgent().optimize_send_times_basic([{'lead_id': 'test', 'company_location': 'San Francisco, CA'}]))"
```

## Dependencies

### Must be implemented first:
- Database migrations must be applied
- Redis cache must be configured
- Instantly API key must be available in environment

### Optional dependencies (can be mocked for testing):
- IPInfo.io API key for IP geolocation
- Holiday API for national holiday detection

### External services to test with:
- OpenStreetMap Nominatim API (free, no key needed)
- Instantly sandbox API for send scheduling
