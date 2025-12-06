# Email Verification Agent - Production Specification

## Metadata

**Agent Name:** `email_verification`
**Category:** Lead Generation & Data
**Priority:** Phase 1 - MVP Foundation
**Dependencies:** Lead List Builder Agent (provides leads with emails)
**Coverage Target:** >85% (agent requirement)

---

## Purpose

Verify email addresses using the Reoon Email Verifier API to ensure lead data quality before campaign launches. Automatically route invalid/risky emails to waterfall enrichment for replacement.

---

## System Prompt

```
You are the Email Verification Agent for Smarter Team, an autonomous AI agency.

Your primary responsibility is to verify the validity of email addresses before they enter marketing campaigns. You ensure high deliverability and protect sender reputation by filtering out invalid, risky, or problematic email addresses.

**Core Responsibilities:**
1. Batch-verify email addresses using the Reoon Email Verifier API
2. Classify emails based on verification status (safe, invalid, risky, unknown)
3. Update lead records with verification results and scores
4. Route invalid/risky emails to the Waterfall Enrichment Agent for replacement
5. Track verification usage to prevent exceeding rate limits (10k/month, alert at 90%)
6. Log all verification actions for audit and quality tracking

**Decision Framework:**
- SAFE/VALID (score ≥80): Mark as VERIFIED, proceed to campaigns
- INVALID (score <40): Mark as INVALID_EMAIL, route to waterfall enrichment
- RISKY (40-79): Mark as RISKY_EMAIL, route to waterfall enrichment for replacement
- UNKNOWN: Mark as UNKNOWN_EMAIL, route to waterfall enrichment
- DISPOSABLE/ROLE_ACCOUNT/CATCH_ALL: Mark accordingly, route to waterfall enrichment

**Quality Standards:**
- Verify emails in batches of 50-500 for efficiency
- Use POWER mode for comprehensive verification (includes inbox checks)
- Log verification scores for data quality analytics
- Alert when approaching rate limit (9k verifications used)
- Never verify the same email twice within 7 days (check cache first)

**Handoff Protocol:**
When emails fail verification or are risky, hand off to the Waterfall Enrichment Agent with:
- Lead ID
- Original email (for reference)
- Verification status and score
- Reason for failure
- Priority: high (to maintain campaign velocity)

You work autonomously but log all decisions for human oversight and system optimization.
```

---

## Agent Implementation

### Class Definition

```python
from src.agents.base_agent import BaseAgent
from src.integrations.reoon import ReoonClient
from src.config import Settings, get_agent_logger
from typing import Any
from datetime import datetime, timedelta
import asyncio

class EmailVerificationAgent(BaseAgent):
    """
    Email Verification Agent - Verifies email addresses with Reoon API.

    Handles batch verification, status routing, and waterfall enrichment handoffs.
    """

    def __init__(self, settings: Settings):
        super().__init__(
            name="email_verification",
            description="Verifies email addresses and routes invalid/risky emails to enrichment"
        )
        self.reoon = ReoonClient(api_key=settings.REOON_API_KEY)
        self.settings = settings
        self.rate_limit_threshold = 9000  # Alert at 90% of 10k

    @property
    def system_prompt(self) -> str:
        return """[See System Prompt section above]"""

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Process email verification task."""
        task_type = task.get("type")

        if task_type == "verify_batch":
            return await self._verify_batch(task)
        elif task_type == "verify_single":
            return await self._verify_single(task)
        elif task_type == "check_rate_limit":
            return await self._check_rate_limit()
        else:
            raise ValueError(f"Unknown task type: {task_type}")
```

---

## Tools

### 1. `verify_email_batch`

**Purpose:** Verify multiple email addresses in a single batch operation

