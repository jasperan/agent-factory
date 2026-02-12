"""
Autonomous Code Improvement System

This module provides autonomous code improvement capabilities using a
Planner → Worker → Judge pipeline powered by local Ollama models via OpenHands SDK.
"""

from .models import (
    Suggestion,
    SuggestionStatus,
    SuggestionCategory,
    Verdict,
    VerdictStatus,
    AutonomousRun,
    RunStatus,
)
from .config import AutonomousConfig
from .suggestion_generator import SuggestionGenerator
from .autonomous_runner import AutonomousRunner

__all__ = [
    # Models
    "Suggestion",
    "SuggestionStatus",
    "SuggestionCategory",
    "Verdict",
    "VerdictStatus",
    "AutonomousRun",
    "RunStatus",
    # Config
    "AutonomousConfig",
    # Core
    "SuggestionGenerator",
    "AutonomousRunner",
]
