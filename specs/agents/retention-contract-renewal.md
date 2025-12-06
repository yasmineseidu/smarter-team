# Contract Renewal Agent Specification

## Overview
The Contract Renewal Agent manages the complete retainer renewal lifecycle for Smarter Team clients. It tracks contract end dates, sends timely reminders, generates renewal proposals, handles negotiations, and processes renewals or offboarding decisions.

## Architecture

### Agent Class
```python
class ContractRenewalAgent(BaseAgent):
    """Manages contract renewals for client retention."""

    @property
    def system_prompt(self) -> str:
        # Comprehensive system prompt for renewal management

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        # Process renewal-related tasks
```

### Database Schema

#### ContractRenewal Table
```sql
CREATE TABLE contract_renewals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    contract_id UUID NOT NULL REFERENCES contracts(id),
    current_end_date DATE NOT NULL,
    renewal_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    renewal_type VARCHAR(20) NOT NULL DEFAULT 'annual',
    current_value DECIMAL(10,2) NOT NULL,
    proposed_value DECIMAL(10,2),
    value_change_percent DECIMAL(5,2),
    renewal_probability INTEGER CHECK (0 <= renewal_probability <= 100),
    last_contact_date DATE,
    next_action_date DATE,
    renewal_strategy JSONB,
    pricing_justification TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### RenewalReminders Table
```sql
CREATE TABLE renewal_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    renewal_id UUID NOT NULL REFERENCES contract_renewals(id),
    reminder_type VARCHAR(20) NOT NULL,
    scheduled_date DATE NOT NULL,
    sent_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    template_name VARCHAR(100),
    template_variables JSONB,
    response_received BOOLEAN DEFAULT FALSE,
    response_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### RenewalNegotiations Table
```sql
CREATE TABLE renewal_negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    renewal_id UUID NOT NULL REFERENCES contract_renewals(id),
    negotiation_round INTEGER NOT NULL,
    client_position TEXT,
    our_position TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    resolution_strategy TEXT,
    outcome VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### RenewalHistory Table
```sql
CREATE TABLE renewal_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    renewal_id UUID NOT NULL REFERENCES contract_renewals(id),
    action VARCHAR(100) NOT NULL,
    action_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    action_by VARCHAR(50),
    details JSONB,
    audit_log TEXT
);
```

### Tools

#### Core Tools
1. **track_contracts()** - Scan for contracts ending within 90 days
2. **schedule_reminders()** - Set up reminder schedule for each renewal
3. **generate_renewal_proposal()** - Create proposal based on client value
4. **calculate_pricing_adjustment()** - Calculate new pricing with justification
5. **send_client_communication()** - Send personalized renewal emails
6. **analyze_renewal_probability()** - Score likelihood of renewal
7. **handle_negotiation()** - Track and support negotiation process
8. **process_renewal_decision()** - Handle acceptance/rejection
9. **initiate_offboarding()** - Handoff to offboarding agent if needed
10. **generate_renewal_report()** - Create management reports

#### Supporting Tools
1. **get_client_value_metrics()** - Retrieve ROI and value delivered
2. **get_market_pricing_data()** - Check competitive pricing
3. **validate_pricing_rules()** - Ensure pricing follows guidelines
4. **escalate_for_approval()** - Flag when human approval needed
5. **update_renewal_status()** - Track status changes
6. **log_renewal_activity()** - Maintain audit trail

### System Prompts

#### Main System Prompt
```
You are the Contract Renewal Agent for Smarter Team, responsible for managing client contract renewals and retention. Your role is to ensure smooth, timely, and successful renewals that maintain strong client relationships while supporting business growth.

Key responsibilities:
1. Monitor contract end dates and initiate renewal process 90 days before expiry
2. Assess client value and determine appropriate renewal pricing
3. Generate personalized renewal proposals that reflect delivered value
4. Manage the complete renewal timeline with strategic client touchpoints
5. Handle negotiations with data-driven justification
6. Maintain detailed renewal history and audit trails
7. Coordinate with other agents for seamless client experience

Renewal Timeline:
- 90 days: Internal alert and strategy development
- 60 days: Client touchpoint to gauge satisfaction
- 30 days: Send formal renewal proposal
- 14 days: Follow-up reminder
- 7 days: Final reminder and decision deadline

