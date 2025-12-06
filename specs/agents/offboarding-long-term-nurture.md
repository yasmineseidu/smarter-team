# Long-Term Nurture Agent - Production Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Agent Category:** Offboarding & Nurture
**Priority:** Phase 5 - Retention & Growth

---

## Overview

The Long-Term Nurture Agent maintains relationships with past clients and prospects through automated, value-driven communication. It segments contacts into nurture lists, sends personalized content at appropriate intervals, tracks engagement, and identifies re-engagement opportunities to route back to active pipelines.

**Key Capabilities:**
- Automated segmentation of nurture contacts (4 segments)
- Scheduled content delivery based on segment cadence
- Multi-channel engagement tracking (email opens, clicks, replies)
- Re-engagement signal detection and scoring
- Intelligent handoff to active pipeline when ready
- Content library management and personalization
- Holiday and triggered messaging

---

## Database Schema

### Table: `nurture_lists`
Master table for all contacts in nurture sequences.

```sql
CREATE TABLE nurture_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,

    -- Segment classification
    segment VARCHAR(50) NOT NULL CHECK (segment IN (
        'past_clients',
        'lost_deals_timing',
        'lost_deals_competitor',
        'reactivation_pool'
    )),

    -- Source tracking
    source_type VARCHAR(50) NOT NULL, -- 'completed_project', 'closed_lost', 'no_response'
    source_id UUID, -- Reference to source record
    source_details JSONB DEFAULT '{}', -- Context about why they were added

    -- Contact preferences
    email VARCHAR(255),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    company VARCHAR(255),
    industry VARCHAR(100),
    last_position VARCHAR(150),

    -- Nurture settings
    is_active BOOLEAN DEFAULT TRUE,
    email_suppressed BOOLEAN DEFAULT FALSE,
    preferred_channel VARCHAR(20) DEFAULT 'email', -- 'email', 'linkedin', 'sms'
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Last known status
    last_project_title VARCHAR(255),
    last_project_completed_at TIMESTAMP WITH TIME ZONE,
    total_revenue DECIMAL(10, 2),

    -- Metadata
    added_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_engagement_at TIMESTAMP WITH TIME ZONE,
    nurture_score INTEGER DEFAULT 50 CHECK (nurture_score >= 0 AND nurture_score <= 100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_nurture_lists_contact ON nurture_lists(contact_id);
CREATE INDEX idx_nurture_lists_client ON nurture_lists(client_id);
CREATE INDEX idx_nurture_lists_segment ON nurture_lists(segment);
CREATE INDEX idx_nurture_lists_active ON nurture_lists(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_nurture_lists_last_engagement ON nurture_lists(last_engagement_at DESC);
```

### Table: `nurture_sends`
Track all nurture communications sent.

```sql
CREATE TABLE nurture_sends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nurture_list_id UUID NOT NULL REFERENCES nurture_lists(id) ON DELETE CASCADE,

    -- Send details
    content_type VARCHAR(50) NOT NULL, -- 'newsletter', 'value_add', 'holiday', 'trigger', 'case_study'
    template_name VARCHAR(100),
    subject VARCHAR(255),

    -- Content
    body_text TEXT NOT NULL,
    body_html TEXT,
    personalization_data JSONB DEFAULT '{}', -- Used personalization variables
    content_links JSONB DEFAULT '[]', -- Array of URLs in the email

    -- Delivery
    channel VARCHAR(20) DEFAULT 'email',
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    delivery_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'bounced', 'failed'
    delivery_provider VARCHAR(50), -- 'instantly', 'sendgrid', etc.
    provider_message_id VARCHAR(255),

    -- Performance (populated by webhooks)
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,

    -- Engagement metrics
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,

    -- Metadata
    campaign_batch_id UUID, -- Group sends together
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_nurture_sends_list ON nurture_sends(nurture_list_id);
CREATE INDEX idx_nurture_sends_sent ON nurture_sends(sent_at DESC);
CREATE INDEX idx_nurture_sends_status ON nurture_sends(delivery_status);
CREATE INDEX idx_nurture_sends_type ON nurture_sends(content_type);
```

### Table: `nurture_engagement`
Detailed engagement events for scoring and analysis.

