# Task: Implement Response-Check-In Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/response-check-in.md
**Created:** 2025-12-06

## Summary

Implement the Response-Check-In Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** Unknown
**Phase:** Phase 1
**Dependencies:** None

## Files to Create/Modify

- [ ] `app/backend/src/agents/response-check-in/__init__.py`
- [ ] `app/backend/src/agents/response-check-in/agent.py`
- [ ] `app/backend/src/agents/response-check-in/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_response-check-in_agent.py`
- [ ] `app/backend/__tests__/integration/test_response-check-in_integration.py`
- [ ] `app/backend/__tests__/fixtures/response-check-in_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `Response-Check-InAgent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
- [ ] Implement `get_conversation_history()` tool
- [ ] Implement `get_check_in_count()` tool
- [ ] Implement `generate_check_in_message()` tool
- [ ] Implement `send_check_in_email()` tool
- [ ] Implement `transition_to_reactivation_pool()` tool
- [ ] Implement `get_check_in_template()` tool


### Phase 3: Integration
- [ ] Implement Tests (Target: >85%) client integration
- [ ] Add error handling with retry logic for Tests (Target: >85%)
- [ ] Add rate limiting for Tests (Target: >85%)


### Phase 4: Database
- [ ] Create/verify database schema:
  - [ ] `check_in_logs` table
  - [ ] `check_in_templates` table
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
pytest --cov=src/agents/response-check-in --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_response-check-in_agent.py -v
pytest __tests__/integration/test_response-check-in_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/response-check-in.md` must be met:

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

- See full specification in `specs/agents/response-check-in.md` for:
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
**Next available task number: 157**
