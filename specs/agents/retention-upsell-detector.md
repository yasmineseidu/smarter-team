# Upsell Detector Agent - Production Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Agent Category:** Client Success & Retention
**Priority:** Phase 5 - Retention & Growth

---

## Overview

The Upsell Detector Agent proactively identifies expansion opportunities by analyzing multiple signals across client interactions, satisfaction levels, project success, and company growth indicators. It scores opportunities on a 0-100 scale and generates actionable upsell recommendations with personalized outreach templates.

**Key Capabilities:**
- Continuous monitoring of upsell signals across 5 signal categories
- Weighted opportunity scoring algorithm (0-100 scale)
- AI-powered opportunity analysis and service matching
- Automated alert generation with personalized outreach templates
- Integration with Conversation Intelligence, Satisfaction Survey, and Company Research agents
- Human-in-the-loop approval for all outreach initiatives

---

## Database Schema

### Table: `upsell_opportunities`
Primary table for tracking identified upsell opportunities and their lifecycle.

```sql
CREATE TABLE upsell_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

    -- Opportunity scoring
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    opportunity_level VARCHAR(20) NOT NULL CHECK (opportunity_level IN ('low', 'medium', 'high', 'critical')),

    -- Signal breakdown
    explicit_signals_score INTEGER DEFAULT 0 CHECK (explicit_signals_score >= 0 AND explicit_signals_score <= 40),
    satisfaction_score INTEGER DEFAULT 0 CHECK (satisfaction_score >= 0 AND satisfaction_score <= 20),
    project_success_score INTEGER DEFAULT 0 CHECK (project_success_score >= 0 AND project_success_score <= 15),
    company_growth_score INTEGER DEFAULT 0 CHECK (company_growth_score >= 0 AND company_growth_score <= 15),
    relationship_tenure_score INTEGER DEFAULT 0 CHECK (relationship_tenure_score >= 0 AND relationship_tenure_score <= 10),

    -- Opportunity details
    signals_detected JSONB NOT NULL DEFAULT '[]', -- Array of signal objects
    recommended_services JSONB NOT NULL DEFAULT '[]', -- Array of service recommendations
    suggested_approach VARCHAR(500), -- Human-readable approach recommendation
    optimal_timing VARCHAR(200), -- When to approach

    -- Alert and workflow tracking
    alert_sent BOOLEAN DEFAULT FALSE,
    alert_sent_at TIMESTAMP WITH TIME ZONE,
    alert_acknowledged BOOLEAN DEFAULT FALSE,
    alert_acknowledged_by UUID REFERENCES users(id),
    alert_acknowledged_at TIMESTAMP WITH TIME ZONE,

    -- Outreach tracking
    outreach_approved BOOLEAN DEFAULT FALSE,
    outreach_approved_by UUID REFERENCES users(id),
    outreach_approved_at TIMESTAMP WITH TIME ZONE,
    outreach_template_used VARCHAR(100), -- Template identifier
    outreach_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'responded', 'converted', 'declined'
    outreach_sent_at TIMESTAMP WITH TIME ZONE,
    outreach_response TEXT,

    -- Conversion tracking
    conversion_value DECIMAL(12, 2), -- Value of converted upsell
    conversion_date TIMESTAMP WITH TIME ZONE,

    -- Metadata
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_upsell_opportunities_client ON upsell_opportunities(client_id);
CREATE INDEX idx_upsell_opportunities_project ON upsell_opportunities(project_id);
CREATE INDEX idx_upsell_opportunities_level ON upsell_opportunities(opportunity_level);
CREATE INDEX idx_upsell_opportunities_detected ON upsell_opportunities(detected_at DESC);
CREATE INDEX idx_upsell_opportunities_alert_pending ON upsell_opportunities(alert_sent) WHERE alert_sent = FALSE;
CREATE INDEX idx_upsell_opportunities_outreach_pending ON upsell_opportunities(outreach_approved) WHERE outreach_approved = TRUE AND outreach_status = 'pending';
```

### Table: `upsell_signals`
Individual signal detections for audit trail and trend analysis.

