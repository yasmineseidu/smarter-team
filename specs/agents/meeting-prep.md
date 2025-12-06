# Meeting Prep Agent - Production Specification

## Overview

**Agent Name:** `meeting_prep`
**Category:** Meeting Management
**Priority:** Phase 2 - Intelligence Layer
**Coverage Requirement:** >85% (agent coverage standard)

## Purpose

Automatically prepare comprehensive meeting materials 1 hour before scheduled calls by aggregating research data, conversation history, and generating AI-powered presentation slides via Gamma API. Delivers a complete prep package via email/Slack to ensure sales/success teams are fully informed before every meeting.

## Dependencies

### Required Agents
- **Lead Research Agent** - Provides lead LinkedIn activity, achievements, mutual connections
- **Company Research Agent** - Provides company news, tech stack, job postings, trigger events
- **Conversation Intelligence Agent** - Provides conversation summary, sentiment, objection patterns

### Required Integrations
- **Gamma API** - Presentation slide generation
- **Email** (Gmail/SMTP) - Prep package delivery
- **Slack** - Alternative prep package delivery
- **Claude API** - Summarization and talking point generation
- **Cal.com** - Meeting metadata (time, duration, attendees)

### Required Database Tables
- `meetings` - Meeting metadata (from scheduler agent)
- `meeting_prep` - Prep package records
- `talking_points` - Generated talking points per meeting
- `lead_research` - Lead research data
- `company_research` - Company research data
- `conversation_analysis` - Conversation history summaries

## System Prompt

```
You are the Meeting Prep Agent for Smarter Team, an AI agency automation platform.

Your role is to prepare comprehensive, actionable meeting materials exactly 1 hour before scheduled calls.

RESPONSIBILITIES:
1. Aggregate all available research on the lead and their company
2. Summarize conversation history with sentiment and key points
3. Generate 3-5 strategic talking points based on their pain points and triggers
4. Create 3-5 discovery questions tailored to their business context
5. Anticipate 2-3 likely objections with prepared responses
6. Generate professional presentation slides via Gamma API
7. Deliver a complete prep package via email or Slack

OUTPUT REQUIREMENTS:
- Prep packages must be concise yet comprehensive (max 2 pages text)
- Talking points must reference specific research insights (news, LinkedIn activity, tech stack)
- Questions must be open-ended and business-focused (not generic)
- Objection responses must be specific to their industry/situation
- Gamma slides must include: intro, company context, agenda, talking points, next steps (5-7 slides max)

TONE:
- Professional and confident
- Data-driven (cite sources: "Based on their recent LinkedIn post about...")
- Action-oriented (what to ASK, not what to SAY)

ERROR HANDLING:
- If research data is incomplete, flag gaps but still generate prep package with available data
- If Gamma API fails, deliver prep package without slides and log error
- If delivery fails, retry once and escalate to human if still failing

TIMING:
- Must complete prep generation within 10 minutes of trigger
- Deliver prep package no later than 45 minutes before meeting start time
- Log all prep deliveries for tracking
```

## Tool Definitions

### 1. `fetch_lead_research`
**Purpose:** Retrieve aggregated lead research data

**Parameters:**
```python
{
    "lead_id": str,  # UUID of lead in database
}
```

**Returns:**
```python
{
    "lead_name": str,
    "job_title": str,
    "company": str,
    "linkedin_url": str,
    "recent_posts": list[dict],  # [{"date": str, "content": str, "engagement": int}]
    "recent_achievements": list[str],
    "mutual_connections": list[str],
    "personalization_angles": list[str],
    "career_highlights": list[str],
    "research_timestamp": str,  # ISO 8601
}
```

