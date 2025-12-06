# System Correction Approval Orchestrator Agent - Production Specification

**Status:** Ready to Build
**Last Updated:** 2025-12-05
**Refined From:** plan/agents/system-correction-approval-orchestrator.md

## Overview

**Category**: System & Administration
**Priority**: Phase 1 - Critical for controlled improvement
**Agent Name**: `system_correction_approval_orchestrator`
**Purpose**: Orchestrate the complete workflow for reviewing, approving, and implementing agent corrections with multi-level approval, rollback capability, and comprehensive audit trail.

The Correction Approval Orchestrator is the guardian of system quality and safety, ensuring that all agent improvements are properly vetted, tested, and implemented with appropriate oversight before reaching production. It manages risk assessment, reviewer routing, approval workflows, implementation, A/B testing validation, and emergency rollback procedures.

---

## Architecture

### High-Level Design
```
┌─────────────────────────────────────────────────────────────────┐
│          Correction Approval Orchestrator Agent                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────────┐  │
│  │    Risk    │  │  Reviewer  │  │   Approval Workflow      │  │
│  │ Classifier │  │  Router    │  │   State Machine          │  │
│  └────────────┘  └────────────┘  └──────────────────────────┘  │
│         │               │                      │                │
│  ┌──────▼───────┐ ┌────▼────────┐   ┌────────▼────────────┐  │
│  │ Auto-Approve │ │ Notification │   │  Implementation     │  │
│  │   Engine     │ │   Service    │   │  & Rollback Engine  │  │
│  └──────────────┘ └─────────────┘   └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  PostgreSQL        │
                    │  - correction_     │
                    │    approval_       │
                    │    workflow        │
                    │  - correction_     │
                    │    reviewers       │
                    │  - correction_     │
                    │    audit_trail     │
                    │  - correction_     │
                    │    templates       │
                    └────────────────────┘
```

### Integration Points
- **Receives corrections from:**
  - `system_learning_feedback` - Learning-based suggestions
  - `system_agent_performance_analyst` - Performance-based alerts
  - All agents via human-in-the-loop workflows
  - Manual submissions via API

- **Triggers actions on:**
  - `system_response_outcome_tracker` - A/B test orchestration
  - `system_audit_log` - Complete audit trail
  - Slack/Email - Reviewer notifications
  - All 79+ agents - Configuration updates

---

## Configuration

```python
from typing import Optional
from pydantic import Field
from enum import Enum

class ApprovalConfig:
    """Configuration for the Correction Approval Orchestrator."""

    # Approval thresholds
    auto_approve_confidence: float = 0.95
    similar_success_rate: float = 0.85
    reviewer_workload_threshold: int = 10

    # Risk thresholds
    low_risk_threshold: float = 0.3
    medium_risk_threshold: float = 0.6
    high_risk_threshold: float = 0.8

    # Timing settings
    review_deadline_hours: dict[str, int] = {
        "low": 72,      # 3 days
        "medium": 48,   # 2 days
        "high": 24,     # 1 day
        "critical": 4   # 4 hours
    }

    # Reminder settings
    first_reminder_hours: int = 12
    escalation_hours: int = 24
    max_reminders: int = 3

    # Rollback settings
    rollback_window_hours: int = 72
    auto_rollback_on_failure: bool = True
    rollback_confirmation_required: bool = True

class CorrectionType(str, Enum):
    """Types of corrections."""
    PROMPT_ADJUSTMENT = "prompt_adjustment"
    TEMPLATE_UPDATE = "template_update"
    CONFIGURATION_CHANGE = "configuration_change"
    RULE_ADDITION = "rule_addition"
    PARAMETER_TUNING = "parameter_tuning"
    FEW_SHOT_EXAMPLE = "few_shot_example"
    CONSTRAINT_UPDATE = "constraint_update"

class CorrectionStatus(str, Enum):
    """Correction approval workflow states."""
    PENDING = "pending"              # Just submitted
    ROUTED = "routed"                # Assigned to reviewer
    UNDER_REVIEW = "under_review"   # Being reviewed
    APPROVED = "approved"            # Approved for implementation
    REJECTED = "rejected"            # Rejected with feedback
    IMPLEMENTING = "implementing"    # Currently being implemented
    IMPLEMENTED = "implemented"      # Successfully implemented
    TESTING = "testing"              # A/B test in progress
    VALIDATED = "validated"          # Test results confirm success
    ROLLED_BACK = "rolled_back"      # Changes reverted
    CANCELLED = "cancelled"          # Withdrawn by requester

class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"            # Auto-approve eligible, single reviewer
    MEDIUM = "medium"      # Single reviewer required
    HIGH = "high"          # Multi-reviewer required
    CRITICAL = "critical"  # Emergency escalation, admin approval

class ImpactLevel(str, Enum):
    """Impact assessment levels."""
    LOW = "low"         # <5% of outputs affected
    MEDIUM = "medium"   # 5-20% of outputs affected
    HIGH = "high"       # 20-50% of outputs affected
    CRITICAL = "critical"  # >50% of outputs or financial impact
```

---

## System Prompt

```
You are the Correction Approval Orchestrator Agent for Smarter Team, the guardian of system quality and controlled improvement.

Your mission is to manage the complete lifecycle of agent corrections and improvements, from initial submission through approval, implementation, validation, and potential rollback, ensuring all changes are safe, effective, and properly governed.

**Core Responsibilities:**
1. Classify correction risk level and impact scope using data-driven analysis
2. Route corrections to appropriate reviewers based on type, impact, and expertise
3. Orchestrate multi-level approval workflows with proper escalation
4. Implement approved corrections with rollback capability and monitoring
5. Coordinate A/B testing to validate correction effectiveness
6. Execute emergency rollbacks when corrections degrade performance
7. Maintain comprehensive audit trail of all correction decisions and implementations
8. Generate compliance reports for correction governance and oversight

**Risk Classification Framework:**
- LOW RISK: Single-field updates, typo fixes, minor wording changes, <5% traffic impact
- MEDIUM RISK: Template changes, prompt modifications, 5-20% traffic impact
- HIGH RISK: Multi-agent changes, rule additions, configuration updates, >20% traffic
- CRITICAL RISK: Financial logic, security-related, system-wide changes, compliance impact

**Approval Requirements by Risk Level:**
- LOW: Auto-approve if confidence >95% and similar corrections succeeded >85%
- MEDIUM: Single reviewer approval required, 48-hour SLA
- HIGH: Two-reviewer consensus required, 24-hour SLA
- CRITICAL: Admin approval + technical review + business sign-off, 4-hour SLA

**Behavioral Guidelines:**
- Be conservative: When in doubt, escalate to higher risk level
- Be transparent: All stakeholders receive clear status updates
- Be accountable: Every decision is logged with full reasoning
- Be responsive: Meet SLAs, send timely reminders, escalate overdue reviews
- Be data-driven: Use historical data to inform approval decisions
- Be protective: Always maintain rollback capability for implemented changes

**Decision Making:**
- Auto-Approval Criteria:
  * Risk level = LOW
  * Confidence score ≥ 0.95
  * Similar corrections success rate ≥ 0.85
  * No reviewer backlog (queue < 10 items)
  * No recent similar failures (30-day window)

- Reviewer Selection:
  * Match correction type to reviewer expertise
  * Balance reviewer workload
  * Respect reviewer availability
  * Escalate if no suitable reviewer available

- Implementation Strategy:
  * Start with small traffic percentage (10%)
  * Monitor key metrics for degradation
  * Gradually increase if successful
  * Auto-rollback if metrics decline >5%

- Rollback Triggers:
  * Performance degradation >5% in key metrics
  * Error rate increase >10%
  * Manual rollback request from reviewer/admin
  * System health check failures

**Communication Style:**
- Review requests: Clear, concise, with all context and examples
- Status updates: Informative with timeline and next steps
- Approval notifications: Include implementation timeline and success criteria
- Rejection feedback: Specific, actionable, with improvement suggestions
- Rollback alerts: Immediate, urgent, with impact assessment and recovery plan

You have access to tools for risk classification, reviewer assignment, auto-approval checking, implementation, A/B testing, rollback, status tracking, and audit reporting. Use these tools systematically to maintain the perfect balance between continuous improvement and system stability.
```

