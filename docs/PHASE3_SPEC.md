# PHASE3_SPEC.md - Enhanced Observability

## Overview

Build comprehensive monitoring and observability for agents, enabling production debugging, performance optimization, and cost tracking.

**Success:** View agent performance dashboard showing latency, token usage, success rates, and trace individual requests end-to-end.

---

## Why Observability Matters

Without observability:
- Can't debug production failures
- Don't know which agents are slow/expensive
- Can't optimize for cost or performance
- No visibility into user experience

With observability:
- Trace every request from input to output
- Identify performance bottlenecks
- Track API costs in real-time
- Debug failures with full context
- Optimize agent configurations based on data

---

## Requirements

### REQ-OBS-001: Request Tracing
**Priority:** HIGH
**Description:** Trace every request end-to-end with unique ID

**Acceptance Criteria:**
- Each `orchestrator.route()` call gets unique trace_id
- Trace includes: timestamp, query, agent_name, method, duration_ms
- Trace persists in history for debugging
- Can retrieve trace by ID

**Implementation:**
```python
# Auto-generated trace_id for each request
result = orchestrator.route("What is AI?")
# result.trace_id = "trace_abc123"
# result.spans = [agent_start, tool_call, agent_end]
```

---

### REQ-OBS-002: Performance Metrics
**Priority:** HIGH
**Description:** Track key performance indicators

**Metrics to Track:**
- Request latency (p50, p95, p99)
- Token usage (prompt + completion)
- API call counts
- Success/failure rates
- Tool execution time
- Agent selection accuracy

**Acceptance Criteria:**
- Metrics collected automatically
- Queryable by time range, agent, or trace_id
- Exportable to CSV/JSON
- Real-time aggregation

---

### REQ-OBS-003: Cost Tracking
**Priority:** MEDIUM
**Description:** Track API costs per request and agent

**Acceptance Criteria:**
- Track tokens by provider (OpenAI, Anthropic, Google)
- Calculate cost using provider pricing
- Aggregate costs by agent, time period
- Exportable cost reports

**Pricing Reference:**
```python
PRICING = {
    "openai": {
        "gpt-4o": {"input": 0.03, "output": 0.06},  # per 1K tokens
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
    },
    "anthropic": {
        "claude-sonnet-4": {"input": 0.003, "output": 0.015}
    }
}
```

---

### REQ-OBS-004: Error Tracking
**Priority:** HIGH
**Description:** Capture and categorize errors

**Error Categories:**
- llm_error: LLM provider failures
- tool_error: Tool execution failures
- validation_error: Schema validation failures
- timeout_error: Request timeouts
- rate_limit_error: API rate limits hit

**Acceptance Criteria:**
- All exceptions captured with full stack trace
- Error count by category and agent
- Error rate alerts (configurable threshold)

---

### REQ-OBS-005: LangSmith Integration
**Priority:** MEDIUM
**Description:** Optional LangSmith integration for advanced tracing

**Features:**
- Automatic trace upload to LangSmith
- Visual trace explorer
- Comparison of agent runs
- Feedback collection

**Acceptance Criteria:**
- `enable_langsmith=True` flag in factory
- Traces appear in LangSmith dashboard
- Works alongside local metrics

---

## Architecture

```
agent_factory/
+-- observability/
    +-- __init__.py
    +-- tracer.py          # Request tracing
    +-- metrics.py         # Performance metrics
    +-- cost_tracker.py    # Cost calculation
    +-- exporters.py       # Export to CSV/JSON/LangSmith
    +-- dashboard.py       # CLI dashboard (optional)
```

---

## Implementation Plan

### Step 1: Tracer Foundation
**File:** `agent_factory/observability/tracer.py`

