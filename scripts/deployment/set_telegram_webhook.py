#!/usr/bin/env python3
"""
Automated Telegram Webhook Configuration Script

Usage:
    python scripts/deployment/set_telegram_webhook.py --service-url https://your-service.onrender.com

This script automates Phase 3 of deployment:
- Sets Telegram webhook
- Verifies webhook configuration
- Tests bot responsiveness
"""

import os
import sys
import requests
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def set_webhook(bot_token: str, service_url: str) -> bool:
    """
    Set Telegram webhook to point to deployed service

    Args:
        bot_token: Telegram bot token from .env
        service_url: Render.com service URL

    Returns:
        True if webhook set successfully, False otherwise
    """
    webhook_url = f"{service_url}/telegram-webhook"
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"

    payload = {
        "url": webhook_url,
        "max_connections": 40,
        "allowed_updates": ["message", "callback_query"]
    }

    print(f"Setting webhook to: {webhook_url}")

    try:
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result.get("ok"):
            print("✅ Webhook set successfully!")
            print(f"   Description: {result.get('description', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to set webhook: {result}")
            return False

    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return False


def verify_webhook(bot_token: str, expected_url: str) -> bool:
    """
    Verify webhook is configured correctly

    Args:
        bot_token: Telegram bot token
        expected_url: Expected webhook URL

    Returns:
        True if webhook verified, False otherwise
    """
    api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"

    print("\nVerifying webhook configuration...")

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result.get("ok"):
            webhook_info = result.get("result", {})
            actual_url = webhook_info.get("url", "")
            pending_count = webhook_info.get("pending_update_count", 0)

            print(f"   Webhook URL: {actual_url}")
            print(f"   Pending updates: {pending_count}")
            print(f"   Max connections: {webhook_info.get('max_connections', 'N/A')}")

            if actual_url == expected_url:
                print("✅ Webhook verified successfully!")
                return True
            else:
                print(f"⚠️  Webhook URL mismatch!")
                print(f"   Expected: {expected_url}")
                print(f"   Actual: {actual_url}")
                return False
        else:
            print(f"❌ Failed to verify webhook: {result}")
            return False

    except Exception as e:
        print(f"❌ Error verifying webhook: {e}")
        return False


def test_bot_health(service_url: str) -> bool:
    """
    Test bot health endpoint

    Args:
        service_url: Render.com service URL

    Returns:
        True if health check passes, False otherwise
    """
    health_url = f"{service_url}/health"

    print(f"\nTesting health endpoint: {health_url}")

    try:
        response = requests.get(health_url, timeout=10)
        response.raise_for_status()

        result = response.json()
        status = result.get("status")
        pid = result.get("pid")
        uptime = result.get("uptime_seconds", 0)

        print(f"   Status: {status}")
        print(f"   PID: {pid}")
        print(f"   Uptime: {uptime} seconds")

        if status == "healthy":
            print("✅ Health check passed!")
            return True
        else:
            print(f"⚠️  Bot status: {status}")
            return False

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Set and verify Telegram webhook for deployed bot"
    )
    parser.add_argument(
        "--service-url",
        required=True,
        help="Render.com service URL (e.g., https://agent-factory-telegram-bot.onrender.com)"
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip health endpoint test"
    )

    args = parser.parse_args()

    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        print("   Please set TELEGRAM_BOT_TOKEN in your .env file")
        return 1

    # Clean service URL (remove trailing slash)
    service_url = args.service_url.rstrip("/")
    webhook_url = f"{service_url}/telegram-webhook"

    print("=" * 60)
    print("TELEGRAM WEBHOOK CONFIGURATION")
    print("=" * 60)
    print(f"Service URL: {service_url}")
    print(f"Webhook URL: {webhook_url}")
    print("=" * 60)
    print()

    # Step 1: Test health endpoint (unless skipped)
    if not args.skip_health_check:
        if not test_bot_health(service_url):
            print("\n⚠️  Health check failed. Bot may not be running.")
            print("   Continue anyway? (y/n): ", end="")
            if input().lower() != "y":
                return 1

    # Step 2: Set webhook
    if not set_webhook(bot_token, service_url):
        return 1

    # Step 3: Verify webhook
    if not verify_webhook(bot_token, webhook_url):
        return 1

    print("\n" + "=" * 60)
    print("✅ WEBHOOK CONFIGURATION COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Open Telegram and send /start to your bot")
    print("2. Bot should respond within 1-2 seconds")
    print("3. If bot doesn't respond, check Render logs for errors")
    print("\nMonitoring:")
    print(f"   Health: {service_url}/health")
    print(f"   Logs: https://dashboard.render.com → Your Service → Logs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
