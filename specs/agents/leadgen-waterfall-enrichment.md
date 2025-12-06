# Waterfall Email Enrichment Agent Specification

## Overview
The Waterfall Email Enrichment Agent finds valid email addresses for leads missing them by trying multiple enrichment services in sequence. Each found email is verified through Reoon before acceptance. The agent optimizes for cost-efficiency while maintaining high deliverability rates.

## Category
Lead Generation & Data

## Agent Classification
- **Type**: Data Enrichment Agent
- **Autonomy Level**: Fully autonomous
- **Execution Pattern**: Event-driven (triggered by invalid/missing emails)

## System Capabilities

### Core Tools

1. **enrich_lead_email** - Main waterfall enrichment orchestrator
   ```python
   async def enrich_lead_email(
       lead_id: str,
       max_cost_per_email: float = 2.00,
       timeout_seconds: int = 60
   ) -> EnrichmentResult
   ```

2. **search_muraena** - Try Muraena API for email finding
   ```python
   async def search_muraena(
       first_name: str,
       last_name: str,
       company_domain: str
   ) -> Optional[EmailResult]
   ```

3. **search_tomba** - Try Tomba API for email finding
   ```python
   async def search_tomba(
       first_name: str,
       last_name: str,
       company_domain: str
   ) -> Optional[EmailResult]
   ```

4. **search_nimbler** - Try Nimbler API for email finding
   ```python
   async def search_nimbler(
       first_name: str,
       last_name: str,
       company_domain: str
   ) -> Optional[EmailResult]
   ```

5. **search_voila_norbert** - Try Voila Norbert API
   ```python
   async def search_voila_norbert(
       first_name: str,
       last_name: str,
       company_domain: str
   ) -> Optional[EmailResult]
   ```

6. **search_icypeas** - Try Icypeas API for email finding
   ```python
   async def search_icypeas(
       first_name: str,
       last_name: str,
       company_domain: str
   ) -> Optional[EmailResult]
   ```

7. **search_anymail_finder** - Try Anymail Finder API
   ```python
   async def search_anymail_finder(
       first_name: str,
       last_name: str,
       company_domain: str
   ) -> Optional[EmailResult]
   ```

8. **search_findymail** - Try Findymail API for email finding
   ```python
   async def search_findymail(
       first_name: str,
       last_name: str,
       company_domain: str
   ) -> Optional[EmailResult]
   ```

9. **verify_email_reoon** - Verify found email with Reoon
   ```python
   async def verify_email_reoon(
       email: str
   ) -> VerificationResult
   ```

10. **calculate_confidence_score** - Calculate confidence based on source + verification
    ```python
    def calculate_confidence_score(
        source: str,
        verification_result: VerificationResult,
        domain_match: bool
    ) -> float
    ```

11. **track_enrichment_cost** - Track costs for ROI analysis
    ```python
    async def track_enrichment_cost(
        lead_id: str,
        service: str,
        cost: float,
        success: bool
    ) -> None
    ```

12. **update_lead_email** - Update lead with enriched email
    ```python
    async def update_lead_email(
        lead_id: str,
        email: str,
        confidence_score: float,
        source: str
    ) -> None
    ```

### System Prompt
```
You are the Waterfall Email Enrichment Agent, an expert at finding valid email addresses for business professionals.

Your core mission is to enrich leads with valid emails by trying multiple services in a cost-optimized sequence. You always verify found emails before accepting them.

Waterfall Priority (cost-optimized order):
1. Muraena ($0.10/lookup) → Verify with Reoon
2. Tomba ($0.15/lookup) → Verify with Reoon
3. Nimbler ($0.20/lookup) → Verify with Reoon
4. Voila Norbert ($0.25/lookup) → Verify with Reoon
5. Icypeas ($0.30/lookup) → Verify with Reoon
6. Anymail Finder ($0.35/lookup) → Verify with Reoon
7. Findymail ($0.40/lookup) → Verify with Reoon

Decision Rules:
- Stop after first successful verification
- Never exceed max_cost_per_email (default $2.00)
- Require 95%+ verification confidence to accept
- Log all attempts for cost tracking
- If email format is invalid, don't attempt verification
- If domain doesn't match company domain, reduce confidence by 30%

Cost Optimization:
- Track cost per successful enrichment
- Stop if accumulated cost > 50% of max budget without success
- Prefer services with historical success rates
- Implement circuit breaker for services with >50% failure rate

Error Handling:
- Implement exponential backoff: 1s, 2s, 4s, 8s, 16s max
- Circuit breaker: disable service after 5 consecutive failures
- Timeout each service call at 10 seconds
- Log all failures with detailed error context

You persist through failures to find valid emails while respecting cost constraints and maintaining high data quality.
```