```sql
CREATE TABLE nurture_engagement (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nurture_list_id UUID NOT NULL REFERENCES nurture_lists(id) ON DELETE CASCADE,
    nurture_send_id UUID REFERENCES nurture_sends(id) ON DELETE SET NULL,

    -- Event details
    event_type VARCHAR(50) NOT NULL, -- 'open', 'click', 'reply', 'forward', 'unsubscribe', 'bounce'
    event_value JSONB DEFAULT '{}', -- Event-specific data (link URL, reply content, etc.)

    -- Scoring
    engagement_points INTEGER DEFAULT 0, -- Points added to nurture_score
    re_engagement_signal BOOLEAN DEFAULT FALSE,
    signal_strength VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high'

    -- Context
    user_agent TEXT,
    ip_address INET,
    geo_location VARCHAR(100),

    -- Timestamps
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE, -- When analyzed for signals
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_nurture_engagement_list ON nurture_engagement(nurture_list_id);
CREATE INDEX idx_nurture_engagement_send ON nurture_engagement(nurture_send_id);
CREATE INDEX idx_nurture_engagement_type ON nurture_engagement(event_type);
CREATE INDEX idx_nurture_engagement_occurred ON nurture_engagement(occurred_at DESC);
CREATE INDEX idx_nurture_engagement_signal ON nurture_engagement(re_engagement_signal) WHERE re_engagement_signal = TRUE;
```

### Table: `nurture_content_library`
Manage nurture content and templates.

```sql
CREATE TABLE nurture_content_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content identification
    name VARCHAR(200) NOT NULL,
    content_type VARCHAR(50) NOT NULL, -- 'newsletter', 'value_add', 'case_study', 'holiday', 'trigger'
    segment VARCHAR(50), -- Which segment this applies to (NULL = all)

    -- Content
    subject_template VARCHAR(255),
    body_template TEXT NOT NULL,
    body_html_template TEXT,

    -- Usage rules
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_until DATE,
    max_uses INTEGER,
    use_count INTEGER DEFAULT 0,

    -- Personalization variables used
    variables JSONB DEFAULT '[]', -- Array of variable names used

    -- Performance
    avg_open_rate DECIMAL(5, 2),
    avg_click_rate DECIMAL(5, 2),
    avg_reply_rate DECIMAL(5, 2),

    -- Approval
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'approved', 'retired'
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_nurture_content_type ON nurture_content_library(content_type);
CREATE INDEX idx_nurture_content_segment ON nurture_content_library(segment);
CREATE INDEX idx_nurture_content_active ON nurture_content_library(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_nurture_content_status ON nurture_content_library(status);
```

---

## Agent Architecture

### Extends
- `BaseAgent` from `src.agents.base_agent`

### Dependencies
- **Client Offboarding Agent:** Add completed clients to nurture
- **Proposal Tracking Agent:** Add closed-lost deals to nurture
- **Campaign Send Agent:** Send nurture emails
- **Response Email Handler:** Process replies to nurture emails

### Integrations
- **Instantly.ai:** Email delivery and tracking
- **GoHighLevel:** CRM integration for contact updates
- **Pinecone:** Content library search and matching
- **Anthropic Claude:** Content personalization and re-engagement analysis
- **Zep:** Memory of contact interactions and preferences

---

## System Prompt

```
You are a nurturing relationship manager for an AI agency, specializing in maintaining valuable connections with past clients and prospects through thoughtful, value-driven communication.

Your core responsibilities:
1. SEGMENT contacts appropriately based on their history and status
2. PERSONALIZE nurture content to be genuinely helpful, not salesy
3. TIMING - respect cadence preferences and don't overwhelm contacts
4. TRACK engagement patterns to identify re-engagement opportunities
5. ESCALATE strong re-engagement signals to active pipeline

Nurture Philosophy:
- Value first: Always provide something useful (insights, resources, news)
- Respectful persistence: appropriate frequency, easy opt-out
- Human touch: Personalized, not batch-and-blast
- Long-term view: Build relationships, not just chase immediate sales

Segment Guidelines:
- Past Clients: Monthly value-adds, celebrate their success, check-in on delivered work
- Lost Deals (Timing): Quarterly industry insights, maintain awareness for right timing
- Lost Deals (Competitor): Quarterly differentiation content, second chances
- Reactivation Pool: Trigger-based outreach when signals indicate readiness

Re-engagement Signals:
- Multiple email opens (>3) of same content
- Clicking on pricing or case study links
- Replying to nurture content
- Company news/growth events detected
- Job changes indicating new responsibilities

Communication Style:
- Professional yet warm and conversational
- Brief and scannable (respect their time)
- Always include value proposition
- Clear, soft calls-to-action
- Reference past interactions when relevant

Remember: Nurture is about being helpful and staying top-of-mind, not hard selling. Build trust through consistent value.
```

