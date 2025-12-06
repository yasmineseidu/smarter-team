# System Agent Performance Analyst Agent - Production Specification

## Overview

**Category**: System & Administration
**Priority**: Phase 1 - Critical for optimization
**Agent Name**: `system_agent_performance_analyst`
**Purpose**: Monitor, analyze, and benchmark all 79+ agents' performance metrics to drive continuous improvement through data-driven insights and actionable recommendations.

**Mission**: Transform raw agent performance data into strategic insights that identify top performers, detect underperformers, measure learning velocity, and recommend targeted optimizations that improve system-wide efficiency and business impact.

**Dependencies**:
- `system-response-outcome-tracker` - Provides response outcome data
- `system-learning-feedback` - Provides correction and learning data
- `system-error-monitor` - Provides error patterns and reliability metrics
- `system-health-check` - Provides health metrics and uptime data
- All agents (data collection from all 79+ agents)

---

## System Prompt

```
You are the System Agent Performance Analyst for Smarter Team, a sophisticated analytics engine that monitors, measures, and optimizes the performance of all 79+ specialized agents in the multi-agent system.

Your mission is to transform raw performance data into actionable insights that drive continuous improvement across the entire agent ecosystem.

**Core Responsibilities:**

1. **Comprehensive Metric Collection**
   - Track success rates, response times, quality scores, and business impact for all agents
   - Monitor learning velocity (rate of improvement over time)
   - Measure correction rates and human intervention needs
   - Calculate cost efficiency and resource utilization

2. **Performance Analysis & Benchmarking**
   - Establish performance benchmarks from top 10% performers by agent type
   - Compare agents against benchmarks to identify gaps
   - Detect performance anomalies (sudden declines, spikes in errors)
   - Analyze performance trends over time (improving, stable, declining)

3. **Business Impact Measurement**
   - Track revenue impact (deals closed, pipeline value)
   - Measure operational efficiency (leads processed, meetings booked)
   - Calculate cost per outcome (e.g., cost per qualified lead)
   - Monitor customer satisfaction metrics

4. **Insight Generation**
   - Identify top performers and extract success patterns
   - Flag underperforming agents with specific failure modes
   - Generate weekly/monthly performance reports with executive summaries
   - Create agent leaderboards ranked by composite performance scores

5. **Improvement Recommendations**
   - Suggest targeted optimizations based on performance data
   - Prioritize recommendations by expected impact and effort
   - Trigger learning feedback loops for agents with high correction rates
   - Recommend resource allocation adjustments

**Analytical Capabilities:**

- **Statistical Analysis**: Use statistical significance testing for trend detection (95% confidence intervals)
- **Trend Analysis**: Track 7-day, 30-day, and 90-day moving averages for performance metrics
- **Anomaly Detection**: Flag performance degradation >10% week-over-week or >20% month-over-month
- **Comparative Analysis**: Rank agents by agent type (research, outreach, sales, delivery)
- **Learning Velocity**: Calculate improvement rate as (current_score - baseline_score) / days_elapsed

**Key Metrics Tracked:**

**Core Performance:**
- Task completion rate (successful_tasks / total_tasks)
- Average response time (milliseconds)
- Quality score (human-rated, 0-10 scale)
- Correction rate (corrections_count / total_tasks)
- Error rate (failed_tasks / total_tasks)

**Learning Metrics:**
- Learning velocity (% improvement per week)
- Correction trend (increasing/stable/decreasing)
- Time to proficiency (days to reach 85% success rate)
- Knowledge retention (consistent performance over time)

**Business Impact:**
- Leads generated/qualified
- Meetings booked
- Proposals sent/closed
- Revenue impact (dollars attributed to agent)
- Conversion rates (by stage)

**Decision-Making Rules:**

**Anomaly Detection:**
- Flag as WARNING: >10% performance decline week-over-week
- Flag as CRITICAL: >20% performance decline or success rate <70%
- Flag as EXCELLENT: >95% success rate sustained for 30+ days

**Benchmark Establishment:**
- Use top 10% performers by agent type for benchmarks
- Require minimum 100 tasks in period for statistical validity
- Recalculate benchmarks monthly to reflect system improvements

**Learning Velocity Classification:**
- FAST: >5% improvement per week
- MODERATE: 1-5% improvement per week
- SLOW: 0-1% improvement per week
- STAGNANT: <0% (declining or no improvement)

**Report Generation:**
- Daily: Quick metrics snapshot (total tasks, critical issues)
- Weekly: Detailed performance report with trends and recommendations
- Monthly: Executive summary with strategic insights and ROI analysis

**Communication Style:**
- Reports should be data-driven, concise, and actionable
- Use clear visualizations (tables, trend indicators) to enhance clarity
- Provide specific, actionable recommendations with expected impact estimates
- Include executive summary (3-5 bullet points) at top of all reports
- Flag critical issues prominently with severity indicators (🔴 CRITICAL, 🟡 WARNING, 🟢 EXCELLENT)

**Behavioral Guidelines:**
- Be objective and data-driven in all assessments
- Contextualize performance (new agents vs. mature agents)
- Consider external factors (system changes, data quality issues)
- Validate trends with statistical significance before reporting
- Prioritize high-impact, high-frequency agents in recommendations

You have access to tools for collecting metrics, calculating success rates, detecting anomalies, generating leaderboards, creating reports, and recommending improvements. Use these tools systematically to create a culture of continuous improvement and data-driven optimization.
```

---

## Agent Architecture

### Class Definition

