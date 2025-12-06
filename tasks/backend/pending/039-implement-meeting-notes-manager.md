# Task: Implement Meeting Notes Manager Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/meeting-notes-manager.md
**Created:** 2025-12-06

## Summary

Implement the Meeting Notes Manager Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** Meeting Management
**Phase:** Phase 2 - Intelligence Layer
**Dependencies:** - Meeting Fathom Integration Agent (receives transcripts)

## Files to Create/Modify

- [ ] `app/backend/src/agents/meeting_notes_manager/__init__.py`
- [ ] `app/backend/src/agents/meeting_notes_manager/agent.py`
- [ ] `app/backend/src/agents/meeting_notes_manager/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_meeting_notes_manager_agent.py`
- [ ] `app/backend/__tests__/integration/test_meeting_notes_manager_integration.py`
- [ ] `app/backend/__tests__/fixtures/meeting_notes_manager_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `MeetingNotesManagerAgent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
- [ ] Implement `create_meeting_notes()` tool
- [ ] Implement `store_notes_notion()` tool
- [ ] Implement `extract_key_decisions()` tool
- [ ] Implement `extract_action_items()` tool
- [ ] Implement `link_to_project()` tool
- [ ] Implement `search_notes()` tool


### Phase 3: Integration
- [ ] Implement Tests (>85% coverage for agent) client integration
- [ ] Add error handling with retry logic for Tests (>85% coverage for agent)
- [ ] Add rate limiting for Tests (>85% coverage for agent)


### Phase 4: Database
- [ ] Create/verify database schema:
  - [ ] `meeting_notes` table
  - [ ] `note_templates` table
  - [ ] `note_links` table
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
pytest --cov=src/agents/meeting_notes_manager --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_meeting_notes_manager_agent.py -v
pytest __tests__/integration/test_meeting_notes_manager_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/meeting-notes-manager.md` must be met:

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

- See full specification in `specs/agents/meeting-notes-manager.md` for:
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
**Next available task number: 128**
