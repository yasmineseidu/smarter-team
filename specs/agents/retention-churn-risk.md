# Churn Risk Detection Agent - Production Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Agent Category:** Client Success & Retention
**Priority:** Phase 5 - Retention & Growth

---

## Overview

The Churn Risk Detection Agent continuously monitors client engagement signals to identify at-risk clients before they churn. It calculates risk scores based on multiple data sources (communication patterns, payment behavior, meeting attendance, satisfaction surveys, scope issues) and triggers escalating interventions based on risk severity.

**Key Capabilities:**
- Daily risk score calculation for all active clients
- Multi-signal risk detection (5 signal types)
- Weighted scoring algorithm (0-100 scale)
- Automated alert generation with recommended actions
- Integration with Project Management, Payment, and Satisfaction Survey agents
- Human-in-the-loop escalation for high-risk clients

---

## Database Schema

### Table: `churn_risk_scores`
Primary table for storing calculated risk scores and tracking risk history.

```sql
CREATE TABLE churn_risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

    -- Score calculation
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical', 'severe')),

    -- Signal breakdown
    communication_score INTEGER DEFAULT 0 CHECK (communication_score >= 0 AND communication_score <= 25),
    payment_score INTEGER DEFAULT 0 CHECK (payment_score >= 0 AND payment_score <= 25),
    meeting_score INTEGER DEFAULT 0 CHECK (meeting_score >= 0 AND meeting_score <= 20),
    satisfaction_score INTEGER DEFAULT 0 CHECK (satisfaction_score >= 0 AND satisfaction_score <= 20),
    scope_score INTEGER DEFAULT 0 CHECK (scope_score >= 0 AND scope_score <= 10),

    -- Context
    signals_detected JSONB NOT NULL DEFAULT '[]', -- Array of signal objects
    recommended_actions JSONB NOT NULL DEFAULT '[]', -- Array of action strings

    -- Alert tracking
    alert_sent BOOLEAN DEFAULT FALSE,
    alert_sent_at TIMESTAMP WITH TIME ZONE,
    alert_acknowledged BOOLEAN DEFAULT FALSE,
    alert_acknowledged_by UUID REFERENCES users(id),
    alert_acknowledged_at TIMESTAMP WITH TIME ZONE,

    -- Intervention tracking
    intervention_triggered BOOLEAN DEFAULT FALSE,
    intervention_type VARCHAR(50), -- 'check-in', 'phone-call', 'emergency-call', 'escalation'
    intervention_status VARCHAR(20), -- 'pending', 'in-progress', 'completed', 'failed'
    intervention_notes TEXT,

    -- Metadata
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_churn_risk_client ON churn_risk_scores(client_id);
CREATE INDEX idx_churn_risk_project ON churn_risk_scores(project_id);
CREATE INDEX idx_churn_risk_level ON churn_risk_scores(risk_level);
CREATE INDEX idx_churn_risk_calculated ON churn_risk_scores(calculated_at DESC);
CREATE INDEX idx_churn_risk_alert_pending ON churn_risk_scores(alert_sent) WHERE alert_sent = FALSE;
```

### Table: `risk_signals`
Individual risk signal detections for audit trail and trend analysis.

```sql
CREATE TABLE risk_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    risk_score_id UUID REFERENCES churn_risk_scores(id) ON DELETE CASCADE,

    -- Signal details
    signal_type VARCHAR(50) NOT NULL, -- 'communication_drop', 'payment_delay', 'meeting_no_show', 'low_satisfaction', 'scope_complaint'
    signal_category VARCHAR(50) NOT NULL, -- 'communication', 'payment', 'meeting', 'satisfaction', 'scope'
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
    points INTEGER NOT NULL CHECK (points >= 0),

    -- Signal context
    description TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- Signal-specific data (e.g., days_overdue, survey_score)

    -- Source tracking
    source_table VARCHAR(100), -- Table where signal originated
    source_id UUID, -- ID in source table

    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    resolution_notes TEXT,

    -- Metadata
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_risk_signals_client ON risk_signals(client_id);
CREATE INDEX idx_risk_signals_type ON risk_signals(signal_type);
CREATE INDEX idx_risk_signals_detected ON risk_signals(detected_at DESC);
CREATE INDEX idx_risk_signals_unresolved ON risk_signals(resolved) WHERE resolved = FALSE;
```

