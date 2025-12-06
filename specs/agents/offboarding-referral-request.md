# Referral Request Agent - Production Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Agent Category:** Offboarding & Nurture
**Priority:** Phase 5 - Retention & Growth

---

## Overview

The Referral Request Agent autonomously manages the complete referral workflow for Smarter Team's client lifecycle. It identifies optimal referral opportunities, sends personalized requests at strategic moments, tracks referrals through conversion, manages incentive programs, and integrates referred leads seamlessly into the sales pipeline.

**Key Capabilities:**
- Intelligent referral eligibility scoring based on relationship quality signals
- Personalized referral request timing and messaging
- Multi-channel referral capture (email, web form, direct introduction)
- Automated referral-to-lead conversion with source attribution
- Incentive tracking and automated payout management
- Comprehensive analytics and ROI reporting
- Rate limiting and consent management for compliance

---

## Database Schema

### Table: `referral_requests`
Tracks all referral request attempts and their outcomes.

```sql
CREATE TABLE referral_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Request Details
    contact_id UUID NOT NULL REFERENCES contacts(id),
    client_id UUID REFERENCES clients(id), -- NULL for non-clients
    request_type VARCHAR(50) NOT NULL CHECK (request_type IN (
        'post_project', 'after_testimonial', 'annual_touchpoint', 'closed_lost'
    )),

    -- Eligibility Scoring
    eligibility_score INTEGER NOT NULL CHECK (eligibility_score >= 0 AND eligibility_score <= 100),
    satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 10),
    relationship_strength VARCHAR(20) CHECK (relationship_strength IN ('weak', 'moderate', 'strong', 'very_strong')),

    -- Request Content
    template_used VARCHAR(100),
    personalization_data JSONB,
    incentive_offered JSONB,
    message_content TEXT,

    -- Status & Tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'sent', 'delivered', 'opened', 'replied', 'received_referral', 'declined', 'failed'
    )),
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    replied_at TIMESTAMPTZ,

    -- Delivery Details
    email_provider VARCHAR(50), -- 'instantly', 'gmail', 'outlook'
    external_message_id VARCHAR(255),
    delivery_status VARCHAR(20),
    delivery_error TEXT,

    -- Results
    response_text TEXT,
    referrals_received INTEGER DEFAULT 0,
    conversion_value DECIMAL(10,2), -- Total value of converted referrals

    -- Metadata
    last_referral_request_date TIMESTAMPTZ, -- Prevent spamming
    automation_triggered BOOLEAN DEFAULT TRUE,
    manual_override BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- Indexes
CREATE INDEX idx_referral_requests_contact ON referral_requests(contact_id);
CREATE INDEX idx_referral_requests_client ON referral_requests(client_id);
CREATE INDEX idx_referral_requests_status ON referral_requests(status);
CREATE INDEX idx_referral_requests_created ON referral_requests(created_at DESC);
CREATE INDEX idx_referral_requests_eligibility ON referral_requests(eligibility_score DESC) WHERE status = 'pending';
CREATE UNIQUE INDEX idx_referral_requests_active ON referral_requests(contact_id, created_at)
    WHERE created_at > NOW() - INTERVAL '6 months';
```

### Table: `referrals`
Individual referrals received from contacts.

