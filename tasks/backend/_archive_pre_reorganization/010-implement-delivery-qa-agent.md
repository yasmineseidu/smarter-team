# Task: Implement Delivery QA Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/delivery-qa.md
**Created:** 2025-12-05

## Summary

Build the delivery_qa_agent to autonomously review all deliverables before client delivery. The agent runs comprehensive QA checklists, performs automated checks (links, spelling, placeholders), validates branding, and generates detailed QA reports with issue tracking. Integrates with delivery project manager for fixes and maintains QA history.

## Files to Create

- `app/backend/src/agents/delivery_qa_agent.py`
- `app/backend/src/agents/tools/link_checker.py`
- `app/backend/src/agents/tools/spell_checker.py`
- `app/backend/src/agents/tools/branding_validator.py`
- `app/backend/src/agents/tools/completeness_checker.py`
- `app/backend/src/agents/tools/screenshot_generator.py`
- `app/backend/__tests__/unit/agents/test_delivery_qa_agent.py`
- `app/backend/__tests__/integration/test_delivery_qa_integration.py`

## Database Migrations

Create migrations for:
- `qa_results` table
- `qa_issues` table
- `qa_checklists` table

## Implementation Checklist

### Core Agent Implementation
- [ ] Create `DeliveryQAAgent` class extending `BaseAgent`
- [ ] Implement system prompt for QA specialist role
- [ ] Set up configuration with timeouts and API settings
- [ ] Register all tools with proper schemas

### Tool Implementations
- [ ] **link_checker.py**: Headless browser link validation
  - Playwright integration for browser automation
  - Parallel link checking with timeouts
  - Handle different response codes and timeouts
- [ ] **spell_checker.py**: LanguageTool API integration
  - Context-aware spell checking
  - Grammar validation
  - Suggestion generation
- [ ] **branding_validator.py**: Brand guideline checking
  - Color validation (hex/RGB)
  - Font usage verification
  - Logo placement checking
- [ ] **completeness_checker.py**: Required items verification
  - Type-specific requirements
  - Missing item detection
  - Completeness scoring
- [ ] **screenshot_generator.py**: Browserless integration
  - Page screenshot capture
  - Mobile view verification
  - Image optimization checking

### Core Workflow
- [ ] Implement `run_automated_checks` method
- [ ] Implement `validate_branding` method
- [ ] Implement `check_completeness` method
- [ ] Implement `generate_qa_report` method
- [ ] Implement `request_fixes` handoff to delivery_project_manager

### Error Handling
- [ ] Network timeout handling with retries
- [ ] Rate limit handling with exponential backoff
- [ ] Graceful degradation when APIs unavailable
- [ ] Fallback behaviors for critical failures

### Database Integration
- [ ] Create SQLAlchemy models for QA tables
- [ ] Implement result storage and retrieval
- [ ] Add history tracking for patterns
- [ ] Client-specific requirements storage

### Performance Optimization
- [ ] Parallel execution of automated checks
- [ ] Configurable timeouts per check type
- [ ] Caching for repeated checks
- [ ] Batch processing for multiple pages

### Testing
- [ ] Unit tests for each tool (mock external APIs)
- [ ] Integration tests for full QA workflow
- [ ] Mock Playwright for link checking
- [ ] Mock LanguageTool API for spell check
- [ ] Test handoff to delivery_project_manager
- [ ] Test auto-approval logic
- [ ] Performance tests for timeout handling

### Documentation & Logging
- [ ] Structured logging with correlation IDs
- [ ] Metrics tracking for QA operations
- [ ] Error reporting for debugging
- [ ] API documentation for tool interfaces

## Acceptance Criteria

- [ ] All deliverable types supported (website, document, video, email, presentation, social)
- [ ] Automated checks complete within 5 minutes for typical website
- [ ] Critical issues always block delivery (approval_status = REJECTED)
- [ ] Quality scores calculated correctly (0-100 scale)
- [ ] Auto-approval works for scores >= threshold
- [ ] Handoff to delivery_project_manager includes all issue details
- [ ] Screenshot URLs expire after 7 days
- [ ] Client-specific QA rules enforced
- [ ] Mobile responsiveness testing accurate
- [ ] Pattern recognition stores recurring issues
- [ ] All tools handle errors gracefully
- [ ] Unit test coverage >90%
- [ ] Integration tests cover all workflows

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_delivery_qa_agent.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_delivery_qa_integration.py -v

# Type checking
mypy app/backend/src/agents/delivery_qa_agent.py

# Linting
ruff check app/backend/src/agents/delivery_qa_agent.py

# Test database migrations
make migrate

# Manual smoke test
python -c "
from app.backend.src.agents.delivery_qa_agent import DeliveryQAAgent
agent = DeliveryQAAgent()
print('Agent initialized successfully')
print(f'Version: {agent.__class__.__module__}')
"

# Test tool integrations
python -c "
import asyncio
from app.backend.src.agents.tools.link_checker import LinkChecker
checker = LinkChecker()
print('Link checker tool ready')
"

# Test end-to-end with mock data
python -c "
import asyncio
from app.backend.src.agents.delivery_qa_agent import DeliveryQAAgent
async def test():
    agent = DeliveryQAAgent()
    result = await agent.process_task({
        'deliverable_id': 'test-123',
        'deliverable_type': 'website',
        'delivery_url': 'https://example.com',
        'project_id': 'proj-123',
        'client_id': 'client-123'
    })
    print(f'Test result: {result.get(\"overall_status\")}')
asyncio.run(test())
"
```

## Dependencies to Add

```python
# pyproject.toml additions
dependencies = [
    # ... existing
    "playwright>=1.40.0",  # For headless browser automation
    "browserless>=0.5.0",  # For screenshot service
    "pillow>=10.0.0",      # For image processing
    "colorama>=0.4.6",     # For color validation
    "pygments>=2.16.0",    # For syntax highlighting in docs
]
```

## External Service Setup

1. **LanguageTool API**:
   - Sign up at https://languagetool.org/
   - Get API key for spell checking
   - Add `LANGUAGETOOL_API_KEY` to environment

2. **Browserless**:
   - Set up account at https://browserless.io/
   - Configure screenshot generation
   - Add `BROWSERLESS_API_KEY` to environment

3. **Playwright Browsers**:
   - Install browsers: `playwright install chromium`
   - Set up browser launch options for headless mode

## Known Challenges & Solutions

1. **Link Checking Timeouts**:
   - Solution: Implement parallel checking with individual timeouts
   - Set reasonable timeout per link (10 seconds)

2. **Spell Check API Limits**:
   - Solution: Use local fallback for basic spell checking
   - Implement exponential backoff for API calls

3. **Screenshot Storage**:
   - Solution: Use cloud storage with expiring URLs
   - Implement cleanup job for old screenshots

4. **Client Brand Variations**:
   - Solution: Store brand guidelines per client
   - Support multiple brand sets per client

## Time Estimate

- Core agent implementation: 4 hours
- Tool implementations: 8 hours (2 hours each)
- Database models & migrations: 2 hours
- Testing (unit + integration): 4 hours
- Error handling & edge cases: 2 hours
- Documentation & final polish: 2 hours

**Total: 22 hours**
