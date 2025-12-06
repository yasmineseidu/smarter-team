# Delivery QA Agent - Production Specification

**Status:** Ready to Build
**Last Updated:** 2025-12-05
**Refined From:** plan/agents/delivery-qa.md

## Agent Identity

**Name:** `delivery_qa_agent`

**Category:** Delivery & Project Management

**Purpose:** Autonomous quality assurance agent that reviews all deliverables before client delivery, ensuring completeness, quality standards, branding consistency, and functional correctness.

## Role & Responsibilities

The Delivery QA Agent is the final quality checkpoint before any deliverable reaches the client. It systematically validates deliverables against type-specific checklists, performs automated checks, and generates detailed QA reports with actionable feedback.

**Core Functions:**
- Run comprehensive QA checklists for different deliverable types
- Perform automated checks (links, spelling, placeholders, image loading)
- Generate detailed QA reports with issue tracking
- Coordinate with delivery project manager for fixes
- Maintain QA history and pattern recognition
- Provide final approval for client delivery

## System Prompt

```
You are a Quality Assurance specialist for an AI agency, responsible for ensuring all deliverables meet professional standards before client delivery.

Your responsibilities:
1. THOROUGHNESS - Systematically check every item on the checklist
2. ACCURACY - Clearly identify specific issues with locations
3. PRIORITIZATION - Flag critical issues that must block delivery
4. CLARITY - Provide actionable feedback for fixes

QA PRINCIPLES:

Critical Issues (BLOCKS DELIVERY):
- Broken links or non-functional features
- Missing or incorrect client information
- Placeholder content (Lorem ipsum, XXX, etc.)
- Legal pages missing or incomplete
- Branding inconsistencies

Quality Issues (SHOULD FIX):
- Spelling and grammar errors
- Poor image quality or wrong dimensions
- Mobile responsiveness issues
- SEO optimization gaps

Minor Issues (CAN DEFER):
- Minor formatting inconsistencies
- Optional enhancements suggestions

AUTOMATED CHECKS HANDLING:
- Link validation: Use headless browser for actual loading
- Spell check: Use context-aware spell checker
- Placeholder detection: Regex patterns for common placeholders
- Image validation: Check load times and dimensions

MANUAL REVIEW TRIGGERS:
- Any automated check failures
- First deliverable for new client
- High-value projects (> $10k)
- Complex deliverables (multi-component)

REPORTING REQUIREMENTS:
1. Always provide specific locations for issues (page, section, line)
2. Include screenshots or exact text for clarity
3. Prioritize issues by severity
4. Suggest specific fixes when possible
5. Track recurring patterns across deliverables

You maintain the agency's reputation for quality. Be thorough but practical - focus on issues that would impact client satisfaction or project success.
```

## Configuration

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class QACheckType(str, Enum):
    """Types of QA checks available."""
    WEBSITE = "website"
    DOCUMENT = "document"
    VIDEO = "video"
    EMAIL_CAMPAIGN = "email_campaign"
    PRESENTATION = "presentation"
    SOCIAL_MEDIA = "social_media"

class QASeverity(str, Enum):
    """Severity levels for QA issues."""
    CRITICAL = "critical"  # Blocks delivery
    HIGH = "high"         # Should fix before delivery
    MEDIUM = "medium"     # Nice to fix
    LOW = "low"          # Minor issue

class AgentConfig:
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: float = 0.3  # Lower for consistency
    max_retries: int = 3
    timeout_seconds: int = 60
    link_check_timeout: int = 30
    spell_check_api: str = "language_tool"
    screenshot_service: str = "browserless"
```

## Input Schema

```python
class QASubmission(BaseModel):
    """Input for QA review request."""

    deliverable_id: str = Field(..., description="UUID of deliverable")
    deliverable_type: QACheckType = Field(..., description="Type of deliverable")
    project_id: str = Field(..., description="Project UUID")
    client_id: str = Field(..., description="Client UUID")
    delivery_url: Optional[str] = Field(None, description="Live URL for checking")
    file_paths: list[str] = Field(default=[], description="Local file paths")
    staging_url: Optional[str] = Field(None, description="Staging URL")
    priority: str = Field(default="normal", description="Priority level")
    auto_approve_threshold: float = Field(default=95.0, description="Auto-approve if score >= this")
    client_requirements: Optional[Dict[str, Any]] = Field(None, description="Client-specific QA rules")
    previous_issues: Optional[list[str]] = Field(None, description="Known issues to watch for")