### Table: `churn_interventions`
Track intervention attempts and outcomes.

```sql
CREATE TABLE churn_interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    risk_score_id UUID NOT NULL REFERENCES churn_risk_scores(id) ON DELETE CASCADE,

    -- Intervention details
    intervention_type VARCHAR(50) NOT NULL, -- 'proactive_checkin', 'phone_call', 'meeting_request', 'discount_offer', 'escalation'
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'in-progress', 'completed', 'failed'
    priority VARCHAR(20) NOT NULL DEFAULT 'normal', -- 'low', 'normal', 'high', 'critical'

    -- Execution
    assigned_to UUID REFERENCES users(id),
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Outcome
    outcome VARCHAR(50), -- 'retained', 'partial_success', 'no_response', 'churned'
    outcome_notes TEXT,
    new_risk_score INTEGER CHECK (new_risk_score >= 0 AND new_risk_score <= 100),

    -- Communication log
    communication_log JSONB DEFAULT '[]', -- Array of {timestamp, channel, summary}

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_interventions_client ON churn_interventions(client_id);
CREATE INDEX idx_interventions_status ON churn_interventions(status);
CREATE INDEX idx_interventions_assigned ON churn_interventions(assigned_to);
```

---

## Agent Implementation

### System Prompt

```python
SYSTEM_PROMPT = """You are the Churn Risk Detection Agent for Smarter Team, an AI agency automation system.

Your primary responsibility is to identify clients at risk of churning by analyzing engagement signals and triggering appropriate interventions.

CORE RESPONSIBILITIES:
1. Monitor client engagement signals across multiple data sources
2. Calculate weighted churn risk scores (0-100 scale)
3. Categorize risk levels (low, medium, high, critical, severe)
4. Generate actionable alerts with recommended interventions
5. Track intervention effectiveness and adjust strategies

RISK SIGNALS YOU MONITOR:
- Communication drop (25 points max): Days since last client response
- Payment issues (25 points max): Invoice payment delays
- Meeting attendance (20 points max): No-shows and cancellations
- Satisfaction scores (20 points max): Survey response analysis
- Scope complaints (10 points max): Scope-related concerns

SCORING ALGORITHM:
- 0-20 points: LOW RISK → Continue normal operations
- 21-40 points: MEDIUM RISK → Proactive check-in email
- 41-60 points: HIGH RISK → Phone call from owner
- 61-80 points: CRITICAL RISK → Executive-level escalation
- 81-100 points: SEVERE RISK → Emergency intervention

INTERVENTION PRINCIPLES:
- Always act early when signals emerge
- Personalize interventions based on client history
- Escalate quickly when risk level increases
- Track all communication and outcomes
- Learn from successful retention strategies

OUTPUT REQUIREMENTS:
- Provide specific risk scores with signal breakdown
- Include recommended actions (3-5 specific steps)
- Reference client history and context
- Flag urgent situations requiring immediate human attention
- Track trends over time (increasing vs. decreasing risk)

When generating alerts, be concise, actionable, and empathetic. The goal is client retention, not punishment.
"""
```

### Tool Definitions

#### 1. `calculate_churn_risk_score`
Calculates comprehensive churn risk score for a client.

