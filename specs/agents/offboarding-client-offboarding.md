# Client Offboarding Agent - Production Specification

## Overview

**Agent Name:** `client_offboarding`

**Category:** Offboarding & Nurture

**Purpose:** Orchestrate complete client project offboarding with checklist-driven process, ensuring smooth transition from active project to long-term nurture while maintaining professionalism and collecting valuable feedback.

**Priority:** Phase 5 - Retention & Growth

**Dependencies:**
- Project Management Agent (provides completion status and project data)
- Invoice Generation Agent (provides final invoice details)
- Testimonial Request Agent (handles testimonial collection)
- Long-term Nurture Agent (receives offboarded clients)
- Stripe integration (payment verification)
- Google Drive integration (file handoff)
- Email sending integration (communication)

---

## System Prompt

```
You are a Client Offboarding Specialist for Smarter Team, an AI agency. Your role is to ensure every client project concludes professionally, completely, and positively, turning satisfied clients into long-term relationships.

**Core Responsibilities:**
1. Execute comprehensive offboarding checklist for each completed project
2. Coordinate final deliverable handoff with proper file organization
3. Verify and collect final payments
4. Manage access revocation and credential returns
5. Archive project data systematically
6. Collect feedback and testimonials gracefully
7. Transition clients to long-term nurture sequence

**Tone & Style:**
- Professional, warm, and appreciative
- Meticulously organized and detail-oriented
- Proactive in anticipating client needs
- Grateful for their business and feedback
- Clear and concise in all communications

**Checklist Philosophy:**
- No item is too small to overlook
- Double-check everything before marking complete
- Document exceptions and special cases
- Escalate to human only for unique situations not covered by playbook

**Communication Guidelines:**
- Always start with gratitude for the opportunity
- Provide clear, actionable next steps
- Include specific links and resources
- Set expectations for timelines
- Leave the door open for future engagement

**Examples:**

Project Completion:
"Congratulations on completing {{project_name}}! I'm thrilled with what we accomplished together. I've prepared all your deliverables and organized them in your Drive folder. Here's what happens next..."

Final Payment:
"Thank you for your prompt payment on {{project_name}}. Your account is now settled in full. We've updated our records and archived the project according to our retention policy."

Feedback Request:
"Your feedback helps us improve. Would you be willing to share 2-3 minutes of thoughts about your experience? If you'd be open to providing a testimonial, that would mean the world to our team."

**Critical Rules:**
- NEVER revoke access until final payment is confirmed
- ALWAYS verify file permissions before sharing with client
- DOCUMENT any deviations from standard process
- FOLLOW UP if no response to important requests within 3 business days
- PRESERVE all project data according to retention policy
```

---

## Agent Architecture

### Base Class
Extends `BaseAgent` from `src/agents/base_agent.py`

### File Structure
```
src/agents/client_offboarding/
├── __init__.py              # Export ClientOffboardingAgent
├── agent.py                 # Main agent class
├── tools.py                 # Tool functions for offboarding tasks
├── prompts.py               # System prompt and email templates
├── schemas.py               # Pydantic models for requests/responses
└── exceptions.py            # Custom exceptions
```

---

## Tools

### 1. `get_offboarding_checklist`

**Description:** Retrieve the offboarding checklist status for a specific client project.

**Parameters:**
```python
@dataclass
class GetOffboardingChecklistParams:
    project_id: str                   # Unique project identifier
    client_id: str                    # Client identifier
    include_completed: bool = False   # Show completed items
```

**Returns:**
```python
@dataclass
class OffboardingChecklist:
    project_id: str
    client_id: str
    status: str                       # NOT_STARTED, IN_PROGRESS, COMPLETED
    sections: list[ChecklistSection]
    last_updated: datetime

@dataclass
class ChecklistSection:
    name: str                         # "Deliverables", "Financial", etc.
    items: list[ChecklistItem]
    completion_rate: float            # 0.0 to 1.0

@dataclass
class ChecklistItem:
    id: str
    description: str
    completed: bool
    completed_at: datetime | None
    notes: str | None
```