**Input Schema:**
```python
from pydantic import BaseModel, Field, conlist
from typing import Literal, Optional
from uuid import UUID
from datetime import datetime

class VerifyBatchInput(BaseModel):
    """Input for email batch verification."""

    lead_ids: conlist(UUID, min_length=1, max_length=500) = Field(
        ...,
        description="List of lead IDs to verify (max 500 per batch)"
    )
    mode: Literal["quick", "power"] = Field(
        default="power",
        description="Verification mode: quick (0.5s) or power (deep)"
    )
    batch_size: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Number of emails per API call"
    )
    skip_recent: bool = Field(
        default=True,
        description="Skip emails verified in last 7 days"
    )
    force_verify: bool = Field(
        default=False,
        description="Force verification even if recently verified"
    )

class VerificationResult(BaseModel):
    """Individual email verification result."""

    lead_id: UUID
    email: str
    status: Literal[
        "safe", "invalid", "risky", "unknown",
        "disposable", "role_account", "catch_all",
        "spamtrap", "inbox_full", "disabled", "error"
    ]
    score: Optional[int] = Field(None, ge=0, le=100)
    reason: Optional[str] = None
    verified_at: datetime
    api_credits_used: int = 1

class VerifyBatchOutput(BaseModel):
    """Output from batch email verification."""

    # Summary counts
    total_submitted: int
    verified_count: int
    safe_count: int
    invalid_count: int
    risky_count: int
    unknown_count: int
    skipped_count: int
    error_count: int

    # Details
    verification_ids: list[UUID]
    results: list[VerificationResult]

    # Handoffs to other agents
    handoff_task_ids: list[str]
    handoff_count: int

    # Rate limiting
    rate_limit_remaining: int
    api_credits_used: int

    # Processing info
    processing_time_seconds: float
    batch_id: str

    # Errors
    errors: list[dict] = Field(default_factory=list)
```

**Error Handling:**
| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Invalid input | Pydantic validation | Return validation error | No |
| Lead not found | Database query | Skip with warning | No |
| Rate limit exceeded | API response 429 | Stop processing, alert | No |
| API server error | HTTP 5xx | Retry with backoff | Yes, 3 attempts |
| Network timeout | httpx.TimeoutError | Retry with longer timeout | Yes, 2 attempts |
| Partial batch failure | Mixed results | Process successful, log failures | Continue |

**Implementation Pattern:**
```python
async def verify_email_batch(self, input: VerifyBatchInput) -> VerifyBatchOutput:
    """
    Verify a batch of email addresses using Reoon API.

    Process:
    1. Validate input
    2. Check rate limit
    3. Load leads from database
    4. Check verification cache
    5. Call Reoon bulk API
    6. Poll for results
    7. Save to database
    8. Update lead records
    9. Route failed emails to enrichment
    10. Return summary
    """
    batch_id = str(uuid4())
    start_time = time.time()

    # 1. Check rate limit first
    usage = await self.check_rate_limit_usage()
    if usage["remaining"] < len(input.lead_ids):
        raise RateLimitExceededError(
            f"Insufficient credits: {usage['remaining']} remaining, "
            f"{len(input.lead_ids)} requested"
        )

    # 2-10. Implementation continues...
```

### 2. `check_verification_cache`

**Purpose:** Check if email was recently verified to avoid duplicate API calls

**Input Schema:**
```python
class CheckCacheInput(BaseModel):
    """Input for verification cache check."""

    email: str = Field(..., description="Email address to check")
    max_age_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Maximum age of cached result in days"
    )

class CheckCacheOutput(BaseModel):
    """Output from verification cache check."""

    cached: bool = Field(..., description="Whether result is cached")
    verification_id: Optional[UUID] = None
    status: Optional[str] = None
    score: Optional[int] = None
    verified_at: Optional[datetime] = None
    age_days: Optional[int] = None
    should_verify: bool = Field(..., description="Whether to verify this email")
```

**Error Handling:**
- Invalid email format → Return `should_verify: False` with reason
- Database error → Log error, return `should_verify: True` (verify anyway)
- Cache corruption → Log warning, return `should_verify: True`

### 3. `route_failed_emails`

**Purpose:** Route invalid/risky emails to Waterfall Enrichment Agent

**Input Schema:**
```python
class RouteFailedInput(BaseModel):
    """Input for routing failed emails to enrichment."""

    verification_ids: conlist(UUID, min_length=1) = Field(
        ...,
        description="Verification IDs to route"
    )
    priority: Literal["critical", "high", "normal", "low"] = Field(
        default="high",
        description="Handoff priority"
    )
    batch_size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Emails per enrichment batch"
    )

class EnrichmentHandoffPayload(BaseModel):
    """Payload for enrichment handoff."""

    lead_id: UUID
    original_email: str
    verification_status: str
    verification_score: Optional[int]
    failure_reason: Optional[str]
    requested_at: datetime
    verification_id: UUID

class RouteFailedOutput(BaseModel):
    """Output from failed email routing."""

    handoff_count: int
    task_ids: list[str]
    payloads: list[EnrichmentHandoffPayload]
    errors: list[dict]
    processing_time_ms: float
```