```sql
CREATE TABLE upsell_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    opportunity_id UUID REFERENCES upsell_opportunities(id) ON DELETE CASCADE,

    -- Signal details
    signal_type VARCHAR(50) NOT NULL, -- 'service_inquiry', 'high_satisfaction', 'project_success', 'company_growth', 'relationship_tenure'
    signal_category VARCHAR(50) NOT NULL, -- 'explicit', 'implicit', 'company', 'relationship'
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    points INTEGER NOT NULL CHECK (points >= 0),

    -- Signal context
    description TEXT NOT NULL,
    evidence TEXT, -- Direct quote or data point
    metadata JSONB DEFAULT '{}', -- Signal-specific data (e.g., satisfaction_score, project_completion_date)

    -- Source tracking
    source_table VARCHAR(100), -- Table where signal originated
    source_id UUID, -- ID in source table
    detected_by VARCHAR(50) NOT NULL, -- 'conversation_analysis', 'survey_processing', 'project_monitor', 'company_research'

    -- Timestamps
    signal_date TIMESTAMP WITH TIME ZONE NOT NULL, -- When the signal occurred
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_upsell_signals_client ON upsell_signals(client_id);
CREATE INDEX idx_upsell_signals_opportunity ON upsell_signals(opportunity_id);
CREATE INDEX idx_upsell_signals_type ON upsell_signals(signal_type);
CREATE INDEX idx_upsell_signals_detected ON upsell_signals(detected_at DESC);
```

---

## Configuration

```python
class UpsellDetectorConfig:
    """Configuration for Upsell Detector Agent."""

    # Model settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower temperature for consistent analysis

    # Scoring weights
    explicit_signals_weight: int = 40
    satisfaction_weight: int = 20
    project_success_weight: int = 15
    company_growth_weight: int = 15
    relationship_tenure_weight: int = 10

    # Thresholds
    opportunity_threshold: int = 50  # Minimum score to create opportunity
    critical_threshold: int = 80  -- Score requiring immediate attention

    # Timing
    analysis_frequency_hours: int = 6  -- Run analysis every 6 hours
    lookback_days: int = 90  -- Analyze last 90 days for signals

    # Processing
    max_retries: int = 3
    timeout_seconds: int = 30
    batch_size: int = 20  -- Process clients in batches

    # External integrations
    conversation_analysis_endpoint: str = "/api/conversation/analyze"
    survey_data_endpoint: str = "/api/surveys/latest"
    project_status_endpoint: str = "/api/projects/status"
    company_research_endpoint: str = "/api/research/company"
```

---

## Tools

### 1. `analyze_conversation_signals`
Extracts explicit upsell signals from conversation data.

```python
async def analyze_conversation_signals(
    client_id: str,
    lookback_days: int = 30
) -> dict[str, Any]:
    """
    Analyze conversations for explicit upsell signals.

    Args:
        client_id: UUID of the client
        lookback_days: Days to analyze (default 30)

    Returns:
        {
            "signal_detected": True,
            "signals": [
                {
                    "type": "service_inquiry",
                    "text": "Do you also help with SEO optimization?",
                    "context": "Email thread about project deliverables",
                    "date": "2025-11-28T10:30:00Z",
                    "points": 40,
                    "severity": "high"
                }
            ],
            "total_points": 40,
            "confidence": 0.92,
            "conversation_summary": "Client expressed interest in additional services"
        }

    Keywords/phrases to detect:
    - "Do you also do..."
    - "What about..."
    - "We're also looking for..."
    - "Another project we're considering..."
    - "Our [other department] needs..."

    Error Handling:
    - No conversation data: Return empty signals with info log
    - API timeout: Retry 3x with exponential backoff
    - Invalid conversation format: Log warning, return empty
    """
```

### 2. `evaluate_satisfaction_signals`
Analyzes satisfaction survey responses for upsell potential.