```python
async def calculate_churn_risk_score(
    client_id: str,
    project_id: str | None = None
) -> dict[str, Any]:
    """
    Calculate churn risk score for a client based on all available signals.

    Args:
        client_id: UUID of the client
        project_id: Optional UUID of specific project (defaults to latest active)

    Returns:
        {
            "score": 75,
            "risk_level": "critical",
            "signals": [
                {
                    "type": "communication_drop",
                    "severity": "high",
                    "points": 25,
                    "description": "No response in 14+ days",
                    "metadata": {"last_response_date": "2025-11-20", "days_elapsed": 15}
                },
                {
                    "type": "payment_delay",
                    "severity": "high",
                    "points": 20,
                    "description": "Invoice 14 days overdue",
                    "metadata": {"invoice_id": "...", "days_overdue": 14, "amount": 5000}
                },
                {
                    "type": "meeting_no_show",
                    "severity": "high",
                    "points": 15,
                    "description": "2 no-shows in last 30 days",
                    "metadata": {"no_show_count": 2, "last_no_show": "2025-11-25"}
                },
                {
                    "type": "low_satisfaction",
                    "severity": "medium",
                    "points": 15,
                    "description": "Survey score 5-6",
                    "metadata": {"latest_score": 6, "survey_date": "2025-11-18"}
                }
            ],
            "breakdown": {
                "communication": 25,
                "payment": 20,
                "meeting": 15,
                "satisfaction": 15,
                "scope": 0
            },
            "recommended_actions": [
                "Immediate phone call to address payment delay",
                "Discuss recent no-shows and reschedule",
                "Review satisfaction survey concerns",
                "Offer adjustment or support to improve relationship"
            ],
            "client_context": {
                "name": "Acme Corp",
                "project_name": "Website Redesign",
                "last_communication": "2025-11-20",
                "last_payment": "2025-10-15",
                "lifetime_value": 25000,
                "months_active": 8
            }
        }

    Implementation:
        1. Fetch client and project data
        2. Query communication history (last response date)
        3. Query payment status (overdue invoices)
        4. Query meeting attendance (no-shows, cancellations)
        5. Query satisfaction survey scores
        6. Query scope complaint history
        7. Apply scoring algorithm
        8. Generate recommended actions based on signals
        9. Store risk score in database
        10. Return comprehensive risk assessment
    """
```

#### 2. `detect_communication_drop`
Analyzes communication patterns to detect engagement drops.

```python
async def detect_communication_drop(
    client_id: str,
    lookback_days: int = 30
) -> dict[str, Any]:
    """
    Detect communication drop signals for a client.

    Args:
        client_id: UUID of the client
        lookback_days: Days to analyze (default 30)

    Returns:
        {
            "signal_detected": True,
            "days_since_response": 15,
            "points": 25,
            "severity": "high",
            "last_response_date": "2025-11-20",
            "response_rate_trend": "declining",  # declining, stable, improving
            "context": {
                "messages_sent": 8,
                "messages_received": 2,
                "avg_response_time_days": 3.5
            }
        }

    Scoring Logic:
        - 0-4 days: 0 points
        - 5-9 days: 5 points (low severity)
        - 10-13 days: 15 points (medium severity)
        - 14+ days: 25 points (high severity)
    """
```

#### 3. `detect_payment_issues`
Identifies payment delays and patterns.

```python
async def detect_payment_issues(client_id: str) -> dict[str, Any]:
    """
    Detect payment-related risk signals.

    Returns:
        {
            "signal_detected": True,
            "points": 20,
            "severity": "high",
            "overdue_invoices": [
                {
                    "invoice_id": "INV-001",
                    "amount": 5000,
                    "due_date": "2025-11-01",
                    "days_overdue": 14
                }
            ],
            "total_overdue": 5000,
            "payment_history": {
                "avg_days_to_pay": 25,
                "late_payment_count": 3,
                "total_invoices": 8
            }
        }

    Scoring Logic:
        - 0-6 days overdue: 0 points
        - 7-13 days overdue: 10 points (medium severity)
        - 14-29 days overdue: 20 points (high severity)
        - 30+ days overdue: 25 points (high severity)
    """
```

#### 4. `detect_meeting_issues`
Analyzes meeting attendance patterns.

