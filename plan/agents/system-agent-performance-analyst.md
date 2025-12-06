# Agent Performance Analyst

## Category
System & Administration

## Purpose
Monitor, analyze, and optimize agent performance through comprehensive metrics and trend analysis

## Key Responsibilities
- Track performance metrics for all agents
- Identify performance trends and patterns
- Generate performance reports and insights
- Recommend improvements based on data
- Monitor agent learning velocity

## Process
1. **Metric Collection**
   - Gather performance data from all agent activities
   - Calculate success rates and efficiency metrics
   - Track quality scores and human feedback
   - Monitor resource utilization

2. **Performance Analysis**
   - Analyze trends over time
   - Compare agent performance
   - Identify top and bottom performers
   - Detect performance anomalies

3. **Reporting & Insights**
   - Generate daily/weekly/monthly reports
   - Create performance dashboards
   - Highlight improvement opportunities
   - Track learning progress

4. **Optimization**
   - Suggest prompt improvements
   - Recommend training areas
   - Identify automation opportunities
   - Monitor impact of changes

## Database Tables
- `agent_performance_analytics` - Main performance data
- `agent_metrics` - Real-time metrics
- `performance_trends` - Historical trend data
- `agent_benchmarks` - Performance standards

## Key Metrics
- Task completion rate
- Average response time
- Quality score (human-rated)
- Correction rate (need for human fixes)
- Learning velocity (improvement rate)
- Cost per task
- Customer satisfaction
- Business impact (leads, meetings, revenue)

## Triggers
- Agent task completion
- Human correction submitted
- Performance threshold breach
- Weekly report generation
- Monthly performance review

## Outputs
- Performance dashboards
- Trend analysis reports
- Agent ranking reports
- Improvement recommendations
- Learning progress tracking

## Integrations
- All agent systems (data collection)
- Task management systems
- Human feedback systems
- Analytics platforms
- Alerting systems

## Cron Schedule
- Every 5 minutes - Update real-time metrics
- Hourly - Calculate performance aggregates
- Daily - Generate daily reports
- Weekly - Trend analysis
- Monthly - Performance reviews

## Priority
Phase 1 - Critical for optimization

## Dependencies
- All agent systems
- Response tracking
- Human feedback collection
- Analytics infrastructure

## Human-in-the-Loop
- Review performance trends
- Approve major changes based on insights
- Validate improvement recommendations
- Set performance targets

## Performance Schema
```json
{
  "id": "uuid",
  "created_at": "2024-01-15T00:00:00Z",
  "agent_name": "cold_email_copywriter",
  "agent_type": "copywriting",
  "agent_version": "v2.3",
  "period_start": "2024-01-15T00:00:00Z",
  "period_end": "2024-01-15T23:59:59Z",
  "period_type": "day",
  "total_tasks": 150,
  "successful_tasks": 135,
  "failed_tasks": 15,
  "success_rate": 90.0,
  "avg_response_time_ms": 2100,
  "avg_task_completion_time_ms": 1500,
  "accuracy_score": 92.5,
  "quality_score": 4.3,
  "corrections_count": 12,
  "improvements_count": 3,
  "new_insights_count": 1,
  "learning_velocity": 0.8,
  "leads_generated": 45,
  "meetings_booked": 8,
  "conversion_rate": 5.3,
  "revenue_impact": 25000.00,
  "campaigns_worked_on": 3,
  "leads_handled": 150,
  "messages_sent": 150,
  "performance_breakdown": {
    "morning_performance": 95.0,
    "afternoon_performance": 87.0,
    "evening_performance": 89.0
  },
  "error_breakdown": {
    "personalization_errors": 5,
    "tone_mismatches": 4,
    "factual_errors": 2
  },
  "success_factors": {
    "recent_post_references": 0.3,
    "pain_point_alignment": 0.4,
    "value_prop_clarity": 0.3
  },
  "performance_trend": "improving",
  "trend_strength": 0.7,
  "status": "calculated"
}
```

## Performance Dashboard Queries
```sql
-- Agent performance ranking
SELECT
    agent_name,
    agent_type,
    AVG(success_rate) as avg_success_rate,
    AVG(quality_score) as avg_quality_score,
    AVG(corrections_count * 100.0 / NULLIF(total_tasks, 0)) as avg_correction_rate,
    AVG(learning_velocity) as avg_learning_velocity,
    SUM(revenue_impact) as total_revenue
FROM agent_performance_analytics
WHERE period_type = 'day'
    AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY agent_name, agent_type
ORDER BY avg_success_rate DESC, avg_quality_score DESC;

-- Performance trends over time
SELECT
    DATE_TRUNC('week', created_at) as week,
    AVG(success_rate) as avg_success_rate,
    AVG(quality_score) as avg_quality_score,
    COUNT(DISTINCT agent_name) as active_agents
FROM agent_performance_analytics
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY week
ORDER BY week;

-- Top performing agents by type
WITH agent_performance AS (
    SELECT
        agent_name,
        agent_type,
        AVG(success_rate) as success_rate,
        AVG(quality_score) as quality_score,
        ROW_NUMBER() OVER (PARTITION BY agent_type ORDER BY AVG(success_rate) DESC) as rank
    FROM agent_performance_analytics
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY agent_name, agent_type
)
SELECT
    agent_type,
    agent_name,
    success_rate,
    quality_score,
    rank as performance_rank
FROM agent_performance
WHERE rank <= 3
ORDER BY agent_type, rank;
```

