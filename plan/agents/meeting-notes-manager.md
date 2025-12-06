# Meeting Notes Manager

## Category
Meeting Management

## Purpose
Manage prospect communication notes and maintain comprehensive relationship history

## Key Responsibilities
- Generate structured meeting notes from transcripts and outcomes
- Add contextual notes to prospect records and CRM systems
- Track conversation history and key discussion points
- Maintain relationship memory across all touchpoints
- Provide quick reference for future interactions

## Process
1. **Note Generation**
   - Analyze meeting transcripts for key discussion points
   - Extract decisions, concerns, objections, and commitments
   - Summarize technical requirements and business needs
   - Identify emotional context and relationship indicators

2. **Note Structuring**
   - Organize notes by topic (business, technical, personal, objections)
   - Highlight action items and follow-up commitments
   - Tag notes with categories for easy retrieval
   - Link notes to specific prospects and opportunities

3. **CRM Integration**
   - Update prospect records with meeting notes
   - Sync with CRM systems (GoHighLevel, HubSpot)
   - Add tags and custom fields for advanced filtering
   - Maintain chronological conversation history

4. **Relationship Intelligence**
   - Track sentiment trends over time
   - Identify recurring themes and concerns
   - Monitor stakeholder engagement levels
   - Flag relationship health indicators

## Database Tables
- `meeting_notes` - Structured notes from meetings
- `prospect_communication_log` - Complete communication history
- `relationship_intelligence` - Sentiment and engagement tracking
- `note_templates` - Reusable note structures

## Key Metrics
- Note generation accuracy
- Information completeness score
- CRM sync success rate
- Note retrieval efficiency
- Relationship health indicators
- Cross-meeting continuity

## Triggers
- New transcript available from Fathom
- Meeting outcome recorded
- Manual note creation
- CRM update request
- Relationship health check

## Outputs
- Structured meeting notes
- Updated prospect records
- Communication history timeline
- Relationship health reports
- Conversation summaries

## Integrations
- Fathom Integration (transcripts)
- Meeting Lifecycle Orchestrator (context)
- CRM systems (GoHighLevel, HubSpot)
- Lead Database (prospect records)
- Communication platforms (email history)

## Cron Schedule
- Real-time - Process new transcripts
- Every hour - Sync notes to CRM
- Daily - Generate note summaries
- Weekly - Analyze relationship trends
- Monthly - Review note patterns

## Priority
Phase 1 - Essential for prospect relationship management

## Dependencies
- Fathom Integration Agent
- Meeting Lifecycle Orchestrator
- CRM integration setup
- Lead database

## Human-in-the-Loop
- Review sensitive notes before CRM sync
- Validate relationship health assessments
- Approve automatic note distribution
- Handle confidential information

