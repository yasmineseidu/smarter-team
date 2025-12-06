# Implement Retention Contract Renewal Agent

**Priority**: High
**Estimated Time**: 4-5 days
**Dependencies**: BaseAgent, Database models, Celery setup, Integration clients

## Task Overview
Implement the Contract Renewal Agent according to the specification in `/specs/agents/retention-contract-renewal.md`. This agent manages the complete contract renewal lifecycle for client retention.

## Implementation Checklist

### Phase 1: Database Setup (Day 1)
- [ ] Create database models in `src/database/models/retention.py`:
  - `ContractRenewal` model with all fields
  - `RenewalReminder` model with template support
  - `RenewalNegotiation` model for negotiation tracking
  - `RenewalHistory` model for audit trail
- [ ] Write Alembic migration for all tables
- [ ] Add proper indexes for performance queries
- [ ] Create database fixtures in `__tests__/fixtures/retention_fixtures.py`
- [ ] Write database model tests

### Phase 2: Agent Core Implementation (Day 1-2)
- [ ] Create `src/agents/retention/` directory structure
- [ ] Implement `ContractRenewalAgent` class extending `BaseAgent`
- [ ] Add comprehensive system prompt from spec
- [ ] Implement core tools in `tools.py`:
  - `track_contracts()` - Scan for upcoming expirations
  - `schedule_reminders()` - Set up reminder schedule
  - `generate_renewal_proposal()` - Create client proposals
  - `calculate_pricing_adjustment()` - Pricing with justification
  - `send_client_communication()` - Personalized emails
  - `analyze_renewal_probability()` - Score renewal likelihood
  - `handle_negotiation()` - Negotiation tracking
  - `process_renewal_decision()` - Handle accept/reject
  - `initiate_offboarding()` - Handoff to offboarding
  - `generate_renewal_report()` - Management reports
- [ ] Create Pydantic schemas in `schemas.py`
- [ ] Add custom exceptions in `exceptions.py`

### Phase 3: Integration Components (Day 2-3)
- [ ] Extend `ContractManagementClient` in `src/integrations/contract_management.py`:
  - Contract retrieval methods
  - Proposal generation from templates
  - Status update tracking
- [ ] Extend `EmailServiceClient` in `src/integrations/email_service.py`:
  - Template-based email sending
  - Personalization variables
  - Delivery tracking
- [ ] Implement pricing calculation module:
  - Market rate analysis
  - Loyalty discount logic
  - Value-based pricing rules
  - Justification generation

### Phase 4: Email Templates (Day 3)
- [ ] Create email templates in `templates/renewal/`:
  - `90-day-internal-alert.html`
  - `60-day-client-touchpoint.html`
  - `30-day-renewal-proposal.html`
  - `14-day-reminder.html`
  - `7-day-final-reminder.html`
  - `negotiation-followup.html`
  - `renewal-confirmation.html`
- [ ] Implement template rendering with Jinja2
- [ ] Add template variable validation
- [ ] Test template rendering with sample data

### Phase 5: Error Handling & Edge Cases (Day 3-4)
- [ ] Implement comprehensive error handling:
  - `MissingContractDataError` recovery
  - `ProposalGenerationError` fallbacks
  - `ClientUnresponsiveError` escalation
  - Integration failure circuit breakers
  - Timeline violation recovery
- [ ] Add validation for all inputs
- - [ ] Implement retry logic with exponential backoff
- [ ] Add logging with structured data
- [ ] Create error recovery procedures

### Phase 6: Celery Tasks (Day 4)
- [ ] Create `src/tasks/retention_tasks.py`:
  - `check_upcoming_renewals` - Monthly scan
  - `send_scheduled_reminders` - Daily reminders
  - `generate_renewal_reports` - Weekly reports
  - `process_renewal_deadlines` - Deadline handling
- [ ] Configure Celery beat schedule:
  - Monthly renewal check
  - Daily reminder sending
  - Weekly report generation
  - Hourly deadline monitoring
- [ ] Add task monitoring and alerting

### Phase 7: Human-in-the-Loop Implementation (Day 4)
- [ ] Implement approval workflow for pricing changes
- [ ] Create escalation triggers:
  - Large pricing increases
  - High-risk clients
  - Negotiation rounds > 3
  - Non-renewal decisions
- [ ] Add approval tracking in database
- [ ] Implement notification system for approvals
- [ ] Create approval dashboard data endpoints

### Phase 8: Testing (Day 4-5)
- [ ] Write unit tests for:
  - All tool functions
  - Database model operations
  - Pricing calculations
  - Template rendering
  - Error handling scenarios
- [ ] Write integration tests for:
  - End-to-end renewal workflow
  - External API integrations
  - Celery task execution
  - Email sending functionality
  - Database transactions
- [ ] Create performance tests:
  - Batch renewal processing
  - Concurrent reminder sending
  - Database query optimization
- [ ] Achieve >90% test coverage

### Phase 9: Documentation & Final Polish (Day 5)
- [ ] Add comprehensive docstrings
- [ ] Create usage examples
- [ ] Update API documentation
- [ ] Add monitoring configuration
- [ ] Create deployment checklist
- [ ] Final code review and optimization

## Key Implementation Details

### Pricing Calculation Logic
```python
def calculate_pricing_adjustment(
    current_value: Decimal,
    client_tenure_months: int,
    delivered_roi: float,
    market_adjustment: float
) -> PricingAdjustment:
    """Calculate renewal pricing with justification."""
    # Base increase: 3-5%
    base_adjustment = Decimal('0.04')  # 4% default

    # Loyalty discount for long-term clients
    loyalty_discount = Decimal('0.00')
    if client_tenure_months >= 36:
        loyalty_discount = Decimal('0.10')  # 10% discount

    # Value-based increase for high ROI
    value_increase = Decimal('0.00')
    if delivered_roi > 5.0:  # 5x ROI threshold
        value_increase = Decimal('0.15')  # 15% increase

    # Calculate final adjustment
    total_adjustment = (
        base_adjustment
        - loyalty_discount
        + value_increase
        + Decimal(str(market_adjustment))
    )

    return PricingAdjustment(
        percentage=total_adjustment,
        justification=generate_justification(...)
    )
```

