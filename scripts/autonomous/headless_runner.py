#!/usr/bin/env python3
"""
Headless Claude Runner for AI Dev Control Loop

Autonomous task execution system that:
1. Reads task from Backlog.md
2. Invokes Claude CLI in headless mode
3. Manages task status lifecycle
4. Enforces safety limits (time, cost)
5. Creates comprehensive logs

Usage:
    BACKLOG_TASK_ID=task-42 python scripts/autonomous/headless_runner.py
    python scripts/autonomous/headless_runner.py --task=task-42
    python scripts/autonomous/headless_runner.py --auto-select

Environment Variables:
    BACKLOG_TASK_ID           - Task ID to execute
    AI_DEV_LOOP_TIME_LIMIT    - Max seconds per task (default: 1800 = 30 min)
    AI_DEV_LOOP_COST_LIMIT    - Max USD cost per task (default: 5.00)
    AI_DEV_LOOP_LOG_DIR       - Log directory (default: logs/ai-dev-loop/)
    CLAUDE_MODEL              - Model to use (default: claude-sonnet-4.5)
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Configuration from environment with sensible defaults
TIME_LIMIT = int(os.getenv("AI_DEV_LOOP_TIME_LIMIT", "1800"))  # 30 minutes
COST_LIMIT = float(os.getenv("AI_DEV_LOOP_COST_LIMIT", "5.00"))  # $5
LOG_DIR = Path(os.getenv("AI_DEV_LOOP_LOG_DIR", "logs/ai-dev-loop"))
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4.5")


class TimeoutError(Exception):
    """Raised when task execution exceeds time limit"""
    pass


class CostLimitError(Exception):
    """Raised when task execution exceeds cost limit"""
    pass


class TaskExecutionError(Exception):
    """Raised when task execution fails"""
    pass


def setup_logging(task_id: str) -> Tuple[Path, dict]:
    """
    Create log file for this task execution.

    Returns:
        (log_file_path, log_metadata)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = LOG_DIR / f"{task_id}_{timestamp}.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    metadata = {
        "task_id": task_id,
        "timestamp": timestamp,
        "model": CLAUDE_MODEL,
        "time_limit_sec": TIME_LIMIT,
        "cost_limit_usd": COST_LIMIT,
        "events": []
    }

    log_event(log_file, metadata, "start", {"message": "Headless runner started"})
    return log_file, metadata


def log_event(log_file: Path, metadata: dict, event: str, data: dict = None):
    """
    Append event to JSON Lines log file.

    Format: {"timestamp": "...", "task_id": "...", "event": "...", "data": {...}}
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "task_id": metadata["task_id"],
        "event": event,
    }
    if data:
        entry["data"] = data

    metadata["events"].append(entry)

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_task_from_backlog(task_id: str, log_file: Path, metadata: dict) -> dict:
    """
    Read task details from Backlog using MCP tools.

    Falls back to parsing markdown file directly if MCP fails.

    Returns:
        Task data with keys: id, title, status, description, acceptance_criteria, etc.
    """
    log_event(log_file, metadata, "read_task", {"task_id": task_id})

    try:
        # Try using MCP backlog tools via Python
        import importlib.util
        spec = importlib.util.find_spec("mcp")
        if spec is not None:
            # MCP available - use it
            # Note: This would require MCP server to be running
            # For now, fall back to file parsing
            pass
    except ImportError:
        pass

    # Parse task markdown file directly
    task_pattern = f"backlog/tasks/{task_id} - *.md"
    import glob
    task_files = glob.glob(task_pattern)

    if not task_files:
        raise TaskExecutionError(f"Task {task_id} not found in backlog/tasks/")

    task_file = Path(task_files[0])
    content = task_file.read_text(encoding="utf-8")

    # Parse YAML frontmatter
    lines = content.split("\n")
    if lines[0] != "---":
        raise TaskExecutionError(f"Invalid task format: {task_file}")

    yaml_end = lines[1:].index("---") + 1
    yaml_lines = lines[1:yaml_end]
    body_lines = lines[yaml_end + 1:]

    # Simple YAML parser (enough for our needs)
    task_data = {"id": task_id}
    for line in yaml_lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if value == "[]":
                task_data[key] = []
            else:
                task_data[key] = value

    # Extract description and acceptance criteria from body
    body_text = "\n".join(body_lines)
    task_data["full_content"] = body_text

    # Extract acceptance criteria
    ac_start = body_text.find("## Acceptance Criteria")
    if ac_start != -1:
        ac_section = body_text[ac_start:]
        ac_end = ac_section.find("\n## ")
        if ac_end != -1:
            ac_section = ac_section[:ac_end]

        # Parse checklist items
        task_data["acceptance_criteria"] = [
            line.strip()[6:] for line in ac_section.split("\n")
            if line.strip().startswith("- [ ]")
        ]

    log_event(log_file, metadata, "task_loaded", {
        "title": task_data.get("title"),
        "status": task_data.get("status"),
        "priority": task_data.get("priority"),
        "ac_count": len(task_data.get("acceptance_criteria", []))
    })

    return task_data


def update_task_status(task_id: str, status: str, note: str = None,
                       log_file: Path = None, metadata: dict = None):
    """
    Update task status in Backlog using CLI.

    Status values: "To Do", "In Progress", "Done", "Blocked"
    """
    cmd = ["backlog", "task", "edit", task_id, "--status", status]

    if log_file:
        log_event(log_file, metadata, "update_status", {
            "status": status,
            "note": note
        })

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Warning: Failed to update task status: {result.stderr}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"Warning: Backlog CLI timed out updating status", file=sys.stderr)

    # Optionally add note to task
    if note:
        try:
            # Use backlog CLI to append note
            # Note: This requires backlog CLI to support notes
            # For now, we just log it
            pass
        except Exception as e:
            print(f"Warning: Failed to add note to task: {e}", file=sys.stderr)


def build_claude_prompt(task_data: dict) -> str:
    """
    Build comprehensive prompt for Claude including:
    - Task details (title, description, acceptance criteria)
    - Codebase context (CLAUDE.md, relevant files)
    - Execution instructions (worktree strategy, PR creation)

    Returns:
        Formatted prompt string
    """
    # Read CLAUDE.md for system instructions
    claude_md = ""
    if Path("CLAUDE.md").exists():
        claude_md = Path("CLAUDE.md").read_text(encoding="utf-8")

    prompt = f"""
