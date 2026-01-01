"""
Agent Factory Tools Package

Provides various tools for agents:
- Research tools: Web search, time
- File tools: Read, write, list, search (Phase 4)
- Caching: Result caching system (Phase 4)
- Validators: Path and size validation (Phase 4)
"""

# Research tools (Phase 1)
from .research_tools import CurrentTimeTool

# Research Executor (autonomous research)
from .research_executor import (
    ResearchExecutorTool,
    ResearchTask,
    ResearchResult,
    ResearchStatus,
    ResearchPriority,
    LLMProvider,
    create_langchain_tool as create_research_executor_tool,
)

# Gap Filling (knowledge base enrichment)
from .response_gap_filler import (
    KnowledgeGapFiller,
    ResponseGapDetector,
    KnowledgeGap,
    GapType,
    FilledGap,
)

# File tools (Phase 4)
from .file_tools import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    FileSearchTool
)

# Caching (Phase 4)
from .cache import (
    CacheManager,
    cached_tool,
    ToolCache,
    get_global_cache,
    clear_global_cache
)

# Validators (Phase 4)
from .validators import (
    PathValidator,
    FileSizeValidator,
    PathTraversalError,
    FileSizeError,
    is_binary_file,
    detect_encoding,
    get_file_type,
    is_allowed_file_type
)

# Factory.io Integration (PLC Code Verification)
from .factoryio import (
    FactoryIOConnectionTool,
    FactoryIOTagTool,
    FactoryIOReadWriteTool
)

__all__ = [
    # Research tools
    "CurrentTimeTool",
    # Research Executor
    "ResearchExecutorTool",
    "ResearchTask",
    "ResearchResult",
    "ResearchStatus",
    "ResearchPriority",
    "LLMProvider",
    "create_research_executor_tool",
    # Gap Filling
    "KnowledgeGapFiller",
    "ResponseGapDetector",
    "KnowledgeGap",
    "GapType",
    "FilledGap",
    # File tools
    "ReadFileTool",
    "WriteFileTool",
    "ListDirectoryTool",
    "FileSearchTool",
    # Caching
    "CacheManager",
    "cached_tool",
    "ToolCache",
    "get_global_cache",
    "clear_global_cache",
    # Validators
    "PathValidator",
    "FileSizeValidator",
    "PathTraversalError",
    "FileSizeError",
    "is_binary_file",
    "detect_encoding",
    "get_file_type",
    "is_allowed_file_type",
    # Factory.io Integration
    "FactoryIOConnectionTool",
    "FactoryIOTagTool",
    "FactoryIOReadWriteTool",
]
