# Campaign Copywriting Agent - Production Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Created:** 2025-12-05
**Agent Category:** Campaign & Outreach
**Phase:** Phase 1 - MVP Foundation

---

## Overview

The Campaign Copywriting Agent specializes in creating ultra-human, conversational cold email copy that avoids salesy language and corporate jargon. It generates email sequences with multiple A/B test variants while enforcing strict character limits and maintaining authentic tone.

**Key Responsibilities:**
- Generate conversational email sequences (3-5 emails)
- Create 2-3 A/B test variants per email position
- Enforce 125-character maximum per email
- Maintain ultra-human tone (no AI tells, no corporate speak)
- Learn from human edits to improve quality
- Store approved copy in database for campaign use

**Dependencies:**
- Niche Research Agent (provides niche context and pain points)
- Persona Research Agent (provides detailed persona insights)

**Integrations:**
- Claude API (generates email copy)
- Instantly API (pushes approved copy to campaigns)
- Slack API (human review notifications)
- PostgreSQL (stores copy and performance data)
- Zep (memory for learning from edits)

---

## Agent Implementation

### System Prompt

```
You are the Campaign Copywriting Agent for Smarter Team, an AI agency automation system.

Your role is to write cold email copy that sounds like a real person typing naturally on their phone - not a corporation or AI.

CORE PRINCIPLES:
1. Ultra-human tone - Write like you're texting a colleague
2. No AI tells - Avoid phrases like "I hope this email finds you well"
3. No corporate jargon - Skip "synergy," "paradigm," "leverage"
4. Conversational style - Use contractions, simple words, short sentences
5. Not salesy - No exclamation points, no hype, no pressure tactics

CHARACTER LIMITS:
- STRICT maximum: 125 characters per email (including spaces)
- This is extremely short - be concise
- Example: "saw you're hiring for a product manager. i've built 3 similar products at startups"

COPYWRITING RULES:
- Start lowercase (unless proper noun)
- Use simple, everyday language
- Focus on one specific observation or question
- Reference something specific about them or their company
- Make it easy to reply with a simple yes/no or short answer

A/B TEST VARIANTS:
For each email position, create 3 distinct variants:
- Variant A: Direct question approach
- Variant B: Observation + curiosity approach
- Variant C: Personal connection approach

MEMORY AND LEARNING:
- Remember which copy styles get approved
- Learn from human edits to improve future generations
- Track which approaches get higher reply rates

HUMAN REVIEW PROCESS:
1. Generate initial drafts
2. Submit all variants for human review
3. Wait for approval, rejection, or revision notes
4. If approved: store in database
5. If rejected: learn from feedback
6. If revise: incorporate specific feedback

When writing, always ask: "Would I send this to a colleague on my phone?"
```

### User Prompt Templates

#### Template 1: New Email Sequence Generation
```
Task: Generate email sequence for {campaign_name}

Context:
- Niche: {niche_description}
- Target Persona: {persona_description}
- Pain Points: {pain_points}
- Offer: {offer_description}
- Tone Guidelines: {tone_guidelines}

Requirements:
- {sequence_length} email sequence
- 3 A/B variants per email position
- Max 125 characters per email (STRICT)
- Ultra-human, conversational tone
- Reference specific pain points or observations

Please generate the complete sequence with all variants.
```

#### Template 2: Revision Request
```
Task: Revise email copy based on feedback

Original Copy:
{original_copy}

Human Feedback:
{feedback}

Context:
- Email Position: {position}
- Variant: {variant_letter}
- Campaign: {campaign_name}

Please revise this specific variant incorporating the feedback.
```

### Class Structure

**File:** `app/backend/src/agents/campaign_copywriting/agent.py`

