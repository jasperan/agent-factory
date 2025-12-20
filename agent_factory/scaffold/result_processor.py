"""SCAFFOLD Platform - Result Processor

Processes task execution results (success/failure).

Features:
- Create draft PRs on success
- Update Backlog.md status
- Log execution details
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ResultProcessorError(Exception):
    """Base exception for ResultProcessor errors."""
    pass


class ResultProcessor:
    """Process task execution results.

    Features:
    - Create draft PRs via PRCreator on success
    - Update Backlog.md task status via MCP
    - Add implementation notes with cost/duration
    - Handle failures gracefully

    Example:
        >>> processor = ResultProcessor()
        >>> pr_url = processor.process_success("task-42", result)
        >>> processor.process_failure("task-43", "Timeout")
    """

    def __init__(self):
        """Initialize ResultProcessor."""
        # Import PRCreator lazily to avoid circular imports
        self._pr_creator = None

    def process_success(
        self,
        task_id: str,
        result: Dict,
        dry_run: bool = False
    ) -> Optional[str]:
        """Process successful task completion.

        Args:
            task_id: Task identifier
            result: Execution result dict with keys: cost, duration_sec, files_changed
            dry_run: If True, log actions without executing

        Returns:
            PR URL (None if dry-run or PR creation failed)
        """
        cost = result.get("cost", 0.0)
        duration = result.get("duration_sec", 0.0)
        files = result.get("files_changed", [])

        logger.info(f"Processing success for {task_id}: cost=${cost:.2f}, duration={duration:.1f}s, {len(files)} files")

        pr_url = None

        # Create PR (if not dry-run)
        if not dry_run:
            pr_url = self._create_pr(task_id, result)
        else:
            logger.info(f"[DRY RUN] Would create PR for {task_id}")

        # Update Backlog.md status
        if not dry_run:
            self._update_backlog_status(
                task_id=task_id,
                status="Done",
                notes=self._format_success_notes(pr_url, cost, duration, files)
            )
        else:
            logger.info(f"[DRY RUN] Would update {task_id} status to Done")

        return pr_url

    def process_failure(
        self,
        task_id: str,
        error: str,
        cost: float = 0.0,
        dry_run: bool = False
    ):
        """Process task failure.

        Args:
            task_id: Task identifier
            error: Error message
            cost: API cost in USD (if any)
            dry_run: If True, log actions without executing
        """
        logger.warning(f"Processing failure for {task_id}: {error}")

        # Update Backlog.md with failure notes
        if not dry_run:
            self._update_backlog_status(
                task_id=task_id,
                status="Blocked",
                notes=self._format_failure_notes(error, cost)
            )
        else:
            logger.info(f"[DRY RUN] Would update {task_id} status to Blocked")

    def _create_pr(self, task_id: str, result: Dict) -> Optional[str]:
        """Create draft PR via PRCreator.

        Args:
            task_id: Task identifier
            result: Execution result

        Returns:
            PR URL (None if creation failed)
        """
        try:
            # Lazy import PRCreator
            if not self._pr_creator:
                import sys
                from pathlib import Path
                project_root = Path(__file__).parent.parent.parent
                project_root_str = str(project_root)
                if project_root_str not in sys.path:
                    sys.path.insert(0, project_root_str)
                from scripts.autonomous.pr_creator import PRCreator
                self._pr_creator = PRCreator()

            # Extract issue number from task_id
            # Simple heuristic: use hash for now
            # TODO: Improve mapping task_id → GitHub issue number
            issue_number = abs(hash(task_id)) % 10000

            # Create PR
            pr_url = self._pr_creator.create_draft_pr(
                issue_number=issue_number,
                claude_result=result
            )

            logger.info(f"PR created: {pr_url}")
            return pr_url

        except ImportError:
            logger.warning("PRCreator not available - skipping PR creation")
            return None

        except Exception as e:
            logger.exception(f"Failed to create PR for {task_id}: {e}")
            # Continue anyway - don't block on PR failures
            return None

    def _update_backlog_status(
        self,
        task_id: str,
        status: str,
        notes: str
    ):
        """Update Backlog.md task status via MCP.

        Args:
            task_id: Task identifier
            status: New status ("Done" or "Blocked")
            notes: Implementation notes to append
        """
        try:
            # Import MCP tool
            from mcp import mcp__backlog__task_edit

            # Update task
            mcp__backlog__task_edit(
                id=task_id,
                status=status,
                implementation_notes=notes
            )

            logger.info(f"Backlog.md updated: {task_id} → {status}")

        except ImportError:
            logger.warning("MCP backlog tools not available - skipping Backlog update")

        except Exception as e:
            logger.exception(f"Failed to update Backlog.md for {task_id}: {e}")
            # Continue anyway - don't block on Backlog failures

    def _format_success_notes(
        self,
        pr_url: Optional[str],
        cost: float,
        duration: float,
        files: list
    ) -> str:
        """Format success notes for Backlog.md.

        Args:
            pr_url: PR URL (if created)
            cost: API cost
            duration: Execution time
            files: Changed files

        Returns:
            Formatted notes
        """
        notes_parts = []

        if pr_url:
            notes_parts.append(f"PR created: {pr_url}")
        else:
            notes_parts.append("PR creation skipped")

        notes_parts.append(f"\nCost: ${cost:.2f}")
        notes_parts.append(f"Duration: {duration:.1f}s")

        if files:
            notes_parts.append(f"\nFiles changed ({len(files)}):")
            for file in files[:10]:  # Limit to first 10
                notes_parts.append(f"- {file}")
            if len(files) > 10:
                notes_parts.append(f"... and {len(files) - 10} more")

        return "\n".join(notes_parts)

    def _format_failure_notes(self, error: str, cost: float) -> str:
        """Format failure notes for Backlog.md.

        Args:
            error: Error message
            cost: API cost (if any)

        Returns:
            Formatted notes
        """
        notes_parts = [
            f"Execution failed: {error}",
            f"\nCost: ${cost:.2f}"
        ]

        return "\n".join(notes_parts)

    def _extract_issue_number(self, task_id: str) -> int:
        """Extract GitHub issue number from task_id.

        Current implementation uses hash as placeholder.
        TODO: Implement proper task_id → issue_number mapping.

        Args:
            task_id: Task identifier

        Returns:
            Issue number
        """
        # Use hash as simple mapping
        # In production, would query Backlog.md for GitHub issue link
        return abs(hash(task_id)) % 10000