---

## Agent Implementation

### Class Definition

```python
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json
import asyncio
from collections import defaultdict, Counter

from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger


@dataclass
class CorrectionRequest:
    """Structured data for a correction submission."""
    id: str
    created_at: datetime
    agent_learning_id: Optional[str]
    response_tracking_id: Optional[str]
    correction_type: CorrectionType
    proposed_correction: str
    original_value: Optional[str]
    reasoning: str
    requested_by: str
    priority: int  # 0-10
    metadata: Dict[str, Any]


@dataclass
class ReviewerAssignment:
    """Reviewer assignment details."""
    correction_id: str
    primary_reviewer: str
    backup_reviewers: List[str]
    required_approvals: int
    deadline: datetime
    expertise_match: float  # 0-1
    workload_balance: float  # 0-1


@dataclass
class ImplementationResult:
    """Result of correction implementation."""
    correction_id: str
    success: bool
    implementation_time: datetime
    traffic_percentage: float
    rollback_token: str
    monitoring_config: Dict[str, Any]
    errors: List[str]


class CorrectionApprovalOrchestrator(BaseAgent):
    """
    Correction Approval Orchestrator agent for managing the complete correction lifecycle.

    Handles risk assessment, routing, approval, implementation, testing, and rollback.
    """

    def __init__(self):
        super().__init__(
            name="system_correction_approval_orchestrator",
            description="Manages correction approval workflow with risk assessment and rollback"
        )

        # Register tools
        self.register_tool(
            classify_correction_risk,
            "classify_correction_risk",
            "Determine risk level based on correction type and impact"
        )
        self.register_tool(
            assign_reviewer,
            "assign_reviewer",
            "Route correction to appropriate reviewer based on expertise"
        )
        self.register_tool(
            check_auto_approve_eligibility,
            "check_auto_approve_eligibility",
            "Check if correction can be auto-approved"
        )
        self.register_tool(
            implement_correction,
            "implement_correction",
            "Apply approved correction to agent configuration"
        )
        self.register_tool(
            trigger_ab_test,
            "trigger_ab_test",
            "Enable A/B testing for validation"
        )
        self.register_tool(
            rollback_correction,
            "rollback_correction",
            "Revert failed or problematic changes"
        )
        self.register_tool(
            track_approval_status,
            "track_approval_status",
            "Monitor approval workflow state"
        )
        self.register_tool(
            generate_audit_report,
            "generate_audit_report",
            "Create compliance audit trail"
        )

    @property
    def system_prompt(self) -> str:
        # Return the system prompt from above
        return """..."""  # Full prompt from above

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process correction approval tasks.

        Supports:
        - submit_correction: New correction submission
        - process_review: Handle review decision
        - implement_approved: Implement approved corrections
        - check_overdue: Check for overdue reviews
        - validate_results: Validate A/B test results
        - emergency_rollback: Execute emergency rollback
        """
        task_type = task.get("type")

        if task_type == "submit_correction":
            return await self._submit_correction(task.get("correction_data"))
        elif task_type == "process_review":
            return await self._process_review(task.get("review_data"))
        elif task_type == "implement_approved":
            return await self._implement_approved(task.get("correction_ids"))
        elif task_type == "check_overdue":
            return await self._check_overdue_reviews()
        elif task_type == "validate_results":
            return await self._validate_ab_test_results(task.get("correction_id"))
        elif task_type == "emergency_rollback":
            return await self._emergency_rollback(task.get("correction_id"), task.get("reason"))
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _submit_correction(self, correction_data: dict) -> dict[str, Any]:
        """Process new correction submission."""
        # 1. Validate correction data
        # 2. Classify risk level
        # 3. Check auto-approve eligibility
        # 4. Route to reviewer or auto-approve
        # 5. Send notifications
        pass

    async def _process_review(self, review_data: dict) -> dict[str, Any]:
        """Process review decision (approve/reject)."""
        # 1. Update correction status
        # 2. Check if all required approvals received
        # 3. Queue for implementation if approved
        # 4. Send feedback if rejected
        pass

    async def _implement_approved(self, correction_ids: List[str]) -> dict[str, Any]:
        """Implement approved corrections."""
        # 1. Retrieve correction details
        # 2. Create rollback point
        # 3. Apply changes with traffic percentage
        # 4. Enable monitoring
        # 5. Trigger A/B test if configured
        pass

    async def _check_overdue_reviews(self) -> dict[str, Any]:
        """Check for overdue reviews and send reminders."""
        # 1. Query corrections with missed deadlines
        # 2. Send reminder notifications
        # 3. Escalate if max reminders reached
        pass

    async def _validate_ab_test_results(self, correction_id: str) -> dict[str, Any]:
        """Validate A/B test results."""
        # 1. Retrieve test metrics
        # 2. Compare against success criteria
        # 3. Make go/no-go decision
        # 4. Execute rollback if failed
        # 5. Increase traffic if successful
        pass

    async def _emergency_rollback(self, correction_id: str, reason: str) -> dict[str, Any]:
        """Execute emergency rollback."""
        # 1. Retrieve rollback configuration
        # 2. Revert changes immediately
        # 3. Verify rollback success
        # 4. Send alerts
        # 5. Update audit trail
        pass
```

---

## Tool Definitions

### 1. classify_correction_risk

**Purpose**: Determine risk level and impact scope based on correction characteristics

**Parameters**:
```python
{
    "correction_id": str,
    "correction_type": CorrectionType,
    "affected_agents": list[str],
    "traffic_impact": float,          # 0-1, percentage of traffic affected
    "has_financial_impact": bool,
    "has_security_impact": bool,
    "has_compliance_impact": bool,
    "similar_corrections": list[dict],  # Historical similar corrections
    "proposed_changes": dict[str, Any]
}
```

**Returns**:
```python
{
    "correction_id": str,
    "risk_level": RiskLevel,
    "impact_level": ImpactLevel,
    "risk_score": float,              # 0-1
    "impact_score": float,            # 0-1
    "risk_factors": list[dict],       # Individual risk contributors
    "mitigation_required": list[str], # Required safety measures
    "auto_approve_eligible": bool,
    "reasoning": str,
    "confidence": float               # 0-1
}
```

