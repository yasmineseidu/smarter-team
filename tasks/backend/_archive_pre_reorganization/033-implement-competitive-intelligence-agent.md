# Task: Implement Competitive Intelligence Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/research-competitive-intelligence.md
**Created:** 2025-12-05

## Summary
Implement the Competitive Intelligence Agent that analyzes prospect communications for competitor mentions, pricing intelligence, feature comparisons, and win/loss reasons. The agent parses emails, call transcripts, and proposal feedback to generate structured competitive intelligence reports.

## Files to Create
- `app/backend/src/agents/research/competitive_intelligence.py`
- `app/backend/src/agents/research/tools/conversation_parser.py`
- `app/backend/src/agents/research/tools/intelligence_extractor.py`
- `app/backend/src/agents/research/tools/report_generator.py`
- `app/backend/src/models/competitive_intelligence.py`
- `app/backend/__tests__/unit/agents/test_competitive_intelligence.py`
- `app/backend/__tests__/integration/test_competitive_intelligence_integration.py`

## Implementation Checklist

### Database Schema
- [ ] Create competitors table with aliases support
- [ ] Create competitor_mentions table with full indexing
- [ ] Create competitive_pricing table for pricing intelligence
- [ ] Create competitive_features table for feature comparisons
- [ ] Create competitive_win_loss table for deal outcomes
- [ ] Write migration SQL file
- [ ] Add database indexes for performance

### Core Agent Implementation
- [ ] Create CompetitiveIntelligenceAgent class extending BaseAgent
- [ ] Implement system prompt with comprehensive instructions
- [ ] Register all required tools with proper schemas
- [ ] Add structured logging for all operations
- [ ] Implement error handling for all failure modes
- [ ] Add retry logic with exponential backoff

### Tool 1: Conversation Parser
- [ ] Implement parse_conversation_for_mentions tool
- [ ] Add fuzzy matching for competitor names
- [ ] Support competitor alias detection
- [ ] Handle email, call, and proposal text formats
- [ ] Extract context around mentions
- [ ] Add input validation and sanitization

### Tool 2: Intelligence Extractor
- [ ] Implement categorize_mentions tool
- [ ] Add pricing extraction with validation
- [ ] Implement feature comparison logic
- [ ] Add sentiment analysis capabilities
- [ ] Create win/loss reason classification
- [ ] Include confidence scoring for all extractions

### Tool 3: Database Operations
- [ ] Implement store_competitive_intelligence tool
- [ ] Add batch insert operations for performance
- [ ] Implement upsert logic for competitors
- [ ] Add transaction management
- [ ] Include proper foreign key handling

### Tool 4: Report Generator
- [ ] Implement generate_weekly_report tool
- [ ] Create executive summary generation
- [ ] Add competitor analysis aggregations
- [ ] Implement pricing trend analysis
- [ ] Add recommendation generation logic
- [ ] Include data quality metrics

### Database Models (SQLAlchemy)
- [ ] Create Competitor model with aliases field
- [ ] Create CompetitorMention model with relationships
- [ ] Create CompetitivePricing model with validation
- [ ] Create CompetitiveFeature model with comparison types
- [ ] Create CompetitiveWinLoss model with outcome tracking
- [ ] Add model methods for common queries

### Testing Suite
- [ ] Write unit tests for conversation parsing
- [ ] Write unit tests for intelligence extraction
- [ ] Write unit tests for database operations
- [ ] Write unit tests for report generation
- [ ] Create integration tests for end-to-end flow
- [ ] Add performance tests for load scenarios
- [ ] Include mock fixtures for test data

### Error Handling & Monitoring
- [ ] Add comprehensive error logging
- [ ] Implement circuit breaker for database failures
- [ ] Add metrics collection for monitoring
- [ ] Create alerting rules for failures
- [ ] Add data quality validation
- [ ] Implement PII redaction for privacy

### Performance Optimizations
- [ ] Add caching for competitor name mappings
- [ ] Implement batch processing for conversations
- [ ] Optimize database queries with proper indexes
- [ ] Add pagination for large result sets
- [ ] Include query performance monitoring

## Acceptance Criteria

### Functional Requirements
- [ ] Agent processes emails, calls, and proposal feedback accurately
- [ ] Competitor mentions detected with >95% precision
- [ ] Mentions categorized correctly >90% of the time
- [ ] Pricing intelligence extracted with currency/period validation
- [ ] Win/loss reasons tracked with evidence quotes
- [ ] Weekly reports generated automatically with actionable insights

### Non-Functional Requirements
- [ ] Single conversation processing: <2 seconds
- [ ] Batch processing (100 conversations): <30 seconds
- [ ] Weekly report generation: <10 seconds
- [ ] Unit test coverage >85%
- [ ] All database writes properly indexed
- [ ] Error handling covers all failure modes

### Integration Requirements
- [ ] Receives data from Response Handler Agent
- [ ] Processes call transcripts from Transcript Processor
- [ ] Provides competitive insights to Campaign Creation
- [ ] Stores all intelligence in Supabase PostgreSQL

## Dependencies
- Python 3.11+
- FastAPI 0.123.10
- SQLAlchemy 2.0 with asyncpg
- pytest 9.0.1 for testing
- anthropic 0.75.0 for Claude integration
- celery 5.6.0 for background tasks

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_competitive_intelligence.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_competitive_intelligence_integration.py -v

# Type checking
mypy app/backend/src/agents/research/competitive_intelligence.py

# Linting
ruff check app/backend/src/agents/research/competitive_intelligence.py

# Performance test
python -c "
from src.agents.research.competitive_intelligence import CompetitiveIntelligenceAgent
import time
agent = CompetitiveIntelligenceAgent()
start = time.time()
result = agent.process_task({'conversation_id': 'test', 'text': 'CompetitorX pricing'})
print(f'Processing time: {time.time() - start:.2f}s')
"

# Database migration
make migration name="create_competitive_intelligence_tables"

# Manual smoke test
python -c "
from src.agents.research.competitive_intelligence import CompetitiveIntelligenceAgent
agent = CompetitiveIntelligenceAgent()
print('✓ Competitive Intelligence Agent imports successfully')
print(f'✓ Agent name: {agent.name}')
print(f'✓ Agent description: {agent.description}')
print(f'✓ Tools registered: {len(agent.tools)}')
"
```

## Notes
- Follow existing agent patterns in the codebase
- Use structured logging via get_agent_logger()
- Implement async I/O operations throughout
- Include comprehensive type hints (mypy --strict)
- Follow project conventions for file organization and naming
