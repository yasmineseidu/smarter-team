# Task: Implement Long-Term Nurture Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/offboarding-long-term-nurture.md
**Created:** 2025-01-04
**Priority:** Phase 5 - Retention & Growth

## Summary

Implement the Long-Term Nurture Agent that maintains relationships with past clients and prospects through automated, value-driven communication. The agent segments contacts into nurture lists, sends personalized content at appropriate intervals, tracks engagement, and identifies re-engagement opportunities to route back to active pipelines.

## Key Features to Implement

1. **Contact Segmentation**: 4 segments (past_clients, lost_deals_timing, lost_deals_competitor, reactivation_pool)
2. **Content Management**: Library with approval workflow and performance tracking
3. **Personalized Delivery**: AI-powered content customization per contact
4. **Engagement Tracking**: Multi-channel monitoring with scoring
5. **Re-engagement Detection**: Signal analysis for sales handoff
6. **Multi-provider Email**: Instantly.ai with fallbacks

## Files to Create

### Core Agent
- `app/backend/src/agents/offboarding/long_term_nurture_agent.py` - Main agent implementation
- `app/backend/src/agents/offboarding/__init__.py` - Module init

### Tools
- `app/backend/src/agents/offboarding/tools/segmentation_tool.py` - Contact segmentation logic
- `app/backend/src/agents/offboarding/tools/content_selection_tool.py` - Content library queries
- `app/backend/src/agents/offboarding/tools/personalization_tool.py` - AI-powered content customization
- `app/backend/src/agents/offboarding/tools/email_sending_tool.py` - Multi-provider email delivery
- `app/backend/src/agents/offboarding/tools/engagement_analysis_tool.py` - Signal detection and scoring
- `app/backend/src/agents/offboarding/tools/pipeline_handoff_tool.py` - Sales handoff logic

### Database Models
- `app/backend/src/models/nurture_models.py` - SQLAlchemy models for nurture tables

### Tasks
- `app/backend/src/tasks/nurture_tasks.py` - Celery tasks for batch processing and scheduled sends

### Tests
- `app/backend/__tests__/unit/agents/offboarding/test_long_term_nurture_agent.py` - Unit tests
- `app/backend/__tests__/unit/agents/offboarding/tools/` - Tool-specific unit tests
- `app/backend/__tests__/integration/test_nurture_integration.py` - End-to-end tests

## Implementation Checklist

### Phase 1: Database Schema (Day 1-2)
- [ ] Create SQLAlchemy models for all 4 nurture tables
- [ ] Add indexes for performance optimization
- [ ] Create Alembic migration files
- [ ] Test database operations (CRUD)

### Phase 2: Core Agent Structure (Day 3-4)
- [ ] Implement LongTermNurtureAgent extending BaseAgent
- [ ] Add system prompt and agent configuration
- [ ] Implement agent registry registration
- [ ] Add basic logging and error handling

### Phase 3: Tools Implementation (Day 5-10)
- [ ] **segmentation_tool.py**: Implement segment rules and scoring
- [ ] **content_selection_tool.py**: Query and rank content library
- [ ] **personalization_tool.py**: AI integration with Claude
- [ ] **email_sending_tool.py**: Multi-provider with Instantly.ai primary
- [ ] **engagement_analysis_tool.py**: Signal detection algorithms
- [ ] **pipeline_handoff_tool.py**: Sales handoff logic

### Phase 4: Integration Layer (Day 11-13)
- [ ] Implement Instantly.ai integration
- [ ] Add GoHighLevel CRM sync
- [ ] Implement Pinecone content search
- [ ] Add Zep memory integration
- [ ] Create webhook handlers for engagement tracking

### Phase 5: Batch Processing (Day 14-16)
- [ ] Implement Celery tasks for daily nurture runs
- [ ] Add batch segmentation for new contacts
- [ ] Create scheduled content delivery
- [ ] Implement engagement webhook processing
- [ ] Add retry logic for failed sends

### Phase 6: Content Management (Day 17-19)
- [ ] Implement content library CRUD operations
- [ ] Add approval workflow
- [ ] Create content performance tracking
- [ ] Implement A/B testing framework
- [ ] Add seasonal content scheduling

### Phase 7: Testing & Quality (Day 20-23)
- [ ] Write comprehensive unit tests (>90% coverage)
- [ ] Create integration tests with mocked providers
- [ ] Implement performance tests
- [ ] Add error handling and logging
- [ ] Create monitoring and alerts

## Acceptance Criteria

### Functional Requirements
- [ ] All 4 nurture segments working with correct cadence
- [ ] Content library with approval workflow functional
- [ ] Email sending through Instantly.ai with fallbacks
- [ ] Real-time engagement tracking via webhooks
- [ ] Re-engagement signal detection with 85% accuracy
- [ ] Automatic handoff to active pipeline
- [ ] Holiday and triggered messaging
- [ ] GDPR compliance and easy unsubscribe

### Performance Requirements
- [ ] Process 1000 contacts in <30 seconds
- [ ] Send throughput of 100 emails/minute
- [ ] Engagement processing <100ms per event
- [ ] Content selection <50ms per contact
- [ ] 99.9% uptime for scheduled sends

### Code Quality
- [ ] All tests passing with >90% coverage
- [ ] Type hints everywhere (MyPy strict mode)
- [ ] Ruff linting and formatting
- [ ] Comprehensive error handling
- [ ] Structured logging with correlation IDs
- [ ] Documentation for all public methods

## Database Schema Implementation

```python
# Example model structure
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship

class NurtureList(Base):
    __tablename__ = 'nurture_lists'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(UUID(as_uuid=True), ForeignKey('contacts.id'), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'))
    segment = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source_id = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)
    nurture_score = Column(Integer, default=50)

    # Add relationships, indexes, and constraints
```

## Verification Commands

```bash
# Run all tests
pytest app/backend/__tests__/unit/agents/offboarding/ -v --cov=app/backend/src/agents/offboarding

# Type checking
mypy app/backend/src/agents/offboarding/

# Linting
ruff check app/backend/src/agents/offboarding/
ruff format app/backend/src/agents/offboarding/

# Integration tests
pytest app/backend/__tests__/integration/test_nurture_integration.py -v

# Database migration
alembic upgrade head

# Performance tests
pytest app/backend/__tests__/performance/test_nurture_performance.py -v
```

## Dependencies

### New Python Packages
- `aiosmtplib` - SMTP client for backup email sending
- `babel` - Date/time localization for different timezones
- `validators` - Email validation and sanitization

### Environment Variables
```bash
# Existing (from .env.example)
ANTHROPIC_API_KEY=...
INSTANTLY_API_KEY=...
PINECONE_API_KEY=...

# New nurture-specific
NURTURE_EMAIL_PROVIDER=instantly
NURTURE_BATCH_SIZE=100
NURTURE_SEND_RATE_LIMIT=100
NURTURE_REENGAGEMENT_THRESHOLD=80
```

## Success Metrics

- Nurture list growth: 500+ contacts in first month
- Engagement rate: >40% open rate, >5% click rate
- Re-engagement: 10-15% handoff to active pipeline monthly
- Content performance: Identify top 3 performing templates
- Delivery success: >98% deliverability rate

## Handoff Criteria

Move task to `_completed/` when:
1. All code implemented and reviewed
2. All tests passing with required coverage
3. Performance benchmarks met
4. Documentation complete
5. Security review passed
6. Production deployment tested

## Notes

- Prioritize past_clients segment first (highest value)
- Implement graceful degradation for personalization failures
- Use batch processing to respect API rate limits
- Log everything for continuous improvement
- Consider GDPR and CAN-SPAM compliance from day 1
