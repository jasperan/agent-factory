"""
Tests for MachineStateManager (Phase 2.3)

Unit tests (mocked):
- Circuit breaker state machine
- Change detection
- Subscriptions (filtering, parallel notification, error isolation)

Integration tests (real Factory.io):
- Real polling with Factory.io running
- State populated after poll cycle
- Multiple machines polling simultaneously
"""

import asyncio
import json
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from agent_factory.platform.config import MachineConfig, TagConfig
from agent_factory.platform.state.machine_state_manager import (
    CircuitBreaker,
    CircuitState,
    MachineState,
    MachineStateManager,
    Subscription,
)
from agent_factory.platform.types import IOTagStatus


# ============================================================================
# Mock Factory.io Tool
# ============================================================================


class MockFactoryIOTool:
    """Mock FactoryIOReadWriteTool for testing."""

    def __init__(self):
        self.call_count = 0
        self.fail_next_n_calls = 0
        self.tag_values = {
            "conveyor_running": False,
            "at_entry": True,
            "pusher_extend": False,
            "sensor_height": 10,
        }

    def _run(self, action, tag_names=None, tag_values=None):
        """Mock _run method."""
        self.call_count += 1

        # Simulate failures if requested
        if self.fail_next_n_calls > 0:
            self.fail_next_n_calls -= 1
            return "ERROR: Cannot connect to Factory.io at http://localhost:7410"

        if action == "read":
            if not tag_names:
                return json.dumps({"success": True, "values": {}})

            # Return current values for requested tags
            values = {
                tag: self.tag_values.get(tag, False) for tag in tag_names
            }
            return json.dumps({"success": True, "values": values})

        if action == "write":
            # Update mock values
            for tag_name, value in tag_values.items():
                self.tag_values[tag_name] = value
            return json.dumps({
                "success": True,
                "message": f"Successfully wrote {len(tag_values)} tag value(s)",
                "tags": list(tag_values.keys())
            })

        return "ERROR: Unknown action"

    def set_tag_value(self, tag_name: str, value):
        """Helper to change tag value (simulate Factory.io change)."""
        self.tag_values[tag_name] = value


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_machine_config():
    """Create sample machine configuration."""
    return MachineConfig(
        machine_id="test_sorting",
        scene_name="Test Sorting System",
        factory_io_url="http://localhost:7410",
        telegram_chat_id=-1001234567890,
        poll_interval_seconds=1,  # Fast for testing
        monitored_inputs=[
            TagConfig(tag="at_entry", label="Part at Entry", emoji="📦"),
            TagConfig(tag="sensor_height", label="Height Sensor", emoji="📏"),
        ],
        controllable_outputs=[
            TagConfig(tag="conveyor_running", label="Conveyor", emoji="▶️"),
            TagConfig(tag="pusher_extend", label="Pusher", emoji="👋"),
        ],
        emergency_stop_tags=["conveyor_running", "pusher_extend"],
    )


@pytest.fixture
def mock_tool():
    """Create mock Factory.io tool."""
    return MockFactoryIOTool()


# ============================================================================
# Unit Tests: Circuit Breaker
# ============================================================================


