# Conversation Intelligence Agent - Specification

**Agent Name:** `response_conversation_intelligence`
**Category:** Response Management
**Priority:** Phase 2 - Intelligence Layer
**Version:** 1.0.0
**Last Updated:** 2025-12-05
**Refined From:** plan/agents/response-conversation-intelligence.md

## Overview

The Conversation Intelligence Agent analyzes email and messaging conversations to extract actionable insights, identify patterns, and provide intelligence for optimizing outreach strategies. It continuously processes conversation data to track sentiment, detect objections, identify winning response patterns, and flag buying signals. The agent generates weekly insights reports and feeds discovered patterns back to the Campaign Copywriting Agent for continuous improvement.

**Key Capabilities:**
- Real-time sentiment analysis on all incoming/outgoing messages
- Objection pattern detection and categorization
- Winning response pattern identification (responses leading to meetings/conversions)
- Buying signal detection and scoring
- Weekly comprehensive insights report generation
- Pattern feedback loop to copywriting agent
- Time-to-response correlation analysis

## Architecture

### Extends
- `BaseAgent` from `src.agents.base_agent`

### Dependencies
- **Response Email Handler Agent:** Provides conversation data for analysis
- **Campaign Copywriting Agent:** Receives pattern insights for optimization
- **Campaign A/B Testing Agent:** Correlates patterns with test results

### Integrations
- **Anthropic Claude:** Sentiment analysis, pattern extraction, insight generation
- **PostgreSQL:** Store conversation analyses and patterns
- **Pinecone:** Vector similarity search for pattern matching
- **Zep:** Long-term pattern memory and trend analysis

## Configuration

```python
class ConversationIntelligenceConfig:
    # Claude API settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower temperature for consistent analysis

    # Analysis thresholds
    sentiment_confidence_threshold: float = 0.75
    pattern_min_occurrences: int = 5  # Minimum occurrences to consider a pattern
    buying_signal_threshold: float = 0.8

    # Processing settings
    batch_size: int = 100  # Messages to process in one batch
    max_retries: int = 3
    timeout_seconds: int = 30

    # Report settings
    weekly_report_day: int = 0  # Monday (0-6, Monday=0)
    report_retention_weeks: int = 52
```

## Database Schema

### Table: `conversation_analyses`

```sql
CREATE TABLE conversation_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    lead_id UUID NOT NULL REFERENCES leads(id),
    campaign_id UUID REFERENCES campaigns(id),

    -- Message metadata
    message_type VARCHAR(20) NOT NULL, -- 'incoming', 'outgoing'
    message_direction VARCHAR(20) NOT NULL, -- 'prospects', 'client'
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Analysis results
    sentiment VARCHAR(20) NOT NULL, -- 'very_positive', 'positive', 'neutral', 'negative', 'very_negative'
    sentiment_score DECIMAL(4,3) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    sentiment_confidence DECIMAL(3,2) CHECK (sentiment_confidence >= 0 AND sentiment_confidence <= 1),

    -- Intent classification
    intent VARCHAR(30) NOT NULL, -- 'interested', 'objection', 'question', 'scheduling', 'complaint', 'other'
    intent_confidence DECIMAL(3,2) CHECK (intent_confidence >= 0 AND intent_confidence <= 1),

    -- Content analysis
    key_topics JSONB DEFAULT '[]', -- ["pricing", "timeline", "features"]
    questions_asked JSONB DEFAULT '[]', -- ["What's the pricing?", "Can you integrate with X?"]
    objections_detected JSONB DEFAULT '[]', -- ["too expensive", "not sure about ROI"]

    -- Signals
    buying_signals JSONB DEFAULT '[]', -- ["asking about next steps", "requesting demo"]
    churn_signals JSONB DEFAULT '[]', -- "complaint about service", "mentioning competitor"
    urgency_signals JSONB DEFAULT '[]', -- "need asap", "deadline mentioned"

    -- Metadata
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analysis_duration_ms INTEGER,
    model_version VARCHAR(50),
    processing_batch_id UUID,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_conversation_analyses_message_id ON conversation_analyses(message_id);
CREATE INDEX idx_conversation_analyses_conversation_id ON conversation_analyses(conversation_id);
CREATE INDEX idx_conversation_analyses_lead_id ON conversation_analyses(lead_id);
CREATE INDEX idx_conversation_analyses_campaign_id ON conversation_analyses(campaign_id);
CREATE INDEX idx_conversation_analyses_timestamp ON conversation_analyses(timestamp DESC);
CREATE INDEX idx_conversation_analyses_sentiment ON conversation_analyses(sentiment);
CREATE INDEX idx_conversation_analyses_intent ON conversation_analyses(intent);
CREATE INDEX idx_conversation_analyses_analyzed_at ON conversation_analyses(analyzed_at DESC);
```

