# Task: Implement Technographic Data Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/leadgen-technographic-data.md
**Created:** 2025-12-06

## Summary

Implement the Technographic Data Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** Lead Generation & Data
**Phase:** Phase 6 - Multi-Channel & Advanced
**Dependencies:** Company Research Agent (provides company context)

## Files to Create/Modify

- [ ] `app/backend/src/agents/technographic_data/__init__.py`
- [ ] `app/backend/src/agents/technographic_data/agent.py`
- [ ] `app/backend/src/agents/technographic_data/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_technographic_data_agent.py`
- [ ] `app/backend/__tests__/integration/test_technographic_data_integration.py`
- [ ] `app/backend/__tests__/fixtures/technographic_data_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `TechnographicDataAgent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
- [ ] Implement `query_builtwith_api()` tool
- [ ] Implement `query_wappalyzer_api()` tool
- [ ] Implement `scrape_website_tech()` tool
- [ ] Implement `analyze_job_postings()` tool
- [ ] Implement `update_company_tech_stack()` tool
- [ ] Implement `generate_tech_signals()` tool


### Phase 3: Integration
- [ ] Implement Tests client integration
- [ ] Add error handling with retry logic for Tests
- [ ] Add rate limiting for Tests


### Phase 4: Database
- [ ] Create/verify database schema:
  - [ ] `company_tech_stack` table
  - [ ] `tech_signals` table
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
pytest --cov=src/agents/technographic_data --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_technographic_data_agent.py -v
pytest __tests__/integration/test_technographic_data_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/leadgen-technographic-data.md` must be met:

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

- See full specification in `specs/agents/leadgen-technographic-data.md` for:
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
**Next available task number: 123**
