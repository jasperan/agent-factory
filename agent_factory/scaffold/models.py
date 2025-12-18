"""SCAFFOLD Platform - Data Models

Data models for SCAFFOLD autonomous development system.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WorktreeMetadata:
    """Metadata for a git worktree managed by SCAFFOLD.

    Attributes:
        task_id: Unique task identifier (e.g., "task-42")
        worktree_path: Absolute path to worktree directory
        branch_name: Git branch name (e.g., "autonomous/task-42")
        created_at: ISO 8601 timestamp of creation
        creator: Who created this worktree (e.g., "scaffold-orchestrator", "agentcli")
        status: Current status (active|stale|merged|abandoned)
        pr_url: GitHub PR URL if created (optional)
    """
    task_id: str
    worktree_path: str
    branch_name: str
    created_at: str
    creator: str
    status: str  # "active", "stale", "merged", "abandoned"
    pr_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "worktree_path": self.worktree_path,
            "branch_name": self.branch_name,
            "created_at": self.created_at,
            "creator": self.creator,
            "status": self.status,
            "pr_url": self.pr_url
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorktreeMetadata":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            task_id=data["task_id"],
            worktree_path=data["worktree_path"],
            branch_name=data["branch_name"],
            created_at=data["created_at"],
            creator=data["creator"],
            status=data["status"],
            pr_url=data.get("pr_url")
        )


@dataclass
class TaskContext:
    """Task specification for SCAFFOLD execution.

    Attributes:
        task_id: Unique task identifier (e.g., "task-42")
        title: Task title
        description: Detailed task description
        acceptance_criteria: List of acceptance criteria
        priority: Task priority (high|medium|low)
        labels: Task labels/tags
    """
    task_id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    priority: str
    labels: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "priority": self.priority,
            "labels": self.labels
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskContext":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            acceptance_criteria=data["acceptance_criteria"],
            priority=data["priority"],
            labels=data["labels"]
        )