**Error Handling:**
- Project not found → Create new checklist with default items
- Database timeout → Retry 3x with exponential backoff
- Multiple checklists → Log warning, use most recent

---

### 2. `update_checklist_item`

**Description:** Mark a checklist item as complete or add notes.

**Parameters:**
```python
@dataclass
class UpdateChecklistItemParams:
    project_id: str
    item_id: str
    completed: bool | None = None     # Set to True/False or None to only add notes
    notes: str | None = None          # Additional context or issues
    evidence: dict | None = None      # Supporting data (file IDs, URLs, etc.)
```

**Returns:**
```python
{
    "success": bool,
    "item_id": str,
    "updated_fields": list[str],
    "section_completion": float,
    "overall_completion": float
}
```

**Error Handling:**
- Invalid item_id → Return validation error with available items
- Concurrent update → Use last-write-wins, log conflict
- Database constraint → Rollback and retry once

---

### 3. `prepare_deliverable_handoff`

**Description:** Organize and prepare final deliverables for client access.

**Parameters:**
```python
@dataclass
class PrepareDeliverableHandoffParams:
    project_id: str
    client_id: str
    deliverable_sources: list[str]    # Drive folders, file IDs, URLs
    access_level: str = "viewer"       # "viewer", "editor", "owner"
    notification_email: bool = True
```

**Returns:**
```python
{
    "handoff_id": str,
    "drive_folder_url": str,
    "shared_files": list[FileInfo],
    "access_granted_to": list[str],
    "notification_sent": bool,
    "expiry_date": datetime | None
}
```

**Error Handling:**
- Drive API failure → Retry 3x, then escalate to human
- Permission denied → Check folder ownership, create new folder
- File not found → Log missing files, continue with available ones
- Quota exceeded → Use alternative sharing method (external link)

---

### 4. `verify_final_payment`

**Description:** Check if final invoice has been paid and update project status.

**Parameters:**
```python
@dataclass
class VerifyFinalPaymentParams:
    project_id: str
    client_id: str
    invoice_id: str | None = None     # If None, query for latest invoice
    grace_period_days: int = 3        # Days after due date to wait
```

**Returns:**
```python
{
    "payment_status": str,            # PAID, PENDING, OVERDUE, NOT_FOUND
    "amount": float,
    "due_date": datetime,
    "paid_date": datetime | None,
    "days_overdue": int | None,
    "last_payment_attempt": datetime | None
}
```

**Error Handling:**
- Stripe API error → Retry with exponential backoff, max 5 attempts
- Invalid invoice_id → Query client's invoice history
- Partial payment → Record amount, notify human for review
- Refund detected → Flag for human review

---

### 5. `revoke_access_credentials`

**Description:** Revoke client access to systems and return credentials.

**Parameters:**
```python
@dataclass
class RevokeAccessCredentialsParams:
    project_id: str
    client_id: str
    access_types: list[str]           # "api_keys", "user_accounts", "shared_tools"
    keep_active: list[str] | None     # Access to maintain (e.g., long-term portal)
    revocation_reason: str = "project_completed"
```

**Returns:**
```python
{
    "revoked": list[AccessRevocation],
    "failed": list[FailedRevocation],
    "maintained": list[str],
    "revocation_summary": {
        "total_attempted": int,
        "successful": int,
        "failed": int
    }
}
```

**Error Handling:**
- API limit exceeded → Queue for batch processing
- Credential not found → Log and continue
- Revocation failed → Escalate to human immediately
- Third-party service down → Schedule retry for later

---

### 6. `archive_project_data`

**Description:** Move project data to archive and update status.

**Parameters:**
```python
@dataclass
class ArchiveProjectDataParams:
    project_id: str
    archive_location: str = "cold_storage"  # "cold_storage", "active_archive"
    retain_sensitive: bool = False           # Keep PII for X days per policy
    create_backup: bool = True
```

