#!/usr/bin/env python3
"""
DEPRECATED: Use scripts/bot_manager.py instead.

This entry point is deprecated to prevent bot instance conflicts.
All bot management should go through the singleton bot_manager.py CLI.

Usage:
    python scripts/bot_manager.py start
    python scripts/bot_manager.py status
    python scripts/bot_manager.py stop
"""

import sys
from pathlib import Path

print("=" * 60)
print("⚠️ WARNING: run_telegram_bot.py is DEPRECATED")
print("=" * 60)
print()
print("To prevent bot instance conflicts, use:")
print("  python scripts/bot_manager.py start")
print()
print("For more options:")
print("  python scripts/bot_manager.py --help")
print()
print("=" * 60)
print()

# Redirect to bot_manager.py
bot_manager = Path(__file__).parent / "scripts" / "bot_manager.py"
sys.argv = ["python", str(bot_manager), "start"]
exec(open(bot_manager).read())
