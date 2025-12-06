# Testimonial Request Agent - Production Specification

**Version:** 1.0
**Status:** Ready for Implementation
**Agent Category:** Client Success & Retention
**Priority:** Phase 5 - Retention & Growth

---

## Overview

The Testimonial Request Agent automatically identifies satisfied clients and requests testimonials at optimal times. It handles the complete testimonial collection workflow including qualification, personalized requests, multi-format collection (written, video, case studies), usage rights management, and thank-you processes with incentives.

**Key Capabilities:**
- Automated client qualification based on project success and satisfaction scores
- Multi-format testimonial collection (written, video, case studies)
- Personalized request templates with dynamic content
- Usage rights tracking and management
- Incentive management and automated thank-you responses
- Integration with Satisfaction Survey and Project Management agents
- Human-in-the-loop review before publishing

---

## Database Schema

### Table: `testimonial_requests`
Tracks all testimonial requests sent and their status.

```sql
CREATE TABLE testimonial_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Request details
    request_type VARCHAR(20) NOT NULL CHECK (request_type IN ('written', 'video', 'case_study')),
    template_used VARCHAR(50) NOT NULL,
    personalization_data JSONB NOT NULL DEFAULT '{}',

    -- Request content
    subject_line VARCHAR(255) NOT NULL,
    email_body TEXT NOT NULL,
    form_link TEXT,
    video_link TEXT,

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'responded', 'declined', 'completed')),
    sent_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,

    -- Response details
    response_type VARCHAR(20), -- 'written', 'video', 'case_study', 'declined'
    testimonial_content TEXT,
    video_url TEXT,
    case_study_approved BOOLEAN DEFAULT FALSE,

    -- Human review
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected', 'edited')),
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_testimonial_requests_client ON testimonial_requests(client_id);
CREATE INDEX idx_testimonial_requests_project ON testimonial_requests(project_id);
CREATE INDEX idx_testimonial_requests_status ON testimonial_requests(status);
CREATE INDEX idx_testimonial_requests_review ON testimonial_requests(review_status);
CREATE INDEX idx_testimonial_requests_sent ON testimonial_requests(sent_at DESC);
```

### Table: `testimonials`
Stores approved testimonials and their metadata.

```sql
CREATE TABLE testimonials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    request_id UUID NOT NULL REFERENCES testimonial_requests(id) ON DELETE CASCADE,

    -- Testimonial details
    testimonial_type VARCHAR(20) NOT NULL CHECK (testimonial_type IN ('written', 'video', 'case_study')),
    content TEXT NOT NULL,
    video_url TEXT,
    video_duration_seconds INTEGER,

    -- Client info for display
    client_name VARCHAR(255) NOT NULL,
    client_title VARCHAR(255),
    client_company VARCHAR(255),
    client_photo_url TEXT,

    -- Usage rights
    usage_rights JSONB NOT NULL DEFAULT '{}', -- {'website': true, 'social_media': false, 'case_study': true}
    name_display BOOLEAN DEFAULT TRUE,
    company_display BOOLEAN DEFAULT TRUE,
    specific_metrics_approved TEXT[], -- Array of approved metrics/numbers

    -- Categorization
    tags TEXT[] DEFAULT '{}',
    featured BOOLEAN DEFAULT FALSE,
    testimonial_strength INTEGER CHECK (testimonial_strength >= 1 AND testimonial_strength <= 5),

    -- Publishing
    published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP WITH TIME ZONE,
    published_locations TEXT[] DEFAULT '{}', -- Array of URLs where published

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_testimonials_client ON testimonials(client_id);
CREATE INDEX idx_testimonials_project ON testimonials(project_id);
CREATE INDEX idx_testimonials_type ON testimonials(testimonial_type);
CREATE INDEX idx_testimonials_published ON testimonials(published);
CREATE INDEX idx_testimonials_featured ON testimonials(featured);
CREATE INDEX idx_testimonials_strength ON testimonials(testimonial_strength);
```

### Table: `testimonial_incentives`
Tracks incentives offered and claimed for testimonials.

