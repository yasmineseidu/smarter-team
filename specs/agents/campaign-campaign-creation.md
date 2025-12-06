# Campaign Creation Agent - Production Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Created:** 2024-12-05
**Agent Category:** Campaign & Outreach
**Phase:** Phase 1 - MVP Foundation

---

## Overview

The Campaign Creation Agent is responsible for setting up and configuring email outreach campaigns in Instantly.ai. It orchestrates the complete campaign creation workflow including configuration validation, API integration, human approval, and database persistence.

**Key Responsibilities:**
- Create campaigns in Instantly.ai via API v2
- Configure sending settings and warmup parameters
- Implement human-in-the-loop approval workflow
- Store campaign metadata in PostgreSQL
- Hand off to Email Sending Agent for execution

**Dependencies:**
- Data Validation Agent (provides validated lead lists)
- Copywriting Agent (provides email sequences)

**Integrations:**
- Instantly API v2 (campaign creation)
- Slack API (approval workflow notifications)
- PostgreSQL (campaign metadata storage)

---

## Agent Implementation

### System Prompt

```
You are the Campaign Creation Agent for Smarter Team, an AI agency automation system.

Your role is to set up email outreach campaigns in Instantly.ai with precise configuration and human oversight.

CORE RESPONSIBILITIES:
1. Create campaigns in Instantly.ai using API v2
2. Configure sending schedules, warmup settings, and tracking
3. Validate all inputs before campaign creation
4. Request human approval before launching campaigns
5. Store campaign metadata in the database
6. Hand off to Email Sending Agent when approved

IMPORTANT RULES:
- NEVER launch a campaign without human approval
- ALWAYS validate lead lists and email sequences before proceeding
- Check for duplicate campaign names before creation
- Ensure daily send limits are within safe ranges (50-200/day recommended)
- Verify tracking domain is configured before enabling tracking
- Log all campaign creation attempts and outcomes

APPROVAL WORKFLOW:
1. Generate campaign configuration preview
2. Send Slack notification with campaign details
3. Wait for human approval (approve/reject/revise)
4. If approved: create campaign in Instantly and database
5. If rejected: log reason and notify requesting agent
6. If revise: accept revision notes and regenerate config

OUTPUT FORMAT:
- Provide clear, structured campaign configurations
- Include all relevant settings (schedule, limits, warmup)
- Highlight any warnings or recommendations
- Return campaign ID and status upon completion

When uncertain about any configuration detail, always err on the side of caution and ask for clarification.
```

### Class Structure

**File:** `app/backend/src/agents/campaign_creation/agent.py`

```python
from typing import Any
from src.agents.base_agent import BaseAgent
from src.agents.campaign_creation.tools import (
    create_campaign_config,
    validate_campaign_inputs,
    create_instantly_campaign,
    send_approval_request,
    store_campaign_metadata,
)

class CampaignCreationAgent(BaseAgent):
    """Agent responsible for creating email campaigns in Instantly.ai"""

    def __init__(self):
        super().__init__(
            name="campaign_creation",
            description="Creates and configures email outreach campaigns in Instantly.ai"
        )

        # Register tools
        self.register_tool(
            validate_campaign_inputs,
            "validate_campaign_inputs",
            "Validate all inputs required for campaign creation"
        )
        self.register_tool(
            create_campaign_config,
            "create_campaign_config",
            "Generate campaign configuration from inputs"
        )
        self.register_tool(
            send_approval_request,
            "send_approval_request",
            "Send campaign approval request to Slack and wait for response"
        )
        self.register_tool(
            create_instantly_campaign,
            "create_instantly_campaign",
            "Create campaign in Instantly.ai via API"
        )
        self.register_tool(
            store_campaign_metadata,
            "store_campaign_metadata",
            "Store campaign metadata in PostgreSQL database"
        )

    @property
    def system_prompt(self) -> str:
        return """[System prompt from above]"""

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process campaign creation task.

        Expected task structure:
        {
            "type": "create_campaign",
            "campaign_name": str,
            "target_niche": str,
            "email_sequence": list[dict],  # From Copywriting Agent
            "lead_list_id": str,           # From Data Validation Agent
            "sending_schedule": dict,
            "daily_send_limit": int,
            "warmup_enabled": bool
        }
        """
        self.logger.info(
            "Processing campaign creation task",
            extra={"campaign_name": task.get("campaign_name")}
        )

        # Agent will use registered tools via Claude
        # This is the fallback processor if Claude doesn't engage
        return {
            "status": "error",
            "message": "Campaign creation requires Claude Agent SDK processing"
        }
```

