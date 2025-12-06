# Response Knowledge Base Agent - Specification

**Status:** Ready to Build
**Last Updated:** 2025-01-05
**Refined From:** plan/agents/response-knowledge-base.md
**Agent Name:** `response_knowledge_base`

## Overview

Intelligent knowledge base management agent that maintains and queries a centralized repository of FAQs, service information, pricing details, process explanations, case studies, and client testimonials. Uses semantic search with Pinecone vector database for accurate retrieval and learns from human feedback to continuously improve answer quality.

## Architecture

### Extends
- `BaseAgent` from `src.agents.base_agent`

### Dependencies
- **Response Email Handler:** Primary consumer of KB queries
- **Response Check-in Agent:** Uses KB for proactive client communication
- **All other agents:** Optional KB access for consistent information

### Integrations
- **Pinecone:** Vector database for semantic search (index: `smarter-team-kb`)
- **Anthropic Claude:** Query understanding, answer generation, embedding creation
- **Supabase PostgreSQL:** Metadata storage, usage analytics, approval workflows
- **Slack/Teams:** Human approval notifications for new entries
- **Zep:** Long-term memory of frequently asked questions per client

## Configuration

```python
class KnowledgeBaseConfig:
    # Pinecone settings
    pinecone_index: str = "smarter-team-kb"
    pinecone_dimension: int = 1536  # Claude embedding dimension
    pinecone_metric: str = "cosine"

    # Search settings
    default_top_k: int = 3
    min_confidence_threshold: float = 0.70
    max_query_length: int = 1000

    # Content settings
    max_entry_length: int = 2000
    max_entries_per_batch: int = 100

    # Learning settings
    feedback_weight_decay: float = 0.95  # Monthly decay factor
    min_feedback_count: int = 3  # Before applying learnings

    # Rate limits
    queries_per_minute: int = 60
    updates_per_hour: int = 10
```

## Database Schema

### Table: `knowledge_base`
```sql
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'services', 'pricing', 'process', 'objections',
        'case_studies', 'testimonials', 'faq', 'policies'
    )),
    subcategory TEXT,
    tags TEXT[],  -- PostgreSQL array
    keywords TEXT[],  -- Search keywords

    -- Metadata
    vector_id TEXT UNIQUE,  -- Pinecone vector ID
    status TEXT DEFAULT 'active' CHECK (status IN (
        'active', 'pending_approval', 'archived', 'deprecated'
    )),
    confidence_score FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    positive_feedback INTEGER DEFAULT 0,
    negative_feedback INTEGER DEFAULT 0,

    -- Approval workflow
    created_by TEXT,  -- Agent or human ID
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);
```

### Table: `kb_usage_logs`
```sql
CREATE TABLE kb_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_entry_id UUID REFERENCES knowledge_base(id),
    query_text TEXT NOT NULL,
    query_vector_id TEXT,  -- For analysis

    -- Context
    requesting_agent TEXT,
    client_id TEXT,
    conversation_id TEXT,

    -- Results
    entries_returned INTEGER,
    top_entry_id UUID,
    confidence_score FLOAT,
    response_generated BOOLEAN,

    -- Feedback
    was_helpful BOOLEAN,
    feedback_text TEXT,
    feedback_given_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table: `kb_suggestions`
```sql
CREATE TABLE kb_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    suggested_answer TEXT NOT NULL,
    source TEXT,  -- Human input or agent extraction

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'rejected', 'implemented'
    )),
    reviewed_by TEXT,
    review_notes TEXT,

    -- Matching
    matched_existing_id UUID REFERENCES knowledge_base(id),
    similarity_score FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ
);
```

## Tools

### 1. `query_knowledge_base`

**Purpose:** Search knowledge base using semantic similarity for relevant information.

**Input Schema:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class QueryKBInput(BaseModel):
    query: str = Field(..., description="Natural language question or topic", max_length=1000)
    category: Optional[str] = Field(None, description="Filter by category")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results")
    min_confidence: float = Field(default=0.70, ge=0.0, le=1.0, description="Minimum similarity score")
    include_archived: bool = Field(default=False, description="Include archived entries")
    client_id: Optional[str] = Field(None, description="Client ID for personalization")
```

