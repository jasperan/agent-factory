"""
Tests for platform types (IOTagStatus, ControlButton, PlatformMessage, AlertMessage).

Run with:
    poetry run pytest tests/test_platform_types.py -v
"""

import pytest
from datetime import datetime
from agent_factory.platform.types import (
    IOTagStatus,
    ControlButton,
    PlatformMessage,
    AlertMessage
)


class TestIOTagStatus:
    """Test IOTagStatus dataclass."""

    def test_create_digital_input(self):
        """Test creating a digital input tag."""
        tag = IOTagStatus(
            tag_name="at_entry",
            value=True,
            tag_type="Input"
        )
        assert tag.tag_name == "at_entry"
        assert tag.value is True
        assert tag.tag_type == "Input"
        assert tag.address is None
        assert isinstance(tag.last_updated, datetime)

    def test_create_digital_output(self):
        """Test creating a digital output tag."""
        tag = IOTagStatus(
            tag_name="conveyor_running",
            value=False,
            tag_type="Output",
            address=0
        )
        assert tag.tag_name == "conveyor_running"
        assert tag.value is False
        assert tag.tag_type == "Output"
        assert tag.address == 0

    def test_create_analog_tag(self):
        """Test creating an analog tag with numeric value."""
        tag = IOTagStatus(
            tag_name="motor_speed",
            value=1500.5,
            tag_type="Output"
        )
        assert tag.value == 1500.5
        assert isinstance(tag.value, float)

    def test_last_updated_auto_set(self):
        """Test that last_updated is automatically set."""
        before = datetime.now()
        tag = IOTagStatus(tag_name="test", value=True, tag_type="Input")
        after = datetime.now()

        assert before <= tag.last_updated <= after


class TestControlButton:
    """Test ControlButton dataclass."""

    def test_create_toggle_button(self):
        """Test creating a toggle button."""
        button = ControlButton(
            label="Toggle Conveyor",
            tag_name="conveyor_running",
            action="toggle",
            emoji="▶️"
        )
        assert button.label == "Toggle Conveyor"
        assert button.tag_name == "conveyor_running"
        assert button.action == "toggle"
        assert button.emoji == "▶️"
        assert button.target_value is None
        assert button.style == "primary"

    def test_create_write_button(self):
        """Test creating a write button with target value."""
        button = ControlButton(
            label="Start Motor",
            tag_name="motor_running",
            action="write",
            target_value=True,
            emoji="🔧"
        )
        assert button.action == "write"
        assert button.target_value is True

    def test_create_emergency_stop_button(self):
        """Test creating an emergency stop button."""
        button = ControlButton(
            label="EMERGENCY STOP",
            tag_name="",
            action="emergency_stop",
            emoji="🚨",
            style="danger"
        )
        assert button.action == "emergency_stop"
        assert button.style == "danger"

    def test_to_callback_data_toggle(self):
        """Test callback data generation for toggle action."""
        button = ControlButton(
            label="Toggle",
            tag_name="conveyor",
            action="toggle"
        )
        callback_data = button.to_callback_data(machine_id="scene1")
        assert callback_data == "toggle:scene1:conveyor:"

    def test_to_callback_data_write(self):
        """Test callback data generation for write action."""
        button = ControlButton(
            label="Start",
            tag_name="motor",
            action="write",
            target_value=True
        )
        callback_data = button.to_callback_data(machine_id="scene2")
        assert callback_data == "write:scene2:motor:True"

    def test_callback_data_length_limit(self):
        """Test that callback data is truncated to 64 chars."""
        button = ControlButton(
            label="Very long label that exceeds the Telegram callback data limit",
            tag_name="extremely_long_tag_name_that_should_be_truncated",
            action="toggle"
        )
        callback_data = button.to_callback_data(machine_id="very_long_machine_identifier")
        assert len(callback_data) <= 64


class TestAlertMessage:
    """Test AlertMessage dataclass."""

    def test_create_info_alert(self):
        """Test creating an info alert."""
        alert = AlertMessage(text="System is running normally")
        assert alert.text == "System is running normally"
        assert alert.level == "info"
        assert isinstance(alert.timestamp, datetime)

    def test_create_warning_alert(self):
        """Test creating a warning alert."""
        alert = AlertMessage(text="Temperature high", level="warning")
        assert alert.level == "warning"

    def test_create_error_alert(self):
        """Test creating an error alert."""
        alert = AlertMessage(text="Connection lost", level="error")
        assert alert.level == "error"

    def test_timestamp_auto_set(self):
        """Test that timestamp is automatically set."""
        before = datetime.now()
        alert = AlertMessage(text="Test")
        after = datetime.now()

        assert before <= alert.timestamp <= after


