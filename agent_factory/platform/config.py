"""
Configuration Loader for Factory.io Machine Definitions

Loads YAML configuration files that define machines, their I/O tags,
Telegram chat mappings, and control settings.

Usage:
    from agent_factory.platform.config import load_machine_config, MachineConfig

    # Load from default path
    config = load_machine_config()

    # Access machines
    for machine in config.machines:
        print(f"{machine.machine_id}: {machine.scene_name}")

    # Get machine by ID
    machine = config.get_machine("scene1_sorting")

    # Get machine by Telegram chat ID
    machine = config.get_by_chat_id(-1001234567890)
"""

import os
import yaml
import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class TagConfig(BaseModel):
    """
    Configuration for a single I/O tag.

    Attributes:
        tag: Tag name in Factory.io (e.g., "conveyor_running")
        label: Display label for UI (e.g., "Conveyor")
        emoji: Optional emoji to display (e.g., "▶️")
    """
    tag: str
    label: str
    emoji: Optional[str] = None

    @field_validator("tag")
    @classmethod
    def validate_tag_name(cls, v):
        """Ensure tag name is not empty."""
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")
        return v.strip()


class MachineConfig(BaseModel):
    """
    Configuration for a single machine/scene.

    Defines the mapping between a Factory.io scene and a Telegram chat,
    including which I/O tags to monitor and control.

    Attributes:
        machine_id: Unique identifier for this machine (e.g., "scene1_sorting")
        scene_name: Display name (e.g., "Sorting System")
        factory_io_url: Factory.io Web API URL (default: http://localhost:7410)
        telegram_chat_id: Telegram chat/group ID (negative for groups)
        telegram_chat_name: Optional chat name for reference
        poll_interval_seconds: How often to poll Factory.io (default: 5)
        monitored_inputs: List of input tags to display
        controllable_outputs: List of output tags with control buttons
        emergency_stop_tags: Tags to set to False on emergency stop
        read_only_tags: Tags that should not be controllable
    """
    machine_id: str
    scene_name: str
    factory_io_url: str = "http://localhost:7410"
    telegram_chat_id: int
    telegram_chat_name: Optional[str] = None
    poll_interval_seconds: int = Field(default=5)  # Validated and clamped by field_validator
    monitored_inputs: List[TagConfig] = Field(default_factory=list)
    controllable_outputs: List[TagConfig] = Field(default_factory=list)
    emergency_stop_tags: List[str] = Field(default_factory=list)
    read_only_tags: List[str] = Field(default_factory=list)

    @field_validator("machine_id")
    @classmethod
    def validate_machine_id(cls, v):
        """Ensure machine_id is alphanumeric with underscores."""
        if not v or not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "machine_id must be alphanumeric with underscores/hyphens"
            )
        return v.strip()

    @field_validator("poll_interval_seconds")
    @classmethod
    def validate_poll_interval(cls, v):
        """Ensure poll interval is reasonable (clamp to 1-60)."""
        if v < 1:
            logger.warning("Poll interval < 1s, setting to 1s")
            return 1
        if v > 60:
            logger.warning("Poll interval > 60s, setting to 60s")
            return 60
        return v


class MachineConfigList(BaseModel):
    """
    Container for all machine configurations.

    Attributes:
        machines: List of machine configurations
    """
    machines: List[MachineConfig] = Field(default_factory=list)

    def get_machine(self, machine_id: str) -> Optional[MachineConfig]:
        """
        Get machine configuration by ID.

        Args:
            machine_id: Machine identifier

        Returns:
            MachineConfig if found, None otherwise
        """
        for machine in self.machines:
            if machine.machine_id == machine_id:
                return machine
        return None

    def get_by_chat_id(self, chat_id: int) -> Optional[MachineConfig]:
        """
        Get machine configuration by Telegram chat ID.

        Args:
            chat_id: Telegram chat/group ID

        Returns:
            MachineConfig if found, None otherwise
        """
        for machine in self.machines:
            if machine.telegram_chat_id == chat_id:
                return machine
        return None

    def get_all(self) -> List[MachineConfig]:
        """Get all machine configurations."""
        return self.machines


def load_machine_config(config_path: Optional[str] = None) -> MachineConfigList:
    """
    Load machine configuration from YAML file.

    Args:
        config_path: Path to YAML file (default: from env var or agent_factory/config/machines.yaml)

    Returns:
        MachineConfigList with all machine configurations

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        pydantic.ValidationError: If config structure is invalid
    """
    if config_path is None:
        config_path = os.getenv(
            "MACHINES_CONFIG_PATH",
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "config",
                "machines.yaml"
            )
        )

    # Resolve relative path
    if not os.path.isabs(config_path):
        config_path = os.path.abspath(config_path)

    logger.info(f"Loading machine config from: {config_path}")

    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning(f"Empty config file: {config_path}")
            return MachineConfigList()

        # Validate and parse with Pydantic
        config = MachineConfigList(**data)

        logger.info(f"Loaded {len(config.machines)} machine configuration(s)")
        for machine in config.machines:
            logger.debug(
                f"  - {machine.machine_id}: {machine.scene_name} "
                f"(chat_id={machine.telegram_chat_id})"
            )

        return config

    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise

    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise


def validate_config_file(config_path: str) -> bool:
    """
    Validate configuration file without raising exceptions.

    Args:
        config_path: Path to YAML file

    Returns:
        True if valid, False otherwise
    """
    try:
        load_machine_config(config_path)
        return True
    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        return False
