"""Real-time manual finder for Route B queries."""

import asyncio
import logging
from typing import List, Dict, Optional
from agent_factory.tools.research_tools import DuckDuckGoSearchTool
from agent_factory.schemas.routing import VendorType

logger = logging.getLogger(__name__)


class ManualFinder:
    """
    Finds manufacturer manuals via web search.

    Optimized for industrial equipment manuals (VFDs, PLCs, HMIs).
    Uses DuckDuckGo for fast, API-key-free search.
    """

    def __init__(self):
        self.search_tool = DuckDuckGoSearchTool(max_results=3)

        # Manufacturer documentation sites (for targeted search)
        self.vendor_sites = {
            VendorType.SIEMENS: "site:support.industry.siemens.com OR site:support.siemens.com",
            VendorType.ROCKWELL: "site:literature.rockwellautomation.com OR site:rockwellautomation.com",
            VendorType.ABB: "site:new.abb.com/drives OR site:library.abb.com",
            VendorType.SCHNEIDER: "site:download.schneider-electric.com",
            VendorType.MITSUBISHI: "site:mitsubishielectric.com/fa/document",
            VendorType.OMRON: "site:omron.com/global/en/support",
            VendorType.FUJI: "site:fujielectric.com/products/manuals",
            VendorType.YASKAWA: "site:yaskawa.com/downloads"
        }

    async def find_manual(
        self,
        query: str,
        vendor: VendorType,
        equipment_type: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Search for manufacturer manual.

        Args:
            query: User query (e.g., "Fuji FRENIC-Mini fault F003")
            vendor: Detected vendor
            equipment_type: Equipment type (e.g., "VFD", "PLC") if known

        Returns:
            List of manual results with title, url, snippet
            Example: [
                {
                    "title": "FRENIC-Mini User Manual",
                    "url": "https://fujielectric.com/.../manual.pdf",
                    "snippet": "Fault code F003 indicates..."
                }
            ]
        """
        try:
            # Build targeted search query
            search_query = self._build_search_query(query, vendor, equipment_type)

            logger.info(f"Searching for manual: {search_query}")

            # Execute search (synchronous, but fast ~1-2 seconds)
            loop = asyncio.get_event_loop()
            results_str = await loop.run_in_executor(
                None,  # Default ThreadPoolExecutor
                self.search_tool._run,
                search_query
            )

            # Parse results
            manuals = self._parse_results(results_str)

            logger.info(f"Found {len(manuals)} manual results")
            return manuals

        except Exception as e:
            logger.error(f"Manual search failed: {e}")
            return []

    def _build_search_query(
        self,
        query: str,
        vendor: VendorType,
        equipment_type: Optional[str]
    ) -> str:
        """Build optimized search query for manual finding."""

        # Base query: add "manual" or "user guide" keyword
        base = f"{query} manual"

        # Add site restriction if vendor has known documentation portal
        site_filter = self.vendor_sites.get(vendor, "")

        # Add file type filter to prioritize PDFs
        file_filter = "filetype:pdf OR manual OR \"user guide\" OR documentation"

        # Combine
        if site_filter:
            return f"{base} {file_filter} {site_filter}"
        else:
            return f"{base} {file_filter}"

    def _parse_results(self, results_str: str) -> List[Dict[str, str]]:
        """Parse DuckDuckGo results into structured format."""
        manuals = []

        # DuckDuckGo returns results as:
        # "Title 1\nSnippet 1\nURL 1\n\nTitle 2\nSnippet 2\nURL 2"

        sections = results_str.strip().split("\n\n")
        for section in sections:
            lines = section.strip().split("\n")
            if len(lines) >= 3:
                manuals.append({
                    "title": lines[0],
                    "snippet": lines[1],
                    "url": lines[2]
                })

        return manuals
