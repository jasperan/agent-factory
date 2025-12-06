"""
Performance Metrics - Track and analyze agent performance

Provides comprehensive metrics collection and analysis for monitoring
agent performance, success rates, and resource usage.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class Metrics:
    """
    Performance metrics aggregator.

    Tracks key performance indicators across all agent requests:
    - Request counts and success rates
    - Latency percentiles
    - Token usage
    - Per-agent breakdowns

    Attributes:
        total_requests: Total number of requests processed
        successful_requests: Number of successful requests
        failed_requests: Number of failed requests
        latencies: List of all request latencies (ms)
        total_tokens: Total tokens used across all requests
        prompt_tokens: Total prompt tokens
        completion_tokens: Total completion tokens
        agent_requests: Request count by agent name
        agent_latencies: Latency list by agent name
        agent_successes: Success count by agent name
        agent_failures: Failure count by agent name
        error_counts: Count by error type

    Example:
        >>> metrics = Metrics()
        >>> metrics.record_request(
        ...     agent_name="research",
        ...     duration_ms=150.5,
        ...     success=True,
        ...     tokens={"prompt": 100, "completion": 50, "total": 150}
        ... )
        >>> print(f"Success rate: {metrics.success_rate:.1f}%")
        >>> print(f"Avg latency: {metrics.avg_latency:.2f}ms")
    """

    # Counters
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Latency tracking (milliseconds)
    latencies: List[float] = field(default_factory=list)

    # Token usage
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    # Per-agent metrics
    agent_requests: Dict[str, int] = field(default_factory=dict)
    agent_latencies: Dict[str, List[float]] = field(default_factory=dict)
    agent_successes: Dict[str, int] = field(default_factory=dict)
    agent_failures: Dict[str, int] = field(default_factory=dict)

    # Error tracking
    error_counts: Dict[str, int] = field(default_factory=dict)

    def record_request(
        self,
        agent_name: str,
        duration_ms: float,
        success: bool,
        tokens: Optional[Dict[str, int]] = None,
        error_type: Optional[str] = None
    ) -> None:
        """
        Record a request's metrics.

        Args:
            agent_name: Name of agent that handled the request
            duration_ms: Request duration in milliseconds
            success: Whether the request succeeded
            tokens: Optional token usage dict with keys: prompt, completion, total
            error_type: Optional error category if failed

        Example:
            >>> metrics.record_request(
            ...     agent_name="coding",
            ...     duration_ms=250.0,
            ...     success=True,
            ...     tokens={"prompt": 200, "completion": 100, "total": 300}
            ... )
        """
        # Overall counters
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        # Latency
        self.latencies.append(duration_ms)

        # Per-agent metrics
        self.agent_requests[agent_name] = self.agent_requests.get(agent_name, 0) + 1

        if agent_name not in self.agent_latencies:
            self.agent_latencies[agent_name] = []
        self.agent_latencies[agent_name].append(duration_ms)

        if success:
            self.agent_successes[agent_name] = self.agent_successes.get(agent_name, 0) + 1
        else:
            self.agent_failures[agent_name] = self.agent_failures.get(agent_name, 0) + 1

        # Token usage
        if tokens:
            self.total_tokens += tokens.get("total", 0)
            self.prompt_tokens += tokens.get("prompt", 0)
            self.completion_tokens += tokens.get("completion", 0)

        # Error tracking
        if error_type:
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    @property
    def success_rate(self) -> float:
        """
        Calculate success rate percentage.

        Returns:
            Success rate as percentage (0.0-100.0)

        Example:
            >>> metrics.success_rate
            95.5
        """
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    @property
    def avg_latency(self) -> float:
        """
        Calculate average latency.

        Returns:
            Average latency in milliseconds

        Example:
            >>> metrics.avg_latency
            125.5
        """
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    @property
    def p50_latency(self) -> float:
        """Calculate 50th percentile (median) latency."""
        return self._percentile(0.50)

    @property
    def p95_latency(self) -> float:
        """
        Calculate 95th percentile latency.

        Returns:
            95th percentile latency in milliseconds

        Example:
            >>> metrics.p95_latency
            450.2
        """
        return self._percentile(0.95)

    @property
    def p99_latency(self) -> float:
        """Calculate 99th percentile latency."""
        return self._percentile(0.99)

    def _percentile(self, p: float) -> float:
        """Calculate percentile of latencies."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * p)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with agent-specific metrics

        Example:
            >>> stats = metrics.get_agent_stats("research")
            >>> print(f"Requests: {stats['requests']}")
            >>> print(f"Success rate: {stats['success_rate']}")
        """
        if agent_name not in self.agent_requests:
            return {}

        latencies = self.agent_latencies.get(agent_name, [])
        requests = self.agent_requests[agent_name]
        successes = self.agent_successes.get(agent_name, 0)
        failures = self.agent_failures.get(agent_name, 0)

        return {
            "requests": requests,
            "successes": successes,
            "failures": failures,
            "success_rate": (successes / requests * 100) if requests > 0 else 0.0,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
            "p95_latency_ms": round(
                sorted(latencies)[int(len(latencies) * 0.95)], 2
            ) if latencies else 0.0
        }

    def summary(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary.

        Returns:
            Dictionary with all metrics

        Example:
            >>> summary = metrics.summary()
            >>> print(f"Total requests: {summary['total_requests']}")
            >>> print(f"Success rate: {summary['success_rate']}")
            >>> for agent, stats in summary['agents'].items():
            ...     print(f"{agent}: {stats['requests']} requests")
        """
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{self.success_rate:.1f}%",
            "failure_rate": f"{self.failure_rate:.1f}%",
            "latency": {
                "avg_ms": round(self.avg_latency, 2),
                "p50_ms": round(self.p50_latency, 2),
                "p95_ms": round(self.p95_latency, 2),
                "p99_ms": round(self.p99_latency, 2)
            },
            "tokens": {
                "total": self.total_tokens,
                "prompt": self.prompt_tokens,
                "completion": self.completion_tokens
            },
            "agents": {
                name: self.get_agent_stats(name)
                for name in sorted(self.agent_requests.keys())
            },
            "errors": dict(sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )) if self.error_counts else {}
        }

    def reset(self) -> None:
        """
        Reset all metrics to zero.

        Useful for starting a new measurement period.

        Example:
            >>> metrics.reset()
            >>> metrics.total_requests
            0
        """
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.latencies.clear()
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.agent_requests.clear()
        self.agent_latencies.clear()
        self.agent_successes.clear()
        self.agent_failures.clear()
        self.error_counts.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": self.summary()
        }
