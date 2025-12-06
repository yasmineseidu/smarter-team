# Task: Implement Duplicate Detection Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/leadgen-duplicate-detection.md
**Created:** 2025-12-05
**Priority:** Phase 1 - MVP Foundation

## Summary

Implement the Duplicate Detection Agent to prevent duplicate leads using fuzzy matching algorithms. The agent will auto-merge exact matches (≥85% confidence) and flag potential duplicates (60-84% confidence) for human review. It must process >1,000 leads/minute with comprehensive audit logging.

## Files to Create

- `app/backend/src/agents/duplicate_detection.py` - Main agent implementation
- `app/backend/src/agents/tools/duplicate_tools.py` - Matching algorithm tools
- `app/backend/__tests__/unit/agents/test_duplicate_detection.py` - Unit tests
- `app/backend/__tests__/integration/test_duplicate_detection_integration.py` - Integration tests
- `app/backend/src/database/migrations/002_duplicate_tables.sql` - Database schema

## Implementation Checklist

### Core Agent Implementation
- [ ] Create `DuplicateDetectionAgent` class extending `BaseAgent`
- [ ] Implement system prompt with detailed matching algorithms
- [ ] Add `process_task()` method with task type routing
- [ ] Configure confidence thresholds (auto-merge: 0.85, review: 0.60)
- [ ] Implement weighted scoring system for different match types

### Database Tools
- [ ] Create `query_existing_leads()` tool with indexed queries
- [ ] Implement `merge_duplicate_records()` with union strategy
- [ ] Add `flag_for_human_review()` for review task creation
- [ ] Create database migrations for `duplicate_checks` and `merge_logs` tables
- [ ] Add proper indexes for performance (lead_id, check_date, confidence)

### Normalization Tools
- [ ] Implement `normalize_email()` with Gmail special handling
- [ ] Create `normalize_phone()` with E.164 formatting
- [ ] Add `normalize_linkedin_url()` for consistent LinkedIn matching
- [ ] Build `fuzzy_match_strings()` with multiple algorithms (Levenshtein, Jaro, difflib)

### Scoring Algorithm
- [ ] Implement `calculate_confidence_score()` with weighted averaging
- [ ] Add match type weights: email (0.35), name_company (0.30), linkedin (0.20), phone (0.15)
- [ ] Create confidence calculation with additive scoring for multiple matches
- [ ] Implement recommendation logic: merge/review/unique

### Error Handling & Retry Logic
- [ ] Add exponential backoff for database failures (max 3 retries)
- [ ] Implement graceful degradation for algorithm failures
- [ ] Add timeout handling (5s query limit, use cached results)
- [ ] Create comprehensive error logging with structured data

### Performance Optimization
- [ ] Implement batch processing (100-500 leads per batch)
- [ ] Add caching for recent comparisons (24-hour TTL)
- [ ] Optimize database queries with proper indexes
- [ ] Add performance monitoring (>1,000 leads/minute requirement)

### Audit Trail & Logging
- [ ] Log all duplicate checks to `duplicate_checks` table
- [ ] Record merge history in `merge_logs` with before/after snapshots
- [ ] Add structured logging with processing times and decisions
- [ ] Implement PII hashing for sensitive data in logs

### Testing Implementation
- [ ] Write unit tests for all normalization functions
- [ ] Create tests for fuzzy matching algorithms
- [ ] Build confidence scoring test cases
- [ ] Add performance tests for batch processing
- [ ] Create integration tests with mock database

## Database Schema Requirements

```sql
-- duplicate_checks table
CREATE TABLE duplicate_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    check_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    candidates JSONB NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    recommendation VARCHAR(20) NOT NULL,
    reasoning TEXT,
    algorithm_version VARCHAR(10) DEFAULT '1.0',
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- merge_logs table
CREATE TABLE merge_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_lead_id UUID NOT NULL REFERENCES leads(id),
    merged_lead_ids UUID[] NOT NULL,
    merge_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    merged_by VARCHAR(50) NOT NULL,
    fields_changed TEXT[],
    merge_strategy VARCHAR(20) DEFAULT 'union',
    pre_merge_data JSONB,
    post_merge_data JSONB,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Key Algorithms to Implement

### Email Normalization
```python
def normalize_email(email: str) -> dict:
    # Lowercase, remove Gmail dots, strip plus aliases
    # Return normalized, domain, is_valid, original
```

### Fuzzy Name + Company Matching
```python
def fuzzy_match_strings(string1: str, string2: str, threshold: float = 0.8) -> dict:
    # Use Levenshtein distance for 80%+ similarity
    # Return similarity, is_match, algorithm, details
```

### Confidence Scoring
```python
def calculate_confidence_score(matches: dict) -> dict:
    # Weighted scoring: email(0.35) + name_company(0.30) + linkedin(0.20) + phone(0.15)
    # Return overall confidence, match_details, recommendation, reasoning
```

## Acceptance Criteria

- [ ] Processes >1,000 leads/minute consistently
- [ ] Auto-merges exact duplicates (≥85% confidence)
- [ ] Flags 60-84% confidence matches for human review
- [ ] Maintains complete audit trail in both tables
- [ ] Handles concurrent duplicate detection without conflicts
- [ ] Preserves data integrity during merges (union strategy)
- [ ] Generates review tasks with full context
- [ ] Provides comprehensive metrics and logging
- [ ] Handles database failures gracefully with retries
- [ ] All unit tests pass (>85% coverage)
- [ ] Integration tests verify end-to-end flow
- [ ] Performance tests meet throughput requirements

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_duplicate_detection.py -v --cov=app/backend/src/agents/duplicate_detection

# Run integration tests
pytest app/backend/__tests__/integration/test_duplicate_detection_integration.py -v

# Type checking
mypy app/backend/src/agents/duplicate_detection.py

# Linting
ruff check app/backend/src/agents/duplicate_detection.py
ruff format app/backend/src/agents/duplicate_detection.py

# Database migrations
make migrate name="add_duplicate_detection_tables"

# Performance test
python -c "
import asyncio
from app.backend.src.agents.duplicate_detection import DuplicateDetectionAgent
# Test 1000 leads processing time
"

# Manual test
python -c "
from app.backend.src.agents.duplicate_detection import DuplicateDetectionAgent
from app.backend.src.config import settings
agent = DuplicateDetectionAgent(settings)
print(agent.system_prompt)
"
```

## Dependencies

- `python-Levenshtein` for fuzzy string matching
- `phonenumbers` for phone number normalization
- `sqlalchemy` async for database operations
- `pytest` for testing framework
- `pytest-asyncio` for async test support

## Notes

- Follow existing BaseAgent pattern from `app/backend/src/agents/base_agent.py`
- Use structured logging via `get_agent_logger()`
- Implement proper error handling with specific error types
- Ensure all database operations are async
- Add comprehensive docstrings for all public methods
- Follow project conventions: snake_case, type hints, line length 100
