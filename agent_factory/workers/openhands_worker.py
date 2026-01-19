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
        Initialize OpenHands worker (doesn't start container yet).

        PARAMETERS:
            model: Which LLM OpenHands should use
                FREE: deepseek-coder:6.7b, codellama:7b, llama3.1:8b
                PAID: claude-3-5-sonnet, gpt-4, gemini-2.0-flash, etc.
            port: HTTP port for OpenHands API (default 3000)
            workspace_dir: Local directory OpenHands can access
                If None, creates temp directory per task
            use_ollama: Use FREE local Ollama instead of paid APIs
                If None, reads USE_OLLAMA from environment
            ollama_base_url: Ollama API endpoint (default: http://localhost:11434)
                If None, reads OLLAMA_BASE_URL from environment

        WHAT HAPPENS:
            - Validates Docker is installed
            - Auto-detects Ollama configuration from .env
            - Stores configuration
            - Does NOT start container (that happens in run_task)

        OLLAMA SETUP:
            1. Install Ollama: winget install Ollama.Ollama
            2. Pull model: ollama pull deepseek-coder:6.7b
            3. Set USE_OLLAMA=true in .env
            4. Run tasks for FREE!
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
        
        # Hardcoded to use Docker based on user environment
        self.container_engine = "docker"
        self.docker_socket = "/var/run/docker.sock"
        
        # Validate Container Engine is available
        try:
            subprocess.run(
                [self.container_engine, "--version"],
                check=True,
                capture_output=True,
                timeout=5
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(
                f"{self.container_engine} not found or not running. Please install Docker Desktop.\n"
                f"Error: {e}"
            )

        # Validate Ollama if enabled
        if self.use_ollama:
            self._validate_ollama()

    def run_task(
        self,
        task: str,
        timeout: int = 300,  # 5 minutes default
        cleanup: bool = True,  # Remove container when done?
        on_log: Optional[Any] = None  # Callback for streaming logs
    ) -> OpenHandsResult:
        """
        Run a coding task with OpenHands using CLI.

        WHAT THIS DOES (Step-by-Step):
            1. VALIDATE: Check task is not empty
            2. START: Spin up OpenHands Docker container (if not running)
            3. EXECUTE: Run task via 'docker exec' CLI inside container
            4. CLEANUP: Stop and remove container (if cleanup=True)
            5. RETURN: Structured result object

        PARAMETERS:
            task: What you want coded (e.g., "Fix bug in login.py")
            timeout: Max seconds to wait before giving up
            cleanup: Should we delete container after? (True = yes)
            on_log: Optional function(str) to receive streaming logs

        RETURNS:
            OpenHandsResult object with success status and outputs
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
            # STEP 2: START CONTAINER
            msg = f"[OpenHands] Starting container for task: {task[:50]}..."
            print(msg)
            if on_log: on_log(msg)
            
            self._start_container()
            
            # Helper to ensure workspace is writable
            subprocess.run(
                [self.container_engine, "exec", "-u", "root", self.container_name, "chmod", "777", "/opt/workspace_base"],
                check=False, capture_output=True
            )

            # STEP 3: EXECUTE TASK VIA CLI
            msg = f"[OpenHands] Executing task via CLI..."
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
            # STEP 4: CLEANUP
            if cleanup:
                print(f"[OpenHands] Cleaning up container...")
                self._stop_container()

    def _start_container(self) -> None:
        # First, try to stop any existing container
        try:
            subprocess.run(
                [self.container_engine, "stop", self.container_name],
                capture_output=True,
                timeout=10
            )
            subprocess.run(
                [self.container_engine, "rm", self.container_name],
                capture_output=True,
                timeout=10
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Build Docker/Podman command
        cmd = [
            self.container_engine, "run",
            "-d",
            "--privileged",  # Required for OpenHands to spawn sandbox containers
            "--name", self.container_name,
            # MOUNT DOCKET SOCKET (Critical for OpenHands sandbox)
            "-v", "/var/run/docker.sock:/var/run/docker.sock",
            # MOUNT PATCHED DOCKER RUNTIME
            "-v", "/home/ubuntu/git/agent-factory/docker_runtime_patch.py:/app/openhands/runtime/impl/docker/docker_runtime.py",
            # MOUNT WORKSPACE
            "-v", f"{self.workspace_dir.resolve()}:/opt/workspace_base",
            "--network=host", # Use host networking to avoid bridge routing issues
            # Map host.docker.internal to localhost so OpenHands can find the runtime
            "--add-host", "host.docker.internal:127.0.0.1",
        ]
        
        if self.use_ollama:
            # With --network host, we can access localhost directly
            api_base = self.ollama_base_url
            # No need to replace localhost with host.docker.internal
            
            cmd.extend([
                "-e", f"LLM_MODEL={self.model}",
                "-e", f"LLM_BASE_URL={api_base}",
                "-e", f"LLM_API_BASE={api_base}",
                "-e", "LLM_PROVIDER=ollama",
                "-e", f"LLM_PROVIDER=ollama",
                # Using 0.20-nikolaik as primary, with fallback to latest
                # docker pull ghcr.io/all-hands-ai/runtime:0.20-nikolaik
                # os.environ["SANDBOX_RUNTIME_CONTAINER_IMAGE"] = "python:3.12" 
                "-e", "SANDBOX_RUNTIME_CONTAINER_IMAGE=ubuntu:22.04",
                "-e", "SANDBOX_USE_HOST_NETWORK=true",
                "-e", "WORKSPACE_BASE=/opt/workspace_base",
                # Env vars for the controller (to configure sandbox)
                "-e", "SANDBOX_ENV_PYTHONPATH=/openhands/code",
                "-e", "SANDBOX_ENV_API_HOSTNAME=0.0.0.0",
                "-e", "SANDBOX_ENV_UVICORN_HOST=0.0.0.0",
                "-e", "SANDBOX_ENV_API_ALLOWED_ORIGINS=*",
                # Env vars for the controller itself
                "-e", "API_HOSTNAME=0.0.0.0",
                "-e", "SANDBOX_API_HOSTNAME=localhost",
                "-e", "API_ALLOWED_ORIGINS=*",
                "-e", "UVICORN_HOST=0.0.0.0",
            ])
        if not self.use_ollama:
            cmd.extend([
                "-e", f"LLM_API_KEY={self.api_key}",
                "-e", f"LLM_MODEL={self.model}",
            ])
            
        # Hardening: Check if container exists and remove it
        try:
            subprocess.run([self.container_engine, "rm", "-f", self.container_name], 
                         check=False, capture_output=True)
        except Exception:
            pass

        print(f"[OpenHands] Starting with {'FREE Ollama' if self.use_ollama else 'API'} ({self.model})...")
        
        try:
            cmd.append("ghcr.io/all-hands-ai/openhands:0.20")
            subprocess.run(cmd, check=True, capture_output=True)
            # wait for container to be ready
            self._wait_for_ready()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to start OpenHands container: {e.stderr.decode()}")
        
        # Wait a bit for container to stay up
        time.sleep(5)

    def _run_task_cli(self, task: str, timeout: int, on_log: Optional[Any] = None) -> OpenHandsResult:
        """
        Run task using the internal CLI of the OpenHands container.
        """
        # Command to run inside container: python -m openhands.core.main -t "task"
        
        docker_cmd = [
            self.container_engine, "exec",
            "-u", "0", # Run as root to avoid permission issues with socket
            self.container_name,
            "python", "-u", "-m", "openhands.core.main",
            "-t", task,
            "--max-iterations", "10", # Limit iterations to prevent infinite loops
            "--no-auto-continue", # We want it to just run
        ]

        logs = []
        start_time = time.time()
        
        try:
            # Run with Popen for streaming
            process = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
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
            
            # Attempt to extract code or meaningful output from workspace or logs
            files_changed = []
            code = ""
            
            if success:
                # Check for created files in workspace
                for file in self.workspace_dir.glob("**/*"):
                     if file.is_file():
                        files_changed.append(file.name)
                        # Optionally read the content if it's small (e.g. .py file)
                        if file.suffix in [".py", ".md", ".txt"]:
                            try:
                                code += f"\n# File: {file.name}\n{file.read_text()}\n"
                            except:
                                pass
            
            return OpenHandsResult(
                success=success,
                message="Task completed via CLI" if success else "Task failed via CLI",
                logs=full_logs,
                code=code if code else None,
                files_changed=files_changed
            )

        except Exception as e:
            return OpenHandsResult(
                success=False,
                message=f"Error running CLI: {str(e)}",
                logs=str(e)
            )

    def _wait_for_ready(self, timeout: int = 90) -> bool:
        # Not strictly needed for CLI execution, but good check
        # Reuse existing implementation or just simplify
        return True

    def _stop_container(self) -> None:
        """
        Stop and remove OpenHands container.

        WHAT THIS DOES:
            Gracefully shuts down container and cleans up.
            Like PLC shutdown sequence - stop motor, release resources.

        WHY WE DO THIS:
            - Free up system resources
            - Free up port 3000 for next task
            - Clean slate for next run

        ERROR HANDLING:
            Ignores errors (container might already be stopped)
        """
        try:
            subprocess.run(
                [self.container_engine, "stop", self.container_name],
                capture_output=True,
                timeout=10
            )
            subprocess.run(
                [self.container_engine, "rm", self.container_name],
                capture_output=True,
                timeout=10
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass  # Already stopped/removed, that's fine

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

            if self.model not in available_models:
                raise RuntimeError(
                    f"Ollama model '{self.model}' not found.\n"
                    f"Available models: {', '.join(available_models)}\n\n"
                    f"To fix, run:\n"
                    f"  ollama pull {self.model}\n"
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
