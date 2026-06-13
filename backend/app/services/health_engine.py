"""Agent health scoring engine — production metrics from stored executions."""

from dataclasses import dataclass


@dataclass
class HealthScoreBreakdown:
    health_score: float
    success_rate: float
    error_rate: float
    latency_score: float
    cost_efficiency_score: float
    reliability_score: float
    avg_latency_ms: float
    avg_cost_per_execution: float
    total_executions: int
    total_cost: float


def compute_health(
    *,
    total_executions: int,
    success_rate_pct: float,
    error_rate_pct: float,
    avg_latency_ms: float,
    total_cost: float,
) -> HealthScoreBreakdown:
    """Compute 0-100 health score from execution aggregates."""
    if total_executions == 0:
        return HealthScoreBreakdown(
            health_score=100.0,
            success_rate=100.0,
            error_rate=0.0,
            latency_score=100.0,
            cost_efficiency_score=100.0,
            reliability_score=100.0,
            avg_latency_ms=0.0,
            avg_cost_per_execution=0.0,
            total_executions=0,
            total_cost=0.0,
        )

    avg_cost = total_cost / total_executions
    latency_score = max(0.0, min(100.0, 100.0 - (avg_latency_ms / 100.0)))
    # Cost efficiency: lower avg cost is better
    cost_efficiency_score = max(0.0, min(100.0, 100.0 - (avg_cost * 10000.0)))
    # Reliability: inverse of error rate
    reliability_score = max(0.0, min(100.0, 100.0 - error_rate_pct))

    health_score = round(
        success_rate_pct * 0.35
        + reliability_score * 0.25
        + latency_score * 0.20
        + cost_efficiency_score * 0.20,
        1,
    )

    return HealthScoreBreakdown(
        health_score=health_score,
        success_rate=round(success_rate_pct, 2),
        error_rate=round(error_rate_pct, 2),
        latency_score=round(latency_score, 1),
        cost_efficiency_score=round(cost_efficiency_score, 1),
        reliability_score=round(reliability_score, 1),
        avg_latency_ms=round(avg_latency_ms, 2),
        avg_cost_per_execution=round(avg_cost, 6),
        total_executions=total_executions,
        total_cost=round(total_cost, 6),
    )
