# Satisfaction Survey Agent - Production Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Agent Category:** Client Success & Retention
**Priority:** Phase 5 - Retention & Growth

---

## Overview

The Satisfaction Survey Agent automates client feedback collection throughout the project lifecycle to monitor satisfaction, identify issues early, and gather testimonials. It manages survey creation, distribution, response collection, sentiment analysis, and alert generation for negative feedback.

**Key Capabilities:**
- Automated survey delivery at 4 key project milestones
- Support for Typeform and Google Forms integrations
- Real-time sentiment analysis of open-text feedback
- NPS scoring and trend tracking
- Immediate alerts for negative feedback (score ≤6)
- Testimonial request automation for promoters (score ≥9)
- Comprehensive reporting and analytics dashboard

---

## Database Schema

### Table: `satisfaction_surveys`
Primary table for survey configuration and tracking.

```sql
CREATE TABLE satisfaction_surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

    -- Survey details
    survey_type VARCHAR(50) NOT NULL, -- 'week1_onboarding', 'mid_project', 'completion', '30_day_followup'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    external_id VARCHAR(255), -- Typeform/Google Forms ID
    external_url VARCHAR(500), -- Public survey URL

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'draft', -- 'draft', 'active', 'closed', 'archived'
    sent_at TIMESTAMP WITH TIME ZONE,
    reminder_sent_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,

    -- Configuration
    provider VARCHAR(20) NOT NULL, -- 'typeform', 'google_forms', 'internal'
    template_version VARCHAR(10) DEFAULT '1.0',
    custom_questions JSONB DEFAULT '[]', -- Override questions

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_surveys_client ON satisfaction_surveys(client_id);
CREATE INDEX idx_surveys_project ON satisfaction_surveys(project_id);
CREATE INDEX idx_surveys_type ON satisfaction_surveys(survey_type);
CREATE INDEX idx_surveys_status ON satisfaction_surveys(status);
CREATE INDEX idx_surveys_sent ON satisfaction_surveys(sent_at);
```

### Table: `survey_responses`
Stores individual survey responses and links to client/project context.

```sql
CREATE TABLE survey_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID NOT NULL REFERENCES satisfaction_surveys(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

    -- Response tracking
    external_response_id VARCHAR(255), -- Provider's response ID
    respondent_email VARCHAR(255),
    respondent_name VARCHAR(255),

    -- Response data
    response_data JSONB NOT NULL, -- Full response from provider
    nps_score INTEGER CHECK (nps_score >= 0 AND nps_score <= 10),
    satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 10),

    -- Open text responses
    feedback_text TEXT,
    concerns_text TEXT,
    suggestions_text TEXT,
    testimonial_text TEXT,

    -- Analysis results
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
    sentiment_label VARCHAR(20), -- 'positive', 'neutral', 'negative'
    sentiment_confidence DECIMAL(3,2), -- 0.0 to 1.0
    key_topics JSONB DEFAULT '[]', -- Extracted topics/themes

    -- Categorization
    response_category VARCHAR(20), -- 'promoter', 'passive', 'detractor'
    urgency_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'

    -- Processing
    processed_at TIMESTAMP WITH TIME ZONE,
    analysis_version VARCHAR(10) DEFAULT '1.0',

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_responses_survey ON survey_responses(survey_id);
CREATE INDEX idx_responses_client ON survey_responses(client_id);
CREATE INDEX idx_responses_nps ON survey_responses(nps_score);
CREATE INDEX idx_responses_sentiment ON survey_responses(sentiment_label);
CREATE INDEX idx_responses_category ON survey_responses(response_category);
CREATE INDEX idx_responses_completed ON survey_responses(completed_at DESC);
```

### Table: `satisfaction_scores`
Aggregated satisfaction metrics for trend analysis.

