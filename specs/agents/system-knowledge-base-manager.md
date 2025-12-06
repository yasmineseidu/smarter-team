# System Knowledge Base Manager Agent - Production Specification

## Overview

**Category**: System & Administration
**Priority**: Phase 2 - Critical for agent improvement
**Agent Name**: `system_knowledge_base_manager`
**Purpose**: Maintain and evolve the centralized knowledge base for agent learning and response optimization through active curation, usage tracking, effectiveness measurement, and auto-extraction from successful interactions.

**Mission**: Transform dispersed agent knowledge into a curated, high-quality, continuously improving knowledge base that serves all 73+ agents with accurate, effective, and contextually relevant information.

**Dependencies**:
- **Response FAQ Evolution Agent**: Receives new FAQ submissions
- **Response Knowledge Base Agent**: Query interface that provides usage data
- **System Response Outcome Tracker**: Receives effectiveness metrics
- **System Learning Feedback Agent**: Receives pattern insights
- **System Correction Approval Orchestrator**: Routes major changes for approval

---

## System Prompt

```
You are the Knowledge Base Manager for Smarter Team, a sophisticated knowledge curation and optimization system responsible for maintaining the centralized knowledge repository serving all 73+ agents.

Your mission is to curate, validate, track, and continuously improve knowledge articles that agents use for client interactions, ensuring maximum effectiveness and accuracy.

**Core Responsibilities:**
1. CURATION: Review, validate, and organize all knowledge submissions from agents and humans
2. QUALITY ASSURANCE: Ensure factual accuracy, relevance, and clarity of all knowledge articles
3. EFFECTIVENESS TRACKING: Monitor which articles are used and measure their success rates
4. AUTO-EXTRACTION: Identify successful response patterns and extract reusable knowledge
5. RELATIONSHIP MANAGEMENT: Link related articles for comprehensive knowledge coverage
6. LIFECYCLE MANAGEMENT: Retire low-performing content and promote high-performing articles
7. REPORTING: Generate weekly knowledge effectiveness reports with actionable insights

**Curation Standards:**
- ACCURACY: All information must be factually correct and verifiable
- TIMELINESS: Content must be current and regularly reviewed for relevance
- CLARITY: Articles must be clear, concise, and actionable
- CONTEXT: Include appropriate context for when/how to use each article
- COMPLETENESS: Cover the topic thoroughly without unnecessary detail

**Quality Criteria:**
- Factual correctness verified through multiple sources
- Language clarity (8th-grade reading level for accessibility)
- Actionability (provides clear next steps or answers)
- Specificity (avoids vague generalizations)
- Usefulness (addresses real agent/client needs)

**Effectiveness Measurement:**
- Usage frequency: How often is this article used?
- Success rate: What percentage of uses lead to positive outcomes?
- Feedback quality: What do agents/humans say about this article?
- Context fit: Does it work for the intended scenarios?
- Time relevance: Is the information still current?

**Auto-Extraction Rules:**
1. Identify responses with >80% success scores from response_tracking
2. Look for reusable patterns in successful responses (min 5 occurrences)
3. Extract generalizable knowledge (remove client-specific details)
4. Validate against existing KB for duplicates (>85% similarity = duplicate)
5. Create draft articles with metadata and submit for approval
6. Track extraction success rate and refine patterns

**Behavioral Guidelines:**
- Be systematic: Follow curation checklists for every submission
- Be conservative: When uncertain about accuracy, flag for human review
- Be data-driven: Use usage metrics and effectiveness data to guide decisions
- Be collaborative: Work with agents to understand knowledge needs
- Be proactive: Identify gaps before they become issues

**Decision Making:**
- Curation Priority: Review by usage count + recent submissions first
- Validation Threshold: Require 2+ sources for critical facts (pricing, legal, technical)
- Effectiveness Threshold: Articles with <50% success rate flagged for review
- Retirement Criteria: <10 uses in 90 days + <60% success rate = candidate for archival
- Auto-Approval: Only FAQ articles from verified agents with high confidence (>0.85)
- Human Escalation: Pricing, legal, policy changes always require human approval

**Communication Style:**
- Reports should be clear, data-driven, and actionable
- Use metrics to demonstrate impact (e.g., "Article A improved response success by 15%")
- Provide specific examples when identifying issues
- Celebrate high-performing articles to reinforce best practices
- Frame suggestions positively with clear rationale

You have access to tools for curating articles, validating accuracy, tracking usage, calculating effectiveness, extracting patterns, managing relationships, retiring content, and generating reports. Use these tools systematically to maintain the highest quality knowledge base that continuously improves agent performance.
```

---

## Agent Architecture

### Class Definition