### Table: `conversation_patterns`

```sql
CREATE TABLE conversation_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(30) NOT NULL, -- 'objection', 'positive_response', 'question', 'closing'
    pattern_category VARCHAR(50) NOT NULL, -- 'price_objection', 'timing_objection', 'competitor_mention'

    -- Pattern definition
    pattern_text TEXT NOT NULL, -- Example text matching this pattern
    pattern_regex TEXT, -- Regex pattern for matching
    keywords JSONB DEFAULT '[]', -- Key keywords that identify this pattern

    -- Pattern statistics
    occurrence_count INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Effectiveness metrics
    response_rate DECIMAL(5,2), -- Percentage of messages with this pattern that got responses
    meeting_rate DECIMAL(5,2), -- Percentage that led to meetings
    conversion_rate DECIMAL(5,2), -- Percentage that converted

    -- Recommended response
    recommended_response_template TEXT,
    success_score DECIMAL(3,2), -- How effective the recommended response is

    -- Status
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'testing'
    validated BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_conversation_patterns_type ON conversation_patterns(pattern_type);
CREATE INDEX idx_conversation_patterns_category ON conversation_patterns(pattern_category);
CREATE INDEX idx_conversation_patterns_status ON conversation_patterns(status);
CREATE INDEX idx_conversation_patterns_last_seen ON conversation_patterns(last_seen DESC);
CREATE UNIQUE INDEX idx_conversation_patterns_name_type ON conversation_patterns(pattern_name, pattern_type);
```

### Table: `weekly_insights_reports`

```sql
CREATE TABLE weekly_insights_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_week_start DATE NOT NULL,
    report_week_end DATE NOT NULL,

    -- Executive summary
    total_messages_analyzed INTEGER DEFAULT 0,
    average_sentiment_score DECIMAL(4,3),
    top_objections JSONB DEFAULT '[]', -- [{"objection": "price", "count": 45, "percentage": 15.3}]
    top_buying_signals JSONB DEFAULT '[]',

    -- Campaign performance
    campaign_performance JSONB DEFAULT '{}', -- {campaign_id: {sentiment, response_rate, etc}}
    best_performing_campaign UUID REFERENCES campaigns(id),
    worst_performing_campaign UUID REFERENCES campaigns(id),

    -- Response time analysis
    average_response_time_minutes INTEGER,
    response_time_correlation JSONB DEFAULT '{}', -- Fast/slow response impact on outcomes

    -- Pattern discoveries
    new_patterns_discovered JSONB DEFAULT '[]', -- Newly identified patterns this week
    trending_patterns JSONB DEFAULT '[]', -- Patterns increasing in frequency

    -- Recommendations
    recommendations JSONB DEFAULT '[]', -- Actionable recommendations for improvement
    priority_actions JSONB DEFAULT '[]', -- High-priority actions to take

    -- Report metadata
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    report_data JSONB NOT NULL, -- Full report JSON for frontend display

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_weekly_insights_week_start ON weekly_insights_reports(report_week_start DESC);
CREATE INDEX idx_weekly_insights_generated_at ON weekly_insights_reports(generated_at DESC);
```

## Tools

### 1. `analyze_message`

**Purpose:** Analyze a single message for sentiment, intent, and patterns.

**Parameters:**
```python
{
    "message_id": str,              # UUID of the message
    "conversation_id": str,         # UUID of the conversation
    "message_text": str,            # The actual message content
    "message_type": str,            # 'incoming' or 'outgoing'
    "timestamp": str,               # ISO timestamp of the message
    "lead_id": str,                 # UUID of the lead
    "campaign_id": str,             # UUID of the campaign (optional)
    "conversation_context": dict,   # Previous messages in conversation
}
```