## Database Schema

### Tables

#### `enrichment_attempts`
```sql
CREATE TABLE enrichment_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    service VARCHAR(50) NOT NULL,
    search_params JSONB NOT NULL, -- {first_name, last_name, company_domain}
    result_status VARCHAR(20) NOT NULL, -- success, failed, timeout, rate_limited
    found_email VARCHAR(255),
    cost DECIMAL(10,4) NOT NULL,
    error_message TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_enrichment_attempts_lead_id ON enrichment_attempts(lead_id);
CREATE INDEX idx_enrichment_attempts_service ON enrichment_attempts(service);
CREATE INDEX idx_enrichment_attempts_created_at ON enrichment_attempts(created_at);
```

#### `enrichment_results`
```sql
CREATE TABLE enrichment_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    email VARCHAR(255) NOT NULL,
    source_service VARCHAR(50) NOT NULL,
    verification_service VARCHAR(50) DEFAULT 'reoon',
    confidence_score DECIMAL(5,4) NOT NULL, -- 0.0000 to 1.0000
    is_verified BOOLEAN NOT NULL,
    verification_status VARCHAR(20), -- valid, invalid, risky, unknown
    total_cost DECIMAL(10,4) NOT NULL,
    attempts_count INTEGER NOT NULL,
    domain_match BOOLEAN NOT NULL,
    enriched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(lead_id)
);

CREATE INDEX idx_enrichment_results_lead_id ON enrichment_results(lead_id);
CREATE INDEX idx_enrichment_results_email ON enrichment_results(email);
CREATE INDEX idx_enrichment_results_confidence ON enrichment_results(confidence_score);
```

#### `enrichment_costs`
```sql
CREATE TABLE enrichment_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    successes INTEGER NOT NULL DEFAULT 0,
    total_cost DECIMAL(10,4) NOT NULL DEFAULT 0,
    avg_cost_per_success DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(service, date)
);

CREATE INDEX idx_enrichment_costs_service_date ON enrichment_costs(service, date);
```

#### `service_circuit_breakers`
```sql
CREATE TABLE service_circuit_breakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(50) NOT NULL UNIQUE,
    is_open BOOLEAN NOT NULL DEFAULT FALSE,
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    opens_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Integration Specifications

### Email Enrichment Services

1. **Muraena** (`https://api.muraena.ai`)
   - Auth: Bearer token
   - Endpoint: `/search/email`
   - Cost: $0.10 per lookup
   - Rate: 100 req/min
   - Response format: `{"email": "...", "confidence": 0.95}`

2. **Tomba** (`https://api.tomba.io`)
   - Auth: Bearer token
   - Endpoint: `/v1/email-finder`
   - Cost: $0.15 per lookup
   - Rate: 60 req/min
   - Response format: `{"email": "...", "score": 85}`

3. **Nimbler** (`https://api.nimbler.com`)
   - Auth: Bearer token
   - Endpoint: `/v1/find-email`
   - Cost: $0.20 per lookup
   - Rate: 50 req/min

4. **Voila Norbert** (`https://api.voilanorbert.com`)
   - Auth: Bearer token
   - Endpoint: `/v1/find-email`
   - Cost: $0.25 per lookup
   - Rate: 40 req/min

5. **Icypeas** (`https://api.icypeas.com`)
   - Auth: Bearer token
   - Endpoint: `/v1/email-finder`
   - Cost: $0.30 per lookup
   - Rate: 30 req/min

6. **Anymail Finder** (`https://api.anymail.finder`)
   - Auth: Bearer token
   - Endpoint: `/v1/search`
   - Cost: $0.35 per lookup
   - Rate: 25 req/min

7. **Findymail** (`https://api.findymail.com`)
   - Auth: Bearer token
   - Endpoint: `/v1/email-finder`
   - Cost: $0.40 per lookup
   - Rate: 20 req/min

### Email Verification Service

**Reoon** (`https://api.reoon.email`)
- Auth: Bearer token
- Endpoint: `/v1/verify`
- Cost: $0.01 per verification
- Rate: 1000 req/min
- Response format: `{"email": "...", "status": "valid", "score": 0.98}`

## Performance Requirements

