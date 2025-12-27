"""Background worker for KB enrichment from gap_requests."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import subprocess

from agent_factory.core.database_manager import DatabaseManager
from agent_factory.core.gap_detector import GapDetector

logger = logging.getLogger(__name__)


class KBEnrichmentWorker:
    """
    Background worker that processes gap_requests and queues sources for ingestion.

    Runs periodically (e.g., hourly) to:
    1. Find high-priority unprocessed gaps
    2. Use gap_detector to find sources
    3. Queue URLs to VPS Redis
    4. Mark gaps as processed
    """

    def __init__(self, batch_size: int = 5, min_priority: int = 50):
        self.db = DatabaseManager()
        self.gap_detector = GapDetector()
        self.batch_size = batch_size
        self.min_priority = min_priority

    async def process_batch(self) -> Dict[str, int]:
        """Process one batch of enrichment gaps."""
        stats = {
            "gaps_processed": 0,
            "sources_found": 0,
            "urls_queued": 0,
            "errors": 0
        }

        # Get unprocessed gaps with priority >= threshold
        gaps = self._get_pending_gaps()
        logger.info(f"Found {len(gaps)} pending enrichment gaps")

        for gap in gaps[:self.batch_size]:
            try:
                # Use gap_detector to find sources
                sources = await self._discover_sources(gap)
                stats["sources_found"] += len(sources)

                # Queue each source URL to VPS
                for source in sources:
                    if await self._queue_to_vps(source["url"]):
                        stats["urls_queued"] += 1

                # Mark gap as processed
                self._mark_processed(gap["id"], len(sources))
                stats["gaps_processed"] += 1

            except Exception as e:
                logger.error(f"Error processing gap {gap['id']}: {e}")
                stats["errors"] += 1

        return stats

    def _get_pending_gaps(self) -> List[Dict]:
        """Get unprocessed gaps from database."""
        query = """
            SELECT id, user_query, vendor, equipment_type, symptom, priority_score
            FROM gap_requests
            WHERE ingestion_completed = FALSE
              AND priority_score >= %s
              AND enrichment_type = 'thin_coverage'
            ORDER BY priority_score DESC, created_at ASC
            LIMIT %s
        """
        results = self.db.execute_query(query, (self.min_priority, self.batch_size * 2))

        return [
            {
                "id": row[0],
                "user_query": row[1],
                "vendor": row[2],
                "equipment_type": row[3],
                "symptom": row[4],
                "priority_score": row[5]
            }
            for row in results
        ]

    async def _discover_sources(self, gap: Dict) -> List[Dict[str, str]]:
        """Use gap_detector to find source URLs."""
        # Build intent from gap data
        from agent_factory.rivet_pro.research.types import RivetIntent, EquipmentType, VendorType

        intent = RivetIntent(
            vendor=VendorType(gap["vendor"]),
            equipment_type=EquipmentType.PLC,  # Default, could enhance
            symptom=gap["symptom"]
        )

        # Analyze gap and generate ingestion trigger
        ingestion_trigger = self.gap_detector.analyze_gap(
            query=gap["user_query"],
            kb_coverage_level="THIN",
            intent=intent
        )

        if not ingestion_trigger:
            return []

        # Extract source URLs from trigger
        sources = []
        for source_type, search_terms in ingestion_trigger.get("sources_to_try", {}).items():
            # TODO: Actually search for URLs using search_terms
            # For MVP, use manufacturer site pattern
            if source_type == "manufacturer_website":
                vendor_sites = {
                    "siemens": "https://support.industry.siemens.com/cs/document/",
                    "rockwell": "https://literature.rockwellautomation.com/",
                    "fuji": "https://www.fujielectric.com/products/manuals/"
                }
                base_url = vendor_sites.get(gap["vendor"].lower())
                if base_url:
                    sources.append({
                        "url": base_url,
                        "type": source_type,
                        "search_terms": search_terms
                    })

        return sources

    async def _queue_to_vps(self, url: str) -> bool:
        """Queue URL to VPS Redis via SSH."""
        try:
            escaped_url = url.replace("'", "'\\''")
            cmd = f'ssh -i ~/.ssh/vps_deploy_key root@72.60.175.144 "docker exec infra_redis_1 redis-cli RPUSH kb_ingest_jobs \'{escaped_url}\'"'

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            success = result.returncode == 0
            if success:
                logger.info(f"Queued to VPS: {url}")
            else:
                logger.warning(f"Failed to queue: {url}, error: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"VPS queue error: {e}")
            return False

    def _mark_processed(self, gap_id: int, sources_found: int) -> None:
        """Mark gap as processed in database."""
        query = """
            UPDATE gap_requests
            SET
                ingestion_completed = TRUE,
                sources_queued = %s,
                processed_at = NOW()
            WHERE id = %s
        """
        self.db.execute_query(query, (sources_found, gap_id))


async def run_enrichment_worker():
    """Main entry point for enrichment worker."""
    worker = KBEnrichmentWorker(batch_size=5, min_priority=50)

    logger.info("Starting KB enrichment worker...")

    while True:
        try:
            stats = await worker.process_batch()
            logger.info(f"Batch complete: {stats}")

            # Wait 1 hour before next batch
            await asyncio.sleep(3600)

        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(300)  # Wait 5 min on error


if __name__ == "__main__":
    asyncio.run(run_enrichment_worker())