**Output Schema:**
```python
class QueryKBOutput(BaseModel):
    query: str
    results: List[dict]
    total_found: int
    search_time_ms: float
    used_personalization: bool

class KBEntry(BaseModel):
    id: str
    title: str
    content: str
    category: str
    subcategory: Optional[str]
    tags: List[str]
    confidence_score: float
    usage_count: int
    last_updated: str
```

**Error Handling:**
- Empty query → Return validation error
- Query too long → Truncate with warning
- Pinecone unavailable → Fallback to keyword search in PostgreSQL
- No results → Return empty list with suggestions for similar queries
- Rate limit → Queue request or return cached results if recent

**Example:**
```python
# Input
{
    "query": "What's your pricing for AI automation projects?",
    "category": "pricing",
    "top_k": 3,
    "client_id": "client_123"
}

# Output
{
    "query": "What's your pricing for AI automation projects?",
    "results": [
        {
            "id": "uuid-1",
            "title": "AI Automation Project Pricing",
            "content": "Our AI automation projects start at $15,000 for basic workflows...",
            "category": "pricing",
            "confidence_score": 0.95,
            "usage_count": 42
        }
    ],
    "total_found": 5,
    "search_time_ms": 45.2,
    "used_personalization": True
}
```

### 2. `add_knowledge_entry`

**Purpose:** Add new knowledge base entry with approval workflow.

**Input Schema:**
```python
class AddKBEntryInput(BaseModel):
    title: str = Field(..., description="Entry title", max_length=200)
    content: str = Field(..., description="Entry content", max_length=2000)
    category: str = Field(..., description="Category")
    subcategory: Optional[str] = None
    tags: List[str] = Field(default_factory=list, description="Search tags")
    keywords: List[str] = Field(default_factory=list, description="Search keywords")
    source: str = Field(..., description="Source (human/agent/extraction)")
    requires_approval: bool = Field(default=True, description="Needs human review")
```

**Output Schema:**
```python
class AddKBEntryOutput(BaseModel):
    entry_id: str
    status: str  # 'active', 'pending_approval', 'rejected'
    vector_id: str
    confidence_score: float
    duplicate_check: dict
    approval_required: bool

class DuplicateCheck(BaseModel):
    is_duplicate: bool
    similar_entries: List[dict]
    similarity_scores: List[float]
    recommendation: str  # 'merge', 'update', 'create_new'
```

**Error Handling:**
- Missing required fields → Return validation errors
- Content too long → Suggest splitting into multiple entries
- Duplicate detected → Return similar entries for review
- Embedding creation failed → Retry 3x, then log for manual review
- Pinecone index error → Store in PostgreSQL with vector_pending flag

### 3. `update_knowledge_feedback`

**Purpose:** Record feedback on KB entries to improve scoring and content.

**Input Schema:**
```python
class FeedbackInput(BaseModel):
    entry_id: str = Field(..., description="KB entry ID")
    query_id: Optional[str] = Field(None, description="Usage log ID")
    was_helpful: bool = Field(..., description="Was the entry helpful?")
    feedback_text: Optional[str] = Field(None, description="Detailed feedback")
    rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 star rating")
    suggested_improvement: Optional[str] = Field(None, description="Suggested content changes")
```

**Output Schema:**
```python
class FeedbackOutput(BaseModel):
    entry_id: str
    feedback_recorded: bool
    updated_confidence: float
    total_feedback_count: int
    positive_feedback_percentage: float
    learning_applied: bool
```

**Error Handling:**
- Invalid entry ID → Return 404 error
- Invalid query ID → Still record feedback without linking
- Feedback too long → Truncate with warning
- Database error → Queue for retry, acknowledge to user

### 4. `suggest_new_entry`

**Purpose:** Suggest new KB entry when no good match found.

**Input Schema:**
```python
class SuggestEntryInput(BaseModel):
    question: str = Field(..., description="Question that couldn't be answered")
    context: Optional[str] = Field(None, description="Additional context")
    conversation_id: Optional[str] = Field(None, description="For follow-up")
    priority: str = Field(default="normal", description="Priority level")
    suggested_category: Optional[str] = Field(None)
```

