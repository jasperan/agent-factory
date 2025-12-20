"""
Pre-configured agents for CLI usage.

Provides ready-to-use agents with common tool configurations:
- Research Agent: Web search, Wikipedia, current time
- Coding Agent: File operations, git status, code search
"""

from typing import Dict, Any
from agent_factory.compat.langchain_shim import AgentExecutor

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
            "honest when you don't know something.\n\n"
            "CONVERSATION CONTEXT:\n"
            "- Review the chat_history to understand previous discussion\n"
            "- Reference specific items mentioned earlier when user uses pronouns (it, they, those, that)\n"
            "- If user asks follow-up questions, connect to prior context\n"
            "- If context is unclear, ask clarifying questions"
        )
    },
    "coding": {
        "name": "Coding Assistant",
        "description": "Code analysis and file operation agent",
        "system_message": (
            "You are a helpful coding assistant. You can read files, write files, "
            "list directories, and search for content in files. Be careful with "
            "file operations and always confirm before making destructive changes.\n\n"
            "CONVERSATION CONTEXT:\n"
            "- Review the chat_history to understand previous discussion\n"
            "- Reference specific items mentioned earlier when user uses pronouns (it, they, those, that)\n"
            "- If user asks follow-up questions, connect to prior context\n"
            "- If context is unclear, ask clarifying questions"
        )
    },
    "bob": {
        "name": "Bob - Market Research Specialist",
        "description": "Market opportunity discovery for apps, agents, and digital products",
        "system_message": (
            "You are a Market Research Specialist that discovers high-value opportunities "
            "for selling apps, agents, and digital products.\n\n"
            "Your mission: Analyze market trends, competitive landscapes, customer pain points, "
            "and emerging niches. Provide actionable insights on where to build and how to "
            "position products for maximum market fit and revenue potential.\n\n"
            "CONVERSATION CONTEXT:\n"
            "- Review the chat_history to understand previous discussion\n"
            "- Reference specific items mentioned earlier when user uses pronouns (it, they, those, that)\n"
            "- If user asks follow-up questions, connect to prior context\n"
            "- When user asks about 'the market', determine which market from context\n"
            "- If context is unclear, ask clarifying questions\n\n"
            "RULES (Must never be violated):\n"
            "1. Evidence-Based: All claims must be backed by verifiable sources and data\n"
            "2. Ethical Research: Never recommend exploitative practices or dark patterns\n"
            "3. Transparency: Always disclose when information is uncertain or based on limited data\n"
            "4. User Focus: Prioritize opportunities that solve real customer problems, not just profit\n"
            "5. Timeliness: Focus on current market conditions (data < 6 months old when possible)\n"
            "6. Actionability: Every insight must include specific next steps or validation methods\n"
            "7. Cost Awareness: Keep API usage under $0.50 per research query\n"
            "8. Response Speed: Deliver initial findings within 60 seconds\n\n"
            "When analyzing markets, always provide:\n"
            "- Specific niches with market size estimates\n"
            "- Customer pain points and willingness to pay\n"
            "- Competition analysis (low/medium/high)\n"
            "- Concrete validation steps (interviews, MVP timeline, pricing tests)\n"
            "- Realistic revenue projections with MRR estimates\n"
            "- Source citations for all market claims"
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


def get_bob_agent(factory: AgentFactory) -> AgentExecutor:
    """
    Create Bob - the market research specialist agent.

    Bob can:
    - Search web (Wikipedia, DuckDuckGo, Tavily)
    - Get current time/date
    - Read and write files
    - List directories and search files
    - Check git status

    Bob specializes in:
    - Market opportunity discovery
    - Competitive landscape analysis
    - Customer pain point identification
    - Niche validation strategies
    - Revenue potential estimation

    Args:
        factory: AgentFactory instance

    Returns:
        AgentExecutor configured for market research

    Example:
        >>> factory = AgentFactory(verbose=True)
        >>> bob = get_bob_agent(factory)
        >>> result = bob.invoke({
        ...     "input": "Find 3 underserved AI automation niches"
        ... })
    """
    config = AGENT_CONFIGS["bob"]

    # Get research tools
    research_tools = get_research_tools(
        include_wikipedia=True,
        include_duckduckgo=True,
        include_tavily=True,  # AI-powered search
        include_time=True
    )

    # Add file operation tools for saving research
    file_tools = [
        ReadFileTool(),
        WriteFileTool(),
        ListDirectoryTool(),
        FileSearchTool()
    ]

    # Combine all tools
    tools = research_tools + file_tools

    # Create agent with higher iteration limit for complex research
    agent = factory.create_agent(
        role=config["name"],
        tools_list=tools,
        system_message=config["system_message"],
        agent_type=AgentFactory.AGENT_TYPE_REACT,
        max_iterations=25,  # Higher limit for multi-step research
        max_execution_time=300  # 5 minutes timeout
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
        name: Agent name ("research", "coding", or "bob")
        factory: AgentFactory instance
        **kwargs: Additional arguments for specific agents

    Returns:
        AgentExecutor for the specified agent

    Raises:
        ValueError: If agent name is unknown

    Example:
        >>> factory = AgentFactory()
        >>> agent = get_agent("research", factory)
        >>> bob = get_agent("bob", factory)
    """
    if name == "research":
        return get_research_agent(factory, **kwargs)
    elif name == "coding":
        return get_coding_agent(factory)
    elif name == "bob":
        return get_bob_agent(factory)
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
