# Response Email Handler Agent - Specification

## Overview

**Agent Name:** `response_email_handler`
**Category:** Response Management
**Priority:** Phase 1 - MVP Foundation
**Description:** Processes and responds to email replies with intelligent classification, automated drafting, and human-in-the-loop approval workflows.

## System Prompt

```
You are an expert email response handler for an AI agency specializing in intelligent, context-aware communication. Your role is to:

1. CLASSIFY incoming email replies accurately into categories (positive, negative, question, objection, out-of-office, unsubscribe, referral, wrong-person)
2. ANALYZE reply sentiment and intent to determine appropriate response tier (auto-send, approval, escalation)
3. DRAFT professional, concise, and helpful email responses that maintain brand voice
4. EXTRACT key information from replies (meeting preferences, objections, referrals, return dates)
5. LEVERAGE knowledge base effectively to provide accurate, consistent information
6. RECOGNIZE buying signals, churn risks, and escalation triggers

**Response Guidelines:**
- Keep responses under 125 characters when possible (ultra-concise, human-sounding)
- Match the recipient's tone and formality level
- Always provide value (answer questions, offer solutions, suggest next steps)
- For objections, acknowledge concerns before addressing them
- Use knowledge base for consistent pricing, process, and service information
- Never make commitments beyond your authority (escalate instead)

**Tone:** Professional yet approachable, helpful, non-pushy, solution-oriented

**Safety:**
- NEVER send responses without required approval tier authorization
- NEVER share pricing/commitments not in knowledge base
- ALWAYS escalate complaints, complex technical questions, or custom requests
- Flag any uncertain classifications for human review
```

## Agent Architecture

### Extends
- `BaseAgent` from `src.agents.base_agent`

### Dependencies
- **Knowledge Base Agent:** Query for FAQ answers and service information
- **Conversation Intelligence Agent:** Store conversation data for analysis (optional)
- **Meeting Scheduler Agent:** Handoff when meeting scheduling is needed

### Integrations
- **Instantly.ai:** Receive email reply webhooks, send responses
- **Slack/Telegram:** Send approval requests to human operators
- **Pinecone:** Query knowledge base via vector search
- **Anthropic Claude:** Classification, sentiment analysis, response drafting
- **Zep:** Store/retrieve conversation memory for context

## Tools

### 1. `classify_email_reply`

**Purpose:** Classify incoming email replies into categories and determine appropriate response tier.

**Parameters:**
```python
{
    "email_body": str,              # The reply email content
    "subject": str,                 # Email subject line
    "sender_email": str,            # Sender's email address
    "original_campaign_id": str,    # ID of the campaign this is replying to
    "conversation_history": list[dict],  # Previous messages in thread
}
```

**Returns:**
```python
{
    "category": str,  # One of: positive, negative, question, objection, out_of_office,
                      #         unsubscribe, referral, wrong_person, meeting_request
    "sentiment": str, # One of: very_positive, positive, neutral, negative, very_negative
    "intent": str,    # One of: interested, not_interested, needs_info, scheduling,
                      #         objection, complaint, other
    "response_tier": str,  # One of: auto_send, approval, escalation
    "confidence": float,   # 0.0 to 1.0
    "buying_signals": list[str],   # Detected buying signals
    "objections": list[str],       # Detected objections
    "key_points": list[str],       # Main points from the email
    "extracted_data": dict,        # Structured data (dates, contact info, etc.)
}
```

**Error Handling:**
- Invalid email format: Return error with "requires_manual_review" flag
- Low confidence (<0.7): Automatically set tier to "approval"
- Anthropic API errors: Retry 3x with exponential backoff, then escalate

### 2. `query_knowledge_base`

**Purpose:** Search knowledge base for relevant information to include in response.

**Parameters:**
```python
{
    "query": str,               # Question or topic to search for
    "category": str,            # Category filter (pricing, services, process, objections)
    "top_k": int = 3,          # Number of results to return
    "min_confidence": float = 0.7,  # Minimum similarity score
}
```