class TestCircuitBreaker:
    """Test circuit breaker state machine."""

    def test_initial_state_is_closed(self):
        """Circuit starts in CLOSED state."""
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_allows_poll_when_closed(self):
        """CLOSED state allows polling."""
        breaker = CircuitBreaker()
        assert breaker.should_attempt_poll() is True

    def test_opens_after_threshold_failures(self):
        """Circuit opens after failure_threshold consecutive failures."""
        breaker = CircuitBreaker(failure_threshold=3)

        breaker.record_failure()  # 1
        assert breaker.state == CircuitState.CLOSED

        breaker.record_failure()  # 2
        assert breaker.state == CircuitState.CLOSED

        breaker.record_failure()  # 3 - opens
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

    def test_blocks_poll_when_open(self):
        """OPEN state blocks polling until backoff expires."""
        breaker = CircuitBreaker(failure_threshold=1, backoff_base_seconds=10)

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        assert breaker.should_attempt_poll() is False

    def test_exponential_backoff(self):
        """Backoff doubles each time circuit opens."""
        breaker = CircuitBreaker(
            failure_threshold=1,
            backoff_base_seconds=5,
            backoff_max_seconds=30
        )

        # First failure: 5s backoff
        breaker.record_failure()
        assert breaker.current_backoff_seconds == 5

        # Simulate recovery then failure again
        breaker.record_success()
        breaker.record_failure()
        assert breaker.current_backoff_seconds == 10  # Doubled

        # Again
        breaker.record_success()
        breaker.record_failure()
        assert breaker.current_backoff_seconds == 20

        # Capped at 30s
        breaker.record_success()
        breaker.record_failure()
        assert breaker.current_backoff_seconds == 30

    def test_transitions_to_half_open_after_backoff(self):
        """After backoff expires, transitions to HALF_OPEN."""
        breaker = CircuitBreaker(failure_threshold=1, backoff_base_seconds=0)

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Backoff expires immediately (0 seconds)
        assert breaker.should_attempt_poll() is True
        assert breaker.state == CircuitState.HALF_OPEN

    def test_recovery_on_success(self):
        """Successful poll resets circuit to CLOSED."""
        breaker = CircuitBreaker(failure_threshold=1)

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


# ============================================================================
# Unit Tests: MachineState
# ============================================================================


class TestMachineState:
    """Test state caching and change detection."""

    def test_initial_state_is_empty(self):
        """MachineState starts with empty current_state."""
        state = MachineState(machine_id="test")
        assert len(state.current_state) == 0

    def test_first_poll_all_tags_are_changed(self):
        """First poll: all tags are considered 'changed'."""
        state = MachineState(machine_id="test")

        tags = [
            IOTagStatus(tag_name="conveyor", value=False, tag_type="Output"),
            IOTagStatus(tag_name="at_entry", value=True, tag_type="Input"),
        ]

        changed = state.get_changed_tags(tags)

        assert len(changed) == 2
        assert changed[0].tag_name == "conveyor"
        assert changed[1].tag_name == "at_entry"

    def test_no_changes_returns_empty_list(self):
        """Same values on subsequent poll returns empty list."""
        state = MachineState(machine_id="test")

        # First poll
        tags = [
            IOTagStatus(tag_name="conveyor", value=False, tag_type="Output"),
        ]
        state.get_changed_tags(tags)

        # Same values
        tags = [
            IOTagStatus(tag_name="conveyor", value=False, tag_type="Output"),
        ]
        changed = state.get_changed_tags(tags)

        assert len(changed) == 0

    def test_value_change_detected(self):
        """Value change is detected correctly."""
        state = MachineState(machine_id="test")

        # First poll
        tags = [
            IOTagStatus(tag_name="conveyor", value=False, tag_type="Output"),
        ]
        state.get_changed_tags(tags)

        # Value changed
        tags = [
            IOTagStatus(tag_name="conveyor", value=True, tag_type="Output"),
        ]
        changed = state.get_changed_tags(tags)

        assert len(changed) == 1
        assert changed[0].tag_name == "conveyor"
        assert changed[0].value is True

    def test_partial_changes_detected(self):
        """Only changed tags are returned, not all tags."""
        state = MachineState(machine_id="test")

        # First poll
        tags = [
            IOTagStatus(tag_name="conveyor", value=False, tag_type="Output"),
            IOTagStatus(tag_name="at_entry", value=True, tag_type="Input"),
        ]
        state.get_changed_tags(tags)

        # Only one tag changed
        tags = [
            IOTagStatus(tag_name="conveyor", value=True, tag_type="Output"),  # CHANGED
            IOTagStatus(tag_name="at_entry", value=True, tag_type="Input"),  # SAME
        ]
        changed = state.get_changed_tags(tags)

        assert len(changed) == 1
        assert changed[0].tag_name == "conveyor"


# ============================================================================
# Unit Tests: Subscription
# ============================================================================


