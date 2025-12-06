# Task: Implement Company Research Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/research-company-research.md
**Created:** 2025-12-06

## Summary

Implement the Company Research Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** Research & Intelligence
**Phase:** Phase 2 - Intelligence Layer
**Dependencies:** None

## Files to Create/Modify

- [ ] `app/backend/src/agents/company_research/__init__.py`
- [ ] `app/backend/src/agents/company_research/agent.py`
- [ ] `app/backend/src/agents/company_research/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_company_research_agent.py`
- [ ] `app/backend/__tests__/integration/test_company_research_integration.py`
- [ ] `app/backend/__tests__/fixtures/company_research_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `CompanyResearchAgent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
- [ ] Implement `search_company_news()` tool
- [ ] Implement `scrape_linkedin_company()` tool
- [ ] Implement `search_job_postings()` tool
- [ ] Implement `analyze_tech_stack()` tool
- [ ] Implement `scrape_company_website()` tool
- [ ] Implement `identify_trigger_events()` tool
- [ ] Implement `generate_company_brief()` tool
- [ ] Implement `research_company_task()` tool
- [ ] Implement `refresh_stale_research_task()` tool


### Phase 3: Integration
- [ ] Implement Clients client integration
- [ ] Add error handling with retry logic for Clients
- [ ] Add rate limiting for Clients
- [ ] Implement Serper client integration
- [ ] Add error handling with retry logic for Serper
- [ ] Add rate limiting for Serper
- [ ] Implement Apify client integration
- [ ] Add error handling with retry logic for Apify
- [ ] Add rate limiting for Apify
- [ ] Implement BuiltWith client integration
- [ ] Add error handling with retry logic for BuiltWith
- [ ] Add rate limiting for BuiltWith
- [ ] Implement NewsAPI client integration
- [ ] Add error handling with retry logic for NewsAPI
- [ ] Add rate limiting for NewsAPI
- [ ] Implement Firecrawl client integration
- [ ] Add error handling with retry logic for Firecrawl
- [ ] Add rate limiting for Firecrawl


### Phase 4: Database
- [ ] Create/verify database schema:
  - [ ] `company_research` table
  - [ ] `company_news` table
  - [ ] `company_jobs` table
  - [ ] `company_tech_stack` table
  - [ ] `trigger_events` table
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
pytest --cov=src/agents/company_research --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_company_research_agent.py -v
pytest __tests__/integration/test_company_research_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/research-company-research.md` must be met:

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

- See full specification in `specs/agents/research-company-research.md` for:
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
**Next available task number: 151**