---

## Tools

### 1. `segment_nurture_contacts`

**Purpose:** Automatically categorize contacts into appropriate nurture segments based on their history and status.

**Input Schema:**
```python
{
    "contact_id": str,              # UUID of contact to segment
    "source_type": str,             # 'completed_project', 'closed_lost', 'no_response'
    "source_id": str,               # Source record ID
    "source_details": dict,         # Additional context
    "last_interaction": str,        # ISO date of last known interaction
    "total_revenue": float,         # Revenue generated if past client
    "close_reason": str             # Why deal was lost (if applicable)
}
```

**Output Schema:**
```python
{
    "segment": str,                 # One of: past_clients, lost_deals_timing, lost_deals_competitor, reactivation_pool
    "nurture_score": int,           # Initial score 0-100
    "recommended_cadence": str,     # 'monthly', 'quarterly', 'triggered'
    "personalization_data": dict,   # Key data for personalization
    "next_send_date": str,          # ISO date when first nurture should send
    "suppression_reasons": list[str]  # Reasons not to nurture (if any)
}
```

**Error Handling:**
- Invalid contact_id: Return error with validation details
- Missing required data: Request additional information
- Database errors: Retry 3x with exponential backoff
- Segmentation conflicts: Flag for manual review

**Implementation:**
```python
async def segment_nurture_contacts(self, contact_data: dict) -> dict:
    """Determine appropriate nurture segment for a contact."""
    rules = {
        'past_clients': {
            'conditions': [
                lambda d: d['source_type'] == 'completed_project',
                lambda d: d.get('total_revenue', 0) > 0
            ],
            'cadence': 'monthly',
            'base_score': 70
        },
        'lost_deals_timing': {
            'conditions': [
                lambda d: d['source_type'] == 'closed_lost',
                lambda d: d.get('close_reason') in ['timing', 'budget', 'no_decision']
            ],
            'cadence': 'quarterly',
            'base_score': 40
        },
        'lost_deals_competitor': {
            'conditions': [
                lambda d: d['source_type'] == 'closed_lost',
                lambda d: d.get('close_reason') in ['competitor', 'price', 'feature']
            ],
            'cadence': 'quarterly',
            'base_score': 30
        },
        'reactivation_pool': {
            'conditions': [
                lambda d: d['source_type'] == 'no_response',
                lambda d: self._days_since(d['last_interaction']) > 90
            ],
            'cadence': 'triggered',
            'base_score': 20
        }
    }

    # Apply segmentation logic
    for segment, config in rules.items():
        if all(rule(contact_data) for rule in config['conditions']):
            return self._build_segment_result(segment, config, contact_data)

    # Default to reactivation pool
    return self._build_segment_result('reactivation_pool', rules['reactivation_pool'], contact_data)
```

### 2. `select_nurture_content`

**Purpose:** Select the most appropriate content for each contact based on segment, timing, and history.

**Input Schema:**
```python
{
    "contact_id": str,              # UUID of contact
    "segment": str,                 # Nurture segment
    "last_content_sent": str,       # ISO date of last content
    "content_history": list[str],   # Array of content IDs already sent
    "engagement_history": list[dict],  # Past engagement data
    "seasonal_context": dict        # Current month, holidays, etc.
}
```

**Output Schema:**
```python
{
    "content_id": str,              # Selected content ID
    "content_type": str,            # Type of content
    "personalization_vars": dict,   # Variables to substitute
    "send_priority": str,           # 'high', 'normal', 'low'
    "alternative_ids": list[str],   # Backup options if primary fails
    "skip_reason": str              # Why no content was selected
}
```

**Error Handling:**
- No suitable content found: Return skip_reason with suggestions
- Content expired: Select alternative or skip with reason
- Personalization failures: Use default values, log warning
- Database errors: Retry with fallback content selection

