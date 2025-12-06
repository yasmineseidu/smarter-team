# Sales Call Analytics Agent

## Category
Meeting Management

## Purpose
Analyze sales call performance and provide actionable improvement insights

## Key Responsibilities
- Analyze sales call transcripts for performance metrics
- Identify strengths and weaknesses in sales conversations
- Generate improvement recommendations for sales team
- Track skill development and performance trends
- Provide coaching insights and best practice identification

## Process
1. **Call Performance Analysis**
   - Evaluate opening effectiveness and rapport building
   - Assess needs discovery and questioning techniques
   - Analyze presentation clarity and value proposition delivery
   - Review objection handling and closing techniques
   - Measure talk-time ratios and participation balance

2. **Skill Assessment**
   - Score communication skills (clarity, empathy, confidence)
   - Evaluate product knowledge articulation
   - Assess listening skills and customer understanding
   - Measure problem-solution alignment effectiveness
   - Track closing and conversion techniques

3. **Comparative Analysis**
   - Compare performance against top performers
   - Analyze trends in successful vs unsuccessful calls
   - Identify patterns in high-conversion scenarios
   - Benchmark against team averages and best practices
   - Track individual performance improvement over time

4. **Improvement Generation**
   - Create personalized coaching recommendations
   - Generate specific skill development exercises
   - Suggest script optimizations based on analysis
   - Identify training opportunities and knowledge gaps
   - Provide best practice examples from successful calls

## Database Tables
- `call_performance_analytics` - Detailed call analysis data
- `sales_skill_metrics` - Individual skill scoring
- `call_comparisons` - Comparative analysis data
- `improvement_recommendations` - Generated coaching insights
- `best_practices_library` - Curated examples from top performers

## Key Metrics
- Opening effectiveness score
- Discovery quality rating
- Value proposition clarity score
- Objection handling success rate
- Talk-time ratio (ideal 40/60 sales/customer)
- Question-to-statement ratio
- Conversion rate by call type
- Skill improvement velocity
- Peer comparison ranking
- Customer engagement score

## Triggers
- New transcript available from Fathom
- Weekly performance report generation
- Monthly skill assessment
- Performance threshold breach
- Coaching request

## Outputs
- Detailed call performance reports
- Personalized improvement recommendations
- Skill development plans
- Best practice library updates
- Team performance dashboards
- Coaching session materials

## Integrations
- Fathom Integration (transcripts)
- Meeting Lifecycle Orchestrator (context)
- Learning & Feedback System (improvement tracking)
- Task Automation (coach task creation)
- Meeting Prep (script optimization)

## Cron Schedule
- Real-time - Process new call transcripts
- Daily - Generate individual call reports
- Weekly - Create team performance summaries
- Monthly - Generate skill development reports
- Quarterly - Update best practices library

## Priority
Phase 1 - Essential for sales team improvement

## Dependencies
- Fathom Integration Agent
- Meeting Notes Manager (context)
- Learning & Feedback System
- Sales performance data

## Human-in-the-Loop
- Review sensitive performance feedback
- Validate coaching recommendations
- Approve best practice examples
- Handle performance improvement plans

