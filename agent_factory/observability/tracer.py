"""
Request Tracer - End-to-end tracing for agent requests

Provides distributed tracing capabilities for debugging and monitoring
agent requests through the entire execution pipeline.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Span:
    """
    Single operation in a trace.

    Represents a unit of work (agent execution, tool call, etc.)
    with timing information and metadata.

    Attributes:
        span_id: Unique identifier for this span
        trace_id: ID of the parent trace
        parent_id: ID of parent span (for nested operations)
        name: Operation name (agent_start, tool_call, etc.)
        start_time: When the span started
        end_time: When the span finished (None if still running)
        duration_ms: Duration in milliseconds
        metadata: Additional context data

    Example:
        >>> span = Span(
        ...     span_id="span_abc",
        ...     trace_id="trace_123",
        ...     parent_id=None,
        ...     name="agent_start",
        ...     start_time=datetime.now(),
        ...     metadata={"agent": "research"}
        ... )
        >>> span.finish()
        >>> print(span.duration_ms)
    """

    span_id: str
    trace_id: str
    parent_id: Optional[str]
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self) -> None:
        """Mark span as complete and calculate duration."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for serialization."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }


@dataclass
class Trace:
    """
    Complete request trace with all spans.

    Represents the entire lifecycle of a request from input to output,
    including all sub-operations (spans).

    Attributes:
        trace_id: Unique identifier for this trace
        query: User query that initiated the request
        agent_name: Name of agent that handled the request
        method: Routing method used (keyword, llm, fallback)
        start_time: When the request started
        end_time: When the request finished
        duration_ms: Total request duration
        success: Whether request succeeded
        error: Error message if failed
        spans: List of all operations in this trace
        metadata: Additional context (model, provider, etc.)

    Example:
        >>> trace = Trace(
        ...     trace_id="trace_123",
        ...     query="What is AI?",
        ...     agent_name="research",
        ...     method="keyword",
        ...     start_time=datetime.now()
        ... )
        >>> trace.spans.append(span)
        >>> trace.finish(success=True)
    """

    trace_id: str
    query: str
    agent_name: str = ""
    method: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    spans: List[Span] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool, error: Optional[str] = None) -> None:
        """Mark trace as complete."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for serialization."""
        return {
            "trace_id": self.trace_id,
            "query": self.query,
            "agent_name": self.agent_name,
            "method": self.method,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "spans": [span.to_dict() for span in self.spans],
            "metadata": self.metadata
        }

    @property
    def latency_p95(self) -> float:
        """Calculate 95th percentile latency of spans."""
        durations = [s.duration_ms for s in self.spans if s.duration_ms is not None]
        if not durations:
            return 0.0
        sorted_durations = sorted(durations)
        idx = int(len(sorted_durations) * 0.95)
        return sorted_durations[min(idx, len(sorted_durations) - 1)]


class Tracer:
    """
    Request tracer with span tracking.

    Manages distributed tracing across agent requests, providing
    end-to-end visibility into request execution.

    Usage:
        >>> tracer = Tracer()
        >>> trace_id = tracer.start_trace("What is AI?")
        >>> span = tracer.start_span("agent_start", agent="research")
        >>> # ... do work ...
        >>> span.finish()
        >>> tracer.finish_trace(success=True)
        >>> trace = tracer.get_trace(trace_id)
    """

    def __init__(self):
        """Initialize tracer with empty trace storage."""
        self._traces: Dict[str, Trace] = {}
        self._current_trace: Optional[str] = None
        self._active_spans: Dict[str, Span] = {}

    def start_trace(
        self,
        query: str,
        **metadata
    ) -> str:
        """
        Start a new trace.

        Args:
            query: User query that initiated the request
            **metadata: Additional context to store

        Returns:
            trace_id: Unique identifier for this trace

        Example:
            >>> trace_id = tracer.start_trace("What is AI?", user="alice")
        """
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        trace = Trace(
            trace_id=trace_id,
            query=query,
            start_time=datetime.now(),
            metadata=metadata
        )
        self._traces[trace_id] = trace
        self._current_trace = trace_id
        return trace_id

    def start_span(
        self,
        name: str,
        parent_id: Optional[str] = None,
        **metadata
    ) -> Span:
        """
        Start a new span in the current trace.

        Args:
            name: Operation name (agent_start, tool_call, etc.)
            parent_id: Optional parent span ID for nested operations
            **metadata: Additional context

        Returns:
            Span: The created span

        Example:
            >>> span = tracer.start_span("tool_call", tool_name="search")
            >>> # ... execute tool ...
            >>> span.finish()
        """
        if not self._current_trace:
            raise RuntimeError("No active trace. Call start_trace() first.")

        span = Span(
            span_id=f"span_{uuid.uuid4().hex[:8]}",
            trace_id=self._current_trace,
            parent_id=parent_id,
            name=name,
            start_time=datetime.now(),
            metadata=metadata
        )

        self._traces[self._current_trace].spans.append(span)
        self._active_spans[span.span_id] = span

        return span

    def finish_trace(
        self,
        success: bool,
        error: Optional[str] = None,
        **metadata
    ) -> None:
        """
        Mark the current trace as complete.

        Args:
            success: Whether the request succeeded
            error: Error message if failed
            **metadata: Additional final metadata

        Example:
            >>> tracer.finish_trace(success=True)
        """
        if not self._current_trace:
            return

        trace = self._traces[self._current_trace]
        trace.finish(success=success, error=error)
        trace.metadata.update(metadata)

        # Clear current trace
        self._current_trace = None

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """
        Retrieve a trace by ID.

        Args:
            trace_id: Trace identifier

        Returns:
            Trace or None if not found

        Example:
            >>> trace = tracer.get_trace("trace_abc123")
            >>> print(trace.duration_ms)
        """
        return self._traces.get(trace_id)

    def get_all_traces(self) -> List[Trace]:
        """
        Get all traces.

        Returns:
            List of all traces

        Example:
            >>> traces = tracer.get_all_traces()
            >>> successful = [t for t in traces if t.success]
        """
        return list(self._traces.values())

    def get_current_trace_id(self) -> Optional[str]:
        """Get the current active trace ID."""
        return self._current_trace

    def clear_traces(self) -> None:
        """Clear all stored traces (useful for testing)."""
        self._traces.clear()
        self._current_trace = None
        self._active_spans.clear()

    def export_traces(self) -> List[Dict[str, Any]]:
        """
        Export all traces as dictionaries.

        Returns:
            List of trace dictionaries

        Example:
            >>> import json
            >>> traces_json = json.dumps(tracer.export_traces(), indent=2)
        """
        return [trace.to_dict() for trace in self._traces.values()]
