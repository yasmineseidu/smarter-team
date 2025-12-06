# Meeting Prep Agent

## Category
Meeting Management

## Purpose
Prepare materials before calls using AI-powered insights and learning from previous sales calls

## Key Responsibilities
- Generate personalized meeting preparation materials
- Create call scripts optimized by sales performance data
- Provide talking points validated by successful conversion patterns
- Prepare objection responses based on proven effective techniques
- Generate tailored presentation slides
- Track prep effectiveness and feedback loops

## Process
1. **Data Collection & Analysis**
   - Pull lead and company research data
   - Retrieve conversation history and previous interactions
   - Analyze similar successful calls with comparable prospects
   - Extract best practices from Sales Call Analytics
   - Identify prospect-specific pain points and opportunities

2. **Script Generation with Learning**
   - Generate call scripts optimized by performance data
   - Incorporate proven opening techniques from top performers
   - Include value propositions that resonated with similar prospects
   - Prepare objection responses with high success rates
   - Customize questions based on industry-specific discovery patterns

3. **Presentation Creation**
   - Generate Gamma slides tailored to prospect's industry and needs
   - Include case studies from similar companies
   - Feature ROI calculations relevant to their specific challenges
   - Incorporate social proof from their industry or company size

4. **Prep Package Assembly**
   - Compile research, scripts, and presentation materials
   - Add real-time context (recent news, market trends)
   - Include competitor intelligence and positioning guidance
   - Provide alternative approaches based on prospect personality type

5. **Delivery & Tracking**
   - Deliver prep package via email/Slack
   - Log prep delivery and open rates
   - Track which materials were used during calls
   - Collect feedback on prep effectiveness
   - Feed usage data back into learning system

## Database Tables
- `meeting_prep` - Prep packages and delivery tracking
- `call_script_templates` - AI-generated scripts with success metrics
- `talking_points` - Validated talking points with performance data
- `objection_responses` - Proven objection handling techniques
- `prep_analytics` - Effectiveness tracking and optimization

## Key Metrics
- Prep package open rate
- Script adoption rate during calls
- Prep effectiveness score (based on call outcomes)
- Talking point usage and conversion correlation
- Objection response success rate
- Presentation engagement metrics
- Learning contribution to call success

## Triggers
- 1 hour before scheduled meeting
- Manual prep request
- New research data available
- Performance analytics update
- Prep feedback received

## Outputs
- AI-optimized call scripts with learning integration
- Research summaries with relevant insights
- Personalized talking points with success metrics
- Proven objection handling responses
- Tailored Gamma presentation slides
- Prep effectiveness analytics
- Continuous learning recommendations

## Integrations
- Gamma API (for slides)
- Email/Slack (for delivery)
- Claude API (for content generation)
- Sales Call Analytics (for performance data)
- Learning & Feedback System (for optimization)
- Lead/Company Research Agents (for data)

## Cron Schedule
- Every hour - Check for meetings in next hour needing prep
- Real-time - Process new performance analytics
- Weekly - Update script templates with latest learnings
- Monthly - Analyze prep effectiveness and optimize

## Priority
Phase 1 - Enhanced with learning capabilities

## Dependencies
- Lead Research Agent (provides lead data)
- Company Research Agent (provides company data)
- Sales Call Analytics Agent (provides performance insights)
- Learning & Feedback System (optimizes based on results)
- Conversation Intelligence (provides conversation summary)

## Human-in-the-Loop
- Prep package is informational, no approval needed
- User may request regeneration with different focus
- Feedback collection for continuous improvement
- Override options for critical meetings