**Error Handling:**
- Missing verification → Log error, skip
- Handoff failure → Retry once, then log for manual review
- Missing target agent → Queue for retry when available

### 4. `check_rate_limit_usage`

**Purpose:** Monitor Reoon API usage and alert when approaching limit

**Input Schema:**
```python
class CheckRateLimitInput(BaseModel):
    """Input for rate limit check."""

    alert_threshold: float = Field(
        default=0.9,
        ge=0.5,
        le=1.0,
        description="Alert threshold as percentage (0.5-1.0)"
    )

class RateLimitStatus(BaseModel):
    """Current rate limit status."""

    current_usage: int = Field(..., ge=0)
    monthly_limit: int = Field(..., gt=0)
    remaining: int = Field(..., ge=0)
    percentage_used: float = Field(..., ge=0, le=1)
    alert_triggered: bool
    reset_date: datetime
    days_until_reset: int

class CheckRateLimitOutput(BaseModel):
    """Output from rate limit check."""

    status: RateLimitStatus
    can_verify_count: int = Field(..., description="How many emails can be verified")
    recommended_batch_size: int
    should_throttle: bool
```

**Error Handling:**
- API unavailable → Return cached usage if <1hr old
- Invalid response → Log error, assume 90% used (safe default)

---

## Database Schema

### `email_verifications` Table

```sql
CREATE TABLE email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Lead Reference
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,

    -- Verification Details
    status VARCHAR(50) NOT NULL,  -- safe, invalid, risky, unknown, disposable, role_account, catch_all, spamtrap, inbox_full, disabled
    mode VARCHAR(20) NOT NULL,    -- quick, power
    overall_score INTEGER,        -- 0-100 score from Reoon

    -- Reoon API Response (JSONB for flexibility)
    raw_response JSONB,

    -- MX and Domain Data
    mx_records JSONB,
    domain_valid BOOLEAN,
    is_disposable BOOLEAN DEFAULT FALSE,
    is_role_account BOOLEAN DEFAULT FALSE,
    is_catch_all BOOLEAN DEFAULT FALSE,
    inbox_full BOOLEAN DEFAULT FALSE,

    -- Routing
    routed_to_enrichment BOOLEAN DEFAULT FALSE,
    enrichment_task_id VARCHAR(100),  -- Celery task ID

    -- Rate Limiting
    api_credits_used INTEGER DEFAULT 1,

    -- Timestamps
    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes for performance
    INDEX idx_email_verifications_lead_id (lead_id),
    INDEX idx_email_verifications_email (email),
    INDEX idx_email_verifications_status (status),
    INDEX idx_email_verifications_verified_at (verified_at),

    -- Prevent duplicate verifications within 7 days
    UNIQUE (email, verified_at::date)
);
```

### `verification_results` Table (Aggregated Stats)

```sql
CREATE TABLE verification_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Time Period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,

    -- Counts
    total_verified INTEGER DEFAULT 0,
    safe_count INTEGER DEFAULT 0,
    invalid_count INTEGER DEFAULT 0,
    risky_count INTEGER DEFAULT 0,
    unknown_count INTEGER DEFAULT 0,
    disposable_count INTEGER DEFAULT 0,
    role_account_count INTEGER DEFAULT 0,

    -- Metrics
    safe_percentage DECIMAL(5,2),
    average_score DECIMAL(5,2),

    -- Rate Limiting
    api_credits_used INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_verification_results_period (period_start, period_end)
);
```

### Lead Table Updates

Add to existing `leads` table:

```sql
ALTER TABLE leads ADD COLUMN email_verification_status VARCHAR(50);
ALTER TABLE leads ADD COLUMN email_verification_score INTEGER;
ALTER TABLE leads ADD COLUMN email_last_verified_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN email_verification_id UUID REFERENCES email_verifications(id);

CREATE INDEX idx_leads_email_verification_status ON leads(email_verification_status);
```

---

## Integration: Reoon Client

### Implementation

