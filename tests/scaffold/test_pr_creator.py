"""Tests for SCAFFOLD PRCreator.

Test coverage:
- PR creation success flow
- No changes to commit (clean worktree)
- Git push failures (authentication, network)
- GitHub CLI not installed
- PR already exists for branch
- Invalid worktree path
- Commit message formatting
- PR body formatting
- URL extraction
- PR number extraction
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from agent_factory.scaffold.pr_creator import PRCreator, PRCreatorError, create_pr_creator
from agent_factory.scaffold.models import TaskContext, PRResult


@pytest.fixture
def sample_task():
    """Sample task for testing."""
    return TaskContext(
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


@pytest.fixture
def pr_creator(tmp_path):
    """PRCreator instance with temporary repo."""
    return PRCreator(
        repo_root=tmp_path,
        gh_cmd="gh",
        remote="origin"
    )


class TestPRCreatorInit:
    """Test PRCreator initialization."""

    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default parameters."""
        pr_creator = PRCreator(repo_root=tmp_path)

        assert pr_creator.repo_root == tmp_path.resolve()
        assert pr_creator.gh_cmd == "gh"
        assert pr_creator.remote == "origin"

    def test_init_with_custom_params(self, tmp_path):
        """Test initialization with custom parameters."""
        pr_creator = PRCreator(
            repo_root=tmp_path,
            gh_cmd="/usr/local/bin/gh",
            remote="upstream"
        )

        assert pr_creator.repo_root == tmp_path.resolve()
        assert pr_creator.gh_cmd == "/usr/local/bin/gh"
        assert pr_creator.remote == "upstream"

    def test_factory_function(self, tmp_path):
        """Test create_pr_creator factory function."""
        pr_creator = create_pr_creator(repo_root=tmp_path, remote="upstream")

        assert pr_creator.repo_root == tmp_path.resolve()
        assert pr_creator.remote == "upstream"

    def test_factory_function_defaults_to_cwd(self):
        """Test factory defaults to current working directory."""
        pr_creator = create_pr_creator()

        assert pr_creator.repo_root == Path.cwd().resolve()


class TestCreatePRSuccess:
    """Test successful PR creation flow."""

    @patch('subprocess.run')
    def test_successful_pr_creation(self, mock_run, pr_creator, sample_task):
        """Test complete successful PR creation flow."""
        worktree_path = "/path/to/worktree"

        # Mock subprocess calls
        mock_run.side_effect = [
            # git status --porcelain (has changes)
            MagicMock(returncode=0, stdout="M file1.py\nA file2.py\n", stderr=""),
            # git add .
            MagicMock(returncode=0, stdout="", stderr=""),
            # git commit
            MagicMock(returncode=0, stdout="", stderr=""),
            # git rev-parse --short HEAD
            MagicMock(returncode=0, stdout="abc1234\n", stderr=""),
            # git push
            MagicMock(returncode=0, stdout="", stderr=""),
            # gh pr create
            MagicMock(
                returncode=0,
                stdout="https://github.com/org/repo/pull/42\n",
                stderr=""
            )
        ]

        result = pr_creator.create_pr(sample_task, worktree_path)

        # Verify result
        assert result.success is True
        assert result.pr_url == "https://github.com/org/repo/pull/42"
        assert result.pr_number == 42
        assert result.branch == "autonomous/task-123"
        assert result.error is None
        assert result.commits_pushed == ["abc1234"]

        # Verify git commands called
        assert mock_run.call_count == 6

    @patch('subprocess.run')
    def test_pr_creation_with_custom_commit_message(self, mock_run, pr_creator, sample_task):
        """Test PR creation with custom commit message."""
        worktree_path = "/path/to/worktree"
        custom_message = "Custom commit message\n\nWith details."

        # Mock subprocess calls
        mock_run.side_effect = [
            # git status (has changes)
            MagicMock(returncode=0, stdout="M file.py\n", stderr=""),
            # git add
            MagicMock(returncode=0, stdout="", stderr=""),
            # git commit
            MagicMock(returncode=0, stdout="", stderr=""),
            # git rev-parse
            MagicMock(returncode=0, stdout="def5678\n", stderr=""),
            # git push
            MagicMock(returncode=0, stdout="", stderr=""),
            # gh pr create
            MagicMock(
                returncode=0,
                stdout="https://github.com/org/repo/pull/99\n",
                stderr=""
            )
        ]

        result = pr_creator.create_pr(
            sample_task,
            worktree_path,
            commit_message=custom_message
        )

        # Verify commit called with custom message
        commit_call = mock_run.call_args_list[2]
        assert commit_call[0][0][0] == "git"
        assert commit_call[0][0][1] == "commit"
        assert commit_call[0][0][2] == "-m"
        assert commit_call[0][0][3] == custom_message


