"""
Coding Tools: File system operations and code analysis tools

This module provides tools for coding agents to read/write files,
perform Git operations, and analyze code.
"""

import os
from pathlib import Path
from typing import ClassVar, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


# =============================================================================
# File Reading Tool
# =============================================================================

class ReadFileInput(BaseModel):
    """Input schema for reading files."""
    file_path: str = Field(description="Path to the file to read")


class ReadFileTool(BaseTool):
    """Tool for reading file contents."""

    name: ClassVar[str] = "read_file"
    description: ClassVar[str] = (
        "Useful for reading the contents of a file. "
        "Input should be a file path (relative or absolute). "
        "Returns the contents of the file."
    )
    args_schema: Type[BaseModel] = ReadFileInput
    base_dir: str = "."

    def _run(self, file_path: str) -> str:
        """Read and return file contents."""
        try:
            # Resolve path relative to base_dir
            full_path = Path(self.base_dir) / file_path
            full_path = full_path.resolve()

            if not full_path.exists():
                return f"Error: File not found: {file_path}"

            if not full_path.is_file():
                return f"Error: Path is not a file: {file_path}"

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return f"Contents of {file_path}:\n\n{content}"

        except UnicodeDecodeError:
            return f"Error: File appears to be binary and cannot be read as text: {file_path}"
        except PermissionError:
            return f"Error: Permission denied reading file: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


# =============================================================================
# File Writing Tool
# =============================================================================

class WriteFileInput(BaseModel):
    """Input schema for writing files."""
    file_path: str = Field(description="Path to the file to write")
    content: str = Field(description="Content to write to the file")
    mode: str = Field(
        default="w",
        description="Write mode: 'w' to overwrite, 'a' to append"
    )


class WriteFileTool(BaseTool):
    """Tool for writing content to files."""

    name: ClassVar[str] = "write_file"
    description: ClassVar[str] = (
        "Useful for writing or appending content to a file. "
        "Input should include file_path and content. "
        "Use mode='w' to overwrite or mode='a' to append."
    )
    args_schema: Type[BaseModel] = WriteFileInput
    base_dir: str = "."

    def _run(self, file_path: str, content: str, mode: str = "w") -> str:
        """Write content to file."""
        try:
            # Resolve path relative to base_dir
            full_path = Path(self.base_dir) / file_path
            full_path = full_path.resolve()

            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Validate mode
            if mode not in ["w", "a"]:
                return f"Error: Invalid mode '{mode}'. Use 'w' or 'a'."

            with open(full_path, mode, encoding='utf-8') as f:
                f.write(content)

            action = "Created/Overwritten" if mode == "w" else "Appended to"
            return f"{action} file: {file_path} ({len(content)} characters)"

        except PermissionError:
            return f"Error: Permission denied writing to file: {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


# =============================================================================
# List Directory Tool
# =============================================================================

class ListDirectoryInput(BaseModel):
    """Input schema for listing directory contents."""
    directory_path: str = Field(
        default=".",
        description="Path to the directory to list (default: current directory)"
    )