```sql
CREATE TABLE satisfaction_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

    -- Aggregated metrics
    avg_satisfaction_score DECIMAL(4,2),
    avg_nps_score DECIMAL(4,2),
    total_responses INTEGER DEFAULT 0,
    promoter_count INTEGER DEFAULT 0,
    passive_count INTEGER DEFAULT 0,
    detractor_count INTEGER DEFAULT 0,

    -- Calculations
    nps_percentage INTEGER, -- Net Promoter Score % (-100 to 100)
    satisfaction_trend VARCHAR(20), -- 'improving', 'stable', 'declining'
    sentiment_distribution JSONB, -- {"positive": 60, "neutral": 25, "negative": 15}

    -- Context
    survey_type VARCHAR(50),
    calculation_period VARCHAR(20), -- 'week', 'month', 'quarter', 'year'
    period_start DATE,
    period_end DATE,

    -- Metadata
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    UNIQUE(client_id, project_id, survey_type, period_start, period_end)
);

-- Indexes
CREATE INDEX idx_scores_client ON satisfaction_scores(client_id);
CREATE INDEX idx_scores_project ON satisfaction_scores(project_id);
CREATE INDEX idx_scores_period ON satisfaction_scores(period_start, period_end);
CREATE INDEX idx_scores_nps ON satisfaction_scores(nps_percentage);
```

### Table: `survey_alerts`
Tracks alerts generated from survey responses.

```sql
CREATE TABLE survey_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL REFERENCES survey_responses(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Alert details
    alert_type VARCHAR(50) NOT NULL, -- 'negative_feedback', 'low_nps', 'urgent_issue'
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    -- Distribution
    channels_sent JSONB DEFAULT '[]', -- ["email", "slack", "sms"]
    recipients JSONB DEFAULT '[]', -- [{"email": "...", "name": "...", "type": "owner"}]

    -- Status
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,

    -- Follow-up
    follow_up_required BOOLEAN DEFAULT TRUE,
    follow_up_assigned_to UUID REFERENCES users(id),
    follow_up_completed BOOLEAN DEFAULT FALSE,
    follow_up_notes TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_alerts_response ON survey_alerts(response_id);
CREATE INDEX idx_alerts_client ON survey_alerts(client_id);
CREATE INDEX idx_alerts_severity ON survey_alerts(severity);
CREATE INDEX idx_alerts_unacknowledged ON survey_alerts(acknowledged) WHERE acknowledged = FALSE;
```

---

## Agent Implementation

### System Prompt

```python
SYSTEM_PROMPT = """You are the Satisfaction Survey Agent for Smarter Team, an AI agency automation system.

Your primary responsibility is to monitor client satisfaction throughout the project lifecycle by collecting, analyzing, and acting on client feedback at critical milestones.

CORE RESPONSIBILITIES:
1. Create and send surveys at 4 key project milestones
2. Analyze responses using sentiment analysis and NPS scoring
3. Generate immediate alerts for negative feedback
4. Request testimonials from satisfied clients
5. Track satisfaction trends over time
6. Coordinate with other agents for follow-up actions

SURVEY MILESTONES:
- Week 1 Onboarding: Check initial client experience
- Mid-Project: Assess progress and alignment
- Project Completion: Evaluate overall delivery
- 30-Day Follow-Up: Measure deliverable performance

SCORING SYSTEM:
- NPS Score (0-10): 9-10 = Promoter, 7-8 = Passive, 0-6 = Detractor
- Satisfaction Score (1-10): 8-10 = High, 6-7 = Medium, 1-5 = Low
- Sentiment Analysis: -1.0 (very negative) to 1.0 (very positive)

ALERT THRESHOLDS:
- Satisfaction ≤ 6: Immediate alert to owner
- NPS ≤ 6: Create follow-up task
- Sentiment ≤ -0.3: High priority alert
- Multiple negative responses: Escalate to management

INTEGRATION POINTS:
- Typeform/Google Forms for survey delivery
- Slack/Email for alert notifications
- Churn Risk Agent for negative feedback correlation
- Testimonial Request Agent for promoter follow-up
- Project Management Agent for milestone tracking

PROCESSING RULES:
- Send survey within 24 hours of milestone trigger
- Send one reminder after 3 days if no response
- Analyze responses within 1 hour of submission
- Send alerts immediately for negative feedback
- Request testimonials within 48 hours for promoters

DATA PRIVACY:
- Store all survey responses securely
- Anonymous feedback option available
- Comply with data protection regulations
- Obtain consent for testimonial usage

Always maintain a professional, empathetic tone. Your goal is to improve client satisfaction through proactive feedback collection and rapid response to concerns.
"""
```