## Sales Call Analytics Schema
```json
{
  "id": "uuid",
  "created_at": "2024-01-16T16:00:00Z",
  "updated_at": "2024-01-16T16:30:00Z",
  "call_id": "call_123",
  "meeting_id": "meeting_456",
  "transcript_id": "trans_789",
  "sales_rep_id": "rep_sarah",
  "prospect_id": "prospect_acme",
  "call_type": "technical_demo",
  "call_outcome": "positive",
  "analysis_confidence": 0.91,

  "performance_scores": {
    "overall_score": 8.2,
    "opening_effectiveness": {
      "score": 8.5,
      "analysis": "Strong personal connection built through company research",
      "evidence": [
        "Referenced prospect's recent funding round",
        "Acknowledged industry challenges",
        "Set clear agenda for the call"
      ],
      "improvement_areas": [
        "Could be more concise in value proposition"
      ]
    },
    "discovery_quality": {
      "score": 7.8,
      "analysis": "Good questioning but missed some pain point depth",
      "evidence": [
        "Asked open-ended questions about challenges",
        "Identified key stakeholders",
        "Uncovered budget constraints"
      ],
      "improvement_areas": [
        "Deeper probing on technical pain points",
        "More exploration of competitive alternatives"
      ]
    },
    "presentation_clarity": {
      "score": 8.8,
      "analysis": "Excellent demo with relevant examples",
      "evidence": [
        "Tailored demo to prospect's use cases",
        "Clear explanation of value proposition",
        "Effective use of stories and examples"
      ],
      "improvement_areas": [
        "Could strengthen ROI justification"
      ]
    },
    "objection_handling": {
      "score": 7.5,
      "analysis": "Handled objections but could be more confident",
      "evidence": [
        "Addressed pricing concerns with value justification",
        "Acknowledged implementation challenges",
        "Provided references for similar cases"
      ],
      "improvement_areas": [
        "More pre-emptive objection handling",
        "Stronger confidence in responses"
      ]
    },
    "closing_effectiveness": {
      "score": 8.0,
      "analysis": "Clear next steps but weak ask for commitment",
      "evidence": [
        "Summarized key points effectively",
        "Outlined clear follow-up steps",
        "Identified decision timeline"
      ],
      "improvement_areas": [
        "More assertive closing statement",
        "Trial close techniques"
      ]
    }
  },

  "conversation_metrics": {
    "talk_time_analysis": {
      "sales_rep_talk_time_percentage": 42,
      "prospect_talk_time_percentage": 58,
      "ideal_ratio": 0.4,
      "assessment": "Good balance, slight over-talking in middle section"
    },
    "question_metrics": {
      "total_questions": 24,
      "open_ended_questions": 18,
      "closed_questions": 6,
      "question_to_statement_ratio": 0.35,
      "clarifying_questions": 8,
      "probing_questions": 12
    },
    "engagement_indicators": {
      "prospect_questions": 15,
      "prospect_interjections": 7,
      "positive_responses": 12,
      "concern_expressions": 4,
      "commitment_indicators": 6
    },
    "content_analysis": {
      "value_proposition_mentions": 8,
      "competitor_references": 3,
      "case_study_mentions": 2,
      "roi_discussions": 5,
      "technical_explanations": 10
    }
  },

  "skill_assessment": {
    "communication_skills": {
      "clarity": 8.5,
      "empathy": 7.8,
      "confidence": 7.2,
      "listening": 8.1,
      "storytelling": 8.3
    },
    "sales_techniques": {
      "rapport_building": 8.5,
      "needs_discovery": 7.8,
      "solution_presentation": 8.8,
      "objection_handling": 7.5,
      "closing": 8.0
    },
    "product_knowledge": {
      "feature_understanding": 9.2,
      "benefit_articulation": 8.5,
      "competitive_positioning": 7.8,
      "technical_accuracy": 8.9,
      "use_case_applications": 8.3
    }
  },

  "comparative_analysis": {
    "team_ranking": {
      "overall_performance_percentile": 78,
      "opening_effectiveness_percentile": 82,
      "discovery_quality_percentile": 71,
      "presentation_skills_percentile": 85,
      "objection_handling_percentile": 68,
      "closing_percentile": 74
    },
    "performance_vs_similar_calls": {
      "same_industry_average": 7.9,
      "same_call_type_average": 8.1,
      "same_prospect_stage_average": 7.7,
      "performance_comparison": "above_average"
    }
  },

  "improvement_recommendations": [
    {
      "category": "objection_handling",
      "priority": "high",
      "recommendation": "Develop stronger pre-emptive objection handling techniques",
      "specific_actions": [
        "Create objection handling matrix for common concerns",
        "Practice confident reframing techniques",
        "Study top performer responses to pricing objections"
      ],
      "expected_impact": "15-20% improvement in conversion rate",
      "implementation_effort": "medium",
      "training_resources": [
        "Objection handling workshop",
        "Role-playing sessions",
        "Top performer call recordings"
      ]
    },
    {
      "category": "closing_techniques",
      "priority": "medium",
      "recommendation": "Implement more assertive closing statements",
      "specific_actions": [
        "Add trial close questions throughout the call",
        "Create urgency through timeline discussion",
        "Use assumptive closing language"
      ],
      "expected_impact": "10-15% improvement in decision acceleration",
      "implementation_effort": "low"
    }
  ],

  "best_practice_identified": {
    "technique": "Industry-specific value proposition framing",
    "description": "Effectively framed solution benefits around prospect's specific industry challenges",
    "evidence": "Used manufacturing industry metrics and compliance requirements in value discussion",
    "replicability": "high",
    "training_value": "excellent"
  },

  "coaching_summary": {
    "strengths_to_reinforce": [
      "Excellent product knowledge and technical confidence",
      "Strong personalization based on prospect research",
      "Effective demonstration with relevant examples"
    ],
    "priority_improvements": [
      "Build confidence in objection handling responses",
      "Implement more assertive closing techniques",
      "Develop deeper discovery questioning skills"
    ],
    "development_focus": [
      "Advanced objection handling strategies",
      "Consultative selling techniques",
      "Value-based selling frameworks"
    ]
  }
}
```

