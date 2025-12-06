# Task: Implement Retention Upsell Detector Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/retention-upsell-detector.md
**Created:** 2025-12-05
**Agent Category:** Client Success & Retention

## Summary

Implement the Upsell Detector Agent that proactively identifies expansion opportunities by analyzing multiple signals across client interactions, satisfaction levels, project success, and company growth indicators. The agent will score opportunities on a 0-100 scale, generate AI-powered recommendations, and create personalized outreach templates.

## Files to Create

### Core Agent Implementation
- `app/backend/src/agents/retention/upsell_detector.py` - Main agent class
- `app/backend/src/agents/retention/__init__.py` - Package exports
- `app/backend/src/agents/retention/tools.py` - Tool functions (7 tools)
- `app/backend/src/agents/retention/prompts.py` - System and user prompts
- `app/backend/src/agents/retention/schemas.py` - Pydantic models
- `app/backend/src/agents/retention/exceptions.py` - Custom exceptions

### Database Migration
- `app/backend/alembic/versions/create_upsell_opportunities_tables.py` - Migration for database schema

### Tasks/Celery
- `app/backend/src/tasks/retention_tasks.py` - Daily analysis cron job
- `app/backend/src/tasks/signal_processing_tasks.py` - Real-time signal processing

### Tests
- `app/backend/__tests__/unit/agents/retention/test_upsell_detector.py` - Unit tests
- `app/backend/__tests__/unit/agents/retention/test_tools.py` - Tool tests
- `app/backend/__tests__/integration/retention/test_upsell_detector_integration.py` - Integration tests
- `app/backend/__tests__/fixtures/retention_fixtures.py` - Test fixtures

## Implementation Checklist

### 1. Database Schema (Priority: High)
- [ ] Create `upsell_opportunities` table with all columns and indexes
- [ ] Create `upsell_signals` table with all columns and indexes
- [ ] Add foreign key constraints
- [ ] Create database migration file
- [ ] Test migration with sample data

### 2. Agent Class (Priority: High)
- [ ] Create UpsellDetectorAgent class extending BaseAgent
- [ ] Implement system_prompt property
- [ ] Implement process_task method
- [ ] Add agent registration
- [ ] Configure agent with UpsellDetectorConfig

### 3. Tool Implementation (Priority: High)
- [ ] Implement `analyze_conversation_signals` tool
  - Conversation analysis API integration
  - Keyword/phrase detection logic
  - Signal extraction and scoring
- [ ] Implement `evaluate_satisfaction_signals` tool
  - Survey data retrieval
  - Score calculation and trend analysis
  - Satisfaction scoring logic
- [ ] Implement `assess_project_success` tool
  - Project metrics retrieval
  - Success criteria evaluation
  - Scoring algorithm
- [ ] Implement `analyze_company_growth` tool
  - Company research data integration
  - Growth signal detection
  - Signal type classification
- [ ] Implement `calculate_relationship_tenure` tool
  - Client history analysis
  - Tenure calculation
  - Engagement scoring
- [ ] Implement `generate_upsell_recommendation` tool
  - AI model integration for analysis
  - Service matching logic
  - Confidence scoring
- [ ] Implement `create_outreach_template` tool
  - Template generation for different scenarios
  - Personalization logic
  - Merge field handling

### 4. Error Handling (Priority: Medium)
- [ ] Implement error handling for all tools
- [ ] Add retry logic with exponential backoff
- [ ] Implement graceful degradation strategies
- [ ] Add comprehensive logging
- [ ] Create custom exception classes

### 5. Integration Points (Priority: High)
- [ ] Integration with Conversation Intelligence Agent
- [ ] Integration with Satisfaction Survey Agent
- [ ] Integration with Company Research Agent
- [ ] Integration with Project Management Agent
- [ ] Outbound integration with Campaign Send Agent
- [ ] Outbound integration with Meeting Scheduler Agent

### 6. Scheduled Tasks (Priority: Medium)
- [ ] Implement daily upsell analysis cron job
- [ ] Implement real-time signal processing task
- [ ] Add Celery task definitions
- [ ] Configure scheduling with Celery Beat
- [ ] Add task monitoring and alerting

### 7. Testing (Priority: High)
- [ ] Write unit tests for all tools
- [ ] Write unit tests for agent class
- [ ] Write integration tests for end-to-end flow
- [ ] Create mock data fixtures
- [ ] Test error handling scenarios
- [ ] Performance tests for batch processing

### 8. Configuration & Deployment (Priority: Medium)
- [ ] Add configuration settings
- [ ] Update environment variables documentation
- [ ] Add logging configuration
- [ ] Update API documentation
- [ ] Deploy database migrations

## Acceptance Criteria

### Functional Requirements
- [ ] Agent detects all 5 signal types correctly
- [ ] Opportunity scoring produces accurate 0-100 scale
- [ ] AI recommendations match services to client needs
- [ ] Outreach templates are personalized and professional
- [ ] Daily batch processing completes within 30 minutes for 500 clients
- [ ] Real-time signal processing completes within 5 seconds
- [ ] Human approval workflow prevents unauthorized outreach

### Technical Requirements
- [ ] All database tables created with proper indexes
- [ ] Error handling covers all failure scenarios
- [ ] Integration with dependent agents works correctly
- [ ] Test coverage exceeds 90%
- [ ] Performance meets all SLA requirements
- [ ] Security controls protect client data
- [ ] Metrics and logging provide full observability

### Integration Requirements
- [ ] Conversation Intelligence integration working
- [ ] Satisfaction Survey data retrieval working
- [ ] Company Research integration working
- [ ] Project Management data access working
- [ ] Outbound handoffs to Campaign and Meeting agents working

## Implementation Notes

### Dependencies
- Ensure dependent agents are implemented or mocked
- Database access through SQLAlchemy async
- Claude AI integration via Anthropic SDK
- Redis for caching and Celery backend
- Supabase PostgreSQL as primary database

### Performance Considerations
- Batch process clients in groups of 20
- Cache company research data for 7 days
- Cache survey data for 30 days
- Use database indexes for all query patterns
- Implement connection pooling

### Security Notes
- All client data encrypted at rest
- API keys stored in environment variables
- Rate limiting on external API calls
- Input validation on all parameters
- Audit trail for opportunity modifications

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/retention/ -v --cov=app/backend/src/agents/retention

# Run integration tests
pytest app/backend/__tests__/integration/retention/ -v

# Type checking
mypy app/backend/src/agents/retention/

# Linting
ruff check app/backend/src/agents/retention/

# Database migration
cd app/backend && alembic upgrade head

# Test agent import
python -c "from app.backend.src.agents.retention.upsell_detector import UpsellDetectorAgent; print('Agent import successful')"
```

## Estimated Timeline

- **Database Schema:** 4 hours
- **Agent Core Implementation:** 8 hours
- **Tool Implementation:** 20 hours (7 tools × ~3 hours each)
- **Error Handling & Integration:** 6 hours
- **Testing Suite:** 12 hours
- **Configuration & Deployment:** 4 hours
- **Code Review & Refinement:** 4 hours

**Total Estimated:** 58 hours (~7-8 working days)
