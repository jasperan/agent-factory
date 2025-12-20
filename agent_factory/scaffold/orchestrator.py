"""SCAFFOLD Platform - Main Orchestrator

Coordinates all SCAFFOLD components for autonomous task execution.

Workflow:
1. Fetch eligible tasks from Backlog.md
2. Check safety limits
3. Allocate worktree
4. Route to handler
5. Execute task
6. Process result (create PR, update Backlog.md)
7. Cleanup worktree
8. Repeat until queue empty or safety limit hit
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from agent_factory.scaffold.task_fetcher import TaskFetcher
from agent_factory.scaffold.task_router import TaskRouter, TaskExecutionError
from agent_factory.scaffold.session_manager import SessionManager
from agent_factory.scaffold.result_processor import ResultProcessor

logger = logging.getLogger(__name__)


class ScaffoldOrchestratorError(Exception):
    """Base exception for ScaffoldOrchestrator errors."""
    pass


class ScaffoldOrchestrator:
    """Main orchestration loop for SCAFFOLD platform.

    Ties together all components:
    - TaskFetcher: Query Backlog.md for eligible tasks
    - TaskRouter: Route tasks to handlers
    - SessionManager: Manage worktrees and safety
    - ResultProcessor: Create PRs and update Backlog.md

    Example:
        >>> orch = ScaffoldOrchestrator(
        ...     repo_root=Path.cwd(),
        ...     dry_run=True,
        ...     max_tasks=10
        ... )
        >>> summary = orch.run()
        >>> print(f"Completed: {summary['tasks_completed']}")
    """

    def __init__(
        self,
        repo_root: Path,
        dry_run: bool = False,
        max_tasks: int = 10,
        max_concurrent: int = 3,
        max_cost: float = 5.0,
        max_time_hours: float = 4.0,
        labels: Optional[List[str]] = None
    ):
        """Initialize ScaffoldOrchestrator.

        Args:
            repo_root: Root directory of git repository
            dry_run: If True, log actions without executing
            max_tasks: Maximum tasks to process
            max_concurrent: Maximum concurrent worktrees
            max_cost: Maximum API cost in USD
            max_time_hours: Maximum wall-clock time in hours
            labels: Optional label filter for tasks
        """
        self.repo_root = Path(repo_root).resolve()
        self.dry_run = dry_run
        self.max_tasks = max_tasks
        self.labels = labels

        # Components
        self.task_fetcher = TaskFetcher(cache_ttl_sec=60)
        self.router = TaskRouter()
        self.session_mgr = SessionManager(
            repo_root=repo_root,
            max_concurrent=max_concurrent,
            max_cost=max_cost,
            max_time_hours=max_time_hours
        )
        self.result_processor = ResultProcessor()

        # Logging
        self.logger = logging.getLogger("scaffold_orchestrator")

        if dry_run:
            self.logger.info("SCAFFOLD Orchestrator initialized (DRY RUN MODE)")
        else:
            self.logger.info("SCAFFOLD Orchestrator initialized")

        self.logger.info(f"Config: max_tasks={max_tasks}, max_concurrent={max_concurrent}, max_cost=${max_cost:.2f}, max_time={max_time_hours}h")

    def run(self) -> Dict[str, Any]:
        """Main orchestration loop.

        Returns:
            Summary dict with session statistics

        Raises:
            ScaffoldOrchestratorError: If critical error occurs
        """
        try:
            # Start session
            session_id = self.session_mgr.start_session(
                max_tasks=self.max_tasks,
                max_cost=self.session_mgr.max_cost,
                max_time_hours=self.session_mgr.max_time_hours
            )
            self.logger.info(f"Session {session_id} started (dry_run={self.dry_run})")

            # Fetch eligible tasks
            tasks = self.task_fetcher.fetch_eligible_tasks(
                max_tasks=self.max_tasks,
                labels=self.labels
            )

            if not tasks:
                self.logger.info("No eligible tasks found")
                return self._build_summary()

            # Queue tasks
            self.session_mgr.state.tasks_queued = [t["id"] for t in tasks]
            self.logger.info(f"Queued {len(tasks)} tasks")

            # Log task list
            for i, task in enumerate(tasks, 1):
                self.logger.info(f"  {i}. {task['id']}: {task.get('title', 'Untitled')} (priority={task.get('priority', 'low')})")

            # Process each task
            for i, task in enumerate(tasks, 1):
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"Processing task {i}/{len(tasks)}: {task['id']}")
                self.logger.info(f"{'='*60}")

                # Check safety limits
                can_continue, reason = self.session_mgr.check_can_continue()
                if not can_continue:
                    self.logger.error(f"Safety limit hit: {reason}")
                    self.logger.error("Stopping session early")
                    break

                # Dry-run mode
                if self.dry_run:
                    self.logger.info(f"[DRY RUN] Would execute {task['id']}: {task.get('title', 'Untitled')}")
                    self.logger.info(f"[DRY RUN] Priority: {task.get('priority', 'low')}, Labels: {task.get('labels', [])}")
                    continue

                # Execute with recovery
                success = self._execute_task_with_recovery(task)

                # Track result
                if success:
                    self.session_mgr.state.tasks_completed.append(task["id"])
                    self.logger.info(f"✓ Task {task['id']} completed successfully")
                else:
                    self.session_mgr.state.tasks_failed.append(task["id"])
                    self.logger.warning(f"✗ Task {task['id']} failed")

            # Build summary
            summary = self._build_summary()

            # Log final summary
            self._log_summary(summary)

            return summary

        except KeyboardInterrupt:
            self.logger.warning("Session interrupted by user (Ctrl+C)")
            return self._build_summary()

        except Exception as e:
            self.logger.error(f"Critical error in orchestrator: {e}", exc_info=True)
            raise ScaffoldOrchestratorError(f"Orchestration failed: {e}") from e

    def _handle_task_failure(
        self,
        task_id: str,
        error: str,
        cost: float = 0.0,
        worktree_path: Optional[str] = None
    ) -> bool:
        """
        Handle task execution failure with cleanup.

        Args:
            task_id: Task identifier
            error: Error message
            cost: Execution cost (USD)
            worktree_path: Worktree path (if any)

        Returns:
            False (failure indicator)
        """
        self.logger.error(f"Task execution failed: {error}")

        # Process failure
        self.result_processor.process_failure(
            task_id=task_id,
            error=error,
            cost=cost,
            dry_run=self.dry_run
        )

        # Record in SafetyMonitor
        self.session_mgr.record_task_failure(
            task_id=task_id,
            error=error,
            cost=cost
        )

        # Cleanup worktree (force)
        if worktree_path:
            try:
                self.session_mgr.cleanup_worktree(task_id, force=True)
            except Exception as cleanup_err:
                self.logger.error(f"Cleanup failed: {cleanup_err}")

        return False

    def _execute_task_with_recovery(self, task: Dict) -> bool:
        """Execute task with error handling and recovery.

        Args:
            task: Task dict

        Returns:
            True if successful, False otherwise
        """
        task_id = task["id"]
        self.logger.info(f"Executing {task_id}: {task.get('title', 'Untitled')}")

        worktree_path = None

        try:
            # Create worktree
            self.logger.info(f"Creating worktree for {task_id}")
            worktree_path = self.session_mgr.allocate_worktree(task_id)
            self.logger.info(f"Worktree created: {worktree_path}")

            # Route to handler
            handler_name = self.router.route(task)
            handler = self.router.get_handler(handler_name)
            self.logger.info(f"Routing to {handler_name} handler")

            # Execute
            self.logger.info(f"Executing task via {handler_name}")
            result = handler.execute(task, worktree_path)

            # Process result
            if result["success"]:
                self.logger.info("Task execution succeeded")

                # Process success
                pr_url = self.result_processor.process_success(
                    task_id=task_id,
                    result=result,
                    dry_run=self.dry_run
                )

                if pr_url:
                    self.logger.info(f"PR created: {pr_url}")

                # Record in SafetyMonitor
                self.session_mgr.record_task_success(
                    task_id=task_id,
                    cost=result.get("cost", 0.0),
                    duration_sec=result.get("duration_sec", 0.0)
                )

                # Cleanup worktree
                self.session_mgr.cleanup_worktree(task_id)

                return True
            else:
                # Execution failed - handle directly
                return self._handle_task_failure(
                    task_id=task_id,
                    error=result.get("output", "Unknown error"),
                    cost=0.0,
                    worktree_path=worktree_path
                )

        except TaskExecutionError as e:
            # Handle exceptions from handler.execute()
            return self._handle_task_failure(
                task_id=task_id,
                error=str(e),
                cost=0.0,
                worktree_path=worktree_path
            )


        except Exception as e:
            self.logger.error(f"Unexpected error executing task {task_id}: {e}", exc_info=True)

            # Process failure
            self.result_processor.process_failure(
                task_id=task_id,
                error=f"Unexpected error: {e}",
                cost=0.0,
                dry_run=self.dry_run
            )

            # Record in SafetyMonitor
            self.session_mgr.record_task_failure(
                task_id=task_id,
                error=str(e),
                cost=0.0
            )

            # Cleanup worktree (force)
            if worktree_path:
                try:
                    self.session_mgr.cleanup_worktree(task_id, force=True)
                except Exception as cleanup_err:
                    self.logger.error(f"Cleanup failed: {cleanup_err}")

            return False

    def _build_summary(self) -> Dict[str, Any]:
        """Build session summary.

        Returns:
            Summary dict
        """
        if not self.session_mgr.state:
            return {
                "error": "No session state",
                "dry_run": self.dry_run
            }

        state = self.session_mgr.state

        summary = {
            "session_id": state.session_id,
            "dry_run": self.dry_run,
            "tasks_queued": len(state.tasks_queued),
            "tasks_in_progress": len(state.tasks_in_progress),
            "tasks_completed": len(state.tasks_completed),
            "tasks_failed": len(state.tasks_failed),
            "total_cost": state.total_cost,
            "total_duration_sec": state.total_duration_sec
        }

        # Add safety stats if available
        try:
            summary["safety_stats"] = self.session_mgr.safety.get_stats()
        except Exception:
            # Safety stats are optional - continue without them
            pass

        return summary

    def _log_summary(self, summary: Dict[str, Any]):
        """Log session summary.

        Args:
            summary: Summary dict
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("SCAFFOLD Session Summary")
        self.logger.info("="*60)
        self.logger.info(f"Session ID: {summary.get('session_id', 'unknown')}")
        self.logger.info(f"Dry Run: {summary.get('dry_run', False)}")
        self.logger.info(f"Tasks Queued: {summary.get('tasks_queued', 0)}")
        self.logger.info(f"Tasks In Progress: {summary.get('tasks_in_progress', 0)}")
        self.logger.info(f"Tasks Completed: {summary.get('tasks_completed', 0)}")
        self.logger.info(f"Tasks Failed: {summary.get('tasks_failed', 0)}")
        self.logger.info(f"Total Cost: ${summary.get('total_cost', 0.0):.2f}")
        self.logger.info(f"Total Duration: {summary.get('total_duration_sec', 0.0):.1f}s")
        self.logger.info("="*60)

        # Log detailed task lists
        if self.session_mgr.state:
            state = self.session_mgr.state

            if state.tasks_completed:
                self.logger.info("\nCompleted Tasks:")
                for task_id in state.tasks_completed:
                    self.logger.info(f"  ✓ {task_id}")

            if state.tasks_failed:
                self.logger.info("\nFailed Tasks:")
                for task_id in state.tasks_failed:
                    self.logger.info(f"  ✗ {task_id}")

            if state.tasks_in_progress:
                self.logger.info("\nTasks Still In Progress (cleanup recommended):")
                for task_id in state.tasks_in_progress:
                    self.logger.info(f"  ⧗ {task_id}")
