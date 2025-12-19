"""
TaskFetcher - Query Backlog.md for Eligible Tasks

Fetches tasks from Backlog.md via MCP that are:
1. Status = "To Do"
2. Labels do NOT include "user-action"
3. All dependencies satisfied (none, or all status="Done")
4. Sorted by priority: critical > high > medium > low
"""

from typing import List, Dict, Optional


class TaskFetcher:
    """Query Backlog.md for eligible tasks via MCP."""

    def __init__(self, mcp_client=None):
        """
        Initialize TaskFetcher.

        Args:
            mcp_client: MCP client wrapper (optional for Week 1 stub)
        """
        self.mcp = mcp_client

    def get_eligible_tasks(
        self,
        labels: Optional[List[str]] = None,
        max_tasks: int = 10
    ) -> List[Dict]:
        """
        Fetch eligible tasks from Backlog.md.

        Eligibility Rules:
        1. Status = "To Do"
        2. Labels do NOT include "user-action"
        3. All dependencies satisfied
        4. Sort by priority: critical > high > medium > low

        Args:
            labels: Filter by labels (default: ["scaffold"])
            max_tasks: Maximum number of tasks to return

        Returns:
            List of task dictionaries sorted by priority
        """
        if labels is None:
            labels = ["scaffold"]

        # Week 1: Stub implementation
        # Week 2: Call actual MCP backlog task list
        if self.mcp is None:
            print("[TaskFetcher] WARNING: MCP client not configured (Week 1 stub)")
            return self._get_stub_tasks(labels)

        # Step 1: Query all "To Do" tasks with labels
        tasks = self.mcp.task_list(status="To Do", labels=labels)

        # Step 2: Filter out "user-action" tasks
        tasks = [t for t in tasks if "user-action" not in t.get("labels", [])]

        # Step 3: Check dependencies satisfied
        tasks = [t for t in tasks if self._deps_satisfied(t)]

        # Step 4: Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        tasks.sort(key=lambda t: priority_order.get(t.get("priority"), 4))

        return tasks[:max_tasks]

    def _deps_satisfied(self, task: Dict) -> bool:
        """
        Check if all task dependencies are satisfied.

        A task's dependencies are satisfied if:
        - It has no dependencies, OR
        - All dependency tasks have status="Done"

        Args:
            task: Task dictionary with 'dependencies' field

        Returns:
            True if dependencies satisfied, False otherwise
        """
        deps = task.get("dependencies", [])
        if not deps:
            return True

        # Query each dependency, check if status="Done"
        for dep_id in deps:
            dep_task = self.mcp.task_view(id=dep_id)
            if dep_task.get("status") != "Done":
                return False

        return True

    def _get_stub_tasks(self, labels: List[str]) -> List[Dict]:
        """
        Return stub task data for Week 1 testing.

        Args:
            labels: Requested labels (for filtering)

        Returns:
            List of stub task dictionaries
        """
        stub_tasks = [
            {
                "id": "task-scaffold-git-manager",
                "title": "BUILD: Git Worktree Manager",
                "status": "To Do",
                "priority": "critical",
                "labels": ["scaffold", "build", "git"],
                "dependencies": ["task-scaffold-orchestrator"],
            },
            {
                "id": "task-scaffold-backlog-parser",
                "title": "BUILD: Backlog Parser",
                "status": "To Do",
                "priority": "high",
                "labels": ["scaffold", "build", "mcp"],
                "dependencies": ["task-scaffold-orchestrator"],
            },
            {
                "id": "task-scaffold-logging",
                "title": "BUILD: Logging System",
                "status": "To Do",
                "priority": "medium",
                "labels": ["scaffold", "build", "logging"],
                "dependencies": [],
            },
        ]

        # Filter by labels
        if labels:
            filtered_tasks = []
            for task in stub_tasks:
                task_labels = task.get("labels", [])
                if any(label in task_labels for label in labels):
                    filtered_tasks.append(task)
            return filtered_tasks

        return stub_tasks
