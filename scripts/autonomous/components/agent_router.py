"""
AgentRouter - Route Tasks to Appropriate Agents

Routes tasks to execution agents based on:
1. Explicit label: agent:claude-code → Claude Code CLI
2. Title prefix: BUILD:, FIX:, TEST: → Claude Code
3. Domain keywords: database → DB specialist (future)
4. Default: Claude Code CLI
"""

from typing import Dict


class AgentRouter:
    """Match tasks to execution agents."""

    def __init__(self):
        """Initialize AgentRouter with routing rules."""
        self.routes = {
            "claude-code": self._route_claude_code,
            # Future: "database": self._route_database_agent,
            # Future: "content": self._route_content_agent,
        }

    def route_task(self, task: Dict) -> str:
        """
        Determine which agent should execute this task.

        Routing Priority Order:
        1. Explicit agent label (agent:claude-code)
        2. Title prefix (BUILD:, FIX:, TEST:)
        3. Domain keywords (database, api, etc.)
        4. Default (claude-code)

        Args:
            task: Task dictionary with 'labels' and 'title' fields

        Returns:
            Agent ID string (e.g., 'claude-code')
        """
        # Check explicit agent label
        labels = task.get("labels", [])
        for label in labels:
            if label.startswith("agent:"):
                agent_id = label.split(":", 1)[1]
                return agent_id

        # Check title prefix
        title = task.get("title", "")
        if any(title.startswith(p) for p in ["BUILD:", "FIX:", "TEST:", "REFACTOR:"]):
            return "claude-code"

        # Check domain keywords (future routing)
        if self._has_keyword(task, ["database", "sql", "postgres", "migration"]):
            # Future: Return "database" agent
            return "claude-code"  # Week 1: Default to claude-code

        if self._has_keyword(task, ["content", "script", "video", "youtube"]):
            # Future: Return "content" agent
            return "claude-code"  # Week 1: Default to claude-code

        # Default to Claude Code CLI
        return "claude-code"

    def _route_claude_code(self, task: Dict, session):
        """
        Execute task using Claude Code CLI.

        Week 1: Stub implementation (just returns routing decision)
        Week 3: Actually invoke Claude Code CLI

        Args:
            task: Task dictionary
            session: Session object with worktree path

        Returns:
            Execution result dictionary
        """
        # Week 1: Just return routing decision
        # Week 3: Actually execute Claude Code
        return {
            "agent": "claude-code",
            "status": "routed",
            "message": "Week 1 stub - execution pending Week 3",
        }

    def _has_keyword(self, task: Dict, keywords: list) -> bool:
        """
        Check if task title/description contains any keywords.

        Args:
            task: Task dictionary with 'title' and optional 'description'
            keywords: List of keywords to search for

        Returns:
            True if any keyword found, False otherwise
        """
        title = task.get("title", "").lower()
        description = task.get("description", "").lower()
        labels = [l.lower() for l in task.get("labels", [])]

        combined = f"{title} {description} {' '.join(labels)}"

        return any(keyword.lower() in combined for keyword in keywords)
