"""
Auto-Research Trigger - Priority-based research triggering

Listens for kb_gap_detected events and triggers research pipeline
based on priority scores.

Priority Routing:
- CRITICAL/HIGH (≥70): Trigger immediately
- MEDIUM (40-69): Batch and trigger hourly
- LOW (<40): Batch and trigger daily
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class AutoResearchTrigger:
    """
    Automatically triggers research pipeline for KB gaps.

    Priority-based triggering:
    - CRITICAL (90-100): Immediate
    - HIGH (70-89): Immediate
    - MEDIUM (40-69): Batched hourly
    - LOW (<40): Batched daily
    """

    def __init__(self, db=None):
        """
        Initialize auto-research trigger.

        Args:
            db: DatabaseManager instance (optional, created if not provided)
        """
        if db is None:
            from agent_factory.core.database_manager import DatabaseManager
            db = DatabaseManager()

        self.db = db
        self.medium_priority_batch: List[Tuple[int, Dict]] = []
        self.low_priority_batch: List[Tuple[int, Dict]] = []

        logger.info("AutoResearchTrigger initialized")

    async def trigger_research(self, event_data: Dict):
        """
        Trigger research based on gap priority.

        Args:
            event_data: kb_gap_detected event payload with:
                - gap_id: int
                - priority: int (0-100)
                - equipment: str (e.g., "siemens:s7_1200")
                - query: str
                - weakness_type: str
        """
        gap_id = event_data["gap_id"]
        priority = event_data["priority"]
        equipment = event_data["equipment"]
        query = event_data["query"]

        logger.info(
            f"Auto-research trigger: gap_id={gap_id}, "
            f"priority={priority}, equipment={equipment}"
        )

        # Parse equipment identifier
        vendor, equipment_type = self._parse_equipment(equipment)

        # Build intent for research pipeline
        intent_data = {
            "vendor": vendor,
            "equipment_type": equipment_type,
            "symptom": query[:200],  # Truncate
            "raw_question": query
        }

        # ULTRA-AGGRESSIVE MODE: Trigger ALL priorities immediately
        # No batching - research everything from day 1
        logger.info(
            f"AGGRESSIVE MODE: Triggering immediate research for ALL priorities"
        )
        await self._trigger_immediate(gap_id, intent_data)

    async def _trigger_immediate(self, gap_id: int, intent_data: Dict):
        """
        Trigger research immediately for high-priority gaps.

        Args:
            gap_id: Gap ID in database
            intent_data: Intent dictionary with vendor, equipment, symptom
        """
        try:
            # Mark ingestion as started
            await asyncio.to_thread(
                self.db.execute_query,
                """
                UPDATE gap_requests
                SET ingestion_started = TRUE, ingestion_started_at = NOW()
                WHERE id = $1
                """,
                (gap_id,),
                fetch_mode="none"
            )

            logger.info(f"Marked gap {gap_id} as ingestion_started")

            # Run research pipeline
            try:
                from agent_factory.rivet_pro.research.research_pipeline import ResearchPipeline
                from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType

                # Build RivetIntent
                try:
                    vendor_enum = VendorType(intent_data["vendor"].lower())
                except ValueError:
                    vendor_enum = VendorType.GENERIC

                try:
                    equipment_enum = EquipmentType(intent_data["equipment_type"].lower())
                except ValueError:
                    equipment_enum = EquipmentType.UNKNOWN

                intent = RivetIntent(
                    vendor=vendor_enum,
                    equipment_type=equipment_enum,
                    symptom=intent_data["symptom"],
                    raw_question=intent_data["raw_question"]
                )

                # Run research pipeline (blocking - may take 30-60 seconds)
                pipeline = ResearchPipeline(self.db)
                result = await asyncio.to_thread(pipeline.run, intent)

                logger.info(
                    f"Research completed: gap_id={gap_id}, "
                    f"sources_found={result.sources_found}, "
                    f"sources_queued={result.sources_queued}"
                )

            except Exception as e:
                logger.error(
                    f"Research pipeline failed for gap_id={gap_id}: {e}",
                    exc_info=True
                )

        except Exception as e:
            logger.error(
                f"Failed to trigger immediate research for gap_id={gap_id}: {e}",
                exc_info=True
            )

    def _parse_equipment(self, equipment_str: str) -> Tuple[str, str]:
        """
        Parse equipment identifier into vendor and type.

        Args:
            equipment_str: Format "vendor:equipment_type" (e.g., "siemens:s7_1200")

        Returns:
            (vendor, equipment_type) tuple
        """
        try:
            parts = equipment_str.split(":")
            if len(parts) == 2:
                return parts[0], parts[1]
        except:
            pass

        # Fallback to generic
        return "generic", "unknown"

    async def process_medium_batch(self):
        """
        Process medium-priority batch (called hourly).
        """
        if not self.medium_priority_batch:
            logger.info("No medium-priority gaps to process")
            return

        logger.info(
            f"Processing {len(self.medium_priority_batch)} medium-priority gaps"
        )

        for gap_id, intent_data in self.medium_priority_batch:
            await self._trigger_immediate(gap_id, intent_data)

        self.medium_priority_batch.clear()
        logger.info("Medium-priority batch processed")

    async def process_low_batch(self):
        """
        Process low-priority batch (called daily).
        """
        if not self.low_priority_batch:
            logger.info("No low-priority gaps to process")
            return

        logger.info(
            f"Processing {len(self.low_priority_batch)} low-priority gaps"
        )

        for gap_id, intent_data in self.low_priority_batch:
            await self._trigger_immediate(gap_id, intent_data)

        self.low_priority_batch.clear()
        logger.info("Low-priority batch processed")


# Singleton instance
_auto_research_trigger: Optional[AutoResearchTrigger] = None


async def trigger_research(event_data: Dict):
    """
    Global function to trigger research.

    Called by KBGapLogger._emit_gap_event().

    Args:
        event_data: kb_gap_detected event payload
    """
    global _auto_research_trigger

    if _auto_research_trigger is None:
        _auto_research_trigger = AutoResearchTrigger()

    await _auto_research_trigger.trigger_research(event_data)


async def process_medium_batch():
    """
    Process medium-priority batch (called hourly by scheduler).
    """
    global _auto_research_trigger

    if _auto_research_trigger is None:
        _auto_research_trigger = AutoResearchTrigger()

    await _auto_research_trigger.process_medium_batch()


async def process_low_batch():
    """
    Process low-priority batch (called daily by scheduler).
    """
    global _auto_research_trigger

    if _auto_research_trigger is None:
        _auto_research_trigger = AutoResearchTrigger()

    await _auto_research_trigger.process_low_batch()
