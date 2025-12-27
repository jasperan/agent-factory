"""
KB Gap Logger - Tracks knowledge base gaps when Route C is triggered.

Logs queries that return 0 KB atoms to identify missing content,
detect patterns, and measure gap resolution over time.
"""
import asyncio
import json
import logging
from typing import Optional, Dict

from agent_factory.core.database_manager import DatabaseManager
from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType

logger = logging.getLogger(__name__)


class KBGapLogger:
    """Logs and tracks knowledge base gaps."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize KB gap logger.

        Args:
            db: DatabaseManager instance for executing queries
        """
        self.db = db

    def log_gap(
        self,
        query: str,
        intent: RivetIntent,
        search_filters: dict,
        user_id: Optional[str] = None,
        route: str = "C",
        confidence: float = 0.0,
        kb_atoms_found: int = 0
    ) -> int:
        """
        Log KB gap to gap_requests table (NEW SCHEMA for autonomous ingestion).
        Increments request_count and updates priority if query seen before (within 7 days).

        Args:
            query: Original user query
            intent: Parsed RivetIntent with vendor, equipment, symptom
            search_filters: Filters used in KB search
            user_id: User identifier (Telegram user_id, etc.)
            route: Route taken (A/B/C/D)
            confidence: Confidence score from routing
            kb_atoms_found: Number of KB atoms found (0 for Route C)

        Returns:
            gap_id: ID of the logged gap record
        """
        try:
            # Extract equipment identifier for deduplication and queuing
            equipment_detected = None
            if intent:
                vendor_str = intent.vendor.value if intent.vendor else "unknown"
                equipment_str = intent.equipment_type.value if intent.equipment_type else "unknown"
                equipment_detected = f"{vendor_str}:{equipment_str}"

            # Check if duplicate gap within 7 days (same equipment)
            check_sql = """
                SELECT id, request_count FROM gap_requests
                WHERE equipment_detected = $1
                AND last_requested_at > NOW() - INTERVAL '7 days'
                AND ingestion_completed = FALSE
                ORDER BY last_requested_at DESC LIMIT 1
            """
            result = self.db.execute_query(check_sql, (equipment_detected,))

            if result:
                # Increment request_count and update priority for existing gap
                gap_id, req_count = result[0]
                new_count = req_count + 1
                new_priority = min(new_count * 10 + confidence * 100, 100.0)

                update_sql = """
                    UPDATE gap_requests
                    SET request_count = $1, priority_score = $2, last_requested_at = NOW()
                    WHERE id = $3
                """
                self.db.execute_query(update_sql, (new_count, new_priority, gap_id), fetch_mode="none")
                logger.info(
                    f"Incremented gap request: gap_id={gap_id}, "
                    f"request_count={new_count}, priority={new_priority:.1f}"
                )
                return gap_id
            else:
                # New gap - insert record to gap_requests table
                initial_priority = 50.0 + confidence * 10  # Base 50 + confidence boost
                insert_sql = """
                    INSERT INTO gap_requests (
                        user_id, query_text, equipment_detected, route,
                        confidence, kb_atoms_found, priority_score
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """
                result = self.db.execute_query(
                    insert_sql,
                    (
                        int(user_id) if user_id and user_id.isdigit() else 0,  # Convert to BIGINT
                        query,
                        equipment_detected,
                        route,
                        confidence,
                        kb_atoms_found,
                        initial_priority
                    )
                )
                gap_id = result[0][0]
                logger.info(
                    f"Logged new gap request: gap_id={gap_id}, "
                    f"equipment={equipment_detected}, query='{query[:50]}...', "
                    f"priority={initial_priority:.1f}"
                )
                return gap_id

        except Exception as e:
            logger.error(f"Failed to log gap request: {e}", exc_info=True)
            # Return -1 to indicate failure (caller can check)
            return -1

    async def log_gap_async(self, gap_entry: Dict) -> Optional[int]:
        """
        Async version of log_gap for use in orchestrator.

        Args:
            gap_entry: Dictionary with gap information:
                - user_query: Original user query
                - vendor: Vendor string (e.g., "siemens", "rockwell")
                - equipment_type: Equipment type string
                - symptom: Symptom or description
                - route: Route taken (e.g., "B_sme_enrich", "C_research")
                - confidence: Confidence score
                - kb_coverage: KB coverage level string
                - atom_count: Number of atoms found
                - avg_relevance: Average relevance score
                - priority_score: Priority score for processing
                - enrichment_type: Type of enrichment ("thin_coverage" or "no_coverage")

        Returns:
            gap_id: ID of the logged gap record, or None on failure
        """
        try:
            # Extract fields from gap_entry
            user_query = gap_entry.get("user_query", "")
            vendor_str = gap_entry.get("vendor", "unknown")
            equipment_str = gap_entry.get("equipment_type", "unknown")
            route = gap_entry.get("route", "C")
            confidence = gap_entry.get("confidence", 0.0)
            atom_count = gap_entry.get("atom_count", 0)
            priority_score = gap_entry.get("priority_score", 50)
            enrichment_type = gap_entry.get("enrichment_type", "no_coverage")

            # Build equipment_detected string
            equipment_detected = f"{vendor_str}:{equipment_str}"

            # Check for duplicate gap within 7 days
            check_sql = """
                SELECT id, request_count FROM gap_requests
                WHERE equipment_detected = $1
                AND last_requested_at > NOW() - INTERVAL '7 days'
                AND ingestion_completed = FALSE
                ORDER BY last_requested_at DESC LIMIT 1
            """

            result = await asyncio.to_thread(
                self.db.execute_query, check_sql, (equipment_detected,)
            )

            if result:
                # Increment request_count for existing gap
                gap_id, req_count = result[0]
                new_count = req_count + 1
                new_priority = min(new_count * 10 + confidence * 100, 100.0)

                update_sql = """
                    UPDATE gap_requests
                    SET request_count = $1, priority_score = $2, last_requested_at = NOW()
                    WHERE id = $3
                """
                await asyncio.to_thread(
                    self.db.execute_query, update_sql, (new_count, new_priority, gap_id), fetch_mode="none"
                )
                logger.info(
                    f"Incremented gap request: gap_id={gap_id}, "
                    f"enrichment_type={enrichment_type}, "
                    f"request_count={new_count}, priority={new_priority:.1f}"
                )
                return gap_id
            else:
                # New gap - insert record with enrichment_type
                insert_sql = """
                    INSERT INTO gap_requests (
                        user_id, query_text, equipment_detected, route,
                        confidence, kb_atoms_found, priority_score, enrichment_type
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """
                result = await asyncio.to_thread(
                    self.db.execute_query,
                    insert_sql,
                    (
                        0,  # user_id - will be set by orchestrator context
                        user_query,
                        equipment_detected,
                        route,
                        confidence,
                        atom_count,
                        priority_score,
                        enrichment_type
                    )
                )
                gap_id = result[0][0]
                logger.info(
                    f"Logged new enrichment gap: gap_id={gap_id}, "
                    f"type={enrichment_type}, equipment={equipment_detected}, "
                    f"query='{user_query[:50]}...', priority={priority_score:.1f}"
                )
                return gap_id

        except Exception as e:
            logger.error(f"Failed to log enrichment gap: {e}", exc_info=True)
            return None

    def mark_resolved(self, gap_id: int, atom_ids: list[str]) -> bool:
        """
        Mark gap as resolved after atoms ingested.

        Args:
            gap_id: ID of the gap to mark resolved
            atom_ids: List of atom IDs that resolved this gap

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sql = """
                UPDATE kb_gaps
                SET resolved = TRUE, resolved_at = NOW(), resolution_atom_ids = %s
                WHERE id = %s
            """
            self.db.execute_query(sql, (atom_ids, gap_id))
            logger.info(f"Marked KB gap resolved: gap_id={gap_id}, atoms={len(atom_ids)}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark gap resolved: {e}", exc_info=True)
            return False

    def get_top_gaps(self, limit: int = 10, resolved: bool = False) -> list[dict]:
        """
        Get top unresolved gaps by frequency.

        Args:
            limit: Maximum number of gaps to return
            resolved: If True, return resolved gaps; if False, return unresolved

        Returns:
            List of gap dictionaries with id, query, frequency, vendor, equipment
        """
        try:
            sql = """
                SELECT id, query, frequency, intent_vendor, intent_equipment, triggered_at, last_asked_at
                FROM kb_gaps
                WHERE resolved = %s
                ORDER BY frequency DESC, last_asked_at DESC
                LIMIT %s
            """
            result = self.db.execute_query(sql, (resolved, limit))
            return [
                {
                    "id": row[0],
                    "query": row[1],
                    "frequency": row[2],
                    "vendor": row[3],
                    "equipment": row[4],
                    "triggered_at": row[5].isoformat() if row[5] else None,
                    "last_asked_at": row[6].isoformat() if row[6] else None
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Failed to get top gaps: {e}", exc_info=True)
            return []

    def get_gap_stats(self) -> dict:
        """
        Get overall KB gap statistics.

        Returns:
            Dictionary with total gaps, resolved count, resolution rate, avg frequency
        """
        try:
            sql = """
                SELECT
                    COUNT(*) as total_gaps,
                    COUNT(*) FILTER (WHERE resolved = TRUE) as resolved_count,
                    COUNT(*) FILTER (WHERE resolved = FALSE) as unresolved_count,
                    AVG(frequency) as avg_frequency,
                    AVG(EXTRACT(EPOCH FROM (resolved_at - triggered_at))/3600) as avg_resolution_hours
                FROM kb_gaps
            """
            result = self.db.execute_query(sql)
            if result:
                row = result[0]
                total = row[0] or 0
                resolved = row[1] or 0
                return {
                    "total_gaps": total,
                    "resolved_count": resolved,
                    "unresolved_count": row[2] or 0,
                    "resolution_rate": (resolved / total * 100) if total > 0 else 0.0,
                    "avg_frequency": float(row[3]) if row[3] else 0.0,
                    "avg_resolution_hours": float(row[4]) if row[4] else None
                }
            return {
                "total_gaps": 0,
                "resolved_count": 0,
                "unresolved_count": 0,
                "resolution_rate": 0.0,
                "avg_frequency": 0.0,
                "avg_resolution_hours": None
            }
        except Exception as e:
            logger.error(f"Failed to get gap stats: {e}", exc_info=True)
            return {}