```python
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json
import asyncio
from collections import defaultdict

from src.agents.base_agent import BaseAgent
from src.config import get_agent_logger


class PerformanceTrend(str, Enum):
    """Performance trend classification."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


class LearningVelocity(str, Enum):
    """Learning velocity classification."""
    FAST = "fast"          # >5% improvement/week
    MODERATE = "moderate"  # 1-5% improvement/week
    SLOW = "slow"          # 0-1% improvement/week
    STAGNANT = "stagnant"  # <0% or declining


class PerformanceSeverity(str, Enum):
    """Performance alert severity levels."""
    EXCELLENT = "excellent"  # >95% success rate, sustained
    NORMAL = "normal"        # Within expected range
    WARNING = "warning"      # 10-20% decline
    CRITICAL = "critical"    # >20% decline or <70% success


@dataclass
class AgentMetrics:
    """Performance metrics for a single agent in a time period."""
    agent_name: str
    period_start: datetime
    period_end: datetime
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    success_rate: float
    avg_response_time_ms: float
    quality_score: float
    correction_rate: float
    learning_velocity: float
    business_impact: Dict[str, Any]  # leads, meetings, revenue
    trend: PerformanceTrend
    severity: PerformanceSeverity


@dataclass
class PerformanceBenchmark:
    """Performance benchmark for an agent type."""
    agent_type: str
    success_rate_target: float
    response_time_max_ms: float
    quality_score_min: float
    correction_rate_max: float
    based_on_agents: List[str]  # Top performers used for benchmark
    updated_at: datetime


class AgentPerformanceAnalyst(BaseAgent):
    """
    System Agent Performance Analyst for continuous monitoring and optimization.

    Tracks metrics for all 79+ agents, detects anomalies, generates reports,
    and recommends improvements based on data-driven insights.
    """

    def __init__(self):
        super().__init__(
            name="system_agent_performance_analyst",
            description="Monitors and optimizes agent performance across the system"
        )

        # Register tools
        self.register_tool(
            self._collect_agent_metrics,
            "collect_agent_metrics",
            "Collect performance metrics for all agents in a time period"
        )
        self.register_tool(
            self._calculate_success_rates,
            "calculate_success_rates",
            "Calculate success rates and performance metrics by agent"
        )
        self.register_tool(
            self._calculate_learning_velocity,
            "calculate_learning_velocity",
            "Measure improvement rate over time for agents"
        )
        self.register_tool(
            self._detect_performance_anomalies,
            "detect_performance_anomalies",
            "Detect agents with declining or exceptional performance"
        )
        self.register_tool(
            self._generate_leaderboard,
            "generate_leaderboard",
            "Generate performance leaderboard ranked by composite score"
        )
        self.register_tool(
            self._generate_performance_report,
            "generate_performance_report",
            "Generate comprehensive performance report (daily/weekly/monthly)"
        )
        self.register_tool(
            self._recommend_improvements,
            "recommend_improvements",
            "Generate improvement recommendations based on performance data"
        )
        self.register_tool(
            self._set_benchmarks,
            "set_benchmarks",
            "Establish performance benchmarks from top performers"
        )

    @property
    def system_prompt(self) -> str:
        # Return the system prompt from above
        return """..."""  # Full prompt from above

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process performance analysis tasks.

        Supported task types:
        - collect_metrics: Gather performance data for a period
        - generate_report: Create performance report (daily/weekly/monthly)
        - detect_anomalies: Find performance issues requiring attention
        - update_benchmarks: Recalculate performance benchmarks
        - recommend_improvements: Generate optimization suggestions
        """
        task_type = task.get("type")

        if task_type == "collect_metrics":
            return await self._collect_metrics_task(task)
        elif task_type == "generate_report":
            return await self._generate_report_task(task)
        elif task_type == "detect_anomalies":
            return await self._detect_anomalies_task(task)
        elif task_type == "update_benchmarks":
            return await self._update_benchmarks_task(task)
        elif task_type == "recommend_improvements":
            return await self._recommend_improvements_task(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _collect_metrics_task(self, task: dict) -> dict[str, Any]:
        """Collect performance metrics for all agents."""
        period_days = task.get("period_days", 7)
        agent_filter = task.get("agent_filter")

        metrics = await self._collect_agent_metrics(
            period_days=period_days,
            agent_filter=agent_filter
        )

        return {
            "status": "completed",
            "metrics_collected": len(metrics),
            "period_days": period_days,
            "metrics": metrics
        }

    async def _generate_report_task(self, task: dict) -> dict[str, Any]:
        """Generate performance report."""
        report_type = task.get("report_type", "weekly")
        send_alerts = task.get("send_alerts", True)

        report = await self._generate_performance_report(
            report_type=report_type,
            send_alerts=send_alerts
        )

        return {
            "status": "completed",
            "report_id": report["report_id"],
            "report_type": report_type
        }

    async def _detect_anomalies_task(self, task: dict) -> dict[str, Any]:
        """Detect performance anomalies."""
        lookback_days = task.get("lookback_days", 30)

        anomalies = await self._detect_performance_anomalies(
            lookback_days=lookback_days
        )

        return {
            "status": "completed",
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies
        }

    async def _update_benchmarks_task(self, task: dict) -> dict[str, Any]:
        """Update performance benchmarks."""
        benchmarks = await self._set_benchmarks()

        return {
            "status": "completed",
            "benchmarks_updated": len(benchmarks),
            "benchmarks": benchmarks
        }

    async def _recommend_improvements_task(self, task: dict) -> dict[str, Any]:
        """Generate improvement recommendations."""
        agent_name = task.get("agent_name")

        recommendations = await self._recommend_improvements(
            agent_name=agent_name
        )

        return {
            "status": "completed",
            "recommendations_count": len(recommendations),
            "recommendations": recommendations
        }
```

### File Structure

```
app/backend/src/agents/system_agent_performance_analyst/
├── __init__.py
├── agent.py                    # AgentPerformanceAnalyst class
├── metrics.py                  # Metric calculation utilities
├── benchmarks.py               # Benchmark establishment logic
├── anomaly_detection.py        # Anomaly detection algorithms
├── reporting.py                # Report generation and formatting
└── recommendations.py          # Improvement recommendation engine
```

---

## Tool Definitions

### 1. collect_agent_metrics

**Purpose**: Collect comprehensive performance metrics for all agents in a specified time period

**Parameters**:
```python
{
    "period_days": int,              # Days to look back (default: 7)
    "agent_filter": list[str] | None,    # Specific agents to include (None = all)
    "include_business_impact": bool,  # Include revenue/leads metrics (default: True)
    "granularity": str               # "hourly", "daily", "weekly" (default: "daily")
}
```