**Implementation**:
```python
async def classify_correction_risk(
    correction_id: str,
    correction_type: CorrectionType,
    affected_agents: list[str],
    traffic_impact: float,
    has_financial_impact: bool = False,
    has_security_impact: bool = False,
    has_compliance_impact: bool = False,
    similar_corrections: list[dict] | None = None,
    proposed_changes: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Classify correction risk using multi-factor analysis.

    Risk assessment considers:
    - Correction type (prompt vs. config vs. financial logic)
    - Traffic impact (% of outputs affected)
    - Domain impact (financial, security, compliance)
    - Historical success rate of similar corrections
    - Number of agents affected
    - Scope of changes (single field vs. multi-field)
    """
    from sqlalchemy import select, and_
    from src.database import get_async_session
    from src.models import CorrectionApprovalWorkflow
    import numpy as np

    logger = get_agent_logger("correction_orchestrator.risk")

    risk_factors = []
    risk_score = 0.0

    # Factor 1: Correction type base risk (0-0.3)
    type_risks = {
        CorrectionType.PROMPT_ADJUSTMENT: 0.1,
        CorrectionType.TEMPLATE_UPDATE: 0.15,
        CorrectionType.FEW_SHOT_EXAMPLE: 0.05,
        CorrectionType.PARAMETER_TUNING: 0.2,
        CorrectionType.CONFIGURATION_CHANGE: 0.25,
        CorrectionType.RULE_ADDITION: 0.3,
        CorrectionType.CONSTRAINT_UPDATE: 0.2,
    }
    type_risk = type_risks.get(correction_type, 0.2)
    risk_score += type_risk
    risk_factors.append({
        "factor": "correction_type",
        "value": correction_type.value,
        "risk_contribution": type_risk,
        "weight": 0.3
    })

    # Factor 2: Traffic impact (0-0.3)
    traffic_risk = traffic_impact * 0.3
    risk_score += traffic_risk
    risk_factors.append({
        "factor": "traffic_impact",
        "value": traffic_impact,
        "risk_contribution": traffic_risk,
        "weight": 0.3
    })

    # Factor 3: Domain impacts (0-0.2)
    domain_risk = 0.0
    if has_financial_impact:
        domain_risk += 0.1
    if has_security_impact:
        domain_risk += 0.1
    if has_compliance_impact:
        domain_risk += 0.1
    domain_risk = min(domain_risk, 0.2)  # Cap at 0.2
    risk_score += domain_risk
    risk_factors.append({
        "factor": "domain_impacts",
        "value": {
            "financial": has_financial_impact,
            "security": has_security_impact,
            "compliance": has_compliance_impact
        },
        "risk_contribution": domain_risk,
        "weight": 0.2
    })

    # Factor 4: Agent scope (0-0.1)
    agent_count = len(affected_agents)
    agent_risk = min(agent_count / 79.0, 1.0) * 0.1  # 79 total agents
    risk_score += agent_risk
    risk_factors.append({
        "factor": "agent_scope",
        "value": agent_count,
        "risk_contribution": agent_risk,
        "weight": 0.1
    })

    # Factor 5: Historical success (0-0.1, reduces risk)
    if similar_corrections:
        success_count = sum(1 for c in similar_corrections if c.get("success"))
        success_rate = success_count / len(similar_corrections)
        # High success rate reduces risk
        history_risk = (1 - success_rate) * 0.1
    else:
        # No history = higher risk
        history_risk = 0.1

    risk_score += history_risk
    risk_factors.append({
        "factor": "historical_success",
        "value": 1 - (history_risk / 0.1) if similar_corrections else 0,
        "risk_contribution": history_risk,
        "weight": 0.1
    })

    # Normalize risk score to 0-1
    risk_score = min(risk_score, 1.0)

    # Determine risk level
    if risk_score < 0.3:
        risk_level = RiskLevel.LOW
    elif risk_score < 0.6:
        risk_level = RiskLevel.MEDIUM
    elif risk_score < 0.8:
        risk_level = RiskLevel.HIGH
    else:
        risk_level = RiskLevel.CRITICAL

    # Override to CRITICAL if critical domains involved
    if has_financial_impact or has_security_impact:
        risk_level = RiskLevel.CRITICAL

    # Determine impact level
    if traffic_impact < 0.05:
        impact_level = ImpactLevel.LOW
    elif traffic_impact < 0.2:
        impact_level = ImpactLevel.MEDIUM
    elif traffic_impact < 0.5:
        impact_level = ImpactLevel.HIGH
    else:
        impact_level = ImpactLevel.CRITICAL

    # Auto-approve eligibility
    auto_approve_eligible = (
        risk_level == RiskLevel.LOW and
        impact_level == ImpactLevel.LOW and
        not has_financial_impact and
        not has_security_impact and
        not has_compliance_impact
    )

    # Determine required mitigations
    mitigation_required = []
    if risk_score > 0.6:
        mitigation_required.append("a_b_testing")
    if traffic_impact > 0.2:
        mitigation_required.append("gradual_rollout")
    if has_financial_impact or has_security_impact:
        mitigation_required.append("admin_approval")
        mitigation_required.append("manual_verification")
    if agent_count > 10:
        mitigation_required.append("multi_agent_testing")

    # Build reasoning
    reasoning = f"""
Risk Classification Analysis:
- Risk Level: {risk_level.value.upper()}
- Impact Level: {impact_level.value.upper()}
- Risk Score: {risk_score:.2f}/1.0

Key Risk Factors:
{chr(10).join(f"- {rf['factor']}: {rf['risk_contribution']:.2f} (weight: {rf['weight']})" for rf in risk_factors)}

Mitigations Required: {', '.join(mitigation_required) if mitigation_required else 'None'}
Auto-Approve Eligible: {'Yes' if auto_approve_eligible else 'No'}
""".strip()

    logger.info(
        f"Classified correction risk: {risk_level.value}",
        extra={
            "correction_id": correction_id,
            "risk_level": risk_level.value,
            "risk_score": risk_score,
            "impact_level": impact_level.value,
            "auto_approve_eligible": auto_approve_eligible
        }
    )

    return {
        "correction_id": correction_id,
        "risk_level": risk_level,
        "impact_level": impact_level,
        "risk_score": risk_score,
        "impact_score": traffic_impact,
        "risk_factors": risk_factors,
        "mitigation_required": mitigation_required,
        "auto_approve_eligible": auto_approve_eligible,
        "reasoning": reasoning,
        "confidence": 0.9
    }
```

**Error Handling**:
- Invalid correction type → Default to MEDIUM risk
- Missing traffic impact → Assume HIGH (50%)
- Database query failure → Use conservative risk classification
- Invalid historical data → Ignore history, increase risk slightly

---

### 2. assign_reviewer

**Purpose**: Route correction to appropriate reviewer based on type and expertise

**Parameters**:
```python
{
    "correction_id": str,
    "correction_type": CorrectionType,
    "risk_level": RiskLevel,
    "impact_level": ImpactLevel,
    "affected_agents": list[str],
    "required_approvals": int  # Calculated from risk level
}
```

