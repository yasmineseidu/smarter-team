# Data Validation Agent - Production Specification

## Metadata

**Agent Name:** `data_validation`
**Category:** Lead Generation & Data
**Priority:** Phase 1 - MVP Foundation
**Dependencies:** Email Verification Agent (provides verification status)
**Coverage Target:** >85% (agent requirement)

---

## Purpose

Ensure lead data quality before campaign enrollment by applying comprehensive validation rules, generating detailed reports, blocking invalid leads, and queuing incomplete leads for enrichment. Maintains high data integrity standards to protect campaign deliverability and conversion rates.

---

## System Prompt

```
You are the Data Validation Agent for Smarter Team, an autonomous AI agency.

Your primary responsibility is to ensure lead data quality through comprehensive validation before campaigns are launched. You maintain data integrity standards that protect deliverability and maximize conversion rates.

**Core Responsibilities:**
1. Apply validation rules to all incoming leads before campaign assignment
2. Generate detailed validation reports with failure reasons and scores
3. Block invalid leads from entering campaigns to protect sender reputation
4. Queue incomplete leads for enrichment with specific requirements
5. Maintain validation logs for quality tracking and pattern analysis
6. Handle batch validations efficiently with parallel processing

**Validation Rules & Decision Matrix:**
- first_name: Must be non-empty and not contain placeholder values ("N/A", "Unknown", "Test")
- company_name: Must be non-empty and at least 2 characters long
- email: Must be valid format AND have verification status from Email Verification Agent
- domain: Must match company domain when both are present (fuzzy matching allowed)
- linkedin_url: Optional but must be valid LinkedIn URL format if present
- job_title: Optional but should indicate seniority level if present

**Validation Scores & Actions:**
- Score 90-100: VALID → Proceed to campaign
- Score 70-89: VALID_WITH_FLAGS → Proceed but log concerns
- Score 50-69: REQUIRES_ENRICHMENT → Queue for enrichment, block from campaigns
- Score <50: INVALID → Block permanently, log for analysis

**Business Logic Rules:**
- Don't block leads with optional fields missing (job_title, linkedin_url)
- Apply fuzzy matching for domain-company validation (allow subdomains, common variations)
- Consider verification status weight (verified emails score higher)
- Prioritize leads with complete information for campaigns
- Flag suspicious patterns (all caps, special characters, placeholder text)

**Quality Standards:**
- Process leads in batches of 100-500 for efficiency
- Provide specific failure reasons for each validation rule
- Track validation trends and common failure patterns
- Log all decisions with supporting evidence
- Maintain validation history for each lead

**Enrichment Handoff Protocol:**
When leads require enrichment, hand off to appropriate agents with:
- Lead ID and contact details
- Validation score and specific missing fields
- Priority level based on data completeness
- Enrichment type required (email, company data, contact info)
- Campaign urgency (if applicable)

**Error Handling:**
- Graceful degradation when external services are unavailable
- Maintain audit trail even when validation fails
- Provide partial results when some validations succeed
- Never lose lead data during validation process

You work autonomously but prioritize data quality while maintaining campaign velocity. Balance thoroughness with efficiency to support scalable lead generation.
```

---

## Agent Implementation

### Class Definition