Pricing Guidelines:
- Standard annual increase: 3-5%
- Loyalty clients (2+ years): Consider loyalty discounts
- High-value clients: Adjust based on demonstrated ROI
- Market adjustments: Align with competitive rates
- All changes require clear justification and client value mapping

Communication Style:
- Professional yet personalized
- Focus on client success and value delivered
- Proactive and well-timed
- Data-backed recommendations
- Transparent about any pricing changes

Always maintain the client relationship as the highest priority. Every interaction should strengthen the partnership, regardless of renewal outcome.
```

#### Pricing Calculation Prompt
```
When calculating renewal pricing, consider:

1. Client ROI Metrics:
   - Projects completed successfully
   - Client satisfaction scores
   - Measurable business impact
   - Strategic value delivered

2. Market Factors:
   - Competitive pricing analysis
   - Industry standard rates
   - Inflation and market adjustments
   - Service scope changes requested

3. Relationship Factors:
   - Length of partnership
   - Payment history
   - Strategic importance
   - Growth potential

4. Pricing Rules:
   - Base increase: 3-5% annually
   - Loyalty discount: Up to 10% for 3+ year clients
   - Value-based increase: Up to 15% for exceptional ROI
   - Special adjustments: Document business case

Generate a clear pricing recommendation with justification for each factor.
```

#### Negotiation Support Prompt
```
During negotiations:

1. Prepare client-specific value dossier:
   - Quantify results achieved
   - Highlight unique value provided
   - Document scope of work
   - Compare to market alternatives

2. Identify flexibility points:
   - Payment terms
   - Contract length options
   - Phased implementations
   - Value-add services

3. Red lines:
   - Minimum acceptable rate
   - Essential service levels
   - Required contract terms
   - Non-negotiable deliverables

4. Escalation triggers:
   - Requests below minimum rate
   - Demanding service reductions
   - Unreasonable terms
   - Strategic client exceptions

Always negotiate from value, not price. Emphasize partnership and mutual success.
```

### Error Handling

#### Critical Error Scenarios
1. **Missing Contract Data**
   - Log error with details
   - Attempt to sync from source systems
   - Create manual review task
   - Notify human administrator

2. **Failed Proposal Generation**
   - Retry with exponential backoff (max 3 attempts)
   - Fallback to standard template
   - Log failure details
   - Flag for manual review

3. **Client Unresponsiveness**
   - Implement multiple contact channels
   - Escalate to account manager after 3 attempts
   - Document all outreach attempts
   - Prepare offboarding checklist

4. **Integration Failures**
   - Circuit breaker pattern for external APIs
   - Queue failed operations for retry
   - Use fallback data sources
   - Alert monitoring system

5. **Timeline Violations**
   - Automatic priority escalation
   - Supervisor notifications
   - Process improvement logging
   - Preventive schedule adjustments

#### Recovery Procedures
```python
async def handle_renewal_error(
    error: Exception,
    renewal_id: str,
    context: dict[str, Any]
) -> dict[str, Any]:
    """Handle errors in renewal process with recovery strategies."""
    error_type = type(error).__name__

    if error_type == "MissingContractDataError":
        # Attempt data recovery
        return await recover_contract_data(renewal_id)

    elif error_type == "ProposalGenerationError":
        # Use fallback proposal
        return await generate_fallback_proposal(renewal_id)

    elif error_type == "ClientUnresponsiveError":
        # Escalate to human
        return await escalate_to_human(renewal_id, context)

    # Generic error handling
    await log_error(error, renewal_id, context)
    return {"status": "error", "recovery_attempted": True}
```

### Integrations

#### Contract Management System
```python
class ContractManagementClient(BaseIntegrationClient):
    """Integration with contract/proposal system (e.g., PandaDoc)."""

    async def get_contract_details(self, contract_id: str) -> dict:
        """Retrieve current contract details."""
        return await self.get(f"/contracts/{contract_id}")

    async def create_renewal_proposal(
        self,
        template_id: str,
        client_data: dict,
        pricing_details: dict
    ) -> dict:
        """Generate renewal proposal from template."""
        return await self.post(
            "/proposals",
            json={
                "template": template_id,
                "client": client_data,
                "pricing": pricing_details
            }
        )

    async def update_proposal_status(
        self,
        proposal_id: str,
        status: str
    ) -> dict:
        """Update proposal status."""
        return await self.patch(
            f"/proposals/{proposal_id}",
            json={"status": status}
        )
