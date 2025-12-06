# PHASE4_SPEC.md - Deterministic Tools

## Overview

Build production-ready, deterministic tools that agents can use reliably. Focus on file operations, caching, and idempotent behavior to ensure consistent, safe execution.

**Success:** Agents can read/write files safely, cache expensive operations, and execute the same command multiple times without side effects.

**Vision:** Tools that "just work" - predictable, safe, and efficient.

---

## Why Deterministic Tools?

### Problem
Current tools (web search, time) are:
- Non-deterministic (different results each time)
- Uncached (expensive repeated calls)
- Potentially unsafe (no validation)

### Solution
Build tools that are:
- **Deterministic** - Same input → same output (when possible)
- **Cached** - Avoid redundant expensive operations
- **Safe** - Validated inputs, proper error handling
- **Idempotent** - Can run multiple times safely

### Use Cases
1. **File Operations** - Agents read/write code with validation
2. **Caching** - Avoid repeated API calls for same query
3. **Code Analysis** - Parse and understand codebases
4. **Idempotent Actions** - State checks before mutations

---

## Files to Create

```
agent_factory/tools/
├── file_tools.py          # File operation tools (read, write, list)
├── cache.py               # Result caching system
├── validators.py          # Input validation and safety

tests/
├── test_file_tools.py     # File tool tests (15-20 tests)
├── test_cache.py          # Cache system tests (10-15 tests)

examples/
├── file_tools_demo.py     # Demonstration
```

---

## Requirements

### REQ-DET-001: File Reading
**Priority:** HIGH
**Description:** Safe file reading with validation

**Features:**
- Read text files with encoding detection
- Path validation (no traversal attacks)
- Size limits (prevent memory issues)
- File type whitelisting (optional)
- Binary file detection

**API:**
```python
class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read contents of a file"

    def _run(self, file_path: str) -> str:
        """
        Read file contents safely.

        Args:
            file_path: Path to file (relative or absolute)

        Returns:
            File contents as string

        Raises:
            ValueError: Invalid path
            FileNotFoundError: File doesn't exist
            PermissionError: No read access
        """
```

**Safety Checks:**
- ✅ Path is within allowed directories
- ✅ File exists and is readable
- ✅ File size < max_size (default 10MB)
- ✅ Detect binary files (return error or metadata)

---

### REQ-DET-002: File Writing
**Priority:** HIGH
**Description:** Safe file writing with backups

**Features:**
- Write text files with encoding
- Automatic backups before overwrite
- Atomic writes (temp file → rename)
- Directory creation if needed
- Rollback on failure

**API:**
```python
class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file"

    def _run(
        self,
        file_path: str,
        content: str,
        create_backup: bool = True
    ) -> str:
        """
        Write content to file safely.

        Args:
            file_path: Path to file
            content: Content to write
            create_backup: Whether to backup existing file

        Returns:
            Success message with path
        """
```

**Safety Checks:**
- ✅ Path is within allowed directories
- ✅ Create parent directories if needed
- ✅ Backup existing file (.bak)
- ✅ Atomic write (write to temp, then rename)
- ✅ Validate content size

---

### REQ-DET-003: Directory Listing
**Priority:** MEDIUM
**Description:** List directory contents

**Features:**
- List files and directories
- Recursive option
- Pattern filtering (glob)
- Sort by name, size, date
- Metadata (size, modified time)

**API:**
```python
class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files in a directory"

    def _run(
        self,
        directory: str,
        pattern: str = "*",
        recursive: bool = False
    ) -> str:
        """
        List directory contents.

        Args:
            directory: Path to directory
            pattern: Glob pattern (e.g., "*.py")
            recursive: Include subdirectories

        Returns:
            Formatted list of files with metadata
        """
```

---

### REQ-DET-004: File Search
**Priority:** MEDIUM
**Description:** Search for content in files

**Features:**
- Search by content (regex)
- Search by filename (glob)
- Recursive search
- Context lines (before/after match)
- Line numbers

**API:**
```python
class FileSearchTool(BaseTool):
    name = "search_files"
    description = "Search for content in files"

    def _run(
        self,
        pattern: str,
        directory: str = ".",
        file_pattern: str = "*",
        case_sensitive: bool = False
    ) -> str:
        """
        Search for pattern in files.

        Args:
            pattern: Regex pattern to search
            directory: Where to search
            file_pattern: Which files to search
            case_sensitive: Case-sensitive search

        Returns:
            Formatted search results with line numbers
        """
```

---

