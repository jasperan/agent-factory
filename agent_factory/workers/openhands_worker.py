"""
OpenHands Worker - AI Coding Agent Integration

PURPOSE:
    Integrates OpenHands (formerly OpenDevin) autonomous coding agent into the factory.
    OpenHands can write code, run commands, browse web, edit files autonomously.

WHAT THIS DOES:
    - Spawns OpenHands Docker container for isolated coding tasks
    - Sends coding tasks to OpenHands agent
    - Receives code/results back
    - Manages container lifecycle safely

WHY WE NEED THIS:
    - Avoid $200/month Claude Code fee (deadline Dec 15th!)
    - Get production-grade coding agent (50%+ SWE-Bench score)
    - Model-agnostic (works with Claude, GPT, Gemini, Llama)
    - Sandboxed execution (safe for untrusted code)

HOW IT WORKS (PLC-Style Explanation):
    1. User calls: worker.run_task("Fix bug in file.py")
    2. Worker starts Docker container with OpenHands
    3. Task sent to OpenHands via HTTP API
    4. OpenHands writes code, runs tests, returns result
    5. Worker parses result and returns structured output
    6. Container cleaned up automatically

INPUTS:
    - task: String describing what to code/fix
    - model: Which LLM to use (default: claude-3-5-sonnet)
    - timeout: Max seconds to wait (default: 300)

OUTPUTS:
    - Dict with: success (bool), code (str), message (str), files_changed (list)

EDGE CASES:
    - Docker not installed → Friendly error message
    - Container startup fails → Retry once, then fail gracefully
    - Task times out → Kill container, return partial results
    - OpenHands crashes → Capture logs, return error

TROUBLESHOOTING:
    - If "Docker not found" → Install Docker Desktop
    - If container won't start → Check port 3000 is free
    - If tasks time out → Increase timeout or simplify task
    - If results are bad → Try different model or clarify task
"""

import subprocess
import time
import requests
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OpenHandsResult:
    """
    Result from an OpenHands coding task.

    WHAT THIS IS:
        Structured output from OpenHands worker - tells you if task succeeded,
        what code was generated, which files changed, and any error messages.

    FIELDS EXPLAINED:
        success: Did the task complete without errors? (True/False)
        message: Human-readable description of what happened
        code: The actual code that was generated (if applicable)
        files_changed: List of file paths that were created/modified
        execution_time: How many seconds the task took
        cost: Estimated API cost in dollars (based on model/tokens)
        logs: Raw output from OpenHands for debugging
    """
    success: bool  # Task completed successfully? (like PLC Done bit)
    message: str  # What happened (like HMI status message)
    code: Optional[str] = None  # Generated code (if any)
    files_changed: List[str] = field(default_factory=list)  # Modified files
    execution_time: float = 0.0  # Seconds elapsed
    cost: float = 0.0  # USD cost estimate
    logs: str = ""  # Debug output (like PLC fault log)


