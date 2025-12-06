"""
Input validation and safety checks for tools.

Provides validators for:
- Path traversal prevention
- File size limits
- Binary file detection
- Permission checks
"""

import os
from pathlib import Path
from typing import List, Optional, Set
import mimetypes


class PathTraversalError(ValueError):
    """Path traversal attempt detected."""
    pass


class FileSizeError(ValueError):
    """File size exceeds limit."""
    pass


class PathValidator:
    """
    Validates file paths for safety.

    Prevents:
    - Path traversal attacks (../)
    - Access to system directories
    - Access outside allowed directories
    - Symlink exploits

    Example:
        >>> validator = PathValidator(allowed_dirs=[Path("/project")])
        >>> safe_path = validator.validate("file.txt")
        >>> # Raises PathTraversalError if unsafe
    """

    # System directories to block (platform-agnostic)
    BLOCKED_DIRS = {
        "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin",
        "/System", "/Library",  # macOS
        "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)",  # Windows
    }

    def __init__(
        self,
        allowed_dirs: Optional[List[Path]] = None,
        allow_absolute: bool = False,
        follow_symlinks: bool = False
    ):
        """
        Initialize path validator.

        Args:
            allowed_dirs: List of allowed base directories (default: current dir)
            allow_absolute: Allow absolute paths (default: False)
            follow_symlinks: Follow symbolic links (default: False)
        """
        if allowed_dirs is None:
            # Default to current working directory
            allowed_dirs = [Path.cwd()]

        self.allowed_dirs = [d.resolve() for d in allowed_dirs]
        self.allow_absolute = allow_absolute
        self.follow_symlinks = follow_symlinks

    def validate(self, path: str) -> Path:
        """
        Validate and normalize a file path.

        Args:
            path: Path to validate (string)

        Returns:
            Validated Path object

        Raises:
            PathTraversalError: Path is unsafe or not allowed
            ValueError: Invalid path format
        """
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")

        # Convert to Path object
        try:
            p = Path(path)
        except Exception as e:
            raise ValueError(f"Invalid path format: {e}")

        # Check for absolute paths
        if p.is_absolute() and not self.allow_absolute:
            raise PathTraversalError("Absolute paths not allowed")

        # Resolve to absolute path (handles .., symlinks)
        try:
            if self.follow_symlinks:
                resolved = p.resolve()
            else:
                # Don't follow symlinks - check if path is symlink
                if p.is_symlink():
                    raise PathTraversalError("Symbolic links not allowed")
                resolved = p.resolve()
        except Exception as e:
            raise PathTraversalError(f"Cannot resolve path: {e}")

        # Check if path is within allowed directories
        is_allowed = False
        for allowed_dir in self.allowed_dirs:
            try:
                resolved.relative_to(allowed_dir)
                is_allowed = True
                break
            except ValueError:
                # Not relative to this allowed dir
                continue

        if not is_allowed:
            raise PathTraversalError(
                f"Path '{resolved}' is not within allowed directories: {self.allowed_dirs}"
            )

        # Check against blocked system directories
        for blocked in self.BLOCKED_DIRS:
            blocked_path = Path(blocked)
            try:
                resolved.relative_to(blocked_path)
                raise PathTraversalError(
                    f"Access to system directory '{blocked}' not allowed"
                )
            except ValueError:
                # Not in this blocked dir, good
                continue

        return resolved

    def is_safe(self, path: str) -> bool:
        """
        Check if path is safe without raising exception.

        Args:
            path: Path to check

        Returns:
            True if safe, False otherwise
        """
        try:
            self.validate(path)
            return True
        except (PathTraversalError, ValueError):
            return False


class FileSizeValidator:
    """
    Validates file sizes.

    Example:
        >>> validator = FileSizeValidator(max_size_mb=10)
        >>> validator.validate(Path("large_file.txt"))
        >>> # Raises FileSizeError if > 10MB
    """

    def __init__(self, max_size_mb: float = 10.0):
        """
        Initialize size validator.

        Args:
            max_size_mb: Maximum file size in megabytes
        """
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)

    def validate(self, path: Path) -> int:
        """
        Validate file size.

        Args:
            path: Path to file

        Returns:
            File size in bytes

        Raises:
            FileSizeError: File exceeds size limit
            FileNotFoundError: File doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        size = path.stat().st_size

        if size > self.max_size_bytes:
            raise FileSizeError(
                f"File size {size / 1024 / 1024:.2f}MB exceeds limit "
                f"{self.max_size_bytes / 1024 / 1024:.2f}MB"
            )

        return size

    def is_valid_size(self, path: Path) -> bool:
        """
        Check if file size is valid without raising exception.

        Args:
            path: Path to check

        Returns:
            True if valid size, False otherwise
        """
        try:
            self.validate(path)
            return True
        except (FileSizeError, FileNotFoundError):
            return False


def is_binary_file(path: Path, sample_size: int = 8192) -> bool:
    """
    Detect if file is binary.

    Reads first sample_size bytes and checks for null bytes.

    Args:
        path: Path to file
        sample_size: Number of bytes to sample

    Returns:
        True if binary, False if text

    Raises:
        FileNotFoundError: File doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with open(path, 'rb') as f:
            chunk = f.read(sample_size)

        # Check for null bytes (common in binary files)
        if b'\x00' in chunk:
            return True

        # Try to decode as text
        try:
            chunk.decode('utf-8')
            return False
        except UnicodeDecodeError:
            return True

    except Exception:
        # If we can't read it, assume binary
        return True


def detect_encoding(path: Path) -> str:
    """
    Detect file encoding.

    Args:
        path: Path to file

    Returns:
        Encoding name (e.g., 'utf-8', 'latin-1')

    Raises:
        FileNotFoundError: File doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Try common encodings
    encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as f:
                f.read(1024)  # Read small sample
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue

    # Default to utf-8
    return 'utf-8'


def get_file_type(path: Path) -> str:
    """
    Get file type/extension.

    Args:
        path: Path to file

    Returns:
        File extension (e.g., 'py', 'md', 'txt') or 'unknown'
    """
    suffix = path.suffix.lstrip('.')
    return suffix if suffix else 'unknown'


def is_allowed_file_type(
    path: Path,
    allowed_extensions: Optional[Set[str]] = None,
    blocked_extensions: Optional[Set[str]] = None
) -> bool:
    """
    Check if file type is allowed.

    Args:
        path: Path to file
        allowed_extensions: Set of allowed extensions (e.g., {'py', 'txt'})
        blocked_extensions: Set of blocked extensions (e.g., {'exe', 'dll'})

    Returns:
        True if allowed, False otherwise
    """
    ext = get_file_type(path)

    # Check blocked list first
    if blocked_extensions and ext in blocked_extensions:
        return False

    # If allowed list exists, check it
    if allowed_extensions and ext not in allowed_extensions:
        return False

    return True
