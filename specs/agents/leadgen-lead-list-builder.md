# Lead List Builder Agent - Production Specification

## Metadata

**Agent Name:** `lead_list_builder`
**Category:** Lead Generation & Data
**Priority:** Phase 1 - MVP Foundation
**Dependencies:** None (entry point agent)
**Coverage Target:** >85% (agent requirement)

---

## Purpose

Build targeted lead lists by scraping data from Apify actors (LinkedIn Sales Navigator, Apollo.io, etc.). Automatically normalize, deduplicate, and qualify lead data before importing into the system. Acts as the primary entry point for the lead generation pipeline.

---

## System Prompt

```
You are the Lead List Builder Agent for Smarter Team, an autonomous AI agency.

Your primary responsibility is to build high-quality lead lists by scraping data from various sources via Apify actors. You ensure data quality through normalization, deduplication, and validation before importing leads into the system.

**Core Responsibilities:**
1. Execute Apify scraping tasks based on approved search criteria
2. Receive and process webhook notifications when scraping completes
3. Normalize raw data from different sources into standardized lead format
4. Perform sophisticated deduplication against existing leads database
5. Validate and assess data quality of each lead record
6. Import verified leads with NEW status for downstream processing
7. Generate comprehensive import reports with quality metrics
8. Monitor scraping costs and prevent budget overruns

**Quality Standards:**
- Field mapping: Normalize all source fields to standard schema (firstName, lastName, email, company, title, etc.)
- Deduplication: Use fuzzy matching on email domain + company + name to catch duplicates
- Validation: Require at least email + company for a valid lead
- Data quality scoring: 0-100 based on completeness and accuracy
- Batch processing: Handle 1,000-10,000 leads per batch efficiently
- Error tolerance: Skip invalid records, log reasons, continue processing

**Decision Framework:**
- High-quality lead (score ≥80): Direct import as NEW status
- Medium-quality lead (score 60-79): Import as NEW but flag for enrichment
- Low-quality lead (score <60): Skip import, log for manual review
- Duplicate lead: Update existing record with new data if more recent
- Invalid record: Skip with detailed reason logging

**Cost Management:**
- Track Apify compute unit usage per scrape
- Alert when approaching 80% of monthly budget
- Optimize scraper parameters for cost efficiency
- Prefer bulk operations over individual requests

**Webhook Processing:**
- Verify webhook signatures for security
- Handle partial results and retry failures
- Process results in batches to avoid memory issues
- Generate import reports with success/failure statistics

**Handoff Protocol:**
When leads are successfully imported, hand off to:
- Email Verification Agent (priority: high) - for email validation
- Data Validation Agent (priority: normal) - for additional data enrichment

You work autonomously but require human approval for:
- Initial search criteria validation
- Scraping budget approval (>$100 per batch)
- Import quality review (for first few batches)
```

---

## Agent Implementation

### Class Definition

```python
from src.agents.base_agent import BaseAgent
from src.integrations.apify import ApifyClient
from src.config import Settings, get_agent_logger
from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import hashlib
import json

class LeadListBuilderAgent(BaseAgent):
    """
    Lead List Builder Agent - Scrapes and processes leads from Apify actors.

    Handles scraping execution, data normalization, deduplication,
    quality assessment, and database import.
    """

    def __init__(self, settings: Settings):
        super().__init__(
            name="lead_list_builder",
            description="Builds lead lists by scraping data from Apify actors"
        )
        self.apify = ApifyClient(api_key=settings.APIFY_API_KEY)
        self.settings = settings
        self.monthly_budget_limit = 1000.0  # Default budget limit
        self.cost_alert_threshold = 0.8  # Alert at 80% of budget

    @property
    def system_prompt(self) -> str:
        return """[See System Prompt section above]"""

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Process lead list building task."""
        task_type = task.get("type")

        if task_type == "scrape_leads":
            return await self._scrape_leads(task)
        elif task_type == "process_webhook":
            return await self._process_webhook(task)
        elif task_type == "normalize_batch":
            return await self._normalize_batch(task)
        elif task_type == "deduplicate_leads":
            return await self._deduplicate_leads(task)
        elif task_type == "assess_quality":
            return await self._assess_quality(task)
        elif task_type == "import_leads":
            return await self._import_leads(task)
        elif task_type == "check_budget":
            return await self._check_budget_usage()
        else:
            raise ValueError(f"Unknown task type: {task_type}")
```

---

## Tools

### 1. `launch_apify_scrape`

**Purpose:** Start a scraping task on Apify with specified criteria

**Parameters:**
```python
{
    "actor_id": str,                    # Apify actor ID (e.g., "clockwork/free-linkedin-scraper")
    "search_criteria": dict,            # Search parameters specific to actor
    "max_results": int = 1000,         # Maximum leads to scrape
    "budget_limit": float = 100.0,     # Max cost for this scrape
    "webhook_url": str,                # URL for completion notification
    "proxy_config": dict = {"useApifyProxy": True}
}
```