## Performance Analysis Engine
```python
async def analyze_call_performance(transcript: str, call_context: dict):
    """
    Analyze sales call performance across multiple dimensions
    """
    analysis_prompt = f"""
    Analyze this sales call transcript for performance evaluation:

    Call Context:
    - Sales Rep: {call_context.get('sales_rep_name')}
    - Prospect: {call_context.get('prospect_name')}
    - Call Type: {call_context.get('call_type')}
    - Outcome: {call_context.get('outcome')}

    Transcript:
    {transcript}

    Evaluate performance on these dimensions (score 1-10):
    1. Opening Effectiveness (rapport, agenda setting, value prop)
    2. Discovery Quality (questioning, listening, need identification)
    3. Presentation Clarity (value articulation, demo effectiveness)
    4. Objection Handling (confidence, resolution, pre-emption)
    5. Closing Effectiveness (commitment, next steps, urgency)

    Also analyze:
    - Talk-time ratios and balance
    - Question patterns and types
    - Engagement indicators
    - Content analysis (value props, competitors, ROI)

    Provide specific evidence for scores and actionable improvement recommendations.
    Format as detailed JSON analysis.
    """

    response = await anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": analysis_prompt
        }]
    )

    # Parse and structure the analysis
    analysis_data = parse_performance_analysis(response.content)
    validated_analysis = await validate_analysis_scores(analysis_data, call_context)

    return validated_analysis
```

## Comparative Analytics
```python
async def generate_comparative_analysis(rep_id: str, call_analysis: dict):
    """
    Compare individual call performance against benchmarks
    """
    # Get team performance data
    team_stats = await get_team_performance_stats()
    similar_calls = await get_similar_call_performance(call_analysis)

    # Calculate percentiles
    percentiles = {}
    for metric in ['overall_score', 'opening_effectiveness', 'discovery_quality',
                   'presentation_clarity', 'objection_handling', 'closing_effectiveness']:
        score = call_analysis.get('performance_scores', {}).get(metric, {}).get('score', 0)
        percentile = calculate_percentile(score, team_stats[metric]['scores'])
        percentiles[f"{metric}_percentile"] = percentile

    # Compare to similar calls
    comparison_scores = {
        'same_industry_average': similar_calls.get('industry_average', 0),
        'same_call_type_average': similar_calls.get('call_type_average', 0),
        'same_prospect_stage_average': similar_calls.get('stage_average', 0)
    }

    # Determine performance category
    overall_score = call_analysis.get('performance_scores', {}).get('overall_score', 0)
    if overall_score >= 8.5:
        performance_category = "excellent"
    elif overall_score >= 7.5:
        performance_category = "good"
    elif overall_score >= 6.5:
        performance_category = "needs_improvement"
    else:
        performance_category = "requires_coaching"

    return {
        "team_ranking": percentiles,
        "performance_vs_similar_calls": comparison_scores,
        "performance_comparison": performance_category,
        "trend_analysis": await calculate_performance_trend(rep_id, call_analysis)
    }
```