## Meeting Prep Schema
```json
{
  "id": "uuid",
  "created_at": "2024-01-16T13:00:00Z",
  "meeting_id": "meeting_123",
  "prospect_id": "prospect_456",
  "sales_rep_id": "rep_sarah",
  "prep_type": "discovery_call",
  "prep_confidence": 0.89,

  "research_insights": {
    "lead_summary": {
      "name": "John Smith",
      "title": "CTO",
      "key_insights": [
        "Recently led $10M funding round",
        "Active in AI/ML community on LinkedIn",
        "Previously scaled engineering team at previous startup"
      ],
      "recent_activity": "Shared post about scaling challenges in SaaS",
      "personality_indicators": ["technical", "growth_focused", "data_driven"],
      "communication_style": "direct, prefers concise technical explanations"
    },

    "company_summary": {
      "name": "Acme Corp",
      "industry": "B2B SaaS",
      "size": "150-200 employees",
      "recent_news": "Announced expansion into European market",
      "tech_stack": ["React", "Node.js", "AWS", "PostgreSQL"],
      "growth_indicators": ["hiring", "product_launches", "funding"],
      "competitive_landscape": "Competing with established players with legacy systems"
    },

    "contextual_factors": {
      "market_trends": "Increasing demand for AI integration in their industry",
      "industry_challenges": ["data privacy compliance", "scalability issues", "integration complexity"],
      "opportunity_signals": ["recent funding", "market expansion", "hiring technical team"]
    }
  },

  "learning_integration": {
    "similar_successful_calls": [
      {
        "prospect": "TechCorp (similar industry, 180 employees)",
        "outcome": "closed deal ($85k)",
        "key_factors": ["focused on ROI", "addressed scalability concerns", "provided case study"],
        "conversion_rate": 0.85
      }
    ],
    "effective_opening_techniques": [
      {
        "technique": "Industry-specific challenge acknowledgment",
        "success_rate": 0.78,
        "example": "Many CTOs in B2B SaaS are struggling with AI integration - is that on your radar?"
      }
    ],
    "proven_value_propositions": [
      {
        "value_prop": "Reduce integration time by 60% with our pre-built connectors",
        "success_rate": 0.82,
        "context": "Companies with existing tech stack"
      }
    ]
  },

  "optimized_script": {
    "opening": {
      "technique": "research_backed_personalization",
      "script": "Hi John, congratulations on the recent funding round! I noticed your LinkedIn post about scaling SaaS platforms - that's exactly where we help companies like yours.",
      "confidence_score": 0.91,
      "alternative_approaches": [
        "Direct value proposition",
        "Industry challenge focus"
      ]
    },

    "discovery_questions": [
      {
        "question": "What's the biggest bottleneck in your current development workflow?",
        "category": "pain_discovery",
        "success_rate": 0.76,
        "expected_response_type": "technical_challenges"
      },
      {
        "question": "How are you currently handling AI/ML integration in your platform?",
        "category": "opportunity_assessment",
        "success_rate": 0.84,
        "follow_up_questions": ["What tools are you using?", "What limitations are you facing?"]
      }
    ],

    "key_talking_points": [
      {
        "point": "Pre-built AI connectors for React/Node.js stack",
        "success_metric": "0.85 positive response rate",
        "context": "Technical CTOs",
        "supporting_data": "Reduced implementation time from 3 months to 3 weeks for TechCorp"
      },
      {
        "point": "GDPR and SOC 2 compliance built-in",
        "success_metric": "0.79 concern resolution rate",
        "context": "Companies expanding to Europe",
        "supporting_evidence": "Certification documents available"
      }
    ]
  },

  "objection_preparation": {
    "predicted_objections": [
      {
        "objection": "We can build this internally",
        "probability": 0.73,
        "proven_response": {
          "approach": "total_cost_of_ownership",
          "script": "That's what TechCorp initially thought too. After 6 months and $200k in development costs, they found our solution was more cost-effective and already had enterprise-grade security.",
          "success_rate": 0.81
        },
        "alternative_responses": [
          "Focus on opportunity cost",
          "Highlight time-to-market advantage"
        ]
      }
    ]
  },

  "presentation_materials": {
    "gamma_slides": {
      "presentation_id": "gamma_deck_789",
      "slides_created": 8,
      "customization_level": "high",
      "key_slides": [
        "ROI calculator for their specific use case",
        "Case study from similar company",
        "Integration timeline for their tech stack"
      ]
    },
    "supporting_materials": [
      {
        "type": "case_study",
        "title": "TechCorp Integration Success",
        "relevance_score": 0.92
      },
      {
        "type": "technical_documentation",
        "title": "React Integration Guide",
        "relevance_score": 0.88
      }
    ]
  },

  "prep_delivery": {
    "delivery_method": "email_slack",
    "delivered_at": "2024-01-16T13:15:00Z",
    "opened_at": "2024-01-16T13:18:00Z",
    "materials_used": ["script", "slides", "case_study"],
    "feedback_collected": true,
    "effectiveness_score": 8.2
  },

  "learning_contribution": {
    "script_sections_used": ["opening", "discovery_questions"],
    "talking_points_effectiveness": {
      "pre_built_connectors": {"used": true, "reception": "positive"},
      "compliance_features": {"used": false, "reason": "objection didn't arise"}
    },
    "objection_preparation": {
      "predicted_accurately": true,
      "response_effectiveness": "high"
    }
  }
}
```

