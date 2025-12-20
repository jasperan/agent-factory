"""SCAFFOLD Platform - Session Manager

Manages session state, worktrees, and safety limits.

Features:
- Integrates WorktreeManager for worktree lifecycle
- Integrates SafetyMonitor for cost/time/failure tracking
- Persists session state to .scaffold/sessions/{id}.json
- Resume functionality for interrupted sessions
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from agent_factory.scaffold.worktree_manager import WorktreeManager
from agent_factory.scaffold.models import SessionState

# Import SafetyMonitor from scripts (absolute import)
import sys
project_root = Path(__file__).parent.parent.parent
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)
from scripts.autonomous.safety_monitor import SafetyMonitor

logger = logging.getLogger(__name__)


class SessionManagerError(Exception):
    """Base exception for SessionManager errors."""
    pass


class SessionNotFoundError(SessionManagerError):
    """Raised when session not found for resume."""
    pass


class SessionManager:
    """Manage SCAFFOLD orchestration sessions.

    Features:
    - Start/resume sessions with unique IDs
    - Allocate/cleanup worktrees
    - Track session state (queued/in-progress/completed/failed)
    - Check safety limits (cost/time/failures)
    - Persist state to .scaffold/sessions/{id}.json

    Example:
        >>> manager = SessionManager(repo_root=Path.cwd())
        >>> session_id = manager.start_session(max_tasks=10)
        >>> worktree_path = manager.allocate_worktree("task-42")
        >>> can_continue, reason = manager.check_can_continue()
        >>> manager.cleanup_worktree("task-42")
    """

    def __init__(
        self,
        repo_root: Path,
        max_concurrent: int = 3,
        max_cost: float = 5.0,
        max_time_hours: float = 4.0
    ):
        """Initialize SessionManager.

        Args:
            repo_root: Root directory of git repository
            max_concurrent: Maximum concurrent worktrees (default: 3)
            max_cost: Maximum API cost in USD (default: 5.0)
            max_time_hours: Maximum wall-clock time in hours (default: 4.0)
        """
        self.repo_root = Path(repo_root).resolve()
        self.max_cost = max_cost
        self.max_time_hours = max_time_hours

        # Components
        self.worktree_mgr = WorktreeManager(
            repo_root=repo_root,
            max_concurrent=max_concurrent
        )
        self.safety = SafetyMonitor(
            max_cost=max_cost,
            max_time_hours=max_time_hours,
            max_consecutive_failures=3
        )

        # Session state
        self.state: Optional[SessionState] = None

        # Ensure sessions directory exists
        self._sessions_dir = self.repo_root / ".scaffold" / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    def start_session(
        self,
        max_tasks: int = 10,
        max_cost: Optional[float] = None,
        max_time_hours: Optional[float] = None
    ) -> str:
        """Start new orchestration session.

        Args:
            max_tasks: Maximum tasks to process
            max_cost: Override default max cost
            max_time_hours: Override default max time

        Returns:
            Session ID (e.g., "20251218_140000")
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.state = SessionState(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            max_tasks=max_tasks,
            max_cost=max_cost or self.max_cost,
            max_time_hours=max_time_hours or self.max_time_hours,
            tasks_queued=[],
            tasks_in_progress={},
            tasks_completed=[],
            tasks_failed=[]
        )

        # Save initial state
        self._save_state()

        logger.info(f"Session {session_id} started (max_tasks={max_tasks}, max_cost=${self.state.max_cost:.2f}, max_time={self.state.max_time_hours}h)")

        return session_id

    def resume_session(self, session_id: str):
        """Resume previous session from saved state.

        Args:
            session_id: Session ID to resume

        Raises:
            SessionNotFoundError: If session file not found
        """
        session_file = self._sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")

        try:
            self.state = SessionState.from_dict(json.loads(session_file.read_text()))
            logger.info(f"Session {session_id} resumed")
        except Exception as e:
            raise SessionManagerError(f"Failed to resume session: {e}")

    def allocate_worktree(self, task_id: str) -> str:
        """Allocate worktree for task.

        Args:
            task_id: Task identifier

        Returns:
            Absolute path to worktree

        Raises:
            WorktreeExistsError: If worktree already exists
            WorktreeLimitError: If max concurrent limit reached
        """
        if not self.state:
            raise SessionManagerError("No active session - call start_session() first")

        logger.info(f"Allocating worktree for {task_id}")

        worktree_path = self.worktree_mgr.create_worktree(
            task_id=task_id,
            creator="scaffold-orchestrator"
        )

        # Track in session state
        self.state.tasks_in_progress[task_id] = worktree_path
        self._save_state()

        logger.debug(f"Worktree allocated: {worktree_path}")

        return worktree_path

    def cleanup_worktree(self, task_id: str, force: bool = False):
        """Cleanup worktree after task completion/failure.

        Args:
            task_id: Task identifier
            force: Force cleanup even if changes exist
        """
        if not self.state:
            raise SessionManagerError("No active session")

        logger.info(f"Cleaning up worktree for {task_id} (force={force})")

        try:
            self.worktree_mgr.cleanup_worktree(task_id, force=force)

            # Remove from session state
            if task_id in self.state.tasks_in_progress:
                del self.state.tasks_in_progress[task_id]
                self._save_state()

            logger.debug(f"Worktree cleaned up: {task_id}")

        except Exception as e:
            logger.exception(f"Failed to cleanup worktree {task_id}: {e}")
            # Continue anyway - don't block on cleanup failures

    def check_can_continue(self) -> Tuple[bool, Optional[str]]:
        """Check if session can continue based on safety limits.

        Returns:
            Tuple of (can_continue, stop_reason)
            - can_continue: True if safe to continue
            - stop_reason: Reason for stopping (if can_continue=False)
        """
        if not self.state:
            return False, "No active session"

        return self.safety.check_limits()

    def record_task_success(
        self,
        task_id: str,
        cost: float,
        duration_sec: float
    ):
        """Record successful task completion.

        Args:
            task_id: Task identifier
            cost: API cost in USD
            duration_sec: Execution time in seconds
        """
        if not self.state:
            raise SessionManagerError("No active session")

        # Update SafetyMonitor
        self.safety.record_issue_success(
            issue_number=task_id,
            cost=cost,
            duration_sec=duration_sec
        )

        # Update session totals
        self.state.total_cost += cost
        self.state.total_duration_sec += duration_sec

        self._save_state()

        logger.info(f"Task {task_id} success recorded (cost=${cost:.2f}, duration={duration_sec:.1f}s)")

    def record_task_failure(
        self,
        task_id: str,
        error: str,
        cost: float = 0.0
    ):
        """Record task failure.

        Args:
            task_id: Task identifier
            error: Error message
            cost: API cost in USD (if any)
        """
        if not self.state:
            raise SessionManagerError("No active session")

        # Update SafetyMonitor
        self.safety.record_issue_failure(
            issue_number=task_id,
            error=error,
            cost=cost
        )

        # Update session totals
        if cost > 0:
            self.state.total_cost += cost

        self._save_state()

        logger.warning(f"Task {task_id} failure recorded: {error}")

    def get_session_summary(self) -> dict:
        """Get current session summary.

        Returns:
            Dict with session statistics
        """
        if not self.state:
            return {"error": "No active session"}

        return {
            "session_id": self.state.session_id,
            "start_time": self.state.start_time,
            "tasks_queued": len(self.state.tasks_queued),
            "tasks_in_progress": len(self.state.tasks_in_progress),
            "tasks_completed": len(self.state.tasks_completed),
            "tasks_failed": len(self.state.tasks_failed),
            "total_cost": self.state.total_cost,
            "total_duration_sec": self.state.total_duration_sec,
            "safety_stats": self.safety.get_stats()
        }

    def _save_state(self):
        """Save session state to JSON file."""
        if not self.state:
            return

        session_file = self._sessions_dir / f"{self.state.session_id}.json"

        try:
            with open(session_file, 'w') as f:
                json.dump(self.state.to_dict(), f, indent=2)

            logger.debug(f"Session state saved: {session_file}")

        except Exception as e:
            logger.exception(f"Failed to save session state: {e}")
            # Don't raise - continue execution

    def list_sessions(self) -> list:
        """List all saved sessions.

        Returns:
            List of session IDs (sorted newest first)
        """
        session_files = sorted(
            self._sessions_dir.glob("*.json"),
            reverse=True
        )

        return [f.stem for f in session_files]