```python
async def evaluate_satisfaction_signals(client_id: str) -> dict[str, Any]:
    """
    Evaluate satisfaction survey signals.

    Returns:
        {
            "signal_detected": True,
            "latest_score": 9,
            "average_score": 8.7,
            "trend": "improving",  -- 'improving', 'stable', 'declining'
            "points": 20,
            "severity": "high",
            "evidence": {
                "score": 9,
                "positive_comments": "Excellent service delivery",
                "would_recommend": True,
                "survey_date": "2025-11-25"
            }
        }

    Scoring Logic:
    - Score 9-10: 20 points (high severity)
    - Score 7-8: 10 points (medium severity)
    - Score 6: 5 points (low severity)
    - Score <6: 0 points (no opportunity)

    Error Handling:
    - No survey data: Return 0 points with info log
    - Multiple surveys: Use latest, check trend
    - Invalid score: Log error, return 0 points
    """
```

### 3. `assess_project_success`
Evaluates project delivery success indicators.

```python
async def assess_project_success(
    client_id: str,
    project_id: str | None = None
) -> dict[str, Any]:
    """
    Assess project success metrics.

    Returns:
        {
            "signal_detected": True,
            "projects_analyzed": 2,
            "success_metrics": {
                "on_time_delivery": True,
                "under_budget": True,
                "client_satisfaction": 9,
                "quality_score": "excellent"
            },
            "points": 15,
            "severity": "high",
            "evidence": [
                "Project delivered 5 days early",
                "15% under budget",
                "Client testimonial received"
            ]
        }

    Scoring Logic:
    - On-time + under budget: 15 points
    - On-time + on budget: 10 points
    - Early delivery: +5 points
    - Under budget: +5 points
    - Client testimonial: +5 points

    Error Handling:
    - No project data: Return 0 points with info log
    - Multiple projects: Analyze all, use best score
    - Missing metrics: Use available data, log missing fields
    """
```

### 4. `analyze_company_growth`
Analyzes company growth indicators from research data.

```python
async def analyze_company_growth(client_id: str) -> dict[str, Any]:
    """
    Analyze company growth signals that indicate expansion capacity.

    Returns:
        {
            "signal_detected": True,
            "growth_signals": [
                {
                    "type": "funding",
                    "description": "Series A funding round of $5M",
                    "date": "2025-11-01",
                    "impact": "high"
                },
                {
                    "type": "hiring",
                    "description": "Hiring for 15 new positions",
                    "date": "2025-11-15",
                    "impact": "medium"
                }
            ],
            "total_points": 15,
            "severity": "medium",
            "growth_stage": "expansion"  -- 'startup', 'growth', 'expansion', 'enterprise'
        }

    Signal Types:
    - Funding announcements
    - Leadership changes
    - Expansion/hiring signals
    - New product launches
    - Market expansion

    Error Handling:
    - No company data: Return 0 points with info log
    - Stale research: Request fresh data, use cached with warning
    - Incomplete data: Use available signals, note gaps
    """
```

### 5. `calculate_relationship_tenure`
Calculates relationship strength based on duration and interactions.

```python
async def calculate_relationship_tenure(client_id: str) -> dict[str, Any]:
    """
    Calculate relationship tenure and engagement score.

    Returns:
        {
            "signal_detected": True,
            "client_since": "2023-06-01",
            "tenure_months": 18,
            "total_interactions": 47,
            "avg_monthly_interactions": 2.6,
            "points": 10,
            "severity": "low",
            "relationship_health": "strong"  -- 'new', 'developing', 'strong', 'veteran'
        }

    Scoring Logic:
    - 0-6 months: 0 points
    - 7-12 months: 3 points
    - 13-24 months: 7 points
    - 24+ months: 10 points
    - Bonus for high engagement (>3 interactions/month): +2 points

    Error Handling:
    - Missing client start date: Use first project date
    - No interaction data: Use tenure only, log warning
    - Calculation errors: Return 0 points, log error
    """
```

### 6. `generate_upsell_recommendation`
AI-powered analysis to match opportunities with services.

