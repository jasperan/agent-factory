"""
FactoryIOConnectionTool - Connect to Factory.io Web API and verify health.

Usage:
    tool = FactoryIOConnectionTool()
    result = tool._run(action="health_check")
    result = tool._run(action="list_tags_summary")
"""

from typing import Optional, Type, ClassVar
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import requests
import os


class FactoryIOConnectionInput(BaseModel):
    """Input schema for FactoryIOConnectionTool."""
    action: str = Field(
        description="Action to perform: 'health_check' or 'list_tags_summary'"
    )


class FactoryIOConnectionTool(BaseTool):
    """Connect to Factory.io Web API and verify health."""

    name: ClassVar[str] = "factoryio_connection"
    description: ClassVar[str] = """
    Connect to Factory.io Web API and verify health.

    Actions:
    - health_check: Verify API is reachable and responsive
    - list_tags_summary: Get count of available tags by type

    Returns JSON with status and details.
    """
    args_schema: Type[BaseModel] = FactoryIOConnectionInput

    base_url: str = os.getenv("FACTORY_IO_URL", "http://localhost:7410")
    timeout: int = int(os.getenv("FACTORY_IO_TIMEOUT", "5"))

    def _run(self, action: str) -> str:
        """Execute connection action."""
        try:
            if action == "health_check":
                return self._health_check()
            elif action == "list_tags_summary":
                return self._list_tags_summary()
            else:
                return f"ERROR: Unknown action '{action}'. Valid actions: health_check, list_tags_summary"
        except requests.exceptions.ConnectionError:
            return (
                f"ERROR: Cannot connect to Factory.io at {self.base_url}. "
                "Is Factory.io running with Web API enabled? "
                "Run 'app.web_server = True' in Factory.io console."
            )
        except requests.exceptions.Timeout:
            return f"ERROR: Connection timeout to {self.base_url}. Check if Factory.io is responding."
        except Exception as e:
            return f"ERROR: {str(e)}"

    def _health_check(self) -> str:
        """Verify API is reachable."""
        response = requests.get(
            f"{self.base_url}/api/tags",
            timeout=self.timeout
        )
        response.raise_for_status()

        tags = response.json()
        return f"SUCCESS: Factory.io API is reachable at {self.base_url} ({len(tags)} tags available)"

    def _list_tags_summary(self) -> str:
        """Get tag count by type."""
        response = requests.get(
            f"{self.base_url}/api/tags",
            timeout=self.timeout
        )
        response.raise_for_status()
        tags = response.json()

        # Group by type and kind
        summary = {}
        for tag in tags:
            tag_type = tag.get("type", "unknown")
            tag_kind = tag.get("kind", "unknown")
            key = f"{tag_type} ({tag_kind})"
            summary[key] = summary.get(key, 0) + 1

        # Format summary
        lines = [f"Tag Summary (Total: {len(tags)}):"]
        for key, count in sorted(summary.items()):
            lines.append(f"  - {key}: {count}")

        return "\n".join(lines)
