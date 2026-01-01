"""
Tests for platform configuration loader (YAML parsing, Pydantic models).

Run with:
    poetry run pytest tests/test_platform_config.py -v
"""

import pytest
import os
import tempfile
from pydantic import ValidationError
from agent_factory.platform.config import (
    TagConfig,
    MachineConfig,
    MachineConfigList,
    load_machine_config,
    validate_config_file
)


class TestTagConfig:
    """Test TagConfig Pydantic model."""

    def test_create_tag_config(self):
        """Test creating a valid tag configuration."""
        tag = TagConfig(
            tag="conveyor_running",
            label="Conveyor",
            emoji="▶️"
        )
        assert tag.tag == "conveyor_running"
        assert tag.label == "Conveyor"
        assert tag.emoji == "▶️"

    def test_tag_config_without_emoji(self):
        """Test creating tag without emoji."""
        tag = TagConfig(tag="sensor", label="Sensor")
        assert tag.tag == "sensor"
        assert tag.emoji is None

    def test_invalid_empty_tag(self):
        """Test that empty tag name raises validation error."""
        with pytest.raises(ValidationError):
            TagConfig(tag="", label="Test")

    def test_tag_name_trimmed(self):
        """Test that tag name is trimmed."""
        tag = TagConfig(tag="  test_tag  ", label="Test")
        assert tag.tag == "test_tag"


class TestMachineConfig:
    """Test MachineConfig Pydantic model."""

    def test_create_machine_config(self):
        """Test creating a valid machine configuration."""
        machine = MachineConfig(
            machine_id="scene1_sorting",
            scene_name="Sorting System",
            telegram_chat_id=-1001234567890
        )
        assert machine.machine_id == "scene1_sorting"
        assert machine.scene_name == "Sorting System"
        assert machine.telegram_chat_id == -1001234567890
        assert machine.factory_io_url == "http://localhost:7410"  # default
        assert machine.poll_interval_seconds == 5  # default

    def test_machine_config_with_tags(self):
        """Test machine config with I/O tags."""
        machine = MachineConfig(
            machine_id="test_machine",
            scene_name="Test",
            telegram_chat_id=12345,
            monitored_inputs=[
                TagConfig(tag="input1", label="Input 1")
            ],
            controllable_outputs=[
                TagConfig(tag="output1", label="Output 1", emoji="🔧")
            ],
            emergency_stop_tags=["output1"],
            read_only_tags=["input1"]
        )
        assert len(machine.monitored_inputs) == 1
        assert len(machine.controllable_outputs) == 1
        assert "output1" in machine.emergency_stop_tags
        assert "input1" in machine.read_only_tags

    def test_custom_poll_interval(self):
        """Test custom poll interval."""
        machine = MachineConfig(
            machine_id="test",
            scene_name="Test",
            telegram_chat_id=12345,
            poll_interval_seconds=10
        )
        assert machine.poll_interval_seconds == 10

    def test_invalid_machine_id(self):
        """Test that invalid machine_id raises validation error."""
        with pytest.raises(ValidationError):
            MachineConfig(
                machine_id="invalid machine id!",  # spaces and special chars
                scene_name="Test",
                telegram_chat_id=12345
            )

    def test_poll_interval_bounds(self):
        """Test poll interval is clamped to 1-60 seconds."""
        # Too low
        machine = MachineConfig(
            machine_id="test",
            scene_name="Test",
            telegram_chat_id=12345,
            poll_interval_seconds=0
        )
        assert machine.poll_interval_seconds == 1  # clamped

        # Too high
        machine = MachineConfig(
            machine_id="test",
            scene_name="Test",
            telegram_chat_id=12345,
            poll_interval_seconds=100
        )
        assert machine.poll_interval_seconds == 60  # clamped