**Returns**:
```python
{
    "correction_id": str,
    "primary_reviewer": str,
    "backup_reviewers": list[str],
    "required_approvals": int,
    "deadline": datetime,
    "expertise_match": float,    # 0-1
    "workload_balance": float,   # 0-1
    "notification_sent": bool,
    "notification_channels": list[str]
}
```

**Implementation**:
```python
async def assign_reviewer(
    correction_id: str,
    correction_type: CorrectionType,
    risk_level: RiskLevel,
    impact_level: ImpactLevel,
    affected_agents: list[str],
    required_approvals: int = 1
) -> dict[str, Any]:
    """
    Assign correction to appropriate reviewer(s) based on expertise and availability.

    Reviewer selection criteria:
    - Expertise match with correction type
    - Current workload (avoid overload)
    - Response time history
    - Availability status
    """
    from sqlalchemy import select, and_
    from src.database import get_async_session
    from src.models import CorrectionReviewer
    from datetime import datetime, timedelta

    logger = get_agent_logger("correction_orchestrator.assign")

    # Reviewer expertise matrix
    reviewer_matrix = {
        CorrectionType.PROMPT_ADJUSTMENT: ["content_manager", "marketing_lead"],
        CorrectionType.TEMPLATE_UPDATE: ["content_manager", "copywriting_specialist"],
        CorrectionType.CONFIGURATION_CHANGE: ["tech_lead", "system_admin"],
        CorrectionType.RULE_ADDITION: ["operations_lead", "compliance_manager"],
        CorrectionType.PARAMETER_TUNING: ["data_scientist", "ml_engineer"],
        CorrectionType.FEW_SHOT_EXAMPLE: ["content_manager", "ai_specialist"],
        CorrectionType.CONSTRAINT_UPDATE: ["tech_lead", "qa_lead"],
    }

    # Get eligible reviewers for this correction type
    eligible_reviewers = reviewer_matrix.get(correction_type, ["admin"])

    # Escalate to admin for critical risk
    if risk_level == RiskLevel.CRITICAL:
        if "admin" not in eligible_reviewers:
            eligible_reviewers.append("admin")

    async with get_async_session() as session:
        # Get reviewer workload
        reviewer_workload = {}
        for reviewer in eligible_reviewers:
            query = select(CorrectionReviewer).where(
                and_(
                    CorrectionReviewer.reviewer == reviewer,
                    CorrectionReviewer.status.in_(["pending", "under_review"])
                )
            )
            result = await session.execute(query)
            pending_count = len(result.scalars().all())
            reviewer_workload[reviewer] = pending_count

    # Sort by workload (ascending)
    sorted_reviewers = sorted(
        eligible_reviewers,
        key=lambda r: reviewer_workload.get(r, 0)
    )

    # Select primary reviewer (lowest workload)
    primary_reviewer = sorted_reviewers[0] if sorted_reviewers else "admin"

    # Select backup reviewers
    backup_reviewers = sorted_reviewers[1:required_approvals] if len(sorted_reviewers) > 1 else []

    # Calculate deadline based on risk level
    deadline_hours = {
        RiskLevel.LOW: 72,
        RiskLevel.MEDIUM: 48,
        RiskLevel.HIGH: 24,
        RiskLevel.CRITICAL: 4
    }
    hours = deadline_hours.get(risk_level, 48)
    deadline = datetime.utcnow() + timedelta(hours=hours)

    # Calculate expertise match (simplified)
    expertise_match = 1.0 if primary_reviewer in eligible_reviewers[:2] else 0.7

    # Calculate workload balance
    current_workload = reviewer_workload.get(primary_reviewer, 0)
    workload_balance = max(0, 1 - (current_workload / 10.0))  # 10 items = full load

    # Send notification
    notification_sent = await _send_reviewer_notification(
        primary_reviewer,
        correction_id,
        correction_type,
        risk_level,
        deadline
    )

    logger.info(
        f"Assigned reviewer: {primary_reviewer}",
        extra={
            "correction_id": correction_id,
            "primary_reviewer": primary_reviewer,
            "backup_reviewers": backup_reviewers,
            "deadline": deadline.isoformat(),
            "workload": current_workload
        }
    )

    return {
        "correction_id": correction_id,
        "primary_reviewer": primary_reviewer,
        "backup_reviewers": backup_reviewers,
        "required_approvals": required_approvals,
        "deadline": deadline,
        "expertise_match": expertise_match,
        "workload_balance": workload_balance,
        "notification_sent": notification_sent,
        "notification_channels": ["email", "slack"]
    }


async def _send_reviewer_notification(
    reviewer: str,
    correction_id: str,
    correction_type: CorrectionType,
    risk_level: RiskLevel,
    deadline: datetime
) -> bool:
    """Send notification to assigned reviewer."""
    # Implementation would integrate with email/Slack
    # For now, placeholder
    return True
```

**Error Handling**:
- No eligible reviewers → Assign to admin
- Reviewer unavailable → Select backup from list
- Notification failure → Log error, continue with assignment
- Database connection error → Retry 3x, fallback to default reviewer

---

### 3. check_auto_approve_eligibility

**Purpose**: Determine if correction meets criteria for automatic approval

**Parameters**:
```python
{
    "correction_id": str,
    "risk_level": RiskLevel,
    "confidence_score": float,
    "similar_corrections": list[dict],
    "reviewer_queue_size": int
}
```

**Returns**:
```python
{
    "correction_id": str,
    "auto_approve_eligible": bool,
    "eligibility_checks": dict[str, bool],
    "similar_success_rate": float,
    "confidence_threshold_met": bool,
    "reasoning": str,
    "bypass_reasons": list[str]  # Why auto-approve was denied
}
```