**Returns**:
```python
{
    "metrics": list[AgentMetrics],
    "total_agents": int,
    "period_start": datetime,
    "period_end": datetime,
    "summary": {
        "total_tasks": int,
        "avg_success_rate": float,
        "avg_quality_score": float,
        "total_corrections": int
    }
}
```

**Implementation**:
```python
async def _collect_agent_metrics(
    self,
    period_days: int = 7,
    agent_filter: list[str] | None = None,
    include_business_impact: bool = True,
    granularity: str = "daily"
) -> dict[str, Any]:
    """
    Collect performance metrics from agent_performance_analytics table.

    Aggregates metrics by agent, calculates success rates, quality scores,
    and business impact metrics.
    """
    from sqlalchemy import select, and_, func
    from src.database import get_async_session
    from src.models import AgentPerformanceAnalytics
    import time

    logger = get_agent_logger("performance_analyst.collect")
    start_time = time.time()

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)

    async with get_async_session() as session:
        # Build query
        query = select(AgentPerformanceAnalytics).where(
            and_(
                AgentPerformanceAnalytics.period_start >= start_date,
                AgentPerformanceAnalytics.period_end <= end_date,
                AgentPerformanceAnalytics.period_type == granularity
            )
        )

        if agent_filter:
            query = query.where(AgentPerformanceAnalytics.agent_name.in_(agent_filter))

        # Execute query
        result = await session.execute(query)
        analytics = result.scalars().all()

        # Aggregate metrics by agent
        agent_metrics_map: Dict[str, List[AgentPerformanceAnalytics]] = defaultdict(list)
        for record in analytics:
            agent_metrics_map[record.agent_name].append(record)

        # Calculate aggregated metrics
        metrics_list = []
        for agent_name, records in agent_metrics_map.items():
            aggregated = _aggregate_agent_metrics(agent_name, records, include_business_impact)
            metrics_list.append(aggregated)

        # Calculate summary statistics
        total_tasks = sum(m.total_tasks for m in metrics_list)
        avg_success_rate = sum(m.success_rate for m in metrics_list) / len(metrics_list) if metrics_list else 0
        avg_quality_score = sum(m.quality_score for m in metrics_list) / len(metrics_list) if metrics_list else 0
        total_corrections = sum(m.total_tasks * m.correction_rate for m in metrics_list)

    processing_time = (time.time() - start_time) * 1000

    logger.info(
        f"Collected metrics for {len(metrics_list)} agents",
        extra={
            "period_days": period_days,
            "total_agents": len(metrics_list),
            "processing_time_ms": processing_time
        }
    )

    return {
        "metrics": metrics_list,
        "total_agents": len(metrics_list),
        "period_start": start_date,
        "period_end": end_date,
        "summary": {
            "total_tasks": total_tasks,
            "avg_success_rate": avg_success_rate,
            "avg_quality_score": avg_quality_score,
            "total_corrections": int(total_corrections)
        }
    }


def _aggregate_agent_metrics(
    agent_name: str,
    records: List[AgentPerformanceAnalytics],
    include_business_impact: bool
) -> AgentMetrics:
    """Aggregate multiple time period records into single metrics object."""
    total_tasks = sum(r.total_tasks for r in records)
    successful_tasks = sum(r.successful_tasks for r in records)
    failed_tasks = sum(r.failed_tasks for r in records)

    success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
    avg_response_time = sum(r.avg_response_time_ms for r in records) / len(records)
    avg_quality_score = sum(r.quality_score for r in records) / len(records) if records else 0

    total_corrections = sum(r.corrections_count for r in records)
    correction_rate = (total_corrections / total_tasks * 100) if total_tasks > 0 else 0

    # Calculate learning velocity (improvement over period)
    learning_velocity = _calculate_learning_velocity_from_records(records)

    # Determine trend
    trend = _determine_performance_trend(records)

    # Classify severity
    severity = _classify_performance_severity(success_rate, trend, learning_velocity)

    # Business impact
    business_impact = {}
    if include_business_impact:
        business_impact = {
            "leads_generated": sum(r.leads_generated for r in records),
            "meetings_booked": sum(r.meetings_booked for r in records),
            "revenue_impact": float(sum(r.revenue_impact for r in records)),
            "conversion_rate": sum(r.conversion_rate for r in records) / len(records) if records else 0
        }

    return AgentMetrics(
        agent_name=agent_name,
        period_start=min(r.period_start for r in records),
        period_end=max(r.period_end for r in records),
        total_tasks=total_tasks,
        successful_tasks=successful_tasks,
        failed_tasks=failed_tasks,
        success_rate=success_rate,
        avg_response_time_ms=avg_response_time,
        quality_score=avg_quality_score,
        correction_rate=correction_rate,
        learning_velocity=learning_velocity,
        business_impact=business_impact,
        trend=trend,
        severity=severity
    )
```

### 2. calculate_success_rates

**Purpose**: Calculate detailed success rate metrics for agents

**Parameters**:
```python
{
    "agent_name": str | None,        # Specific agent or None for all
    "period_days": int,              # Analysis period (default: 30)
    "breakdown_by": list[str]        # ["agent_type", "task_category", "time_of_day"]
}
```

**Returns**:
```python
{
    "overall_success_rate": float,
    "by_agent": dict[str, float],
    "by_agent_type": dict[str, float],
    "by_task_category": dict[str, float],
    "by_time_of_day": dict[str, float],
    "statistical_significance": dict[str, bool]
}
```

### 3. calculate_learning_velocity

**Purpose**: Measure the rate of improvement for agents over time

**Parameters**:
```python
{
    "agent_name": str,
    "comparison_days": int,          # Days for current period (default: 30)
    "baseline_days": int,            # Days for baseline period (default: 60)
    "metrics": list[str]             # ["success_rate", "quality_score", "correction_rate"]
}
```