### Tool Definitions

#### 1. `create_survey`
Creates a new survey based on template and milestone.

```python
async def create_survey(
    client_id: str,
    project_id: str | None = None,
    survey_type: str,  # 'week1_onboarding', 'mid_project', 'completion', '30_day_followup'
    provider: str = "typeform",  # 'typeform', 'google_forms'
    custom_questions: list[dict] | None = None,
    scheduled_send_at: str | None = None
) -> dict[str, Any]:
    """
    Create a satisfaction survey for a client milestone.

    Args:
        client_id: UUID of the client
        project_id: Optional UUID of specific project
        survey_type: Type of survey milestone
        provider: Survey provider (typeform or google_forms)
        custom_questions: Optional custom question overrides
        scheduled_send_at: Optional ISO datetime to send survey

    Returns:
        {
            "survey_id": "uuid...",
            "external_id": "form_id_123",
            "external_url": "https://form.typeform.com/...",
            "status": "draft",
            "questions": [
                {
                    "id": "q1",
                    "type": "rating",
                    "title": "How satisfied are you with...",
                    "required": True,
                    "scale": 10
                },
                ...
            ],
            "scheduled_send_at": "2025-12-06T10:00:00Z",
            "estimated_completion_time": "2 minutes"
        }

    Implementation:
        1. Validate client/project exists and milestone reached
        2. Select survey template based on survey_type
        3. Apply custom questions if provided
        4. Create survey in provider API
        5. Store survey configuration in database
        6. Schedule survey send if specified
        7. Return survey details and URL
    """
```

#### 2. `send_survey_invitation`
Sends survey invitation to client via email.

```python
async def send_survey_invitation(
    survey_id: str,
    recipient_email: str,
    recipient_name: str,
    custom_message: str | None = None
) -> dict[str, Any]:
    """
    Send survey invitation email to client.

    Args:
        survey_id: UUID of survey to send
        recipient_email: Client's email address
        recipient_name: Client's first name
        custom_message: Optional custom message

    Returns:
        {
            "sent": True,
            "sent_at": "2025-12-05T10:30:00Z",
            "email_id": "msg_123",
            "survey_url": "https://form.typeform.com/...",
            "estimated_completion_time": "2 minutes",
            "reminder_scheduled": True
        }

    Email Template:
        Subject: {{survey_type.subject}}

        Body:
            Hi {{first_name}},

            {{survey_type.intro_message}}

            Survey link: {{survey_url}}

            {{survey_type.closing_message}}

            This takes just 2 minutes to complete.
    """
```

#### 3. `analyze_survey_response`
Performs sentiment analysis and categorization.

```python
async def analyze_survey_response(
    response_id: str,
    response_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Analyze survey response for sentiment and categorization.

    Args:
        response_id: UUID of survey response
        response_data: Raw response data from provider

    Returns:
        {
            "nps_score": 9,
            "satisfaction_score": 8,
            "response_category": "promoter",
            "sentiment_analysis": {
                "overall_sentiment": 0.75,
                "sentiment_label": "positive",
                "confidence": 0.92,
                "emotions": ["satisfied", "impressed"]
            },
            "key_topics": [
                {
                    "topic": "communication",
                    "sentiment": "positive",
                    "quotes": ["Great communication throughout"]
                },
                {
                    "topic": "timeline",
                    "sentiment": "neutral",
                    "quotes": ["Project met deadlines"]
                }
            ],
            "urgency_level": "low",
            "alerts_triggered": []
        }

    Analysis Logic:
        1. Extract NPS and satisfaction scores
        2. Analyze open-text responses for sentiment
        3. Identify key topics and themes
        4. Categorize as promoter/passive/detractor
        5. Determine urgency level
        6. Flag for alerts if needed
    """
```