class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents."""

    name: ClassVar[str] = "list_directory"
    description: ClassVar[str] = (
        "Useful for listing files and subdirectories in a directory. "
        "Input should be a directory path. Returns a list of files and folders."
    )
    args_schema: Type[BaseModel] = ListDirectoryInput
    base_dir: str = "."

    def _run(self, directory_path: str = ".") -> str:
        """List directory contents."""
        try:
            # Resolve path relative to base_dir
            full_path = Path(self.base_dir) / directory_path
            full_path = full_path.resolve()

            if not full_path.exists():
                return f"Error: Directory not found: {directory_path}"

            if not full_path.is_dir():
                return f"Error: Path is not a directory: {directory_path}"

            items = []
            for item in sorted(full_path.iterdir()):
                item_type = "DIR" if item.is_dir() else "FILE"
                relative_path = item.relative_to(full_path)
                items.append(f"[{item_type}] {relative_path}")

            if not items:
                return f"Directory is empty: {directory_path}"

            return f"Contents of {directory_path}:\n\n" + "\n".join(items)

        except PermissionError:
            return f"Error: Permission denied accessing directory: {directory_path}"
        except Exception as e:
            return f"Error listing directory: {str(e)}"


# =============================================================================
# Git Status Tool
# =============================================================================

class GitStatusInput(BaseModel):
    """Input schema for Git status."""
    repository_path: str = Field(
        default=".",
        description="Path to the Git repository (default: current directory)"
    )


class GitStatusTool(BaseTool):
    """Tool for checking Git repository status."""

    name: ClassVar[str] = "git_status"
    description: ClassVar[str] = (
        "Useful for checking the status of a Git repository. "
        "Shows modified files, untracked files, and current branch. "
        "Input should be the repository path (optional)."
    )
    args_schema: Type[BaseModel] = GitStatusInput

    def _run(self, repository_path: str = ".") -> str:
        """Get Git repository status."""
        try:
            import git

            repo = git.Repo(repository_path, search_parent_directories=True)

            # Get current branch
            try:
                branch = repo.active_branch.name
            except TypeError:
                branch = "DETACHED HEAD"

            # Get status
            changed_files = [item.a_path for item in repo.index.diff(None)]
            staged_files = [item.a_path for item in repo.index.diff("HEAD")]
            untracked_files = repo.untracked_files

            status_parts = [f"Branch: {branch}\n"]

            if staged_files:
                status_parts.append("Staged files:")
                status_parts.extend([f"  - {f}" for f in staged_files])
                status_parts.append("")

            if changed_files:
                status_parts.append("Modified files (not staged):")
                status_parts.extend([f"  - {f}" for f in changed_files])
                status_parts.append("")

            if untracked_files:
                status_parts.append("Untracked files:")
                status_parts.extend([f"  - {f}" for f in untracked_files])
                status_parts.append("")

            if not (staged_files or changed_files or untracked_files):
                status_parts.append("Working tree is clean")

            return "\n".join(status_parts)

        except ImportError:
            return "GitPython not installed. Install with: pip install gitpython"
        except git.InvalidGitRepositoryError:
            return f"Error: Not a Git repository: {repository_path}"
        except Exception as e:
            return f"Error getting Git status: {str(e)}"


# =============================================================================
# File Search Tool
# =============================================================================

class FileSearchInput(BaseModel):
    """Input schema for file search."""
    pattern: str = Field(description="File name pattern to search for (supports wildcards)")
    directory: str = Field(
        default=".",
        description="Directory to search in (default: current directory)"
    )


class FileSearchTool(BaseTool):
    """Tool for searching files by name pattern."""

    name: ClassVar[str] = "search_files"
    description: ClassVar[str] = (
        "Useful for finding files by name pattern. "
        "Supports wildcards like *.py or test_*. "
        "Input should include the pattern and optionally the directory."
    )
    args_schema: Type[BaseModel] = FileSearchInput
    base_dir: str = "."
    max_results: int = 50

    def _run(self, pattern: str, directory: str = ".") -> str:
        """Search for files matching pattern."""
        try:
            # Resolve path relative to base_dir
            full_path = Path(self.base_dir) / directory
            full_path = full_path.resolve()

            if not full_path.exists():
                return f"Error: Directory not found: {directory}"

            # Search recursively
            matches = list(full_path.rglob(pattern))
            matches = matches[:self.max_results]  # Limit results

            if not matches:
                return f"No files found matching pattern: {pattern}"

            relative_paths = [str(m.relative_to(full_path)) for m in matches]
            result = f"Found {len(matches)} file(s) matching '{pattern}':\n\n"
            result += "\n".join(relative_paths)

            if len(matches) == self.max_results:
                result += f"\n\n(Limited to first {self.max_results} results)"

            return result

        except Exception as e:
            return f"Error searching files: {str(e)}"


# =============================================================================
# Utility Functions
# =============================================================================

def get_coding_tools(
    include_read: bool = True,
    include_write: bool = True,
    include_list: bool = True,
    include_git: bool = True,
    include_search: bool = True,
    base_dir: str = "."
) -> list:
    """
    Get a list of coding tools.

    Args:
        include_read: Include file reading tool
        include_write: Include file writing tool
        include_list: Include directory listing tool
        include_git: Include Git status tool
        include_search: Include file search tool
        base_dir: Base directory for file operations

    Returns:
        list: List of tool instances

    Example:
        >>> tools = get_coding_tools(base_dir="/path/to/project")
        >>> agent = factory.create_coding_agent(tools)
    """
    tools = []

    if include_read:
        read_tool = ReadFileTool()
        read_tool.base_dir = base_dir
        tools.append(read_tool)

    if include_write:
        write_tool = WriteFileTool()
        write_tool.base_dir = base_dir
        tools.append(write_tool)

    if include_list:
        list_tool = ListDirectoryTool()
        list_tool.base_dir = base_dir
        tools.append(list_tool)

    if include_git:
        tools.append(GitStatusTool())

    if include_search:
        search_tool = FileSearchTool()
        search_tool.base_dir = base_dir
        tools.append(search_tool)

    return tools


def register_coding_tools(registry, base_dir: str = ".") -> None:
    """
    Register all coding tools in a tool registry.

    Args:
        registry: ToolRegistry instance
        base_dir: Base directory for file operations

    Example:
        >>> from agent_factory.tools.tool_registry import ToolRegistry
        >>> registry = ToolRegistry()
        >>> register_coding_tools(registry, base_dir="/path/to/project")
    """
    read_tool = ReadFileTool()
    read_tool.base_dir = base_dir

    write_tool = WriteFileTool()
    write_tool.base_dir = base_dir

    list_tool = ListDirectoryTool()
    list_tool.base_dir = base_dir

    search_tool = FileSearchTool()
    search_tool.base_dir = base_dir

    registry.register(
        "read_file",
        read_tool,
        category="coding",
        description="Read file contents"
    )

    registry.register(
        "write_file",
        write_tool,
        category="coding",
        description="Write or append to files"
    )

    registry.register(
        "list_directory",
        list_tool,
        category="coding",
        description="List directory contents"
    )

    registry.register(
        "git_status",
        GitStatusTool(),
        category="coding",
        description="Check Git repository status"
    )

    registry.register(
        "search_files",
        search_tool,
        category="coding",
        description="Search files by pattern"
    )
