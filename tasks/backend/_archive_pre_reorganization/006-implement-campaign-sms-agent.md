# Task: Implement Campaign SMS Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/campaign-sms-agent.md
**Created:** 2025-12-04
**Estimated Hours:** 24-32

## Summary

Implement the Campaign SMS Agent for sending compliant SMS messages to high-value leads. The agent handles phone validation, consent verification, message generation, delivery tracking, and response processing with full TCPA compliance.

## Files to Create

### Core Agent Files
- `app/backend/src/agents/campaign_sms/__init__.py` - Package exports
- `app/backend/src/agents/campaign_sms/agent.py` - Main SMS agent class
- `app/backend/src/agents/campaign_sms/tools.py` - All tool implementations
- `app/backend/src/agents/campaign_sms/prompts.py` - System and message templates
- `app/backend/src/agents/campaign_sms/schemas.py` - Pydantic data models
- `app/backend/src/agents/campaign_sms/exceptions.py` - Custom exceptions

### Integration Layer
- `app/backend/src/integrations/twilio.py` - Twilio client extending BaseIntegrationClient

### Database
- `app/backend/src/migrations/versions/xxx_create_sms_tables.py` - Database schema migration
- `app/backend/src/models/sms.py` - SQLAlchemy models for SMS tables

### Tasks
- `app/backend/src/tasks/sms_tasks.py` - Celery tasks for SMS operations
- `app/backend/src/api/routes/sms.py` - API endpoints for SMS management
- `app/backend/src/webhooks/twilio.py` - Twilio webhook handlers

### Tests
- `app/backend/__tests__/unit/agents/test_campaign_sms.py` - Unit tests
- `app/backend/__tests__/integration/test_campaign_sms.py` - Integration tests
- `app/backend/__tests__/unit/integrations/test_twilio.py` - Twilio client tests
- `app/backend/__tests__/fixtures/sms_fixtures.py` - Test fixtures

## Implementation Checklist

### Phase 1: Foundation (8 hours)
- [ ] Create SMS agent directory structure
- [ ] Implement database models for SMS tables
- [ ] Create migration for SMS schema
- [ ] Set up Twilio integration client
- [ ] Configure environment variables for Twilio
- [ ] Create base agent class extending BaseAgent
- [ ] Implement Pydantic schemas for all inputs/outputs

### Phase 2: Tools Implementation (12 hours)
- [ ] Implement `validate_phone_number` tool
  - Use Twilio Lookup API for validation
  - Add international formatting support
  - Handle landline/VoIP detection
- [ ] Implement `check_sms_consent` tool
  - Query consent from database
  - Check rate limiting tables
  - Return compliance status
- [ ] Implement `generate_sms_message` tool
  - Create message templates for each trigger type
  - Add personalization logic
  - Enforce 160 character limit
- [ ] Implement `send_sms` tool
  - Integrate with Twilio API
  - Add delivery tracking
  - Handle scheduling
- [ ] Implement `track_delivery` tool
  - Process Twilio webhooks
  - Update delivery status
  - Handle retry logic
- [ ] Implement `handle_incoming_sms` tool
  - Parse incoming messages
  - Detect opt-outs and commands
  - Route to appropriate handlers
- [ ] Implement `log_sms_conversation` tool
  - Store all messages for audit
  - Generate conversation threads
  - Calculate compliance scores

### Phase 3: Agent Logic (6 hours)
- [ ] Implement main `process_task` method
  - Validate input data
  - Execute tool sequence
  - Handle errors gracefully
- [ ] Add system prompt with TCPA guidelines
- [ ] Implement response processing pipeline
- [ ] Add agent handoff logic for sales/scheduling
- [ ] Create rate limiting enforcement
- [ ] Add business hours validation

### Phase 4: Integration (4 hours)
- [ ] Create Celery tasks for background processing
- [ ] Add API endpoints for manual SMS sending
- [ ] Implement Twilio webhook handlers
- [ ] Add to agent registry
- [ ] Configure webhook endpoints in Twilio

### Phase 5: Testing (6 hours)
- [ ] Write unit tests for all tools (90%+ coverage)
  - Mock Twilio API responses
  - Test all error conditions
  - Verify compliance logic