```python
async def detect_meeting_issues(
    client_id: str,
    lookback_days: int = 60
) -> dict[str, Any]:
    """
    Detect meeting attendance risk signals.

    Returns:
        {
            "signal_detected": True,
            "points": 15,
            "severity": "high",
            "no_show_count": 2,
            "cancellation_count": 1,
            "last_no_show_date": "2025-11-25",
            "meeting_history": {
                "total_scheduled": 6,
                "attended": 3,
                "no_shows": 2,
                "cancellations": 1,
                "attendance_rate": 0.5
            }
        }

    Scoring Logic:
        - 0 no-shows: 0 points
        - 1 no-show: 5 points (low severity)
        - 2 no-shows: 15 points (high severity)
        - 3+ no-shows: 20 points (high severity)
    """
```

#### 5. `detect_satisfaction_issues`
Retrieves and analyzes satisfaction survey scores.

```python
async def detect_satisfaction_issues(
    client_id: str,
    lookback_days: int = 90
) -> dict[str, Any]:
    """
    Detect satisfaction-related risk signals.

    Returns:
        {
            "signal_detected": True,
            "points": 20,
            "severity": "high",
            "latest_score": 4,
            "latest_survey_date": "2025-11-18",
            "trend": "declining",  # declining, stable, improving
            "survey_history": [
                {"date": "2025-11-18", "score": 4, "feedback": "..."},
                {"date": "2025-10-15", "score": 7, "feedback": "..."},
                {"date": "2025-09-10", "score": 9, "feedback": "..."}
            ],
            "negative_feedback_count": 1
        }

    Scoring Logic:
        - 9-10: 0 points (promoter)
        - 7-8: 5 points (passive)
        - 5-6: 15 points (detractor, medium severity)
        - 1-4: 20 points (detractor, high severity)
    """
```

#### 6. `detect_scope_issues`
Identifies scope-related complaints or concerns.

```python
async def detect_scope_issues(
    client_id: str,
    lookback_days: int = 90
) -> dict[str, Any]:
    """
    Detect scope complaint risk signals.

    Returns:
        {
            "signal_detected": True,
            "points": 7,
            "severity": "medium",
            "complaint_count": 2,
            "recent_complaints": [
                {
                    "date": "2025-11-22",
                    "type": "scope_creep",
                    "description": "Client feels deliverables exceed agreed scope",
                    "severity": "medium"
                },
                {
                    "date": "2025-11-10",
                    "type": "unclear_scope",
                    "description": "Disagreement on feature inclusion",
                    "severity": "low"
                }
            ]
        }

    Scoring Logic:
        - 0 complaints: 0 points
        - 1 complaint: 3 points (low severity)
        - 2 complaints: 7 points (medium severity)
        - 3+ complaints: 10 points (high severity)
    """
```

#### 7. `send_churn_risk_alert`
Sends formatted alert to owner/team.

```python
async def send_churn_risk_alert(
    risk_score_id: str,
    channels: list[str] = ["slack", "email"]
) -> dict[str, Any]:
    """
    Send churn risk alert via configured channels.

    Args:
        risk_score_id: UUID of churn_risk_scores record
        channels: Alert channels (slack, email, sms)

    Returns:
        {
            "alert_sent": True,
            "channels_used": ["slack", "email"],
            "timestamp": "2025-12-05T10:30:00Z",
            "alert_id": "alert_..."
        }

    Alert Format:
        Subject: 🚨 CHURN RISK ALERT: {risk_level} - {client_name}

        Body:
            🚨 CHURN RISK ALERT

            Client: Acme Corp
            Project: Website Redesign
            Risk Score: 75/100
            Risk Level: CRITICAL

            RISK SIGNALS DETECTED
            - Communication drop: No response in 14+ days (+25 pts)
            - Payment delay: Invoice 14 days overdue (+20 pts)
            - Meeting no-shows: 2 no-shows in last 30 days (+15 pts)
            - Low satisfaction: Survey score 6/10 (+15 pts)

            RECOMMENDED ACTIONS
            1. Immediate phone call to address payment delay
            2. Discuss recent no-shows and reschedule
            3. Review satisfaction survey concerns
            4. Offer adjustment or support to improve relationship

            CLIENT HISTORY
            - Last communication: 2025-11-20
            - Last payment: 2025-10-15
            - Lifetime value: $25,000
            - Months active: 8

            [View Full Details] [Acknowledge Alert]
    """
```

