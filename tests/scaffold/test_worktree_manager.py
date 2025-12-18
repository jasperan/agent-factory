"""Tests for SCAFFOLD WorktreeManager

Tests the core worktree management functionality.
"""

import json
import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from agent_factory.scaffold import (
    WorktreeManager,
    WorktreeManagerError,
    WorktreeExistsError,
    WorktreeNotFoundError,
    WorktreeLimitError,
    WorktreeMetadata,
)


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )

    # Create initial commit
    (repo_dir / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True
    )

    return repo_dir


@pytest.fixture
def worktree_manager(temp_repo):
    """Create WorktreeManager instance with temporary repo."""
    return WorktreeManager(repo_root=temp_repo)


class TestWorktreeManagerInit:
    """Test WorktreeManager initialization."""

    def test_init_creates_metadata_directory(self, temp_repo):
        """Test that initialization creates .scaffold directory."""
        manager = WorktreeManager(repo_root=temp_repo)

        assert manager.metadata_path.parent.exists()
        assert manager.metadata_path.parent.name == ".scaffold"

    def test_init_with_custom_metadata_path(self, temp_repo):
        """Test initialization with custom metadata path."""
        custom_path = temp_repo / "custom" / "metadata.json"
        manager = WorktreeManager(repo_root=temp_repo, metadata_path=custom_path)

        assert manager.metadata_path == custom_path
        assert manager.metadata_path.parent.exists()

    def test_init_with_custom_max_concurrent(self, temp_repo):
        """Test initialization with custom max_concurrent limit."""
        manager = WorktreeManager(repo_root=temp_repo, max_concurrent=5)

        assert manager.max_concurrent == 5


class TestCreateWorktree:
    """Test worktree creation."""

    def test_create_worktree_success(self, worktree_manager, temp_repo):
        """Test successful worktree creation."""
        task_id = "task-1"

        # Create worktree
        worktree_path = worktree_manager.create_worktree(task_id)

        # Verify path
        assert worktree_path
        assert "agent-factory-task-1" in worktree_path
        assert Path(worktree_path).exists()

        # Verify metadata
        metadata = worktree_manager.get_worktree(task_id)
        assert metadata is not None
        assert metadata.task_id == task_id
        assert metadata.branch_name == "autonomous/task-1"
        assert metadata.status == "active"
        assert metadata.creator == "scaffold-orchestrator"

        # Verify git worktree list
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )
        assert "agent-factory-task-1" in result.stdout
        assert "autonomous/task-1" in result.stdout

    def test_create_worktree_with_custom_creator(self, worktree_manager):
        """Test worktree creation with custom creator."""
        task_id = "task-2"

        worktree_manager.create_worktree(task_id, creator="test-suite")

        metadata = worktree_manager.get_worktree(task_id)
        assert metadata.creator == "test-suite"

    def test_create_worktree_duplicate_raises_error(self, worktree_manager):
        """Test that creating duplicate worktree raises error."""
        task_id = "task-3"

        # Create first worktree
        worktree_manager.create_worktree(task_id)

        # Attempt to create duplicate
        with pytest.raises(WorktreeExistsError) as exc_info:
            worktree_manager.create_worktree(task_id)

        assert "already exists" in str(exc_info.value)

    def test_create_worktree_max_concurrent_limit(self, worktree_manager):
        """Test max_concurrent limit enforcement."""
        # Set limit to 2
        worktree_manager.max_concurrent = 2

        # Create 2 worktrees (should succeed)
        worktree_manager.create_worktree("task-4")
        worktree_manager.create_worktree("task-5")

        # Attempt to create 3rd (should fail)
        with pytest.raises(WorktreeLimitError) as exc_info:
            worktree_manager.create_worktree("task-6")

        assert "Maximum concurrent worktrees" in str(exc_info.value)
        assert "2" in str(exc_info.value)

    def test_create_worktree_empty_task_id_raises_error(self, worktree_manager):
        """Test that empty task_id raises error."""
        with pytest.raises(WorktreeManagerError) as exc_info:
            worktree_manager.create_worktree("")

        assert "cannot be empty" in str(exc_info.value)

    def test_create_worktree_normalizes_task_id(self, worktree_manager):
        """Test that task_id is normalized (lowercase, hyphens)."""
        task_id = "Task_7 Name"

        worktree_path = worktree_manager.create_worktree(task_id)

        # Should be normalized
        assert "task-7-name" in worktree_path
        metadata = worktree_manager.get_worktree("task-7-name")
        assert metadata is not None