**Returns**:
```python
{
    "agent_name": str,
    "learning_velocity": float,      # Overall improvement rate (% per week)
    "velocity_classification": LearningVelocity,
    "metric_velocities": {
        "success_rate": float,       # % improvement per week
        "quality_score": float,
        "correction_rate": float     # % reduction per week
    },
    "current_metrics": dict,
    "baseline_metrics": dict,
    "improvement_trend": str,        # "accelerating", "steady", "decelerating"
    "days_to_target": int | None     # Estimated days to reach target performance
}
```

**Implementation**:
```python
async def _calculate_learning_velocity(
    self,
    agent_name: str,
    comparison_days: int = 30,
    baseline_days: int = 60,
    metrics: list[str] = ["success_rate", "quality_score", "correction_rate"]
) -> dict[str, Any]:
    """
    Calculate how quickly an agent is improving over time.

    Learning velocity = (current_performance - baseline_performance) / time_elapsed
    Positive velocity = improvement, negative = decline
    """
    from sqlalchemy import select, and_, func
    from src.database import get_async_session
    from src.models import AgentPerformanceAnalytics

    # Get current period metrics
    current_end = datetime.utcnow()
    current_start = current_end - timedelta(days=comparison_days)

    # Get baseline period metrics (further back in time)
    baseline_end = current_start
    baseline_start = baseline_end - timedelta(days=baseline_days)

    async with get_async_session() as session:
        # Query current period
        current_query = select(AgentPerformanceAnalytics).where(
            and_(
                AgentPerformanceAnalytics.agent_name == agent_name,
                AgentPerformanceAnalytics.period_start >= current_start,
                AgentPerformanceAnalytics.period_end <= current_end
            )
        )
        current_result = await session.execute(current_query)
        current_records = current_result.scalars().all()

        # Query baseline period
        baseline_query = select(AgentPerformanceAnalytics).where(
            and_(
                AgentPerformanceAnalytics.agent_name == agent_name,
                AgentPerformanceAnalytics.period_start >= baseline_start,
                AgentPerformanceAnalytics.period_end <= baseline_end
            )
        )
        baseline_result = await session.execute(baseline_query)
        baseline_records = baseline_result.scalars().all()

    if not current_records or not baseline_records:
        return {
            "agent_name": agent_name,
            "learning_velocity": 0.0,
            "velocity_classification": LearningVelocity.INSUFFICIENT_DATA,
            "error": "Insufficient data for velocity calculation"
        }

    # Calculate average metrics for each period
    current_metrics = _calculate_average_metrics(current_records)
    baseline_metrics = _calculate_average_metrics(baseline_records)

    # Calculate velocity for each metric (per week)
    weeks_elapsed = (baseline_days + comparison_days) / 7
    metric_velocities = {}

    for metric in metrics:
        current_val = current_metrics.get(metric, 0)
        baseline_val = baseline_metrics.get(metric, 0)

        if baseline_val > 0:
            if metric == "correction_rate":
                # Lower is better for correction rate
                velocity = ((baseline_val - current_val) / baseline_val) * 100 / weeks_elapsed
            else:
                # Higher is better for other metrics
                velocity = ((current_val - baseline_val) / baseline_val) * 100 / weeks_elapsed

            metric_velocities[metric] = round(velocity, 2)
        else:
            metric_velocities[metric] = 0.0

    # Calculate overall learning velocity (weighted average)
    overall_velocity = (
        metric_velocities.get("success_rate", 0) * 0.4 +
        metric_velocities.get("quality_score", 0) * 0.4 +
        metric_velocities.get("correction_rate", 0) * 0.2
    )

    # Classify velocity
    if overall_velocity > 5:
        classification = LearningVelocity.FAST
    elif overall_velocity > 1:
        classification = LearningVelocity.MODERATE
    elif overall_velocity > 0:
        classification = LearningVelocity.SLOW
    else:
        classification = LearningVelocity.STAGNANT

    # Determine trend (accelerating/steady/decelerating)
    trend = _determine_improvement_trend(current_records, baseline_records)

    # Estimate days to target (if applicable)
    days_to_target = _estimate_days_to_target(
        current_metrics,
        overall_velocity,
        target_success_rate=95.0
    )

    return {
        "agent_name": agent_name,
        "learning_velocity": round(overall_velocity, 2),
        "velocity_classification": classification,
        "metric_velocities": metric_velocities,
        "current_metrics": current_metrics,
        "baseline_metrics": baseline_metrics,
        "improvement_trend": trend,
        "days_to_target": days_to_target
    }
```

### 4. detect_performance_anomalies

**Purpose**: Identify agents with declining or exceptional performance

**Parameters**:
```python
{
    "lookback_days": int,            # Period to analyze (default: 30)
    "comparison_period": int,        # Previous period for comparison (default: 30)
    "thresholds": dict               # Custom thresholds for anomaly detection
}
```

**Returns**:
```python
{
    "anomalies": [
        {
            "agent_name": str,
            "anomaly_type": str,     # "decline", "spike", "excellence", "stagnation"
            "severity": PerformanceSeverity,
            "metrics": {
                "current_success_rate": float,
                "previous_success_rate": float,
                "change_percent": float
            },
            "description": str,
            "recommended_action": str,
            "detected_at": datetime
        }
    ],
    "critical_count": int,
    "warning_count": int,
    "excellent_count": int
}
```

### 5. generate_leaderboard

**Purpose**: Generate performance leaderboard ranked by composite score

**Parameters**:
```python
{
    "period_days": int,              # Ranking period (default: 30)
    "group_by": str | None,          # "agent_type", "category", or None
    "top_n": int,                    # Number of top performers to show (default: 10)
    "scoring_weights": dict          # Custom weights for composite score
}
```

**Returns**:
```python
{
    "leaderboard": [
        {
            "rank": int,
            "agent_name": str,
            "agent_type": str,
            "composite_score": float,    # 0-100 weighted score
            "success_rate": float,
            "quality_score": float,
            "learning_velocity": float,
            "business_impact": float,
            "badges": list[str]          # ["top_performer", "fast_learner", "high_quality"]
        }
    ],
    "by_agent_type": dict[str, list],   # Leaderboards grouped by type
    "generated_at": datetime
}
```

### 6. generate_performance_report

**Purpose**: Generate comprehensive performance report for specified period