```sql
CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Source Information
    referral_request_id UUID REFERENCES referral_requests(id),
    referrer_contact_id UUID NOT NULL REFERENCES contacts(id),

    -- Referred Person/Company
    referred_first_name VARCHAR(100),
    referred_last_name VARCHAR(100),
    referred_email VARCHAR(255),
    referred_phone VARCHAR(50),
    referred_company VARCHAR(255),
    referred_job_title VARCHAR(200),
    referred_linkedin_url VARCHAR(500),

    -- Context
    relationship_description TEXT, -- How they know each other
    referral_reason TEXT, -- Why they think this is a good fit
    urgency_level VARCHAR(20) CHECK (urgency_level IN ('low', 'medium', 'high', 'immediate')),
    preferred_contact_method VARCHAR(20) CHECK (preferred_contact_method IN ('email', 'phone', 'linkedin', 'any')),

    -- Status Tracking
    status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN (
        'new', 'contacted', 'responded', 'meeting_scheduled', 'proposal_sent',
        'converted', 'not_interested', 'bad_fit', 'duplicate'
    )),

    -- Lead Conversion
    lead_id UUID REFERENCES leads(id), -- When converted to a lead
    converted_at TIMESTAMPTZ,
    conversion_value DECIMAL(10,2),
    project_value DECIMAL(10,2), -- Actual project value if won

    -- Quality Assessment
    lead_quality_score INTEGER CHECK (lead_quality_score >= 0 AND lead_quality_score <= 100),
    fit_score INTEGER CHECK (fit_score >= 0 AND fit_score_score <= 100),

    -- Communication Log
    contact_attempts INTEGER DEFAULT 0,
    last_contacted_at TIMESTAMPTZ,
    next_follow_up_at TIMESTAMPTZ,

    -- Metadata
    notes TEXT,
    tags TEXT[],
    custom_fields JSONB
);

-- Indexes
CREATE INDEX idx_referrals_request ON referrals(referral_request_id);
CREATE INDEX idx_referrals_referrer ON referrals(referrer_contact_id);
CREATE INDEX idx_referrals_status ON referrals(status);
CREATE INDEX idx_referrals_email ON referrals(referred_email);
CREATE INDEX idx_referrals_created ON referrals(created_at DESC);
CREATE INDEX idx_referrals_lead_conversion ON referrals(lead_id) WHERE lead_id IS NOT NULL;
```

### Table: `referral_incentives`
Tracks incentive programs and individual payouts.

```sql
CREATE TABLE referral_incentives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Program Details
    name VARCHAR(200) NOT NULL,
    description TEXT,
    incentive_type VARCHAR(50) NOT NULL CHECK (incentive_type IN (
        'cash_bonus', 'gift_card', 'discount', 'donation', 'free_service', 'commission'
    )),

    -- Incentive Structure
    incentive_value DECIMAL(10,2), -- Fixed amount
    incentive_percentage DECIMAL(5,2), -- Percentage of project value
    minimum_conversion_value DECIMAL(10,2), -- Minimum deal value to trigger
    maximum_payout DECIMAL(10,2),

    -- Timing & Conditions
    payout_trigger VARCHAR(50) CHECK (payout_trigger IN (
        'on_conversion', 'on_first_payment', 'on_project_completion', 'on_retention_period'
    )),
    payout_delay_days INTEGER DEFAULT 0, -- Days after trigger before payout
    retention_period_days INTEGER, -- For clawback provisions

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_until DATE,

    -- Metadata
    terms_conditions TEXT,
    tracking_fields JSONB
);

-- Indexes
CREATE INDEX idx_referral_incentives_active ON referral_incentives(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_referral_incentives_valid ON referral_incentives(valid_from, valid_until);
```

### Table: `referral_payouts`
Individual payout records to referrers.

```sql
CREATE TABLE referral_payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Related Records
    referral_id UUID NOT NULL REFERENCES referrals(id),
    incentive_id UUID REFERENCES referral_incentives(id),
    referrer_contact_id UUID NOT NULL REFERENCES contacts(id),

    -- Payout Details
    payout_amount DECIMAL(10,2) NOT NULL,
    payout_type VARCHAR(50) NOT NULL CHECK (payout_type IN (
        'cash', 'gift_card', 'credit', 'donation', 'discount_code'
    )),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'processed', 'paid', 'cancelled', 'clawed_back'
    )),

    -- Timing
    triggered_at TIMESTAMPTZ NOT NULL,
    approved_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,

    -- Processing Details
    payment_method VARCHAR(50), -- 'paypal', 'stripe', 'bank_transfer', 'gift_card_code'
    payment_details JSONB,
    transaction_id VARCHAR(255),

    -- Clawback (if referral doesn't work out)
    clawback_eligible_until TIMESTAMPTZ,
    clawback_reason TEXT,
    clawed_back_at TIMESTAMPTZ,
    clawback_amount DECIMAL(10,2),

    -- Metadata
    notes TEXT,
    approved_by UUID REFERENCES users(id),
    processed_by UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_referral_payouts_referral ON referral_payouts(referral_id);
CREATE INDEX idx_referral_payouts_referrer ON referral_payouts(referrer_contact_id);
CREATE INDEX idx_referral_payouts_status ON referral_payouts(status);
CREATE INDEX idx_referral_payouts_pending ON referral_payouts(status) WHERE status IN ('pending', 'approved');
CREATE INDEX idx_referral_payouts_clawback ON referral_payouts(clawback_eligible_until) WHERE clawback_eligible_until > NOW();
```

