"""
Tests for SCAFFOLD SafetyMonitor.

Comprehensive test suite covering all safety monitoring functionality.
"""

import pytest
import time
from datetime import datetime, timedelta
from agent_factory.scaffold.safety_monitor import (
    SafetyMonitor,
    SafetyLimits,
    SafetyState
)


class TestSafetyLimits:
    """Test SafetyLimits dataclass."""

    def test_safety_limits_defaults(self):
        """Test default safety limits."""
        limits = SafetyLimits()

        assert limits.max_cost == 5.0
        assert limits.max_time_hours == 4.0
        assert limits.max_consecutive_failures == 3

    def test_safety_limits_custom(self):
        """Test custom safety limits."""
        limits = SafetyLimits(
            max_cost=10.0,
            max_time_hours=8.0,
            max_consecutive_failures=5
        )

        assert limits.max_cost == 10.0
        assert limits.max_time_hours == 8.0
        assert limits.max_consecutive_failures == 5


class TestSafetyState:
    """Test SafetyState dataclass."""

    def test_safety_state_defaults(self):
        """Test default safety state."""
        state = SafetyState()

        assert state.total_cost == 0.0
        assert state.consecutive_failures == 0
        assert state.start_time is None

    def test_safety_state_elapsed_hours_no_start_time(self):
        """Test elapsed_hours returns 0 when start_time is None."""
        state = SafetyState()
        assert state.elapsed_hours() == 0.0

    def test_safety_state_elapsed_hours(self):
        """Test elapsed_hours calculation."""
        now = datetime.utcnow()
        past = now - timedelta(hours=2.5)
        state = SafetyState(start_time=past)

        elapsed = state.elapsed_hours()
        # Allow 0.1 hour tolerance for test execution time
        assert 2.4 <= elapsed <= 2.6


class TestSafetyMonitorInitialization:
    """Test SafetyMonitor initialization."""

    def test_monitor_initialization_defaults(self):
        """Test creating monitor with default limits."""
        monitor = SafetyMonitor()

        assert monitor.limits.max_cost == 5.0
        assert monitor.limits.max_time_hours == 4.0
        assert monitor.limits.max_consecutive_failures == 3
        assert monitor.state.total_cost == 0.0
        assert monitor.state.consecutive_failures == 0
        assert monitor.state.start_time is not None

    def test_monitor_initialization_custom(self):
        """Test creating monitor with custom limits."""
        monitor = SafetyMonitor(
            max_cost=10.0,
            max_time_hours=8.0,
            max_consecutive_failures=5
        )

        assert monitor.limits.max_cost == 10.0
        assert monitor.limits.max_time_hours == 8.0
        assert monitor.limits.max_consecutive_failures == 5


class TestCheckLimits:
    """Test check_limits() method."""

    def test_check_limits_within_all_limits(self):
        """Test check_limits passes when within all limits."""
        monitor = SafetyMonitor()

        allowed, reason = monitor.check_limits()

        assert allowed is True
        assert reason == ""

    def test_check_limits_cost_exceeded(self):
        """Test check_limits fails when cost limit exceeded."""
        monitor = SafetyMonitor(max_cost=1.0)
        monitor.record_cost(1.5)

        allowed, reason = monitor.check_limits()

        assert allowed is False
        assert "Cost limit exceeded" in reason
        assert "$1.50" in reason
        assert "$1.00" in reason

    def test_check_limits_cost_exactly_at_limit(self):
        """Test check_limits fails when cost exactly at limit."""
        monitor = SafetyMonitor(max_cost=5.0)
        monitor.record_cost(5.0)

        allowed, reason = monitor.check_limits()

        assert allowed is False
        assert "Cost limit exceeded" in reason

    def test_check_limits_time_exceeded(self):
        """Test check_limits fails when time limit exceeded."""
        # Manually set start time to 5 hours ago
        monitor = SafetyMonitor(max_time_hours=4.0)
        monitor.state.start_time = datetime.utcnow() - timedelta(hours=5)

        allowed, reason = monitor.check_limits()

        assert allowed is False
        assert "Time limit exceeded" in reason

    def test_check_limits_consecutive_failures_exceeded(self):
        """Test check_limits fails when consecutive failures limit exceeded."""
        monitor = SafetyMonitor(max_consecutive_failures=3)
        monitor.record_failure()
        monitor.record_failure()
        monitor.record_failure()

        allowed, reason = monitor.check_limits()

        assert allowed is False
        assert "Consecutive failures limit exceeded" in reason
        assert "3 >= 3" in reason

    def test_check_limits_multiple_exceeded(self):
        """Test check_limits fails on first exceeded limit (cost checked first)."""
        monitor = SafetyMonitor(
            max_cost=1.0,
            max_time_hours=0.001,
            max_consecutive_failures=1
        )
        monitor.record_cost(1.5)
        monitor.record_failure()

        allowed, reason = monitor.check_limits()

        assert allowed is False
        # Cost is checked first
        assert "Cost limit exceeded" in reason