```python
from src.agents.base_agent import BaseAgent
from src.config import Settings, get_agent_logger
from src.tasks.orchestration_tasks import agent_handoff
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum
import asyncio
import re
from urllib.parse import urlparse

class ValidationStatus(str, Enum):
    VALID = "VALID"
    VALID_WITH_FLAGS = "VALID_WITH_FLAGS"
    REQUIRES_ENRICHMENT = "REQUIRES_ENRICHMENT"
    INVALID = "INVALID"

class ValidationRule(str, Enum):
    FIRST_NAME_REQUIRED = "first_name_required"
    FIRST_NAME_NOT_PLACEHOLDER = "first_name_not_placeholder"
    COMPANY_NAME_REQUIRED = "company_name_required"
    COMPANY_NAME_MIN_LENGTH = "company_name_min_length"
    EMAIL_VALID_FORMAT = "email_valid_format"
    EMAIL_VERIFIED = "email_verified"
    DOMAIN_MATCHES_COMPANY = "domain_matches_company"
    LINKEDIN_URL_FORMAT = "linkedin_url_format"
    JOB_TITLE_PRESENT = "job_title_present"

class LeadData(BaseModel):
    """Schema for lead data input."""
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    job_title: Optional[str] = None
    verification_status: Optional[str] = None  # From Email Verification Agent
    verification_score: Optional[int] = None  # From Email Verification Agent

class ValidationResult(BaseModel):
    """Schema for validation result."""
    lead_id: str
    status: ValidationStatus
    score: int = Field(ge=0, le=100)
    failed_rules: List[ValidationRule] = []
    warnings: List[str] = []
    enrichment_required: List[str] = []
    blocked_fields: List[str] = []
    metadata: Dict[str, Any] = {}
    validated_at: datetime = Field(default_factory=datetime.utcnow)

class ValidationReport(BaseModel):
    """Schema for batch validation report."""
    batch_id: str
    total_leads: int
    valid_count: int
    valid_with_flags_count: int
    requires_enrichment_count: int
    invalid_count: int
    results: List[ValidationResult]
    summary: Dict[str, Any] = {}
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class DataValidationAgent(BaseAgent):
    """
    Data Validation Agent - Ensures lead data quality before campaigns.

    Applies comprehensive validation rules, generates reports, and routes
    leads to enrichment when needed.
    """

    def __init__(self, settings: Settings):
        super().__init__(
            name="data_validation",
            description="Validates lead data quality and routes to enrichment"
        )
        self.settings = settings
        self.placeholder_patterns = [
            r"^(n/a|na|none|null|unknown|test|demo|sample)\b",
            r"^\s*$",
            r"^(first|last|name|contact|info)$"
        ]
        self.batch_size = 250  # Optimal for performance

    @property
    def system_prompt(self) -> str:
        return """[See System Prompt section above]"""

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Process data validation task."""
        task_type = task.get("type")

        if task_type == "validate_single":
            return await self._validate_single(task)
        elif task_type == "validate_batch":
            return await self._validate_batch(task)
        elif task_type == "generate_report":
            return await self._generate_report(task)
        else:
            self.logger.error(f"Unknown task type: {task_type}")
            raise ValueError(f"Unknown task type: {task_type}")

    async def _validate_single(self, task: dict[str, Any]) -> dict[str, Any]:
        """Validate a single lead."""
        lead_data = LeadData(**task["lead"])
        result = await self._validate_lead(lead_data)

        # Route based on validation status
        if result.status in [ValidationStatus.REQUIRES_ENRICHMENT, ValidationStatus.INVALID]:
            await self._route_for_enrichment(lead_data, result)

        return {"validation_result": result.dict()}

    async def _validate_batch(self, task: dict[str, Any]) -> dict[str, Any]:
        """Validate a batch of leads."""
        leads = [LeadData(**lead) for lead in task["leads"]]
        batch_id = task.get("batch_id", f"batch_{datetime.utcnow().timestamp()}")

        # Process in parallel for efficiency
        results = await asyncio.gather(
            *[self._validate_lead(lead) for lead in leads],
            return_exceptions=True
        )

        # Filter out exceptions and log errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error validating lead {leads[i].id}: {result}")
                continue
            valid_results.append(result)

        # Route problematic leads
        enrichment_leads = [
            (leads[i], results[i])
            for i, result in enumerate(valid_results)
            if result.status in [ValidationStatus.REQUIRES_ENRICHMENT, ValidationStatus.INVALID]
        ]

        if enrichment_leads:
            await asyncio.gather(
                *[self._route_for_enrichment(lead, result) for lead, result in enrichment_leads]
            )

        # Generate report
        report = ValidationReport(
            batch_id=batch_id,
            total_leads=len(leads),
            valid_count=sum(1 for r in valid_results if r.status == ValidationStatus.VALID),
            valid_with_flags_count=sum(1 for r in valid_results if r.status == ValidationStatus.VALID_WITH_FLAGS),
            requires_enrichment_count=sum(1 for r in valid_results if r.status == ValidationStatus.REQUIRES_ENRICHMENT),
            invalid_count=sum(1 for r in valid_results if r.status == ValidationStatus.INVALID),
            results=valid_results
        )

        # Log batch summary
        self.logger.info(
            f"Batch validation complete",
            extra={
                "batch_id": batch_id,
                "total": len(leads),
                "valid": report.valid_count,
                "requires_enrichment": report.requires_enrichment_count,
                "invalid": report.invalid_count
            }
        )

        return {"validation_report": report.dict()}

    async def _validate_lead(self, lead: LeadData) -> ValidationResult:
        """Apply all validation rules to a lead."""
        score = 100
        failed_rules = []
        warnings = []
        enrichment_required = []
        blocked_fields = []
        metadata = {}

        # Rule: First name required
        if not lead.first_name or not lead.first_name.strip():
            score -= 30
            failed_rules.append(ValidationRule.FIRST_NAME_REQUIRED)
            blocked_fields.append("first_name")
            enrichment_required.append("first_name")
        else:
            # Rule: First name not placeholder
            if self._is_placeholder(lead.first_name):
                score -= 25
                failed_rules.append(ValidationRule.FIRST_NAME_NOT_PLACEHOLDER)
                blocked_fields.append("first_name")
                enrichment_required.append("first_name")

        # Rule: Company name required
        if not lead.company_name or not lead.company_name.strip():
            score -= 25
            failed_rules.append(ValidationRule.COMPANY_NAME_REQUIRED)
            blocked_fields.append("company_name")
            enrichment_required.append("company_name")
        else:
            # Rule: Company name minimum length
            if len(lead.company_name.strip()) < 2:
                score -= 15
                failed_rules.append(ValidationRule.COMPANY_NAME_MIN_LENGTH)
                warnings.append("Company name appears too short")

        # Rule: Email format
        if not lead.email:
            score -= 40
            failed_rules.append(ValidationRule.EMAIL_VALID_FORMAT)
            blocked_fields.append("email")
            enrichment_required.append("email")
        else:
            # Rule: Email verification status (weighted more heavily)
            if not lead.verification_status:
                score -= 30
                failed_rules.append(ValidationRule.EMAIL_VERIFIED)
                enrichment_required.append("email_verification")
                warnings.append("Email not verified")
            elif lead.verification_status not in ["SAFE", "VALID"]:
                score -= 35
                failed_rules.append(ValidationRule.EMAIL_VERIFIED)
                blocked_fields.append("email")
                enrichment_required.append("email_replacement")

            # Apply verification score if available
            if lead.verification_score is not None:
                if lead.verification_score >= 80:
                    pass  # No penalty
                elif lead.verification_score >= 60:
                    score -= 10
                    warnings.append("Email score moderate")
                else:
                    score -= 25
                    blocked_fields.append("email")

        # Rule: Domain matches company
        if lead.domain and lead.company_name:
            if not self._domain_matches_company(lead.domain, lead.company_name):
                score -= 10
                failed_rules.append(ValidationRule.DOMAIN_MATCHES_COMPANY)
                warnings.append("Domain doesn't match company name")

        # Rule: LinkedIn URL format (optional)
        if lead.linkedin_url:
            if not self._is_valid_linkedin_url(lead.linkedin_url):
                score -= 5
                warnings.append("Invalid LinkedIn URL format")

        # Determine status
        if score >= 90:
            status = ValidationStatus.VALID
        elif score >= 70:
            status = ValidationStatus.VALID_WITH_FLAGS
        elif score >= 50:
            status = ValidationStatus.REQUIRES_ENRICHMENT
        else:
            status = ValidationStatus.INVALID

        metadata.update({
            "validation_checks_performed": len(ValidationRule),
            "field_completeness": sum(1 for v in [lead.first_name, lead.company_name, lead.email, lead.domain, lead.job_title, lead.linkedin_url] if v),
            "has_verification": lead.verification_status is not None
        })

        return ValidationResult(
            lead_id=lead.id,
            status=status,
            max(score, 0),
            failed_rules=failed_rules,
            warnings=warnings,
            enrichment_required=enrichment_required,
            blocked_fields=blocked_fields,
            metadata=metadata
        )

    def _is_placeholder(self, value: str) -> bool:
        """Check if value is a placeholder."""
        value_lower = value.lower().strip()
        return any(re.match(pattern, value_lower) for pattern in self.placeholder_patterns)

    def _domain_matches_company(self, domain: str, company: str) -> bool:
        """Check if domain matches company name (fuzzy matching)."""
        # Extract domain without TLD
        domain_parts = domain.lower().split('.')
        domain_base = domain_parts[0] if len(domain_parts) >= 2 else domain

        # Clean company name
        company_clean = re.sub(r'[^a-zA-Z0-9]', '', company.lower())

        # Check for exact match
        if domain_base in company_clean or company_clean in domain_base:
            return True

        # Check for partial match (at least 3 chars)
        for i in range(len(domain_base) - 2):
            if domain_base[i:i+3] in company_clean:
                return True

        return False

    def _is_valid_linkedin_url(self, url: str) -> bool:
        """Validate LinkedIn URL format."""
        try:
            parsed = urlparse(url)
            return parsed.netloc in ['linkedin.com', 'www.linkedin.com'] and '/in/' in parsed.path
        except:
            return False

    async def _route_for_enrichment(self, lead: LeadData, result: ValidationResult) -> None:
        """Route lead to appropriate enrichment agent."""
        # Determine enrichment priority
        if result.status == ValidationStatus.INVALID:
            priority = "low"
        elif "email" in result.enrichment_required:
            priority = "high"
        else:
            priority = "normal"

        # Determine enrichment type
        if "email" in result.enrichment_required or "email_verification" in result.enrichment_required:
            target_agent = "email_verification"
        elif "company" in result.enrichment_required:
            target_agent = "company_enrichment"
        elif "first_name" in result.enrichment_required or "last_name" in result.enrichment_required:
            target_agent = "contact_enrichment"
        else:
            target_agent = "waterfall_enrichment"

        payload = {
            "lead_id": lead.id,
            "validation_result": result.dict(),
            "missing_fields": result.enrichment_required,
            "blocked_fields": result.blocked_fields,
            "current_data": lead.dict(exclude_unset=True),
            "campaign_urgency": result.metadata.get("campaign_urgency", "normal")
        }

        await self.handoff_to(target_agent, payload, priority)

        self.logger.info(
            f"Routed lead {lead.id} to {target_agent}",
            extra={
                "priority": priority,
                "missing_fields": result.enrichment_required,
                "validation_score": result.score
            }
        )

    async def _generate_report(self, task: dict[str, Any]) -> dict[str, Any]:
        """Generate validation quality report."""
        # This would query validation_logs and generate analytics
        # For now, return a placeholder
        return {
            "report_type": "validation_quality",
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": {
                "total_validations": 0,
                "average_score": 0,
                "common_failures": []
            }
        }
```

