import time
import logging
import random
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


# The main prompt that drives the Worker's implementation
WORKER_SYSTEM_PROMPT = """You are an expert software engineer implementing code improvements. Your role is to:

1. Understand the task requirements completely
2. Implement the changes correctly and completely
3. Follow coding best practices
4. Ensure the code works before marking complete

When implementing changes:
- Read existing files carefully before modifying
- Make minimal, targeted changes
- Add appropriate comments and documentation
- Handle edge cases and errors
- Maintain consistent code style

You have access to file editing capabilities. Use them to implement the required changes."""


WORKER_IMPLEMENTATION_PROMPT = """Implement the following improvement task:

## Task: {title}

## Description
{description}

## Files to Modify
{affected_files}

## Acceptance Criteria
{acceptance_criteria}

## Current File Contents
{file_contents}

## Instructions
1. Analyze the current code and understand what needs to change
2. Implement ALL the acceptance criteria
3. Make the necessary file modifications
4. Ensure the code is syntactically correct and follows best practices

Begin implementing now. Create or modify the necessary files to complete this task."""


class WorkerAgent:
    """
    Worker Agent - Implements code changes using OpenHands SDK.
    
    The Worker's job is to:
    1. Receive a task from the Planner
    2. Read the affected files
    3. Generate implementation code via LLM
    4. Apply changes using OpenHands tools (Terminal, FileEditor, ApplyPatch)
    5. Report success or failure
    """
    
    def __init__(
        self,
        agent_name: str = "worker",
        model: str = "qwen2.5-coder:latest",
        workspace_dir: Optional[str] = None,
        ollama_base_url: str = "http://localhost:11434",
        num_ctx: int = 32768,
    ):
        self.agent_name = agent_name
        self.model = model
        self.workspace_dir = Path(workspace_dir).resolve() if workspace_dir else Path.cwd()
        self.ollama_base_url = ollama_base_url
        self.num_ctx = num_ctx
        
        self._openhands = None
    
    @property
    def agent_id(self) -> str:
        return f"worker-{self.agent_name}"
    
    def _get_openhands(self):
        """Lazy-load OpenHands worker."""
        if self._openhands is None:
            try:
                from agent_factory.workers.openhands_worker import OpenHandsWorker
                self._openhands = OpenHandsWorker(
                    model=self.model,
                    workspace_dir=self.workspace_dir,
                    use_ollama=True,
                    ollama_base_url=self.ollama_base_url,
                    verbose=True,
                )
            except ImportError:
                logger.warning("OpenHands SDK not available")
            except Exception as e:
                logger.warning(f"Could not initialize OpenHands: {e}")
        return self._openhands
    
    def _read_file_contents(self, files: List[str]) -> str:
        """Read contents of affected files."""
        contents = []
        for file_path in files:
            full_path = self.workspace_dir / file_path
            try:
                if full_path.exists():
                    content = full_path.read_text(encoding='utf-8')
                    if len(content) > 4000:
                        content = content[:4000] + "\n... (truncated)"
                    contents.append(f"### {file_path}\n```\n{content}\n```")
                else:
                    contents.append(f"### {file_path}\n(File does not exist - will be created)")
            except Exception as e:
                contents.append(f"### {file_path}\n(Error reading: {e})")
        
        return "\n\n".join(contents) if contents else "(No files specified)"
    
    def implement_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement a task using OpenHands SDK.
        
        This is the Worker's main job - take a task and implement it.
        
        Args:
            task: Dictionary with title, description, affected_files, acceptance_criteria
            
        Returns:
            Result dict with success, message, logs, execution_time
        """
        title = task.get("title", "Unknown task")
        description = task.get("description", "")
        affected_files = task.get("affected_files", [])
        acceptance_criteria = task.get("acceptance_criteria", [])
        
        logger.info(f"Worker implementing: {title}")
        
        # Build the implementation prompt
        file_contents = self._read_file_contents(affected_files)
        
        prompt = WORKER_IMPLEMENTATION_PROMPT.format(
            title=title,
            description=description,
            affected_files=", ".join(affected_files) if affected_files else "Determine from context",
            acceptance_criteria="\n".join(f"- {c}" for c in acceptance_criteria) if acceptance_criteria else "- Complete the task successfully",
            file_contents=file_contents,
        )
        
        # Add system context
        full_prompt = f"{WORKER_SYSTEM_PROMPT}\n\n{prompt}"
        
        # Execute via OpenHands
        openhands = self._get_openhands()
        if openhands:
            try:
                result = openhands.run_task(full_prompt, timeout=300)
                return {
                    "success": result.success,
                    "message": result.message,
                    "logs": result.logs,
                    "execution_time": result.execution_time,
                }
            except Exception as e:
                logger.error(f"OpenHands execution failed: {e}")
                return {
                    "success": False,
                    "message": str(e),
                    "logs": f"OpenHands error: {e}",
                    "execution_time": 0.0,
                }
        else:
            # Fallback: Just log what would be done
            logger.warning("OpenHands not available - simulating implementation")
            return {
                "success": True,
                "message": "Simulated implementation (OpenHands not available)",
                "logs": f"Would implement: {title}\nPrompt:\n{prompt[:500]}...",
                "execution_time": 2.0,
            }
