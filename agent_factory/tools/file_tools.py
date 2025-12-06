"""
Deterministic file operation tools for agents.

Provides safe, validated file operations:
- ReadFileTool: Read file contents
- WriteFileTool: Write to files with backups
- ListDirectoryTool: List directory contents
- FileSearchTool: Search for content in files

All tools include:
- Path validation (prevent traversal)
- Size limits
- Error handling
- Idempotent behavior where possible
"""

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from langchain_core.tools import BaseTool

from .validators import (
    PathValidator,
    FileSizeValidator,
    PathTraversalError,
    FileSizeError,
    is_binary_file,
    detect_encoding,
    get_file_type
)


class ReadFileTool(BaseTool):
    """Read contents of a text file safely."""

    name: str = "read_file"
    description: str = """Read the contents of a text file.
    Input: file_path (string) - Path to the file to read
    Output: File contents as a string
    Use this when you need to read file contents."""

    def _run(self, file_path: str) -> str:
        """Read file contents."""
        try:
            # Validate path
            path_validator = PathValidator(allowed_dirs=[Path.cwd()])
            safe_path = path_validator.validate(file_path)

            # Check if file exists
            if not safe_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if not safe_path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")

            # Check size
            size_validator = FileSizeValidator(max_size_mb=10.0)
            size_validator.validate(safe_path)

            # Check if binary
            if is_binary_file(safe_path):
                raise ValueError(f"File '{file_path}' appears to be binary.")

            # Detect encoding and read
            encoding = detect_encoding(safe_path)

            with open(safe_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()

            return content

        except (PathTraversalError, FileSizeError, FileNotFoundError, ValueError) as e:
            return f"Error reading file: {str(e)}"
        except Exception as e:
            return f"Unexpected error reading file: {str(e)}"


class WriteFileTool(BaseTool):
    """Write content to a file safely."""

    name: str = "write_file"
    description: str = """Write content to a file.
    Input: file_path (string), content (string)
    Output: Success message
    Use this when you need to create or update files."""

    def _run(self, file_path: str, content: str) -> str:
        """Write content to file."""
        try:
            # Validate path
            path_validator = PathValidator(allowed_dirs=[Path.cwd()])
            safe_path = path_validator.validate(file_path)

            # Validate content size
            size_validator = FileSizeValidator(max_size_mb=10.0)
            content_size = len(content.encode('utf-8'))
            if content_size > size_validator.max_size_bytes:
                raise FileSizeError(f"Content size {content_size / 1024 / 1024:.2f}MB exceeds limit 10MB")

            # Idempotent check
            if safe_path.exists():
                try:
                    with open(safe_path, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                    if current_content == content:
                        return f"File '{file_path}' already has the correct content (unchanged)"
                except Exception:
                    pass

            # Create parent directories
            safe_path.parent.mkdir(parents=True, exist_ok=True)

            # Backup existing file
            if safe_path.exists():
                backup_path = safe_path.with_suffix(safe_path.suffix + '.bak')
                shutil.copy2(safe_path, backup_path)

            # Atomic write
            temp_fd, temp_path = tempfile.mkstemp(
                dir=safe_path.parent,
                prefix=f".{safe_path.name}.",
                suffix=".tmp"
            )

            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    f.write(content)
                shutil.move(temp_path, safe_path)
                return f"Successfully wrote {content_size} bytes to '{file_path}'"
            except Exception as e:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
                raise e

        except (PathTraversalError, FileSizeError) as e:
            return f"Error writing file: {str(e)}"
        except Exception as e:
            return f"Unexpected error writing file: {str(e)}"


class ListDirectoryTool(BaseTool):
    """List contents of a directory."""

    name: str = "list_directory"
    description: str = """List files and directories.
    Input: directory (string), pattern (string, optional), recursive (bool, optional)
    Output: Formatted list of files with metadata
    Use this to explore directory contents."""

    def _run(self, directory: str = ".", pattern: str = "*", recursive: bool = False) -> str:
        """List directory contents."""
        try:
            # Validate path
            path_validator = PathValidator(allowed_dirs=[Path.cwd()])
            safe_dir = path_validator.validate(directory)

            if not safe_dir.exists():
                return f"Error: Directory not found: {directory}"

            if not safe_dir.is_dir():
                return f"Error: Path is not a directory: {directory}"

            # Get files
            if recursive:
                files = sorted(safe_dir.rglob(pattern))
            else:
                files = sorted(safe_dir.glob(pattern))

            if not files:
                return f"No files found matching pattern '{pattern}' in {directory}"

            # Format output
            lines = [f"Directory: {directory}", f"Pattern: {pattern}", ""]

            for file in files:
                try:
                    rel_path = file.relative_to(safe_dir)
                except ValueError:
                    rel_path = file

                if file.is_file():
                    size = file.stat().st_size
                    modified = datetime.fromtimestamp(file.stat().st_mtime)
                    lines.append(
                        f"  {rel_path} ({size:,} bytes, modified: {modified.strftime('%Y-%m-%d %H:%M')})"
                    )
                elif file.is_dir():
                    lines.append(f"  {rel_path}/ (directory)")

            lines.append(f"\nTotal: {len(files)} items")
            return "\n".join(lines)

        except PathTraversalError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error listing directory: {str(e)}"


class FileSearchTool(BaseTool):
    """Search for content in files."""

    name: str = "search_files"
    description: str = """Search for text patterns in files.
    Input: pattern (string), directory (string, optional), file_pattern (string, optional), case_sensitive (bool, optional)
    Output: Search results with file names and line numbers
    Use this to find specific content in files."""

    def _run(self, pattern: str, directory: str = ".", file_pattern: str = "*", case_sensitive: bool = False) -> str:
        """Search for pattern in files."""
        try:
            # Validate directory
            path_validator = PathValidator(allowed_dirs=[Path.cwd()])
            safe_dir = path_validator.validate(directory)

            if not safe_dir.exists():
                return f"Error: Directory not found: {directory}"

            if not safe_dir.is_dir():
                return f"Error: Path is not a directory: {directory}"

            # Compile regex
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return f"Error: Invalid regex pattern: {e}"

            # Search files
            results = []
            files_searched = 0
            max_results = 100

            for file in safe_dir.rglob(file_pattern):
                if not file.is_file():
                    continue

                if is_binary_file(file):
                    continue

                files_searched += 1

                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, start=1):
                        if regex.search(line):
                            rel_path = file.relative_to(safe_dir)
                            results.append((rel_path, line_num, line.rstrip()))

                            if len(results) >= max_results:
                                break
                except Exception:
                    continue

                if len(results) >= max_results:
                    break

            # Format output
            if not results:
                return f"No matches found for pattern '{pattern}' in {files_searched} files"

            lines = [f"Search results for: {pattern}", f"Directory: {directory}", f"Files searched: {files_searched}", ""]

            for file_path, line_num, line_content in results:
                lines.append(f"{file_path}:{line_num}: {line_content}")

            if len(results) >= max_results:
                lines.append(f"\n(Showing first {max_results} results)")

            return "\n".join(lines)

        except PathTraversalError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error searching files: {str(e)}"