---

## Tools

### Tool: validate_lead_data
**Purpose:** Validate a single lead's data against all rules

**Input Schema:**
```python
class ValidateLeadInput(BaseModel):
    lead: dict[str, Any] = Field(..., description="Lead data to validate")
    strict_mode: bool = Field(default=False, description="Use strict validation rules")
```

**Output Schema:**
```python
class ValidateLeadOutput(BaseModel):
    validation_result: ValidationResult
    routed_for_enrichment: bool
    enrichment_target: Optional[str]
```

**Error Handling:**
- Invalid lead data → Return validation error with details
- Missing required fields → Log and continue with available data
- Database timeout → Retry 3x with exponential backoff

---

### Tool: validate_batch_leads
**Purpose:** Validate multiple leads in parallel

**Input Schema:**
```python
class ValidateBatchInput(BaseModel):
    leads: list[dict[str, Any]] = Field(..., min_items=1, max_items=500)
    batch_id: Optional[str] = Field(None, description="Custom batch identifier")
    continue_on_error: bool = Field(default=True)
```

**Output Schema:**
```python
class ValidateBatchOutput(BaseModel):
    validation_report: ValidationReport
    routed_for_enrichment: int
    errors: list[str]
```

**Error Handling:**
- Batch too large → Split into smaller batches and process
- Some leads fail → Continue processing others if continue_on_error=True
- Parallel processing errors → Fall back to sequential processing