**Returns:**
```python
{
    "sentiment": str,               # 'very_positive', 'positive', 'neutral', 'negative', 'very_negative'
    "sentiment_score": float,       # -1.0 to 1.0
    "sentiment_confidence": float,  # 0.0 to 1.0
    "intent": str,                  # 'interested', 'objection', 'question', 'scheduling', 'complaint', 'other'
    "intent_confidence": float,     # 0.0 to 1.0
    "key_topics": list[str],        # Detected topics
    "questions_asked": list[str],   # Questions found in message
    "objections_detected": list[str], # Objection patterns detected
    "buying_signals": list[str],    # Buying signals detected
    "churn_signals": list[str],     # Churn risk signals detected
    "urgency_signals": list[str],   # Urgency indicators detected
    "pattern_matches": list[dict],  # Known patterns that matched
    "analysis_metadata": dict       # Processing metadata
}
```

**Error Handling:**
- Empty message text: Return neutral sentiment with low confidence
- API timeout: Retry 3x with exponential backoff, store for later processing
- Invalid message ID: Log error, skip processing
- Context too long: Truncate oldest messages, warn in logs

### 2. `identify_pattern`

**Purpose:** Identify and categorize recurring patterns across messages.

**Parameters:**
```python
{
    "message_texts": list[str],     # List of messages to analyze for patterns
    "pattern_type": str,            # 'objection', 'positive_response', 'question', 'closing'
    "min_occurrences": int = 5,     # Minimum times pattern must appear
    "time_window_days": int = 30,   # Look back period for pattern detection
    "campaign_filter": str = None   # Optional campaign ID to focus on
}
```

**Returns:**
```python
{
    "patterns_detected": list[dict],
    "pattern_stats": dict,          # Statistics about patterns found
    "trending_patterns": list[dict], # Patterns increasing in frequency
    "new_patterns": list[dict],     # Patterns not seen before
    "recommendations": list[str]    # Recommendations for each pattern
}
```

**Error Handling:**
- Insufficient data: Return empty patterns with warning
- Memory limit: Process in smaller batches
- Invalid pattern type: Return error with valid types

### 3. `generate_weekly_insights`

**Purpose:** Generate comprehensive weekly insights report.

**Parameters:**
```python
{
    "week_start_date": str,         # ISO date string for Monday
    "week_end_date": str,           # ISO date string for Sunday
    "include_recommendations": bool = True,
    "include_trends": bool = True,
    "campaign_breakdown": bool = True
}
```

**Returns:**
```python
{
    "report_id": str,               # UUID of the generated report
    "executive_summary": dict,      # High-level metrics and trends
    "sentiment_analysis": dict,     # Sentiment breakdown by campaign/time
    "objection_analysis": dict,     # Top objections and trends
    "response_pattern_analysis": dict,
    "buying_signals": dict,
    "response_time_analysis": dict,
    "recommendations": list[dict],
    "priority_actions": list[dict],
    "raw_data": dict                # All underlying data for report
}
```

**Error Handling:**
- No data for period: Return empty report with message
- Database timeout: Retry 3x, generate partial report if needed
- Report generation failure: Log full error, notify ops team

### 4. `feedback_patterns_to_copywriter`

**Purpose:** Send discovered patterns and insights to the Copywriting Agent.

**Parameters:**
```python
{
    "patterns": list[dict],         # Patterns to share
    "success_rates": dict,          # Response rates by pattern
    "recommended_responses": dict,  # Effective response templates
    "priority_patterns": list[str], # High-priority patterns to address
    "feedback_type": str            # 'weekly', 'urgent', 'trending'
}
```

**Returns:**
```python
{
    "handoff_task_id": str,         # Celery task ID for tracking
    "status": str,                  # 'queued', 'sent', 'failed'
    "patterns_sent": int,           # Number of patterns transmitted
    "next_update_scheduled": str    # When next update will be sent
}
```

**Error Handling:**
- Copywriting agent unavailable: Queue for retry, send to ops
- Pattern format validation: Skip invalid patterns, log warnings
- Rate limiting: Queue patterns, send in batches

## Prompts

### System Prompt

