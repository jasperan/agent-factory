"""
Tests for callbacks.py - Event System

Generated from: specs/callbacks-v1.0.md
Tests: REQ-CB-003 through REQ-CB-010
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from agent_factory.core.callbacks import EventBus, Event, EventType


class TestEventBus:
    """Test EventBus functionality (REQ-CB-003)"""

    def test_emit_and_on(self):
        """Test basic emit and listener registration (REQ-CB-004, REQ-CB-005)"""
        bus = EventBus()
        received_events = []

        def listener(event: Event):
            received_events.append(event)

        bus.on(EventType.AGENT_START, listener)
        bus.emit(EventType.AGENT_START, {"agent_name": "test_agent"})

        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.AGENT_START
        assert received_events[0].data["agent_name"] == "test_agent"

    def test_event_history(self):
        """Test event history tracking (REQ-CB-006)"""
        bus = EventBus()
        bus.emit(EventType.AGENT_START, {"agent": "agent1"})
        bus.emit(EventType.TOOL_CALL, {"tool": "tool1"})
        bus.emit(EventType.AGENT_END, {"agent": "agent1"})

        history = bus.get_history()
        assert len(history) == 3
        assert history[0].event_type == EventType.AGENT_START
        assert history[1].event_type == EventType.TOOL_CALL
        assert history[2].event_type == EventType.AGENT_END

    def test_event_filtering(self):
        """Test event filtering by type (REQ-CB-007)"""
        bus = EventBus()
        bus.emit(EventType.AGENT_START, {"agent": "agent1"})
        bus.emit(EventType.TOOL_CALL, {"tool": "tool1"})
        bus.emit(EventType.AGENT_END, {"agent": "agent1"})

        agent_events = bus.get_history(event_type=EventType.AGENT_START)
        assert len(agent_events) == 1
        assert agent_events[0].event_type == EventType.AGENT_START

        tool_events = bus.get_history(event_type=EventType.TOOL_CALL)
        assert len(tool_events) == 1
        assert tool_events[0].event_type == EventType.TOOL_CALL

    def test_multiple_listeners(self):
        """Test multiple listeners for same event (REQ-CB-005)"""
        bus = EventBus()
        listener1_count = []
        listener2_count = []

        def listener1(event: Event):
            listener1_count.append(event)

        def listener2(event: Event):
            listener2_count.append(event)

        bus.on(EventType.AGENT_START, listener1)
        bus.on(EventType.AGENT_START, listener2)
        bus.emit(EventType.AGENT_START, {"agent": "test"})

        assert len(listener1_count) == 1
        assert len(listener2_count) == 1

    def test_listener_error_isolation(self):
        """Test that listener errors don't affect other listeners (REQ-CB-008)"""
        bus = EventBus()
        successful_calls = []

        def failing_listener(event: Event):
            raise ValueError("Test error")

        def successful_listener(event: Event):
            successful_calls.append(event)

        bus.on(EventType.AGENT_START, failing_listener)
        bus.on(EventType.AGENT_START, successful_listener)

        # Should not raise exception
        bus.emit(EventType.AGENT_START, {"agent": "test"})

        # Successful listener should still have been called
        assert len(successful_calls) == 1

    def test_event_timestamp(self):
        """Test that events have timestamps (REQ-CB-004)"""
        bus = EventBus()
        bus.emit(EventType.AGENT_START, {"agent": "test"})

        history = bus.get_history()
        assert len(history) == 1
        assert history[0].timestamp is not None

    def test_clear_history(self):
        """Test clearing event history (REQ-CB-006)"""
        bus = EventBus()
        bus.emit(EventType.AGENT_START, {"agent": "test"})
        bus.emit(EventType.TOOL_CALL, {"tool": "test"})

        assert len(bus.get_history()) == 2

        bus.clear_history()
        assert len(bus.get_history()) == 0

    def test_no_listeners(self):
        """Test emitting events with no listeners registered"""
        bus = EventBus()
        # Should not raise exception
        bus.emit(EventType.AGENT_START, {"agent": "test"})

        history = bus.get_history()
        assert len(history) == 1

    def test_event_data_captured(self):
        """Test that event data is captured"""
        bus = EventBus()
        data = {"agent": "test", "count": 1}
        bus.emit(EventType.AGENT_START, data)

        history = bus.get_history()
        assert history[0].data["agent"] == "test"
        assert history[0].data["count"] == 1


class TestEvent:
    """Test Event dataclass (REQ-CB-004)"""

    def test_event_creation(self):
        """Test creating Event instances"""
        event = Event(
            event_type=EventType.AGENT_START,
            data={"agent_name": "test"},
            timestamp="2025-12-05T10:00:00"
        )

        assert event.event_type == EventType.AGENT_START
        assert event.data["agent_name"] == "test"
        assert event.timestamp == "2025-12-05T10:00:00"

    def test_event_repr(self):
        """Test Event string representation"""
        event = Event(
            event_type=EventType.TOOL_CALL,
            data={"tool": "search"},
            timestamp="2025-12-05T10:00:00"
        )

        repr_str = repr(event)
        assert "TOOL_CALL" in repr_str or "tool_call" in repr_str
        assert "search" in repr_str


class TestEventType:
    """Test EventType enum (REQ-CB-004)"""

    def test_all_event_types_defined(self):
        """Test that all required event types are defined"""
        required_types = [
            "AGENT_START",
            "AGENT_END",
            "ROUTE_DECISION",
            "ERROR",
            "TOOL_CALL",
        ]

        for type_name in required_types:
            assert hasattr(EventType, type_name), f"EventType.{type_name} not defined"

    def test_event_type_values(self):
        """Test that event types have string values"""
        assert isinstance(EventType.AGENT_START.value, str)
        assert EventType.AGENT_START.value == "agent_start"