**Error Handling:**
- Raises `LeadNotFoundError` if lead_id doesn't exist
- Returns empty lists if no research data available (don't fail)
- Logs warning if research is >7 days old

---

### 2. `fetch_company_research`
**Purpose:** Retrieve aggregated company research data

**Parameters:**
```python
{
    "company_id": str,  # UUID of company in database
}
```

**Returns:**
```python
{
    "company_name": str,
    "industry": str,
    "employee_count": int,
    "recent_news": list[dict],  # [{"date": str, "headline": str, "source": str, "url": str}]
    "tech_stack": list[str],
    "job_postings": list[dict],  # [{"title": str, "department": str, "posted_date": str}]
    "trigger_events": list[dict],  # [{"event_type": str, "description": str, "date": str}]
    "linkedin_activity": list[dict],
    "research_timestamp": str,
}
```

**Error Handling:**
- Raises `CompanyNotFoundError` if company_id doesn't exist
- Returns empty lists if no research data available
- Logs warning if research is >14 days old

---

### 3. `fetch_conversation_summary`
**Purpose:** Retrieve conversation history summary for a lead

**Parameters:**
```python
{
    "lead_id": str,
    "limit": int = 20,  # Max number of messages to include in summary
}
```

**Returns:**
```python
{
    "total_messages": int,
    "summary": str,  # Claude-generated summary of conversation
    "sentiment_score": float,  # -1.0 to 1.0
    "objections_raised": list[str],
    "buying_signals": list[str],
    "key_topics": list[str],
    "last_message_date": str,
    "response_rate": float,  # 0.0 to 1.0
}
```

**Error Handling:**
- Returns empty summary if no conversation history exists
- Logs warning if conversation is >30 days old with no recent activity

---

### 4. `generate_talking_points`
**Purpose:** Use Claude to generate strategic talking points

**Parameters:**
```python
{
    "lead_research": dict,  # Output from fetch_lead_research
    "company_research": dict,  # Output from fetch_company_research
    "conversation_summary": dict,  # Output from fetch_conversation_summary
    "meeting_type": str,  # "discovery", "demo", "closing", "check-in"
}
```

**Returns:**
```python
{
    "talking_points": list[dict],  # [{"point": str, "context": str, "source": str}]
    "discovery_questions": list[str],
    "potential_objections": list[dict],  # [{"objection": str, "response": str}]
}
```

**Implementation:**
- Uses `anthropic.messages.create()` with claude-3-5-sonnet
- Includes all research context in prompt
- Max 5 talking points, 5 questions, 3 objections
- Each talking point must cite source (e.g., "LinkedIn post from Nov 2025")

---

### 5. `create_gamma_presentation`
**Purpose:** Generate presentation slides via Gamma API

**Parameters:**
```python
{
    "meeting_title": str,  # e.g., "Discovery Call with [Lead] at [Company]"
    "content_outline": dict,  # Structure: {slide_title: slide_content}
    "theme": str = "professional",  # Gamma theme name
}
```

**Returns:**
```python
{
    "presentation_url": str,  # Public URL to view/present
    "edit_url": str,  # URL to edit (optional)
    "slide_count": int,
    "created_at": str,
}
```

**Error Handling:**
- Raises `GammaAPIError` if API call fails (catch and log, continue without slides)
- Validates content_outline has 3-7 slides (enforce constraints)
- Retries once on timeout (30s timeout per request)

**Gamma API Integration Notes:**
- Endpoint: `POST https://api.gamma.app/v1/presentations`
- Auth: `Bearer {GAMMA_API_KEY}` header
- Request body:
```json
{
  "title": "Meeting Title",
  "slides": [
    {"title": "Intro", "content": "markdown content"},
    {"title": "Company Context", "content": "..."}
  ],
  "theme": "professional"
}
```
- Rate limits: 100 requests/hour (track in integration client)

---

### 6. `deliver_prep_package`
**Purpose:** Send prep package via email or Slack

**Parameters:**
```python
{
    "recipient_email": str | None,  # Email address (if email delivery)
    "slack_channel": str | None,  # Slack channel ID (if Slack delivery)
    "prep_content": dict,  # Full prep package data
    "delivery_method": str,  # "email" or "slack"
}
```

**Returns:**
```python
{
    "delivery_id": str,  # Unique delivery tracking ID
    "delivered_at": str,
    "delivery_method": str,
    "status": str,  # "delivered", "failed", "retrying"
}
```

**Error Handling:**
- Retries once on delivery failure (5s delay)
- Logs delivery attempts for audit trail
- Raises `DeliveryFailedError` after 2 failed attempts (escalate to human)

---

### 7. `store_prep_package`
**Purpose:** Save prep package to database for historical tracking

**Parameters:**
```python
{
    "meeting_id": str,
    "prep_data": dict,  # Complete prep package
    "gamma_url": str | None,
}
```

**Returns:**
```python
{
    "prep_id": str,  # UUID of stored prep package
    "created_at": str,
}
```

**Database Schema:**
```sql
CREATE TABLE meeting_prep (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id),
    lead_summary JSONB NOT NULL,
    company_summary JSONB NOT NULL,
    conversation_summary JSONB NOT NULL,
    talking_points JSONB NOT NULL,
    gamma_presentation_url TEXT,
    delivery_method TEXT,
    delivery_status TEXT,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE TABLE talking_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prep_id UUID NOT NULL REFERENCES meeting_prep(id),
    point_text TEXT NOT NULL,
    context TEXT,
    source TEXT,
    display_order INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_meeting_prep_meeting_id ON meeting_prep(meeting_id);
CREATE INDEX idx_meeting_prep_created_at ON meeting_prep(created_at);
CREATE INDEX idx_talking_points_prep_id ON talking_points(prep_id);
```

## Process Flow

### Trigger Mechanism
**Celery Beat Schedule:**
```python
# In celery_app.py beat_schedule
"check-upcoming-meetings": {
    "task": "src.tasks.meeting_tasks.check_upcoming_meetings",
    "schedule": crontab(minute="*/15"),  # Every 15 minutes
}
```

**Task Logic:**
1. Query `meetings` table for meetings starting in 45-75 minutes
2. Filter out meetings that already have prep packages (`meeting_prep.meeting_id`)
3. For each meeting, trigger `generate_meeting_prep.delay(meeting_id)`

---

### Main Process (Async)

```python
async def process_task(task: dict[str, Any]) -> dict[str, Any]:
    """
    Generate and deliver meeting prep package.

    Args:
        task: {"meeting_id": str, "recipient_email": str, "delivery_method": str}

    Returns:
        {"prep_id": str, "delivery_status": str, "gamma_url": str | None}
    """
    meeting_id = task["meeting_id"]

    # Step 1: Fetch meeting metadata from database
    meeting = await fetch_meeting(meeting_id)  # Get lead_id, company_id, meeting_time, type

    # Step 2: Aggregate research data (parallel)
    lead_research, company_research, conversation_summary = await asyncio.gather(
        fetch_lead_research(meeting.lead_id),
        fetch_company_research(meeting.company_id),
        fetch_conversation_summary(meeting.lead_id),
    )

    # Step 3: Generate talking points (Claude API)
    talking_points = await generate_talking_points(
        lead_research=lead_research,
        company_research=company_research,
        conversation_summary=conversation_summary,
        meeting_type=meeting.type,
    )

    # Step 4: Create Gamma presentation (optional, non-blocking)
    gamma_url = None
    try:
        gamma_result = await create_gamma_presentation(
            meeting_title=f"{meeting.type.title()} with {lead_research['lead_name']} at {company_research['company_name']}",
            content_outline=build_slide_outline(lead_research, company_research, talking_points),
            theme="professional",
        )
        gamma_url = gamma_result["presentation_url"]
    except GammaAPIError as e:
        self.logger.error("Gamma presentation failed", extra={"error": str(e)})
        # Continue without slides

    # Step 5: Build prep package
    prep_package = build_prep_package(
        lead_research=lead_research,
        company_research=company_research,
        conversation_summary=conversation_summary,
        talking_points=talking_points,
        gamma_url=gamma_url,
        meeting_time=meeting.meeting_time,
    )

    # Step 6: Store prep package in database
    prep_id = await store_prep_package(
        meeting_id=meeting_id,
        prep_data=prep_package,
        gamma_url=gamma_url,
    )

    # Step 7: Deliver prep package
    delivery_result = await deliver_prep_package(
        recipient_email=task.get("recipient_email"),
        slack_channel=task.get("slack_channel"),
        prep_content=prep_package,
        delivery_method=task.get("delivery_method", "email"),
    )

    # Step 8: Log completion
    self.log_action(
        "meeting_prep.completed",
        {
            "prep_id": prep_id,
            "meeting_id": meeting_id,
            "delivery_status": delivery_result["status"],
            "has_gamma": gamma_url is not None,
        },
    )

    return {
        "prep_id": prep_id,
        "delivery_status": delivery_result["status"],
        "gamma_url": gamma_url,
    }
```

## Prep Package Format

### Email Template (HTML + Plain Text)

**Subject:** `Meeting Prep: {lead_name} at {company} - {meeting_time}`

**Body Structure:**
```
========================================
MEETING PREP: {lead_name} at {company}
========================================

Date: {meeting_time}
Duration: {duration} minutes
Meeting Type: {type}

---
LEAD SUMMARY
---
Name: {lead_name}
Role: {job_title}

Key Insight: {personalization_angles[0]}

Recent LinkedIn Activity:
• {recent_post_1_summary} ({date})
• {recent_post_2_summary} ({date})

Career Highlights:
• {career_highlight_1}

---
COMPANY SUMMARY
---
Company: {company_name}
Industry: {industry}
Size: {employee_count} employees

Recent News:
• {news_headline_1} ({source}, {date})
• {news_headline_2} ({source}, {date})

Tech Stack: {tech_stack_list}

Trigger Events:
• {trigger_event_1}

---
CONVERSATION HISTORY
---
Total Messages: {total_messages}
Sentiment: {sentiment_score} ({positive/neutral/negative})
Response Rate: {response_rate}%

Summary:
{conversation_summary}

Objections Raised:
• {objection_1}

Buying Signals:
• {buying_signal_1}

---
TALKING POINTS
---
1. {talking_point_1}
   Context: {context_1}
   Source: {source_1}

2. {talking_point_2}
   Context: {context_2}

3. {talking_point_3}
   Context: {context_3}

---
DISCOVERY QUESTIONS
---
1. {question_1}
2. {question_2}
3. {question_3}

---
POTENTIAL OBJECTIONS & RESPONSES
---
Objection: "{objection_1}"
Response: {response_1}

Objection: "{objection_2}"
Response: {response_2}

---
PRESENTATION SLIDES
---
{gamma_url if available, else "Slides generation failed - see details above"}

---
Generated by Smarter Team Meeting Prep Agent
{timestamp}
```

### Slack Message Format (Markdown Blocks)

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {"type": "plain_text", "text": "Meeting Prep: {lead_name} at {company}"}
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Date:*\n{meeting_time}"},
        {"type": "mrkdwn", "text": "*Duration:*\n{duration} min"}
      ]
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*Lead Summary*\n{summary}"}
    },
    // ... more sections ...
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "View Slides"},
          "url": "{gamma_url}",
          "style": "primary"
        }
      ]
    }
  ]
}
```

## Error Handling & Edge Cases

### Incomplete Research Data
**Scenario:** Lead or company research is missing or outdated

**Handling:**
1. Log warning with specific missing data fields
2. Generate prep package with available data
3. Include "Research Gap" section noting what's missing
4. Still deliver prep (partial info better than none)

---

### Gamma API Failure
**Scenario:** Gamma API returns 500 error or times out

**Handling:**
1. Catch `GammaAPIError` exception
2. Log error with full context (request payload, response)
3. Continue prep generation without slides
4. Include note in delivery: "Slide generation failed - presenting from prep doc"
5. Don't block delivery on Gamma failure

---

### Delivery Failure
**Scenario:** Email/Slack delivery fails (SMTP error, Slack API error)

**Handling:**
1. Retry once after 5 seconds
2. If second attempt fails, log critical error
3. Create task for human review in `tasks/backend/pending/` (automated task creation)
4. Send fallback notification to operations Slack channel
5. Mark delivery status as "failed" in database

---

### Meeting Too Soon
**Scenario:** Meeting starts in <30 minutes (too late for prep)

**Handling:**
1. Log warning: "Meeting prep triggered late"
2. Generate prep anyway (better late than never)
3. Send with urgent flag: "⚠️ URGENT: Meeting in {minutes} minutes"
4. Track late prep instances for scheduler optimization

---

### Duplicate Prep Generation
**Scenario:** Prep already exists for this meeting

**Handling:**
1. Check `meeting_prep` table before starting
2. If prep exists and was delivered <2 hours ago, skip
3. If user requests regeneration (future feature), allow override
4. Log skip event for monitoring

## Testing Requirements

### Unit Tests (>90% coverage for tools)

**Test File:** `__tests__/unit/agents/test_meeting_prep_agent.py`

**Test Cases:**
1. `test_fetch_lead_research_success` - Returns valid lead research data
2. `test_fetch_lead_research_not_found` - Raises LeadNotFoundError
3. `test_fetch_lead_research_empty_data` - Returns empty lists gracefully
4. `test_fetch_company_research_success` - Returns valid company data
5. `test_fetch_conversation_summary_no_history` - Returns empty summary
6. `test_generate_talking_points` - Claude API integration, validates output structure
7. `test_create_gamma_presentation_success` - Mocked Gamma API success
8. `test_create_gamma_presentation_failure` - Handles API error gracefully
9. `test_deliver_prep_package_email` - Email delivery via SMTP
10. `test_deliver_prep_package_slack` - Slack delivery via API
11. `test_deliver_prep_package_retry` - Retry logic on failure
12. `test_store_prep_package` - Database insertion
13. `test_build_prep_package` - Correct formatting of all sections
14. `test_build_slide_outline` - Gamma slide structure generation

---

### Integration Tests (>85% coverage for agent)

**Test File:** `__tests__/integration/test_meeting_prep_agent.py`

**Test Cases:**
1. `test_full_prep_generation_flow` - End-to-end with real database
2. `test_prep_with_missing_research` - Handles partial data gracefully
3. `test_prep_without_gamma` - Completes without slides on API failure
4. `test_prep_delivery_email` - Full email delivery integration
5. `test_prep_delivery_slack` - Full Slack delivery integration
6. `test_duplicate_prep_prevention` - Skips if prep exists
7. `test_late_meeting_prep` - Urgent flag for late preps
8. `test_celery_task_trigger` - Scheduled task execution
9. `test_handoff_from_scheduler` - Agent handoff integration

---

### Fixtures Required

**File:** `__tests__/fixtures/meeting_prep_fixtures.py`

```python
@pytest.fixture
def mock_lead_research():
    return {
        "lead_name": "Jane Doe",
        "job_title": "VP of Engineering",
        "company": "TechCorp",
        "linkedin_url": "https://linkedin.com/in/janedoe",
        "recent_posts": [
            {"date": "2025-11-15", "content": "Excited about our new AI initiative...", "engagement": 45}
        ],
        "recent_achievements": ["Promoted to VP", "Led migration to microservices"],
        "mutual_connections": ["John Smith", "Sarah Johnson"],
        "personalization_angles": ["Recent AI initiative", "Microservices expertise"],
        "career_highlights": ["10 years in SaaS", "Built team from 5 to 50"],
        "research_timestamp": "2025-12-05T12:00:00Z",
    }

