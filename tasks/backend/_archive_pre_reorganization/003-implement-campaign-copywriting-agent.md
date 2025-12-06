# Task: Implement Campaign Copywriting Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/campaign-copywriting.md
**Created:** 2025-12-05
**Estimated Duration:** 2-3 days

## Summary

Implement the Campaign Copywriting Agent that generates ultra-human cold email copy with A/B testing variants. The agent must enforce strict 125-character limits, maintain conversational tone, and integrate with Claude API, Instantly API, and human review workflows.

## Files to Create

### Core Implementation
- `app/backend/src/agents/campaign_copywriting/__init__.py`
- `app/backend/src/agents/campaign_copywriting/agent.py`
- `app/backend/src/agents/campaign_copywriting/tools.py`
- `app/backend/src/agents/campaign_copywriting/prompts.py`

### Database Models
- `app/backend/src/models/email_copy.py`

### Tests
- `app/backend/__tests__/unit/agents/test_campaign_copywriting.py`
- `app/backend/__tests__/unit/agents/test_campaign_copywriting_tools.py`
- `app/backend/__tests__/integration/test_campaign_copywriting_integration.py`
- `app/backend/__tests__/fixtures/campaign_copywriting_fixtures.py`

## Implementation Checklist

### Phase 1: Agent Structure (Day 1)
- [ ] Create `CampaignCopywritingAgent` class extending `BaseAgent`
- [ ] Initialize Claude AsyncAnthropic client with retry logic
- [ ] Initialize Slack client for review notifications
- [ ] Set up structured logging with agent name
- [ ] Register all 7 tools with proper signatures

### Phase 2: Tool Implementation (Day 1-2)
- [ ] **pull_research_data**: Retrieve niche/persona data from database
- [ ] **generate_email_drafts**: Claude API integration for initial drafts
- [ ] **create_ab_variants**: Generate 3 distinct variants per position
- [ ] **validate_copy_constraints**: Enforce 125-char limit and AI detection
- [ ] **store_copy_database**: Save approved copy to PostgreSQL
- [ ] **submit_for_review**: Slack integration for human approval
- [ ] **push_to_instantly**: API integration for campaign setup
- [ ] **analyze_performance**: Performance analytics and learning

### Phase 3: Database Models (Day 2)
- [ ] Create SQLAlchemy models for all tables in spec
- [ ] Implement proper indexes and constraints
- [ ] Add migration script for schema creation
- [ ] Set up database connection and session management

### Phase 4: Error Handling & Validation (Day 2)
- [ ] Implement exponential backoff for Claude API retries
- [ ] Add rate limit detection and handling
- [ ] Create comprehensive error logging
- [ ] Implement graceful degradation strategies
- [ ] Add input validation for all tool inputs

### Phase 5: Testing (Day 2-3)
- [ ] Write unit tests for agent initialization
- [ ] Write unit tests for each tool function
- [ ] Test error handling scenarios
- [ ] Create integration tests for full workflow
- [ ] Add mock fixtures for external APIs
- [ ] Test database operations with testcontainers

### Phase 6: Performance & Monitoring (Day 3)
- [ ] Implement performance metrics collection
- [ ] Add token usage tracking
- [ ] Set up alerting for critical errors
- [ ] Optimize for <10s generation time
- [ ] Add caching for research data

## Acceptance Criteria

### Functional Requirements
- [ ] Generates 3-5 email sequences with 3 A/B variants each
- [ ] Enforces strict 125-character limit on ALL generated content
- [ ] Detects and prevents AI tell phrases with 95% accuracy
- [ ] Maintains ultra-human tone scoring ≥ 0.8
- [ ] Integrates with Claude API for content generation
- [ ] Submits all copy for human review via Slack
- [ ] Stores approved copy in database with full metadata
- [ ] Pushes approved sequences to Instantly API

### Technical Requirements
- [ ] All I/O operations are async
- [ ] Full type hints with mypy compliance
- [ ] Code coverage >90%
- [ ] Ruff linting passes with no errors
- [ ] Handles API failures gracefully with retries
- [ ] Implements proper logging with structured data
- [ ] Database migrations included and tested

### Performance Requirements
- [ ] Sequence generation < 10 seconds for 3-email sequence
- [ ] Single variant generation < 2 seconds
- [ ] Validation checks < 100ms
- [ ] Database operations < 500ms
- [ ] Supports up to 5 concurrent generations

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_campaign_copywriting.py -v --cov=src/agents/campaign_copywriting

# Run integration tests
pytest app/backend/__tests__/integration/test_campaign_copywriting_integration.py -v

# Type checking
mypy app/backend/src/agents/campaign_copywriting/

# Linting
ruff check app/backend/src/agents/campaign_copywriting/
ruff format app/backend/src/agents/campaign_copywriting/ --check

# Database migration
make migration name="add_email_copy_tables"

# Manual smoke test
python -c "
import asyncio
from src.agents.campaign_copywriting import CampaignCopywritingAgent

async def test():
    agent = CampaignCopywritingAgent()
    result = await agent.process_task({
        'type': 'generate_sequence',
        'campaign_name': 'Test',
        'niche_id': 'test-niche',
        'persona_id': 'test-persona',
        'offer_details': 'Test offer'
    })
    print(result)

asyncio.run(test())
"
```

## Key Implementation Notes

### Claude API Integration
- Use `anthropic.AsyncAnthropic` for async operations
- Implement rate limit handling with exponential backoff
- Track token usage for cost monitoring
- Use `claude-3-5-sonnet-20241022` model by default

### Character Limit Enforcement
- Check character count BEFORE returning from tools
- Implement auto-truncation with warning for violations
- Log all violations for quality monitoring

### AI Tell Detection
- Maintain list of 50+ common AI phrases
- Score content on AI-likeness (0-1 scale)
- Reject content with score > 0.3

### Human Review Workflow
- Use Slack API for approval notifications
- Include preview of all variants in notification
- Track review status and feedback
- Learn from approved/rejected patterns

### Database Schema
- Follow exact schema from spec
- Include all constraints and indexes
- Add proper foreign key relationships
- Create migrations for all tables

### Error Recovery
- Claude API failures: Retry with backoff, then fail gracefully
- Database failures: Log and continue with partial results
- Slack failures: Fallback to email notifications
- Validation failures: Return specific error messages

## Dependencies

### Required Python Packages (already in project)
- `anthropic>=0.75.0` - Claude API client
- `sqlalchemy>=2.0.0` - Database ORM
- `asyncpg>=0.31.0` - PostgreSQL async driver
- `httpx>=0.27.0` - HTTP client for API calls
- `pydantic>=2.12.5` - Data validation

### External Services
- Claude API key (ANTHROPIC_API_KEY)
- Instantly API key (INSTANTLY_API_KEY)
- Slack webhook (SLACK_WEBHOOK_URL)
- PostgreSQL connection (DATABASE_URL)

## References

- Specification: `specs/agents/campaign-copywriting.md`
- Base Agent: `app/backend/src/agents/base_agent.py`
- Integration Patterns: `app/backend/src/integrations/base.py`
- Database Examples: Check other model files in `app/backend/src/models/`
- Test Patterns: `app/backend/__tests__/fixtures/agent_fixtures.py`
