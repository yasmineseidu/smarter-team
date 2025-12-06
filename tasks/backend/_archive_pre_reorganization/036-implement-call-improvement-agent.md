# Task: Implement Call Improvement Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/proposal-call-improvement.md
**Created:** 2025-12-05

## Summary

Implement the Call Improvement Agent that analyzes sales call transcripts to provide coaching insights and track performance improvement. The agent evaluates calls based on talk time ratio, question quality, objection handling, and closing ability, generating actionable suggestions and maintaining historical trends.

## Files to Create

- `app/backend/src/agents/call_improvement/agent.py` - Main agent implementation
- `app/backend/src/agents/call_improvement/tools.py` - Tool functions
- `app/backend/src/agents/call_improvement/schemas.py` - Pydantic models
- `app/backend/src/agents/call_improvement/prompts.py` - System prompts
- `app/backend/src/agents/call_improvement/exceptions.py` - Custom exceptions
- `app/backend/__tests__/unit/agents/call_improvement/test_agent.py` - Unit tests
- `app/backend/__tests__/unit/agents/call_improvement/test_models.py` - Model tests
- `app/backend/__tests__/integration/test_call_improvement_workflow.py` - Integration tests
- `app/backend/__tests__/fixtures/call_improvement_fixtures.py` - Test fixtures

## Implementation Checklist

### Core Agent Implementation
- [ ] Create `CallImprovementAgent` class extending `BaseAgent`
- [ ] Register all 6 tools (calculate_call_score, store_call_score, create_improvement_suggestions, generate_weekly_coaching_report, send_coaching_email, track_improvement_progress)
- [ ] Implement `_analyze_call()` method for main workflow
- [ ] Implement `_extract_call_score()` using Claude API
- [ ] Implement `_check_weekly_report()` for Friday reports
- [ ] Implement `_generate_weekly_report()` and `_track_improvement()`
- [ ] Add comprehensive error handling with retry logic

### Database Integration
- [ ] Create SQL migrations for `call_scores`, `improvement_suggestions`, and `coaching_sessions` tables
- [ ] Implement database models using SQLAlchemy 2.0 async
- [ ] Add proper indexes for performance optimization
- [ ] Implement running average and trend calculation logic
- [ ] Add database connection handling with proper error recovery

### Tool Functions
- [ ] Implement `calculate_call_score()` with Claude API integration
- [ ] Implement `store_call_score()` with trend calculation
- [ ] Implement `create_improvement_suggestions()` with bulk insert
- [ ] Implement `generate_weekly_coaching_report()` with date range queries
- [ ] Implement `send_coaching_email()` integration (using existing email service)
- [ ] Implement `track_improvement_progress()` with score comparison

### Pydantic Schemas
- [ ] Create `TalkTimeAnalysis`, `QuestionAnalysis`, `ObjectionAnalysis`, `ClosingAnalysis`
- [ ] Create `CallScoreExtraction` with proper validation
- [ ] Create `ImprovementSuggestionCreate` and `CoachingReportData`
- [ ] Add custom validators for grade calculation
- [ ] Ensure all fields have proper constraints and descriptions

### Testing Suite
- [ ] Write unit tests for agent initialization
- [ ] Write unit tests for score calculation with various transcript types
- [ ] Write unit tests for grade calculation edge cases
- [ ] Write unit tests for trend analysis logic
- [ ] Write unit tests for all tool functions with mocked dependencies
- [ ] Write integration tests for end-to-end workflow
- [ ] Write integration tests for weekly report generation
- [ ] Create comprehensive fixtures for test scenarios
- [ ] Achieve >85% test coverage

### Performance & Monitoring
- [ ] Add structured logging with correlation IDs
- [ ] Implement performance metrics tracking
- [ ] Add database query optimization
- [ ] Configure caching for running averages
- [ ] Set up alert thresholds for analysis failures

## Acceptance Criteria

1. **Call Analysis**: Successfully analyzes transcripts and returns accurate scores (0-100) with proper breakdown
2. **Scoring Accuracy**: Talk time, questioning, objection handling, and closing scores match manual evaluation within ±5 points
3. **Grade Calculation**: Correct letter grades assigned based on score ranges (A+, A, B+, B, C, D, F)
4. **Improvement Suggestions**: Generates 2-5 actionable suggestions with specific examples and timestamps
5. **Trend Tracking**: Maintains running 10-call averages and detects improvement/stable/declining trends
6. **Weekly Reports**: Automatically generates and emails coaching reports every Friday
7. **Error Handling**: Gracefully handles malformed transcripts, API failures, and database errors
8. **Performance**: Analyzes calls within 30 seconds average processing time

## Database Schema Notes

### call_scores Table
- Store detailed scoring breakdowns (25 points each category)
- Track metrics like talk time ratio, question counts, objections handled
- Maintain running averages and trend indicators
- Link to transcripts, leads, and meetings

### improvement_suggestions Table
- Categorize suggestions (talk_time, questioning, objections, closing, general)
- Include priority levels and specific moments from transcript
- Track suggestion status through acknowledgment to mastery
- Link suggestions across multiple calls to track improvement

### coaching_sessions Table
- Weekly aggregation of call performance
- Track email engagement (sent, opened)
- Store top strengths and focus areas for the period
- Maintain unique constraint per rep per week

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/call_improvement/ -v --cov=app/backend/src/agents/call_improvement

# Run integration tests
pytest app/backend/__tests__/integration/test_call_improvement_workflow.py -v

# Type checking
mypy app/backend/src/agents/call_improvement/

# Linting
ruff check app/backend/src/agents/call_improvement/

# Format check
ruff format --check app/backend/src/agents/call_improvement/

# Manual test
python -c "from app.backend.src.agents.call_improvement.agent import CallImprovementAgent; print('Agent imports successfully')"

# Database migration
make migration name="create_call_improvement_tables"
make migrate
```

## Dependencies

- `anthropic>=0.75.0` - Claude API for transcript analysis
- `sqlalchemy>=2.0.44` - Database ORM with async support
- `pydantic>=2.12.5` - Data validation
- `tenacity>=8.2.0` - Retry logic for API calls
- Existing email service integration
- Existing BaseAgent class

## Integration Points

1. **Receives from**: Call Transcript Processor Agent (provides transcript_id and text)
2. **Triggers**: Response Check-in Agent (for coaching reminders)
3. **Database**: Reads from call_transcripts, writes to call_scores and improvement_suggestions
4. **Email Service**: Sends weekly coaching reports
