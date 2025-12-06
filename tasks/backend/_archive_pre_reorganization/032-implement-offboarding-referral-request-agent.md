# Implement Offboarding Referral Request Agent

**Priority:** High
**Estimated Time:** 5 days
**Dependencies:** BaseAgent, InstantlyClient, Database models, CRM integration
**Spec File:** `/specs/agents/offboarding-referral-request.md`

## Task Overview

Implement the Referral Request Agent according to the production specification. This agent will autonomously manage the complete referral workflow - from identifying eligible contacts and sending personalized requests at optimal moments, to tracking referrals through conversion and managing incentive programs.

## Implementation Checklist

### Phase 1: Database Setup (Day 1)
- [ ] Create SQLAlchemy models for all referral tables:
  - `ReferralRequest`
  - `Referral`
  - `ReferralIncentive`
  - `ReferralPayout`
  - `ReferralAnalytics`
- [ ] Write Alembic migration for all tables
- [ ] Add proper indexes for performance optimization
- [ ] Create test fixtures for all models in `__tests__/fixtures/`
- [ ] Add foreign key constraints and cascade rules
- [ ] Implement audit logging trigger for `referral_audit_log`

### Phase 2: Agent Core Implementation (Day 1-2)
- [ ] Create `offboarding/referral_request/` directory structure
- [ ] Implement `ReferralRequestAgent` class extending `BaseAgent`
- [ ] Add comprehensive system prompt with decision framework
- [ ] Implement core tools with full error handling:
  - `check_referral_eligibility`
  - `calculate_eligibility_score`
  - `personalize_referral_request`
  - `send_referral_request`
  - `process_referral_response`
  - `create_referral_lead`
  - `calculate_incentive_payout`
  - `generate_referral_analytics`

### Phase 3: Personalization Engine (Day 2)
- [ ] Implement template system for referral requests:
  - Post-project completion template
  - After testimonial template
  - Annual touchpoint template
  - Closed-lost deal template
- [ ] Create personalization token resolver:
  - Project history injection
  - Satisfaction score references
  - Relationship context building
  - Incentive details formatting
- [ ] Implement tone adjustment based on relationship strength
- [ ] Add A/B testing support for subject lines and templates
- [ ] Create effectiveness prediction model

### Phase 4: Integration Components (Day 2-3)
- [ ] Extend `InstantlyClient` with referral-specific endpoints:
  - Campaign creation for referral requests
  - Open and reply tracking
  - Response webhook handling
- [ ] Implement CRM integration for lead creation:
  - Referral lead attribution
  - Source tracking
  - Custom field mapping
- [ ] Add email response parsing:
  - Referral information extraction
  - Contact details parsing
  - Relationship context analysis
- [ ] Implement rate limiting and consent checking:
  - 6-month minimum between requests
  - Do-not-contact list respect
  - Opt-out handling

### Phase 5: Error Handling & Edge Cases (Day 3)
- [ ] Implement comprehensive error handling:
  - Email delivery failures with exponential backoff
  - Duplicate referral detection
  - Invalid referral data handling
  - Incentive calculation errors
  - API service failures with fallbacks
- [ ] Add retry logic for transient failures:
  - 3 attempts with exponential backoff
  - Circuit breaker pattern for API failures
  - Dead letter queue for failed requests
- [ ] Implement graceful degradation:
  - Fallback templates when personalization fails
  - Manual review queue for edge cases
  - Admin notifications for critical errors

### Phase 6: Incentive Management System (Day 3-4)
- [ ] Implement incentive calculation engine:
  - Fixed amount payouts
  - Percentage-based commissions
  - Minimum conversion thresholds
  - Maximum payout caps
- [ ] Add payout processing workflow:
  - Automated approval for standard amounts
  - Manual review for large payouts
  - Clawback provisions and tracking
- [ ] Create incentive tracking:
  - Payout status management
  - Payment method preferences
  - Tax documentation collection
- [ ] Implement ROI calculation engine
- [ ] Add incentive effectiveness reporting

### Phase 7: Analytics & Reporting (Day 4)
- [ ] Implement analytics calculation module:
  - Request metrics (sent, delivered, opened, replied)
  - Referral funnel tracking
  - Conversion rate calculations
  - ROI and LTV analysis
