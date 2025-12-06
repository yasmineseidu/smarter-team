# A/B Testing Framework Agent Specification

## Overview
The A/B Testing Framework Agent autonomously tests and optimizes email campaign performance through statistical rigor and automated winner selection. This agent integrates with Instantly.ai for campaign execution and uses scipy for statistical analysis.

## Category
Campaign & Outreach

## Agent Classification
- **Type**: Analytics Agent
- **Autonomy Level**: Semi-autonomous (requires human approval for test setup)
- **Execution Pattern**: Scheduled + Event-driven

## System Capabilities

### Core Tools
1. **create_test_campaign** - Initialize A/B test with variants
2. **assign_leads_to_variants** - Randomly distribute leads across test groups
3. **track_campaign_metrics** - Collect performance data from Instantly API
4. **calculate_statistical_significance** - Perform chi-square tests
5. **determine_winner** - Select winning variant based on confidence thresholds
6. **promote_winner** - Deploy winning variant to full audience
7. **generate_test_report** - Create comprehensive analysis reports

### Integrations
- **Primary**: Instantly.ai API (campaign management and analytics)
- **Analytics**: scipy.stats (chi-square statistical testing)
- **Database**: Supabase PostgreSQL via SQLAlchemy 2.0
- **Memory**: Zep (for test context and historical decisions)
- **Task Queue**: Celery (for async test processing)

## Database Schema

### Tables

#### `ab_test_campaigns`
```sql
CREATE TABLE ab_test_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    hypothesis TEXT,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, running, completed, paused
    confidence_level DECIMAL(5,2) DEFAULT 0.95,
    minimum_sample_size INTEGER DEFAULT 100,
    traffic_split JSONB DEFAULT '{"A": 50, "B": 50}', -- Flexible N-way testing
    test_variables JSONB NOT NULL, -- ['subject_line', 'body_copy', 'send_time']
    start_at TIMESTAMP WITH TIME ZONE,
    end_at TIMESTAMP WITH TIME ZONE,
    winner_variant VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_ab_test_status ON ab_test_campaigns(status);
CREATE INDEX idx_ab_test_campaign_id ON ab_test_campaigns(campaign_id);
```

#### `ab_test_variants`
```sql
CREATE TABLE ab_test_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_campaign_id UUID NOT NULL REFERENCES ab_test_campaigns(id) ON DELETE CASCADE,
    variant_name VARCHAR(10) NOT NULL, -- A, B, C, etc.
    subject_line TEXT,
    body_copy TEXT,
    send_time TIME,
    personalization_approach JSONB,
    sequence_length INTEGER,
    instantly_campaign_id UUID, -- Links to Instantly campaign
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(test_campaign_id, variant_name)
);

CREATE INDEX idx_ab_variants_test_id ON ab_test_variants(test_campaign_id);
```

#### `ab_test_results`
```sql
CREATE TABLE ab_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_campaign_id UUID NOT NULL REFERENCES ab_test_campaigns(id) ON DELETE CASCADE,
    variant_name VARCHAR(10) NOT NULL,
    metric_date DATE NOT NULL,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    replied_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4), -- Primary KPI
    confidence_interval JSONB, -- Statistical confidence bounds
    p_value DECIMAL(10,8),
    is_statistically_significant BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(test_campaign_id, variant_name, metric_date)
);

CREATE INDEX idx_ab_results_test_variant ON ab_test_results(test_campaign_id, variant_name);
CREATE INDEX idx_ab_results_date ON ab_test_results(metric_date);
```

#### `ab_test_events`
```sql
CREATE TABLE ab_test_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_campaign_id UUID NOT NULL REFERENCES ab_test_campaigns(id),
    variant_name VARCHAR(10) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- test_started, winner_selected, test_paused
    event_data JSONB,
    triggered_by VARCHAR(50), -- system, user, agent
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ab_events_test_id ON ab_test_events(test_campaign_id);
```

## Agent Implementation

### Class Structure
```python
from src.agents.base_agent import BaseAgent
from src.integrations.instantly import InstantlyClient
from src.database.models import ABTestCampaign, ABTestVariant, ABTestResult
from scipy import stats
import numpy as np
from datetime import datetime, timedelta

class CampaignABTestingAgent(BaseAgent):
    """Autonomous A/B testing agent for email campaign optimization."""

    def __init__(self):
        super().__init__(
            name="campaign_ab_testing",
            description="Runs statistical A/B tests on email campaigns to optimize performance"
        )
        self.instantly = InstantlyClient()
        self.min_confidence = 0.95
        self.min_sample_size = 100
```

### System Prompt
```python
@property
def system_prompt(self) -> str:
    return """You are an expert A/B testing specialist focused on email campaign optimization.

Your core responsibilities:
1. Design statistically valid A/B tests with proper sample sizes
2. Execute tests through Instantly.ai API integration
3. Analyze results using chi-square statistical tests
4. Make data-driven decisions about variant performance
5. Maintain strict statistical rigor (95% confidence minimum)
6. Document all test decisions and outcomes

Key principles:
- Never promote a winner without statistical significance (p < 0.05)
- Ensure minimum sample size of 100 per variant before analysis
- Track multiple metrics: open rate, click rate, reply rate, conversion rate
- Consider statistical power and effect size in test design
- Handle inconclusive tests by extending duration or modifying variables
- Always maintain audit trail of test decisions

When analyzing results:
1. Check minimum sample size requirements
2. Perform chi-square test for categorical variables
3. Calculate confidence intervals for key metrics
4. Consider practical significance beyond statistical significance
5. Provide clear explanation of statistical findings"""
```

