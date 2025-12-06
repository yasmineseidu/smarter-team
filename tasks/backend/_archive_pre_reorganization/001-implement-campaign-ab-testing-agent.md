# Implement Campaign A/B Testing Agent

**Priority**: High
**Estimated Time**: 3-4 days
**Dependencies**: BaseAgent, InstantlyClient, Database models

## Task Overview
Implement the Campaign A/B Testing Agent according to the specification in `/specs/agents/campaign-ab-testing.md`. This agent will autonomously run statistical A/B tests on email campaigns to optimize performance.

## Implementation Checklist

### Phase 1: Database Setup (Day 1)
- [ ] Create SQLAlchemy models for:
  - `ABTestCampaign`
  - `ABTestVariant`
  - `ABTestResult`
  - `ABTestEvent`
- [ ] Write Alembic migration for all tables
- [ ] Add proper indexes for performance
- [ ] Create test fixtures for database models

### Phase 2: Agent Core Implementation (Day 1-2)
- [ ] Create `campaign_ab_testing/` directory structure
- [ ] Implement `CampaignABTestingAgent` class extending `BaseAgent`
- [ ] Add system prompt with statistical focus
- [ ] Implement core tools:
  - `create_ab_test`
  - `assign_leads_to_variants`
  - `track_campaign_metrics`
  - `calculate_statistical_significance`
  - `determine_winner`
  - `promote_winner`
  - `generate_test_report`

### Phase 3: Integration Components (Day 2)
- [ ] Extend `InstantlyClient` with A/B testing endpoints:
  - Campaign variant creation
  - Performance metrics retrieval
  - Lead assignment tracking
- [ ] Implement statistical analysis module using scipy:
  - Chi-square test implementation
  - Confidence interval calculation
  - Effect size calculation
  - Power analysis

### Phase 4: Error Handling & Edge Cases (Day 2-3)
- [ ] Implement comprehensive error handling:
  - Insufficient sample size scenarios
  - API failure retry logic
  - Inconclusive result handling
  - Statistical anomaly detection
- [ ] Add validation for test parameters
- [ ] Implement rate limiting for API calls

### Phase 5: Celery Tasks (Day 3)
- [ ] Create Celery tasks for async operations:
  - `run_ab_test_analysis`
  - `check_test_completion`
  - `promote_test_winner`
  - `generate_daily_report`
- [ ] Implement cron schedule configuration
- [ ] Add task monitoring and logging

### Phase 6: Testing (Day 3-4)
- [ ] Write unit tests for:
  - Statistical calculations
  - Agent tool functions
  - Database model operations
- [ ] Write integration tests for:
  - End-to-end test workflow
  - Instantly API integration
  - Celery task execution
- [ ] Add performance tests for large datasets
- [ ] Mock external dependencies properly

### Phase 7: Documentation & Final Polish (Day 4)
- [ ] Add comprehensive docstrings
- [ ] Create usage examples
- [ ] Update API documentation
- [ ] Add monitoring and alerting hooks
- [ ] Final code review and optimization

## Key Implementation Details

### Statistical Requirements
- Use `scipy.stats.chi2_contingency` for chi-square tests
- Implement 95% confidence level minimum
- Ensure minimum sample size of 100 per variant
- Calculate Cohen's h for effect size

### Database Patterns
- Follow existing SQLAlchemy 2.0 async patterns
- Use UUID primary keys following project conventions
- Implement proper foreign key relationships
- Add created_at/updated_at timestamps

### API Integration
- Extend existing `InstantlyClient` class
- Implement proper rate limiting
- Add comprehensive error handling
- Use async HTTP calls throughout

### Testing Strategy
- Use pytest with pytest-asyncio
- Mock Instantly API responses
- Test statistical calculations with known datasets
- Achieve >90% test coverage

## Success Criteria
1. All unit tests pass with >90% coverage
2. Integration tests with Instantly sandbox successful
3. Statistical calculations verified with known datasets
4. Error handling covers all edge cases
5. Performance acceptable for 100k+ lead lists
6. Documentation complete and accurate

## Files to Create/Modify

### New Files
```
app/backend/src/agents/campaign_ab_testing/
├── __init__.py
├── agent.py              # CampaignABTestingAgent class
├── tools.py              # Tool implementations
├── statistical.py        # Statistical analysis functions
├── schemas.py            # Pydantic models
├── exceptions.py         # Custom exceptions
└── prompts.py            # System and tool prompts

app/backend/src/database/models/ab_testing.py
├── ABTestCampaign
├── ABTestVariant
├── ABTestResult
└── ABTestEvent

app/backend/src/tasks/ab_testing_tasks.py
├── run_ab_test_analysis
├── check_test_completion
├── promote_test_winner
└── generate_daily_report

app/backend/__tests__/unit/agents/test_campaign_ab_testing.py
app/backend/__tests__/integration/test_ab_testing_workflow.py
app/backend/__tests__/fixtures/ab_testing_fixtures.py
```

### Modified Files
- `app/backend/src/integrations/instantly.py` - Add A/B testing methods
- `app/backend/src/celery_app.py` - Add new task schedule
- `app/backend/migrations/versions/` - Add new migration
- `app/backend/src/config.py` - Add A/B testing configuration

## Dependencies to Install
```bash
# Already in project:
# scipy - For statistical analysis
# sqlalchemy - Database ORM
# pytest - Testing framework

# Ensure these are installed:
pip install scipy>=1.13.0
```

## Environment Variables
```bash
# A/B Testing Configuration
AB_TEST_MIN_CONFIDENCE=0.95
AB_TEST_MIN_SAMPLE_SIZE=100
AB_TEST_MAX_DURATION_DAYS=30
AB_TEST_DEFAULT_TRAFFIC_SPLIT='{"A": 50, "B": 50}'
```

## Implementation Notes

1. **Statistical Rigor**: Always validate statistical assumptions before making decisions
2. **Performance**: Use database indexes and query optimization for large datasets
3. **Reliability**: Implement proper error recovery and retry mechanisms
4. **Audit Trail**: Log all test decisions for compliance and analysis
5. **Extensibility**: Design for future enhancement (multi-variant testing, Bayesian analysis)

## Review Checklist Before Completion
- [ ] Code follows project conventions (snake_case, type hints, async)
- [ ] All tests pass and coverage >90%
- [ ] Documentation is complete and accurate
- [ ] Error handling is comprehensive
- [ ] Performance is acceptable
- [ ] Security considerations addressed
- [ ] Database migrations tested
- [ ] API integration fully tested
- [ ] Monitoring and logging in place