class TestSubscription:
    """Test subscription observer pattern."""

    @pytest.mark.asyncio
    async def test_callback_receives_changed_tags(self):
        """Subscription callback is called with changed tags."""
        callback_calls = []

        async def test_callback(machine_id, changed_tags):
            callback_calls.append((machine_id, changed_tags))

        sub = Subscription(
            subscription_id="sub_1",
            machine_id="test",
            callback=test_callback
        )

        tags = [IOTagStatus(tag_name="conveyor", value=True, tag_type="Output")]
        await sub.notify(tags)

        assert len(callback_calls) == 1
        assert callback_calls[0][0] == "test"
        assert len(callback_calls[0][1]) == 1

    @pytest.mark.asyncio
    async def test_tag_filter_works(self):
        """Tag filter only passes specified tags to callback."""
        callback_calls = []

        async def test_callback(machine_id, changed_tags):
            callback_calls.append((machine_id, changed_tags))

        sub = Subscription(
            subscription_id="sub_1",
            machine_id="test",
            callback=test_callback,
            tag_filter={"conveyor"}  # Only care about conveyor
        )

        tags = [
            IOTagStatus(tag_name="conveyor", value=True, tag_type="Output"),
            IOTagStatus(tag_name="at_entry", value=False, tag_type="Input"),
        ]
        await sub.notify(tags)

        # Callback should receive only 'conveyor' tag
        assert len(callback_calls) == 1
        assert len(callback_calls[0][1]) == 1
        assert callback_calls[0][1][0].tag_name == "conveyor"

    @pytest.mark.asyncio
    async def test_callback_error_is_caught(self):
        """Errors in callback are caught and logged (don't crash)."""
        async def bad_callback(machine_id, changed_tags):
            raise Exception("Callback failed!")

        sub = Subscription(
            subscription_id="sub_1",
            machine_id="test",
            callback=bad_callback
        )

        tags = [IOTagStatus(tag_name="conveyor", value=True, tag_type="Output")]

        # Should not raise exception
        await sub.notify(tags)


# ============================================================================
# Unit Tests: MachineStateManager (Mocked)
# ============================================================================


class TestMachineStateManager:
    """Test MachineStateManager with mocked Factory.io."""

    @pytest.mark.asyncio
    async def test_initialization(self, sample_machine_config):
        """Manager initializes correctly with machines."""
        manager = MachineStateManager([sample_machine_config])

        assert len(manager.machines) == 1
        assert "test_sorting" in manager.machines
        assert len(manager.states) == 1

    @pytest.mark.asyncio
    async def test_start_creates_polling_tasks(self, sample_machine_config, mock_tool):
        """start() creates background tasks for each machine."""
        manager = MachineStateManager([sample_machine_config])
        manager.readwrite_tool = mock_tool

        await manager.start()

        assert len(manager.polling_tasks) == 1
        assert "test_sorting" in manager.polling_tasks
        assert manager.running is True

        await manager.stop()

    @pytest.mark.asyncio
    async def test_subscribe_and_notify(self, sample_machine_config, mock_tool):
        """Subscriptions receive state change notifications."""
        manager = MachineStateManager([sample_machine_config])
        manager.readwrite_tool = mock_tool

        callback_calls = []

        async def test_callback(machine_id, changed_tags):
            callback_calls.append((machine_id, changed_tags))

        # Subscribe
        sub_id = manager.subscribe("test_sorting", test_callback)
        assert sub_id.startswith("test_sorting")

        # Start polling
        await manager.start()
        await asyncio.sleep(2)  # Wait for at least one poll

        # Should have received initial state
        assert len(callback_calls) > 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_unsubscribe_works(self, sample_machine_config, mock_tool):
        """unsubscribe() removes subscription."""
        manager = MachineStateManager([sample_machine_config])
        manager.readwrite_tool = mock_tool

        async def test_callback(machine_id, changed_tags):
            pass

        sub_id = manager.subscribe("test_sorting", test_callback)
        assert len(manager.subscriptions["test_sorting"]) == 1

        manager.unsubscribe(sub_id)
        assert len(manager.subscriptions["test_sorting"]) == 0

    @pytest.mark.asyncio
    async def test_get_state_returns_cached_state(
        self, sample_machine_config, mock_tool
    ):
        """get_state() returns current cached state."""
        manager = MachineStateManager([sample_machine_config])
        manager.readwrite_tool = mock_tool

        await manager.start()
        await asyncio.sleep(2)  # Wait for one poll

        state = manager.get_state("test_sorting")
        assert state is not None
        assert len(state) > 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(
        self, sample_machine_config, mock_tool
    ):
        """Circuit breaker opens after consecutive failures."""
        manager = MachineStateManager([sample_machine_config])
        manager.readwrite_tool = mock_tool

        # Cause next 3 calls to fail
        mock_tool.fail_next_n_calls = 3

        await manager.start()
        await asyncio.sleep(4)  # Wait for failures

        # Circuit should be OPEN
        assert manager.is_healthy("test_sorting") is False

        await manager.stop()

    @pytest.mark.asyncio
    async def test_multiple_machines_poll_independently(self, mock_tool):
        """Multiple machines can poll simultaneously."""
        config1 = MachineConfig(
            machine_id="machine1",
            scene_name="Machine 1",
            factory_io_url="http://localhost:7410",
            telegram_chat_id=-1001,
            poll_interval_seconds=1,
            monitored_inputs=[TagConfig(tag="at_entry", label="Entry")],
        )

        config2 = MachineConfig(
            machine_id="machine2",
            scene_name="Machine 2",
            factory_io_url="http://localhost:7410",
            telegram_chat_id=-1002,
            poll_interval_seconds=1,
            monitored_inputs=[TagConfig(tag="at_exit", label="Exit")],
        )

        manager = MachineStateManager([config1, config2])
        manager.readwrite_tool = mock_tool

        await manager.start()
        await asyncio.sleep(2)

        # Both machines should have state
        state1 = manager.get_state("machine1")
        state2 = manager.get_state("machine2")

        assert state1 is not None
        assert state2 is not None

        await manager.stop()


