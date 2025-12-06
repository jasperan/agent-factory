"""
Tests for agent_factory.observability module

Tests tracing, metrics, and cost tracking functionality.
"""
import sys
from pathlib import Path
from datetime import datetime
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from agent_factory.observability import (
    Tracer,
    Trace,
    Span,
    Metrics,
    CostTracker,
)


class TestTracer:
    """Test request tracing functionality."""

    def test_tracer_creates_trace(self):
        """REQ-OBS-001: Tracer creates traces with unique IDs."""
        tracer = Tracer()
        trace_id = tracer.start_trace("test query")

        assert trace_id is not None
        assert trace_id.startswith("trace_")
        assert len(trace_id) > 10  # Should have unique hash

    def test_tracer_stores_trace(self):
        """REQ-OBS-001: Tracer stores traces for retrieval."""
        tracer = Tracer()
        trace_id = tracer.start_trace("test query")

        trace = tracer.get_trace(trace_id)

        assert trace is not None
        assert trace.query == "test query"
        assert trace.trace_id == trace_id

    def test_span_creation(self):
        """REQ-OBS-001: Tracer creates spans within traces."""
        tracer = Tracer()
        trace_id = tracer.start_trace("test query")

        span = tracer.start_span("test_operation")

        assert span is not None
        assert span.name == "test_operation"
        assert span.trace_id == trace_id

    def test_span_finish(self):
        """REQ-OBS-001: Span calculates duration when finished."""
        tracer = Tracer()
        tracer.start_trace("test")

        span = tracer.start_span("operation")
        time.sleep(0.01)  # 10ms
        span.finish()

        assert span.end_time is not None
        assert span.duration_ms is not None
        assert span.duration_ms >= 10  # At least 10ms

    def test_trace_finish(self):
        """REQ-OBS-001: Trace marked as complete with status."""
        tracer = Tracer()
        trace_id = tracer.start_trace("test")

        tracer.finish_trace(success=True)

        trace = tracer.get_trace(trace_id)
        assert trace.success is True
        assert trace.end_time is not None
        assert trace.duration_ms is not None

    def test_trace_with_error(self):
        """REQ-OBS-004: Trace captures error information."""
        tracer = Tracer()
        trace_id = tracer.start_trace("test")

        tracer.finish_trace(success=False, error="Test error message")

        trace = tracer.get_trace(trace_id)
        assert trace.success is False
        assert trace.error == "Test error message"

    def test_export_traces(self):
        """REQ-OBS-001: Traces exportable to dict format."""
        tracer = Tracer()
        tracer.start_trace("query 1")
        tracer.finish_trace(success=True)

        tracer.start_trace("query 2")
        tracer.finish_trace(success=False, error="Test error")

        traces = tracer.export_traces()

        assert len(traces) == 2
        assert all(isinstance(t, dict) for t in traces)
        assert all("trace_id" in t for t in traces)


class TestMetrics:
    """Test performance metrics functionality."""

    def test_metrics_record_request(self):
        """REQ-OBS-002: Metrics record request data."""
        metrics = Metrics()

        metrics.record_request(
            agent_name="test_agent",
            duration_ms=100.5,
            success=True
        )

        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0

    def test_metrics_success_rate(self):
        """REQ-OBS-002: Metrics calculate success rate."""
        metrics = Metrics()

        metrics.record_request("agent1", 100, True)
        metrics.record_request("agent2", 150, True)
        metrics.record_request("agent3", 200, False)

        assert metrics.success_rate == pytest.approx(66.67, abs=0.01)
        assert metrics.total_requests == 3

    def test_metrics_latency_tracking(self):
        """REQ-OBS-002: Metrics track latency percentiles."""
        metrics = Metrics()

        # Record 10 requests with increasing latency
        for i in range(10):
            metrics.record_request(f"agent{i}", i * 100, True)

        assert metrics.avg_latency == 450.0  # (0+100+...+900) / 10
        assert metrics.p50_latency == 500.0  # 50th percentile (median of 0-900)
        assert metrics.p95_latency == 900.0  # 95th percentile

    def test_metrics_token_tracking(self):
        """REQ-OBS-002: Metrics track token usage."""
        metrics = Metrics()

        metrics.record_request(
            "agent",
            100,
            True,
            tokens={"prompt": 100, "completion": 50, "total": 150}
        )

        assert metrics.total_tokens == 150
        assert metrics.prompt_tokens == 100
        assert metrics.completion_tokens == 50

    def test_metrics_per_agent_stats(self):
        """REQ-OBS-002: Metrics provide per-agent breakdown."""
        metrics = Metrics()

        metrics.record_request("research", 100, True)
        metrics.record_request("research", 150, True)
        metrics.record_request("coding", 200, True)

        stats = metrics.get_agent_stats("research")

        assert stats["requests"] == 2
        assert stats["success_rate"] == 100.0
        assert stats["avg_latency_ms"] == 125.0  # (100+150)/2

    def test_metrics_error_tracking(self):
        """REQ-OBS-004: Metrics track error types."""
        metrics = Metrics()

        metrics.record_request("agent1", 100, False, error_type="timeout")
        metrics.record_request("agent2", 150, False, error_type="timeout")
        metrics.record_request("agent3", 200, False, error_type="llm_error")

        assert metrics.error_counts["timeout"] == 2
        assert metrics.error_counts["llm_error"] == 1

    def test_metrics_summary(self):
        """REQ-OBS-002: Metrics provide comprehensive summary."""
        metrics = Metrics()

        metrics.record_request("research", 100, True)
        metrics.record_request("coding", 150, True)

        summary = metrics.summary()

        assert "total_requests" in summary
        assert "success_rate" in summary
        assert "latency" in summary
        assert "tokens" in summary
        assert "agents" in summary