**Returns:**
```python
{
    "archive_id": str,
    "archive_location": str,
    "data_size_gb": float,
    "files_archived": int,
    "retention_policy": {
        "standard_data": "years_7",
        "sensitive_data": "days_90"
    },
    "completion_time": datetime
}
```

**Error Handling:**
- Insufficient storage → Alert ops, use alternative location
- Data corruption during transfer → Retry from source
- Archive service unavailable → Queue for later processing
- Retention policy conflict → Flag for compliance review

---

### 7. `send_feedback_request`

**Description:** Send satisfaction survey and testimonial request.

**Parameters:**
```python
@dataclass
class SendFeedbackRequestParams:
    project_id: str
    client_id: str
    client_email: str
    client_name: str
    request_type: str = "both"          # "survey", "testimonial", "both"
    testimonial_eligible: bool = True
    personalization: dict | None = None
```

**Returns:**
```python
{
    "survey_sent": bool,
    "survey_url": str | None,
    "testimonial_sent": bool,
    "testimonial_url": str | None,
    "email_ids": list[str],
    "follow_up_scheduled": datetime
}
```

**Error Handling:**
- Email bounce → Update contact info, retry with alternative
- Survey platform down → Send simple email instead
- Personalization merge failed → Use default template
- Rate limited → Queue for next available slot

---

### 8. `transition_to_nurture`

**Description:** Move client to long-term nurture sequence.

**Parameters:**
```python
@dataclass
class TransitionToNurtureParams:
    client_id: str
    project_id: str
    nurture_sequence: str = "standard"   # "standard", "vip", "custom"
    tags: list[str] | None = None       # "testimonial_provided", "high_value"
    preferences: dict | None = None      # Communication preferences
```

**Returns:**
```python
{
    "nurture_id": str,
    "sequence_name": str,
    "next_touchpoint": datetime,
    "added_tags": list[str],
    "preferences_set": bool
}
```

**Error Handling:**
- Already in nurture → Update existing record, log
- Invalid sequence → Default to standard
- Tag creation failed → Continue without tags
- Preference validation error → Use defaults

---

## Error Handling Matrix

| Component | Error Type | Detection | Response | Retry Strategy |
|-----------|------------|-----------|----------|----------------|
| Database | Connection timeout | Exception | Retry 3x | Exponential backoff |
| Database | Constraint violation | DB error | Log, skip item | No |
| Stripe | Rate limit (429) | Status code | Wait, retry | Yes, exponential |
| Stripe | Auth error (401) | Status code | Alert ops | No |
| Google Drive | Quota exceeded | Error code | Use external link | Yes, immediate |
| Google Drive | Permission denied | Error code | Check ownership | Yes, 3 attempts |
| Email | Bounce/Complaint | Webhook | Update contact | No |
| Email | Rate limit | Response | Queue | Yes, with delay |
| Archive | Storage full | Check before | Alert ops | No |
| Archive | Service down | Health check | Queue | Yes, later |

---

## Testing Strategy

### Unit Tests

```python
# Test file: __tests__/unit/agents/test_client_offboarding.py

class TestClientOffboardingAgent:
    @pytest.mark.asyncio
    async def test_get_offboarding_checklist_new_project(self):
        """Verify checklist creation for new project."""

    @pytest.mark.asyncio
    async def test_verify_payment_paid_invoice(self):
        """Verify successful payment detection."""

    @pytest.mark.asyncio
    async def test_prepare_deliverable_handoff_success(self):
        """Test successful file organization and sharing."""

    @pytest.mark.asyncio
    async def test_revoke_access_partial_failure(self):
        """Test handling of mixed success/failure revocations."""

    @pytest.mark.asyncio
    async def test_archive_project_insufficient_storage(self):
        """Test graceful handling of storage issues."""
```

### Integration Tests

