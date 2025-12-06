# Reactivation Agent - Production Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Agent Category:** Offboarding & Nurture
**Priority:** Phase 6 - Multi-Channel & Advanced

---

## Overview

The Reactivation Agent monitors cold leads in nurture pools and detects trigger events that indicate renewed buying interest. It continuously scans for job changes, funding rounds, company growth, leadership changes, competitor mentions, and industry events to re-engage prospects at the optimal time with personalized outreach.

**Key Capabilities:**
- Multi-source trigger detection (LinkedIn, news APIs, job boards, intent data)
- Intelligent reactivation timing based on trigger type
- Personalized outreach generation with trigger-specific templates
- Integration with Long-Term Nurture, Company Research, and Campaign agents
- Comprehensive tracking of reactivation attempts and success metrics

---

## Database Schema

### Table: `reactivation_pools`
Stores different nurture pools for categorizing cold leads.

```sql
CREATE TABLE reactivation_pools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    pool_type VARCHAR(50) NOT NULL, -- 'lost_deals', 'cold_prospects', 'dormant_clients'
    criteria JSONB NOT NULL DEFAULT '{}', -- Pool-specific filters

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reactivation_pools_type ON reactivation_pools(pool_type);
CREATE INDEX idx_reactivation_pools_active ON reactivation_pools(is_active);
```

### Table: `reactivation_triggers`
Primary table for storing detected triggers and their metadata.

```sql
CREATE TABLE reactivation_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,

    -- Trigger details
    trigger_type VARCHAR(50) NOT NULL CHECK (trigger_type IN (
        'job_change', 'funding_round', 'company_growth', 'leadership_change',
        'competitor_mention', 'industry_event'
    )),
    trigger_source VARCHAR(100) NOT NULL, -- 'linkedin', 'news_api', 'crunchbase', 'job_board'

    -- Trigger data
    trigger_data JSONB NOT NULL DEFAULT '{}', -- Specific trigger information
    confidence_score INTEGER DEFAULT 50 CHECK (confidence_score >= 0 AND confidence_score <= 100),
    relevance_score INTEGER DEFAULT 50 CHECK (relevance_score >= 0 AND relevance_score <= 100),

    -- Timing
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    optimal_contact_date DATE, -- When to reach out based on trigger type

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'processing', 'contacted', 'converted', 'expired', 'ignored'
    )),

    -- Processing
    processed_at TIMESTAMP WITH TIME ZONE,
    campaign_id UUID REFERENCES campaigns(id),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reactivation_triggers_lead ON reactivation_triggers(lead_id);
CREATE INDEX idx_reactivation_triggers_company ON reactivation_triggers(company_id);
CREATE INDEX idx_reactivation_triggers_type ON reactivation_triggers(trigger_type);
CREATE INDEX idx_reactivation_triggers_status ON reactivation_triggers(status);
CREATE INDEX idx_reactivation_triggers_detected ON reactivation_triggers(detected_at DESC);
CREATE INDEX idx_reactivation_triggers_contact ON reactivation_triggers(optimal_contact_date)
    WHERE status = 'pending';
```

### Table: `reactivation_campaigns`
Tracks reactivation campaigns and their performance.

```sql
CREATE TABLE reactivation_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_id UUID NOT NULL REFERENCES reactivation_triggers(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Campaign details
    campaign_name VARCHAR(200) NOT NULL,
    template_used VARCHAR(100) NOT NULL,
    personalized_content TEXT NOT NULL,

    -- Execution
    sent_via VARCHAR(50), -- 'email', 'linkedin', 'sms', 'voice'
    sent_at TIMESTAMP WITH TIME ZONE,
    scheduled_for TIMESTAMP WITH TIME ZONE,

    -- Response tracking
    first_reply_at TIMESTAMP WITH TIME ZONE,
    reply_count INTEGER DEFAULT 0,
    positive_reply BOOLEAN,

    -- Conversion tracking
    meeting_booked BOOLEAN DEFAULT FALSE,
    meeting_date DATE,
    deal_won BOOLEAN DEFAULT FALSE,
    deal_value DECIMAL(12, 2),
    deal_date DATE,

    -- Metrics
    total_cost DECIMAL(10, 2) DEFAULT 0, -- Cost of reactivation effort

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reactivation_campaigns_trigger ON reactivation_campaigns(trigger_id);
CREATE INDEX idx_reactivation_campaigns_lead ON reactivation_campaigns(lead_id);
CREATE INDEX idx_reactivation_campaigns_sent ON reactivation_campaigns(sent_at DESC);
CREATE INDEX idx_reactivation_campaigns_conversion ON reactivation_campaigns(deal_won) WHERE deal_won = TRUE;
```

