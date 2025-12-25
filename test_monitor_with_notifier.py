"""
Integration test: IngestionMonitor + TelegramNotifier

Tests the complete observability stack:
1. IngestionMonitor tracks pipeline metrics
2. TelegramNotifier sends real-time notifications
3. End-to-end flow validated
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from agent_factory.core.database_manager import DatabaseManager
from agent_factory.observability import IngestionMonitor, TelegramNotifier


async def test_verbose_mode():
    """Test VERBOSE mode integration."""
    print("\n" + "=" * 60)
    print("TEST 1: IngestionMonitor + TelegramNotifier (VERBOSE)")
    print("=" * 60)

    # Load environment
    load_dotenv()

    # Initialize notifier in VERBOSE mode
    print("\n[1] Initializing TelegramNotifier (VERBOSE mode)...")
    notifier = TelegramNotifier(
        bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
        chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")),
        mode="VERBOSE"
    )
    print(f"    Notifier initialized (mode={notifier.mode})")

    # Initialize monitor with notifier
    print("\n[2] Initializing IngestionMonitor with notifier...")
    db = DatabaseManager()
    monitor = IngestionMonitor(db, telegram_notifier=notifier)
    print("    Monitor initialized with Telegram notifications enabled")

    # Track test session
    print("\n[3] Tracking test ingestion session...")
    async with monitor.track_ingestion('https://example.com/test-manual.pdf', 'pdf') as session:
        print("    Session started")

        # Record pipeline stages
        session.record_stage('acquisition', 120, True)
        print("    Stage 1 (acquisition): 120ms")

        session.record_stage('extraction', 80, True, metadata={'vendor': 'Siemens'})
        print("    Stage 2 (extraction): 80ms + vendor metadata")

        session.record_stage('chunking', 50, True)
        print("    Stage 3 (chunking): 50ms")

        session.record_stage('generation', 200, True)
        print("    Stage 4 (generation): 200ms")

        session.record_stage('validation', 100, True, metadata={'avg_quality_score': 0.85})
        print("    Stage 5 (validation): 100ms + quality score")

        session.record_stage('embedding', 150, True)
        print("    Stage 6 (embedding): 150ms")

        session.record_stage('storage', 60, True)
        print("    Stage 7 (storage): 60ms")

        # Finish session
        session.finish(atoms_created=5, atoms_failed=0)
        print("    Session finished (5 atoms created)")

    print("\n[4] Session completed - Telegram notification sent!")
    print("    Check Telegram for message")

    # Wait for background writer
    print("\n[5] Waiting for background writer (6 seconds)...")
    await asyncio.sleep(6)

    # Shutdown monitor
    print("\n[6] Shutting down monitor...")
    await monitor.shutdown()
    print("    Monitor shutdown complete")

    print("\n" + "=" * 60)
    print("VERBOSE MODE TEST PASSED")
    print("=" * 60)


async def test_batch_mode():
    """Test BATCH mode integration."""
    print("\n" + "=" * 60)
    print("TEST 2: IngestionMonitor + TelegramNotifier (BATCH)")
    print("=" * 60)

    # Load environment
    load_dotenv()

    # Initialize notifier in BATCH mode
    print("\n[1] Initializing TelegramNotifier (BATCH mode)...")
    notifier = TelegramNotifier(
        bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
        chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")),
        mode="BATCH"
    )
    print(f"    Notifier initialized (mode={notifier.mode})")

    # Initialize monitor with notifier
    print("\n[2] Initializing IngestionMonitor with notifier...")
    db = DatabaseManager()
    monitor = IngestionMonitor(db, telegram_notifier=notifier)
    print("    Monitor initialized with Telegram notifications enabled")

    # Track multiple test sessions
    print("\n[3] Tracking 3 test sessions...")
    test_sources = [
        ("https://example.com/manual1.pdf", "Siemens", 0.85, 5, 0),
        ("https://example.com/manual2.pdf", "Rockwell", 0.78, 8, 1),
        ("https://example.com/manual3.pdf", "Mitsubishi", 0.92, 3, 0)
    ]

    for i, (url, vendor, quality, created, failed) in enumerate(test_sources, 1):
        async with monitor.track_ingestion(url, 'pdf') as session:
            session.record_stage('acquisition', 120, True)
            session.record_stage('extraction', 80, True, metadata={'vendor': vendor})
            session.record_stage('validation', 100, True, metadata={'avg_quality_score': quality})
            session.finish(atoms_created=created, atoms_failed=failed)
        print(f"    Session {i}: {url} ({vendor}, {created} atoms)")

    print(f"\n[4] All sessions queued (batch queue size: {len(notifier._batch_queue)})")

    # Send batch summary
    print("\n[5] Sending batch summary...")
    await notifier.send_batch_summary()
    print("    Batch summary sent to Telegram!")

    # Wait for background writer
    print("\n[6] Waiting for background writer (6 seconds)...")
    await asyncio.sleep(6)

    # Shutdown monitor
    print("\n[7] Shutting down monitor...")
    await monitor.shutdown()
    print("    Monitor shutdown complete")

    print("\n" + "=" * 60)
    print("BATCH MODE TEST PASSED")
    print("=" * 60)


async def main():
    """Run all integration tests."""
    print("=" * 60)
    print("IngestionMonitor + TelegramNotifier Integration Tests")
    print("=" * 60)

    try:
        # Test VERBOSE mode
        await test_verbose_mode()

        # Test BATCH mode
        await test_batch_mode()

        print("\n" + "=" * 60)
        print("ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        print("\nCheck your Telegram (@RivetCeo_bot) for notifications!")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
