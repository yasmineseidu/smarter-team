# Duplicate Detection Agent - Production Specification

## Metadata

**Agent Name:** `duplicate_detection`
**Category:** Lead Generation & Data
**Priority:** Phase 1 - MVP Foundation
**Dependencies:** Lead List Builder Agent (runs during import)
**Coverage Target:** >85% (agent requirement)
**Rate Limit:** None (internal operations)

---

## Purpose

Prevent duplicate leads across the database using sophisticated fuzzy matching algorithms. Automatically merge exact matches, flag potential duplicates for human review, and maintain data quality standards to ensure clean lead lists for marketing campaigns.

---

## System Prompt

```
You are the Duplicate Detection Agent for Smarter Team, an autonomous AI agency.

Your primary responsibility is to identify and handle duplicate leads in the database using multiple matching algorithms and confidence scoring. You ensure data integrity by preventing duplicate records while preserving valuable lead information.

**Core Responsibilities:**
1. Scan incoming leads against existing database records using multiple matching criteria
2. Apply fuzzy matching algorithms with configurable confidence thresholds
3. Auto-merge exact matches (confidence ≥85%) with audit trail logging
4. Flag potential duplicates (confidence 60-84%) for human review
5. Log all duplicate detection decisions and merges for audit purposes
6. Maintain performance through efficient database queries and batch processing

**Matching Algorithms:**
- Email: Exact match after normalization (lowercase, remove dots/plus)
- Name + Company: Fuzzy match using Levenshtein distance (threshold: 80%)
- LinkedIn URL: Exact match after normalization
- Phone Number: Exact match after normalization (E.164 format)
- Domain + Job Title: Fuzzy match with industry consideration

**Confidence Scoring:**
- Exact email match: 95% confidence
- Name + Company match (≥90%): 85% confidence
- LinkedIn URL match: 90% confidence
- Phone number match: 85% confidence
- Multiple weak matches: Additive scoring

**Decision Framework:**
- CONFIDENCE ≥85%: Auto-merge exact duplicates, log to merge_logs
- CONFIDENCE 60-84%: Flag for human review, create review task
- CONFIDENCE <60%: Consider unique, proceed with import
- TIES (multiple matches): Flag for human review with all candidates

**Data Preservation Rules:**
- Keep most recent created_at timestamp
- Merge non-null fields (union of data)
- Preserve original source information
- Track merge history in audit trail

**Performance Requirements:**
- Process 1000 leads/minute minimum
- Use database indexes for efficient querying
- Batch similar operations for performance
- Cache recent comparisons (24-hour TTL)

**Error Handling:**
- Database failures: Retry with exponential backoff (max 3 attempts)
- Algorithm failures: Log error, continue with next lead
- Merge conflicts: Flag for human resolution
- Performance degradation: Alert if <500 leads/minute

You work autonomously but ensure all duplicate decisions are logged for audit trails and system optimization.
```

---

## Agent Implementation

### Class Definition

```python
from src.agents.base_agent import BaseAgent
from src.config import Settings, get_agent_logger
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import re
from difflib import SequenceMatcher
import hashlib

class DuplicateDetectionAgent(BaseAgent):
    """
    Duplicate Detection Agent - Identifies and handles duplicate leads.

    Uses fuzzy matching algorithms and confidence scoring to detect duplicates.
    Auto-merges exact matches and flags potential duplicates for review.
    """

    def __init__(self, settings: Settings):
        super().__init__(
            name="duplicate_detection",
            description="Detects and handles duplicate leads using fuzzy matching"
        )
        self.settings = settings
        # Confidence thresholds
        self.auto_merge_threshold = 0.85
        self.review_threshold = 0.60
        # Algorithm weights for scoring
        self.weights = {
            'email': 0.35,
            'name_company': 0.30,
            'linkedin': 0.20,
            'phone': 0.15
        }

    @property
    def system_prompt(self) -> str:
        return """[See System Prompt section above]"""

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Process duplicate detection task."""
        task_type = task.get("type")

        if task_type == "check_batch":
            return await self._check_batch_duplicates(task)
        elif task_type == "check_single":
            return await self._check_single_duplicate(task)
        elif task_type == "merge_duplicates":
            return await self._merge_duplicate_group(task)
        elif task_type == "flag_for_review":
            return await self._flag_for_human_review(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
```

