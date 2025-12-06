"""
Tests for agent_factory.tools file tools and validators.

Tests:
- Path validation and security
- File reading with safety checks
- File writing with backups
- Directory listing
- File searching
- Size validation
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from agent_factory.tools import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    FileSearchTool,
    PathValidator,
    FileSizeValidator,
    PathTraversalError,
    FileSizeError,
    is_binary_file
)


class TestPathValidator:
    """Test path validation and security."""

    def test_validate_safe_path(self, tmp_path, monkeypatch):
        """REQ-DET-006: Validate safe relative path."""
        monkeypatch.chdir(tmp_path)
        validator = PathValidator(allowed_dirs=[tmp_path])

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Should validate successfully
        safe_path = validator.validate("test.txt")
        assert safe_path.name == "test.txt"

    def test_reject_path_traversal(self, tmp_path):
        """REQ-DET-006: Reject path traversal attempts."""
        validator = PathValidator(allowed_dirs=[tmp_path])

        # Try to traverse up
        with pytest.raises(PathTraversalError):
            validator.validate("../etc/passwd")

    def test_reject_absolute_path_by_default(self, tmp_path):
        """REQ-DET-006: Reject absolute paths by default."""
        validator = PathValidator(allowed_dirs=[tmp_path])

        with pytest.raises(PathTraversalError):
            validator.validate("/etc/passwd")

    def test_allow_absolute_path_when_enabled(self, tmp_path):
        """REQ-DET-006: Allow absolute paths when configured."""
        validator = PathValidator(allowed_dirs=[tmp_path], allow_absolute=True)

        # Should validate if within allowed dirs
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        safe_path = validator.validate(str(test_file))
        assert safe_path == test_file

    def test_reject_path_outside_allowed_dirs(self, tmp_path):
        """REQ-DET-006: Reject paths outside allowed directories."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()

        validator = PathValidator(allowed_dirs=[allowed])

        # Try to access parent
        with pytest.raises(PathTraversalError):
            validator.validate("..")


class TestFileSizeValidator:
    """Test file size validation."""

    def test_validate_small_file(self, tmp_path):
        """REQ-DET-001: Validate small file passes."""
        validator = FileSizeValidator(max_size_mb=1.0)

        test_file = tmp_path / "small.txt"
        test_file.write_text("Small content")

        size = validator.validate(test_file)
        assert size > 0
        assert size < 1024 * 1024  # < 1MB

    def test_reject_large_file(self, tmp_path):
        """REQ-DET-001: Reject file exceeding size limit."""
        validator = FileSizeValidator(max_size_mb=0.001)  # 1KB limit

        test_file = tmp_path / "large.txt"
        test_file.write_text("x" * 2000)  # 2KB file

        with pytest.raises(FileSizeError):
            validator.validate(test_file)

    def test_file_not_found(self, tmp_path):
        """REQ-DET-001: Handle missing file."""
        validator = FileSizeValidator(max_size_mb=1.0)

        nonexistent = tmp_path / "missing.txt"

        with pytest.raises(FileNotFoundError):
            validator.validate(nonexistent)


class TestReadFileTool:
    """Test file reading functionality."""

    def test_read_existing_file(self, tmp_path, monkeypatch):
        """REQ-DET-001: Read existing text file."""
        monkeypatch.chdir(tmp_path)
        tool = ReadFileTool()

        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        result = tool._run("test.txt")
        assert result == test_content

    def test_read_nonexistent_file(self, tmp_path, monkeypatch):
        """REQ-DET-001: Handle missing file gracefully."""
        monkeypatch.chdir(tmp_path)
        tool = ReadFileTool()

        result = tool._run("missing.txt")
        assert "not found" in result.lower()

    def test_read_large_file_rejected(self, tmp_path, monkeypatch):
        """REQ-DET-001: Reject files exceeding size limit."""
        monkeypatch.chdir(tmp_path)
        tool = ReadFileTool()

        test_file = tmp_path / "large.txt"
        test_file.write_text("x" * 15 * 1024 * 1024)  # 15MB

        result = tool._run("large.txt")
        assert "size" in result.lower() and "exceeds" in result.lower()

    def test_path_traversal_rejected(self, tmp_path, monkeypatch):
        """REQ-DET-006: Reject path traversal in read."""
        monkeypatch.chdir(tmp_path)
        tool = ReadFileTool()

        result = tool._run("../../../etc/passwd")
        assert "error" in result.lower()

    def test_binary_file_detection(self, tmp_path, monkeypatch):
        """REQ-DET-001: Detect and reject binary files."""
        monkeypatch.chdir(tmp_path)
        tool = ReadFileTool()

        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\x04")

        result = tool._run("test.bin")
        assert "binary" in result.lower()