```sql
CREATE TABLE testimonial_incentives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    testimonial_request_id UUID NOT NULL REFERENCES testimonial_requests(id) ON DELETE CASCADE,

    -- Incentive details
    incentive_type VARCHAR(50) NOT NULL, -- 'discount', 'credit', 'gift_card', 'free_month'
    incentive_value DECIMAL(10,2),
    incentive_description TEXT NOT NULL,
    incentive_code VARCHAR(100) UNIQUE,

    -- Status
    status VARCHAR(20) DEFAULT 'offered' CHECK (status IN ('offered', 'claimed', 'expired', 'voided')),
    offered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    claimed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Usage tracking
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP WITH TIME ZONE,
    used_on_project_id UUID REFERENCES projects(id),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_testimonial_incentives_request ON testimonial_incentives(testimonial_request_id);
CREATE INDEX idx_testimonial_incentives_status ON testimonial_incentives(status);
CREATE INDEX idx_testimonial_incentives_code ON testimonial_incentives(incentive_code);
```

---

## Agent Implementation

### Class: `TestimonialRequestAgent`

```python
from src.agents.base_agent import BaseAgent
from src.integrations.email import EmailIntegration
from src.integrations.survey import SurveyIntegration
from src.models.database import get_db_session
from typing import Any, Dict, List, Optional
import asyncio
import json

class TestimonialRequestAgent(BaseAgent):
    """Agent for collecting client testimonials through automated requests."""

    def __init__(self):
        super().__init__(
            name="testimonial_request",
            description="Collects and manages client testimonials"
        )
        self.email_integration = EmailIntegration()
        self.survey_integration = SurveyIntegration()

    @property
    def system_prompt(self) -> str:
        return """You are a Testimonial Request Agent responsible for collecting client testimonials.

        Your responsibilities:
        1. Qualify clients based on project success and satisfaction
        2. Send personalized testimonial requests at optimal times
        3. Collect and format testimonials in multiple formats
        4. Manage usage rights and approval workflows
        5. Handle incentive distribution and thank-you processes

        Always be respectful of client time and preferences. Never pressure clients for testimonials.
        Ensure all usage rights are clearly obtained and documented before publishing."""

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process testimonial request tasks."""
        task_type = task.get("type")

        try:
            if task_type == "qualify_clients":
                return await self._qualify_clients(task.get("criteria", {}))
            elif task_type == "send_request":
                return await self._send_testimonial_request(task)
            elif task_type == "collect_response":
                return await self._collect_testimonial_response(task)
            elif task_type == "review_testimonial":
                return await self._review_testimonial(task)
            elif task_type == "publish_testimonial":
                return await self._publish_testimonial(task)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

        except Exception as e:
            self.logger.error(f"Task processing failed: {e}", extra={"task": task})
            raise

    async def _qualify_clients(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Identify clients eligible for testimonial requests."""
        async with get_db_session() as db:
            # Query clients based on qualification criteria
            query = """
            SELECT DISTINCT c.id, c.first_name, c.last_name, c.email,
                   p.id as project_id, p.name as project_name,
                   ps.satisfaction_score, p.completed_at
            FROM clients c
            JOIN projects p ON c.id = p.client_id
            LEFT JOIN project_satisfaction ps ON p.id = ps.project_id
            WHERE p.status = 'completed'
              AND p.completed_at >= NOW() - INTERVAL '30 days'
              AND (ps.satisfaction_score >= 8 OR ps.satisfaction_score IS NULL)
              AND NOT EXISTS (
                  SELECT 1 FROM testimonial_requests tr
                  WHERE tr.client_id = c.id
                    AND tr.created_at >= NOW() - INTERVAL '90 days'
              )
            ORDER BY p.completed_at DESC, ps.satisfaction_score DESC NULLS LAST
            """

            result = await db.execute(query)
            qualified_clients = [dict(row) for row in result.fetchall()]

            # Rate each client on testimonial likelihood
            for client in qualified_clients:
                client['testimonial_score'] = self._calculate_testimonial_score(client)
                client['recommended_type'] = self._recommend_testimonial_type(client)

            # Filter by minimum score
            min_score = criteria.get("min_score", 7)
            high_quality_clients = [
                c for c in qualified_clients
                if c['testimonial_score'] >= min_score
            ]

            self.log_action(
                "clients.qualified",
                {
                    "total_clients": len(qualified_clients),
                    "high_quality": len(high_quality_clients),
                    "min_score": min_score
                }
            )

            return {
                "status": "completed",
                "qualified_clients": high_quality_clients,
                "total_reviewed": len(qualified_clients)
            }

    async def _send_testimonial_request(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Send personalized testimonial request to client."""
        client_id = task["client_id"]
        project_id = task["project_id"]
        request_type = task.get("request_type", "written")
        personalization = task.get("personalization", {})

        async with get_db_session() as db:
            # Get client and project details
            client = await self._get_client_details(db, client_id)
            project = await self._get_project_details(db, project_id)

            # Generate personalized content
            email_content = await self._generate_request_email(
                client, project, request_type, personalization
            )

            # Create testimonial request record
            request_data = {
                "client_id": client_id,
                "project_id": project_id,
                "request_type": request_type,
                "template_used": email_content["template_name"],
                "personalization_data": personalization,
                "subject_line": email_content["subject"],
                "email_body": email_content["body"],
                "form_link": email_content["form_link"],
                "video_link": email_content.get("video_link"),
                "status": "sent"
            }

            result = await db.execute(
                """INSERT INTO testimonial_requests
                   (client_id, project_id, request_type, template_used,
                    personalization_data, subject_line, email_body, form_link, video_link, status, sent_at)
                   VALUES (:client_id, :project_id, :request_type, :template_used,
                           :personalization_data, :subject_line, :email_body, :form_link, :video_link, :status, NOW())
                   RETURNING id""",
                request_data
            )
            request_id = result.scalar_one()

            # Send email
            email_sent = await self.email_integration.send_email(
                to_email=client["email"],
                subject=email_content["subject"],
                body=email_content["body"],
                template_name="testimonial_request",
                template_data={**client, **project, **email_content}
            )

            # Create incentive if applicable
            if task.get("offer_incentive", False):
                await self._create_incentive(db, request_id, task.get("incentive_details"))

            # Schedule follow-up if no response in 7 days
            if task.get("schedule_followup", True):
                await self._schedule_follow_up(request_id, days=7)

            self.log_action(
                "testimonial.request_sent",
                {
                    "request_id": request_id,
                    "client_id": client_id,
                    "project_id": project_id,
                    "request_type": request_type,
                    "email_sent": email_sent
                }
            )

            return {
                "status": "completed",
                "request_id": request_id,
                "email_sent": email_sent,
                "next_follow_up": task.get("schedule_followup", True)
            }

    async def _collect_testimonial_response(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming testimonial response."""
        request_id = task["request_id"]
        response_data = task["response_data"]

        async with get_db_session() as db:
            # Update request record
            update_data = {
                "status": "responded",
                "responded_at": "NOW()",
                "response_type": response_data.get("type"),
                "testimonial_content": response_data.get("content"),
                "video_url": response_data.get("video_url"),
                "case_study_approved": response_data.get("case_study_approved", False)
            }

            await db.execute(
                """UPDATE testimonial_requests
                   SET status = :status, responded_at = NOW(),
                       response_type = :response_type, testimonial_content = :content,
                       video_url = :video_url, case_study_approved = :case_study_approved
                   WHERE id = :request_id""",
                {**update_data, "request_id": request_id, "content": response_data.get("content")}
            )

            # Get request details for testimonial creation
            request = await self._get_testimonial_request(db, request_id)

            # Create testimonial record (in review status)
            if response_data.get("content"):
                testimonial_data = {
                    "client_id": request["client_id"],
                    "project_id": request["project_id"],
                    "request_id": request_id,
                    "testimonial_type": response_data.get("type", "written"),
                    "content": response_data.get("content"),
                    "video_url": response_data.get("video_url"),
                    "client_name": f"{request['first_name']} {request['last_name']}",
                    "review_status": "pending"
                }

                result = await db.execute(
                    """INSERT INTO testimonials
                       (client_id, project_id, request_id, testimonial_type, content,
                        video_url, client_name, review_status)
                       VALUES (:client_id, :project_id, :request_id, :testimonial_type, :content,
                               :video_url, :client_name, :review_status)
                       RETURNING id""",
                    testimonial_data
                )
                testimonial_id = result.scalar_one()

                # Trigger review workflow
                await self.handoff_to(
                    target_agent="human_review",
                    payload={
                        "action": "review_testimonial",
                        "testimonial_id": testimonial_id,
                        "priority": "normal"
                    }
                )

            # Send thank you email
            await self._send_thank_you_email(request, response_data)

            # Process incentive if offered
            await self._process_incentive(request_id)

            self.log_action(
                "testimonial.response_collected",
                {
                    "request_id": request_id,
                    "testimonial_id": testimonial_id if response_data.get("content") else None,
                    "response_type": response_data.get("type")
                }
            )

            return {
                "status": "completed",
                "request_id": request_id,
                "testimonial_id": testimonial_id if response_data.get("content") else None,
                "review_required": True
            }

    async def _review_testimonial(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Review and approve/reject testimonial."""
        testimonial_id = task["testimonial_id"]
        review_data = task["review_data"]

        async with get_db_session() as db:
            # Update testimonial with review results
            update_fields = [
                "review_status = :status",
                "reviewed_by = :reviewer_id",
                "reviewed_at = NOW()",
                "review_notes = :notes"
            ]

            if review_data["status"] == "approved":
                update_fields.extend([
                    "client_name = :client_name",
                    "client_title = :client_title",
                    "client_company = :client_company",
                    "client_photo_url = :client_photo",
                    "usage_rights = :usage_rights",
                    "name_display = :name_display",
                    "company_display = :company_display",
                    "specific_metrics_approved = :metrics",
                    "tags = :tags",
                    "testimonial_strength = :strength"
                ])

            query = f"UPDATE testimonials SET {', '.join(update_fields)} WHERE id = :testimonial_id"

            await db.execute(query, {
                "testimonial_id": testimonial_id,
                "status": review_data["status"],
                "reviewer_id": review_data["reviewer_id"],
                "notes": review_data.get("notes"),
                **{k: v for k, v in review_data.items() if k in [
                    "client_name", "client_title", "client_company", "client_photo",
                    "usage_rights", "name_display", "company_display", "metrics",
                    "tags", "strength"
                ]}
            })

            # If approved and ready to publish
            if review_data["status"] == "approved" and review_data.get("publish_immediately"):
                await self._publish_testimonial({"testimonial_id": testimonial_id})

            self.log_action(
                "testimonial.reviewed",
                {
                    "testimonial_id": testimonial_id,
                    "status": review_data["status"],
                    "reviewer_id": review_data["reviewer_id"]
                }
            )

            return {
                "status": "completed",
                "testimonial_id": testimonial_id,
                "review_status": review_data["status"]
            }

    async def _publish_testimonial(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Publish approved testimonial to various locations."""
        testimonial_id = task["testimonial_id"]
        locations = task.get("locations", ["website"])

        async with get_db_session() as db:
            # Get testimonial details
            testimonial = await self._get_testimonial_details(db, testimonial_id)

            if not testimonial or testimonial["review_status"] != "approved":
                raise ValueError("Testimonial not approved for publishing")

            published_urls = []

            # Publish to website testimonial page
            if "website" in locations:
                website_url = await self._publish_to_website(testimonial)
                if website_url:
                    published_urls.append(website_url)

            # Publish to social media
            if "social_media" in locations and testimonial["usage_rights"].get("social_media"):
                social_urls = await self._publish_to_social_media(testimonial)
                published_urls.extend(social_urls)

            # Create/update case study
            if "case_study" in locations and testimonial["testimonial_type"] == "case_study":
                case_study_url = await self._create_case_study(testimonial)
                if case_study_url:
                    published_urls.append(case_study_url)

            # Update testimonial record
            await db.execute(
                """UPDATE testimonials
                   SET published = TRUE, published_at = NOW(),
                       published_locations = :locations
                   WHERE id = :testimonial_id""",
                {
                    "testimonial_id": testimonial_id,
                    "locations": published_urls
                }
            )

            # Update request status
            await db.execute(
                """UPDATE testimonial_requests
                   SET status = 'completed'
                   WHERE id = :request_id""",
                {"request_id": testimonial["request_id"]}
            )

            self.log_action(
                "testimonial.published",
                {
                    "testimonial_id": testimonial_id,
                    "published_urls": published_urls,
                    "locations": locations
                }
            )

            return {
                "status": "completed",
                "testimonial_id": testimonial_id,
                "published_urls": published_urls,
                "locations_count": len(published_urls)
            }

    # Helper methods
    def _calculate_testimonial_score(self, client: Dict[str, Any]) -> int:
        """Calculate likelihood score for testimonial request (1-10)."""
        score = 5  # Base score

        # Satisfaction score impact
        if client.get("satisfaction_score"):
            score += min(client["satisfaction_score"] - 5, 3)

        # Recency impact
        days_since_completion = (datetime.now() - client["completed_at"]).days
        if days_since_completion <= 7:
            score += 2
        elif days_since_completion <= 14:
            score += 1

        # Project success indicators (could be extended)
        # - On-time delivery
        # - Within budget
        # - No scope issues

        return min(score, 10)

    def _recommend_testimonial_type(self, client: Dict[str, Any]) -> str:
        """Recommend best testimonial type for this client."""
        score = self._calculate_testimonial_score(client)

        if score >= 9:
            return "case_study"  # High-value clients for detailed case studies
        elif score >= 7:
            return "video"  # Good relationship, ask for video
        else:
            return "written"  # Standard written testimonial
```