class QAReport(BaseModel):
    """Output from QA review."""

    deliverable_id: str
    overall_status: str  # PASS, FAIL, NEEDS_FIXES
    qa_score: float = Field(..., ge=0.0, le=100.0, description="Quality score")
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    checklist_results: Dict[str, bool]
    issues_found: list["QAIssue"]
    automated_checks: Dict[str, Any]
    recommendations: list[str]
    approval_status: str  # APPROVED, REJECTED, NEEDS_REVIEW
    estimated_fix_time: Optional[int] = None  # minutes

class QAIssue(BaseModel):
    """Individual QA issue found."""

    id: str = Field(..., description="Unique issue ID")
    severity: QASeverity
    category: str  # links, branding, content, functionality
    description: str
    location: str  # Page URL, file name, section
    specific_element: Optional[str] = None  # CSS selector, line number
    screenshot_url: Optional[str] = None
    suggested_fix: Optional[str] = None
    blocks_delivery: bool = False
```

## Tools

### 1. run_automated_checks

**Purpose:** Execute all automated QA checks on a deliverable

**Input Schema:**
```python
class AutomatedChecksInput(BaseModel):
    deliverable_type: QACheckType
    delivery_url: Optional[str]
    file_paths: list[str]
    checks_to_run: list[str] = Field(default=["all"])
```

**Output Schema:**
```python
class AutomatedChecksOutput(BaseModel):
    link_check: Dict[str, Any]  # status, broken_links, total_checked
    spell_check: Dict[str, Any]  # errors_found, suggestions
    placeholder_check: Dict[str, Any]  # placeholders_found, locations
    image_check: Dict[str, Any]  # broken_images, load_times
    technical_check: Dict[str, Any]  # mobile_responsive, page_speed
    completed_at: datetime
```

**Error Handling:**
- Network timeout → Retry 3x with increasing timeout
- Rate limit (APIs) → Exponential backoff, max 5 retries
- Invalid URL → Log and continue with other checks
- File access error → Fail gracefully, report specific file

### 2. validate_branding

**Purpose:** Check branding consistency against client guidelines

**Input Schema:**
```python
class BrandingInput(BaseModel):
    deliverable_url: Optional[str]
    file_paths: list[str]
    branding_guidelines: Dict[str, Any]  # colors, fonts, logo usage
```

**Output Schema:**
```python
class BrandingOutput(BaseModel):
    brand_score: float = Field(..., ge=0.0, le=100.0)
    issues: list[Dict[str, Any]]  # color_mismatches, font_issues, logo_problems
    compliant_sections: list[str]
    violations: list[Dict[str, Any]]
```

### 3. check_completeness

**Purpose:** Verify all required sections/components are present

**Input Schema:**
```python
class CompletenessInput(BaseModel):
    deliverable_type: QACheckType
    deliverable_content: str  # Extracted text/content
    requirements: Dict[str, Any]  # Required items by type
```

**Output Schema:**
```python
class CompletenessOutput(BaseModel):
    completeness_score: float
    missing_items: list[str]
    present_items: list[str]
    optional_items: list[str]
    total_required: int
    total_present: int
```

### 4. generate_qa_report

**Purpose:** Compile all findings into comprehensive QA report

**Input Schema:**
```python
class ReportInput(BaseModel):
    deliverable_id: str
    deliverable_type: QACheckType
    automated_results: AutomatedChecksOutput
    branding_results: BrandingOutput
    completeness_results: CompletenessOutput
    priority: str
    auto_approve_threshold: float
```

### 5. request_fixes

**Purpose:** Hand off to delivery project manager with fix requirements

**Input Schema:**
```python
class FixRequestInput(BaseModel):
    deliverable_id: str
    project_id: str
    issues: list[QAIssue]
    priority: str
    deadline: Optional[datetime]
    auto_recheck: bool = True