class TestWriteFileTool:
    """Test file writing functionality."""

    def test_write_new_file(self, tmp_path, monkeypatch):
        """REQ-DET-002: Write new file."""
        monkeypatch.chdir(tmp_path)
        tool = WriteFileTool()

        content = "New file content"
        result = tool._run("new.txt", content)

        assert "success" in result.lower()
        assert (tmp_path / "new.txt").read_text() == content

    def test_overwrite_with_backup(self, tmp_path, monkeypatch):
        """REQ-DET-002: Overwrite with backup creation."""
        monkeypatch.chdir(tmp_path)
        tool = WriteFileTool()

        test_file = tmp_path / "test.txt"
        original_content = "Original"
        test_file.write_text(original_content)

        new_content = "Updated"
        tool._run("test.txt", new_content)

        # Check new content
        assert test_file.read_text() == new_content

        # Check backup exists
        backup = tmp_path / "test.txt.bak"
        assert backup.exists()
        assert backup.read_text() == original_content

    def test_idempotent_write(self, tmp_path, monkeypatch):
        """REQ-DET-007: Idempotent writes (no change if same content)."""
        monkeypatch.chdir(tmp_path)
        tool = WriteFileTool()

        content = "Same content"
        test_file = tmp_path / "test.txt"
        test_file.write_text(content)

        result = tool._run("test.txt", content)
        assert "unchanged" in result.lower()

    def test_create_parent_dirs(self, tmp_path, monkeypatch):
        """REQ-DET-002: Create parent directories if needed."""
        monkeypatch.chdir(tmp_path)
        tool = WriteFileTool()

        nested_path = "subdir/nested/file.txt"
        content = "Nested file"

        result = tool._run(nested_path, content)

        assert "success" in result.lower()
        assert (tmp_path / nested_path).read_text() == content

    def test_path_traversal_rejected_write(self, tmp_path, monkeypatch):
        """REQ-DET-006: Reject path traversal in write."""
        monkeypatch.chdir(tmp_path)
        tool = WriteFileTool()

        result = tool._run("../../../tmp/evil.txt", "content")
        assert "error" in result.lower()

    def test_size_limit_on_write(self, tmp_path, monkeypatch):
        """REQ-DET-002: Enforce size limit on write."""
        monkeypatch.chdir(tmp_path)
        tool = WriteFileTool()

        large_content = "x" * 15 * 1024 * 1024  # 15MB
        result = tool._run("large.txt", large_content)

        assert "size" in result.lower() and "exceeds" in result.lower()


class TestListDirectoryTool:
    """Test directory listing functionality."""

    def test_list_files(self, tmp_path, monkeypatch):
        """REQ-DET-003: List files in directory."""
        monkeypatch.chdir(tmp_path)
        tool = ListDirectoryTool()

        # Create test files
        (tmp_path / "file1.txt").write_text("test")
        (tmp_path / "file2.txt").write_text("test")

        result = tool._run(".")

        assert "file1.txt" in result
        assert "file2.txt" in result

    def test_list_with_pattern(self, tmp_path, monkeypatch):
        """REQ-DET-003: List files matching pattern."""
        monkeypatch.chdir(tmp_path)
        tool = ListDirectoryTool()

        (tmp_path / "test.py").write_text("print('hello')")
        (tmp_path / "test.txt").write_text("text")

        result = tool._run(".", pattern="*.py")

        assert "test.py" in result
        assert "test.txt" not in result

    def test_recursive_listing(self, tmp_path, monkeypatch):
        """REQ-DET-003: List files recursively."""
        monkeypatch.chdir(tmp_path)
        tool = ListDirectoryTool()

        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")

        result = tool._run(".", pattern="*.txt", recursive=True)

        assert "nested.txt" in result

    def test_list_nonexistent_directory(self, tmp_path, monkeypatch):
        """REQ-DET-003: Handle missing directory."""
        monkeypatch.chdir(tmp_path)
        tool = ListDirectoryTool()

        result = tool._run("nonexistent")
        assert "not found" in result.lower()


class TestFileSearchTool:
    """Test file search functionality."""

    def test_search_content(self, tmp_path, monkeypatch):
        """REQ-DET-004: Search for content in files."""
        monkeypatch.chdir(tmp_path)
        tool = FileSearchTool()

        (tmp_path / "file1.txt").write_text("Contains TODO item")
        (tmp_path / "file2.txt").write_text("Regular content")

        result = tool._run("TODO", directory=".")

        assert "file1.txt" in result
        assert "TODO" in result
        assert "file2.txt" not in result

    def test_search_with_regex(self, tmp_path, monkeypatch):
        """REQ-DET-004: Search using regex pattern."""
        monkeypatch.chdir(tmp_path)
        tool = FileSearchTool()

        (tmp_path / "test.py").write_text("def function_name():\n    pass")

        result = tool._run(r"def \w+\(", directory=".")

        assert "test.py" in result
        assert "def function_name" in result

    def test_case_insensitive(self, tmp_path, monkeypatch):
        """REQ-DET-004: Case-insensitive search."""
        monkeypatch.chdir(tmp_path)
        tool = FileSearchTool()

        (tmp_path / "test.txt").write_text("Hello World")

        result = tool._run("hello", directory=".", case_sensitive=False)

        assert "test.txt" in result

    def test_no_results(self, tmp_path, monkeypatch):
        """REQ-DET-004: Handle no search results."""
        monkeypatch.chdir(tmp_path)
        tool = FileSearchTool()

        (tmp_path / "test.txt").write_text("No match here")

        result = tool._run("MISSING", directory=".")

        assert "no matches" in result.lower()