```python
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict, Counter
import json
import asyncio

from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger


class KnowledgeCategory(str, Enum):
    """Categories for knowledge articles."""
    SERVICES = "services"
    PRICING = "pricing"
    PROCESS = "process"
    OBJECTIONS = "objections"
    CASE_STUDIES = "case_studies"
    TESTIMONIALS = "testimonials"
    FAQ = "faq"
    POLICIES = "policies"
    TECHNICAL = "technical"
    BEST_PRACTICES = "best_practices"


class KnowledgeStatus(str, Enum):
    """Status of knowledge articles."""
    ACTIVE = "active"
    PENDING_APPROVAL = "pending_approval"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    UNDER_REVIEW = "under_review"


class ValidationStatus(str, Enum):
    """Validation status for accuracy checks."""
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"
    NEEDS_UPDATE = "needs_update"


@dataclass
class KnowledgeArticle:
    """Structured data for a knowledge base article."""
    id: str
    title: str
    content: str
    category: KnowledgeCategory
    subcategory: Optional[str]
    tags: List[str]
    keywords: List[str]

    # Metadata
    status: KnowledgeStatus
    confidence_score: float
    usage_count: int
    effectiveness_score: float

    # Context
    industry: Optional[str]
    company_size: Optional[str]
    use_cases: List[str]

    # Validation
    verified: bool
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    sources: List[str]

    # Relationships
    related_ids: List[str]
    parent_id: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]


@dataclass
class UsageMetrics:
    """Usage and effectiveness metrics for an article."""
    article_id: str
    usage_count: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_confidence: float
    last_used: Optional[datetime]
    contexts_used: List[str]


@dataclass
class ExtractionPattern:
    """Pattern detected from successful responses."""
    pattern_type: str
    occurrences: int
    success_rate: float
    example_responses: List[str]
    suggested_title: str
    suggested_content: str
    suggested_category: KnowledgeCategory
    confidence: float


class KnowledgeBaseManagerAgent(BaseAgent):
    """
    System Knowledge Base Manager agent for curating and optimizing knowledge.

    Manages the complete lifecycle of knowledge articles from submission to retirement.
    """

    def __init__(self):
        super().__init__(
            name="system_knowledge_base_manager",
            description="Maintains and evolves centralized knowledge base for agent optimization"
        )

        # Register tools
        self.register_tool(
            curate_knowledge_article,
            "curate_knowledge_article",
            "Review and organize new knowledge submissions"
        )
        self.register_tool(
            validate_knowledge_accuracy,
            "validate_knowledge_accuracy",
            "Verify factual correctness of knowledge articles"
        )
        self.register_tool(
            track_knowledge_usage,
            "track_knowledge_usage",
            "Monitor which articles are used and when"
        )
        self.register_tool(
            calculate_effectiveness,
            "calculate_effectiveness",
            "Measure success rate when KB articles are used"
        )
        self.register_tool(
            extract_from_responses,
            "extract_from_responses",
            "Auto-extract patterns from successful agent responses"
        )
        self.register_tool(
            create_knowledge_relationships,
            "create_knowledge_relationships",
            "Link related articles for comprehensive coverage"
        )
        self.register_tool(
            retire_knowledge,
            "retire_knowledge",
            "Archive low-performing or outdated articles"
        )
        self.register_tool(
            generate_kb_report,
            "generate_kb_report",
            "Generate weekly knowledge effectiveness report"
        )

    @property
    def system_prompt(self) -> str:
        # Return the full system prompt from above
        return """..."""  # Full prompt from above

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process knowledge base management tasks.

        Supports:
        - curate_submissions: Review new knowledge submissions
        - validate_accuracy: Verify article accuracy
        - track_usage: Monitor article usage patterns
        - extract_patterns: Auto-extract from successful responses
        - manage_relationships: Link related articles
        - retire_articles: Archive low-performing content
        - generate_report: Create effectiveness report
        """
        task_type = task.get("type")

        if task_type == "curate_submissions":
            return await self._curate_new_submissions(task.get("batch_size", 50))
        elif task_type == "validate_accuracy":
            return await self._validate_article_accuracy(task.get("article_ids"))
        elif task_type == "track_usage":
            return await self._track_usage_patterns(task.get("period_days", 7))
        elif task_type == "extract_patterns":
            return await self._extract_from_responses(task.get("min_success_rate", 0.8))
        elif task_type == "manage_relationships":
            return await self._manage_article_relationships()
        elif task_type == "retire_articles":
            return await self._retire_low_performers(task.get("criteria"))
        elif task_type == "generate_report":
            return await self._generate_effectiveness_report(task.get("report_type", "weekly"))
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _curate_new_submissions(self, batch_size: int) -> dict[str, Any]:
        """Curate new knowledge submissions."""
        # Implementation details
        pass

    async def _validate_article_accuracy(self, article_ids: List[str]) -> dict[str, Any]:
        """Validate accuracy of knowledge articles."""
        # Implementation details
        pass

    async def _track_usage_patterns(self, period_days: int) -> dict[str, Any]:
        """Track how articles are being used."""
        # Implementation details
        pass

    async def _extract_from_responses(self, min_success_rate: float) -> dict[str, Any]:
        """Extract knowledge from successful responses."""
        # Implementation details
        pass

    async def _manage_article_relationships(self) -> dict[str, Any]:
        """Create and maintain article relationships."""
        # Implementation details
        pass

    async def _retire_low_performers(self, criteria: dict) -> dict[str, Any]:
        """Retire articles based on performance criteria."""
        # Implementation details
        pass

    async def _generate_effectiveness_report(self, report_type: str) -> dict[str, Any]:
        """Generate knowledge effectiveness report."""
        # Implementation details
        pass
```

**File Structure**:
```
app/backend/src/agents/system/
├── __init__.py
└── knowledge_base_manager.py  # KnowledgeBaseManagerAgent class
```

---

## Tool Definitions

### 1. curate_knowledge_article

**Purpose**: Review, validate, and organize new knowledge submissions

**Parameters**:
```python
{
    "submission_id": str,              # UUID of submission to curate
    "action": str,                     # "approve", "reject", "request_changes"
    "category": str | None,            # Override category if needed
    "subcategory": str | None,         # Assign subcategory
    "tags": list[str] | None,          # Add/override tags
    "keywords": list[str] | None,      # Add search keywords
    "validation_required": bool,       # Flag for accuracy validation
    "approval_tier": str,              # "auto", "human_required"
    "notes": str | None                # Curation notes
}
```

**Returns**:
```python
{
    "submission_id": str,
    "action_taken": str,
    "kb_article_id": str | None,       # If approved and created
    "status": str,                     # Article status
    "validation_scheduled": bool,      # If validation queued
    "duplicate_detected": bool,
    "similar_articles": list[dict],    # Articles with >85% similarity
    "curation_notes": str,
    "next_steps": list[str]            # What happens next
}
```

**Implementation**:
```python
async def curate_knowledge_article(
    submission_id: str,
    action: str,
    category: str | None = None,
    subcategory: str | None = None,
    tags: list[str] | None = None,
    keywords: list[str] | None = None,
    validation_required: bool = True,
    approval_tier: str = "auto",
    notes: str | None = None
) -> dict[str, Any]:
    """
    Curate knowledge submission through review and organization.

    Checks for duplicates, validates category assignment, tags appropriately,
    and routes for approval based on content type and confidence.
    """
    from sqlalchemy import select, and_
    from src.database import get_async_session
    from src.models import KnowledgeBase, KnowledgeSubmission
    from anthropic import Anthropic
    import time

    logger = get_agent_logger("kb_manager.curate")
    start_time = time.time()

    async with get_async_session() as session:
        # Fetch submission
        query = select(KnowledgeSubmission).where(
            KnowledgeSubmission.id == submission_id
        )
        result = await session.execute(query)
        submission = result.scalar_one_or_none()

        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        # Check for duplicates using semantic similarity
        duplicate_check = await _check_for_duplicates(
            session,
            submission.title,
            submission.content
        )

        similar_articles = []
        duplicate_detected = False
        if duplicate_check["max_similarity"] > 0.85:
            duplicate_detected = True
            similar_articles = duplicate_check["similar_articles"]

        # Determine action
        if action == "reject":
            submission.status = "rejected"
            submission.rejection_reason = notes
            await session.commit()

            logger.info(
                f"Submission rejected: {submission_id}",
                extra={"reason": notes}
            )

            return {
                "submission_id": submission_id,
                "action_taken": "rejected",
                "kb_article_id": None,
                "status": "rejected",
                "validation_scheduled": False,
                "duplicate_detected": duplicate_detected,
                "similar_articles": similar_articles,
                "curation_notes": notes,
                "next_steps": []
            }

        if action == "request_changes":
            submission.status = "needs_changes"
            submission.change_requested = notes
            # Notify submitter
            await _notify_change_request(submission, notes)
            await session.commit()

            return {
                "submission_id": submission_id,
                "action_taken": "requested_changes",
                "kb_article_id": None,
                "status": "needs_changes",
                "validation_scheduled": False,
                "duplicate_detected": duplicate_detected,
                "similar_articles": similar_articles,
                "curation_notes": notes,
                "next_steps": ["Awaiting submitter revision"]
            }

        # Approve and create KB article
        kb_article = KnowledgeBase(
            title=submission.title,
            content=submission.content,
            category=category or submission.suggested_category,
            subcategory=subcategory or submission.suggested_subcategory,
            tags=tags or submission.tags or [],
            search_keywords=keywords or [],
            status="pending_approval" if approval_tier == "human_required" else "active",
            confidence_score=submission.confidence_score or 0.0,
            created_by=submission.created_by,
            sources=submission.sources or [],
            verified=False
        )

        session.add(kb_article)
        submission.status = "approved"
        submission.kb_article_id = kb_article.id
        await session.commit()

        # Schedule validation if required
        validation_scheduled = False
        if validation_required:
            await _schedule_validation(kb_article.id)
            validation_scheduled = True

        processing_time = (time.time() - start_time) * 1000

        logger.info(
            f"Article curated: {kb_article.id}",
            extra={
                "submission_id": submission_id,
                "category": kb_article.category,
                "status": kb_article.status,
                "validation_scheduled": validation_scheduled,
                "processing_time_ms": processing_time
            }
        )

        next_steps = []
        if validation_scheduled:
            next_steps.append("Accuracy validation scheduled")
        if approval_tier == "human_required":
            next_steps.append("Awaiting human approval")
        else:
            next_steps.append("Article active in knowledge base")

        return {
            "submission_id": submission_id,
            "action_taken": "approved",
            "kb_article_id": str(kb_article.id),
            "status": kb_article.status,
            "validation_scheduled": validation_scheduled,
            "duplicate_detected": duplicate_detected,
            "similar_articles": similar_articles,
            "curation_notes": notes or "",
            "next_steps": next_steps
        }
```

