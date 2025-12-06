# Correction Approval Orchestrator

## Category
System & Administration

## Purpose
Manage the workflow for approving and implementing agent corrections and improvements

## Key Responsibilities
- Coordinate correction approval process
- Route corrections to appropriate reviewers
- Track correction status and outcomes
- Implement approved corrections
- Maintain audit trail of all changes

## Process
1. **Correction Intake**
   - Receive correction requests from various sources
   - Classify correction type and priority
   - Extract context and metadata
   - Check for duplicate or similar corrections

2. **Review Routing**
   - Route corrections to appropriate reviewers
   - Set approval requirements based on impact
   - Notify reviewers of pending items
   - Track review deadlines

3. **Approval Workflow**
   - Manage multi-level approval process
   - Handle rejection with feedback
   - Coordinate between multiple reviewers
   - Escalate overdue items

4. **Implementation**
   - Apply approved corrections
   - Update agent configurations
   - Log implementation details
   - Verify changes applied correctly

## Database Tables
- `correction_approval_workflow` - Main workflow tracking
- `correction_reviewers` - Reviewer assignments
- `correction_audit_trail` - Complete audit log
- `correction_templates` - Reusable correction types

## Key Metrics
- Correction processing time
- Approval backlog size
- Reviewer response time
- Implementation success rate
- Correction effectiveness
- Audit compliance rate

## Triggers
- New correction submitted
- Review deadline approaching
- Correction approved/rejected
- Implementation completed
- Weekly compliance check

## Outputs
- Correction queue dashboard
- Reviewer workload reports
- Implementation status updates
- Audit compliance reports
- Correction effectiveness analysis

## Integrations
- All agent systems (correction sources)
- Agent configuration management
- Notification systems (Slack, email)
- Human approval interfaces
- Audit logging systems

## Cron Schedule
- Every minute - Check for new corrections
- Every 5 minutes - Send reminders for overdue items
- Hourly - Update status dashboards
- Daily - Generate compliance reports
- Weekly - Reviewer performance analysis

## Priority
Phase 1 - Critical for controlled improvement

## Dependencies
- All agent systems
- Human approval interfaces
- Configuration management
- Notification systems

## Human-in-the-Loop
- Review and approve corrections
- Provide feedback on rejected items
- Verify implementation success
- Set approval policies

## Correction Workflow Schema
```json
{
  "id": "uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:45:00Z",
  "agent_learning_id": "learn_123",
  "response_tracking_id": "resp_456",
  "correction_type": "prompt_adjustment",
  "proposed_correction": "Change tone from formal to conversational",
  "original_value": "Dear Mr. Smith, I am writing to inquire...",
  "reasoning": "Current tone too formal for cold outreach",
  "status": "approved",
  "priority": 7,
  "requested_by": "sarah_sales",
  "reviewed_by": "marketing_lead",
  "approved_by": "system_admin",
  "review_date": "2024-01-15T11:00:00Z",
  "approval_date": "2024-01-15T13:30:00Z",
  "implementation_date": "2024-01-15T14:45:00Z",
  "review_notes": "Good suggestion, matches our brand voice",
  "approval_conditions": "Test with 10% of traffic first",
  "rejection_reason": null,
  "estimated_impact": "medium",
  "impact_description": "Could improve reply rates by 5-10%",
  "risk_level": "low",
  "auto_approve": false,
  "auto_approve_conditions": {},
  "confidence_threshold": 0.8,
  "implemented": true,
  "implementation_details": {
    "prompt_file": "cold_email_v2.prompt",
    "backup_created": true,
    "test_percentage": 0.1
  },
  "rollback_available": true,
  "rollback_procedure": "Revert to previous prompt version",
  "post_implementation_metrics": {
    "reply_rate_before": 0.12,
    "reply_rate_after": 0.15,
    "improvement": 0.03
  },
  "success_criteria": "Reply rate increases by >2%",
  "actual_impact": {
    "reply_rate_improvement": 0.03,
    "positive_reply_increase": 0.02
  },
  "metadata": {},
  "tags": ["tone", "cold_email", "brand_voice"],
  "status_history": [
    {
      "status": "pending",
      "timestamp": "2024-01-15T10:30:00Z",
      "changed_by": "system"
    },
    {
      "status": "under_review",
      "timestamp": "2024-01-15T11:00:00Z",
      "changed_by": "marketing_lead"
    },
    {
      "status": "approved",
      "timestamp": "2024-01-15T13:30:00Z",
      "changed_by": "system_admin"
    },
    {
      "status": "implemented",
      "timestamp": "2024-01-15T14:45:00Z",
      "changed_by": "system"
    }
  ]
}
```