#### 4. `generate_satisfaction_alert`
Creates and sends alerts for negative feedback.

```python
async def generate_satisfaction_alert(
    response_id: str,
    alert_type: str,
    severity: str,
    channels: list[str] = ["slack", "email"]
) -> dict[str, Any]:
    """
    Generate and send satisfaction alert.

    Args:
        response_id: UUID of survey response
        alert_type: Type of alert ('negative_feedback', 'low_nps', 'urgent_issue')
        severity: Alert severity ('low', 'medium', 'high', 'critical')
        channels: Alert channels to use

    Returns:
        {
            "alert_id": "uuid...",
            "sent": True,
            "channels_used": ["slack", "email"],
            "sent_at": "2025-12-05T10:35:00Z",
            "recipients_notified": 3,
            "follow_up_task_created": True,
            "task_id": "task_123"
        }

    Alert Format:
        🚨 SATISFACTION ALERT - {{severity.upper()}}

        Client: {{client_name}}
        Project: {{project_name}}
        Survey: {{survey_type}}

        ISSUE:
        {{alert_summary}}

        DETAILS:
        - NPS Score: {{nps}}/10
        - Satisfaction: {{satisfaction}}/10
        - Key Concern: {{extracted_concern}}

        RECOMMENDED ACTION:
        {{recommended_action}}

        [View Full Response] [Acknowledge Alert]
    """
```

#### 5. `request_testimonial`
Requests testimonial from promoters.

```python
async def request_testimonial(
    response_id: str,
    custom_message: str | None = None
) -> dict[str, Any]:
    """
    Request testimonial from satisfied client.

    Args:
        response_id: UUID of positive survey response
        custom_message: Optional personalized message

    Returns:
        {
            "request_sent": True,
            "sent_at": "2025-12-05T11:00:00Z",
            "email_id": "msg_456",
            "testimonials_collected": 0,
            "follow_up_scheduled": "2025-12-12T10:00:00Z"
        }

    Email Template:
        Subject: You made our day! 🎉

        Hi {{first_name}},

        Thank you for your amazing feedback! We're thrilled you had a great experience.

        Would you be willing to share a brief testimonial? It would help other companies like yours.

        {{testimonial_link}}

        As a thank you, we'd love to offer you {{incentive}}.

        Warmly,
        The Smarter Team
    """
```

#### 6. `calculate_satisfaction_trends`
Calculates satisfaction metrics over time.

```python
async def calculate_satisfaction_trends(
    client_id: str,
    project_id: str | None = None,
    period_days: int = 90
) -> dict[str, Any]:
    """
    Calculate satisfaction trends for a client.

    Args:
        client_id: UUID of the client
        project_id: Optional UUID of specific project
        period_days: Number of days to analyze

    Returns:
        {
            "period_analyzed": "2025-09-06 to 2025-12-05",
            "total_responses": 12,
            "avg_satisfaction_score": 8.2,
            "avg_nps_score": 72,
            "nps_distribution": {
                "promoters": 67,
                "passives": 25,
                "detractors": 8
            },
            "trend_analysis": {
                "satisfaction_trend": "improving",
                "nps_trend": "stable",
                "response_rate_trend": "increasing"
            },
            "milestone_comparison": [
                {
                    "milestone": "week1_onboarding",
                    "avg_score": 8.5,
                    "response_count": 3
                },
                {
                    "milestone": "mid_project",
                    "avg_score": 7.8,
                    "response_count": 4
                }
            ],
            "key_insights": [
                "Consistently high satisfaction with communication",
                "Improvement needed in project timeline management",
                "Strong likelihood of renewal"
            ]
        }
    """
```

#### 7. `sync_survey_responses`
Syncs responses from provider APIs.

