"""PRCreator Usage Demo

Demonstrates how to use PRCreator to create draft PRs after task completion.

This example shows:
1. Creating a task context
2. Preparing a worktree with changes
3. Creating a draft PR
4. Handling success and failure cases
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.scaffold.pr_creator import PRCreator, create_pr_creator
from agent_factory.scaffold.models import TaskContext


def demo_pr_creation():
    """Demonstrate basic PR creation workflow."""
    print("=" * 70)
    print("PRCreator Demo - SCAFFOLD Platform")
    print("=" * 70)
    print()

    # 1. Create task context
    print("1. Creating task context...")
    task = TaskContext(
        task_id="task-123",
        title="Fix authentication bug",
        description="Fix session timeout issue in user authentication system",
        acceptance_criteria=[
            "Bug fixed and verified",
            "Tests passing",
            "Documentation updated"
        ],
        priority="high",
        labels=["bug", "auth"]
    )
    print(f"   Task: {task.task_id} - {task.title}")
    print(f"   Priority: {task.priority}")
    print(f"   Criteria: {len(task.acceptance_criteria)} items")
    print()

    # 2. Initialize PRCreator
    print("2. Initializing PRCreator...")
    repo_root = Path.cwd()
    pr_creator = create_pr_creator(repo_root=repo_root)
    print(f"   Repo root: {pr_creator.repo_root}")
    print(f"   GitHub CLI: {pr_creator.gh_cmd}")
    print(f"   Remote: {pr_creator.remote}")
    print()

    # 3. Show generated commit message
    print("3. Generated commit message:")
    print("-" * 70)
    commit_msg = pr_creator._generate_commit_message(task)
    print(commit_msg)
    print("-" * 70)
    print()

    # 4. Show generated PR title
    print("4. Generated PR title:")
    pr_title = pr_creator._generate_pr_title(task)
    print(f"   {pr_title}")
    print()

    # 5. Show generated PR body
    print("5. Generated PR body:")
    print("-" * 70)
    pr_body = pr_creator._generate_pr_body(task)
    print(pr_body)
    print("-" * 70)
    print()

    # 6. Explain actual usage
    print("6. Actual usage (requires git worktree):")
    print()
    print("   # After task execution completes in worktree...")
    print("   worktree_path = '/path/to/agent-factory-task-123'")
    print("   result = pr_creator.create_pr(task, worktree_path)")
    print()
    print("   if result.success:")
    print(f"       print(f'PR created: {{result.pr_url}}')")
    print(f"       print(f'PR number: {{result.pr_number}}')")
    print(f"       print(f'Branch: {{result.branch}}')")
    print(f"       print(f'Commits: {{result.commits_pushed}}')")
    print("   else:")
    print(f"       print(f'PR failed: {{result.error}}')")
    print()

    print("=" * 70)
    print("Demo Complete")
    print("=" * 70)


def demo_different_task_types():
    """Demonstrate PR titles for different task types."""
    print()
    print("=" * 70)
    print("PR Title Generation for Different Task Types")
    print("=" * 70)
    print()

    pr_creator = create_pr_creator()

    task_types = [
        TaskContext(
            task_id="task-bug-1",
            title="Fix memory leak in cache",
            description="Description",
            acceptance_criteria=["Fixed"],
            priority="high",
            labels=["bug", "performance"]
        ),
        TaskContext(
            task_id="task-feat-1",
            title="Add user profile page",
            description="Description",
            acceptance_criteria=["Implemented"],
            priority="medium",
            labels=["feature", "ui"]
        ),
        TaskContext(
            task_id="task-docs-1",
            title="Update API documentation",
            description="Description",
            acceptance_criteria=["Updated"],
            priority="low",
            labels=["documentation"]
        ),
        TaskContext(
            task_id="task-test-1",
            title="Add unit tests for auth module",
            description="Description",
            acceptance_criteria=["Tests added"],
            priority="medium",
            labels=["test", "auth"]
        ),
        TaskContext(
            task_id="task-refactor-1",
            title="Refactor database connection pool",
            description="Description",
            acceptance_criteria=["Refactored"],
            priority="low",
            labels=["refactor", "database"]
        )
    ]

    for task in task_types:
        title = pr_creator._generate_pr_title(task)
        print(f"Labels: {', '.join(task.labels)}")
        print(f"Title:  {title}")
        print()


def demo_pr_result_serialization():
    """Demonstrate PRResult serialization/deserialization."""
    print()
    print("=" * 70)
    print("PRResult Serialization Demo")
    print("=" * 70)
    print()

    from agent_factory.scaffold.models import PRResult

    # 1. Create successful result
    print("1. Creating successful PRResult...")
    result = PRResult(
        success=True,
        pr_url="https://github.com/org/repo/pull/42",
        pr_number=42,
        branch="autonomous/task-123",
        error=None,
        commits_pushed=["abc1234", "def5678"]
    )
    print(f"   Success: {result.success}")
    print(f"   PR URL: {result.pr_url}")
    print(f"   PR Number: {result.pr_number}")
    print(f"   Branch: {result.branch}")
    print(f"   Commits: {result.commits_pushed}")
    print()

    # 2. Serialize to dict
    print("2. Serializing to dict...")
    data = result.to_dict()
    print(f"   Dict keys: {list(data.keys())}")
    print()

    # 3. Deserialize from dict
    print("3. Deserializing from dict...")
    restored = PRResult.from_dict(data)
    print(f"   Restored success: {restored.success}")
    print(f"   Restored URL: {restored.pr_url}")
    print(f"   Match: {restored.pr_url == result.pr_url}")
    print()

    # 4. Create failed result
    print("4. Creating failed PRResult...")
    failed = PRResult(
        success=False,
        pr_url=None,
        pr_number=None,
        branch="autonomous/task-456",
        error="Failed to push branch: authentication failed",
        commits_pushed=[]
    )
    print(f"   Success: {failed.success}")
    print(f"   Error: {failed.error}")
    print()


if __name__ == "__main__":
    # Run demos
    demo_pr_creation()
    demo_different_task_types()
    demo_pr_result_serialization()

    print()
    print("All demos completed successfully!")