## Meeting Notes Schema
```json
{
  "id": "uuid",
  "created_at": "2024-01-16T15:00:00Z",
  "updated_at": "2024-01-16T15:30:00Z",
  "meeting_id": "meeting_123",
  "prospect_id": "prospect_456",
  "transcript_id": "trans_789",
  "note_type": "structured_summary",
  "author": "system_generated",
  "confidence_score": 0.94,

  "meeting_context": {
    "title": "Technical Demo Follow-up",
    "date": "2024-01-16T14:00:00Z",
    "duration_minutes": 45,
    "attendees": [
      {
        "name": "John Smith",
        "role": "CTO",
        "company": "Acme Corp",
        "engagement_level": "high",
        "sentiment_score": 0.8
      }
    ],
    "meeting_type": "technical_demo",
    "outcome": "positive"
  },

  "structured_notes": {
    "business_discussion": {
      "key_points": [
        "Budget confirmed: $75k - $100k for initial implementation",
        "Timeline: Decision by end of Q1 2024",
        "Key stakeholders: John (CTO), Lisa (CFO), Mark (CEO)"
      ],
      "decisions_made": [
        "Technical feasibility confirmed",
        "Integration approach accepted",
        "Pilot program approved"
      ],
      "concerns_raised": [
        "Data migration complexity",
        "Training requirements for team",
        "Ongoing support costs"
      ],
      "commitments_offered": [
        "Dedicated implementation specialist",
        "3-month complimentary support",
        "Custom training sessions"
      ]
    },

    "technical_discussion": {
      "requirements": [
        "REST API integration with existing systems",
        "Single Sign-On (SSO) capability",
        "Custom reporting dashboard",
        "Data export functionality"
      ],
      "constraints": [
        "Must comply with SOC 2 standards",
        "99.9% uptime SLA required",
        "Max 2-week implementation timeline"
      ],
      "technical_objections": [
        "Concerns about API rate limits",
        "Questions about data encryption",
        "Compatibility with legacy systems"
      ],
      "solutions_presented": [
        "Enterprise API tier with custom limits",
        "End-to-end encryption documentation",
        "Legacy system integration modules"
      ]
    },

    "relationship_indicators": {
      "engagement_cues": [
        "Active participation throughout demo",
        "Asked detailed implementation questions",
        "Shared internal timeline constraints"
      ],
      "buying_signals": [
        "Discussed budget allocation",
        "Introduced to decision maker (CEO)",
        "Requested next steps timeline"
      ],
      "relationship_level": "trusted_advisor",
      "trust_score": 0.85,
      "urgency_level": "medium"
    },

    "action_items_summary": [
      {
        "item": "Send detailed implementation proposal",
        "owner": "Sales Team",
        "due_date": "2024-01-17T17:00:00Z",
        "priority": "high"
      },
      {
        "item": "Schedule technical deep-dive with engineering",
        "owner": "John Smith (CTO)",
        "due_date": "2024-01-18T10:00:00Z",
        "priority": "medium"
      }
    ]
  },

  "sentiment_analysis": {
    "overall_sentiment": "positive",
    "sentiment_score": 0.78,
    "emotional_indicators": {
      "excitement": 0.6,
      "concern": 0.3,
      "confidence": 0.8,
      "skepticism": 0.1
    },
    "sentiment_trend": "improving"
  },

  "crm_sync": {
    "sync_status": "completed",
    "synced_at": "2024-01-16T15:30:00Z",
    "crm_systems": ["gohighlevel", "hubspot"],
    "sync_errors": [],
    "record_updates": {
      "last_meeting_date": "2024-01-16T14:00:00Z",
      "relationship_stage": "technical_validation",
      "next_step": "proposal_review",
      "engagement_score": 85,
      "deal_probability": 0.75,
      "estimated_close_date": "2024-03-15T00:00:00Z"
    }
  },

  "tags": [
    "technical_demo",
    "budget_discussed",
    "implementation_planning",
    "stakeholder_identified",
    "positive_outcome",
    "next_step_proposal"
  ],

  "searchable_content": "Acme Corp technical demo John Smith CTO budget $75k-$100k timeline Q1 2024 REST API integration SSO SOC 2 compliance implementation proposal",
  "note_hash": "sha256:abc123def456..."
}
```

## Note Generation Logic
```python
async def generate_structured_notes(transcript: str, meeting_context: dict):
    """
    Generate structured notes from meeting transcript
    """
    note_generation_prompt = f"""
    Analyze this meeting transcript and create structured notes:

    Meeting Context:
    - Client: {meeting_context.get('prospect_name')}
    - Attendees: {meeting_context.get('attendees')}
    - Meeting Type: {meeting_context.get('meeting_type')}

    Transcript:
    {transcript}

    Generate structured notes with these sections:
    1. Business Discussion (key points, decisions, concerns, commitments)
    2. Technical Discussion (requirements, constraints, objections, solutions)
    3. Relationship Indicators (engagement cues, buying signals, trust level)
    4. Action Items Summary
    5. Sentiment Analysis (overall sentiment, emotional indicators)

    Format as structured JSON with detailed insights and quotes where relevant.
    """

    # Use Claude API for note generation
    response = await anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": note_generation_prompt
        }]
    )

    # Parse and validate structured notes
    structured_notes = parse_structured_notes(response.content)
    validated_notes = await validate_note_content(structured_notes, meeting_context)

    return validated_notes
```