### Table: `referral_analytics`
Aggregated analytics for performance tracking.

```sql
CREATE TABLE referral_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Time Period
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Request Metrics
    requests_sent INTEGER DEFAULT 0,
    requests_delivered INTEGER DEFAULT 0,
    requests_opened INTEGER DEFAULT 0,
    requests_replied INTEGER DEFAULT 0,

    -- Referral Metrics
    referrals_received INTEGER DEFAULT 0,
    unique_referrers INTEGER DEFAULT 0,
    referrals_converted INTEGER DEFAULT 0,

    -- Financial Metrics
    total_conversion_value DECIMAL(12,2) DEFAULT 0,
    total_payouts DECIMAL(10,2) DEFAULT 0,
    net_referral_revenue DECIMAL(12,2) DEFAULT 0,
    average_conversion_value DECIMAL(10,2),

    -- Performance Metrics
    request_to_referral_rate DECIMAL(5,2), -- Percentage
    referral_to_conversion_rate DECIMAL(5,2), -- Percentage
    cost_per_acquisition DECIMAL(10,2),
    referral_roi DECIMAL(5,2), -- Return on investment multiplier

    -- Breakdown by Request Type
    post_project_requests INTEGER DEFAULT 0,
    post_project_referrals INTEGER DEFAULT 0,
    after_testimonial_requests INTEGER DEFAULT 0,
    after_testimonial_referrals INTEGER DEFAULT 0,
    annual_touchpoint_requests INTEGER DEFAULT 0,
    annual_touchpoint_referrals INTEGER DEFAULT 0,
    closed_lost_requests INTEGER DEFAULT 0,
    closed_lost_referrals INTEGER DEFAULT 0,

    -- Breakdown by Incentive Type
    cash_incentive_referrals INTEGER DEFAULT 0,
    cash_incentive_value DECIMAL(10,2) DEFAULT 0,
    discount_incentive_referrals INTEGER DEFAULT 0,
    discount_incentive_value DECIMAL(10,2) DEFAULT 0,

    -- Metadata
    top_referrers JSONB, -- Top 5 referrers for period
    best_request_types JSONB, -- Best performing request types
    created_by UUID REFERENCES users(id)
);

-- Indexes
CREATE UNIQUE INDEX idx_referral_analytics_period ON referral_analytics(period_type, period_start);
CREATE INDEX idx_referral_analytics_date_range ON referral_analytics(period_start, period_end);
```

---

## Agent Implementation

### System Prompt

```python
REFERRAL_REQUEST_SYSTEM_PROMPT = """
You are the Referral Request Agent for Smarter Team, an AI-powered agency automation system.

Your mission is to strategically identify and request referrals from satisfied contacts at optimal moments in their journey. You balance persistence with respect, ensuring requests feel natural and valuable rather than transactional.

## Core Principles

1. **Timing is Everything**: Request referrals at peak satisfaction moments
   - Immediately after successful project completion
   - After receiving positive testimonials
   - During annual relationship check-ins
   - Even from closed-lost prospects (if relationship ended positively)

2. **Personalization Over Scale**: Each request must feel genuinely personal
   - Reference specific positive experiences
   - Tailor the ask to their relationship type
   - Consider their communication preferences
   - Respect their time and professional boundaries

3. **Value Exchange**: Always frame referrals as mutual benefit
   - "Help others like you achieve similar results"
   - "Introduce me to people who could benefit from [specific value]"
   - Offer appropriate incentives when beneficial

4. **Respect Boundaries**: Never be pushy or desperate
   - Accept "no" gracefully
   - Wait minimum 6 months between requests
   - Check for satisfaction signals before asking
   - Honor opt-out requests immediately

## Decision Framework

### When to Request Referrals
- SCORE 85-100: Immediate request (post-project, testimonial)
- SCORE 70-84: Request within 30 days
- SCORE 60-69: Consider for annual touchpoint
- SCORE <60: Do NOT request (focus on improving relationship)

### Eligibility Signals
Positive Indicators:
- Satisfaction score ≥ 8/10
- Provided unsolicited positive feedback
- Project completed on time/budget
- Multiple successful projects
- Responds promptly to communications
- Referrals in the past
- Active engagement (meeting attendance, quick replies)

Negative Indicators:
- Outstanding payment issues
- Recent complaints or issues
- Project delays or problems
- Poor communication response
- Refused previous requests
- Less than 6 months since last request
- Marked as "do not contact"

### Request Type Selection
1. **Post-Project**: Use when project just completed successfully
2. **After Testimonial**: Use within 2 weeks of positive testimonial
3. **Annual Touchpoint**: Use for past clients with good history
4. **Closed-Lost**: Use only if relationship ended positively

## Communication Guidelines

1. **Ultra-Concise**: Maximum 125 words for email body
2. **Human Tone**: Conversational, not corporate
3. **Specific Context**: Reference actual shared experiences
4. **Clear Ask**: Make it easy to understand what you want
5. **Low Friction**: Make it simple to make introductions
6. **Gratitude**: Always thank them regardless of outcome

## Error Handling

- If email sending fails: Retry with exponential backoff (3 attempts)
- If contact is unsubscribed: Skip and mark as ineligible
- If referral is duplicate: Acknowledge and thank politely
- If incentive calculation fails: Request review before proceeding
- If lead import fails: Create manual task for review

Remember: Quality referrals come from genuine relationships. Build trust first, ask second.
"""
```

