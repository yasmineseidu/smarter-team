# Task: Implement Payment Processing Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/payment-processing.md
**Created:** 2025-12-05
**Estimated Effort:** 40-60 hours

## Summary
Implement a production-ready Payment Processing Agent that securely handles Stripe webhook events, updates payment records, synchronizes with QuickBooks, sends notifications, and manages disputes. The agent processes payment successes, failures, and chargebacks with comprehensive error handling, audit trails, and multi-agent coordination.

## Files to Create
- `app/backend/src/agents/payment_processing.py` - Main agent implementation
- `app/backend/src/agents/tools/payment_tools.py` - Payment-specific tools
- `app/backend/src/integrations/stripe_client.py` - Stripe integration client
- `app/backend/src/integrations/quickbooks_client.py` - QuickBooks integration client
- `app/backend/src/models/payment.py` - Database models
- `app/backend/src/webhooks/stripe.py` - Stripe webhook endpoints
- `app/backend/__tests__/unit/agents/test_payment_processing.py` - Unit tests
- `app/backend/__tests__/unit/agents/test_payment_tools.py` - Tool tests
- `app/backend/__tests__/integration/test_payment_processing_integration.py` - Integration tests
- `app/backend/__tests__/fixtures/payment_fixtures.py` - Test fixtures

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Create payment database models (Payment, PaymentEvent, PaymentFailure, Dispute)
- [ ] Implement StripeClient integration with webhook signature verification
- [ ] Implement QuickBooksClient with authentication and retry logic
- [ ] Create PaymentProcessingAgent class extending BaseAgent
- [ ] Implement basic webhook event processing pipeline

### Phase 2: Webhook Processing
- [ ] Implement `verify_webhook_signature` tool with Stripe verification
- [ ] Implement `check_event_processed` tool for idempotency
- [ ] Create FastAPI webhook endpoint with proper error handling
- [ ] Implement async webhook processing via Celery tasks
- [ ] Add comprehensive logging and metrics

### Phase 3: Payment Handlers
- [ ] Implement `_handle_payment_succeeded` with invoice updates
- [ ] Implement `_handle_payment_failed` with retry logic
- [ ] Implement `_handle_charge_disputed` with project pause
- [ ] Add payment amount validation against invoices
- [ ] Implement client balance updates

### Phase 4: Integrations & Notifications
- [ ] Implement QuickBooks payment synchronization
- [ ] Create email notification templates and delivery
- [ ] Implement Slack/Telegram urgent alerts
- [ ] Add handoff mechanisms to other agents (onboarding, project management)
- [ ] Implement evidence gathering for disputes

### Phase 5: Tools Implementation
- [ ] Implement all 15 tools with proper input validation
- [ ] Add retry logic with exponential backoff for external APIs
- [ ] Implement circuit breaker pattern for failing integrations
- [ ] Add comprehensive error handling and recovery
- [ ] Create audit logging for all payment operations

### Phase 6: Testing
- [ ] Write unit tests for all agent methods
- [ ] Write unit tests for all tools
- [ ] Create integration tests for webhook processing
- [ ] Mock Stripe and QuickBooks APIs for testing
- [ ] Test error scenarios and recovery paths
- [ ] Performance tests for webhook throughput

### Phase 7: Security & Compliance
- [ ] Implement webhook signature verification
- [ ] Add rate limiting for webhook endpoints
- [ ] Implement IP whitelisting for Stripe webhooks
- [ ] Add audit logging for security events
- [ ] Ensure PCI compliance through Stripe integration

### Phase 8: Monitoring & Observability
- [ ] Add structured logging with correlation IDs
- [ ] Implement metrics for payment processing
- [ ] Create health checks for all integrations
- [ ] Set up alerting for critical events
- [ ] Add dashboard for payment operations

## Acceptance Criteria

### Functional Requirements
- [ ] Process Stripe webhooks securely with signature verification
- [ ] Prevent duplicate event processing with 100% reliability
- [ ] Update payment records and client balances accurately
- [ ] Sync payments to QuickBooks within 30 seconds
- [ ] Send email notifications for all payment events
- [ ] Pause projects immediately on disputes
- [ ] Trigger onboarding for deposit payments
- [ ] Generate complete audit trails

### Performance Requirements
- [ ] Webhook processing time: < 5 seconds average
- [ ] Handle 1000+ webhook events/minute
- [ ] QuickBooks sync completion: < 30 seconds
- [ ] Email delivery: < 2 minutes
- [ ] No data loss during processing failures

### Security Requirements
- [ ] All webhooks verified with Stripe signatures
- [ ] Rate limiting: 100 webhooks/minute
- [ ] No sensitive card data stored
- [ ] All external API calls encrypted
- [ ] Comprehensive security event logging

### Reliability Requirements
- [ ] 99.9% uptime for payment processing
- [ ] Automatic retry for transient failures
- [ ] Graceful degradation for external service failures
- [ ] Complete audit trail for all operations
- [ ] Recovery procedures for payment data

## Technical Requirements

### Database Models
```python
# Core payment models must include:
class Payment(BaseModel):
    stripe_payment_id: str  # Unique
    invoice_id: Optional[UUID]
    client_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    metadata: dict

class PaymentEvent(BaseModel):
    stripe_event_id: str  # Unique
    event_type: str
    payment_id: UUID
    status: str
    processing_time_ms: int
    error_message: Optional[str]

class Dispute(BaseModel):
    stripe_dispute_id: str  # Unique
    payment_id: UUID
    amount: Decimal
    reason: str
    status: str
    evidence_due: datetime
```

### API Endpoints
```python
# Required webhook endpoint
POST /webhooks/stripe
Headers: Stripe-Signature
Body: Stripe event payload
Response: 200 OK (always acknowledge)

# Health check
GET /health/payments
Response: { status: "healthy", checks: {...} }
```

### Environment Variables
```bash
# Required for production
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
QUICKBOOKS_CLIENT_ID=...
QUICKBOOKS_CLIENT_SECRET=...
SMTP_HOST=...
SMTP_USERNAME=...
SMTP_PASSWORD=...
```

## Verification Commands

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_payment_processing.py -v
pytest app/backend/__tests__/unit/agents/test_payment_tools.py -v

# Run integration tests
pytest app/backend/__tests__/integration/test_payment_processing_integration.py -v

# Type checking
mypy app/backend/src/agents/payment_processing.py
mypy app/backend/src/agents/tools/payment_tools.py
mypy app/backend/src/models/payment.py

# Linting
ruff check app/backend/src/agents/payment_processing.py
ruff check app/backend/src/agents/tools/payment_tools.py
ruff check app/backend/src/models/payment.py

# Database migrations
make migrate

# Manual webhook test
curl -X POST http://localhost:8000/webhooks/stripe \
  -H "Stripe-Signature: $STRIPE_SIGNATURE" \
  -H "Content-Type: application/json" \
  -d @test_webhook.json

# Health check
curl http://localhost:8000/health/payments
```

## Dependencies
- New pip packages: `stripe`, `quickbooks`, `cryptography` (for signature verification)
- Database: PostgreSQL with required tables and indexes
- External: Stripe account, QuickBooks Developer account, SMTP server
- Services: Redis for Celery task queue

## Notes
- Follow existing BaseAgent pattern for consistency
- Use async/await for all I/O operations
- Implement proper error handling with specific exception types
- Add comprehensive logging with correlation IDs
- Test thoroughly with mock Stripe and QuickBooks APIs
- Consider edge cases: partial payments, refunds, chargebacks
- Ensure all payment data is properly validated
- Document all error codes and recovery procedures
