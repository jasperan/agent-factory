#!/usr/bin/env python3
"""
Test KB Weakness Detection System

Tests the Phoenix trace analyzer in monitoring mode.
Runs a single analysis cycle and prints results.

Usage:
    python scripts/test_kb_weakness_detection.py
"""

import os
import sys
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_factory.observability.phoenix_trace_analyzer import PhoenixTraceAnalyzer, WeaknessType
from agent_factory.observability.kb_feedback_monitor import KBFeedbackMonitor
from agent_factory.core.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_weakness_details(weakness):
    """Print formatted weakness details."""
    print(f"\n  Weakness Type: {weakness.weakness_type.value}")
    print(f"  Priority: {weakness.priority_score} ", end="")

    if weakness.priority_score >= 90:
        print("(CRITICAL)")
    elif weakness.priority_score >= 70:
        print("(HIGH)")
    elif weakness.priority_score >= 40:
        print("(MEDIUM)")
    else:
        print("(LOW)")

    print(f"  Equipment: {weakness.equipment_detected}")
    print(f"  Query: {weakness.query_text[:100]}...")
    print(f"  Atoms Found: {weakness.atoms_found}")
    print(f"  Confidence: {weakness.confidence:.2f}")

    if weakness.relevance_scores:
        top_score = max(weakness.relevance_scores)
        print(f"  Top Relevance: {top_score:.2f}")

    if "latency_ms" in weakness.context:
        print(f"  Latency: {weakness.context['latency_ms']}ms")


async def main():
    print("=" * 70)
    print("KB WEAKNESS DETECTION TEST")
    print("=" * 70)
    print()

    # Initialize analyzer
    phoenix_url = os.getenv("PHOENIX_URL", "http://localhost:6006")
    analyzer = PhoenixTraceAnalyzer(phoenix_url=phoenix_url)

    print(f"Phoenix URL: {phoenix_url}")
    print(f"Looking back: 5 minutes")
    print()

    # Analyze recent traces
    print("[1/3] Polling Phoenix for recent traces...")
    all_weaknesses = analyzer.analyze_recent_traces(lookback_minutes=5)

    print(f"Found {len(all_weaknesses)} total weaknesses\n")

    if not all_weaknesses:
        print("No weaknesses detected!")
        print()
        print("Possible reasons:")
        print("  - Phoenix has no recent traces")
        print("  - All traces show good KB coverage")
        print("  - Phoenix is not running at", phoenix_url)
        print()
        print("Try:")
        print("  1. Run: python phoenix_integration/test_phoenix_traces.py")
        print("  2. Then run this script again")
        return

    # Group weaknesses by type
    by_type = {}
    for weakness in all_weaknesses:
        weakness_type = weakness.weakness_type.value
        if weakness_type not in by_type:
            by_type[weakness_type] = []
        by_type[weakness_type].append(weakness)

    print("[2/3] Weakness Summary:")
    print()
    for weakness_type, weaknesses in sorted(by_type.items()):
        count = len(weaknesses)
        print(f"  {weakness_type}: {count} detected")

        # Show details for first weakness of each type
        if weaknesses:
            print_weakness_details(weaknesses[0])

    # Show what would be triggered in production
    print()
    print("[3/3] Production Mode Simulation:")
    print()

    critical_high = [w for w in all_weaknesses if w.priority_score >= 70]
    medium = [w for w in all_weaknesses if 40 <= w.priority_score < 70]
    low = [w for w in all_weaknesses if w.priority_score < 40]

    print(f"  CRITICAL/HIGH (immediate research): {len(critical_high)}")
    print(f"  MEDIUM (hourly batch): {len(medium)}")
    print(f"  LOW (daily batch): {len(low)}")
    print()

    if critical_high:
        print("  Immediate Research Triggers:")
        for weakness in critical_high[:3]:  # Show first 3
            print(f"    - {weakness.equipment_detected}: {weakness.weakness_type.value} (priority={weakness.priority_score})")

    # Check for DB feedback monitor
    print()
    print("[BONUS] KB Health Check:")
    try:
        db = DatabaseManager()
        monitor = KBFeedbackMonitor(db)

        completion = monitor.get_completion_rate(7)
        if completion:
            print(f"  7-day Completion Rate: {completion['completion_rate']:.1f}%")
            print(f"  Open Gaps: {completion['in_progress'] + completion['not_started']}")

        stuck = monitor.get_stuck_gaps(24)
        if stuck:
            print(f"  [WARNING] {len(stuck)} stuck gaps (>24 hours)")

    except Exception as e:
        print(f"  (Could not load health stats: {e})")

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("  1. Review detected weaknesses above")
    print("  2. To run in production:")
    print("     python scripts/services/phoenix_analyzer_service.py")
    print("  3. To enable monitoring mode (no auto-research):")
    print("     MONITORING_MODE=true python scripts/services/phoenix_analyzer_service.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())
