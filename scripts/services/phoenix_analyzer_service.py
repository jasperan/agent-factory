#!/usr/bin/env python3
"""
Phoenix Trace Analyzer Background Service

Polls Phoenix every 5 minutes, detects KB weaknesses, triggers research.

Run as:
  python scripts/services/phoenix_analyzer_service.py

Or with systemd/supervisor for production.

Environment Variables:
  PHOENIX_URL - Phoenix server URL (default: http://localhost:6006)
  POLL_INTERVAL_SECONDS - Polling interval (default: 300 = 5 minutes)
  MONITORING_MODE - If "true", only log weaknesses (no research triggers)
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent_factory.observability.phoenix_trace_analyzer import PhoenixTraceAnalyzer
from agent_factory.core.kb_gap_logger import KBGapLogger
from agent_factory.core.database_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def analyzer_loop():
    """Main analyzer loop - runs every N seconds."""

    # Configuration
    phoenix_url = os.getenv("PHOENIX_URL", "http://localhost:6006")
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))  # 5 minutes
    monitoring_mode = os.getenv("MONITORING_MODE", "false").lower() == "true"

    # Initialize components
    analyzer = PhoenixTraceAnalyzer(phoenix_url=phoenix_url)
    db = DatabaseManager()
    gap_logger = KBGapLogger(db)

    mode_str = "MONITORING MODE (no auto-research)" if monitoring_mode else "PRODUCTION MODE (auto-research enabled)"
    logger.info(f"Phoenix Analyzer Service started - {mode_str}")
    logger.info(f"Phoenix URL: {phoenix_url}")
    logger.info(f"Poll interval: {poll_interval} seconds")

    iteration = 0

    while True:
        try:
            iteration += 1
            logger.info(f"\n[Iteration {iteration}] Polling Phoenix for new traces...")

            # Poll traces from last 5 minutes
            traces = analyzer.poll_recent_traces(lookback_minutes=5)

            logger.info(f"Found {len(traces)} traces to analyze")

            total_weaknesses = 0
            weakness_summary = {}

            # Analyze each trace
            for trace in traces:
                weaknesses = analyzer.detect_weaknesses(trace)

                for weakness in weaknesses:
                    total_weaknesses += 1

                    # Count by weakness type
                    weakness_type = weakness.weakness_type.value
                    weakness_summary[weakness_type] = weakness_summary.get(weakness_type, 0) + 1

                    logger.info(
                        f"Weakness detected: {weakness_type} "
                        f"(priority={weakness.priority_score}, "
                        f"equipment={weakness.equipment_detected})"
                    )

                    if monitoring_mode:
                        # Monitoring mode - log only, don't trigger research
                        logger.info(
                            f"[MONITORING] Would trigger research for gap: "
                            f"query='{weakness.query_text[:50]}...', "
                            f"equipment={weakness.equipment_detected}"
                        )
                    else:
                        # Production mode - log to gap_requests (triggers research)
                        try:
                            gap_id = await gap_logger.log_weakness_signal(weakness)
                            if gap_id:
                                logger.info(
                                    f"[PRODUCTION] Logged gap: gap_id={gap_id}, "
                                    f"research triggered (priority={weakness.priority_score})"
                                )
                        except Exception as e:
                            logger.error(f"Failed to log weakness: {e}", exc_info=True)

            # Summary for this iteration
            if total_weaknesses > 0:
                logger.info(f"\nIteration {iteration} Summary:")
                logger.info(f"  Total weaknesses: {total_weaknesses}")
                for weakness_type, count in weakness_summary.items():
                    logger.info(f"  - {weakness_type}: {count}")
            else:
                logger.info(f"No weaknesses detected in iteration {iteration}")

            # Sleep until next poll
            logger.info(f"Sleeping for {poll_interval} seconds...\n")
            await asyncio.sleep(poll_interval)

        except KeyboardInterrupt:
            logger.info("\nShutting down Phoenix Analyzer Service...")
            break

        except Exception as e:
            logger.error(f"Analyzer loop error: {e}", exc_info=True)
            logger.info("Waiting 60 seconds before retry...")
            await asyncio.sleep(60)  # Wait 1 min on error


if __name__ == "__main__":
    print("=" * 70)
    print("PHOENIX TRACE ANALYZER SERVICE")
    print("=" * 70)
    print()
    print("Monitoring Phoenix for KB weaknesses...")
    print("Press Ctrl+C to stop")
    print()

    try:
        asyncio.run(analyzer_loop())
    except KeyboardInterrupt:
        print("\n\nService stopped")
        print("=" * 70)
