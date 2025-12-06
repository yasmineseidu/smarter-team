# Task: Implement Email Verification Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/leadgen-email-verification.md
**Created:** 2025-12-05
**Priority:** High (Phase 1 - MVP Foundation)

## Summary

Implement the Email Verification Agent that validates email addresses using the Reoon Email Verifier API. The agent processes emails in batches, caches recent verifications, routes failed emails to waterfall enrichment, and monitors API usage to prevent exceeding rate limits.

## Files to Create

### Core Implementation
- `app/backend/src/agents/email_verification/__init__.py` - Package init
- `app/backend/src/agents/email_verification/agent.py` - Main agent implementation
- `app/backend/src/agents/email_verification/schemas.py` - Pydantic models
- `app/backend/src/agents/email_verification/validator.py` - Email validation logic
- `app/backend/src/integrations/reoon.py` - Reoon API client

### Database
- `app/backend/alembic/versions/xxxx_add_email_verification_tables.py` - Migration

### Tests
- `app/backend/__tests__/unit/agents/test_email_verification_agent.py` - Unit tests
- `app/backend/__tests__/unit/agents/test_reoon_client.py` - Integration tests
- `app/backend/__tests__/integration/test_email_verification_integration.py` - E2E tests
- `app/backend/__tests__/fixtures/email_verification_fixtures.py` - Test fixtures

## Implementation Checklist

### Phase 1: Foundation Setup
- [ ] Create agent package structure
- [ ] Implement `EmailVerificationAgent` class extending `BaseAgent`
- [ ] Define all Pydantic schemas in `schemas.py`
- [ ] Create database migration with all tables
- [ ] Write basic agent initialization tests
- [ ] Run `make check` - ensure all quality gates pass

### Phase 2: Reoon Integration
- [ ] Implement `ReoonClient` extending `BaseIntegrationClient`
  - [ ] `verify_single()` method with proper error handling
  - [ ] `verify_bulk()` method for batch processing
  - [ ] `get_bulk_results()` with polling logic
  - [ ] `get_usage_stats()` for rate limit monitoring
- [ ] Add comprehensive retry logic with tenacity
- [ ] Implement timeout handling with adaptive timeouts
- [ ] Write integration tests for Reoon client
- [ ] Test with real Reoon API (use test credits)

### Phase 3: Core Verification Tools
- [ ] Implement `verify_email_batch()` tool
  - [ ] Input validation with Pydantic schemas
  - [ ] Rate limit checking before processing
  - [ ] Load leads from database efficiently
  - [ ] Check verification cache (7-day TTL)
  - [ ] Call Reoon API (bulk or single based on size)
  - [ ] Poll for bulk results with adaptive intervals
  - [ ] Parse and validate API responses
  - [ ] Save results to database transactionally
  - [ ] Update lead records with verification status
  - [ ] Route failed emails to enrichment agent
- [ ] Implement `check_verification_cache()` tool
- [ ] Implement `route_failed_emails()` with proper handoff payload
- [ ] Implement `check_rate_limit_usage()` with alerting
- [ ] Register all tools in agent `__init__`

### Phase 4: Advanced Error Handling
- [ ] Add `EmailValidator` class with comprehensive validation
- [ ] Implement `RateLimitExceededError` exception
- [ ] Add Redis fallback for database failures
- [ ] Implement circuit breaker for persistent API failures
- [ ] Add memory management for large batches
- [ ] Handle partial batch failures gracefully
- [ ] Add structured logging throughout

### Phase 5: Database & Persistence
- [ ] Apply database migration
- [ ] Create `EmailVerification` SQLAlchemy model
- [ ] Implement async database operations
- [ ] Add proper indexes for performance
- [ ] Create Redis caching layer for recent verifications
- [ ] Write database transaction tests

### Phase 6: Testing & Coverage
- [ ] Write unit tests for all tools (>90% coverage)
  - [ ] Test input validation
  - [ ] Test error handling paths
  - [ ] Test retry logic
  - [ ] Test cache behavior
- [ ] Write integration tests
  - [ ] Test full verification workflow
  - [ ] Test handoff to enrichment agent
  - [ ] Test rate limiting behavior
  - [ ] Test bulk API polling
- [ ] Create comprehensive test fixtures
- [ ] Run `make test` - achieve >85% coverage