## Reviewer Assignment Logic
```python
async def assign_reviewer(correction):
    """
    Determine appropriate reviewer based on correction type and impact
    """
    # Default reviewer matrix
    reviewer_matrix = {
        'prompt_adjustment': {
            'low_impact': ['team_lead'],
            'medium_impact': ['team_lead', 'specialist'],
            'high_impact': ['team_lead', 'specialist', 'admin']
        },
        'template_update': {
            'low_impact': ['content_manager'],
            'medium_impact': ['content_manager', 'marketing_lead'],
            'high_impact': ['content_manager', 'marketing_lead', 'admin']
        },
        'configuration_change': {
            'low_impact': ['tech_lead'],
            'medium_impact': ['tech_lead', 'system_admin'],
            'high_impact': ['tech_lead', 'system_admin', 'admin']
        },
        'rule_addition': {
            'low_impact': ['operations_lead'],
            'medium_impact': ['operations_lead', 'compliance'],
            'high_impact': ['operations_lead', 'compliance', 'admin']
        }
    }

    # Determine impact level
    impact_level = calculate_impact(correction)

    # Get required reviewers
    correction_type = correction['correction_type']
    required_reviewers = reviewer_matrix.get(correction_type, {}).get(impact_level, ['admin'])

    # Check availability
    available_reviewers = await get_available_reviewers(required_reviewers)

    # Assign primary reviewer
    primary = available_reviewers[0] if available_reviewers else required_reviewers[0]

    # Assign backup reviewers if high impact
    backup_reviewers = []
    if impact_level == 'high' and len(available_reviewers) > 1:
        backup_reviewers = available_reviewers[1:]

    return {
        'primary': primary,
        'backup': backup_reviewers,
        'required': len(required_reviewers),
        'deadline': calculate_deadline(correction, impact_level)
    }
```

## Approval Workflow States
```python
class CorrectionStatus(Enum):
    PENDING = "pending"                    # Just submitted
    ROUTED = "routed"                      # Assigned to reviewer
    UNDER_REVIEW = "under_review"         # Being reviewed
    APPROVED = "approved"                  # Approved for implementation
    REJECTED = "rejected"                  # Rejected with feedback
    IMPLEMENTING = "implementing"          # Currently being implemented
    IMPLEMENTED = "implemented"            # Successfully implemented
    ROLLED_BACK = "rolled_back"            # Changes reverted
    CANCELLED = "cancelled"                # Withdrawn by requester

# State transitions
VALID_TRANSITIONS = {
    CorrectionStatus.PENDING: [
        CorrectionStatus.ROUTED,
        CorrectionStatus.CANCELLED
    ],
    CorrectionStatus.ROUTED: [
        CorrectionStatus.UNDER_REVIEW,
        CorrectionStatus.CANCELLED
    ],
    CorrectionStatus.UNDER_REVIEW: [
        CorrectionStatus.APPROVED,
        CorrectionStatus.REJECTED,
        CorrectionStatus.CANCELLED
    ],
    CorrectionStatus.APPROVED: [
        CorrectionStatus.IMPLEMENTING,
        CorrectionStatus.CANCELLED
    ],
    CorrectionStatus.IMPLEMENTING: [
        CorrectionStatus.IMPLEMENTED,
        CorrectionStatus.ROLLED_BACK
    ],
    CorrectionStatus.IMPLEMENTED: [
        CorrectionStatus.ROLLED_BACK
    ],
    CorrectionStatus.REJECTED: [
        CorrectionStatus.PENDING  # Can resubmit with changes
    ]
}
```