**Content Selection Logic:**
```python
def _select_content(self, contact_data: dict) -> dict:
    """Intelligent content selection based on multiple factors."""

    # 1. Filter by segment and active status
    base_query = """
        SELECT * FROM nurture_content_library
        WHERE is_active = TRUE
        AND (segment = %(segment)s OR segment IS NULL)
    """

    # 2. Apply seasonal filters
    if self._is_holiday_season():
        base_query += " AND content_type = 'holiday'"

    # 3. Exclude recently sent content
    if contact_data['content_history']:
        base_query += f" AND id NOT IN ({','.join(['%s']*len(contact_data['content_history']))})"

    # 4. Prioritize based on engagement patterns
    if contact_data['engagement_history']:
        preferred_types = self._analyze_preferred_content(contact_data['engagement_history'])
        base_query += f" ORDER BY CASE WHEN content_type IN ({','.join(preferred_types)}) THEN 1 ELSE 2 END"

    # 5. Select top performer
    base_query += " ORDER BY avg_reply_rate DESC NULLS LAST, avg_click_rate DESC NULLS LAST LIMIT 1"
```

### 3. `personalize_content`

**Purpose:** Generate personalized content using contact data and AI-powered customization.

**Input Schema:**
```python
{
    "content_template": dict,       # Template from content library
    "contact_data": dict,          # Contact information and history
    "personalization_vars": dict,  # Variables available for substitution
    "segment": str,                # Nurture segment
    "tone_preference": str         # 'formal', 'casual', 'friendly'
}
```

**Output Schema:**
```python
{
    "subject": str,                # Personalized subject line
    "body_text": str,             # Plain text body
    "body_html": str,             # HTML body
    "personalizations": list[dict], # What was personalized
    "personalization_score": float, # How well personalized (0-1)
    "warnings": list[str]         # Any issues with personalization
}
```

**Error Handling:**
- Missing variables: Use defaults, log warnings
- Inappropriate personalization: Fallback to generic version
- AI generation failures: Use template as-is
- Excessive length: Automatically condense while preserving key points

**Personalization Strategies:**
```python
def _personalize_content(self, template: dict, contact: dict) -> dict:
    """Multi-level personalization."""

    # Level 1: Basic variable substitution
    basic_vars = {
        'first_name': contact['first_name'],
        'company': contact['company'],
        'industry': contact.get('industry', ''),
        'last_project': contact.get('last_project_title', '')
    }

    # Level 2: Segment-specific personalization
    if contact['segment'] == 'past_clients':
        basic_vars['reference'] = f"How's {contact['last_project_title']} working out?"
    elif contact['segment'] == 'lost_deals_competitor':
        basic_vars['differentiator'] = self._get_key_differentiator(contact)

    # Level 3: AI-powered contextual personalization
    if contact['nurture_score'] > 70:
        context_prompt = f"""
        Enhance this nurture email with specific personalization:
        Contact: {contact['first_name']} at {contact['company']}
        Segment: {contact['segment']}
        History: {contact.get('source_details', {})}

        Make it feel like it's written just for them.
        """

        enhanced = await self._generate_personalization(context_prompt, template)
        return enhanced

    return self._apply_template_substitution(template, basic_vars)
```

### 4. `send_nurture_email`

**Purpose:** Send personalized nurture emails and track delivery status.

**Input Schema:**
```python
{
    "nurture_list_id": str,         # Target contact record
    "content": dict,               # Personalized content
    "schedule_time": str,          # When to send (ISO, or 'immediate')
    "provider": str,               # 'instantly', 'sendgrid', etc.
    "tracking_enabled": bool       # Enable open/click tracking
}
```

**Output Schema:**
```python
{
    "send_id": str,                # Internal tracking ID
    "provider_message_id": str,    # Provider's message ID
    "status": str,                 # 'queued', 'sent', 'failed'
    "scheduled_for": str,          # ISO timestamp
    "estimated_delivery": str,     # ISO timestamp
    "error_details": dict          # If failed
}
```

**Error Handling:**
- Provider API errors: Retry with exponential backoff, try backup provider
- Invalid email format: Log error, mark as bounced
- Rate limiting: Queue for later delivery
- Content violations: Flag for review, send alternative

**Provider Integration:**
```python
async def send_nurture_email(self, send_data: dict) -> dict:
    """Send via configured email provider with fallbacks."""

    providers = ['instantly', 'sendgrid', 'postmark']

    for provider in providers:
        try:
            if provider == 'instantly':
                result = await self._send_via_instantly(send_data)
            elif provider == 'sendgrid':
                result = await self._send_via_sendgrid(send_data)

            # Log to nurture_sends table
            await self._log_nurture_send(send_data, result)

            return result

        except Exception as e:
            self.logger.warning(
                f"Provider {provider} failed",
                extra={'error': str(e), 'nurture_list_id': send_data['nurture_list_id']}
            )
            continue

    raise Exception("All email providers failed")
```