**Returns:**
```python
{
    "task_id": str,                    # Apify run ID
    "status": str,                     # "READY", "RUNNING", "SUCCEEDED", "FAILED"
    "estimated_cost": float,           # Estimated compute units
    "estimated_duration": int,         # Estimated minutes
    "started_at": datetime
}
```

**Implementation:**
```python
async def launch_apify_scrape(
    self,
    actor_id: str,
    search_criteria: dict,
    max_results: int = 1000,
    budget_limit: float = 100.0,
    webhook_url: str | None = None,
    proxy_config: dict = None
) -> dict[str, Any]:
    """
    Launch a scraping task on Apify.

    Args:
        actor_id: Apify actor ID to run
        search_criteria: Actor-specific search parameters
        max_results: Maximum number of results to collect
        budget_limit: Maximum cost in USD for this scrape
        webhook_url: URL to notify on completion
        proxy_config: Proxy configuration for scraping

    Returns:
        Task details with ID and status
    """
    # Implementation in implementation checklist
    pass
```

### 2. `normalize_lead_data`

**Purpose:** Convert raw data from various sources into standardized lead format

**Parameters:**
```python
{
    "raw_leads": List[dict],           # Raw data from Apify
    "source_type": str,                # "linkedin", "apollo", "etc"
    "field_mapping": dict = {},        # Custom field mappings
    "required_fields": List[str] = ["email", "company"]
}
```

**Returns:**
```python
{
    "normalized_leads": List[dict],    # Standardized lead records
    "skipped_count": int,              # Records that couldn't be normalized
    "mapping_errors": List[dict],      # Details of mapping failures
    "field_coverage": dict             # % coverage for each field
}
```

**Standard Schema:**
```python
{
    "firstName": str | None,
    "lastName": str | None,
    "email": str,
    "company": str,
    "title": str | None,
    "industry": str | None,
    "location": str | None,
    "companySize": str | None,
    "website": str | None,
    "linkedinUrl": str | None,
    "phone": str | None,
    "source": str,                     # Source system
    "sourceId": str,                   # ID in source system
    "scrapedAt": datetime,
    "rawData": dict                    # Original data for reference
}
```

### 3. `detect_duplicates`

**Purpose:** Find and handle duplicate leads in the database

**Parameters:**
```python
{
    "leads": List[dict],               # Leads to check
    "match_threshold": float = 0.85,  # Similarity threshold (0-1)
    "match_fields": List[str] = ["email", "company", "name"]
}
```

**Returns:**
```python
{
    "unique_leads": List[dict],        # Non-duplicate leads
    "duplicates": List[dict],          # Duplicate records found
    "duplicate_groups": List[List[dict]],  # Groups of similar leads
    "updates_needed": List[dict]       # Existing leads to update
}
```

**Matching Strategy:**
1. **Exact email match** - Automatic duplicate
2. **Email domain + name similarity** - Fuzzy matching (Levenshtein)
3. **Company + title similarity** - Secondary check
4. **LinkedIn URL match** - Tertiary confirmation

### 4. `assess_lead_quality`

**Purpose:** Score lead records based on data completeness and accuracy

**Parameters:**
```python
{
    "leads": List[dict],               # Leads to score
    "scoring_weights": dict = {        # Field importance weights
        "email": 30,
        "company": 20,
        "title": 15,
        "phone": 10,
        "linkedinUrl": 15,
        "industry": 5,
        "location": 5
    }
}
```

**Returns:**
```python
{
    "scored_leads": List[dict],        # Leads with quality scores
    "quality_distribution": {          # Count by quality tier
        "high": int,
        "medium": int,
        "low": int
    },
    "average_score": float,            # Overall average quality
    "field_quality": dict              # Quality score by field
}
```

**Scoring Logic:**
- **Email validity** (30%): Format check, domain validity, disposable check
- **Data completeness** (40%): % of required fields filled
- **Data accuracy** (20%): Title matches industry, location matches company
- **Source reliability** (10%): Trust score for data source

### 5. `import_leads_to_db`

**Purpose:** Import validated leads into the database

**Parameters:**
```python
{
    "leads": List[dict],               # Leads to import
    "batch_size": int = 500,           # Records per database transaction
    "status": str = "NEW",             # Initial lead status
    "assign_to_campaign": bool = False # Auto-assign to active campaign
}
```

**Returns:**
```python
{
    "imported_count": int,
    "failed_count": int,
    "import_ids": List[UUID],          # Database IDs of imported leads
    "errors": List[dict],              # Details of failed imports
    "campaign_assignments": List[dict] # If auto-assigned
}
```

### 6. `generate_import_report`

**Purpose:** Create comprehensive report of scraping and import results

**Parameters:**
```python
{
    "task_id": str,                    # Apify task ID
    "scrape_results": dict,            # Raw scraping statistics
    "import_results": dict,            # Database import statistics
    "quality_metrics": dict,           # Data quality assessment
    "cost_breakdown": dict             # Cost analysis
}
```