### Table: `reactivation_monitoring`
Configuration for monitoring sources and keywords.

```sql
CREATE TABLE reactivation_monitoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Monitoring configuration
    source_type VARCHAR(50) NOT NULL, -- 'linkedin', 'news_api', 'job_board'
    source_config JSONB NOT NULL DEFAULT '{}', -- API keys, search terms, etc.

    -- Keywords and patterns
    company_keywords TEXT[] DEFAULT '{}',
    person_keywords TEXT[] DEFAULT '{}',
    industry_keywords TEXT[] DEFAULT '{}',
    competitor_keywords TEXT[] DEFAULT '{}',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reactivation_monitoring_type ON reactivation_monitoring(source_type);
CREATE INDEX idx_reactivation_monitoring_active ON reactivation_monitoring(is_active);
```

---

## Agent Configuration

```python
class ReactivationAgentConfig:
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower temperature for consistent trigger detection
    max_retries: int = 3
    timeout_seconds: int = 60

    # Monitoring frequency
    scan_interval_hours: int = 6  # How often to scan for triggers

    # Trigger timing rules (days after trigger)
    job_change_delay: int = 45    # 30-60 days, use 45 as default
    funding_delay: int = 21       # 2-4 weeks, use 3 weeks
    growth_delay: int = 7         # Immediate during growth
    leadership_delay: int = 75    # 60-90 days, use 75 as default
    competitor_delay: int = 1     # Within 48 hours

    # Batch processing
    batch_size: int = 100         # Process triggers in batches
    daily_limit: int = 50         # Max reactivations per day
```

---

## Tools

### Tool: `monitor_linkedin_changes`
**Purpose:** Monitor LinkedIn for job changes and updates in target companies/contacts

**Input Schema:**
```python
class MonitorLinkedInInput(BaseModel):
    contact_ids: list[str] = Field(default=[], description="Specific contact IDs to monitor")
    company_ids: list[str] = Field(default=[], description="Company IDs to monitor")
    keywords: list[str] = Field(default=[], description="Keywords to search for")
    max_results: int = Field(default=100, ge=1, le=500, description="Maximum results to return")
```

**Output Schema:**
```python
class MonitorLinkedInOutput(BaseModel):
    triggers_found: list[dict]
    total_scanned: int
    api_calls_remaining: int
    next_cursor: str | None = None
```

**Error Handling:**
- Rate limit (429) → Exponential backoff, max 5 retries, wait 1-60 minutes
- Auth error (401/403) → Fail immediately, log security issue
- Timeout (504) → Retry with longer timeout, max 3 attempts
- Invalid response → Log error, continue with other contacts

---

### Tool: `scan_news_sources`
**Purpose:** Scan news APIs for funding rounds, leadership changes, and company growth

**Input Schema:**
```python
class ScanNewsInput(BaseModel):
    sources: list[str] = Field(default=["crunchbase", "techcrunch", "prnewswire"])
    keywords: list[str] = Field(default=[])
    date_range_days: int = Field(default=7, ge=1, le=30)
    max_articles: int = Field(default=200, ge=1, le=1000)
```

**Output Schema:**
```python
class ScanNewsOutput(BaseModel):
    articles_processed: int
    triggers_found: list[dict]
    companies_mentioned: list[dict]
    funding_events: list[dict]
    leadership_changes: list[dict]
```

**Error Handling:**
- API quota exceeded → Switch to backup source, log warning
- Invalid JSON response → Skip article, continue processing
- Network timeout → Retry 3x with exponential backoff
- Source unavailable → Mark as inactive, try next source