**Implementation**:
```python
async def check_auto_approve_eligibility(
    correction_id: str,
    risk_level: RiskLevel,
    confidence_score: float,
    similar_corrections: list[dict] | None = None,
    reviewer_queue_size: int = 0
) -> dict[str, Any]:
    """
    Check if correction can be auto-approved based on confidence and history.

    Auto-approval criteria (ALL must be true):
    1. Risk level = LOW
    2. Confidence score ≥ 0.95
    3. Similar corrections success rate ≥ 0.85
    4. Reviewer queue size < 10 (no backlog)
    5. No recent similar failures in last 30 days
    """
    logger = get_agent_logger("correction_orchestrator.auto_approve")

    eligibility_checks = {}
    bypass_reasons = []

    # Check 1: Risk level must be LOW
    risk_check = risk_level == RiskLevel.LOW
    eligibility_checks["risk_level_low"] = risk_check
    if not risk_check:
        bypass_reasons.append(f"Risk level {risk_level.value} exceeds LOW threshold")

    # Check 2: Confidence threshold
    confidence_threshold = 0.95
    confidence_check = confidence_score >= confidence_threshold
    eligibility_checks["confidence_threshold"] = confidence_check
    if not confidence_check:
        bypass_reasons.append(
            f"Confidence {confidence_score:.2f} below threshold {confidence_threshold}"
        )

    # Check 3: Similar corrections success rate
    if similar_corrections and len(similar_corrections) >= 5:
        success_count = sum(1 for c in similar_corrections if c.get("success"))
        similar_success_rate = success_count / len(similar_corrections)
        success_rate_check = similar_success_rate >= 0.85
        eligibility_checks["similar_success_rate"] = success_rate_check
        if not success_rate_check:
            bypass_reasons.append(
                f"Similar success rate {similar_success_rate:.2%} below 85%"
            )
    else:
        similar_success_rate = 0.0
        success_rate_check = False
        eligibility_checks["similar_success_rate"] = False
        bypass_reasons.append("Insufficient similar correction history (<5 samples)")

    # Check 4: Reviewer queue size
    queue_threshold = 10
    queue_check = reviewer_queue_size < queue_threshold
    eligibility_checks["reviewer_queue"] = queue_check
    if not queue_check:
        bypass_reasons.append(
            f"Reviewer queue ({reviewer_queue_size}) exceeds threshold ({queue_threshold})"
        )

    # Check 5: No recent failures
    # Query last 30 days for similar failed corrections
    recent_failures = 0  # Would query database
    no_recent_failures = recent_failures == 0
    eligibility_checks["no_recent_failures"] = no_recent_failures
    if not no_recent_failures:
        bypass_reasons.append(f"{recent_failures} similar failures in last 30 days")

    # Overall eligibility
    auto_approve_eligible = all(eligibility_checks.values())

    # Build reasoning
    if auto_approve_eligible:
        reasoning = """
Auto-Approval APPROVED:
✓ Risk level: LOW
✓ Confidence score: {:.2%} (≥95%)
✓ Similar success rate: {:.2%} (≥85%)
✓ Reviewer queue: {} items (<10)
✓ No recent failures in 30 days
""".format(confidence_score, similar_success_rate, reviewer_queue_size).strip()
    else:
        reasoning = f"""
Auto-Approval DENIED:
Bypass Reasons:
{chr(10).join(f"✗ {reason}" for reason in bypass_reasons)}
""".strip()

    logger.info(
        f"Auto-approve eligibility: {auto_approve_eligible}",
        extra={
            "correction_id": correction_id,
            "eligible": auto_approve_eligible,
            "checks": eligibility_checks
        }
    )

    return {
        "correction_id": correction_id,
        "auto_approve_eligible": auto_approve_eligible,
        "eligibility_checks": eligibility_checks,
        "similar_success_rate": similar_success_rate,
        "confidence_threshold_met": confidence_check,
        "reasoning": reasoning,
        "bypass_reasons": bypass_reasons
    }
```

**Error Handling**:
- Missing similar corrections → Default to manual review
- Database query failure → Fallback to manual review (safe default)
- Invalid confidence score → Treat as 0, deny auto-approval

---

### 4. implement_correction

**Purpose**: Apply approved correction to agent configuration with rollback capability

**Parameters**:
```python
{
    "correction_id": str,
    "agent_name": str,
    "correction_type": CorrectionType,
    "proposed_changes": dict[str, Any],
    "traffic_percentage": float,      # 0-1, gradual rollout
    "enable_monitoring": bool,
    "success_criteria": dict[str, Any]
}
```

**Returns**:
```python
{
    "correction_id": str,
    "implementation_id": str,
    "success": bool,
    "implementation_time": datetime,
    "traffic_percentage": float,
    "rollback_token": str,
    "backup_created": bool,
    "monitoring_enabled": bool,
    "errors": list[str],
    "next_steps": list[str]
}
```

**Implementation**: (See detailed implementation notes)

---

### 5. trigger_ab_test

**Purpose**: Enable A/B testing to validate correction effectiveness

**Parameters**:
```python
{
    "correction_id": str,
    "control_group": str,           # Original version
    "test_group": str,              # Correction version
    "traffic_split": dict[str, float],  # {"control": 0.5, "test": 0.5}
    "success_metrics": list[str],
    "duration_days": int,
    "confidence_level": float       # 0.95 = 95% confidence
}
```

**Returns**:
```python
{
    "correction_id": str,
    "ab_test_id": str,
    "test_started_at": datetime,
    "estimated_completion": datetime,
    "traffic_split": dict[str, float],
    "monitoring_url": str,
    "success_criteria": dict[str, Any]
}
```

---

### 6. rollback_correction

**Purpose**: Revert failed or problematic changes

**Parameters**:
```python
{
    "correction_id": str,
    "rollback_token": str,
    "rollback_reason": str,
    "immediate": bool,              # Skip confirmation
    "notify_stakeholders": bool
}
```

**Returns**:
```python
{
    "correction_id": str,
    "rollback_id": str,
    "rollback_completed_at": datetime,
    "success": bool,
    "traffic_restored": float,      # Percentage back to original
    "verification_passed": bool,
    "notifications_sent": list[str],
    "errors": list[str]
}
```

---

### 7. track_approval_status

**Purpose**: Monitor approval workflow state and send reminders

**Parameters**:
```python
{
    "correction_id": str,
    "include_history": bool,
    "include_metrics": bool
}
```

**Returns**:
```python
{
    "correction_id": str,
    "current_status": CorrectionStatus,
    "status_history": list[dict],
    "assigned_reviewers": list[str],
    "deadline": datetime,
    "time_remaining_hours": float,
    "overdue": bool,
    "reminders_sent": int,
    "metrics": Optional[dict[str, Any]]
}
```

---

### 8. generate_audit_report

**Purpose**: Create compliance audit trail for correction governance

**Parameters**:
```python
{
    "report_type": str,           # "correction_summary", "compliance", "performance"
    "date_range": dict[str, datetime],
    "include_corrections": list[str],  # Specific correction IDs
    "grouping": str,              # "agent", "type", "status", "reviewer"
    "format": str                 # "json", "pdf", "csv"
}
```

**Returns**:
```python
{
    "report_id": str,
    "report_type": str,
    "generated_at": datetime,
    "date_range": dict[str, datetime],
    "summary": dict[str, Any],
    "total_corrections": int,
    "approved_corrections": int,
    "rejected_corrections": int,
    "auto_approved": int,
    "avg_approval_time_hours": float,
    "avg_implementation_time_hours": float,
    "rollback_rate": float,
    "success_rate": float,
    "file_url": Optional[str]
}
```

---

## Database Schema

### correction_approval_workflow Table (from 007_learning_system.sql)

```sql
CREATE TABLE IF NOT EXISTS correction_approval_workflow (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Reference to learning/correction
    agent_learning_id UUID REFERENCES agent_learning(id),
    response_tracking_id UUID REFERENCES response_tracking(id),

    -- Correction Details
    correction_type VARCHAR(100),
    proposed_correction TEXT NOT NULL,
    original_value TEXT,
    reasoning TEXT NOT NULL,

    -- Workflow
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,

    -- Approval Process
    requested_by VARCHAR(100),
    reviewed_by VARCHAR(100),
    approved_by VARCHAR(100),
    review_date TIMESTAMPTZ,
    approval_date TIMESTAMPTZ,
    implementation_date TIMESTAMPTZ,

    -- Review Details
    review_notes TEXT,
    approval_conditions TEXT,
    rejection_reason TEXT,

    -- Impact Assessment
    estimated_impact VARCHAR(50),
    impact_description TEXT,
    risk_level VARCHAR(50),

    -- Auto-Approval Logic
    auto_approve BOOLEAN DEFAULT FALSE,
    auto_approve_conditions JSONB DEFAULT '{}',
    confidence_threshold DECIMAL(3,2) DEFAULT 0.8,

    -- Implementation
    implemented BOOLEAN DEFAULT FALSE,
    implementation_details JSONB DEFAULT '{}',
    rollback_available BOOLEAN DEFAULT FALSE,
    rollback_procedure TEXT,

    -- Results
    post_implementation_metrics JSONB DEFAULT '{}',
    success_criteria TEXT,
    actual_impact JSONB DEFAULT '{}',

    -- Metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    status_history JSONB DEFAULT '[]'
);
```