**Parameters**:
```python
{
    "report_type": str,              # "daily", "weekly", "monthly"
    "date": str | None,              # Specific date (YYYY-MM-DD) or None for latest
    "include_sections": list[str],   # Sections to include in report
    "send_alerts": bool,             # Whether to send via Slack/email
    "format": str                    # "markdown", "html", "json"
}
```

**Returns**:
```python
{
    "report_id": str,
    "report_type": str,
    "period_start": datetime,
    "period_end": datetime,
    "executive_summary": {
        "total_agents": int,
        "avg_success_rate": float,
        "top_performer": str,
        "agents_needing_attention": int,
        "key_insights": list[str]
    },
    "sections": {
        "overview": dict,            # System-wide metrics
        "top_performers": list,      # Top 10 agents
        "underperformers": list,     # Bottom 10 agents
        "anomalies": list,           # Performance anomalies
        "trends": dict,              # Week-over-week, month-over-month
        "recommendations": list      # Actionable improvements
    },
    "report_text": str,              # Formatted report
    "generated_at": datetime
}
```

### 7. recommend_improvements

**Purpose**: Generate specific improvement recommendations based on performance data

**Parameters**:
```python
{
    "agent_name": str | None,        # Specific agent or None for all
    "focus_areas": list[str],        # ["accuracy", "speed", "quality", "cost"]
    "max_recommendations": int,      # Maximum recommendations to return
    "priority_filter": str | None    # "high", "medium", "low", or None
}
```

**Returns**:
```python
{
    "recommendations": [
        {
            "recommendation_id": str,
            "agent_name": str,
            "category": str,             # "prompt_optimization", "training_data", "architecture"
            "priority": str,             # "high", "medium", "low"
            "issue": str,                # Problem description
            "recommendation": str,       # Specific action to take
            "expected_impact": {
                "success_rate_improvement": float,  # Expected % improvement
                "cost_reduction": float,
                "time_saving": float
            },
            "effort_estimate": str,      # "low", "medium", "high"
            "implementation_steps": list[str],
            "related_patterns": list[str],  # Similar issues in other agents
            "confidence": float          # Confidence in recommendation (0-1)
        }
    ],
    "total_recommendations": int,
    "high_priority_count": int,
    "estimated_total_impact": dict
}
```

### 8. set_benchmarks

**Purpose**: Establish performance benchmarks from top performers

**Parameters**:
```python
{
    "percentile": int,               # Percentile for top performers (default: 90)
    "min_tasks": int,                # Minimum tasks required for inclusion (default: 100)
    "period_days": int,              # Period to analyze (default: 30)
    "force_update": bool             # Force recalculation (default: False)
}
```

**Returns**:
```python
{
    "benchmarks": {
        "research": PerformanceBenchmark,
        "outreach": PerformanceBenchmark,
        "sales": PerformanceBenchmark,
        "delivery": PerformanceBenchmark,
        "system": PerformanceBenchmark
    },
    "updated_at": datetime,
    "next_update": datetime,
    "agents_analyzed": int
}
```

---

## Database Schema

The agent uses the following tables from migration `007_learning_system.sql`:

### agent_performance_analytics Table

```sql
CREATE TABLE IF NOT EXISTS agent_performance_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Agent Information
    agent_name VARCHAR(100) NOT NULL,
    agent_type VARCHAR(100),
    agent_version VARCHAR(50),

    -- Time Period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    period_type VARCHAR(20) DEFAULT 'day', -- hour, day, week, month

    -- Key Metrics
    total_tasks INTEGER DEFAULT 0,
    successful_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),

    -- Performance Metrics
    avg_response_time_ms INTEGER,
    avg_task_completion_time_ms INTEGER,
    accuracy_score DECIMAL(5,2), -- 0-100%
    quality_score DECIMAL(5,2), -- Human-rated quality

    -- Learning Metrics
    corrections_count INTEGER DEFAULT 0,
    improvements_count INTEGER DEFAULT 0,
    new_insights_count INTEGER DEFAULT 0,
    learning_velocity DECIMAL(5,2), -- Rate of improvement

    -- Business Impact
    leads_generated INTEGER DEFAULT 0,
    meetings_booked INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,2),
    revenue_impact DECIMAL(12,2),

    -- Context
    campaigns_worked_on INTEGER DEFAULT 0,
    leads_handled INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,

    -- Detailed Breakdown
    performance_breakdown JSONB DEFAULT '{}', -- Detailed metrics by category
    error_breakdown JSONB DEFAULT '{}', -- Types of errors and frequencies
    success_factors JSONB DEFAULT '{}', -- What contributed to success

    -- Trends
    performance_trend VARCHAR(20), -- improving, stable, declining
    trend_strength DECIMAL(3,2), -- How strong is the trend

    -- Metadata
    metadata JSONB DEFAULT '{}',
    notes TEXT,

    -- Status
    status VARCHAR(50) DEFAULT 'calculated'
);

CREATE INDEX IF NOT EXISTS idx_apa_agent_period ON agent_performance_analytics(agent_name, period_start);
CREATE INDEX IF NOT EXISTS idx_apa_success ON agent_performance_analytics(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_apa_trend ON agent_performance_analytics(performance_trend, trend_strength);
```

### agent_metrics Table (Real-time metrics)

```sql
CREATE TABLE IF NOT EXISTS agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Agent Information
    agent_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- task_completion, response_time, error_rate

    -- Metric Value
    metric_value DECIMAL(10,2) NOT NULL,
    metric_unit VARCHAR(20), -- percent, milliseconds, count

    -- Context
    context JSONB DEFAULT '{}',

    -- Timestamp
    measured_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_agent_metrics_name_type ON agent_metrics(agent_name, metric_type),
    INDEX idx_agent_metrics_measured ON agent_metrics(measured_at DESC)
);
```

### performance_trends Table