## Improvement Recommendation Engine
```python
async def generate_improvement_recommendations(call_analysis: dict, rep_skills: dict):
    """
    Generate personalized improvement recommendations
    """
    recommendations = []

    # Analyze performance gaps
    performance_scores = call_analysis.get('performance_scores', {})

    for category, score_data in performance_scores.items():
        if isinstance(score_data, dict) and 'score' in score_data:
            score = score_data['score']

            if score < 7.0:  # Critical improvement area
                priority = "high"
                recommendation = await generate_critical_improvement(category, score_data)
            elif score < 8.0:  # Development area
                priority = "medium"
                recommendation = await generate_development_improvement(category, score_data)
            elif score < 9.0:  # Refinement area
                priority = "low"
                recommendation = await generate_refinement_improvement(category, score_data)
            else:
                # Strength to reinforce or best practice to capture
                best_practice = await identify_best_practice(category, score_data)
                if best_practice:
                    return {
                        "category": "best_practice",
                        "technique": best_practice['technique'],
                        "description": best_practice['description'],
                        "replicability": best_practice['replicability'],
                        "training_value": best_practice['training_value']
                    }
                continue

            if recommendation:
                recommendation['priority'] = priority
                recommendation['category'] = category
                recommendations.append(recommendation)

    # Add skill-specific recommendations based on assessment
    skill_gaps = await analyze_skill_gaps(call_analysis, rep_skills)
    for gap in skill_gaps:
        skill_rec = await generate_skill_development_plan(gap)
        recommendations.append(skill_rec)

    # Prioritize by impact and effort
    prioritized_recommendations = prioritize_recommendations(recommendations)

    return prioritized_recommendations[:5]  # Return top 5 recommendations
```

## Performance Tracking
```python
async def track_performance_trends(rep_id: str, days: int = 90):
    """
    Track individual performance trends over time
    """
    # Get historical call data
    historical_calls = await get_rep_call_history(rep_id, days)

    if len(historical_calls) < 5:
        return {"status": "insufficient_data", "minimum_calls_needed": 5}

    # Calculate trends for each metric
    trends = {}
    for metric in ['overall_score', 'opening_effectiveness', 'discovery_quality',
                   'presentation_clarity', 'objection_handling', 'closing_effectiveness']:

        scores = [call.get('performance_scores', {}).get(metric, {}).get('score', 0)
                  for call in historical_calls]

        if len(scores) >= 3:
            # Calculate linear regression trend
            trend_line = calculate_trend_line(scores)
            improvement_rate = calculate_improvement_rate(scores)

            trends[metric] = {
                "trend_direction": "improving" if improvement_rate > 0.05 else "declining" if improvement_rate < -0.05 else "stable",
                "improvement_rate": improvement_rate,
                "current_average": sum(scores[-10:]) / min(len(scores), 10),
                "previous_average": sum(scores[-20:-10]) / min(len(scores[-20:-10]), 10),
                "trend_strength": abs(improvement_rate),
                "forecast_next_period": trend_line[-1] + improvement_rate
            }

    # Identify skill development areas
    development_areas = []
    for metric, trend_data in trends.items():
        if trend_data['trend_direction'] == 'declining' or trend_data['current_average'] < 7.0:
            development_areas.append({
                "skill": metric,
                "current_level": trend_data['current_average'],
                "trend": trend_data['trend_direction'],
                "priority": "high" if trend_data['current_average'] < 6.5 else "medium"
            })

    return {
        "rep_id": rep_id,
        "analysis_period_days": days,
        "total_calls_analyzed": len(historical_calls),
        "performance_trends": trends,
        "development_areas": development_areas,
        "skill_velocity": calculate_skill_velocity(trends),
        "improvement_momentum": calculate_improvement_momentum(trends)
    }
```

