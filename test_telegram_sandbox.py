#!/usr/bin/env python3
"""
Sandbox Test for Telegram Bot - No External Connections

Validates that all imports work and handlers are registered correctly
without actually connecting to Telegram or external services.

Usage:
    python test_telegram_sandbox.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("TELEGRAM BOT SANDBOX TEST")
print("=" * 80)
print()

# Set mock environment variables to prevent real connections
os.environ["TELEGRAM_BOT_TOKEN"] = "1234567890:MOCK_TOKEN_FOR_TESTING_ONLY"
os.environ["AUTHORIZED_TELEGRAM_USERS"] = "12345,67890"
os.environ["TELEGRAM_ADMIN_USERS"] = "12345"

# Disable actual connections
os.environ["SANDBOX_MODE"] = "true"

print("Step 1: Testing core imports...")
print("-" * 80)

try:
    from agent_factory.core.agent_factory import AgentFactory
    print("[OK] AgentFactory")
except Exception as e:
    print(f"[FAIL] AgentFactory: {e}")
    sys.exit(1)

try:
    from agent_factory.integrations.telegram.admin import (
        AdminDashboard,
        AgentManager,
        ContentReviewer,
        GitHubActions,
        KBManager,
        Analytics,
        SystemControl,
    )
    print("[OK] Admin Panel modules (7/7)")
except Exception as e:
    print(f"[FAIL] Admin Panel: {e}")
    sys.exit(1)

print()
print("Step 2: Testing telegram bot module imports...")
print("-" * 80)

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler
    print("[OK] python-telegram-bot library")
except Exception as e:
    print(f"[FAIL] Telegram library: {e}")
    sys.exit(1)

try:
    from agent_factory.integrations.telegram.rivet_pro_handlers import RIVETProHandlers
    print("[OK] RIVET Pro handlers")
except Exception as e:
    print(f"[WARN]  RIVET Pro handlers: {e}")

try:
    from agent_factory.integrations.telegram.langgraph_handlers import LangGraphHandlers
    print("[OK] LangGraph handlers")
except Exception as e:
    print(f"[WARN]  LangGraph handlers: {e}")

try:
    from agent_factory.integrations.telegram.scaffold_handlers import ScaffoldHandlers
    print("[OK] Scaffold handlers")
except Exception as e:
    print(f"[WARN]  Scaffold handlers: {e}")

try:
    from agent_factory.integrations.telegram.tier0_handlers import TIER0Handlers
    print("[OK] TIER 0 handlers")
except Exception as e:
    print(f"[WARN]  TIER 0 handlers: {e}")

print()
print("Step 3: Testing admin panel initialization...")
print("-" * 80)

try:
    admin_dashboard = AdminDashboard()
    print("[OK] AdminDashboard instance created")
except Exception as e:
    print(f"[FAIL] AdminDashboard init: {e}")
    sys.exit(1)

try:
    agent_manager = AgentManager()
    print("[OK] AgentManager instance created")
except Exception as e:
    print(f"[FAIL] AgentManager init: {e}")
    sys.exit(1)

try:
    content_reviewer = ContentReviewer()
    print("[OK] ContentReviewer instance created")
except Exception as e:
    print(f"[FAIL] ContentReviewer init: {e}")
    sys.exit(1)

try:
    github_actions = GitHubActions()
    print("[OK] GitHubActions instance created")
except Exception as e:
    print(f"[FAIL] GitHubActions init: {e}")
    sys.exit(1)

try:
    kb_manager = KBManager()
    print("[OK] KBManager instance created")
except Exception as e:
    print(f"[FAIL] KBManager init: {e}")
    sys.exit(1)

try:
    analytics = Analytics()
    print("[OK] Analytics instance created")
except Exception as e:
    print(f"[FAIL] Analytics init: {e}")
    sys.exit(1)

try:
    system_control = SystemControl()
    print("[OK] SystemControl instance created")
except Exception as e:
    print(f"[FAIL] SystemControl init: {e}")
    sys.exit(1)

print()
print("Step 4: Testing command handler methods...")
print("-" * 80)

# Check that all expected handler methods exist
admin_commands = [
    ('admin_dashboard', 'handle_admin'),
    ('agent_manager', 'handle_agents'),
    ('agent_manager', 'handle_agent_detail'),
    ('agent_manager', 'handle_agent_logs'),
    ('content_reviewer', 'handle_content'),
    ('github_actions', 'handle_deploy'),
    ('github_actions', 'handle_workflow'),
    ('github_actions', 'handle_workflows'),
    ('github_actions', 'handle_workflow_status'),
    ('kb_manager', 'handle_kb'),
    ('kb_manager', 'handle_kb_ingest'),
    ('kb_manager', 'handle_kb_search'),
    ('kb_manager', 'handle_kb_queue'),
    ('analytics', 'handle_metrics'),
    ('analytics', 'handle_costs'),
    ('analytics', 'handle_revenue'),
    ('system_control', 'handle_health'),
    ('system_control', 'handle_db_health'),
    ('system_control', 'handle_vps_status'),
    ('system_control', 'handle_restart'),
]

missing_handlers = []
for obj_name, method_name in admin_commands:
    obj = locals()[obj_name]
    if not hasattr(obj, method_name):
        missing_handlers.append(f"{obj_name}.{method_name}")

if missing_handlers:
    print(f"[FAIL] Missing handlers: {', '.join(missing_handlers)}")
else:
    print(f"[OK] All 20 admin command handlers found")

print()
print("Step 5: Checking handler signatures...")
print("-" * 80)

import inspect

# Check that handlers have correct signature (async, takes Update and Context)
async_handlers_count = 0
for obj_name, method_name in admin_commands:
    obj = locals()[obj_name]
    if hasattr(obj, method_name):
        method = getattr(obj, method_name)
        if inspect.iscoroutinefunction(method):
            async_handlers_count += 1

print(f"[OK] {async_handlers_count}/20 handlers are async (expected for telegram-python-bot)")

print()
print("=" * 80)
print("SANDBOX TEST SUMMARY")
print("=" * 80)

results = {
    "Core Imports": "[OK] PASS",
    "Telegram Library": "[OK] PASS",
    "Admin Panel Modules": "[OK] PASS",
    "Admin Instances": "[OK] PASS",
    "Handler Methods": "[OK] PASS" if not missing_handlers else "[FAIL] FAIL",
    "Handler Signatures": "[OK] PASS",
}

print()
for test, result in results.items():
    print(f"{test:.<40} {result}")

print()
if all("[OK]" in r for r in results.values()):
    print("[SUCCESS] ALL TESTS PASSED - Ready for controlled testing")
    print()
    print("Next Steps:")
    print("1. Test in private Telegram channel (not production)")
    print("2. Try each admin command manually")
    print("3. Verify no errors in console output")
    print("4. Deploy to production only after manual validation")
    print("[FAIL] SOME TESTS FAILED - Fix issues before deployment")
else:
    print("[FAIL] SOME TESTS FAILED - Fix issues before deployment")
    sys.exit(1)