```python
from typing import Any, Dict, List
from anthropic import AsyncAnthropic
from src.agents.base_agent import BaseAgent
from src.agents.campaign_copywriting.tools import (
    pull_research_data,
    generate_email_drafts,
    create_ab_variants,
    validate_copy_constraints,
    store_copy_database,
    submit_for_review,
    push_to_instantly,
    analyze_performance,
)
from src.config import get_agent_logger
from src.integrations.slack_client import SlackClient

class CampaignCopywritingAgent(BaseAgent):
    """Agent that writes ultra-human cold email copy with A/B testing variants"""

    def __init__(self):
        super().__init__(
            name="campaign_copywriting",
            description="Writes ultra-human cold email copy with A/B test variants"
        )

        # Initialize Claude client
        self.claude = AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_retries=3,
            timeout=30.0
        )

        # Initialize Slack client for review notifications
        self.slack = SlackClient()

        # Register tools
        self.register_tool(pull_research_data, "pull_research_data")
        self.register_tool(generate_email_drafts, "generate_email_drafts")
        self.register_tool(create_ab_variants, "create_ab_variants")
        self.register_tool(validate_copy_constraints, "validate_copy_constraints")
        self.register_tool(store_copy_database, "store_copy_database")
        self.register_tool(submit_for_review, "submit_for_review")
        self.register_tool(push_to_instantly, "push_to_instantly")
        self.register_tool(analyze_performance, "analyze_performance")

    @property
    def system_prompt(self) -> str:
        return self._get_system_prompt()

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process copywriting tasks"""
        task_type = task.get("type")

        if task_type == "generate_sequence":
            return await self._handle_sequence_generation(task)
        elif task_type == "revise_copy":
            return await self._handle_revision_request(task)
        elif task_type == "analyze_performance":
            return await self._handle_performance_analysis(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
```

---

## Tools

### Tool: pull_research_data
**Purpose:** Retrieve niche and persona research data

**Input Schema:**
```python
from pydantic import BaseModel, Field
from typing import Optional

class PullResearchInput(BaseModel):
    niche_id: str = Field(..., description="Niche research ID")
    persona_id: str = Field(..., description="Persona research ID")
    include_pain_points: bool = Field(default=True)
    include_competitors: bool = Field(default=False)

class PullResearchOutput(BaseModel):
    niche: Dict[str, Any]
    persona: Dict[str, Any]
    pain_points: List[str]
    competitors: Optional[List[Dict[str, Any]]] = None
    retrieval_time_ms: float
```

**Error Handling:**
- Research not found → Return empty with warning, allow manual input
- Database timeout → Retry 3x with exponential backoff
- Invalid ID → Return validation error message

### Tool: generate_email_drafts
**Purpose:** Generate initial email drafts using Claude

**Input Schema:**
```python
class GenerateDraftsInput(BaseModel):
    sequence_length: int = Field(default=3, ge=2, le=5, description="Number of emails in sequence")
    niche_context: Dict[str, Any]
    persona_context: Dict[str, Any]
    offer_details: str = Field(..., max_length=500)
    tone_guidelines: str = Field(default="casual, curious")
    max_chars: int = Field(default=125, ge=50, le=200)

class GenerateDraftsOutput(BaseModel):
    drafts: List[Dict[str, Any]]  # Each draft has position and content
    generation_time_ms: float
    tokens_used: Dict[str, int]  # input, output, total
```

**Error Handling:**
- Claude API error (429) → Exponential backoff, max 5 retries
- Claude API error (5xx) → Retry 3x, then fail gracefully
- Content filter trigger → Log and regenerate with adjusted prompt
- Token limit exceeded → Truncate input and retry

### Tool: create_ab_variants
**Purpose:** Create A/B test variants for each email

**Input Schema:**
```python
class CreateVariantsInput(BaseModel):
    base_drafts: List[Dict[str, Any]]
    variants_per_email: int = Field(default=3, ge=2, le=4)
    approaches: List[str] = Field(
        default=["direct_question", "observation_curiosity", "personal_connection"]
    )

class CreateVariantsOutput(BaseModel):
    variants: Dict[int, List[Dict[str, Any]]]  # position -> variants
    variant_count: int
    creation_time_ms: float
```

**Error Handling:**
- Generation timeout → Retry with shorter variants
- Duplicate variants detected → Regenerate with diversity constraint
- Character limit violation → Auto-truncate and log warning

### Tool: validate_copy_constraints
**Purpose:** Enforce all copywriting rules and constraints

**Input Schema:**
```python
class ValidateInput(BaseModel):
    email_copy: str = Field(..., max_length=200)
    position: int = Field(..., ge=1)
    constraints: Dict[str, Any] = Field(default_factory=dict)

class ValidateOutput(BaseModel):
    is_valid: bool
    violations: List[str]
    suggestions: List[str]
    character_count: int
    ai_tell_score: float  # 0-1, higher means more AI-like
```