```

#### Email Service Integration
```python
class EmailServiceClient(BaseIntegrationClient):
    """Integration with email service for renewal communications."""

    async def send_renewal_email(
        self,
        template_name: str,
        recipient: str,
        variables: dict
    ) -> dict:
        """Send personalized renewal email."""
        return await self.post(
            "/send",
            json={
                "template": template_name,
                "to": recipient,
                "variables": variables
            }
        )
```

### Celery Tasks

#### Scheduled Tasks
```python
@celery_app.task(bind=True, max_retries=3)
def check_upcoming_renewals(self):
    """Monthly check for contracts ending in next 90 days."""
    logger.info("Checking upcoming renewals")

    try:
        agent = ContractRenewalAgent()
        await agent.track_contracts()

    except Exception as exc:
        logger.error(f"Error checking renewals: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_scheduled_reminders(self):
    """Send daily renewal reminders."""
    logger.info("Sending scheduled reminders")

    try:
        agent = ContractRenewalAgent()
        await agent.send_pending_reminders()

    except Exception as exc:
        logger.error(f"Error sending reminders: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def generate_renewal_reports(self):
    """Generate weekly renewal status reports."""
    logger.info("Generating renewal reports")

    try:
        agent = ContractRenewalAgent()
        report = await agent.generate_renewal_report()
        await agent.handoff_to(
            target_agent="client_success",
            payload={"report": report},
            priority="normal"
        )

    except Exception as exc:
        logger.error(f"Error generating reports: {exc}")
        raise self.retry(exc=exc, countdown=60)
```

### Human-in-the-Loop Gates

#### Gate 1: Pricing Approval (60 days before)
Trigger when:
- Proposed increase > 10%
- Client flagged as high-risk
- Special pricing terms requested

Approval from: Sales Director or Account Manager

#### Gate 2: Proposal Review (30 days before)
All proposals require:
- Account manager sign-off
- Pricing validation
- Value justification review

#### Gate 3: Negotiation Strategy
Trigger when:
- Client requests significant concessions
- Multi-round negotiations (> 3 rounds)
- Strategic client exception needed

#### Gate 4: Non-Renewal Decision
All non-renewals require:
- Revenue impact assessment
- Client feedback collection
- Offboarding plan approval

### Testing Strategy

#### Unit Tests
- Tool function testing
- Pricing calculation validation
- Template rendering tests
- Database model operations
- Error handling scenarios

#### Integration Tests
- End-to-end renewal workflow
- External API integrations
- Celery task execution
- Database transaction integrity
- Email sending functionality

#### Performance Tests
- Large renewal batch processing
- Concurrent reminder sending
- Database query optimization
- Rate limiting effectiveness

### Monitoring and Alerting

#### Key Metrics
- Renewal rate by month
- Average time to renewal decision
- Pricing adjustment acceptance rate
- Client satisfaction during renewal
- Revenue retention percentage

#### Alerts
- Renewal rate below 80%
- Pending renewals without progress
- Failed email deliveries
- Missing contract data
- Escalation timeouts

### Security and Compliance

#### Data Protection
- Encrypt sensitive client data
- Audit all pricing changes
- Secure API credentials
- GDPR compliance for EU clients

#### Access Controls
- Role-based permissions
- Approval audit trails
- Pricing change restrictions
- Client data access logging

## Dependencies
- BaseAgent from agents/base_agent.py
- SQLAlchemy 2.0 for database operations
- Celery for background tasks
- Integration clients for external systems
- Email service for communications
- Contract management system

## Success Metrics
1. >90% renewal rate for retained clients
2. 30+ day advance notice for all renewals
3. <5% pricing dispute escalations
4. 100% audit trail completeness
5. <24 hour response time for client queries
6. Seamless offboarding for non-renewals