### 2. validate_knowledge_accuracy

**Purpose**: Verify factual correctness and accuracy of knowledge articles

**Parameters**:
```python
{
    "article_id": str,                 # KB article to validate
    "validation_method": str,          # "source_check", "cross_reference", "expert_review"
    "sources": list[str] | None,       # Source URLs for verification
    "expert_reviewer": str | None,     # Human expert if needed
    "strict_mode": bool                # Require multiple source confirmation
}
```

**Returns**:
```python
{
    "article_id": str,
    "validation_status": str,          # "verified", "failed", "needs_update"
    "accuracy_score": float,           # 0-1 confidence in accuracy
    "sources_verified": int,           # Number of sources confirming
    "discrepancies": list[dict],       # Issues found
    "suggested_corrections": list[str],
    "verified_by": str,
    "verified_at": datetime,
    "revalidate_date": datetime | None # When to revalidate
}
```

### 3. track_knowledge_usage

**Purpose**: Monitor which knowledge articles are used and in what contexts

**Parameters**:
```python
{
    "period_days": int,                # Days to analyze
    "article_ids": list[str] | None,   # Specific articles or all
    "group_by": str,                   # "article", "category", "agent"
    "min_usage": int,                  # Filter articles with <N uses
    "include_context": bool            # Include usage context data
}
```

**Returns**:
```python
{
    "period": dict,                    # Start/end dates
    "total_usage_events": int,
    "unique_articles_used": int,
    "articles": list[UsageMetrics],
    "category_breakdown": dict,
    "agent_breakdown": dict,
    "context_analysis": dict,
    "trending_articles": list[dict],   # Increasing usage
    "declining_articles": list[dict],  # Decreasing usage
    "unused_articles": list[str]       # No usage in period
}
```

### 4. calculate_effectiveness

**Purpose**: Measure success rate when knowledge base articles are used

**Parameters**:
```python
{
    "article_id": str | None,          # Specific article or all
    "period_days": int,                # Analysis period
    "success_criteria": dict,          # Define what counts as success
    "segment_by": list[str],           # ["industry", "company_size", "agent"]
    "compare_to_baseline": bool        # Compare to no-KB responses
}
```

**Returns**:
```python
{
    "article_id": str | None,
    "period": dict,
    "effectiveness_metrics": {
        "total_uses": int,
        "successful_uses": int,
        "success_rate": float,
        "avg_confidence": float,
        "avg_response_time": float,
        "conversion_impact": float     # Impact on conversion rate
    },
    "segmented_results": dict,         # Breakdown by segments
    "baseline_comparison": dict | None,
    "performance_trend": str,          # "improving", "stable", "declining"
    "recommendations": list[str]       # Improvement suggestions
}
```

### 5. extract_from_responses

**Purpose**: Auto-extract reusable patterns from successful agent responses

**Parameters**:
```python
{
    "min_success_rate": float,         # Only extract from responses >X% success
    "min_occurrences": int,            # Pattern must appear N+ times
    "period_days": int,                # Look back period
    "agent_filter": list[str] | None,  # Specific agents or all
    "exclude_categories": list[str],   # Don't extract from these
    "auto_create": bool                # Create draft articles automatically
}
```

**Returns**:
```python
{
    "period": dict,
    "responses_analyzed": int,
    "patterns_detected": int,
    "patterns": list[ExtractionPattern],
    "articles_created": int,           # If auto_create=True
    "draft_article_ids": list[str],
    "extraction_quality": float,       # Confidence in extractions
    "similar_to_existing": int,        # Patterns matching existing KB
    "processing_time_ms": float
}
```

### 6. create_knowledge_relationships

**Purpose**: Link related knowledge articles for comprehensive coverage

**Parameters**:
```python
{
    "article_id": str | None,          # Specific article or analyze all
    "relationship_type": str,          # "related", "parent_child", "prerequisite"
    "similarity_threshold": float,     # Min similarity to create link
    "max_relationships": int,          # Max links per article
    "bidirectional": bool              # Create two-way links
}
```

**Returns**:
```python
{
    "article_id": str | None,
    "relationships_created": int,
    "relationships_removed": int,      # Outdated links
    "relationship_map": dict,          # Full relationship graph
    "orphaned_articles": list[str],    # Articles with no links
    "hub_articles": list[dict],        # Highly connected articles
    "suggested_hierarchies": list[dict] # Potential parent-child structures
}
```

### 7. retire_knowledge

**Purpose**: Archive low-performing or outdated knowledge articles

**Parameters**:
```python
{
    "criteria": dict,                  # Retirement criteria
    "dry_run": bool,                   # Preview without executing
    "notify_stakeholders": bool,
    "preserve_references": bool,       # Keep for historical queries
    "auto_redirect": bool              # Redirect to replacement article
}
```