## CRM Integration
```python
async def sync_notes_to_crm(prospect_id: str, notes: dict):
    """
    Sync meeting notes to CRM systems
    """
    crm_updates = []

    # GoHighLevel Integration
    if GHL_API_KEY:
        ghl_update = await update_gohighlevel_contact(
            prospect_id,
            {
                "notes": format_crm_notes(notes),
                "tags": notes.get('tags', []),
                "customField": {
                    "last_meeting_date": notes.get('meeting_context', {}).get('date'),
                    "relationship_stage": extract_relationship_stage(notes),
                    "engagement_score": calculate_engagement_score(notes),
                    "next_step": get_primary_action_item(notes),
                    "deal_probability": estimate_deal_probability(notes)
                }
            }
        )
        crm_updates.append({"system": "gohighlevel", "status": ghl_update})

    # HubSpot Integration
    if HUBSPOT_API_KEY:
        hubspot_update = await update_hubspot_contact(
            prospect_id,
            {
                "notes": format_crm_notes(notes),
                "properties": {
                    "last_meeting_date": notes.get('meeting_context', {}).get('date'),
                    "relationship_stage": extract_relationship_stage(notes),
                    "engagement_score": calculate_engagement_score(notes),
                    "next_step": get_primary_action_item(notes),
                    "deal_probability": estimate_deal_probability(notes),
                    "last_activity_date": datetime.utcnow().isoformat()
                }
            }
        )
        crm_updates.append({"system": "hubspot", "status": hubspot_update})

    return crm_updates
```

## Relationship Intelligence
```python
async def analyze_relationship_intelligence(prospect_id: str, all_notes: list):
    """
    Analyze relationship trends and health indicators
    """
    intelligence = {
        "prospect_id": prospect_id,
        "analysis_date": datetime.utcnow(),
        "relationship_trend": {},
        "engagement_patterns": {},
        "concern_themes": {},
        "relationship_health": {}
    }

    # Analyze sentiment trend over time
    sentiment_scores = [note.get('sentiment_analysis', {}).get('sentiment_score', 0)
                       for note in all_notes if note.get('sentiment_analysis')]

    if len(sentiment_scores) > 1:
        trend = calculate_trend(sentiment_scores)
        intelligence["relationship_trend"]["sentiment"] = {
            "current": sentiment_scores[-1],
            "previous": sentiment_scores[-2],
            "trend": trend,
            "direction": "improving" if trend > 0.05 else "declining" if trend < -0.05 else "stable"
        }

    # Analyze engagement patterns
    engagement_scores = [calculate_engagement_score(note) for note in all_notes]
    intelligence["engagement_patterns"] = {
        "average_engagement": sum(engagement_scores) / len(engagement_scores),
        "engagement_trend": calculate_trend(engagement_scores),
        "peak_engagement_topics": extract_peak_topics(all_notes)
    }

    # Identify recurring concerns
    concerns = []
    for note in all_notes:
        note_concerns = note.get('structured_notes', {}).get('business_discussion', {}).get('concerns_raised', [])
        concerns.extend(note_concerns)

    concern_counts = Counter(concerns)
    intelligence["concern_themes"] = {
        "top_concerns": concern_counts.most_common(5),
        "new_concerns": identify_new_concerns(all_notes),
        "resolved_concerns": identify_resolved_concerns(all_notes)
    }

    # Calculate relationship health score
    intelligence["relationship_health"] = {
        "health_score": calculate_relationship_health(intelligence),
        "health_factors": identify_health_factors(intelligence),
        "risk_indicators": detect_risk_indicators(all_notes)
    }

    return intelligence
```