---

## Tools Registration

```python
async def register_tools(self):
    """Register tools for the Testimonial Request Agent."""

    # Qualification tool
    self.register_tool(
        tool=self._qualify_clients,
        name="qualify_clients",
        description="Identify clients eligible for testimonial requests based on project success and satisfaction scores"
    )

    # Request sending tool
    self.register_tool(
        tool=self._send_testimonial_request,
        name="send_testimonial_request",
        description="Send personalized testimonial request to a client"
    )

    # Response collection tool
    self.register_tool(
        tool=self._collect_testimonial_response,
        name="collect_testimonial_response",
        description="Process and store incoming testimonial responses"
    )

    # Review management tool
    self.register_tool(
        tool=self._review_testimonial,
        name="review_testimonial",
        description="Review and approve/reject submitted testimonials"
    )

    # Publishing tool
    self.register_tool(
        tool=self._publish_testimonial,
        name="publish_testimonial",
        description="Publish approved testimonials to various platforms"
    )

    # Follow-up scheduling tool
    self.register_tool(
        tool=self._schedule_follow_up,
        name="schedule_follow_up",
        description="Schedule automated follow-up for pending testimonial requests"
    )
```

---

## Error Handling

### Critical Error Scenarios

1. **Email Sending Failure**
   - Retry up to 3 times with exponential backoff
   - Mark request as failed if all retries exhausted
   - Alert human administrator