---

## Tools

### 1. `normalize_email`

**Purpose:** Standardize email format for accurate matching

**Parameters:**
```python
{
    "email": str,                   # Email address to normalize
    "lowercase": bool = True,       # Convert to lowercase
    "remove_dots": bool = True,     # Remove dots from Gmail addresses
    "remove_plus": bool = True      # Remove plus aliases
}
```

**Returns:**
```python
{
    "normalized": str,              # Normalized email
    "domain": str,                  # Extracted domain
    "is_valid": bool,               # Valid email format
    "original": str                 # Original email
}
```

**Error Handling:**
- Invalid email format → Return empty normalized, is_valid=False
- Null/empty email → Return empty strings, is_valid=False

### 2. `normalize_phone`

**Purpose:** Standardize phone numbers to E.164 format

**Parameters:**
```python
{
    "phone": str,                   # Phone number to normalize
    "country_code": str = "US",     # Default country for parsing
    "format": str = "E.164"         # Output format
}
```

**Returns:**
```python
{
    "normalized": str,              # E.164 formatted number
    "is_valid": bool,               # Valid phone format
    "country": str,                 # Detected country
    "original": str                 # Original phone
}
```

**Error Handling:**
- Invalid phone format → Return empty normalized, is_valid=False
- Unable to parse → Return original with is_valid=False

### 3. `fuzzy_match_strings`

**Purpose:** Calculate similarity between two strings using multiple algorithms

**Parameters:**
```python
{
    "string1": str,                 # First string
    "string2": str,                 # Second string
    "algorithm": str = "levenshtein",  # Algorithm: levenshtein, jaro, difflib
    "threshold": float = 0.8        # Minimum similarity score
}
```

**Returns:**
```python
{
    "similarity": float,            # Similarity score (0-1)
    "is_match": bool,               # Above threshold
    "algorithm": str,               # Algorithm used
    "details": dict                 # Algorithm-specific details
}
```

**Error Handling:**
- Empty strings → Return similarity=0.0, is_match=False
- Algorithm error → Default to difflib, log warning

### 4. `query_existing_leads`

**Purpose:** Search database for potential duplicate leads

**Parameters:**
```python
{
    "email": Optional[str],         # Normalized email to match
    "name": Optional[str],          # Name to fuzzy match
    "company": Optional[str],       # Company to fuzzy match
    "linkedin_url": Optional[str],  # LinkedIn URL to match
    "phone": Optional[str],         # Normalized phone to match
    "limit": int = 100,             # Max candidates to return
    "exclude_ids": List[str] = []   # IDs to exclude from search
}
```

**Returns:**
```python
{
    "candidates": List[dict],       # Potential duplicate records
    "total_found": int,             # Total candidates
    "query_time_ms": float,         # Database query duration
    "search_params": dict           # What was searched for
}
```

**Error Handling:**
- Database connection error → Retry 3x with exponential backoff
- Query timeout → Return empty candidates, log error
- Invalid parameters → Return validation error

### 5. `calculate_confidence_score`

**Purpose:** Calculate overall duplicate confidence using weighted scoring

**Parameters:**
```python
{
    "matches": dict,                # Match results from various algorithms
    "weights": Optional[dict]       # Custom weights (override defaults)
}
```

**Returns:**
```python
{
    "confidence": float,            # Overall confidence score (0-1)
    "match_details": dict,          # Breakdown by match type
    "recommendation": str,          # "merge", "review", or "unique"
    "reasoning": str                # Explanation of score
}
```

**Error Handling:**
- Missing match data → Return confidence=0.0, recommend="unique"
- Invalid weights → Use default weights, log warning

### 6. `merge_duplicate_records`

**Purpose:** Merge two or more duplicate lead records

**Parameters:**
```python
{
    "primary_id": str,              # ID of record to keep (master)
    "duplicate_ids": List[str],     # IDs of records to merge
    "merge_strategy": str = "union", # union, latest, or custom
    "preserve_history": bool = True  # Keep merge audit trail
}
```