## AI-Enhanced Script Generation
```python
async def generate_optimized_script(prospect_data: dict, learning_data: dict):
    """
    Generate call script optimized by performance analytics
    """
    script_prompt = f"""
    Generate an optimized sales call script using these insights:

    Prospect Data:
    - Name: {prospect_data.get('name')}
    - Company: {prospect_data.get('company')}
    - Industry: {prospect_data.get('industry')}
    - Title: {prospect_data.get('title')}
    - Recent Activity: {prospect_data.get('recent_activity')}

    Learning from Similar Successful Calls:
    {format_learning_insights(learning_data)}

    Generate script sections:
    1. Opening (personalized + research-backed)
    2. Value Proposition (proven with similar prospects)
    3. Discovery Questions (high-impact patterns)
    4. Key Talking Points (validated by conversion data)
    5. Objection Preparation (predicted + proven responses)

    For each section, include:
    - Success rate from similar contexts
    - Alternative approaches
    - Confidence score
    - Supporting evidence

    Format as structured JSON with optimization metrics.
    """

    response = await anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": script_prompt
        }]
    )

    optimized_script = parse_script_response(response.content)
    validated_script = await validate_script_optimization(optimized_script, learning_data)

    return validated_script
```

## Learning Integration
```python
async def integrate_performance_learnings(prospect_profile: dict):
    """
    Extract relevant learnings from similar successful calls
    """
    # Find similar prospects based on industry, company size, role
    similar_prospects = await find_similar_prospects(prospect_profile)

    # Get performance analytics for these prospects
    successful_calls = await get_successful_calls_for_prospects(similar_prospects)

    # Extract patterns and best practices
    learnings = {
        "effective_openings": extract_top_opening_techniques(successful_calls),
        "successful_value_props": extract_converting_value_props(successful_calls),
        "high_impact_questions": extract_effective_discovery_questions(successful_calls),
        "proven_objection_handlers": extract_successful_objection_responses(successful_calls),
        "optimal_talking_points": extract_high_conversion_points(successful_calls),
        "contextual_factors": identify_success_contexts(successful_calls)
    }

    # Score relevance to current prospect
    scored_learnings = await score_learning_relevance(learnings, prospect_profile)

    return scored_learnings
```

## Prep Package Format
```
MEETING PREP: {{lead_name}} at {{company}}
Date: {{meeting_time}}
Duration: {{duration}} minutes
🤖 AI-Optimized with {{success_rate}}% similar-call success rate

---
⚡ AI-ENHANCED OPENING ({{opening_confidence}}% confidence)
{{optimized_opening}}
Alternative: {{alternative_opening}}

---
📊 RESEARCH SUMMARY
LEAD INSIGHTS:
- Role: {{job_title}} ({{communication_style}} communication style)
- Key insight: {{research_highlight}}
- Recent activity: {{recent_activity}}
- Personality indicators: {{personality_traits}}

COMPANY CONTEXT:
- Industry: {{industry}} ({{growth_stage}} stage)
- Size: {{employee_count}} employees
- Recent developments: {{key_updates}}
- Tech alignment: {{tech_compatibility}}% match

📈 SUCCESS PATTERNS FROM SIMILAR PROSPECTS:
{{similar_call_insights}}

---
🎯 OPTIMIZED TALKING POINTS (validated by {{conversion_data}} conversions)
1. {{point_1}} ✅ {{success_rate}}% success rate
   Supporting data: {{supporting_evidence}}

2. {{point_2}} ✅ {{success_rate}}% success rate
   Case study: {{relevant_case_study}}

3. {{point_3}} ✅ {{success_rate}}% success rate
   ROI calculation: {{specific_roi}}

---
❓ HIGH-IMPACT DISCOVERY QUESTIONS
1. {{question_1}} ({{engagement_rate}}% engagement rate)
   Follow-up: {{follow_up_probes}}

2. {{question_2}} ({{engagement_rate}}% engagement rate)
   Context: {{question_rationale}}

3. {{question_3}} ({{engagement_rate}}% engagement rate)
   Expected insights: {{expected_outcome}}

---
🛡️ OBJECTION PREPARATION (AI-predicted with {{prediction_accuracy}}% accuracy)
Most likely objection: "{{predicted_objection}}" ({{probability}}% probability)

✅ Proven response ({{response_success_rate}}% success rate):
{{optimized_response}}

Alternative approaches:
- {{alt_approach_1}}
- {{alt_approach_2}}

---
📊 PRESENTATION DECK
🔗 {{gamma_link}} ({{customization_level}}% customized for this prospect)

Key slides highlighted:
- {{key_slide_1}}
- {{key_slide_2}}
- {{key_slide_3}}

---
📈 PREPARATION METRICS
Prep effectiveness score: {{prep_score}}/10
Similar calls success rate: {{benchmark_rate}}%
Learning optimization level: {{learning_level}}%
```

## API Endpoints
- `POST /api/prep/generate` - Generate AI-optimized prep package
- `GET /api/prep/{meeting_id}` - Retrieve prep package
- `PUT /api/prep/{meeting_id}/feedback` - Submit prep feedback
- `GET /api/prep/analytics` - Prep effectiveness analytics
- `POST /api/prep/scripts/optimize` - Generate optimized script
- `GET /api/prep/learnings/{prospect_id}` - Get relevant learnings