class OpenHandsWorker:
    """
    OpenHands AI Coding Agent Worker

    PURPOSE:
        Manages OpenHands Docker container and sends it coding tasks.
        Think of this like a PLC controlling a robotic workcell - you send commands,
        it does the work autonomously, you get results back.

    HOW TO USE:
        worker = OpenHandsWorker(model="claude-3-5-sonnet")
        result = worker.run_task("Add a function to calculate factorial")
        if result.success:
            print(f"Code generated: {result.code}")

    LIFECYCLE:
        __init__() → Container NOT started yet (saves resources)
        run_task() → Starts container, runs task, stops container
        (Container is ephemeral - created and destroyed per task)

    WHY EPHEMERAL:
        - Cleaner: No state carried between tasks
        - Safer: Each task in fresh environment
        - Cheaper: Only pay when actually running
    """

    def __init__(
        self,
        model: str = "deepseek-coder:6.7b",  # Default to FREE Ollama model
        port: int = 3000,  # OpenHands web UI port
        workspace_dir: Optional[Path] = None,  # Where OpenHands works
        use_ollama: bool = None,  # Auto-detect from env if None
        ollama_base_url: str = None,  # Auto-detect from env if None
    ):
        """
        Initialize OpenHands worker (uses local installation).

        WHAT HAPPENS:
            - Auto-detects Ollama configuration from .env
            - Stores configuration
            - Uses local 'openhands' CLI (no Docker required for controller)
        """
        import os

        # Auto-detect Ollama from environment
        if use_ollama is None:
            use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"

        if ollama_base_url is None:
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # If no model specified but USE_OLLAMA=true, use default Ollama model
        if use_ollama and model == "deepseek-coder:6.7b":
            model = os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b")

        self.model = model
        self.port = port
        self.workspace_dir = workspace_dir or Path("./openhands_workspace")
        self.container_name = f"openhands_worker_{port}"
        self.use_ollama = use_ollama
        self.ollama_base_url = ollama_base_url
        
        # Local binary path
        self.openhands_bin = os.path.expanduser("~/.local/bin/openhands")
        
        # Validate openhands is installed
        if not os.path.exists(self.openhands_bin):
            raise RuntimeError(
                f"OpenHands binary not found at {self.openhands_bin}.\n"
                "Please install it using:\n"
                "  uv tool install openhands --python 3.12"
            )

        # Validate Ollama if enabled
        if self.use_ollama:
            self._validate_ollama()

    def run_task(
        self,
        task: str,
        timeout: int = 300,  # 5 minutes default
        cleanup: bool = True,  # Remove workspace files when done?
        on_log: Optional[Any] = None  # Callback for streaming logs
    ) -> OpenHandsResult:
        """
        Run a coding task with local OpenHands CLI.

        WHAT THIS DOES (Step-by-Step):
            1. VALIDATE: Check task is not empty
            2. PREPARE: Ensure workspace directory exists
            3. EXECUTE: Run 'openhands -t "task"' locally
            4. RETURN: Structured result object
        """
        start_time = time.time()

        # STEP 1: VALIDATE INPUT
        if not task or not task.strip():
            return OpenHandsResult(
                success=False,
                message="Task cannot be empty",
                execution_time=time.time() - start_time
            )

        try:
            # STEP 2: PREPARE WORKSPACE
            msg = f"[OpenHands] Preparing local task: {task[:50]}..."
            print(msg)
            if on_log: on_log(msg)
            
            self._start_container()
            
            # STEP 3: EXECUTE TASK VIA CLI
            msg = f"[OpenHands] Executing task locally..."
            print(msg)
            if on_log: on_log(msg)
            
            result = self._run_task_cli(task, timeout, on_log=on_log)
            
            result.execution_time = time.time() - start_time
            return result

        except Exception as e:
            return OpenHandsResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                logs=str(e),
                execution_time=time.time() - start_time
            )

        finally:
            # STEP 4: CLEANUP (Optional for local)
            if cleanup:
                pass # For now keep workspace for debugging

    def _start_container(self) -> None:
        """Prepare workspace for local task."""
        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OpenHands] Workspace ready at {self.workspace_dir.resolve()}")

    def _run_task_cli(self, task: str, timeout: int, on_log: Optional[Any] = None) -> OpenHandsResult:
        """
        Run task using local OpenHands CLI.
        """
        import os
        
        env = os.environ.copy()
        env.update({
            "LLM_MODEL": self.model,
            "LLM_BASE_URL": self.ollama_base_url if self.use_ollama else env.get("LLM_BASE_URL", ""),
            "LLM_API_BASE": self.ollama_base_url if self.use_ollama else env.get("LLM_API_BASE", ""),
            "LLM_PROVIDER": "ollama" if self.use_ollama else env.get("LLM_PROVIDER", "openai"),
            "SANDBOX_RUNTIME_CONTAINER_IMAGE": "ubuntu:22.04", # Stick to user requested image
            "SANDBOX_USE_HOST_NETWORK": "true",
            "WORKSPACE_BASE": str(self.workspace_dir.resolve()),
        })

        cmd = [
            self.openhands_bin,
            "-t", task,
            "--headless",
            "--json",
            "--always-approve"
        ]

        logs = []
        start_time = time.time()
        
        try:
            # Run with Popen for streaming
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            # Reads logs line by line
            while True:
                # Check for timeout
                if time.time() - start_time > timeout:
                    process.terminate()
                    return OpenHandsResult(
                        success=False,
                        message=f"Task timed out after {timeout} seconds",
                        logs="".join(logs) + "\n[Timeout]"
                    )
                
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    logs.append(output)
                    if on_log:
                        on_log(output.strip())
            
            returncode = process.poll()
            success = returncode == 0
            full_logs = "".join(logs)
            
            # Attempt to extract code or meaningful output from workspace
            files_changed = []
            code = ""
            
            # Check for created files in workspace
            for file in self.workspace_dir.glob("**/*"):
                 if file.is_file() and not str(file).startswith(str(self.workspace_dir / ".openhands")):
                    files_changed.append(str(file.relative_to(self.workspace_dir)))
                    # Optionally read the content if it's small
                    if file.suffix in [".py", ".md", ".txt"]:
                        try:
                            code += f"\n# File: {file.name}\n{file.read_text()}\n"
                        except:
                            pass
            
            return OpenHandsResult(
                success=success,
                message="Task completed locally" if success else "Task failed locally",
                logs=full_logs,
                code=code if code else None,
                files_changed=files_changed
            )

        except Exception as e:
            return OpenHandsResult(
                success=False,
                message=f"Error running local CLI: {str(e)}",
                logs=str(e)
            )

    def _wait_for_ready(self, timeout: int = 90) -> bool:
        return True

    def _stop_container(self) -> None:
        """No-op for local setup."""
        pass

    def _validate_ollama(self) -> None:
        """
        Validate Ollama is running and model is available.

        WHAT THIS DOES:
            Checks if Ollama service is running and requested model exists.
            Provides helpful error messages if setup incomplete.

        WHY WE DO THIS:
            Fail fast with clear instructions instead of cryptic Docker errors.

        ERROR MESSAGES:
            - Ollama not running → Instructions to start Ollama
            - Model not found → Instructions to pull model
        """
        try:
            # Check if Ollama is accessible
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            response.raise_for_status()

            # Check if model is available
            data = response.json()
            available_models = [m["name"] for m in data.get("models", [])]
            
            # Handle ollama/ prefix for validation
            check_model = self.model
            if check_model.startswith("ollama/"):
                check_model = check_model.replace("ollama/", "")

            if check_model not in available_models and self.model not in available_models:
                raise RuntimeError(
                    f"Ollama model '{self.model}' not found.\n"
                    f"Available models: {', '.join(available_models)}\n\n"
                    f"To fix, run:\n"
                    f"  ollama pull {check_model}\n"
                )

            print(f"[OpenHands] ✓ Using FREE Ollama model: {self.model}")

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Ollama not running at {self.ollama_base_url}\n\n"
                f"To fix:\n"
                f"  1. Install Ollama: winget install Ollama.Ollama\n"
                f"  2. Ollama auto-starts on Windows after install\n"
                f"  3. Or run: ollama serve\n"
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Failed to connect to Ollama: {e}\n"
                f"Make sure Ollama is running at {self.ollama_base_url}"
            )


# FACTORY FUNCTION (convenience wrapper like PLC function block)
def create_openhands_worker(
    model: str = "claude-3-5-sonnet-20241022"
) -> OpenHandsWorker:
    """
    Create a pre-configured OpenHands worker.

    WHAT THIS IS:
        Convenience function to create worker with sensible defaults.
        Like a PLC function block with default parameters.

    PARAMETERS:
        model: Which LLM OpenHands should use (default: latest Claude)

    RETURNS:
        Ready-to-use OpenHandsWorker instance

    EXAMPLE:
        worker = create_openhands_worker()
        result = worker.run_task("Fix the bug")
    """
    return OpenHandsWorker(model=model)
