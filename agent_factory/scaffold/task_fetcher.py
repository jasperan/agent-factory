"""SCAFFOLD Platform - Task Fetcher

Queries Backlog.md via MCP for eligible tasks.

Features:
- Fetches tasks with status="To Do"
- Filters for dependencies satisfied
- Sorts by priority score
- 60-second caching to reduce MCP calls
"""

import time
import logging
from typing import List, Dict, Optional

from agent_factory.scaffold.backlog_parser import BacklogParser, TaskSpec

logger = logging.getLogger(__name__)


class TaskFetcher:
    """Fetch eligible tasks from Backlog.md via MCP.

    Features:
    - Query Backlog.md via MCP tools
    - Filter for eligible tasks (status="To Do", dependencies satisfied)
    - Sort by priority score (high/critical first)
    - Cache results for 60 seconds

    Example:
        >>> fetcher = TaskFetcher(cache_ttl_sec=60)
        >>> tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        >>> print(f"Found {len(tasks)} eligible tasks")
    """

    def __init__(self, cache_ttl_sec: int = 60):
        """Initialize TaskFetcher.

        Args:
            cache_ttl_sec: Cache TTL in seconds (default: 60)
        """
        self._cache: Optional[List[Dict]] = None
        self._cache_time: Optional[float] = None
        self._cache_ttl = cache_ttl_sec
        self._parser = BacklogParser()

    def fetch_eligible_tasks(
        self,
        max_tasks: int = 10,
        labels: Optional[List[str]] = None
    ) -> List[Dict]:
        """Fetch eligible tasks from Backlog.md with caching.

        Args:
            max_tasks: Maximum tasks to return
            labels: Optional label filter (e.g., ["build", "rivet-pro"])

        Returns:
            List of task dicts, sorted by priority (highest first)
        """
        # Check cache
        if self._cache and (time.time() - self._cache_time < self._cache_ttl):
            logger.debug("Using cached tasks")
            filtered = self._cache
            if labels:
                filtered = [t for t in filtered if any(label in t.get("labels", []) for label in labels)]
            return filtered[:max_tasks]

        try:
            # Query Backlog.md via BacklogParser (fetch extra to filter locally)
            logger.info(f"Fetching tasks from Backlog.md (limit={max_tasks * 2})")

            # Use BacklogParser to fetch tasks with dependencies satisfied
            task_specs = self._parser.list_tasks(
                status="To Do",
                labels=labels,
                dependencies_satisfied=True,
                limit=max_tasks * 2
            )

            # Convert TaskSpec objects to dicts for backward compatibility
            tasks = [spec.to_dict() for spec in task_specs]

            # Sort by priority score
            tasks.sort(key=lambda t: self._priority_score(t), reverse=True)

            # Update cache
            self._cache = tasks
            self._cache_time = time.time()

            logger.info(f"Found {len(tasks)} eligible tasks")

            return tasks[:max_tasks]

        except Exception as e:
            logger.exception(f"Error fetching tasks: {e}")
            return []

    def _priority_score(self, task: Dict) -> float:
        """Calculate priority score for sorting (0-100).

        Scoring:
        - Base priority: high=10, medium=5, low=1
        - Label bonuses: critical=+5, quick-win=+3
        - Label penalties: user-action=-10 (deprioritize manual)
        - Age bonus: +0-2 based on days old

        Args:
            task: Task dict

        Returns:
            Priority score (0-100, higher = more important)
        """
        # Base priority
        priority_map = {"high": 10, "medium": 5, "low": 1}
        base = priority_map.get(task.get("priority", "low"), 1)

        # Label bonuses/penalties
        labels = task.get("labels", [])
        bonus = 0

        if "critical" in labels:
            bonus += 5
        if "quick-win" in labels:
            bonus += 3
        if "user-action" in labels:
            bonus -= 10  # Deprioritize manual tasks

        # Age factor (older = slightly higher priority)
        age_bonus = self._calculate_age_bonus(task)

        score = base + bonus + age_bonus

        logger.debug(f"Task {task.get('id', 'unknown')}: score={score:.1f} (base={base}, bonus={bonus}, age={age_bonus:.1f})")

        return max(0, score)  # Ensure non-negative

    def _calculate_age_bonus(self, task: Dict) -> float:
        """Calculate age bonus (0-2 based on days old).

        Args:
            task: Task dict

        Returns:
            Age bonus (0-2)
        """
        created_date = task.get("created_date", "")

        if not created_date:
            return 0.0

        try:
            from datetime import datetime
            created = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            now = datetime.now(created.tzinfo)
            age_days = (now - created).days
            # Cap at 60 days = 2.0 bonus
            return min(age_days / 30, 2.0)
        except Exception as e:
            logger.debug(f"Could not calculate age: {e}")
            return 0.0

    def _get_placeholder_tasks(self, max_tasks: int) -> List[Dict]:
        """Return placeholder tasks when MCP not available.

        Args:
            max_tasks: Maximum tasks to return

        Returns:
            List of placeholder task dicts
        """
        return [
            {
                "id": "task-placeholder-1",
                "title": "Placeholder Task 1",
                "description": "MCP tools not available",
                "status": "To Do",
                "priority": "medium",
                "labels": [],
                "dependencies": []
            }
        ][:max_tasks]

    def invalidate_cache(self):
        """Invalidate cache to force fresh fetch on next call."""
        self._cache = None
        self._cache_time = None
        logger.debug("Cache invalidated")
