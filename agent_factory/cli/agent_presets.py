"""
Pre-configured agents for CLI usage.

Provides ready-to-use agents with common tool configurations:
- Research Agent: Web search, Wikipedia, current time
- Coding Agent: File operations, git status, code search
"""

from typing import Dict, Any
from langchain.agents import AgentExecutor

from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import get_research_tools
from agent_factory.tools import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    FileSearchTool
)


# =============================================================================
# Agent Configurations
# =============================================================================

AGENT_CONFIGS = {
    "research": {
        "name": "Research Assistant",
        "description": "Web research agent with Wikipedia, DuckDuckGo, and time tools",
        "system_message": (
            "You are a helpful research assistant. Your goal is to find accurate "
            "information from reliable sources. Always cite your sources and be "
            "honest when you don't know something."
        )
    },
    "coding": {
        "name": "Coding Assistant",
        "description": "Code analysis and file operation agent",
        "system_message": (
            "You are a helpful coding assistant. You can read files, write files, "
            "list directories, and search for content in files. Be careful with "
            "file operations and always confirm before making destructive changes."
        )
    }
}


# =============================================================================
# Agent Factories
# =============================================================================

def get_research_agent(
    factory: AgentFactory,
    include_tavily: bool = False
) -> AgentExecutor:
    """
    Create a research agent with web search tools.

    The research agent can:
    - Search Wikipedia for factual information
    - Search the web via DuckDuckGo
    - Optionally use Tavily for AI-optimized search (requires API key)
    - Get the current time/date

    Args:
        factory: AgentFactory instance
        include_tavily: Include Tavily search (requires TAVILY_API_KEY)

    Returns:
        AgentExecutor configured for research

    Example:
        >>> factory = AgentFactory(verbose=True)
        >>> agent = get_research_agent(factory)
        >>> result = agent.invoke({"input": "What is LangChain?"})
    """
    config = AGENT_CONFIGS["research"]

    # Get research tools
    tools = get_research_tools(
        include_wikipedia=True,
        include_duckduckgo=True,
        include_tavily=include_tavily,
        include_time=True
    )

    # Create agent
    agent = factory.create_agent(
        role=config["name"],
        tools_list=tools,
        system_message=config["system_message"],
        agent_type=AgentFactory.AGENT_TYPE_REACT
    )

    return agent


def get_coding_agent(factory: AgentFactory) -> AgentExecutor:
    """
    Create a coding agent with file operation tools.

    The coding agent can:
    - Read file contents
    - Write to files (with backups)
    - List directory contents
    - Search for content in files

    Args:
        factory: AgentFactory instance

    Returns:
        AgentExecutor configured for coding tasks

    Example:
        >>> factory = AgentFactory(verbose=True)
        >>> agent = get_coding_agent(factory)
        >>> result = agent.invoke({"input": "List all Python files"})
    """
    config = AGENT_CONFIGS["coding"]

    # Create file operation tools
    tools = [
        ReadFileTool(),
        WriteFileTool(),
        ListDirectoryTool(),
        FileSearchTool()
    ]

    # Create agent
    agent = factory.create_agent(
        role=config["name"],
        tools_list=tools,
        system_message=config["system_message"],
        agent_type=AgentFactory.AGENT_TYPE_REACT
    )

    return agent


# =============================================================================
# Agent Registry
# =============================================================================

def list_available_agents() -> Dict[str, Dict[str, str]]:
    """
    Get information about all available preset agents.

    Returns:
        Dictionary mapping agent names to their configurations

    Example:
        >>> agents = list_available_agents()
        >>> for name, info in agents.items():
        ...     print(f"{name}: {info['description']}")
    """
    return {
        name: {
            "name": config["name"],
            "description": config["description"]
        }
        for name, config in AGENT_CONFIGS.items()
    }


def get_agent(name: str, factory: AgentFactory, **kwargs) -> AgentExecutor:
    """
    Get an agent by name.

    Args:
        name: Agent name ("research" or "coding")
        factory: AgentFactory instance
        **kwargs: Additional arguments for specific agents

    Returns:
        AgentExecutor for the specified agent

    Raises:
        ValueError: If agent name is unknown

    Example:
        >>> factory = AgentFactory()
        >>> agent = get_agent("research", factory)
    """
    if name == "research":
        return get_research_agent(factory, **kwargs)
    elif name == "coding":
        return get_coding_agent(factory)
    else:
        available = ", ".join(AGENT_CONFIGS.keys())
        raise ValueError(
            f"Unknown agent: {name}. Available agents: {available}"
        )


def get_agent_description(name: str) -> str:
    """
    Get a description of an agent.

    Args:
        name: Agent name

    Returns:
        Agent description string

    Example:
        >>> desc = get_agent_description("research")
        >>> print(desc)
    """
    if name not in AGENT_CONFIGS:
        return f"Unknown agent: {name}"

    config = AGENT_CONFIGS[name]
    return f"{config['name']}: {config['description']}"