class TestCreatePRFailures:
    """Test failure scenarios in PR creation."""

    @patch('subprocess.run')
    def test_no_changes_to_commit(self, mock_run, pr_creator, sample_task):
        """Test failure when worktree has no changes."""
        worktree_path = "/path/to/worktree"

        # Mock git status returning empty (clean worktree)
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = pr_creator.create_pr(sample_task, worktree_path)

        # Verify failure
        assert result.success is False
        assert result.pr_url is None
        assert result.pr_number is None
        assert "No changes to commit" in result.error
        assert result.commits_pushed == []

        # Only git status should be called
        assert mock_run.call_count == 1

    @patch('subprocess.run')
    def test_commit_fails(self, mock_run, pr_creator, sample_task):
        """Test failure when git commit fails."""
        worktree_path = "/path/to/worktree"

        # Mock subprocess calls
        mock_run.side_effect = [
            # git status (has changes)
            MagicMock(returncode=0, stdout="M file.py\n", stderr=""),
            # git add
            MagicMock(returncode=0, stdout="", stderr=""),
            # git commit (FAILS)
            MagicMock(returncode=1, stdout="", stderr="Nothing to commit"),
        ]

        result = pr_creator.create_pr(sample_task, worktree_path)

        # Verify failure
        assert result.success is False
        assert result.pr_url is None
        assert "Failed to commit changes" in result.error
        assert result.commits_pushed == []

    @patch('subprocess.run')
    def test_push_fails_authentication(self, mock_run, pr_creator, sample_task):
        """Test failure when git push fails (authentication)."""
        worktree_path = "/path/to/worktree"

        # Mock subprocess calls
        mock_run.side_effect = [
            # git status
            MagicMock(returncode=0, stdout="M file.py\n", stderr=""),
            # git add
            MagicMock(returncode=0, stdout="", stderr=""),
            # git commit
            MagicMock(returncode=0, stdout="", stderr=""),
            # git rev-parse
            MagicMock(returncode=0, stdout="abc1234\n", stderr=""),
            # git push (FAILS)
            MagicMock(
                returncode=128,
                stdout="",
                stderr="fatal: Authentication failed"
            )
        ]

        result = pr_creator.create_pr(sample_task, worktree_path)

        # Verify failure
        assert result.success is False
        assert result.pr_url is None
        assert "Failed to push branch" in result.error
        assert result.commits_pushed == ["abc1234"]  # Commit succeeded

    @patch('subprocess.run')
    def test_gh_cli_not_installed(self, mock_run, pr_creator, sample_task):
        """Test failure when GitHub CLI not installed."""
        worktree_path = "/path/to/worktree"

        # Mock subprocess calls
        mock_run.side_effect = [
            # git status
            MagicMock(returncode=0, stdout="M file.py\n", stderr=""),
            # git add
            MagicMock(returncode=0, stdout="", stderr=""),
            # git commit
            MagicMock(returncode=0, stdout="", stderr=""),
            # git rev-parse
            MagicMock(returncode=0, stdout="abc1234\n", stderr=""),
            # git push
            MagicMock(returncode=0, stdout="", stderr=""),
            # gh pr create (NOT FOUND)
            FileNotFoundError("gh command not found")
        ]

        result = pr_creator.create_pr(sample_task, worktree_path)

        # Verify failure
        assert result.success is False
        assert result.pr_url is None
        assert "Failed to create PR" in result.error
        assert result.commits_pushed == ["abc1234"]

    @patch('subprocess.run')
    def test_gh_pr_create_fails(self, mock_run, pr_creator, sample_task):
        """Test failure when gh pr create returns error."""
        worktree_path = "/path/to/worktree"

        # Mock subprocess calls
        mock_run.side_effect = [
            # git status
            MagicMock(returncode=0, stdout="M file.py\n", stderr=""),
            # git add
            MagicMock(returncode=0, stdout="", stderr=""),
            # git commit
            MagicMock(returncode=0, stdout="", stderr=""),
            # git rev-parse
            MagicMock(returncode=0, stdout="abc1234\n", stderr=""),
            # git push
            MagicMock(returncode=0, stdout="", stderr=""),
            # gh pr create (FAILS)
            MagicMock(
                returncode=1,
                stdout="",
                stderr="pull request already exists for branch"
            )
        ]

        result = pr_creator.create_pr(sample_task, worktree_path)

        # Verify failure
        assert result.success is False
        assert result.pr_url is None
        assert "Failed to create PR" in result.error

    @patch('subprocess.run')
    def test_timeout_handling(self, mock_run, pr_creator, sample_task):
        """Test timeout handling during git operations."""
        worktree_path = "/path/to/worktree"

        # Mock git status timeout
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["git", "status"],
            timeout=10
        )

        result = pr_creator.create_pr(sample_task, worktree_path)

        # Should fail gracefully (no changes detected)
        assert result.success is False
        assert "No changes to commit" in result.error