**Returns**:
```python
{
    "articles_evaluated": int,
    "retirement_candidates": list[dict],
    "articles_retired": int,           # If not dry_run
    "articles_updated": int,           # Updated to point to replacements
    "notifications_sent": int,
    "retirement_report": dict,
    "rollback_available": bool
}
```

**Example criteria**:
```python
{
    "max_age_days": 180,
    "min_usage_count": 10,
    "min_success_rate": 0.6,
    "last_used_days_ago": 90,
    "exclude_categories": ["policies", "legal"]
}
```

### 8. generate_kb_report

**Purpose**: Generate comprehensive weekly knowledge effectiveness report

**Parameters**:
```python
{
    "report_type": str,                # "weekly", "monthly", "quarterly"
    "include_sections": list[str],     # Sections to include
    "format": str,                     # "markdown", "html", "json"
    "recipients": list[str],           # Email/Slack recipients
    "compare_to_previous": bool        # Show trends
}
```

**Returns**:
```python
{
    "report_id": str,
    "report_type": str,
    "period": dict,
    "summary": {
        "total_articles": int,
        "active_articles": int,
        "new_articles": int,
        "retired_articles": int,
        "avg_effectiveness": float,
        "total_usage": int
    },
    "top_performers": list[dict],      # Best articles
    "underperformers": list[dict],     # Needs attention
    "usage_trends": dict,
    "effectiveness_trends": dict,
    "gap_analysis": list[dict],        # Missing knowledge areas
    "recommendations": list[str],
    "report_url": str,                 # Link to full report
    "generated_at": datetime
}
```

**Report sections**:
- Executive Summary
- Usage Statistics
- Effectiveness Metrics
- Top Performing Articles
- Articles Needing Attention
- New Knowledge Added
- Retired Knowledge
- Gap Analysis
- Pattern Insights
- Recommendations

---

## Database Schema

### knowledge_base Table (from migration 007)

Used for storing all curated knowledge articles.

**Key Fields**:
- `id`, `title`, `content`, `category`, `subcategory`, `tags`
- `usage_count`, `effectiveness_score`, `last_used_at`
- `verified`, `verified_by`, `verified_at`, `confidence_score`
- `related_ids`, `parent_id`, `sources`
- `status` (active, pending_approval, archived, deprecated)

### knowledge_usage Table (extends knowledge_base)

**Purpose**: Track every use of knowledge articles by agents

```sql
CREATE TABLE knowledge_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Reference
    kb_article_id UUID REFERENCES knowledge_base(id) ON DELETE CASCADE,

    -- Usage Context
    agent_name VARCHAR(100) NOT NULL,
    agent_type VARCHAR(100),
    query_text TEXT,

    -- Usage Details
    lead_id UUID REFERENCES leads(id),
    campaign_id UUID REFERENCES campaigns(id),
    conversation_id UUID REFERENCES conversations(id),

    -- Context
    industry VARCHAR(100),
    company_size VARCHAR(50),
    lead_stage VARCHAR(50),

    -- Outcome
    was_successful BOOLEAN,
    confidence_used FLOAT,
    response_generated BOOLEAN,
    response_sent BOOLEAN,

    -- Performance
    response_time_ms INTEGER,
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    INDEX idx_ku_article_created (kb_article_id, created_at DESC),
    INDEX idx_ku_agent (agent_name, created_at DESC),
    INDEX idx_ku_success (was_successful, created_at DESC)
);
```

### knowledge_relationships Table

**Purpose**: Link related knowledge articles

```sql
CREATE TABLE knowledge_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Relationship
    article_id UUID REFERENCES knowledge_base(id) ON DELETE CASCADE,
    related_article_id UUID REFERENCES knowledge_base(id) ON DELETE CASCADE,

    -- Relationship Type
    relationship_type VARCHAR(50) NOT NULL CHECK (
        relationship_type IN ('related', 'parent_child', 'prerequisite', 'alternative', 'update_of')
    ),

    -- Strength
    similarity_score FLOAT,
    confidence FLOAT DEFAULT 0.0,

    -- Bidirectional
    is_bidirectional BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_by VARCHAR(100),
    auto_detected BOOLEAN DEFAULT FALSE,

    UNIQUE(article_id, related_article_id, relationship_type),
    INDEX idx_kr_article (article_id),
    INDEX idx_kr_related (related_article_id),
    INDEX idx_kr_type (relationship_type)
);
```

### knowledge_validation_log Table

**Purpose**: Track validation history for articles

```sql
CREATE TABLE knowledge_validation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Reference
    kb_article_id UUID REFERENCES knowledge_base(id) ON DELETE CASCADE,

    -- Validation
    validation_method VARCHAR(50) NOT NULL,
    validation_status VARCHAR(50) NOT NULL CHECK (
        validation_status IN ('verified', 'failed', 'needs_update', 'pending')
    ),

    -- Results
    accuracy_score FLOAT,
    sources_checked INTEGER DEFAULT 0,
    sources_verified INTEGER DEFAULT 0,

    -- Issues
    discrepancies JSONB DEFAULT '[]',
    suggested_corrections TEXT[],

    -- Validator
    validated_by VARCHAR(100),
    is_automated BOOLEAN DEFAULT TRUE,

    -- Next Steps
    revalidate_at TIMESTAMPTZ,

    INDEX idx_kvl_article (kb_article_id, created_at DESC),
    INDEX idx_kvl_status (validation_status)
);
```

---

## Knowledge Article Schema

Complete structure for knowledge base articles:

```json
{
    "id": "uuid-123",
    "title": "How to respond to pricing objections for enterprise clients",
    "content": "When enterprise clients object to price, first acknowledge their concern: 'I understand budget is a critical consideration for enterprise deployments.' Then frame value: 'Our clients typically see 3-5x ROI within 6 months through efficiency gains and reduced manual processes.' Provide social proof: 'Companies like [Customer A] started with similar concerns but found the investment paid for itself in Q1.' Offer flexibility: 'We can structure payments across fiscal quarters or tie milestones to value delivery.' Always ask: 'What specific budget constraints are you working within?' to understand the real objection.",

    "category": "objections",
    "subcategory": "pricing",
    "tags": ["enterprise", "pricing", "objection_handling", "value_selling"],
    "keywords": ["too expensive", "budget", "cost", "price", "ROI"],

    "usage_count": 145,
    "effectiveness_score": 8.2,
    "success_rate": 78.5,
    "last_used_at": "2025-01-04T15:30:00Z",

    "industry": "SaaS",
    "company_size": "enterprise",
    "use_cases": ["discovery_call", "proposal_followup", "negotiation"],

    "verified": true,
    "verified_by": "sales_director",
    "verified_at": "2024-12-15T10:00:00Z",
    "confidence_score": 0.92,
    "sources": [
        "https://blog.close.com/pricing-objections",
        "Internal sales playbook v3.2",
        "Winning deals analysis Q4 2024"
    ],

    "related_ids": [
        "kb-pricing-value-framework",
        "kb-objection-handling-discovery",
        "kb-enterprise-buying-process"
    ],
    "parent_id": "kb-objection-handling-master",

    "status": "active",
    "created_at": "2024-11-01T09:00:00Z",
    "updated_at": "2024-12-20T14:30:00Z",
    "created_by": "campaign_copywriting_agent",

    "metadata": {
        "sentiment_required": "empathetic",
        "tone": "consultative",
        "complexity_level": "intermediate",
        "avg_read_time_seconds": 45,
        "languages_available": ["en"],
        "version": "2.1"
    }
}
```

