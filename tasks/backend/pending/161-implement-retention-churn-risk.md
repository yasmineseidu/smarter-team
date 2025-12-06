# Task: Implement Retention-Churn-Risk Agent

**Status:** Pending
**Domain:** backend
**Source:** specs/agents/retention-churn-risk.md
**Created:** 2025-12-06

## Summary

Implement the Retention-Churn-Risk Agent with all tools, tests, and integrations as specified in the production spec.

## Agent Details

**Category:** Unknown
**Phase:** Phase 5 - Retention & Growth
**Dependencies:** None

## Files to Create/Modify

- [ ] `app/backend/src/agents/retention-churn-risk/__init__.py`
- [ ] `app/backend/src/agents/retention-churn-risk/agent.py`
- [ ] `app/backend/src/agents/retention-churn-risk/tools.py`
- [ ] `app/backend/__tests__/unit/agents/test_retention-churn-risk_agent.py`
- [ ] `app/backend/__tests__/integration/test_retention-churn-risk_integration.py`
- [ ] `app/backend/__tests__/fixtures/retention-churn-risk_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Class Setup
- [ ] Create agent directory structure
- [ ] Implement `Retention-Churn-RiskAgent` class extending BaseAgent
- [ ] Define `system_prompt` property
- [ ] Implement `process_task()` method with task routing
- [ ] Register all tools in `_register_tools()`

### Phase 2: Tool Implementation
- [ ] Implement `calculate_churn_risk_score()` tool
- [ ] Implement `detect_communication_drop()` tool
- [ ] Implement `detect_payment_issues()` tool
- [ ] Implement `detect_meeting_issues()` tool
- [ ] Implement `detect_satisfaction_issues()` tool
- [ ] Implement `detect_scope_issues()` tool
- [ ] Implement `send_churn_risk_alert()` tool
- [ ] Implement `create_intervention()` tool
- [ ] Implement `get_risk_trends()` tool


### Phase 3: Integration
- [ ] Implement Failures client integration
- [ ] Add error handling with retry logic for Failures
- [ ] Add rate limiting for Failures


### Phase 4: Database
- [ ] Create/verify database schema:
  - [ ] `churn_risk_scores` table
  - [ ] `risk_signals` table
  - [ ] `churn_interventions` table
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
pytest --cov=src/agents/retention-churn-risk --cov-report=term-missing

# Run specific agent tests
pytest __tests__/unit/agents/test_retention-churn-risk_agent.py -v
pytest __tests__/integration/test_retention-churn-risk_integration.py -v

# Quality checks
make check
```

## Acceptance Criteria

All criteria from `specs/agents/retention-churn-risk.md` must be met:

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

- See full specification in `specs/agents/retention-churn-risk.md` for:
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
**Next available task number: 162**