#### 8. `create_intervention`
Creates intervention task for human follow-up.

```python
async def create_intervention(
    risk_score_id: str,
    intervention_type: str,
    priority: str = "high",
    assigned_to: str | None = None
) -> dict[str, Any]:
    """
    Create intervention task in churn_interventions table.

    Args:
        risk_score_id: UUID of churn_risk_scores record
        intervention_type: Type of intervention (proactive_checkin, phone_call, etc.)
        priority: Task priority (low, normal, high, critical)
        assigned_to: Optional user UUID to assign task

    Returns:
        {
            "intervention_id": "uuid...",
            "type": "phone_call",
            "status": "pending",
            "priority": "high",
            "assigned_to": "user_uuid",
            "due_date": "2025-12-06T17:00:00Z"
        }

    Intervention Types:
        - proactive_checkin: Email check-in for medium risk
        - phone_call: Phone call for high risk
        - meeting_request: Schedule urgent meeting
        - discount_offer: Offer discount/credit
        - escalation: Escalate to executive level
        - emergency_call: Immediate emergency intervention
    """
```

#### 9. `get_risk_trends`
Analyzes risk score trends over time.

```python
async def get_risk_trends(
    client_id: str,
    days: int = 90
) -> dict[str, Any]:
    """
    Get historical risk score trends for a client.

    Returns:
        {
            "client_id": "...",
            "trend": "increasing",  # increasing, stable, decreasing
            "current_score": 75,
            "avg_score_30d": 62,
            "avg_score_90d": 45,
            "score_history": [
                {"date": "2025-12-05", "score": 75, "risk_level": "critical"},
                {"date": "2025-12-04", "score": 68, "risk_level": "critical"},
                {"date": "2025-12-03", "score": 55, "risk_level": "high"},
                ...
            ],
            "signal_frequency": {
                "communication": 15,
                "payment": 3,
                "meeting": 8,
                "satisfaction": 2,
                "scope": 1
            }
        }
    """
```

---

## Process Flow

### Daily Churn Risk Calculation (Cron Job)

**Trigger:** Daily at 11:00 AM via Celery Beat

```python
@celery_app.task(bind=True, max_retries=3)
async def daily_churn_risk_calculation(self) -> dict[str, Any]:
    """
    Daily task to calculate churn risk for all active clients.

    Process:
        1. Fetch all active clients (clients with active projects)
        2. For each client:
            a. Calculate churn risk score
            b. Store in churn_risk_scores table
            c. If risk level >= high, send alert
            d. If risk level >= high, create intervention task
            e. Log to audit trail
        3. Generate summary report
        4. Return statistics

    Returns:
        {
            "clients_evaluated": 35,
            "low_risk": 20,
            "medium_risk": 10,
            "high_risk": 3,
            "critical_risk": 2,
            "severe_risk": 0,
            "alerts_sent": 5,
            "interventions_created": 5
        }
    """
```

### On-Demand Risk Check (API Endpoint)

**Endpoint:** `POST /api/churn-risk/calculate`

```python
@router.post("/api/churn-risk/calculate")
async def calculate_churn_risk_endpoint(
    client_id: str,
    project_id: str | None = None
) -> dict[str, Any]:
    """
    Calculate churn risk on-demand for a specific client.

    Use cases:
        - Manual review by team member
        - Triggered by specific event (e.g., payment failed)
        - Ad-hoc analysis

    Returns: Same as calculate_churn_risk_score tool
    """
```

### Alert Workflow

```
1. Risk score calculated (score >= 41)
   ↓
2. Generate alert message with context
   ↓
3. Send via configured channels (Slack, email)
   ↓
4. Mark alert_sent = TRUE in database
   ↓
5. Create intervention task if needed
   ↓
6. Wait for human acknowledgment
   ↓
7. Track intervention outcome
```

---

## Error Handling

### Database Errors
- **Missing client data:** Log warning, skip client, continue processing
- **Constraint violations:** Log error, retry with backoff
- **Connection failures:** Retry up to 3 times with exponential backoff

