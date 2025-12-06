"""
File Tools Demo - Deterministic file operations with safety

Demonstrates Phase 4 features:
1. Safe file reading with validation
2. Safe file writing with backups
3. Directory listing
4. File searching
5. Result caching for performance
"""

import os
import sys
from pathlib import Path

# Add parent to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.tools import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    FileSearchTool,
    CacheManager
)


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print("=" * 60)


def main():
    print_section("FILE TOOLS DEMO - Phase 4: Deterministic Tools")

    # Create tools
    read_tool = ReadFileTool()
    write_tool = WriteFileTool()
    list_tool = ListDirectoryTool()
    search_tool = FileSearchTool()

    # Demo 1: Write File
    print_section("1. WRITE FILE (with backup & idempotent)")

    content = "# Agent Factory\n\nDeterministic tools demo file.\n"
    result = write_tool._run("demo_output.txt", content)
    print(result)

    # Try writing again (idempotent - no change)
    result = write_tool._run("demo_output.txt", content)
    print(f"Second write: {result}")

    # Demo 2: Read File
    print_section("2. READ FILE (with validation)")

    result = read_tool._run("demo_output.txt")
    print(f"File contents:\n{result}")

    # Demo 3: List Directory
    print_section("3. LIST DIRECTORY")

    result = list_tool._run(".", pattern="*.py", recursive=False)
    print(result)

    # Demo 4: Search Files
    print_section("4. SEARCH FILES")

    result = search_tool._run("AgentFactory", directory=".", file_pattern="*.py")
    print(result)

    # Demo 5: Caching
    print_section("5. RESULT CACHING")

    cache = CacheManager(default_ttl=60)
    print(f"Cache created with 60s TTL")

    # Simulate expensive operation
    cache.set("search_results", "Cached search results", ttl=30)
    print(f"Cached: search_results")

    # Retrieve from cache
    cached = cache.get("search_results")
    print(f"Retrieved: {cached}")

    # Cache stats
    stats = cache.stats()
    print(f"\nCache Stats:")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Size: {stats['size']}")
    print(f"  Hit Rate: {stats['hit_rate']}")

    # Demo 6: Safety Features
    print_section("6. SAFETY FEATURES")

    print("Path Validation:")
    result = read_tool._run("../../../etc/passwd")
    print(f"  Traversal attempt: {result[:50]}...")

    print("\nSize Limits:")
    large_content = "x" * 15 * 1024 * 1024  # 15MB
    result = write_tool._run("large.txt", large_content)
    print(f"  Large file: {result[:50]}...")

    print("\nBinary Detection:")
    Path("test.bin").write_bytes(b"\x00\x01\x02")
    result = read_tool._run("test.bin")
    print(f"  Binary file: {result[:50]}...")
    Path("test.bin").unlink()  # Cleanup

    # Cleanup
    print_section("CLEANUP")
    if Path("demo_output.txt").exists():
        Path("demo_output.txt").unlink()
        print("Removed demo_output.txt")
    if Path("demo_output.txt.bak").exists():
        Path("demo_output.txt.bak").unlink()
        print("Removed demo_output.txt.bak")

    print_section("DEMO COMPLETE")
    print("\nPhase 4 Features:")
    print("  [X] Safe file reading with path validation")
    print("  [X] Safe file writing with atomic operations & backups")
    print("  [X] Directory listing with patterns")
    print("  [X] File searching with regex")
    print("  [X] Result caching with TTL")
    print("  [X] Path traversal prevention")
    print("  [X] Size limit enforcement")
    print("  [X] Binary file detection")
    print("  [X] Idempotent operations")


if __name__ == "__main__":
    main()
