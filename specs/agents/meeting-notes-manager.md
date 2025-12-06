# Meeting Notes Manager Agent - Production Specification

## Overview

**Agent Name:** `meeting_notes_manager`

**Category:** Meeting Management

**Purpose:** Automatically generate, organize, and manage comprehensive meeting documentation from transcripts, providing structured notes with searchable context, action items, key decisions, and relationship insights stored in Notion with full project linking.

**Priority:** Phase 2 - Intelligence Layer

**Dependencies:**
- Meeting Fathom Integration Agent (receives transcripts)
- Meeting Prep Agent (provides context for future meetings)
- Meeting Task Automation Agent (receives action items)
- Notion API integration
- Google Drive API integration
- Claude API (summarization and extraction)

---

## System Prompt

```
You are the Meeting Notes Manager for Smarter Team, an AI agency automation platform.

Your role is to transform meeting transcripts into comprehensive, actionable documentation that becomes the single source of truth for all meeting context.

CORE RESPONSIBILITIES:
1. Process meeting transcripts from Fathom and generate structured notes
2. Extract and categorize key decisions, action items, and commitments
3. Organize notes hierarchically in Notion by client, project, and meeting type
4. Create searchable note summaries for quick reference
5. Link notes to relevant projects, tasks, and client records
6. Provide semantic search across all meeting notes
7. Track follow-up items and their completion status

OUTPUT REQUIREMENTS:
- Notes must be comprehensive yet scannable (hierarchical structure with clear sections)
- Extract ALL action items with owners, due dates, and priority levels
- Identify ALL decisions made with context and stakeholders involved
- Summarize key discussion points by topic (business, technical, concerns, next steps)
- Tag notes with relevant keywords (project names, technologies, stakeholders, topics)
- Include relationship indicators (sentiment, engagement level, trust signals)
- Generate executive summary (3-5 bullet points) for quick reference

NOTE STRUCTURE:
1. **Meeting Metadata** - Date, attendees, duration, meeting type, outcome
2. **Executive Summary** - 3-5 key takeaways
3. **Key Decisions** - What was decided, by whom, rationale
4. **Action Items** - Who, what, when, priority
5. **Discussion Summary** - Main topics covered with context
6. **Technical Details** - Requirements, constraints, integrations discussed
7. **Concerns & Objections** - Issues raised and how they were addressed
8. **Next Steps** - Immediate follow-ups and long-term commitments
9. **Relationship Notes** - Sentiment, buying signals, trust indicators

TONE:
- Professional and precise
- Objective (capture facts, not opinions)
- Concise but complete (include all important context)
- Action-oriented (focus on outcomes and next steps)

ERROR HANDLING:
- If transcript is incomplete or low quality, flag sections needing human review
- If action item owner is unclear, mark as "[TO BE ASSIGNED]" and flag for review
- If meeting context is missing, pull from previous notes for the same client/project
- If Notion sync fails, store notes locally and retry with exponential backoff
- If semantic search indexing fails, log error but don't block note creation

TIMING:
- Process transcripts within 15 minutes of availability
- Sync to Notion within 5 minutes of processing
- Update search index within 10 minutes of note creation
- Send summary to meeting participants within 30 minutes of meeting end
```

---

## Agent Architecture

### Base Class
Extends `BaseAgent` from `src/agents/base_agent.py`

### File Structure
```
src/agents/meeting_notes_manager/
├── __init__.py              # Export MeetingNotesManagerAgent
├── agent.py                 # Main agent class
├── tools.py                 # Tool functions for note processing
├── prompts.py               # System prompt and extraction prompts
├── schemas.py               # Pydantic models for notes structure
├── exceptions.py            # Custom exceptions
└── templates.py             # Note template definitions by meeting type
```

---

## Tool Definitions

### 1. `create_meeting_notes`

**Purpose:** Generate structured notes from meeting transcript using Claude API

**Parameters:**
```python
@dataclass
class CreateMeetingNotesParams:
    meeting_id: str                    # UUID of meeting record
    transcript: str                    # Full meeting transcript from Fathom
    meeting_context: dict[str, Any]    # Metadata (attendees, date, type, duration)
    previous_notes: list[dict] | None = None  # Previous notes for context continuity
```

**Returns:**
```python
@dataclass
class MeetingNotes:
    meeting_id: str
    note_id: str                       # UUID
    created_at: str                    # ISO 8601 timestamp

    # Metadata
    meeting_date: str
    meeting_type: str                  # discovery, demo, check-in, closing, technical
    attendees: list[dict]              # [{name, role, company, email}]
    duration_minutes: int

    # Executive summary
    executive_summary: list[str]       # 3-5 key takeaways

    # Structured content
    key_decisions: list[dict]          # [{decision, rationale, stakeholders, timestamp}]
    action_items: list[dict]           # [{item, owner, due_date, priority, status}]
    discussion_summary: dict[str, list[str]]  # {topic: [points]}
    technical_details: dict            # {requirements, constraints, integrations}
    concerns_objections: list[dict]    # [{concern, raised_by, response, resolved}]
    next_steps: list[str]              # Immediate follow-ups

    # Relationship intelligence
    sentiment_score: float             # -1.0 to 1.0
    engagement_level: str              # low, medium, high
    buying_signals: list[str]
    trust_indicators: list[str]

    # Metadata
    tags: list[str]                    # Searchable keywords
    searchable_content: str            # Concatenated summary for search
    confidence_score: float            # 0.0 to 1.0 (Claude's confidence)
```