## Auto-Approval Rules
```python
async def check_auto_approve(correction):
    """
    Check if correction can be auto-approved based on rules
    """
    # Don't auto-approve high-risk corrections
    if correction['risk_level'] in ['high', 'critical']:
        return False

    # Auto-approval conditions
    auto_approve_conditions = {
        'low_risk_threshold': 0.95,
        'confidence_threshold': 0.9,
        'similar_success_rate': 0.85,
        'reviewer_workload': 10  # items
    }

    # Check if similar corrections were successful
    success_rate = await get_similar_correction_success_rate(correction)
    if success_rate < auto_approve_conditions['similar_success_rate']:
        return False

    # Check reviewer workload
    reviewer_queue = await get_reviewer_queue_size()
    if reviewer_queue < auto_approve_conditions['reviewer_workload']:
        return True  # Quick approval available

    # Check confidence level
    if correction.get('confidence', 0) < auto_approve_conditions['confidence_threshold']:
        return False

    return True
```

## Implementation Verification
```python
async def verify_implementation(correction_id):
    """
    Verify that approved correction was implemented correctly
    """
    correction = await get_correction(correction_id)

    verification = {
        'correction_id': correction_id,
        'verified': False,
        'checks_performed': [],
        'issues_found': []
    }

    # Check implementation based on type
    if correction['correction_type'] == 'prompt_adjustment':
        # Verify prompt was updated
        current_prompt = await get_agent_prompt(correction['agent_name'])
        expected_change = correction['proposed_correction']

        if expected_change in current_prompt:
            verification['checks_performed'].append('Prompt content verified')
            verification['verified'] = True
        else:
            verification['issues_found'].append('Prompt not updated correctly')

    elif correction['correction_type'] == 'template_update':
        # Verify template was updated
        template = await get_template(correction['template_id'])
        # ... verification logic

    elif correction['correction_type'] == 'configuration_change':
        # Verify configuration was changed
        config = await get_agent_config(correction['agent_name'])
        # ... verification logic

    # Log verification
    await log_verification(verification)

    return verification
```

## Performance Metrics Dashboard
```sql
-- Correction processing time
SELECT
    AVG(EXTRACT(EPOCH FROM (review_date - created_at))/60) as avg_review_minutes,
    AVG(EXTRACT(EPOCH FROM (approval_date - review_date))/60) as avg_approval_minutes,
    AVG(EXTRACT(EPOCH FROM (implementation_date - approval_date))/60) as avg_implementation_minutes
FROM correction_approval_workflow
WHERE status = 'implemented'
    AND created_at >= NOW() - INTERVAL '30 days';

-- Reviewer performance
SELECT
    reviewer,
    COUNT(*) as reviews_completed,
    AVG(EXTRACT(EPOCH FROM (review_date - created_at))/60) as avg_review_time,
    COUNT(CASE WHEN status = 'approved' THEN 1 END) * 100.0 / COUNT(*) as approval_rate
FROM correction_approval_workflow
WHERE reviewed_at >= NOW() - INTERVAL '30 days'
GROUP BY reviewer
ORDER BY reviews_completed DESC;

-- Correction effectiveness
SELECT
    correction_type,
    COUNT(*) as total_corrections,
    COUNT(CASE WHEN actual_impact->>'reply_rate_improvement' > 0 THEN 1 END) as successful_corrections,
    AVG(actual_impact->>'reply_rate_improvement') as avg_improvement
FROM correction_approval_workflow
WHERE status = 'implemented'
    AND implementation_date >= NOW() - INTERVAL '90 days'
GROUP BY correction_type;
```

## Notification Templates
```python
# Review assignment notification
review_assignment_template = """
New correction requires your review:

Type: {correction_type}
Priority: {priority}
Impact: {estimated_impact}

Proposed Change:
{proposed_correction}

Reasoning:
{reasoning}

Review Deadline: {deadline}

[Review Now]({review_link}) | [View Details]({details_link})
"""

# Approval notification
approval_notification_template = """
Your correction has been approved!

Correction ID: {correction_id}
Approved by: {approved_by}

It will be implemented by {implementation_date}.

[Track Progress]({progress_link})
"""

# Rejection notification
rejection_notification_template = """
Your correction requires changes:

Correction ID: {correction_id}
Rejected by: {rejected_by}

Reason: {rejection_reason}

Suggested Changes:
{suggested_changes}

[Resubmit]({resubmit_link})
"""
```

## API Endpoints
- `POST /api/corrections` - Submit new correction
- `GET /api/corrections/pending` - Get pending corrections
- `POST /api/corrections/{id}/review` - Review correction
- `GET /api/corrections/{id}/status` - Check status
- `GET /api/corrections/analytics` - Performance analytics
- `POST /api/corrections/{id}/rollback` - Rollback correction