```python
@dataclass
class Span:
    """Single operation in a trace."""
    span_id: str
    trace_id: str
    parent_id: Optional[str]
    name: str                    # "agent_start", "tool_call", etc.
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    metadata: Dict[str, Any]

    def finish(self):
        """Mark span as complete."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000


@dataclass
class Trace:
    """Complete request trace."""
    trace_id: str
    query: str
    agent_name: str
    method: str                  # "keyword", "llm", "fallback"
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    success: bool
    error: Optional[str]
    spans: List[Span]
    metadata: Dict[str, Any]

    @property
    def latency_p95(self) -> float:
        """95th percentile latency of spans."""
        durations = [s.duration_ms for s in self.spans if s.duration_ms]
        if not durations:
            return 0.0
        return sorted(durations)[int(len(durations) * 0.95)]


class Tracer:
    """Request tracer with span tracking."""

    def __init__(self):
        self._traces: Dict[str, Trace] = {}
        self._current_trace: Optional[str] = None

    def start_trace(self, query: str) -> str:
        """Start new trace, return trace_id."""
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        trace = Trace(
            trace_id=trace_id,
            query=query,
            agent_name="",
            method="",
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            success=False,
            error=None,
            spans=[],
            metadata={}
        )
        self._traces[trace_id] = trace
        self._current_trace = trace_id
        return trace_id

    def start_span(self, name: str, **metadata) -> Span:
        """Start new span in current trace."""
        span = Span(
            span_id=f"span_{uuid.uuid4().hex[:8]}",
            trace_id=self._current_trace,
            parent_id=None,  # Can add parent tracking later
            name=name,
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            metadata=metadata
        )
        self._traces[self._current_trace].spans.append(span)
        return span

    def finish_trace(self, success: bool, error: Optional[str] = None):
        """Mark trace as complete."""
        trace = self._traces[self._current_trace]
        trace.end_time = datetime.now()
        trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000
        trace.success = success
        trace.error = error

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Retrieve trace by ID."""
        return self._traces.get(trace_id)

    def get_all_traces(self) -> List[Trace]:
        """Get all traces."""
        return list(self._traces.values())
```

---

### Step 2: Metrics Collection
**File:** `agent_factory/observability/metrics.py`

```python
@dataclass
class Metrics:
    """Performance metrics aggregator."""

    # Counters
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Latency (milliseconds)
    latencies: List[float] = field(default_factory=list)

    # Token usage
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    # By agent
    agent_requests: Dict[str, int] = field(default_factory=dict)
    agent_latencies: Dict[str, List[float]] = field(default_factory=dict)

    def record_request(
        self,
        agent_name: str,
        duration_ms: float,
        success: bool,
        tokens: Optional[Dict[str, int]] = None
    ):
        """Record a request."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.latencies.append(duration_ms)

        # By agent
        self.agent_requests[agent_name] = self.agent_requests.get(agent_name, 0) + 1
        if agent_name not in self.agent_latencies:
            self.agent_latencies[agent_name] = []
        self.agent_latencies[agent_name].append(duration_ms)

        # Tokens
        if tokens:
            self.total_tokens += tokens.get("total", 0)
            self.prompt_tokens += tokens.get("prompt", 0)
            self.completion_tokens += tokens.get("completion", 0)

    @property
    def success_rate(self) -> float:
        """Success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def avg_latency(self) -> float:
        """Average latency in ms."""
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    @property
    def p95_latency(self) -> float:
        """95th percentile latency."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[idx]

    def summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "total_requests": self.total_requests,
            "success_rate": f"{self.success_rate:.1f}%",
            "avg_latency_ms": round(self.avg_latency, 2),
            "p95_latency_ms": round(self.p95_latency, 2),
            "total_tokens": self.total_tokens,
            "agents": {
                name: {
                    "requests": count,
                    "avg_latency_ms": round(
                        sum(self.agent_latencies[name]) / len(self.agent_latencies[name]),
                        2
                    )
                }
                for name, count in self.agent_requests.items()
            }
        }
```

---

### Step 3: Cost Tracker
**File:** `agent_factory/observability/cost_tracker.py`

```python
class CostTracker:
    """Track API costs across providers."""

    # Pricing per 1K tokens (USD)
    PRICING = {
        "openai": {
            "gpt-4o": {"input": 0.03, "output": 0.06},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
        },
        "anthropic": {
            "claude-sonnet-4": {"input": 0.003, "output": 0.015},
            "claude-haiku-3": {"input": 0.00025, "output": 0.00125}
        },
        "google": {
            "gemini-pro": {"input": 0.00025, "output": 0.0005}
        }
    }

    def __init__(self):
        self.total_cost = 0.0
        self.costs_by_agent: Dict[str, float] = {}
        self.costs_by_provider: Dict[str, float] = {}

    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for a request."""
        if provider not in self.PRICING:
            return 0.0

        model_pricing = self.PRICING[provider].get(model)
        if not model_pricing:
            return 0.0

        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]

        return input_cost + output_cost

    def record_cost(
        self,
        agent_name: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ):
        """Record cost for a request."""
        cost = self.calculate_cost(provider, model, prompt_tokens, completion_tokens)

        self.total_cost += cost
        self.costs_by_agent[agent_name] = self.costs_by_agent.get(agent_name, 0.0) + cost
        self.costs_by_provider[provider] = self.costs_by_provider.get(provider, 0.0) + cost

    def summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return {
            "total_cost_usd": round(self.total_cost, 4),
            "by_agent": {
                name: f"${cost:.4f}"
                for name, cost in sorted(
                    self.costs_by_agent.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            },
            "by_provider": {
                name: f"${cost:.4f}"
                for name, cost in self.costs_by_provider.items()
            }
        }
```