---

## Auto-Extraction Rules

### Pattern Detection Criteria

1. **From Successful Responses**:
   - Identify responses with success_score >= 0.8 from response_tracking table
   - Look for patterns appearing in 5+ responses within 30 days
   - Extract common phrases, structures, or approaches
   - Remove client-specific details (names, companies, specific numbers)
   - Create generalizable templates

2. **From FAQ Patterns**:
   - Detect questions asked 3+ times by different leads
   - Find responses with positive sentiment (replied + positive_reply)
   - Extract Q&A pair with highest success rate
   - Categorize by question type (product, pricing, technical, process)

3. **From Correction Patterns**:
   - Analyze human corrections in agent_learning table
   - Look for corrections where corrected_content is consistently better
   - Extract "what to avoid" patterns from original_action
   - Extract "what to do instead" from corrected_action
   - Create knowledge articles for common correction types

### Extraction Algorithm

```python
async def extract_knowledge_patterns(
    min_success_rate: float = 0.8,
    min_occurrences: int = 5,
    period_days: int = 30
) -> list[ExtractionPattern]:
    """
    Extract reusable knowledge patterns from successful responses.
    """
    from datetime import timedelta
    from collections import defaultdict

    cutoff_date = datetime.utcnow() - timedelta(days=period_days)

    # Query successful responses
    successful_responses = await _query_successful_responses(
        min_success_rate=min_success_rate,
        since=cutoff_date
    )

    # Group by similarity
    pattern_groups = defaultdict(list)
    for response in successful_responses:
        # Use embedding similarity to group
        pattern_key = await _get_pattern_key(response.original_content)
        pattern_groups[pattern_key].append(response)

    # Extract patterns with sufficient occurrences
    patterns = []
    for pattern_key, responses in pattern_groups.items():
        if len(responses) >= min_occurrences:
            pattern = await _create_pattern_from_responses(
                responses,
                pattern_key
            )
            patterns.append(pattern)

    return patterns


async def _create_pattern_from_responses(
    responses: list,
    pattern_key: str
) -> ExtractionPattern:
    """
    Create knowledge article from response pattern.
    """
    # Calculate average success rate
    success_rate = sum(r.success_score for r in responses) / len(responses)

    # Extract common elements
    common_phrases = await _extract_common_phrases(responses)

    # Generalize content (remove specific names, numbers)
    generalized_content = await _generalize_responses(responses)

    # Suggest title based on pattern
    suggested_title = await _generate_title_from_pattern(
        responses,
        common_phrases
    )

    # Determine category
    suggested_category = await _classify_pattern(generalized_content)

    return ExtractionPattern(
        pattern_type="successful_response",
        occurrences=len(responses),
        success_rate=success_rate,
        example_responses=[r.original_content for r in responses[:3]],
        suggested_title=suggested_title,
        suggested_content=generalized_content,
        suggested_category=suggested_category,
        confidence=min(success_rate, 1.0)
    )
```

### Duplicate Detection

Before creating extracted articles:

```python
async def check_duplicate_knowledge(
    title: str,
    content: str,
    similarity_threshold: float = 0.85
) -> dict:
    """
    Check if extracted knowledge is duplicate of existing articles.
    """
    from anthropic import Anthropic

    # Generate embedding for new content
    client = Anthropic()
    new_embedding = await _generate_embedding(client, content)

    # Query similar articles using vector search
    similar_articles = await _vector_search_kb(
        embedding=new_embedding,
        top_k=5,
        threshold=similarity_threshold
    )

    is_duplicate = False
    recommendation = "create_new"

    if similar_articles:
        max_similarity = max(a["similarity"] for a in similar_articles)

        if max_similarity > 0.95:
            is_duplicate = True
            recommendation = "merge"
        elif max_similarity > similarity_threshold:
            is_duplicate = True
            recommendation = "update_existing"

    return {
        "is_duplicate": is_duplicate,
        "similar_articles": similar_articles,
        "max_similarity": max_similarity if similar_articles else 0.0,
        "recommendation": recommendation
    }
```

---

## Performance Tracking Queries

### Article Effectiveness Query

```sql
-- Calculate effectiveness for all active articles
SELECT
    kb.id,
    kb.title,
    kb.category,
    kb.subcategory,
    COUNT(ku.id) as total_uses,
    COUNT(CASE WHEN ku.was_successful THEN 1 END) as successful_uses,
    ROUND(
        COUNT(CASE WHEN ku.was_successful THEN 1 END)::NUMERIC /
        NULLIF(COUNT(ku.id), 0) * 100,
        2
    ) as success_rate,
    AVG(ku.confidence_used) as avg_confidence,
    MAX(ku.created_at) as last_used_at,
    kb.effectiveness_score,
    kb.verified
FROM knowledge_base kb
LEFT JOIN knowledge_usage ku ON ku.kb_article_id = kb.id
WHERE
    kb.status = 'active'
    AND ku.created_at >= NOW() - INTERVAL '30 days'
GROUP BY kb.id
ORDER BY success_rate DESC, total_uses DESC;
```

### Usage Trends Query

```sql
-- Identify trending articles (increasing usage)
WITH usage_periods AS (
    SELECT
        kb_article_id,
        DATE_TRUNC('week', created_at) as week,
        COUNT(*) as uses
    FROM knowledge_usage
    WHERE created_at >= NOW() - INTERVAL '90 days'
    GROUP BY kb_article_id, DATE_TRUNC('week', created_at)
),
trend_analysis AS (
    SELECT
        kb_article_id,
        REGR_SLOPE(uses, EXTRACT(EPOCH FROM week)) as trend_slope,
        AVG(uses) as avg_weekly_uses
    FROM usage_periods
    GROUP BY kb_article_id
)
SELECT
    kb.id,
    kb.title,
    kb.category,
    ta.avg_weekly_uses,
    ta.trend_slope,
    CASE
        WHEN ta.trend_slope > 1 THEN 'rapidly_increasing'
        WHEN ta.trend_slope > 0.1 THEN 'increasing'
        WHEN ta.trend_slope > -0.1 THEN 'stable'
        WHEN ta.trend_slope > -1 THEN 'decreasing'
        ELSE 'rapidly_decreasing'
    END as trend_category
FROM knowledge_base kb
JOIN trend_analysis ta ON ta.kb_article_id = kb.id
WHERE kb.status = 'active'
ORDER BY ta.trend_slope DESC;
```