**Returns:**
```python
{
    "report_id": UUID,
    "summary": {
        "total_scraped": int,
        "total_imported": int,
        "import_rate": float,          # % of scraped leads imported
        "average_quality": float,
        "total_cost": float,
        "cost_per_lead": float
    },
    "quality_breakdown": dict,
    "source_performance": dict,
    "recommendations": List[str],
    "generated_at": datetime
}
```

### 7. `check_budget_usage`

**Purpose:** Monitor Apify spending and budget consumption

**Parameters:**
```python
{
    "period": str = "month",           # "week", "month", "year"
    "alert_threshold": float = 0.8     # Alert at this % of budget
}
```

**Returns:**
```python
{
    "current_spend": float,
    "budget_limit": float,
    "remaining": float,
    "percentage_used": float,
    "alert_triggered": bool,
    "forecast": {                      # Predict end-of-period spending
        "projected_spend": float,
        "days_remaining": int,
        "daily_budget_remaining": float
    },
    "breakdown": {
        "scrapes_completed": int,
        "average_cost_per_scrape": float,
        "leads_per_dollar": float
    }
}
```

---

## Database Schema

### `lead_sources` Table

```sql
CREATE TABLE lead_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source Identification
    name VARCHAR(100) NOT NULL,        -- "LinkedIn Sales Navigator", "Apollo.io"
    actor_id VARCHAR(100),             -- Apify actor ID
    source_type VARCHAR(50) NOT NULL,  -- "linkedin", "apollo", "crunchbase"

    -- Configuration
    default_fields JSONB,              -- Standard field mappings
    required_fields JSONB,             -- Required field list
    proxy_required BOOLEAN DEFAULT TRUE,

    -- Cost & Performance
    average_cost_per_1k DECIMAL(10,2),
    average_quality_score DECIMAL(5,2),
    reliability_score DECIMAL(3,2),    -- 0-100 success rate

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes
    UNIQUE (name),
    INDEX idx_lead_sources_type (source_type)
);
```

### `scrape_tasks` Table

```sql
CREATE TABLE scrape_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task Details
    apify_task_id VARCHAR(100) UNIQUE NOT NULL,
    actor_id VARCHAR(100) NOT NULL,
    source_id UUID REFERENCES lead_sources(id),

    -- Search Criteria
    search_criteria JSONB NOT NULL,    -- Original search parameters
    max_results INTEGER,

    -- Execution
    status VARCHAR(50) NOT NULL,       -- "PENDING", "RUNNING", "COMPLETED", "FAILED"
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    runtime_minutes INTEGER,

    -- Results
    results_count INTEGER DEFAULT 0,
    results_url TEXT,                  -- Apify results URL

    -- Cost Tracking
    compute_units_used DECIMAL(10,2),
    estimated_cost DECIMAL(10,2),
    actual_cost DECIMAL(10,2),

    -- Metadata
    webhook_received BOOLEAN DEFAULT FALSE,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_scrape_tasks_status (status),
    INDEX idx_scrape_tasks_source (source_id),
    INDEX idx_scrape_tasks_created (created_at)
);
```

### `import_logs` Table

```sql
CREATE TABLE import_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Import Details
    scrape_task_id UUID REFERENCES scrape_tasks(id),
    batch_id VARCHAR(100),             -- For tracking large imports

    -- Processing Statistics
    total_scraped INTEGER DEFAULT 0,
    total_normalized INTEGER DEFAULT 0,
    total_unique INTEGER DEFAULT 0,
    total_imported INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,

    -- Quality Metrics
    average_quality_score DECIMAL(5,2),
    high_quality_count INTEGER DEFAULT 0,
    medium_quality_count INTEGER DEFAULT 0,
    low_quality_count INTEGER DEFAULT 0,

    -- Deduplication
    duplicates_found INTEGER DEFAULT 0,
    duplicates_merged INTEGER DEFAULT 0,

    -- Cost Analysis
    total_cost DECIMAL(10,2),
    cost_per_lead DECIMAL(10,2),

    -- Processing Time
    processing_time_seconds INTEGER,

    -- Report
    report_data JSONB,                 -- Full detailed report

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_import_logs_scrape (scrape_task_id),
    INDEX idx_import_logs_created (created_at)
);
```

### `leads` Table Updates

Add to existing `leads` table:

```sql
ALTER TABLE leads ADD COLUMN source_id UUID REFERENCES lead_sources(id);
ALTER TABLE leads ADD COLUMN source_task_id VARCHAR(100);
ALTER TABLE leads ADD COLUMN source_lead_id VARCHAR(100);
ALTER TABLE leads ADD COLUMN quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100);
ALTER TABLE leads ADD COLUMN scraped_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN raw_data JSONB;  -- Original scraped data
ALTER TABLE leads ADD COLUMN normalized_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN duplicate_of UUID REFERENCES leads(id);

CREATE INDEX idx_leads_source ON leads(source_id);
CREATE INDEX idx_leads_quality ON leads(quality_score);
CREATE INDEX idx_leads_scraped ON leads(scraped_at);
CREATE INDEX idx_leads_source_lead ON leads(source_lead_id);
```

---

## Integration: Apify Client

### Implementation

