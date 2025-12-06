# Knowledge Transfer Agent - Production Specification

**Status:** Ready to Build
**Version:** 1.0.0
**Created:** 2025-12-05
**Category:** Offboarding & Nurture
**Phase:** Phase 5 - Retention & Growth
**Refined From:** plan/agents/offboarding-knowledge-transfer.md

---

## 1. Overview

### Purpose
Autonomously create and deliver comprehensive knowledge transfer packages for clients during project offboarding, ensuring smooth transition from agency delivery to client ownership with ongoing support and training.

### Agent Classification
- **Type:** Knowledge Management Agent
- **Execution Mode:** Event-driven (triggered by Client Offboarding Agent)
- **Human-in-the-Loop:** Required for training calls, complex documentation review
- **Priority:** High (critical for client retention and successful offboarding)

### Dependencies
- **Upstream Agents:**
  - Client Offboarding Agent (triggers knowledge transfer process)
  - Project Management Agent (provides project context, deliverables list)
- **Downstream Agents:**
  - Referral Request Agent (triggered after successful knowledge transfer)
  - Long-term Nurture Agent (continues relationship after support window)
- **External Services:**
  - Loom API (video recording and management)
  - Google Drive/Docs API (documentation creation and sharing)
  - Cal.com API (training call scheduling)
  - Email service (Gmail/SendGrid for materials delivery)

---

## 2. System Prompt

```
You are the Knowledge Transfer Agent for Smarter Team, an AI agency automation system.

Your mission is to ensure every client feels confident and fully equipped to succeed with their deliverables after project completion. You create comprehensive, easy-to-understand training materials and provide hands-on support.

**Core Responsibilities:**
- Create comprehensive documentation packages tailored to each deliverable
- Record clear, concise video walkthroughs demonstrating key features
- Schedule and prepare training calls for complex deliverables
- Deliver materials in a well-organized, professional manner
- Provide responsive support during the designated support window
- Track client understanding and satisfaction with the transfer process

**Knowledge Transfer Components You Create:**

1. **Quick Start Guide** (1-page summary)
   - 3-5 steps to get started immediately
   - Key features with brief descriptions
   - Essential links and contact info

2. **Detailed User Manual**
   - Comprehensive feature documentation
   - Step-by-step instructions for all tasks
   - Screenshots and visual aids
   - Troubleshooting section

3. **Video Walkthrough Package**
   - Overview/introduction video (2-3 minutes)
   - Core features demonstration (5-10 minutes)
   - Advanced features walkthrough (if applicable)
   - Common tasks tutorials (3-5 minutes each)

4. **FAQ Document**
   - Anticipated questions with detailed answers
   - "How do I..." scenarios
   - Best practices and tips

**Your Process:**
1. **Analyze Deliverable:** Review project specifications, code, documentation, and complexity
2. **Determine Transfer Level:** Basic (documentation only) or Premium (documentation + videos + training)
3. **Create Documentation:** Generate clear, professional documentation using templates
4. **Record Videos:** Create Loom videos demonstrating key functionality
5. **Package Materials:** Organize everything in a shared folder with clear structure
6. **Send to Client:** Professional email with all links and next steps
7. **Schedule Training:** Set up call if needed (Cal.com integration)
8. **Track Understanding:** Confirm client comprehension and satisfaction

**Support Windows:**
- Standard: 14 days post-delivery
- Extended: 30 days (complex projects)
- Premium: 90 days (enterprise clients)

**Guidelines:**
- ALWAYS use client's name and reference their specific deliverable
- Create materials that someone with basic technical skills can understand
- Include real examples from their actual deliverable, not generic examples
- Format times in client's timezone
- Track all metrics: material creation time, client engagement, satisfaction scores

**Tools Available:**
- create_documentation: Generate documentation from deliverable analysis
- record_video: Initiate Loom recording with guided script
- organize_materials: Structure and package all knowledge transfer assets
- send_materials: Email comprehensive package to client
- schedule_training: Book training call via Cal.com
- track_understanding: Monitor client engagement and comprehension
- extend_support: Manage support window extensions

**Error Handling:**
- If Loom recording fails → Provide detailed screenshots + text walkthrough
- If Google Docs access fails → Create PDF and email directly
- If client doesn't respond → Send follow-up after 3 days, escalate if needed
- If training call missed → Automatically reschedule, send recording

Always structure responses as JSON with:
{
  "status": "success|pending|error|escalated",
  "knowledge_transfer_id": "uuid",
  "components_created": ["quick_start", "user_manual", "videos"],
  "delivery_method": "email|portal|handoff",
  "support_window": {"days": 14, "end_date": "2025-01-22"},
  "client_engagement": {"opened": true, "videos_watched": 3, "training_scheduled": true},
  "next_steps": ["monitor_engagement", "schedule_followup"],
  "metrics": {"creation_time_hours": 4, "client_satisfaction": null}
}
```

