# Implement Waterfall Email Enrichment Agent

## Task Overview
Implement the Waterfall Email Enrichment Agent that finds valid emails for leads by trying multiple enrichment services in a cost-optimized sequence, with verification for all found emails.

## Priority
High - Phase 6 core enrichment functionality

## Files to Create/Modify

### 1. Agent Implementation
- **Create**: `app/backend/src/agents/leadgen_waterfall_enrichment/agent.py`
  - Implement WaterfallEmailEnrichmentAgent extending BaseAgent
  - Add system prompt from spec
  - Implement async process_task method
  - Register all 12 tools

### 2. Agent Tools
- **Create**: `app/backend/src/agents/leadgen_waterfall_enrichment/tools.py`
  - Implement all 12 tool functions with proper signatures
  - Add error handling and retries
  - Implement circuit breaker logic
  - Add cost tracking

### 3. Integration Clients
- **Create**: `app/backend/src/integrations/muraena.py`
- **Create**: `app/backend/src/integrations/tomba.py`
- **Create**: `app/backend/src/integrations/nimbler.py`
- **Create**: `app/backend/src/integrations/voila_norbert.py`
- **Create**: `app/backend/src/integrations/icypeas.py`
- **Create**: `app/backend/src/integrations/anymail_finder.py`
- **Create**: `app/backend/src/integrations/findymail.py`
- **Create**: `app/backend/src/integrations/reoon.py`
  - All extend BaseIntegrationClient
  - Implement service-specific API calls
  - Add rate limiting awareness

### 4. Schemas
- **Create**: `app/backend/src/agents/leadgen_waterfall_enrichment/schemas.py`
  - Pydantic models: EmailResult, VerificationResult, EnrichmentResult
  - Request/response models for API

### 5. Database Migration
- **Create**: `app/backend/alembic/versions/xxx_add_enrichment_tables.py`
  - Create all 4 tables: enrichment_attempts, enrichment_results, enrichment_costs, service_circuit_breakers
  - Add all indexes specified in spec

### 6. Tests
- **Create**: `app/backend/__tests__/unit/agents/test_leadgen_waterfall_enrichment.py`
  - Unit tests for agent class
  - Mock all external API calls
  - Test confidence score calculations
  - Test cost tracking logic

- **Create**: `app/backend/__tests__/integration/test_waterfall_enrichment_integration.py`
  - End-to-end waterfall test
  - Test database updates
  - Test circuit breaker behavior
  - Test error handling scenarios

### 7. Celery Task
- **Create**: `app/backend/src/tasks/enrichment_tasks.py`
  - Background task for async enrichment
  - Handle large batches of leads
  - Implement progress tracking

## Key Implementation Details

### Circuit Breaker Logic
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

### Cost Optimization
- Track running cost during waterfall
- Stop if cost exceeds 50% of budget without success
- Prefer services with historical success rates
- Log all costs to enrichment_costs table

### Confidence Score Calculation
```python
def calculate_confidence_score(source, verification_result, domain_match):
    base_scores = {
        "muraena": 0.90,
        "tomba": 0.88,
        "nimbler": 0.85,
        "voila_norbert": 0.82,
        "icypeas": 0.80,
        "anymail_finder": 0.78,
        "findymail": 0.75
    }

    score = base_scores.get(source, 0.70)
    if verification_result.status == "valid":
        score *= 0.95
    if domain_match:
        score += 0.05

    return min(score, 1.0)
```

### Error Handling
- Exponential backoff: 1s, 2s, 4s, 8s, 16s max
- Retry transient errors (network, rate limits)
- Don't retry permanent errors (4xx, auth)
- Log all failures with context

### Performance Optimization
- Use async/await for concurrent API calls
- Implement request timeouts (10s per service)
- Cache circuit breaker state in Redis
- Batch database writes

## Acceptance Criteria

### Functional Requirements
- [ ] Successfully enriches 65%+ of test leads
- [ ] Verifies all found emails with Reoon
- [ ] Stops waterfall on first successful verification
- [ ] Tracks all costs accurately
- [ ] Implements circuit breakers for all services
- [ ] Respects rate limits for all APIs

### Technical Requirements
- [ ] All tests pass (>90% code coverage)
- [ ] Linting and type checking pass
- [ ] Database migration runs successfully
- [ ] Circuit breaker persists state in Redis
- [ ] Average enrichment time < 60 seconds
- [ ] Average cost per successful enrichment < $0.75

### Documentation
- [ ] API documentation for all endpoints
- [ ] Integration guides for each service
- [ ] Performance benchmarks
- [ ] Troubleshooting guide

## Testing Checklist

### Unit Tests
- [ ] Agent initialization and setup
- [ ] Each tool function in isolation
- [ ] Confidence score calculation
- [ ] Cost tracking accuracy
- [ ] Circuit breaker state transitions
- [ ] Error handling for all scenarios

### Integration Tests
- [ ] Full waterfall flow
- [ ] Database updates
- [ ] Redis caching
- [ ] API client behavior
- [ ] Celery task execution

### Performance Tests
- [ ] Concurrent enrichment requests
- [ ] Rate limit handling
- [ ] Memory usage under load
- [ ] Database query optimization

## Dependencies
- Database migration must be applied first
- All API keys must be configured in environment
- Redis must be running for circuit breaker state
- Celery worker must be running for background tasks

## Time Estimate
2-3 days for full implementation including tests

## Notes
- Start with 2-3 services for initial testing
- Use test API keys where possible to reduce costs
- Monitor service quotas during development
- Consider adding a dry-run mode for testing