---

## Tool Definitions

### 1. validate_campaign_inputs

**Purpose:** Validate all required inputs before campaign creation

**File:** `app/backend/src/agents/campaign_creation/tools.py`

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime

class CampaignInputs(BaseModel):
    """Validated campaign inputs"""
    campaign_name: str = Field(..., min_length=3, max_length=100)
    target_niche: str = Field(..., min_length=3)
    email_sequence: list[dict] = Field(..., min_items=1, max_items=10)
    lead_list_id: str = Field(..., regex=r'^[a-f0-9-]+$')
    sending_schedule: dict
    daily_send_limit: int = Field(..., ge=10, le=500)
    warmup_enabled: bool = True
    tracking_domain: str | None = None
    start_date: str | None = None  # YYYY-MM-DD format

    @validator('daily_send_limit')
    def validate_send_limit(cls, v):
        if v > 200:
            # Warning: high daily limit
            pass
        return v

    @validator('email_sequence')
    def validate_sequence(cls, v):
        for step in v:
            if 'subject' not in step or 'body' not in step:
                raise ValueError("Each sequence step must have subject and body")
        return v

async def validate_campaign_inputs(
    campaign_name: str,
    target_niche: str,
    email_sequence: list[dict],
    lead_list_id: str,
    sending_schedule: dict,
    daily_send_limit: int,
    warmup_enabled: bool = True,
    tracking_domain: str | None = None,
    start_date: str | None = None,
) -> dict[str, Any]:
    """
    Validate campaign creation inputs.

    Returns:
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str],
            "validated_inputs": dict
        }
    """
    from src.config import get_agent_logger

    logger = get_agent_logger("campaign_creation.validate")
    errors = []
    warnings = []

    try:
        # Pydantic validation
        validated = CampaignInputs(
            campaign_name=campaign_name,
            target_niche=target_niche,
            email_sequence=email_sequence,
            lead_list_id=lead_list_id,
            sending_schedule=sending_schedule,
            daily_send_limit=daily_send_limit,
            warmup_enabled=warmup_enabled,
            tracking_domain=tracking_domain,
            start_date=start_date,
        )

        # Check for duplicate campaign name
        # TODO: Query database for existing campaign with same name

        # Validate lead list exists
        # TODO: Check database for lead_list_id

        # Warnings
        if daily_send_limit > 200:
            warnings.append(f"Daily send limit of {daily_send_limit} is high. Consider 50-200 for better deliverability.")

        if not warmup_enabled:
            warnings.append("Warmup is disabled. This may impact deliverability for new accounts.")

        if tracking_domain and not tracking_domain.startswith("http"):
            warnings.append("Tracking domain should include protocol (https://)")

        logger.info("Campaign inputs validated", extra={
            "campaign_name": campaign_name,
            "warnings_count": len(warnings)
        })

        return {
            "valid": True,
            "errors": errors,
            "warnings": warnings,
            "validated_inputs": validated.dict()
        }

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        errors.append(str(e))
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "validated_inputs": None
        }
```

**Parameters:**
- `campaign_name`: Campaign name (3-100 chars)
- `target_niche`: Target niche/persona description
- `email_sequence`: List of email steps with subject/body
- `lead_list_id`: UUID of validated lead list
- `sending_schedule`: Schedule config (days, times)
- `daily_send_limit`: Max emails per day (10-500)
- `warmup_enabled`: Enable warmup mode (default: true)
- `tracking_domain`: Custom tracking domain (optional)
- `start_date`: Campaign start date YYYY-MM-DD (optional)

**Returns:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Daily send limit of 250 is high..."],
  "validated_inputs": {...}
}
```

**Error Handling:**
- Pydantic validation errors for invalid inputs
- Database errors when checking duplicates
- Returns structured error messages

---

### 2. create_campaign_config

**Purpose:** Generate complete campaign configuration for Instantly API

