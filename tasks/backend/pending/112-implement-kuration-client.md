# Task: Implement Kuration AI Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for Kuration AI extending BaseIntegrationClient with B2B data and company intelligence capabilities.

## Integration Details

**Category:** Search & Research
**Base URL:** https://api.kuration.ai/v1
**Authentication:** Bearer Token (API Key)
**Documentation:** https://docs.kuration.ai
**Rate Limits:** Varies by plan

## Files to Create/Modify

- [ ] `app/backend/src/integrations/kuration.py`
- [ ] `app/backend/__tests__/unit/integrations/test_kuration.py`
- [ ] `app/backend/__tests__/fixtures/kuration_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `KurationClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `KURATION_API_KEY` environment variable
- [ ] Set base URL to `https://api.kuration.ai/v1`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `search_companies(query: str, **kwargs) -> dict` - Search for companies
- [ ] `get_company(company_id: str) -> dict` - Get company details
- [ ] `enrich_company(domain: str) -> dict` - Enrich company data by domain
- [ ] `search_people(company_id: str, **kwargs) -> dict` - Find people at company
- [ ] `get_person(person_id: str) -> dict` - Get person details
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `KurationAPIError` exception class
- [ ] Add `KurationNotFoundError` exception class for missing data
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting
- [ ] Log errors with context (company_id, domain, query)

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses for companies, people
- [ ] Test error scenarios (404 not found, 429 rate limit)
- [ ] Test data enrichment flow
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List available filters (industry, size, location)
- [ ] Note data freshness and accuracy
- [ ] Document use cases (lead enrichment, company research)

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## API Methods to Implement

```python
async def search_companies(
    self,
    query: str,
    industry: str | None = None,
    employee_range: str | None = None,
    location: str | None = None,
    limit: int = 20
) -> dict[str, Any]:
    """
    Search for companies.

    Args:
        query: Company name or keyword
        industry: Industry filter
        employee_range: Employee count range (1-10, 11-50, etc.)
        location: Location filter
        limit: Number of results

    Returns:
        Matching companies with basic info
    """

async def enrich_company(self, domain: str) -> dict[str, Any]:
    """
    Enrich company data by domain.

    Args:
        domain: Company website domain

    Returns:
        Enriched company data (size, industry, tech stack, etc.)
    """

async def search_people(
    self,
    company_id: str,
    role: str | None = None,
    seniority: str | None = None,
    limit: int = 20
) -> dict[str, Any]:
    """
    Find people at a company.

    Args:
        company_id: Company ID
        role: Job role filter (engineering, sales, etc.)
        seniority: Seniority level (c-level, vp, director, etc.)
        limit: Number of results

    Returns:
        People with contact info and titles
    """
```

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_kuration.py -v

# Check coverage
pytest --cov=src/integrations/kuration --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `KURATION_API_KEY`
- Primary use case: Company research, lead enrichment, B2B data
- See https://docs.kuration.ai for full API reference
