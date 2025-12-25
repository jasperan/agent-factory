#!/usr/bin/env python3
"""
Extract project metrics for README updates.

This script collects git statistics, database metrics, and generates plain English
summaries from commit messages. It's designed to be fast (<5 seconds) and gracefully
degrade if the database is unavailable.

Usage:
    poetry run python scripts/update_readme_metrics.py

Output:
    JSON to stdout with timestamp, git_stats, db_stats, and summaries

Example Output:
    {
      "timestamp": "2025-12-25T22:15:30Z",
      "git_stats": {
        "files_changed": 8,
        "lines_added": 245,
        "lines_removed": 67,
        "commit_message": "feat: Enable KB ingestion via Telegram"
      },
      "db_stats": {
        "atom_count": 2018,
        "atom_count_delta": 54
      },
      "summaries": [
        "Added KB ingestion via Telegram (/kb_ingest, /kb_queue commands)",
        "Lowered KB coverage thresholds for small KB",
        "Fixed Route A/B routing - PLC queries now return citations"
      ]
    }
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.core.database_manager import DatabaseManager


# Cache file for last known atom count
CACHE_DIR = Path("data/cache")
CACHE_FILE = CACHE_DIR / "last_atom_count.txt"


def get_git_stats() -> Dict[str, Any]:
    """
    Extract git statistics from the last commit.

    Returns:
        Dictionary with files_changed, lines_added, lines_removed, commit_message
    """
    try:
        # Get commit message
        commit_msg_result = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            capture_output=True,
            text=True,
            timeout=5
        )
        commit_message = commit_msg_result.stdout.strip() if commit_msg_result.returncode == 0 else "Unknown commit"

        # Get commit body (for multi-line messages)
        commit_body_result = subprocess.run(
            ["git", "log", "-1", "--format=%b"],
            capture_output=True,
            text=True,
            timeout=5
        )
        commit_body = commit_body_result.stdout.strip() if commit_body_result.returncode == 0 else ""

        # Combine subject and body
        full_message = commit_message
        if commit_body and commit_body != commit_message:
            full_message = f"{commit_message}\n{commit_body}"

        # Get files changed
        files_result = subprocess.run(
            ["git", "diff", "HEAD^..HEAD", "--stat", "--format="],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Parse file count from last line (e.g., "8 files changed, 245 insertions(+), 67 deletions(-)")
        files_changed = 0
        lines = files_result.stdout.strip().split("\n")
        if lines and lines[-1]:
            summary_line = lines[-1]
            if "file" in summary_line:
                parts = summary_line.split()
                files_changed = int(parts[0])

        # Get lines added/removed with numstat
        numstat_result = subprocess.run(
            ["git", "diff", "HEAD^..HEAD", "--numstat"],
            capture_output=True,
            text=True,
            timeout=5
        )

        lines_added = 0
        lines_removed = 0
        if numstat_result.returncode == 0:
            for line in numstat_result.stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            added = int(parts[0]) if parts[0] != "-" else 0
                            removed = int(parts[1]) if parts[1] != "-" else 0
                            lines_added += added
                            lines_removed += removed
                        except ValueError:
                            continue

        return {
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "commit_message": full_message
        }

    except subprocess.TimeoutExpired:
        print("WARNING: Git stats extraction timed out", file=sys.stderr)
        return {
            "files_changed": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "commit_message": "Timeout extracting commit message"
        }
    except Exception as e:
        print(f"WARNING: Failed to extract git stats: {e}", file=sys.stderr)
        return {
            "files_changed": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "commit_message": f"Error: {str(e)}"
        }


def load_cached_atom_count() -> int:
    """
    Load last known atom count from cache file.

    Returns:
        Last cached atom count, or 0 if no cache exists
    """
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                return int(f.read().strip())
    except Exception as e:
        print(f"WARNING: Could not load cached atom count: {e}", file=sys.stderr)

    return 0


def save_cached_atom_count(count: int) -> None:
    """
    Save atom count to cache file.

    Args:
        count: Atom count to cache
    """
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            f.write(str(count))
    except Exception as e:
        print(f"WARNING: Could not save cached atom count: {e}", file=sys.stderr)


def get_db_stats() -> Dict[str, Any]:
    """
    Query database for atom count with automatic failover.

    Uses DatabaseManager's multi-provider failover (Neon → Supabase → Railway).
    Falls back to cached value if all providers fail.

    Returns:
        Dictionary with atom_count and atom_count_delta (change from last run)
    """
    try:
        # Initialize database manager (handles failover automatically)
        db = DatabaseManager()

        # Query current atom count
        query = "SELECT COUNT(*) FROM knowledge_atoms"
        result = db.execute_query(query)
        current_count = result[0][0] if result else 0

        # Load cached count for delta calculation
        cached_count = load_cached_atom_count()
        delta = current_count - cached_count if cached_count > 0 else 0

        # Save current count to cache
        save_cached_atom_count(current_count)

        return {
            "atom_count": current_count,
            "atom_count_delta": delta,
            "source": "database"
        }

    except Exception as e:
        print(f"WARNING: Database query failed, using cached value: {e}", file=sys.stderr)

        # Graceful degradation: use cached value
        cached_count = load_cached_atom_count()

        return {
            "atom_count": cached_count,
            "atom_count_delta": 0,
            "source": "cache",
            "error": str(e)
        }


def parse_conventional_commit(commit_message: str) -> Optional[Dict[str, str]]:
    """
    Parse conventional commit format: type(scope): subject

    Args:
        commit_message: First line of commit message

    Returns:
        Dictionary with type, scope, subject, or None if not conventional format
    """
    # Extract first line
    first_line = commit_message.split("\n")[0].strip()

    # Check for conventional commit format
    if ":" not in first_line:
        return None

    # Split into type(scope) and subject
    parts = first_line.split(":", 1)
    if len(parts) != 2:
        return None

    type_scope = parts[0].strip()
    subject = parts[1].strip()

    # Extract type and scope
    commit_type = type_scope
    scope = None

    if "(" in type_scope and ")" in type_scope:
        type_part, scope_part = type_scope.split("(", 1)
        commit_type = type_part.strip()
        scope = scope_part.rstrip(")").strip()

    return {
        "type": commit_type,
        "scope": scope,
        "subject": subject
    }


def generate_summaries(commit_message: str) -> List[str]:
    """
    Convert commit message to plain English summaries.

    Uses template-based conversion for speed (<100ms vs LLM which takes seconds).

    Conventional commit format: type(scope): subject
    - feat(kb): Add cache → "Added LLM response cache"
    - fix(telegram): Wire button → "Fixed Telegram button integration"
    - docs(readme): Update guide → "Updated documentation"

    Args:
        commit_message: Commit message to convert

    Returns:
        List of plain English summary strings
    """
    summaries = []

    # Try parsing as conventional commit
    parsed = parse_conventional_commit(commit_message)

    if parsed:
        commit_type = parsed["type"].lower()
        scope = parsed["scope"]
        subject = parsed["subject"]

        # Template-based conversion
        if commit_type == "feat":
            prefix = "Added"
        elif commit_type == "fix":
            prefix = "Fixed"
        elif commit_type == "docs":
            prefix = "Updated documentation for"
        elif commit_type == "chore":
            prefix = "Maintained"
        elif commit_type == "perf":
            prefix = "Optimized"
        elif commit_type == "test":
            prefix = "Added tests for"
        elif commit_type == "refactor":
            prefix = "Refactored"
        elif commit_type == "style":
            prefix = "Improved code style for"
        elif commit_type == "build":
            prefix = "Updated build for"
        elif commit_type == "ci":
            prefix = "Updated CI for"
        else:
            prefix = "Updated"

        # Build summary
        if scope:
            summary = f"{prefix} {subject} ({scope})"
        else:
            summary = f"{prefix} {subject}"

        summaries.append(summary)

    else:
        # Non-conventional format: use commit subject as-is
        first_line = commit_message.split("\n")[0].strip()
        summaries.append(first_line)

    # Parse multi-line body for additional details (if present)
    lines = commit_message.split("\n")
    if len(lines) > 1:
        for line in lines[1:]:
            line = line.strip()
            # Add bullet points as summaries
            if line.startswith("-") or line.startswith("*"):
                summaries.append(line.lstrip("-*").strip())

    return summaries


def main():
    """
    Main entry point for metrics extraction.

    Collects all metrics and outputs JSON to stdout.
    """
    # Get current timestamp
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Collect git statistics
    git_stats = get_git_stats()

    # Collect database statistics
    db_stats = get_db_stats()

    # Generate plain English summaries
    summaries = generate_summaries(git_stats["commit_message"])

    # Build output JSON
    metrics = {
        "timestamp": timestamp,
        "git_stats": git_stats,
        "db_stats": db_stats,
        "summaries": summaries
    }

    # Output JSON to stdout (consumed by update_readme.py)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
