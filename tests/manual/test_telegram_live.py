#!/usr/bin/env python3
"""
Test if Telegram bot is responding.
Sends a test message via API to check bot status.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Get bot info
response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
print("=" * 60)
print("BOT INFO")
print("=" * 60)
print(response.json())
print()

# Get recent updates
response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=5")
updates = response.json()

print("=" * 60)
print("RECENT UPDATES (Last 5 messages)")
print("=" * 60)

if updates.get("ok") and updates.get("result"):
    for update in updates["result"]:
        if "message" in update:
            msg = update["message"]
            print(f"From: {msg.get('from', {}).get('first_name', 'Unknown')}")
            print(f"Text: {msg.get('text', 'N/A')}")
            print(f"Date: {msg.get('date', 'N/A')}")
            print("-" * 60)
else:
    print("No recent messages")

print()
print("=" * 60)
print("BOT STATUS")
print("=" * 60)

# Check if webhook is set
response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
webhook = response.json()

if webhook.get("result", {}).get("url"):
    print(f"Mode: WEBHOOK")
    print(f"URL: {webhook['result']['url']}")
else:
    print(f"Mode: POLLING (or not running)")

print()
print("=" * 60)
print("TO TEST BOT")
print("=" * 60)
print("Open Telegram and send:")
print("  /kb_stats")
print()
print("Or search for: @Agent_Factory_Bot")
print("=" * 60)