- [ ] Create automated report generation:
  - Daily performance summaries
  - Weekly trend analysis
  - Monthly comprehensive reviews
- [ ] Add dashboard metrics:
  - Real-time request status
  - Referral pipeline health
  - Top referrers leaderboard
  - Incentive program performance
- [ ] Implement data aggregation for performance:
  - Time-series data optimization
  - Pre-calculated metrics caching
  - Efficient querying patterns

### Phase 8: Testing Suite (Day 4-5)
- [ ] Write comprehensive unit tests:
  - `test_referral_request_agent.py` - Core agent functionality
  - `test_eligibility_scoring.py` - Score calculation accuracy
  - `test_personalization.py` - Template rendering
  - `test_referral_processing.py` - Response parsing
  - `test_incentive_calculations.py` - Payout logic
  - `test_analytics.py` - Metrics calculations
- [ ] Create integration tests:
  - `test_referral_integration.py` - End-to-end workflow
  - `test_email_integration.py` - Email service integration
  - `test_crm_integration.py` - Lead creation flow
- [ ] Add performance tests:
  - `test_bulk_eligibility.py` - 1000 contact processing
  - `test_concurrent_sending.py` - 100 concurrent requests
- [ ] Implement test coverage reporting (target: >90%)

### Phase 9: Monitoring & Security (Day 5)
- [ ] Add comprehensive logging:
  - Structured JSON logging for all operations
  - Performance metrics tracking
  - Error correlation IDs
  - Security event logging
- [ ] Implement audit trail:
  - All referral request attempts
  - Payout approvals and processing
  - Data access and modifications
  - Configuration changes
- [ ] Add rate limiting and throttling:
  - Per-contact request limits
  - Daily sending quotas
  - API rate limit respect
  - Backpressure handling
- [ ] Implement security controls:
  - Input validation and sanitization
  - SQL injection prevention
  - Data encryption at rest
  - Access control and permissions

### Phase 10: Documentation & Deployment (Day 5)
- [ ] Write comprehensive documentation:
  - API endpoint documentation
  - Configuration guide
  - Troubleshooting guide
  - Best practices document
- [ ] Create deployment playbooks:
  - Database migration procedures
  - Environment configuration
  - Service monitoring setup
  - Rollback procedures
- [ ] Add health checks:
  - Database connectivity
  - Email service health
  - CRM integration status
  - Queue health monitoring
- [ ] Prepare production deployment:
  - Environment variable configuration
  - Secret management setup
  - Monitoring dashboard configuration
  - Alert rule definitions

## Implementation Notes

### Performance Considerations
- Eligibility scoring should use cached data where possible
- Bulk operations for high-volume referral checking
- Index optimization for frequent queries
- Connection pooling for database operations

### Security Requirements
- All referral data must be encrypted at rest
- Audit logging for all financial transactions
- Rate limiting to prevent abuse
- Input validation for all user-provided data

### Integration Dependencies
- Instantly.ai for email sending and tracking
- CRM system for lead creation and management
- Payment processor for incentive payouts
- Analytics service for performance tracking

### Success Metrics
- Email delivery rate: >95%
- Open rate: >40%
- Reply rate: >15%
- Referral conversion rate: >5%
- Processing time: <5 minutes per request
- ROI on incentive program: >3:1

## Testing Requirements

1. **Unit Tests**: >90% code coverage
2. **Integration Tests**: All major workflows
3. **Performance Tests**: Handle 1000+ concurrent requests
4. **Security Tests**: Validate all security controls
5. **Load Tests**: System behavior under peak load

## Deliverables

1. Complete ReferralRequestAgent implementation
2. All database models and migrations
3. Comprehensive test suite
4. Integration with email and CRM services
5. Analytics and reporting capabilities
6. Documentation and deployment guides

## Approval Checklist

- [ ] All tests passing (unit, integration, performance)
- [ ] Code review completed and approved
- [ ] Security review passed
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Monitoring and alerting configured
- [ ] Rollback plan tested
- [ ] Stakeholder sign-off received