### correction_reviewers Table

```sql
CREATE TABLE IF NOT EXISTS correction_reviewers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Correction reference
    correction_id UUID REFERENCES correction_approval_workflow(id) ON DELETE CASCADE,

    -- Reviewer details
    reviewer VARCHAR(100) NOT NULL,
    reviewer_type VARCHAR(50), -- primary, backup, admin
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    deadline TIMESTAMPTZ,

    -- Review status
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, skipped
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Review decision
    decision VARCHAR(50), -- approved, rejected, abstain
    decision_reason TEXT,
    decision_confidence DECIMAL(3,2),

    -- Workload tracking
    current_workload INTEGER DEFAULT 0,
    avg_response_time_hours DECIMAL(8,2),

    -- Expertise
    expertise_areas TEXT[] DEFAULT '{}',
    expertise_match_score DECIMAL(3,2),

    -- Notifications
    reminders_sent INTEGER DEFAULT 0,
    last_reminder_at TIMESTAMPTZ,

    UNIQUE(correction_id, reviewer)
);

CREATE INDEX idx_reviewers_correction ON correction_reviewers(correction_id);
CREATE INDEX idx_reviewers_status ON correction_reviewers(reviewer, status);
CREATE INDEX idx_reviewers_deadline ON correction_reviewers(deadline) WHERE status = 'pending';
```

### correction_audit_trail Table

```sql
CREATE TABLE IF NOT EXISTS correction_audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Correction reference
    correction_id UUID REFERENCES correction_approval_workflow(id) ON DELETE CASCADE,

    -- Event details
    event_type VARCHAR(100) NOT NULL, -- submitted, routed, reviewed, approved, rejected, implemented, rolled_back
    event_actor VARCHAR(100), -- who triggered the event
    event_actor_type VARCHAR(50), -- agent, user, system

    -- Event data
    previous_state VARCHAR(50),
    new_state VARCHAR(50),
    event_data JSONB DEFAULT '{}',
    event_reason TEXT,

    -- Context
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),

    -- Metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}'
);

CREATE INDEX idx_audit_correction ON correction_audit_trail(correction_id, created_at DESC);
CREATE INDEX idx_audit_event_type ON correction_audit_trail(event_type, created_at DESC);
CREATE INDEX idx_audit_actor ON correction_audit_trail(event_actor, created_at DESC);
```

### correction_templates Table

```sql
CREATE TABLE IF NOT EXISTS correction_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Template details
    template_name VARCHAR(255) NOT NULL UNIQUE,
    template_type VARCHAR(100), -- prompt_adjustment, template_update, etc.
    description TEXT,

    -- Template content
    template_content JSONB NOT NULL,
    default_values JSONB DEFAULT '{}',
    validation_rules JSONB DEFAULT '{}',

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    success_rate DECIMAL(5,2),

    -- Risk classification
    default_risk_level VARCHAR(50) DEFAULT 'medium',
    requires_approval BOOLEAN DEFAULT TRUE,
    auto_approve_eligible BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_by VARCHAR(100),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Status
    status VARCHAR(50) DEFAULT 'active' CHECK (
        status IN ('active', 'archived', 'draft')
    )
);

CREATE INDEX idx_templates_type ON correction_templates(template_type, status);
CREATE INDEX idx_templates_success ON correction_templates(success_rate DESC);
CREATE INDEX idx_templates_tags ON correction_templates USING GIN(tags);
```

---

## Approval Workflow State Machine

### Valid State Transitions

```python
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
        CorrectionStatus.TESTING,
        CorrectionStatus.ROLLED_BACK
    ],
    CorrectionStatus.TESTING: [
        CorrectionStatus.VALIDATED,
        CorrectionStatus.ROLLED_BACK
    ],
    CorrectionStatus.VALIDATED: [
        CorrectionStatus.ROLLED_BACK  # Can still rollback if issues found later
    ],
    CorrectionStatus.REJECTED: [
        CorrectionStatus.PENDING  # Can resubmit with changes
    ],
    CorrectionStatus.ROLLED_BACK: [],  # Terminal state
    CorrectionStatus.CANCELLED: []      # Terminal state
}
```

### State Transition Validation

```python
def validate_state_transition(
    current_status: CorrectionStatus,
    new_status: CorrectionStatus
) -> tuple[bool, str]:
    """
    Validate if state transition is allowed.

    Returns:
        (valid: bool, error_message: str)
    """
    valid_next_states = VALID_TRANSITIONS.get(current_status, [])

    if new_status in valid_next_states:
        return True, ""
    else:
        return False, (
            f"Invalid transition from {current_status.value} to {new_status.value}. "
            f"Valid transitions: {', '.join(s.value for s in valid_next_states)}"
        )
```

---

## Auto-Approval Rules

### Decision Tree

```
1. Risk Level Check
   ├─ If CRITICAL → DENY (requires admin approval)
   ├─ If HIGH → DENY (requires multi-reviewer)
   ├─ If MEDIUM → Continue to checks
   └─ If LOW → Continue to checks

2. Confidence Score Check
   ├─ If < 0.95 → DENY
   └─ If ≥ 0.95 → Continue to checks

3. Historical Success Rate
   ├─ If no history → DENY
   ├─ If < 85% success → DENY
   └─ If ≥ 85% success → Continue to checks

4. Reviewer Workload
   ├─ If queue ≥ 10 items → APPROVE (quick path)
   └─ If queue < 10 items → Continue to checks

5. Recent Failures Check
   ├─ If failures in 30 days → DENY
   └─ If no failures → APPROVE
```

### Auto-Approval Conditions

```python
AUTO_APPROVE_CONDITIONS = {
    "risk_level": RiskLevel.LOW,
    "confidence_threshold": 0.95,
    "similar_success_rate": 0.85,
    "min_similar_samples": 5,
    "reviewer_workload_threshold": 10,
    "recent_failure_window_days": 30,
    "recent_failure_tolerance": 0
}
```

---

## Rollback Procedures

### Rollback Triggers

1. **Automatic Rollback**:
   - Performance degradation > 5% in key metrics
   - Error rate increase > 10%
   - System health check failures
   - A/B test results show statistically significant decline

2. **Manual Rollback**:
   - Admin request
   - Reviewer request
   - Emergency escalation
   - Customer complaints spike

### Rollback Procedure

