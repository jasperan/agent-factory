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
from pathlib import Path

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
            logger.debug("Using markdown fallback mode (MCP disabled)")

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
            return self._list_tasks_markdown(status, labels, dependencies_satisfied, limit)

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
            return self._get_task_markdown(task_id)

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
            return self._update_status_markdown(task_id, new_status)

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
            return self._add_notes_markdown(task_id, notes, append)

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

    def add_task(self, task: TaskSpec) -> bool:
        """Add a new task to Backlog.md.

        Args:
            task: TaskSpec to add

        Returns:
            True if successful
        """
        if not self._mcp_available:
            return self._add_task_markdown(task)

        try:
            from mcp import mcp__backlog__task_add
            mcp__backlog__task_add(**task.to_dict())
            return True
        except Exception as e:
            logger.error(f"Failed to add task via MCP: {e}")
            return self._add_task_markdown(task)

    # --- Markdown Fallback Methods ---

    def _get_backlog_dir(self) -> Path:
        """Get directory containing task files."""
        return Path("backlog/tasks")

    def _get_backlog_summary_path(self) -> Path:
        """Get path to the summary backlog.md."""
        return Path("backlog.md")

    def _list_tasks_markdown(self, status=None, labels=None, dependencies_satisfied=False, limit=100) -> List[TaskSpec]:
        """Fallback: Parse backlog tasks from the tasks directory."""
        tasks_dir = self._get_backlog_dir()
        tasks = []
        
        if not tasks_dir.exists():
            # Fallback to summary file if tasks dir missing
            summary_path = self._get_backlog_summary_path()
            if not summary_path.exists():
                return []
            return self._parse_file_for_tasks(summary_path, status, limit)

        try:
            # Scan all .md files in the tasks directory
            for task_file in tasks_dir.glob("*.md"):
                file_tasks = self._parse_file_for_tasks(task_file, status, limit - len(tasks))
                tasks.extend(file_tasks)
                if len(tasks) >= limit:
                    break
            return tasks
        except Exception as e:
            logger.error(f"Manual backlog parse failed in {tasks_dir}: {e}")
            return []

    def _parse_file_for_tasks(self, path: Path, status_filter=None, limit=100) -> List[TaskSpec]:
        """Helper to parse a single markdown file for tasks."""
        tasks = []
        try:
            content = path.read_text()
            import re
            
            # Look for task ID in filename if not in content (e.g., task-86)
            filename_id = None
            filename_match = re.search(r'(task-\w+)', path.name)
            if filename_match:
                filename_id = filename_match.group(1)

            # Split by headers
            blocks = re.split(r'\n(?=#{1,4} )', content)
            if len(blocks) == 1 and filename_id:
                # Whole file is one task
                blocks = [content]

            for block in blocks:
                # Find ID: <!-- id: task-id --> or in YAML frontmatter id: task-id
                id_match = re.search(r'(?:<!-- id: |id: )(["\']?)(task-[\w\.]+)\1', block)
                tid = id_match.group(2) if id_match else filename_id
                
                if not tid:
                    continue
                
                # Find Title and Status
                title_match = re.search(r'#+ (?:\[(.*?)\] )?(.*)', block)
                status_val = "To Do"
                title = tid
                
                if title_match:
                    status_val = title_match.group(1) or "To Do"
                    title = title_match.group(2).split("<!--")[0].strip()
                
                # Check status filter
                if status_filter and status_val.lower() != status_filter.lower():
                    continue
                
                # Basic TaskSpec creation
                task = TaskSpec(
                    task_id=tid,
                    title=title,
                    description=block[:500] + "..." if len(block) > 500 else block,
                    status=status_val,
                    priority="medium",
                    labels=[],
                    dependencies=[],
                    acceptance_criteria=[]
                )
                tasks.append(task)
                if len(tasks) >= limit:
                    break
            return tasks
        except Exception as e:
            logger.error(f"Failed to parse tasks from {path}: {e}")
            return []

    def _get_task_markdown(self, task_id: str) -> TaskSpec:
        tasks = self._list_tasks_markdown()
        for t in tasks:
            if t.task_id == task_id: return t
        raise BacklogParserError(f"Task {task_id} not found in markdown")

    def _update_status_markdown(self, task_id: str, new_status: str) -> bool:
        path = self._get_backlog_path()
        if not path.exists(): return False
        content = path.read_text()
        import re
        # Look for the task block and update the status in brackets
        pattern = rf'### \[.*?\] (.*?) <!-- id: {re.escape(task_id)} -->'
        replacement = f'### [{new_status}] \\1 <!-- id: {task_id} -->'
        new_content = re.sub(pattern, replacement, content)
        path.write_text(new_content)
        return True

    def _add_task_markdown(self, task: TaskSpec) -> bool:
        path = self._get_backlog_path()
        task_markdown = f"\n### [{task.status}] {task.title} <!-- id: {task.task_id} -->\n{task.description}\n"
        if task.priority:
            task_markdown += f"- **Priority**: {task.priority}\n"
        if task.labels:
            task_markdown += f"- **Labels**: {', '.join(task.labels)}\n"
        
        with open(path, "a") as f:
            f.write(task_markdown)
        return True

    def _add_notes_markdown(self, task_id: str, notes: str, append: bool) -> bool:
        # Simplified: just append to the end of the file for now if fallback
        path = self._get_backlog_path()
        with open(path, "a") as f:
            f.write(f"\n\n#### Implementation Notes for {task_id}\n{notes}\n")
        return True