2. **Database Constraint Violations**
   - Validate all data before insertion
   - Handle duplicate request detection gracefully
   - Log all constraint violations for debugging

3. **Incentive Processing Errors**
   - Rollback incentive creation on errors
   - Ensure incentives are not double-claimed
   - Validate incentive codes are unique

4. **Publishing Failures**
   - Rollback published state on partial failures
   - Maintain audit trail of publishing attempts
   - Allow manual retry for failed publishes

### Recovery Mechanisms

```python
async def _handle_email_failure(self, request_id: UUID, error: Exception):
    """Handle email sending failures with retry logic."""
    async with get_db_session() as db:
        # Get retry count
        result = await db.execute(
            "SELECT retry_count FROM testimonial_requests WHERE id = :id",
            {"id": request_id}
        )
        retry_count = (result.scalar_one() or 0) + 1

        if retry_count <= 3:
            # Schedule retry with exponential backoff
            delay = 2 ** retry_count * 60  # 2min, 4min, 8min
            await self._schedule_email_retry(request_id, delay)
        else:
            # Mark as failed
            await db.execute(
                "UPDATE testimonial_requests SET status = 'failed' WHERE id = :id",
                {"id": request_id}
            )
            # Alert admin
            await self.handoff_to(
                target_agent="admin_alert",
                payload={
                    "alert_type": "testimonial_email_failed",
                    "request_id": str(request_id),
                    "error": str(error)
                },
                priority="high"
            )
```