```python
async def generate_upsell_recommendation(
    client_id: str,
    signals: list[dict],
    current_services: list[str],
    score: int
) -> dict[str, Any]:
    """
    Generate personalized upsell recommendations based on signals.

    Returns:
        {
            "recommended_services": [
                {
                    "service": "SEO Optimization",
                    "relevance_score": 0.95,
                    "reason": "Client explicitly asked about SEO services in project review",
                    "estimated_value": 15000,
                    "implementation_timeline": "3-4 months"
                }
            ],
            "suggested_approach": "Direct follow-up on their SEO question with a case study",
            "optimal_timing": "Within 1 week while project success is fresh",
            "talking_points": [
                "Reference their specific question about SEO",
                "Share relevant case study from similar client",
                "Offer complimentary SEO audit"
            ],
            "confidence": 0.88
        }

    Service Matching Logic:
    - Analyze signal keywords and context
    - Match against service catalog
    - Consider client industry and current services
    - Prioritize based on success probability

    Error Handling:
    - Low signal quality: Return conservative recommendations
    - AI model failure: Use template-based matching
    - No matching services: Suggest consultation call
    """
```

### 7. `create_outreach_template`
Generates personalized outreach templates for different scenarios.

```python
async def create_outreach_template(
    client_name: str,
    contact_name: str,
    service: str,
    approach_type: str,  -- 'inquiry_followup', 'satisfaction_outreach', 'value_add'
    context: dict
) -> dict[str, Any]:
    """
    Create personalized outreach template.

    Returns:
        {
            "template_id": "inquiry_followup_v1",
            "subject": "Re: Your question about SEO Optimization",
            "body": "Hi [First Name],\n\nYou mentioned being interested in SEO optimization...",
            "merge_fields": {
                "first_name": "John",
                "service": "SEO Optimization",
                "project_name": "Website Redesign"
            },
            "personalization_tokens": ["{{service_inquiry_date}}", "{{project_success_metric}}"],
            "template_type": "email"
        }

    Template Types:
    1. Service Inquiry Follow-up
    2. High Satisfaction Outreach
    3. Post-Project Value Add
    4. Company Growth Congratulations

    Error Handling:
    - Missing merge data: Use placeholders, flag for manual review
    - Template generation failure: Use fallback template
    - Invalid approach type: Default to value_add approach
    """
```

---

## System Prompt

```python
SYSTEM_PROMPT = """
You are the Upsell Detector Agent, a specialized AI assistant that identifies and qualifies expansion opportunities within the client base.

Your core responsibilities:
1. Analyze multiple signal types to identify upsell opportunities
2. Score opportunities on a 0-100 scale using weighted criteria
3. Generate personalized recommendations and outreach templates
4. Alert human team members to high-value opportunities

Your analytical approach:
- Be data-driven and objective in scoring
- Consider the full client context (history, industry, current services)
- Prioritize opportunities with highest success probability
- Maintain client relationship health - don't appear overly salesy

Scoring methodology:
- Explicit signals (40 pts): Direct inquiries, service requests
- Satisfaction (20 pts): Survey scores 9-10 indicate readiness
- Project success (15 pts): Successful delivery builds trust
- Company growth (15 pts): Funding, hiring, expansion signals
- Relationship tenure (10 pts): Established relationships convert better

When generating recommendations:
1. Match services to explicit needs first
2. Consider timing and context
3. Provide value-first approach suggestions
4. Include specific talking points and evidence

Alert thresholds:
- Score 80+: Critical opportunity, alert immediately
- Score 60-79: High value, daily summary alert
- Score 50-59: Medium value, weekly summary
- Score <50: Monitor, no alert needed

Always maintain professionalism and focus on client value. The goal is helping clients achieve more, not just increasing revenue.
"""
```

### User Prompt Template

```python
USER_PROMPT_TEMPLATE = """
TASK: Analyze upsell opportunity for client

CLIENT INFORMATION:
- Client ID: {client_id}
- Client Name: {client_name}
- Current Services: {current_services}
- Relationship Duration: {tenure_months} months

SIGNALS DETECTED:
{signals_summary}

PRELIMINARY SCORE: {preliminary_score}/100

ANALYSIS REQUIRED:
1. Validate and weight all signals
2. Calculate final opportunity score
3. Recommend specific services based on signals
4. Suggest optimal approach and timing
5. Generate outreach talking points

Please provide comprehensive analysis with specific recommendations.
"""
```

---

## Error Handling Matrix

