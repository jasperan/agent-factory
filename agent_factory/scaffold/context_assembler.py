"""SCAFFOLD Platform - Context Assembler

Assembles execution context for Claude Code CLI.

Features:
- Reads CLAUDE.md system prompts
- Generates repo snapshot (file tree, recent commits, key files)
- Formats task specifications
- Creates execution-ready prompts
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, List

from agent_factory.scaffold.backlog_parser import BacklogParser, TaskSpec

logger = logging.getLogger(__name__)


class ContextAssemblerError(Exception):
    """Base exception for ContextAssembler errors."""
    pass


class ContextAssembler:
    """Assemble context for Claude Code CLI execution.

    Prepares complete execution environment:
    - System prompts from CLAUDE.md
    - Repository snapshot (files, commits, structure)
    - Task specification (title, description, acceptance criteria)
    - Execution template

    Example:
        >>> assembler = ContextAssembler(repo_root=Path.cwd())
        >>> context = assembler.assemble_context("task-42", "/path/to/worktree")
        >>> # Pass context to Claude Code CLI
    """

    def __init__(
        self,
        repo_root: Path,
        max_tree_depth: int = 3,
        max_commits: int = 10
    ):
        """Initialize ContextAssembler.

        Args:
            repo_root: Root directory of repository
            max_tree_depth: Maximum depth for file tree (default: 3)
            max_commits: Maximum commits to include (default: 10)
        """
        self.repo_root = Path(repo_root).resolve()
        self.max_tree_depth = max_tree_depth
        self.max_commits = max_commits
        self.backlog_parser = BacklogParser()

        # Verify CLAUDE.md exists
        self.claude_md_path = self.repo_root / "CLAUDE.md"
        if not self.claude_md_path.exists():
            logger.warning(f"CLAUDE.md not found at {self.claude_md_path}")

    def assemble_context(
        self,
        task: Dict,
        worktree_path: str
    ) -> str:
        """Assemble complete context for Claude Code CLI.

        Args:
            task: Task dict with id, title, description, acceptance_criteria
            worktree_path: Path to git worktree for execution

        Returns:
            Complete context string ready for Claude Code CLI

        Raises:
            ContextAssemblerError: If context assembly fails
        """
        task_id = task.get("id", "unknown")
        logger.info(f"Assembling context for {task_id}")

        try:
            # Components
            system_prompt = self._read_claude_md()
            file_tree = self._generate_file_tree()
            git_history = self._extract_git_commits()
            task_spec = self._format_task_spec(task)

            # Assemble complete context
            context = f"""# SCAFFOLD Task Execution Context

## System Prompt
{system_prompt}

## Repository Snapshot

### File Tree
{file_tree}

### Recent Commits
{git_history}

## Task Specification
{task_spec}

## Execution Environment
- **Worktree Path:** `{worktree_path}`
- **Task ID:** `{task_id}`