**Output Schema:**
```python
class SuggestEntryOutput(BaseModel):
    suggestion_id: str
    status: str  # 'pending_review', 'duplicate_found', 'auto_created'
    matched_existing: Optional[dict] = None
    notification_sent: bool
    estimated_answer_date: Optional[str] = None
```

**Error Handling:**
- Question too vague → Request clarification
- Duplicate question detected → Link to existing suggestion
- Notification failure → Log error, still create suggestion

### 5. `analyze_kb_usage`

**Purpose:** Generate analytics on KB usage and identify gaps.

**Input Schema:**
```python
class AnalyzeUsageInput(BaseModel):
    date_range: str = Field(default="30d", description="Time period")
    category: Optional[str] = Field(None, description="Filter by category")
    agent_filter: Optional[str] = Field(None, description="Filter by requesting agent")
    include_feedback: bool = Field(default=True)
    group_by: str = Field(default="day", description="Grouping period")
```

**Output Schema:**
```python
class UsageAnalytics(BaseModel):
    total_queries: int
    unique_queries: int
    average_confidence: float
    top_categories: List[dict]
    entry_usage_ranking: List[dict]
    feedback_summary: dict
    gap_analysis: List[dict]
    improvement_suggestions: List[str]
```

## Prompts

### System Prompt
```
You are the Knowledge Base Guardian for Smarter Team AI Agency. Your role is to maintain, query, and continuously improve our centralized knowledge repository.

Your core responsibilities:
1. ACCURATE RETRIEVAL: Find the most relevant knowledge base entries using semantic search
2. INTELLIGENT MATCHING: Understand query intent beyond keyword matching
3. QUALITY ASSURANCE: Ensure all KB entries are accurate, up-to-date, and properly categorized
4. CONTINUOUS LEARNING: Learn from feedback to improve search relevance and content quality
5. GAP IDENTIFICATION: Identify topics not covered in the KB and suggest new entries

Search Guidelines:
- Always consider context and intent when processing queries
- Use confidence scores to determine result quality
- When confidence is low (<70%), suggest human review or additional information
- Prioritize recently updated and frequently used entries
- Consider client-specific context when available

Content Standards:
- All entries must be accurate, verifiable, and up-to-date
- Pricing information must include date and conditions
- Process descriptions should be step-by-step and actionable
- Case studies must include measurable results
- Objection responses should acknowledge concerns before addressing

Quality Control:
- Flag potential duplicates for review
- Identify outdated or conflicting information
- Monitor entry usage and feedback patterns
- Suggest improvements based on user interactions

When adding entries:
- Check for duplicates using semantic similarity
- Categorize accurately with appropriate tags
- Ensure content is clear, concise, and actionable
- Set appropriate approval workflow based on content type

Tone: Professional, helpful, accurate, and continuously improving.
```

### User Prompt Templates

#### Query Template
```
Task: Find relevant information from our knowledge base

Query: {query}

Context:
- Requesting Agent: {agent_name}
- Client ID: {client_id}
- Conversation ID: {conversation_id}
- Previous Context: {context}

Search Parameters:
- Category Filter: {category}
- Minimum Confidence: {min_confidence}
- Max Results: {top_k}

Please search the knowledge base and return the most relevant entries with confidence scores.
```

#### Entry Addition Template
```
Task: Add new knowledge base entry

Entry Details:
- Title: {title}
- Content: {content}
- Category: {category}
- Subcategory: {subcategory}
- Tags: {tags}
- Keywords: {keywords}

Source Information:
- Source: {source}
- Created By: {created_by}
- Requires Approval: {requires_approval}

Please create this knowledge base entry, checking for duplicates and ensuring proper categorization.
```

#### Feedback Processing Template
```
Task: Process feedback on knowledge base entry

Feedback Details:
- Entry ID: {entry_id}
- Query ID: {query_id}
- Was Helpful: {was_helpful}
- Rating: {rating}/5
- Feedback Text: {feedback_text}
- Suggested Improvement: {suggested_improvement}

Please update the entry's confidence score based on this feedback and identify any patterns that might indicate content issues.
```