**Returns:**
```python
{
    "results": list[{
        "content": str,         # Knowledge base entry content
        "title": str,          # Entry title
        "category": str,       # Entry category
        "confidence": float,   # Similarity score
        "metadata": dict,      # Additional metadata
    }],
    "found_answer": bool,      # Whether a confident answer was found
}
```

**Error Handling:**
- Pinecone connection errors: Fallback to cached KB entries, log error
- No results found: Return empty list with found_answer=False
- Query too broad: Request more specific query

### 3. `draft_email_response`

**Purpose:** Generate appropriate email response based on classification and knowledge base.

**Parameters:**
```python
{
    "classification": dict,     # Output from classify_email_reply
    "knowledge_base_info": list[dict],  # Relevant KB entries
    "conversation_history": list[dict], # Previous messages
    "sender_name": str,        # Recipient's name
    "response_tier": str,      # Target tier (auto_send, approval, escalation)
}
```

**Returns:**
```python
{
    "subject": str,            # Email subject line
    "body": str,              # Email body
    "response_type": str,     # Type of response (answer, meeting_link, objection_handle)
    "includes_kb_refs": bool, # Whether KB was used
    "suggested_tier": str,    # Recommended tier (may differ from input)
    "rationale": str,         # Why this response was drafted
    "next_action": str | None,  # Suggested follow-up action
}
```

**Error Handling:**
- Draft too long: Automatically condense while preserving key points
- Inappropriate content detected: Escalate to human review
- Missing context: Request additional information before drafting

### 4. `send_approval_request`

**Purpose:** Send draft response to human operator for approval via Slack/Telegram.

**Parameters:**
```python
{
    "draft_response": dict,       # Output from draft_email_response
    "original_email": dict,       # Original reply details
    "classification": dict,       # Classification results
    "urgency": str,              # One of: low, medium, high, critical
    "approval_channel": str,     # slack or telegram
}
```

**Returns:**
```python
{
    "approval_id": str,          # Unique ID for tracking
    "sent_at": str,             # ISO timestamp
    "channel": str,             # Where it was sent
    "message_id": str,          # Platform message ID
    "status": str,              # sent, delivered, failed
}
```

**Error Handling:**
- Slack/Telegram API errors: Try alternate channel, escalate if both fail
- Rate limiting: Queue for retry with exponential backoff
- Invalid message format: Log error, send simplified version

### 5. `send_email_response`

**Purpose:** Send approved/auto-send email response via Instantly.

**Parameters:**
```python
{
    "to_email": str,
    "subject": str,
    "body": str,
    "reply_to_message_id": str,    # Thread to reply to
    "campaign_id": str,
    "lead_id": str,
    "approval_id": str | None,     # If approved, link to approval
}
```

**Returns:**
```python
{
    "sent": bool,
    "message_id": str,             # Instantly message ID
    "sent_at": str,               # ISO timestamp
    "error": str | None,
}
```

**Error Handling:**
- Instantly API errors: Retry 3x, then escalate
- Invalid email address: Mark lead as invalid, notify human
- Rate limiting: Respect Instantly rate limits, queue for later

### 6. `handle_special_case`

**Purpose:** Process special email types (out-of-office, unsubscribe, referral, wrong-person).

**Parameters:**
```python
{
    "case_type": str,  # out_of_office, unsubscribe, referral, wrong_person
    "email_data": dict,
    "extracted_data": dict,  # Parsed information (dates, contacts, etc.)
}
```

**Returns:**
```python
{
    "action_taken": str,           # Description of action
    "next_steps": list[str],       # Scheduled follow-ups
    "database_updates": list[dict], # DB changes made
    "handoffs": list[dict],        # Agent handoffs created
}
```

**Actions by Case Type:**
- **out_of_office:** Parse return date, schedule follow-up, pause campaign
- **unsubscribe:** Remove from all campaigns, update lead status, log compliance
- **referral:** Create new lead record, send thank-you, assign to lead gen
- **wrong_person:** Request correct contact, update lead data, keep warm

**Error Handling:**
- Failed to parse data: Request human review of email
- Database update errors: Rollback and escalate
- Handoff failures: Queue for retry, alert human