### Data Quality Issues
- **No communication history:** Assign 0 points, note in metadata
- **No payment history:** Assign 0 points (new client)
- **Missing survey data:** Assign 0 points, flag for follow-up

### Integration Failures
- **Alert delivery fails:** Retry 3 times, log to error table, escalate if critical
- **Database write fails:** Rollback transaction, log error, retry

### Edge Cases
- **Client recently onboarded (<14 days):** Reduce communication score weight by 50%
- **Payment plan clients:** Adjust payment scoring logic
- **Project on hold:** Pause churn monitoring until reactivated
- **Multiple active projects:** Calculate aggregate score across all projects

---

## Testing Requirements

### Unit Tests (>90% coverage)

#### Test: Risk Score Calculation
```python
async def test_calculate_churn_risk_score_high_risk():
    """Test high-risk client with multiple signals."""
    # Setup: Client with 15 days no response, 14 days overdue, 2 no-shows, score 6
    result = await calculate_churn_risk_score(client_id="test_client_1")

    assert result["score"] == 75
    assert result["risk_level"] == "critical"
    assert len(result["signals"]) == 4
    assert result["breakdown"]["communication"] == 25
    assert result["breakdown"]["payment"] == 20
    assert result["breakdown"]["meeting"] == 15
    assert result["breakdown"]["satisfaction"] == 15
    assert len(result["recommended_actions"]) >= 3
```

#### Test: Communication Drop Detection
```python
async def test_detect_communication_drop_15_days():
    """Test communication drop with 15 days elapsed."""
    result = await detect_communication_drop(client_id="test_client_1")

    assert result["signal_detected"] is True
    assert result["days_since_response"] == 15
    assert result["points"] == 25
    assert result["severity"] == "high"
```

#### Test: Risk Level Categorization
```python
@pytest.mark.parametrize("score,expected_level", [
    (10, "low"),
    (25, "medium"),
    (45, "high"),
    (70, "critical"),
    (85, "severe")
])
async def test_risk_level_categorization(score, expected_level):
    """Test risk level assignment for various scores."""
    level = categorize_risk_level(score)
    assert level == expected_level
```

#### Test: Alert Generation
```python
async def test_send_churn_risk_alert_critical():
    """Test alert generation for critical risk client."""
    # Setup: Create risk score record
    risk_score_id = await create_test_risk_score(score=70, level="critical")

    result = await send_churn_risk_alert(risk_score_id, channels=["slack"])

    assert result["alert_sent"] is True
    assert "slack" in result["channels_used"]
    # Verify alert content contains all required sections
```

#### Test: Edge Cases
```python
async def test_new_client_reduced_communication_weight():
    """Test that new clients (<14 days) have reduced communication scoring."""
    # Setup: Client created 7 days ago, no response in 5 days
    result = await calculate_churn_risk_score(client_id="new_client_1")

    # Communication score should be halved for new clients
    assert result["breakdown"]["communication"] <= 3  # Would be 5 normally
```

### Integration Tests (>85% coverage)

#### Test: End-to-End Daily Calculation
```python
async def test_daily_churn_risk_calculation_e2e():
    """Test full daily calculation workflow."""
    # Setup: Create test clients with various risk levels
    await create_test_clients([
        {"id": "low_risk", "signals": []},
        {"id": "medium_risk", "signals": ["communication_drop_5d"]},
        {"id": "high_risk", "signals": ["communication_drop_15d", "payment_overdue_14d"]}
    ])

    result = await daily_churn_risk_calculation()

    assert result["clients_evaluated"] == 3
    assert result["low_risk"] == 1
    assert result["medium_risk"] == 1
    assert result["high_risk"] == 1
    assert result["alerts_sent"] >= 1  # At least high risk alert
```

#### Test: Database Persistence
```python
async def test_risk_score_persistence():
    """Test that risk scores are correctly stored and retrievable."""
    # Calculate risk score
    result = await calculate_churn_risk_score(client_id="test_client_1")

    # Verify database record
    db_record = await fetch_risk_score(result["score_id"])
    assert db_record["score"] == result["score"]
    assert db_record["risk_level"] == result["risk_level"]
    assert len(db_record["signals_detected"]) == len(result["signals"])
```