**Returns:**
```python
{
    "success": bool,                # Merge completed successfully
    "merged_record": dict,          # Final merged record
    "merged_ids": List[str],        # IDs that were merged
    "merge_id": str,                # Audit log entry ID
    "fields_updated": List[str]     # Which fields were changed
}
```

**Error Handling:**
- Record not found → Fail merge, log missing IDs
- Concurrent modification → Retry with updated data
- Constraint violation → Flag for manual review

### 7. `flag_for_human_review`

**Purpose:** Create review tasks for potential duplicates

**Parameters:**
```python
{
    "lead_id": str,                 # New lead ID
    "candidates": List[dict],       # Potential duplicate records
    "confidence": float,            # Confidence score
    "reasoning": str,               # Why flagged
    "priority": str = "normal"      # Task priority
}
```

**Returns:**
```python
{
    "review_id": str,               # Review task ID
    "assigned_to": Optional[str],   # Assigned reviewer (if any)
    "due_date": datetime,           # Review deadline
    "status": str,                  # "pending", "assigned", etc.
    "notification_sent": bool       # Reviewer notified
}
```

**Error Handling:**
- Unable to create task → Log error, continue processing
- No available reviewers → Keep in queue for assignment

---

## Error Handling Matrix

| Error Type | Detection | Response | Retry | Alert |
|------------|-----------|----------|-------|-------|
| Database connection | Exception on query | Exponential backoff | Yes, 3 attempts | Yes |
| Query timeout | Query >5s | Use cached results | Yes, 1 attempt | No |
| Invalid lead data | Validation failure | Skip record, log | No | Yes |
| Merge conflict | Constraint error | Flag for review | No | Yes |
| Performance <500/min | Timing metrics | Alert ops team | No | Yes |
| Algorithm error | Exception in matching | Use fallback algorithm | No | No |

---

## Database Schema

### `duplicate_checks`
```sql
CREATE TABLE duplicate_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id),
    check_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    candidates JSONB NOT NULL,              -- Potential duplicate IDs with scores
    confidence_score DECIMAL(3,2) NOT NULL, -- 0.00 to 1.00
    recommendation VARCHAR(20) NOT NULL,    -- merge, review, unique
    reasoning TEXT,
    algorithm_version VARCHAR(10) DEFAULT '1.0',
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_duplicate_checks_lead_id ON duplicate_checks(lead_id);
CREATE INDEX idx_duplicate_checks_date ON duplicate_checks(check_date);
CREATE INDEX idx_duplicate_checks_confidence ON duplicate_checks(confidence_score);
```

### `merge_logs`
```sql
CREATE TABLE merge_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_lead_id UUID NOT NULL REFERENCES leads(id),
    merged_lead_ids UUID[] NOT NULL,
    merge_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    merged_by VARCHAR(50) NOT NULL,         -- agent or human
    fields_changed TEXT[],
    merge_strategy VARCHAR(20) DEFAULT 'union',
    pre_merge_data JSONB,                   -- Snapshot before merge
    post_merge_data JSONB,                  -- Snapshot after merge
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_merge_logs_primary_id ON merge_logs(primary_lead_id);
CREATE INDEX idx_merge_logs_date ON merge_logs(merge_date);
```

---

## Testing Strategy

### Unit Tests
```python
def test_normalize_email_gmail():
    """Test Gmail-specific normalization (dots, plus)."""

def test_fuzzy_match_levenshtein():
    """Test Levenshtein distance matching algorithm."""

def test_confidence_scoring():
    """Test weighted confidence score calculation."""

def test_exact_email_match():
    """Test 95% confidence for exact email matches."""

def test_name_company_fuzzy():
    """Test 85% confidence for name+company matches."""

def test_merge_strategy_union():
    """Test union merge preserves non-null fields."""

def test_performance_batch_processing():
    """Verify >1000 leads/minute processing rate."""
```

### Integration Tests
```python
def test_end_to_end_duplicate_detection():
    """Full pipeline with mock database."""

def test_concurrent_duplicate_detection():
    """Handle multiple agents checking same lead."""

def test_merge_conflict_resolution():
    """Resolve conflicting field values during merge."""

def test_review_task_creation():
    """Verify human review tasks are created properly."""

def test_audit_trail_completeness():
    """All actions logged to duplicate_checks/merge_logs."""
```