class TestCleanupWorktree:
    """Test worktree cleanup."""

    def test_cleanup_worktree_success(self, worktree_manager):
        """Test successful worktree cleanup."""
        task_id = "task-8"

        # Create worktree
        worktree_path = worktree_manager.create_worktree(task_id)
        assert Path(worktree_path).exists()

        # Cleanup
        result = worktree_manager.cleanup_worktree(task_id)

        assert result is True
        assert not Path(worktree_path).exists()
        assert worktree_manager.get_worktree(task_id) is None

    def test_cleanup_worktree_not_found_raises_error(self, worktree_manager):
        """Test cleanup of non-existent worktree raises error."""
        with pytest.raises(WorktreeNotFoundError) as exc_info:
            worktree_manager.cleanup_worktree("task-999")

        assert "not found" in str(exc_info.value)

    def test_cleanup_worktree_with_uncommitted_changes(self, worktree_manager):
        """Test cleanup with uncommitted changes (force=True)."""
        task_id = "task-9"

        # Create worktree
        worktree_path = worktree_manager.create_worktree(task_id)

        # Make uncommitted changes
        (Path(worktree_path) / "test.txt").write_text("Uncommitted change")

        # Cleanup with force (should succeed)
        result = worktree_manager.cleanup_worktree(task_id, force=True)

        assert result is True
        assert not Path(worktree_path).exists()

    def test_cleanup_worktree_keep_branch(self, worktree_manager, temp_repo):
        """Test cleanup while keeping branch."""
        task_id = "task-10"

        # Create worktree
        worktree_manager.create_worktree(task_id)

        # Cleanup without deleting branch
        worktree_manager.cleanup_worktree(task_id, delete_branch=False)

        # Check branch still exists
        result = subprocess.run(
            ["git", "branch", "--list", "autonomous/task-10"],
            cwd=temp_repo,
            capture_output=True,
            text=True
        )
        assert "autonomous/task-10" in result.stdout


class TestListWorktrees:
    """Test listing worktrees."""

    def test_list_worktrees_empty(self, worktree_manager):
        """Test listing when no worktrees exist."""
        worktrees = worktree_manager.list_worktrees()

        assert worktrees == []

    def test_list_worktrees_multiple(self, worktree_manager):
        """Test listing multiple worktrees."""
        # Create 3 worktrees
        worktree_manager.create_worktree("task-11")
        worktree_manager.create_worktree("task-12")
        worktree_manager.create_worktree("task-13")

        worktrees = worktree_manager.list_worktrees()

        assert len(worktrees) == 3
        task_ids = [wt.task_id for wt in worktrees]
        assert "task-11" in task_ids
        assert "task-12" in task_ids
        assert "task-13" in task_ids


class TestGetWorktree:
    """Test getting individual worktree metadata."""

    def test_get_worktree_success(self, worktree_manager):
        """Test getting worktree that exists."""
        task_id = "task-14"
        worktree_manager.create_worktree(task_id)

        metadata = worktree_manager.get_worktree(task_id)

        assert metadata is not None
        assert metadata.task_id == task_id
        assert metadata.status == "active"

    def test_get_worktree_not_found(self, worktree_manager):
        """Test getting worktree that doesn't exist."""
        metadata = worktree_manager.get_worktree("task-999")

        assert metadata is None


