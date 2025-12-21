"""Integration tests for PRCreator with real git operations.

These tests create actual git worktrees and test the complete PR workflow.
They are marked with pytest.mark.integration and can be run separately.

Note: These tests require:
- git command available
- gh CLI installed and authenticated (for PR creation tests)
- Write access to test repository
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from agent_factory.scaffold.pr_creator import PRCreator
from agent_factory.scaffold.models import TaskContext


@pytest.fixture
def test_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=repo_path,
        capture_output=True,
        check=True
    )

    # Configure git user (required for commits)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        capture_output=True,
        check=True
    )

    # Create initial commit
    readme = repo_path / "README.md"
    readme.write_text("# Test Repository\n")

    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo_path,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
        check=True
    )

    yield repo_path

    # Cleanup
    if repo_path.exists():
        shutil.rmtree(repo_path, ignore_errors=True)


@pytest.fixture
def sample_task():
    """Sample task for testing."""
    return TaskContext(
        task_id="task-integration-test",
        title="Integration test task",
        description="Testing PRCreator with real git operations",
        acceptance_criteria=[
            "Commits created successfully",
            "Branch pushed to remote",
            "PR created as draft"
        ],
        priority="high",
        labels=["test", "integration"]
    )


@pytest.fixture
def pr_creator(test_repo):
    """PRCreator instance for test repository."""
    return PRCreator(
        repo_root=test_repo,
        gh_cmd="gh",
        remote="origin"
    )


@pytest.mark.integration
class TestPRCreatorWithRealGit:
    """Integration tests using real git commands."""

    def test_has_changes_clean_repo(self, pr_creator, test_repo):
        """Test detecting clean repository (no changes)."""
        result = pr_creator._has_changes(str(test_repo))
        assert result is False

    def test_has_changes_with_modifications(self, pr_creator, test_repo):
        """Test detecting changes in repository."""
        # Modify a file
        readme = test_repo / "README.md"
        readme.write_text("# Modified\n")

        result = pr_creator._has_changes(str(test_repo))
        assert result is True

    def test_has_changes_with_new_file(self, pr_creator, test_repo):
        """Test detecting new untracked file."""
        # Create new file
        new_file = test_repo / "new_file.txt"
        new_file.write_text("New content\n")

        result = pr_creator._has_changes(str(test_repo))
        assert result is True

    def test_commit_changes_success(self, pr_creator, test_repo):
        """Test successful commit creation."""
        # Create changes
        test_file = test_repo / "test.py"
        test_file.write_text("print('Hello, World!')\n")

        commit_msg = "Add test file"
        commit_sha = pr_creator._commit_changes(str(test_repo), commit_msg)

        # Verify commit created
        assert commit_sha is not None
        assert len(commit_sha) == 7  # Short SHA

        # Verify commit exists
        result = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            cwd=test_repo,
            capture_output=True,
            text=True
        )
        assert "Add test file" in result.stdout

    def test_commit_changes_empty_repo(self, pr_creator, test_repo):
        """Test commit fails when no changes exist."""
        commit_sha = pr_creator._commit_changes(
            str(test_repo),
            "No changes"
        )

        # Should fail (nothing to commit)
        assert commit_sha is None

    def test_commit_message_formatting(self, pr_creator, test_repo, sample_task):
        """Test commit with formatted message."""
        # Create changes
        test_file = test_repo / "feature.py"
        test_file.write_text("# New feature\n")

        # Generate commit message
        commit_msg = pr_creator._generate_commit_message(sample_task)

        # Commit
        commit_sha = pr_creator._commit_changes(str(test_repo), commit_msg)

        assert commit_sha is not None

        # Verify message
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=test_repo,
            capture_output=True,
            text=True
        )

        assert sample_task.title in result.stdout
        assert sample_task.description in result.stdout
        assert "Acceptance Criteria:" in result.stdout


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("gh") is None,
    reason="GitHub CLI (gh) not installed"
)
class TestPRCreatorWithGitHub:
    """Integration tests requiring GitHub CLI.

    These tests are skipped if gh CLI is not installed.
    They also require:
    - gh auth login (authenticated)
    - Access to a test repository
    """

    def test_gh_authentication_check(self):
        """Test GitHub CLI authentication status."""
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True
        )

        # If not authenticated, skip remaining tests
        if result.returncode != 0:
            pytest.skip("GitHub CLI not authenticated (run 'gh auth login')")


@pytest.mark.integration
class TestPRCreatorFullWorkflow:
    """Test complete PR creation workflow (without actual GitHub operations)."""

    def test_create_pr_no_changes(self, pr_creator, test_repo, sample_task):
        """Test PR creation fails when no changes exist."""
        result = pr_creator.create_pr(sample_task, str(test_repo))

        # Should fail with no changes error
        assert result.success is False
        assert "No changes to commit" in result.error
        assert result.commits_pushed == []

    def test_create_pr_with_changes_no_remote(
        self,
        pr_creator,
        test_repo,
        sample_task
    ):
        """Test PR creation with changes but no remote (push fails)."""
        # Create changes
        test_file = test_repo / "feature.py"
        test_file.write_text("# Feature implementation\n")

        # Try to create PR (will fail at push - no remote)
        result = pr_creator.create_pr(sample_task, str(test_repo))

        # Should fail at push step
        assert result.success is False
        assert "Failed to push branch" in result.error
        # Commit should have succeeded
        assert len(result.commits_pushed) == 1

    def test_commit_and_extract_sha(self, pr_creator, test_repo, sample_task):
        """Test that commit SHA is correctly extracted."""
        # Create changes
        test_file = test_repo / "test.py"
        test_file.write_text("print('test')\n")

        # Generate commit message
        commit_msg = pr_creator._generate_commit_message(sample_task)

        # Commit
        commit_sha = pr_creator._commit_changes(str(test_repo), commit_msg)

        # Verify SHA format
        assert commit_sha is not None
        assert len(commit_sha) == 7
        assert all(c in "0123456789abcdef" for c in commit_sha.lower())

        # Verify commit exists with this SHA
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%h"],
            cwd=test_repo,
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == commit_sha


@pytest.mark.integration
class TestPRCreatorErrorHandling:
    """Test error handling in real scenarios."""

    def test_invalid_worktree_path(self, pr_creator, sample_task):
        """Test handling of invalid worktree path."""
        invalid_path = "/nonexistent/path/to/worktree"

        result = pr_creator.create_pr(sample_task, invalid_path)

        # Should fail gracefully
        assert result.success is False
        assert result.error is not None

    def test_commit_with_very_long_message(self, pr_creator, test_repo):
        """Test commit with very long message (edge case)."""
        # Create changes
        test_file = test_repo / "test.txt"
        test_file.write_text("content\n")

        # Generate very long commit message
        long_message = "A" * 10000 + "\n\nBody text."

        # Should handle gracefully
        commit_sha = pr_creator._commit_changes(str(test_repo), long_message)

        # Git should accept it (might truncate subject)
        assert commit_sha is not None


def test_pr_result_persistence():
    """Test PRResult can be persisted and restored."""
    from agent_factory.scaffold.models import PRResult
    import json

    # Create result
    result = PRResult(
        success=True,
        pr_url="https://github.com/test/repo/pull/99",
        pr_number=99,
        branch="autonomous/task-test",
        commits_pushed=["abc1234", "def5678"]
    )

    # Serialize to JSON
    json_str = json.dumps(result.to_dict())

    # Deserialize
    restored_data = json.loads(json_str)
    restored = PRResult.from_dict(restored_data)

    # Verify match
    assert restored.success == result.success
    assert restored.pr_url == result.pr_url
    assert restored.pr_number == result.pr_number
    assert restored.branch == result.branch
    assert restored.commits_pushed == result.commits_pushed


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"])