---

### Tool: update_validation_rules
**Purpose:** Update validation rules and weights

**Input Schema:**
```python
class UpdateRulesInput(BaseModel):
    rule_updates: dict[str, dict] = Field(..., description="Rule changes")
    effective_date: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str = Field(..., description="Who made the change")
```

**Output Schema:**
```python
class UpdateRulesOutput(BaseModel):
    rules_updated: int
    validation_version: str
    rollback_available: bool
```

**Error Handling:**
- Invalid rule definition → Return specific validation error
- Unauthorized changes → Reject and log security event
- Rule conflicts → Detect and report conflicts

---

## Error Handling Matrix

| Error Type | Detection | Response | Retry |
|------------|-----------|----------|-------|
| Invalid lead data | Pydantic validation | Return detailed error | No |
| Database connection error | SQLAlchemy exception | Retry 3x with backoff | Yes |
| Concurrent modification | Version conflict | Retry once with fresh data | Yes |
| Enrichment handoff failure | Celery task error | Log and queue for retry | Yes |
| Rate limit exceeded | HTTP 429 | Exponential backoff, max 5 retries | Yes |
| Invalid validation rules | Rule validation | Reject with details | No |
| Missing verification status | Field check | Route to email verification | Yes (via handoff) |

### Recovery Strategies
1. **Partial validation:** Return results for successful validations when batch partially fails
2. **Fallback processing:** Switch from parallel to sequential processing on errors
3. **Audit persistence:** Never lose validation data, store in dead-letter queue on failure
4. **Graceful degradation:** Continue with available data when external services down

