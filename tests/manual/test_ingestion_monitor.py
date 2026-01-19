"""
Quick test script for IngestionMonitor.

Tests:
1. Session tracking
2. Stage recording
3. Database write
4. Stats query
"""

import asyncio
import sys
from agent_factory.core.database_manager import DatabaseManager
from agent_factory.observability.ingestion_monitor import IngestionMonitor


async def main():
    print("=" * 60)
    print("IngestionMonitor Test")
    print("=" * 60)

    # Initialize monitor
    print("\n[1] Initializing monitor...")
    db = DatabaseManager()
    monitor = IngestionMonitor(db)
    print("    Monitor initialized successfully")

    # Create test session
    print("\n[2] Creating test session...")
    async with monitor.track_ingestion('https://example.com/test-manual.pdf', 'pdf') as session:
        print("    Session started")

        # Record stages
        print("\n[3] Recording stages...")
        session.record_stage('acquisition', 120, True)
        print("    Stage 1 (acquisition): 120ms")

        session.record_stage('extraction', 80, True)
        print("    Stage 2 (extraction): 80ms")

        session.record_stage('chunking', 50, True, metadata={'vendor': 'Siemens'})
        print("    Stage 3 (chunking): 50ms + vendor metadata")

        session.record_stage('generation', 200, True)
        print("    Stage 4 (generation): 200ms")

        session.record_stage('validation', 100, True, metadata={'avg_quality_score': 0.85})
        print("    Stage 5 (validation): 100ms + quality score")

        session.record_stage('embedding', 150, True)
        print("    Stage 6 (embedding): 150ms")

        session.record_stage('storage', 60, True)
        print("    Stage 7 (storage): 60ms")

        # Finish session
        print("\n[4] Finishing session...")
        session.finish(atoms_created=5, atoms_failed=0)
        print("    Session marked complete (5 atoms created, 0 failed)")

    print("\n[5] Session queued for background write...")

    # Wait for background writer to flush (5 second interval)
    print("\n[6] Waiting for background writer to flush (6 seconds)...")
    await asyncio.sleep(6)

    print("\n[7] Querying stats...")
    stats = monitor.get_stats_summary()
    print(f"    Total sources: {stats['total_sources']}")
    print(f"    Success rate: {stats['success_rate']:.1%}")
    print(f"    Avg duration: {stats['avg_duration_ms']}ms")
    print(f"    Atoms created: {stats['atoms_created']}")
    print(f"    Active vendors: {stats['active_vendors']}")

    # Shutdown monitor
    print("\n[8] Shutting down monitor...")
    await monitor.shutdown()
    print("    Monitor shutdown complete")

    print("\n" + "=" * 60)
    print("TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