1. **Latency**: Complete waterfall within 60 seconds
2. **Success Rate**: Minimum 65% enrichment success rate
3. **Verification Accuracy**: 99%+ verification accuracy
4. **Cost Efficiency**: Average cost < $0.75 per successful enrichment
5. **Throughput**: Process 100 leads per minute concurrently

## Error Handling Strategy

### Retry Logic
```python
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 16.0  # seconds
```

### Circuit Breaker Configuration
- Failure threshold: 5 consecutive failures
- Timeout duration: 5 minutes before retry
- Half-open retries: 3 requests to test recovery

### Error Categories
1. **Transient Errors**: Rate limits, timeouts, network issues (retry)
2. **Permanent Errors**: Invalid credentials, 4xx errors (no retry)
3. **Service Errors**: 5xx errors (retry with circuit breaker)

## Testing Strategy

### Unit Tests
- Test each tool function independently
- Mock external API responses
- Verify confidence score calculations
- Test cost tracking accuracy

### Integration Tests
- Test waterfall flow end-to-end
- Verify database updates
- Test error handling scenarios
- Validate circuit breaker behavior

### Performance Tests
- Benchmark waterfall completion time
- Test concurrent enrichment requests
- Measure cost per successful enrichment
- Validate rate limiting compliance

### Mock Scenarios
1. All services fail (verify graceful degradation)
2. First service succeeds (verify early termination)
3. Verification fails (verify rejection logic)
4. Circuit breaker opens (verify service skipping)
5. Rate limit hit (verify backoff logic)

## Monitoring & Analytics

### Key Metrics
- Enrichment success rate by service
- Average cost per successful enrichment
- Verification accuracy by source
- Waterfall completion time distribution
- Circuit breaker events

### Alerts
- Success rate drops below 50%
- Average cost exceeds $1.00 per email
- Circuit breaker opens for primary services
- Verification accuracy drops below 95%

## Security Considerations

1. **API Keys**: Encrypt stored API keys
2. **Rate Limits**: Respect all service rate limits
3. **Data Privacy**: Hash email addresses for logging
4. **Access Control**: Restrict enrichment to authorized users
5. **Audit Trail**: Log all enrichment attempts

## Configuration

### Environment Variables
```bash
# API Keys
MURAENA_API_KEY=
TOMBA_API_KEY=
NIMBLER_API_KEY=
VOILA_NORBERT_API_KEY=
ICYPEAS_API_KEY=
ANYMAIL_FINDER_API_KEY=
FINDYMAIL_API_KEY=
REOON_API_KEY=

# Agent Settings
ENRICHMENT_MAX_COST_PER_EMAIL=2.00
ENRICHMENT_TIMEOUT_SECONDS=60
ENRICHMENT_MAX_CONCURRENT=10
ENRICHMENT_CIRCUIT_BREAKER_THRESHOLD=5
```

### Service Priority Configuration
```python
ENRICHMENT_WATERFALL = [
    {"service": "muraena", "cost": 0.10, "priority": 1},
    {"service": "tomba", "cost": 0.15, "priority": 2},
    {"service": "nimbler", "cost": 0.20, "priority": 3},
    {"service": "voila_norbert", "cost": 0.25, "priority": 4},
    {"service": "icypeas", "cost": 0.30, "priority": 5},
    {"service": "anymail_finder", "cost": 0.35, "priority": 6},
    {"service": "findymail", "cost": 0.40, "priority": 7},
]
```

## Dependencies

### Internal Dependencies
- BaseAgent class
- Database models (leads, enrichment_* tables)
- Integration clients for all services
- Celery task queue

### External Dependencies
- FastAPI for webhooks
- SQLAlchemy 2.0 for database
- httpx for HTTP requests
- pydantic for data validation
- Redis for caching circuit breaker state

## Agent Handoffs

1. **Email Verification Agent** - When enriched email needs verification
2. **Lead Data Validation Agent** - After successful enrichment
3. **Cost Tracking Agent** - For cost analysis and optimization

## Triggers

1. **Webhook**: `/webhooks/email-invalid` - When email marked invalid
2. **Scheduled**: Daily check for leads without emails
3. **Manual**: API endpoint `/api/agents/enrich-email`
4. **Event**: Lead created without email

## Expected Outputs

1. **Primary**: Updated lead record with valid email
2. **Secondary**: Enrichment attempt logs
3. **Analytics**: Cost tracking data
4. **Audit**: Complete trail of all attempts

## Success Criteria

- 65%+ enrichment success rate
- < $0.75 average cost per successful enrichment
- 99%+ verification accuracy
- < 60 seconds average waterfall time
- Zero duplicate enrichments per lead