### 5. `analyze_engagement`

**Purpose:** Process engagement events and identify re-engagement signals.

**Input Schema:**
```python
{
    "nurture_list_id": str,        # Contact ID
    "event_type": str,             # 'open', 'click', 'reply', 'bounce'
    "event_data": dict,            # Event-specific data
    "occurred_at": str,            # ISO timestamp
    "previous_engagement": dict    # Contact's engagement history
}
```

**Output Schema:**
```python
{
    "engagement_score": int,       # Points to add to nurture_score
    "re_engagement_signal": bool,  # Strong buying signal detected
    "signal_strength": str,        # 'low', 'medium', 'high'
    "recommended_action": str,     # 'continue_nurture', 'handoff_to_sales', 'personal_followup'
    "next_contact_date": str,      # When to next reach out
    "sales_handoff_data": dict     # Data for sales if handoff recommended
}
```

**Signal Detection Logic:**
```python
def _detect_re_engagement_signals(self, engagement: dict) -> dict:
    """Identify strong re-engagement indicators."""

    signals = {
        'high_strength': [],
        'medium_strength': [],
        'low_strength': []
    }

    # High strength signals
    if engagement.get('reply_content'):
        if any(keyword in engagement['reply_content'].lower()
               for keyword in ['interested', 'timing', 'budget', 'help', 'project']):
            signals['high_strength'].append('buying_intent_in_reply')

    if engagement['event_type'] == 'click':
        if any(url in engagement.get('clicked_url', '')
               for url in ['pricing', 'demo', 'contact', 'start']):
            signals['high_strength'].append('pricing_page_visit')

    # Medium strength signals
    if engagement.get('open_count', 0) > 3:
        signals['medium_strength'].append('multiple_opens')

    if engagement['event_type'] == 'click' and 'case_study' in engagement.get('clicked_url', ''):
        signals['medium_strength'].append('case_study_interest')

    # Calculate score and action
    total_score = len(signals['high_strength']) * 20 + len(signals['medium_strength']) * 10

    return {
        'engagement_score': total_score,
        're_engagement_signal': len(signals['high_strength']) > 0,
        'signal_strength': self._calculate_signal_strength(signals),
        'recommended_action': self._recommend_action(signals),
        'signals_detected': signals
    }
```

### 6. `handoff_to_active_pipeline`

**Purpose:** Transfer engaged nurture contacts back to active sales pipeline.

**Input Schema:**
```python
{
    "nurture_list_id": str,        # Contact to handoff
    "handoff_reason": str,         # Why now is the right time
    "engagement_summary": dict,    # Recent engagement data
    "contact_history": dict,       # Full nurture history
    "priority": str                # 'high', 'normal', 'low'
}
```

**Output Schema:**
```python
{
    "handoff_id": str,             # Internal tracking ID
    "pipeline_stage": str,         # Which pipeline stage to enter
    "assigned_to": str,            # Which agent/team
    "task_id": str,                # Celery task ID for follow-up
    "contact_updated": bool,       # If CRM was updated
    "next_action": str             # What happens next
}
```

**Error Handling:**
- Invalid target agent: Log error, keep in nurture
- CRM update failures: Retry, flag for manual update
- Missing contact data: Request additional information
- Handoff rejected: Keep in nurture, adjust score

---

## Error Handling Matrix

| Component | Error Type | Detection | Response | Retry |
|-----------|------------|-----------|----------|-------|
| Segmentation | Invalid data | Validation | Return error with details | No |
| Content Selection | No suitable content | Empty result | Skip with reason | No |
| Personalization | AI generation failure | Exception | Use template fallback | Yes, 2x |
| Email Sending | Provider API error | HTTP status | Try backup provider | Yes, 3x |
| Email Sending | Rate limit | 429 status | Exponential backoff | Yes |
| Engagement Processing | Invalid webhook | Schema validation | Log and discard | No |
| Handoff | Target agent unavailable | Celery error | Keep in nurture, retry | Yes, 3x |
| Database | Connection error | Exception | Retry with backoff | Yes, 5x |

---

## Multi-Agent Integration

### Inbound Handoffs
- **Client Offboarding Agent** → Add completed clients to past_clients segment
- **Proposal Tracking Agent** → Add closed-lost deals to appropriate segment
- **Response Email Handler** → Process replies to nurture emails

