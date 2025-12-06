# Task: Implement Testimonial Request Agent

**Task ID:** 037
**Priority:** High
**Estimated Time:** 3-4 days
**Spec File:** `/specs/agents/retention-testimonial-request.md`
**Agent Category:** Client Success & Retention
**Phase:** Phase 5 - Retention & Growth

---

## Overview

Implement the Testimonial Request Agent that automatically identifies satisfied clients and requests testimonials at optimal times. The agent handles the complete workflow from qualification to publishing, including multi-format collection (written, video, case studies), usage rights management, and incentive processing.

---

## Implementation Checklist

### Database Schema (Day 1)
- [ ] Create `testimonial_requests` table with all required fields
- [ ] Create `testimonials` table with approval and publishing fields
- [ ] Create `testimonial_incentives` table with tracking fields
- [ ] Add proper indexes for performance
- [ ] Create database migration file
- [ ] Test schema creation and constraints

### Core Agent Implementation (Day 2)
- [ ] Create `TestimonialRequestAgent` class extending `BaseAgent`
- [ ] Implement system prompt with clear responsibilities
- [ ] Add all required tools via `register_tool()`
- [ ] Implement `process_task()` with task routing
- [ ] Add proper error handling and logging
- [ ] Create helper methods for scoring and recommendations

### Qualification System (Day 2)
- [ ] Implement `_qualify_clients()` method
- [ ] Create scoring algorithm (1-10 scale)
- [ ] Add recommendation logic for testimonial types
- [ ] Integrate with Satisfaction Survey Agent data
- [ ] Connect to Project Management Agent for completion status
- [ ] Test qualification logic with various scenarios

### Email & Request System (Day 2-3)
- [ ] Implement `_send_testimonial_request()` method
- [ ] Create email template system with personalization
- [ ] Add support for written, video, and case study requests
- [ ] Integrate with Email Service (Instantly.ai/SendGrid)
- [ ] Implement form link generation
- [ ] Add video recording link support
- [ ] Create follow-up scheduling system

### Response Processing (Day 3)
- [ ] Implement `_collect_testimonial_response()` method
- [ ] Add support for multiple response formats
- [ ] Create testimonial record from responses
- [ ] Implement automatic thank-you emails
- [ ] Add incentive processing logic
- [ ] Handle video upload processing

### Review & Approval Workflow (Day 3)
- [ ] Implement `_review_testimonial()` method
- [ ] Create approval/rejection workflow
- [ ] Add usage rights management
- [ ] Implement client data display controls
- [ ] Add strength scoring system (1-5)
- [ ] Create tag and categorization system
- [ ] Hand off to human review agent

### Publishing System (Day 3-4)
- [ ] Implement `_publish_testimonial()` method
- [ ] Add website testimonial page publishing
- [ ] Create social media publishing workflow
- [ ] Implement case study creation
- [ ] Add published location tracking
- [ ] Create publishing audit trail

### Testing (Day 4)
- [ ] Write unit tests for all agent methods (>90% coverage)
- [ ] Test qualification logic with various client scenarios
- [ ] Test email generation and sending
- [ ] Test response processing and validation
- [ ] Test review workflow transitions
- [ ] Test publishing to all platforms

### Integration Tests (Day 4)
- [ ] Test complete end-to-end workflow
- [ ] Test agent handoffs to Satisfaction Survey
- [ ] Test email service integration
- [ ] Test database transactions and rollbacks
- [ ] Test concurrent processing scenarios
- [ ] Test error recovery mechanisms

### Error Handling (Throughout)
- [ ] Implement retry logic for email failures
- [ ] Add database constraint violation handling
- [ ] Create incentive processing error recovery
- [ ] Add publishing failure rollback
- [ ] Implement comprehensive logging
- [ ] Create admin alerting for critical failures

### Documentation & Code Quality (Throughout)
- [ ] Add comprehensive docstrings
- [ ] Include type hints for all methods
- [ ] Follow project conventions (snake_case, double quotes)
- [ ] Ensure async/await patterns for I/O
- [ ] Add inline comments for complex logic
- [ ] Verify code passes all linting and formatting

---

## Acceptance Criteria

1. **Functional Requirements**
   - [ ] Agent can identify qualified clients based on satisfaction scores and project success
   - [ ] Sends personalized testimonial requests with proper templates
   - [ ] Collects and processes responses in multiple formats
   - [ ] Manages complete review and approval workflow
   - [ ] Publishes approved testimonials to specified platforms

2. **Quality Requirements**
   - [ ] All tests pass with >90% unit coverage and >85% integration coverage
   - [ ] No MyPy type errors
   - [ ] Code passes all Ruff linting and formatting checks
   - [ ] Database migrations run successfully
   - [ ] All error scenarios have proper handling

3. **Integration Requirements**
   - [ ] Successfully integrates with Email Service
   - [ ] Connects to Satisfaction Survey Agent for scores
   - [ ] Integrates with Project Management Agent for completion status
   - [ ] Handoffs work correctly with Human Review workflow
   - [ ] Webhook processing functions correctly

4. **Performance Requirements**
   - [ ] Can qualify 1000+ clients in under 30 seconds
   - [ ] Can send 100 emails/hour without rate limiting issues
   - [ ] Database queries use indexes effectively
   - [ ] Concurrent response processing works correctly

---

## Implementation Notes

### Key Patterns to Follow

1. **Use existing BaseAgent patterns** from `/src/agents/base_agent.py`
2. **Follow database schema patterns** from other agent specs (e.g., `retention-churn-risk.md`)
3. **Use proper async/await** for all I/O operations
4. **Implement structured logging** via `get_agent_logger()`
5. **Use BaseIntegrationClient** for email service integration

### Dependencies to Configure

1. **Email Service Integration** - Check `.env.example` for configuration
2. **Survey/Form Service** - For testimonial collection forms
3. **Storage Service** - For video file storage
4. **Database Models** - Create if not exists in `/src/models/`

### Testing Requirements

1. **Mock external services** in unit tests
2. **Use test database** for integration tests
3. **Test all error paths** including network failures
4. **Verify database constraints** are enforced
5. **Test concurrent scenarios** for race conditions

---

## Definition of Done

This task is complete when:

1. All implementation checklist items are checked off
2. All acceptance criteria are met
3. Tests pass with required coverage
4. Code passes all quality checks (`make check`)
5. Agent can handle the complete testimonial workflow
6. Documentation is updated if needed
7. Task is moved to `_completed/` with notes

---

## Related Tasks

- Prerequisite: Satisfaction Survey Agent implementation
- Prerequisite: Project Management Agent integration
- Related: Human Review workflow setup
- Related: Website testimonial page development
- Future: Video testimonial processing enhancement
- Future: Advanced testimonial analytics dashboard
