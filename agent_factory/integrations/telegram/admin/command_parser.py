"""
Command Parser for Telegram Admin Panel

Parses text commands (and future voice commands) into structured actions.

Supports:
- Natural language commands ("show agent status", "trigger deployment")
- Slash commands ("/agents", "/deploy")
- Voice messages (future: speech-to-text → command)

Usage:
    parser = CommandParser()
    action = parser.parse("show me agent status")
    if action:
        await action.execute(update, context)
"""

import re
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CommandType(str, Enum):
    """Types of admin commands"""
    AGENT_STATUS = "agent_status"
    AGENT_LOGS = "agent_logs"
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"

    CONTENT_QUEUE = "content_queue"
    CONTENT_APPROVE = "content_approve"
    CONTENT_REJECT = "content_reject"

    DEPLOY = "deploy"
    WORKFLOW = "workflow"
    WORKFLOW_STATUS = "workflow_status"

    KB_STATS = "kb_stats"
    KB_INGEST = "kb_ingest"
    KB_SEARCH = "kb_search"

    METRICS = "metrics"
    COSTS = "costs"
    REVENUE = "revenue"

    HEALTH = "health"
    DB_HEALTH = "db_health"
    VPS_STATUS = "vps_status"

    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """
    Parsed command with action and parameters.

    Attributes:
        type: Command type
        params: Command parameters
        raw_text: Original command text
        confidence: Parsing confidence (0.0-1.0)
    """
    type: CommandType
    params: Dict[str, Any]
    raw_text: str
    confidence: float = 1.0

    def __str__(self) -> str:
        return f"{self.type.value}({self.params})"


class CommandParser:
    """
    Parser for natural language and slash commands.

    Examples:
        >>> parser = CommandParser()
        >>> cmd = parser.parse("show agent status")
        >>> cmd.type == CommandType.AGENT_STATUS
        True
        >>> cmd = parser.parse("deploy to production")
        >>> cmd.type == CommandType.DEPLOY
        True
    """

    def __init__(self):
        """Initialize command patterns"""
        # Pattern: (regex, command_type, param_extractor)
        self.patterns = [
            # Agent commands
            (r"(show|view|check|get)\s+(agent|agents)\s+status", CommandType.AGENT_STATUS, {}),
            (r"agent\s+logs?\s+(\w+)", CommandType.AGENT_LOGS, {"agent_name": 1}),
            (r"start\s+agent\s+(\w+)", CommandType.AGENT_START, {"agent_name": 1}),
            (r"stop\s+agent\s+(\w+)", CommandType.AGENT_STOP, {"agent_name": 1}),

            # Content commands
            (r"(show|view|check)\s+content(\s+queue)?", CommandType.CONTENT_QUEUE, {}),
            (r"approve\s+(\d+)", CommandType.CONTENT_APPROVE, {"content_id": 1}),
            (r"reject\s+(\d+)", CommandType.CONTENT_REJECT, {"content_id": 1}),

            # Deploy commands
            (r"deploy(\s+to)?\s+(production|vps)?", CommandType.DEPLOY, {}),
            (r"trigger\s+deployment", CommandType.DEPLOY, {}),
            (r"run\s+workflow\s+(\w+)", CommandType.WORKFLOW, {"workflow_name": 1}),
            (r"workflow\s+status", CommandType.WORKFLOW_STATUS, {}),

            # KB commands
            (r"(kb|knowledge\s+base)\s+stats?", CommandType.KB_STATS, {}),
            (r"(kb\s+)?ingest\s+(https?://\S+)", CommandType.KB_INGEST, {"url": 2}),
            (r"(kb\s+)?search\s+(.+)", CommandType.KB_SEARCH, {"query": 2}),

            # Analytics commands
            (r"(show|view|check)\s+metrics", CommandType.METRICS, {}),
            (r"(show|view|check)\s+costs?", CommandType.COSTS, {}),
            (r"(show|view|check)\s+revenue", CommandType.REVENUE, {}),

            # System commands
            (r"(system\s+)?health(\s+check)?", CommandType.HEALTH, {}),
            (r"(database|db)\s+health", CommandType.DB_HEALTH, {}),
            (r"vps\s+status", CommandType.VPS_STATUS, {}),
        ]

        logger.info(f"CommandParser initialized with {len(self.patterns)} patterns")

    def parse(self, text: str) -> Optional[ParsedCommand]:
        """
        Parse command text into structured action.

        Args:
            text: Command text (from message or voice)

        Returns:
            ParsedCommand or None if no match
        """
        text_lower = text.lower().strip()

        # Try each pattern
        for pattern, cmd_type, param_spec in self.patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Extract parameters
                params = {}
                for param_name, group_idx in param_spec.items():
                    if isinstance(group_idx, int):
                        params[param_name] = match.group(group_idx)
                    else:
                        params[param_name] = group_idx

                logger.info(f"Parsed command: {cmd_type.value} with params {params}")

                return ParsedCommand(
                    type=cmd_type,
                    params=params,
                    raw_text=text,
                    confidence=1.0
                )

        # No match found
        logger.warning(f"Could not parse command: {text}")
        return ParsedCommand(
            type=CommandType.UNKNOWN,
            params={},
            raw_text=text,
            confidence=0.0
        )

    def parse_voice(self, audio_text: str) -> Optional[ParsedCommand]:
        """
        Parse voice-transcribed text (future feature).

        Args:
            audio_text: Transcribed audio from Whisper API

        Returns:
            ParsedCommand or None
        """
        # For now, just use regular parse
        # Future: Add voice-specific preprocessing
        return self.parse(audio_text)

    def suggest_commands(self, partial: str) -> list[str]:
        """
        Suggest commands based on partial input (for autocomplete).

        Args:
            partial: Partial command text

        Returns:
            List of suggested commands
        """
        suggestions = []
        partial_lower = partial.lower()

        # Common commands
        commands = [
            "show agent status",
            "show content queue",
            "deploy to production",
            "kb stats",
            "show metrics",
            "health check",
        ]

        for cmd in commands:
            if partial_lower in cmd.lower():
                suggestions.append(cmd)

        return suggestions[:5]  # Top 5 suggestions
