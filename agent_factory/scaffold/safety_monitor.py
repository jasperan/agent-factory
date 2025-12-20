"""
Safety Monitor for SCAFFOLD orchestrator sessions.

Enforces hard limits on API costs, execution time, and consecutive failures
to prevent runaway costs and infinite loops.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, Optional


@dataclass
class SafetyLimits:
    """Configurable safety limits for SCAFFOLD sessions."""
    max_cost: float = 5.0  # Maximum total cost in USD
    max_time_hours: float = 4.0  # Maximum session duration in hours
    max_consecutive_failures: int = 3  # Maximum consecutive task failures


@dataclass
class SafetyState:
    """Current safety state for a SCAFFOLD session."""
    total_cost: float = 0.0
    consecutive_failures: int = 0
    start_time: Optional[datetime] = None

    def elapsed_hours(self) -> float:
        """Calculate elapsed time in hours."""
        if self.start_time is None:
            return 0.0
        elapsed = datetime.utcnow() - self.start_time
        return elapsed.total_seconds() / 3600.0


class SafetyMonitor:
    """
    Monitors API costs, execution time, and consecutive failures.

    Enforces hard limits to prevent runaway costs and infinite loops.
    Each SCAFFOLD session should create one SafetyMonitor instance.
    """

    def __init__(
        self,
        max_cost: float = 5.0,
        max_time_hours: float = 4.0,
        max_consecutive_failures: int = 3
    ):
        """
        Initialize safety monitor.

        Args:
            max_cost: Maximum total cost in USD (default: $5)
            max_time_hours: Maximum session duration in hours (default: 4)
            max_consecutive_failures: Maximum consecutive task failures (default: 3)
        """
        self.limits = SafetyLimits(
            max_cost=max_cost,
            max_time_hours=max_time_hours,
            max_consecutive_failures=max_consecutive_failures
        )
        self.state = SafetyState(start_time=datetime.utcnow())

    def check_limits(self) -> Tuple[bool, str]:
        """
        Check if current state exceeds safety limits.

        Returns:
            Tuple of (allowed, reason):
                - allowed: True if session can continue, False if limits exceeded
                - reason: Empty string if allowed, otherwise reason for abort
        """
        # Check cost limit
        if self.state.total_cost >= self.limits.max_cost:
            return (
                False,
                f"Cost limit exceeded: ${self.state.total_cost:.2f} >= ${self.limits.max_cost:.2f}"
            )

        # Check time limit
        elapsed_hours = self.state.elapsed_hours()
        if elapsed_hours >= self.limits.max_time_hours:
            return (
                False,
                f"Time limit exceeded: {elapsed_hours:.2f}h >= {self.limits.max_time_hours:.2f}h"
            )

        # Check consecutive failures limit
        if self.state.consecutive_failures >= self.limits.max_consecutive_failures:
            return (
                False,
                f"Consecutive failures limit exceeded: {self.state.consecutive_failures} >= {self.limits.max_consecutive_failures}"
            )

        return (True, "")

    def record_cost(self, cost: float):
        """
        Record API cost from a task execution.

        Args:
            cost: Cost in USD to add to total
        """
        self.state.total_cost += cost

    def record_success(self, cost: float = 0.0):
        """
        Record successful task execution.

        Resets consecutive failures counter and optionally records cost.

        Args:
            cost: Optional cost in USD to add to total (default: 0.0)
        """
        self.state.consecutive_failures = 0
        if cost > 0:
            self.record_cost(cost)

    def record_failure(self):
        """
        Record failed task execution.

        Increments consecutive failures counter.
        """
        self.state.consecutive_failures += 1

    def reset_consecutive_failures(self):
        """Reset consecutive failures counter to zero."""
        self.state.consecutive_failures = 0

    def get_state_summary(self) -> dict:
        """
        Get current safety state as a dictionary.

        Returns:
            Dictionary with total_cost, elapsed_hours, consecutive_failures
        """
        return {
            "total_cost": self.state.total_cost,
            "elapsed_hours": self.state.elapsed_hours(),
            "consecutive_failures": self.state.consecutive_failures
        }

    def get_limits_summary(self) -> dict:
        """
        Get configured limits as a dictionary.

        Returns:
            Dictionary with max_cost, max_time_hours, max_consecutive_failures
        """
        return {
            "max_cost": self.limits.max_cost,
            "max_time_hours": self.limits.max_time_hours,
            "max_consecutive_failures": self.limits.max_consecutive_failures
        }

    def get_remaining_budget(self) -> dict:
        """
        Calculate remaining budget for cost, time, and failures.

        Returns:
            Dictionary with remaining_cost, remaining_hours, remaining_failures
        """
        return {
            "remaining_cost": max(0, self.limits.max_cost - self.state.total_cost),
            "remaining_hours": max(0, self.limits.max_time_hours - self.state.elapsed_hours()),
            "remaining_failures": max(0, self.limits.max_consecutive_failures - self.state.consecutive_failures)
        }
