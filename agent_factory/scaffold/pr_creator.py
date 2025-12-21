"""SCAFFOLD Platform - PR Creator

Creates draft pull requests automatically after successful task execution.

Features:
- Commits all changes in worktree with detailed message
- Pushes branch to remote origin
- Creates draft PR using GitHub CLI (gh)
- Includes task ID, summary, acceptance criteria in PR body
- Returns PR URL on success

Example:
    >>> pr_creator = PRCreator(repo_root=Path.cwd())
    >>> task = TaskContext(
    ...     task_id="task-123",
    ...     title="Fix authentication bug",
    ...     description="Fix session timeout issue",
    ...     acceptance_criteria=["Bug fixed", "Tests passing"],
    ...     priority="high",
    ...     labels=["bug", "auth"]
    ... )
    >>> result = pr_creator.create_pr(task, "/path/to/worktree")
    >>> if result.success:
    ...     print(f"PR created: {result.pr_url}")
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import Optional

from agent_factory.scaffold.models import TaskContext, PRResult

logger = logging.getLogger(__name__)


class PRCreatorError(Exception):
    """Base exception for PRCreator errors."""
    pass


class PRCreator:
    """Create draft pull requests automatically after task execution.

    Handles the complete PR creation workflow:
    1. Validates worktree has changes
    2. Commits changes with detailed message
    3. Pushes branch to remote
    4. Creates draft PR via GitHub CLI
    5. Returns PR URL and metadata
    """

    def __init__(
        self,
        repo_root: Path,
        gh_cmd: str = "gh",
        remote: str = "origin"
    ):
        """Initialize PRCreator.

        Args:
            repo_root: Root directory of repository
            gh_cmd: GitHub CLI command (default: "gh")
            remote: Git remote name (default: "origin")
        """
        self.repo_root = Path(repo_root).resolve()
        self.gh_cmd = gh_cmd
        self.remote = remote

    def create_pr(
        self,
        task: TaskContext,
        worktree_path: str,
        commit_message: Optional[str] = None
    ) -> PRResult:
        """Create draft PR for completed task.

        Args:
            task: TaskContext with task details
            worktree_path: Path to git worktree
            commit_message: Custom commit message (optional, auto-generated if None)

        Returns:
            PRResult with success status, PR URL, number, branch, commits

        Workflow:
            1. Check for uncommitted changes (fail if clean)
            2. Commit changes with detailed message
            3. Push branch to remote
            4. Create draft PR via gh CLI
            5. Extract PR URL and number
        """
        task_id = task.task_id
        branch = f"autonomous/{task_id}"
        logger.info(f"Creating PR for task {task_id} from worktree {worktree_path}")

        try:
            # 1. Validate worktree has changes
            if not self._has_changes(worktree_path):
                error = "No changes to commit (clean working tree)"
                logger.error(f"Task {task_id}: {error}")
                return PRResult(
                    success=False,
                    pr_url=None,
                    pr_number=None,
                    branch=branch,
                    error=error,
                    commits_pushed=[]
                )

            # 2. Commit changes
            commit_msg = commit_message or self._generate_commit_message(task)
            commit_sha = self._commit_changes(worktree_path, commit_msg)

            if not commit_sha:
                error = "Failed to commit changes"
                logger.error(f"Task {task_id}: {error}")
                return PRResult(
                    success=False,
                    pr_url=None,
                    pr_number=None,
                    branch=branch,
                    error=error,
                    commits_pushed=[]
                )

            # 3. Push branch
            push_success = self._push_branch(worktree_path, branch)

            if not push_success:
                error = f"Failed to push branch {branch} to {self.remote}"
                logger.error(f"Task {task_id}: {error}")
                return PRResult(
                    success=False,
                    pr_url=None,
                    pr_number=None,
                    branch=branch,
                    error=error,
                    commits_pushed=[commit_sha]
                )

            # 4. Create draft PR
            pr_url, pr_number = self._create_draft_pr(
                worktree_path,
                task,
                branch
            )

            if not pr_url:
                error = "Failed to create PR via GitHub CLI"
                logger.error(f"Task {task_id}: {error}")
                return PRResult(
                    success=False,
                    pr_url=None,
                    pr_number=None,
                    branch=branch,
                    error=error,
                    commits_pushed=[commit_sha]
                )

            # 5. Success!
            logger.info(
                f"Task {task_id}: PR #{pr_number} created successfully at {pr_url}"
            )

            return PRResult(
                success=True,
                pr_url=pr_url,
                pr_number=pr_number,
                branch=branch,
                error=None,
                commits_pushed=[commit_sha]
            )

        except Exception as e:
            error = f"Unexpected error during PR creation: {str(e)}"
            logger.exception(f"Task {task_id}: {error}")
            return PRResult(
                success=False,
                pr_url=None,
                pr_number=None,
                branch=branch,
                error=error,
                commits_pushed=[]
            )

    def _has_changes(self, worktree_path: str) -> bool:
        """Check if worktree has uncommitted changes.

        Args:
            worktree_path: Path to worktree

        Returns:
            True if changes exist, False if clean
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            # If output is empty, working tree is clean
            return bool(result.stdout.strip())

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Could not check git status: {e}")
            return False

    def _commit_changes(self, worktree_path: str, commit_message: str) -> Optional[str]:
        """Commit all changes in worktree.

        Args:
            worktree_path: Path to worktree
            commit_message: Commit message

        Returns:
            Commit SHA (7 chars) if successful, None if failed
        """
        try:
            # Stage all changes
            result = subprocess.run(
                ["git", "add", "."],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"git add failed: {result.stderr}")
                return None

            # Commit with message
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"git commit failed: {result.stderr}")
                return None

            # Get commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                commit_sha = result.stdout.strip()
                logger.info(f"Created commit {commit_sha}")
                return commit_sha

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"Commit failed: {e}")
            return None

    def _push_branch(self, worktree_path: str, branch: str) -> bool:
        """Push branch to remote origin.

        Args:
            worktree_path: Path to worktree
            branch: Branch name (e.g., "autonomous/task-123")

        Returns:
            True if successful, False if failed
        """
        try:
            # Push with -u to set upstream tracking
            result = subprocess.run(
                ["git", "push", "-u", self.remote, branch],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"git push failed: {result.stderr}")
                return False

            logger.info(f"Pushed branch {branch} to {self.remote}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("git push timeout (60s)")
            return False
        except FileNotFoundError:
            logger.error("git command not found")
            return False

    def _create_draft_pr(
        self,
        worktree_path: str,
        task: TaskContext,
        branch: str
    ) -> tuple[Optional[str], Optional[int]]:
        """Create draft PR using GitHub CLI.

        Args:
            worktree_path: Path to worktree
            task: TaskContext with task details
            branch: Branch name

        Returns:
            Tuple of (pr_url, pr_number) if successful, (None, None) if failed
        """
        try:
            # Generate PR title and body
            pr_title = self._generate_pr_title(task)
            pr_body = self._generate_pr_body(task)

            # Create PR via gh CLI
            result = subprocess.run(
                [
                    self.gh_cmd,
                    "pr", "create",
                    "--title", pr_title,
                    "--body", pr_body,
                    "--draft",
                    "--head", branch
                ],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"gh pr create failed: {result.stderr}")
                return None, None

            # Extract PR URL from output
            # gh CLI returns URL on last line of stdout
            output = result.stdout.strip()
            pr_url = self._extract_pr_url(output)

            if not pr_url:
                logger.error(f"Could not extract PR URL from output: {output}")
                return None, None

            # Extract PR number from URL
            pr_number = self._extract_pr_number(pr_url)

            logger.info(f"Created draft PR #{pr_number} at {pr_url}")
            return pr_url, pr_number

        except subprocess.TimeoutExpired:
            logger.error("gh pr create timeout (60s)")
            return None, None
        except FileNotFoundError:
            logger.error("gh CLI not found - is GitHub CLI installed?")
            return None, None

    def _generate_commit_message(self, task: TaskContext) -> str:
        """Generate detailed commit message from task.

        Format:
            {task.title}

            {task.description}

            Acceptance Criteria:
            - [ ] {criterion 1}
            - [ ] {criterion 2}

            Generated with [Claude Code](https://claude.com/claude-code)

            Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

        Args:
            task: TaskContext with task details

        Returns:
            Formatted commit message
        """
        # Build acceptance criteria checklist
        criteria_lines = []
        for criterion in task.acceptance_criteria:
            criteria_lines.append(f"- [ ] {criterion}")

        criteria_text = "\n".join(criteria_lines) if criteria_lines else "- [ ] Complete implementation"

        # Format message
        message = f"""{task.title}

{task.description}

Acceptance Criteria:
{criteria_text}

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""

        return message

    def _generate_pr_title(self, task: TaskContext) -> str:
        """Generate PR title from task.

        Format: feat: {task.title} (task-{id})

        Args:
            task: TaskContext

        Returns:
            PR title
        """
        # Determine prefix from labels
        if "bug" in task.labels or "fix" in task.labels:
            prefix = "fix"
        elif "docs" in task.labels or "documentation" in task.labels:
            prefix = "docs"
        elif "test" in task.labels or "testing" in task.labels:
            prefix = "test"
        elif "refactor" in task.labels:
            prefix = "refactor"
        else:
            prefix = "feat"

        return f"{prefix}: {task.title}"

    def _generate_pr_body(self, task: TaskContext) -> str:
        """Generate PR body from task.

        Format:
            ## Task: {task_id}

            {task.description}

            ### Acceptance Criteria
            - [ ] {criterion 1}
            - [ ] {criterion 2}

            ### Implementation Notes
            [Auto-generated by SCAFFOLD]

            ---
            Generated with [Claude Code](https://claude.com/claude-code)

        Args:
            task: TaskContext

        Returns:
            Formatted PR body
        """
        # Build acceptance criteria checklist
        criteria_lines = []
        for criterion in task.acceptance_criteria:
            criteria_lines.append(f"- [ ] {criterion}")

        criteria_text = "\n".join(criteria_lines) if criteria_lines else "- [ ] Complete implementation"

        # Format body
        body = f"""## Task: {task.task_id}

{task.description}

### Acceptance Criteria
{criteria_text}

### Implementation Notes
[Auto-generated by SCAFFOLD]

---
Generated with [Claude Code](https://claude.com/claude-code)"""

        return body

    def _extract_pr_url(self, gh_output: str) -> Optional[str]:
        """Extract PR URL from gh CLI output.

        Args:
            gh_output: stdout from gh pr create

        Returns:
            PR URL if found, None otherwise
        """
        # gh CLI typically returns URL on last line
        lines = gh_output.strip().split('\n')
        for line in reversed(lines):
            # Look for GitHub PR URL pattern
            match = re.search(r'https://github\.com/[^/]+/[^/]+/pull/\d+', line)
            if match:
                return match.group(0)

        return None

    def _extract_pr_number(self, pr_url: str) -> Optional[int]:
        """Extract PR number from GitHub PR URL.

        Args:
            pr_url: GitHub PR URL (e.g., "https://github.com/org/repo/pull/42")

        Returns:
            PR number (e.g., 42) if found, None otherwise
        """
        match = re.search(r'/pull/(\d+)', pr_url)
        if match:
            return int(match.group(1))
        return None


def create_pr_creator(
    repo_root: Optional[Path] = None,
    gh_cmd: str = "gh",
    remote: str = "origin"
) -> PRCreator:
    """Factory function to create PRCreator.

    Args:
        repo_root: Repository root (defaults to cwd)
        gh_cmd: GitHub CLI command
        remote: Git remote name

    Returns:
        PRCreator instance
    """
    if repo_root is None:
        repo_root = Path.cwd()

    return PRCreator(
        repo_root=repo_root,
        gh_cmd=gh_cmd,
        remote=remote
    )
