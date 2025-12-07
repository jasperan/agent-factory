"""
========================================================================
TOOL REGISTRY - Complete Catalog of Available Tools
========================================================================

PURPOSE:
    Central registry of all available tools for agents.
    Used by AgentEditor to show/select tools interactively.

WHAT THIS PROVIDES:
    - Complete list of research, file, code, web tools
    - Tool descriptions and categories
    - Tool import paths
    - Tool initialization logic

WHY WE NEED THIS:
    Users need to see ALL available tools when building agents,
    not just remember names from memory.
========================================================================
"""

from typing import Dict, List, Any, Callable
from dataclasses import dataclass


@dataclass
class ToolInfo:
    """
    PURPOSE: Metadata about a single tool

    WHAT THIS STORES:
        - name: Tool class name
        - description: What the tool does
        - category: research, file, code, web, etc.
        - requires_api_key: Whether tool needs API key
        - api_key_name: Name of env var (if applicable)
        - import_path: Where to import from
    """
    name: str
    description: str
    category: str
    requires_api_key: bool = False
    api_key_name: str = None
    import_path: str = None


# ========================================================================
# TOOL CATALOG - Complete Registry
# ========================================================================

TOOL_CATALOG: Dict[str, ToolInfo] = {
    # RESEARCH TOOLS
    "WikipediaSearchTool": ToolInfo(
        name="WikipediaSearchTool",
        description="Search Wikipedia for factual information, definitions, historical context",
        category="research",
        requires_api_key=False,
        import_path="agent_factory.tools.research_tools"
    ),

    "DuckDuckGoSearchTool": ToolInfo(
        name="DuckDuckGoSearchTool",
        description="Web search via DuckDuckGo - current events, news, general research",
        category="research",
        requires_api_key=False,
        import_path="agent_factory.tools.research_tools"
    ),

    "TavilySearchTool": ToolInfo(
        name="TavilySearchTool",
        description="AI-optimized search engine - best for market intelligence and research",
        category="research",
        requires_api_key=True,
        api_key_name="TAVILY_API_KEY",
        import_path="agent_factory.tools.research_tools"
    ),

    "CurrentTimeTool": ToolInfo(
        name="CurrentTimeTool",
        description="Get current date and time - useful for temporal analysis",
        category="utility",
        requires_api_key=False,
        import_path="agent_factory.tools.research_tools"
    ),

    # FILE OPERATION TOOLS
    "ReadFileTool": ToolInfo(
        name="ReadFileTool",
        description="Read file contents - code, docs, data files",
        category="file",
        requires_api_key=False,
        import_path="agent_factory.tools"
    ),

    "WriteFileTool": ToolInfo(
        name="WriteFileTool",
        description="Write to files - save reports, generate code, create documents",
        category="file",
        requires_api_key=False,
        import_path="agent_factory.tools"
    ),

    "ListDirectoryTool": ToolInfo(
        name="ListDirectoryTool",
        description="List directory contents - browse file structures",
        category="file",
        requires_api_key=False,
        import_path="agent_factory.tools"
    ),

    "FileSearchTool": ToolInfo(
        name="FileSearchTool",
        description="Search for text patterns in files - find code, analyze content",
        category="file",
        requires_api_key=False,
        import_path="agent_factory.tools"
    ),

    # CODE/GIT TOOLS
    "GitStatusTool": ToolInfo(
        name="GitStatusTool",
        description="Check git repository status - analyze repos, track changes",
        category="code",
        requires_api_key=False,
        import_path="agent_factory.tools.coding_tools"
    ),

    # WEB TOOLS (if implemented)
    "WebBrowserTool": ToolInfo(
        name="WebBrowserTool",
        description="Browse websites, extract content, interact with web pages",
        category="web",
        requires_api_key=False,
        import_path="langchain_community.tools"
    ),

    # DATABASE TOOLS (if implemented)
    "SQLDatabaseTool": ToolInfo(
        name="SQLDatabaseTool",
        description="Query SQL databases - analyze data, run reports",
        category="data",
        requires_api_key=False,
        import_path="langchain_community.tools.sql_database.tool"
    ),
}


# ========================================================================
# TOOL COLLECTIONS - Pre-configured Sets
# ========================================================================

TOOL_COLLECTIONS = {
    "research_basic": [
        "WikipediaSearchTool",
        "DuckDuckGoSearchTool",
        "CurrentTimeTool",
    ],

    "research_advanced": [
        "WikipediaSearchTool",
        "DuckDuckGoSearchTool",
        "TavilySearchTool",
        "CurrentTimeTool",
    ],

    "file_operations": [
        "ReadFileTool",
        "WriteFileTool",
        "ListDirectoryTool",
        "FileSearchTool",
    ],

    "code_analysis": [
        "ReadFileTool",
        "FileSearchTool",
        "ListDirectoryTool",
        "GitStatusTool",
    ],

    "full_power": [
        "WikipediaSearchTool",
        "DuckDuckGoSearchTool",
        "TavilySearchTool",
        "CurrentTimeTool",
        "ReadFileTool",
        "WriteFileTool",
        "ListDirectoryTool",
        "FileSearchTool",
        "GitStatusTool",
    ],
}


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def list_tools_by_category() -> Dict[str, List[ToolInfo]]:
    """
    PURPOSE: Group tools by category for display

    RETURNS:
        Dict mapping category -> list of tools

    EXAMPLE:
        {
            "research": [WikipediaSearchTool, ...],
            "file": [ReadFileTool, ...],
            ...
        }
    """
    categories: Dict[str, List[ToolInfo]] = {}

    for tool_name, tool_info in TOOL_CATALOG.items():
        category = tool_info.category
        if category not in categories:
            categories[category] = []
        categories[category].append(tool_info)

    return categories


