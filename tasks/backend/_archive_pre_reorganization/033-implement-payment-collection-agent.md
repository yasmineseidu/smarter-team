# Task: Implement Payment Collection Agent

**Status:** Pending
**Domain:** Backend
**Spec Reference:** specs/agents/payment-collection.md
**Created:** 2025-12-05
**Priority:** High (Revenue-critical)

## Summary

Implement the Payment Collection Agent that monitors invoice due dates, sends escalating reminders, tracks payment status, and manages collection workflows. The agent integrates with Stripe for payment status checking, email for reminders, and Slack for internal alerts. Handles payment arrangements, work pauses, and collections escalation.

## Files to Create

### Core Implementation
- `app/backend/src/agents/payment_collection/agent.py` - Main agent class extending BaseAgent
- `app/backend/src/agents/payment_collection/tools.py` - All tool functions with decorators
- `app/backend/src/agents/payment_collection/prompts.py` - System prompt and reminder templates
- `app/backend/src/agents/payment_collection/schemas.py` - Pydantic models for validation
- `app/backend/src/agents/payment_collection/exceptions.py` - Custom exception classes
- `app/backend/src/agents/payment_collection/__init__.py` - Package exports

### Integration Clients
- `app/backend/src/integrations/stripe_client.py` - Extend existing base for payment status
- `app/backend/src/integrations/email_client.py` - Email service client for reminders
- `app/backend/src/integrations/slack_client.py` - Slack client for internal alerts

### Database & Models
- `app/backend/src/models/collection.py` - SQLAlchemy models for collection events, arrangements
- `app/backend/migrations/002_add_collection_tables.sql` - Database migration

### Tasks
- `app/backend/src/tasks/collection_tasks.py` - Celery tasks for async collection processing
- Update `app/backend/src/tasks/orchestration_tasks.py` - Add collection-related tasks

### Tests
- `app/backend/__tests__/unit/agents/test_payment_collection_agent.py` - Unit tests (>90% coverage)
- `app/backend/__tests__/integration/test_payment_collection_integration.py` - Integration tests
- `app/backend/__tests__/fixtures/collection_fixtures.py` - Test fixtures and mocks

## Implementation Checklist

### 1. Core Agent Implementation
- [ ] Create PaymentCollectionAgent class extending BaseAgent
- [ ] Implement system prompt with collection responsibilities
- [ ] Configure reminder schedules and business hours
- [ ] Set up lazy-loaded integration clients (Stripe, Email, Slack)
- [ ] Implement process_task method for different task types

### 2. Tool Implementation
- [ ] Implement get_overdue_invoices tool with database queries
- [ ] Implement check_stripe_payment_status tool with API integration
- [ ] Implement send_payment_reminder tool with template rendering
- [ ] Implement send_internal_alert tool for Slack notifications
- [ ] Implement update_collection_status tool for audit logging
- [ ] Implement request_payment_arrangement tool for client requests
- [ ] Implement pause_project_work tool with PM agent handoff
- [ ] Add comprehensive error handling and retry logic to all tools

### 3. Reminder Templates
- [ ] Create all reminder templates (due_date, gentle, firm, warning, final, escalation)
- [ ] Implement template rendering with Jinja2 or f-strings
- [ ] Add template variables and formatting
- [ ] Store templates in database for customization
- [ ] Add multi-language support structure (English initially)

### 4. Database Schema
- [ ] Create CollectionEvent model for audit trail
- [ ] Create PaymentArrangement model for payment plans
- [ ] Create ReminderTemplate model for customizable templates
- [ ] Add collection columns to existing Invoice table
- [ ] Write SQL migration with proper indexes and constraints
- [ ] Add database methods for CRUD operations

### 5. Integration Clients
- [ ] Implement StripeClient extending BaseIntegrationClient
- [ ] Add methods: get_invoice, check_payment_status, handle_webhooks
- [ ] Implement EmailClient with HTML/text template support
- [ ] Add bounce handling and delivery tracking
- [ ] Implement SlackClient for webhook-based notifications
- [ ] Add rate limiting and error handling for all clients

### 6. Celery Tasks
- [ ] Create daily_collection_check task (runs at 9 AM)
- [ ] Create process_payment_webhook task for Stripe events
- [ ] Create send_reminder_batch task for bulk operations
- [ ] Add retry logic with exponential backoff
- [ ] Implement task monitoring and dead-letter queue

### 7. Webhook Handlers
- [ ] Create Stripe webhook handler for invoice events
- [ ] Add webhook signature verification
- [ ] Implement async event processing
- [ ] Add duplicate event prevention
- [ ] Create webhook test endpoints

