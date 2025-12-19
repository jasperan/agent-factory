"""
ResultProcessor - Update Task Status After Execution

Updates Backlog.md after task execution:
- Success: Mark status="Done", add PR link
- Failure: Mark status="Blocked", add error notes

Week 1 Scope: Stub implementation (logs to console only)
Week 4 Scope: Actually update Backlog.md via MCP
"""

from typing import Optional


class ResultProcessor:
    """Update Backlog.md after task execution."""

    def __init__(self, mcp_client=None):
        """
        Initialize ResultProcessor.

        Args:
            mcp_client: MCP client wrapper (optional for Week 1 stub)
        """
        self.mcp = mcp_client

    def process_success(self, task_id: str, pr_url: Optional[str] = None):
        """
        Process successful task completion.

        Week 1: Just logs to console
        Week 4: Update Backlog.md status="Done", add PR link

        Args:
            task_id: Backlog.md task ID
            pr_url: Optional pull request URL
        """
        # Week 1: Just log
        print(f"[SUCCESS] {task_id}")
        if pr_url:
            print(f"  PR: {pr_url}")

        # Week 4: Actually update Backlog
        # if self.mcp:
        #     self.mcp.task_edit(
        #         id=task_id,
        #         status="Done",
        #         notesAppend=[f"Completed by SCAFFOLD orchestrator\nPR: {pr_url}"]
        #     )

    def process_failure(self, task_id: str, error: str):
        """
        Process failed task execution.

        Week 1: Just logs to console
        Week 4: Update Backlog.md status="Blocked", add error notes

        Args:
            task_id: Backlog.md task ID
            error: Error message describing failure
        """
        # Week 1: Just log
        print(f"[FAILED] {task_id}: {error}")

        # Week 4: Update Backlog
        # if self.mcp:
        #     self.mcp.task_edit(
        #         id=task_id,
        #         status="Blocked",
        #         notesAppend=[f"Failed: {error}"]
        #     )

    def process_partial(self, task_id: str, completed_items: list, remaining_items: list):
        """
        Process partially completed task.

        Week 1: Just logs to console
        Week 4: Update Backlog.md acceptance criteria checkboxes

        Args:
            task_id: Backlog.md task ID
            completed_items: List of completed acceptance criteria indices
            remaining_items: List of remaining acceptance criteria indices
        """
        # Week 1: Just log
        print(f"[PARTIAL] {task_id}")
        print(f"  Completed: {completed_items}")
        print(f"  Remaining: {remaining_items}")

        # Week 4: Update acceptance criteria
        # if self.mcp:
        #     self.mcp.task_edit(
        #         id=task_id,
        #         acceptanceCriteriaCheck=completed_items
        #     )
