"""
Simple Demo: Solve a GitHub Issue with OpenHands + Ollama

PURPOSE:
    Educational example showing how to automatically solve GitHub issues
    using FREE local LLMs (Ollama) instead of paid APIs.

WHAT THIS DEMONSTRATES:
    1. Fetching issue from GitHub
    2. Creating OpenHands worker (FREE Ollama)
    3. Generating solution
    4. Reviewing and committing

COST:
    $0.00 per issue (vs $0.15-0.50 with Claude API)

USAGE:
    poetry run python examples/solve_issue_demo.py
"""

import sys
import subprocess
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment
load_dotenv()

from agent_factory.core.agent_factory import AgentFactory


def demo_solve_issue():
    """
    Demonstrate solving a GitHub issue with FREE Ollama.

    This is a simplified version of solve_github_issues.py
    for educational purposes.
    """
    print("""
╔══════════════════════════════════════════════════════════════════╗
║       Demo: Solve GitHub Issue with FREE Ollama                 ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Step 1: Choose an issue
    print("[Step 1] Choose an issue to solve")
    print("\nLet's list open issues:")

    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--json", "number,title"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print("ERROR: Failed to fetch issues")
            print("Make sure you're in a git repo and 'gh' is authenticated")
            return

        issues = json.loads(result.stdout)

        if not issues:
            print("\nNo open issues found.")
            print("\nTo test this demo:")
            print("  1. Create a test issue on GitHub:")
            print("     gh issue create --title 'Test: Add hello function' ")
            print("        --body 'Create a function that prints hello'")
            print("  2. Run this demo again")
            return

        print(f"\nFound {len(issues)} open issues:")
        for issue in issues[:5]:  # Show first 5
            print(f"  #{issue['number']}: {issue['title']}")

        # Let user pick
        issue_num = input("\nEnter issue number to solve: ").strip()
        if not issue_num.isdigit():
            print("Invalid issue number")
            return

        issue_num = int(issue_num)

    except Exception as e:
        print(f"ERROR: {e}")
        return

    # Step 2: Fetch full issue details
    print(f"\n[Step 2] Fetching issue #{issue_num} details...")

    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_num),
             "--json", "title,body,labels"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print(f"ERROR: Could not fetch issue #{issue_num}")
            return

        issue = json.loads(result.stdout)

        print(f"\nTitle: {issue['title']}")
        print(f"Body: {issue.get('body', '(no description)')[:200]}...")

    except Exception as e:
        print(f"ERROR: {e}")
        return

    # Step 3: Create OpenHands worker
    print("\n[Step 3] Creating OpenHands worker with FREE Ollama...")

    try:
        factory = AgentFactory()
        worker = factory.create_openhands_agent()

        print(f"  Worker ready!")
        print(f"  Model: {worker.model}")
        print(f"  Using Ollama: {worker.use_ollama}")
        print(f"  Cost: $0.00 per task")

    except Exception as e:
        print(f"ERROR: Failed to create worker: {e}")
        print("\nMake sure:")
        print("  - Ollama is running: ollama list")
        print("  - Model pulled: ollama pull deepseek-coder:6.7b")
        print("  - .env has USE_OLLAMA=true")
        return

    # Step 4: Create task
    print("\n[Step 4] Creating task from issue...")

    task = f"""
GitHub Issue: {issue['title']}

Description:
{issue.get('body', 'No description provided')}

Instructions:
- Write production-ready Python code
- Add docstrings and type hints
- Include error handling
- Follow PEP 8 style
- Make it ready to commit without changes

Output:
- Complete working code
- Explain what it does
"""

    print(f"\nTask created ({len(task)} characters)")

    # Step 5: Solve with OpenHands
    print("\n[Step 5] Solving with OpenHands (FREE!)...")
    print("  This will take 10-30 seconds...")

    confirm = input("\n  Proceed? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled")
        return

    result = worker.run_task(task, timeout=300)

    # Step 6: Show results
    print("\n[Step 6] Results:")
    print("="*70)

    if result.success:
        print(f"\n✓ SUCCESS!")
        print(f"  Time: {result.execution_time:.1f}s")
        print(f"  Cost: $0.00 (FREE with Ollama!)")

        print("\n--- Generated Code ---")
        print(result.code[:500] if result.code else "(No code generated)")
        if result.code and len(result.code) > 500:
            print(f"... ({len(result.code) - 500} more characters)")
        print("--- End Code ---")

        # Step 7: Save and commit
        print("\n[Step 7] Save and commit?")

        save = input("  Save this code? (yes/no): ").strip().lower()
        if save != "yes":
            print("\nCode not saved (you can review above)")
            print("\nTo use for real, run:")
            print("  poetry run python solve_github_issues.py --issue", issue_num)
            return

        # Ask for filename
        filename = input("  Filename: ").strip()
        if not filename:
            filename = f"issue_{issue_num}_solution.py"

        # Save file
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result.code if result.code else "# Generated\n")

            print(f"  ✓ Saved to {filename}")

            # Commit
            commit = input("  Commit to git? (yes/no): ").strip().lower()
            if commit == "yes":
                subprocess.run(["git", "add", filename], check=True)
                subprocess.run([
                    "git", "commit", "-m",
                    f"feat: {issue['title']} (closes #{issue_num})"
                ], check=True)

                print(f"  ✓ Committed")

                # Push
                push = input("  Push to GitHub? (yes/no): ").strip().lower()
                if push == "yes":
                    subprocess.run(["git", "push", "origin", "main"], check=True)
                    print(f"  ✓ Pushed - Issue #{issue_num} will auto-close!")

        except Exception as e:
            print(f"  ERROR: {e}")
            return

    else:
        print(f"\n✗ FAILED")
        print(f"  Message: {result.message}")
        if result.logs:
            print(f"\n  Logs:\n{result.logs[:300]}")

    print("\n" + "="*70)
    print("\nDemo complete!")
    print("\nFor production use:")
    print("  poetry run python solve_github_issues.py --help")


if __name__ == "__main__":
    demo_solve_issue()
