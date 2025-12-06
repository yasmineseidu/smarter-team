# Task: Implement QuickBooks Client

**Status:** Pending
**Domain:** backend
**Source:** .env.example + BaseIntegrationClient pattern
**Created:** 2025-12-06

## Summary

Create integration client for QuickBooks extending BaseIntegrationClient with Accounting and financial record management.

## Integration Details

**Category:** Payments & Finance
**Base URL:** https://quickbooks.api.intuit.com/v3
**Authentication:** OAuth 2.0
**Documentation:** https://developer.intuit.com/app/developer/qbo/docs/api
**Special:** OAuth 2.0 flow - requires QUICKBOOKS_CLIENT_ID, QUICKBOOKS_CLIENT_SECRET, realm_id

## Files to Create/Modify

- [ ] `app/backend/src/integrations/quickbooks.py`
- [ ] `app/backend/__tests__/unit/integrations/test_quickbooks.py`
- [ ] `app/backend/__tests__/fixtures/quickbooks_fixtures.py`
- [ ] Update `app/backend/src/integrations/__init__.py` to export new client

## Implementation Checklist

### Phase 1: Client Class Setup
- [ ] Create `QuickBooksClient` class extending `BaseIntegrationClient`
- [ ] Initialize with API key from `QUICKBOOKS_CLIENT_ID` environment variable
- [ ] Set base URL to `https://quickbooks.api.intuit.com/v3`
- [ ] Set timeout to 30.0 seconds
- [ ] Add structured logging

### Phase 2: Core Methods
- [ ] `create_invoice(customer_ref: str, line_items: list[dict], **kwargs) -> dict - Create invoice`
- [ ] `create_customer(name: str, **kwargs) -> dict - Create customer`
- [ ] `create_payment(customer_ref: str, amount: float, **kwargs) -> dict - Record payment`
- [ ] `query_invoices(query: str) -> list[dict] - Query invoices`
- [ ] `get_company_info() -> dict - Get company details`
- [ ] Add request/response type hints
- [ ] Include docstrings with examples

### Phase 3: Error Handling
- [ ] Add `QuickBooksAPIError` exception class
- [ ] Implement retry logic for transient errors (max 3 retries)
- [ ] Handle rate limiting
- [ ] Log errors with context

### Phase 4: Testing
- [ ] Write unit tests for all methods
- [ ] Mock API responses
- [ ] Test error scenarios (401, 429, invalid requests)
- [ ] Achieve >90% coverage

### Phase 5: Documentation
- [ ] Add usage examples in docstrings
- [ ] Document authentication setup
- [ ] List key features and capabilities
- [ ] Note rate limits and best practices

### Phase 6: Quality Gates
- [ ] Run `make lint` - no errors
- [ ] Run `make typecheck` - no errors
- [ ] Run `make test` - >90% coverage
- [ ] Verify integration with actual API (manual test)

## Verification

```bash
# Run tests
cd app/backend
pytest __tests__/unit/integrations/test_quickbooks.py -v

# Check coverage
pytest --cov=src/integrations/quickbooks --cov-report=term-missing

# Quality checks
make check
```

## Notes

- Extends `BaseIntegrationClient` from `src/integrations/base.py`
- Uses `get_agent_logger()` for structured logging
- API key loaded from environment: `QUICKBOOKS_CLIENT_ID`
- **Special**: OAuth 2.0 flow - requires QUICKBOOKS_CLIENT_ID, QUICKBOOKS_CLIENT_SECRET, realm_id
- Primary use case: Accounting and financial record management
- See https://developer.intuit.com/app/developer/qbo/docs/api for full API reference
