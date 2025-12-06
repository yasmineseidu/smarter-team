# Task: Implement Campaign Warmup Monitor Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/campaign-warmup-monitor.md
**Created:** 2025-12-05
**Priority:** High (Phase 3 - Closing & Proposals)

## Summary

Implement the Campaign Warmup Monitor agent to track email warmup progress for sending domains. This agent monitors engagement metrics, tracks domain reputation, generates alerts for deliverability issues, and recommends when domains are ready for volume scaling. Critical for protecting sender reputation and ensuring high deliverability rates.

## Files to Create

### Core Implementation
- `app/backend/src/agents/campaign_warmup_monitor/agent.py` - Main agent class
- `app/backend/src/agents/campaign_warmup_monitor/tools.py` - All tool implementations
- `app/backend/src/agents/campaign_warmup_monitor/models.py` - Pydantic models
- `app/backend/src/agents/campaign_warmup_monitor/__init__.py` - Package init

### Integration Clients
- `app/backend/src/integrations/google_postmaster.py` - Google Postmaster API client
- `app/backend/src/integrations/senderscore.py` - SenderScore API client

### Database
- `app/backend/migrations/versions/001_create_domain_warmup_tables.py` - Schema migrations

### Tests
- `app/backend/__tests__/unit/agents/test_campaign_warmup_monitor.py` - Agent tests
- `app/backend/__tests__/unit/agents/tools/test_warmup_tools.py` - Tool tests
- `app/backend/__tests__/integration/test_warmup_monitor_integration.py` - Integration tests
- `app/backend/__tests__/fixtures/warmup_fixtures.py` - Test fixtures

### Tasks
- `app/backend/src/tasks/warmup_tasks.py` - Celery tasks for monitoring

## Implementation Checklist

### Phase 1: Foundation (Day 1-2)
- [ ] Create agent package directory structure
- [ ] Implement `WarmupMonitorAgent` class extending `BaseAgent`
- [ ] Define all Pydantic models (input/output schemas)
- [ ] Create database migration for 5 tables:
  - `domain_warmup`
  - `warmup_metrics`
  - `domain_reputation`
  - `warmup_alerts`
  - `warmup_reports`
- [ ] Apply migrations and verify schema in test DB
- [ ] Write system prompt following spec
- [ ] Create test fixtures for warmup data

### Phase 2: Core Tools (Day 3-4)
- [ ] Implement `track_daily_metrics()` tool with trend analysis
- [ ] Implement `analyze_engagement_health()` with benchmark comparison
- [ ] Implement `generate_alerts()` with threshold checking and de-duplication
- [ ] Implement `assess_scaling_readiness()` with conservative decision logic
- [ ] Implement `update_warmup_schedule()` for pause/resume/promote actions
- [ ] Add comprehensive error handling to all tools
- [ ] Write unit tests for each tool (>90% coverage required)

### Phase 3: Reputation Integration (Day 5)
- [ ] Create `GooglePostmasterClient` extending `BaseIntegrationClient`
- [ ] Create `SenderScoreClient` extending `BaseIntegrationClient`
- [ ] Implement `check_domain_reputation()` tool
- [ ] Add caching layer for reputation data (24h TTL)
- [ ] Handle API rate limits and failures gracefully
- [ ] Mock external APIs for testing
- [ ] Write integration tests for reputation services

### Phase 4: Reporting & Analytics (Day 6)
- [ ] Implement `create_weekly_report()` tool
- [ ] Add chart data generation for visualizations
- [ ] Implement email delivery for reports
- [ ] Create HTML/email templates for reports
- [ ] Add report scheduling logic
- [ ] Test report generation with sample data

### Phase 5: Automation & Scheduling (Day 7)
- [ ] Create `daily_monitoring` Celery task
- [ ] Create `weekly_reporting` Celery task
- [ ] Create `process_alerts` Celery task
- [ ] Configure cron schedules in Celery Beat:
  - Daily monitoring: 0 2 * * * (2 AM UTC)
  - Weekly reports: 0 9 * * 0 (Sunday 9 AM UTC)
  - Alert processing: */30 * * * * (every 30 minutes)
- [ ] Add alert notification system (email/Slack)
- [ ] Test all scheduled tasks

### Phase 6: Agent Workflow (Day 8-9)
- [ ] Implement `process_task()` async method with complete workflow
- [ ] Integrate all tools into cohesive monitoring system
- [ ] Add state management for domain warmup stages
- [ ] Implement graceful failure recovery
- [ ] Add comprehensive logging and metrics
- [ ] Write end-to-end integration tests

### Phase 7: Testing & Quality Assurance (Day 10-11)
- [ ] Run complete test suite: `make test`
- [ ] Verify >85% agent coverage, >90% tool coverage
- [ ] Run type checking: `make typecheck`
- [ ] Run linting: `make lint`
- [ ] Fix all errors and warnings
- [ ] Load test with 100 simulated domains
- [ ] Test all failure scenarios and recovery