```python
from src.integrations.base import BaseIntegrationClient
from typing import Any, Literal, Dict, List
from datetime import datetime

class ApifyClient(BaseIntegrationClient):
    """
    Apify API client for web scraping and automation.

    Docs: https://docs.apify.com/api/v2
    """

    def __init__(self, api_key: str):
        super().__init__(
            name="apify",
            base_url="https://api.apify.com/v2",
            api_key=api_key,
            timeout=300.0  # Long timeout for scraping tasks
        )

    async def run_actor(
        self,
        actor_id: str,
        input_data: dict,
        build: str = "latest",
        memory_mbytes: int = 4096,
        timeout_secs: int = 3600
    ) -> dict[str, Any]:
        """
        Run an Apify actor.

        Args:
            actor_id: Actor ID or username/actor-name
            input_data: Input parameters for the actor
            build: Build version to run
            memory_mbytes: Memory allocation
            timeout_secs: Maximum runtime

        Returns:
            {
                "id": str,  # Run ID
                "status": str,
                "defaultDatasetId": str,
                "buildNumber": str
            }
        """
        payload = {
            "build": build,
            "memoryMbytes": memory_mbytes,
            "timeoutSecs": timeout_secs,
            "input": input_data
        }

        endpoint = f"/acts/{actor_id}/runs"
        return await self.post(endpoint, json=payload)

    async def get_run_status(self, run_id: str) -> dict[str, Any]:
        """
        Get the status of a running actor.

        Returns:
            {
                "id": str,
                "status": str,  # READY, RUNNING, SUCCEEDED, FAILED, ABORTED, TIMED-OUT
                "finishedAt": datetime | None,
                "stats": {
                    "inputBodyLen": int,
                    "restartCount": int,
                    "runTimeSecs": int,
                    "computeUnits": float,
                    "MET": float  # Memory execution time
                }
            }
        """
        endpoint = f"/actor-runs/{run_id}"
        return await self.get(endpoint)

    async def get_dataset_items(
        self,
        dataset_id: str,
        limit: int = 1000,
        offset: int = 0,
        clean: bool = True,
        desc: bool = False
    ) -> dict[str, Any]:
        """
        Retrieve items from an actor's dataset.

        Args:
            dataset_id: Dataset ID from run response
            limit: Maximum items to retrieve
            offset: Offset for pagination
            clean: Clean HTML from text fields
            desc: Return items in descending order

        Returns:
            {
                "items": List[dict],
                "total": int,
                "offset": int,
                "count": int,
                "limit": int
            }
        """
        params = {
            "limit": limit,
            "offset": offset,
            "clean": str(clean).lower(),
            "desc": str(desc).lower()
        }

        endpoint = f"/datasets/{dataset_id}/items"
        return await self.get(endpoint, params=params)

    async def list_actors(
        self,
        limit: int = 100,
        offset: int = 0,
        filter_by_username: str | None = None
    ) -> dict[str, Any]:
        """
        List available actors.

        Returns:
            {
                "items": [
                    {
                        "id": str,
                        "name": str,
                        "username": str,
                        "description": str,
                        "defaultRunOptions": dict,
                        "stats": dict
                    }
                ],
                "total": int,
                "offset": int,
                "count": int,
                "limit": int
            }
        """
        params = {
            "limit": limit,
            "offset": offset
        }

        if filter_by_username:
            params["filterByUsername"] = filter_by_username

        endpoint = "/actors"
        return await self.get(endpoint, params=params)

    async def get_user_info(self) -> dict[str, Any]:
        """
        Get current user information including plan limits.

        Returns:
            {
                "id": str,
                "username": str,
                "email": str,
                "plan": {
                    "name": str,
                    "computeUnitsPerMonth": int,
                    "computeUnitsUsed": int
                }
            }
        """
        endpoint = "/users/me"
        return await self.get(endpoint)

    async def create_webhook(
        self,
        event_types: List[str],
        url: str,
        actor_id: str | None = None
    ) -> dict[str, Any]:
        """
        Create a webhook for actor events.

        Args:
            event_types: ["RUN.SUCCEEDED", "RUN.FAILED", etc.]
            url: Webhook endpoint URL
            actor_id: Optional specific actor

        Returns:
            {
                "id": str,
                "isAdHoc": bool,
                "eventTypes": List[str],
                "url": str,
                "actorId": str | None
            }
        """
        payload = {
            "isAdHoc": True,
            "eventTypes": event_types,
            "url": url
        }

        if actor_id:
            payload["actorId"] = actor_id

        endpoint = "/webhooks"
        return await self.post(endpoint, json=payload)
```

---

## Error Handling Strategy

### 1. Apify API Errors

**Scenario:** Apify API returns failures or timeouts

**Handling:**
- Rate limit (429) → Exponential backoff, max 5 retries
- Invalid actor ID → Fail fast, require human review
- Insufficient compute units → Queue task, alert when available
- Actor timeout → Retry with increased timeout/mem
- Authentication error → Alert immediately, halt all scraping