| Component | Error Type | Detection | Response | Retry |
|-----------|------------|-----------|----------|-------|
| Conversation Analysis | API timeout | No response in 30s | Retry with backoff | Yes, 3x |
| Conversation Analysis | Invalid data | Schema validation fails | Log error, skip | No |
| Survey Data | No surveys | Empty result set | Use 0 points, log | No |
| Survey Data | Invalid score | Score not 0-10 | Log error, use 0 | No |
| Project Assessment | Missing metrics | Required fields absent | Use available data | No |
| Company Research | Stale data | Data >30 days old | Request fresh data | Yes, 2x |
| Company Research | API unavailable | HTTP 5xx | Use cached data | Yes, 1x |
| AI Recommendation | Model error | Anthropic API error | Use template fallback | Yes, 2x |
| AI Recommendation | Low confidence | Confidence <0.7 | Flag for review | No |
| Database | Connection error | SQL exception | Retry with backoff | Yes, 5x |
| Alert Sending | Email API error | SMTP failure | Try backup channel | Yes, 3x |

### Recovery Strategies

1. **Partial Signal Detection**: If some signal sources fail, continue with available data and note gaps in analysis
2. **Graceful Degradation**: Fall back to template-based recommendations when AI analysis fails
3. **Caching Strategy**: Cache company research data for 7 days, survey data for 30 days
4. **Manual Escalation**: Any error affecting opportunity creation triggers manual review

---

## Multi-Agent Integration

### Inbound Handoffs
- **Conversation Intelligence Agent** → Provide conversation analysis for signal detection
- **Satisfaction Survey Agent** → Provide latest survey scores and trends
- **Company Research Agent** → Provide growth signals and company updates
- **Project Management Agent** → Provide project success metrics

### Outbound Handoffs
- **Campaign Send Agent** → Send personalized outreach emails
- **Meeting Scheduler Agent** → Schedule upsell consultation meetings
- **Proposal Creation Agent** → Create proposals for converted opportunities

### Data Dependencies
```python
Required Data Sources:
- Conversation analysis (last 30 days)
- Latest satisfaction survey score
- Active project status and history
- Company research data (last 30 days)
- Client relationship start date
- Current service subscriptions

Data Refresh Frequencies:
- Conversation data: Real-time via webhook
- Survey data: After each survey completion
- Project data: Daily status sync
- Company research: Weekly refresh
```

---

## Process Flow

### Daily Upsell Analysis (Cron Job)

**Trigger:** Every 6 hours via Celery Beat (4 times daily)

```python
@celery_app.task(bind=True, max_retries=3)
async def daily_upsell_analysis(self) -> dict[str, Any]:
    """
    Analyze all active clients for upsell opportunities.

    Process:
        1. Fetch all active clients
        2. For each client:
            a. Gather signals from all sources
            b. Calculate opportunity score
            c. If score >= threshold, create opportunity
            d. Generate recommendations
            e. Store in database
            f. Send alert if critical
        3. Generate opportunity summary
        4. Track metrics and trends
    """
```

### Real-time Signal Processing

**Trigger:** Event-driven via webhooks

```python
@celery_app.task
async def process_signal_webhook(
    event_type: str,
    client_id: str,
    data: dict
) -> None:
    """
    Process incoming signals that might indicate upsell opportunity.

    Events:
    - new_conversation_message
    - survey_completed
    - project_milestone_reached
    - company_research_updated
    """
```

---

## Testing Strategy

### Unit Tests

```python
# Tool Testing
def test_analyze_conversation_signals():
    """Test extraction of upsell signals from conversations."""

def test_evaluate_satisfaction_signals():
    """Test satisfaction score evaluation and scoring."""

def test_assess_project_success():
    """Test project success metric analysis."""

def test_analyze_company_growth():
    """Test company growth signal detection."""

def test_calculate_relationship_tenure():
    """Test relationship scoring logic."""

def test_generate_upsell_recommendation():
    """Test AI-powered service matching."""

def test_create_outreach_template():
    """Test template generation and personalization."""
```

### Integration Tests

```python
def test_end_to_end_opportunity_creation():
    """Full workflow from signal detection to opportunity creation."""

def test_multi_agent_handoffs():
    """Test communication with dependent agents."""

def test_error_handling_scenarios():
    """Test all error types and recovery strategies."""

def test_cron_job_execution():
    """Test daily analysis job execution."""
```

