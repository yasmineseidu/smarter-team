# Task: Implement Meeting No-Show Handler Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/meeting-no-show-handler.md
**Created:** 2025-12-05
**Priority:** High (Phase 2 - Intelligence Layer)

## Summary

Build an autonomous agent that detects missed meetings, sends personalized follow-up emails with reschedule options, tracks no-show patterns, and manages chronic no-shows by moving them to a reactivation pool. The agent must handle failures gracefully and integrate with video conferencing platforms, email providers, and Cal.com for rescheduling.

## Files to Create

### Core Implementation
- `app/backend/src/agents/meeting/meeting_no_show_handler.py`
- `app/backend/src/agents/meeting/tools/check_meeting_attendance.py`
- `app/backend/src/agents/meeting/tools/get_no_show_history.py`
- `app/backend/src/agents/meeting/tools/send_no_show_email.py`
- `app/backend/src/agents/meeting/tools/generate_reschedule_link.py`
- `app/backend/src/agents/meeting/tools/update_no_show_record.py`
- `app/backend/src/agents/meeting/tools/move_to_reactivation_pool.py`

### Database Migrations
- `app/backend/migrations/versions/xxx_create_no_show_tables.py`

### Tests
- `app/backend/__tests__/unit/agents/meeting/test_meeting_no_show_handler.py`
- `app/backend/__tests__/unit/agents/meeting/tools/test_*.py` (one per tool)
- `app/backend/__tests__/integration/test_no_show_handler_integration.py`
- `app/backend/__tests__/fixtures/meeting_fixtures.py`

### Email Templates
- `app/backend/templates/email/no_show_first.html`
- `app/backend/templates/email/no_show_second.html`
- `app/backend/templates/email/no_show_third.html`
- `app/backend/templates/email/no_show_follow_up.html`

## Implementation Checklist

### Database Schema
- [ ] Create migration for `no_show_logs` table
- [ ] Create migration for `reschedule_attempts` table
- [ ] Create migration for `reactivation_pool` table
- [ ] Add all required indexes for performance
- [ ] Add constraints for data integrity

### Agent Implementation
- [ ] Create `MeetingNoShowHandler` class extending `BaseAgent`
- [ ] Implement system prompt property
- [ ] Implement `process_task` method with state machine
- [ ] Register all tools with proper schemas
- [ ] Add configuration constants class
- [ ] Implement proper error handling at agent level

### Tool Implementations
- [ ] **check_meeting_attendance**: Integrate with Zoom/Google Meet/Teams APIs
  - Implement platform-specific adapters
  - Add rate limiting and retry logic
  - Handle API authentication failures
- [ ] **get_no_show_history**: Query database with joins
  - Implement efficient pagination
  - Add caching for recent queries
- [ ] **send_no_show_email**: Email sending with templates
  - Support multiple email providers
  - Implement personalization
  - Add delivery tracking
- [ ] **generate_reschedule_link**: Cal.com integration
  - Handle different event types
  - Manage link expiration
  - Fallback for API failures
- [ ] **update_no_show_record**: Database updates
  - Atomic transactions
  - Constraint validation
  - Audit logging
- [ ] **move_to_reactivation_pool**: Client lifecycle management
  - Check for existing records
  - Calculate reactivation timing
  - Update client status

### Email Templates
- [ ] Create responsive HTML templates
- [ ] Add personalization placeholders
- [ ] Implement plain text fallbacks
- [ ] Add tracking pixels (optional)
- [ ] Test across email clients

### Error Handling
- [ ] Implement exponential backoff for retries
- [ ] Add circuit breakers for external APIs
- [ ] Create fallback strategies for each failure mode
- [ ] Log all errors with sufficient context
- [ ] Implement graceful degradation

### Testing
- [ ] Write unit tests for each tool
  - Mock external APIs
  - Test all error paths
  - Validate input/output schemas
- [ ] Write agent tests
  - Test state machine transitions
  - Mock tool responses
  - Verify logging
- [ ] Write integration tests
  - End-to-end flow with mocks
  - Database transaction tests
  - API integration tests
- [ ] Create test fixtures
  - Sample meeting data
  - Mock API responses
  - Test client records

### Performance & Reliability
- [ ] Add Redis caching for frequently accessed data
- [ ] Implement async/await throughout
- [ ] Add monitoring and metrics
- [ ] Set up log aggregation
- [ ] Configure alerting rules

## Acceptance Criteria

Must pass all tests and meet requirements from spec:
- [ ] Detects no-shows exactly 10 minutes after start time
- [ ] Sends correct email template based on no-show count (1st, 2nd, 3rd)
- [ ] Generates working Cal.com reschedule links
- [ ] Accurately tracks and increments no-show count
- [ ] Sends 24-hour follow-up when no reschedule response
- [ ] Moves clients to reactivation pool after 3rd no-show
- [ ] Prevents duplicate processing with database constraints
- [ ] Handles all integration failures without data loss
- [ ] Completes processing in under 10 seconds
- [ ] Maintains professional, empathetic tone
- [ ] Logs all actions with structured context

## Verification

```bash
# Run database migrations
make migrate

# Run unit tests
pytest app/backend/__tests__/unit/agents/meeting/ -v --cov=src.agents.meeting

# Run integration tests
pytest app/backend/__tests__/integration/test_no_show_handler_integration.py -v

# Type checking
mypy app/backend/src/agents/meeting/

# Linting
ruff check app/backend/src/agents/meeting/
ruff format --check app/backend/src/agents/meeting/

# Manual smoke test
python -c "
from src.agents.meeting.meeting_no_show_handler import MeetingNoShowHandler
agent = MeetingNoShowHandler()
print('Agent created successfully:', agent.name)
"

# Test email templates (optional)
python -m src.tools.email_preview --template no_show_first
```

## Dependencies & Environment Variables

Add to `.env.example`:
```bash
# Video Conferencing Platforms
ZOOM_API_KEY=your_zoom_api_key
ZOOM_API_SECRET=your_zoom_api_secret
GOOGLE_MEET_CREDENTIALS_JSON=path/to/credentials.json
TEAMS_TENANT_ID=your_teams_tenant_id

# Email Provider (choose one)
SENDGRID_API_KEY=your_sendgrid_key
# OR
AWS_SES_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Cal.com Integration
CAL_COM_API_KEY=your_cal_com_key
CAL_COM_WEBHOOK_SECRET=your_webhook_secret

# No-Show Handler Settings
NO_SHOW_THRESHOLD_MINUTES=10
FOLLOW_UP_HOURS=24
REACTIVATION_THRESHOLD=3
```

## Implementation Notes

1. **Start with database schema** - Create tables first, they're needed for all other features
2. **Build tools independently** - Each tool should be testable in isolation
3. **Use BaseAgent patterns** - Follow existing conventions from `base_agent.py`
4. **Mock external APIs in tests** - Never hit real APIs in unit tests
5. **Consider timezone handling** - All timestamps should be UTC with proper conversion
6. **Email deliverability** - Set up proper SPF/DKIM records for sending domain
7. **Rate limits matter** - Video platform APIs are strict about rate limits
8. **Idempotency is key** - Duplicate processing must be prevented at database level

## Integration Points

After implementing, ensure these agents properly coordinate:
- **Meeting Scheduler Agent** → Meeting No-Show Handler (meeting data)
- **Meeting No-Show Handler** → Meeting Scheduler Agent (reschedule)
- **Meeting No-Show Handler** → Client Success Agent (chronic no-shows)
- **Meeting No-Show Handler** → Reactivation Agent (reactivation pool)

Test these handoffs with the `agent_handoff` Celery task.