## Implementation Details

### 1. Test Creation Process
```python
async def create_ab_test(
    self,
    campaign_id: str,
    test_variables: list[str],
    variants: dict[str, dict],
    hypothesis: str | None = None,
    traffic_split: dict[str, float] | None = None,
    duration_days: int = 14
) -> dict[str, Any]:
    """
    Create a new A/B test campaign.

    Args:
        campaign_id: Base campaign to test
        test_variables: Variables being tested (e.g., ['subject_line', 'send_time'])
        variants: Variant definitions (A, B, C, etc.)
        hypothesis: Test hypothesis statement
        traffic_split: Traffic allocation per variant
        duration_days: Test duration in days

    Returns:
        Test campaign details with variant assignments
    """
```

### 2. Lead Assignment Algorithm
```python
async def assign_leads_to_variants(
    self,
    test_campaign_id: str,
    lead_list: list[str],
    assignment_method: str = "random_hash"
) -> dict[str, list[str]]:
    """
    Assign leads to test variants using consistent randomization.

    Methods:
    - random_hash: Hash-based assignment (consistent across runs)
    - round_robin: Sequential assignment
    - weighted_random: Probability-based assignment
    """
```

### 3. Statistical Analysis Engine
```python
async def analyze_test_results(
    self,
    test_campaign_id: str,
    metric: str = "conversion_rate"
) -> dict[str, Any]:
    """
    Perform statistical analysis on test results.

    Analysis includes:
    1. Chi-square test for categorical comparison
    2. Confidence interval calculation
    3. Effect size calculation (Cohen's h)
    4. Power analysis
    5. Recommendation for winner/no winner
    """
```

### 4. Winner Determination Logic
```python
async def determine_winner(
    self,
    test_campaign_id: str,
    require_significance: bool = True,
    min_improvement: float = 0.05  # 5% minimum improvement
) -> dict[str, Any]:
    """
    Determine winning variant based on statistical criteria.

    Criteria:
    1. Statistical significance (p < 0.05)
    2. Minimum sample size met
    3. Practical significance (minimum improvement threshold)
    4. No negative impact on secondary metrics
    """
```

## Error Handling & Edge Cases

### 1. Insufficient Sample Size
- Monitor daily sample accumulation
- Automatically extend test duration if sample size not met
- Alert human operator if extension exceeds maximum duration

### 2. Inconclusive Results
- Check for seasonal effects or external factors
- Suggest test modifications (different variables, larger sample)
- Consider multi-armed bandit approach for continuous optimization

### 3. API Failures
- Implement exponential backoff for Instantly API calls
- Cache results locally to reduce API dependency
- Fallback to manual data entry if API unavailable

### 4. Statistical Anomalies
- Detect and handle outliers in performance data
- Implement robust statistical methods (Welch's t-test for unequal variances)
- Validate data integrity before analysis

## Testing Strategy

### Unit Tests
- Test statistical calculations with known datasets
- Mock Instantly API responses for isolated testing
- Test edge cases (empty data, single variant, etc.)

### Integration Tests
- End-to-end test with Instantly sandbox API
- Database migration and model tests
- Celery task execution tests

### Performance Tests
- Load testing with large lead lists (>100,000)
- Concurrent test execution
- Database query optimization

## Security Considerations

1. **Data Privacy**: All lead data encrypted at rest
2. **API Security**: Rate limiting and retry logic for Instantly API
3. **Access Control**: Human approval required for test activation
4. **Audit Trail**: Complete logging of all test decisions

## Monitoring & Alerts

### Key Metrics
- Test duration and completion rate
- Statistical significance achievement rate
- Winner implementation success rate
- API error rates and response times

### Alert Conditions
- Test running longer than expected
- API failure rate > 5%
- Statistical anomalies detected
- Winner promotion failures

## Cron Schedule
```python
# Daily at 9:00 AM - Check for test completion
0 9 * * * check_test_completion

# Daily at 10:00 AM - Analyze results and determine winners
0 10 * * * analyze_test_results

# Daily at 11:00 AM - Promote winners (with human approval gating)
0 11 * * * promote_test_winners

# Weekly on Monday 9:30 AM - Generate weekly test summary
30 9 * * 1 generate_weekly_report
```

## Human-in-the-Loop Gates

### Gate 1: Test Setup Approval
- Review test hypothesis and variables
- Validate sample size calculations
- Approve traffic allocation
- Maximum 24-hour approval window

### Gate 2: Winner Promotion
- Review statistical analysis
- Consider business context beyond statistics
- Approve or reject winner promotion
- Option to extend test or modify parameters

## Dependencies
- **Campaign Creation Agent**: Provides campaigns to test
- **Copywriting Agent**: Generates test variants
- **Lead List Builder**: Provides test audience segments

## Success Metrics
1. **Test Velocity**: Number of completed tests per month
2. **Statistical Validity**: Percentage of tests reaching significance
3. **Improvement Rate**: Average performance uplift from winning variants
4. **Implementation Rate**: Percentage of winning variants implemented
5. **ROI Improvement**: Measurable revenue impact from optimizations

## Version History
- **v1.0**: Initial specification with chi-square testing
- **v1.1**: Added multi-variant support (A/B/n testing)
- **v1.2**: Enhanced statistical analysis with confidence intervals
- **v1.3**: Added Bayesian analysis option for faster decisions