**Implementation:**
```python
try:
    result = await self.apify.run_actor(actor_id, input_data)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        self.logger.critical("Apify authentication failed")
        raise AuthenticationError("Invalid Apify API key")
    elif e.response.status_code == 402:
        self.logger.error("Insufficient compute units")
        raise InsufficientCreditsError("Apify credits exhausted")
    elif e.response.status_code == 429:
        await asyncio.sleep(2 ** retry_count)
        # Retry logic
```

### 2. Webhook Failures

**Scenario:** Webhook delivery fails or data is corrupted

**Handling:**
- Signature verification fails → Reject webhook, log security alert
- Malformed JSON → Log error, request manual processing
- Missing required fields → Partial processing, flag for review
- Duplicate webhook → Process once, log duplicate

**Webhook Validation Pattern:**
```python
async def verify_webhook_signature(request: Request) -> bool:
    """Verify Apify webhook signature."""
    signature = request.headers.get("X-Apify-Webhook-Signature")
    if not signature:
        return False

    # Apify uses HMAC-SHA256 with webhook secret
    payload = await request.body()
    expected = hmac_sha256(self.webhook_secret, payload)

    return hmac.compare_digest(signature, f"sha256={expected}")
```

### 3. Data Processing Errors

**Scenario:** Lead data is malformed or can't be normalized

**Handling:**
- Invalid email format → Mark as invalid, continue processing
- Missing required fields → Log warning, skip record
- Encoding issues → Attempt encoding fixes, skip if fails
- Large batch memory → Process in chunks, use streaming

### 4. Database Errors

**Scenario:** Failed to save leads or import logs

**Handling:**
- Connection errors → Retry with exponential backoff
- Constraint violations → Skip duplicate, log warning
- Transaction timeout → Reduce batch size, retry
- Disk full → Alert ops, halt processing

### 5. Budget Overrun

**Scenario:** Scraping costs exceed budget limits

**Handling:**
- Check cost before each scrape
- Stop scraping at 90% of budget
- Alert on approaching limit
- Queue remaining tasks for next billing period

---

## Testing Requirements

### Unit Tests (`__tests__/unit/agents/test_lead_list_builder.py`)

**Coverage Target:** >85%

```python
import pytest
from src.agents.lead_list_builder import LeadListBuilderAgent

class TestLeadListBuilderAgent:

    @pytest.mark.asyncio
    async def test_launch_apify_scrape_success(self, agent, mock_apify):
        """Test successful Apify scrape launch."""
        result = await agent.launch_apify_scrape(
            actor_id="clockwork/free-linkedin-scraper",
            search_criteria={"keywords": "CEO", "location": "US"},
            max_results=1000
        )
        assert "task_id" in result
        assert result["status"] in ["READY", "RUNNING"]

    @pytest.mark.asyncio
    async def test_normalize_lead_data_linkedin(self, agent, mock_linkedin_data):
        """Test normalization of LinkedIn data."""
        result = await agent.normalize_lead_data(
            raw_leads=mock_linkedin_data,
            source_type="linkedin"
        )
        assert result["normalized_leads"]
        assert all("email" in lead for lead in result["normalized_leads"])
        assert result["field_coverage"]["email"] >= 0.8

    @pytest.mark.asyncio
    async def test_detect_duplicates_email_match(self, agent, mock_leads):
        """Test duplicate detection by exact email match."""
        # Add existing lead to database
        existing_email = mock_leads[0]["email"]

        # Create duplicate lead
        duplicate_lead = {**mock_leads[1], "email": existing_email}

        result = await agent.detect_duplicates([duplicate_lead])
        assert result["duplicates"]
        assert len(result["unique_leads"]) == 0

    @pytest.mark.asyncio
    async def test_assess_lead_quality_scoring(self, agent, mock_varied_leads):
        """Test lead quality scoring algorithm."""
        result = await agent.assess_lead_quality(mock_varied_leads)

        assert "scored_leads" in result
        assert all(0 <= lead["quality_score"] <= 100 for lead in result["scored_leads"])
        assert 0 <= result["average_score"] <= 100
        assert "high" in result["quality_distribution"]

    @pytest.mark.asyncio
    async def test_import_leads_batch_processing(self, agent, mock_valid_leads):
        """Test batch import to database."""
        result = await agent.import_leads_to_db(
            leads=mock_valid_leads,
            batch_size=100
        )
        assert result["imported_count"] == len(mock_valid_leads)
        assert result["failed_count"] == 0
        assert len(result["import_ids"]) == len(mock_valid_leads)

    @pytest.mark.asyncio
    async def test_generate_import_report_metrics(self, agent, mock_scrape_data):
        """Test comprehensive import report generation."""
        result = await agent.generate_import_report(
            task_id="test-task-123",
            scrape_results={"total": 1000, "successful": 950},
            import_results={"imported": 900, "failed": 50},
            quality_metrics={"average_score": 75},
            cost_breakdown={"total_cost": 25.50}
        )
        assert result["summary"]["import_rate"] == 0.9
        assert result["summary"]["cost_per_lead"] == 25.50 / 900
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_budget_usage_alerting(self, agent, mock_high_usage):
        """Test budget monitoring and alerting."""
        result = await agent.check_budget_usage(alert_threshold=0.8)
        assert result["alert_triggered"] is True
        assert result["percentage_used"] >= 80
        assert "daily_budget_remaining" in result["forecast"]

    @pytest.mark.asyncio
    async def test_webhook_processing_validation(self, agent, mock_webhook_payload):
        """Test webhook payload processing and validation."""
        result = await agent._process_webhook({
            "event_data": mock_webhook_payload,
            "signature": "valid-signature"
        })
        assert result["status"] == "processed"
        assert result["leads_imported"] > 0

    @pytest.mark.asyncio
    async def test_invalid_task_type_raises_error(self, agent):
        """Test unknown task type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown task type"):
            await agent.process_task({"type": "invalid_type"})
```