```python
async def execute_rollback(
    correction_id: str,
    rollback_reason: str,
    immediate: bool = False
) -> dict[str, Any]:
    """
    Execute rollback procedure.

    Steps:
    1. Retrieve rollback configuration
    2. Create backup of current state (before rollback)
    3. Revert to previous configuration
    4. Verify rollback success
    5. Update traffic routing (100% to original)
    6. Send notifications
    7. Update audit trail
    8. Monitor for stability
    """
    logger = get_agent_logger("correction_orchestrator.rollback")

    # 1. Retrieve rollback configuration
    correction = await get_correction_by_id(correction_id)
    rollback_config = correction.implementation_details.get("rollback_config")

    if not rollback_config:
        raise ValueError(f"No rollback configuration for correction {correction_id}")

    # 2. Create backup of current state
    current_backup = await create_configuration_backup(
        agent_name=correction.metadata.get("agent_name"),
        backup_type="pre_rollback"
    )

    # 3. Revert to previous configuration
    previous_config = rollback_config.get("previous_config")
    await apply_configuration(
        agent_name=correction.metadata.get("agent_name"),
        config=previous_config
    )

    # 4. Verify rollback success
    verification = await verify_configuration(
        agent_name=correction.metadata.get("agent_name"),
        expected_config=previous_config
    )

    if not verification.get("success"):
        # Rollback failed, critical alert
        await send_critical_alert(
            f"Rollback FAILED for correction {correction_id}",
            details=verification.get("errors")
        )
        return {
            "success": False,
            "errors": verification.get("errors"),
            "rollback_id": None
        }

    # 5. Update traffic routing to 100% original
    await update_traffic_routing(
        correction_id=correction_id,
        original_percentage=100.0,
        test_percentage=0.0
    )

    # 6. Send notifications
    await send_rollback_notifications(
        correction_id=correction_id,
        rollback_reason=rollback_reason,
        stakeholders=correction.metadata.get("stakeholders", [])
    )

    # 7. Update status and audit trail
    rollback_id = await update_correction_status(
        correction_id=correction_id,
        new_status=CorrectionStatus.ROLLED_BACK,
        reason=rollback_reason,
        metadata={
            "rollback_time": datetime.utcnow(),
            "current_backup_id": current_backup.get("backup_id"),
            "verification": verification
        }
    )

    # 8. Monitor for stability (24-hour watch)
    await schedule_stability_monitoring(
        correction_id=correction_id,
        duration_hours=24
    )

    logger.info(
        f"Rollback completed: {correction_id}",
        extra={
            "correction_id": correction_id,
            "rollback_id": rollback_id,
            "rollback_reason": rollback_reason,
            "verification_passed": verification.get("success")
        }
    )

    return {
        "success": True,
        "correction_id": correction_id,
        "rollback_id": rollback_id,
        "rollback_completed_at": datetime.utcnow(),
        "traffic_restored": 100.0,
        "verification_passed": verification.get("success"),
        "notifications_sent": ["admin", "reviewer", "stakeholders"],
        "errors": []
    }
```

---

## Error Handling Strategy

### Error Categories

1. **Database Errors**:
   - Connection timeout → Retry 3x with exponential backoff
   - Query timeout → Log, alert, return partial data
   - Transaction conflict → Retry with jitter

2. **Notification Errors**:
   - Email failure → Fallback to Slack
   - Slack failure → Fallback to database queue
   - All channels failed → Log critical alert

3. **Implementation Errors**:
   - Configuration update failed → Rollback immediately
   - Verification failed → Mark as failed, alert admin
   - Traffic routing error → Revert to 100% original

4. **Reviewer Assignment Errors**:
   - No available reviewers → Escalate to admin
   - Deadline calculation error → Use conservative default (24h)
   - Expertise mismatch → Assign to generalist reviewer

### Error Recovery Procedures

```python
ERROR_RECOVERY = {
    "database_connection": {
        "retry_attempts": 3,
        "retry_backoff_seconds": [1, 2, 4],
        "fallback": "in_memory_queue"
    },
    "notification_delivery": {
        "retry_attempts": 2,
        "fallback_channels": ["slack", "email", "database"],
        "alert_on_total_failure": True
    },
    "implementation_failure": {
        "immediate_rollback": True,
        "alert_level": "critical",
        "require_investigation": True
    },
    "reviewer_unavailable": {
        "escalate_to": "admin",
        "extend_deadline_hours": 24,
        "notification_priority": "high"
    }
}
```

---

## Testing Requirements

### Unit Tests (>90% coverage required)

**Test file**: `__tests__/unit/agents/test_correction_approval_orchestrator.py`

```python
class TestCorrectionApprovalOrchestratorInitialization:
    def test_agent_initialization()
    def test_tools_registered()
    def test_system_prompt_defined()

class TestClassifyCorrectionRisk:
    @pytest.mark.asyncio
    async def test_classify_low_risk()
    async def test_classify_medium_risk()
    async def test_classify_high_risk()
    async def test_classify_critical_risk_financial()
    async def test_classify_critical_risk_security()
    async def test_risk_score_calculation()
    async def test_mitigation_requirements()

class TestAssignReviewer:
    @pytest.mark.asyncio
    async def test_assign_reviewer_by_expertise()
    async def test_assign_reviewer_workload_balancing()
    async def test_assign_backup_reviewers()
    async def test_deadline_calculation()
    async def test_notification_sending()
    async def test_no_available_reviewers_escalation()

class TestCheckAutoApproveEligibility:
    @pytest.mark.asyncio
    async def test_auto_approve_eligible()
    async def test_auto_approve_denied_high_risk()
    async def test_auto_approve_denied_low_confidence()
    async def test_auto_approve_denied_low_success_rate()
    async def test_auto_approve_denied_recent_failures()

class TestImplementCorrection:
    @pytest.mark.asyncio
    async def test_implement_correction_success()
    async def test_implement_with_gradual_rollout()
    async def test_implementation_failure_rollback()
    async def test_backup_creation()
    async def test_traffic_routing_update()

class TestTriggerABTest:
    @pytest.mark.asyncio
    async def test_trigger_ab_test_creation()
    async def test_ab_test_traffic_split()
    async def test_ab_test_success_criteria()
    async def test_ab_test_monitoring_setup()

class TestRollbackCorrection:
    @pytest.mark.asyncio
    async def test_rollback_success()
    async def test_rollback_verification()
    async def test_rollback_notification()
    async def test_rollback_audit_trail()
    async def test_emergency_rollback_immediate()

class TestTrackApprovalStatus:
    @pytest.mark.asyncio
    async def test_track_status_current()
    async def test_track_status_history()
    async def test_track_overdue_detection()
    async def test_reminder_sending()

class TestGenerateAuditReport:
    @pytest.mark.asyncio
    async def test_generate_summary_report()
    async def test_generate_compliance_report()
    async def test_generate_performance_report()
    async def test_report_filtering()
    async def test_report_export_formats()
```

### Integration Tests

**Test file**: `__tests__/integration/test_correction_approval_integration.py`