```python
# Test file: __tests__/integration/test_client_offboarding_integration.py

class TestClientOffboardingIntegration:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_end_to_end_offboarding_flow(self):
        """Complete offboarding from project completion to nurture."""

    @pytest.mark.asyncio
    async def test_concurrent_offboardings(self):
        """Verify multiple projects can be offboarded simultaneously."""

    @pytest.mark.asyncio
    async def test_payment_retry_flow(self):
        """Test payment verification retry logic."""
```

### Mock Strategy

```python
# fixtures/offboarding_fixtures.py

@pytest.fixture
def mock_stripe_client():
    with patch("src.integrations.stripe.StripeClient") as mock:
        mock.return_value.get_invoice.return_value = {
            "status": "paid",
            "amount": 5000,
            "paid_at": datetime.now()
        }
        yield mock

@pytest.fixture
def mock_drive_client():
    with patch("src.integrations.google_drive.DriveClient") as mock:
        mock.return_value.create_folder.return_value = {
            "id": "folder_123",
            "url": "https://drive.google.com/drive/folders/..."
        }
        yield mock

@pytest.fixture
def mock_email_client():
    with patch("src.integrations.email.EmailClient") as mock:
        mock.return_value.send_template.return_value = {
            "message_id": "msg_456",
            "status": "sent"
        }
        yield mock
```

---

## Performance & Scalability

### Expected Performance
- **Offboarding initiation:** < 2 seconds
- **Checklist updates:** < 500ms per item
- **File handoff preparation:** < 10 seconds for up to 100 files
- **Payment verification:** < 3 seconds (including retries)
- **Full offboarding process:** 5-15 minutes depending on complexity

### Batch Processing
- Support for processing multiple projects simultaneously
- Queue-based email sending to respect rate limits
- Batch archive operations during off-peak hours

### Caching Strategy
- Cache checklist templates (1 hour TTL)
- Cache client preferences (24 hours TTL)
- Cache Stripe invoice status (5 minutes TTL)

---

## Monitoring & Observability

### Key Metrics
- Offboarding completion rate (target: >95%)
- Average time to complete offboarding
- Payment collection rate (target: >98%)
- Testimonial collection rate (target: >30%)
- Error rates by component

### Logging Levels
- **INFO:** Normal offboarding progress, checklist updates
- **WARN:** Retry attempts, partial failures, client non-responses
- **ERROR:** Failed revocations, archive failures, payment issues
- **DEBUG:** API call details, state transitions

### Alerts
- Payment overdue > 7 days
- Archive failure > 3 attempts
- Access revocation failure for critical systems
- Offboarding stuck > 48 hours without progress

---

## Security Considerations

### Data Protection
- Encrypt sensitive client data before archiving
- Rotate all API keys after offboarding
- Maintain audit trail of all access changes
- Follow GDPR/CCPA for data retention/deletion

### Access Control
- Principle of least privilege for all systems
- Document all shared access during project
- Verify revocation completion
- Keep emergency access for critical issues

### Compliance
- Retention policy: 7 years standard, 90 days for PII
- Audit logging for all financial transactions
- Client data export on request
- Right to deletion implementation

---

## Acceptance Criteria

- [ ] All offboarding checklists can be customized per project type
- [ ] Final deliverables are properly organized and shared with clients
- [ ] Final payments are verified before access revocation
- [ ] All system access is properly revoked and documented
- [ ] Project data is archived according to retention policy
- [ ] Satisfaction surveys are sent to all clients
- [ ] Testimonial requests are sent when eligible
- [ ] Clients are transitioned to nurture sequence
- [ ] All actions are logged for audit purposes
- [ ] Error handling covers all failure modes
- [ ] Performance meets specified targets
- [ ] Security requirements are fully implemented
- [ ] Integration tests pass with 100% success rate
- [ ] Unit test coverage > 90% for all tools

---

**Status:** Ready to Build
**Last Updated:** 2025-12-05
**Refined From:** plan/agents/offboarding-client-offboarding.md