```sql
CREATE TABLE IF NOT EXISTS performance_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Agent Information
    agent_name VARCHAR(100) NOT NULL,

    -- Trend Analysis
    trend_type VARCHAR(50) NOT NULL, -- success_rate, quality_score, learning_velocity
    trend_direction VARCHAR(20), -- improving, stable, declining
    trend_strength DECIMAL(3,2), -- 0-1 confidence in trend

    -- Time Period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,

    -- Statistical Analysis
    baseline_value DECIMAL(10,2),
    current_value DECIMAL(10,2),
    change_percent DECIMAL(5,2),
    statistical_significance DECIMAL(3,2), -- p-value

    -- Metadata
    metadata JSONB DEFAULT '{}',

    INDEX idx_perf_trends_agent ON performance_trends(agent_name, trend_type),
    INDEX idx_perf_trends_period ON performance_trends(period_start, period_end)
);
```

### agent_benchmarks Table

```sql
CREATE TABLE IF NOT EXISTS agent_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Benchmark Scope
    agent_type VARCHAR(100) NOT NULL UNIQUE,

    -- Target Metrics
    success_rate_target DECIMAL(5,2) NOT NULL,
    response_time_max_ms INTEGER NOT NULL,
    quality_score_min DECIMAL(5,2) NOT NULL,
    correction_rate_max DECIMAL(5,2) NOT NULL,

    -- Benchmark Source
    based_on_percentile INTEGER DEFAULT 90, -- Top 10% performers
    based_on_agents TEXT[] DEFAULT '{}', -- Agent names used
    sample_size INTEGER, -- Number of agents in sample

    -- Validity
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    INDEX idx_benchmarks_type ON agent_benchmarks(agent_type),
    INDEX idx_benchmarks_validity ON agent_benchmarks(valid_from, valid_until)
);
```

---

## Learning Velocity Calculation Algorithm

```python
def calculate_learning_velocity(agent_name: str, days: int = 30) -> float:
    """
    Calculate how quickly an agent is improving.

    Formula:
    velocity = weighted_avg([
        (recent_success - older_success) / older_success * 0.4,
        (recent_quality - older_quality) / older_quality * 0.4,
        (older_corrections - recent_corrections) / older_corrections * 0.2
    ]) / weeks_elapsed * 100

    Returns: % improvement per week
    """
    # Get performance data
    recent = get_agent_performance(agent_name, days=days)
    older = get_agent_performance(agent_name, start_days=days*2, end_days=days)

    if not older or not recent:
        return 0.0

    weeks_elapsed = days / 7

    # Calculate improvement rates (handle division by zero)
    success_improvement = 0
    if older['avg_success_rate'] > 0:
        success_improvement = (
            (recent['avg_success_rate'] - older['avg_success_rate'])
            / older['avg_success_rate']
        )

    quality_improvement = 0
    if older['avg_quality_score'] > 0:
        quality_improvement = (
            (recent['avg_quality_score'] - older['avg_quality_score'])
            / older['avg_quality_score']
        )

    correction_improvement = 0
    if older['correction_rate'] > 0:
        correction_improvement = (
            (older['correction_rate'] - recent['correction_rate'])
            / older['correction_rate']
        )

    # Weighted average (success and quality weighted higher)
    velocity = (
        success_improvement * 0.4 +
        quality_improvement * 0.4 +
        correction_improvement * 0.2
    ) / weeks_elapsed * 100

    return round(velocity, 2)
```

---

## Performance Alert Thresholds

```python
# Anomaly Detection Thresholds
THRESHOLDS = {
    # Success rate thresholds
    "CRITICAL_SUCCESS_RATE": 70.0,      # Below this = CRITICAL
    "WARNING_SUCCESS_RATE": 85.0,       # Below this = WARNING
    "EXCELLENT_SUCCESS_RATE": 95.0,     # Above this = EXCELLENT

    # Performance decline thresholds
    "WARNING_DECLINE_PERCENT": 10.0,    # Week-over-week decline
    "CRITICAL_DECLINE_PERCENT": 20.0,   # Week-over-week decline

    # Learning velocity thresholds
    "FAST_VELOCITY": 5.0,               # >5% improvement/week
    "MODERATE_VELOCITY": 1.0,           # 1-5% improvement/week
    "SLOW_VELOCITY": 0.0,               # 0-1% improvement/week
    # <0% = STAGNANT

    # Quality score thresholds
    "MIN_QUALITY_SCORE": 7.0,           # Out of 10
    "EXCELLENT_QUALITY_SCORE": 9.0,     # Out of 10

    # Correction rate thresholds
    "MAX_CORRECTION_RATE": 15.0,        # % of tasks requiring correction
    "CRITICAL_CORRECTION_RATE": 25.0,   # % of tasks requiring correction

    # Statistical significance
    "MIN_SAMPLE_SIZE": 100,             # Minimum tasks for valid statistics
    "CONFIDENCE_LEVEL": 0.95,           # 95% confidence interval

    # Benchmark recalculation
    "BENCHMARK_UPDATE_DAYS": 30,        # Update benchmarks monthly
    "TOP_PERFORMER_PERCENTILE": 90,     # Use top 10% for benchmarks
}
```

---

## Error Handling Strategy

### Error Categories

1. **Insufficient Data Errors**
   - Handle agents with <100 tasks gracefully
   - Return `INSUFFICIENT_DATA` status
   - Recommend minimum data collection period

2. **Database Connection Errors**
   - Retry with exponential backoff (3 attempts)
   - Fall back to cached metrics if available
   - Alert system administrator if persistent

3. **Calculation Errors**
   - Handle division by zero in velocity calculations
   - Validate metric ranges (0-100 for percentages)
   - Log invalid data and skip corrupted records

4. **Integration Failures**
   - Gracefully handle missing agent data
   - Continue processing other agents if one fails
   - Aggregate and report all failures at end

### Error Recovery

```python
async def _safe_metric_collection(self, agent_name: str) -> dict[str, Any] | None:
    """Safely collect metrics with error handling."""
    try:
        return await self._collect_agent_metrics(agent_filter=[agent_name])
    except InsufficientDataError:
        self.logger.warning(f"Insufficient data for {agent_name}")
        return None
    except DatabaseError as e:
        self.logger.error(f"Database error collecting metrics for {agent_name}: {e}")
        # Try cached data
        cached = await self._get_cached_metrics(agent_name)
        if cached:
            return cached
        return None
    except Exception as e:
        self.logger.error(f"Unexpected error for {agent_name}: {e}")
        return None
```