### REQ-DET-005: Result Caching
**Priority:** HIGH
**Description:** Cache expensive tool results

**Features:**
- In-memory cache (default)
- Redis cache (optional, production)
- TTL-based expiration
- Cache key generation
- Cache stats (hits, misses)
- Selective caching per tool

**API:**
```python
class CacheManager:
    """Manages result caching for tools."""

    def __init__(
        self,
        cache_type: str = "memory",  # "memory" | "redis"
        default_ttl: int = 3600,      # 1 hour
        max_size: int = 1000           # Max cached items
    ):
        pass

    def get(self, key: str) -> Optional[Any]:
        """Get cached result."""

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Cache a result."""

    def invalidate(self, key: str):
        """Remove from cache."""

    def clear(self):
        """Clear all cache."""

    def stats(self) -> Dict[str, int]:
        """Return cache statistics."""
```

**Usage:**
```python
from agent_factory.tools.cache import cached_tool

@cached_tool(ttl=3600)
class ExpensiveSearchTool(BaseTool):
    # Results cached for 1 hour
    pass
```

---

### REQ-DET-006: Path Validation
**Priority:** CRITICAL
**Description:** Prevent path traversal attacks

**Features:**
- Whitelist allowed directories
- Detect `..` traversal attempts
- Resolve symlinks
- Normalize paths
- Check permissions

**API:**
```python
class PathValidator:
    """Validates file paths for safety."""

    def __init__(
        self,
        allowed_dirs: List[Path],
        allow_absolute: bool = False
    ):
        pass

    def validate(self, path: str) -> Path:
        """
        Validate and normalize path.

        Raises:
            ValueError: Path not allowed
        """

    def is_safe(self, path: str) -> bool:
        """Check if path is safe."""
```

**Security Checks:**
- ✅ No `..` traversal
- ✅ Path is within allowed directories
- ✅ Symlinks resolved correctly
- ✅ No access to system files (/etc, C:\Windows)

---

### REQ-DET-007: Idempotent Operations
**Priority:** MEDIUM
**Description:** Tools that can run multiple times safely

**Pattern:**
```python
class IdempotentWriteTool(BaseTool):
    def _run(self, file_path: str, content: str) -> str:
        # Check current state
        if file_exists(file_path):
            current = read_file(file_path)
            if current == content:
                return f"File already has correct content"

        # Only write if different
        write_file(file_path, content)
        return f"File written successfully"
```

**Examples:**
- Write file only if content differs
- Create directory only if doesn't exist
- Append to file only if line not present

---

### REQ-DET-008: Error Handling
**Priority:** HIGH
**Description:** Graceful error handling with helpful messages

**Features:**
- Custom exception types
- Detailed error messages
- Error recovery suggestions
- Logging of errors

**Custom Exceptions:**
```python
class FileToolError(Exception):
    """Base exception for file tools."""
    pass

class PathTraversalError(FileToolError):
    """Path traversal attempt detected."""
    pass

class FileSizeError(FileToolError):
    """File size exceeds limit."""
    pass

class PermissionError(FileToolError):
    """Insufficient permissions."""
    pass
```

---

## Implementation Plan

### Phase 4.1: File Tools (2 hours)

**Step 1:** Create `validators.py` (30 min)
- PathValidator class
- Size validation helpers
- Binary file detection

**Step 2:** Create `file_tools.py` (1 hour)
- ReadFileTool
- WriteFileTool
- ListDirectoryTool
- FileSearchTool

**Step 3:** Testing (30 min)
- test_file_tools.py (15-20 tests)
- Test safety checks
- Test error handling

---

### Phase 4.2: Caching System (1.5 hours)

**Step 1:** Create `cache.py` (45 min)
- CacheManager class
- In-memory cache implementation
- Cache key generation
- TTL handling

**Step 2:** Cache decorator (30 min)
- @cached_tool decorator
- Integrate with LangChain tools
- Cache statistics

**Step 3:** Testing (15 min)
- test_cache.py (10-15 tests)
- Test TTL expiration
- Test cache invalidation

---

### Phase 4.3: Integration & Demo (1 hour)

**Step 1:** Update AgentFactory (15 min)
- Add file tools to default imports
- Create convenience methods

**Step 2:** Create demo (30 min)
- examples/file_tools_demo.py
- Show read/write operations
- Show caching benefits
- Show safety features

**Step 3:** Documentation (15 min)
- Update README
- Add safety guidelines
- Document allowed directories

---

## Testing Strategy