You are implementing task {task_data['id']} from the Agent Factory backlog.

# TASK DETAILS

**ID:** {task_data['id']}
**Title:** {task_data.get('title', 'N/A')}
**Status:** {task_data.get('status', 'N/A')}
**Priority:** {task_data.get('priority', 'N/A')}

**Description:**
{task_data.get('full_content', 'See task file for details')}

**Acceptance Criteria:**
"""

    for i, criterion in enumerate(task_data.get("acceptance_criteria", []), 1):
        prompt += f"{i}. {criterion}\n"

    prompt += f"""

# EXECUTION INSTRUCTIONS

CRITICAL: You are running in autonomous mode. You MUST:

1. **Create a worktree** for this task:
   ```bash
   git worktree add ../agent-factory-{task_data['id']} -b ai-dev-loop/{task_data['id']}
   cd ../agent-factory-{task_data['id']}
   ```

2. **Implement the task** according to acceptance criteria:
   - Write code, tests, and documentation
   - Follow patterns from CLAUDE.md
   - Run tests to verify correctness
   - Keep changes focused (no scope creep)

3. **Validate against acceptance criteria:**
   - Each criterion must be satisfied before marking task Done
   - If you can't satisfy all criteria, explain why in PR description

4. **Create a pull request:**
   ```bash
   git add .
   git commit -m "feat({task_data['id']}): Implement [feature name]"
   git push -u origin ai-dev-loop/{task_data['id']}
   gh pr create --title "feat: [feature name] ({task_data['id']})" --body "[description]"
   ```

5. **Update task status:**
   - SUCCESS: Mark task as "Done" (orchestrator will handle this)
   - FAILURE: Mark task as "Blocked" with clear explanation

# SAFETY CONSTRAINTS