def get_tool_info(tool_name: str) -> ToolInfo:
    """
    PURPOSE: Get metadata for a specific tool

    INPUTS:
        tool_name (str): Name of tool

    RETURNS:
        ToolInfo object

    RAISES:
        KeyError: If tool not found
    """
    if tool_name not in TOOL_CATALOG:
        available = ", ".join(TOOL_CATALOG.keys())
        raise KeyError(f"Tool '{tool_name}' not found. Available: {available}")

    return TOOL_CATALOG[tool_name]


def search_tools(query: str) -> List[ToolInfo]:
    """
    PURPOSE: Search for tools by name or description

    INPUTS:
        query (str): Search query

    RETURNS:
        List of matching tools

    EXAMPLE:
        >>> search_tools("search")
        [WikipediaSearchTool, DuckDuckGoSearchTool, TavilySearchTool, FileSearchTool]
    """
    query_lower = query.lower()
    matches = []

    for tool_name, tool_info in TOOL_CATALOG.items():
        if (query_lower in tool_name.lower() or
            query_lower in tool_info.description.lower() or
            query_lower in tool_info.category.lower()):
            matches.append(tool_info)

    return matches


def get_collection(collection_name: str) -> List[str]:
    """
    PURPOSE: Get pre-configured tool collection

    INPUTS:
        collection_name: Name of collection

    RETURNS:
        List of tool names

    EXAMPLE:
        >>> get_collection("research_basic")
        ["WikipediaSearchTool", "DuckDuckGoSearchTool", "CurrentTimeTool"]
    """
    if collection_name not in TOOL_COLLECTIONS:
        available = ", ".join(TOOL_COLLECTIONS.keys())
        raise KeyError(
            f"Collection '{collection_name}' not found. Available: {available}"
        )

    return TOOL_COLLECTIONS[collection_name]


def format_tool_list(tools: List[str], show_selected: bool = False,
                     selected: List[str] = None) -> str:
    """
    PURPOSE: Format tool list for display

    INPUTS:
        tools: List of tool names
        show_selected: Whether to show checkboxes
        selected: Currently selected tools

    RETURNS:
        Formatted string for display

    EXAMPLE:
        [X] WikipediaSearchTool - Search Wikipedia for factual information
        [ ] DuckDuckGoSearchTool - Web search via DuckDuckGo
    """
    if selected is None:
        selected = []

    lines = []
    for tool_name in tools:
        tool_info = TOOL_CATALOG.get(tool_name)
        if not tool_info:
            continue

        if show_selected:
            checkbox = "[X]" if tool_name in selected else "[ ]"
            line = f"  {checkbox} {tool_name}"
        else:
            line = f"  - {tool_name}"

        # Add description
        line += f" - {tool_info.description}"

        # Add API key requirement
        if tool_info.requires_api_key:
            line += f" (requires {tool_info.api_key_name})"

        lines.append(line)

    return "\n".join(lines)


# ========================================================================
# TOOL INITIALIZATION
# ========================================================================

def get_tool_initialization_code(tool_names: List[str]) -> str:
    """
    PURPOSE: Generate Python code to initialize tools

    INPUTS:
        tool_names: List of tool names to initialize

    RETURNS:
        Python code string

    EXAMPLE:
        >>> get_tool_initialization_code(["WikipediaSearchTool", "ReadFileTool"])
        '''
        from agent_factory.tools.research_tools import get_research_tools
        from agent_factory.tools import ReadFileTool

        tools = get_research_tools(include_wikipedia=True, ...)
        tools.append(ReadFileTool())
        '''
    """
    # Group tools by import path
    research_tools = []
    file_tools = []
    other_tools = []

    for tool_name in tool_names:
        tool_info = TOOL_CATALOG.get(tool_name)
        if not tool_info:
            continue

        if "research_tools" in tool_info.import_path:
            research_tools.append(tool_name)
        elif tool_name in ["ReadFileTool", "WriteFileTool", "ListDirectoryTool", "FileSearchTool"]:
            file_tools.append(tool_name)
        else:
            other_tools.append(tool_name)

    code_lines = []

    # Research tools
    if research_tools:
        code_lines.append("from agent_factory.tools.research_tools import get_research_tools")
        params = []
        if "WikipediaSearchTool" in research_tools:
            params.append("include_wikipedia=True")
        if "DuckDuckGoSearchTool" in research_tools:
            params.append("include_duckduckgo=True")
        if "TavilySearchTool" in research_tools:
            params.append("include_tavily=True")
        if "CurrentTimeTool" in research_tools:
            params.append("include_time=True")

        code_lines.append(f"tools = get_research_tools({', '.join(params)})")
    else:
        code_lines.append("tools = []")

    # File tools
    if file_tools:
        code_lines.append("from agent_factory.tools.coding_tools import get_coding_tools")
        code_lines.append("tools.extend(get_coding_tools(")
        code_lines.append("    include_read=True,")
        code_lines.append("    include_write=True,")
        code_lines.append("    include_list=True,")
        code_lines.append("    include_git=True,")
        code_lines.append("    include_search=True,")
        code_lines.append("    base_dir='.'")
        code_lines.append("))")

    return "\n".join(code_lines)