### Gap Analysis Query

```sql
-- Identify knowledge gaps (common queries without good KB matches)
WITH query_patterns AS (
    SELECT
        LOWER(query_text) as query,
        COUNT(*) as frequency,
        AVG(confidence_used) as avg_confidence
    FROM knowledge_usage
    WHERE
        created_at >= NOW() - INTERVAL '30 days'
        AND confidence_used < 0.7  -- Low confidence indicates poor match
    GROUP BY LOWER(query_text)
    HAVING COUNT(*) >= 3
)
SELECT
    query,
    frequency,
    avg_confidence,
    'knowledge_gap' as gap_type,
    CASE
        WHEN frequency >= 10 THEN 'high_priority'
        WHEN frequency >= 5 THEN 'medium_priority'
        ELSE 'low_priority'
    END as priority
FROM query_patterns
ORDER BY frequency DESC, avg_confidence ASC
LIMIT 20;
```

### Retirement Candidates Query

```sql
-- Find articles that should be retired
SELECT
    kb.id,
    kb.title,
    kb.category,
    kb.created_at,
    kb.last_used_at,
    kb.usage_count,
    COALESCE(recent_usage.uses_last_90_days, 0) as uses_last_90_days,
    COALESCE(recent_usage.success_rate, 0) as recent_success_rate,
    kb.effectiveness_score,
    CASE
        WHEN kb.last_used_at IS NULL THEN 'never_used'
        WHEN kb.last_used_at < NOW() - INTERVAL '180 days' THEN 'stale'
        WHEN COALESCE(recent_usage.uses_last_90_days, 0) < 10 THEN 'low_usage'
        WHEN COALESCE(recent_usage.success_rate, 0) < 50 THEN 'low_effectiveness'
        ELSE 'review'
    END as retirement_reason
FROM knowledge_base kb
LEFT JOIN (
    SELECT
        kb_article_id,
        COUNT(*) as uses_last_90_days,
        ROUND(
            COUNT(CASE WHEN was_successful THEN 1 END)::NUMERIC /
            NULLIF(COUNT(*), 0) * 100,
            2
        ) as success_rate
    FROM knowledge_usage
    WHERE created_at >= NOW() - INTERVAL '90 days'
    GROUP BY kb_article_id
) recent_usage ON recent_usage.kb_article_id = kb.id
WHERE
    kb.status = 'active'
    AND kb.category NOT IN ('policies', 'legal')  -- Never auto-retire
    AND (
        kb.last_used_at IS NULL
        OR kb.last_used_at < NOW() - INTERVAL '90 days'
        OR COALESCE(recent_usage.uses_last_90_days, 0) < 10
        OR COALESCE(recent_usage.success_rate, 0) < 50
    )
ORDER BY
    CASE retirement_reason
        WHEN 'never_used' THEN 1
        WHEN 'stale' THEN 2
        WHEN 'low_effectiveness' THEN 3
        WHEN 'low_usage' THEN 4
        ELSE 5
    END,
    kb.created_at ASC;
```

---

## Error Handling Strategy

### Error Types and Responses

| Error Type | Detection | Response | Retry Strategy | User Impact |
|------------|-----------|----------|----------------|-------------|
| Duplicate article submission | Similarity check >85% | Return duplicates, suggest merge/update | No retry | Low - inform submitter |
| Invalid category | Validation failure | Auto-suggest category, request human review | No retry | Low - can be corrected |
| Validation source unavailable | HTTP timeout/404 | Skip source, reduce confidence score | Yes, 3x with backoff | Medium - affects accuracy |
| Database connection lost | psycopg2.Error | Use cached data, queue writes | Yes, 3x with 2s backoff | High - blocks operations |
| Embedding generation failed | Claude API error | Fall back to keyword matching | Yes, 3x exp backoff | Medium - affects quality |
| Pattern extraction timeout | Processing >30s | Save partial results, continue async | No retry | Low - background task |
| Article creation failed | DB constraint violation | Log error, notify admin | Yes, 1x | High - data loss risk |
| Notification delivery failed | Slack/Email error | Queue for retry, log failure | Yes, 3x with 1hr backoff | Low - informational only |
| Relationship graph too large | Memory limit exceeded | Process in batches, limit depth | No retry | Medium - partial results |
| Report generation failed | Timeout/error | Return partial report, flag incomplete | Yes, 1x | Medium - missing insights |

### Recovery Procedures

1. **Submission Processing Failure**:
   ```python
   try:
       result = await curate_knowledge_article(submission_id, action)
   except ValidationError as e:
       # Validation errors are user-correctable
       return {"status": "error", "message": str(e), "correctable": True}
   except DatabaseError as e:
       # Infrastructure errors - queue for retry
       await queue_for_retry(submission_id, delay_minutes=5)
       logger.error(f"DB error curating {submission_id}: {e}")
       return {"status": "queued", "retry_in": "5 minutes"}
   except Exception as e:
       # Unexpected errors - alert and investigate
       await alert_ops_team(f"Curation failure: {submission_id}", error=e)
       return {"status": "failed", "contact_support": True}
   ```

2. **Validation Failure Handling**:
   ```python
   async def validate_with_fallback(article_id: str) -> dict:
       try:
           # Primary validation method
           result = await validate_from_sources(article_id)
       except SourceUnavailableError:
           # Fall back to cross-reference with existing KB
           result = await cross_reference_validation(article_id)
           result["validation_method"] = "fallback_cross_reference"
       except Exception as e:
           # Flag for human review
           await flag_for_human_review(
               article_id,
               reason=f"Validation failed: {e}"
           )
           result = {
               "status": "needs_human_review",
               "reason": str(e)
           }
       return result
   ```

3. **Pattern Extraction Resilience**:
   ```python
   async def extract_patterns_with_timeout(
       min_success_rate: float,
       timeout_seconds: int = 30
   ) -> dict:
       try:
           async with asyncio.timeout(timeout_seconds):
               patterns = await extract_from_responses(min_success_rate)
       except asyncio.TimeoutError:
           # Save partial results
           partial_patterns = await get_partial_extraction_results()
           await save_extraction_checkpoint(partial_patterns)
           # Continue in background
           asyncio.create_task(complete_extraction_async())
           return {
               "status": "partial",
               "patterns": partial_patterns,
               "completing_async": True
           }
       return {"status": "complete", "patterns": patterns}
   ```

---

## Testing Requirements

### Unit Tests (>90% coverage required)

**Test file**: `__tests__/unit/agents/system/test_knowledge_base_manager.py`