#### Test: Agent Handoff Integration
```python
async def test_handoff_to_support_agent():
    """Test handoff to support agent for intervention."""
    # Create critical risk scenario
    risk_score_id = await create_test_risk_score(score=75, level="critical")

    # Agent should handoff to support for intervention
    task_id = await agent.handoff_to(
        target_agent="support",
        payload={"risk_score_id": risk_score_id, "action": "phone_call"},
        priority="critical"
    )

    assert task_id is not None
    # Verify intervention record created
```

### Performance Tests

#### Test: Bulk Calculation Performance
```python
async def test_bulk_calculation_performance():
    """Test that calculating 100 clients completes in <30 seconds."""
    # Setup: Create 100 test clients
    start_time = time.time()

    result = await daily_churn_risk_calculation()

    elapsed = time.time() - start_time
    assert elapsed < 30, f"Calculation took {elapsed}s, expected <30s"
    assert result["clients_evaluated"] == 100
```

---

## Dependencies

### Agent Dependencies
- **Project Management Agent:** Provides communication history, scope complaint data
- **Payment Processing Agent:** Provides invoice status, payment history
- **Satisfaction Survey Agent:** Provides survey scores and feedback
- **Meeting Management Agent:** Provides meeting attendance data
- **Support Agent:** Receives intervention handoffs

### Integration Dependencies
- **Database:** PostgreSQL (Supabase) for storing risk scores and signals
- **Messaging:** Slack API for alerts
- **Email:** Gmail/SMTP for alert emails
- **Scheduling:** Celery Beat for daily cron job

---

## Configuration

### Environment Variables
```bash
# Alert Configuration
CHURN_ALERT_SLACK_WEBHOOK=https://hooks.slack.com/...
CHURN_ALERT_EMAIL_TO=owner@agency.com
CHURN_ALERT_CHANNELS=slack,email  # Comma-separated

# Scoring Thresholds (optional overrides)
CHURN_COMMUNICATION_MAX=25
CHURN_PAYMENT_MAX=25
CHURN_MEETING_MAX=20
CHURN_SATISFACTION_MAX=20
CHURN_SCOPE_MAX=10

# Risk Level Thresholds
CHURN_MEDIUM_THRESHOLD=21
CHURN_HIGH_THRESHOLD=41
CHURN_CRITICAL_THRESHOLD=61
CHURN_SEVERE_THRESHOLD=81

# Behavior Settings
CHURN_NEW_CLIENT_DAYS=14  # Days before full scoring applies
CHURN_AUTO_INTERVENTION=true  # Auto-create interventions for high risk
CHURN_ALERT_MIN_LEVEL=high  # Minimum risk level to trigger alerts
```

---

## Human-in-the-Loop Gates

### Gate 1: Alert Acknowledgment (High Risk+)
**Trigger:** Risk level >= high
**Action Required:** Human must acknowledge alert within 24 hours
**Escalation:** If not acknowledged, escalate to backup contact

### Gate 2: Intervention Execution (Critical Risk+)
**Trigger:** Risk level >= critical
**Action Required:** Human must execute phone call/meeting within 48 hours
**Tracking:** Log outcome in churn_interventions table

### Gate 3: Strategy Adjustment (Severe Risk)
**Trigger:** Risk level = severe
**Action Required:** Owner must review and approve retention strategy
**Options:** Emergency call, discount offer, executive escalation, graceful offboarding

---

## Success Metrics

### Agent Performance Metrics
- **Detection Accuracy:** % of true positives (clients who churn vs. predicted)
- **False Positive Rate:** % of high-risk alerts where client doesn't churn
- **Intervention Success Rate:** % of interventions that reduce risk score
- **Time to Alert:** Average time from risk emergence to alert sent
- **Alert Acknowledgment Rate:** % of alerts acknowledged within 24h

