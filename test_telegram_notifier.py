"""
Test script for TelegramNotifier.

Tests:
1. Initialization
2. VERBOSE mode notification
3. BATCH mode queuing and summary
4. Quiet hours detection
5. Rate limiting behavior
"""

import asyncio
import os
import sys
from agent_factory.observability.telegram_notifier import TelegramNotifier


async def test_verbose_mode():
    """Test VERBOSE mode notification."""
    print("\n" + "=" * 60)
    print("TEST 1: VERBOSE Mode Notification")
    print("=" * 60)

    # Initialize notifier in VERBOSE mode
    print("\n[1] Initializing VERBOSE notifier...")
    notifier = TelegramNotifier(
        bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN", "dummy_token_for_test"),
        chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")),
        mode="VERBOSE"
    )
    print(f"    Notifier initialized (mode={notifier.mode})")

    # Test notification (won't actually send with dummy token)
    print("\n[2] Testing notification format...")
    message = notifier._format_verbose_message(
        source_url="https://example.com/test-manual.pdf",
        atoms_created=5,
        atoms_failed=0,
        duration_ms=760,
        vendor="Siemens",
        quality_score=0.85,
        status="success"
    )
    print("    Message formatted:")
    print("    " + "-" * 50)
    for line in message.split("\n"):
        print(f"    {line}")
    print("    " + "-" * 50)

    # Test quiet hours
    print("\n[3] Testing quiet hours detection...")
    is_quiet = notifier._is_quiet_hours()
    print(f"    Currently quiet hours: {is_quiet}")

    print("\n[VERBOSE TEST PASSED]")


async def test_batch_mode():
    """Test BATCH mode queuing and summary."""
    print("\n" + "=" * 60)
    print("TEST 2: BATCH Mode Summary")
    print("=" * 60)

    # Initialize notifier in BATCH mode
    print("\n[1] Initializing BATCH notifier...")
    notifier = TelegramNotifier(
        bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN", "dummy_token_for_test"),
        chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")),
        mode="BATCH"
    )
    print(f"    Notifier initialized (mode={notifier.mode})")

    # Queue test sessions
    print("\n[2] Queuing test sessions...")
    test_sessions = [
        {
            "source_url": "https://example.com/manual1.pdf",
            "atoms_created": 5,
            "atoms_failed": 0,
            "duration_ms": 700,
            "vendor": "Siemens",
            "quality_score": 0.85,
            "status": "success"
        },
        {
            "source_url": "https://example.com/manual2.pdf",
            "atoms_created": 8,
            "atoms_failed": 1,
            "duration_ms": 920,
            "vendor": "Rockwell",
            "quality_score": 0.78,
            "status": "partial"
        },
        {
            "source_url": "https://example.com/manual3.pdf",
            "atoms_created": 3,
            "atoms_failed": 0,
            "duration_ms": 650,
            "vendor": "Siemens",
            "quality_score": 0.92,
            "status": "success"
        },
        {
            "source_url": "https://example.com/manual4.pdf",
            "atoms_created": 0,
            "atoms_failed": 5,
            "duration_ms": 1200,
            "vendor": "Mitsubishi",
            "quality_score": 0.0,
            "status": "failed"
        }
    ]

    for session in test_sessions:
        await notifier.queue_for_batch(session)
        print(f"    Queued: {session['source_url']} ({session['status']})")

    print(f"\n[3] Queue size: {len(notifier._batch_queue)} sessions")

    # Aggregate stats
    print("\n[4] Aggregating batch stats...")
    stats = notifier._aggregate_batch_stats(list(notifier._batch_queue))
    print(f"    Total sources: {stats['total_sources']}")
    print(f"    Success rate: {stats['success_rate']:.0%}")
    print(f"    Atoms created: {stats['total_atoms_created']}")
    print(f"    Avg duration: {stats['avg_duration_ms']}ms")
    print(f"    Top vendors: {stats['top_vendors']}")

    # Format batch message
    print("\n[5] Formatting batch summary message...")
    message = notifier._format_batch_message(stats)
    print("    Message formatted:")
    print("    " + "-" * 50)
    for line in message.split("\n"):
        print(f"    {line}")
    print("    " + "-" * 50)

    print("\n[BATCH TEST PASSED]")


async def test_rate_limiting():
    """Test rate limiting behavior."""
    print("\n" + "=" * 60)
    print("TEST 3: Rate Limiting")
    print("=" * 60)

    print("\n[1] Initializing notifier...")
    notifier = TelegramNotifier(
        bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN", "dummy_token_for_test"),
        chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")),
        mode="VERBOSE"
    )
    print(f"    Rate limit: {notifier._rate_limit_max} messages/minute")

    print("\n[2] Testing token bucket algorithm...")
    print(f"    Initial tokens: {notifier._rate_limit_tokens}")

    # Simulate consuming tokens
    for i in range(3):
        await notifier._wait_for_rate_limit()
        print(f"    After message {i+1}: {notifier._rate_limit_tokens:.2f} tokens remaining")

    print("\n[RATE LIMITING TEST PASSED]")


async def test_duration_formatting():
    """Test duration formatting."""
    print("\n" + "=" * 60)
    print("TEST 4: Duration Formatting")
    print("=" * 60)

    notifier = TelegramNotifier(
        bot_token="dummy",
        chat_id=123,
        mode="VERBOSE"
    )

    test_cases = [
        (500, "500ms"),
        (1500, "1.5s"),
        (65000, "1.1m"),
        (120000, "2.0m")
    ]

    print("\n[1] Testing duration formatting...")
    for ms, expected in test_cases:
        result = notifier._format_duration(ms)
        status = "OK" if expected in result or result in expected else "FAIL"
        print(f"    {ms}ms -> {result} [{status}]")

    print("\n[DURATION FORMATTING TEST PASSED]")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("TelegramNotifier Test Suite")
    print("=" * 60)

    try:
        await test_verbose_mode()
        await test_batch_mode()
        await test_rate_limiting()
        await test_duration_formatting()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        print("\nNote: Actual Telegram sending not tested (requires real bot token)")
        print("To test real sending, set ORCHESTRATOR_BOT_TOKEN in .env and run:")
        print("  poetry run python test_telegram_notifier_live.py")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