### 7. `log_conversation_event`

**Purpose:** Store conversation event in database and memory systems.

**Parameters:**
```python
{
    "event_type": str,  # reply_received, response_sent, approval_requested, etc.
    "lead_id": str,
    "campaign_id": str,
    "email_data": dict,
    "classification": dict | None,
    "response_data": dict | None,
    "metadata": dict,
}
```

**Returns:**
```python
{
    "event_id": str,
    "stored_in_db": bool,
    "stored_in_memory": bool,
    "stored_at": str,
}
```

**Error Handling:**
- Database errors: Ensure at least memory storage succeeds
- Memory errors: Ensure at least DB storage succeeds
- Both fail: Cache locally and retry async

## Response Tier Classification

### Auto-Send Tier
**Criteria:**
- Category: `meeting_request` (with clear calendar link context)
- Category: `positive` + Intent: `interested` or `scheduling`
- Category: `out_of_office` (auto-acknowledge)
- Confidence: >= 0.9
- No complex questions or objections
- Knowledge base has clear, confident answer

**Examples:**
- "Yes, I'd love to chat! What's your calendar link?"
- "Thanks for reaching out! When can we schedule a call?"
- "I'm out until Monday, will respond then."

**Response Actions:**
- Send immediately via Instantly
- Log conversation event
- Update lead status to "engaged"
- No human approval needed

### Approval Tier
**Criteria:**
- Category: `question` with knowledge base answer
- Category: `objection` (pricing, timing, fit concerns)
- Category: `negative` but engagement possible
- Confidence: 0.7-0.9
- Requires nuanced response
- Pricing discussions

**Examples:**
- "What's your pricing for enterprise clients?"
- "Not sure this is right for us, we already use [competitor]"
- "Can you explain how your process works?"

**Response Actions:**
- Draft response using knowledge base
- Send to Slack/Telegram with context
- Wait for human approval/edit
- Send approved version
- Log approval workflow

### Escalation Tier
**Criteria:**
- Category: `complaint` or very negative sentiment
- Category: `question` with no knowledge base answer
- Complex technical questions
- Custom requests beyond standard services
- Legal/compliance concerns
- Confidence: < 0.7
- Multiple unresolved objections

**Examples:**
- "I want to cancel and get a refund immediately."
- "This doesn't work at all, very disappointed."
- "Can you build a custom integration with our proprietary system?"
- "I need this ASAP for a board presentation tomorrow."

**Response Actions:**
- Immediate Slack/Telegram notification to senior team
- Do NOT send automated response
- Create high-priority support ticket
- Assign to human operator immediately
- Log as escalation event

## Database Schema

### `email_responses`
```sql
CREATE TABLE email_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    campaign_id UUID NOT NULL REFERENCES campaigns(id),

    -- Email details
    from_email VARCHAR(255) NOT NULL,
    to_email VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    received_at TIMESTAMP NOT NULL,

    -- Threading
    thread_id VARCHAR(255),
    reply_to_message_id VARCHAR(255),
    instantly_message_id VARCHAR(255),

    -- Classification
    category VARCHAR(50) NOT NULL,  -- positive, negative, question, etc.
    sentiment VARCHAR(50) NOT NULL, -- very_positive to very_negative
    intent VARCHAR(50) NOT NULL,    -- interested, not_interested, etc.
    confidence DECIMAL(3,2) NOT NULL,

    -- Response tier
    response_tier VARCHAR(20) NOT NULL,  -- auto_send, approval, escalation

    -- Extracted data
    buying_signals JSONB DEFAULT '[]',
    objections JSONB DEFAULT '[]',
    key_points JSONB DEFAULT '[]',
    extracted_data JSONB DEFAULT '{}',

    -- Processing
    processed_at TIMESTAMP,
    response_sent_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_lead_id (lead_id),
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_category (category),
    INDEX idx_response_tier (response_tier),
    INDEX idx_received_at (received_at)
);
```