**Implementation:**
```python
async def create_meeting_notes(params: CreateMeetingNotesParams) -> MeetingNotes:
    """Generate structured notes using Claude API."""

    # Build context from previous notes if available
    context_summary = ""
    if params.previous_notes:
        context_summary = await summarize_previous_context(params.previous_notes)

    # Create extraction prompt
    extraction_prompt = f"""
    Analyze this meeting transcript and extract structured information.

    Meeting Context:
    - Type: {params.meeting_context.get('type')}
    - Date: {params.meeting_context.get('date')}
    - Attendees: {params.meeting_context.get('attendees')}
    - Duration: {params.meeting_context.get('duration')} minutes

    {f"Previous Meeting Context: {context_summary}" if context_summary else ""}

    Transcript:
    {params.transcript}

    Extract and return structured JSON with these sections:
    1. executive_summary (3-5 key takeaways as bullet points)
    2. key_decisions (list of decisions with decision, rationale, stakeholders)
    3. action_items (list with item, owner, due_date if mentioned, priority: high/medium/low)
    4. discussion_summary (object with topics as keys, discussion points as values)
    5. technical_details (requirements, constraints, integrations mentioned)
    6. concerns_objections (list with concern, raised_by, response, resolved: true/false)
    7. next_steps (list of immediate follow-up actions)
    8. sentiment_score (overall meeting sentiment from -1.0 to 1.0)
    9. engagement_level (low/medium/high based on participation)
    10. buying_signals (list of indicators of purchase intent)
    11. trust_indicators (list of relationship trust signals)
    12. tags (list of keywords: project names, technologies, stakeholders, topics)

    Be thorough and capture all important context. For action items, if owner or due date
    is unclear, mark as "[TO BE ASSIGNED]" or "[DATE TBD]".
    """

    # Call Claude API
    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[{"role": "user", "content": extraction_prompt}]
    )

    # Parse and validate structured notes
    extracted_data = parse_claude_response(response.content)

    # Create MeetingNotes object
    notes = MeetingNotes(
        meeting_id=params.meeting_id,
        note_id=str(uuid4()),
        created_at=datetime.utcnow().isoformat(),
        meeting_date=params.meeting_context['date'],
        meeting_type=params.meeting_context['type'],
        attendees=params.meeting_context['attendees'],
        duration_minutes=params.meeting_context['duration'],
        **extracted_data
    )

    # Generate searchable content
    notes.searchable_content = generate_searchable_content(notes)

    return notes
```

**Error Handling:**
- `TranscriptTooShortError`: Transcript <100 characters (likely incomplete)
- `ClaudeAPIError`: API call failed (retry with exponential backoff)
- `InvalidJSONError`: Claude response not valid JSON (retry once, then flag for human review)

---

### 2. `store_notes_notion`

**Purpose:** Save meeting notes to Notion with proper hierarchy and formatting

**Parameters:**
```python
@dataclass
class StoreNotesNotionParams:
    notes: MeetingNotes
    client_id: str                     # Link to client database
    project_id: str | None = None     # Link to project (if applicable)
    parent_page_id: str | None = None # Notion parent page (defaults to client page)
```

**Returns:**
```python
@dataclass
class NotionStorageResponse:
    notion_page_id: str                # Notion page ID
    notion_url: str                    # Public URL to Notion page
    parent_page_id: str
    created_at: str
    sync_status: str                   # "success" | "partial" | "failed"
    errors: list[str]                  # Any sync errors encountered
```

**Notion Page Structure:**
```markdown
# [Meeting Type] - [Client Name] - [Date]

## Executive Summary
- Key takeaway 1
- Key takeaway 2
- Key takeaway 3

## Attendees
- John Doe (CTO, Acme Corp)
- Sarah Smith (CEO, Acme Corp)

## Key Decisions
### Decision 1: [Title]
**Rationale:** ...
**Stakeholders:** John Doe, Sarah Smith
**Timestamp:** 14:23

## Action Items
- [ ] **[HIGH]** Send proposal by Dec 15 (@John)
- [ ] **[MEDIUM]** Schedule technical review (@Sarah)
- [ ] **[LOW]** Share case studies (@Team)

## Discussion Summary

### Business Requirements
- Point 1
- Point 2

### Technical Implementation
- Point 1
- Point 2

## Technical Details
**Requirements:**
- REST API integration
- SSO support

**Constraints:**
- 2-week implementation timeline
- SOC 2 compliance required

## Concerns & Objections
### Concern 1: Data security
**Raised by:** John Doe
**Response:** Provided SOC 2 certification details
**Status:** ✅ Resolved

## Next Steps
1. Send detailed proposal
2. Schedule technical deep-dive
3. Arrange intro to engineering team

## Relationship Intelligence
**Sentiment:** Positive (0.78)
**Engagement:** High
**Buying Signals:** Discussed budget, requested timeline, introduced decision makers
**Trust Indicators:** Shared internal constraints, asked for custom terms
```