## Instructions
Execute the task according to the acceptance criteria. Make all necessary changes, run tests, and ensure the implementation is complete before finishing.
"""

            logger.debug(f"Context assembled: {len(context)} chars")
            return context

        except Exception as e:
            logger.exception(f"Failed to assemble context: {e}")
            raise ContextAssemblerError(f"Context assembly failed: {e}") from e

    def _read_claude_md(self) -> str:
        """Read CLAUDE.md and extract system prompts.

        Returns:
            System prompt content
        """
        if not self.claude_md_path.exists():
            logger.warning("CLAUDE.md not found - using minimal prompt")
            return "You are a helpful AI assistant helping implement tasks."

        try:
            content = self.claude_md_path.read_text(encoding='utf-8')

            # Extract first section (usually contains core instructions)
            lines = content.split('\n')
            prompt_lines = []
            in_prompt = False

            for line in lines:
                # Start collecting after first header
                if line.startswith('# ') and not in_prompt:
                    in_prompt = True
                    prompt_lines.append(line)
                elif in_prompt:
                    # Stop at second major section (##)
                    if line.startswith('## ') and len(prompt_lines) > 50:
                        break
                    prompt_lines.append(line)

            prompt = '\n'.join(prompt_lines[:200])  # Limit to first 200 lines
            logger.debug(f"Extracted {len(prompt_lines)} lines from CLAUDE.md")

            return prompt

        except Exception as e:
            logger.warning(f"Error reading CLAUDE.md: {e}")
            return "You are a helpful AI assistant helping implement tasks."

    def _generate_file_tree(self) -> str:
        """Generate file tree snapshot (max depth 3).

        Returns:
            File tree as markdown string
        """
        try:
            # Use tree command if available, otherwise fallback to custom implementation
            result = subprocess.run(
                ['tree', '-L', str(self.max_tree_depth), '-I', 'node_modules|__pycache__|.git|.venv|venv'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return f"```\n{result.stdout}\n```"
            else:
                # Fallback: use dir /s /b (Windows) or find (Unix)
                return self._fallback_file_tree()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            # tree command not found or timeout - use fallback
            return self._fallback_file_tree()

    def _fallback_file_tree(self) -> str:
        """Fallback file tree generator.

        Returns:
            File tree as markdown string
        """
        import os

        tree_lines = []
        tree_lines.append(str(self.repo_root.name) + "/")

        # Walk directory tree using os.walk
        for root, dirs, files in os.walk(self.repo_root):
            root_path = Path(root)

            # Skip excluded dirs
            dirs[:] = [d for d in dirs if d not in {
                'node_modules', '__pycache__', '.git', '.venv', 'venv',
                '.pytest_cache', '.mypy_cache', 'dist', 'build'
            }]

            # Calculate depth
            depth = len(root_path.relative_to(self.repo_root).parts)
            if depth >= self.max_tree_depth:
                dirs[:] = []  # Don't descend further
                continue

            # Add files
            indent = "  " * depth
            for file in sorted(files):
                tree_lines.append(f"{indent}{file}")

        tree_text = '\n'.join(tree_lines[:100])  # Limit to first 100 lines
        return f"```\n{tree_text}\n... (truncated)\n```"

    def _extract_git_commits(self) -> str:
        """Extract last 10 commits from git log.

        Returns:
            Git history as markdown string
        """
        try:
            result = subprocess.run(
                ['git', 'log', f'-{self.max_commits}', '--oneline', '--decorate'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return f"```\n{result.stdout}\n```"
            else:
                logger.warning("git log failed")
                return "Git history unavailable"

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Error extracting git commits: {e}")
            return "Git history unavailable"

    def _format_task_spec(self, task: Dict) -> str:
        """Format task specification as markdown.

        Args:
            task: Task dict

        Returns:
            Formatted task spec
        """
        task_id = task.get("id", "unknown")
        title = task.get("title", "Untitled")
        description = task.get("description", "No description")
        criteria = task.get("acceptance_criteria", [])

        # Format acceptance criteria
        criteria_lines = []
        for i, criterion in enumerate(criteria, 1):
            criteria_lines.append(f"{i}. {criterion}")

        criteria_text = '\n'.join(criteria_lines) if criteria_lines else "None specified"

        spec = f"""
### Task: {title}
**ID:** `{task_id}`

**Description:**
{description}

**Acceptance Criteria:**
{criteria_text}
"""

        return spec.strip()


def create_context_assembler(
    repo_root: Optional[Path] = None,
    max_tree_depth: int = 3,
    max_commits: int = 10
) -> ContextAssembler:
    """Factory function to create ContextAssembler.

    Args:
        repo_root: Repository root (defaults to cwd)
        max_tree_depth: Maximum file tree depth
        max_commits: Maximum commits to include

    Returns:
        ContextAssembler instance
    """
    if repo_root is None:
        repo_root = Path.cwd()

    return ContextAssembler(
        repo_root=repo_root,
        max_tree_depth=max_tree_depth,
        max_commits=max_commits
    )
