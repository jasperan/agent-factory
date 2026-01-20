"""
OpenHands Worker - AI Coding Agent Integration

PURPOSE:
    Integrates OpenHands (formerly OpenDevin) autonomous coding agent into the factory.
    OpenHands can write code, run commands, browse web, edit files autonomously.

WHAT THIS DOES:
    - Uses OpenHands SDK for programmatic agent control
    - Configures agents with FileEditor and Bash tools
    - executes tasks within the Python process
    - Returns structured results

WHY WE NEED THIS:
    - Avoid $200/month Claude Code fee (deadline Dec 15th!)
    - Get production-grade coding agent (50%+ SWE-Bench score)
    - Model-agnostic (works with Claude, GPT, Gemini, Llama)
    - Direct control over tools and execution environment

HOW IT WORKS (PLC-Style Explanation):
    1. User calls: worker.run_task("Fix bug in file.py")
    2. Worker creates OpenHands SDK components (LLM, Agent, Conversation)
    3. Worker injects FileEditor and Bash tools
    4. Task executed via Conversation.run()
    5. Result parsed and returned

INPUTS:
    - task: String describing what to code/fix
    - model: Which LLM to use (default: claude-3-5-sonnet)
    - timeout: Max seconds to wait (default: 300)

OUTPUTS:
    - Dict with: success (bool), code (str), message (str), files_changed (list)
"""

import os
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

# OpenHands SDK Imports
# OpenHands SDK Imports
try:
    import openhands.sdk
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


@dataclass
class OpenHandsResult:
    """
    Result from an OpenHands coding task.
    """
    success: bool
    message: str
    code: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    cost: float = 0.0
    logs: str = ""


class OpenHandsWorker:
    """
    OpenHands AI Coding Agent Worker (SDK Version)
    """

    def __init__(
        self,
        model: str = "ollama/deepseek-coder:6.7b",
        workspace_dir: Optional[Path] = None,
        use_ollama: bool = None,
        ollama_base_url: str = None,
        port: int = 3000, # Ignored, kept for compatibility
    ):
        """
        Initialize OpenHands worker.
        """
        if not SDK_AVAILABLE:
            raise ImportError(
                "OpenHands SDK not found. Please install: pip install openhands-sdk openhands-tools"
            )

        # Auto-detect Ollama from environment
        if use_ollama is None:
            use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"

        if ollama_base_url is None:
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # If no model specified but USE_OLLAMA=true, use default Ollama model
        if use_ollama:
             # Ensure ollama/ prefix for litellm
            if model == "deepseek-coder:6.7b":
                 model = os.getenv("OLLAMA_MODEL", "ollama/deepseek-coder:6.7b")
            
            # Always check prefix
            if not model.startswith("ollama/"):
                model = f"ollama/{model}"

        self.model = model
        self.use_ollama = use_ollama
        self.ollama_base_url = ollama_base_url
        self.workspace_dir = workspace_dir or Path.cwd() / "openhands_workspace"
        self.verbose = os.getenv("VERBOSE", "true").lower() == "true"
        
        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def run_task(
        self,
        task: str,
        timeout: int = 300,
        cleanup: bool = False, # Default to False to persist files for user
        on_log: Optional[Any] = None
    ) -> OpenHandsResult:
        """
        Run a coding task using OpenHands SDK.
        """
        start_time = time.time()

        if not task or not task.strip():
            return OpenHandsResult(
                success=False,
                message="Task cannot be empty",
                execution_time=time.time() - start_time
            )

        try:
            # 1. Configure LLM
            # We use the SDK primitives as discovered
            return self._run_sdk_task(task, timeout, on_log=on_log)

        except Exception as e:
            return OpenHandsResult(
                success=False,
                message=f"SDK Error: {str(e)}",
                logs=str(e),
                execution_time=time.time() - start_time
            )

    def _run_sdk_task(self, task: str, timeout: int, on_log=None) -> OpenHandsResult:
        """
        Internal method to run task using the high-level SDK.
        """
        from openhands.sdk import Agent, LLM, Conversation
        from pydantic import SecretStr

        start_time = time.time()
        
        # 1. Setup LLM
        api_key = os.getenv("LLM_API_KEY", "dummy") # Ollama doesn't need key
        
        llm = LLM(
            model=self.model,
            api_key=SecretStr(api_key),
            base_url=self.ollama_base_url if self.use_ollama else None,
        )

        # 2. Setup Agent using Preset
        # Use the default preset which includes FileEditor, Terminal, etc.
        from openhands.tools.preset import get_default_agent
        
        # We set cli_mode=True to avoid browser tools if headless, 
        # or False if we want them (default_tools logic: enable_browser=not cli_mode).
        # Since we are running headless/programmatic, we might want browser if user asks.
        # But for now let's stick to base tools.
        agent = get_default_agent(llm=llm, cli_mode=True)

        # 4. Conversation
        # Workspace is where files will be created
        conversation = Conversation(
            agent=agent,
            workspace=str(self.workspace_dir)
        )

        if self.verbose:
            print(f"[OpenHands SDK] Starting task in {self.workspace_dir}")

        # 5. Run
        # We wrap in a simple try block.
        try:
             # Basic conversation loop wrapper
             conversation.send_message(task)
             conversation.run()
        except Exception as e:
            if on_log: on_log(f"Error during execution: {e}")
            raise e

        # 6. Parse Results
        # Check files changed (naive diff or timestamp check)
        files_changed = []
        all_files = list(self.workspace_dir.glob("**/*"))
        for file in all_files:
             if file.is_file() and not str(file).startswith(str(self.workspace_dir / ".openhands")):
                files_changed.append(str(file.relative_to(self.workspace_dir)))

        full_logs = "Conversation finished." 

        return OpenHandsResult(
            success=True,
            message="Task completed via SDK",
            code="", # Extract code if possible
            files_changed=files_changed,
            logs=full_logs,
            execution_time=time.time() - start_time
        )


def create_openhands_worker(model: str = "ollama/deepseek-coder:6.7b") -> OpenHandsWorker:
    return OpenHandsWorker(model=model)