class TestCommitMessageFormatting:
    """Test commit message generation."""

    def test_generate_commit_message(self, pr_creator, sample_task):
        """Test commit message formatting."""
        message = pr_creator._generate_commit_message(sample_task)

        # Verify structure
        assert sample_task.title in message
        assert sample_task.description in message
        assert "Acceptance Criteria:" in message
        assert "- [ ] Bug fixed and verified" in message
        assert "- [ ] Tests passing" in message
        assert "- [ ] Documentation updated" in message
        assert "Generated with [Claude Code]" in message
        assert "Co-Authored-By: Claude Sonnet 4.5" in message

    def test_commit_message_no_criteria(self, pr_creator):
        """Test commit message with no acceptance criteria."""
        task = TaskContext(
            task_id="task-99",
            title="Simple task",
            description="Simple description",
            acceptance_criteria=[],
            priority="low",
            labels=[]
        )

        message = pr_creator._generate_commit_message(task)

        # Should have default criterion
        assert "- [ ] Complete implementation" in message


class TestPRBodyFormatting:
    """Test PR body generation."""

    def test_generate_pr_title_bug(self, pr_creator):
        """Test PR title with bug label."""
        task = TaskContext(
            task_id="task-123",
            title="Fix authentication bug",
            description="Description",
            acceptance_criteria=[],
            priority="high",
            labels=["bug", "auth"]
        )

        title = pr_creator._generate_pr_title(task)
        assert title == "fix: Fix authentication bug"

    def test_generate_pr_title_feature(self, pr_creator):
        """Test PR title with feature (default)."""
        task = TaskContext(
            task_id="task-123",
            title="Add new feature",
            description="Description",
            acceptance_criteria=[],
            priority="high",
            labels=["enhancement"]
        )

        title = pr_creator._generate_pr_title(task)
        assert title == "feat: Add new feature"

    def test_generate_pr_title_docs(self, pr_creator):
        """Test PR title with docs label."""
        task = TaskContext(
            task_id="task-123",
            title="Update README",
            description="Description",
            acceptance_criteria=[],
            priority="medium",
            labels=["documentation"]
        )

        title = pr_creator._generate_pr_title(task)
        assert title == "docs: Update README"

    def test_generate_pr_body(self, pr_creator, sample_task):
        """Test PR body formatting."""
        body = pr_creator._generate_pr_body(sample_task)

        # Verify structure
        assert f"## Task: {sample_task.task_id}" in body
        assert sample_task.description in body
        assert "### Acceptance Criteria" in body
        assert "- [ ] Bug fixed and verified" in body
        assert "- [ ] Tests passing" in body
        assert "### Implementation Notes" in body
        assert "[Auto-generated by SCAFFOLD]" in body
        assert "Generated with [Claude Code]" in body

    def test_pr_body_no_criteria(self, pr_creator):
        """Test PR body with no acceptance criteria."""
        task = TaskContext(
            task_id="task-99",
            title="Simple task",
            description="Simple description",
            acceptance_criteria=[],
            priority="low",
            labels=[]
        )

        body = pr_creator._generate_pr_body(task)

        # Should have default criterion
        assert "- [ ] Complete implementation" in body