**Implementation:**
```python
async def store_notes_notion(params: StoreNotesNotionParams) -> NotionStorageResponse:
    """Store meeting notes in Notion with proper formatting and linking."""

    # Build Notion page properties
    properties = {
        "Name": {"title": [{"text": {"content": f"{params.notes.meeting_type.title()} - {params.client_id} - {params.notes.meeting_date}"}}]},
        "Meeting Type": {"select": {"name": params.notes.meeting_type}},
        "Date": {"date": {"start": params.notes.meeting_date}},
        "Client": {"relation": [{"id": params.client_id}]},
        "Sentiment": {"number": params.notes.sentiment_score},
        "Engagement": {"select": {"name": params.notes.engagement_level}},
        "Tags": {"multi_select": [{"name": tag} for tag in params.notes.tags]}
    }

    if params.project_id:
        properties["Project"] = {"relation": [{"id": params.project_id}]}

    # Build page content blocks
    blocks = build_notion_blocks(params.notes)

    # Create Notion page
    try:
        response = await notion_client.pages.create(
            parent={"page_id": params.parent_page_id or params.client_id},
            properties=properties,
            children=blocks
        )

        return NotionStorageResponse(
            notion_page_id=response["id"],
            notion_url=response["url"],
            parent_page_id=params.parent_page_id or params.client_id,
            created_at=datetime.utcnow().isoformat(),
            sync_status="success",
            errors=[]
        )
    except NotionAPIError as e:
        # Retry with exponential backoff
        return await retry_notion_sync(params, e)
```

**Error Handling:**
- `NotionAPIError`: API call failed (retry 3 times with exponential backoff)
- `NotionAuthError`: Invalid API credentials (alert ops team)
- `NotionPageNotFoundError`: Parent page doesn't exist (create new parent)

---

### 3. `extract_key_decisions`

**Purpose:** Extract structured decision records from notes for tracking

**Parameters:**
```python
@dataclass
class ExtractKeyDecisionsParams:
    notes: MeetingNotes
    include_rationale: bool = True
    include_stakeholders: bool = True
```

**Returns:**
```python
@dataclass
class Decision:
    decision_id: str                   # UUID
    decision_text: str                 # What was decided
    rationale: str | None              # Why this decision was made
    stakeholders: list[str]            # Who was involved
    timestamp: str | None              # When in meeting (MM:SS format)
    impact_level: str                  # high, medium, low
    category: str                      # business, technical, process, financial

@dataclass
class ExtractKeyDecisionsResponse:
    decisions: list[Decision]
    total_count: int
```

**Implementation:**
```python
async def extract_key_decisions(params: ExtractKeyDecisionsParams) -> ExtractKeyDecisionsResponse:
    """Extract and structure decision records from meeting notes."""

    decisions = []
    for decision_data in params.notes.key_decisions:
        decision = Decision(
            decision_id=str(uuid4()),
            decision_text=decision_data["decision"],
            rationale=decision_data.get("rationale") if params.include_rationale else None,
            stakeholders=decision_data.get("stakeholders", []) if params.include_stakeholders else [],
            timestamp=decision_data.get("timestamp"),
            impact_level=classify_impact_level(decision_data["decision"]),
            category=classify_decision_category(decision_data["decision"])
        )
        decisions.append(decision)

    return ExtractKeyDecisionsResponse(
        decisions=decisions,
        total_count=len(decisions)
    )
```

---

### 4. `extract_action_items`

**Purpose:** Extract structured action items for task management integration

**Parameters:**
```python
@dataclass
class ExtractActionItemsParams:
    notes: MeetingNotes
    assign_to_meeting_owner: bool = True  # Auto-assign unassigned items to meeting owner
```

**Returns:**
```python
@dataclass
class ActionItem:
    action_id: str                     # UUID
    item_text: str                     # What needs to be done
    owner: str | None                  # Who is responsible
    due_date: str | None               # ISO 8601 date (if mentioned)
    priority: str                      # high, medium, low
    status: str                        # pending, in_progress, completed
    category: str                      # follow_up, deliverable, internal, external
    related_decision_id: str | None    # Link to decision if applicable

@dataclass
class ExtractActionItemsResponse:
    action_items: list[ActionItem]
    total_count: int
    unassigned_count: int
    high_priority_count: int
```

**Implementation:**
```python
async def extract_action_items(params: ExtractActionItemsParams) -> ExtractActionItemsResponse:
    """Extract and structure action items from meeting notes."""

    action_items = []
    unassigned_count = 0
    high_priority_count = 0

    for item_data in params.notes.action_items:
        owner = item_data.get("owner")

        # Auto-assign if requested and owner is missing
        if not owner and params.assign_to_meeting_owner:
            owner = get_meeting_owner(params.notes.meeting_id)

        if not owner or owner == "[TO BE ASSIGNED]":
            unassigned_count += 1

        priority = item_data.get("priority", "medium")
        if priority == "high":
            high_priority_count += 1

        action_item = ActionItem(
            action_id=str(uuid4()),
            item_text=item_data["item"],
            owner=owner,
            due_date=parse_due_date(item_data.get("due_date")),
            priority=priority,
            status="pending",
            category=classify_action_category(item_data["item"]),
            related_decision_id=find_related_decision(item_data["item"], params.notes.key_decisions)
        )
        action_items.append(action_item)

    return ExtractActionItemsResponse(
        action_items=action_items,
        total_count=len(action_items),
        unassigned_count=unassigned_count,
        high_priority_count=high_priority_count
    )
```

---

### 5. `link_to_project`

**Purpose:** Connect meeting notes to relevant project context in database

