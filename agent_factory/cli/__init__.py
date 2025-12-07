"""
CLI Module - Interactive agent creation tools and chat interface
"""

from .app import app  # Typer app for CLI
from .interactive_creator import InteractiveAgentCreator
from .templates import get_template, list_templates, TEMPLATES
from .wizard_state import WizardState
from .agent_presets import (
    get_research_agent,
    get_coding_agent,
    get_agent,
    list_available_agents
)
from .chat_session import ChatSession
from .agent_editor import AgentEditor, list_editable_agents
from .tool_registry import TOOL_CATALOG, list_tools_by_category

__all__ = [
    # CLI app
    "app",
    # Interactive creator
    "InteractiveAgentCreator",
    "get_template",
    "list_templates",
    "TEMPLATES",
    "WizardState",
    # Agent presets
    "get_research_agent",
    "get_coding_agent",
    "get_agent",
    "list_available_agents",
    # Chat session
    "ChatSession",
    # Agent editor
    "AgentEditor",
    "list_editable_agents",
    # Tool registry
    "TOOL_CATALOG",
    "list_tools_by_category",
]
