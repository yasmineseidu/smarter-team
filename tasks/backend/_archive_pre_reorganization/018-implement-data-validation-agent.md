# Task: Implement Data Validation Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/leadgen-data-validation.md
**Created:** 2025-12-05

## Summary

Implement the Data Validation Agent that ensures lead data quality before campaign enrollment. The agent applies comprehensive validation rules, generates detailed reports, blocks invalid leads, and routes incomplete leads to appropriate enrichment agents.

## Files to Create

### Core Implementation
- `app/backend/src/agents/data_validation/__init__.py`
- `app/backend/src/agents/data_validation/agent.py`
- `app/backend/src/agents/data_validation/tools.py`
- `app/backend/src/agents/data_validation/schemas.py`
- `app/backend/src/agents/data_validation/exceptions.py`

### Database
- `app/backend/src/models/validation.py` - Validation logs and rules tables
- `app/backend/migrations/versions/XXXX_add_validation_tables.py`

### Tests
- `app/backend/__tests__/unit/agents/test_data_validation.py`
- `app/backend/__tests__/integration/test_data_validation_integration.py`

## Implementation Checklist

### 1. Project Structure
- [ ] Create data validation agent directory structure
- [ ] Set up `__init__.py` with proper exports
- [ ] Create package-level documentation

### 2. Schemas and Models
- [ ] Implement `LeadData`, `ValidationResult`, `ValidationReport` Pydantic models
- [ ] Create SQLAlchemy models for `validation_logs` and `validation_rules` tables
- [ ] Add database migration for validation tables
- [ ] Implement field validation rules and enums

### 3. Core Agent Implementation
- [ ] Implement `DataValidationAgent` class extending `BaseAgent`
- [ ] Add system prompt with comprehensive validation logic
- [ ] Implement `process_task` method with task routing
- [ ] Add configuration initialization with batch size settings

### 4. Validation Logic
- [ ] Implement `_validate_lead` method with all validation rules:
  - First name validation (required, not placeholder)
  - Company name validation (required, minimum length)
  - Email validation with verification status checking
  - Domain-company matching with fuzzy logic
  - LinkedIn URL format validation
  - Job title presence checking
- [ ] Implement scoring algorithm with rule weights
- [ ] Add status determination logic (VALID, VALID_WITH_FLAGS, etc.)
- [ ] Implement placeholder detection patterns

### 5. Batch Processing
- [ ] Implement `_validate_batch` with parallel processing
- [ ] Add batch size management and error handling
- [ ] Implement partial failure recovery
- [ ] Add batch report generation

### 6. Enrichment Routing
- [ ] Implement `_route_for_enrichment` with target agent determination
- [ ] Add priority calculation based on missing fields
- [ ] Implement handoff payload construction
- [ ] Add enrichment type mapping logic

### 7. Database Integration
- [ ] Implement validation log persistence
- [ ] Add validation rule storage and retrieval
- [ ] Implement audit trail functionality
- [ ] Add database transaction handling

### 8. Tool Implementation
- [ ] Implement `validate_lead_data` tool with full schema validation
- [ ] Implement `validate_batch_leads` with parallel processing
- [ ] Implement `update_validation_rules` for dynamic rule updates
- [ ] Add comprehensive error handling for all tools

### 9. Error Handling
- [ ] Implement retry logic for database failures
- [ ] Add graceful degradation for external service failures
- [ ] Implement dead-letter queue for persistent failures
- [ ] Add detailed error logging with context

### 10. Performance Optimization
- [ ] Implement caching for validation patterns
- [ ] Add parallel processing with asyncio.gather
- [ ] Optimize database queries with bulk operations
- [ ] Implement connection pooling

### 11. Logging and Monitoring
- [ ] Add structured logging for all validation actions
- [ ] Implement metrics collection for validation scores
- [ ] Add performance timing for validations
- [ ] Create health check endpoint

### 12. Testing
- [ ] Write unit tests for all validation rules
- [ ] Add tests for batch processing scenarios
- [ ] Implement integration tests for enrichment handoffs
- [ ] Add performance tests for batch validation
- [ ] Create tests for error handling scenarios
- [ ] Add tests for database operations
- [ ] Mock external dependencies properly
- [ ] Achieve >90% test coverage

### 13. Documentation
- [ ] Add inline documentation for all methods
- [ ] Create README for the agent package
- [ ] Document validation rules and scoring logic
- [ ] Add examples for common usage patterns

### 14. Integration
- [ ] Register agent in agent registry
- [ ] Add Celery tasks for background validation
- [ ] Configure API endpoints if needed
- [ ] Add to deployment configuration

## Acceptance Criteria

From spec/agents/leadgen-data-validation.md:

- [ ] Lead validation completes within 50ms for single leads
- [ ] Batch validation processes 500 leads in under 5 seconds
- [ ] All validation rules are enforced with correct scoring
- [ ] Invalid/risky leads are blocked from campaigns
- [ ] Leads requiring enrichment are routed with correct priority
- [ ] Validation reports include detailed failure reasons
- [ ] All validation decisions are logged for audit
- [ ] System handles parallel validation without data corruption
- [ ] Validation rules can be updated without code deployment
- [ ] Unit test coverage >90% for agent logic
- [ ] Integration tests cover all handoff scenarios
- [ ] Performance benchmarks met under load
- [ ] Security requirements implemented (PII masking, audit logs)
- [ ] Monitoring and alerting configured for all critical metrics

## Technical Requirements

### Dependencies
- Claude Agent SDK
- SQLAlchemy 2.0 with async support
- Pydantic v2 for data validation
- AsyncIO for parallel processing
- Redis for caching (if implemented)

### Performance
- Single validation: <50ms
- Batch validation: <5s for 500 leads
- Memory usage: <50MB base + 1KB per lead
- Concurrent validations: Support 100+ parallel

### Quality
- Type hints for all methods
- Async/await for all I/O operations
- Comprehensive error handling
- Structured logging with context
- Database transactions for consistency

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_data_validation.py -v --cov=app/backend/src/agents/data_validation

# Run integration tests
pytest app/backend/__tests__/integration/test_data_validation_integration.py -v

# Type checking
mypy app/backend/src/agents/data_validation/

# Linting
ruff check app/backend/src/agents/data_validation/

# Performance test (create a test script)
python -m tests.performance.test_validation_performance

# Manual test
python -c "
from app.backend.src.agents.data_validation.agent import DataValidationAgent
from app.backend.src.config import Settings
import asyncio

async def test():
    agent = DataValidationAgent(Settings())
    lead = {
        'id': 'test-123',
        'first_name': 'John',
        'company_name': 'TechCorp',
        'email': 'john@techcorp.com',
        'verification_status': 'SAFE'
    }
    result = await agent.process_task({'type': 'validate_single', 'lead': lead})
    print(result)

asyncio.run(test())
"
```

## Dependencies

This task depends on:
- BaseAgent class implementation (complete)
- Database connection setup (complete)
- Celery task infrastructure (complete)
- Enrichment agents (for handoff testing)

## Notes

1. Focus on implementing the validation scoring algorithm correctly - it's critical for lead routing decisions
2. Ensure comprehensive logging for audit compliance
3. Test parallel processing thoroughly to avoid race conditions
4. Implement proper PII handling in logs
5. Consider adding a dry-run mode for testing validation rules without side effects