**Parameters:**
```python
@dataclass
class LinkToProjectParams:
    note_id: str                       # Meeting note UUID
    project_id: str | None = None      # Project UUID (auto-detect if None)
    link_type: str = "related"         # related, milestone, deliverable
```

**Returns:**
```python
@dataclass
class LinkToProjectResponse:
    link_id: str                       # UUID of link record
    note_id: str
    project_id: str
    link_type: str
    auto_detected: bool                # True if project was auto-detected
    confidence_score: float            # 0.0 to 1.0 for auto-detection
    created_at: str
```

**Implementation:**
```python
async def link_to_project(params: LinkToProjectParams) -> LinkToProjectResponse:
    """Link meeting notes to project records with auto-detection."""

    auto_detected = False
    confidence_score = 1.0
    project_id = params.project_id

    # Auto-detect project if not provided
    if not project_id:
        notes = await get_meeting_notes(params.note_id)
        project_id, confidence_score = await detect_project_from_notes(notes)
        auto_detected = True

    # Create link record
    link_id = str(uuid4())
    await db.execute(
        """
        INSERT INTO note_links (id, note_id, project_id, link_type, auto_detected, confidence_score, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """,
        link_id, params.note_id, project_id, params.link_type, auto_detected, confidence_score
    )

    return LinkToProjectResponse(
        link_id=link_id,
        note_id=params.note_id,
        project_id=project_id,
        link_type=params.link_type,
        auto_detected=auto_detected,
        confidence_score=confidence_score,
        created_at=datetime.utcnow().isoformat()
    )
```

---

### 6. `search_notes`

**Purpose:** Semantic search across all meeting notes using vector embeddings

**Parameters:**
```python
@dataclass
class SearchNotesParams:
    query: str                         # Natural language search query
    filters: dict[str, Any] | None = None  # {client_id, project_id, meeting_type, date_range}
    limit: int = 10                    # Max results to return
    include_summary: bool = True       # Include note summary in results
```

**Returns:**
```python
@dataclass
class SearchResult:
    note_id: str
    meeting_id: str
    relevance_score: float             # 0.0 to 1.0
    meeting_date: str
    meeting_type: str
    executive_summary: list[str] | None
    matching_sections: list[str]       # Sections that matched the query
    notion_url: str | None

@dataclass
class SearchNotesResponse:
    results: list[SearchResult]
    total_results: int
    query: str
    execution_time_ms: int
```

**Implementation:**
```python
async def search_notes(params: SearchNotesParams) -> SearchNotesResponse:
    """Perform semantic search across meeting notes using Pinecone."""

    start_time = time.time()

    # Generate query embedding using Claude/OpenAI
    query_embedding = await generate_embedding(params.query)

    # Build filters for vector search
    metadata_filter = {}
    if params.filters:
        if params.filters.get("client_id"):
            metadata_filter["client_id"] = params.filters["client_id"]
        if params.filters.get("project_id"):
            metadata_filter["project_id"] = params.filters["project_id"]
        if params.filters.get("meeting_type"):
            metadata_filter["meeting_type"] = params.filters["meeting_type"]

    # Query Pinecone vector database
    search_results = await pinecone_client.query(
        vector=query_embedding,
        filter=metadata_filter,
        top_k=params.limit,
        include_metadata=True
    )

    # Build response
    results = []
    for match in search_results["matches"]:
        result = SearchResult(
            note_id=match["id"],
            meeting_id=match["metadata"]["meeting_id"],
            relevance_score=match["score"],
            meeting_date=match["metadata"]["meeting_date"],
            meeting_type=match["metadata"]["meeting_type"],
            executive_summary=match["metadata"].get("executive_summary") if params.include_summary else None,
            matching_sections=match["metadata"].get("matching_sections", []),
            notion_url=match["metadata"].get("notion_url")
        )
        results.append(result)

    execution_time_ms = int((time.time() - start_time) * 1000)

    return SearchNotesResponse(
        results=results,
        total_results=len(results),
        query=params.query,
        execution_time_ms=execution_time_ms
    )
```

**Error Handling:**
- `PineconeAPIError`: Vector database error (fallback to keyword search)
- `EmbeddingGenerationError`: Embedding API failed (retry once)

---

## Database Schema

### Table: `meeting_notes`

Stores all meeting notes with structured content.