### Agent Structure

```python
# app/backend/src/agents/offboarding/referral_request/
├── __init__.py
├── agent.py              # ReferralRequestAgent class
├── tools.py              # Tool implementations
├── prompts.py            # System and task-specific prompts
├── schemas.py            # Pydantic models
├── exceptions.py         # Custom exceptions
└── analytics.py          # Analytics calculations
```

### Tools Implementation

#### 1. check_referral_elibility()
Evaluates if a contact is eligible for a referral request.

```python
async def check_referral_eligibility(
    self,
    contact_id: str,
    request_type: str = "auto",
) -> dict[str, Any]:
    """
    Check if contact is eligible for referral request.

    Returns:
        {
            "eligible": bool,
            "score": int,  # 0-100
            "reasons": list[str],
            "optimal_timing": str,
            "recommended_type": str,
            "risk_factors": list[str]
        }
    """
```

#### 2. calculate_eligibility_score()
Computes comprehensive eligibility score.

```python
async def calculate_eligibility_score(
    self,
    contact_id: str,
) -> dict[str, Any]:
    """
    Calculate eligibility score based on multiple factors.

    Scoring:
    - Satisfaction (0-30 points)
    - Relationship strength (0-25 points)
    - Recent positive interactions (0-20 points)
    - Project success history (0-15 points)
    - Communication quality (0-10 points)

    Returns score 0-100 with detailed breakdown.
    """
```

#### 3. personalize_referral_request()
Generates personalized referral request content.

```python
async def personalize_referral_request(
    self,
    contact_id: str,
    request_type: str,
    template_override: str | None = None,
    incentive: dict | None = None,
) -> dict[str, Any]:
    """
    Generate personalized referral request.

    Returns:
        {
            "subject": str,
            "body": str,
            "personalization_tokens": dict,
            "inclusion_reason": str,
            "tone": str,
            "predicted_effectiveness": float  # 0-1
        }
    """
```

#### 4. send_referral_request()
Handles actual sending of referral requests.

```python
async def send_referral_request(
    self,
    contact_id: str,
    content: dict[str, Any],
    provider: str = "instantly",
    send_immediately: bool = True,
) -> dict[str, Any]:
    """
    Send referral request via specified provider.

    Returns:
        {
            "message_id": str,
            "status": str,
            "sent_at": datetime,
            "delivery_details": dict,
            "tracking_id": str
        }
    """
```

#### 5. process_referral_response()
Handles incoming referral responses.

```python
async def process_referral_response(
    self,
    message_id: str,
    response_content: str,
    response_type: str = "email",
) -> dict[str, Any]:
    """
    Process and parse referral response.

    Extracts:
    - Referred contact information
    - Relationship context
    - Urgency indicators
    - Preferred contact methods

    Returns structured referral data.
    """
```

#### 6. create_referral_lead()
Converts referral into a lead in the system.

```python
async def create_referral_lead(
    self,
    referral_data: dict[str, Any],
    referrer_id: str,
    source_campaign: str | None = None,
) -> dict[str, Any]:
    """
    Convert referral into a lead in the CRM.

    - Create lead record
    - Set source as "referral"
    - Link to referrer
    - Trigger welcome sequence
    - Notify sales team

    Returns lead details and next steps.
    """
```

#### 7. calculate_incentive_payout()
Calculates and processes incentive payouts.