---

### Tool: `analyze_job_postings`
**Purpose:** Analyze job postings to detect company growth and expansion signals

**Input Schema:**
```python
class AnalyzeJobsInput(BaseModel):
    company_ids: list[str] = Field(description="Target companies to analyze")
    job_boards: list[str] = Field(default=["linkedin", "indeed", "company_careers"])
    lookback_days: int = Field(default=30, ge=1, le=90)
    hiring_threshold: int = Field(default=5, ge=1, description="Min new postings to signal growth")
```

**Output Schema:**
```python
class AnalyzeJobsOutput(BaseModel):
    growth_signals: list[dict]
    hiring_spikes: list[dict]
    new_locations: list[dict]
    department_expansion: list[dict]
```

**Error Handling:**
- Board rate limit → Rotate through boards, implement delays
- Parsing errors → Log problematic postings, skip
- Inconsistent data → Use confidence scoring, mark for review

---

### Tool: `generate_reactivation_content`
**Purpose:** Generate personalized reactivation outreach based on trigger type

**Input Schema:**
```python
class GenerateContentInput(BaseModel):
    lead_id: str = Field(..., description="Lead to reactivate")
    trigger: dict = Field(..., description="Trigger data including type and details")
    template_type: str = Field(..., description="Template to use")
    personalization_level: str = Field(default="high", enum=["low", "medium", "high"])
    tone: str = Field(default="professional", enum=["casual", "professional", "formal"])
```

**Output Schema:**
```python
class GenerateContentOutput(BaseModel):
    subject_line: str
    email_body: str
    personalization_notes: list[str]
    call_to_action: str
    follow_up_suggestions: list[str]
    confidence_score: int = Field(ge=0, le=100)
```

**Error Handling:**
- Insufficient data → Request more context, use generic template
- Content too long → Truncate, prioritize key points
- Inappropriate tone detected → Regenerate with stricter guidelines

---

### Tool: `schedule_reactivation`
**Purpose:** Schedule and execute reactivation campaigns

**Input Schema:**
```python
class ScheduleReactivationInput(BaseModel):
    trigger_id: str = Field(..., description="Trigger to act on")
    campaign_details: dict = Field(..., description="Campaign configuration")
    send_time: datetime = Field(..., description="When to send")
    channel: str = Field(..., enum=["email", "linkedin", "sms", "multi"])
    priority: str = Field(default="normal", enum=["low", "normal", "high", "urgent"])
```

**Output Schema:**
```python
class ScheduleReactivationOutput(BaseModel):
    campaign_id: str
    scheduled_time: datetime
    estimated_cost: Decimal
    delivery_status: str
    next_steps: list[str]
```

**Error Handling:**
- Duplicate campaign → Detect and merge with existing
- Lead unsubscribed → Skip, mark as do-not-contact
- Daily limit exceeded → Queue for next day
- Send failure → Retry with different channel

---

## Prompts

### System Prompt
```
You are a Reactivation Agent, specialized in identifying optimal moments to re-engage cold leads based on trigger events.

Your core responsibilities:
1. Monitor multiple sources for trigger events (job changes, funding, growth, leadership changes)
2. Assess trigger relevance and timing for each prospect
3. Generate personalized reactivation content that acknowledges the trigger
4. Coordinate with campaign agents for execution

Key principles:
- Timing is critical: Each trigger type has an optimal contact window
- Personalization drives success: Reference the specific trigger in outreach
- Quality over quantity: Focus on high-confidence, high-relevance triggers
- Respect preferences: Honor unsubscribes and communication preferences

When analyzing triggers:
- Verify the trigger's accuracy and relevance
- Consider the prospect's previous engagement history
- Assess the buying potential based on the trigger
- Calculate the optimal contact timing

When generating content:
- Reference the specific trigger that prompted reactivation
- Keep it concise and relevant to their new situation
- Provide clear value proposition for their current role/company
- Include a soft, contextually appropriate call-to-action

You have access to tools for monitoring, analysis, content generation, and scheduling. Use them systematically to maximize reactivation success rates.
```