**Validation Rules:**
- Character count ≤ 125 (strict)
- No corporate jargon words (list of 100+ words)
- No AI tell phrases (list of 50+ phrases)
- Conversational tone score ≥ 0.7
- Must start with lowercase (unless proper noun)

### Tool: store_copy_database
**Purpose:** Store approved copy in database

**Input Schema:**
```python
class StoreCopyInput(BaseModel):
    campaign_id: str
    sequence_id: str
    variants: List[Dict[str, Any]]
    approval_metadata: Dict[str, Any]

class StoreCopyOutput(BaseModel):
    stored_count: int
    copy_ids: List[str]
    storage_time_ms: float
```

**Error Handling:**
- Database connection → Retry 3x with backoff
- Constraint violation → Log details and skip
- Duplicate detection → Merge with existing record

### Tool: submit_for_review
**Purpose:** Submit generated copy for human approval

**Input Schema:**
```python
class SubmitReviewInput(BaseModel):
    campaign_name: str
    sequence_data: Dict[str, Any]
    reviewer: str = Field(default="campaign_manager")
    deadline_hours: int = Field(default=24)

class SubmitReviewOutput(BaseModel):
    review_id: str
    slack_message_ts: str
    review_url: Optional[str]
    submission_time: str
```

**Error Handling:**
- Slack API failure → Fallback to email notification
- Invalid reviewer → Default to campaign manager
- Message size limit → Split into multiple messages

### Tool: push_to_instantly
**Purpose:** Push approved copy to Instantly campaign

**Input Schema:**
```python
class PushToInstantlyInput(BaseModel):
    campaign_id: str
    sequence_id: str
    approved_variants: List[Dict[str, Any]]

class PushToInstantlyOutput(BaseModel):
    instantly_sequence_id: str
    push_status: str
    pushed_variant_count: int
    api_response: Dict[str, Any]
```

**Error Handling:**
- Instantly API rate limit → Queue for retry after 60s
- Authentication error → Alert ops immediately
- Invalid campaign → Log and create new campaign

### Tool: analyze_performance
**Purpose:** Analyze copy performance for learning

**Input Schema:**
```python
class AnalyzePerformanceInput(BaseModel):
    copy_ids: List[str]
    time_range_days: int = Field(default=30)
    metrics: List[str] = Field(default=["open_rate", "reply_rate", "conversion_rate"])

class AnalyzePerformanceOutput(BaseModel):
    performance_data: Dict[str, Dict[str, float]]
    insights: List[str]
    recommendations: List[str]
    analysis_time_ms: float
```

---

## Error Handling Matrix

| Component | Error Type | Detection | Response | Retry |
|-----------|------------|-----------|----------|-------|
| Claude API | Rate limit (429) | Status code | Exponential backoff | Yes, 5 attempts |
| Claude API | Server error (5xx) | Status code | Log and retry | Yes, 3 attempts |
| Claude API | Content filter | Response flag | Adjust prompt | Yes, 2 attempts |
| Database | Connection timeout | Exception | Retry with backoff | Yes, 3 attempts |
| Database | Constraint violation | DB error | Log and skip | No |
| Instantly API | Rate limit | Status code | Queue for later | Yes, after delay |
| Instantly API | Auth error | Status code | Alert ops | No |
| Slack API | Message too large | Exception | Split message | Yes |
| Validation | Char limit exceeded | Check result | Auto-truncate | No |
| Validation | AI tell detected | Score threshold | Regenerate | Yes, 2 attempts |

---

## Multi-Agent Integration

### Handoff Patterns

1. **From Research Agents:**
   ```python
   # Niche Research Agent provides data
   await self.handoff_to(
       target_agent="campaign_copywriting",
       payload={
           "type": "generate_sequence",
           "niche_id": niche["id"],
           "persona_id": persona["id"],
           "campaign_context": {...}
       },
       priority="normal"
   )
   ```

2. **To Campaign Creation Agent:**
   ```python
   # After copy approval
   await self.handoff_to(
       target_agent="campaign_creation",
       payload={
           "type": "setup_campaign",
           "sequence_id": sequence_id,
           "approved_copy": variants,
           "campaign_config": {...}
       },
       priority="high"
   )
   ```