### Phase 7: Performance & Optimization
- [ ] Implement batch processing optimizations
- [ ] Add concurrent processing for multiple batches
- [ ] Optimize database queries (batch inserts/updates)
- [ ] Add memory monitoring and throttling
- [ ] Implement adaptive batch sizing
- [ ] Add metrics collection

### Phase 8: Documentation & Quality
- [ ] Update all docstrings with detailed descriptions
- [ ] Add inline comments for complex logic
- [ ] Update CLAUDE.md with new agent details
- [ ] Create usage examples in README
- [ ] Run `make check` - all quality gates pass
- [ ] Run `make lint-fix` and `make format`
- [ ] Verify zero MyPy errors
- [ ] Review logging output for completeness

## Acceptance Criteria

### Functional Requirements
- [ ] Agent verifies emails using Reoon API (quick and power modes)
- [ ] Batches of 1-500 emails processed efficiently
- [ ] Results cached for 7 days to avoid duplicate verifications
- [ ] Rate limit monitoring with alerts at 90% usage
- [ ] Invalid/risky emails routed to Waterfall Enrichment Agent
- [ ] All verification states stored in database
- [ ] Lead records updated with verification status

### Performance Requirements
- [ ] Single verification: <1s (quick), <3s (power)
- [ ] Batch verification (100 emails): <30s
- [ ] Database operations: <100ms per record
- [ ] Cache lookup: <10ms
- [ ] Memory usage: <256MB for 500 email batch
- [ ] API error rate: <1% under normal conditions

### Quality Requirements
- [ ] Unit test coverage: >90% for tools
- [ ] Integration test coverage: >85% for agent
- [ ] Zero MyPy type errors
- [ ] Zero Ruff linting errors
- [ ] All error scenarios tested
- [ ] Structured logging throughout

### Security Requirements
- [ ] API key stored securely via Settings
- [ ] Input validation on all parameters
- [ ] SQL injection prevention via SQLAlchemy
- [ ] Rate limiting enforcement
- [ ] Error messages don't leak sensitive data

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_email_verification*.py -v --cov=app/backend/src/agents/email_verification

# Run integration tests
pytest app/backend/__tests__/integration/test_email_verification_integration.py -v

# Type checking
mypy app/backend/src/agents/email_verification/

# Linting
ruff check app/backend/src/agents/email_verification/
ruff check app/backend/src/integrations/reoon.py

# Format
ruff format app/backend/src/agents/email_verification/
ruff format app/backend/src/integrations/reoon.py

# Full test suite
make test

# Database migration
make migrate

# Manual test
python -c "
from app.backend.src.agents.email_verification.agent import EmailVerificationAgent
from app.backend.src.config import Settings
import asyncio

async def test():
    settings = Settings()
    agent = EmailVerificationAgent(settings)
    print(f'Agent initialized: {agent.name}')
    print(f'System prompt length: {len(agent.system_prompt)}')

asyncio.run(test())
"
```

## Dependencies

### Required Environment Variables
```bash
REOON_API_KEY=your_api_key_here  # Required for Reoon API
```

### Python Dependencies (add to pyproject.toml if missing)
- `tenacity>=8.2.0` - Retry logic with exponential backoff
- `redis>=4.5.0` - For caching and fallback storage
- All other dependencies already exist in the project

## Related Tasks

This task enables:
- Waterfall Email Enrichment Agent (receives failed emails)
- Campaign Creation Agent (receives verified emails)

## Notes

1. **Bulk API Polling**: Reoon's bulk API is asynchronous. Implement proper polling with exponential backoff.
2. **Memory Management**: Process large batches in chunks to avoid memory issues.
3. **Error Recovery**: Use Redis as a fallback when database is unavailable.
4. **Rate Limiting**: Always check credits before processing to avoid API failures.
5. **Testing**: Use mocking for Reoon API in unit tests, real API in integration tests.

## Completion

Move this task to `_completed/` and update `tasks/TASK-LOG.md` with:
- Implementation summary
- Test coverage achieved
- Any deviations from spec
- Performance benchmarks

---
**Task created from spec:** specs/agents/leadgen-email-verification.md
**Implementation estimated time:** 3-5 days
**Reviewer:** TBD