### Trigger Detection Prompt Template
```
Analyze the following event for reactivation potential:

Event Type: {trigger_type}
Event Data: {trigger_data}
Lead Context: {lead_context}
Company Context: {company_context}

Evaluate:
1. Confidence: How certain are we this is a valid trigger? (0-100)
2. Relevance: How relevant is this trigger to our services? (0-100)
3. Urgency: How time-sensitive is this opportunity? (0-100)
4. Value: What's the potential deal value? (low/medium/high)

Determine:
- Optimal contact date (consider trigger type and best practices)
- Recommended outreach angle
- Personalization opportunities
- Required context for successful outreach

Respond with structured analysis in JSON format.
```

### Content Generation Prompt Template
```
Generate personalized reactivation outreach for:

Lead: {lead_name} at {company_name} as {title}
Trigger: {trigger_type} - {trigger_details}
Previous Context: {interaction_history}
Value Proposition: {service_value}

Requirements:
- Reference the trigger in the first 2 sentences
- Keep under 125 words for maximum readability
- Use {tone} tone
- Focus on their current situation, not our past conversation
- Include specific relevance to their new role/company

Generate:
1. Subject line (under 50 characters)
2. Email body (under 125 words)
3. Personalization notes (what we referenced)
4. Call to action (soft, appropriate for context)
5. Follow-up suggestions (if no response)

Ensure the message feels timely, relevant, and valuable to their current situation.
```

---

## Error Handling Matrix

| Error Type | Detection | Response | Retry | Alert |
|------------|-----------|----------|-------|-------|
| LinkedIn rate limit | HTTP 429 | Exponential backoff | Yes, 5x | No |
| News API quota exceeded | HTTP 403 | Switch to backup source | No | Yes |
| Invalid trigger data | Validation failure | Log and skip | No | No |
| Content generation fails | Model error | Use fallback template | Yes, 2x | No |
| Campaign scheduling fails | Database error | Retry, then manual review | Yes, 3x | Yes |
| Lead unsubscribed | Database flag | Skip, mark DNC | No | No |
| Daily limit exceeded | Counter check | Queue for next day | No | No |
| Duplicate trigger | Database constraint | Merge with existing | No | No |

### Recovery Strategies

1. **Graceful Degradation:** If premium sources fail, use free alternatives
2. **Batch Processing:** Queue failed items for retry in next batch
3. **Fallback Content:** Use generic reactivation templates if personalization fails
4. **Manual Review Queue:** Flag high-value failures for human review
5. **Circuit Breaker:** Temporarily disable failing sources after repeated failures

---

## Multi-Agent Integration

### Dependencies and Handoffs

1. **Long-Term Nurture Agent**
   - Provides pool of cold leads to monitor
   - Receives reactivated leads back for continued nurturing
   - Handoff format: `{lead_ids, pool_id, reason: "reactivation_opportunity"}`

2. **Company Research Agent**
   - Provides company context and intelligence
   - Validates trigger events with additional research
   - Handoff format: `{company_id, trigger_type, verification_request: true}`

3. **Campaign Agents**
   - Receives reactivation campaigns for execution
   - Reports back engagement and conversion metrics
   - Handoff format: `{campaign_details, priority: "reactivation"}`

4. **Intent Signal Agent**
   - Cross-references triggers with intent data
   - Prioritizes triggers based on buying signals
   - Handoff format: `{lead_id, intent_signals, priority_score}`

### Agent Communication Patterns

```python
# Receiving leads from Long-Term Nurture
async def receive_nurture_leads(self, payload: dict) -> dict:
    """Add leads to monitoring pool."""

# Validating triggers with Company Research
async def validate_trigger(self, payload: dict) -> dict:
    """Request verification of trigger data."""

# Handing off to Campaign agents
await self.handoff_to(
    target_agent="campaign_send",
    payload={
        "campaign_type": "reactivation",
        "trigger_id": trigger.id,
        "content": content,
        "priority": "high"
    },
    priority="high"
)
```

---

## Testing Strategy

### Unit Tests