### Integration Tests (`__tests__/integration/test_lead_list_builder_integration.py`)

```python
import pytest
from src.agents.lead_list_builder import LeadListBuilderAgent
from src.integrations.apify import ApifyClient

class TestLeadListBuilderIntegration:

    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self, agent, db_session):
        """Test complete workflow from scrape to import."""
        # Launch scrape
        scrape_result = await agent.launch_apify_scrape(
            actor_id="clockwork/free-linkedin-scraper",
            search_criteria={"keywords": "CTO", "industry": "SaaS"},
            max_results=100
        )
        task_id = scrape_result["task_id"]

        # Simulate webhook completion
        webhook_data = {
            "event": {"eventType": "ACTOR.RUN.SUCCEEDED"},
            "resource": {"id": task_id},
            "input": {},
            "output": {
                "defaultDatasetId": "test-dataset-123"
            }
        }

        # Process webhook and normalize data
        process_result = await agent._process_webhook({
            "event_data": webhook_data
        })

        # Verify leads imported
        assert process_result["leads_imported"] > 0

        # Check database records
        leads = db_session.query(Lead).filter_by(
            source_task_id=task_id
        ).all()

        assert len(leads) == process_result["leads_imported"]
        assert all(lead.source == "linkedin" for lead in leads)

    @pytest.mark.asyncio
    async def test_deduplication_across_sources(self, agent, db_session, test_leads):
        """Test deduplication across different data sources."""
        # Import leads from LinkedIn
        linkedin_leads = test_leads[:50]
        await agent.import_leads_to_db(linkedin_leads, source="linkedin")

        # Try to import same leads from Apollo
        apify_leads = [
            {**lead, "source": "apollo", "email": lead["email"].upper()}
            for lead in linkedin_leads[:25]
        ]

        result = await agent.import_leads_to_db(apify_leads, source="apollo")

        # Should detect and skip duplicates
        assert result["imported_count"] == 0
        assert result["duplicates_found"] == 25

    @pytest.mark.mark.integration
    @pytest.mark.asyncio
    async def test_apify_api_integration(self, apify_client):
        """Test real Apify API integration (requires API key)."""
        # Get user info
        user_info = await apify_client.get_user_info()
        assert "id" in user_info
        assert "plan" in user_info

        # List actors
        actors = await apify_client.list_actors(limit=10)
        assert "items" in actors
        assert len(actors["items"]) <= 10
```

### Fixtures (`__tests__/fixtures/lead_list_builder_fixtures.py`)

```python
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

@pytest.fixture
def mock_linkedin_data():
    """Mock LinkedIn scraped data."""
    return [
        {
            "name": "John Doe",
            "firstName": "John",
            "lastName": "Doe",
            "headline": "CEO at TechCorp",
            "company": "TechCorp",
            "position": "CEO",
            "location": "San Francisco, CA",
            "url": "https://linkedin.com/in/johndoe",
            "email": "john@techcorp.com"
        },
        # More test records...
    ]

@pytest.fixture
def mock_varied_leads():
    """Mock leads with varying data quality."""
    return [
        {
            "email": "complete@example.com",
            "company": "Complete Corp",
            "title": "CEO",
            "phone": "+1-555-0100",
            "linkedinUrl": "https://linkedin.com/in/complete"
        },
        {
            "email": "partial@example.com",
            "company": "Partial Inc"
            # Missing title, phone, linkedin
        },
        {
            "company": "No Email Corp",
            "title": "CTO"
            # Missing email - invalid lead
        }
    ]

@pytest.fixture
def mock_webhook_payload():
    """Mock Apify webhook payload."""
    return {
        "event": {
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "createdAt": datetime.now().isoformat()
        },
        "resource": {
            "id": "run-12345",
            "actId": "clockwork/free-linkedin-scraper"
        },
        "input": {
            "search": "CEO SaaS"
        },
        "output": {
            "defaultDatasetId": "dataset-67890",
            "stats": {
                "inputBodyLen": 156,
                "restartCount": 0,
                "runTimeSecs": 245,
                "computeUnits": 2.5
            }
        }
    }

@pytest.fixture
def mock_high_usage():
    """Mock high Apify usage (>80% of budget)."""
    return {
        "current_spend": 850.0,
        "budget_limit": 1000.0,
        "remaining": 150.0,
        "percentage_used": 85.0
    }
```

---