---

## Multi-Agent Integration

### Handoff Destinations
- **email_verification**: When email needs verification or replacement
- **company_enrichment**: When company data missing or incomplete
- **contact_enrichment**: When contact details missing
- **waterfall_enrichment**: When multiple fields need enrichment

### Handoff Triggers
- Validation score < 50 (INVALID)
- Validation score 50-69 (REQUIRES_ENRICHMENT)
- Missing critical fields (email, first_name, company_name)
- Unverified email status

### Incoming Dependencies
- **Lead List Builder**: Provides initial lead data
- **Email Verification Agent**: Provides verification status and scores

### Outgoing Dependencies
- **Campaign Creation Agent**: Receives validated leads
- **Enrichment Agents**: Receive leads needing completion

---

## Testing Strategy

### Unit Tests
```python
class TestDataValidationAgent:
    @pytest.mark.asyncio
    async def test_validate_complete_lead(self):
        """Verify valid lead passes all validation rules"""

    @pytest.mark.asyncio
    async def test_validate_missing_email(self):
        """Verify missing email reduces score and routes to enrichment"""

    @pytest.mark.asyncio
    async def test_placeholder_first_name(self):
        """Verify placeholder names are detected and penalized"""

    @pytest.mark.asyncio
    async def test_domain_company_match(self):
        """Verify fuzzy matching works for domain-company validation"""

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Verify batch validation processes all leads in parallel"""

    @pytest.mark.asyncio
    async def test_enrichment_routing(self):
        """Verify leads route to correct enrichment agent"""
```

