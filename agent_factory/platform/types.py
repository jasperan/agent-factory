"""
Universal Data Types for Platform Layer

Platform-agnostic data structures for Factory.io state management,
message formatting, and control operations.

Usage:
    from agent_factory.platform.types import IOTagStatus, ControlButton, PlatformMessage

    # Create tag status
    tag = IOTagStatus(
        tag_name="conveyor_running",
        value=True,
        tag_type="Output"
    )

    # Create control button
    button = ControlButton(
        label="Toggle Conveyor",
        tag_name="conveyor_running",
        action="toggle",
        emoji="▶️"
    )

    # Create platform message
    message = PlatformMessage(
        title="Sorting System",
        description="Main assembly line",
        io_status={"conveyor_running": tag},
        controls=[button]
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Union, Literal


@dataclass
class IOTagStatus:
    """
    Represents a single Factory.io I/O tag with its current value.

    Used for displaying I/O status in messages and tracking state changes.

    Attributes:
        tag_name: Name of the tag (e.g., "conveyor_running", "at_entry")
        value: Current value (bool for digital, int/float for analog, str for custom)
        tag_type: Type of tag ("Input" or "Output")
        address: Optional I/O address (e.g., 0 for first tag)
        last_updated: Timestamp of last value change
    """
    tag_name: str
    value: Union[bool, int, float, str]
    tag_type: Literal["Input", "Output"]
    address: Optional[int] = None
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Ensure last_updated is always set."""
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class ControlButton:
    """
    Represents a control button for user interaction.

    Used for building inline keyboards in Telegram and other platforms.

    Attributes:
        label: Display text on button (e.g., "Toggle Conveyor")
        tag_name: Factory.io tag to control (e.g., "conveyor_running")
        action: Action to perform ("toggle" | "write" | "emergency_stop")
        target_value: Specific value to write (for "write" action)
        emoji: Optional emoji to display on button
        style: Button style ("primary" | "danger" | "secondary")
    """
    label: str
    tag_name: str
    action: Literal["toggle", "write", "emergency_stop"]
    target_value: Optional[Union[bool, int, float]] = None
    emoji: str = "🔘"
    style: Literal["primary", "danger", "secondary"] = "primary"

    def to_callback_data(self, machine_id: str) -> str:
        """
        Generate callback data string for button.

        Format: action:machine_id:tag_name:target_value

        Args:
            machine_id: ID of machine this button controls

        Returns:
            Callback data string (max 64 chars for Telegram)
        """
        parts = [
            self.action,
            machine_id,
            self.tag_name,
            str(self.target_value) if self.target_value is not None else ""
        ]
        callback_data = ":".join(parts)
        return callback_data[:64]  # Telegram callback_data limit


@dataclass
class AlertMessage:
    """
    Represents an alert or notification message.

    Attributes:
        text: Alert message content
        level: Severity level ("info" | "warning" | "error")
        timestamp: When alert was created
    """
    text: str
    level: Literal["info", "warning", "error"] = "info"
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Ensure timestamp is always set."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PlatformMessage:
    """
    Universal message format for any platform (Telegram, WhatsApp, Slack, etc.).

    Contains all data needed to display Factory.io status with controls.

    Attributes:
        title: Message title (e.g., "SORTING SYSTEM")
        description: Optional description/subtitle
        io_status: Dict of tag_name → IOTagStatus
        controls: List of control buttons to display
        alerts: List of alerts to show
        metadata: Optional platform-specific metadata
    """
    title: str
    description: str = ""
    io_status: Dict[str, IOTagStatus] = field(default_factory=dict)
    controls: List[ControlButton] = field(default_factory=list)
    alerts: List[AlertMessage] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)

    def add_io_tag(self, tag: IOTagStatus) -> None:
        """Add an I/O tag to the message."""
        self.io_status[tag.tag_name] = tag

    def add_control(self, control: ControlButton) -> None:
        """Add a control button to the message."""
        self.controls.append(control)

    def add_alert(self, alert: Union[AlertMessage, str], level: str = "info") -> None:
        """
        Add an alert to the message.

        Args:
            alert: AlertMessage object or string message
            level: Severity level if alert is a string
        """
        if isinstance(alert, str):
            alert = AlertMessage(text=alert, level=level)
        self.alerts.append(alert)

    def get_inputs(self) -> Dict[str, IOTagStatus]:
        """Get all input tags."""
        return {name: tag for name, tag in self.io_status.items() if tag.tag_type == "Input"}

    def get_outputs(self) -> Dict[str, IOTagStatus]:
        """Get all output tags."""
        return {name: tag for name, tag in self.io_status.items() if tag.tag_type == "Output"}
