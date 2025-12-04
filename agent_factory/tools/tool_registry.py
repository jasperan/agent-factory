"""
Tool Registry: Dynamic tool registration and retrieval system

This module provides a centralized registry for managing LangChain tools,
enabling dynamic tool discovery and assignment to agents.
"""

from typing import Dict, List, Type, Optional, Callable
from langchain_core.tools import BaseTool


class ToolRegistry:
    """
    Centralized registry for managing and retrieving LangChain tools.

    This allows dynamic tool registration, categorization, and retrieval,
    making it easy to create agents with different tool sets.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        self._tool_metadata: Dict[str, Dict] = {}

    def register(
        self,
        name: str,
        tool: BaseTool,
        category: Optional[str] = None,
        description: Optional[str] = None,
        requires_api_key: bool = False,
        api_key_env_var: Optional[str] = None
    ) -> None:
        """
        Register a tool in the registry.

        Args:
            name: Unique identifier for the tool
            tool: The BaseTool instance to register
            category: Optional category (e.g., "search", "file_ops", "computation")
            description: Optional extended description
            requires_api_key: Whether this tool requires an API key
            api_key_env_var: Environment variable name for the API key

        Example:
            >>> registry = ToolRegistry()
            >>> registry.register(
            ...     "wikipedia",
            ...     WikipediaQueryRun(),
            ...     category="research",
            ...     description="Search Wikipedia articles"
            ... )
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        self._tools[name] = tool

        # Store metadata
        self._tool_metadata[name] = {
            "category": category,
            "description": description or getattr(tool, "description", ""),
            "requires_api_key": requires_api_key,
            "api_key_env_var": api_key_env_var
        }

        # Add to category
        if category:
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(name)

    def register_class(
        self,
        name: str,
        tool_class: Type[BaseTool],
        category: Optional[str] = None,
        description: Optional[str] = None,
        requires_api_key: bool = False,
        api_key_env_var: Optional[str] = None,
        **init_kwargs
    ) -> None:
        """
        Register a tool by instantiating a tool class.

        Args:
            name: Unique identifier for the tool
            tool_class: The BaseTool class to instantiate
            category: Optional category
            description: Optional extended description
            requires_api_key: Whether this tool requires an API key
            api_key_env_var: Environment variable name for the API key
            **init_kwargs: Arguments to pass to tool class constructor

        Example:
            >>> registry.register_class(
            ...     "search",
            ...     DuckDuckGoSearchRun,
            ...     category="research"
            ... )
        """
        tool_instance = tool_class(**init_kwargs)
        self.register(
            name=name,
            tool=tool_instance,
            category=category,
            description=description,
            requires_api_key=requires_api_key,
            api_key_env_var=api_key_env_var
        )

    def get(self, name: str) -> BaseTool:
        """
        Retrieve a tool by name.

        Args:
            name: Tool identifier

        Returns:
            BaseTool: The registered tool

        Raises:
            KeyError: If tool is not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def get_many(self, names: List[str]) -> List[BaseTool]:
        """
        Retrieve multiple tools by name.

        Args:
            names: List of tool identifiers

        Returns:
            List[BaseTool]: List of tools in the same order as names

        Example:
            >>> tools = registry.get_many(["wikipedia", "search", "calculator"])
        """
        return [self.get(name) for name in names]

    def get_by_category(self, category: str) -> List[BaseTool]:
        """
        Retrieve all tools in a category.

        Args:
            category: Category name

        Returns:
            List[BaseTool]: All tools in the category

        Example:
            >>> research_tools = registry.get_by_category("research")
        """
        if category not in self._categories:
            return []

        tool_names = self._categories[category]
        return [self._tools[name] for name in tool_names]

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List[str]: List of all tool names
        """
        return list(self._tools.keys())

    def list_categories(self) -> List[str]:
        """
        List all categories.

        Returns:
            List[str]: List of all category names
        """
        return list(self._categories.keys())

    def get_metadata(self, name: str) -> Dict:
        """
        Get metadata for a tool.

        Args:
            name: Tool identifier

        Returns:
            Dict: Tool metadata including category, description, etc.
        """
        if name not in self._tool_metadata:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tool_metadata[name]

    def unregister(self, name: str) -> None:
        """
        Remove a tool from the registry.

        Args:
            name: Tool identifier
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")

        # Remove from tools
        del self._tools[name]

        # Remove from metadata
        metadata = self._tool_metadata.pop(name)

        # Remove from category
        category = metadata.get("category")
        if category and category in self._categories:
            self._categories[category].remove(name)
            if not self._categories[category]:
                del self._categories[category]

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._categories.clear()
        self._tool_metadata.clear()

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def __len__(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)

    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"ToolRegistry(tools={len(self._tools)}, categories={len(self._categories)})"


# Global registry instance
_global_registry = ToolRegistry()


def get_global_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        ToolRegistry: The global registry
    """
    return _global_registry


def register_tool(
    name: str,
    tool: BaseTool,
    category: Optional[str] = None,
    **kwargs
) -> None:
    """
    Convenience function to register a tool in the global registry.

    Args:
        name: Tool identifier
        tool: BaseTool instance
        category: Optional category
        **kwargs: Additional metadata
    """
    _global_registry.register(name, tool, category, **kwargs)


def get_tool(name: str) -> BaseTool:
    """
    Convenience function to get a tool from the global registry.

    Args:
        name: Tool identifier

    Returns:
        BaseTool: The registered tool
    """
    return _global_registry.get(name)


def get_tools(names: List[str]) -> List[BaseTool]:
    """
    Convenience function to get multiple tools from the global registry.

    Args:
        names: List of tool identifiers

    Returns:
        List[BaseTool]: List of tools
    """
    return _global_registry.get_many(names)