class TestMachineConfigList:
    """Test MachineConfigList container."""

    def test_create_empty_list(self):
        """Test creating empty config list."""
        config = MachineConfigList()
        assert config.machines == []

    def test_create_with_machines(self):
        """Test creating config list with machines."""
        config = MachineConfigList(
            machines=[
                MachineConfig(
                    machine_id="scene1",
                    scene_name="Scene 1",
                    telegram_chat_id=11111
                ),
                MachineConfig(
                    machine_id="scene2",
                    scene_name="Scene 2",
                    telegram_chat_id=22222
                )
            ]
        )
        assert len(config.machines) == 2

    def test_get_machine_by_id(self):
        """Test retrieving machine by ID."""
        config = MachineConfigList(
            machines=[
                MachineConfig(
                    machine_id="scene1_sorting",
                    scene_name="Sorting",
                    telegram_chat_id=11111
                ),
                MachineConfig(
                    machine_id="scene2_bottling",
                    scene_name="Bottling",
                    telegram_chat_id=22222
                )
            ]
        )

        machine = config.get_machine("scene1_sorting")
        assert machine is not None
        assert machine.scene_name == "Sorting"

        # Non-existent
        machine = config.get_machine("nonexistent")
        assert machine is None

    def test_get_machine_by_chat_id(self):
        """Test retrieving machine by Telegram chat ID."""
        config = MachineConfigList(
            machines=[
                MachineConfig(
                    machine_id="scene1",
                    scene_name="Scene 1",
                    telegram_chat_id=-1001234567890
                ),
                MachineConfig(
                    machine_id="scene2",
                    scene_name="Scene 2",
                    telegram_chat_id=-1009876543210
                )
            ]
        )

        machine = config.get_by_chat_id(-1001234567890)
        assert machine is not None
        assert machine.machine_id == "scene1"

        # Non-existent
        machine = config.get_by_chat_id(999999)
        assert machine is None

    def test_get_all(self):
        """Test getting all machines."""
        machines_list = [
            MachineConfig(
                machine_id=f"scene{i}",
                scene_name=f"Scene {i}",
                telegram_chat_id=i * 1000
            )
            for i in range(3)
        ]

        config = MachineConfigList(machines=machines_list)
        all_machines = config.get_all()

        assert len(all_machines) == 3
        assert all_machines == machines_list


class TestLoadMachineConfig:
    """Test load_machine_config function."""

    def test_load_default_config(self):
        """Test loading from default config path."""
        config = load_machine_config()
        assert isinstance(config, MachineConfigList)
        assert len(config.machines) >= 2  # At least the 2 examples

        # Verify example machines
        sorting = config.get_machine("scene1_sorting")
        assert sorting is not None
        assert sorting.scene_name == "Sorting System"

        bottling = config.get_machine("scene2_bottling")
        assert bottling is not None
        assert bottling.scene_name == "Bottling Station"

    def test_load_from_custom_path(self):
        """Test loading from custom YAML file."""
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
machines:
  - machine_id: test_machine
    scene_name: "Test Machine"
    telegram_chat_id: 12345
    monitored_inputs:
      - tag: "test_input"
        label: "Test Input"
    controllable_outputs:
      - tag: "test_output"
        label: "Test Output"
        emoji: "🔧"
""")
            temp_path = f.name

        try:
            config = load_machine_config(temp_path)
            assert len(config.machines) == 1
            machine = config.machines[0]
            assert machine.machine_id == "test_machine"
            assert len(machine.monitored_inputs) == 1
            assert len(machine.controllable_outputs) == 1
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_machine_config("/nonexistent/path/to/config.yaml")

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("invalid: yaml: content: [unclosed")
            temp_path = f.name

        try:
            with pytest.raises(Exception):  # yaml.YAMLError
                load_machine_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_invalid_structure(self):
        """Test loading YAML with invalid structure raises ValidationError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
machines:
  - machine_id: "test"
    # Missing required field: telegram_chat_id
    scene_name: "Test"
""")
            temp_path = f.name

        try:
            with pytest.raises(ValidationError):
                load_machine_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_empty_config(self):
        """Test loading empty config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            config = load_machine_config(temp_path)
            assert len(config.machines) == 0
        finally:
            os.unlink(temp_path)


class TestValidateConfigFile:
    """Test validate_config_file function."""

    def test_validate_valid_config(self):
        """Test validating a valid config file."""
        # Use the default config file (should be valid)
        default_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "agent_factory",
            "config",
            "machines.yaml"
        )
        assert validate_config_file(default_path) is True

    def test_validate_invalid_config(self):
        """Test validating an invalid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("invalid yaml [")
            temp_path = f.name

        try:
            assert validate_config_file(temp_path) is False
        finally:
            os.unlink(temp_path)

    def test_validate_nonexistent_file(self):
        """Test validating non-existent file."""
        assert validate_config_file("/nonexistent/file.yaml") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
