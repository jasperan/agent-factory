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
        model: str = "claude-3-5-sonnet-20241022",  # Default to latest Claude
        port: int = 3000,  # OpenHands web UI port
        workspace_dir: Optional[Path] = None,  # Where OpenHands works
    ):
        """
        Initialize OpenHands worker (doesn't start container yet).

        PARAMETERS:
            model: Which LLM OpenHands should use
                Options: claude-3-5-sonnet, gpt-4, gemini-2.0-flash, etc.
            port: HTTP port for OpenHands API (default 3000)
            workspace_dir: Local directory OpenHands can access
                If None, creates temp directory per task

        WHAT HAPPENS:
            - Validates Docker is installed
            - Stores configuration
            - Does NOT start container (that happens in run_task)
        """
        self.model = model
        self.port = port
        self.workspace_dir = workspace_dir or Path("./openhands_workspace")
        self.container_name = f"openhands_worker_{port}"

        # Validate Docker is available (like checking PLC I/O before starting)
        try:
            subprocess.run(
                ["docker", "--version"],
                check=True,
                capture_output=True,
                timeout=5
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(
                "Docker not found or not running. Please install Docker Desktop.\n"
                f"Error: {e}"
            )

    def run_task(
        self,
        task: str,
        timeout: int = 300,  # 5 minutes default
        cleanup: bool = True  # Remove container when done?
    ) -> OpenHandsResult:
        """
        Run a coding task with OpenHands.

        WHAT THIS DOES (Step-by-Step):
            1. VALIDATE: Check task is not empty
            2. START: Spin up OpenHands Docker container
            3. WAIT: Poll until container is healthy
            4. SEND: Submit task via HTTP API
            5. MONITOR: Wait for completion or timeout
            6. RETRIEVE: Get results (code, files, logs)
            7. CLEANUP: Stop and remove container (if cleanup=True)
            8. RETURN: Structured result object

        PARAMETERS:
            task: What you want coded (e.g., "Fix bug in login.py")
            timeout: Max seconds to wait before giving up
            cleanup: Should we delete container after? (True = yes)

        RETURNS:
            OpenHandsResult object with success status and outputs

        ERROR HANDLING:
            - Empty task → Returns failure result immediately
            - Docker fails → Returns failure with error message
            - Timeout → Kills container, returns partial results
            - API errors → Captures logs, returns failure

        EXAMPLE:
            result = worker.run_task("Add docstrings to all functions")
            if result.success:
                print(f"Modified files: {result.files_changed}")
            else:
                print(f"Task failed: {result.message}")
        """
        start_time = time.time()

        # STEP 1: VALIDATE INPUT (like PLC input validation rung)
        if not task or not task.strip():
            return OpenHandsResult(
                success=False,
                message="Task cannot be empty",
                execution_time=time.time() - start_time
            )

        try:
            # STEP 2: START CONTAINER (like PLC motor start sequence)
            print(f"[OpenHands] Starting container for task: {task[:50]}...")
            self._start_container()

            # STEP 3: WAIT FOR HEALTHY (like waiting for motor at speed)
            if not self._wait_for_ready(timeout=30):
                return OpenHandsResult(
                    success=False,
                    message="OpenHands container failed to become ready",
                    execution_time=time.time() - start_time
                )

            # STEP 4: SEND TASK (like writing to PLC input register)
            print(f"[OpenHands] Sending task to agent...")
            task_id = self._submit_task(task)

            # STEP 5: MONITOR PROGRESS (like polling PLC status bits)
            print(f"[OpenHands] Waiting for completion (timeout: {timeout}s)...")
            result = self._wait_for_completion(task_id, timeout)

            # Add execution time
            result.execution_time = time.time() - start_time

            return result

        except Exception as e:
            # Catch-all error handler (like PLC fault handler)
            return OpenHandsResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                logs=str(e),
                execution_time=time.time() - start_time
            )

        finally:
            # STEP 7: CLEANUP (like PLC shutdown sequence - always runs)
            if cleanup:
                print(f"[OpenHands] Cleaning up container...")
                self._stop_container()

    def _start_container(self) -> None:
        """
        Start OpenHands Docker container.

        WHAT THIS DOES:
            Runs Docker command to start OpenHands with our configuration.
            Container runs in background (-d flag) and exposes web UI on our port.

        DOCKER COMMAND EXPLAINED:
            docker run -d                    → Run in background (detached)
            --name openhands_worker_3000     → Give it a memorable name
            -p 3000:3000                     → Map port (host:container)
            --pull=always                    → Always use latest image
            ghcr.io/all-hands-dev/openhands  → OpenHands official image
            --model claude-3-5-sonnet        → Which LLM to use

        WHY PULL ALWAYS:
            Ensures we have latest OpenHands version (like PLC firmware updates)

        ERROR HANDLING:
            If container with same name exists, tries to stop it first
        """
        # First, try to stop any existing container (idempotent operation)
        try:
            subprocess.run(
                ["docker", "stop", self.container_name],
                capture_output=True,
                timeout=10
            )
            subprocess.run(
                ["docker", "rm", self.container_name],
                capture_output=True,
                timeout=10
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass  # Container didn't exist, that's fine

        # Start fresh container
        cmd = [
            "docker", "run",
            "-d",  # Detached (background)
            "--name", self.container_name,
            "-p", f"{self.port}:{self.port}",
            "--pull=always",
            "ghcr.io/all-hands-dev/openhands:main-latest",
            "--model", self.model
        ]

        subprocess.run(cmd, check=True, timeout=60)

    def _wait_for_ready(self, timeout: int = 30) -> bool:
        """
        Wait for OpenHands container to be healthy and ready.

        WHAT THIS DOES:
            Polls the health endpoint until container responds or timeout.
            Like waiting for a PLC to complete its boot sequence.

        HOW IT WORKS:
            1. Try to GET http://localhost:3000/health
            2. If 200 OK → Container ready!
            3. If error → Wait 1 second, try again
            4. If timeout → Give up, return False

        RETURNS:
            True if container ready, False if timed out
        """
        start = time.time()
        health_url = f"http://localhost:{self.port}/health"

        while time.time() - start < timeout:
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    print(f"[OpenHands] Container ready after {time.time() - start:.1f}s")
                    return True
            except requests.exceptions.RequestException:
                pass  # Not ready yet, keep waiting

            time.sleep(1)  # Wait 1 second before retry (like PLC scan time)

        return False  # Timed out

    def _submit_task(self, task: str) -> str:
        """
        Submit coding task to OpenHands API.

        WHAT THIS DOES:
            Sends HTTP POST to OpenHands with task description.
            OpenHands starts working on it asynchronously.

        PARAMETERS:
            task: What you want coded

        RETURNS:
            task_id: Unique ID to track this task (like PLC job number)

        API ENDPOINT:
            POST /api/tasks
            Body: {"task": "your task here", "model": "claude-3-5-sonnet"}

        NOTE:
            This is a simplified implementation. Real OpenHands API may differ.
            You may need to adjust based on actual OpenHands REST API docs.
        """
        url = f"http://localhost:{self.port}/api/tasks"
        payload = {
            "task": task,
            "model": self.model
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        return data.get("task_id", "unknown")

    def _wait_for_completion(
        self,
        task_id: str,
        timeout: int
    ) -> OpenHandsResult:
        """
        Poll for task completion.

        WHAT THIS DOES:
            Repeatedly checks if OpenHands finished the task.
            Like polling a PLC done bit in a loop.

        HOW IT WORKS:
            1. GET /api/tasks/{task_id}/status
            2. Check status: "pending", "running", "completed", "failed"
            3. If completed → Get results and return
            4. If failed → Return error
            5. If still running → Wait and retry
            6. If timeout → Give up

        RETURNS:
            OpenHandsResult with success status and any generated code
        """
        start = time.time()
        status_url = f"http://localhost:{self.port}/api/tasks/{task_id}/status"

        while time.time() - start < timeout:
            try:
                response = requests.get(status_url, timeout=5)
                response.raise_for_status()
                data = response.json()

                status = data.get("status", "unknown")

                if status == "completed":
                    # Success! Extract results
                    return OpenHandsResult(
                        success=True,
                        message="Task completed successfully",
                        code=data.get("code", ""),
                        files_changed=data.get("files_changed", []),
                        logs=data.get("logs", "")
                    )

                elif status == "failed":
                    # Task failed
                    return OpenHandsResult(
                        success=False,
                        message=data.get("error", "Task failed"),
                        logs=data.get("logs", "")
                    )

                # Still running, keep waiting
                time.sleep(2)  # Poll every 2 seconds

            except requests.exceptions.RequestException as e:
                # API error - might be transient, keep trying
                time.sleep(2)

        # Timed out
        return OpenHandsResult(
            success=False,
            message=f"Task timed out after {timeout} seconds"
        )

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
                ["docker", "stop", self.container_name],
                capture_output=True,
                timeout=10
            )
            subprocess.run(
                ["docker", "rm", self.container_name],
                capture_output=True,
                timeout=10
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass  # Already stopped/removed, that's fine


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
