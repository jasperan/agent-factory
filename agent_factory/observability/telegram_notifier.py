"""
TelegramNotifier - Real-time KB ingestion notifications via Telegram.

Sends notifications when knowledge base ingestion completes.
Supports two modes:
- VERBOSE: Notify on every source completion (10-50 msg/hour)
- BATCH: 5-minute summaries (12 msg/hour)

Features:
- Quiet hours (11pm-7am) - no notifications during sleep
- Rate limiting (20 msg/min) - avoid Telegram API throttling
- Error tolerance - never crash the ingestion pipeline
- Graceful degradation - log failures, retry with backoff

Author: Agent Factory
Created: 2025-12-25
"""

import asyncio
import logging
from collections import deque
from datetime import datetime, time
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import time as time_module

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Send real-time Telegram notifications for KB ingestion events.

    Attributes:
        bot_token: Telegram bot token (from .env)
        chat_id: Admin chat ID to send notifications to
        mode: Notification mode ("VERBOSE" or "BATCH")
        quiet_hours_start: Hour to start quiet period (24h format)
        quiet_hours_end: Hour to end quiet period (24h format)

    Example:
        >>> notifier = TelegramNotifier(
        ...     bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
        ...     chat_id=8445149012,
        ...     mode="BATCH"
        ... )
        >>> await notifier.notify_ingestion_complete(
        ...     source_url="https://example.com/manual.pdf",
        ...     atoms_created=5,
        ...     atoms_failed=0,
        ...     duration_ms=760,
        ...     vendor="Siemens",
        ...     quality_score=0.85,
        ...     status="success"
        ... )
    """

    def __init__(
        self,
        bot_token: str,
        chat_id: int,
        mode: str = "BATCH",
        quiet_hours_start: int = 23,
        quiet_hours_end: int = 7
    ):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token (from .env)
            chat_id: Admin chat ID to send notifications to
            mode: Notification mode ("VERBOSE" or "BATCH")
            quiet_hours_start: Hour to start quiet period (24h format, default 11pm)
            quiet_hours_end: Hour to end quiet period (24h format, default 7am)

        Raises:
            ValueError: If mode is not "VERBOSE" or "BATCH"
        """
        if mode not in ("VERBOSE", "BATCH"):
            raise ValueError(f"Invalid mode: {mode}. Must be 'VERBOSE' or 'BATCH'")

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.mode = mode
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end

        # Rate limiting (token bucket algorithm)
        self._rate_limit_tokens = 20.0  # 20 messages per minute
        self._rate_limit_max = 20.0
        self._rate_limit_refill_rate = 20.0 / 60.0  # 20 per 60 seconds = 1/3 per second
        self._last_refill = time_module.time()

        # BATCH mode queue
        self._batch_queue: deque = deque(maxlen=1000)

        # Error tracking
        self._failed_sends_log = Path("data/observability/failed_telegram_sends.jsonl")
        self._failed_sends_log.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"TelegramNotifier initialized (mode={mode}, chat_id={chat_id})")

    async def notify_ingestion_complete(
        self,
        source_url: str,
        atoms_created: int,
        atoms_failed: int,
        duration_ms: int,
        vendor: Optional[str] = None,
        quality_score: Optional[float] = None,
        status: str = "success"
    ):
        """
        Send notification when ingestion completes (VERBOSE mode).

        Args:
            source_url: URL that was ingested
            atoms_created: Number of atoms created
            atoms_failed: Number of atoms that failed
            duration_ms: Total duration in milliseconds
            vendor: Equipment vendor (optional)
            quality_score: Average quality score (optional)
            status: Ingestion status ("success", "partial", "failed")
        """
        if self.mode != "VERBOSE":
            logger.debug(f"Skipping VERBOSE notification (mode={self.mode})")
            return

        # Check quiet hours
        if self._is_quiet_hours():
            logger.debug(f"Skipping notification (quiet hours)")
            return

        # Format message
        message = self._format_verbose_message(
            source_url=source_url,
            atoms_created=atoms_created,
            atoms_failed=atoms_failed,
            duration_ms=duration_ms,
            vendor=vendor,
            quality_score=quality_score,
            status=status
        )

        # Send message
        await self._send_message(message)

    async def queue_for_batch(self, session_data: Dict[str, Any]):
        """
        Queue session data for batch notification (BATCH mode).

        Args:
            session_data: Session metrics dictionary
        """
        if self.mode != "BATCH":
            logger.debug(f"Skipping BATCH queuing (mode={self.mode})")
            return

        self._batch_queue.append(session_data)
        logger.debug(f"Queued session for batch (queue_size={len(self._batch_queue)})")

    async def send_batch_summary(self):
        """
        Send 5-minute batch summary (called by background timer).

        Aggregates queued sessions and sends summary message.
        """
        if self.mode != "BATCH":
            logger.debug(f"Skipping BATCH summary (mode={self.mode})")
            return

        # Check if queue is empty
        if not self._batch_queue:
            logger.debug("Batch queue empty, skipping summary")
            return

        # Check quiet hours
        if self._is_quiet_hours():
            logger.debug("Skipping batch summary (quiet hours)")
            return

        # Aggregate stats
        sessions = list(self._batch_queue)
        stats = self._aggregate_batch_stats(sessions)

        # Format message
        message = self._format_batch_message(stats)

        # Send message
        await self._send_message(message)

        # Clear queue
        self._batch_queue.clear()
        logger.info(f"Sent batch summary ({stats['total_sources']} sources)")

    def _is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours."""
        now = datetime.now().time()
        start = time(hour=self.quiet_hours_start)
        end = time(hour=self.quiet_hours_end)

        # Handle overnight quiet hours (e.g., 11pm - 7am)
        if start > end:
            return now >= start or now < end
        else:
            return start <= now < end

    async def _send_message(self, text: str, parse_mode: str = "Markdown"):
        """
        Send message to Telegram with rate limiting.

        Args:
            text: Message text (supports Markdown)
            parse_mode: Message parse mode ("Markdown" or "HTML")
        """
        # Rate limiting (token bucket)
        await self._wait_for_rate_limit()

        # Import here to avoid startup dependency
        try:
            import httpx
        except ImportError:
            logger.error("httpx not installed. Run: poetry add httpx")
            self._log_failed_send(text, "httpx not installed")
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        # Retry logic (3 attempts with exponential backoff)
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    logger.debug(f"Telegram message sent successfully")
                    return
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limit hit - wait and retry
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    logger.warning(f"Telegram rate limit hit, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                else:
                    logger.error(f"Telegram API error (attempt {attempt+1}/3): {e}")
                    if attempt == 2:
                        self._log_failed_send(text, str(e))
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Failed to send Telegram message (attempt {attempt+1}/3): {e}")
                if attempt == 2:
                    self._log_failed_send(text, str(e))
                await asyncio.sleep(2 ** attempt)

    async def _wait_for_rate_limit(self):
        """Wait if rate limit tokens are exhausted (token bucket algorithm)."""
        # Refill tokens
        now = time_module.time()
        elapsed = now - self._last_refill
        self._rate_limit_tokens = min(
            self._rate_limit_max,
            self._rate_limit_tokens + elapsed * self._rate_limit_refill_rate
        )
        self._last_refill = now

        # Wait if no tokens available
        if self._rate_limit_tokens < 1.0:
            wait_time = (1.0 - self._rate_limit_tokens) / self._rate_limit_refill_rate
            logger.debug(f"Rate limit: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            self._rate_limit_tokens = 1.0

        # Consume token
        self._rate_limit_tokens -= 1.0

    def _format_verbose_message(
        self,
        source_url: str,
        atoms_created: int,
        atoms_failed: int,
        duration_ms: int,
        vendor: Optional[str],
        quality_score: Optional[float],
        status: str
    ) -> str:
        """Format VERBOSE mode message."""
        # Status indicator (ASCII-only for Windows compatibility)
        status_symbol = {
            "success": "[OK]",
            "partial": "[WARN]",
            "failed": "[FAIL]"
        }.get(status, "[INFO]")

        # Build message
        lines = [
            f"{status_symbol} *KB Ingestion {status.title()}*",
            "",
            f"*Source:* {source_url}",
            f"*Atoms:* {atoms_created} created, {atoms_failed} failed",
            f"*Duration:* {self._format_duration(duration_ms)}",
        ]

        if vendor:
            lines.append(f"*Vendor:* {vendor}")

        if quality_score is not None:
            lines.append(f"*Quality:* {quality_score:.0%}")

        lines.append(f"*Status:* {status}")
        lines.append("")
        lines.append(f"#ingestion #{status}")

        return "\n".join(lines)

    def _format_batch_message(self, stats: Dict[str, Any]) -> str:
        """Format BATCH mode message (ASCII-only for Windows compatibility)."""
        lines = [
            "[STATS] *KB Ingestion Summary* (Last 5 min)",
            "",
            f"*Sources:* {stats['total_sources']} processed",
            f"[OK] Success: {stats['success_count']} ({stats['success_rate']:.0%})",
        ]

        if stats['partial_count'] > 0:
            lines.append(f"[WARN] Partial: {stats['partial_count']} ({stats['partial_rate']:.0%})")

        if stats['failed_count'] > 0:
            lines.append(f"[FAIL] Failed: {stats['failed_count']} ({stats['failed_rate']:.0%})")

        lines.extend([
            "",
            f"*Atoms:* {stats['total_atoms_created']} created, {stats['total_atoms_failed']} failed",
            f"*Avg Duration:* {self._format_duration(stats['avg_duration_ms'])}",
        ])

        if stats['avg_quality_score'] is not None:
            lines.append(f"*Avg Quality:* {stats['avg_quality_score']:.0%}")

        if stats['top_vendors']:
            lines.append("")
            lines.append("*Top Vendors:*")
            for vendor, count in stats['top_vendors'][:3]:
                lines.append(f"  - {vendor} ({count} sources)")

        lines.append("")
        lines.append("#kb_summary #batch")

        return "\n".join(lines)

    def _aggregate_batch_stats(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate statistics from batch queue."""
        total = len(sessions)
        success = sum(1 for s in sessions if s.get("status") == "success")
        partial = sum(1 for s in sessions if s.get("status") == "partial")
        failed = sum(1 for s in sessions if s.get("status") == "failed")

        total_atoms_created = sum(s.get("atoms_created", 0) for s in sessions)
        total_atoms_failed = sum(s.get("atoms_failed", 0) for s in sessions)

        durations = [s.get("duration_ms", 0) for s in sessions if s.get("duration_ms")]
        avg_duration = sum(durations) // len(durations) if durations else 0

        quality_scores = [s.get("quality_score") for s in sessions if s.get("quality_score") is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

        # Count vendors
        vendor_counts: Dict[str, int] = {}
        for s in sessions:
            vendor = s.get("vendor")
            if vendor:
                vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1

        top_vendors = sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_sources": total,
            "success_count": success,
            "partial_count": partial,
            "failed_count": failed,
            "success_rate": success / total if total > 0 else 0,
            "partial_rate": partial / total if total > 0 else 0,
            "failed_rate": failed / total if total > 0 else 0,
            "total_atoms_created": total_atoms_created,
            "total_atoms_failed": total_atoms_failed,
            "avg_duration_ms": avg_duration,
            "avg_quality_score": avg_quality,
            "top_vendors": top_vendors
        }

    def _format_duration(self, ms: int) -> str:
        """Format milliseconds to human-readable duration."""
        if ms < 1000:
            return f"{ms}ms"
        elif ms < 60000:
            return f"{ms/1000:.1f}s"
        else:
            return f"{ms/60000:.1f}m"

    def _log_failed_send(self, message: str, error: str):
        """Log failed send to file for manual retry."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "chat_id": self.chat_id,
            "message": message[:200],  # First 200 chars
            "error": error
        }

        try:
            with open(self._failed_sends_log, "a") as f:
                f.write(json.dumps(record) + "\n")
            logger.warning(f"Logged failed send to {self._failed_sends_log}")
        except Exception as e:
            logger.error(f"Failed to log failed send: {e}")