## Learning Velocity Calculation
```python
def calculate_learning_velocity(agent_name: str, days: int = 30):
    """
    Calculate how quickly an agent is improving
    """
    # Get performance data
    recent = get_agent_performance(agent_name, days)
    older = get_agent_performance(agent_name, days*2, days)

    if not older or not recent:
        return 0

    # Calculate improvement rates
    success_improvement = (recent['avg_success_rate'] - older['avg_success_rate']) / older['avg_success_rate']
    quality_improvement = (recent['avg_quality_score'] - older['avg_quality_score']) / older['avg_quality_score']
    correction_improvement = (older['correction_rate'] - recent['correction_rate']) / older['correction_rate']

    # Weight improvements
    velocity = (
        success_improvement * 0.4 +
        quality_improvement * 0.4 +
        correction_improvement * 0.2
    )

    return round(velocity, 2)
```

## Performance Alerts
```python
async def check_performance_alerts():
    """
    Check for performance issues that need attention
    """
    alerts = []

    # Check agents with declining performance
    for agent in get_all_agents():
        current_score = get_current_performance_score(agent)
        previous_score = get_previous_performance_score(agent)

        if current_score < previous_score * 0.9:  # 10% decline
            alerts.append({
                'type': 'performance_decline',
                'agent': agent,
                'current_score': current_score,
                'previous_score': previous_score,
                'severity': 'high'
            })

    # Check high correction rates
    high_correction_agents = get_agents_with_high_correction_rate(threshold=0.2)
    for agent in high_correction_agents:
        alerts.append({
            'type': 'high_correction_rate',
            'agent': agent['name'],
            'rate': agent['correction_rate'],
            'severity': 'medium'
        })

    # Check learning velocity
    slow_learners = get_slow_learners(threshold=-0.05)
    for agent in slow_learners:
        alerts.append({
            'type': 'slow_learning',
            'agent': agent['name'],
            'velocity': agent['learning_velocity'],
            'severity': 'medium'
        })

    return alerts
```

## Performance Improvement Recommendations
```python
async def generate_improvement_recommendations(agent_name: str):
    """
    Generate specific recommendations based on agent performance
    """
    performance = get_agent_performance(agent_name, 30)
    recommendations = []

    # Analyze error patterns
    if performance['error_breakdown']['personalization_errors'] > 5:
        recommendations.append({
            'category': 'personalization',
            'issue': 'High rate of personalization errors',
            'recommendation': 'Review lead research data quality',
            'priority': 'high',
            'expected_impact': '20-30% improvement in reply rate'
        })

    # Analyze response time
    if performance['avg_response_time_ms'] > 5000:
        recommendations.append({
            'category': 'efficiency',
            'issue': 'Slow response generation',
            'recommendation': 'Optimize prompts and reduce token usage',
            'priority': 'medium',
            'expected_impact': '40% faster response time'
        })

    # Analyze success factors
    if performance['success_factors']['pain_point_alignment'] < 0.3:
        recommendations.append({
            'category': 'content_quality',
            'issue': 'Low pain point alignment',
            'recommendation': 'Improve research on prospect pain points',
            'priority': 'high',
            'expected_impact': '15-25% improvement in engagement'
        })

    return recommendations
```

## Benchmarking
```python
async def update_agent_benchmarks():
    """
    Update performance benchmarks based on top performers
    """
    # Get top 10% performers by agent type
    top_performers = get_top_performers(percentile=90)

    benchmarks = {}
    for agent_type in AGENT_TYPES:
        type_agents = [a for a in top_performers if a['type'] == agent_type]
        if type_agents:
            benchmarks[agent_type] = {
                'success_rate_min': min(a['success_rate'] for a in type_agents),
                'success_rate_avg': sum(a['success_rate'] for a in type_agents) / len(type_agents),
                'quality_score_min': min(a['quality_score'] for a in type_agents),
                'response_time_max': max(a['avg_response_time_ms'] for a in type_agents),
                'correction_rate_max': max(a['correction_rate'] for a in type_agents)
            }

    # Save benchmarks
    await save_benchmarks(benchmarks)
    return benchmarks
```

## API Endpoints
- `GET /api/agents/{name}/performance` - Agent performance
- `GET /api/agents/performance/leaderboard` - Performance ranking
- `GET /api/agents/performance/trends` - Trend analysis
- `GET /api/agents/performance/alerts` - Performance alerts
- `POST /api/agents/{name}/recommendations` - Get improvement recommendations
- `GET /api/agents/benchmarks` - Performance benchmarks
