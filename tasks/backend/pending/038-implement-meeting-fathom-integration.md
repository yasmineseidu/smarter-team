# Task: Implement Meeting Fathom Integration Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/meeting-fathom-integration.md
**Created:** 2025-12-06

## Summary

Implement the Meeting Fathom Integration Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** Meeting Management
**Phase:** Phase 1 - MVP Foundation
**Dependencies:** - **Meeting Scheduler Agent** - Provides meeting metadata (lead_id, meeting_id, type)

## Files to Create/Modify

- [ ] `app/backend/src/agents/meeting_fathom_integration/__init__.py`
- [ ] `app/backend/src/agents/meeting_fathom_integration/agent.py`
- [ ] `app/backend/src/agents/meeting_fathom_integration/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_meeting_fathom_integration_agent.py`
- [ ] `app/backend/__tests__/integration/test_meeting_fathom_integration_integration.py`
- [ ] `app/backend/__tests__/fixtures/meeting_fathom_integration_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `MeetingFathomIntegrationAgent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
- [ ] Implement `validate_fathom_webhook()` tool
- [ ] Implement `fetch_fathom_transcript()` tool
- [ ] Implement `match_meeting_to_transcript()` tool
- [ ] Implement `store_transcript()` tool
- [ ] Implement `store_in_zep_memory()` tool
- [ ] Implement `handoff_to_transcript_processor()` tool
- [ ] Implement `update_meeting_record()` tool
- [ ] Implement `check_transcript_quality()` tool


### Phase 3: Integration
- [ ] Implement Tests (Coverage > 85%) client integration
- [ ] Add error handling with retry logic for Tests (Coverage > 85%)
- [ ] Add rate limiting for Tests (Coverage > 85%)
- [ ] Implement Fathom client integration
- [ ] Add error handling with retry logic for Fathom
- [ ] Add rate limiting for Fathom


### Phase 4: Database
- [ ] Create/verify database schema:
  - [ ] `call_transcripts` table
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
pytest --cov=src/agents/meeting_fathom_integration --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_meeting_fathom_integration_agent.py -v
pytest __tests__/integration/test_meeting_fathom_integration_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/meeting-fathom-integration.md` must be met:

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

- See full specification in `specs/agents/meeting-fathom-integration.md` for:
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
**Next available task number: 125**