@pytest.fixture
def mock_company_research():
    return {
        "company_name": "TechCorp",
        "industry": "SaaS",
        "employee_count": 250,
        "recent_news": [
            {"date": "2025-11-20", "headline": "TechCorp raises $10M Series A", "source": "TechCrunch", "url": "..."}
        ],
        "tech_stack": ["Python", "React", "PostgreSQL", "AWS"],
        "job_postings": [{"title": "Senior ML Engineer", "department": "Engineering", "posted_date": "2025-11-10"}],
        "trigger_events": [{"event_type": "funding", "description": "Series A $10M", "date": "2025-11-20"}],
        "linkedin_activity": [],
        "research_timestamp": "2025-12-05T12:00:00Z",
    }

@pytest.fixture
def mock_conversation_summary():
    return {
        "total_messages": 5,
        "summary": "Lead expressed interest in automating sales workflows. Mentioned current manual process is time-consuming.",
        "sentiment_score": 0.7,
        "objections_raised": ["Concerned about implementation time"],
        "buying_signals": ["Asked about pricing", "Requested demo"],
        "key_topics": ["automation", "sales workflows", "ROI"],
        "last_message_date": "2025-12-01T10:00:00Z",
        "response_rate": 0.8,
    }

@pytest.fixture
def mock_gamma_client():
    # Mock GammaClient with AsyncMock
    pass