class TestURLExtraction:
    """Test URL and PR number extraction."""

    def test_extract_pr_url_standard(self, pr_creator):
        """Test extracting PR URL from gh CLI output."""
        gh_output = "https://github.com/org/repo/pull/42\n"

        url = pr_creator._extract_pr_url(gh_output)
        assert url == "https://github.com/org/repo/pull/42"

    def test_extract_pr_url_multiline(self, pr_creator):
        """Test extracting PR URL from multiline output."""
        gh_output = """
Creating pull request...
Done!
https://github.com/org/repo/pull/99
"""

        url = pr_creator._extract_pr_url(gh_output)
        assert url == "https://github.com/org/repo/pull/99"

    def test_extract_pr_url_no_match(self, pr_creator):
        """Test URL extraction when no URL present."""
        gh_output = "Error: something went wrong"

        url = pr_creator._extract_pr_url(gh_output)
        assert url is None

    def test_extract_pr_number(self, pr_creator):
        """Test extracting PR number from URL."""
        url = "https://github.com/org/repo/pull/42"

        number = pr_creator._extract_pr_number(url)
        assert number == 42

    def test_extract_pr_number_large(self, pr_creator):
        """Test extracting large PR number."""
        url = "https://github.com/org/repo/pull/9999"

        number = pr_creator._extract_pr_number(url)
        assert number == 9999

    def test_extract_pr_number_no_match(self, pr_creator):
        """Test PR number extraction from invalid URL."""
        url = "https://github.com/org/repo"

        number = pr_creator._extract_pr_number(url)
        assert number is None


class TestPRResultModel:
    """Test PRResult dataclass."""

    def test_pr_result_success(self):
        """Test successful PRResult."""
        result = PRResult(
            success=True,
            pr_url="https://github.com/org/repo/pull/42",
            pr_number=42,
            branch="autonomous/task-123",
            error=None,
            commits_pushed=["abc1234"]
        )

        assert result.success is True
        assert result.pr_url == "https://github.com/org/repo/pull/42"
        assert result.pr_number == 42
        assert result.branch == "autonomous/task-123"
        assert result.error is None
        assert result.commits_pushed == ["abc1234"]

    def test_pr_result_failure(self):
        """Test failed PRResult."""
        result = PRResult(
            success=False,
            pr_url=None,
            pr_number=None,
            branch="autonomous/task-123",
            error="Failed to push branch",
            commits_pushed=[]
        )

        assert result.success is False
        assert result.pr_url is None
        assert result.pr_number is None
        assert result.error == "Failed to push branch"

    def test_pr_result_to_dict(self):
        """Test PRResult serialization."""
        result = PRResult(
            success=True,
            pr_url="https://github.com/org/repo/pull/42",
            pr_number=42,
            branch="autonomous/task-123",
            commits_pushed=["abc1234"]
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["pr_url"] == "https://github.com/org/repo/pull/42"
        assert data["pr_number"] == 42
        assert data["branch"] == "autonomous/task-123"
        assert data["commits_pushed"] == ["abc1234"]

    def test_pr_result_from_dict(self):
        """Test PRResult deserialization."""
        data = {
            "success": True,
            "pr_url": "https://github.com/org/repo/pull/42",
            "pr_number": 42,
            "branch": "autonomous/task-123",
            "error": None,
            "commits_pushed": ["abc1234"]
        }

        result = PRResult.from_dict(data)

        assert result.success is True
        assert result.pr_url == "https://github.com/org/repo/pull/42"
        assert result.pr_number == 42
        assert result.commits_pushed == ["abc1234"]

    def test_pr_result_default_commits(self):
        """Test PRResult initializes empty commits list."""
        result = PRResult(
            success=False,
            pr_url=None,
            pr_number=None,
            branch="test"
        )

        assert result.commits_pushed == []