## Error Handling Matrix

| Error Type | Detection | Response | Retry Strategy |
|------------|-----------|----------|----------------|
| Pinecone query timeout | Exception after 5s | Return cached results if < 1hr old | Yes, 2x with 1s backoff |
| Pinecone rate limit (429) | Status code | Queue request, notify if >10 queued | No, use queue |
| Embedding creation failure | Claude API error | Use fallback text search | Yes, 3x with exp backoff |
| Database connection lost | psycopg2.Error | Use read replica if available | Yes, 3x with 2s backoff |
| Invalid query format | Pydantic validation | Return error message | No |
| No results found | Empty Pinecone response | Suggest similar queries, create suggestion | No |
| Duplicate entry detected | Similarity > 0.9 | Return duplicates for review | No |
| Approval workflow failure | Slack/Teams error | Store in pending queue, retry notifications | Yes, 3x with 1hr backoff |
| Vector index full | Pinecone error | Archive oldest entries, create cleanup task | No |
| Content too long | Length validation | Suggest splitting into multiple entries | No |

### Recovery Strategies

1. **Pinecone Unavailable:**
   - Fall back to PostgreSQL full-text search
   - Cache recent queries for 1 hour
   - Notify operations team

2. **High Load:**
   - Implement request queuing for non-urgent queries
   - Use cached results for identical recent queries
   - Dynamically adjust top_k based on load

3. **Data Corruption:**
   - Daily integrity checks between Pinecone and PostgreSQL
   - Automatic re-indexing for mismatched entries
   - Version history for content rollback

## Multi-Agent Integration

### Handoff Patterns

1. **To Response Email Handler:**
   ```python
   await self.handoff_to(
       target_agent="response_email_handler",
       payload={
           "kb_results": query_results,
           "confidence": avg_confidence,
           "suggested_response": generated_response,
           "requires_approval": low_confidence
       },
       priority="normal"
   )
   ```

2. **From Any Agent:**
   - Standardized query interface via Celery task
   - Asynchronous response with callback URL
   - Context passing for personalization

### Integration Events

1. **Knowledge Updated:**
   - Publish event to all agents
   - Invalidate relevant caches
   - Update client-specific context

2. **New Entry Approved:**
   - Trigger re-indexing
   - Notify dependent agents
   - Update search index

## Testing Strategy

### Unit Tests

```python
class TestKnowledgeBaseAgent:
    @pytest.mark.asyncio
    async def test_query_with_high_confidence(self):
        """Verify high-confidence queries return accurate results"""

    @pytest.mark.asyncio
    async def test_query_fallback_to_text_search(self):
        """Verify fallback when Pinecone unavailable"""

    @pytest.mark.asyncio
    async def test_duplicate_detection(self):
        """Verify duplicate entry detection"""

    @pytest.mark.asyncio
    async def test_feedback_updates_confidence(self):
        """Verify feedback processing updates scores"""

    @pytest.mark.asyncio
    async def test_suggestion_workflow(self):
        """Verify suggestion creation and notification"""
```

### Integration Tests

```python
class TestKBIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_query_flow(self):
        """Full query from request to response"""

    @pytest.mark.asyncio
    async def test_agent_handoff_with_kb_context(self):
        """Verify context passing between agents"""

    @pytest.mark.asyncio
    async def test_approval_workflow(self):
        """Test human approval flow for new entries"""
```

### Performance Tests

- Load testing: 100 QPS sustained
- Latency: <500ms for 95th percentile
- Memory usage: <500MB for 10k entries
- Concurrent queries: Support 50 simultaneous

### Mocking Strategy

```python
@pytest.fixture
def mock_pinecone():
    with patch('pinecone.Index') as mock:
        mock.return_value.query.return_value = {
            'matches': [
                {'id': 'test-1', 'score': 0.95, 'metadata': {...}},
                {'id': 'test-2', 'score': 0.87, 'metadata': {...}}
            ]
        }
        yield mock

@pytest.fixture
def mock_claude():
    with patch('anthropic.Anthropic') as mock:
        mock.return_value.messages.create.return_value = {
            'content': [{'text': 'test embedding'}]
        }
        yield mock
```