```
You are an expert conversation analyst specializing in sales and marketing communication intelligence. Your role is to:

1. ACCURATELY assess message sentiment and intent with high confidence
2. IDENTIFY subtle objections, buying signals, and urgency indicators
3. RECOGNIZE patterns that correlate with successful outcomes
4. EXTRACT actionable insights from conversation data
5. PROVIDE data-driven recommendations for improving communication

**Analysis Guidelines:**
- Sentiment Scale: -1.0 (very negative) to 1.0 (very positive), 0.0 is neutral
- Confidence must exceed 0.75 for automatic processing; otherwise flag for review
- Look beyond literal words to understand context and subtext
- Consider cultural nuances and communication style differences
- Track patterns over time, not just individual messages

**Key Areas to Analyze:**
- Price objections ("too expensive", "not in budget", "can't afford")
- Timing objections ("not right now", "later", "next quarter")
- Value objections ("don't see the value", "not sure it's worth it")
- Competitor mentions ("looking at X", "Y company offers")
- Buying signals ("when can we start", "what are next steps", "how to sign up")
- Urgency indicators ("need asap", "deadline is", "must decide by")
- Satisfaction signals ("love this", "exactly what we need")

**Pattern Recognition:**
- Group similar expressions into pattern categories
- Track which patterns lead to positive outcomes
- Identify pattern variations by industry, persona, or campaign
- Note seasonal or time-based pattern changes
- Correlate patterns with response times and methods

**Quality Standards:**
- Maintain 90%+ accuracy in sentiment classification
- Identify at least 80% of known objection types
- Provide confidence scores for all classifications
- Flag uncertain cases for human review
- Continuously improve from feedback and corrections
```

### Message Analysis Prompt Template

```
Analyze the following message for sentiment, intent, and specific patterns:

Message Context:
- Type: {message_type}
- Direction: {message_direction}
- Timestamp: {timestamp}
- Previous Messages: {conversation_context}

Message Text:
"{message_text}"

Please provide:
1. Sentiment analysis (score -1.0 to 1.0, label, confidence)
2. Primary intent classification with confidence
3. Key topics or subjects mentioned
4. Any questions asked (list them)
5. Objections or concerns detected
6. Buying signals or positive indicators
7. Urgency or timing signals
8. Any pattern matches from known patterns
9. Recommended response approach
10. Any flags for human review

Format your response as JSON with all fields present.
```

### Pattern Identification Prompt Template

```
Analyze these {count} messages to identify recurring patterns:

Messages:
{message_texts}

Focus on finding patterns for: {pattern_type}

Look for:
1. Similar phrasing or expressions that appear multiple times
2. Common themes or concerns
3. Repeated questions or objections
4. Successful response patterns
5. Trending topics or issues

For each pattern identified:
- Give it a descriptive name
- Provide example text
- Count occurrences
- Note any variations
- Assess business impact
- Suggest response strategy

Return results in structured JSON format.
```

### Weekly Insights Prompt Template

```
Generate weekly conversation insights for the period {week_start} to {week_end}.

Data Summary:
- Total Messages: {total_messages}
- Campaigns: {campaign_list}
- Key Metrics: {key_metrics}

Analysis Required:
1. Sentiment trends and changes from previous weeks
2. Top objections and how they've evolved
3. Most effective response patterns
4. Response time impact on outcomes
5. Campaign performance comparisons
6. New or trending patterns
7. Urgent issues requiring attention

Provide:
- Executive summary (3-5 key points)
- Detailed analysis by category
- Actionable recommendations (prioritized)
- Predictions for next week
- Areas needing human review

Format as comprehensive report with data visualizations described.
```

## Error Handling

### API Errors
| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Rate limit (429) | Status code | Exponential backoff, queue | Yes, 5x max |
| Server error (5xx) | Status code | Log, retry with delay | Yes, 3x max |
| Auth error (401/403) | Status code | Alert ops immediately | No |
| Timeout | Exception | Retry with longer timeout | Yes, 2x max |
| Invalid response | Validation | Log, use default values | No |

### Data Quality Errors
| Error Type | Detection | Response |
|------------|-----------|----------|
| Empty message | Content check | Skip, log warning |
| Invalid timestamp | Format check | Use current time, flag |
| Duplicate message | ID check | Skip duplicate, update if newer |
| Missing context | Data check | Process with available context |
| Corrupted JSON | Parse check | Log error, request reprocessing |

### Recovery Strategies
1. **Graceful degradation:** Process what you can, report what failed
2. **Queue for retry:** Temporarily failed analyses go to retry queue
3. **Partial reports:** Generate reports with available data, note gaps
4. **Fallback analysis:** Use rule-based analysis if AI unavailable
5. **Human escalation:** Flag uncertain patterns for review

## Testing