class TestCostTracker:
    """Test cost tracking functionality."""

    def test_cost_tracker_calculate_openai_cost(self):
        """REQ-OBS-003: Cost tracker calculates OpenAI costs."""
        tracker = CostTracker()

        cost = tracker.calculate_cost("openai", "gpt-4o", 1000, 500)

        # 1K * 0.0025 + 0.5K * 0.01 = 0.0025 + 0.005 = 0.0075
        assert cost == pytest.approx(0.0075, abs=0.0001)

    def test_cost_tracker_calculate_anthropic_cost(self):
        """REQ-OBS-003: Cost tracker calculates Anthropic costs."""
        tracker = CostTracker()

        cost = tracker.calculate_cost("anthropic", "claude-sonnet-4", 1000, 500)

        # 1K * 0.003 + 0.5K * 0.015 = 0.003 + 0.0075 = 0.0105
        assert cost == pytest.approx(0.0105, abs=0.0001)

    def test_cost_tracker_record_cost(self):
        """REQ-OBS-003: Cost tracker records costs by agent."""
        tracker = CostTracker()

        cost = tracker.record_cost(
            agent_name="research",
            provider="openai",
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500
        )

        assert cost > 0
        assert tracker.total_cost == pytest.approx(cost, abs=0.0001)
        assert tracker.get_agent_cost("research") == pytest.approx(cost, abs=0.0001)

    def test_cost_tracker_by_provider(self):
        """REQ-OBS-003: Cost tracker breaks down by provider."""
        tracker = CostTracker()

        tracker.record_cost("agent1", "openai", "gpt-4o", 1000, 500)
        tracker.record_cost("agent2", "anthropic", "claude-sonnet-4", 1000, 500)

        openai_cost = tracker.get_provider_cost("openai")
        anthropic_cost = tracker.get_provider_cost("anthropic")

        assert openai_cost > 0
        assert anthropic_cost > 0
        assert tracker.total_cost == pytest.approx(openai_cost + anthropic_cost, abs=0.0001)

    def test_cost_tracker_top_agents(self):
        """REQ-OBS-003: Cost tracker identifies top agents by cost."""
        tracker = CostTracker()

        tracker.record_cost("research", "openai", "gpt-4o", 10000, 5000)  # Higher cost
        tracker.record_cost("coding", "openai", "gpt-4o", 1000, 500)  # Lower cost

        top_agents = tracker.get_top_agents_by_cost(2)

        assert len(top_agents) == 2
        assert top_agents[0][0] == "research"  # Most expensive first
        assert top_agents[0][1] > top_agents[1][1]

    def test_cost_tracker_monthly_estimate(self):
        """REQ-OBS-003: Cost tracker estimates monthly costs."""
        tracker = CostTracker()

        # Record $0.10 in 1 day
        tracker.total_cost = 0.10

        monthly = tracker.estimate_monthly_cost(days_of_data=1)

        assert monthly == pytest.approx(3.0, abs=0.01)  # 0.10 * 30 = 3.0

    def test_cost_tracker_summary(self):
        """REQ-OBS-003: Cost tracker provides summary."""
        tracker = CostTracker()

        tracker.record_cost("research", "openai", "gpt-4o", 1000, 500)

        summary = tracker.summary()

        assert "total_cost_usd" in summary
        assert "by_agent" in summary
        assert "by_provider" in summary
        assert "by_model" in summary


class TestSpanLifecycle:
    """Test span lifecycle and metadata."""

    def test_span_to_dict(self):
        """Span converts to dictionary for serialization."""
        span = Span(
            span_id="span_123",
            trace_id="trace_456",
            parent_id=None,
            name="test_op",
            start_time=datetime.now(),
            metadata={"key": "value"}
        )
        span.finish()

        data = span.to_dict()

        assert data["span_id"] == "span_123"
        assert data["trace_id"] == "trace_456"
        assert data["name"] == "test_op"
        assert data["duration_ms"] is not None
        assert data["metadata"] == {"key": "value"}


class TestTraceLifecycle:
    """Test trace lifecycle and methods."""

    def test_trace_to_dict(self):
        """Trace converts to dictionary for serialization."""
        trace = Trace(
            trace_id="trace_123",
            query="test query",
            agent_name="research",
            method="keyword"
        )
        trace.finish(success=True)

        data = trace.to_dict()

        assert data["trace_id"] == "trace_123"
        assert data["query"] == "test query"
        assert data["agent_name"] == "research"
        assert data["method"] == "keyword"
        assert data["success"] is True
        assert data["duration_ms"] is not None