3. **To Analysis Agent (for learning):**
   ```python
   # After performance data available
   await self.handoff_to(
       target_agent="campaign_analysis",
       payload={
           "type": "learn_from_performance",
           "copy_performance": performance_data,
           "original_prompts": prompts_used
       },
       priority="low"
   )
   ```

---

## Testing Strategy

### Unit Tests

```python
# app/backend/__tests__/unit/agents/test_campaign_copywriting.py

import pytest
from unittest.mock import AsyncMock, patch
from src.agents.campaign_copywriting import CampaignCopywritingAgent

class TestCampaignCopywritingAgent:

    @pytest.fixture
    def agent(self):
        return CampaignCopywritingAgent()

    @pytest.mark.asyncio
    async def test_generate_sequence_happy_path(self, agent):
        """Test successful sequence generation"""
        task = {
            "type": "generate_sequence",
            "campaign_name": "AI Agency Outreach",
            "niche_id": "tech-startups",
            "persona_id": "cto-vp",
            "offer_details": "AI automation consulting",
            "sequence_length": 3
        }

        with patch.object(agent, 'pull_research_data') as mock_research:
            mock_research.return_value = {
                "niche": {"description": "Tech startups"},
                "persona": {"role": "CTO"},
                "pain_points": ["hiring challenges", "scaling issues"]
            }

            with patch.object(agent, 'generate_email_drafts') as mock_generate:
                mock_generate.return_value = {
                    "drafts": [
                        {"position": 1, "content": "saw you're hiring engineers"},
                        {"position": 2, "content": "how's scaling going"},
                        {"position": 3, "content": "want to chat about solutions"}
                    ]
                }

                result = await agent.process_task(task)

                assert result["status"] == "pending_review"
                assert len(result["sequence"]) == 3
                assert all(len(email["content"]) <= 125 for email in result["sequence"])

    @pytest.mark.asyncio
    async def test_character_limit_enforcement(self, agent):
        """Test that 125-character limit is strictly enforced"""
        long_copy = "this is a very long email that exceeds the 125 character limit and should be automatically truncated"

        result = await agent.validate_copy_constraints({
            "email_copy": long_copy,
            "position": 1
        })

        assert not result["is_valid"]
        assert "character limit exceeded" in result["violations"]
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_ai_tell_detection(self, agent):
        """Test detection of AI-like phrases"""
        ai_copy = "I hope this email finds you well. I am writing to inquire about your esteemed organization's strategic initiatives."

        result = await agent.validate_copy_constraints({
            "email_copy": ai_copy,
            "position": 1
        })

        assert result["ai_tell_score"] > 0.5
        assert not result["is_valid"]
        assert any("AI tell" in v for v in result["violations"])

    @pytest.mark.asyncio
    async def test_claude_api_rate_limit_handling(self, agent):
        """Test exponential backoff on Claude API rate limit"""
        with patch('anthropic.AsyncAnthropic') as mock_claude:
            mock_response = AsyncMock()
            mock_response.status_code = 429
            mock_claude.return_value.messages.create.side_effect = [
                Exception("Rate limit exceeded"),
                Exception("Rate limit exceeded"),
                {"content": [{"text": "valid response"}]}
            ]

            result = await agent.generate_email_drafts({
                "niche_context": {},
                "persona_context": {},
                "offer_details": "test offer"
            })

            assert "drafts" in result
            assert mock_claude.return_value.messages.create.call_count == 3

    def test_system_prompt_includes_constraints(self, agent):
        """Verify system prompt contains all critical constraints"""
        prompt = agent.system_prompt

        assert "125 characters" in prompt
        assert "ultra-human" in prompt
        assert "no corporate jargon" in prompt.lower()
        assert "A/B test" in prompt
```

### Integration Tests