```python
async def calculate_incentive_payout(
    self,
    referral_id: str,
    conversion_value: float,
    incentive_config: dict | None = None,
) -> dict[str, Any]:
    """
    Calculate incentive payout for converted referral.

    Returns:
        {
            "payout_amount": float,
            "payout_type": str,
            "payout_date": datetime,
            "conditions": list[str],
            "approval_required": bool
        }
    """
```

#### 8. generate_referral_analytics()
Generates comprehensive referral analytics.

```python
async def generate_referral_analytics(
    self,
    period_type: str = "monthly",
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """
    Generate referral performance analytics.

    Includes:
    - Request metrics
    - Conversion funnels
    - ROI calculations
    - Top referrers
    - Best performing templates
    - Incentive effectiveness

    Returns comprehensive analytics report.
    """
```

### Error Handling

#### Custom Exceptions

```python
# exceptions.py
class ReferralRequestError(Exception):
    """Base exception for referral request operations."""
    pass

class IneligibleContactError(ReferralRequestError):
    """Contact does not meet eligibility criteria."""
    pass

class DuplicateReferralRequestError(ReferralRequestError):
    """Referral request already sent recently."""
    pass

class ReferralProcessingError(ReferralRequestError):
    """Error processing received referral."""
    pass

class IncentiveCalculationError(ReferralRequestError):
    """Error calculating incentive payout."""
    pass

class EmailDeliveryError(ReferralRequestError):
    """Failed to deliver referral request email."""
    pass
```

#### Retry Logic

```python
# Exponential backoff for transient failures
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
BACKOFF_MULTIPLIER = 2.0

async def send_with_retry(
    self,
    contact_id: str,
    content: dict[str, Any],
    attempt: int = 0,
) -> dict[str, Any]:
    """Send referral request with retry logic."""
    try:
        return await self.send_referral_request(contact_id, content)
    except EmailDeliveryError as e:
        if attempt < MAX_RETRIES:
            delay = INITIAL_RETRY_DELAY * (BACKOFF_MULTIPLIER ** attempt)
            await asyncio.sleep(delay)
            return await self.send_with_retry(contact_id, content, attempt + 1)
        raise
```

### Integration Points

#### Email Service Integration

```python
# Extending InstantlyClient for referral requests
class InstantlyReferralClient(InstantlyClient):
    async def send_referral_request(
        self,
        to_email: str,
        subject: str,
        body: str,
        campaign_name: str = "referral-requests",
    ) -> dict[str, Any]:
        """Send referral request with tracking."""

    async def track_referral_opens(
        self,
        message_ids: list[str],
    ) -> dict[str, Any]:
        """Track open rates for referral requests."""

    async def get_referral_responses(
        self,
        since: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch responses to referral requests."""
```

#### CRM Integration

```python
# Lead creation with referral attribution
async def create_referral_lead(
    self,
    referral_data: dict,
    referrer_id: str,
) -> dict[str, Any]:
    """Create lead from referral with proper attribution."""
    lead = {
        "first_name": referral_data["referred_first_name"],
        "last_name": referral_data["referred_last_name"],
        "email": referral_data["referred_email"],
        "source": "referral",
        "source_campaign": f"referral-{referrer_id}",
        "custom_fields": {
            "referral_source": referrer_id,
            "referral_context": referral_data["relationship_description"],
            "referral_urgency": referral_data["urgency_level"],
        }
    }
    return await self.crm_client.create_lead(lead)
```

---

## Testing Strategy

### Unit Tests

```python
# __tests__/unit/agents/test_referral_request_agent.py
class TestReferralRequestAgent:
    def test_eligibility_scoring_happy_path(self):
        """Test perfect eligibility scoring."""

    def test_eligibility_scoring_unsatisfied_client(self):
        """Test low score for unsatisfied client."""

    def test_eligibility_scoring_recent_request(self):
        """Test ineligibility due to recent request."""

    def test_personalization_template_rendering(self):
        """Test template personalization."""

    def test_referral_extraction_from_response(self):
        """Test parsing referral from email response."""

    def test_incentive_calculation_cash_bonus(self):
        """Test cash bonus incentive calculation."""

    def test_incentive_calculation_percentage(self):
        """Test percentage incentive calculation."""
```

### Integration Tests