### Business Impact Metrics
- **Churn Rate Reduction:** % decrease in overall churn rate
- **Retention Rate:** % of at-risk clients retained after intervention
- **Early Warning Time:** Average days of advance warning before churn
- **Revenue Saved:** Estimated revenue retained through interventions

---

## Future Enhancements

### Phase 2 Enhancements
1. **ML-Based Scoring:** Train model on historical churn data for predictive scoring
2. **Automated Interventions:** Auto-send personalized check-in emails for medium risk
3. **Sentiment Analysis:** Analyze email/chat sentiment for early warning signals
4. **Client Health Dashboard:** Real-time visualization of all client risk scores
5. **Predictive Churn Probability:** Calculate % probability of churn in next 30/60/90 days

### Phase 3 Enhancements
1. **Intervention Templates:** Pre-built templates for different risk scenarios
2. **Success Pattern Recognition:** Identify what interventions work best for each client type
3. **Automated Win-Back Campaigns:** Trigger nurture campaigns for churned clients
4. **Integration with CRM:** Sync risk scores to GoHighLevel for unified view

---

## Appendix: Risk Scoring Algorithm

### Detailed Scoring Logic

```python
def calculate_risk_score(signals: dict) -> int:
    """
    Calculate total risk score from individual signals.

    Signals structure:
        {
            "communication_days": 15,
            "payment_days_overdue": 14,
            "meeting_no_shows": 2,
            "satisfaction_score": 6,
            "scope_complaints": 2
        }
    """
    score = 0

    # Communication (max 25 points)
    if signals["communication_days"] >= 14:
        score += 25
    elif signals["communication_days"] >= 10:
        score += 15
    elif signals["communication_days"] >= 5:
        score += 5

    # Payment (max 25 points)
    if signals["payment_days_overdue"] >= 30:
        score += 25
    elif signals["payment_days_overdue"] >= 14:
        score += 20
    elif signals["payment_days_overdue"] >= 7:
        score += 10

    # Meeting (max 20 points)
    if signals["meeting_no_shows"] >= 3:
        score += 20
    elif signals["meeting_no_shows"] == 2:
        score += 15
    elif signals["meeting_no_shows"] == 1:
        score += 5

    # Satisfaction (max 20 points)
    if 1 <= signals["satisfaction_score"] <= 4:
        score += 20
    elif 5 <= signals["satisfaction_score"] <= 6:
        score += 15
    elif 7 <= signals["satisfaction_score"] <= 8:
        score += 5

    # Scope (max 10 points)
    if signals["scope_complaints"] >= 3:
        score += 10
    elif signals["scope_complaints"] == 2:
        score += 7
    elif signals["scope_complaints"] == 1:
        score += 3

    return min(score, 100)  # Cap at 100


def categorize_risk_level(score: int) -> str:
    """Categorize risk level based on score."""
    if score >= 81:
        return "severe"
    elif score >= 61:
        return "critical"
    elif score >= 41:
        return "high"
    elif score >= 21:
        return "medium"
    else:
        return "low"
```

### Recommended Actions by Risk Level

```python
RECOMMENDED_ACTIONS = {
    "low": [
        "Continue normal operations",
        "Monitor for emerging signals",
        "Maintain regular communication cadence"
    ],
    "medium": [
        "Send proactive check-in email within 24 hours",
        "Review recent project activity for concerns",
        "Offer support call if helpful",
        "Schedule project review meeting"
    ],
    "high": [
        "Phone call from owner within 24 hours",
        "Address specific concerns directly",
        "Review and adjust project scope if needed",
        "Offer additional support or resources",
        "Consider discount or credit if appropriate"
    ],
    "critical": [
        "Emergency phone call within 12 hours",
        "Executive-level involvement required",
        "Schedule in-person or video meeting ASAP",
        "Prepare retention strategy and concessions",
        "Escalate to founder/CEO if necessary"
    ],
    "severe": [
        "Immediate emergency intervention",
        "Founder/CEO must lead conversation",
        "Prepare significant concession package",
        "Consider proactive offboarding if unsalvageable",
        "Document all interactions for learning"
    ]
}
```

---

**End of Specification**