```python
from src.integrations.base import BaseIntegrationClient
from typing import Any, Literal

class ReoonClient(BaseIntegrationClient):
    """
    Reoon Email Verifier API client.

    Docs: https://www.reoon.com/articles/api-documentation-of-reoon-email-verifier/
    """

    def __init__(self, api_key: str):
        super().__init__(
            name="reoon",
            base_url="https://emailverifier.reoon.com/api/v1",
            api_key=api_key,
            timeout=60.0  # Verification can take time
        )

    async def verify_single(
        self,
        email: str,
        mode: Literal["quick", "power"] = "power"
    ) -> dict[str, Any]:
        """
        Verify a single email address.

        Args:
            email: Email address to verify
            mode: "quick" (0.5s, basic) or "power" (deep verification)

        Returns:
            {
                "email": str,
                "status": str,  # safe, invalid, disabled, disposable, inbox_full, catch_all, role_account, spamtrap, unknown
                "overall_score": int  # 0-100
            }

        Raises:
            httpx.HTTPStatusError: On API errors
        """
        endpoint = f"/verify?email={email}&mode={mode}&key={self.api_key}"
        return await self.get(endpoint)

    async def verify_bulk(
        self,
        emails: list[str],
        mode: Literal["quick", "power"] = "power",
        task_name: str | None = None
    ) -> dict[str, Any]:
        """
        Start a bulk verification task.

        Args:
            emails: List of email addresses (max 500 per batch recommended)
            mode: "quick" or "power"
            task_name: Optional name for the verification task

        Returns:
            {
                "task_id": str,
                "status": str,  # waiting, running, completed
                "count_total": int,
                "count_checked": int
            }
        """
        payload = {
            "emails": emails,
            "mode": mode,
            "name": task_name or f"batch_{datetime.now().isoformat()}"
        }
        return await self.post("/bulk-verify", json=payload)

    async def get_bulk_results(self, task_id: str) -> dict[str, Any]:
        """
        Retrieve results from a bulk verification task.

        Args:
            task_id: Task ID from verify_bulk()

        Returns:
            {
                "task_id": str,
                "status": str,
                "count_total": int,
                "count_checked": int,
                "results": [
                    {
                        "email": str,
                        "status": str,
                        "overall_score": int
                    },
                    ...
                ]
            }
        """
        endpoint = f"/get-result-bulk-verification-task/?key={self.api_key}&task_id={task_id}"
        return await self.get(endpoint)

    async def get_usage_stats(self) -> dict[str, Any]:
        """
        Get current API usage statistics.

        Returns:
            {
                "current_usage": int,
                "monthly_limit": int,
                "remaining": int,
                "reset_date": datetime
            }
        """
        # Note: This endpoint may need to be confirmed with Reoon docs
        return await self.get(f"/usage?key={self.api_key}")
```

---

## Error Handling Strategy

### 1. API Errors

**Scenario:** Reoon API returns 4xx/5xx errors

**Handling:**
- Log error with full context (lead_ids, email count, mode, retry_count)
- Retry with exponential backoff: 1s → 2s → 4s (max 3 retries)
- If persistent failure, mark verification as "error" status
- Alert human operators after 3 consecutive failures
- Store error details in `raw_response` JSONB field
- For 429 (rate limit): check remaining credits immediately

**Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError)
)
async def _verify_with_retry(self, email: str, mode: str) -> dict:
    try:
        return await self.reoon.verify_single(email, mode=mode)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # Rate limit hit - check actual usage
            usage = await self.reoon.get_usage_stats()
            self.logger.warning(
                "Rate limit hit during verification",
                extra={
                    "email": email,
                    "status_code": e.response.status_code,
                    "remaining_credits": usage.get("remaining", 0),
                    "response": e.response.text[:500]
                }
            )
        raise
    except httpx.TimeoutException as e:
        self.logger.warning(
            "Verification timeout",
            extra={"email": email, "timeout": e.args[0] if e.args else "unknown"}
        )
        raise
```

### 2. Rate Limit Exceeded

**Scenario:** Monthly limit of 10k verifications reached

**Handling:**
- Check usage before each batch
- If >9k used, alert via logger and stop verification
- Return specific error to calling process with reset date
- Store unverified leads for next month or alternative verification
- Implement backpressure: delay new verification requests until reset

**Implementation:**
```python
class RateLimitExceededError(Exception):
    """Raised when Reoon API rate limit is exceeded."""

    def __init__(self, message: str, usage: dict, reset_date: datetime):
        super().__init__(message)
        self.usage = usage
        self.reset_date = reset_date
        self.hours_until_reset = (reset_date - datetime.now()).total_seconds() / 3600

