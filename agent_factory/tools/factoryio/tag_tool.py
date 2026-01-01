"""
FactoryIOTagTool - Discover tags and get metadata.

Usage:
    tool = FactoryIOTagTool()
    # List all tags
    result = tool._run(action="list")
    # Filter by type
    result = tool._run(action="list", tag_type="Bit")
    # Filter by kind
    result = tool._run(action="list", tag_kind="Input")
    # Get specific tag by name
    result = tool._run(action="get_by_name", tag_name="Conveyor")
"""

from typing import Optional, Type, ClassVar, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import requests
import json
import os


class FactoryIOTagInput(BaseModel):
    """Input schema for FactoryIOTagTool."""
    action: str = Field(
        description="Action: 'list' (all tags), 'get_by_name' (specific tag by name)"
    )
    tag_name: Optional[str] = Field(
        default=None,
        description="Tag name for 'get_by_name' action"
    )
    tag_type: Optional[str] = Field(
        default=None,
        description="Filter by type for 'list': Bit, Int, Float"
    )
    tag_kind: Optional[str] = Field(
        default=None,
        description="Filter by kind for 'list': Input, Output"
    )
    name_filter: Optional[str] = Field(
        default=None,
        description="Filter by name pattern for 'list' (case-insensitive substring match)"
    )


class FactoryIOTagTool(BaseTool):
    """Discover Factory.io tags and get metadata."""

    name: ClassVar[str] = "factoryio_tag"
    description: ClassVar[str] = """
    Discover Factory.io tags and get metadata.

    Actions:
    - list: Get all tags (optionally filtered by type/kind/name)
    - get_by_name: Get specific tag details by name

    Returns JSON with tag details.
    """
    args_schema: Type[BaseModel] = FactoryIOTagInput

    base_url: str = os.getenv("FACTORY_IO_URL", "http://localhost:7410")
    timeout: int = int(os.getenv("FACTORY_IO_TIMEOUT", "5"))

    def _run(
        self,
        action: str,
        tag_name: Optional[str] = None,
        tag_type: Optional[str] = None,
        tag_kind: Optional[str] = None,
        name_filter: Optional[str] = None
    ) -> str:
        """Execute tag discovery action."""
        try:
            if action == "list":
                return self._list_tags(tag_type, tag_kind, name_filter)
            elif action == "get_by_name":
                if not tag_name:
                    return "ERROR: tag_name required for 'get_by_name' action"
                return self._get_tag_by_name(tag_name)
            else:
                return f"ERROR: Unknown action '{action}'. Valid actions: list, get_by_name"
        except requests.exceptions.ConnectionError:
            return f"ERROR: Cannot connect to Factory.io at {self.base_url}"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def _list_tags(
        self,
        tag_type: Optional[str] = None,
        tag_kind: Optional[str] = None,
        name_filter: Optional[str] = None
    ) -> str:
        """List all tags with optional filters."""
        params = {}
        if tag_type:
            params["type"] = tag_type
        if tag_kind:
            params["kind"] = tag_kind

        response = requests.get(
            f"{self.base_url}/api/tags",
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        tags = response.json()

        # Apply name filter if provided
        if name_filter:
            name_filter_lower = name_filter.lower()
            tags = [
                tag for tag in tags
                if name_filter_lower in tag.get("name", "").lower()
            ]

        return json.dumps({
            "count": len(tags),
            "tags": tags
        }, indent=2)

    def _get_tag_by_name(self, tag_name: str) -> str:
        """Get specific tag details by name."""
        # Factory.io API uses /api/tags/by-name/{name} endpoint
        # URL encode the name (safe='' ensures "/" is also encoded)
        import urllib.parse
        encoded_name = urllib.parse.quote(tag_name, safe='')

        response = requests.get(
            f"{self.base_url}/api/tags/by-name/{encoded_name}",
            timeout=self.timeout
        )
        response.raise_for_status()
        tags = response.json()

        # API returns array of tags (names not unique in Factory.io)
        if not tags:
            return f"ERROR: No tag found with name '{tag_name}'"

        if len(tags) == 1:
            return json.dumps(tags[0], indent=2)
        else:
            # Multiple tags with same name
            return json.dumps({
                "count": len(tags),
                "message": f"Found {len(tags)} tags with name '{tag_name}'",
                "tags": tags
            }, indent=2)