- [ ] Write integration tests
  - End-to-end SMS flow
  - Webhook processing
  - Multi-agent handoffs
- [ ] Add performance tests
  - Rate limiting behavior
  - Concurrent sending
  - Delivery tracking

### Phase 6: Monitoring & Security (2 hours)
- [ ] Add structured logging with sensitive data masking
- [ ] Implement metrics collection
- [ ] Set up alerting rules
- [ ] Add phone number encryption
- [ ] Configure webhook signature verification

## Acceptance Criteria

### Functional Requirements
- [ ] Valid phone numbers pass validation, invalid ones are rejected
- [ ] No SMS sent without proper consent verification
- [ ] Opt-outs processed within 5 seconds
- [ ] All messages respect business hours (recipient timezone)
- [ ] Rate limiting: max 1 message/hour, 3/day per lead
- [ ] Messages <= 160 characters with appropriate content
- [ ] Delivery status tracked and updated
- [ ] Incoming responses routed correctly
- [ ] Full audit trail maintained for compliance

### Technical Requirements
- [ ] Database schema created with proper indexes
- [ ] All async operations properly implemented
- [ ] Error handling covers all failure modes
- [ ] Retry logic with exponential backoff
- [ ] Type hints everywhere (MyPy strict compliance)
- [ ] Code passes Ruff linting and formatting
- [ ] Unit tests >90% coverage, integration tests complete
- [ ] Performance meets latency requirements

### Integration Requirements
- [ ] Twilio client properly configured and tested
- [ ] Webhook endpoints responding correctly
- [ ] Agent handoffs working with other agents
- [ ] Celery tasks executing in background
- [ ] API endpoints documented and functional

## Dependencies

### External Services
- Twilio account with phone number provisioned
- Database access for schema creation
- Redis for Celery task queue

### Internal Components
- BaseAgent class from `src/agents/base_agent.py`
- BaseIntegrationClient from `src/integrations/base.py`
- Celery app configuration
- Database models and migrations

### Environment Variables
```bash
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...
```

## Verification Commands

### Database Setup
```bash
# Create migration
make migration name="create_sms_tables"

# Apply migration
make migrate
```

### Code Quality
```bash
# Type checking
mypy app/backend/src/agents/campaign_sms/

# Linting
ruff check app/backend/src/agents/campaign_sms/

# Formatting
ruff format app/backend/src/agents/campaign_sms/
```

### Testing
```bash
# Unit tests
pytest app/backend/__tests__/unit/agents/test_campaign_sms.py -v --cov=app/backend/src/agents/campaign_sms

# Integration tests
pytest app/backend/__tests__/integration/test_campaign_sms.py -v

# All tests with coverage
pytest --cov=src --cov-report=html
```

### Manual Testing
```bash
# Test agent import
python -c "from app.backend.src.agents.campaign_sms import CampaignSmsAgent; print('✓ Agent imports')"

# Test Twilio client
python -c "from app.backend.src.integrations.twilio import TwilioClient; print('✓ Client imports')"
```

### API Testing
```bash
# Start services
make run
make worker

# Test endpoint
curl -X POST http://localhost:8000/api/sms/send \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "...", "trigger_type": "high_intent"}'
```

## Rollout Plan

1. **Phase 1**: Deploy to staging with test Twilio number
2. **Phase 2**: Manual testing with consented test numbers
3. **Phase 3**: Internal team pilot with real leads
4. **Phase 4**: Gradual rollout with monitoring
5. **Phase 5**: Full production deployment

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| TCPA compliance violation | High | Strict consent checking, opt-out handling, legal review |
| Twilio rate limits | Medium | Implement queueing, exponential backoff |
| Phone number validation failures | Medium | Fallback to email, manual review queue |
| High costs | Low | Monitor spend, set alerts, optimize routing |
| Delivery failures | Medium | Retry logic, alternative channels |

## Success Metrics

- Delivery success rate >95%
- Opt-out rate <2%
- Response rate >15%
- Average delivery time <30s
- Compliance score 100%
- Cost per successful delivery <$0.05

## Notes

- Prioritize TCPA compliance above all else
- Implement comprehensive logging for audit trails
- Start with conservative rate limits, adjust based on performance
- All phone numbers should be stored encrypted
- Consider adding SMS templates database for future flexibility