### `response_drafts`
```sql
CREATE TABLE response_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_response_id UUID NOT NULL REFERENCES email_responses(id),

    -- Draft content
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    response_type VARCHAR(50) NOT NULL,

    -- Metadata
    used_knowledge_base BOOLEAN DEFAULT false,
    kb_entries_used JSONB DEFAULT '[]',
    suggested_tier VARCHAR(20) NOT NULL,
    rationale TEXT,
    next_action TEXT,

    -- Version control
    version INTEGER DEFAULT 1,
    is_latest BOOLEAN DEFAULT true,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50) DEFAULT 'agent',  -- agent or human_id

    INDEX idx_email_response_id (email_response_id),
    INDEX idx_is_latest (is_latest)
);
```

### `response_approvals`
```sql
CREATE TABLE response_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID NOT NULL REFERENCES response_drafts(id),
    email_response_id UUID NOT NULL REFERENCES email_responses(id),

    -- Approval details
    status VARCHAR(20) NOT NULL,  -- pending, approved, rejected, edited
    urgency VARCHAR(20) NOT NULL, -- low, medium, high, critical

    -- Channel info
    approval_channel VARCHAR(20) NOT NULL,  -- slack, telegram
    channel_message_id VARCHAR(255),

    -- Approval outcome
    approved_by VARCHAR(100),  -- User ID or name
    approved_at TIMESTAMP,
    rejection_reason TEXT,

    -- Edits
    was_edited BOOLEAN DEFAULT false,
    edited_subject TEXT,
    edited_body TEXT,
    edit_notes TEXT,

    -- Timing
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    response_time_seconds INTEGER,

    INDEX idx_status (status),
    INDEX idx_urgency (urgency),
    INDEX idx_requested_at (requested_at)
);
```

### `conversation_history`
```sql
CREATE TABLE conversation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    campaign_id UUID NOT NULL REFERENCES campaigns(id),

    -- Event details
    event_type VARCHAR(50) NOT NULL,  -- reply_received, response_sent, etc.
    event_timestamp TIMESTAMP NOT NULL,

    -- References
    email_response_id UUID REFERENCES email_responses(id),
    draft_id UUID REFERENCES response_drafts(id),
    approval_id UUID REFERENCES response_approvals(id),

    -- Content snapshot
    email_subject TEXT,
    email_body TEXT,
    response_subject TEXT,
    response_body TEXT,

    -- Context
    classification_data JSONB,
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_lead_id (lead_id),
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_event_type (event_type),
    INDEX idx_event_timestamp (event_timestamp)
);
```

## Webhook Handler

### Endpoint
`POST /webhooks/instantly/email_replied`

### Authentication
- Verify webhook signature using `INSTANTLY_WEBHOOK_SECRET`
- Reject requests with invalid signatures (403 Forbidden)

### Payload Structure
```python
{
    "event": "email.replied",
    "timestamp": "2025-12-05T10:30:00Z",
    "data": {
        "campaign_id": "camp_123",
        "lead_id": "lead_456",
        "from_email": "prospect@company.com",
        "to_email": "outreach@agency.com",
        "subject": "Re: Quick question about AI automation",
        "body": "Thanks for reaching out! I'd love to learn more...",
        "thread_id": "thread_789",
        "reply_to_message_id": "msg_012",
        "received_at": "2025-12-05T10:29:45Z"
    }
}
```

### Handler Implementation
```python
# File: src/webhooks/instantly_webhooks.py

from fastapi import APIRouter, HTTPException, Header, Request
from src.agents.response_email_handler import ResponseEmailHandlerAgent
from src.config import get_agent_logger

router = APIRouter(prefix="/webhooks/instantly", tags=["webhooks"])
logger = get_agent_logger("instantly_webhook")

@router.post("/email_replied")
async def handle_email_replied(
    request: Request,
    x_instantly_signature: str = Header(None)
):
    """Handle incoming email reply webhook from Instantly."""
    # 1. Verify webhook signature
    body = await request.body()
    if not verify_instantly_signature(body, x_instantly_signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # 2. Parse payload
    payload = await request.json()

    # 3. Trigger agent processing (async via Celery)
    from src.tasks.response_tasks import process_email_reply
    task = process_email_reply.delay(payload["data"])

    # 4. Return 200 immediately (webhook best practice)
    return {
        "status": "accepted",
        "task_id": task.id,
        "message": "Email reply processing started"
    }
```