---

## Testing Requirements

### Unit Tests (>90% coverage required)

**Test file**: `__tests__/unit/agents/test_agent_performance_analyst.py`

```python
class TestAgentPerformanceAnalystInitialization:
    def test_agent_initialization()
    def test_tools_registered()
    def test_system_prompt_defined()

class TestCollectAgentMetrics:
    @pytest.mark.asyncio
    async def test_collect_all_agents()
    async def test_collect_filtered_agents()
    async def test_collect_with_granularity()
    async def test_collect_insufficient_data()
    async def test_metric_aggregation()

class TestCalculateSuccessRates:
    @pytest.mark.asyncio
    async def test_overall_success_rate()
    async def test_success_rate_by_agent_type()
    async def test_success_rate_by_time()
    async def test_statistical_significance()

class TestCalculateLearningVelocity:
    @pytest.mark.asyncio
    async def test_velocity_fast_learner()
    async def test_velocity_stagnant_agent()
    async def test_velocity_declining_agent()
    async def test_velocity_insufficient_data()
    async def test_days_to_target_calculation()

class TestDetectPerformanceAnomalies:
    @pytest.mark.asyncio
    async def test_detect_decline_anomaly()
    async def test_detect_excellence_anomaly()
    async def test_detect_stagnation_anomaly()
    async def test_anomaly_severity_classification()

class TestGenerateLeaderboard:
    @pytest.mark.asyncio
    async def test_leaderboard_generation()
    async def test_leaderboard_by_type()
    async def test_composite_score_calculation()
    async def test_badge_assignment()

class TestGeneratePerformanceReport:
    @pytest.mark.asyncio
    async def test_daily_report_generation()
    async def test_weekly_report_generation()
    async def test_monthly_report_generation()
    async def test_executive_summary_generation()
    async def test_report_formatting()

class TestRecommendImprovements:
    @pytest.mark.asyncio
    async def test_accuracy_recommendations()
    async def test_speed_recommendations()
    async def test_cost_recommendations()
    async def test_recommendation_priority()

class TestSetBenchmarks:
    @pytest.mark.asyncio
    async def test_benchmark_establishment()
    async def test_benchmark_by_agent_type()
    async def test_benchmark_update_logic()
```

### Integration Tests

**Test file**: `__tests__/integration/test_agent_performance_analyst_integration.py`

```python
class TestPerformanceAnalystIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_analysis_flow()
    async def test_multi_agent_metric_collection()
    async def test_anomaly_detection_with_real_data()
    async def test_report_generation_and_delivery()
    async def test_benchmark_comparison()

class TestDatabaseIntegration:
    @pytest.mark.asyncio
    async def test_metrics_persistence()
    async def test_trend_calculation()
    async def test_benchmark_storage()

class TestAlertingIntegration:
    @pytest.mark.asyncio
    async def test_slack_alert_delivery()
    async def test_email_report_delivery()
```

---

## Implementation Checklist

### Phase 1: Core Metric Collection
- [ ] Implement `AgentPerformanceAnalyst` class extending `BaseAgent`
- [ ] Implement `collect_agent_metrics` tool with aggregation logic
- [ ] Implement `calculate_success_rates` tool with breakdowns
- [ ] Create database models for `agent_metrics`, `performance_trends`
- [ ] Write unit tests for metric collection (>90% coverage)

### Phase 2: Analysis & Detection
- [ ] Implement `calculate_learning_velocity` tool with trend analysis
- [ ] Implement `detect_performance_anomalies` tool with thresholds
- [ ] Create anomaly detection algorithms
- [ ] Implement statistical significance testing
- [ ] Write unit tests for analysis functions

### Phase 3: Benchmarking
- [ ] Implement `set_benchmarks` tool
- [ ] Create benchmark calculation logic (top 10% performers)
- [ ] Create `agent_benchmarks` table and model
- [ ] Implement benchmark comparison logic
- [ ] Write unit tests for benchmarking

### Phase 4: Reporting & Recommendations
- [ ] Implement `generate_leaderboard` tool
- [ ] Implement `generate_performance_report` tool
- [ ] Implement `recommend_improvements` tool
- [ ] Create report templates (daily/weekly/monthly)
- [ ] Integrate with Slack/email for delivery
- [ ] Write unit tests for reporting

### Phase 5: Integration & Automation
- [ ] Create Celery tasks for scheduled analysis
- [ ] Configure Celery Beat schedule (daily/weekly/monthly)
- [ ] Integrate with `system-response-outcome-tracker`
- [ ] Integrate with `system-learning-feedback`
- [ ] Integrate with `system-error-monitor`
- [ ] Write comprehensive integration tests

### Phase 6: Testing & Optimization
- [ ] Achieve >90% test coverage
- [ ] Performance test with 79+ agents
- [ ] Optimize query performance with proper indexing
- [ ] Test alert delivery mechanisms
- [ ] Document all procedures and runbooks

---

## Success Metrics

- **Metric Coverage**: 100% of 79+ agents tracked with daily metrics
- **Report Accuracy**: >95% accuracy in anomaly detection (validated by human review)
- **Report Timeliness**: Daily reports generated within 1 hour of period end
- **Benchmark Validity**: Benchmarks updated monthly, based on min 100 tasks per agent
- **Recommendation Effectiveness**: >70% of implemented recommendations improve performance
- **System Performance**: Report generation <5 minutes for 79+ agents
- **Alert Precision**: <5% false positive rate for performance alerts
- **User Satisfaction**: >85% satisfaction with report actionability
- **Test Coverage**: >90% code coverage

---

## Celery Tasks & Scheduling

### Celery Tasks

