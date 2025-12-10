#!/usr/bin/env python3
"""
GitHub Issue Solver - Autonomous issue resolution with OpenHands + Ollama

PURPOSE:
    Automatically solve GitHub issues using FREE local LLMs.
    Fetches issues, generates solutions with OpenHands, commits results.

COST:
    $0.00 per issue (uses Ollama instead of $0.15-0.50 paid APIs)
    Annual savings: $780-2,600 for 10 issues/week

USAGE:
    poetry run python solve_github_issues.py --issue 52
    poetry run python solve_github_issues.py --label "agent-task"
    poetry run python solve_github_issues.py --all --dry-run
    poetry run python solve_github_issues.py --issue 52 --timeout 600

WORKFLOW:
    1. Fetch issue from GitHub (gh CLI)
    2. Convert to OpenHands task
    3. Solve with FREE Ollama (DeepSeek Coder)
    4. Review generated code
    5. Get your approval
    6. Commit and push
    7. Issue auto-closes

REQUIREMENTS:
    - GitHub CLI (gh) authenticated
    - Ollama running with model pulled
    - USE_OLLAMA=true in .env
    - Git repository
"""

import subprocess
import json
import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment
load_dotenv()

from agent_factory.core.agent_factory import AgentFactory
from agent_factory.workers.openhands_worker import OpenHandsResult


# =============================================================================
# Configuration
# =============================================================================

# Default timeout for OpenHands tasks (seconds)
DEFAULT_TIMEOUT = 300  # 5 minutes

# Maximum code preview length
MAX_CODE_PREVIEW = 1000  # characters

# Statistics tracking
class Stats:
    """Track session statistics"""
    def __init__(self):
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.total_time = 0.0
        self.total_cost = 0.0  # Always $0.00 with Ollama!

    def add_success(self, time_taken: float):
        self.processed += 1
        self.successful += 1
        self.total_time += time_taken

    def add_failure(self, time_taken: float):
        self.processed += 1
        self.failed += 1
        self.total_time += time_taken

    def summary(self) -> str:
        if self.processed == 0:
            return "No issues processed"

        success_rate = (self.successful / self.processed) * 100
        avg_time = self.total_time / self.processed

        return f"""
Session Summary:
- Issues processed: {self.processed}
- Successful: {self.successful}
- Failed: {self.failed}
- Success rate: {success_rate:.1f}%
- Total time: {self.total_time:.1f}s
- Avg time per issue: {avg_time:.1f}s
- Total cost: $0.00 (FREE with Ollama!)
- Savings vs Claude API: ${self.processed * 0.25:.2f}
"""


# =============================================================================
# GitHub CLI Functions
# =============================================================================

def check_gh_cli() -> bool:
    """
    Check if GitHub CLI is installed and authenticated.

    Returns:
        bool: True if gh CLI is ready to use
    """
    try:
        # Check if gh is installed
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            timeout=5
        )

        if result.returncode != 0:
            print("ERROR: GitHub CLI (gh) not found")
            print("Install: https://cli.github.com/")
            return False

        # Check if authenticated
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            timeout=5
        )

        if result.returncode != 0:
            print("ERROR: Not authenticated with GitHub")
            print("Run: gh auth login")
            return False

        return True

    except Exception as e:
        print(f"ERROR: Failed to check gh CLI: {e}")
        return False


def get_issue(issue_number: int) -> Optional[Dict]:
    """
    Fetch issue details from GitHub.

    Args:
        issue_number: GitHub issue number

    Returns:
        Dict with issue details, or None if failed
    """
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number),
             "--json", "title,body,labels,number,state"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print(f"ERROR: Failed to fetch issue #{issue_number}")
            print(result.stderr)
            return None

        return json.loads(result.stdout)

    except Exception as e:
        print(f"ERROR: Failed to fetch issue: {e}")
        return None


