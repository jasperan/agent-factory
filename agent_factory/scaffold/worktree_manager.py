"""SCAFFOLD Platform - Git Worktree Manager

Manages isolated git worktrees for parallel task execution.

Extracted and enhanced from agentcli.py (lines 675-940).
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from agent_factory.scaffold.models import WorktreeMetadata


class WorktreeManagerError(Exception):
    """Base exception for WorktreeManager errors."""
    pass


class WorktreeExistsError(WorktreeManagerError):
    """Raised when attempting to create duplicate worktree."""
    pass


class WorktreeNotFoundError(WorktreeManagerError):
    """Raised when worktree not found."""
    pass


class WorktreeLimitError(WorktreeManagerError):
    """Raised when max concurrent worktrees limit reached."""
    pass


class WorktreeManager:
    """Manages isolated git worktrees for parallel task execution.

    Features:
    - Creates worktrees at ../agent-factory-{task-id} on branch autonomous/{task-id}
    - Tracks worktree metadata in .scaffold/worktrees.json
    - Prevents duplicate worktrees for same task
    - Enforces max_concurrent_worktrees limit
    - Provides cleanup with force option

    Example:
        >>> manager = WorktreeManager(repo_root=Path.cwd())
        >>> worktree_path = manager.create_worktree("task-42")
        >>> print(f"Created: {worktree_path}")
        >>> manager.cleanup_worktree("task-42")
    """

    def __init__(
        self,
        repo_root: Path,
        metadata_path: Optional[Path] = None,
        max_concurrent: int = 3
    ):
        """Initialize WorktreeManager.

        Args:
            repo_root: Root directory of git repository
            metadata_path: Path to metadata JSON file (default: .scaffold/worktrees.json)
            max_concurrent: Maximum concurrent worktrees allowed (default: 3)
        """
        self.repo_root = Path(repo_root).resolve()
        self.metadata_path = metadata_path or (self.repo_root / ".scaffold" / "worktrees.json")
        self.max_concurrent = max_concurrent

        # Ensure .scaffold directory exists
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

        # Load metadata
        self._metadata: Dict[str, WorktreeMetadata] = self._load_metadata()

    def create_worktree(
        self,
        task_id: str,
        creator: str = "scaffold-orchestrator"
    ) -> str:
        """Create worktree at ../agent-factory-{task-id} on branch autonomous/{task-id}.

        Args:
            task_id: Task identifier (e.g., "task-42")
            creator: Who is creating this worktree (default: "scaffold-orchestrator")

        Returns:
            str: Absolute path to created worktree

        Raises:
            WorktreeExistsError: If worktree for this task already exists
            WorktreeLimitError: If max_concurrent limit reached
            WorktreeManagerError: If git command fails
        """
        # 1. Validate task_id format
        if not task_id or not task_id.strip():
            raise WorktreeManagerError("task_id cannot be empty")

        # Clean task_id (lowercase, hyphens)
        clean_id = task_id.lower().replace(" ", "-").replace("_", "-")

        # 2. Check if already exists
        if clean_id in self._metadata:
            raise WorktreeExistsError(
                f"Worktree for task '{clean_id}' already exists at: "
                f"{self._metadata[clean_id].worktree_path}"
            )

        # 3. Check max_concurrent limit
        active_worktrees = [
            wt for wt in self._metadata.values()
            if wt.status == "active"
        ]
        if len(active_worktrees) >= self.max_concurrent:
            raise WorktreeLimitError(
                f"Maximum concurrent worktrees ({self.max_concurrent}) reached. "
                f"Active worktrees: {[wt.task_id for wt in active_worktrees]}"
            )

        # 4. Construct paths and branch name
        worktree_path = self.repo_root.parent / f"agent-factory-{clean_id}"
        branch_name = f"autonomous/{clean_id}"

        # Check with git worktree list (belt-and-suspenders check)
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise WorktreeManagerError(f"Failed to list worktrees: {result.stderr}")

        if str(worktree_path) in result.stdout:
            raise WorktreeExistsError(
                f"Worktree already exists at: {worktree_path} "
                "(detected by git worktree list, not in metadata - possibly orphaned)"
            )

        # 5. Create worktree with git
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise WorktreeManagerError(
                f"Failed to create worktree: {result.stderr}"
            )

        # 6. Track in metadata
        metadata = WorktreeMetadata(
            task_id=clean_id,
            worktree_path=str(worktree_path),
            branch_name=branch_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            creator=creator,
            status="active",
            pr_url=None
        )

        self._metadata[clean_id] = metadata
        self._save_metadata()

        # 7. Return absolute path
        return str(worktree_path)

    def cleanup_worktree(
        self,
        task_id: str,
        force: bool = False,
        delete_branch: bool = True
    ) -> bool:
        """Remove worktree and optionally delete branch.

        Args:
            task_id: Task identifier (e.g., "task-42")
            force: Force removal even with uncommitted changes
            delete_branch: Delete the branch after removing worktree (default: True)

        Returns:
            bool: True if successful

        Raises:
            WorktreeNotFoundError: If worktree not found
            WorktreeManagerError: If git command fails
        """
        # Clean task_id
        clean_id = task_id.lower().replace(" ", "-").replace("_", "-")

        # Check metadata
        if clean_id not in self._metadata:
            raise WorktreeNotFoundError(
                f"Worktree for task '{clean_id}' not found in metadata"
            )

        metadata = self._metadata[clean_id]
        worktree_path = metadata.worktree_path

        # Remove worktree
        cmd = ["git", "worktree", "remove", worktree_path]
        if force:
            cmd.append("--force")

        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Try with --force if not already used
            if not force:
                result = subprocess.run(
                    ["git", "worktree", "remove", worktree_path, "--force"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    raise WorktreeManagerError(
                        f"Failed to remove worktree: {result.stderr}"
                    )
            else:
                raise WorktreeManagerError(
                    f"Failed to remove worktree: {result.stderr}"
                )

        # Delete branch if requested
        if delete_branch:
            result = subprocess.run(
                ["git", "branch", "-d", metadata.branch_name],
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )

            # If -d fails (unmerged), try -D
            if result.returncode != 0:
                subprocess.run(
                    ["git", "branch", "-D", metadata.branch_name],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True
                )

        # Prune
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=self.repo_root,
            capture_output=True
        )

        # Remove from metadata
        del self._metadata[clean_id]
        self._save_metadata()

        return True

    def list_worktrees(self) -> List[WorktreeMetadata]:
        """Return all tracked worktrees.

        Returns:
            List[WorktreeMetadata]: List of worktree metadata objects
        """
        return list(self._metadata.values())

    def get_worktree(self, task_id: str) -> Optional[WorktreeMetadata]:
        """Get worktree metadata by task ID.

        Args:
            task_id: Task identifier (e.g., "task-42")

        Returns:
            WorktreeMetadata if found, None otherwise
        """
        clean_id = task_id.lower().replace(" ", "-").replace("_", "-")
        return self._metadata.get(clean_id)

    def update_worktree_status(
        self,
        task_id: str,
        status: str,
        pr_url: Optional[str] = None
    ) -> None:
        """Update worktree status and PR URL.

        Args:
            task_id: Task identifier
            status: New status (active|stale|merged|abandoned)
            pr_url: PR URL if created (optional)

        Raises:
            WorktreeNotFoundError: If worktree not found
        """
        clean_id = task_id.lower().replace(" ", "-").replace("_", "-")

        if clean_id not in self._metadata:
            raise WorktreeNotFoundError(
                f"Worktree for task '{clean_id}' not found in metadata"
            )

        metadata = self._metadata[clean_id]
        metadata.status = status

        if pr_url is not None:
            metadata.pr_url = pr_url

        self._save_metadata()

    def _load_metadata(self) -> Dict[str, WorktreeMetadata]:
        """Load metadata from JSON file.

        Returns:
            Dict[str, WorktreeMetadata]: task_id -> metadata mapping
        """
        if not self.metadata_path.exists():
            return {}

        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                task_id: WorktreeMetadata.from_dict(metadata_dict)
                for task_id, metadata_dict in data.items()
            }
        except (json.JSONDecodeError, KeyError) as e:
            # If metadata is corrupted, start fresh
            return {}

    def _save_metadata(self) -> None:
        """Save metadata to JSON file."""
        data = {
            task_id: metadata.to_dict()
            for task_id, metadata in self._metadata.items()
        }

        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
