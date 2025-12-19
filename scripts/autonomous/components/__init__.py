"""
SCAFFOLD Orchestrator Components

Core components for autonomous task execution:
- TaskFetcher: Query Backlog.md for eligible tasks
- AgentRouter: Route tasks to appropriate agents
- SessionManager: Track execution sessions
- ResultProcessor: Update task status after completion
"""

from .task_fetcher import TaskFetcher
from .agent_router import AgentRouter
from .session_manager import SessionManager, Session
from .result_processor import ResultProcessor

__all__ = [
    "TaskFetcher",
    "AgentRouter",
    "SessionManager",
    "Session",
    "ResultProcessor",
]