### Celery Task
```python
# File: src/tasks/response_tasks.py

from src.celery_app import celery_app
from src.agents.response_email_handler import ResponseEmailHandlerAgent

@celery_app.task(bind=True, max_retries=3)
def process_email_reply(self, email_data: dict):
    """Process email reply asynchronously."""
    agent = ResponseEmailHandlerAgent()

    try:
        result = await agent.process_task({
            "type": "email_reply",
            "data": email_data
        })
        return result
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

## Agent Implementation Structure

```
src/agents/response_email_handler/
├── __init__.py              # Exports ResponseEmailHandlerAgent
├── agent.py                 # Main agent class
├── tools.py                 # Tool implementations
├── prompts.py               # System prompt and templates
├── schemas.py               # Pydantic models for validation
├── exceptions.py            # Custom exceptions
└── classifiers.py           # Classification logic
```

## Error Handling Strategy

### Classification Errors
- **Low confidence (<0.7):** Automatically upgrade to "approval" tier
- **Anthropic API timeout:** Retry 3x with exponential backoff (2s, 4s, 8s)
- **API rate limit:** Queue for retry after rate limit window
- **Invalid email format:** Log error, send to manual review queue

### Knowledge Base Errors
- **Pinecone connection failure:** Fallback to cached KB entries from Redis
- **No results found:** Proceed with draft but flag "missing_kb_info"
- **Query timeout:** Use default response templates

### Sending Errors
- **Instantly API failure:** Retry 3x, then create manual task for human
- **Slack/Telegram failure:** Try alternate channel, escalate if both fail
- **Rate limiting:** Respect limits, queue with appropriate delay

### Database Errors
- **Write failure:** Ensure at least one of (DB, Zep memory, Redis cache) succeeds
- **Transaction rollback:** Retry once, then escalate to system admin
- **Constraint violation:** Log error, investigate data integrity

### General Error Handling
```python
try:
    # Process email
    result = await process_email_reply(email_data)
except AnthropicAPIError as e:
    # Retry with backoff
    await retry_with_backoff(process_email_reply, email_data, max_retries=3)
except DatabaseError as e:
    # Escalate to system admin
    await escalate_to_admin(
        error=e,
        context={"email_id": email_data["id"]},
        urgency="high"
    )
except Exception as e:
    # Catch-all: log and escalate
    logger.error(f"Unexpected error: {e}", extra={"email_data": email_data})
    await escalate_to_admin(error=e, urgency="critical")
```

## Testing Requirements

### Unit Tests (>90% coverage)

**Test Files:**
- `__tests__/unit/agents/response_email_handler/test_agent.py`
- `__tests__/unit/agents/response_email_handler/test_tools.py`
- `__tests__/unit/agents/response_email_handler/test_classifiers.py`

**Test Cases:**

1. **Classification Tests:**
   - Test all 9 categories (positive, negative, question, objection, out_of_office, unsubscribe, referral, wrong_person, meeting_request)
   - Test sentiment analysis accuracy
   - Test confidence scoring
   - Test low-confidence handling (auto-upgrade to approval)
   - Test buying signal detection
   - Test objection extraction

2. **Response Tier Tests:**
   - Test auto-send criteria (confidence, category, KB availability)
   - Test approval tier routing
   - Test escalation triggers
   - Test edge cases (borderline confidence scores)

3. **Knowledge Base Tests:**
   - Test semantic search with mock Pinecone
   - Test fallback to cache on connection failure
   - Test empty results handling
   - Test confidence threshold filtering

4. **Draft Generation Tests:**
   - Test response quality for each category
   - Test 125-character limit enforcement
   - Test KB integration in drafts
   - Test tone matching

5. **Special Case Tests:**
   - Test out-of-office date parsing
   - Test unsubscribe compliance
   - Test referral data extraction
   - Test wrong-person contact request

6. **Tool Tests:**
   - Mock all external API calls (Anthropic, Pinecone, Instantly, Slack)
   - Test each tool's input validation
   - Test each tool's error handling
   - Test each tool's retry logic

### Integration Tests (>85% coverage)

**Test Files:**
- `__tests__/integration/test_email_reply_workflow.py`
- `__tests__/integration/test_approval_workflow.py`
- `__tests__/integration/test_webhook_handler.py`

**Test Scenarios:**

1. **End-to-End Workflow Tests:**
   - Webhook → Classification → Auto-send (complete flow)
   - Webhook → Classification → Approval → Send (approval flow)
   - Webhook → Classification → Escalation (escalation flow)

2. **Approval Workflow Tests:**
   - Send approval request to Slack
   - Handle approval response
   - Handle rejection with edits
   - Handle timeout/no response

3. **Database Integration Tests:**
   - Test email_responses record creation
   - Test response_drafts versioning
   - Test response_approvals lifecycle
   - Test conversation_history logging
   - Test transaction rollback scenarios

4. **Agent Handoff Tests:**
   - Handoff to Knowledge Base Agent
   - Handoff to Meeting Scheduler
   - Handoff to Support Agent (escalations)

5. **Webhook Integration Tests:**
   - Test signature verification
   - Test malformed payload handling
   - Test duplicate webhook detection
   - Test async processing trigger

### Fixtures

**Required Fixtures:**
```python
# __tests__/fixtures/response_handler_fixtures.py