### 8. Error Handling & Edge Cases
- [ ] Handle Stripe API unavailability gracefully
- [ ] Implement email delivery failures and retries
- [ ] Process partial payments and overpayments
- [ ] Handle payment disputes and chargebacks
- [ ] Respect weekends/holidays for reminder scheduling
- [ ] Implement business hours checking

### 9. Security & Compliance
- [ ] Ensure PCI compliance (no card data storage)
- [ ] Add input validation and sanitization
- [ ] Implement rate limiting for reminder sends
- [ ] Add audit logging for all collection activities
- [ ] Secure API endpoints with authentication

### 10. Testing
- [ ] Write unit tests for all tools and methods
- [ ] Mock external API responses (Stripe, Email, Slack)
- [ ] Test all reminder templates and edge cases
- [ ] Write integration tests with test database
- [ ] Test complete collection workflows
- [ ] Add performance tests for bulk operations
- [ ] Achieve >90% code coverage

### 11. Monitoring & Observability
- [ ] Add Prometheus metrics for collection activities
- [ ] Implement structured logging with correlation IDs
- [ ] Create Grafana dashboards for collection metrics
- [ ] Set up alerting rules for critical failures
- [ ] Add health check endpoints

### 12. Configuration & Deployment
- [ ] Add environment variables for all integrations
- [ ] Configure Celery beat schedule for daily checks
- [ ] Set up Stripe webhook endpoints in production
- [ ] Add feature flags for reminder customization
- [ ] Update deployment scripts and documentation

## Acceptance Criteria

1. **Functional Requirements:**
   - Agent correctly identifies overdue invoices based on due dates
   - Sends appropriate reminders according to schedule (3, 7, 14, 30, 60 days)
   - Checks Stripe payment status before sending reminders
   - Updates collection status and logs all activities
   - Handles payment arrangement requests and escalates for approval
   - Coordinates project work pauses with PM agent
   - Processes Stripe webhooks for payment updates

2. **Performance Requirements:**
   - Daily collection check completes within 2 minutes
   - Reminder emails send within 5 seconds of trigger
   - Handles 1000+ overdue invoices efficiently
   - Stripe API calls include proper retry logic
   - Database queries optimized with proper indexes

3. **Quality Requirements:**
   - >90% unit test coverage
   - >85% integration test coverage
   - All tools handle errors gracefully
   - No sensitive data logged or exposed
   - Proper audit trail for all collection activities

4. **Integration Requirements:**
   - Stripe API integration for payment status
   - Email service integration for reminders
   - Slack integration for internal alerts
   - Celery integration for async processing
   - PM agent handoff for project pauses

5. **Usability Requirements:**
   - Configurable reminder schedules per client
   - Customizable reminder templates
   - Clear payment arrangement workflow
   - Comprehensive dashboard for collection status

## Verification

```bash
# Run unit tests
pytest app/backend/__tests__/unit/agents/test_payment_collection_agent.py -v --cov=src.agents.payment_collection

# Run integration tests
pytest app/backend/__tests__/integration/test_payment_collection_integration.py -v

# Type checking
mypy app/backend/src/agents/payment_collection/

# Linting
ruff check app/backend/src/agents/payment_collection/

# Database migration
make migration name="add_collection_tables"

# Manual test - Initialize agent
python -c "
from src.agents.payment_collection import PaymentCollectionAgent
agent = PaymentCollectionAgent()
print(f'Agent initialized: {agent.name}')
print(f'Reminder schedule: {agent.reminder_schedule}')
"

# Test Stripe integration
python -c "
from src.integrations.stripe_client import StripeClient
client = StripeClient(api_key='sk_test_...')
print('Stripe client initialized successfully')
"

# Test email template rendering
python -c "
from src.agents.payment_collection import PaymentCollectionAgent
agent = PaymentCollectionAgent()
template = agent._get_gentle_reminder_template()
print('Template keys:', template.keys())
"
```

## Dependencies

- Must complete: Invoice Generation Agent (provides invoice data)
- Integrates with: Project Management Agent (work pauses)
- Integrates with: Finance Agent (revenue tracking)
- Requires: Stripe API setup with webhooks
- Requires: Email service configuration (SendGrid/SES)
- Requires: Slack webhook configuration

## Notes

- Collection agent is revenue-critical - prioritize reliability
- Consider timezone differences for international clients
- Implement graceful degradation for external service failures
- Monitor collection effectiveness and adjust schedules as needed
- Ensure compliance with collection laws and regulations