# ============================================================================
# Integration Tests (Real Factory.io)
# ============================================================================


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("FACTORY_IO_URL"),
    reason="Factory.io not available (set FACTORY_IO_URL env var)"
)
class TestMachineStateManagerIntegration:
    """Integration tests with real Factory.io."""

    @pytest.mark.asyncio
    async def test_real_polling(self, sample_machine_config):
        """Test polling with real Factory.io instance."""
        # Override URL with environment variable
        sample_machine_config.factory_io_url = os.getenv(
            "FACTORY_IO_URL", "http://localhost:7410"
        )

        manager = MachineStateManager([sample_machine_config])

        await manager.start()
        await asyncio.sleep(6)  # Wait for at least one poll cycle

        # Verify state was populated
        state = manager.get_state("test_sorting")
        assert state is not None
        assert len(state) > 0

        # Verify all configured tags were read
        expected_tags = {"at_entry", "sensor_height", "conveyor_running", "pusher_extend"}
        actual_tags = set(state.keys())
        assert expected_tags.issubset(actual_tags)

        await manager.stop()

    @pytest.mark.asyncio
    async def test_real_subscription_notifications(self, sample_machine_config):
        """Test subscriptions receive real Factory.io changes."""
        sample_machine_config.factory_io_url = os.getenv(
            "FACTORY_IO_URL", "http://localhost:7410"
        )

        manager = MachineStateManager([sample_machine_config])

        callback_calls = []

        async def test_callback(machine_id, changed_tags):
            callback_calls.append((machine_id, changed_tags))

        manager.subscribe("test_sorting", test_callback)

        await manager.start()
        await asyncio.sleep(6)  # Wait for polls

        # Should have received at least initial state
        assert len(callback_calls) > 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_health_status(self, sample_machine_config):
        """Test health status reporting."""
        sample_machine_config.factory_io_url = os.getenv(
            "FACTORY_IO_URL", "http://localhost:7410"
        )

        manager = MachineStateManager([sample_machine_config])

        await manager.start()
        await asyncio.sleep(6)

        health = manager.get_health_status()
        assert "test_sorting" in health
        assert health["test_sorting"]["state"] == "closed"  # Should be healthy

        await manager.stop()