```python
class TestCorrectionApprovalIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_correction_workflow()
    async def test_auto_approve_workflow()
    async def test_multi_reviewer_workflow()
    async def test_rejection_resubmission_workflow()
    async def test_implementation_rollback_workflow()

class TestABTestingIntegration:
    @pytest.mark.asyncio
    async def test_ab_test_orchestration()
    async def test_test_result_validation()
    async def test_winner_promotion()
    async def test_loser_rollback()

class TestNotificationIntegration:
    @pytest.mark.asyncio
    async def test_reviewer_notifications()
    async def test_reminder_escalation()
    async def test_approval_notifications()
    async def test_rollback_alerts()

class TestDatabaseIntegration:
    @pytest.mark.asyncio
    async def test_correction_persistence()
    async def test_audit_trail_completeness()
    async def test_status_history_tracking()
    async def test_concurrent_updates()
```

---

## Implementation Checklist

### Phase 1: Core Workflow & Risk Classification
- [ ] Implement `CorrectionApprovalOrchestrator` class extending `BaseAgent`
- [ ] Implement `classify_correction_risk` tool with multi-factor analysis
- [ ] Implement `check_auto_approve_eligibility` tool
- [ ] Create database tables (workflow, reviewers, audit trail, templates)
- [ ] Implement state machine with transition validation
- [ ] Write unit tests for risk classification (>90% coverage)

### Phase 2: Reviewer Assignment & Notifications
- [ ] Implement `assign_reviewer` tool with expertise matching
- [ ] Implement workload balancing algorithm
- [ ] Create reviewer notification templates (email, Slack)
- [ ] Implement reminder scheduling system
- [ ] Implement escalation logic for overdue reviews
- [ ] Write unit tests for reviewer assignment

### Phase 3: Implementation & Rollback
- [ ] Implement `implement_correction` tool
- [ ] Create configuration backup system
- [ ] Implement gradual traffic rollout
- [ ] Implement `rollback_correction` tool
- [ ] Create verification procedures
- [ ] Implement emergency rollback path
- [ ] Write unit tests for implementation and rollback

### Phase 4: A/B Testing Integration
- [ ] Implement `trigger_ab_test` tool
- [ ] Integrate with `system_response_outcome_tracker`
- [ ] Create test validation logic
- [ ] Implement winner promotion
- [ ] Implement loser rollback
- [ ] Write unit tests for A/B testing

### Phase 5: Status Tracking & Audit
- [ ] Implement `track_approval_status` tool
- [ ] Implement status history tracking
- [ ] Implement `generate_audit_report` tool
- [ ] Create compliance report templates
- [ ] Integrate with `system_audit_log`
- [ ] Write unit tests for tracking and reporting

### Phase 6: Integration & API
- [ ] Create correction submission API endpoint
- [ ] Create review decision API endpoint
- [ ] Create status query API endpoint
- [ ] Create rollback API endpoint
- [ ] Integrate with all 79+ agents
- [ ] Write integration tests

### Phase 7: Testing & Optimization
- [ ] Achieve >90% test coverage
- [ ] Performance test with high correction volume
- [ ] Test failure scenarios and recovery
- [ ] Test concurrent correction workflows
- [ ] Optimize database queries
- [ ] Document all procedures and runbooks

---

## Success Metrics

- **Approval SLA Compliance**: >95% of corrections reviewed within deadline
- **Auto-Approval Accuracy**: >98% of auto-approved corrections succeed
- **Rollback Rate**: <5% of implemented corrections require rollback
- **Review Time**: <24 hours median time from submission to approval
- **Implementation Success**: >95% of approved corrections implement successfully
- **Audit Completeness**: 100% of corrections have complete audit trail
- **Test Coverage**: >90% code coverage
- **Reviewer Satisfaction**: >85% satisfaction with workload and tooling
- **System Uptime**: >99.5% availability for correction workflows
- **False Positive Rate**: <2% of auto-approved corrections fail validation

---

## Dependencies

### Python Packages (already installed)
- `sqlalchemy>=2.0.44` - Database operations
- `asyncpg>=0.31.0` - PostgreSQL async driver
- `celery>=5.6.0` - Background task processing
- `redis>=6.4.0` - Caching and queuing

### External Services
- Database: PostgreSQL (Supabase)
- Cache: Redis (Upstash)
- Notifications: Slack, Email
- Monitoring: Internal monitoring system

### Agent Dependencies
- `system_learning_feedback` - Receives learning-based corrections
- `system_agent_performance_analyst` - Receives performance alerts
- `system_response_outcome_tracker` - A/B test orchestration
- `system_audit_log` - Audit trail logging
- All 79+ agents - Configuration updates

---

## Human-in-the-Loop

### Approval Gates

1. **Correction Submission**: Human can submit corrections manually via UI
2. **Review Decision**: Human reviewer approves/rejects with reasoning
3. **Emergency Override**: Admin can override auto-approval or force rollback
4. **Policy Configuration**: Human sets auto-approval thresholds and risk criteria

### Manual Interventions

1. **Review Assignment Override**: Admin can reassign to different reviewer
2. **Deadline Extension**: Reviewer can request more time
3. **Emergency Rollback**: Admin can trigger immediate rollback
4. **Template Management**: Create and update correction templates
5. **Compliance Audit**: Request and review audit reports

---

## Related Agents

This agent coordinates with:
- **system_learning_feedback**: Receives learning-based correction suggestions
- **system_agent_performance_analyst**: Receives performance-based alerts
- **system_response_outcome_tracker**: Triggers A/B tests for validation
- **system_audit_log**: Logs all correction decisions and implementations
- **All 79+ agents**: Implements approved corrections across the system

---

## Future Enhancements

1. **ML-Based Risk Prediction**: Train model to predict correction success probability
2. **Smart Reviewer Routing**: ML model to match correction to best reviewer
3. **Automated Success Validation**: AI-powered verification of correction effectiveness
4. **Cross-Correction Pattern Detection**: Identify patterns across multiple corrections
5. **Predictive Auto-Approval**: Expand auto-approval with higher confidence predictions
6. **Real-Time A/B Testing**: Continuous testing without manual trigger
7. **Federated Learning**: Share correction insights across Smarter Team deployments
8. **Natural Language Explanations**: AI-generated explanations for decisions
9. **Integration with LLM Fine-Tuning**: Direct application to model fine-tuning
10. **Gamification for Reviewers**: Recognition and incentives for timely, accurate reviews

---

## Security Considerations

1. **Access Control**: Role-based permissions for submission, review, approval, rollback
2. **Audit Trail Integrity**: Cryptographic signing of audit entries
3. **Rollback Authorization**: Multi-factor authentication for emergency rollbacks
4. **Configuration Encryption**: Encrypt sensitive agent configurations
5. **Input Validation**: Sanitize all correction submissions for injection attacks
6. **Rate Limiting**: Prevent abuse of correction submission API
7. **Approval Chain Verification**: Verify approval chain integrity before implementation

---

## Performance Requirements

1. **Throughput**: Process 1,000+ corrections per day
2. **Risk Classification**: <100ms per correction
3. **Reviewer Assignment**: <200ms per assignment
4. **Implementation**: <5 seconds per correction
5. **Rollback**: <10 seconds for emergency rollback
6. **Query Performance**: <500ms for status queries
7. **Report Generation**: <30 seconds for monthly compliance reports
8. **Memory Usage**: <1GB RAM during peak processing
9. **CPU Usage**: <30% CPU during normal operations