```python
async def create_campaign_config(
    validated_inputs: dict,
) -> dict[str, Any]:
    """
    Generate Instantly API v2 campaign configuration.

    Args:
        validated_inputs: Output from validate_campaign_inputs

    Returns:
        {
            "config": dict,  # Ready for Instantly API
            "preview": str,  # Human-readable summary
            "estimated_reach": int
        }
    """
    from src.config import get_agent_logger

    logger = get_agent_logger("campaign_creation.config")

    # Build Instantly API v2 payload
    config = {
        "name": validated_inputs["campaign_name"],
        "start_date": validated_inputs.get("start_date"),
        "sequences": [
            {
                "steps": [
                    {
                        "subject": step["subject"],
                        "body": step["body"],
                        "delay_days": step.get("delay_days", 0)
                    }
                    for step in validated_inputs["email_sequence"]
                ]
            }
        ],
        "settings": {
            "daily_limit": validated_inputs["daily_send_limit"],
            "warmup_enabled": validated_inputs["warmup_enabled"],
            "schedule": validated_inputs["sending_schedule"],
        }
    }

    if validated_inputs.get("tracking_domain"):
        config["settings"]["tracking_domain"] = validated_inputs["tracking_domain"]

    # Generate human-readable preview
    preview = f"""
Campaign: {validated_inputs['campaign_name']}
Target: {validated_inputs['target_niche']}
Sequence Steps: {len(validated_inputs['email_sequence'])}
Daily Limit: {validated_inputs['daily_send_limit']}
Warmup: {'Enabled' if validated_inputs['warmup_enabled'] else 'Disabled'}
Schedule: {validated_inputs['sending_schedule']}
"""

    # TODO: Calculate estimated reach based on lead list size
    estimated_reach = 0

    logger.info("Campaign config generated", extra={
        "campaign_name": validated_inputs["campaign_name"],
        "sequence_steps": len(validated_inputs["email_sequence"])
    })

    return {
        "config": config,
        "preview": preview.strip(),
        "estimated_reach": estimated_reach
    }
```

**Parameters:**
- `validated_inputs`: Dict from validate_campaign_inputs tool

**Returns:**
```json
{
  "config": {...},  // Instantly API v2 payload
  "preview": "Campaign: ...\nTarget: ...",
  "estimated_reach": 500
}
```

---

### 3. send_approval_request

**Purpose:** Send campaign approval request to Slack and wait for response

```python
from enum import Enum

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISE = "revise"

async def send_approval_request(
    campaign_config: dict,
    preview: str,
) -> dict[str, Any]:
    """
    Send approval request to Slack and create pending approval in database.

    Args:
        campaign_config: Instantly API config
        preview: Human-readable summary

    Returns:
        {
            "approval_id": str,
            "status": ApprovalStatus,
            "slack_message_id": str
        }
    """
    from src.config import get_agent_logger
    import uuid

    logger = get_agent_logger("campaign_creation.approval")

    # Generate approval ID
    approval_id = str(uuid.uuid4())

    # TODO: Send Slack message with preview and approval buttons
    # Slack message should include:
    # - Campaign preview
    # - Approve button (green)
    # - Reject button (red)
    # - Revise button (yellow)
    # - Direct link to edit campaign settings

    slack_message = {
        "text": f"🚀 Campaign Approval Request",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*New Campaign Ready for Review*\n\n```\n{preview}\n```"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve"},
                        "style": "primary",
                        "value": approval_id,
                        "action_id": f"approve_{approval_id}"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject"},
                        "style": "danger",
                        "value": approval_id,
                        "action_id": f"reject_{approval_id}"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✏️ Revise"},
                        "value": approval_id,
                        "action_id": f"revise_{approval_id}"
                    }
                ]
            }
        ]
    }

    # TODO: Post to Slack API
    # slack_response = await slack_client.post_message(channel="approvals", message=slack_message)
    slack_message_id = "mock_slack_id"  # Placeholder

    # Store approval request in database
    # TODO: Create campaign_approvals table entry
    # await db.execute(
    #     "INSERT INTO campaign_approvals (id, config, status, created_at) VALUES ($1, $2, $3, NOW())",
    #     approval_id, campaign_config, ApprovalStatus.PENDING
    # )

    logger.info("Approval request sent", extra={
        "approval_id": approval_id,
        "campaign_name": campaign_config.get("name")
    })

    return {
        "approval_id": approval_id,
        "status": ApprovalStatus.PENDING,
        "slack_message_id": slack_message_id
    }
```

**Parameters:**
- `campaign_config`: Instantly API configuration dict
- `preview`: Human-readable campaign summary

**Returns:**
```json
{
  "approval_id": "uuid-here",
  "status": "pending",
  "slack_message_id": "slack-msg-id"
}
```