```python
class TestReactivationAgent:
    @pytest.mark.asyncio
    async def test_detect_job_change_trigger(self):
        """Verify job change detection from LinkedIn data."""

    @pytest.mark.asyncio
    async def test_funding_round_analysis(self):
        """Test funding round signal extraction."""

    @pytest.mark.asyncio
    async def test_timing_calculation(self):
        """Verify optimal contact date calculation."""

    @pytest.mark.asyncio
    async def test_content_personalization(self):
        """Test personalized content generation."""

    def test_trigger_confidence_scoring(self):
        """Verify confidence score calculation."""

    def test_rate_limit_handling(self):
        """Test exponential backoff on rate limits."""
```

### Integration Tests

```python
class TestReactivationIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_job_change(self):
        """Complete flow from detection to campaign handoff."""

    @pytest.mark.asyncio
    async def test_cross_agent_coordination(self):
        """Test handoff with Company Research agent."""

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Verify batch trigger processing."""

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test recovery from API failures."""
```

### Mock Strategy

```python
@pytest.fixture
def mock_linkedin_client():
    with patch('src.integrations.linkedin.LinkedInClient') as mock:
        mock.return_value.search_changes.return_value = {
            "results": [{"trigger_type": "job_change", ...}]
        }
        yield mock

@pytest.fixture
def mock_news_api():
    with patch('src.integrations.news.NewsAPIClient') as mock:
        mock.return_value.search_articles.return_value = {
            "articles": [{"title": "Company raises $10M", ...}]
        }
        yield mock
```

---

## Performance Requirements

### Processing Targets
- **Latency:** < 5 seconds for trigger analysis
- **Throughput:** Process 1000 triggers per hour
- **Accuracy:** > 90% trigger detection precision
- **Coverage:** Monitor all active leads weekly

### Resource Limits
- **API Calls:** Respect all third-party rate limits
- **Database:** Optimize for batch inserts/updates
- **Memory:** < 1GB for processing batches
- **CPU:** < 50% utilization during scans

---

## Observability

### Metrics to Track
1. **Trigger Detection:**
   - Triggers detected per source
   - False positive rate
   - Detection latency

2. **Reactivation Performance:**
   - Reactivation success rate
   - Response rate by trigger type
   - Conversion rate by trigger type
   - Time to conversion

3. **Operational Metrics:**
   - API usage and costs
   - Processing errors
   - Daily reactivation volume
   - ROI of reactivation campaigns

### Logging Strategy

```python
# Structured logging with context
self.logger.info(
    "Trigger detected",
    extra={
        "trigger_type": "job_change",
        "lead_id": lead.id,
        "confidence": 85,
        "source": "linkedin",
        "processing_time_ms": 245
    }
)

self.logger.error(
    "Content generation failed",
    extra={
        "lead_id": lead.id,
        "trigger_id": trigger.id,
        "error": str(e),
        "fallback_used": True
    }
)
```

---

## Security Considerations

1. **API Key Management:**
   - Store all API keys in environment variables
   - Rotate keys regularly
   - Monitor for unauthorized usage

2. **Data Privacy:**
   - Respect GDPR and CCPA requirements
   - Honor opt-out requests immediately
   - Minimal data retention for failed triggers

3. **Rate Limit Protection:**
   - Implement client-side rate limiting
   - Queue requests during peak times
   - Fail gracefully when limits exceeded

---

## Acceptance Criteria

- [ ] Monitor all configured sources for trigger events
- [ ] Detect and classify 6 types of triggers with >90% accuracy
- [ ] Calculate optimal contact timing based on trigger type
- [ ] Generate personalized reactivation content for all trigger types
- [ ] Schedule and execute reactivation campaigns within limits
- [ ] Track all reactivation activities and outcomes
- [ ] Integrate with Long-Term Nurture, Company Research, and Campaign agents
- [ ] Handle all error scenarios with appropriate recovery
- [ ] Achieve >15% reactivation response rate
- [ ] Generate positive ROI on reactivation efforts
- [ ] Pass all unit and integration tests
- [ ] Comply with privacy regulations and rate limits
