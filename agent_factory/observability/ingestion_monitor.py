"""
Knowledge Base Ingestion Monitor.

Tracks the 7-stage ingestion pipeline in real-time with metrics collection,
background database writes, Telegram notifications, and query capabilities.

Architecture:
- Async background writer (queue pattern) - <5ms overhead per stage
- Batch writes (50 records OR 5 seconds interval)
- Multi-tier fallback (PostgreSQL → file logging)
- Thread-safe for concurrent ingestion sessions
- Optional Telegram notifications (VERBOSE or BATCH mode)

Database Table:
- ingestion_metrics_realtime (see docs/database/observability_migration.sql)

Example Usage (Basic):
    >>> from agent_factory.core.database_manager import DatabaseManager
    >>> from agent_factory.observability.ingestion_monitor import IngestionMonitor
    >>>
    >>> db = DatabaseManager()
    >>> monitor = IngestionMonitor(db)
    >>>
    >>> async with monitor.track_ingestion("https://example.com/manual.pdf", "pdf") as session:
    ...     session.record_stage("acquisition", 120, True)
    ...     session.record_stage("extraction", 80, True)
    ...     session.finish(5, 0)

Example Usage (With Telegram Notifications):
    >>> from agent_factory.core.database_manager import DatabaseManager
    >>> from agent_factory.observability import IngestionMonitor, TelegramNotifier
    >>> import os
    >>>
    >>> # Initialize notifier
    >>> notifier = TelegramNotifier(
    ...     bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
    ...     chat_id=8445149012,
    ...     mode="VERBOSE"  # or "BATCH"
    ... )
    >>>
    >>> # Initialize monitor with notifier
    >>> db = DatabaseManager()
    >>> monitor = IngestionMonitor(db, telegram_notifier=notifier)
    >>>
    >>> async with monitor.track_ingestion("https://example.com/manual.pdf", "pdf") as session:
    ...     session.record_stage("acquisition", 120, True)
    ...     session.finish(5, 0)  # Telegram notification sent automatically
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


# ============================================================================
# Stage Name Mapping
# ============================================================================

STAGE_MAPPING = {
    "acquisition": "stage_1_acquisition_ms",
    "extraction": "stage_2_extraction_ms",
    "chunking": "stage_3_chunking_ms",
    "generation": "stage_4_generation_ms",
    "validation": "stage_5_validation_ms",
    "embedding": "stage_6_embedding_ms",
    "storage": "stage_7_storage_ms"
}


# ============================================================================
# Ingestion Session
# ============================================================================

class IngestionSession:
    """
    Tracks a single ingestion session through the 7-stage pipeline.

    Usage:
        async with monitor.track_ingestion(url, source_type) as session:
            session.record_stage("acquisition", 120, True)
            session.finish(atoms_created=5, atoms_failed=0)
    """

    def __init__(self, session_id: str, url: str, source_type: str, monitor: "IngestionMonitor"):
        """
        Initialize ingestion session.

        Args:
            session_id: Unique session identifier (UUID)
            url: Source URL being ingested
            source_type: Type of source ("web", "pdf", "youtube")
            monitor: Parent IngestionMonitor instance
        """
        self.session_id = session_id
        self.url = url
        self.source_type = source_type
        self.monitor = monitor

        # Track state
        self.started_at = datetime.utcnow()
        self.stage_timings: Dict[str, int] = {}  # stage_name → duration_ms
        self.metadata: Dict[str, Any] = {}  # vendor, equipment_type, etc.
        self.error_stage: Optional[str] = None
        self.error_message: Optional[str] = None
        self.atoms_created = 0
        self.atoms_failed = 0
        self.chunks_processed = 0
        self.completed = False

    def record_stage(
        self,
        stage_name: str,
        duration_ms: int,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record completion of a pipeline stage.

        Args:
            stage_name: Stage identifier ("acquisition", "extraction", etc.)
            duration_ms: Time taken in milliseconds
            success: Whether stage succeeded
            metadata: Optional metadata (vendor, equipment_type, quality_score, etc.)
        """
        # Map stage name to database column
        if stage_name not in STAGE_MAPPING:
            logger.warning(f"Unknown stage name: {stage_name}")
            return

        # Store timing
        self.stage_timings[stage_name] = duration_ms

        # Store metadata
        if metadata:
            self.metadata.update(metadata)

        # Track errors
        if not success:
            self.error_stage = stage_name
            self.error_message = metadata.get("error_message") if metadata else None

        logger.debug(
            f"[{self.session_id}] Stage {stage_name}: {duration_ms}ms "
            f"(success={success})"
        )

    def finish(
        self,
        atoms_created: int,
        atoms_failed: int,
        error: Optional[str] = None
    ):
        """
        Mark session complete and queue for database write.

        Args:
            atoms_created: Number of atoms successfully created
            atoms_failed: Number of atoms that failed validation
            error: Error message if ingestion failed
        """
        self.atoms_created = atoms_created
        self.atoms_failed = atoms_failed

        if error:
            self.error_message = error

        self.completed = True

        logger.info(
            f"[{self.session_id}] Session complete: "
            f"{atoms_created} atoms created, {atoms_failed} failed"
        )

    async def __aenter__(self):
        """Context manager entry - start timing."""
        self.started_at = datetime.utcnow()
        logger.debug(f"[{self.session_id}] Session started: {self.url}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - queue for database write and send Telegram notification."""
        # If exception occurred and not already finished, record error
        if exc_type and not self.completed:
            self.error_message = str(exc_val)
            self.error_stage = "unknown"

        # Calculate status
        if self.atoms_created > 0 and self.atoms_failed == 0:
            status = "success"
        elif self.atoms_created > 0 and self.atoms_failed > 0:
            status = "partial"
        else:
            status = "failed"

        # Build metric record
        metric = self._build_metric_record(status)

        # Queue for batch write
        await self.monitor._queue_write(metric)

        logger.debug(f"[{self.session_id}] Session queued for write (status={status})")

        # Send Telegram notification (if notifier configured)
        if self.monitor.notifier:
            try:
                total_duration_ms = sum(self.stage_timings.values())

                if self.monitor.notifier.mode == "VERBOSE":
                    # Send immediate notification
                    await self.monitor.notifier.notify_ingestion_complete(
                        source_url=self.url,
                        atoms_created=self.atoms_created,
                        atoms_failed=self.atoms_failed,
                        duration_ms=total_duration_ms,
                        vendor=self.metadata.get("vendor"),
                        quality_score=self.metadata.get("avg_quality_score"),
                        status=status
                    )
                else:  # BATCH mode
                    # Queue for batch summary
                    await self.monitor.notifier.queue_for_batch({
                        "source_url": self.url,
                        "atoms_created": self.atoms_created,
                        "atoms_failed": self.atoms_failed,
                        "duration_ms": total_duration_ms,
                        "vendor": self.metadata.get("vendor"),
                        "quality_score": self.metadata.get("avg_quality_score"),
                        "status": status
                    })
            except Exception as e:
                # Never let notification failures break the pipeline
                logger.error(f"[{self.session_id}] Telegram notification failed: {e}")

        # Don't suppress exceptions
        return False

    def _build_metric_record(self, status: str) -> Dict[str, Any]:
        """Build database record from session data."""
        # Calculate total duration
        total_duration_ms = sum(self.stage_timings.values())

        # Hash URL for deduplication
        url_hash = hashlib.sha256(self.url.encode()).hexdigest()[:16]

        # Build record
        record = {
            "source_url": self.url,
            "source_type": self.source_type,
            "source_hash": url_hash,
            "status": status,
            "atoms_created": self.atoms_created,
            "atoms_failed": self.atoms_failed,
            "chunks_processed": self.chunks_processed,
            "total_duration_ms": total_duration_ms,
            "started_at": self.started_at,
            "completed_at": datetime.utcnow(),
            "error_stage": self.error_stage,
            "error_message": self.error_message[:500] if self.error_message else None,
            "vendor": self.metadata.get("vendor"),
            "equipment_type": self.metadata.get("equipment_type"),
            "avg_quality_score": self.metadata.get("avg_quality_score"),
            "quality_pass_rate": self.metadata.get("quality_pass_rate")
        }

        # Add stage timings
        for stage_name, column_name in STAGE_MAPPING.items():
            record[column_name] = self.stage_timings.get(stage_name, 0)

        return record


# ============================================================================
# Ingestion Monitor
# ============================================================================

class IngestionMonitor:
    """
    Real-time ingestion pipeline monitor with async background writes.

    Features:
    - Tracks 7-stage pipeline metrics
    - Async background writer (queue pattern)
    - Batch database writes (50 records OR 5s interval)
    - Query methods for dashboards/Telegram
    - Graceful degradation (PostgreSQL → file logging)

    Example:
        >>> db = DatabaseManager()
        >>> monitor = IngestionMonitor(db)
        >>>
        >>> async with monitor.track_ingestion(url, "pdf") as session:
        ...     session.record_stage("acquisition", 120, True)
        ...     session.finish(5, 0)
    """

    def __init__(self, db_manager, telegram_notifier=None):
        """
        Initialize monitor with database connection and optional Telegram notifier.

        Args:
            db_manager: DatabaseManager instance
            telegram_notifier: Optional TelegramNotifier for real-time notifications
        """
        self.db = db_manager
        self.notifier = telegram_notifier

        # Background writer queue
        self._write_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._writer_task: Optional[asyncio.Task] = None
        self._shutdown = False

        # Failover logging
        self._failover_log_path = Path("data/observability/failed_metrics.jsonl")
        self._failover_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Stats tracking
        self._total_writes = 0
        self._failed_writes = 0

        # Start background writer
        self._start_background_writer()

        notifier_status = "enabled" if telegram_notifier else "disabled"
        logger.info(f"IngestionMonitor initialized with background writer (notifier={notifier_status})")

    def _start_background_writer(self):
        """Start the background writer task."""
        loop = asyncio.get_event_loop()
        self._writer_task = loop.create_task(self._background_writer())
        logger.debug("Background writer task started")

    async def _background_writer(self):
        """
        Background task that batches and writes metrics to database.

        Flushes every:
        - 50 records accumulated, OR
        - 5 seconds elapsed (whichever comes first)
        """
        batch: List[Dict[str, Any]] = []
        last_flush = time.time()
        flush_interval = 5.0  # seconds
        batch_size = 50

        logger.debug("Background writer running")

        while not self._shutdown:
            try:
                # Wait for next metric (with timeout for periodic flush)
                try:
                    metric = await asyncio.wait_for(
                        self._write_queue.get(),
                        timeout=flush_interval
                    )
                    batch.append(metric)
                except asyncio.TimeoutError:
                    # Timeout elapsed - flush if batch has data
                    pass

                # Flush conditions
                should_flush = (
                    len(batch) >= batch_size or
                    (time.time() - last_flush) >= flush_interval
                )

                if should_flush and batch:
                    await self._write_batch(batch)
                    batch.clear()
                    last_flush = time.time()

            except Exception as e:
                logger.error(f"Background writer error: {e}", exc_info=True)
                await asyncio.sleep(1)  # Backoff on error

        # Flush remaining records on shutdown
        if batch:
            await self._write_batch(batch)

        logger.debug("Background writer stopped")

    async def _write_batch(self, batch: List[Dict[str, Any]]):
        """
        Write batch of metrics to database.

        Args:
            batch: List of metric records to write
        """
        if not batch:
            return

        try:
            # Build INSERT query (batch)
            values_list = []
            for record in batch:
                values_list.append((
                    record["source_url"],
                    record["source_type"],
                    record["source_hash"],
                    record["status"],
                    record["atoms_created"],
                    record["atoms_failed"],
                    record["chunks_processed"],
                    record.get("avg_quality_score"),
                    record.get("quality_pass_rate"),
                    record.get("stage_1_acquisition_ms", 0),
                    record.get("stage_2_extraction_ms", 0),
                    record.get("stage_3_chunking_ms", 0),
                    record.get("stage_4_generation_ms", 0),
                    record.get("stage_5_validation_ms", 0),
                    record.get("stage_6_embedding_ms", 0),
                    record.get("stage_7_storage_ms", 0),
                    record["total_duration_ms"],
                    record.get("error_stage"),
                    record.get("error_message"),
                    record.get("vendor"),
                    record.get("equipment_type"),
                    record["started_at"],
                    record["completed_at"]
                ))

            # Execute batch insert
            query = """
                INSERT INTO ingestion_metrics_realtime (
                    source_url, source_type, source_hash, status,
                    atoms_created, atoms_failed, chunks_processed,
                    avg_quality_score, quality_pass_rate,
                    stage_1_acquisition_ms, stage_2_extraction_ms, stage_3_chunking_ms,
                    stage_4_generation_ms, stage_5_validation_ms, stage_6_embedding_ms,
                    stage_7_storage_ms, total_duration_ms,
                    error_stage, error_message, vendor, equipment_type,
                    started_at, completed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23)
            """

            # Execute each record in thread pool (database calls are sync)
            loop = asyncio.get_event_loop()
            for values in values_list:
                await loop.run_in_executor(
                    None,
                    self.db.execute_query,
                    query,
                    values,
                    "none"  # fetch_mode - we don't need results from INSERT
                )

            self._total_writes += len(batch)
            logger.debug(f"Wrote batch of {len(batch)} metrics to database")

        except Exception as e:
            logger.error(f"Batch write failed: {e}", exc_info=True)
            self._failed_writes += len(batch)

            # Failover: Write to file
            await self._write_to_failover_log(batch)

            # Alert if failure rate is high
            if self._total_writes > 0:
                failure_rate = self._failed_writes / (self._total_writes + self._failed_writes)
                if failure_rate > 0.1:  # >10% failure rate
                    logger.warning(
                        f"High write failure rate: {failure_rate:.1%} "
                        f"({self._failed_writes}/{self._total_writes + self._failed_writes})"
                    )

    async def _write_to_failover_log(self, batch: List[Dict[str, Any]]):
        """Write failed batch to JSONL file for later retry."""
        try:
            with open(self._failover_log_path, "a") as f:
                for record in batch:
                    # Convert datetime to ISO format for JSON
                    record_json = {
                        **record,
                        "started_at": record["started_at"].isoformat() if record.get("started_at") else None,
                        "completed_at": record["completed_at"].isoformat() if record.get("completed_at") else None
                    }
                    f.write(json.dumps(record_json) + "\n")

            logger.info(f"Wrote {len(batch)} metrics to failover log: {self._failover_log_path}")

        except Exception as e:
            logger.error(f"Failover log write failed: {e}")

    async def _queue_write(self, metric: Dict[str, Any]):
        """
        Queue metric for background write.

        Args:
            metric: Metric record to write
        """
        try:
            self._write_queue.put_nowait(metric)
        except asyncio.QueueFull:
            logger.warning("Write queue full, dropping metric")

    def track_ingestion(self, url: str, source_type: str) -> IngestionSession:
        """
        Create an ingestion session context manager.

        Args:
            url: Source URL being ingested
            source_type: Type of source ("web", "pdf", "youtube")

        Returns:
            IngestionSession context manager

        Example:
            >>> async with monitor.track_ingestion(url, "pdf") as session:
            ...     session.record_stage("acquisition", 120, True)
            ...     session.finish(5, 0)
        """
        session_id = str(uuid.uuid4())[:8]
        return IngestionSession(session_id, url, source_type, self)

    def get_recent_metrics(
        self,
        hours: int = 24,
        vendor: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query recent ingestion metrics.

        Args:
            hours: Number of hours to look back (default: 24)
            vendor: Filter by equipment vendor (optional)
            status: Filter by status ("success", "partial", "failed") (optional)

        Returns:
            List of metric records

        Example:
            >>> metrics = monitor.get_recent_metrics(hours=6, vendor="Siemens")
            >>> for m in metrics:
            ...     print(f"{m['source_url']}: {m['atoms_created']} atoms")
        """
        # Build query with filters
        query_parts = [
            "SELECT * FROM ingestion_metrics_realtime",
            f"WHERE completed_at > NOW() - INTERVAL '{hours} hours'"
        ]

        params = []
        param_idx = 1

        if vendor:
            query_parts.append(f"AND vendor = ${param_idx}")
            params.append(vendor)
            param_idx += 1

        if status:
            query_parts.append(f"AND status = ${param_idx}")
            params.append(status)
            param_idx += 1

        query_parts.append("ORDER BY completed_at DESC")
        query_parts.append("LIMIT 100")

        query = " ".join(query_parts)

        try:
            results = self.db.execute_query(query, *params)
            return results if results else []

        except Exception as e:
            logger.error(f"Failed to query recent metrics: {e}")
            return []

    def get_stats_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for dashboard/Telegram.

        Returns:
            Dictionary with aggregate stats:
            {
                "total_sources": 1234,
                "success_rate": 0.92,
                "avg_duration_ms": 8500,
                "atoms_created": 15678,
                "last_ingestion": "2025-12-25T10:30:00Z",
                "active_vendors": ["Siemens", "Rockwell", "Mitsubishi"]
            }

        Example:
            >>> stats = monitor.get_stats_summary()
            >>> print(f"Success rate: {stats['success_rate']:.1%}")
        """
        try:
            # Query last 24 hours
            query = """
                SELECT
                    COUNT(*) as total_sources,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    AVG(total_duration_ms) as avg_duration_ms,
                    SUM(atoms_created) as atoms_created,
                    MAX(completed_at) as last_ingestion,
                    ARRAY_AGG(DISTINCT vendor) FILTER (WHERE vendor IS NOT NULL) as vendors
                FROM ingestion_metrics_realtime
                WHERE completed_at > NOW() - INTERVAL '24 hours'
            """

            result = self.db.execute_query(query)

            if not result:
                return {
                    "total_sources": 0,
                    "success_rate": 0.0,
                    "avg_duration_ms": 0,
                    "atoms_created": 0,
                    "last_ingestion": None,
                    "active_vendors": []
                }

            row = result[0]

            return {
                "total_sources": row[0] or 0,
                "success_rate": (row[1] / row[0]) if row[0] and row[0] > 0 else 0.0,
                "avg_duration_ms": int(row[2]) if row[2] else 0,
                "atoms_created": row[3] or 0,
                "last_ingestion": row[4].isoformat() if row[4] else None,
                "active_vendors": row[5] or []
            }

        except Exception as e:
            logger.error(f"Failed to get stats summary: {e}")
            return {
                "total_sources": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0,
                "atoms_created": 0,
                "last_ingestion": None,
                "active_vendors": [],
                "error": str(e)
            }

    async def shutdown(self):
        """Gracefully shutdown the background writer."""
        logger.info("Shutting down IngestionMonitor...")
        self._shutdown = True

        if self._writer_task:
            await self._writer_task

        logger.info("IngestionMonitor shutdown complete")