### Unit Tests (test_file_tools.py)
```python
class TestReadFileTool:
    def test_read_existing_file()
    def test_read_nonexistent_file()
    def test_read_large_file_rejected()
    def test_path_traversal_rejected()
    def test_binary_file_detection()

class TestWriteFileTool:
    def test_write_new_file()
    def test_overwrite_with_backup()
    def test_atomic_write()
    def test_create_parent_dirs()
    def test_path_traversal_rejected()

class TestListDirectoryTool:
    def test_list_files()
    def test_list_with_pattern()
    def test_recursive_listing()

class TestFileSearchTool:
    def test_search_content()
    def test_search_with_regex()
    def test_case_insensitive()
```

### Cache Tests (test_cache.py)
```python
class TestCacheManager:
    def test_cache_set_get()
    def test_cache_expiration()
    def test_cache_invalidation()
    def test_cache_stats()
    def test_max_size_enforcement()
```

### Integration Tests
```python
class TestFileToolsWithAgent:
    def test_agent_reads_file()
    def test_agent_writes_file()
    def test_cached_results()
```

---

## Safety Guidelines

### Allowed Directories
By default, only allow:
- Current working directory
- User-specified project directories
- Temp directory

**Never allow:**
- System directories (/etc, /bin, C:\Windows, C:\Program Files)
- User home directory (unless explicitly allowed)
- Parent directories outside project root

### File Size Limits
- **Read:** Default 10MB (configurable)
- **Write:** Default 10MB (configurable)
- **Binary files:** Reject or return metadata only

### File Type Restrictions
Optional whitelist/blacklist:
```python
ALLOWED_EXTENSIONS = [".py", ".md", ".txt", ".json", ".yaml"]
BLOCKED_EXTENSIONS = [".exe", ".dll", ".so", ".dylib"]
```

---

## Cache Configuration

### Default Settings
```python
DEFAULT_CACHE_CONFIG = {
    "cache_type": "memory",
    "default_ttl": 3600,      # 1 hour
    "max_size": 1000,          # 1000 items
    "enable_stats": True
}
```

### Per-Tool TTL
```python
TOOL_TTL_OVERRIDES = {
    "read_file": 300,          # 5 minutes (files change)
    "search_files": 600,       # 10 minutes
    "current_time": 0,         # Never cache
}
```

---

## Example Usage

### Basic File Operations
```python
from agent_factory import AgentFactory
from agent_factory.tools.file_tools import ReadFileTool, WriteFileTool

factory = AgentFactory()

# Create agent with file tools
agent = factory.create_agent(
    role="File Manager",
    tools_list=[ReadFileTool(), WriteFileTool()],
    system_prompt="You can read and write files safely."
)

# Agent can now read/write files
response = agent.invoke({
    "input": "Read the contents of README.md and summarize it"
})
```

### With Caching
```python
from agent_factory.tools.cache import CacheManager

# Enable caching
cache = CacheManager(default_ttl=3600)

# Tools automatically use cache
agent = factory.create_agent(
    role="Researcher",
    tools_list=[SearchTool(), ReadFileTool()],
    cache_manager=cache
)

# First call: executes search
agent.invoke({"input": "Search for 'LangChain' in docs"})

# Second call: returns cached result (instant)
agent.invoke({"input": "Search for 'LangChain' in docs"})

# Cache stats
print(cache.stats())
# {"hits": 1, "misses": 1, "size": 1}
```

---

## Success Criteria

### Phase 4 Complete When:
- ✅ All file tools implemented and tested
- ✅ Caching system working with TTL
- ✅ Path validation prevents traversal
- ✅ 25+ tests passing
- ✅ Demo shows safe file operations
- ✅ Documentation complete
- ✅ Committed with tag `phase-4-complete`

### Test Coverage Goal
- File tools: 15-20 tests
- Cache system: 10-15 tests
- Integration: 5 tests
- **Total: 30-40 tests** (122-132 total)

---

## Future Enhancements (Post-Phase 4)

### Advanced Caching
- Redis backend for distributed caching
- Cache warming strategies
- Cache sharing between agents

### Advanced File Tools
- Diff tool (compare files)
- Patch tool (apply changes)
- Archive tool (zip/tar operations)
- Git integration (read from commits)

### Database Tools
- SQLite read/write
- CSV parsing
- JSON schema validation

---

**Ready to implement Phase 4?**

```bash
# Checkpoint: Start Phase 4
poetry run python -c "print('PHASE 4: Deterministic Tools - Starting...')"
```