---

## Testing Strategy

### Unit Tests (Coverage >90%)

1. **Client Qualification Logic**
   - Test scoring algorithm with various client data
   - Test filtering criteria and edge cases
   - Test recommendation logic for testimonial types

2. **Email Generation**
   - Test template personalization
   - Test subject line generation
   - Test form/video link inclusion

3. **Response Processing**
   - Test response data validation
   - Test testimonial creation from responses
   - Test incentive processing

4. **Review Workflow**
   - Test approval/rejection workflows
   - Test usage rights management
   - Test metadata updates

### Integration Tests (Coverage >85%)

1. **End-to-End Workflow**
   - Test complete testimonial collection flow
   - Test agent handoffs to satisfaction survey
   - Test human review integration

2. **Email Integration**
   - Test actual email sending via provider
   - Test email webhook processing
   - Test bounce handling

3. **Database Operations**
   - Test all CRUD operations
   - Test transaction rollbacks
   - Test concurrent access

### Performance Tests

1. **Bulk Qualification**
   - Test qualifying 1000+ clients efficiently
   - Optimize database queries with proper indexes

2. **Email Throughput**
   - Test sending 100 emails/hour
   - Test rate limiting with email provider

3. **Concurrent Processing**
   - Test multiple testimonial responses simultaneously
   - Test review queue processing

