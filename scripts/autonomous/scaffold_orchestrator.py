#!/usr/bin/env python3
"""
SCAFFOLD Orchestrator - Autonomous Task Execution Loop

Main orchestration loop that:
1. Fetches eligible tasks from Backlog.md via MCP
2. Routes tasks to appropriate agents (Claude Code CLI, custom agents)
3. Executes in isolated git worktrees with resource tracking
4. Updates task status and creates PRs on completion

Week 1 Scope: Core skeleton with dry-run mode
Week 2-5: Execution, PR creation, monitoring, safety

Usage:
    # Dry-run mode (preview eligible tasks)
    poetry run python scripts/autonomous/scaffold_orchestrator.py --dry-run

    # Execute up to 5 tasks
    poetry run python scripts/autonomous/scaffold_orchestrator.py --max-tasks 5

    # Filter by custom labels
    poetry run python scripts/autonomous/scaffold_orchestrator.py --labels build test
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from components.task_fetcher import TaskFetcher
from components.agent_router import AgentRouter
from components.session_manager import SessionManager
from components.result_processor import ResultProcessor


class ScaffoldOrchestrator:
    """Main orchestration loop for autonomous task execution."""

    def __init__(self, repo_root: Path, dry_run: bool = False):
        """
        Initialize SCAFFOLD Orchestrator.

        Args:
            repo_root: Path to repository root
            dry_run: If True, preview tasks without executing
        """
        self.repo_root = repo_root
        self.dry_run = dry_run

        # Initialize components
        self.task_fetcher = TaskFetcher(mcp_client=None)  # TODO: Wrap MCP
        self.agent_router = AgentRouter()
        self.session_manager = SessionManager(repo_root)
        self.result_processor = ResultProcessor(mcp_client=None)

    def run(self, max_tasks: int = 1, labels: List[str] = None):
        """
        Main execution loop.

        Args:
            max_tasks: Maximum number of tasks to execute
            labels: Task labels to filter by
        """
        if labels is None:
            labels = ["scaffold"]

        print("=" * 60)
        print("SCAFFOLD Orchestrator Starting")
        print("=" * 60)
        print(f"Mode:      {'DRY-RUN' if self.dry_run else 'LIVE EXECUTION'}")
        print(f"Max tasks: {max_tasks}")
        print(f"Labels:    {', '.join(labels)}")
        print(f"Repo root: {self.repo_root}")
        print("=" * 60)
        print()

        # Step 1: Fetch eligible tasks
        print("Fetching eligible tasks from Backlog.md...")
        tasks = self.task_fetcher.get_eligible_tasks(labels=labels, max_tasks=max_tasks)

        if not tasks:
            print("No eligible tasks found.")
            print()
            print("Eligibility Rules:")
            print("  - Status = 'To Do'")
            print("  - Labels do NOT include 'user-action'")
            print("  - All dependencies satisfied")
            print("  - Matches requested labels")
            return

        print(f"Found {len(tasks)} eligible task(s):")
        print()
        for i, task in enumerate(tasks, 1):
            priority = task.get("priority", "none")
            deps = task.get("dependencies", [])
            dep_count = len(deps)
            print(f"  {i}. {task['id']}")
            print(f"     Title:    {task.get('title', 'No title')}")
            print(f"     Priority: {priority}")
            print(f"     Deps:     {dep_count} ({', '.join(deps) if deps else 'none'})")
            print()

        if self.dry_run:
            print("=" * 60)
            print("DRY-RUN MODE: Stopping before execution")
            print("=" * 60)
            print()
            print("To execute tasks, run without --dry-run flag:")
            print(f"  poetry run python {Path(__file__).name} --max-tasks {max_tasks}")
            return

        # Step 2: Execute each task
        print("=" * 60)
        print("Starting Task Execution")
        print("=" * 60)
        print()

        for task in tasks[:max_tasks]:
            self._execute_task(task)

        # Step 3: Summary
        print("=" * 60)
        print("Execution Complete")
        print("=" * 60)
        print(f"Tasks processed: {len(tasks[:max_tasks])}")
        print(f"Active sessions: {self.session_manager.get_active_count()}")
        print()

    def _execute_task(self, task: Dict):
        """
        Execute a single task.

        Week 1: Simulated execution (dry-run internally)
        Week 3: Actually invoke Claude Code

        Args:
            task: Task dictionary from Backlog.md
        """
        task_id = task["id"]
        print(f"Executing: {task_id}")
        print(f"  Title: {task.get('title', 'No title')}")

        # Route to agent
        agent_type = self.agent_router.route_task(task)
        print(f"  Agent: {agent_type}")

        # Create session
        if not self.session_manager.can_create_session():
            print(f"  SKIPPED: Max concurrent sessions reached")
            print(f"  Active: {self.session_manager.get_active_count()}")
            print()
            return

        session = self.session_manager.create_session(task_id, agent_type)
        print(f"  Session:  {session.session_id}")
        print(f"  Worktree: {session.worktree_path}")

        # Week 1: Don't actually execute yet
        print(f"  [WEEK 1 STUB] Would execute {agent_type} here")
        print(f"  [WEEK 3] Will invoke Claude Code CLI with task prompt")

        # Close session
        self.session_manager.close_session(session.session_id, success=True)
        print(f"  Status: SUCCESS (simulated)")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SCAFFOLD Orchestrator - Autonomous Task Execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview eligible tasks
  %(prog)s --dry-run

  # Execute next task
  %(prog)s

  # Execute up to 5 tasks
  %(prog)s --max-tasks 5

  # Filter by labels
  %(prog)s --labels build test --dry-run
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview eligible tasks without executing"
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=1,
        help="Maximum number of tasks to execute (default: 1)"
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        default=None,
        help="Task labels to filter by (default: scaffold)"
    )

    args = parser.parse_args()

    # Find repo root (parent of scripts/)
    repo_root = Path(__file__).parent.parent.parent

    # Run orchestrator
    try:
        orchestrator = ScaffoldOrchestrator(repo_root, dry_run=args.dry_run)
        orchestrator.run(max_tasks=args.max_tasks, labels=args.labels)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
