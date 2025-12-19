"""
SessionManager - Track Execution Sessions

Manages active task execution sessions:
- Creates worktree paths for tasks
- Tracks active sessions (in-memory)
- Enforces concurrency limits (max 3 sessions)
- Records start time, task ID, worktree path

Week 1 Scope: Tracking only (no actual worktree creation)
Week 2 Scope: Actually create/cleanup worktrees
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict


@dataclass
class Session:
    """
    Represents an active task execution session.

    Attributes:
        session_id: Unique session identifier
        task_id: Backlog.md task ID
        worktree_path: Path to git worktree
        start_time: When session started
        agent_type: Agent handling this task (e.g., "claude-code")
        status: Session status ("active", "complete", "failed")
    """
    session_id: str
    task_id: str
    worktree_path: Path
    start_time: datetime
    agent_type: str
    status: str  # "active", "complete", "failed"


class SessionManager:
    """Track active execution sessions and enforce limits."""

    def __init__(self, repo_root: Path, max_concurrent: int = 3):
        """
        Initialize SessionManager.

        Args:
            repo_root: Path to main repository root
            max_concurrent: Maximum concurrent sessions allowed
        """
        self.repo_root = repo_root
        self.max_concurrent = max_concurrent
        self.active_sessions: Dict[str, Session] = {}

    def can_create_session(self) -> bool:
        """
        Check if a new session can be created.

        Returns:
            True if under max_concurrent limit, False otherwise
        """
        return len(self.active_sessions) < self.max_concurrent

    def create_session(self, task_id: str, agent_type: str) -> Session:
        """
        Create a new execution session.

        Week 1: Only tracks session metadata (no actual worktree creation)
        Week 2: Actually create git worktree

        Args:
            task_id: Backlog.md task ID
            agent_type: Agent handling this task

        Returns:
            Session object

        Raises:
            RuntimeError: If max concurrent sessions reached
        """
        if not self.can_create_session():
            raise RuntimeError(
                f"Max concurrent sessions ({self.max_concurrent}) reached. "
                f"Active sessions: {list(self.active_sessions.keys())}"
            )

        # Generate session ID
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        session_id = f"session-{timestamp}"

        # Create worktree path
        worktree_path = self.repo_root.parent / f"agent-factory-{task_id}"

        # Week 1: Don't actually create worktree yet
        # Week 2: Add git worktree add command
        # Example: subprocess.run(["git", "worktree", "add", str(worktree_path), "-b", f"task/{task_id}"])

        session = Session(
            session_id=session_id,
            task_id=task_id,
            worktree_path=worktree_path,
            start_time=datetime.now(),
            agent_type=agent_type,
            status="active"
        )

        self.active_sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Session:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session object

        Raises:
            KeyError: If session not found
        """
        return self.active_sessions[session_id]

    def close_session(self, session_id: str, success: bool):
        """
        Close an execution session.

        Week 1: Just updates status and removes from active sessions
        Week 2: Cleanup worktree if failed, keep if success (for PR)

        Args:
            session_id: Session identifier
            success: Whether task execution succeeded

        Raises:
            KeyError: If session not found
        """
        session = self.active_sessions.pop(session_id)
        session.status = "complete" if success else "failed"

        # Week 2: Cleanup worktree if failed
        # if not success:
        #     subprocess.run(["git", "worktree", "remove", str(session.worktree_path)])

        # Week 2: Keep worktree if success (for PR creation)

    def list_active_sessions(self) -> Dict[str, Session]:
        """
        Get all active sessions.

        Returns:
            Dictionary of session_id -> Session
        """
        return self.active_sessions.copy()

    def get_active_count(self) -> int:
        """
        Get count of active sessions.

        Returns:
            Number of active sessions
        """
        return len(self.active_sessions)