## Implementation Checklist

### Phase 1: Foundation (Day 1-2)

- [ ] Create agent directory: `src/agents/lead_list_builder/`
- [ ] Implement `LeadListBuilderAgent` class extending `BaseAgent`
- [ ] Define `system_prompt` property
- [ ] Implement basic `process_task()` method with task routing
- [ ] Create Apify integration client in `src/integrations/apify.py`
- [ ] Add Apify to `config/webhooks.py` for webhook support
- [ ] Write unit tests for agent initialization
- [ ] Run `make check` - ensure all quality gates pass

### Phase 2: Database Schema (Day 2-3)

- [ ] Create migration: `make migration name="add_lead_list_builder_tables"`
- [ ] Define `lead_sources` table schema
- [ ] Define `scrape_tasks` table schema
- [ ] Define `import_logs` table schema
- [ ] Add columns to `leads` table
- [ ] Create necessary indexes for performance
- [ ] Apply migration: `make migrate`
- [ ] Write unit tests for schema validation

### Phase 3: Apify Integration (Day 3-4)

- [ ] Implement `ApifyClient.run_actor()`
- [ ] Implement `ApifyClient.get_run_status()`
- [ ] Implement `ApifyClient.get_dataset_items()`
- [ ] Implement `ApifyClient.create_webhook()`
- [ ] Add error handling with retry logic
- [ ] Write integration tests (mark with `@pytest.mark.integration`)
- [ ] Test with real Apify API (use test compute units)

### Phase 4: Core Tools - Scraping (Day 4-5)

- [ ] Implement `launch_apify_scrape()` tool
  - [ ] Validate search criteria
  - [ ] Check budget before launch
  - [ ] Configure webhook URL
  - [ ] Store task in database
- [ ] Implement webhook handler for scrape completion
- [ ] Implement dataset retrieval and processing
- [ ] Register all tools in agent initialization
- [ ] Write unit tests for each tool (>90% coverage)

### Phase 5: Data Processing (Day 5-6)

- [ ] Implement `normalize_lead_data()` tool
  - [ ] Field mapping for LinkedIn, Apollo, other sources
  - [ ] Data type conversion and validation
  - [ ] Required field enforcement
- [ ] Implement `detect_duplicates()` tool
  - [ ] Exact email matching
  - [ ] Fuzzy name/company matching
  - [ ] Merge conflict resolution
- [ ] Implement `assess_lead_quality()` tool
  - [ ] Email validation and scoring
  - [ ] Data completeness scoring
  - [ ] Source reliability scoring
- [ ] Write comprehensive tests for data processing

### Phase 6: Database Integration (Day 6-7)

- [ ] Implement `import_leads_to_db()` tool
  - [ ] Batch processing for large datasets
  - [ ] Transaction handling and rollback
  - [ ] Duplicate updates
- [ ] Implement `generate_import_report()` tool
  - [ ] Quality metrics calculation
  - [ ] Cost analysis
  - [ ] Performance recommendations
- [ ] Implement `check_budget_usage()` tool
  - [ ] Usage tracking
  - [ ] Alert threshold checking
  - [ ] Forecast calculations
- [ ] Write integration tests for database operations

### Phase 7: Error Handling & Quality (Day 7-8)

- [ ] Add comprehensive error handling for all scenarios
- [ ] Implement retry logic with exponential backoff
- [ ] Add webhook signature verification
- [ ] Add budget monitoring and alerts
- [ ] Implement data validation and sanitization
- [ ] Write error scenario tests
- [ ] Test all error paths and recovery

### Phase 8: Performance & Monitoring (Day 8-9)

- [ ] Optimize batch processing for 10k+ leads
- [ ] Implement streaming for large datasets
- [ ] Add performance metrics and logging
- [ ] Optimize database queries with indexes
- [ ] Add memory usage monitoring
- [ ] Test with large datasets (simulate 10k leads)
- [ ] Profile and optimize bottlenecks

### Phase 9: Integration & End-to-End Testing (Day 9-10)

- [ ] Write end-to-end integration tests
- [ ] Test complete workflow from scrape to import
- [ ] Test webhook delivery and processing
- [ ] Test budget management and alerts
- [ ] Test deduplication across sources
- [ ] Run `make test` - achieve >85% coverage
- [ ] Generate coverage report: `make test-html`

### Phase 10: Documentation & Final Quality (Day 10)

- [ ] Update agent docstrings with examples
- [ ] Add inline code comments for complex logic
- [ ] Update CLAUDE.md with new agent
- [ ] Create troubleshooting guide for common issues
- [ ] Run `make check` - all quality gates pass
- [ ] Run `make lint-fix` and `make format`
- [ ] Run `mypy` type checking - zero errors
- [ ] Review logging - ensure structured logging throughout
- [ ] Move task to `_completed/`
- [ ] Update `tasks/TASK-LOG.md`

---

## Quality Gates

**All must pass before merging:**