```

## Error Handling Matrix

| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Network timeout | Exception | Retry with longer timeout | Yes, 3 attempts |
| Rate limit (429) | Status code | Exponential backoff | Yes, 5 attempts |
| Auth error (401) | Status code | Fail immediately, alert | No |
| Invalid URL | Validation | Log error, skip check | No |
| File not found | OS error | Report missing file | No |
| API limit exceeded | Response header | Queue for next batch | Yes, with delay |
| Screenshot failure | Service response | Try alternative service | Yes, 1 attempt |
| Spell check API down | Health check | Use local fallback | Yes, basic check |

## Multi-Agent Integration

### Handoff Protocols

1. **To delivery_project_manager:**
   - Trigger: Critical issues found or fixes needed
   - Payload: deliverable_id, issues, priority, deadline
   - Priority: High for critical, Normal otherwise

2. **To client_update_agent:**
   - Trigger: QA complete, ready for client notification
   - Payload: deliverable_id, status, summary
   - Priority: Normal

3. **From meeting_prep_agent:**
   - Receive: Client feedback on deliverables
   - Action: Add feedback to QA checklist for next time

### Context Management

- Store QA results in `qa_results` table with full history
- Track common issues per client for pattern recognition
- Maintain brand guideline variations per client
- Link to project management for delivery status

## Implementation Flow

### Primary Flow: Standard QA Review

1. Receive QA submission via task queue
2. Determine deliverable type and load appropriate checklist
3. Run automated checks in parallel:
   - Link validation (headless browser)
   - Spell/grammar check
   - Placeholder content detection
   - Image loading verification
4. Perform branding compliance check
5. Verify completeness against requirements
6. Generate comprehensive QA report
7. Calculate quality score and determine status
8. If issues found:
   - Hand off to delivery_project_manager
   - Track fixes and re-check
9. If passed:
   - Mark as approved for delivery
   - Notify stakeholders

### Automated Check Implementations

**Link Checking:**
```python
async def _check_links(self, url: str) -> Dict[str, Any]:
    """Check all links on a page using headless browser."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate and wait for load
        await page.goto(url, wait_until="networkidle")

        # Extract all links
        links = await page.eval_on_selector_all("a[href]", "els => els.map(el => el.href)")

        # Check each link
        broken_links = []
        for link in links:
            try:
                response = await page.goto(link)
                if response.status >= 400:
                    broken_links.append({"url": link, "status": response.status})
            except:
                broken_links.append({"url": link, "status": "Failed to load"})

        await browser.close()
        return {"total": len(links), "broken": broken_links}
```

**Spell Check Integration:**
```python
async def _check_spelling(self, content: str) -> Dict[str, Any]:
    """Check spelling using LanguageTool API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.languagetool.org/v2/check",
            data={"language": "en-US", "text": content}
        )
        results = response.json()

        errors = []
        for match in results.get("matches", []):
            errors.append({
                "message": match["message"],
                "offset": match["offset"],
                "length": match["length"],
                "suggestions": match.get("replacements", [])[:3]
            })

        return {"errors": errors, "error_count": len(errors)}
```

## Testing Strategy

### Unit Tests

```python
def test_link_check_with_broken_links():
    """Verify broken links are detected and reported."""

def test_spell_check_finds_errors():
    """Test spell checking identifies common errors."""

def test_placeholder_detection_various_formats():
    """Check for Lorem ipsum, XXX, TBD, etc."""

def test_branding_color_validation():
    """Verify hex/RGB color matching works."""

def test_completeness_check_missing_sections():
    """Ensure missing required items are flagged."""

def test_qa_score_calculation():
    """Verify score calculation weights correctly."""

def test_auto_approve_threshold():
    """Test automatic approval for high scores."""

def test_critical_issue_blocks_delivery():
    """Verify critical issues set approval_status to REJECTED."""

def test_issue_severity_classification():
    """Test proper categorization of issue severity."""
```

### Integration Tests

```python
def test_end_to_end_qa_workflow():
    """Full QA process from submission to approval."""

def test_multi_type_deliverable_handling():
    """Test handling of websites, documents, videos."""

def test_handoff_to_delivery_manager():
    """Verify issue handoff to delivery project manager."""

def test_qa_report_generation():
    """Complete report with all check results."""

def test_recheck_after_fixes():
    """Re-running QA after reported fixes."""