**Error Handling:**
- Slack API errors (retry with exponential backoff)
- Database errors when storing approval
- Return error status with message

---

### 4. create_instantly_campaign

**Purpose:** Create campaign in Instantly.ai via API v2

```python
async def create_instantly_campaign(
    campaign_config: dict,
) -> dict[str, Any]:
    """
    Create campaign in Instantly.ai using API v2.

    Args:
        campaign_config: Validated configuration for Instantly API

    Returns:
        {
            "success": bool,
            "campaign_id": str,
            "instantly_response": dict,
            "error": str | None
        }
    """
    from src.integrations.instantly import InstantlyClient
    from src.config import get_agent_logger, Settings

    logger = get_agent_logger("campaign_creation.instantly")
    settings = Settings()

    try:
        # Initialize Instantly client
        client = InstantlyClient(api_key=settings.INSTANTLY_API_KEY)

        # Create campaign via API v2
        response = await client.create_campaign(campaign_config)

        campaign_id = response.get("id")

        logger.info("Campaign created in Instantly", extra={
            "campaign_id": campaign_id,
            "campaign_name": campaign_config.get("name")
        })

        await client.close()

        return {
            "success": True,
            "campaign_id": campaign_id,
            "instantly_response": response,
            "error": None
        }

    except Exception as e:
        logger.error(f"Failed to create Instantly campaign: {str(e)}", extra={
            "campaign_name": campaign_config.get("name")
        })

        return {
            "success": False,
            "campaign_id": None,
            "instantly_response": None,
            "error": str(e)
        }
```

**Parameters:**
- `campaign_config`: Instantly API v2 configuration dict

**Returns:**
```json
{
  "success": true,
  "campaign_id": "instantly-campaign-id",
  "instantly_response": {...},
  "error": null
}
```

**Error Handling:**
- HTTP errors from Instantly API (4xx, 5xx)
- Rate limiting (429 responses)
- Invalid API key (401)
- Malformed request (400)
- Network errors (timeout, connection)

**Retry Strategy:**
- Max retries: 3
- Backoff: Exponential (1s, 2s, 4s)
- Retry on: 429, 500, 502, 503, 504, network errors
- No retry on: 400, 401, 403

---

### 5. store_campaign_metadata

**Purpose:** Store campaign metadata in PostgreSQL

```python
from datetime import datetime
from pydantic import BaseModel

class CampaignMetadata(BaseModel):
    """Campaign metadata for database"""
    id: str  # Internal UUID
    instantly_campaign_id: str
    name: str
    target_niche: str
    lead_list_id: str
    status: str  # pending_approval, approved, active, paused, completed
    config: dict
    created_at: datetime
    approved_at: datetime | None = None
    launched_at: datetime | None = None

async def store_campaign_metadata(
    campaign_id: str,
    instantly_campaign_id: str,
    campaign_config: dict,
    lead_list_id: str,
    status: str = "approved",
) -> dict[str, Any]:
    """
    Store campaign metadata in PostgreSQL.

    Args:
        campaign_id: Internal UUID
        instantly_campaign_id: Instantly campaign ID
        campaign_config: Complete campaign configuration
        lead_list_id: Lead list UUID
        status: Campaign status

    Returns:
        {
            "success": bool,
            "campaign_id": str,
            "error": str | None
        }
    """
    from src.config import get_agent_logger

    logger = get_agent_logger("campaign_creation.database")

    try:
        # TODO: Insert into campaigns table
        # await db.execute(
        #     """
        #     INSERT INTO campaigns (
        #         id, instantly_campaign_id, name, target_niche,
        #         lead_list_id, status, config, created_at, approved_at
        #     ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        #     """,
        #     campaign_id, instantly_campaign_id, campaign_config["name"],
        #     campaign_config.get("target_niche"), lead_list_id,
        #     status, campaign_config
        # )

        logger.info("Campaign metadata stored", extra={
            "campaign_id": campaign_id,
            "instantly_id": instantly_campaign_id
        })

        return {
            "success": True,
            "campaign_id": campaign_id,
            "error": None
        }

    except Exception as e:
        logger.error(f"Failed to store campaign metadata: {str(e)}", extra={
            "campaign_id": campaign_id
        })

        return {
            "success": False,
            "campaign_id": campaign_id,
            "error": str(e)
        }
```

**Parameters:**
- `campaign_id`: Internal UUID
- `instantly_campaign_id`: Instantly campaign ID from API
- `campaign_config`: Full configuration dict
- `lead_list_id`: Lead list UUID
- `status`: Campaign status (default: "approved")