### Renewal Timeline Implementation
```python
class RenewalTimeline:
    """Manages the renewal communication timeline."""

    TIMELINE_MILESTONES = [
        {"days": 90, "type": "internal", "template": "90-day-internal-alert"},
        {"days": 60, "type": "client", "template": "60-day-client-touchpoint"},
        {"days": 30, "type": "client", "template": "30-day-renewal-proposal"},
        {"days": 14, "type": "client", "template": "14-day-reminder"},
        {"days": 7, "type": "client", "template": "7-day-final-reminder"},
    ]

    async def schedule_reminders(self, renewal_id: str):
        """Schedule all reminders for a renewal."""
        for milestone in self.TIMELINE_MILESTONES:
            await self.schedule_reminder(
                renewal_id=renewal_id,
                milestone=milestone
            )
```

### Database Patterns
- Use SQLAlchemy 2.0 async patterns throughout
- UUID primary keys following project conventions
- Proper foreign key relationships with cascading deletes
- Comprehensive indexing for performance
- Audit fields (created_at, updated_at) on all tables
- Soft deletes for historical data

### API Integration
- Extend existing integration client patterns
- Implement proper rate limiting
- Add comprehensive error handling
- Use async HTTP calls throughout
- Implement circuit breaker for external services

### Email Template System
```python
class EmailTemplateManager:
    """Manages renewal email templates."""

    async def render_template(
        self,
        template_name: str,
        variables: dict[str, Any]
    ) -> str:
        """Render email template with variables."""
        template = self.jinja_env.get_template(f"renewal/{template_name}")
        return await template.render_async(variables)
```

## Files to Create/Modify

### New Files
```
app/backend/src/agents/retention/
├── __init__.py
├── agent.py              # ContractRenewalAgent class
├── tools.py              # All tool implementations
├── pricing.py            # Pricing calculation logic
├── templates.py          # Template management
├── schemas.py            # Pydantic models
├── exceptions.py         # Custom exceptions
└── prompts.py            # System and tool prompts

app/backend/src/database/models/retention.py
├── ContractRenewal
├── RenewalReminder
├── RenewalNegotiation
└── RenewalHistory

app/backend/src/tasks/retention_tasks.py
├── check_upcoming_renewals
├── send_scheduled_reminders
├── generate_renewal_reports
└── process_renewal_deadlines

app/backend/src/integrations/contract_management.py
app/backend/src/integrations/email_service.py

app/backend/templates/renewal/
├── 90-day-internal-alert.html
├── 60-day-client-touchpoint.html
├── 30-day-renewal-proposal.html
├── 14-day-reminder.html
├── 7-day-final-reminder.html
├── negotiation-followup.html
└── renewal-confirmation.html

app/backend/__tests__/unit/agents/test_retention_contract_renewal.py
app/backend/__tests__/integration/test_retention_workflow.py
app/backend/__tests__/fixtures/retention_fixtures.py
```

### Modified Files
- `app/backend/src/celery_app.py` - Add new task schedules
- `app/backend/src/config.py` - Add retention-specific settings
- `app/backend/migrations/versions/` - Add new migration
- `app/backend/src/main.py` - Add health check endpoints

## Environment Variables
```bash
# Contract Renewal Configuration
RENEWAL_BASE_INCREASE_RATE=0.04
RENEWAL_LOYALTY_DISCOUNT_RATE=0.10
RENEWAL_VALUE_INCREASE_THRESHOLD=5.0
RENEWAL_VALUE_INCREASE_RATE=0.15
RENEWAL_MAX_NEGOTIATION_ROUNDS=3
RENEWAL_REMINDER_BATCH_SIZE=50
RENEWAL_REPORT_RECIPIENTS="success@smarterteam.com"
```

## Dependencies to Install
```bash
# Already in project:
# sqlalchemy - Database ORM
# celery - Task queue
# httpx - HTTP client
# pytest - Testing framework

# Additional if needed:
pip install jinja2>=3.1.0  # Template rendering
```

## Implementation Notes

1. **Data Integrity**: Ensure all contract data is validated before processing
2. **Performance**: Use database indexes and query optimization for large datasets
3. **Reliability**: Implement proper error recovery and retry mechanisms
4. **Audit Trail**: Log all renewal decisions and actions for compliance
5. **Extensibility**: Design for future enhancement (multi-year contracts, custom terms)
6. **Security**: Protect sensitive client data and pricing information
7. **Testing**: Mock external dependencies for reliable unit testing

## Review Checklist Before Completion
- [ ] Code follows project conventions (snake_case, type hints, async)
- [ ] All tests pass and coverage >90%
- [ ] Documentation is complete and accurate
- [ ] Error handling is comprehensive
- [ ] Performance is acceptable for 1000+ contracts
- [ ] Security considerations addressed
- [ ] Database migrations tested
- [ ] API integration fully tested
- [ ] Email templates render correctly
- [ ] Celery tasks scheduled properly
- [ ] Monitoring and alerting configured
- [ ] Human approval workflows tested

## Success Criteria
1. All unit tests pass with >90% coverage
2. Integration tests demonstrate complete renewal workflow
3. Email templates render with all variables
4. Pricing calculations match business rules
5. Error recovery handles all failure scenarios
6. Performance acceptable for scale
7. Audit trail is comprehensive
8. Human approval gates function correctly