async def _check_rate_limit(self, requested_credits: int) -> None:
    """Check if we have enough credits for the requested operation."""
    usage = await self.reoon.get_usage_stats()
    remaining = usage.get("remaining", 0)

    if remaining < requested_credits:
        self.logger.critical(
            "Rate limit would be exceeded",
            extra={
                "requested": requested_credits,
                "remaining": remaining,
                "percentage_used": usage.get("percentage_used", 0),
                "reset_date": usage.get("reset_date")
            }
        )
        raise RateLimitExceededError(
            f"Insufficient credits: {remaining} remaining, {requested_credits} requested",
            usage,
            usage.get("reset_date")
        )
```

### 3. Invalid Email Format

**Scenario:** Email fails basic syntax validation

**Handling:**
- Perform client-side validation before API call
- Mark as "invalid" without using API credits
- Skip API call and save credits
- Log validation failure with specific reason
- Handle edge cases: international domains, plus signs, quotes

**Validation Pattern:**
```python
import re
from typing import Tuple, Optional

class EmailValidator:
    """Comprehensive email validation."""

    # Basic pattern (catches most errors)
    BASIC_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    # More comprehensive pattern (for edge cases)
    ADVANCED_REGEX = re.compile(
        r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}'
        r'[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    )

    @classmethod
    def validate(cls, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format.

        Returns:
            (is_valid, error_reason)
        """
        if not email or len(email) > 254:
            return False, "invalid_length"

        if not cls.BASIC_REGEX.match(email):
            return False, "syntax_error"

        # Check for common invalid patterns
        if '..' in email:
            return False, "consecutive_dots"

        if email.startswith('.') or email.endswith('.'):
            return False, "leading_trailing_dot"

        if '@.' in email or '.@' in email:
            return False, "invalid_dot_placement"

        return True, None
```

### 4. Database Errors

**Scenario:** Failed to save verification results to database

**Handling:**
- Log error with verification data for manual recovery
- Retry transaction (max 2 retries) with exponential backoff
- If failure persists, store in Redis cache temporarily (TTL: 24h)
- Alert for investigation with full context
- Implement circuit breaker pattern for persistent DB issues

**Implementation:**
```python
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import redis.asyncio as redis

async def _save_with_fallback(
    self,
    verification_data: dict,
    session: AsyncSession
) -> UUID:
    """Save verification with Redis fallback."""
    try:
        return await self._save_to_database(verification_data, session)
    except (SQLAlchemyError, OperationalError) as e:
        self.logger.error(
            "Database save failed, using Redis fallback",
            extra={
                "verification_id": verification_data.get("id"),
                "error": str(e),
                "email": verification_data.get("email")
            }
        )

        # Store in Redis for later recovery
        redis_client = redis.from_url(self.settings.REDIS_URL)
        await redis_client.setex(
            f"verification_fallback:{verification_data['id']}",
            86400,  # 24 hours
            json.dumps(verification_data, default=str)
        )

        # Raise for retry
        raise
```

### 5. Missing Lead Records

**Scenario:** Lead ID doesn't exist in database

**Handling:**
- Log warning with lead_id and context
- Skip verification for that lead
- Continue processing batch
- Return error in results summary
- Track orphaned verifications for data cleanup

### 6. Network Timeouts

**Scenario:** Reoon API doesn't respond within timeout

**Handling:**
- Initial timeout: 30s (quick), 60s (power)
- Retry with increased timeout: 45s (quick), 90s (power)
- Log timeout event with request details
- If repeated timeouts (>10% of requests), reduce batch size
- Implement adaptive timeout based on recent performance

### 7. Bulk API Polling Issues

**Scenario:** Bulk verification task doesn't complete or polling fails

**Handling:**
- Maximum poll time: 5 minutes for quick mode, 15 minutes for power mode
- Poll interval: 2s (first 30s) → 5s (next 2min) → 10s (after)
- If timeout, check task status one final time
- If still running, mark as "unknown" and log for manual review
- Implement webhook support for future (Phase 2)

### 8. Partial Batch Failures

**Scenario:** Some emails in batch fail while others succeed

**Handling:**
- Process all successful results normally
- Group failed emails by error type
- Retry transient failures (timeouts, 5xx) in smaller batches
- Log permanent failures (invalid, domain not found)
- Return comprehensive results with both success and failure counts

### 9. Memory Management for Large Batches

**Scenario:** Processing 500+ emails causes memory issues

**Handling:**
- Stream results from Reoon API (if supported)
- Process in chunks of 100 emails
- Use generators instead of lists where possible
- Monitor memory usage and auto-throttle if >500MB
- Implement backpressure when queue is full

---

## Testing Requirements

### Unit Tests (`__tests__/unit/agents/test_email_verification_agent.py`)

**Coverage Target:** >85%

```python
import pytest
from src.agents.email_verification_agent import EmailVerificationAgent

class TestEmailVerificationAgent:

    @pytest.mark.asyncio
    async def test_initialization(self, mock_settings):
        """Test agent initializes with correct name and description."""
        agent = EmailVerificationAgent(mock_settings)
        assert agent.name == "email_verification"
        assert agent.reoon is not None

    @pytest.mark.asyncio
    async def test_verify_batch_success(self, agent, mock_leads, mock_reoon_response):
        """Test successful batch verification."""
        result = await agent.verify_email_batch(
            lead_ids=[lead.id for lead in mock_leads],
            mode="power"
        )
        assert result["verified_count"] == len(mock_leads)
        assert result["safe_count"] > 0

    @pytest.mark.asyncio
    async def test_verify_batch_handles_invalid_emails(self, agent, mock_invalid_leads):
        """Test batch verification routes invalid emails to enrichment."""
        result = await agent.verify_email_batch(
            lead_ids=[lead.id for lead in mock_invalid_leads]
        )
        assert result["invalid_count"] > 0
        assert len(result["handoff_task_ids"]) > 0

    @pytest.mark.asyncio
    async def test_cache_skip_recent_verifications(self, agent, mock_recent_verification):
        """Test that recently verified emails are skipped."""
        result = await agent.verify_email_batch(
            lead_ids=[mock_recent_verification.lead_id],
            skip_recent=True
        )
        assert result["skipped_count"] == 1

    @pytest.mark.asyncio
    async def test_rate_limit_check(self, agent, mock_high_usage):
        """Test rate limit monitoring and alerting."""
        result = await agent.check_rate_limit_usage()
        assert result["alert_triggered"] is True
        assert result["percentage_used"] >= 90

    @pytest.mark.asyncio
    async def test_handoff_to_enrichment(self, agent, mock_failed_verifications):
        """Test handoff to waterfall enrichment agent."""
        result = await agent.route_failed_emails(
            verification_ids=[v.id for v in mock_failed_verifications],
            priority="high"
        )
        assert result["handoff_count"] == len(mock_failed_verifications)
        assert all(isinstance(tid, str) for tid in result["task_ids"])

    @pytest.mark.asyncio
    async def test_invalid_task_type_raises_error(self, agent):
        """Test unknown task type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown task type"):
            await agent.process_task({"type": "invalid_type"})

    @pytest.mark.asyncio
    async def test_system_prompt_exists(self, agent):
        """Test system prompt is defined."""
        assert len(agent.system_prompt) > 100
        assert "Email Verification Agent" in agent.system_prompt
```

### Integration Tests (`__tests__/integration/test_email_verification_integration.py`)

```python
import pytest
from src.agents.email_verification_agent import EmailVerificationAgent
from src.integrations.reoon import ReoonClient

class TestEmailVerificationIntegration:

    @pytest.mark.asyncio
    async def test_reoon_api_verify_single(self, reoon_client, test_email):
        """Test Reoon API single verification (requires API key)."""
        result = await reoon_client.verify_single(test_email, mode="quick")
        assert "email" in result
        assert "status" in result
        assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_reoon_api_bulk_verification(self, reoon_client, test_emails):
        """Test Reoon API bulk verification flow."""
        # Start bulk task
        task = await reoon_client.verify_bulk(test_emails, mode="power")
        assert "task_id" in task

        # Poll for results
        import asyncio
        await asyncio.sleep(5)  # Wait for processing

        results = await reoon_client.get_bulk_results(task["task_id"])
        assert results["status"] in ["running", "completed"]

    @pytest.mark.asyncio
    async def test_database_verification_record_creation(self, agent, db_session, test_lead):
        """Test verification creates database record."""
        await agent.verify_email_batch([test_lead.id])

        verification = db_session.query(EmailVerification).filter_by(
            lead_id=test_lead.id
        ).first()

        assert verification is not None
        assert verification.status in ["safe", "invalid", "risky", "unknown"]

    @pytest.mark.asyncio
    async def test_full_verification_workflow(self, agent, db_session, test_leads):
        """Test complete verification workflow from batch to handoff."""
        result = await agent.verify_email_batch(
            lead_ids=[lead.id for lead in test_leads]
        )

        # Check verifications created
        verifications = db_session.query(EmailVerification).filter(
            EmailVerification.lead_id.in_([lead.id for lead in test_leads])
        ).all()

        assert len(verifications) == result["verified_count"]

        # Check failed emails routed to enrichment
        failed_verifications = [v for v in verifications if v.routed_to_enrichment]
        assert len(failed_verifications) == len(result["handoff_task_ids"])
```

### Fixtures (`__tests__/fixtures/email_verification_fixtures.py`)

```python
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

@pytest.fixture
def mock_leads():
    """Mock lead records with emails to verify."""
    return [
        {"id": uuid4(), "email": "valid@example.com"},
        {"id": uuid4(), "email": "test@company.com"},
        {"id": uuid4(), "email": "contact@startup.io"},
    ]

@pytest.fixture
def mock_invalid_leads():
    """Mock leads with invalid emails."""
    return [
        {"id": uuid4(), "email": "invalid@fakeemail.com"},
        {"id": uuid4(), "email": "bounced@badomain.xyz"},
    ]

@pytest.fixture
def mock_reoon_response():
    """Mock Reoon API response."""
    return {
        "email": "test@example.com",
        "status": "safe",
        "overall_score": 95
    }

@pytest.fixture
def mock_recent_verification():
    """Mock recent verification (within 7 days)."""
    return {
        "id": uuid4(),
        "lead_id": uuid4(),
        "email": "recent@example.com",
        "status": "safe",
        "verified_at": datetime.now() - timedelta(days=3)
    }

@pytest.fixture
def mock_high_usage():
    """Mock high API usage (>90%)."""
    return {
        "current_usage": 9500,
        "monthly_limit": 10000,
        "remaining": 500,
        "percentage_used": 95.0
    }
```

---

## Implementation Checklist

### Phase 1: Foundation (Day 1-2)

- [ ] Create agent directory: `src/agents/email_verification/`
- [ ] Implement `EmailVerificationAgent` class extending `BaseAgent`
- [ ] Define `system_prompt` property
- [ ] Implement basic `process_task()` method with task routing
- [ ] Create Reoon integration client in `src/integrations/reoon.py`
- [ ] Write unit tests for agent initialization
- [ ] Run `make check` - ensure all quality gates pass

### Phase 2: Database Schema (Day 2)

- [ ] Create migration: `make migration name="add_email_verification_tables"`
- [ ] Define `email_verifications` table schema
- [ ] Define `verification_results` table schema
- [ ] Add columns to `leads` table
- [ ] Create necessary indexes
- [ ] Apply migration: `make migrate`
- [ ] Write unit tests for schema validation

### Phase 3: Reoon Integration (Day 3)

- [ ] Implement `ReoonClient.verify_single()`
- [ ] Implement `ReoonClient.verify_bulk()`
- [ ] Implement `ReoonClient.get_bulk_results()`
- [ ] Implement `ReoonClient.get_usage_stats()`
- [ ] Add error handling with retry logic
- [ ] Write integration tests (mark with `@pytest.mark.integration`)
- [ ] Test with real Reoon API (use test credits)

### Phase 4: Core Tools (Day 4-5)

- [ ] Implement `verify_email_batch()` tool
  - [ ] Load leads from database
  - [ ] Check verification cache
  - [ ] Call Reoon API (bulk or single)
  - [ ] Parse and store results
  - [ ] Update lead records
  - [ ] Calculate statistics
- [ ] Implement `check_verification_cache()` tool
- [ ] Implement `route_failed_emails()` tool with handoff
- [ ] Implement `check_rate_limit_usage()` tool
- [ ] Register all tools in agent initialization
- [ ] Write unit tests for each tool (>90% coverage)

### Phase 5: Error Handling (Day 5-6)

- [ ] Add API error handling with retries
- [ ] Add rate limit checking and alerting
- [ ] Add email syntax validation (client-side)
- [ ] Add database error handling
- [ ] Add timeout handling
- [ ] Write error scenario tests
- [ ] Test all error paths

### Phase 6: Integration & Testing (Day 6-7)

- [ ] Write integration tests for full workflow
- [ ] Create test fixtures for all scenarios
- [ ] Test batch processing with 100+ emails
- [ ] Test cache behavior (skip recent verifications)
- [ ] Test handoff to waterfall enrichment agent
- [ ] Test rate limit alerting at 90%
- [ ] Run `make test` - achieve >85% coverage
- [ ] Generate coverage report: `make test-html`

### Phase 7: Documentation & Quality (Day 7)

- [ ] Update agent docstrings
- [ ] Add inline code comments for complex logic
- [ ] Update CLAUDE.md with new agent
- [ ] Run `make check` - all quality gates pass
- [ ] Run `make lint-fix` and `make format`
- [ ] Run `mypy` type checking - zero errors
- [ ] Review logging - ensure structured logging throughout
- [ ] Move task to `_completed/`
- [ ] Update `tasks/TASK-LOG.md`

---

## Quality Gates

**All must pass before merging:**

- [ ] All unit tests pass (`pytest __tests__/unit/agents/test_email_verification*`)
- [ ] All integration tests pass (`pytest __tests__/integration/test_email_verification*`)
- [ ] Coverage ≥85% for agent code
- [ ] Coverage ≥90% for tools
- [ ] No linting errors (`ruff check`)
- [ ] No type errors (`mypy --strict`)
- [ ] No formatting issues (`ruff format --check`)
- [ ] All database migrations apply cleanly
- [ ] Rate limit monitoring works correctly
- [ ] Handoff to enrichment agent tested
- [ ] Error handling covers all scenarios
- [ ] Logging structured and complete

---

## Performance Targets

- **Single Verification:** <1s (quick mode), <3s (power mode)
- **Batch Verification (100 emails):** <30s (bulk API)
- **Database Writes:** <100ms per record
- **Cache Lookup:** <10ms
- **Rate Limit Check:** <50ms
- **Memory Usage:** <256MB for 500 email batch

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Verification Volume:** Emails verified per day/week/month
2. **Status Distribution:** % safe vs invalid vs risky
3. **Average Score:** Overall quality of lead data
4. **Rate Limit Usage:** % of monthly limit used
5. **API Errors:** Error rate and types
6. **Handoff Volume:** Emails routed to enrichment
7. **Cache Hit Rate:** % of verifications skipped (recent)

### Alert Conditions

- Rate limit usage >90% (critical)
- API error rate >5% (warning)
- Average score drops below 60 (warning)
- Invalid email rate >30% (investigate data source)
- API timeout rate >10% (warning)

---

## Dependencies

### Python Packages (add to `pyproject.toml`)

```toml
[project.dependencies]
# Existing dependencies...
# No new packages needed - httpx already included
```

### Environment Variables (add to `.env`)

```bash
# Reoon Email Verifier
REOON_API_KEY=your_api_key_here  # Required
```

### Database Migration

```bash
make migration name="add_email_verification_tables"
make migrate
```

---

## API Endpoints (Future - Phase 2+)

If exposing verification via REST API:

```python
# FastAPI routes (future)
POST /api/verifications/batch
GET /api/verifications/{id}
GET /api/verifications/stats
GET /api/verifications/rate-limit
```

---

## Related Agents

**Upstream (provides data to this agent):**
- Lead List Builder Agent → Provides leads with emails to verify

**Downstream (receives data from this agent):**
- Waterfall Email Enrichment Agent → Receives invalid/risky emails for replacement
- Campaign Creation Agent → Receives verified leads for campaigns

---

## References

- [Reoon API Documentation](https://www.reoon.com/articles/api-documentation-of-reoon-email-verifier/)
- [Email Verification Status Meanings](https://www.reoon.com/articles/meaning-of-different-email-verification-statuses/)
- BaseAgent Pattern: `/app/backend/src/agents/base_agent.py`
- BaseIntegrationClient: `/app/backend/src/integrations/base.py`
- Project Conventions: `CLAUDE.md`

---

## Notes

- Use POWER mode by default for comprehensive verification (includes inbox checks)
- Cache verifications for 7 days to avoid duplicate API calls
- Alert at 9000 verifications (90% of 10k monthly limit)
- Batch size recommendation: 100-500 emails per bulk API call
- Always route risky/invalid emails to waterfall enrichment (don't discard)
- Log all verification decisions for audit and quality tracking
- Consider implementing webhook support for async bulk results (Phase 2+)

---

**Specification Version:** 1.0
**Last Updated:** 2025-12-05
**Status:** Ready for Implementation