class TestRecordCost:
    """Test record_cost() method."""

    def test_record_cost_single(self):
        """Test recording a single cost."""
        monitor = SafetyMonitor()
        monitor.record_cost(0.25)

        assert monitor.state.total_cost == 0.25

    def test_record_cost_multiple(self):
        """Test recording multiple costs accumulates."""
        monitor = SafetyMonitor()
        monitor.record_cost(0.10)
        monitor.record_cost(0.15)
        monitor.record_cost(0.20)

        assert monitor.state.total_cost == 0.45

    def test_record_cost_zero(self):
        """Test recording zero cost."""
        monitor = SafetyMonitor()
        monitor.record_cost(0.0)

        assert monitor.state.total_cost == 0.0


class TestRecordSuccess:
    """Test record_success() method."""

    def test_record_success_resets_failures(self):
        """Test record_success resets consecutive failures."""
        monitor = SafetyMonitor()
        monitor.record_failure()
        monitor.record_failure()
        assert monitor.state.consecutive_failures == 2

        monitor.record_success()

        assert monitor.state.consecutive_failures == 0

    def test_record_success_with_cost(self):
        """Test record_success records cost and resets failures."""
        monitor = SafetyMonitor()
        monitor.record_failure()

        monitor.record_success(cost=0.25)

        assert monitor.state.consecutive_failures == 0
        assert monitor.state.total_cost == 0.25

    def test_record_success_without_cost(self):
        """Test record_success without cost."""
        monitor = SafetyMonitor()
        monitor.record_success()

        assert monitor.state.total_cost == 0.0
        assert monitor.state.consecutive_failures == 0


class TestRecordFailure:
    """Test record_failure() method."""

    def test_record_failure_single(self):
        """Test recording a single failure."""
        monitor = SafetyMonitor()
        monitor.record_failure()

        assert monitor.state.consecutive_failures == 1

    def test_record_failure_multiple(self):
        """Test recording multiple failures accumulates."""
        monitor = SafetyMonitor()
        monitor.record_failure()
        monitor.record_failure()
        monitor.record_failure()

        assert monitor.state.consecutive_failures == 3

    def test_record_failure_after_success(self):
        """Test failure after success starts counting again."""
        monitor = SafetyMonitor()
        monitor.record_failure()
        monitor.record_failure()
        monitor.record_success()
        monitor.record_failure()

        assert monitor.state.consecutive_failures == 1


class TestResetConsecutiveFailures:
    """Test reset_consecutive_failures() method."""

    def test_reset_consecutive_failures(self):
        """Test resetting consecutive failures."""
        monitor = SafetyMonitor()
        monitor.record_failure()
        monitor.record_failure()
        assert monitor.state.consecutive_failures == 2

        monitor.reset_consecutive_failures()

        assert monitor.state.consecutive_failures == 0

    def test_reset_consecutive_failures_already_zero(self):
        """Test resetting when already zero."""
        monitor = SafetyMonitor()
        monitor.reset_consecutive_failures()

        assert monitor.state.consecutive_failures == 0


class TestGetStateSummary:
    """Test get_state_summary() method."""

    def test_get_state_summary(self):
        """Test getting state summary."""
        monitor = SafetyMonitor()
        monitor.record_cost(0.50)
        monitor.record_failure()
        monitor.record_failure()

        summary = monitor.get_state_summary()

        assert summary["total_cost"] == 0.50
        assert summary["consecutive_failures"] == 2
        assert "elapsed_hours" in summary
        assert summary["elapsed_hours"] >= 0


class TestGetLimitsSummary:
    """Test get_limits_summary() method."""

    def test_get_limits_summary(self):
        """Test getting limits summary."""
        monitor = SafetyMonitor(
            max_cost=10.0,
            max_time_hours=8.0,
            max_consecutive_failures=5
        )

        summary = monitor.get_limits_summary()

        assert summary["max_cost"] == 10.0
        assert summary["max_time_hours"] == 8.0
        assert summary["max_consecutive_failures"] == 5


class TestGetRemainingBudget:
    """Test get_remaining_budget() method."""

    def test_get_remaining_budget_full(self):
        """Test remaining budget when nothing consumed."""
        monitor = SafetyMonitor(
            max_cost=5.0,
            max_time_hours=4.0,
            max_consecutive_failures=3
        )

        budget = monitor.get_remaining_budget()

        assert budget["remaining_cost"] == 5.0
        assert budget["remaining_hours"] >= 3.99  # Allow small time elapsed
        assert budget["remaining_failures"] == 3

    def test_get_remaining_budget_partial(self):
        """Test remaining budget after partial consumption."""
        monitor = SafetyMonitor(
            max_cost=5.0,
            max_time_hours=4.0,
            max_consecutive_failures=3
        )
        monitor.record_cost(2.5)
        monitor.record_failure()

        budget = monitor.get_remaining_budget()

        assert budget["remaining_cost"] == 2.5
        assert budget["remaining_failures"] == 2

    def test_get_remaining_budget_exceeded(self):
        """Test remaining budget shows zero when exceeded."""
        monitor = SafetyMonitor(max_cost=1.0)
        monitor.record_cost(1.5)

        budget = monitor.get_remaining_budget()

        assert budget["remaining_cost"] == 0.0


