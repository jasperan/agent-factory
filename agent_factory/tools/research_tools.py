"""
Research Tools: Web search, Wikipedia, and knowledge retrieval tools

This module provides tools for research agents to search the web,
access Wikipedia, and gather information from various sources.
"""

import os
from typing import ClassVar, Type, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


# =============================================================================
# Wikipedia Tool
# =============================================================================

class WikipediaSearchInput(BaseModel):
    """Input schema for Wikipedia search tool."""
    query: str = Field(description="The search query for Wikipedia")


class WikipediaSearchTool(BaseTool):
    """Tool for searching Wikipedia articles."""

    name: ClassVar[str] = "wikipedia_search"
    description: ClassVar[str] = (
        "Useful for when you need to look up factual information on Wikipedia. "
        "Input should be a search query string. Returns a summary of the Wikipedia article."
    )
    args_schema: Type[BaseModel] = WikipediaSearchInput

    def _run(self, query: str) -> str:
        """Search Wikipedia and return article summary."""
        try:
            from wikipedia import summary, DisambiguationError, PageError

            try:
                result = summary(query, sentences=3)
                return f"Wikipedia result for '{query}':\n\n{result}"
            except DisambiguationError as e:
                # Return first few options if disambiguation is needed
                options = e.options[:5]
                return f"Multiple results found. Please be more specific. Options: {', '.join(options)}"
            except PageError:
                return f"No Wikipedia page found for '{query}'"

        except ImportError:
            return "Wikipedia package not installed. Install with: pip install wikipedia"
        except Exception as e:
            return f"Error searching Wikipedia: {str(e)}"


# =============================================================================
# DuckDuckGo Search Tool
# =============================================================================

class DuckDuckGoSearchInput(BaseModel):
    """Input schema for DuckDuckGo search tool."""
    query: str = Field(description="The search query for DuckDuckGo")


class DuckDuckGoSearchTool(BaseTool):
    """Tool for searching the web using DuckDuckGo (no API key required)."""

    name: ClassVar[str] = "duckduckgo_search"
    description: ClassVar[str] = (
        "Useful for searching the web for current information. "
        "Input should be a search query. Returns search results from DuckDuckGo."
    )
    args_schema: Type[BaseModel] = DuckDuckGoSearchInput
    max_results: int = 5

    def _run(self, query: str) -> str:
        """Search DuckDuckGo and return results."""
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=self.max_results))

            if not results:
                return f"No results found for query: {query}"

            formatted_results = [f"**{i+1}. {r['title']}**\n{r['body']}\nURL: {r['href']}\n"
                                 for i, r in enumerate(results)]

            return f"Search results for '{query}':\n\n" + "\n".join(formatted_results)

        except ImportError:
            return "DuckDuckGo search package not installed. Install with: pip install duckduckgo-search"
        except Exception as e:
            return f"Error searching DuckDuckGo: {str(e)}"


# =============================================================================
# Tavily Search Tool (requires API key)
# =============================================================================

class TavilySearchInput(BaseModel):
    """Input schema for Tavily search tool."""
    query: str = Field(description="The search query for Tavily")


class TavilySearchTool(BaseTool):
    """Tool for AI-optimized web search using Tavily (requires API key)."""

    name: ClassVar[str] = "tavily_search"
    description: ClassVar[str] = (
        "Useful for AI-optimized web search with high-quality results. "
        "Input should be a search query. Returns comprehensive search results."
    )
    args_schema: Type[BaseModel] = TavilySearchInput

    def _run(self, query: str) -> str:
        """Search using Tavily API and return results."""
        try:
            from tavily import TavilyClient

            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                return "TAVILY_API_KEY environment variable not set"

            client = TavilyClient(api_key=api_key)
            results = client.search(query=query)

            if not results or "results" not in results:
                return f"No results found for query: {query}"

            formatted_results = []
            for i, result in enumerate(results["results"][:5], 1):
                formatted_results.append(
                    f"**{i}. {result.get('title', 'N/A')}**\n"
                    f"{result.get('content', 'N/A')}\n"
                    f"URL: {result.get('url', 'N/A')}\n"
                )

            return f"Tavily search results for '{query}':\n\n" + "\n".join(formatted_results)

        except ImportError:
            return "Tavily package not installed. Install with: pip install tavily-python"
        except Exception as e:
            return f"Error searching Tavily: {str(e)}"


# =============================================================================
# Current Time Tool
# =============================================================================

class CurrentTimeInput(BaseModel):
    """Input schema for current time tool."""
    format: str = Field(
        default="%I:%M %p",
        description="Time format string (default: 12-hour with AM/PM)"
    )


class CurrentTimeTool(BaseTool):
    """Tool for getting the current time."""

    name: ClassVar[str] = "current_time"
    description: ClassVar[str] = "Useful for when you need to know the current time. Returns the current time."
    args_schema: Type[BaseModel] = CurrentTimeInput

    def _run(self, format: str = "%I:%M %p") -> str:
        """Get current time."""
        import datetime
        now = datetime.datetime.now()
        return f"Current time: {now.strftime(format)}"


# =============================================================================
# Utility Functions
# =============================================================================

def get_research_tools(
    include_wikipedia: bool = True,
    include_duckduckgo: bool = True,
    include_tavily: bool = False,
    include_time: bool = True
) -> list:
    """
    Get a list of research tools.

    Args:
        include_wikipedia: Include Wikipedia search
        include_duckduckgo: Include DuckDuckGo search
        include_tavily: Include Tavily search (requires API key)
        include_time: Include current time tool

    Returns:
        list: List of tool instances

    Example:
        >>> tools = get_research_tools(include_tavily=True)
        >>> agent = factory.create_research_agent(tools)
    """
    tools = []

    if include_wikipedia:
        tools.append(WikipediaSearchTool())

    if include_duckduckgo:
        tools.append(DuckDuckGoSearchTool())

    if include_tavily:
        tools.append(TavilySearchTool())

    if include_time:
        tools.append(CurrentTimeTool())

    return tools


def register_research_tools(registry) -> None:
    """
    Register all research tools in a tool registry.

    Args:
        registry: ToolRegistry instance

    Example:
        >>> from agent_factory.tools.tool_registry import ToolRegistry
        >>> registry = ToolRegistry()
        >>> register_research_tools(registry)
    """
    registry.register(
        "wikipedia",
        WikipediaSearchTool(),
        category="research",
        description="Search Wikipedia articles"
    )

    registry.register(
        "duckduckgo",
        DuckDuckGoSearchTool(),
        category="research",
        description="Web search via DuckDuckGo"
    )

    registry.register(
        "tavily",
        TavilySearchTool(),
        category="research",
        description="AI-optimized web search",
        requires_api_key=True,
        api_key_env_var="TAVILY_API_KEY"
    )

    registry.register(
        "current_time",
        CurrentTimeTool(),
        category="utility",
        description="Get current time"
    )