```python
# app/backend/__tests__/integration/test_campaign_copywriting_integration.py

import pytest
from testcontainers.postgres import PostgreSqlContainer
from src.agents.campaign_copywriting import CampaignCopywritingAgent
from src.database import get_db_session

class TestCampaignCopywritingIntegration:

    @pytest.fixture(scope="class")
    def postgres_container(self):
        with PostgreSqlContainer("postgres:15") as postgres:
            yield postgres

    @pytest.fixture
    def agent(self, postgres_container):
        # Setup test database
        os.environ["DATABASE_URL"] = postgres_container.get_connection_url()
        return CampaignCopywritingAgent()

    @pytest.mark.asyncio
    async def test_full_workflow_with_database(self, agent):
        """Test complete workflow from generation to storage"""
        # 1. Generate sequence
        task = {
            "type": "generate_sequence",
            "campaign_name": "Test Campaign",
            "niche_id": "test-niche",
            "persona_id": "test-persona",
            "offer_details": "Test offer"
        }

        result = await agent.process_task(task)
        assert result["status"] == "pending_review"

        # 2. Simulate approval
        approval_data = {
            "review_id": result["review_id"],
            "decision": "approved",
            "approved_variants": result["sequence"]
        }

        # 3. Store approved copy
        with get_db_session() as db:
            stored = await agent.store_copy_database({
                "campaign_id": "test-campaign",
                "sequence_id": result["sequence_id"],
                "variants": approval_data["approved_variants"],
                "approval_metadata": approval_data
            })

            assert stored["stored_count"] > 0
            assert len(stored["copy_ids"]) == len(approval_data["approved_variants"])

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, agent):
        """Test graceful error handling throughout workflow"""
        task = {
            "type": "generate_sequence",
            "campaign_name": "Error Test",
            "niche_id": "invalid-id",
            "persona_id": "invalid-id"
        }

        result = await agent.process_task(task)

        # Should handle invalid IDs gracefully
        assert result["status"] in ["error", "pending_manual_input"]
        assert "message" in result
        assert not result.get("sequence")  # No sequence generated on error
```

### Mock Strategy

```python
# app/backend/__tests__/fixtures/campaign_copywriting_fixtures.py

import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_claude_copy_response():
    """Mock Claude API response for copy generation"""
    return {
        "content": [
            {
                "type": "text",
                "text": """Here are 3 email variants for position 1:

Variant A: saw you're hiring for a product manager. i've built 3 similar products at startups.

Variant B: noticed your series B announcement. congrats! scaling team is always the hardest part.

Variant C: your product looks interesting. used something similar at my last startup and learned a lot."""
            }
        ],
        "usage": {"input_tokens": 150, "output_tokens": 80},
        "model": "claude-3-5-sonnet-20241022"
    }

@pytest.fixture
def mock_instantly_api():
    """Mock Instantly API client"""
    mock = AsyncMock()
    mock.create_sequence.return_value = {
        "id": "seq_12345",
        "status": "active",
        "emails": [{"position": i, "id": f"email_{i}"} for i in range(1, 4)]
    }
    return mock

@pytest.fixture
def sample_campaign_copy_data():
    """Sample approved copy data"""
    return {
        "campaign_id": "camp_test_001",
        "sequence_id": "seq_test_001",
        "variants": {
            1: [
                {"variant": "A", "content": "saw you're hiring engineers", "status": "approved"},
                {"variant": "B", "content": "noticed your funding round", "status": "approved"},
                {"variant": "C", "content": "your product looks interesting", "status": "approved"}
            ],
            2: [
                {"variant": "A", "content": "how's the team scaling", "status": "approved"},
                {"variant": "B", "content": "what's your biggest challenge", "status": "approved"},
                {"variant": "C", "content": "need help with tech debt", "status": "approved"}
            ],
            3: [
                {"variant": "A", "content": "want to chat sometime", "status": "approved"},
                {"variant": "B", "content": "free for a quick call", "status": "approved"},
                {"variant": "C", "content": "got 15 mins next week", "status": "approved"}
            ]
        }
    }
```

---

## Performance Requirements

### Latency
- **Sequence generation:** < 10 seconds for 3-email sequence
- **Single variant generation:** < 2 seconds
- **Validation check:** < 100ms
- **Database storage:** < 500ms

### Throughput
- **Concurrent sequences:** Up to 5 simultaneous generations
- **API rate limits:** Respect Claude (50 req/min) and Instantly (100 req/min)

### Token Usage
- **Average per sequence:** 200 input tokens, 300 output tokens
- **Monthly budget:** ~100K tokens for moderate usage
- **Cost optimization:** Use Claude 3 Haiku for initial drafts, Sonnet for final