def test_client_specific_requirements():
    """Custom QA rules per client."""

def test_pattern_recognition_storage():
    """Store and detect recurring issue patterns."""
```

### Mock Strategy

```python
@pytest.fixture
def mock_playwright():
    with patch('playwright.async_api.async_playwright') as mock:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.goto.return_value = AsyncMock(status=200)
        mock_browser.new_page.return_value = mock_page
        mock.return_value.__aenter__.return_value = mock_browser
        yield mock

@pytest.fixture
def mock_spell_check_api():
    with patch('httpx.AsyncClient.post') as mock:
        mock.return_value.json.return_value = {
            "matches": [
                {"message": "Spelling error", "offset": 10, "length": 8}
            ]
        }
        yield mock
```

## Performance Requirements

- **Link checking:** 30 seconds timeout per page
- **Spell checking:** 10 seconds per 1000 words
- **Screenshot generation:** 5 seconds per page
- **Total QA time:** <5 minutes for typical website
- **Concurrent checks:** Up to 10 pages in parallel

## Observability

### Logging

```python
# Structured logging examples
logger.info(
    "QA check started",
    extra={
        "deliverable_id": deliverable_id,
        "deliverable_type": deliverable_type,
        "checks_requested": checks
    }
)

logger.warning(
    "Critical issue found",
    extra={
        "issue_id": issue_id,
        "severity": "critical",
        "blocks_delivery": True
    }
)
```

### Metrics to Track

- QA pass/fail rate by deliverable type
- Average time to complete QA
- Most common issue categories
- Client-specific issue patterns
- Auto-approval rate
- Re-check success rate

### Dashboards

1. **QA Metrics Dashboard:**
   - Daily QA volume
   - Pass/fail trends
   - Issue distribution by type

2. **Client Quality Portal:**
   - QA status per deliverable
   - Historical quality scores
   - Common issues per client

## Security

- No client data stored locally after QA
- Screenshot URLs expire after 7 days
- API keys for external services encrypted
- Access logs for all QA activities
- Client isolation in QA results

## Acceptance Criteria

- [ ] All deliverable types supported with specific checklists
- [ ] Automated checks run with <5% false positives
- [ ] Critical issues always block delivery
- [ ] QA reports generated within 10 minutes
- [ ] Integration with delivery project manager working
- [ ] Client-specific requirements enforced
- [ ] QA history maintained for 6 months
- [ ] Pattern recognition identifies recurring issues
- [ ] Mobile responsiveness testing accurate
- [ ] Branding guidelines properly validated
- [ ] All tools handle errors gracefully
- [ ] Unit test coverage >90%
- [ ] Integration tests cover all workflows
- [ ] Performance benchmarks met

## Database Schema

### qa_results table
```sql
CREATE TABLE qa_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deliverable_id UUID NOT NULL,
    deliverable_type VARCHAR(50) NOT NULL,
    project_id UUID NOT NULL,
    client_id UUID NOT NULL,
    overall_status VARCHAR(20) NOT NULL,
    qa_score FLOAT NOT NULL,
    checklist_results JSONB NOT NULL,
    issues_found JSONB NOT NULL,
    automated_checks JSONB NOT NULL,
    approval_status VARCHAR(20) NOT NULL,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checked_by VARCHAR(100) DEFAULT 'delivery_qa_agent',
    INDEX idx_deliverable_id (deliverable_id),
    INDEX idx_project_id (project_id),
    INDEX idx_client_id (client_id),
    INDEX idx_checked_at (checked_at)
);
```

### qa_issues table
```sql
CREATE TABLE qa_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qa_result_id UUID NOT NULL REFERENCES qa_results(id),
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    location TEXT,
    specific_element TEXT,
    screenshot_url TEXT,
    suggested_fix TEXT,
    blocks_delivery BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'open',  -- open, fixed, ignored
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_qa_result_id (qa_result_id),
    INDEX idx_severity (severity),
    INDEX idx_status (status)
);
```

### qa_checklists table
```sql
CREATE TABLE qa_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deliverable_type VARCHAR(50) NOT NULL,
    client_id UUID,  -- NULL for default
    checklist_name VARCHAR(100) NOT NULL,
    checklist_items JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (deliverable_type, client_id, checklist_name)
);
```
