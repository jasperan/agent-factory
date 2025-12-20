"""SCAFFOLD Platform - Task Router

Routes tasks to appropriate handlers based on labels and context.

Handlers:
- ClaudeCodeHandler: Executes via Claude Code CLI (default)
- ManualActionHandler: Flags for user intervention
"""

import time
import re
import logging
import subprocess
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskExecutionError(Exception):
    """Raised when task execution fails."""
    pass


class TaskRouter:
    """Route tasks to appropriate execution handlers.

    Routing Logic:
    - Label "user-action" → ManualActionHandler
    - Default → ClaudeCodeHandler

    Example:
        >>> router = TaskRouter()
        >>> handler_name = router.route(task)
        >>> handler = router.get_handler(handler_name)
        >>> result = handler.execute(task, worktree_path)
    """

    def __init__(self):
        """Initialize TaskRouter with handler registry."""
        self.handlers = {
            "claude-code": ClaudeCodeHandler(),
            "manual": ManualActionHandler()
        }

    def route(self, task: Dict) -> str:
        """Determine handler name based on task labels.

        Args:
            task: Task dict with labels

        Returns:
            Handler name ("claude-code" or "manual")
        """
        labels = task.get("labels", [])

        # Manual tasks (user action required)
        if "user-action" in labels:
            logger.info(f"Task {task['id']}: Routing to manual handler")
            return "manual"

        # Default: Claude Code CLI
        logger.info(f"Task {task['id']}: Routing to claude-code handler")
        return "claude-code"

    def get_handler(self, handler_name: str):
        """Get handler instance by name.

        Args:
            handler_name: Handler name ("claude-code" or "manual")

        Returns:
            Handler instance

        Raises:
            KeyError: If handler not found
        """
        if handler_name not in self.handlers:
            raise KeyError(f"Handler not found: {handler_name}")

        return self.handlers[handler_name]


class ClaudeCodeHandler:
    """Execute tasks via Claude Code CLI in worktree.

    Executes subprocess: claude code execute --cwd {worktree_path}
    Parses output for cost, duration, files changed.
    """

    def execute(
        self,
        task: Dict,
        worktree_path: str,
        timeout_sec: int = 1800
    ) -> Dict:
        """Execute task via Claude Code CLI.

        Args:
            task: Task dict with title, description, acceptance_criteria
            worktree_path: Absolute path to worktree
            timeout_sec: Timeout in seconds (default: 1800 = 30 min)

        Returns:
            Result dict with keys: success, output, cost, duration_sec, files_changed

        Raises:
            TaskExecutionError: If execution fails critically
        """
        # Use ContextAssembler for rich context (with fallback to minimal prompt)
        try:
            from agent_factory.scaffold.context_assembler import ContextAssembler
            assembler = ContextAssembler(repo_root=Path.cwd())
            prompt = assembler.assemble_context(task, worktree_path)
            logger.info(f"Using rich context ({len(prompt)} chars)")
        except Exception as e:
            # Fallback to minimal prompt if assembly fails
            logger.warning(f"Context assembly failed, using minimal prompt: {e}")
            prompt = self._build_prompt(task)

        logger.info(f"Executing task {task['id']} via Claude Code CLI")
        logger.debug(f"Worktree: {worktree_path}")
        logger.debug(f"Timeout: {timeout_sec}s")

        start_time = time.time()

        try:
            result = subprocess.run(
                ["claude", "code", "execute", "--cwd", worktree_path],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )

            duration = time.time() - start_time

            success = result.returncode == 0
            output = result.stdout if success else result.stderr

            logger.info(f"Task {task['id']}: returncode={result.returncode}, duration={duration:.1f}s")

            return {
                "success": success,
                "output": output,
                "cost": self._estimate_cost(output),
                "duration_sec": duration,
                "files_changed": self._extract_files(output)
            }

        except subprocess.TimeoutExpired:
            duration = timeout_sec
            logger.error(f"Task {task['id']}: Timeout after {timeout_sec}s")

            return {
                "success": False,
                "output": f"Timeout after {timeout_sec}s",
                "cost": 0.0,
                "duration_sec": duration,
                "files_changed": []
            }

        except FileNotFoundError:
            logger.error("Claude Code CLI not found - is it installed?")
            raise TaskExecutionError("Claude Code CLI not found in PATH") from None

        except Exception as e:
            logger.error(f"Unexpected error executing task: {e}")
            raise TaskExecutionError(f"Execution error: {e}") from e

    def _build_prompt(self, task: Dict) -> str:
        """Build prompt from task specification.

        Args:
            task: Task dict with title, description, acceptance_criteria

        Returns:
            Formatted prompt string
        """
        criteria = task.get("acceptance_criteria", [])
        criteria_text = "\n".join(f"- {c}" for c in criteria) if criteria else "None specified"

        prompt = f"""Task: {task.get('title', 'Untitled')}

Description:
{task.get('description', 'No description provided')}

Acceptance Criteria:
{criteria_text}

Please implement this task following the acceptance criteria.
Make all necessary code changes, tests, and documentation updates.
"""

        return prompt

    def _estimate_cost(self, output: str) -> float:
        """Estimate API cost from Claude output.

        Looks for cost patterns in output like:
        - "Cost: $0.42"
        - "API cost: $1.23"

        Args:
            output: Claude output text

        Returns:
            Estimated cost in USD (0.0 if not found)
        """
        # Try to extract cost from output
        cost_patterns = [
            r"Cost:\s*\$?([\d.]+)",
            r"API cost:\s*\$?([\d.]+)",
            r"Total cost:\s*\$?([\d.]+)"
        ]

        for pattern in cost_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    cost = float(match.group(1))
                    logger.debug(f"Extracted cost: ${cost:.2f}")
                    return cost
                except ValueError:
                    continue

        # Fallback: rough estimate based on output length
        # Assume ~$0.01 per 1000 chars (very rough)
        estimated = len(output) / 100000
        logger.debug(f"Estimated cost (fallback): ${estimated:.4f}")
        return estimated

    def _extract_files(self, output: str) -> list:
        """Extract list of changed files from output.

        Looks for file paths mentioned in output.

        Args:
            output: Claude output text

        Returns:
            List of file paths (may be empty)
        """
        # Simple heuristic: look for common file patterns
        file_patterns = [
            r"(?:Created|Modified|Updated|Edited):\s*([^\s\n]+\.(?:py|js|ts|md|txt|json|yaml|yml))",
            r"File:\s*([^\s\n]+\.(?:py|js|ts|md|txt|json|yaml|yml))"
        ]

        files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            files.extend(matches)

        # Deduplicate
        files = list(set(files))

        if files:
            logger.debug(f"Extracted {len(files)} changed files")

        return files


class ManualActionHandler:
    """Handler for tasks requiring manual user intervention.

    These tasks are flagged but not executed automatically.
    """

    def execute(
        self,
        task: Dict,
        worktree_path: str,
        timeout_sec: int = 1800
    ) -> Dict:
        """Flag task as requiring manual intervention.

        Args:
            task: Task dict
            worktree_path: Worktree path (unused for manual tasks)
            timeout_sec: Timeout (unused for manual tasks)

        Returns:
            Result dict indicating manual action required
        """
        logger.warning(f"Task {task['id']}: Requires manual user action")

        return {
            "success": False,
            "output": f"Task requires manual action: {task.get('title', 'Untitled')}",
            "cost": 0.0,
            "duration_sec": 0.0,
            "files_changed": []
        }
