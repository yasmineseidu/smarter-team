# Learning & Feedback Agent

## Category
System & Administration

## Purpose
Improve system from human corrections

## Learning Sources
- Email response corrections
- Personalization edits
- Proposal modifications
- Send Agent feedback
- Copy performance data

## Process
1. **Collect Learning Data**
   - Gather human corrections from all agent systems
   - Track response outcomes via response_tracking
   - Collect FAQ feedback and usage patterns
   - Monitor performance metrics from agent_performance_analytics

2. **Analyze Patterns**
   - Identify recurring correction types
   - Detect performance trends and anomalies
   - Analyze successful response patterns
   - Map learning to specific agents/types

3. **Generate Insights**
   - Create knowledge base articles from learnings
   - Update FAQ with new questions/answers
   - Suggest prompt and template improvements
   - Identify training opportunities

4. **Implement Improvements**
   - Coordinate with correction_approval_workflow
   - Update agent configurations
   - Create A/B tests for improvements
   - Document best practices

5. **Track Impact**
   - Monitor post-change performance
   - Calculate ROI of improvements
   - Update learning effectiveness metrics
   - Feed results back into learning loop

## Database Tables
- `agent_learning` - Track all learning events and improvements
- `response_tracking` - Monitor response outcomes for learning
- `knowledge_base` - Central repository of learned knowledge
- `faq_management` - Dynamic FAQ that evolves from interactions
- `agent_performance_analytics` - Performance metrics and trends
- `correction_approval_workflow` - Approval workflow for changes

## Integrations
- All agents with human-in-the-loop
- Prompt management system
- Template versioning

## Priority
Phase 7 - Polish & Scale

## Dependencies
- All agents that receive human corrections

## Human-in-the-Loop
- Improvement suggestions reviewed before implementation
- Prompt/template changes require approval

## Agent Learning Schema
```json
{
  "id": "uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:45:00Z",
  "agent_name": "response_handler",
  "agent_type": "communication",
  "agent_version": "v2.1",
  "event_type": "correction",
  "event_category": "tone_adjustment",
  "original_action": "Generated overly enthusiastic response",
  "original_context": {
    "lead_industry": "finance",
    "lead_stage": "initial_response",
    "conversation_tone": "professional"
  },
  "original_parameters": {
    "temperature": 0.7,
    "max_tokens": 150
  },
  "original_outcome": {
    "sentiment": "negative",
    "reply_rate": 0.05
  },
  "corrected_action": "Adjusted tone to be more measured",
  "correction_reason": "too_enthusiastic for professional audience",
  "correction_source": "human_feedback",
  "lesson_learned": "Enterprise prospects prefer measured, professional tone",
  "confidence_level": 0.92,
  "applicability_score": 0.85,
  "impact_potential": 0.7,
  "pattern_detected": true,
  "pattern_description": "Tone mismatches by industry",
  "similar_cases": ["learn_001", "learn_003"],
  "implemented_at": "2024-01-15T11:00:00Z",
  "implementation_method": "prompt_update",
  "implementation_status": "validated",
  "validated": true,
  "validation_method": "a_b_test",
  "validation_results": {
    "reply_rate_improvement": 0.08,
    "sentiment_improvement": 0.3
  },
  "validated_at": "2024-01-15T13:00:00Z",
  "validated_by": "marketing_lead",
  "baseline_performance": 0.65,
  "improved_performance": 0.73,
  "performance_change": 0.08,
  "measurement_period": "1_week",
  "kb_article_id": "kb_tone_enterprise_01",
  "rule_created": true,
  "rule_description": "Adjust tone based on industry",
  "metadata": {},
  "tags": ["tone", "enterprise", "professional"],
  "sources": ["human_feedback", "performance_data"],
  "status": "integrated"
}
```

## Correction Categories

### Tone Corrections
```
too_formal → more_casual
too_casual → more_formal
too_enthusiastic → more_measured
too_generic → more_specific
too_long → more_concise
too_salesy → more_helpful
```

### Content Corrections
```
factually_incorrect → corrected_facts
missing_information → added_info
irrelevant_content → removed_content
wrong_context → corrected_context
hallucination → removed_hallucination
```

### Structural Corrections
```
wrong_format → correct_format
missing_cta → added_cta
wrong_signoff → correct_signoff
missing_personalization → added_personalization
```

## Pattern Analysis
```python
async def analyze_corrections(period_days: int = 30):
    corrections = await get_corrections(period_days)

    patterns = {
        "by_agent": {},
        "by_type": {},
        "by_context": {}
    }

    for c in corrections:
        # Count by agent
        patterns["by_agent"][c.agent_name] = \
            patterns["by_agent"].get(c.agent_name, 0) + 1

        # Count by correction type
        patterns["by_type"][c.correction_type] = \
            patterns["by_type"].get(c.correction_type, 0) + 1

        # Count by context (e.g., industry)
        if c.context.get("industry"):
            key = f"{c.agent_name}:{c.context['industry']}"
            patterns["by_context"][key] = \
                patterns["by_context"].get(key, 0) + 1

    return patterns
```

## Improvement Suggestions

### Prompt Updates
```
When pattern detected (>5 corrections of same type):

1. Analyze original prompt
2. Identify cause of errors
3. Generate suggested prompt update
4. Test on historical data
5. Submit for approval
```

### Template Updates
```
When template consistently corrected:

1. Identify problematic sections
2. Generate improved version
3. A/B test against original
4. Promote winner after validation
```

### Few-Shot Examples
```
When specific context causes errors:

1. Collect corrected examples
2. Add to few-shot prompt
3. Test improvement
4. Update production prompt
```

## Weekly Learning Report
```
📚 WEEKLY LEARNING REPORT - {{date_range}}

CORRECTIONS RECEIVED
- Total: {{total_corrections}}
- By agent: {{agent_breakdown}}
- By type: {{type_breakdown}}

TOP PATTERNS
1. {{pattern_1}}: {{count_1}} occurrences
   Suggested action: {{action_1}}

2. {{pattern_2}}: {{count_2}} occurrences
   Suggested action: {{action_2}}

IMPROVEMENTS MADE
- Prompts updated: {{prompts_updated}}
- Templates updated: {{templates_updated}}
- Few-shot examples added: {{examples_added}}

IMPROVEMENT METRICS
- Correction rate this week: {{rate}}%
- vs last week: {{change}}%
- Agent accuracy trend: {{trend}}
```

## Improvement Metrics
```sql
-- Correction rate by agent
SELECT
    agent_name,
    COUNT(*) as corrections,
    (SELECT COUNT(*) FROM agent_outputs
     WHERE agent_name = c.agent_name
     AND created_at >= NOW() - INTERVAL '7 days') as total_outputs,
    COUNT(*) * 100.0 / NULLIF(total_outputs, 0) as correction_rate
FROM correction_logs c
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY agent_name;

-- Improvement over time
SELECT
    DATE_TRUNC('week', created_at) as week,
    agent_name,
    COUNT(*) as corrections
FROM correction_logs
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY week, agent_name
ORDER BY week;
```

## Cron Schedule
- Daily - Process new corrections
- Weekly - Generate learning report
- Monthly on 15th at 10:00 AM - Analyze correction patterns for improvements