## Conversation History
```python
async def build_conversation_timeline(prospect_id: str):
    """
    Build comprehensive conversation timeline for prospect
    """
    # Get all communication records
    communications = await get_all_communications(prospect_id)

    timeline = []
    for comm in communications:
        timeline_entry = {
            "date": comm["timestamp"],
            "type": comm["type"],
            "channel": comm["channel"],
            "summary": comm["summary"],
            "key_points": comm.get("key_points", []),
            "participants": comm.get("participants", []),
            "outcome": comm.get("outcome"),
            "next_steps": comm.get("next_steps", []),
            "sentiment": comm.get("sentiment_score"),
            "relationship_stage": comm.get("relationship_stage")
        }
        timeline.append(timeline_entry)

    # Sort by date and group into conversation threads
    timeline.sort(key=lambda x: x["date"])
    conversation_threads = group_conversation_threads(timeline)

    return {
        "prospect_id": prospect_id,
        "timeline": timeline,
        "conversation_threads": conversation_threads,
        "summary_statistics": {
            "total_touchpoints": len(timeline),
            "channels_used": list(set(t["channel"] for t in timeline)),
            "average_sentiment": sum(t["sentiment"] for t in timeline if t["sentiment"]) / len([t for t in timeline if t["sentiment"]]),
            "relationship_progression": extract_stage_progression(timeline)
        }
    }
```

## Note Templates
```python
NOTE_TEMPLATES = {
    "discovery_call": {
        "sections": ["business_discussion", "pain_points", "current_solutions", "budget_timeline", "decision_process"],
        "key_fields": ["industry", "company_size", "current_challenges", "competitors", "decision_makers"],
        "required_tags": ["discovery", "prospect_qualification"]
    },
    "technical_demo": {
        "sections": ["technical_discussion", "requirements", "objections", "solutions", "integration_needs"],
        "key_fields": ["technical_stack", "integration_points", "security_requirements", "scalability_needs"],
        "required_tags": ["technical_demo", "solution_validation"]
    },
    "proposal_review": {
        "sections": ["business_discussion", "proposal_feedback", "negotiation_points", "next_steps"],
        "key_fields": ["pricing_feedback", "contract_terms", "implementation_timeline", "stakeholder_approval"],
        "required_tags": ["proposal", "negotiation", "closing"]
    }
}

async def apply_note_template(meeting_type: str, notes: dict):
    """
    Apply structured template to notes based on meeting type
    """
    template = NOTE_TEMPLATES.get(meeting_type, NOTE_TEMPLATES["discovery_call"])

    # Ensure all required sections are present
    structured_notes = notes.get("structured_notes", {})

    for section in template["sections"]:
        if section not in structured_notes:
            structured_notes[section] = {}

    # Ensure all required tags are present
    current_tags = notes.get("tags", [])
    for tag in template["required_tags"]:
        if tag not in current_tags:
            current_tags.append(tag)

    # Extract and validate key fields
    extracted_fields = {}
    for field in template["key_fields"]:
        value = extract_field_from_notes(notes, field)
        if value:
            extracted_fields[field] = value

    return {
        **notes,
        "structured_notes": structured_notes,
        "tags": current_tags,
        "extracted_fields": extracted_fields,
        "template_applied": meeting_type
    }
```

## Analytics and Reporting
```sql
-- Note quality metrics
SELECT
    DATE(created_at) as date,
    COUNT(*) as notes_generated,
    AVG(confidence_score) as avg_confidence,
    AVG(LENGTH(searchable_content)) as avg_note_length,
    COUNT(DISTINCT prospect_id) as unique_prospects
FROM meeting_notes
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY date;

-- CRM sync performance
SELECT
    crm_system,
    COUNT(*) as sync_attempts,
    COUNT(CASE WHEN sync_status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as success_rate,
    AVG(EXTRACT(EPOCH FROM (synced_at - created_at))) as avg_sync_latency
FROM meeting_notes
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY crm_system;

-- Relationship health trends
SELECT
    prospect_id,
    relationship_health->>'health_score' as health_score,
    relationship_health->>'trend_direction' as trend,
    created_at
FROM relationship_intelligence
WHERE created_at >= NOW() - INTERVAL '30 days'
ORDER BY prospect_id, created_at;
```

## API Endpoints
- `POST /api/notes/generate` - Generate notes from transcript
- `GET /api/notes/{prospect_id}` - Get prospect notes
- `POST /api/notes/{prospect_id}/sync-crm` - Sync notes to CRM
- `GET /api/notes/timeline/{prospect_id}` - Get conversation timeline
- `GET /api/notes/intelligence/{prospect_id}` - Get relationship intelligence
- `POST /api/notes/manual` - Create manual notes
