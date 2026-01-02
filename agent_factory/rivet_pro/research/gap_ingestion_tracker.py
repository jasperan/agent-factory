"""
Gap Ingestion Tracker - Connects ingestion completion to gap resolution.

Tracks gap_id through ingestion pipeline and marks gaps completed
when atoms are successfully created.
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from agent_factory.core.database_manager import DatabaseManager
from agent_factory.core.kb_gap_logger import KBGapLogger

logger = logging.getLogger(__name__)


class GapIngestionTracker:
    """
    Tracks gap-related ingestions and marks gaps completed.

    Usage:
        tracker = GapIngestionTracker()

        # After research pipeline queues sources:
        tracker.register_gap_sources(
            gap_id=123,
            source_urls=["http://example.com/manual.pdf"]
        )

        # After ingestion completes:
        await tracker.mark_ingestion_complete(
            source_url="http://example.com/manual.pdf",
            atoms_created=15
        )
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        """
        Initialize gap ingestion tracker.

        Args:
            db: DatabaseManager instance (creates new if None)
        """
        self.db = db or DatabaseManager()
        self.gap_logger = KBGapLogger(self.db)

        # In-memory mapping: source_url → gap_id
        # (For production, use Redis or database table)
        self._gap_source_map: Dict[str, int] = {}

        logger.info("GapIngestionTracker initialized")

    def register_gap_sources(self, gap_id: int, source_urls: list[str]):
        """
        Register sources associated with a gap.

        Args:
            gap_id: Gap ID that triggered research
            source_urls: List of source URLs queued for ingestion
        """
        for url in source_urls:
            self._gap_source_map[url] = gap_id

        logger.info(
            f"Registered {len(source_urls)} sources for gap_id={gap_id}"
        )

    async def mark_ingestion_complete(
        self,
        source_url: str,
        atoms_created: int
    ) -> bool:
        """
        Mark gap completed after ingestion finishes.

        Called by ingestion chain after atoms are stored.

        Args:
            source_url: Source URL that was ingested
            atoms_created: Number of atoms created from this source

        Returns:
            bool: True if gap was marked completed, False otherwise
        """
        # Check if this source is associated with a gap
        gap_id = self._gap_source_map.get(source_url)

        if gap_id is None:
            logger.debug(
                f"Ingestion complete for {source_url} but no associated gap "
                "(probably manual ingestion or VPS KB source)"
            )
            return False

        # Mark gap as completed
        try:
            success = await self.gap_logger.mark_gap_completed(
                gap_id=gap_id,
                atoms_created=atoms_created
            )

            if success:
                # Remove from map (gap is now resolved)
                del self._gap_source_map[source_url]

                logger.info(
                    f"Gap {gap_id} marked completed: "
                    f"{atoms_created} atoms from {source_url}"
                )

            return success

        except Exception as e:
            logger.error(
                f"Failed to mark gap completed: gap_id={gap_id}, error={e}",
                exc_info=True
            )
            return False

    def get_pending_gaps(self) -> Dict[str, int]:
        """
        Get all pending gap-source mappings.

        Returns:
            Dict mapping source_url → gap_id for all pending ingestions
        """
        return self._gap_source_map.copy()

    def get_gap_for_source(self, source_url: str) -> Optional[int]:
        """
        Get gap_id associated with a source URL.

        Args:
            source_url: Source URL to look up

        Returns:
            gap_id if found, None otherwise
        """
        return self._gap_source_map.get(source_url)


# Global singleton instance
_gap_tracker: Optional[GapIngestionTracker] = None


def get_gap_tracker() -> GapIngestionTracker:
    """
    Get global gap ingestion tracker instance.

    Returns:
        GapIngestionTracker singleton
    """
    global _gap_tracker

    if _gap_tracker is None:
        _gap_tracker = GapIngestionTracker()

    return _gap_tracker


async def mark_ingestion_complete(source_url: str, atoms_created: int):
    """
    Mark gap completed after ingestion (global function).

    Called by ingestion chain after atoms stored.

    Args:
        source_url: Source URL that was ingested
        atoms_created: Number of atoms created
    """
    tracker = get_gap_tracker()
    await tracker.mark_ingestion_complete(source_url, atoms_created)