**Returns:**
```json
{
  "success": true,
  "campaign_id": "internal-uuid",
  "error": null
}
```

**Error Handling:**
- Database connection errors
- Constraint violations (duplicate IDs)
- Serialization errors (invalid JSON)

---

## Database Schema

### campaigns table

```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instantly_campaign_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    target_niche TEXT NOT NULL,
    lead_list_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending_approval',
    config JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMP,
    launched_at TIMESTAMP,
    paused_at TIMESTAMP,
    completed_at TIMESTAMP,

    CONSTRAINT fk_lead_list FOREIGN KEY (lead_list_id) REFERENCES lead_lists(id)
);

CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at);
CREATE INDEX idx_campaigns_instantly_id ON campaigns(instantly_campaign_id);
```

### campaign_approvals table

```sql
CREATE TABLE campaign_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    slack_message_id VARCHAR(255),
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    rejection_reason TEXT,
    revision_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

CREATE INDEX idx_approvals_status ON campaign_approvals(status);
CREATE INDEX idx_approvals_campaign_id ON campaign_approvals(campaign_id);
```

---

## Integration: Instantly API

### Client Implementation

**File:** `app/backend/src/integrations/instantly.py`

```python
from src.integrations.base import BaseIntegrationClient
from typing import Any

class InstantlyClient(BaseIntegrationClient):
    """Instantly.ai API v2 client"""

    def __init__(self, api_key: str):
        super().__init__(
            name="instantly",
            base_url="https://api.instantly.ai/api/v2",
            api_key=api_key,
            timeout=30.0
        )

    async def create_campaign(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Create campaign using Instantly API v2.

        Endpoint: POST /campaigns
        Scopes: campaigns:create, campaigns:all, all:create, all:all

        Args:
            config: Campaign configuration matching Instantly API spec

        Returns:
            API response with campaign ID
        """
        return await self.post("/campaigns", json=config)

    async def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Get campaign details"""
        return await self.get(f"/campaigns/{campaign_id}")

    async def update_campaign(self, campaign_id: str, updates: dict) -> dict[str, Any]:
        """Update campaign settings"""
        return await self.patch(f"/campaigns/{campaign_id}", json=updates)

    async def pause_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Pause active campaign"""
        return await self.post(f"/campaigns/{campaign_id}/pause")

    async def resume_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Resume paused campaign"""
        return await self.post(f"/campaigns/{campaign_id}/resume")
```