```python
async def sync_survey_responses(
    survey_id: str,
    provider: str,
    last_sync_at: str | None = None
) -> dict[str, Any]:
    """
    Sync survey responses from provider API.

    Args:
        survey_id: UUID of survey
        provider: Survey provider name
        last_sync_at: Optional timestamp for incremental sync

    Returns:
        {
            "responses_found": 5,
            "responses_synced": 3,
            "responses_updated": 2,
            "sync_at": "2025-12-05T10:00:00Z",
            "errors": []
        }

    Implementation:
        1. Query provider API for new/updated responses
        2. Upsert responses to database
        3. Trigger analysis for new responses
        4. Update survey statistics
        5. Handle API rate limits and errors
        6. Return sync summary
    """
```

---

## Process Flow

### Automated Survey Workflow

#### 1. Milestone Detection (Daily Cron)
**Trigger:** Daily at 9:00 AM via Celery Beat

```python
@celery_app.task(bind=True, max_retries=3)
async def check_survey_milestones() -> dict[str, Any]:
    """
    Check for clients reaching survey milestones.

    Process:
        1. Query projects for milestone dates
        2. Check if survey already created/sent
        3. Create surveys for newly reached milestones
        4. Schedule survey sends
        5. Log milestone detections

    Returns:
        {
            "clients_checked": 45,
            "milestones_reached": 8,
            "surveys_created": 6,
            "surveys_scheduled": 6,
            "errors": []
        }
    """
```

#### 2. Survey Delivery (Scheduled)
**Trigger:** Scheduled send time or immediately for new milestones

```python
@celery_app.task(bind=True, max_retries=3)
async def send_scheduled_surveys() -> dict[str, Any]:
    """
    Send surveys scheduled for delivery.

    Process:
        1. Fetch surveys with send_date <= now
        2. Send invitation emails
        3. Schedule reminders
        4. Update survey status
        5. Log delivery attempts

    Returns:
        {
            "surveys_sent": 12,
            "emails_delivered": 12,
            "reminders_scheduled": 12,
            "delivery_failures": 0
        }
    """
```

#### 3. Response Processing (Real-time)
**Trigger:** Webhook from survey provider

```python
@app.post("/webhooks/surveys/{provider}")
async def survey_response_webhook(
    provider: str,
    payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle real-time survey response webhooks.

    Process:
        1. Verify webhook signature
        2. Extract response data
        3. Store in database
        4. Trigger analysis task
        5. Return acknowledgment

    Supported Providers:
        - Typeform: Response submitted/updated
        - Google Forms: Form submitted
    """
```

#### 4. Response Analysis Queue
**Trigger:** New response webhook

```python
@celery_app.task(bind=True, max_retries=3)
async def analyze_response(response_id: str) -> dict[str, Any]:
    """
    Analyze survey response for insights.

    Process:
        1. Fetch response data
        2. Perform sentiment analysis
        3. Categorize response
        4. Generate alerts if needed
        5. Request testimonial if promoter
        6. Update satisfaction scores
        7. Notify stakeholders
    """
```

### Alert Escalation Workflow

```
Response Received (score <= 6)
   ↓
Sentiment Analysis Complete
   ↓
Generate Alert (severity based on score)
   ↓
Send to Owner (Slack + Email)
   ↓
Wait 4 hours
   ↓
If not acknowledged → Escalate to Manager
   ↓
Wait 8 hours
   ↓
If not acknowledged → Escalate to Executive
   ↓
Create Follow-up Task in Project System
   ↓
Track resolution
```

---

## Error Handling

### Provider API Errors
| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Rate limit (429) | Status code | Wait with exponential backoff | Yes, up to 5 retries |
| Authentication (401/403) | Status code | Refresh credentials or fail | No, alert ops |
| Service unavailable (503) | Status code | Retry with backoff | Yes, 3 retries |
| Timeout | Exception | Retry with longer timeout | Yes, 2 retries |
| Invalid response | Validation error | Log and skip record | No |