### Mock Strategy
```python
@pytest.fixture
def mock_database():
    """Mock database with sample duplicate leads."""

@pytest.fixture
def mock_review_assignment():
    """Mock reviewer assignment system."""

@pytest.fixture
def sample_duplicate_scenarios():
    """Common duplicate scenarios for testing."""
```

---

## Performance Requirements

### Throughput
- **Minimum:** 1,000 leads/minute processing
- **Target:** 2,500 leads/minute with optimized indexes
- **Batch Size:** 100-500 leads per batch

### Latency
- **Single check:** <100ms average
- **Batch of 100:** <2 seconds
- **Database query:** <50ms average

### Resource Usage
- **Memory:** <512MB for 10,000 lead batch
- **CPU:** <30% utilization on standard instance
- **Database:** <5 queries/second average

---

## Observability

### Metrics to Track
```python
{
    "duplicate_detection_rate": float,      # % of leads flagged
    "auto_merge_rate": float,              # % merged automatically
    "human_review_rate": float,            # % sent for review
    "processing_latency_ms": float,        # Average check time
    "false_positive_rate": float,          # Wrong duplicates flagged
    "false_negative_rate": float,          # Missed duplicates
    "merge_success_rate": float,           # Successful merges
    "review_completion_time_hours": float  # Time to review
}
```

### Logging
```python
# Structured logging examples
logger.info(
    "Duplicate check completed",
    extra={
        "lead_id": lead.id,
        "candidates_found": len(candidates),
        "confidence_score": confidence,
        "recommendation": "merge",
        "processing_time_ms": processing_time
    }
)

logger.warning(
    "High duplicate rate detected",
    extra={
        "batch_id": batch.id,
        "duplicate_rate": 0.15,
        "threshold": 0.10
    }
)
```

---

## Security & Compliance

### Data Privacy
- Hash PII before logging to duplicate_checks
- Encrypt merge_logs containing sensitive data
- Follow GDPR right to be forgotten (merge logs)

### Access Control
- Only merge agents can modify records
- Reviewers need explicit permissions
- Audit trail immutable (no deletes)

### Data Sanitization
- Remove temporary data after processing
- Sanitize logs for PII before storage
- Validate all inputs before processing

---

## Acceptance Criteria

- [ ] Processes >1,000 leads/minute consistently
- [ ] Auto-merges exact duplicates (≥85% confidence)
- [ ] Flags 60-84% confidence matches for human review
- [ ] Maintains complete audit trail in duplicate_checks and merge_logs
- [ ] Handles concurrent duplicate detection without conflicts
- [ ] Preserves data integrity during merges (union strategy)
- [ ] Generates review tasks with all necessary context
- [ ] Provides comprehensive metrics and logging
- [ ] Handles database failures gracefully with retries
- [ ] Maintains >99.9% uptime with proper error handling

---

## Multi-Agent Integration

### Input Triggers
- **Lead List Builder:** On new lead import
- **Data Validation Agent:** After lead enrichment
- **Manual Upload:** CSV/Excel import workflows
- **API Ingestion:** Real-time lead creation

### Output Handoffs
- **To Review Queue:** Potential duplicates (60-84% confidence)
- **To Campaign Agent:** Clean, deduplicated leads
- **To Notification Agent:** High duplicate rate alerts

### Context Sharing
- Lead metadata for matching context
- Confidence scores for reviewer decisions
- Merge history for data lineage

---

## Implementation Priority

**Phase 1 (MVP - Immediate):**
1. Basic exact email matching
2. Simple name + company fuzzy matching
3. Auto-merge exact duplicates
4. Basic audit logging

**Phase 2 (Enhancement - Week 2):**
1. LinkedIn URL matching
2. Phone number normalization
3. Weighted confidence scoring
4. Human review workflow

**Phase 3 (Advanced - Week 3):**
1. Advanced fuzzy matching algorithms
2. Batch optimization
3. Performance monitoring
4. ML-based confidence tuning