---

## Observability

### Logging
```python
# Structured logging examples
self.logger.info(
    "Email sequence generated",
    extra={
        "campaign_name": campaign_name,
        "sequence_length": len(sequence),
        "total_variants": variant_count,
        "generation_time_ms": generation_time,
        "tokens_used": token_usage,
        "avg_char_count": avg_chars
    }
)

self.logger.warning(
    "Character limit violations detected",
    extra={
        "email_position": position,
        "char_count": count,
        "limit_exceeded_by": count - 125,
        "action_taken": "auto_truncated"
    }
)
```

### Metrics to Track
- **Generation Metrics:** Success rate, latency, token usage
- **Quality Metrics:** Approval rate, revision requests, AI tell scores
- **Performance Metrics:** Open rates, reply rates, conversion rates by variant
- **Business Metrics:** Campaign success rate, ROI by copy style

---

## Security

### API Key Management
- Claude API key stored in environment variables
- Instantly API key rotated monthly
- All API calls use HTTPS with certificate validation

### Data Sanitization
- Input validation for all user-provided content
- Output sanitization before database storage
- PII detection and masking in logs

### Access Controls
- Copy generation requires campaign assignment
- Approval workflow restricted to authorized users
- Audit trail for all copy modifications

---

## Acceptance Criteria

- [ ] Generates 2-5 email sequences per request
- [ ] Creates exactly 3 A/B variants per email position
- [ ] Enforces strict 125-character limit on all generated copy
- [ ] Detects and prevents AI tell phrases with 95% accuracy
- [ ] Maintains ultra-human tone scoring ≥ 0.8
- [ ] Submits all generated copy for human review before approval
- [ ] Stores approved copy in PostgreSQL with full metadata
- [ ] Pushes approved sequences to Instantly API
- [ ] Handles API failures gracefully with appropriate retries
- [ ] Learns from human edits to improve future generations
- [ ] Provides performance analytics on copy effectiveness
- [ ] Achieves < 10s generation time for 3-email sequences
- [ ] Maintains > 90% uptime for copy generation service
- [ ] All unit tests pass with > 90% code coverage
- [ ] Integration tests cover end-to-end workflows
- [ ] Error recovery scenarios tested and documented

---

## Database Schema

```sql
-- Email copy storage
CREATE TABLE email_copy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id VARCHAR(100) NOT NULL,
    sequence_id VARCHAR(100) NOT NULL,
    email_position INTEGER NOT NULL,
    variant_letter CHAR(1) NOT NULL,
    content TEXT NOT NULL,
    character_count INTEGER NOT NULL,
    ai_tell_score FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by VARCHAR(100),

    CONSTRAINT unique_variant UNIQUE(campaign_id, sequence_id, email_position, variant_letter),
    CONSTRAINT char_limit CHECK (character_count <= 125),
    CONSTRAINT valid_position CHECK (email_position BETWEEN 1 AND 10),
    CONSTRAINT valid_variant CHECK (variant_letter IN ('A', 'B', 'C', 'D'))
);

-- Copy performance tracking
CREATE TABLE copy_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    copy_id UUID REFERENCES email_copy(id),
    sent_date DATE NOT NULL,
    emails_sent INTEGER NOT NULL,
    opens INTEGER NOT NULL,
    replies INTEGER NOT NULL,
    positive_replies INTEGER NOT NULL,
    conversions INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Review tracking
CREATE TABLE copy_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_id VARCHAR(100) NOT NULL,
    reviewer VARCHAR(100) NOT NULL,
    decision VARCHAR(20) NOT NULL, -- approved, rejected, revise
    feedback TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning from edits
CREATE TABLE copy_edits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_copy_id UUID REFERENCES email_copy(id),
    original_content TEXT NOT NULL,
    edited_content TEXT NOT NULL,
    edit_reason TEXT,
    agent_learned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_email_copy_campaign ON email_copy(campaign_id, sequence_id);
CREATE INDEX idx_copy_performance_copy_date ON copy_performance(copy_id, sent_date);
CREATE INDEX idx_copy_reviews_sequence ON copy_reviews(sequence_id);
```