### Integration Tests
```python
class TestValidationIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_validation_flow(self):
        """Test full flow from lead data to enrichment handoff"""

    @pytest.mark.asyncio
    async def test_database_persistence(self):
        """Test validation results saved to database"""

    @pytest.mark.asyncio
    async def test_concurrent_validation(self):
        """Test multiple validations running concurrently"""
```

### Mock Strategy
```python
@pytest.fixture
def mock_enrichment_agent():
    with patch('src.agents.data_validation.agent_handoff') as mock:
        mock.return_value.id = "task_123"
        yield mock

@pytest.fixture
def mock_database():
    with patch('src.database.SessionLocal') as mock:
        yield mock
```

### Performance Tests
- **Batch size scaling**: Test 10, 100, 500 lead batches
- **Parallel processing**: Verify <1s per 100 leads average
- **Memory usage**: Ensure <100MB for 1000 lead batch
- **Error rate**: Verify <0.1% validation failures on good data

---

## Performance

### Targets
- **Single validation**: <50ms latency
- **Batch validation**: <1s for 100 leads (parallel)
- **Throughput**: 500+ leads/second sustained
- **Memory**: <50MB base, +1KB per lead in batch

### Caching Strategy
- **Domain patterns**: Cache domain-company matches (24h TTL)
- **Placeholder patterns**: Cache compiled regex patterns
- **Validation rules**: Cache rule definitions with version
- **Enrichment routing**: Cache target agent decisions

### Scaling Considerations
- Horizontal scaling with multiple agent instances
- Database connection pooling for high throughput
- Redis caching for frequent validation patterns
- Queue-based processing for large batches

---

## Observability

### Logging
```python
# Structured logging examples
self.logger.info(
    "Lead validation completed",
    extra={
        "lead_id": lead.id,
        "score": result.score,
        "status": result.status,
        "failed_rules": len(result.failed_rules),
        "processing_time_ms": processing_time
    }
)

self.logger.error(
    "Validation batch failed",
    extra={
        "batch_id": batch_id,
        "error": str(error),
        "processed_count": processed,
        "total_count": total
    }
)
```

### Metrics to Track
- **Validation rates**: Total validations, success rate, failure rate
- **Score distribution**: Histogram of validation scores
- **Common failures**: Top 10 failed validation rules
- **Enrichment routing**: Volume by target agent
- **Processing latency**: P95, P99 response times
- **Throughput**: Validations per second

### Dashboards
- **Real-time validation queue**: Current queue size and processing rate
- **Quality metrics**: Validation score trends over time
- **Error tracking**: Failed validations by error type
- **Enrichment pipeline**: Leads requiring enrichment by field

---

## Security

### Data Protection
- **PII detection**: Flag and mask sensitive data in logs
- **Audit trail**: Immutable log of all validation decisions
- **Data retention**: Configurable retention periods for validation logs

### Access Control
- **Rule updates**: Require admin role for validation rule changes
- **Audit access**: Role-based access to validation reports
- **API rate limiting**: Prevent abuse of validation endpoints

### Compliance
- **GDPR**: Right to deletion extends to validation logs
- **Data residency**: Store validation data in configured regions
- **Consent tracking**: Validate consent status where required

---

## Acceptance Criteria

- [ ] Lead validation completes within 50ms for single leads
- [ ] Batch validation processes 500 leads in under 5 seconds
- [ ] All validation rules are enforced with correct scoring
- [ ] Invalid/risky leads are blocked from campaigns
- [ ] Leads requiring enrichment are routed with correct priority
- [ ] Validation reports include detailed failure reasons
- [ ] All validation decisions are logged for audit
- [ ] System handles parallel validation without data corruption
- [ ] Validation rules can be updated without code deployment
- [ ] Unit test coverage >90% for agent logic
- [ ] Integration tests cover all handoff scenarios
- [ ] Performance benchmarks met under load
- [ ] Security requirements implemented (PII masking, audit logs)
- [ ] Monitoring and alerting configured for all critical metrics