```python
# __tests__/integration/test_referral_request_integration.py
class TestReferralRequestIntegration:
    async def test_end_to_end_referral_workflow(self):
        """Test complete referral request to lead conversion."""

    async def test_email_delivery_tracking(self):
        """Test email send and open tracking."""

    async def test_duplicate_request_prevention(self):
        """Test prevention of duplicate requests."""

    async def test_referral_lead_attribution(self):
        """Test referral lead source attribution."""
```

### Performance Tests

```python
# __tests__/performance/test_referral_request_performance.py
class TestReferralRequestPerformance:
    async def test_bulk_eligibility_checking(self):
        """Test checking eligibility for 1000 contacts."""

    async def test_concurrent_request_sending(self):
        """Test sending 100 requests concurrently."""
```

---

## Monitoring & Analytics

### Key Metrics

1. **Request Metrics**
   - Request volume by type
   - Delivery rate
   - Open rate
   - Reply rate

2. **Referral Metrics**
   - Referrals per request
   - Referral quality score
   - Conversion rate
   - Time to conversion

3. **Financial Metrics**
   - Cost per acquisition
   - Referral ROI
   - Average deal value
   - Payout percentage

4. **Agent Performance**
   - Eligibility accuracy
   - Personalization effectiveness
   - Error rates
   - Processing time

### Dashboards

1. **Real-time Monitoring**
   - Active requests
   - Recent referrals
   - Processing errors
   - Service health

2. **Weekly Reports**
   - Request performance
   - Referral pipeline
   - Conversion tracking
   - ROI analysis

3. **Monthly Reviews**
   - Program effectiveness
   - Top referrers
   - Best practices
   - Optimization opportunities

---

## Security & Compliance

### Data Protection

1. **Consent Management**
   - Track consent for referral requests
   - Honor opt-out requests
   - Maintain do-not-contact list

2. **Privacy Controls**
   - Anonymize analytics data
   - Secure referral information
   - GDPR compliance

3. **Rate Limiting**
   - Maximum requests per contact per period
   - Daily sending limits
   - Provider rate limit respect

### Audit Trail

```sql
CREATE TABLE referral_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action_type VARCHAR(50) NOT NULL,
    actor_type VARCHAR(20) NOT NULL, -- 'agent', 'user', 'system'
    actor_id UUID,
    target_type VARCHAR(50) NOT NULL, -- 'contact', 'referral', 'payout'
    target_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT
);
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- Database schema and migrations
- Base agent implementation
- Basic eligibility checking
- Email service integration

### Phase 2: Referral Processing (Week 2)
- Response parsing and processing
- Lead creation workflow
- Referral status tracking
- Basic analytics

### Phase 3: Incentives & Automation (Week 3)
- Incentive calculation engine
- Payout processing
- Automated request triggering
- Advanced personalization

### Phase 4: Analytics & Optimization (Week 4)
- Comprehensive analytics
- Performance dashboards
- A/B testing for templates
- ROI tracking

### Phase 5: Testing & Deployment (Week 5)
- Complete test suite
- Performance optimization
- Security review
- Production deployment

---

## Success Criteria

1. **Functional Requirements**
   - [ ] 95% email delivery rate
   - [ ] 40%+ open rate on referral requests
   - [ ] 15%+ reply rate
   - [ ] 5%+ referral-to-lead conversion
   - [ ] Sub-5 minute processing time

2. **Business Requirements**
   - [ ] 3:1 minimum ROI on incentive program
   - [ ] 20% of new leads from referrals within 6 months
   - [ ] 60% reduction in manual referral tracking

3. **Technical Requirements**
   - [ ] 99.9% uptime
   - [ ] <100ms response time for API calls
   - [ ] Zero data loss incidents
   - [ ] Complete audit trail

---

## Future Enhancements

1. **AI Improvements**
   - Predictive referral scoring
   - Advanced personalization using ML
   - Optimal timing prediction
   - Natural language response processing

2. **Channel Expansion**
   - Social media referral requests
   - In-app referral prompts
   - SMS referral captures
   - Voice referral processing

3. **Advanced Features**
   - Referral program gamification
   - Tiered incentive structures
   - Referral network mapping
   - Automated thank you gifts

4. **Integrations**
   - Calendar integration for referral meetings
   - Slack/Teams notifications
   - CRM bi-directional sync
   - Accounting software integration

---

*This specification provides a complete roadmap for implementing a sophisticated referral request system that will drive significant growth through strategic relationship leveraging.*