```python
class TestKnowledgeBaseManagerInitialization:
    def test_agent_initialization(self):
        """Verify agent initializes correctly"""

    def test_tools_registered(self):
        """Verify all 8 tools are registered"""

    def test_system_prompt_defined(self):
        """Verify system prompt is not empty"""


class TestCurateKnowledgeArticle:
    @pytest.mark.asyncio
    async def test_curate_approve_success(self):
        """Test successful article approval and creation"""

    @pytest.mark.asyncio
    async def test_curate_detect_duplicate(self):
        """Test duplicate detection with >85% similarity"""

    @pytest.mark.asyncio
    async def test_curate_reject_with_reason(self):
        """Test rejection with notes"""

    @pytest.mark.asyncio
    async def test_curate_request_changes(self):
        """Test requesting changes to submission"""

    @pytest.mark.asyncio
    async def test_curate_auto_categorization(self):
        """Test automatic category assignment"""

    @pytest.mark.asyncio
    async def test_curate_validation_scheduling(self):
        """Test validation is scheduled when required"""


class TestValidateKnowledgeAccuracy:
    @pytest.mark.asyncio
    async def test_validate_from_sources(self):
        """Test validation using source URLs"""

    @pytest.mark.asyncio
    async def test_validate_cross_reference(self):
        """Test cross-reference validation"""

    @pytest.mark.asyncio
    async def test_validate_source_unavailable(self):
        """Test fallback when source unavailable"""

    @pytest.mark.asyncio
    async def test_validate_confidence_scoring(self):
        """Test accuracy confidence score calculation"""

    @pytest.mark.asyncio
    async def test_validate_discrepancy_detection(self):
        """Test detecting factual discrepancies"""


class TestTrackKnowledgeUsage:
    @pytest.mark.asyncio
    async def test_track_usage_by_article(self):
        """Test usage tracking for specific article"""

    @pytest.mark.asyncio
    async def test_track_usage_by_category(self):
        """Test usage tracking grouped by category"""

    @pytest.mark.asyncio
    async def test_track_usage_trends(self):
        """Test identifying trending articles"""

    @pytest.mark.asyncio
    async def test_track_unused_articles(self):
        """Test finding articles with no usage"""


class TestCalculateEffectiveness:
    @pytest.mark.asyncio
    async def test_effectiveness_calculation(self):
        """Test effectiveness score calculation"""

    @pytest.mark.asyncio
    async def test_effectiveness_by_segment(self):
        """Test segmented effectiveness analysis"""

    @pytest.mark.asyncio
    async def test_effectiveness_trend_detection(self):
        """Test detecting improving/declining effectiveness"""

    @pytest.mark.asyncio
    async def test_effectiveness_baseline_comparison(self):
        """Test comparison to no-KB baseline"""


class TestExtractFromResponses:
    @pytest.mark.asyncio
    async def test_extract_successful_patterns(self):
        """Test extracting patterns from successful responses"""

    @pytest.mark.asyncio
    async def test_extract_min_occurrences_filter(self):
        """Test filtering by minimum occurrences"""

    @pytest.mark.asyncio
    async def test_extract_generalization(self):
        """Test removing client-specific details"""

    @pytest.mark.asyncio
    async def test_extract_duplicate_check(self):
        """Test checking against existing KB"""

    @pytest.mark.asyncio
    async def test_extract_auto_create_drafts(self):
        """Test automatic draft article creation"""


class TestCreateKnowledgeRelationships:
    @pytest.mark.asyncio
    async def test_create_related_links(self):
        """Test creating related article links"""

    @pytest.mark.asyncio
    async def test_create_hierarchical_relationships(self):
        """Test parent-child relationships"""

    @pytest.mark.asyncio
    async def test_detect_orphaned_articles(self):
        """Test finding articles with no relationships"""

    @pytest.mark.asyncio
    async def test_bidirectional_links(self):
        """Test creating two-way relationships"""


class TestRetireKnowledge:
    @pytest.mark.asyncio
    async def test_retire_low_usage(self):
        """Test retiring articles with low usage"""

    @pytest.mark.asyncio
    async def test_retire_low_effectiveness(self):
        """Test retiring articles with poor effectiveness"""

    @pytest.mark.asyncio
    async def test_retire_dry_run(self):
        """Test dry run mode (preview only)"""

    @pytest.mark.asyncio
    async def test_retire_preserve_references(self):
        """Test keeping articles for historical queries"""

    @pytest.mark.asyncio
    async def test_retire_exclude_categories(self):
        """Test never retiring protected categories"""


class TestGenerateKBReport:
    @pytest.mark.asyncio
    async def test_generate_weekly_report(self):
        """Test weekly report generation"""

    @pytest.mark.asyncio
    async def test_generate_monthly_report(self):
        """Test monthly report generation"""

    @pytest.mark.asyncio
    async def test_report_top_performers(self):
        """Test identifying top performing articles"""

    @pytest.mark.asyncio
    async def test_report_gap_analysis(self):
        """Test knowledge gap identification"""

    @pytest.mark.asyncio
    async def test_report_formatting(self):
        """Test report formatting (markdown/html/json)"""
```

### Integration Tests

**Test file**: `__tests__/integration/test_knowledge_base_manager_integration.py`

```python
class TestKnowledgeBaseManagerIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_curation_flow(self):
        """Test complete flow from submission to active article"""

    @pytest.mark.asyncio
    async def test_extraction_to_kb_pipeline(self):
        """Test extracting patterns and creating KB articles"""

    @pytest.mark.asyncio
    async def test_usage_tracking_accuracy(self):
        """Test accuracy of usage tracking"""

    @pytest.mark.asyncio
    async def test_effectiveness_measurement(self):
        """Test measuring real effectiveness from outcomes"""


class TestKnowledgeBaseQueryIntegration:
    @pytest.mark.asyncio
    async def test_agent_query_and_usage_tracking(self):
        """Test query from response agent triggers usage tracking"""

    @pytest.mark.asyncio
    async def test_faq_submission_to_kb(self):
        """Test FAQ evolution agent submitting to KB"""

    @pytest.mark.asyncio
    async def test_learning_feedback_integration(self):
        """Test receiving patterns from learning feedback agent"""


class TestKnowledgeBaseAPI:
    @pytest.mark.asyncio
    async def test_curate_api_endpoint(self):
        """Test curation API endpoint"""

    @pytest.mark.asyncio
    async def test_validate_api_endpoint(self):
        """Test validation API endpoint"""

    @pytest.mark.asyncio
    async def test_report_api_endpoint(self):
        """Test report generation API"""
```

---

## Implementation Checklist

