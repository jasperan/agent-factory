"""SCAFFOLD Platform - Backlog Parser

Clean wrapper around Backlog.md MCP tools for task management.

Features:
- List tasks with filters (status, labels, dependencies)
- Get task details as TaskSpec objects
- Update task status (To Do → In Progress → Done)
- Add implementation notes to tasks
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TaskSpec:
    """Task specification from Backlog.md.

    Attributes:
        task_id: Unique task identifier
        title: Task title
        description: Task description
        status: Current status (To Do, In Progress, Done)
        priority: Task priority (high, medium, low)
        labels: Task labels/tags
        dependencies: List of task IDs this depends on
        acceptance_criteria: List of acceptance criteria
        assignee: List of assignees
        parent_task_id: Parent task ID (if subtask)
        created_date: Creation date
        implementation_notes: Implementation notes
    """
    task_id: str
    title: str
    description: str
    status: str
    priority: str
    labels: List[str]
    dependencies: List[str]
    acceptance_criteria: List[str]
    assignee: List[str] = None
    parent_task_id: Optional[str] = None
    created_date: Optional[str] = None
    implementation_notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "TaskSpec":
        """Create TaskSpec from MCP task dict.

        Args:
            data: Task dict from MCP

        Returns:
            TaskSpec instance
        """
        return cls(
            task_id=data.get("id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=data.get("status", "To Do"),
            priority=data.get("priority", "medium"),
            labels=data.get("labels", []),
            dependencies=data.get("dependencies", []),
            acceptance_criteria=data.get("acceptance_criteria", []),
            assignee=data.get("assignee", []),
            parent_task_id=data.get("parent_task_id"),
            created_date=data.get("created_date"),
            implementation_notes=data.get("implementation_notes")
        )

    def to_dict(self) -> Dict:
        """Convert to dict for serialization.

        Returns:
            Dict representation
        """
        return {
            "id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "labels": self.labels,
            "dependencies": self.dependencies,
            "acceptance_criteria": self.acceptance_criteria,
            "assignee": self.assignee,
            "parent_task_id": self.parent_task_id,
            "created_date": self.created_date,
            "implementation_notes": self.implementation_notes
        }


class BacklogParserError(Exception):
    """Base exception for BacklogParser errors."""
    pass


class BacklogParser:
    """Clean wrapper around Backlog.md MCP tools.

    Features:
    - List tasks with filters
    - Get task details as TaskSpec objects
    - Update task status
    - Add implementation notes

    Example:
        >>> parser = BacklogParser()
        >>> tasks = parser.list_tasks(status="To Do", labels=["scaffold"])
        >>> task = parser.get_task("task-scaffold-orchestrator")
        >>> parser.update_status("task-42", "In Progress")
        >>> parser.add_notes("task-42", "Started implementation")
    """

    def __init__(self):
        """Initialize BacklogParser."""
        self._mcp_available = self._check_mcp_available()

        if not self._mcp_available:
            logger.warning("MCP backlog tools not available - using fallback mode")

    def list_tasks(
        self,
        status: Optional[str] = None,
        labels: Optional[List[str]] = None,
        dependencies_satisfied: bool = False,
        limit: int = 100
    ) -> List[TaskSpec]:
        """List tasks from Backlog.md with filters.

        Args:
            status: Filter by status (e.g., "To Do", "In Progress", "Done")
            labels: Filter by labels (must have at least one)
            dependencies_satisfied: If True, only return tasks with all deps Done
            limit: Maximum tasks to return

        Returns:
            List of TaskSpec objects
        """
        if not self._mcp_available:
            logger.warning("MCP not available - returning empty list")
            return []

        try:
            from mcp import mcp__backlog__task_list

            # Query MCP
            tasks = mcp__backlog__task_list(
                status=status,
                limit=limit
            )

            # Convert to TaskSpec objects
            task_specs = [TaskSpec.from_dict(t) for t in tasks]

            # Apply label filter if provided
            if labels:
                task_specs = [
                    t for t in task_specs
                    if any(label in t.labels for label in labels)
                ]

            # Apply dependencies filter if requested
            if dependencies_satisfied:
                task_specs = [
                    t for t in task_specs
                    if self._are_dependencies_satisfied(t)
                ]

            logger.info(f"Listed {len(task_specs)} tasks (status={status}, labels={labels})")

            return task_specs

        except Exception as e:
            logger.exception(f"Error listing tasks: {e}")
            raise BacklogParserError(f"Failed to list tasks: {e}") from e

    def get_task(self, task_id: str) -> TaskSpec:
        """Get task details by ID.

        Args:
            task_id: Task identifier

        Returns:
            TaskSpec object

        Raises:
            BacklogParserError: If task not found or error occurs
        """
        if not self._mcp_available:
            raise BacklogParserError("MCP not available")

        try:
            from mcp import mcp__backlog__task_view

            # Query MCP
            task_dict = mcp__backlog__task_view(id=task_id)

            # Convert to TaskSpec
            task_spec = TaskSpec.from_dict(task_dict)

            logger.debug(f"Retrieved task {task_id}: {task_spec.title}")

            return task_spec

        except Exception as e:
            logger.exception(f"Error getting task {task_id}: {e}")
            raise BacklogParserError(f"Failed to get task {task_id}: {e}") from e

    def update_status(
        self,
        task_id: str,
        new_status: str
    ) -> bool:
        """Update task status.

        Args:
            task_id: Task identifier
            new_status: New status ("To Do", "In Progress", "Done")

        Returns:
            True if successful

        Raises:
            BacklogParserError: If update fails
        """
        valid_statuses = ["To Do", "In Progress", "Done"]

        if new_status not in valid_statuses:
            raise BacklogParserError(
                f"Invalid status: {new_status}. Must be one of: {valid_statuses}"
            )

        if not self._mcp_available:
            raise BacklogParserError("MCP not available")

        try:
            from mcp import mcp__backlog__task_edit

            # Update via MCP
            mcp__backlog__task_edit(
                id=task_id,
                status=new_status
            )

            logger.info(f"Updated {task_id} status → {new_status}")

            return True

        except Exception as e:
            logger.exception(f"Error updating status for {task_id}: {e}")
            raise BacklogParserError(f"Failed to update status: {e}") from e

    def add_notes(
        self,
        task_id: str,
        notes: str,
        append: bool = True
    ) -> bool:
        """Add implementation notes to task.

        Args:
            task_id: Task identifier
            notes: Notes to add
            append: If True, append to existing notes; if False, replace

        Returns:
            True if successful

        Raises:
            BacklogParserError: If update fails
        """
        if not self._mcp_available:
            raise BacklogParserError("MCP not available")

        try:
            from mcp import mcp__backlog__task_edit

            if append:
                # Get current notes and append
                task = self.get_task(task_id)
                current_notes = task.implementation_notes or ""
                new_notes = f"{current_notes}\n\n{notes}".strip()
            else:
                new_notes = notes

            # Update via MCP
            mcp__backlog__task_edit(
                id=task_id,
                implementation_notes=new_notes
            )

            logger.info(f"Added notes to {task_id} ({len(notes)} chars)")

            return True

        except Exception as e:
            logger.exception(f"Error adding notes to {task_id}: {e}")
            raise BacklogParserError(f"Failed to add notes: {e}") from e

    def _check_mcp_available(self) -> bool:
        """Check if MCP backlog tools are available.

        Returns:
            True if MCP tools available
        """
        try:
            from mcp import mcp__backlog__task_list
            return True
        except ImportError:
            return False

    def _are_dependencies_satisfied(self, task: TaskSpec) -> bool:
        """Check if all task dependencies are satisfied.

        Args:
            task: TaskSpec to check

        Returns:
            True if all dependencies are Done
        """
        if not task.dependencies:
            return True

        try:
            for dep_id in task.dependencies:
                dep_task = self.get_task(dep_id)
                if dep_task.status != "Done":
                    logger.debug(f"Task {task.task_id} blocked by {dep_id} (status={dep_task.status})")
                    return False

            return True

        except Exception as e:
            logger.warning(f"Error checking dependencies for {task.task_id}: {e}")
            return False