```python
from src.celery_app import celery_app
from datetime import date, timedelta

@celery_app.task(bind=True, max_retries=3)
def update_real_time_metrics(self):
    """Update real-time metrics every 5 minutes."""
    from src.agents.system_agent_performance_analyst.agent import AgentPerformanceAnalyst

    agent = AgentPerformanceAnalyst()

    # Collect metrics for last 5 minutes
    result = await agent._collect_agent_metrics(
        period_days=0.00347,  # ~5 minutes in days
        granularity="hourly"
    )

    return {"status": "completed", "agents_updated": result["total_agents"]}


@celery_app.task(bind=True, max_retries=3)
def calculate_daily_performance(self):
    """Calculate daily performance aggregates."""
    from src.agents.system_agent_performance_analyst.agent import AgentPerformanceAnalyst

    agent = AgentPerformanceAnalyst()

    # Collect and aggregate yesterday's metrics
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    result = await agent.process_task({
        "type": "collect_metrics",
        "period_days": 1,
        "granularity": "daily"
    })

    return result


@celery_app.task(bind=True, max_retries=3)
def detect_daily_anomalies(self):
    """Detect performance anomalies daily."""
    from src.agents.system_agent_performance_analyst.agent import AgentPerformanceAnalyst

    agent = AgentPerformanceAnalyst()

    result = await agent.process_task({
        "type": "detect_anomalies",
        "lookback_days": 30
    })

    # Send alerts for critical anomalies
    critical_anomalies = [a for a in result["anomalies"] if a["severity"] == "critical"]
    if critical_anomalies:
        await agent._send_anomaly_alerts(critical_anomalies)

    return result


@celery_app.task(bind=True, max_retries=3)
def generate_weekly_report(self):
    """Generate weekly performance report."""
    from src.agents.system_agent_performance_analyst.agent import AgentPerformanceAnalyst

    agent = AgentPerformanceAnalyst()

    result = await agent.process_task({
        "type": "generate_report",
        "report_type": "weekly",
        "send_alerts": True
    })

    return result


@celery_app.task(bind=True, max_retries=3)
def update_monthly_benchmarks(self):
    """Update performance benchmarks monthly."""
    from src.agents.system_agent_performance_analyst.agent import AgentPerformanceAnalyst

    agent = AgentPerformanceAnalyst()

    result = await agent.process_task({
        "type": "update_benchmarks"
    })

    return result
```

### Celery Beat Schedule

```python
# In src/celery_app.py or config

from celery.schedules import crontab

beat_schedule = {
    "update-real-time-metrics": {
        "task": "src.tasks.performance_tasks.update_real_time_metrics",
        "schedule": 300.0,  # Every 5 minutes
    },
    "calculate-daily-performance": {
        "task": "src.tasks.performance_tasks.calculate_daily_performance",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1:00 AM
    },
    "detect-daily-anomalies": {
        "task": "src.tasks.performance_tasks.detect_daily_anomalies",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2:00 AM
    },
    "generate-weekly-report": {
        "task": "src.tasks.performance_tasks.generate_weekly_report",
        "schedule": crontab(day_of_week=1, hour=8, minute=0),  # Monday at 8:00 AM
    },
    "update-monthly-benchmarks": {
        "task": "src.tasks.performance_tasks.update_monthly_benchmarks",
        "schedule": crontab(day_of_month=1, hour=3, minute=0),  # 1st of month at 3:00 AM
    },
}
```

---

## Related Agents

**Data Sources:**
- `system-response-outcome-tracker` - Response effectiveness data
- `system-learning-feedback` - Correction patterns and learning events
- `system-error-monitor` - Error rates and reliability metrics
- `system-health-check` - System health and uptime data
- All 79+ agents - Task execution metrics

**Data Consumers:**
- `system-learning-feedback` - Receives improvement triggers
- `system-correction-approval-orchestrator` - Receives performance alerts
- Human operators - Performance reports and dashboards

---

## Future Enhancements

1. **Predictive Analytics**
   - ML models to predict future performance trends
   - Early warning system for performance degradation
   - Capacity planning based on historical trends

2. **Advanced Visualization**
   - Interactive performance dashboards
   - Real-time performance monitoring UI
   - Trend charts and heatmaps

3. **Automated Optimization**
   - Auto-tune agent parameters based on performance data
   - A/B test agent configurations automatically
   - Self-healing agents that adapt to performance issues

4. **Cross-Agent Learning**
   - Identify patterns across similar agents
   - Transfer learning from high performers to low performers
   - Build shared knowledge repository

5. **ROI Calculation**
   - Calculate return on investment for each agent
   - Cost-benefit analysis for improvements
   - Budget optimization recommendations

6. **Explainable AI**
   - Detailed explanations for performance changes
   - Root cause analysis using AI
   - Natural language insights generation

---

## Dependencies

### Python Packages (already installed)
- `numpy>=1.24.0` - Statistical calculations
- `scipy>=1.10.0` - Statistical significance testing
- `sqlalchemy>=2.0.44` - Database operations
- `asyncpg>=0.31.0` - PostgreSQL async driver

### External Services
- Database: PostgreSQL (Supabase)
- Cache: Redis (Upstash)
- Monitoring: Internal monitoring system
- Notifications: Slack, Email

### Agent Dependencies
- Receives data from: All 79+ agents, system-response-outcome-tracker, system-learning-feedback, system-error-monitor, system-health-check
- Sends data to: system-learning-feedback, system-correction-approval-orchestrator

---

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0

# Optional - Alerting
SLACK_PERFORMANCE_WEBHOOK_URL=https://hooks.slack.com/services/...
PERFORMANCE_ALERT_EMAIL=team@smarterteam.com

# Optional - Configuration
PERFORMANCE_BENCHMARK_PERCENTILE=90  # Top 10% for benchmarks
PERFORMANCE_MIN_SAMPLE_SIZE=100      # Minimum tasks for statistics
PERFORMANCE_UPDATE_INTERVAL=300      # Seconds between metric updates
```

---

## Security Considerations

1. **Data Privacy**: Anonymize agent names in external reports if needed
2. **Access Control**: Role-based access to performance insights
3. **Audit Trail**: Log all performance report generations
4. **Rate Limiting**: Prevent abuse of performance API endpoints
5. **Data Retention**: Retain performance metrics for 2+ years for trend analysis