- [ ] All unit tests pass (`pytest __tests__/unit/agents/test_lead_list_builder*`)
- [ ] All integration tests pass (`pytest __tests__/integration/test_lead_list_builder*`)
- [ ] Coverage ≥85% for agent code
- [ ] Coverage ≥90% for tools
- [ ] No linting errors (`ruff check`)
- [ ] No type errors (`mypy --strict`)
- [ ] No formatting issues (`ruff format --check`)
- [ ] All database migrations apply cleanly
- [ ] Webhook signature verification works
- [ ] Budget monitoring and alerting tested
- [ ] Deduplication accuracy >95%
- [ ] Data quality scoring consistent
- [ ] Error handling covers all scenarios
- [ ] Logging structured and complete

---

## Performance Targets

- **Apify Scrape Launch:** <2s
- **Data Normalization:** <100ms per record
- **Duplicate Detection:** <50ms per record (with indexes)
- **Quality Assessment:** <20ms per record
- **Database Import:** <10ms per record (batch)
- **Report Generation:** <5s for 10k leads
- **Memory Usage:** <512MB for 10k lead batch
- **Concurrent Scrapes:** Support up to 10 parallel tasks

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Scraping Volume:** Leads scraped per day/week/month
2. **Import Rate:** % of scraped leads successfully imported
3. **Data Quality:** Average quality score by source
4. **Cost Efficiency:** Cost per lead by source
5. **Duplicate Rate:** % of leads identified as duplicates
6. **Source Performance:** Quality and cost by data source
7. **Processing Speed:** Records processed per second
8. **Budget Usage:** % of monthly budget consumed

### Alert Conditions

- Budget usage >80% (critical)
- Import failure rate >10% (warning)
- Average quality score <60 (warning)
- Duplicate rate >50% (investigate source)
- Processing errors >5% (warning)
- Scrape timeout rate >20% (critical)
- Cost per lead >$0.50 (review source)

---

## Dependencies

### Python Packages (add to `pyproject.toml`)

```toml
[project.dependencies]
# Existing dependencies...
# No new packages needed - httpx already included
# Consider adding: recordlinkage for advanced deduplication (Phase 2+)
```

### Environment Variables (add to `.env`)

```bash
# Apify Web Scraping
APIFY_API_KEY=apify_api_your-token-here    # Required
APIFY_WEBHOOK_SECRET=your_webhook_secret_here                    # Required for webhooks
```

### Webhook Configuration (add to `config/webhooks.py`)

```python
WEBHOOKS = {
    # Existing webhooks...
    "apify": WebhookConfig(
        name="Apify",
        path="/webhooks/apify",
        secret_env_key="APIFY_WEBHOOK_SECRET",
    ),
}
```

### Database Migration

```bash
make migration name="add_lead_list_builder_tables"
make migrate
```

---

## API Endpoints (Future - Phase 2+)

If exposing via REST API:

```python
# FastAPI routes (future)
POST /api/lead-sources               # Create new lead source configuration
GET /api/lead-sources               # List available sources
POST /api/scrape-tasks              # Launch new scrape
GET /api/scrape-tasks/{id}          # Get scrape status
POST /api/scrape-tasks/{id}/cancel  # Cancel running scrape
GET /api/import-logs               # Get import history
POST /api/import-preview           # Preview import results
```

---

## Related Agents

**Upstream (provides data to this agent):**
- None (entry point agent - receives human input)

**Downstream (receives data from this agent):**
- Email Verification Agent → Validates email addresses
- Data Validation Agent → Enriches missing data
- Campaign Creation Agent → Uses verified leads for campaigns
- Lead Nurturing Agent → Adds leads to nurture sequences

---

## Security Considerations

1. **API Key Management:**
   - Store Apify API key in environment variables
   - Rotate keys regularly
   - Monitor for unauthorized usage

2. **Webhook Security:**
   - Verify all webhook signatures
   - Rate limit webhook endpoints
   - Log all webhook deliveries

3. **Data Privacy:**
   - Sanitize PII before logging
   - Comply with GDPR/CCPA
   - Implement data retention policies

4. **Scraping Ethics:**
   - Respect robots.txt
   - Implement rate limiting
   - Don't scrape private data

---

## References

- [Apify API Documentation](https://docs.apify.com/api/v2)
- [Apify Python SDK](https://github.com/apify/apify-sdk-python)
- [LinkedIn Scraper Actor](https://apify.com/clockwork/free-linkedin-scraper)
- [Apollo.io Scraper Actor](https://apify.com/voyn/pro Apollo-scraper)
- BaseAgent Pattern: `/app/backend/src/agents/base_agent.py`
- BaseIntegrationClient: `/app/backend/src/integrations/base.py`
- Project Conventions: `CLAUDE.md`

---

## Notes

- Start with LinkedIn Sales Navigator scraper as primary source
- Implement flexible field mapping system for easy source addition
- Use streaming for large datasets to avoid memory issues
- Cache source configurations to reduce API calls
- Consider implementing actor auto-discovery (Phase 2+)
- Monitor scraping costs carefully - can escalate quickly
- Implement progressive enhancement for data quality

---

**Specification Version:** 1.0
**Last Updated:** 2025-12-05
**Status:** Ready for Implementation