def get_issues_by_label(label: str) -> List[Dict]:
    """
    Fetch all issues with specific label.

    Args:
        label: Label to filter by (e.g., "agent-task")

    Returns:
        List of issue dicts
    """
    try:
        result = subprocess.run(
            ["gh", "issue", "list",
             "--label", label,
             "--json", "title,body,labels,number,state"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print(f"ERROR: Failed to fetch issues with label '{label}'")
            print(result.stderr)
            return []

        return json.loads(result.stdout)

    except Exception as e:
        print(f"ERROR: Failed to fetch issues: {e}")
        return []


def get_all_issues() -> List[Dict]:
    """
    Fetch all open issues.

    Returns:
        List of issue dicts
    """
    try:
        result = subprocess.run(
            ["gh", "issue", "list",
             "--json", "title,body,labels,number,state"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print("ERROR: Failed to fetch issues")
            print(result.stderr)
            return []

        return json.loads(result.stdout)

    except Exception as e:
        print(f"ERROR: Failed to fetch issues: {e}")
        return []


# =============================================================================
# OpenHands Task Generation
# =============================================================================

def create_task_from_issue(issue: Dict) -> str:
    """
    Convert GitHub issue to OpenHands task.

    Creates a detailed task description that includes:
    - Issue title and body
    - Label-derived requirements
    - Codebase context
    - Quality standards
    - Agent Factory patterns

    Args:
        issue: Issue dict from GitHub CLI

    Returns:
        str: Task description for OpenHands
    """
    title = issue["title"]
    body = issue.get("body", "")
    number = issue["number"]
    labels = [l["name"] for l in issue.get("labels", [])]

    # Determine requirements based on labels
    requirements = []
    if "bug" in labels:
        requirements.append("- Fix the bug and add regression tests")
        requirements.append("- Identify root cause and document")
    if "enhancement" in labels:
        requirements.append("- Implement new functionality")
        requirements.append("- Follow existing code patterns")
    if "documentation" in labels:
        requirements.append("- Write clear, comprehensive documentation")
        requirements.append("- Include examples and usage")
    if "test" in labels:
        requirements.append("- Write comprehensive unit tests")
        requirements.append("- Achieve >90% code coverage")

    # Default requirements
    if not requirements:
        requirements = [
            "- Write production-ready code",
            "- Follow Agent Factory patterns",
        ]

    # Build task
    task = f"""
GitHub Issue #{number}: {title}

Issue Description:
{body if body else '(No description provided)'}

Labels: {', '.join(labels) if labels else 'None'}

Requirements:
{chr(10).join(requirements)}
- Add comprehensive docstrings (Google style)
- Include type hints for all functions
- Add error handling for edge cases
- Follow PEP 8 style guide
- Write code that works without modifications

Context:
- This is for the Agent Factory project
- Look for similar patterns in agent_factory/ directory
- Follow existing code structure and naming conventions
- Use existing utilities and helpers where possible

Output:
- Complete, working code ready to commit
- If multiple files needed, provide all of them
- Include any necessary imports
- Add TODO comments for manual steps if needed
"""

    return task


# =============================================================================
# Solution Validation
# =============================================================================

def validate_code_syntax(code: str) -> bool:
    """
    Validate Python code syntax.

    Args:
        code: Python code to validate

    Returns:
        bool: True if syntax is valid
    """
    try:
        import ast
        ast.parse(code)
        return True
    except SyntaxError as e:
        print(f"  [WARNING] Syntax error: {e}")
        return False


def check_for_secrets(code: str) -> List[str]:
    """
    Check for potential hardcoded secrets in code.

    Args:
        code: Code to check

    Returns:
        List of warnings
    """
    warnings = []

    # Simple pattern checks
    if "sk-" in code and "api" in code.lower():
        warnings.append("Possible API key detected (sk-)")
    if "password" in code.lower() and "=" in code:
        warnings.append("Possible hardcoded password")
    if "secret" in code.lower() and "=" in code:
        warnings.append("Possible hardcoded secret")

    return warnings


# =============================================================================
# Issue Solving
# =============================================================================

def solve_issue(
    issue_number: int,
    worker,
    timeout: int = DEFAULT_TIMEOUT,
    dry_run: bool = False,
    auto_approve: bool = False
) -> bool:
    """
    Solve a single GitHub issue with OpenHands.

    Workflow:
        1. Fetch issue details
        2. Generate OpenHands task
        3. Solve with FREE Ollama
        4. Validate solution
        5. Get approval (unless auto_approve)
        6. Commit and push
        7. Issue auto-closes

    Args:
        issue_number: GitHub issue number
        worker: OpenHandsWorker instance
        timeout: Max seconds for OpenHands
        dry_run: If True, show what would be done but don't commit
        auto_approve: If True, skip approval prompt

    Returns:
        bool: True if successfully solved and committed
    """
    print(f"\n{'='*70}")
    print(f"  Processing Issue #{issue_number}")
    print(f"{'='*70}")

    # Fetch issue
    print("\n[1/7] Fetching issue from GitHub...")
    issue = get_issue(issue_number)

    if not issue:
        print(f"  ERROR: Could not fetch issue #{issue_number}")
        return False

    if issue["state"] != "OPEN":
        print(f"  WARNING: Issue is {issue['state']}, skipping")
        return False

    print(f"  Title: {issue['title']}")
    labels = [l["name"] for l in issue.get("labels", [])]
    print(f"  Labels: {', '.join(labels) if labels else 'None'}")

    # Create task
    print("\n[2/7] Creating OpenHands task...")
    task = create_task_from_issue(issue)
    print(f"  Task length: {len(task)} characters")

    if dry_run:
        print("\n[DRY RUN] Would send this task to OpenHands:")
        print("-" * 70)
        print(task)
        print("-" * 70)
        return False

    # Solve with OpenHands
    print(f"\n[3/7] Solving with OpenHands (FREE Ollama, timeout: {timeout}s)...")
    print("  This may take 10-60 seconds...")

    start_time = time.time()
    result = worker.run_task(task, timeout=timeout)
    elapsed = time.time() - start_time

    if not result.success:
        print(f"\n  ERROR: OpenHands failed")
        print(f"  Message: {result.message}")
        if result.logs:
            print(f"\n  Logs:\n{result.logs[:500]}")
        return False

    print(f"  SUCCESS in {elapsed:.1f}s")
    print(f"  Cost: $0.00 (FREE with Ollama!)")

    # Validate solution
    print("\n[4/7] Validating solution...")

    if result.code:
        # Check syntax
        if validate_code_syntax(result.code):
            print("  [OK] Syntax valid")
        else:
            print("  [WARNING] Syntax errors detected")

        # Check for secrets
        warnings = check_for_secrets(result.code)
        if warnings:
            print("  [WARNING] Security concerns:")
            for w in warnings:
                print(f"    - {w}")
        else:
            print("  [OK] No obvious security issues")

    # Show generated code
    print("\n[5/7] Generated solution:")
    print("-" * 70)
    if result.code:
        preview = result.code[:MAX_CODE_PREVIEW]
        print(preview)
        if len(result.code) > MAX_CODE_PREVIEW:
            remaining = len(result.code) - MAX_CODE_PREVIEW
            print(f"\n... ({remaining} more characters)")
    else:
        print("(No code generated - check if this was a documentation task)")
    print("-" * 70)

    if result.files_changed:
        print(f"\nFiles changed: {', '.join(result.files_changed)}")

    # Get approval
    if not auto_approve:
        print("\n[6/7] Approval required:")
        approval = input("  Apply this solution? (yes/no): ").strip().lower()

        if approval != "yes":
            print("  Solution rejected by user")
            return False
    else:
        print("\n[6/7] Auto-approving (--auto-approve flag)")

    # Save and commit
    print("\n[7/7] Saving and committing...")

    # Determine filename
    if result.files_changed:
        filename = result.files_changed[0]
    else:
        # Ask user
        suggested = f"issue_{issue_number}_solution.py"
        filename = input(f"  Filename to save ({suggested}): ").strip()
        if not filename:
            filename = suggested

    # Write file
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result.code if result.code else "# Generated by OpenHands\n")

        print(f"  [OK] Saved to {filename}")
    except Exception as e:
        print(f"  ERROR: Failed to save file: {e}")
        return False

    # Commit
    commit_msg = f"feat: {issue['title']} (closes #{issue_number})"

    try:
        subprocess.run(["git", "add", filename], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print(f"  [OK] Committed: {commit_msg}")
    except subprocess.CalledProcessError as e:
        print(f"  ERROR: Git commit failed: {e}")
        return False

    # Push
    push = input("  Push to GitHub? (yes/no): ").strip().lower()
    if push == "yes":
        try:
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print(f"  [OK] Pushed to GitHub")
            print(f"  [OK] Issue #{issue_number} will auto-close")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: Git push failed: {e}")
            return False
    else:
        print("  [INFO] Not pushed - run 'git push' manually")
        print(f"  [INFO] Issue will close when you push")

    print(f"\n{'='*70}")
    print(f"  Issue #{issue_number} SOLVED!")
    print(f"  Time: {elapsed:.1f}s | Cost: $0.00")
    print(f"{'='*70}")

    return True


# =============================================================================
# Main Function
# =============================================================================

def main():
    """
    Main entry point for GitHub issue solver.

    Handles command-line arguments and orchestrates solving.
    """
    parser = argparse.ArgumentParser(
        description="Solve GitHub issues autonomously with OpenHands + Ollama (FREE!)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Solve single issue
  %(prog)s --issue 52

  # Solve all "agent-task" labeled issues
  %(prog)s --label "agent-task"

  # See what would be solved (no changes)
  %(prog)s --label "agent-task" --dry-run

  # Solve all open issues with custom timeout
  %(prog)s --all --timeout 600

  # Auto-approve (skip confirmation)
  %(prog)s --issue 52 --auto-approve

Cost:
  $0.00 per issue with Ollama (vs $0.15-0.50 with Claude API)
  Annual savings: $780-2,600 for 10 issues/week
        """
    )

    # Issue selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--issue", type=int, help="Solve single issue by number")
    group.add_argument("--label", help="Solve all issues with this label")
    group.add_argument("--all", action="store_true", help="Solve all open issues")

    # Options
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                       help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done but don't commit")
    parser.add_argument("--auto-approve", action="store_true",
                       help="Skip approval prompt (use with caution!)")

    args = parser.parse_args()

    # Print header
    print("""
╔══════════════════════════════════════════════════════════════════╗
║        GitHub Issue Solver - OpenHands + Ollama (FREE!)          ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Check prerequisites
    print("[Prerequisites]")

    if not check_gh_cli():
        print("\nERROR: GitHub CLI not ready")
        sys.exit(1)
    print("  [OK] GitHub CLI authenticated")

    # Create OpenHands worker
    print("\n[Creating Worker]")
    print("  Loading OpenHands with FREE Ollama...")

    try:
        factory = AgentFactory()
        worker = factory.create_openhands_agent()
        print("  [OK] Worker ready")
        print(f"  Model: {worker.model}")
        print(f"  Using Ollama: {worker.use_ollama}")
        print(f"  Cost per task: $0.00")
    except Exception as e:
        print(f"  ERROR: Failed to create worker: {e}")
        print("\n  Make sure:")
        print("    - Ollama is running: ollama list")
        print("    - Model is pulled: ollama pull deepseek-coder:6.7b")
        print("    - .env has USE_OLLAMA=true")
        sys.exit(1)

    # Solve issues
    stats = Stats()

    if args.issue:
        # Single issue
        print(f"\n[Mode] Solving single issue #{args.issue}")

        start = time.time()
        success = solve_issue(
            args.issue,
            worker,
            timeout=args.timeout,
            dry_run=args.dry_run,
            auto_approve=args.auto_approve
        )
        elapsed = time.time() - start

        if success:
            stats.add_success(elapsed)
        else:
            stats.add_failure(elapsed)

    elif args.label:
        # Issues by label
        print(f"\n[Mode] Solving issues with label '{args.label}'")

        issues = get_issues_by_label(args.label)
        print(f"Found {len(issues)} issues")

        if not issues:
            print("No issues to solve")
            sys.exit(0)

        for issue in issues:
            start = time.time()
            success = solve_issue(
                issue["number"],
                worker,
                timeout=args.timeout,
                dry_run=args.dry_run,
                auto_approve=args.auto_approve
            )
            elapsed = time.time() - start

            if success:
                stats.add_success(elapsed)
            else:
                stats.add_failure(elapsed)

    elif args.all:
        # All open issues
        print("\n[Mode] Solving ALL open issues")

        issues = get_all_issues()
        print(f"Found {len(issues)} open issues")

        if not issues:
            print("No issues to solve")
            sys.exit(0)

        confirm = input(f"\nProcess {len(issues)} issues? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled")
            sys.exit(0)

        for issue in issues:
            start = time.time()
            success = solve_issue(
                issue["number"],
                worker,
                timeout=args.timeout,
                dry_run=args.dry_run,
                auto_approve=args.auto_approve
            )
            elapsed = time.time() - start

            if success:
                stats.add_success(elapsed)
            else:
                stats.add_failure(elapsed)

    # Print summary
    print("\n" + "="*70)
    print(stats.summary())
    print("="*70)


if __name__ == "__main__":
    main()