---

## Security Considerations

1. **Data Privacy**
   - Encrypt testimonial content at rest
   - Obtain explicit consent for all usage rights
   - Allow clients to request content removal

2. **Access Control**
   - Role-based access for review workflows
   - Audit trail for all testimonial modifications
   - Secure API endpoints for testimonial submission

3. **Content Moderation**
   - Filter inappropriate content
   - Validate video uploads for malware
   - Implement content size limits

---

## Monitoring and Metrics

### Key Performance Indicators

1. **Request Metrics**
   - Testimonial request rate: requests/week
   - Response rate: responses/requests (target: >30%)
   - Average response time: days

2. **Quality Metrics**
   - Approval rate: approved/submitted (target: >80%)
   - Average testimonial strength score
   - Featured testimonial percentage

3. **Publishing Metrics**
   - Publication lag: approval to publish days
   - Published testimonial count by type
   - Website placement conversion rate

### Health Checks

```python
async def health_check(self) -> Dict[str, Any]:
    """Return agent health status."""
    async with get_db_session() as db:
        # Check pending requests older than 14 days
        stale_requests = await db.scalar(
            """SELECT COUNT(*) FROM testimonial_requests
               WHERE status = 'sent' AND sent_at < NOW() - INTERVAL '14 days'"""
        )

        # Check reviews pending >7 days
        stale_reviews = await db.scalar(
            """SELECT COUNT(*) FROM testimonials
               WHERE review_status = 'pending' AND created_at < NOW() - INTERVAL '7 days'"""
        )

        return {
            "agent": self.name,
            "status": "healthy" if stale_requests == 0 and stale_reviews == 0 else "warning",
            "stale_requests": stale_requests,
            "stale_reviews": stale_reviews,
            "last_request": await self._get_last_request_timestamp()
        }
```

---

## Implementation Dependencies

### Required Integrations

1. **Email Service** (Instantly.ai or SendGrid)
   - Personalized email sending
   - Template management
   - Delivery tracking and bounces

2. **Survey/Form Service** (Typeform or Google Forms)
   - Testimonial collection forms
   - Video upload support
   - Structured data capture

3. **Storage Service** (AWS S3 or CloudFront)
   - Video file storage
   - Image storage for client photos
   - CDN delivery

4. **Notification Service** (for internal alerts)
   - Review request notifications
   - Publishing confirmations
   - Error alerts

### Agent Dependencies

1. **Satisfaction Survey Agent**
   - Provides satisfaction scores
   - Triggers testimonial eligibility

2. **Project Management Agent**
   - Provides project completion status
   - Supplies project context

3. **Human Review Agent** (or workflow)
   - Approves/rejects testimonials
   - Manages usage rights
   - Handles publishing decisions

---

## Migration Plan

### Phase 1: Database Setup
1. Create schema tables
2. Migrate existing client data
3. Set up indexes and constraints

### Phase 2: Core Agent Implementation
1. Implement BaseAgent extension
2. Add qualification logic
3. Integrate email service

### Phase 3: Workflow Integration
1. Connect to satisfaction survey agent
2. Set up review workflows
3. Implement publishing pipeline

### Phase 4: Testing & Rollout
1. Comprehensive testing
2. Pilot with select clients
3. Full deployment

---

**Next Steps:**
1. Review and approve this specification
2. Set up database schema migrations
3. Configure required integrations
4. Begin Phase 1 implementation