### Email Delivery Errors
| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Hard bounce | SMTP response | Mark as invalid, update client | No |
| Soft bounce | SMTP response | Retry after 1 hour | Yes, 3 retries |
| Complained | Feedback loop | Remove from marketing emails | No |
| Timeout | Exception | Retry with different provider | Yes, 2 retries |

### Data Quality Issues
- **Missing required fields:** Log error, set default values, continue processing
- **Invalid scores:** Clamp to valid range, log warning
- **Empty text feedback:** Skip sentiment analysis, note in record
- **Duplicate responses:** Deduplicate by external_response_id

### Edge Cases
- **Client unsubscribed:** Skip surveys, mark preference in database
- **Project on hold:** Pause all surveys for project
- **Multiple projects:** Send project-specific surveys
- **Recent survey sent:** Skip if survey sent <7 days ago

---

## Testing Requirements

### Unit Tests (>90% coverage)

#### Test: Survey Creation
```python
async def test_create_week1_onboarding_survey():
    """Test creating week 1 onboarding survey."""
    result = await create_survey(
        client_id="test_client_1",
        project_id="test_project_1",
        survey_type="week1_onboarding",
        provider="typeform"
    )

    assert result["status"] == "draft"
    assert "external_id" in result
    assert len(result["questions"]) == 3  # Standard template size
```

#### Test: Sentiment Analysis
```python
async def test_analyze_negative_feedback():
    """Test sentiment analysis of negative feedback."""
    response_data = {
        "feedback_text": "The project was delayed and communication was poor",
        "nps_score": 3,
        "satisfaction_score": 4
    }

    result = await analyze_survey_response("response_1", response_data)

    assert result["response_category"] == "detractor"
    assert result["sentiment_analysis"]["sentiment_label"] == "negative"
    assert result["urgency_level"] in ["high", "critical"]
    assert len(result["alerts_triggered"]) > 0
```

#### Test: Alert Generation
```python
async def test_alert_for_critical_feedback():
    """Test alert generation for critical feedback."""
    # Setup: Create very negative response
    response_id = await create_test_response(nps=1, satisfaction=2)

    result = await generate_satisfaction_alert(
        response_id=response_id,
        alert_type="negative_feedback",
        severity="critical"
    )

    assert result["sent"] is True
    assert "email" in result["channels_used"]
    assert result["follow_up_task_created"] is True
```

#### Test: Testimonial Request
```python
async def test_request_testimonial_from_promoter():
    """Test testimonial request for promoter."""
    # Setup: Create promoter response
    response_id = await create_test_response(nps=10, satisfaction=9)

    result = await request_testimonial(response_id=response_id)

    assert result["request_sent"] is True
    assert result["follow_up_scheduled"] is not None
```

### Integration Tests (>85% coverage)

#### Test: End-to-End Survey Workflow
```python
async def test_complete_survey_workflow():
    """Test full survey from creation to analysis."""
    # 1. Create survey
    survey = await create_survey(
        client_id="test_client_1",
        survey_type="mid_project"
    )

    # 2. Send invitation
    invite = await send_survey_invitation(
        survey_id=survey["survey_id"],
        recipient_email="client@test.com",
        recipient_name="John"
    )

    # 3. Mock webhook response
    webhook_data = create_mock_webhook_response(
        survey_id=survey["survey_id"],
        nps=9,
        satisfaction=8
    )

    # 4. Process webhook
    await survey_response_webhook("typeform", webhook_data)

    # 5. Verify analysis completed
    response = await fetch_survey_response(webhook_data["response_id"])
    assert response["nps_score"] == 9
    assert response["response_category"] == "promoter"
```

#### Test: Provider API Integration
```python
async def test_typeform_integration():
    """Test Typeform API integration."""
    # Create actual survey in Typeform
    result = await create_survey(
        client_id="test_client_1",
        survey_type="completion",
        provider="typeform"
    )

    # Verify survey exists in Typeform
    form_details = await typeform_client.get_form(result["external_id"])
    assert form_details["id"] == result["external_id"]

    # Test response sync
    sync_result = await sync_survey_responses(
        survey_id=result["survey_id"],
        provider="typeform"
    )
    assert sync_result["sync_at"] is not None
```