**API Documentation:** [Instantly API v2](https://developer.instantly.ai/api/v2/campaign)

---

## Human-in-the-Loop Workflow

### Approval Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Agent generates campaign config                         │
│     ├─ Validate inputs                                      │
│     ├─ Create config                                        │
│     └─ Generate preview                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Send Slack notification                                 │
│     ├─ Post message with preview                            │
│     ├─ Add approval buttons (Approve/Reject/Revise)         │
│     └─ Store approval request in database                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Human reviews campaign                                  │
│     ├─ Check niche/persona fit                              │
│     ├─ Review email copy quality                            │
│     ├─ Verify sending schedule                              │
│     ├─ Assess target list quality                           │
│     └─ Make decision                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    ┌────────┐   ┌────────┐   ┌──────────┐
    │Approve │   │Reject  │   │  Revise  │
    └────┬───┘   └───┬────┘   └────┬─────┘
         │           │              │
         ▼           ▼              ▼
    ┌────────┐   ┌────────┐   ┌──────────┐
    │Launch  │   │Log &   │   │Send notes│
    │campaign│   │notify  │   │back to   │
    │        │   │        │   │agent     │
    └────┬───┘   └────────┘   └────┬─────┘
         │                          │
         ▼                          │
    ┌────────────────────┐          │
    │ 4. Create campaign │          │
    │    in Instantly    │          │
    └────────┬───────────┘          │
             │                      │
             ▼                      │
    ┌────────────────────┐          │
    │ 5. Store metadata  │          │
    │    in database     │          │
    └────────┬───────────┘          │
             │                      │
             ▼                      │
    ┌────────────────────┐          │
    │ 6. Hand off to     │          │
    │    Email Sending   │◄─────────┘
    │    Agent           │  (after revision)
    └────────────────────┘
```

### Slack Webhook Handler

**File:** `app/backend/src/webhooks/slack_approvals.py`

```python
from fastapi import APIRouter, Request, HTTPException
from src.config import get_agent_logger

router = APIRouter(prefix="/webhooks/slack", tags=["webhooks"])
logger = get_agent_logger("webhook.slack")

@router.post("/campaign-approval")
async def handle_campaign_approval(request: Request):
    """
    Handle Slack button interactions for campaign approvals.

    Slack sends payload with:
    - action_id: approve_{approval_id}, reject_{approval_id}, revise_{approval_id}
    - user: Slack user who clicked button
    - message: Original message
    """
    payload = await request.json()

    action_id = payload["actions"][0]["action_id"]
    approval_id = payload["actions"][0]["value"]
    user_id = payload["user"]["id"]

    if action_id.startswith("approve_"):
        # Update approval status to approved
        # Trigger campaign creation in Instantly
        # Update Slack message to show "Approved by @user"
        pass

    elif action_id.startswith("reject_"):
        # Update approval status to rejected
        # Prompt for rejection reason
        # Notify requesting agent
        pass

    elif action_id.startswith("revise_"):
        # Update approval status to revise
        # Prompt for revision notes
        # Send notes back to agent for regeneration
        pass

    return {"ok": True}
```

---

## Error Handling Strategy

### Error Categories

1. **Input Validation Errors**
   - Missing required fields
   - Invalid data types
   - Out of range values
   - **Action:** Return structured error to requesting agent

2. **Instantly API Errors**
   - 400 Bad Request: Invalid campaign config
   - 401 Unauthorized: Invalid API key
   - 429 Rate Limit: Too many requests
   - 500+ Server Errors: Instantly service issues
   - **Action:** Retry with backoff for 429/5xx, fail fast for 4xx

3. **Database Errors**
   - Connection failures
   - Constraint violations
   - Timeout errors
   - **Action:** Retry connection errors, fail for constraint violations

4. **Slack API Errors**
   - Message posting failures
   - Channel not found
   - Rate limiting
   - **Action:** Retry with backoff, log errors, continue workflow

5. **Approval Timeout**
   - No response after 24 hours
   - **Action:** Send reminder notification, escalate after 48 hours

### Error Recovery

```python
# Example retry decorator for tools
from functools import wraps
import asyncio

def retry_on_error(max_retries=3, backoff_base=1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise

                    # Exponential backoff
                    delay = backoff_base * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s",
                        extra={"error": str(e)}
                    )
                    await asyncio.sleep(delay)

        return wrapper
    return decorator
```

---

## Testing Requirements

### Unit Tests (>90% coverage)

**File:** `app/backend/__tests__/unit/agents/test_campaign_creation.py`

1. **Test Agent Initialization**
   - Verify agent name and description
   - Check all tools are registered
   - Validate system prompt

2. **Test validate_campaign_inputs**
   - Valid inputs pass validation
   - Invalid inputs return errors
   - Edge cases (min/max values)
   - Warnings for risky configs

3. **Test create_campaign_config**
   - Config matches Instantly API spec
   - Preview text is generated correctly
   - All settings are included

4. **Test send_approval_request**
   - Slack message is formatted correctly
   - Approval ID is generated
   - Database entry is created

5. **Test create_instantly_campaign**
   - Successful API call returns campaign ID
   - API errors are handled gracefully
   - Retry logic works correctly

6. **Test store_campaign_metadata**
   - Data is stored with correct types
   - Foreign key constraints work
   - Errors are caught and returned

### Integration Tests (>85% coverage)

**File:** `app/backend/__tests__/integration/test_campaign_creation_flow.py`

1. **Test Full Campaign Creation Flow**
   - End-to-end from inputs to database
   - Mock Instantly API responses
   - Mock Slack API responses
   - Verify database state after completion

2. **Test Approval Workflow**
   - Approval request creates pending state
   - Approve action creates campaign
   - Reject action logs reason
   - Revise action sends feedback

3. **Test Error Scenarios**
   - Instantly API failure
   - Database connection failure
   - Slack notification failure
   - Invalid approval ID

4. **Test Agent Handoff**
   - Successful handoff to Email Sending Agent
   - Payload includes campaign ID and config
   - Priority is set correctly

### Mock Fixtures

**File:** `app/backend/__tests__/fixtures/campaign_fixtures.py`

```python
import pytest

@pytest.fixture
def valid_campaign_inputs():
    return {
        "campaign_name": "SaaS Founders Outreach Q1",
        "target_niche": "B2B SaaS founders with 10-50 employees",
        "email_sequence": [
            {
                "subject": "Quick question about [Company]",
                "body": "Hi {{firstName}}, noticed your work at {{company}}...",
                "delay_days": 0
            },
            {
                "subject": "Re: Quick question",
                "body": "Following up on my previous email...",
                "delay_days": 3
            }
        ],
        "lead_list_id": "123e4567-e89b-12d3-a456-426614174000",
        "sending_schedule": {
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "hours": [9, 10, 11, 14, 15, 16]
        },
        "daily_send_limit": 100,
        "warmup_enabled": True
    }

@pytest.fixture
def mock_instantly_response():
    return {
        "id": "instantly-campaign-123",
        "name": "SaaS Founders Outreach Q1",
        "status": "draft",
        "created_at": "2024-12-05T10:00:00Z"
    }

@pytest.fixture
def mock_slack_response():
    return {
        "ok": True,
        "channel": "C12345678",
        "ts": "1234567890.123456",
        "message": {...}
    }
```

### Coverage Requirements

- **Tools:** >90% line coverage, 100% branch coverage for critical paths
- **Agent class:** >85% coverage
- **Integration client:** >90% coverage
- **Error handling:** All error paths tested
- **Edge cases:** Min/max values, empty inputs, malformed data

---

## Implementation Checklist

### Phase 1: Core Structure
- [ ] Create agent directory: `src/agents/campaign_creation/`
- [ ] Implement `agent.py` with CampaignCreationAgent class
- [ ] Define system prompt
- [ ] Create `tools.py` file
- [ ] Create `schemas.py` with Pydantic models
- [ ] Create `exceptions.py` for custom errors

### Phase 2: Tools Implementation
- [ ] Implement `validate_campaign_inputs` tool
- [ ] Implement `create_campaign_config` tool
- [ ] Implement `send_approval_request` tool
- [ ] Implement `create_instantly_campaign` tool
- [ ] Implement `store_campaign_metadata` tool
- [ ] Add retry decorators for error handling

### Phase 3: Integrations
- [ ] Create `src/integrations/instantly.py`
- [ ] Implement InstantlyClient with all methods
- [ ] Add Slack client to `src/integrations/slack.py`
- [ ] Test API connections with real credentials

### Phase 4: Database
- [ ] Create migration for `campaigns` table
- [ ] Create migration for `campaign_approvals` table
- [ ] Add indexes for performance
- [ ] Test CRUD operations

### Phase 5: Webhooks
- [ ] Create `src/webhooks/slack_approvals.py`
- [ ] Implement approval button handlers
- [ ] Add webhook route to FastAPI app
- [ ] Configure Slack app with webhook URL

### Phase 6: Testing
- [ ] Write unit tests for all tools
- [ ] Write integration tests for workflow
- [ ] Create test fixtures
- [ ] Achieve >85% coverage
- [ ] Test error scenarios

### Phase 7: Documentation
- [ ] Add docstrings to all functions
- [ ] Document API endpoints
- [ ] Create usage examples
- [ ] Update CLAUDE.md with agent details

### Phase 8: Quality Assurance
- [ ] Run `make lint` and fix issues
- [ ] Run `make typecheck` and fix type errors
- [ ] Run `make test` and ensure all pass
- [ ] Run `make check` for full validation
- [ ] Manual testing with real Instantly account

### Phase 9: Integration
- [ ] Register agent in orchestration system
- [ ] Test handoff from Data Validation Agent
- [ ] Test handoff to Email Sending Agent
- [ ] End-to-end workflow test

---

## References

- [Instantly API v2 Documentation](https://developer.instantly.ai/api/v2/campaign)
- [Claude Agent SDK Best Practices](https://docs.claude.com/en/api/agent-sdk/overview)
- [Slack Interactive Messages](https://api.slack.com/messaging/interactivity)
- BaseAgent: `/app/backend/src/agents/base_agent.py`
- BaseIntegrationClient: `/app/backend/src/integrations/base.py`

---

## Notes

- **Character Limits:** Follow 125-char max for email body (from Copywriting Agent spec)
- **Warmup Best Practices:** Start low (20-30/day), increase 10-20% weekly
- **Deliverability:** Monitor bounce rates, spam complaints via separate agent
- **Compliance:** Ensure CAN-SPAM compliance in all campaigns
- **Testing:** Use Instantly sandbox/test mode during development
