"""SCAFFOLD Platform - Autonomous Development System

SCAFFOLD = Specification-driven Autonomous Code generation Framework
          for Orchestrated Large-scale Development

Components:
- WorktreeManager: Manages isolated git worktrees for parallel task execution
- ContextAssembler: Prepares execution context for Claude Code CLI (Phase 2)
- PRCreator: Creates draft PRs automatically after task completion (Phase 3)
"""

from agent_factory.scaffold.models import WorktreeMetadata, TaskContext
from agent_factory.scaffold.worktree_manager import (
    WorktreeManager,
    WorktreeManagerError,
    WorktreeExistsError,
    WorktreeNotFoundError,
    WorktreeLimitError,
)

__all__ = [
    # Models
    "WorktreeMetadata",
    "TaskContext",
    # WorktreeManager
    "WorktreeManager",
    "WorktreeManagerError",
    "WorktreeExistsError",
    "WorktreeNotFoundError",
    "WorktreeLimitError",
]

__version__ = "0.1.0"