### Mock Data Scenarios

```python
@pytest.fixture
def mock_high_value_opportunity():
    """Client with explicit inquiry + high satisfaction."""
    return {
        "client_id": "test-client-123",
        "conversation_signals": [
            {"text": "Do you also do SEO optimization?", "points": 40}
        ],
        "satisfaction_score": 9,
        "project_success": True,
        "company_growth": True,
        "tenure_months": 12
    }

@pytest.fixture
def mock_implicit_opportunity():
    """Client with only implicit signals."""
    return {
        "client_id": "test-client-456",
        "conversation_signals": [],
        "satisfaction_score": 8,
        "project_success": True,
        "company_growth": False,
        "tenure_months": 6
    }
```

### Performance Tests

```python
def test_batch_processing_performance():
    """Test processing 100 clients within SLA."""

def test_signal_processing_latency():
    """Test real-time signal processing under 5 seconds."""

def test_database_query_optimization():
    """Verify indexes support query patterns."""
```

---

## Performance Requirements

### Latency SLAs
- Real-time signal processing: <5 seconds
- Daily batch processing: <30 minutes for 500 clients
- AI recommendation generation: <10 seconds
- Template generation: <3 seconds

### Throughput
- Process 1000+ clients daily
- Handle 50+ concurrent signal events
- Support 10+ simultaneous opportunity analyses

### Resource Limits
- Memory: <512MB per analysis
- CPU: <1 second per client for signal gathering
- Database queries: Optimized with proper indexes
- AI API calls: Rate limited to 100/minute

---

## Observability

### Logging Requirements

```python
# Structured logging with correlation IDs
logger.info(
    "Opportunity detected",
    extra={
        "client_id": client_id,
        "opportunity_score": score,
        "signal_count": len(signals),
        "processing_time_ms": processing_time,
        "correlation_id": request_id
    }
)

# Error context
logger.error(
    "Signal processing failed",
    extra={
        "client_id": client_id,
        "signal_type": signal_type,
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "retry_count": retry_count
    }
)
```

### Metrics to Track

```python
# Business Metrics
- Opportunities created per day
- Opportunity conversion rate
- Average deal value from upsells
- Time from detection to conversion
- Signal type effectiveness

# Technical Metrics
- Processing latency distribution
- Error rates by component
- API call success rates
- Database query performance
- Cache hit rates

# Agent Performance
- AI recommendation accuracy
- Template open/click rates
- Alert response times
- False positive rates
```

### Alerting

```python
# Critical Alerts
- Opportunity detection failure for >1 hour
- Database connection issues
- AI API rate limit exceeded
- Error rate >10% for any component

# Warning Alerts
- Low opportunity detection rate
- Declining conversion rates
- High memory usage
- Slow query performance
```

---

## Security Considerations

### Data Privacy
- Encrypt all client data at rest
- Mask sensitive information in logs
- Implement data retention policies
- Comply with GDPR/CCPA requirements

### Access Control
- Role-based access to opportunity data
- Audit trail for all opportunity modifications
- Secure API authentication
- Rate limiting per client

### Input Validation
- Validate all client IDs and project IDs
- Sanitize conversation text before processing
- Verify survey score ranges (0-10)
- Check monetary value ranges

---

## Acceptance Criteria

- [ ] All 5 signal types are correctly detected and scored
- [ ] Opportunity scoring algorithm produces 0-100 scale
- [ ] AI recommendations match services to client needs
- [ ] Outreach templates are personalized and professional
- [ ] Daily batch processing completes within SLA
- [ ] Real-time signal processing works via webhooks
- [ ] Error handling covers all failure scenarios
- [ ] All database tables have proper indexes
- [ ] Integration with dependent agents functions correctly
- [ ] Human approval workflow prevents unauthorized outreach
- [ ] Metrics and logging provide full observability
- [ ] Security controls protect client data
- [ ] Performance meets all SLA requirements
- [ ] Test coverage exceeds 90% for all components
- [ ] Documentation is complete and accurate