### Performance Tests

#### Test: Bulk Survey Processing
```python
async def test_bulk_response_processing():
    """Test processing 1000 responses efficiently."""
    # Setup: Create 1000 mock responses
    start_time = time.time()

    tasks = []
    for i in range(1000):
        task = analyze_response.delay(f"response_{i}")
        tasks.append(task)

    # Wait for all to complete
    await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    assert elapsed < 300, f"Processing took {elapsed}s, expected <5min"
```

---

## Dependencies

### Agent Dependencies
- **Onboarding Orchestrator:** Triggers Week 1 surveys
- **Project Management Agent:** Provides milestone dates and project status
- **Offboarding Agent:** Triggers completion surveys
- **Churn Risk Agent:** Receives negative feedback correlation
- **Testimonial Request Agent:** Receives promoter handoffs
- **Support Agent:** Receives urgent issue alerts

### Integration Dependencies
- **Survey Providers:**
  - Typeform API: Primary survey provider
  - Google Forms API: Alternative survey provider
- **Email Service:** Gmail/SMTP for survey invitations and alerts
- **Messaging:** Slack API for real-time alerts
- **Sentiment Analysis:** Google Cloud Natural Language API
- **Database:** PostgreSQL for storing all survey data
- **Scheduler:** Celery Beat for automated workflows

---

## Configuration

### Environment Variables
```bash
# Survey Providers
TYPEFORM_API_TOKEN=ts_...
TYPEFORM_WORKSPACE_ID=ws_...
GOOGLE_FORMS_CREDENTIALS_JSON=path/to/credentials.json

# Email Configuration
SATISFACTION_EMAIL_FROM=surveys@smarterteam.com
SATISFACTION_EMAIL_REPLY_TO=support@smarterteam.com

# Alert Configuration
SATISFACTION_ALERT_SLACK_WEBHOOK=https://hooks.slack.com/...
SATISFACTION_ALERT_EMAIL_TO=owner@smarterteam.com,manager@smarterteam.com

# Sentiment Analysis
GOOGLE_CLOUD_PROJECT_ID=smarter-team-prod
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Survey Timing
SATISFACTION_REMINDER_DELAY_DAYS=3
SATISFACTION_CLOSE_AFTER_DAYS=14
SATISFACTION_30_DAY_FOLLOWUP_DAYS=30

# Scoring Thresholds
SATISFACTION_ALERT_THRESHOLD=6
SATISFACTION_TESTIMONIAL_THRESHOLD=9
SATISFACTION_CRITICAL_THRESHOLD=3

# Behavior Settings
SATISFACTION_AUTO_TESTIMONIAL_REQUEST=true
SATISFACTION_SENTIMENT_ANALYSIS_ENABLED=true
SATISFACTION_WEEKLY_REPORT_ENABLED=true
```

### Survey Templates

#### Week 1 Onboarding Template
```json
{
  "questions": [
    {
      "id": "q1",
      "type": "rating",
      "title": "How satisfied are you with the onboarding process so far?",
      "description": "1 = Very dissatisfied, 10 = Very satisfied",
      "required": true,
      "scale": 10
    },
    {
      "id": "q2",
      "type": "yes_no",
      "title": "Is communication meeting your expectations?",
      "required": true
    },
    {
      "id": "q3",
      "type": "long_text",
      "title": "Any concerns or feedback so far?",
      "required": false
    }
  ],
  "settings": {
    "show_progress_bar": true,
    "allow_backward_navigation": true,
    "completion_time_estimate": "2 minutes"
  }
}
```

---

## Human-in-the-Loop Gates