## Performance

### Latency Requirements
- Simple queries: <200ms (95th percentile)
- Complex queries: <500ms (95th percentile)
- Entry updates: <1s
- Analytics queries: <5s

### Throughput Requirements
- Queries per minute: 60 sustained, 100 burst
- Entries per hour: 10 updates, 5 additions
- Concurrent users: 50 agents

### Caching Strategy
- Query results: 15-minute TTL for identical queries
- Popular entries: 1-hour TTL based on usage frequency
- Category listings: 30-minute TTL
- Analytics data: 5-minute cache

## Observability

### Metrics to Track
```python
# Query metrics
kb_queries_total = Counter('kb_queries_total', ['agent', 'category'])
kb_query_duration = Histogram('kb_query_duration_seconds')
kb_confidence_scores = Histogram('kb_confidence_scores')

# Entry metrics
kb_entries_total = Gauge('kb_entries_total', ['category', 'status'])
kb_entry_updates = Counter('kb_entry_updates_total')
kb_duplicates_detected = Counter('kb_duplicates_detected')

# Feedback metrics
kb_feedback_total = Counter('kb_feedback_total', ['helpful'])
kb_average_rating = Gauge('kb_average_rating')

# Performance metrics
kb_pinecone_errors = Counter('kb_pinecone_errors', ['error_type'])
kb_cache_hit_rate = Gauge('kb_cache_hit_rate')
```

### Logging Format
```python
logger.info(
    "KB query executed",
    extra={
        "query_id": query_id,
        "agent": agent_name,
        "query_length": len(query),
        "results_count": len(results),
        "top_confidence": top_score,
        "duration_ms": duration,
        "cache_hit": from_cache
    }
)
```

### Health Checks
- Pinecone connectivity: Every 30s
- Database connectivity: Every 30s
- Index freshness: Check every 5 minutes
- Queue depth: Monitor for backlogs

## Security

### Data Privacy
- PII detection in entries before indexing
- Client-specific content isolation
- RBAC for entry modification (agents vs humans)
- Audit trail for all changes

### Access Control
```python
class KBPermissions:
    # Read permissions
    all_agents_can_read = True
    client_specific_entries = True  # Only agents serving that client

    # Write permissions
    agent_suggestions = True  # Can suggest, needs approval
    human_editors = ["kb_manager", "sales_director", "tech_lead"]
    auto_approval_categories = ["faq", "process"]
```

### Input Sanitization
- Strip HTML from all content
- Limit markdown to safe subset
- Validate all links and remove malicious ones
- Sanitize user feedback before storage

## Acceptance Criteria

- [ ] Agent extends BaseAgent and implements required abstract methods
- [ ] All 5 tools implemented with proper input/output schemas
- [ ] Pinecone integration with fallback to PostgreSQL search
- [ ] Approval workflow for new entries with Slack/Teams notifications
- [ ] Feedback loop that updates confidence scores
- [ ] Duplicate detection with >90% similarity threshold
- [ ] Usage analytics with gap analysis
- [ ] Unit test coverage >90%
- [ ] Integration tests for all agent interactions
- [ ] Performance: <500ms latency for 95th percentile
- [ ] Error handling for all failure modes
- [ ] Comprehensive logging and metrics
- [ ] Security controls for data privacy
- [ ] Documentation for all APIs and tools

## Implementation Notes

1. **Vector Indexing:**
   - Use Claude's embedding API (1536 dimensions)
   - Batch embed entries to optimize API calls
   - Store metadata in Pinecone for filtering

2. **Search Optimization:**
   - Implement hybrid search (vector + keyword)
   - Use category filters to narrow search space
   - Cache frequent queries with TTL

3. **Learning Loop:**
   - Weekly confidence score recalculation
   - Monthly usage pattern analysis
   - Quarterly content review and archival

4. **Human Workflow:**
   - Daily digest of pending entries
   - Weekly report on low-performing entries
   - Monthly knowledge gap analysis