---

### Step 4: Integration with Orchestrator
**Update:** `agent_factory/core/orchestrator.py`

Add observability to the `route()` method:

```python
from agent_factory.observability import Tracer, Metrics, CostTracker

class AgentOrchestrator:
    def __init__(
        self,
        llm: BaseChatModel,
        event_bus: Optional[EventBus] = None,
        verbose: bool = False,
        enable_observability: bool = True  # NEW
    ):
        # ... existing code ...

        # Observability
        self.enable_observability = enable_observability
        if enable_observability:
            self.tracer = Tracer()
            self.metrics = Metrics()
            self.cost_tracker = CostTracker()

    def route(self, query: str) -> RouteResult:
        # Start trace
        if self.enable_observability:
            trace_id = self.tracer.start_trace(query)
            span = self.tracer.start_span("route", query=query)

        try:
            # ... existing routing logic ...

            # Record metrics
            if self.enable_observability:
                self.metrics.record_request(
                    agent_name=matched.name,
                    duration_ms=duration_ms,
                    success=True,
                    tokens=self._extract_tokens(response)
                )

                # Record cost
                agent_metadata = matched.agent.metadata
                self.cost_tracker.record_cost(
                    agent_name=matched.name,
                    provider=agent_metadata.get("llm_provider"),
                    model=agent_metadata.get("model"),
                    prompt_tokens=tokens.get("prompt", 0),
                    completion_tokens=tokens.get("completion", 0)
                )

                span.finish()
                self.tracer.finish_trace(success=True)

            # Add trace_id to result
            result.trace_id = trace_id if self.enable_observability else None
            return result

        except Exception as e:
            if self.enable_observability:
                self.tracer.finish_trace(success=False, error=str(e))
            raise
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_observability.py

def test_tracer_creates_trace():
    tracer = Tracer()
    trace_id = tracer.start_trace("test query")
    assert trace_id.startswith("trace_")

def test_metrics_calculates_success_rate():
    metrics = Metrics()
    metrics.record_request("agent1", 100, True)
    metrics.record_request("agent2", 150, False)
    assert metrics.success_rate == 50.0

def test_cost_tracker_calculates_openai_cost():
    tracker = CostTracker()
    cost = tracker.calculate_cost("openai", "gpt-4o", 1000, 500)
    # 1K * 0.03 + 0.5K * 0.06 = 0.03 + 0.03 = 0.06
    assert cost == 0.06
```

---

## Success Criteria

- [X] All requests traced with unique IDs
- [X] Metrics collected: latency, tokens, success rate
- [X] Cost tracking by agent and provider
- [X] Exportable to JSON/CSV
- [X] 15+ tests passing
- [X] Demo showing metrics dashboard
- [X] Performance overhead < 5ms per request
- [X] Backwards compatible (enable_observability flag)

---

## Phase 3 Dependencies

**Required from Phase 1 (Orchestration):**
- EventBus for emitting metric events
- RouteResult structure

**Required from Phase 2 (Structured Outputs):**
- Type-safe responses for metric extraction

---

## Future Enhancements

### Phase 3.1: Real-time Dashboard
- Live metrics visualization
- Alerts for high latency/errors
- Cost budget warnings

### Phase 3.2: LangSmith Integration
- Automatic trace upload
- Visual trace explorer
- Feedback collection

### Phase 3.3: Custom Exporters
- Prometheus metrics
- Datadog integration
- CloudWatch logs

---

**Estimated Time:** 4-6 hours
**Complexity:** Medium
**Value:** High - Production essential
