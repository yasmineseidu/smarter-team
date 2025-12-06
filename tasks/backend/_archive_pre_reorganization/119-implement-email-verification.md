# Task: Implement Email Verification Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/leadgen-email-verification.md
**Created:** 2025-12-06

## Summary

Implement the Email Verification Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** Lead Generation & Data
**Phase:** Phase 1 - MVP Foundation
**Dependencies:** Lead List Builder Agent (provides leads with emails)

## Files to Create/Modify

- [ ] `app/backend/src/agents/email_verification/__init__.py`
- [ ] `app/backend/src/agents/email_verification/agent.py`
- [ ] `app/backend/src/agents/email_verification/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_email_verification_agent.py`
- [ ] `app/backend/__tests__/integration/test_email_verification_integration.py`
- [ ] `app/backend/__tests__/fixtures/email_verification_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `EmailVerificationAgent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
- [ ] Implement `verify_email_batch()` tool
- [ ] Implement `check_verification_cache()` tool
- [ ] Implement `route_failed_emails()` tool
- [ ] Implement `check_rate_limit_usage()` tool


### Phase 3: Integration
- [ ] Implement Reoon Client client integration
- [ ] Add error handling with retry logic for Reoon Client
- [ ] Add rate limiting for Reoon Client
- [ ] Implement Reoon client integration
- [ ] Add error handling with retry logic for Reoon
- [ ] Add rate limiting for Reoon


### Phase 4: Database
- [ ] Create/verify database schema:
  - [ ] `email_verifications` table
  - [ ] `verification_results` table
- [ ] Implement database operations (CRUD)
- [ ] Add indexes for performance


### Phase 5: Testing
- [ ] Write unit tests for agent class initialization
- [ ] Write unit tests for each tool (>90% coverage target)
- [ ] Write integration tests for complete workflows
- [ ] Create comprehensive test fixtures
- [ ] Mock external API calls appropriately
- [ ] Run `make test` - ensure all pass

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make format-check` - properly formatted
- [ ] Run `make test` - >85% coverage for agent, >90% for tools
- [ ] Verify all acceptance criteria met (see spec)
- [ ] Test error handling for all failure scenarios
- [ ] Verify logging is structured and complete

## Verification Commands

```bash
# Run tests
cd app/backend
make test

# Check coverage for this agent
pytest --cov=src/agents/email_verification --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_email_verification_agent.py -v
pytest __tests__/integration/test_email_verification_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/leadgen-email-verification.md` must be met:

- [ ] All tools implemented and tested
- [ ] Error handling matrix covered
- [ ] Performance targets met
- [ ] Database schema created/updated
- [ ] Integration clients working with proper error handling
- [ ] >85% test coverage for agent code
- [ ] >90% test coverage for tools
- [ ] All quality gates pass (lint, typecheck, format)
- [ ] Structured logging implemented throughout
- [ ] Agent handoffs properly configured (if applicable)

## Notes

- See full specification in `specs/agents/leadgen-email-verification.md` for:
  - Detailed tool specifications with parameters and return types
  - Error handling matrix with all scenarios
  - Performance requirements and targets
  - Multi-agent handoff patterns (if applicable)
  - Security considerations
  - Monitoring and alerting requirements

- Follow BaseAgent pattern from `/app/backend/src/agents/base_agent.py`
- Use BaseIntegrationClient for all external APIs
- Implement async/await for all I/O operations
- Use structured logging via `get_agent_logger()`
- Add type hints for all functions and methods
- Follow project conventions in `CLAUDE.md`

## Related Tasks

This task may depend on or be related to other agent implementations. Check the agent dependencies listed above and coordinate accordingly.

---

**Task created by automated task generation script**
**Next available task number: 120**
