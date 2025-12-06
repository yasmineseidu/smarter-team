# Task: Implement Client Offboarding Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/offboarding-client-offboarding.md
**Created:** 2025-12-06

## Summary

Implement the Client Offboarding Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** Offboarding & Nurture
**Phase:** Phase 5 - Retention & Growth
**Dependencies:** - Project Management Agent (provides completion status and project data)

## Files to Create/Modify

- [ ] `app/backend/src/agents/client_offboarding/__init__.py`
- [ ] `app/backend/src/agents/client_offboarding/agent.py`
- [ ] `app/backend/src/agents/client_offboarding/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_client_offboarding_agent.py`
- [ ] `app/backend/__tests__/integration/test_client_offboarding_integration.py`
- [ ] `app/backend/__tests__/fixtures/client_offboarding_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `ClientOffboardingAgent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
- [ ] Implement `get_offboarding_checklist()` tool
- [ ] Implement `update_checklist_item()` tool
- [ ] Implement `prepare_deliverable_handoff()` tool
- [ ] Implement `verify_final_payment()` tool
- [ ] Implement `revoke_access_credentials()` tool
- [ ] Implement `archive_project_data()` tool
- [ ] Implement `send_feedback_request()` tool
- [ ] Implement `transition_to_nurture()` tool


### Phase 3: Integration
- [ ] Implement Tests client integration
- [ ] Add error handling with retry logic for Tests
- [ ] Add rate limiting for Tests


### Phase 4: Database
- [ ] Verify database schema (uses existing tables)
- [ ] Implement database operations


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
pytest --cov=src/agents/client_offboarding --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_client_offboarding_agent.py -v
pytest __tests__/integration/test_client_offboarding_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/offboarding-client-offboarding.md` must be met:

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

- See full specification in `specs/agents/offboarding-client-offboarding.md` for:
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
**Next available task number: 134**