---

## 3. Agent Architecture

### Base Class
Extends `BaseAgent` from `src/agents/base_agent.py`

### File Structure
```
src/agents/offboarding/knowledge_transfer/
├── __init__.py           # Export KnowledgeTransferAgent
├── agent.py              # Main agent class
├── tools.py              # Tool functions for knowledge transfer
├── prompts.py            # System prompt constants
├── schemas.py            # Pydantic models for requests/responses
├── templates/            # Document templates
│   ├── quick_start.md
│   ├── user_manual.md
│   └── faq.md
└── exceptions.py         # Custom exceptions
```

---

## 4. Tools

### 4.1 `create_documentation`

**Description:** Generate comprehensive documentation package based on deliverable analysis.

**Parameters:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DeliverableType(str, Enum):
    WEBSITE = "website"
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    API = "api"
    AUTOMATION = "automation"
    DASHBOARD = "dashboard"
    DOCUMENTATION = "documentation"
    OTHER = "other"

class CreateDocumentationParams(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    client_id: str = Field(..., description="Client identifier")
    deliverable_id: str = Field(..., description="Specific deliverable ID")
    deliverable_type: DeliverableType = Field(..., description="Type of deliverable")
    complexity_level: str = Field(..., description="simple|moderate|complex")
    access_info: dict = Field(..., description="URLs, login credentials, API keys")
    special_features: List[str] = Field(default=[], description="Unique features to highlight")
    target_audience: str = Field(..., description="technical_level of end users")

class DocumentationSection(BaseModel):
    title: str
    content: str
    screenshots: List[str] = Field(default=[])
    videos: List[str] = Field(default=[])

class CreateDocumentationResponse(BaseModel):
    documentation_id: str
    quick_start_url: str
    user_manual_url: str
    faq_url: str
    sections: List[DocumentationSection]
    creation_time_minutes: int
```

**Implementation Details:**
- Use Claude to analyze project files and documentation
- Generate screenshots using browser automation if needed
- Create Google Docs with proper formatting and branding
- Apply templates based on deliverable type
- Include actual examples from the client's deliverable

**Error Handling:**
- `DocumentationGenerationError`: AI generation fails
- `AccessDeniedError`: Cannot access deliverable for analysis
- `TemplateError`: Template application fails
- `GoogleDocsError`: API quota or authentication issues

### 4.2 `record_video`

**Description:** Create Loom video walkthroughs with AI-generated scripts.

**Parameters:**
```python
class VideoType(str, Enum):
    OVERVIEW = "overview"          # 2-3 min introduction
    FEATURES = "features"          # 5-10 min core demo
    TASKS = "tasks"               # 3-5 min specific tasks
    ADVANCED = "advanced"          # Optional advanced features

class RecordVideoParams(BaseModel):
    documentation_id: str = Field(..., description="Related documentation")
    video_type: VideoType = Field(..., description="Type of video to record")
    script_points: List[str] = Field(..., description="Key points to cover")
    deliverable_url: str = Field(..., description="URL to demonstrate")
    include_audio: bool = Field(default=True, description="Include voice narration")

class LoomVideo(BaseModel):
    video_id: str
    url: str
    thumbnail_url: str
    duration_seconds: int
    views: int = 0

class RecordVideoResponse(BaseModel):
    video: LoomVideo
    transcript: Optional[str] = None
    key_timestamps: List[dict] = Field(default=[])
    recording_status: str  # "recording|completed|failed"
```

**Implementation Details:**
- Generate video script using Claude based on documentation
- Launch Loom recorder with prepared script prompt
- Use AI to identify optimal moments for emphasis
- Generate timestamps for key features
- Create transcript automatically if enabled

**Error Handling:**
- `LoomAPIError`: Recording or upload fails
- `ScriptGenerationError`: AI cannot create coherent script
- `AccessDeniedError`: Cannot access deliverable for recording
- `TimeoutError`: Recording exceeds maximum duration

### 4.3 `organize_materials`

**Description:** Structure and package all knowledge transfer materials in client folder.

**Parameters:**
```python
class MaterialType(str, Enum):
    DOCUMENTATION = "documentation"
    VIDEO = "video"
    CHEAT_SHEET = "cheat_sheet"
    TROUBLESHOOTING = "troubleshooting"
    CONTACT_INFO = "contact_info"

class OrganizeMaterialsParams(BaseModel):
    knowledge_transfer_id: str = Field(..., description="Transfer session ID")
    client_id: str = Field(..., description="Client identifier")
    materials: dict = Field(..., description="Material URLs and metadata")
    folder_structure: dict = Field(default_factory=lambda: {
        "Quick Start": ["quick_start.pdf", "overview_video.mp4"],
        "Documentation": ["user_manual.pdf", "api_reference.pdf"],
        "Videos": ["feature_walkthrough.mp4", "tasks_demo.mp4"],
        "Support": ["faq.pdf", "contact_info.txt", "troubleshooting.pdf"]
    })

class OrganizedFolder(BaseModel):
    folder_id: str
    folder_url: str
    structure: dict
    total_size_mb: float
    material_count: int

class OrganizeMaterialsResponse(BaseModel):
    folder: OrganizedFolder
    access_permissions: str  # "client_only|team_shared|public"
    expiry_date: Optional[datetime] = None
    download_stats: dict = Field(default_factory=dict)
```

**Implementation Details:**
- Create structured Google Drive folder with client branding
- Set appropriate sharing permissions (client + team)
- Generate table of contents for easy navigation
- Create archive package for offline access
- Track organization metrics

**Error Handling:**
- `GoogleDriveError`: Folder creation or sharing fails
- `PermissionError`: Cannot set proper access rights
- `StorageError`: Exceeds storage limits
- `OrganizationError**: Invalid structure or missing materials

### 4.4 `send_materials`

**Description:** Deliver knowledge transfer package to client via professional email.

**Parameters:**
```python
class SendMaterialsParams(BaseModel):
    knowledge_transfer_id: str = Field(..., description="Transfer session ID")
    client_email: str = Field(..., description="Client email address")
    client_name: str = Field(..., description="Client first name")
    deliverable_name: str = Field(..., description="Name of deliverable")
    materials: dict = Field(..., description="Material URLs and descriptions")
    support_window_days: int = Field(default=14, description="Support duration")
    include_training_call: bool = Field(default=False, description="Offer training call")
    personalization: dict = Field(default={}, description="Custom message elements")

class EmailTracking(BaseModel):
    sent_at: datetime
    message_id: str
    opened_at: Optional[datetime] = None
    clicked_links: List[str] = Field(default=[])
    replied_at: Optional[datetime] = None

class SendMaterialsResponse(BaseModel):
    email_status: str  # "sent|failed|queued"
    tracking: EmailTracking
    materials_accessed: dict = Field(default_factory=dict)
    followup_scheduled: bool = False
```

**Implementation Details:**
- Use dynamic email template with client personalization
- Track email opens, link clicks, and engagement
- Schedule automatic follow-up if no engagement in 3 days
- Provide clear next steps and support contact info
- Include material access analytics

**Error Handling:**
- `EmailDeliveryError`: SMTP or API delivery fails
- `TemplateError`: Email template rendering fails
- `RateLimitError`: Exceeds sending rate limits
- `PersonalizationError`: Missing required personalization data

### 4.5 `schedule_training`

**Description:** Book optional training call via Cal.com integration.

**Parameters:**
```python
class TrainingType(str, Enum):
    BASIC = "basic"            # 30 min overview
    COMPREHENSIVE = "comprehensive"  # 60 min detailed
    HANDS_ON = "hands_on"      # 90 min with client participation
    Q_AND_A = "q_and_a"        # 30 min focused Q&A

class ScheduleTrainingParams(BaseModel):
    knowledge_transfer_id: str = Field(..., description="Transfer session ID")
    client_email: str = Field(..., description="Client email")
    client_timezone: str = Field(..., description="Client IANA timezone")
    training_type: TrainingType = Field(..., description="Type of training session")
    availability_window_days: int = Field(default=7, description="Days to offer")
    preparation_needed: List[str] = Field(default=[], description="Items client should prepare")

class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    available: bool

class TrainingSession(BaseModel):
    booking_id: str
    meeting_url: str
    calendar_event_id: str
    preparation_sent: bool = False
    reminder_scheduled: bool = False

class ScheduleTrainingResponse(BaseModel):
    available_slots: List[TimeSlot]
    booked_session: Optional[TrainingSession] = None
    booking_status: str  # "offered|booked|confirmed|failed"
    preparation_materials: List[str] = Field(default=[])
```

**Implementation Details:**
- Sync with Cal.com to get available slots
- Convert times to client timezone automatically
- Send preparation materials 24 hours before call
- Set up calendar invites with all necessary links
- Record session for future reference

**Error Handling:**
- `CalComAPIError`: Scheduling API fails
- `TimezoneError`: Invalid or unsupported timezone
- `NoAvailabilityError`: No slots in requested window
- `CalendarSyncError`: Cannot add to client calendar

### 4.6 `track_understanding`

**Description:** Monitor client engagement and comprehension of materials.

**Parameters:**
```python
class EngagementMetric(BaseModel):
    metric_type: str  # "open_rate|click_rate|video_watch_time|document_reads"
    value: float
    timestamp: datetime
    material_id: Optional[str] = None

class TrackUnderstandingParams(BaseModel):
    knowledge_transfer_id: str = Field(..., description="Transfer session ID")
    client_id: str = Field(..., description="Client identifier")
    time_window_days: int = Field(default=7, description="Tracking period")
    metrics_to_track: List[str] = Field(default=[
        "email_opened", "materials_accessed", "videos_watched",
        "documents_read", "questions_asked"
    ])

class UnderstandingScore(BaseModel):
    overall_score: float  # 0-100
    engagement_level: str  # "low|medium|high"
    risk_factors: List[str] = Field(default=[])
    recommendations: List[str] = Field(default=[])

class TrackUnderstandingResponse(BaseModel):
    metrics: List[EngagementMetric]
    understanding_score: UnderstandingScore
    followup_needed: bool = False
    support_extension_recommended: bool = False
```

**Implementation Details:**
- Track material access patterns and timing
- Calculate engagement score based on multiple metrics
- Identify risk factors (no access, low engagement, many questions)
- Generate recommendations for additional support
- Schedule proactive check-ins if needed

**Error Handling:**
- `AnalyticsError`: Cannot track engagement metrics
- `InsufficientDataError`: Not enough data to assess understanding
- `ScoringError**: Cannot calculate understanding score

---

## 5. Error Handling Matrix

| Error Type | Detection | Response | Retry | Escalation |
|------------|-----------|----------|-------|------------|
| Loom API failure | HTTP 5xx/4xx | Use screenshots + text | Yes, 3x | To project manager |
| Google Docs error | Access denied | Create PDF + email | Yes, 2x | To human |
| Cal.com unavailable | API timeout | Manual scheduling | No | To scheduler |
| Email delivery fails | SMTP bounce | Queue for retry | Yes, 5x | To delivery team |
| Client no response | 3 days inactivity | Send follow-up | Yes | Account manager |
| Video recording fails | Loom error | Text walkthrough | No | Create anyway |
| Documentation generation | Claude error | Use existing docs | Yes, 2x | Use template |

### Recovery Strategies
1. **Graceful degradation:** Always provide basic text documentation if advanced features fail
2. **Fallback content:** Use existing project artifacts if AI generation fails
3. **Manual override:** Human can step in for complex situations
4. **Progressive delivery:** Send materials as they're ready, not all at once

---

## 6. Database Schema

### knowledge_transfers Table
```sql
CREATE TABLE knowledge_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    client_id UUID NOT NULL REFERENCES clients(id),
    deliverable_id UUID NOT NULL REFERENCES deliverables(id),
    status VARCHAR(20) NOT NULL DEFAULT 'initiated',
    transfer_level VARCHAR(20) NOT NULL DEFAULT 'standard',
    components_created JSONB DEFAULT '{}',
    delivery_email_sent_at TIMESTAMP WITH TIME ZONE,
    materials_folder_url TEXT,
    support_window_days INTEGER DEFAULT 14,
    support_window_end TIMESTAMP WITH TIME ZONE,
    client_engagement_score FLOAT,
    understanding_assessment JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### training_materials Table
```sql
CREATE TABLE training_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_transfer_id UUID NOT NULL REFERENCES knowledge_transfers(id),
    material_type VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_url TEXT,
    video_url TEXT,
    loom_video_id TEXT,
    duration_seconds INTEGER,
    file_size_bytes INTEGER,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### training_sessions Table
```sql
CREATE TABLE training_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_transfer_id UUID NOT NULL REFERENCES knowledge_transfers(id),
    calcom_booking_id VARCHAR(100),
    scheduled_start TIMESTAMP WITH TIME ZONE,
    scheduled_end TIMESTAMP WITH TIME ZONE,
    actual_start TIMESTAMP WITH TIME ZONE,
    actual_end TIMESTAMP WITH TIME ZONE,
    meeting_url TEXT,
    recording_url TEXT,
    status VARCHAR(20) DEFAULT 'scheduled',
    preparation_sent BOOLEAN DEFAULT FALSE,
    reminder_sent BOOLEAN DEFAULT FALSE,
    client_attended BOOLEAN,
    feedback_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 7. Multi-Agent Integration

### Trigger from Client Offboarding Agent
```json
{
  "trigger": "knowledge_transfer_initiated",
  "payload": {
    "project_id": "uuid",
    "client_id": "uuid",
    "deliverable_id": "uuid",
    "offboarding_date": "2025-01-15",
    "complexity_level": "moderate",
    "special_requirements": ["video_tutorials", "training_call"]
  }
}
```

### Handoff to Referral Request Agent
```json
{
  "handoff": "referral_request",
  "payload": {
    "client_id": "uuid",
    "knowledge_transfer_id": "uuid",
    "client_satisfaction": 4.5,
    "support_window_end": "2025-02-15",
    "referral_eligibility": true,
    "optimal_contact_time": "2025-02-20"
  }
}
```

### Handoff to Long-term Nurture Agent
```json
{
  "handoff": "long_term_nurture",
  "payload": {
    "client_id": "uuid",
    "last_engagement": "2025-01-20",
    "support_window_closed": true,
    "nurture_track": "quarterly_checkins",
    "next_touchpoint": "2025-04-20"
  }
}
```

---

## 8. Testing Strategy

### Unit Tests
```python
def test_create_documentation_success():
    """Verify documentation generation with valid inputs"""

def test_create_documentation_handles_access_denied():
    """Verify graceful handling when deliverable access fails"""

def test_record_video_script_generation():
    """Verify AI generates coherent video scripts"""

def test_organize_materials_folder_structure():
    """Verify proper Google Drive folder creation"""

def test_send_materials_personalization():
    """Verify email template personalization works"""

def test_schedule_training_timezone_conversion():
    """Verify correct timezone handling for scheduling"""

def test_track_understanding_score_calculation():
    """Verify engagement scoring algorithm"""
```

### Integration Tests
```python
def test_end_to_end_knowledge_transfer():
    """Complete workflow from trigger to delivery"""

def test_multi_agent_handoffs():
    """Verify proper handoff to downstream agents"""

def test_external_api_failures():
    """Test behavior when Loom, Google Docs, or Cal.com fail"""

def test_client_engagement_tracking():
    """Verify analytics collection and processing"""
```

### Mocking Strategy
```python
@pytest.fixture
def mock_loom_client():
    with patch('src.integrations.loom.LoomClient') as mock:
        mock.return_value.start_recording.return_value = {"video_id": "test_123"}
        yield mock

@pytest.fixture
def mock_google_docs():
    with patch('src.integrations.google_docs.GoogleDocsClient') as mock:
        mock.return_value.create_document.return_value = {"doc_id": "doc_123", "url": "https://docs.google.com/..."}
        yield mock

@pytest.fixture
def mock_cal_com():
    with patch('src.integrations.cal_com.CalComClient') as mock:
        mock.return_value.get_available_slots.return_value = [
            {"start": "2025-01-20T14:00:00Z", "end": "2025-01-20T15:00:00Z"}
        ]
        yield mock
```

---

## 9. Performance & Observability

### Expected Performance Metrics
- **Documentation Generation:** < 5 minutes for simple deliverables
- **Video Recording:** 2-15 minutes depending on complexity
- **Material Organization:** < 2 minutes
- **Email Delivery:** < 30 seconds
- **Training Scheduling:** < 1 minute

### Logging Requirements
```python
# Track these events with structured logging
{
  "event": "knowledge_transfer_initiated",
  "knowledge_transfer_id": "uuid",
  "project_id": "uuid",
  "client_id": "uuid",
  "complexity_level": "moderate"
}

{
  "event": "material_created",
  "type": "documentation|video|training_session",
  "duration_seconds": 245,
  "file_size_mb": 12.5
}

{
  "event": "client_engagement",
  "action": "email_opened|material_accessed|video_watched",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Metrics to Track
- Knowledge transfer completion rate
- Average time to create materials
- Client engagement scores
- Support window utilization
- Training session attendance
- Material access patterns
- Client satisfaction ratings

---

## 10. Security Considerations

### Access Control
- Client materials shared only with designated client + internal team
- Training links expire after 90 days
- API keys stored securely via environment variables
- All client data encrypted at rest and in transit

### Data Privacy
- No client credentials stored in plain text
- Video recordings stored with client consent
- Analytics data anonymized after 1 year
- Compliance with GDPR and CCPA

---

## 11. Acceptance Criteria

- [ ] Successfully creates all documentation types (quick start, manual, FAQ)
- [ ] Generates professional video walkthroughs with clear narration
- [ ] Organizes materials in structured, accessible format
- [ ] Sends personalized delivery emails with tracking
- [ ] Schedules training calls with timezone accuracy
- [ ] Tracks and reports client engagement metrics
- [ ] Handles all external API failures gracefully
- [ ] Maintains audit trail of all knowledge transfer activities
- [ ] Integrates properly with upstream and downstream agents
- [ ] Achieves >90% client satisfaction with transfer process
- [ ] Completes standard transfers within 4 business hours
- [ ] Maintains >95% uptime for material access

---

## 12. Configuration

### Environment Variables
```bash
# Required
KNOWLEDGE_TRANSFER_DEFAULT_SUPPORT_DAYS=14
KNOWLEDGE_TRANSFER_FOLDER_ID=your_google_drive_folder_id
KNOWLEDGE_TRANSFER_TEMPLATE_ID=your_docs_template_id

# Optional
LOOM_WEBHOOK_SECRET=...
GOOGLE_DOCS_CREDENTIALS_JSON=path/to/credentials.json
CAL_COM_API_KEY=cal_...
CAL_COM_EVENT_TYPE_ID=12345
KNOWLEDGE_TRANSFER_AUTO_SCHEDULE_TRAINING=true
```

### Agent Configuration
```python
class KnowledgeTransferConfig:
    max_documentation_retries: int = 3
    max_video_duration_minutes: int = 20
    material_retention_days: int = 365
    engagement_check_interval_hours: int = 24
    followup_delay_days: int = 3
    support_reminder_days: int = [3, 7, 14]
```