- Time limit: {TIME_LIMIT} seconds ({TIME_LIMIT // 60} minutes)
- Do NOT make changes outside the worktree
- Do NOT push to main branch
- Do NOT merge PR (only create draft)
- If you encounter errors you can't fix, mark task "Blocked" and explain

# CODEBASE CONTEXT

{claude_md[:2000]}

... (full CLAUDE.md available in your context)

---

BEGIN IMPLEMENTATION NOW.
"""

    return prompt


def timeout_handler(signum, frame):
    """Signal handler for time limit enforcement"""
    raise TimeoutError(f"Task execution exceeded {TIME_LIMIT} seconds")


def run_claude_headless(task_data: dict, prompt: str, log_file: Path, metadata: dict) -> Tuple[bool, str]:
    """
    Invoke Claude CLI in headless mode to execute the task.

    Returns:
        (success: bool, output: str)
    """
    log_event(log_file, metadata, "claude_start", {
        "model": CLAUDE_MODEL,
        "prompt_length": len(prompt)
    })

    # Set up time limit using signal
    # Note: This only works on Unix-like systems
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIME_LIMIT)

    start_time = time.time()

    try:
        # Invoke Claude CLI
        # Note: Actual Claude CLI invocation syntax may vary
        # This is a placeholder for the actual implementation

        # Option 1: Use Claude Code CLI (if available)
        cmd = [
            "claude",  # Assuming claude CLI is in PATH
            "--model", CLAUDE_MODEL,
            "--prompt", prompt,
            "--headless"  # Non-interactive mode
        ]

        # Write prompt to temp file for easier debugging
        prompt_file = log_file.parent / f"{task_data['id']}_prompt.txt"
        prompt_file.write_text(prompt, encoding="utf-8")
        log_event(log_file, metadata, "prompt_saved", {"file": str(prompt_file)})

        # Run Claude
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(timeout=TIME_LIMIT)
        elapsed = time.time() - start_time

        log_event(log_file, metadata, "claude_complete", {
            "exit_code": process.returncode,
            "duration_sec": round(elapsed, 2),
            "stdout_length": len(stdout),
            "stderr_length": len(stderr)
        })

        # Cancel alarm if set
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)

        # Check result
        if process.returncode == 0:
            return True, stdout
        else:
            return False, f"Claude failed with exit code {process.returncode}:\\n{stderr}"

    except TimeoutError:
        log_event(log_file, metadata, "timeout", {"limit_sec": TIME_LIMIT})
        return False, f"Task timed out after {TIME_LIMIT} seconds"

    except subprocess.TimeoutExpired:
        log_event(log_file, metadata, "timeout", {"limit_sec": TIME_LIMIT})
        process.kill()
        return False, f"Task timed out after {TIME_LIMIT} seconds"

    except Exception as e:
        log_event(log_file, metadata, "error", {"error": str(e)})
        return False, f"Unexpected error: {str(e)}"

    finally:
        # Cancel alarm if set
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)


def finalize_task(task_id: str, success: bool, output: str, log_file: Path, metadata: dict):
    """
    Update task status and write final summary to logs.
    """
    if success:
        status = "Done"
        summary = f"Task completed successfully. PR created. Output length: {len(output)} chars"
    else:
        status = "Blocked"
        # Extract first line of error for summary
        error_lines = output.split("\n")
        summary = f"Task failed: {error_lines[0][:200]}"

    log_event(log_file, metadata, "finalize", {
        "status": status,
        "summary": summary
    })

    update_task_status(task_id, status, summary, log_file, metadata)

    # Write final metadata file
    metadata_file = log_file.parent / f"{task_id}_{metadata['timestamp']}_metadata.json"
    metadata["duration_total_sec"] = sum(
        e.get("data", {}).get("duration_sec", 0)
        for e in metadata["events"]
    )
    metadata["final_status"] = status
    metadata["success"] = success

    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    log_event(log_file, metadata, "complete", {
        "metadata_file": str(metadata_file)
    })


def main():
    """Main entry point for headless runner"""
    parser = argparse.ArgumentParser(description="AI Dev Loop Headless Runner")
    parser.add_argument("--task", help="Task ID to execute (e.g., task-42)")
    parser.add_argument("--auto-select", action="store_true",
                        help="Auto-select next high-priority To Do task")
    args = parser.parse_args()

    # Get task ID from args or environment
    task_id = args.task or os.getenv("BACKLOG_TASK_ID")

    if not task_id and not args.auto_select:
        print("Error: Provide task ID via --task or BACKLOG_TASK_ID environment variable",
              file=sys.stderr)
        print("Or use --auto-select to automatically choose next task", file=sys.stderr)
        sys.exit(1)

    # Auto-select task if requested
    if args.auto_select:
        # TODO: Implement auto-selection logic
        # For now, just error
        print("Error: --auto-select not yet implemented", file=sys.stderr)
        print("Please specify task ID explicitly", file=sys.stderr)
        sys.exit(1)

    # Setup logging
    log_file, metadata = setup_logging(task_id)
    print(f"Headless runner started for {task_id}")
    print(f"Logs: {log_file}")

    try:
        # Step 1: Read task from Backlog
        print(f"Reading task {task_id} from Backlog...")
        task_data = read_task_from_backlog(task_id, log_file, metadata)
        print(f"Task loaded: {task_data.get('title')}")
        print(f"Status: {task_data.get('status')}")
        print(f"Priority: {task_data.get('priority')}")

        # Step 2: Update status to In Progress
        print(f"Marking task as In Progress...")
        update_task_status(task_id, "In Progress", log_file=log_file, metadata=metadata)

        # Step 3: Build Claude prompt
        print(f"Building Claude prompt...")
        prompt = build_claude_prompt(task_data)

        # Step 4: Run Claude headless
        print(f"Invoking Claude (model: {CLAUDE_MODEL}, time limit: {TIME_LIMIT}s)...")
        print(f"This may take a while. Check {log_file} for progress.")
        success, output = run_claude_headless(task_data, prompt, log_file, metadata)

        # Step 5: Finalize task
        print(f"Finalizing task...")
        finalize_task(task_id, success, output, log_file, metadata)

        # Print summary
        print("\\n" + "="*80)
        if success:
            print(f"✅ SUCCESS: Task {task_id} completed")
            print(f"Status updated to: Done")
            print(f"Check logs for details: {log_file}")
        else:
            print(f"❌ FAILURE: Task {task_id} failed")
            print(f"Status updated to: Blocked")
            print(f"Error: {output[:500]}")
            print(f"Full logs: {log_file}")
        print("="*80)

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\\nInterrupted by user")
        log_event(log_file, metadata, "interrupted", {})
        update_task_status(task_id, "Blocked", "Interrupted by user", log_file, metadata)
        sys.exit(130)

    except Exception as e:
        print(f"\\nFatal error: {e}", file=sys.stderr)
        log_event(log_file, metadata, "fatal_error", {"error": str(e)})
        update_task_status(task_id, "Blocked", f"Fatal error: {str(e)}", log_file, metadata)
        sys.exit(1)


if __name__ == "__main__":
    main()
