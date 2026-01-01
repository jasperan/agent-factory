"""
Factory.io integration tools for PLC code verification.

Provides three tools:
- FactoryIOConnectionTool: Connect and health check
- FactoryIOTagTool: Discover tags and metadata
- FactoryIOReadWriteTool: Read/write tag values

Example usage:
    from agent_factory.tools.factoryio import (
        FactoryIOConnectionTool,
        FactoryIOTagTool,
        FactoryIOReadWriteTool
    )

    # Health check
    conn_tool = FactoryIOConnectionTool()
    result = conn_tool._run(action="health_check")

    # Discover tags
    tag_tool = FactoryIOTagTool()
    tags = tag_tool._run(action="list")

    # Read tag values
    rw_tool = FactoryIOReadWriteTool()
    value = rw_tool._run(action="read", tag_ids=["Conveyor"])
"""

from .connection_tool import FactoryIOConnectionTool
from .tag_tool import FactoryIOTagTool
from .readwrite_tool import FactoryIOReadWriteTool

__all__ = [
    "FactoryIOConnectionTool",
    "FactoryIOTagTool",
    "FactoryIOReadWriteTool",
]