```sql
CREATE TABLE meeting_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Metadata
    meeting_date TIMESTAMPTZ NOT NULL,
    meeting_type VARCHAR(50) NOT NULL,  -- discovery, demo, check-in, closing, technical
    attendees JSONB NOT NULL,           -- Array of {name, role, company, email}
    duration_minutes INTEGER,

    -- Executive summary
    executive_summary JSONB NOT NULL,   -- Array of key takeaways

    -- Structured content
    key_decisions JSONB DEFAULT '[]'::jsonb,
    action_items JSONB DEFAULT '[]'::jsonb,
    discussion_summary JSONB DEFAULT '{}'::jsonb,
    technical_details JSONB DEFAULT '{}'::jsonb,
    concerns_objections JSONB DEFAULT '[]'::jsonb,
    next_steps JSONB DEFAULT '[]'::jsonb,

    -- Relationship intelligence
    sentiment_score FLOAT CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    engagement_level VARCHAR(20),       -- low, medium, high
    buying_signals JSONB DEFAULT '[]'::jsonb,
    trust_indicators JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,
    searchable_content TEXT NOT NULL,   -- For full-text search
    confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),

    -- Notion integration
    notion_page_id VARCHAR(255),
    notion_url TEXT,
    notion_sync_status VARCHAR(50) DEFAULT 'pending',  -- pending, synced, failed
    notion_sync_error TEXT,

    -- Indexes
    CONSTRAINT fk_meeting FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);

CREATE INDEX idx_meeting_notes_meeting_id ON meeting_notes(meeting_id);
CREATE INDEX idx_meeting_notes_meeting_date ON meeting_notes(meeting_date);
CREATE INDEX idx_meeting_notes_meeting_type ON meeting_notes(meeting_type);
CREATE INDEX idx_meeting_notes_tags ON meeting_notes USING GIN(tags);
CREATE INDEX idx_meeting_notes_searchable ON meeting_notes USING GIN(to_tsvector('english', searchable_content));
CREATE INDEX idx_meeting_notes_notion_page ON meeting_notes(notion_page_id);
```

### Table: `note_templates`

Stores customizable note templates by meeting type.

```sql
CREATE TABLE note_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) UNIQUE NOT NULL,
    meeting_type VARCHAR(50) NOT NULL,

    -- Template structure
    sections JSONB NOT NULL,            -- Array of section names and prompts
    required_fields JSONB DEFAULT '[]'::jsonb,
    optional_fields JSONB DEFAULT '[]'::jsonb,
    extraction_prompts JSONB DEFAULT '{}'::jsonb,  -- Custom prompts per section

    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255)
);

CREATE INDEX idx_note_templates_meeting_type ON note_templates(meeting_type);
CREATE INDEX idx_note_templates_default ON note_templates(is_default) WHERE is_default = TRUE;
```

### Table: `note_links`

Links meeting notes to projects, clients, and other entities.

```sql
CREATE TABLE note_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID NOT NULL REFERENCES meeting_notes(id) ON DELETE CASCADE,

    -- Link targets
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    related_note_id UUID REFERENCES meeting_notes(id) ON DELETE CASCADE,

    -- Link metadata
    link_type VARCHAR(50) NOT NULL,     -- related, milestone, deliverable, follow_up
    auto_detected BOOLEAN DEFAULT FALSE,
    confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_note_links_note_id ON note_links(note_id);
CREATE INDEX idx_note_links_project_id ON note_links(project_id);
CREATE INDEX idx_note_links_client_id ON note_links(client_id);
CREATE INDEX idx_note_links_type ON note_links(link_type);
```

---

## Note Template Structure

### Template Definitions by Meeting Type

```python
NOTE_TEMPLATES = {
    "discovery": {
        "sections": [
            "executive_summary",
            "business_context",
            "pain_points",
            "current_solutions",
            "requirements",
            "budget_timeline",
            "decision_process",
            "key_decisions",
            "action_items",
            "next_steps"
        ],
        "required_fields": [
            "company_name",
            "industry",
            "primary_contact",
            "main_pain_points"
        ],
        "extraction_prompts": {
            "pain_points": "Extract all pain points and challenges mentioned. Include specific examples and impact on business.",
            "budget_timeline": "Identify any budget ranges or timeline constraints mentioned. Note if tentative or confirmed.",
            "decision_process": "Extract information about decision makers, approval process, and timeline."
        }
    },

    "demo": {
        "sections": [
            "executive_summary",
            "features_demonstrated",
            "technical_discussion",
            "integration_requirements",
            "questions_asked",
            "concerns_objections",
            "key_decisions",
            "action_items",
            "next_steps"
        ],
        "required_fields": [
            "features_shown",
            "technical_requirements",
            "integration_needs"
        ],
        "extraction_prompts": {
            "features_demonstrated": "List all features shown during demo with client reactions and questions.",
            "technical_discussion": "Extract technical requirements, constraints, and integration points discussed.",
            "concerns_objections": "Capture all concerns, objections, or hesitations raised during demo."
        }
    },

    "check_in": {
        "sections": [
            "executive_summary",
            "project_status_update",
            "blockers_issues",
            "wins_progress",
            "upcoming_milestones",
            "client_feedback",
            "key_decisions",
            "action_items",
            "next_steps"
        ],
        "required_fields": [
            "project_status",
            "next_milestone"
        ],
        "extraction_prompts": {
            "project_status_update": "Summarize current project status, progress since last check-in, and overall health.",
            "blockers_issues": "Identify any blockers, issues, or risks mentioned. Include severity and proposed solutions.",
            "client_feedback": "Extract all client feedback - positive and negative - with specific examples."
        }
    },

    "technical": {
        "sections": [
            "executive_summary",
            "technical_requirements",
            "architecture_discussion",
            "integration_points",
            "security_compliance",
            "performance_scalability",
            "technical_decisions",
            "implementation_plan",
            "action_items",
            "next_steps"
        ],
        "required_fields": [
            "tech_stack",
            "integration_requirements",
            "technical_constraints"
        ],
        "extraction_prompts": {
            "technical_requirements": "Extract all technical requirements, specifications, and constraints discussed.",
            "architecture_discussion": "Summarize architecture decisions, design patterns, and technical approaches.",
            "security_compliance": "Identify security requirements, compliance needs (SOC 2, GDPR, etc.), and data handling."
        }
    },

    "closing": {
        "sections": [
            "executive_summary",
            "proposal_discussion",
            "pricing_terms",
            "contract_details",
            "implementation_timeline",
            "success_criteria",
            "concerns_resolved",
            "key_decisions",
            "action_items",
            "next_steps"
        ],
        "required_fields": [
            "pricing_agreed",
            "contract_terms",
            "start_date"
        ],
        "extraction_prompts": {
            "proposal_discussion": "Extract all proposal feedback, pricing discussions, and negotiation points.",
            "contract_details": "Capture contract terms, payment schedule, deliverables, and SLAs discussed.",
            "success_criteria": "Identify success metrics, KPIs, and expectations for project outcomes."
        }
    }
}
```