class TestPlatformMessage:
    """Test PlatformMessage dataclass."""

    def test_create_empty_message(self):
        """Test creating an empty message."""
        message = PlatformMessage(
            title="Test System",
            description="Test description"
        )
        assert message.title == "Test System"
        assert message.description == "Test description"
        assert message.io_status == {}
        assert message.controls == []
        assert message.alerts == []
        assert message.metadata == {}

    def test_add_io_tag(self):
        """Test adding I/O tags to message."""
        message = PlatformMessage(title="Test")

        tag1 = IOTagStatus(tag_name="input1", value=True, tag_type="Input")
        tag2 = IOTagStatus(tag_name="output1", value=False, tag_type="Output")

        message.add_io_tag(tag1)
        message.add_io_tag(tag2)

        assert len(message.io_status) == 2
        assert "input1" in message.io_status
        assert "output1" in message.io_status

    def test_add_control(self):
        """Test adding control buttons to message."""
        message = PlatformMessage(title="Test")

        button1 = ControlButton(label="Button 1", tag_name="tag1", action="toggle")
        button2 = ControlButton(label="Button 2", tag_name="tag2", action="write", target_value=True)

        message.add_control(button1)
        message.add_control(button2)

        assert len(message.controls) == 2
        assert message.controls[0].label == "Button 1"
        assert message.controls[1].label == "Button 2"

    def test_add_alert_as_object(self):
        """Test adding alert as AlertMessage object."""
        message = PlatformMessage(title="Test")
        alert = AlertMessage(text="Test alert", level="warning")
        message.add_alert(alert)

        assert len(message.alerts) == 1
        assert message.alerts[0].text == "Test alert"
        assert message.alerts[0].level == "warning"

    def test_add_alert_as_string(self):
        """Test adding alert as string."""
        message = PlatformMessage(title="Test")
        message.add_alert("Simple alert", level="error")

        assert len(message.alerts) == 1
        assert message.alerts[0].text == "Simple alert"
        assert message.alerts[0].level == "error"

    def test_get_inputs(self):
        """Test filtering input tags."""
        message = PlatformMessage(title="Test")

        message.add_io_tag(IOTagStatus(tag_name="input1", value=True, tag_type="Input"))
        message.add_io_tag(IOTagStatus(tag_name="output1", value=False, tag_type="Output"))
        message.add_io_tag(IOTagStatus(tag_name="input2", value=False, tag_type="Input"))

        inputs = message.get_inputs()
        assert len(inputs) == 2
        assert "input1" in inputs
        assert "input2" in inputs
        assert "output1" not in inputs

    def test_get_outputs(self):
        """Test filtering output tags."""
        message = PlatformMessage(title="Test")

        message.add_io_tag(IOTagStatus(tag_name="input1", value=True, tag_type="Input"))
        message.add_io_tag(IOTagStatus(tag_name="output1", value=False, tag_type="Output"))
        message.add_io_tag(IOTagStatus(tag_name="output2", value=True, tag_type="Output"))

        outputs = message.get_outputs()
        assert len(outputs) == 2
        assert "output1" in outputs
        assert "output2" in outputs
        assert "input1" not in outputs

    def test_complete_message(self):
        """Test creating a complete message with all components."""
        message = PlatformMessage(
            title="SORTING SYSTEM",
            description="Main assembly line"
        )

        # Add I/O tags
        message.add_io_tag(IOTagStatus(tag_name="at_entry", value=True, tag_type="Input"))
        message.add_io_tag(IOTagStatus(tag_name="conveyor_running", value=False, tag_type="Output"))

        # Add controls
        message.add_control(ControlButton(
            label="Start Conveyor",
            tag_name="conveyor_running",
            action="write",
            target_value=True,
            emoji="▶️"
        ))

        # Add alerts
        message.add_alert("System ready", level="info")

        # Add metadata
        message.metadata["machine_id"] = "scene1_sorting"

        # Verify complete message
        assert message.title == "SORTING SYSTEM"
        assert len(message.io_status) == 2
        assert len(message.controls) == 1
        assert len(message.alerts) == 1
        assert message.metadata["machine_id"] == "scene1_sorting"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
