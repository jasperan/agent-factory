"""
Agent Factory Observability Package

Production monitoring and observability for agent systems.

Provides:
- Request tracing (end-to-end visibility)
- Performance metrics (latency, success rates)
- Cost tracking (API usage costs)

Usage:
    from agent_factory.observability import Tracer, Metrics, CostTracker

    # Create observability components
    tracer = Tracer()
    metrics = Metrics()
    cost_tracker = CostTracker()

    # Start tracing a request
    trace_id = tracer.start_trace("What is AI?")
    span = tracer.start_span("agent_start")

    # Record metrics
    metrics.record_request(
        agent_name="research",
        duration_ms=150.5,
        success=True,
        tokens={"prompt": 100, "completion": 50, "total": 150}
    )

    # Track costs
    cost_tracker.record_cost(
        agent_name="research",
        provider="openai",
        model="gpt-4o",
        prompt_tokens=100,
        completion_tokens=50
    )

    # Get summaries
    trace = tracer.get_trace(trace_id)
    metrics_summary = metrics.summary()
    cost_summary = cost_tracker.summary()

Available Classes:
    Tracer: Request tracing with spans
    Trace: Complete request trace
    Span: Single operation in a trace
    Metrics: Performance metrics aggregator
    CostTracker: API cost calculator and tracker
"""

from .tracer import Tracer, Trace, Span
from .metrics import Metrics
from .cost_tracker import CostTracker

__all__ = [
    # Tracing
    "Tracer",
    "Trace",
    "Span",
    # Metrics
    "Metrics",
    # Cost tracking
    "CostTracker",
]
