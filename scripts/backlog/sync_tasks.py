#!/usr/bin/env python3
"""
TASK.md Sync Script - Phase 3 of Backlog.md Integration

Syncs Backlog.md task statuses to TASK.md for Claude Code integration.
One-way sync: Backlog → TASK.md (Backlog is source of truth).

Usage:
    poetry run python scripts/backlog/sync_tasks.py                     # Full sync
    poetry run python scripts/backlog/sync_tasks.py --dry-run           # Preview changes
    poetry run python scripts/backlog/sync_tasks.py --section current   # Sync only current task
"""

import argparse
import re
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Sync zone markers
CURRENT_BEGIN = "<!-- BACKLOG_SYNC:CURRENT:BEGIN -->"
CURRENT_END = "<!-- BACKLOG_SYNC:CURRENT:END -->"
USER_ACTIONS_BEGIN = "<!-- BACKLOG_SYNC:USER_ACTIONS:BEGIN -->"
USER_ACTIONS_END = "<!-- BACKLOG_SYNC:USER_ACTIONS:END -->"
BACKLOG_BEGIN = "<!-- BACKLOG_SYNC:BACKLOG:BEGIN -->"
BACKLOG_END = "<!-- BACKLOG_SYNC:BACKLOG:END -->"


def get_backlog_tasks_cli(status: str) -> List[Dict]:
    """
    Query Backlog tasks using CLI (backlog task list).

    Args:
        status: Task status filter ("To Do", "In Progress", "Done")

    Returns:
        List of task dicts with: id, title, priority, labels, description
    """
    try:
        # Run backlog task list command with --plain for plain text output
        # Use shell=True on Windows to find backlog in PATH
        is_windows = platform.system() == "Windows"
        result = subprocess.run(
            ["backlog", "task", "list", "--status", status, "--plain"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=is_windows
        )

        if result.returncode != 0:
            print(f"Warning: backlog CLI returned error for status='{status}'")
            print(f"stderr: {result.stderr}")
            return []

        # Parse plain text output
        # Format:  [PRIORITY] task-id - Title
        tasks = []
        if result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            for line in lines:
                line = line.strip()
                # Skip header line (e.g., "To Do:" or "In Progress:")
                if not line or line.endswith(':'):
                    continue

                # Parse format: [PRIORITY] task-id - Title
                match = re.match(r'\s*(?:\[([A-Z]+)\]\s+)?(task-[^\s]+)\s+-\s+(.+)', line)
                if match:
                    priority = match.group(1).lower() if match.group(1) else "medium"
                    task_id = match.group(2)
                    title = match.group(3)

                    tasks.append({
                        "id": task_id,
                        "title": title,
                        "priority": priority,
                        "labels": [],  # Not available in plain output
                        "description": f"View task details: `backlog task view {task_id}`"
                    })
        return tasks

    except FileNotFoundError:
        print("ERROR: 'backlog' CLI not found. Please install Backlog.md CLI.")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: backlog CLI timed out")
        return []


def get_task_details(task_id: str) -> Dict:
    """
    Query full task metadata including labels using backlog task view.

    Parses file content to extract YAML frontmatter and acceptance criteria.

    Args:
        task_id: Task identifier (e.g., "task-14")

    Returns:
        Dict with full task metadata (id, title, priority, labels, acceptance_criteria, etc.)
    """
    try:
        # Read task file directly from backlog/tasks/ directory
        repo_root = Path(__file__).parent.parent.parent
        task_files = list((repo_root / "backlog" / "tasks").glob(f"{task_id} - *.md"))

        if not task_files:
            print(f"Warning: Task file not found for {task_id}")
            return {}

        task_file = task_files[0]
        content = task_file.read_text(encoding='utf-8')

        # Extract YAML frontmatter between --- markers
        yaml_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
        if not yaml_match:
            return {"id": task_id}

        yaml_content = yaml_match.group(1)

        # Parse YAML (simple key-value + list parsing)
        task_data = {"id": task_id}
        current_key = None
        current_list = []

        for line in yaml_content.split('\n'):
            line_stripped = line.strip()

            # Key-value line
            if ':' in line and not line.startswith('  ') and not line.startswith('-'):
                # Save previous list if exists
                if current_key and current_list:
                    task_data[current_key] = current_list
                    current_list = []
                    current_key = None

                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip("'\"")

                if value:
                    task_data[key] = value
                else:
                    current_key = key  # List follows

            # List item
            elif line_stripped.startswith('- '):
                item = line_stripped[2:].strip()
                current_list.append(item)

        # Finalize last list
        if current_key and current_list:
            task_data[current_key] = current_list

        # Extract acceptance criteria from markdown content
        ac_match = re.search(r'<!-- AC:BEGIN -->(.*?)<!-- AC:END -->', content, re.DOTALL)
        if ac_match:
            ac_text = ac_match.group(1)
            # Parse checkbox lines: - [ ] #1 Description
            ac_lines = re.findall(r'- \[ \] #(\d+) (.+)', ac_text)
            task_data['acceptance_criteria'] = [text for num, text in ac_lines]

        # Extract description
        desc_match = re.search(r'<!-- SECTION:DESCRIPTION:BEGIN -->(.*?)<!-- SECTION:DESCRIPTION:END -->', content, re.DOTALL)
        if desc_match:
            task_data['description'] = desc_match.group(1).strip()

        return task_data

    except Exception as e:
        print(f"Warning: Error reading task {task_id}: {e}")
        return {"id": task_id}


def get_user_action_tasks() -> List[Dict]:
    """
    Query all To Do tasks with 'user-action' label.

    Returns:
        List of user action task dicts with full metadata
    """
    # Get all To Do tasks (lightweight query)
    all_tasks = get_backlog_tasks_cli(status="To Do")

    # Filter by fetching details for each task
    user_actions = []

    for task in all_tasks:
        task_id = task.get("id")
        if not task_id:
            continue

        # Fetch full details (includes labels)
        details = get_task_details(task_id)

        # Check for user-action label
        labels = details.get("labels", [])
        if isinstance(labels, list) and "user-action" in labels:
            user_actions.append(details)

    return user_actions


def format_current_task_section(tasks: List[Dict]) -> str:
    """
    Format 'Current Task' section from In Progress tasks.

    Args:
        tasks: List of task dicts

    Returns:
        Formatted markdown section
    """
    if not tasks:
        return "## Current Task\n\nNo tasks currently in progress.\n\n"

    # Sort by priority (high > medium > low)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    tasks_sorted = sorted(tasks, key=lambda t: priority_order.get(t.get("priority", "medium"), 1))

    sections = ["## Current Task\n\n"]

    for i, task in enumerate(tasks_sorted):
        task_id = task.get("id", "unknown")
        title = task.get("title", "Untitled")
        priority = task.get("priority", "medium").capitalize()
        labels = task.get("labels", [])
        description = task.get("description", "No description available")

        # Add separator if multiple tasks
        if i > 0:
            sections.append("---\n\n")

        sections.append(f"### {task_id}: {title}\n\n")
        sections.append(f"**Priority:** {priority}\n")
        if labels:
            sections.append(f"**Labels:** {', '.join(labels)}\n")
        sections.append(f"\n{description}\n\n")

        # Add acceptance criteria if available
        acceptance_criteria = task.get("acceptanceCriteria", [])
        if acceptance_criteria:
            sections.append("**Acceptance Criteria:**\n")
            for j, ac in enumerate(acceptance_criteria, 1):
                sections.append(f"- [ ] {j}. {ac}\n")
            sections.append("\n")

    return "".join(sections)


def format_backlog_section(tasks: List[Dict]) -> str:
    """
    Format 'Backlog' section from To Do tasks.

    Args:
        tasks: List of task dicts

    Returns:
        Formatted markdown section grouped by priority
    """
    if not tasks:
        return "## Backlog\n\nNo tasks in backlog.\n\n"

    # Group by priority
    high = [t for t in tasks if t.get("priority") == "high"]
    medium = [t for t in tasks if t.get("priority") == "medium"]
    low = [t for t in tasks if t.get("priority") == "low"]

    sections = ["## Backlog\n\n"]

    if high:
        sections.append("### High Priority\n\n")
        for task in high:
            task_id = task.get("id", "unknown")
            title = task.get("title", "Untitled")
            labels = task.get("labels", [])
            description = task.get("description", "No description")

            sections.append(f"**{task_id}:** {title}\n")
            if labels:
                sections.append(f"- Labels: {', '.join(labels)}\n")

            # Truncate description to first 150 chars
            desc_short = description[:150] + "..." if len(description) > 150 else description
            # Remove newlines for compact display
            desc_short = desc_short.replace("\n", " ")
            sections.append(f"- {desc_short}\n\n")

    if medium:
        sections.append("### Medium Priority\n\n")
        for task in medium:
            task_id = task.get("id", "unknown")
            title = task.get("title", "Untitled")
            labels = task.get("labels", [])

            sections.append(f"**{task_id}:** {title}\n")
            if labels:
                sections.append(f"- Labels: {', '.join(labels)}\n")
            sections.append("\n")

    if low:
        sections.append("### Low Priority\n\n")
        for task in low:
            task_id = task.get("id", "unknown")
            title = task.get("title", "Untitled")
            sections.append(f"**{task_id}:** {title}\n\n")

    return "".join(sections)


def _format_user_action_task(task: Dict) -> str:
    """
    Format a single user action task with inline acceptance criteria.

    Args:
        task: Task dict with metadata

    Returns:
        Formatted markdown for one user action task
    """
    task_id = task.get("id", "unknown")
    title = task.get("title", "Untitled")
    description = task.get("description", "")
    ac_criteria = task.get("acceptance_criteria", [])

    # Extract time estimate from description (if present)
    # Pattern: **Estimated Time:** 15-30 minutes or Estimated Time: 15 minutes
    time_estimate = None
    time_patterns = [
        r'\*\*Estimated Time:\*\*\s*([^\n]+)',
        r'Estimated Time:\s*([^\n]+)'
    ]
    for pattern in time_patterns:
        time_match = re.search(pattern, description, re.IGNORECASE)
        if time_match:
            time_estimate = time_match.group(1).strip()
            break

    # Build output
    output = []
    output.append(f"**[ACTION REQUIRED] {task_id}:** {title}\n")

    # Show time estimate if available
    if time_estimate:
        output.append(f"- **Estimated Time:** {time_estimate}\n")

    # Show first 200 chars of description
    desc_short = description[:200] + "..." if len(description) > 200 else description
    desc_short = desc_short.replace("\n", " ").strip()
    if desc_short and desc_short != f"View task details: `backlog task view {task_id}`":
        output.append(f"- {desc_short}\n")

    # Show acceptance criteria (max 3)
    if ac_criteria:
        output.append("- **Acceptance Criteria:**\n")
        for ac in ac_criteria[:3]:
            output.append(f"  - [ ] {ac}\n")
        if len(ac_criteria) > 3:
            output.append(f"  - ...and {len(ac_criteria) - 3} more\n")

    output.append(f"\n**View details:** `backlog task view {task_id}`\n\n")
    output.append("---\n\n")

    return "".join(output)


def format_user_actions_section(tasks: List[Dict]) -> str:
    """
    Format 'User Actions' section from user-action labeled tasks.

    Args:
        tasks: List of user action task dicts

    Returns:
        Formatted markdown section grouped by priority
    """
    if not tasks:
        return "## User Actions\n\nNo manual tasks requiring user execution.\n\n"

    # Group by priority
    high = [t for t in tasks if t.get("priority") == "high"]
    medium = [t for t in tasks if t.get("priority") == "medium"]
    low = [t for t in tasks if t.get("priority") == "low"]

    # Sort by created_date (oldest first)
    for group in [high, medium, low]:
        group.sort(key=lambda t: t.get("created_date", ""))

    sections = ["## User Actions\n\n"]
    sections.append("**Manual tasks requiring human execution:**\n\n")

    if high:
        sections.append("### High Priority\n\n")
        for task in high:
            sections.append(_format_user_action_task(task))

    if medium:
        sections.append("### Medium Priority\n\n")
        for task in medium:
            sections.append(_format_user_action_task(task))

    if low:
        sections.append("### Low Priority\n\n")
        for task in low:
            sections.append(_format_user_action_task(task))

    return "".join(sections)


def replace_section(content: str, begin_marker: str, end_marker: str, new_content: str) -> str:
    """
    Replace content between markers, preserving markers.

    Args:
        content: Full document content
        begin_marker: Starting marker (e.g., "<!-- BACKLOG_SYNC:CURRENT:BEGIN -->")
        end_marker: Ending marker
        new_content: New content to insert between markers

    Returns:
        Updated content with replaced section
    """
    pattern = f"{re.escape(begin_marker)}.*?{re.escape(end_marker)}"
    replacement = f"{begin_marker}\n{new_content}{end_marker}"

    # Check if markers exist
    if not re.search(pattern, content, flags=re.DOTALL):
        print(f"Warning: Markers not found in TASK.md ({begin_marker})")
        return content

    return re.sub(pattern, replacement, content, flags=re.DOTALL)


def sync_task_md(
    task_md_path: Path,
    section: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False
) -> bool:
    """
    Main sync function.

    Args:
        task_md_path: Path to TASK.md file
        section: 'current', 'backlog', or None (sync both)
        dry_run: Preview changes without writing
        force: Ignore warnings

    Returns:
        True if changes made, False otherwise
    """
    # Read current TASK.md
    if not task_md_path.exists():
        print(f"ERROR: TASK.md not found at {task_md_path}")
        return False

    content = task_md_path.read_text(encoding='utf-8')
    original_content = content

    # Get tasks from Backlog
    if section in (None, 'current'):
        print("Querying Backlog for 'In Progress' tasks...")
        current_tasks = get_backlog_tasks_cli(status="In Progress")
        print(f"Found {len(current_tasks)} In Progress task(s)")

        current_section = format_current_task_section(current_tasks)
        content = replace_section(content, CURRENT_BEGIN, CURRENT_END, current_section)

    # NEW: User Actions section
    if section in (None, 'user_actions'):
        print("Querying Backlog for 'User Action' tasks...")
        user_action_tasks = get_user_action_tasks()
        print(f"Found {len(user_action_tasks)} User Action task(s)")

        user_actions_section = format_user_actions_section(user_action_tasks)
        content = replace_section(content, USER_ACTIONS_BEGIN, USER_ACTIONS_END, user_actions_section)

    if section in (None, 'backlog'):
        print("Querying Backlog for 'To Do' tasks...")
        backlog_tasks = get_backlog_tasks_cli(status="To Do")
        print(f"Found {len(backlog_tasks)} To Do task(s)")

        backlog_section = format_backlog_section(backlog_tasks)
        content = replace_section(content, BACKLOG_BEGIN, BACKLOG_END, backlog_section)

    # Check if changes made
    if content == original_content:
        print("\nNo changes needed. TASK.md is already in sync.")
        return False

    # Show diff if dry-run
    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN - Changes that would be made")
        print("=" * 60 + "\n")

        # Simple diff: show lines that changed
        original_lines = original_content.split('\n')
        new_lines = content.split('\n')

        # Count differences
        added = 0
        removed = 0
        for i, (old, new) in enumerate(zip(original_lines, new_lines)):
            if old != new:
                if old.strip() and not new.strip():
                    removed += 1
                elif new.strip() and not old.strip():
                    added += 1

        print(f"Approximately {added} lines added, {removed} lines removed")
        print("\nTASK.md would be updated with new task statuses.")
        print("Run without --dry-run to apply changes.\n")
        return True

    # Write changes
    task_md_path.write_text(content, encoding='utf-8')

    print("\n" + "=" * 60)
    print("[OK] TASK.md updated successfully")
    print("=" * 60)
    print(f"Synced section(s): {section or 'current + backlog'}")
    print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    return True


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sync Backlog.md tasks to TASK.md (one-way sync: Backlog → TASK.md)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Full sync (current + backlog)
  %(prog)s --dry-run          # Preview changes
  %(prog)s --section current  # Sync only current task section
  %(prog)s --section backlog  # Sync only backlog section
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to TASK.md"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore warnings (reserved for future use)"
    )
    parser.add_argument(
        "--section",
        choices=['current', 'user_actions', 'backlog'],
        help="Sync only one section (current, user_actions, or backlog)"
    )

    args = parser.parse_args()

    # Find TASK.md
    repo_root = Path(__file__).parent.parent.parent
    task_md = repo_root / "TASK.md"

    if not task_md.exists():
        print(f"[ERROR] TASK.md not found at {task_md}")
        print("Please ensure you're running from the repository root.")
        sys.exit(1)

    print(f"Repository root: {repo_root}")
    print(f"TASK.md location: {task_md}\n")

    # Run sync
    success = sync_task_md(
        task_md,
        section=args.section,
        dry_run=args.dry_run,
        force=args.force
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