```

## Implementation Checklist

### Phase 1: Setup & Foundation
- [ ] Create agent directory: `src/agents/meeting_prep/`
- [ ] Create agent file: `agent.py` with `MeetingPrepAgent` class extending `BaseAgent`
- [ ] Create tools file: `tools.py` with all 7 tool functions
- [ ] Create prompts file: `prompts.py` with system prompt constant
- [ ] Create schemas file: `schemas.py` with Pydantic models for all data structures
- [ ] Create exceptions file: `exceptions.py` with custom exceptions (LeadNotFoundError, GammaAPIError, DeliveryFailedError)

### Phase 2: Integrations
- [ ] Create Gamma integration: `src/integrations/gamma.py` extending `BaseIntegrationClient`
- [ ] Add Gamma API configuration to `.env.example`
- [ ] Create email delivery service: `src/integrations/email_service.py`
- [ ] Create Slack delivery service: `src/integrations/slack_service.py` (or use existing if available)
- [ ] Add integration tests for each client

### Phase 3: Database
- [ ] Create migration: `specs/database-schema/migrations/004_meeting_prep_tables.sql`
- [ ] Add `meeting_prep` table schema
- [ ] Add `talking_points` table schema
- [ ] Add indexes for performance
- [ ] Run migration on dev database
- [ ] Verify foreign key constraints

### Phase 4: Core Implementation
- [ ] Implement `fetch_lead_research` tool with database queries
- [ ] Implement `fetch_company_research` tool with database queries
- [ ] Implement `fetch_conversation_summary` tool with Claude API
- [ ] Implement `generate_talking_points` tool with Claude API
- [ ] Implement `create_gamma_presentation` tool with Gamma client
- [ ] Implement `deliver_prep_package` tool with email/Slack services
- [ ] Implement `store_prep_package` tool with database inserts
- [ ] Implement `build_prep_package` helper function
- [ ] Implement `build_slide_outline` helper function

### Phase 5: Agent Logic
- [ ] Implement `system_prompt` property
- [ ] Implement `process_task` method with full workflow
- [ ] Add error handling for all edge cases
- [ ] Add logging at each step
- [ ] Add timing metrics logging
- [ ] Test manual agent invocation

### Phase 6: Celery Integration
- [ ] Create Celery task: `src/tasks/meeting_tasks.py`
- [ ] Implement `check_upcoming_meetings` periodic task
- [ ] Implement `generate_meeting_prep` task
- [ ] Add Celery beat schedule configuration
- [ ] Test task execution locally
- [ ] Test retry logic

### Phase 7: Testing
- [ ] Create test fixtures: `__tests__/fixtures/meeting_prep_fixtures.py`
- [ ] Write unit tests for all 7 tools (>90% coverage)
- [ ] Write unit tests for helper functions
- [ ] Write integration test for full prep flow
- [ ] Write integration tests for edge cases (missing data, API failures, delivery failures)
- [ ] Run `make test` and verify >85% agent coverage
- [ ] Fix any failing tests

### Phase 8: Quality Assurance
- [ ] Run `make lint` and fix all linting errors
- [ ] Run `make typecheck` and fix all type errors
- [ ] Run `make format` to format code
- [ ] Run `make check` to verify all quality gates pass
- [ ] Manual testing with real database and API keys
- [ ] Test email delivery to real inbox
- [ ] Test Slack delivery to test channel
- [ ] Test Gamma slide generation

### Phase 9: Documentation & Deployment
- [ ] Update root `CLAUDE.md` if needed
- [ ] Add agent to agent registry (if applicable)
- [ ] Document environment variables in `.env.example`
- [ ] Create runbook for monitoring prep delivery rate
- [ ] Move task to `tasks/backend/_completed/`
- [ ] Update `tasks/TASK-LOG.md` with completion notes
- [ ] Create PR with all changes

### Phase 10: Monitoring & Optimization
- [ ] Set up alerts for prep delivery failures
- [ ] Monitor prep generation latency (target <10 minutes)
- [ ] Track Gamma API success rate
- [ ] Monitor research data freshness
- [ ] Collect feedback from users on prep quality
- [ ] Iterate on talking point generation prompt based on feedback

## Performance Targets

- **Prep Generation Time:** <10 minutes from trigger to delivery
- **Research Aggregation:** <2 minutes (parallel queries)
- **Claude API Calls:** <3 minutes (talking points generation)
- **Gamma API:** <3 minutes (slide generation, non-blocking)
- **Delivery:** <1 minute (email/Slack)
- **Database Operations:** <30 seconds (all queries combined)

## Monitoring & Metrics

### Key Metrics to Track
1. **Prep Delivery Rate:** % of meetings with prep delivered >45 min before start
2. **Gamma Success Rate:** % of preps with successful slide generation
3. **Research Freshness:** Average age of lead/company research data
4. **Delivery Failure Rate:** % of failed email/Slack deliveries
5. **Late Prep Rate:** % of preps delivered <30 min before meeting
6. **User Engagement:** % of prep emails opened (track with email analytics)

### Logging Events
- `meeting_prep.triggered` - When prep generation starts
- `meeting_prep.research_fetched` - When all research data aggregated
- `meeting_prep.talking_points_generated` - When Claude completes talking points
- `meeting_prep.gamma_success` - When Gamma slides created
- `meeting_prep.gamma_failed` - When Gamma API fails
- `meeting_prep.delivered` - When prep package sent successfully
- `meeting_prep.delivery_failed` - When delivery fails after retries
- `meeting_prep.completed` - Final success event

## Future Enhancements (Post-MVP)

1. **User Preferences:** Allow users to customize prep format (verbose vs. concise, slide themes)
2. **Regeneration:** Allow manual regeneration with different focus (e.g., "focus on technical capabilities")
3. **Voice Prep:** Generate audio summary via ElevenLabs for listening on the go
4. **Real-time Updates:** If new research/conversation data arrives <30 min before meeting, send update
5. **Prep Feedback Loop:** Collect post-meeting feedback to improve talking point quality
6. **Competitive Intelligence:** Add competitor analysis section when relevant
7. **Deal Room:** Generate shareable deal room URL with all prep materials
8. **Mobile App:** Push notification delivery option for mobile users

## Security & Compliance

- **Data Privacy:** Prep packages contain PII - use encrypted email delivery
- **Access Control:** Only send prep to assigned meeting owner (validate recipient)
- **Data Retention:** Store prep packages for 90 days, then archive/delete per policy
- **API Key Security:** Gamma API key stored in environment variables, never logged
- **Audit Trail:** All prep deliveries logged with recipient, timestamp, delivery method

## Dependencies (Python Packages)

```toml
# Add to pyproject.toml [project.dependencies]
anthropic = ">=0.75.0"  # Already installed
httpx = ">=0.27.0"      # Already installed
pydantic = ">=2.12.5"   # Already installed

# Gamma client will use BaseIntegrationClient (httpx)
# Email via Python stdlib smtplib or existing integration
# Slack via slack-sdk (check if already installed)
```

## API Endpoints (Optional - for manual trigger)

```python
# In src/main.py
@app.post("/api/meetings/{meeting_id}/prep")
async def trigger_meeting_prep(meeting_id: str):
    """Manually trigger prep generation for a meeting."""
    from src.tasks.meeting_tasks import generate_meeting_prep

    task = generate_meeting_prep.delay(meeting_id)
    return {"task_id": task.id, "status": "queued"}
```

---

**Specification Version:** 1.0
**Created:** 2025-12-05
**Status:** Ready for Implementation