### Gate 1: Negative Feedback Acknowledgment (Score ≤6)
**Trigger:** Survey response with satisfaction score ≤6
**Action Required:** Owner must acknowledge alert within 4 hours
**Escalation:** If not acknowledged, alert manager after 4 hours, executive after 12 hours

### Gate 2: Critical Issue Review (Score ≤3)
**Trigger:** Survey response with satisfaction score ≤3
**Action Required:** Executive review and approval of response plan within 24 hours
**Options:** Personal call from founder, project review meeting, discount offer, intervention

### Gate 3: Testimonial Usage Approval
**Trigger:** Client agrees to provide testimonial
**Action Required:** Marketing team review and approve testimonial content before publication
**Tracking:** Store testimonial status and usage rights in database

---

## Success Metrics

### Agent Performance Metrics
- **Survey Response Rate:** % of sent surveys with responses
- **Average Completion Time:** Average time to complete surveys
- **Alert Response Time:** Average time to acknowledge negative feedback
- **Analysis Accuracy:** % of sentiment analysis matching human assessment
- **Testimonial Conversion Rate:** % of promoters who provide testimonials

### Business Impact Metrics
- **Client Satisfaction Trend:** Month-over-month satisfaction score change
- **NPS Improvement:** Change in Net Promoter Score over time
- **Issue Resolution Rate:** % of negative feedback resolved successfully
- **Client Retention Correlation:** Correlation between satisfaction scores and client retention
- **Testimonials Collected:** Number of usable testimonials per month

### Operational Metrics
- **Survey Delivery Success Rate:** % of surveys successfully delivered
- **API Integration Health:** Uptime and error rates for provider integrations
- **Processing Latency:** Time from response submission to analysis completion
- **False Positive Rate:** % of alerts that don't require action

---

## Future Enhancements

### Phase 2 Enhancements
1. **AI-Powered Question Generation:** Dynamic question creation based on project type
2. **Predictive Satisfaction:** Use ML to predict satisfaction scores before surveys
3. **Multi-Language Support:** Surveys in client's preferred language
4. **Video Testimonials:** Request video testimonials from highly satisfied clients
5. **Integration with CRM:** Sync satisfaction data to GoHighLevel

### Phase 3 Enhancements
1. **Benchmarking:** Compare satisfaction scores against industry averages
2. **Automated Action Plans:** Generate specific action plans based on feedback themes
3. **Client Health Dashboard:** Real-time visualization of all satisfaction metrics
4. **Feedback Loop Automation:** Close the loop with clients on implemented changes
5. **Integration with Financials:** Correlate satisfaction with payment behavior and renewals

---

## Appendix: Survey Question Templates

### Email Templates by Survey Type

#### Week 1 Onboarding Email
```html
Subject: Quick check-in: How's everything going?

Hi {{first_name}},

You've been with us for a week now! I wanted to check in on how your onboarding experience is going.

<a href="{{survey_url}}" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Take 30-Second Survey</a>

Your feedback helps us improve the experience for all our clients.

Best regards,
The Smarter Team
```

#### Project Completion Email
```html
Subject: We'd love your feedback! 🎉

Hi {{first_name}},

Congratulations on completing {{project_name}}!

We're proud of what we accomplished together and would love to hear your thoughts on the experience.

<a href="{{survey_url}}" style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Share Your Feedback</a>

Your feedback means the world to our team and helps us continuously improve.

With gratitude,
The Smarter Team
```

### Alert Templates

#### Negative Feedback Alert (Slack)
```
🚨 SATISFACTION ALERT - HIGH

Client: {{client_name}}
Project: {{project_name}}
Alert: Negative feedback received

⚠️  CRITICAL METRICS
   • NPS Score: {{nps}}/10
   • Satisfaction: {{satisfaction}}/10
   • Sentiment: {{sentiment}}%

📝 KEY FEEDBACK
   "{{feedback_snippet}}"

🎯 RECOMMENDED ACTION
   {{recommended_action}}

[View Full Response]({dashboard_url}) | [Acknowledge Alert]({acknowledge_url})
```

---

**End of Specification**
