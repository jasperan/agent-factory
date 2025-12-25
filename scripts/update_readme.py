#!/usr/bin/env python3
"""
Inject metrics into README.md.

This script reads metrics JSON from stdin and injects a new entry into the
"## 📝 Latest Updates" section of README.md in reverse chronological order.

Usage:
    poetry run python scripts/update_readme_metrics.py | poetry run python scripts/update_readme.py

    # Or with a file:
    poetry run python scripts/update_readme.py < metrics.json

    # Dry-run (show changes without modifying):
    poetry run python scripts/update_readme.py --dry-run < metrics.json

Behavior:
    - Finds or creates "## 📝 Latest Updates" section after line 12
    - Injects new entry at top of section (reverse chronological)
    - Keeps maximum 10 entries (prunes oldest)
    - Skips update if no changes detected
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


# Configuration
MAX_ENTRIES = 10
SECTION_HEADER = "## 📝 Latest Updates"
README_PATH = Path("README.md")
INSERTION_LINE = 12  # Insert section after line 12 (after vision statement)


def find_or_create_section(readme_lines: List[str]) -> int:
    """
    Find 'Latest Updates' section or create it after line 12.

    Args:
        readme_lines: List of README lines

    Returns:
        Line index where section starts
    """
    # Search for existing section
    for i, line in enumerate(readme_lines):
        if SECTION_HEADER in line:
            print(f"Found existing section at line {i+1}", file=sys.stderr)
            return i

    # Section doesn't exist - insert after line 12
    print(f"Section not found - inserting after line {INSERTION_LINE}", file=sys.stderr)

    # Insert section header with blank lines
    insert_lines = [
        "\n",
        "---\n",
        "\n",
        f"{SECTION_HEADER}\n",
        "\n"
    ]

    # Insert at INSERTION_LINE (0-indexed)
    for offset, line in enumerate(insert_lines):
        readme_lines.insert(INSERTION_LINE + offset, line)

    # Return index of section header
    return INSERTION_LINE + 3


def format_entry(metrics: Dict[str, Any]) -> str:
    """
    Format metrics as a markdown entry.

    Args:
        metrics: Metrics dictionary with timestamp, git_stats, db_stats, summaries

    Returns:
        Formatted markdown entry string
    """
    # Parse timestamp (ISO 8601 format)
    timestamp = metrics["timestamp"]
    # Convert "2025-12-25T22:15:30Z" to "2025-12-25 22:15"
    date_time = timestamp[:19].replace("T", " ")

    git = metrics["git_stats"]
    db = metrics["db_stats"]
    summaries = metrics["summaries"]

    # Build entry
    entry = f"**{date_time} UTC**\n"

    # Add summaries as bullets
    for summary in summaries:
        # Skip empty summaries
        if summary.strip():
            entry += f"- {summary}\n"

    # Add metrics line
    metrics_parts = []

    # Files changed
    if git.get("files_changed", 0) > 0:
        metrics_parts.append(f"Files: {git['files_changed']}")

    # Lines changed
    lines_added = git.get("lines_added", 0)
    lines_removed = git.get("lines_removed", 0)
    if lines_added > 0 or lines_removed > 0:
        metrics_parts.append(f"Lines: +{lines_added}/-{lines_removed}")

    # KB atoms
    atom_count = db.get("atom_count", 0)
    atom_delta = db.get("atom_count_delta", 0)
    if atom_count > 0:
        atom_str = f"KB Atoms: {atom_count:,}"
        if atom_delta > 0:
            atom_str += f" (+{atom_delta})"
        metrics_parts.append(atom_str)
    elif db.get("source") == "cache":
        # Database unavailable - show cached value with warning
        metrics_parts.append("KB Atoms: (unavailable)")

    # Combine metrics
    if metrics_parts:
        entry += f"- **Metrics:** {' | '.join(metrics_parts)}\n"

    entry += "\n"

    return entry


def parse_existing_entries(readme_lines: List[str], section_idx: int) -> List[Dict[str, Any]]:
    """
    Parse existing entries from README to extract timestamps.

    Args:
        readme_lines: List of README lines
        section_idx: Index of section header

    Returns:
        List of dictionaries with {timestamp, start_line, end_line}
    """
    entries = []
    current_entry = None

    # Pattern to match entry header: **2025-12-25 22:15 UTC**
    timestamp_pattern = re.compile(r'^\*\*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC\*\*$')

    # Start scanning after section header + blank line
    for i in range(section_idx + 2, len(readme_lines)):
        line = readme_lines[i].strip()

        # Check if this is an entry header
        match = timestamp_pattern.match(line)
        if match:
            # Save previous entry
            if current_entry:
                current_entry["end_line"] = i - 1
                entries.append(current_entry)

            # Start new entry
            current_entry = {
                "timestamp": match.group(1),
                "start_line": i,
                "end_line": None  # Will be set when next entry starts
            }

        # Stop if we hit another section header
        elif line.startswith("##"):
            if current_entry:
                current_entry["end_line"] = i - 1
                entries.append(current_entry)
            break

    # Save last entry
    if current_entry:
        current_entry["end_line"] = len(readme_lines) - 1
        entries.append(current_entry)

    return entries


def inject_entry(readme_path: Path, metrics: Dict[str, Any], dry_run: bool = False) -> bool:
    """
    Inject new entry into README.

    Args:
        readme_path: Path to README.md
        metrics: Metrics dictionary
        dry_run: If True, show changes without modifying file

    Returns:
        True if README was modified, False if no changes
    """
    # Read README
    if not readme_path.exists():
        print(f"ERROR: {readme_path} not found", file=sys.stderr)
        return False

    with open(readme_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find or create section
    section_idx = find_or_create_section(lines)

    # Format new entry
    new_entry = format_entry(metrics)

    # Find insertion point (after section header + blank line)
    insert_idx = section_idx + 2

    # Insert new entry
    entry_lines = new_entry.split("\n")
    # Add newline to each line (split removes them)
    entry_lines = [line + "\n" for line in entry_lines]

    # Insert in reverse order to maintain indices
    for line in reversed(entry_lines):
        lines.insert(insert_idx, line)

    # Parse existing entries and prune if > MAX_ENTRIES
    entries = parse_existing_entries(lines, section_idx)

    if len(entries) > MAX_ENTRIES:
        print(f"Pruning {len(entries) - MAX_ENTRIES} old entries (keeping {MAX_ENTRIES})", file=sys.stderr)

        # Remove oldest entries (beyond MAX_ENTRIES)
        for entry in entries[MAX_ENTRIES:]:
            # Mark lines for deletion
            start = entry["start_line"]
            end = entry["end_line"]

            # Delete from end to start to maintain indices
            for i in range(end, start - 1, -1):
                if i < len(lines):
                    del lines[i]

    # Check if content changed
    original_content = ""
    with open(readme_path, "r", encoding="utf-8") as f:
        original_content = f.read()

    new_content = "".join(lines)

    if original_content == new_content:
        print("No changes to README.md", file=sys.stderr)
        return False

    if dry_run:
        # Show summary of changes
        print("=" * 70, file=sys.stderr)
        print("DRY RUN - Changes that would be made:", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(f"\n{new_entry}", file=sys.stderr)
        print(f"Would be inserted at line {insert_idx + 1}", file=sys.stderr)

        existing_count = len(entries)
        if existing_count > MAX_ENTRIES:
            print(f"\nWould prune {existing_count - MAX_ENTRIES} old entries", file=sys.stderr)

        print("=" * 70, file=sys.stderr)
        return False

    # Write updated README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"✅ Updated {readme_path}", file=sys.stderr)
    return True


def main():
    """
    Main entry point for README injection.

    Reads metrics JSON from stdin and injects into README.md.
    """
    # Check for --dry-run flag
    dry_run = "--dry-run" in sys.argv

    # Read metrics JSON from stdin
    try:
        metrics = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON from stdin: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read stdin: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate required fields
    required_fields = ["timestamp", "git_stats", "db_stats", "summaries"]
    for field in required_fields:
        if field not in metrics:
            print(f"ERROR: Missing required field '{field}' in metrics JSON", file=sys.stderr)
            sys.exit(1)

    # Inject entry into README
    modified = inject_entry(README_PATH, metrics, dry_run=dry_run)

    # Exit with appropriate code
    if dry_run:
        sys.exit(0)
    elif modified:
        print("README.md updated successfully", file=sys.stderr)
        sys.exit(0)
    else:
        print("No changes needed", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