---

## Error Handling Strategy

### Error Categories

1. **Transcript Processing Errors**
   - **Incomplete Transcript**: Flag sections needing review, process available content
   - **Low Quality Audio**: Note confidence score, highlight uncertain sections
   - **Missing Context**: Pull previous notes for context continuity
   - **Multiple Speakers**: Use speaker diarization from Fathom

2. **Claude API Errors**
   - **Rate Limiting**: Exponential backoff with max 5 retries (2s, 4s, 8s, 16s, 32s)
   - **Invalid Response**: Retry once with simplified prompt, flag for human review if fails
   - **Token Limit**: Split transcript into chunks, process separately, merge results
   - **API Timeout**: Retry with lower token limit, log for monitoring

3. **Notion Sync Errors**
   - **Authentication Error**: Alert ops team immediately (don't retry)
   - **Rate Limit**: Queue sync request with exponential backoff
   - **Parent Page Not Found**: Create new parent page or escalate to human
   - **Network Error**: Retry 3 times, store locally if all fail
   - **Partial Sync**: Mark as "partial", log missing sections, retry missing parts

4. **Search Indexing Errors**
   - **Pinecone Error**: Log error, continue with note creation (async indexing)
   - **Embedding Generation Error**: Retry once, fallback to keyword indexing
   - **Duplicate Entry**: Update existing entry instead of creating new

### Escalation Rules

Escalate to human when:
- Transcript confidence score < 0.6 (low quality)
- Multiple critical action items without owners
- High-value client meeting (enterprise tier)
- Security/compliance discussions detected
- Contract negotiations or legal terms discussed
- Note creation fails after 3 retries

### Retry Logic

```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=32),
    retry=retry_if_exception_type((ClaudeAPIError, NotionAPIError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def process_with_retry(func, *args, **kwargs):
    """Generic retry wrapper for API calls."""
    return await func(*args, **kwargs)
```

---

## Process Flow

### Main Workflow

```python
async def process_task(task: dict[str, Any]) -> dict[str, Any]:
    """
    Process meeting transcript and generate comprehensive notes.

    Args:
        task: {
            "meeting_id": str,
            "transcript": str,
            "meeting_context": dict,
            "client_id": str,
            "project_id": str | None
        }

    Returns:
        {
            "note_id": str,
            "notion_url": str,
            "action_items_count": int,
            "decisions_count": int,
            "search_indexed": bool
        }
    """
    meeting_id = task["meeting_id"]
    transcript = task["transcript"]

    # Step 1: Fetch previous notes for context continuity
    previous_notes = await fetch_previous_notes(task["client_id"], limit=3)

    # Step 2: Generate structured notes using Claude
    notes = await create_meeting_notes(
        CreateMeetingNotesParams(
            meeting_id=meeting_id,
            transcript=transcript,
            meeting_context=task["meeting_context"],
            previous_notes=previous_notes
        )
    )

    # Step 3: Store notes in database
    note_id = await store_notes_in_database(notes)

    # Step 4: Extract structured data
    decisions_response = await extract_key_decisions(
        ExtractKeyDecisionsParams(notes=notes)
    )

    action_items_response = await extract_action_items(
        ExtractActionItemsParams(notes=notes, assign_to_meeting_owner=True)
    )

    # Step 5: Link to project (auto-detect or use provided)
    project_link = await link_to_project(
        LinkToProjectParams(
            note_id=note_id,
            project_id=task.get("project_id")
        )
    )

    # Step 6: Sync to Notion (async, non-blocking)
    notion_response = await store_notes_notion(
        StoreNotesNotionParams(
            notes=notes,
            client_id=task["client_id"],
            project_id=project_link.project_id
        )
    )

    # Step 7: Index for semantic search (async, non-blocking)
    search_indexed = await index_notes_for_search(notes, note_id)

    # Step 8: Send action items to task automation agent
    if action_items_response.action_items:
        await self.handoff_to(
            target_agent="meeting_task_automation",
            payload={
                "action_items": [asdict(item) for item in action_items_response.action_items],
                "meeting_id": meeting_id,
                "note_id": note_id
            },
            priority="high" if action_items_response.high_priority_count > 0 else "normal"
        )

    # Step 9: Send summary to participants
    await send_notes_summary(notes, notion_response.notion_url)

    # Step 10: Log completion
    self.log_action(
        "meeting_notes.created",
        {
            "note_id": note_id,
            "meeting_id": meeting_id,
            "action_items_count": action_items_response.total_count,
            "decisions_count": decisions_response.total_count,
            "notion_synced": notion_response.sync_status == "success",
            "search_indexed": search_indexed
        }
    )

    return {
        "note_id": note_id,
        "notion_url": notion_response.notion_url,
        "action_items_count": action_items_response.total_count,
        "decisions_count": decisions_response.total_count,
        "search_indexed": search_indexed
    }
```

---

## Testing Requirements

### Unit Tests (>90% coverage for tools)

**Test File:** `__tests__/unit/agents/test_meeting_notes_manager.py`

**Test Cases:**
1. `test_create_meeting_notes_success` - Full note generation from transcript
2. `test_create_meeting_notes_with_previous_context` - Context continuity
3. `test_create_meeting_notes_incomplete_transcript` - Handles short/incomplete transcript
4. `test_store_notes_notion_success` - Notion page creation
5. `test_store_notes_notion_retry` - Retry logic on API failure
6. `test_extract_key_decisions_complete` - All decision fields extracted
7. `test_extract_key_decisions_missing_stakeholders` - Handles missing data
8. `test_extract_action_items_with_auto_assign` - Auto-assigns unassigned items
9. `test_extract_action_items_priority_classification` - Correct priority levels
10. `test_link_to_project_auto_detect` - Auto-detects project from content
11. `test_link_to_project_explicit` - Uses provided project ID
12. `test_search_notes_semantic` - Semantic search with Pinecone
13. `test_search_notes_with_filters` - Filtered search by client/project
14. `test_template_application_discovery` - Discovery call template
15. `test_template_application_technical` - Technical meeting template

### Integration Tests (>85% coverage for agent)

**Test File:** `__tests__/integration/test_meeting_notes_manager.py`

**Test Cases:**
1. `test_full_notes_generation_flow` - End-to-end from transcript to Notion
2. `test_notes_with_real_claude_api` - Real Claude API call (mocked in CI)
3. `test_notion_sync_with_retry` - Notion sync with failure recovery
4. `test_search_indexing` - Pinecone indexing and search
5. `test_action_items_handoff` - Handoff to task automation agent
6. `test_multiple_meetings_context` - Context from previous meetings
7. `test_project_auto_detection` - Project linking from note content
8. `test_notes_summary_delivery` - Email/Slack summary to participants
9. `test_concurrent_note_processing` - Multiple transcripts processed simultaneously

### Fixtures

**File:** `__tests__/fixtures/meeting_notes_fixtures.py`

```python
@pytest.fixture
def sample_transcript():
    return """
    [00:00] Sarah (CEO): Thanks for joining, John. Let's discuss the API integration project.
    [00:15] John (CTO): Appreciate the time. We're excited about the possibilities.
    [00:30] Sarah: Our main goal is to automate our sales workflow. Currently everything is manual.
    [01:00] John: That makes sense. What's your current process?
    [01:15] Sarah: We have reps manually entering data from emails into Salesforce. Takes 2-3 hours daily.
    [02:00] John: We can definitely help with that. Our API can integrate directly with Salesforce.
    [02:30] Sarah: Perfect. What's the implementation timeline?
    [02:45] John: Typically 2 weeks for standard integrations. Would that work?
    [03:00] Sarah: Yes, that's ideal. Budget-wise, we're looking at $50k-$75k for initial implementation.
    [03:30] John: That's in the right range. Let me send a detailed proposal by Friday.
    [03:45] Sarah: Great. I'll need to get approval from our CFO Lisa, but I don't foresee issues.
    [04:00] John: Understood. Should we schedule a technical deep-dive with your engineering team?
    [04:15] Sarah: Yes, let's do that next week. I'll introduce you to our lead engineer Mark.
    [04:30] John: Perfect. I'll send calendar invites tomorrow.
    """

@pytest.fixture
def expected_notes_structure():
    return {
        "executive_summary": [
            "Client wants to automate manual sales workflow (currently 2-3 hours daily)",
            "Budget confirmed: $50k-$75k for initial implementation",
            "2-week implementation timeline agreed upon",
            "Next steps: Proposal by Friday, technical deep-dive next week"
        ],
        "key_decisions": [
            {
                "decision": "2-week implementation timeline",
                "rationale": "Meets client's timeline needs",
                "stakeholders": ["Sarah", "John"]
            }
        ],
        "action_items": [
            {
                "item": "Send detailed proposal",
                "owner": "John",
                "due_date": "Friday",
                "priority": "high"
            },
            {
                "item": "Schedule technical deep-dive",
                "owner": "John",
                "due_date": "Tomorrow",
                "priority": "medium"
            },
            {
                "item": "Introduce to lead engineer Mark",
                "owner": "Sarah",
                "due_date": "Next week",
                "priority": "medium"
            }
        ]
    }

@pytest.fixture
def mock_notion_client():
    """Mock Notion API client."""
    client = AsyncMock()
    client.pages.create.return_value = {
        "id": "notion-page-123",
        "url": "https://notion.so/workspace/page-123"
    }
    return client

@pytest.fixture
def mock_pinecone_client():
    """Mock Pinecone vector database client."""
    client = AsyncMock()
    client.query.return_value = {
        "matches": [
            {
                "id": "note-456",
                "score": 0.89,
                "metadata": {
                    "meeting_id": "meeting-789",
                    "meeting_date": "2025-12-10",
                    "meeting_type": "discovery",
                    "executive_summary": ["Key point 1", "Key point 2"]
                }
            }
        ]
    }
    return client
```

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Create agent directory structure
- [ ] Implement base agent class extending `BaseAgent`
- [ ] Define Pydantic schemas for all data structures
- [ ] Create note templates for all meeting types
- [ ] Implement database migrations (meeting_notes, note_templates, note_links)
- [ ] Write unit tests for schemas and templates

### Phase 2: Core Processing (Week 1-2)
- [ ] Implement `create_meeting_notes` tool with Claude API
- [ ] Implement `extract_key_decisions` tool
- [ ] Implement `extract_action_items` tool
- [ ] Add context continuity from previous notes
- [ ] Write unit tests for processing tools (>90% coverage)
- [ ] Test with sample transcripts

### Phase 3: Storage & Syncing (Week 2)
- [ ] Implement `store_notes_notion` tool
- [ ] Create Notion page builder with proper formatting
- [ ] Add retry logic for Notion API failures
- [ ] Implement database storage functions
- [ ] Write integration tests for Notion sync
- [ ] Test with real Notion workspace

### Phase 4: Linking & Search (Week 2-3)
- [ ] Implement `link_to_project` tool with auto-detection
- [ ] Implement `search_notes` tool with Pinecone
- [ ] Add embedding generation for search indexing
- [ ] Create search filters and ranking logic
- [ ] Write tests for linking and search
- [ ] Test semantic search accuracy

### Phase 5: Agent Integration (Week 3)
- [ ] Implement main `process_task` workflow
- [ ] Add handoff to meeting task automation agent
- [ ] Implement notes summary delivery
- [ ] Add error handling and retry logic
- [ ] Write end-to-end integration tests
- [ ] Test full workflow from transcript to Notion

### Phase 6: Quality & Optimization (Week 3-4)
- [ ] Run `make lint` and fix all issues
- [ ] Run `make typecheck` and fix all type errors
- [ ] Run `make test` and achieve >85% coverage
- [ ] Optimize Claude prompts for accuracy
- [ ] Add performance monitoring and logging
- [ ] Load test with multiple concurrent transcripts

### Phase 7: Documentation & Deployment (Week 4)
- [ ] Update CLAUDE.md with agent details
- [ ] Document environment variables
- [ ] Create runbook for common issues
- [ ] Write deployment guide
- [ ] Deploy to staging and test
- [ ] Deploy to production
- [ ] Monitor for 48 hours post-launch

---

## Success Metrics

**Processing Metrics:**
- **Note Generation Success Rate:** >98% (transcripts processed successfully)
- **Note Generation Time:** <3 minutes (from transcript to database)
- **Claude API Confidence:** >0.85 average confidence score
- **Extraction Accuracy:** >95% (action items and decisions correctly identified)

**Storage Metrics:**
- **Notion Sync Success Rate:** >99% (notes synced to Notion)
- **Notion Sync Time:** <2 minutes (from note creation to Notion page)
- **Database Storage Time:** <10 seconds

**Search Metrics:**
- **Search Response Time:** <500ms (p95)
- **Search Relevance:** >0.8 average relevance score
- **Index Update Time:** <1 minute (from note creation to searchable)

**Quality Metrics:**
- **Action Items Completeness:** >90% (all items captured from transcript)
- **Decision Tracking:** >95% (all decisions documented)
- **Context Continuity:** >85% (references to previous meetings maintained)
- **User Satisfaction:** >4.5/5 (measured via feedback surveys)

---

## Future Enhancements (Post-MVP)

1. **AI-Powered Summaries:** Generate different summary lengths (executive, detailed, technical)
2. **Multi-Language Support:** Process transcripts in languages beyond English
3. **Real-Time Notes:** Live note-taking during meetings (not just post-meeting)
4. **Smart Templates:** ML-based template recommendation based on meeting content
5. **Action Item Tracking:** Automatic status updates from task management integrations
6. **Meeting Insights Dashboard:** Analytics on meeting patterns, topics, sentiment trends
7. **Voice Notes:** Generate audio summaries via ElevenLabs
8. **PDF Export:** Export notes to PDF for offline access
9. **Custom Webhooks:** Trigger custom workflows on note creation
10. **Version Control:** Track note revisions and changes over time

---

## Security & Compliance

**Data Privacy:**
- Encrypt meeting transcripts at rest and in transit
- PII redaction option for sensitive client information
- GDPR/CCPA compliant data retention (90 days default, configurable)
- Secure Notion workspace access with role-based permissions

**Access Control:**
- Notes visible only to meeting participants and assigned team members
- Admin access for compliance and audit purposes
- API key rotation every 90 days
- Audit logging for all note access and modifications

**Compliance:**
- SOC 2 Type II requirements for data handling
- HIPAA compliance for healthcare clients (if applicable)
- Data residency options (US, EU, APAC)
- Right to deletion and data export

---

## Dependencies (Python Packages)

```toml
# Already installed
anthropic = ">=0.75.0"
httpx = ">=0.27.0"
pydantic = ">=2.12.5"

# New dependencies
notion-client = ">=2.2.1"       # Notion API integration
pinecone-client = ">=6.0.0"     # Vector search (already installed)
tenacity = ">=8.2.0"            # Retry logic with exponential backoff
python-dateutil = ">=2.8.2"     # Date parsing for action items
```

---

**Specification Version:** 1.0
**Created:** 2025-12-05
**Status:** Ready for Implementation