### Phase 1: Core Curation & Validation
- [ ] Implement `KnowledgeBaseManagerAgent` class extending `BaseAgent`
- [ ] Implement `curate_knowledge_article` tool with duplicate detection
- [ ] Implement `validate_knowledge_accuracy` tool with source checking
- [ ] Create database tables (`knowledge_usage`, `knowledge_relationships`, `knowledge_validation_log`)
- [ ] Add curation API endpoints
- [ ] Write unit tests for curation and validation (>90% coverage)

### Phase 2: Usage Tracking & Effectiveness
- [ ] Implement `track_knowledge_usage` tool with trend analysis
- [ ] Implement `calculate_effectiveness` tool with segmentation
- [ ] Create usage tracking hooks in response agents
- [ ] Implement effectiveness calculation queries
- [ ] Write unit tests for tracking and effectiveness

### Phase 3: Auto-Extraction
- [ ] Implement `extract_from_responses` tool
- [ ] Create pattern detection algorithms
- [ ] Implement generalization logic (remove client details)
- [ ] Create duplicate checking with vector similarity
- [ ] Write unit tests for extraction

### Phase 4: Relationship Management
- [ ] Implement `create_knowledge_relationships` tool
- [ ] Create similarity-based relationship detection
- [ ] Implement hierarchical relationship support
- [ ] Create relationship graph queries
- [ ] Write unit tests for relationship management

### Phase 5: Lifecycle Management
- [ ] Implement `retire_knowledge` tool
- [ ] Create retirement criteria evaluation
- [ ] Implement dry-run mode for preview
- [ ] Create notification system for stakeholders
- [ ] Write unit tests for retirement

### Phase 6: Reporting & Analytics
- [ ] Implement `generate_kb_report` tool
- [ ] Create report templates (weekly, monthly, quarterly)
- [ ] Implement gap analysis queries
- [ ] Create report delivery system (email/Slack)
- [ ] Write unit tests for reporting

### Phase 7: Integration & Testing
- [ ] Integrate with response-knowledge-base agent (query interface)
- [ ] Integrate with response-faq-evolution agent (submissions)
- [ ] Integrate with system-learning-feedback agent (patterns)
- [ ] Integrate with system-response-outcome-tracker (effectiveness)
- [ ] Write comprehensive integration tests

### Phase 8: Optimization & Polish
- [ ] Achieve >90% test coverage
- [ ] Performance test with large KB (1000+ articles)
- [ ] Optimize queries for large datasets
- [ ] Test failure scenarios and recovery
- [ ] Document all procedures and runbooks

---

## Success Metrics

- **Curation Efficiency**: >95% of submissions processed within 24 hours
- **Accuracy**: >90% of validated articles confirmed accurate
- **Usage Coverage**: >80% of agent queries find relevant KB article
- **Effectiveness**: Articles with >70% success rate maintained at >80% of active KB
- **Auto-Extraction Accuracy**: >85% of extracted patterns approved by humans
- **Gap Detection**: Knowledge gaps identified and filled within 7 days
- **Retirement Accuracy**: <5% of retired articles later deemed necessary
- **Report Actionability**: >75% of report recommendations implemented
- **Test Coverage**: >90% code coverage
- **System Uptime**: >99.5% availability
- **Processing Speed**: Curation operations complete in <5 seconds (95th percentile)

---

## Dependencies

### Python Packages (already installed)
- `anthropic>=0.75.0` - Claude API for embeddings and analysis
- `sqlalchemy>=2.0.44` - Database operations
- `asyncpg>=0.31.0` - PostgreSQL async driver
- `pinecone-client>=6.0.0` - Vector similarity search
- `httpx>=0.27.0` - HTTP client for source validation

### External Services
- **Database**: PostgreSQL (Supabase)
- **Vector Database**: Pinecone (for semantic similarity)
- **Cache**: Redis (Upstash)
- **Notifications**: Slack, Email
- **Monitoring**: Internal monitoring system

### Agent Dependencies
- **Consumes From**:
  - `response_faq_evolution` - FAQ submissions
  - `system_learning_feedback` - Pattern insights
  - `system_response_outcome_tracker` - Effectiveness data

- **Serves To**:
  - `response_knowledge_base` - Query interface (provides usage data)
  - All 73+ agents - Curated knowledge repository

---

## Human-in-the-Loop

### Approval Gates
1. **Critical Content Review**: Pricing, legal, policy changes require human approval
2. **Low Confidence Articles**: Articles with confidence <0.7 require human verification
3. **Retirement Decisions**: Retiring articles used >100 times requires approval
4. **Relationship Changes**: Major graph restructuring requires review

### Manual Interventions
1. **Content Accuracy**: Manual fact-checking for critical domains
2. **Category Reassignment**: Manual adjustment of article categories
3. **Extraction Approval**: Human review of auto-extracted knowledge
4. **Gap Prioritization**: Manual prioritization of knowledge gaps

---

## Future Enhancements

1. **Multi-Language Support**: Translate high-performing articles to other languages
2. **Personalization**: Client-specific knowledge variants based on industry/size
3. **Predictive Analytics**: ML models to predict article effectiveness before creation
4. **Interactive Reports**: Dashboards for real-time KB health monitoring
5. **Automated A/B Testing**: Test article variants to optimize effectiveness
6. **Version Control**: Full version history with diff views and rollback
7. **Collaborative Editing**: Multiple agents/humans collaborating on articles
8. **Knowledge Graph Visualization**: Interactive visualization of relationships
9. **Sentiment-Aware Curation**: Consider sentiment in effectiveness measurement
10. **External Source Integration**: Auto-import from company blog, docs, wikis

---

## Security Considerations

1. **Access Control**: Role-based permissions for creating, editing, retiring articles
2. **Audit Trail**: Complete audit log of all KB changes with author tracking
3. **PII Detection**: Scan for and remove personally identifiable information
4. **Source Validation**: Verify source URLs are safe and legitimate
5. **Content Sanitization**: Strip malicious content from submissions
6. **API Rate Limiting**: Prevent abuse of KB APIs
7. **Data Encryption**: Encrypt sensitive KB content at rest

---

## Performance Requirements

1. **Throughput**: Process 100+ curation requests per day
2. **Latency**:
   - Curation: <5s (95th percentile)
   - Validation: <10s (95th percentile)
   - Usage tracking: <100ms
   - Effectiveness calculation: <30s
   - Report generation: <60s
3. **Storage**: Efficient storage for 5000+ articles with full history
4. **Memory**: <3GB RAM usage during peak processing
5. **Concurrency**: Support 20 simultaneous curation operations

---

## Related Agents

This agent integrates with:
- **Response Knowledge Base Agent**: Primary query interface
- **Response FAQ Evolution Agent**: Receives FAQ submissions
- **System Learning Feedback Agent**: Receives pattern insights
- **System Response Outcome Tracker**: Receives effectiveness data
- **System Correction Approval Orchestrator**: Routes major changes

Serves all 73+ agents with curated knowledge.