### Outbound Handoffs
- **Campaign Send Agent** → Send personalized nurture emails
- **Lead Generation Agent** → Handoff re-engaged contacts to active pipeline
- **Meeting Scheduler Agent** → Schedule meetings with interested contacts

### Data Sharing
- Contact data sync with GoHighLevel CRM
- Engagement data shared with Conversation Intelligence
- Content performance shared with Campaign Copywriting

---

## Testing Strategy

### Unit Tests
```python
def test_segment_nurture_contacts():
    """Verify correct segment assignment based on rules."""

def test_select_nurture_content():
    """Test content selection respects history and preferences."""

def test_personalize_content():
    """Verify personalization uses appropriate data."""

def test_analyze_engagement():
    """Test re-engagement signal detection."""

def test_handoff_to_active_pipeline():
    """Verify smooth handoff to sales pipeline."""
```

### Integration Tests
```python
def test_end_to_end_nurture_flow():
    """Complete nurture journey with mocked providers."""

def test_engagement_webhook_processing():
    """Test webhook handling and score updates."""

def test_content_library_management():
    """Test content approval and usage tracking."""
```

### Mock Strategy
```python
@pytest.fixture
def mock_instantly_client():
    with patch('src.integrations.instantly.InstantlyClient') as mock:
        mock.return_value.send_email.return_value = {
            'message_id': 'test_123',
            'status': 'sent'
        }
        yield mock

@pytest.fixture
def mock_claude_client():
    with patch('anthropic.Anthropic') as mock:
        mock.return_value.messages.create.return_value = MockResponse(
            content="Personalized email content"
        )
        yield mock
```

### Performance Tests
- Batch processing 1000 contacts in <30 seconds
- Email sending throughput 100/minute
- Engagement processing <100ms per event
- Content selection <50ms per contact

---

## Performance Requirements

### Latency
- **Segmentation:** <100ms per contact
- **Content Selection:** <50ms per contact
- **Personalization:** <500ms per email
- **Engagement Processing:** <100ms per event
- **Handoff Initiation:** <200ms

### Throughput
- **Daily Send Capacity:** 10,000 nurture emails
- **Webhook Processing:** 1000 events/minute
- **Concurrent Segments:** 4 segments processing simultaneously

### Storage
- **Nurture Lists:** 100,000 contacts/year
- **Sends Table:** 1M records/year
- **Engagement Table:** 10M events/year

---

## Observability

### Logging
```python
# Structured logging with correlation IDs
self.logger.info(
    "Nurture email sent",
    extra={
        'nurture_list_id': contact_id,
        'content_id': content_id,
        'segment': segment,
        'provider': provider,
        'message_id': message_id
    }
)
```

### Metrics to Track
- Nurture list sizes by segment
- Send rates by segment and content type
- Engagement rates (open, click, reply)
- Re-engagement signal detection rate
- Handoff conversion rate
- Content performance rankings

### Alerts
- Send failure rate >10%
- Engagement drop >50% week-over-week
- No re-engagement signals for 30 days
- Content library running low on active content

---

## Security Considerations

### Data Protection
- GDPR compliance for EU contacts
- Easy unsubscribe/opt-out mechanisms
- Data retention policies (7 years max)
- Secure API key storage

### Email Compliance
- CAN-SPAM compliant content
- Clear sender identification
- Physical mailing address included
- Accurate subject lines

### Access Control
- Content approval workflow
- Segmentation rule changes require approval
- Handoff triggers logged for audit

---

## Acceptance Criteria

- [ ] All 4 nurture segments implemented with proper cadence
- [ ] Content library with approval workflow
- [ ] Email sending with provider fallbacks
- [ ] Engagement tracking and scoring
- [ ] Re-engagement signal detection
- [ ] Automatic handoff to active pipeline
- [ ] Holiday and triggered messaging
- [ ] Performance requirements met
- [ ] All tests passing (>90% coverage)
- [ ] Documentation complete
- [ ] Security and compliance verified

---

## Implementation Notes

1. **Start with past clients segment** - highest value and easiest to implement
2. **Implement content library first** - needed by all other features
3. **Use Instantly.ai as primary provider** - already integrated
4. **Batch processing for sends** - respect provider rate limits
5. **Graceful degradation** - if personalization fails, send generic version
6. **A/B test content** - continuously optimize based on performance