@pytest.fixture
def sample_email_reply():
    return {
        "from_email": "prospect@company.com",
        "subject": "Re: AI Automation Question",
        "body": "Thanks for reaching out! I'd love to learn more about your services.",
        "campaign_id": "camp_123",
        "lead_id": "lead_456"
    }

@pytest.fixture
def mock_anthropic_classification():
    return {
        "category": "positive",
        "sentiment": "positive",
        "intent": "interested",
        "confidence": 0.92,
        "buying_signals": ["love to learn more"],
        "objections": [],
        "key_points": ["Interested in services"]
    }

@pytest.fixture
def mock_knowledge_base_results():
    return {
        "results": [{
            "content": "Our services include...",
            "title": "Service Overview",
            "confidence": 0.89
        }],
        "found_answer": True
    }

@pytest.fixture
def mock_slack_client():
    # Mock Slack client for approval requests
    pass

@pytest.fixture
def mock_instantly_client():
    # Mock Instantly client for sending emails
    pass
```

### Performance Tests
- Response time: < 2 seconds for classification
- Draft generation: < 3 seconds
- End-to-end (webhook to DB): < 5 seconds
- Concurrent webhook handling: 50+ per second

### Edge Case Tests
- Empty email body
- Email with only emoji
- Extremely long emails (>10,000 chars)
- Non-English emails
- HTML-heavy emails
- Multiple languages in one email
- Malformed email headers

## Implementation Checklist

### Phase 1: Core Agent Setup
- [ ] Create agent directory structure
- [ ] Define Pydantic schemas for all data models
- [ ] Implement `ResponseEmailHandlerAgent` class extending `BaseAgent`
- [ ] Write system prompt in `prompts.py`
- [ ] Set up custom exceptions in `exceptions.py`

### Phase 2: Classification Tools
- [ ] Implement `classify_email_reply` tool
- [ ] Implement sentiment analysis logic
- [ ] Implement buying signal detection
- [ ] Implement objection extraction
- [ ] Write unit tests for classification (>90% coverage)

### Phase 3: Knowledge Base Integration
- [ ] Implement `query_knowledge_base` tool
- [ ] Set up Pinecone client for vector search
- [ ] Implement Redis cache fallback
- [ ] Write unit tests for KB queries

### Phase 4: Response Drafting
- [ ] Implement `draft_email_response` tool
- [ ] Create response templates for each category
- [ ] Implement 125-character condensing logic
- [ ] Implement tone matching
- [ ] Write unit tests for drafting

### Phase 5: Tier Logic
- [ ] Implement tier classification logic
- [ ] Write auto-send criteria checks
- [ ] Write approval tier criteria checks
- [ ] Write escalation tier criteria checks
- [ ] Write unit tests for tier logic

### Phase 6: Approval Workflow
- [ ] Implement `send_approval_request` tool
- [ ] Create Slack integration client
- [ ] Create Telegram integration client
- [ ] Implement approval response handler
- [ ] Write integration tests for approval flow

### Phase 7: Email Sending
- [ ] Implement `send_email_response` tool
- [ ] Create Instantly.ai client
- [ ] Implement retry logic with exponential backoff
- [ ] Write integration tests for sending

### Phase 8: Special Cases
- [ ] Implement `handle_special_case` tool
- [ ] Implement out-of-office parser
- [ ] Implement unsubscribe handler
- [ ] Implement referral handler
- [ ] Implement wrong-person handler
- [ ] Write unit tests for each special case

### Phase 9: Database Layer
- [ ] Create database migration for all 4 tables
- [ ] Implement SQLAlchemy models
- [ ] Implement `log_conversation_event` tool
- [ ] Write database integration tests

### Phase 10: Webhook Handler
- [ ] Implement webhook endpoint in FastAPI
- [ ] Implement signature verification
- [ ] Create Celery task for async processing
- [ ] Write webhook integration tests

### Phase 11: Memory Integration
- [ ] Implement Zep memory storage
- [ ] Implement context retrieval from memory
- [ ] Write memory integration tests

### Phase 12: Error Handling
- [ ] Implement retry logic for all external APIs
- [ ] Implement fallback mechanisms
- [ ] Implement escalation pathways
- [ ] Write error handling tests

### Phase 13: Integration Testing
- [ ] Write end-to-end workflow tests
- [ ] Write agent handoff tests
- [ ] Write concurrent processing tests
- [ ] Write performance tests

### Phase 14: Documentation
- [ ] Write API documentation
- [ ] Write runbook for operators
- [ ] Document tier criteria for humans
- [ ] Create troubleshooting guide

### Phase 15: Production Readiness
- [ ] Run full test suite (>85% coverage)
- [ ] Performance testing (load testing)
- [ ] Security review (input validation)
- [ ] Deploy to staging environment
- [ ] Human operator training
- [ ] Gradual rollout plan (10% → 50% → 100%)

## Metrics & Monitoring

### Key Metrics
- **Classification Accuracy:** % of correct classifications (validated by human)
- **Auto-Send Rate:** % of emails in auto-send tier
- **Approval Rate:** % of drafts approved without edits
- **Escalation Rate:** % of emails escalated
- **Response Time:** Time from webhook to email sent
- **Human Approval Time:** Time from approval request to human response

### Alerts
- Classification confidence < 0.5 for >10% of emails
- Escalation rate > 20%
- Response time > 10 seconds
- Approval request backlog > 50
- Error rate > 5%
- Anthropic API failures

### Dashboards
- Real-time email processing queue
- Approval requests pending
- Classification distribution (pie chart)
- Sentiment trend over time
- Response tier breakdown
- Knowledge base hit rate

## Deployment Notes

### Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...
INSTANTLY_API_KEY=...
INSTANTLY_WEBHOOK_SECRET=...
SLACK_BOT_TOKEN=xoxb-...
TELEGRAM_BOT_TOKEN=...
PINECONE_API_KEY=...
ZEP_API_KEY=...
```

### Celery Configuration
```python
# High priority queue for email responses
CELERY_TASK_ROUTES = {
    'src.tasks.response_tasks.process_email_reply': {'queue': 'high_priority'}
}
```

### Rate Limits
- Anthropic API: 50 requests/minute
- Instantly API: 100 requests/minute
- Slack API: 1 request/second per channel

### Rollout Strategy
1. **Phase 1 (Week 1):** Deploy to staging, process 10% of emails
2. **Phase 2 (Week 2):** Increase to 50% if metrics look good
3. **Phase 3 (Week 3):** Full rollout to 100% of emails
4. **Monitoring:** Daily review for first month

---

**Specification Version:** 1.0
**Last Updated:** 2025-12-05
**Author:** AI Agent Architect
**Status:** Ready for Implementation
