# Task: Implement Proposal-Creation Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/proposal-creation.md
**Created:** 2025-12-06

## Summary

Implement the Proposal-Creation Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** Unknown
**Phase:** Phase 1
**Dependencies:** None

## Files to Create/Modify

- [ ] `app/backend/src/agents/proposal-creation/__init__.py`
- [ ] `app/backend/src/agents/proposal-creation/agent.py`
- [ ] `app/backend/src/agents/proposal-creation/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_proposal-creation_agent.py`
- [ ] `app/backend/__tests__/integration/test_proposal-creation_integration.py`
- [ ] `app/backend/__tests__/fixtures/proposal-creation_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `Proposal-CreationAgent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
- [ ] Implement `get_call_insights()` tool
- [ ] Implement `get_client_data()` tool
- [ ] Implement `select_template()` tool
- [ ] Implement `calculate_pricing()` tool
- [ ] Implement `create_milestones()` tool
- [ ] Implement `create_pandadoc_draft()` tool
- [ ] Implement `save_proposal()` tool
- [ ] Implement `queue_for_review()` tool
- [ ] Implement `send_proposal()` tool


### Phase 3: Integration
- [ ] Implement Tests (>85% coverage for agent workflow) client integration
- [ ] Add error handling with retry logic for Tests (>85% coverage for agent workflow)
- [ ] Add rate limiting for Tests (>85% coverage for agent workflow)
- [ ] Implement PandaDoc client integration
- [ ] Add error handling with retry logic for PandaDoc
- [ ] Add rate limiting for PandaDoc


### Phase 4: Database
- [ ] Create/verify database schema:
  - [ ] `proposals` table
  - [ ] `proposal_templates` table
  - [ ] `proposal_line_items` table
  - [ ] `proposal_milestones` table
  - [ ] `proposal_versions` table
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
pytest --cov=src/agents/proposal-creation --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_proposal-creation_agent.py -v
pytest __tests__/integration/test_proposal-creation_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/proposal-creation.md` must be met:

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

- See full specification in `specs/agents/proposal-creation.md` for:
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
**Next available task number: 147**