## Best Practices Library
```python
async def extract_best_practices(call_analysis: dict):
    """
    Identify and extract best practices from high-performing calls
    """
    best_practices = []

    # Check for exceptional performance
    performance_scores = call_analysis.get('performance_scores', {})

    for category, score_data in performance_scores.items():
        if isinstance(score_data, dict) and score_data.get('score', 0) >= 9.0:
            # Extract best practice from this category
            practice = await analyze_best_practice(category, score_data, call_analysis)
            if practice:
                best_practices.append(practice)

    # Look for effective techniques across all categories
    techniques = await identify_effective_techniques(call_analysis)
    for technique in techniques:
        if technique['effectiveness_score'] >= 8.5:
            best_practices.append({
                "technique": technique['name'],
                "description": technique['description'],
                "evidence": technique['evidence'],
                "replicability": technique['replicability'],
                "training_value": technique['training_value'],
                "context": technique['context']
            })

    return best_practices

async def update_best_practices_library(new_practices: list):
    """
    Update the library with identified best practices
    """
    for practice in new_practices:
        # Check if similar practice exists
        existing = await find_similar_best_practice(practice)

        if existing:
            # Update existing practice with new evidence
            await update_best_practice(existing['id'], {
                "additional_evidence": practice.get('evidence', []),
                "effectiveness_score": calculate_new_effectiveness(existing, practice),
                "usage_count": existing['usage_count'] + 1
            })
        else:
            # Add new best practice
            practice_id = await create_best_practice({
                "technique": practice['technique'],
                "description": practice['description'],
                "evidence": [practice.get('evidence', [])],
                "replicability": practice['replicability'],
                "training_value": practice['training_value'],
                "context": practice['context'],
                "usage_count": 1,
                "created_at": datetime.utcnow(),
                "effectiveness_score": 8.5
            })

            # Create training material suggestions
            await generate_training_suggestions(practice_id, practice)
```

## Analytics Dashboard
```sql
-- Team performance overview
SELECT
    sales_rep_id,
    COUNT(*) as total_calls,
    AVG(performance_scores->>'overall_score') as avg_performance,
    COUNT(CASE WHEN call_outcome = 'positive' THEN 1 END) * 100.0 / COUNT(*) as conversion_rate,
    AVG(conversation_metrics->'talk_time_analysis'->>'sales_rep_talk_time_percentage') as avg_talk_time,
    AVG(skill_assessment->'sales_techniques'->>'objection_handling') as avg_objection_handling
FROM call_performance_analytics
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY sales_rep_id
ORDER BY avg_performance DESC;

-- Skill development tracking
SELECT
    skill_category,
    DATE_TRUNC('week', created_at) as week,
    AVG(score) as average_score,
    COUNT(*) as call_count,
    STDDEV(score) as score_variance
FROM (
    SELECT
        created_at,
        'opening' as skill_category,
        (performance_scores->'opening_effectiveness'->>'score')::numeric as score
    FROM call_performance_analytics
    UNION ALL
    SELECT
        created_at,
        'discovery' as skill_category,
        (performance_scores->'discovery_quality'->>'score')::numeric as score
    FROM call_performance_analytics
) skill_scores
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY skill_category, week
ORDER BY skill_category, week;

-- Improvement effectiveness tracking
SELECT
    improvement_category,
    COUNT(*) as recommendations_made,
    COUNT(CASE WHEN status = 'implemented' THEN 1 END) as implemented,
    COUNT(CASE WHEN status = 'implemented' THEN 1 END) * 100.0 / COUNT(*) as implementation_rate,
    AVG(performance_improvement) as avg_improvement
FROM improvement_recommendations
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY improvement_category;
```

## API Endpoints
- `POST /api/analytics/call` - Analyze single call performance
- `GET /api/analytics/performance/{rep_id}` - Get rep performance trends
- `GET /api/analytics/team-performance` - Get team analytics dashboard
- `POST /api/analytics/best-practices` - Submit best practice
- `GET /api/analytics/improvements/{rep_id}` - Get improvement recommendations
- `GET /api/analytics/coaching-report/{rep_id}` - Generate coaching report