### Phase 8: Documentation & Deployment (Day 12)
- [ ] Add comprehensive docstrings to all methods
- [ ] Create README in agent package
- [ ] Update CLAUDE.md with new agent details
- [ ] Set up monitoring dashboards
- [ ] Configure production alerts
- [ ] Test in staging environment
- [ ] Prepare deployment runbook

## Acceptance Criteria

From spec/agents/campaign-warmup-monitor.md:

### Functional Requirements
- [ ] Successfully tracks daily warmup metrics for all domains
- [ ] Monitors engagement rates against industry benchmarks
- [ ] Generates alerts for threshold breaches (critical, high, medium, low)
- [ ] Checks domain reputation from Google Postmaster and SenderScore
- [ ] Assesses readiness for warmup stage progression
- [ ] Generates comprehensive weekly reports with charts
- [ ] Auto-pauses domains on critical issues
- [ ] Provides actionable scaling recommendations

### Quality Requirements
- [ ] All tests pass with >85% agent coverage, >90% tool coverage
- [ ] Type checking passes with zero errors (`mypy --strict`)
- [ ] Linting passes with zero errors (`ruff check`)
- [ ] Can monitor 100 domains in <10 minutes
- [ ] Zero data loss on failures (database transactions)
- [ ] Graceful handling of external API failures

### Integration Requirements
- [ ] Receives metrics from Campaign Send Agent
- [ ] Sends pause/resume commands to Campaign Send Agent
- [ ] Fetches data from Instantly API
- [ ] Integrates with Google Postmaster Tools API
- [ ] Integrates with SenderScore API
- [ ] Delivers reports via email

## Verification

```bash
# Database setup
cd app/backend
make migrate  # Apply migrations

# Run tests
make test  # Full test suite
pytest app/backend/__tests__/unit/agents/test_campaign_warmup_monitor.py -v
pytest app/backend/__tests__/integration/test_warmup_monitor_integration.py -v

# Quality checks
make typecheck
make lint
make format-check

# Manual verification
python -c "
from src.agents.campaign_warmup_monitor.agent import WarmupMonitorAgent
agent = WarmupMonitorAgent()
print(f'Agent created: {agent.name}')
print(f'System prompt length: {len(agent.system_prompt)} chars')
"

# Test with sample data
python scripts/test_warmup_monitor.py --domain test.example.com --days 7
```

## Critical Implementation Notes

1. **Conservative Approach**: Always err on the side of caution for warmup decisions. Better to warm up slowly than damage reputation.

2. **Data Quality**: Implement strict validation for all incoming metrics. Reject or flag implausible values (e.g., >100% open rates).

3. **Rate Limiting**: Respect API rate limits for all external services. Implement exponential backoff for retries.

4. **Alert Fatigue**: Implement alert de-duplication and grouping to avoid overwhelming the ops team.

5. **Historical Context**: Maintain full historical data to identify trends, not just daily snapshots.

6. **Reputation Lag**: Account for 24-48 hour delays in reputation data updates.

7. **Testing**: Mock all external APIs in unit tests. Use sandbox environments for integration tests.

## Dependencies

### Must be completed first:
- Database migrations applied
- Instantly API client integration
- BaseAgent class implemented
- Celery task queue configured

### Blocking dependencies:
- None - this agent can operate independently once basic infrastructure is in place

### External services needed:
- Instantly API (already configured)
- Google Postmaster Tools API access
- SenderScore API access (optional but recommended)
- Email service for report delivery (SendGrid/SES)

## Risk Mitigation

1. **API Failures**: Implement fallback behavior when external APIs are unavailable
2. **Data Gaps**: Handle missing reputation data gracefully
3. **False Positives**: Review and tune alert thresholds based on initial data
4. **Performance**: Use database indexes and caching for scalable monitoring
5. **Security**: Secure API keys and encrypt sensitive domain data

## Success Metrics

- **Accuracy**: <5% false positive rate for critical alerts
- **Performance**: Monitor 100 domains in <10 minutes
- **Reliability**: >99.9% uptime for daily monitoring
- **Effectiveness**: Zero domain reputation crashes during warmup
- **User Satisfaction**: <2 critical alerts per month per 100 domains

## Rollback Plan

If issues arise:
1. Pause the agent's Celery tasks
2. Domains continue in current warmup stage (no automatic progression)
3. Manual monitoring can continue via database queries
4. Alert generation can be disabled while keeping monitoring active
5. All historical data remains intact for analysis

## Post-Implementation

1. Monitor agent performance for first week
2. Collect feedback from deliverability team
3. Tune alert thresholds based on real data
4. Add custom alert rules if needed
5. Consider additional reputation providers
6. Plan Phase 2 enhancements (ML predictions, advanced analytics)