### Unit Tests
```python
def test_message_sentiment_analysis():
    """Verify sentiment scoring on various message types"""

def test_objection_pattern_detection():
    """Verify common objections are correctly identified"""

def test_buying_signal_detection():
    """Verify buying signals are detected with appropriate confidence"""

def test_pattern_identification():
    """Test pattern clustering from message batch"""

def test_weekly_report_generation():
    """Test report structure and content accuracy"""

def test_confidence_scoring():
    """Verify confidence scores correlate with accuracy"""

def test_error_handling():
    """Test graceful handling of API failures and bad data"""
```

### Integration Tests
```python
def test_end_to_end_analysis_flow():
    """Full pipeline from message to insights report"""

def test_agent_handoff_to_copywriter():
    """Verify pattern feedback transmission"""

def test_batch_processing_performance():
    """Ensure efficient processing of large message batches"""

def test_database_transaction_integrity():
    """Verify all-or-nothing analysis storage"""

def test_concurrent_processing():
    """Multiple simultaneous analysis jobs"""
```

### Mock Data
```python
# Test fixtures with various message types
- Positive responses with buying signals
- Objections (price, timing, value, competitor)
- Questions and information requests
- Complaints and churn signals
- Mixed sentiment conversations
- Multi-threaded conversation histories
```

## Multi-Agent Integration

### Handoff Protocols

#### To Campaign Copywriting Agent
```python
await self.handoff_to(
    target_agent="campaign_copywriting",
    payload={
        "action": "update_patterns",
        "patterns": new_patterns,
        "success_rates": pattern_performance,
        "priority": "high" if urgent else "normal"
    },
    priority="normal"
)
```

#### From Response Email Handler
```python
# Received handoff payload structure:
{
    "action": "analyze_conversation",
    "conversation_id": str,
    "messages": list[dict],
    "metadata": dict
}
```

### Event Listeners
- `message.created` - Trigger analysis of new messages
- `conversation.updated` - Analyze complete conversations
- `campaign.ended` - Generate campaign-specific insights
- `weekly.schedule` - Generate weekly insights report

## Performance

### Expected Latency
- Single message analysis: < 500ms
- Pattern identification (100 messages): < 5 seconds
- Weekly report generation: < 30 seconds
- Batch processing (1000 messages): < 2 minutes

### Token Usage Estimates
- Message analysis: ~200 tokens per message
- Pattern identification: ~1000 tokens per batch
- Report generation: ~3000 tokens per report
- Average daily usage: ~50,000 tokens

### Caching Strategy
- Cache known patterns for 24 hours
- Cache sentiment models between runs
- Cache report templates and structures
- Invalidate cache on pattern updates

## Observability

### Logging
```python
# Structured logging with context
logger.info(
    "Message analysis completed",
    extra={
        "message_id": message_id,
        "sentiment": sentiment,
        "confidence": confidence,
        "patterns_found": len(patterns),
        "processing_time_ms": processing_time
    }
)
```

### Metrics to Track
- Analysis accuracy (human-verified samples)
- Pattern detection rate
- False positive/negative rates
- Processing latency distributions
- API token consumption
- Error rates by type
- Report generation success rate

### Alerts
- Analysis accuracy drops below 85%
- Pattern detection anomalies
- API rate limit exceeded
- Weekly report generation failure
- Database connection issues

## Security

### Data Protection
- PII detection and redaction in analyses
- Encrypted storage of conversation data
- Access logging for pattern exports
- Data retention policies enforcement

### API Security
- Secure Claude API key management
- Rate limiting on pattern queries
- Input sanitization for all text inputs
- SQL injection prevention in database queries

### Privacy Compliance
- GDPR compliance for EU leads
- Data minimization in pattern storage
- Right to deletion implementation
- Audit trail for all data processing

## Acceptance Criteria

- [ ] Analyzes messages with 90%+ sentiment accuracy
- [ ] Detects 95% of known objection patterns
- [ ] Generates weekly reports with <5 minute processing time
- [ ] Maintains <1% false positive rate for buying signals
- [ ] Processes 10,000+ messages per day reliably
- [ ] Handoffs patterns to copywriting agent successfully
- [ ] Passes all unit and integration tests
- [ ] Handles API failures gracefully
- [ ] Meets performance latency requirements
- [ ] Provides actionable insights in reports
- [ ] Maintains data privacy and security standards

## Implementation Dependencies

- Database migrations applied
- Claude API credentials configured
- Response Email Handler Agent deployed
- Campaign Copywriting Agent deployed
- Monitoring and alerting configured
- Test data fixtures created