class TestUpdateWorktreeStatus:
    """Test updating worktree status."""

    def test_update_status_success(self, worktree_manager):
        """Test updating worktree status."""
        task_id = "task-15"
        worktree_manager.create_worktree(task_id)

        # Update status
        worktree_manager.update_worktree_status(task_id, "merged")

        metadata = worktree_manager.get_worktree(task_id)
        assert metadata.status == "merged"

    def test_update_status_with_pr_url(self, worktree_manager):
        """Test updating status with PR URL."""
        task_id = "task-16"
        worktree_manager.create_worktree(task_id)

        # Update status and PR URL
        pr_url = "https://github.com/user/repo/pull/123"
        worktree_manager.update_worktree_status(task_id, "merged", pr_url=pr_url)

        metadata = worktree_manager.get_worktree(task_id)
        assert metadata.status == "merged"
        assert metadata.pr_url == pr_url

    def test_update_status_not_found_raises_error(self, worktree_manager):
        """Test updating non-existent worktree raises error."""
        with pytest.raises(WorktreeNotFoundError):
            worktree_manager.update_worktree_status("task-999", "merged")


class TestMetadataPersistence:
    """Test metadata persistence to JSON file."""

    def test_metadata_persisted_to_file(self, worktree_manager):
        """Test that metadata is saved to JSON file."""
        task_id = "task-17"
        worktree_manager.create_worktree(task_id)

        # Check file exists
        assert worktree_manager.metadata_path.exists()

        # Read file
        with open(worktree_manager.metadata_path, 'r') as f:
            data = json.load(f)

        assert task_id in data
        assert data[task_id]["task_id"] == task_id
        assert data[task_id]["status"] == "active"

    def test_metadata_reloaded_on_new_instance(self, temp_repo):
        """Test that metadata is reloaded when creating new instance."""
        task_id = "task-18"

        # Create worktree with first manager
        manager1 = WorktreeManager(repo_root=temp_repo)
        manager1.create_worktree(task_id)

        # Create second manager (should reload metadata)
        manager2 = WorktreeManager(repo_root=temp_repo)

        metadata = manager2.get_worktree(task_id)
        assert metadata is not None
        assert metadata.task_id == task_id

    def test_corrupted_metadata_handled_gracefully(self, temp_repo):
        """Test that corrupted metadata file doesn't crash."""
        # Create corrupted metadata file
        metadata_path = temp_repo / ".scaffold" / "worktrees.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text("{ invalid json }")

        # Should handle gracefully (start fresh)
        manager = WorktreeManager(repo_root=temp_repo)
        assert manager.list_worktrees() == []


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow_create_use_cleanup(self, worktree_manager):
        """Test complete workflow: create -> use -> cleanup."""
        task_id = "task-19"

        # 1. Create worktree
        worktree_path = worktree_manager.create_worktree(task_id)
        assert Path(worktree_path).exists()

        # 2. Simulate work (create file)
        (Path(worktree_path) / "work.txt").write_text("Some work done")

        # 3. Update status
        worktree_manager.update_worktree_status(
            task_id,
            "merged",
            pr_url="https://github.com/user/repo/pull/42"
        )

        # 4. Cleanup
        worktree_manager.cleanup_worktree(task_id)

        # Verify cleanup
        assert not Path(worktree_path).exists()
        assert worktree_manager.get_worktree(task_id) is None

    def test_multiple_worktrees_concurrent(self, worktree_manager):
        """Test multiple worktrees can coexist."""
        # Create 3 worktrees
        path1 = worktree_manager.create_worktree("task-20")
        path2 = worktree_manager.create_worktree("task-21")
        path3 = worktree_manager.create_worktree("task-22")

        # All should exist
        assert Path(path1).exists()
        assert Path(path2).exists()
        assert Path(path3).exists()

        # All should be tracked
        assert len(worktree_manager.list_worktrees()) == 3

        # Cleanup all
        worktree_manager.cleanup_worktree("task-20")
        worktree_manager.cleanup_worktree("task-21")
        worktree_manager.cleanup_worktree("task-22")

        # All should be gone
        assert len(worktree_manager.list_worktrees()) == 0