class TestCircuitBreakerBehavior:
    """Test circuit breaker behavior."""

    def test_circuit_breaker_three_failures(self):
        """Test circuit breaker trips after 3 consecutive failures."""
        monitor = SafetyMonitor(max_consecutive_failures=3)

        # First two failures - still allowed
        monitor.record_failure()
        assert monitor.check_limits()[0] is True

        monitor.record_failure()
        assert monitor.check_limits()[0] is True

        # Third failure - circuit breaker trips
        monitor.record_failure()
        allowed, reason = monitor.check_limits()
        assert allowed is False
        assert "Consecutive failures" in reason

    def test_circuit_breaker_reset_on_success(self):
        """Test circuit breaker resets on success."""
        monitor = SafetyMonitor(max_consecutive_failures=3)

        monitor.record_failure()
        monitor.record_failure()
        monitor.record_success()  # Reset
        monitor.record_failure()
        monitor.record_failure()

        # Only 2 consecutive failures, should still be allowed
        assert monitor.check_limits()[0] is True


class TestIntegration:
    """Integration tests for full session workflow."""

    def test_full_session_within_limits(self):
        """Test full session that stays within all limits."""
        monitor = SafetyMonitor(
            max_cost=5.0,
            max_time_hours=4.0,
            max_consecutive_failures=3
        )

        # Execute 5 tasks successfully
        for i in range(5):
            allowed, _ = monitor.check_limits()
            assert allowed is True

            monitor.record_success(cost=0.10)

        # Final check
        allowed, _ = monitor.check_limits()
        assert allowed is True
        assert monitor.state.total_cost == 0.50
        assert monitor.state.consecutive_failures == 0

    def test_full_session_cost_abort(self):
        """Test session aborts when cost limit exceeded."""
        monitor = SafetyMonitor(max_cost=1.0)

        # Execute tasks until cost limit
        for i in range(5):
            allowed, reason = monitor.check_limits()
            if not allowed:
                assert "Cost limit exceeded" in reason
                break
            monitor.record_success(cost=0.25)
        else:
            pytest.fail("Should have aborted due to cost limit")

    def test_full_session_failure_abort(self):
        """Test session aborts after 3 consecutive failures."""
        monitor = SafetyMonitor(max_consecutive_failures=3)

        # Execute tasks with failures
        for i in range(5):
            allowed, reason = monitor.check_limits()
            if not allowed:
                assert "Consecutive failures" in reason
                assert i == 3  # Should abort on 4th iteration (after 3 failures)
                break
            monitor.record_failure()
        else:
            pytest.fail("Should have aborted due to consecutive failures")

    def test_full_session_mixed_results(self):
        """Test session with mixed success/failure results."""
        monitor = SafetyMonitor(
            max_cost=5.0,
            max_consecutive_failures=3
        )

        # Success
        monitor.record_success(cost=0.25)
        assert monitor.check_limits()[0] is True

        # Failure (1 consecutive)
        monitor.record_failure()
        assert monitor.check_limits()[0] is True

        # Failure (2 consecutive)
        monitor.record_failure()
        assert monitor.check_limits()[0] is True

        # Success (resets consecutive failures)
        monitor.record_success(cost=0.30)
        assert monitor.check_limits()[0] is True
        assert monitor.state.consecutive_failures == 0

        # Two more failures (2 consecutive)
        monitor.record_failure()
        monitor.record_failure()
        assert monitor.check_limits()[0] is True

        # Final state
        assert monitor.state.total_cost == 0.55
        assert monitor.state.consecutive_failures == 2

    def test_get_remaining_budget_tracking(self):
        """Test remaining budget decreases as session progresses."""
        monitor = SafetyMonitor(
            max_cost=5.0,
            max_consecutive_failures=3
        )

        # Initial budget
        budget = monitor.get_remaining_budget()
        assert budget["remaining_cost"] == 5.0
        assert budget["remaining_failures"] == 3

        # After task 1
        monitor.record_success(cost=1.0)
        budget = monitor.get_remaining_budget()
        assert budget["remaining_cost"] == 4.0
        assert budget["remaining_failures"] == 3

        # After task 2 (failure)
        monitor.record_failure()
        budget = monitor.get_remaining_budget()
        assert budget["remaining_cost"] == 4.0
        assert budget["remaining_failures"] == 2

        # After task 3 (success with cost)
        monitor.record_success(cost=2.0)
        budget = monitor.get_remaining_budget()
        assert budget["remaining_cost"] == 2.0
        assert budget["remaining_failures"] == 3  # Reset on success
