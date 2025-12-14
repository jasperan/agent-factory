#!/usr/bin/env python3
"""
UptimeRobot Monitoring Setup Helper

Guides user through UptimeRobot configuration for Phase 4 (Monitoring)

Usage:
    python scripts/deployment/setup_uptimerobot.py --service-url https://your-service.onrender.com

This script provides:
- Step-by-step UptimeRobot account setup instructions
- Monitor configuration templates
- Telegram alert webhook setup
- Verification commands
- Optional: API-based monitor creation (if API key provided)
"""

import os
import sys
import requests
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class UptimeRobotSetupGuide:
    """Interactive guide for UptimeRobot monitoring setup"""

    def __init__(self, service_url: str, api_key: str = None):
        self.service_url = service_url.rstrip("/")
        self.api_key = api_key
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}\n")

    def print_step(self, step: int, title: str):
        """Print step header"""
        print(f"\n[STEP {step}] {title}")
        print("-" * 60)

    def guide_account_setup(self):
        """Guide user through account creation"""
        self.print_header("UPTIMEROBOT ACCOUNT SETUP")

        self.print_step(1, "Create Free Account")
        print("1. Go to: https://uptimerobot.com/signUp")
        print("2. Sign up with email (no credit card required)")
        print("3. Verify your email address")
        print("4. Log in to dashboard: https://uptimerobot.com/dashboard")
        print("\nPress Enter when you've completed account setup...")
        input()

    def guide_monitor_creation(self):
        """Guide user through monitor creation"""
        self.print_header("CREATE BOT HEALTH MONITOR")

        health_url = f"{self.service_url}/health"

        self.print_step(2, "Add Monitor")
        print("1. Click 'Add New Monitor' button")
        print("2. Fill in the following configuration:\n")

        print("   Monitor Configuration:")
        print("   ┌─────────────────────────────────────────────────────┐")
        print(f"   │ Monitor Type:       HTTP(s)                         │")
        print(f"   │ Friendly Name:      Agent Factory Bot               │")
        print(f"   │ URL:                {health_url:<30} │")
        print(f"   │ Monitoring Interval: 5 minutes                      │")
        print(f"   │ Monitor Timeout:    30 seconds                      │")
        print("   └─────────────────────────────────────────────────────┘\n")

        print("3. Click 'Create Monitor'")
        print("\nPress Enter when you've created the monitor...")
        input()

    def guide_alert_contact_setup(self):
        """Guide user through alert contact setup"""
        self.print_header("CONFIGURE TELEGRAM ALERTS")

        if not self.bot_token or not self.admin_chat_id:
            print("WARNING: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_ADMIN_CHAT_ID")
            print("Skipping Telegram alert setup.\n")
            return

        webhook_url = (
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            f"?chat_id={self.admin_chat_id}"
            f"&text=ALERT:%20Bot%20is%20DOWN"
        )

        self.print_step(3, "Add Alert Contact")
        print("1. Go to 'My Settings' -> 'Alert Contacts'")
        print("2. Click 'Add Alert Contact'")
        print("3. Select 'Webhook'")
        print("4. Fill in configuration:\n")

        print("   Alert Contact Configuration:")
        print("   ┌─────────────────────────────────────────────────────┐")
        print(f"   │ Friendly Name:      Telegram Bot Alerts             │")
        print(f"   │ Webhook URL:        (see below)                     │")
        print("   └─────────────────────────────────────────────────────┘\n")

        print("   Webhook URL (copy this):")
        print(f"   {webhook_url}\n")

        print("5. Click 'Create Alert Contact'")
        print("6. Go back to your monitor settings")
        print("7. Enable 'Telegram Bot Alerts' in alert contacts")
        print("\nPress Enter when you've configured alerts...")
        input()

    def guide_heartbeat_monitor(self):
        """Guide user through cron job heartbeat monitor"""
        self.print_header("CREATE CRON JOB HEARTBEAT MONITOR")

        self.print_step(4, "Add Heartbeat Monitor (Optional)")
        print("This monitor ensures your daily KB automation job is running.\n")

        print("1. Click 'Add New Monitor' button")
        print("2. Select 'Heartbeat' type")
        print("3. Fill in configuration:\n")

        print("   Heartbeat Configuration:")
        print("   ┌─────────────────────────────────────────────────────┐")
        print(f"   │ Friendly Name:      KB Automation Job               │")
        print(f"   │ Interval:           1 day                           │")
        print(f"   │ Grace Period:       2 hours                         │")
        print("   └─────────────────────────────────────────────────────┘\n")

        print("4. Copy the heartbeat URL provided")
        print("5. Add this URL to your cron job script to ping on success")
        print("\nPress Enter to continue (or skip if not needed)...")
        input()

    def test_monitor(self):
        """Guide user through monitor testing"""
        self.print_header("TEST MONITOR & ALERTS")

        self.print_step(5, "Verify Monitor Status")
        print("1. Go to UptimeRobot dashboard: https://uptimerobot.com/dashboard")
        print("2. Your 'Agent Factory Bot' monitor should show:")
        print("   - Status: Up (green)")
        print("   - Uptime: 100%")
        print("   - Latest response time: < 1000ms")
        print("\nPress Enter when monitor shows 'Up' status...")
        input()

        self.print_step(6, "Test Alert System (Optional)")
        print("To test Telegram alerts:")
        print("1. Click on your monitor")
        print("2. Click 'Pause Monitoring'")
        print("3. Wait 10 minutes")
        print("4. Check Telegram - you should receive alert")
        print("5. Click 'Resume Monitoring'")
        print("6. Check Telegram - you should receive 'Up' notification")
        print("\nPress Enter to skip alert test...")
        input()

    def create_monitor_via_api(self):
        """Attempt to create monitor via API if key provided"""
        if not self.api_key:
            return False

        self.print_header("CREATING MONITOR VIA API")

        api_url = "https://api.uptimerobot.com/v2/newMonitor"
        health_url = f"{self.service_url}/health"

        payload = {
            "api_key": self.api_key,
            "format": "json",
            "type": 1,  # HTTP(s)
            "friendly_name": "Agent Factory Bot",
            "url": health_url,
            "interval": 300,  # 5 minutes
            "timeout": 30
        }

        try:
            print(f"Creating monitor for: {health_url}")
            response = requests.post(api_url, data=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("stat") == "ok":
                monitor_id = result.get("monitor", {}).get("id")
                print(f"Monitor created successfully! ID: {monitor_id}")
                print("Monitor URL: https://uptimerobot.com/dashboard")
                return True
            else:
                print(f"Failed to create monitor: {result}")
                return False

        except Exception as e:
            print(f"Error creating monitor via API: {e}")
            print("Falling back to manual setup...\n")
            return False

    def verify_monitor_status(self):
        """Verify monitor is working via API"""
        if not self.api_key:
            print("\nNo API key - skipping automated verification")
            return

        self.print_header("VERIFYING MONITOR STATUS")

        api_url = "https://api.uptimerobot.com/v2/getMonitors"

        payload = {
            "api_key": self.api_key,
            "format": "json",
            "logs": 0
        }

        try:
            response = requests.post(api_url, data=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("stat") == "ok":
                monitors = result.get("monitors", [])
                bot_monitor = None

                for monitor in monitors:
                    if "Agent Factory" in monitor.get("friendly_name", ""):
                        bot_monitor = monitor
                        break

                if bot_monitor:
                    print(f"Monitor Name: {bot_monitor.get('friendly_name')}")
                    print(f"Status: {bot_monitor.get('status')} (2 = Up)")
                    print(f"URL: {bot_monitor.get('url')}")
                    print(f"Uptime: {bot_monitor.get('all_time_uptime_ratio')}%")
                    print("\nMonitor is operational!")
                else:
                    print("No 'Agent Factory' monitor found")

        except Exception as e:
            print(f"Error verifying monitor: {e}")

    def print_summary(self):
        """Print setup summary"""
        self.print_header("SETUP COMPLETE")

        print("UptimeRobot monitoring is now active!\n")

        print("What's Monitoring:")
        print(f"  Health Endpoint: {self.service_url}/health")
        print(f"  Check Interval: Every 5 minutes")
        print(f"  Alerts: Telegram notifications\n")

        print("Why This Matters:")
        print("  - Prevents Render.com free tier from sleeping")
        print("  - Immediate alerts if bot goes down")
        print("  - 24/7 uptime monitoring\n")

        print("Next Steps:")
        print("  1. Monitor should show 100% uptime within 24 hours")
        print("  2. Test bot responsiveness (send /start in Telegram)")
        print("  3. Verify health endpoint manually:")
        print(f"     curl {self.service_url}/health\n")

        print("Dashboard Access:")
        print("  https://uptimerobot.com/dashboard\n")

    def run_interactive_setup(self):
        """Run complete interactive setup"""
        print("="*60)
        print("UPTIMEROBOT MONITORING SETUP")
        print("="*60)
        print(f"Service URL: {self.service_url}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Try API-based setup first
        if self.api_key:
            print("API key detected - attempting automated setup...")
            if self.create_monitor_via_api():
                self.verify_monitor_status()
                self.guide_alert_contact_setup()
                self.test_monitor()
                self.print_summary()
                return

        # Fall back to manual setup
        print("Running manual setup guide...\n")
        self.guide_account_setup()
        self.guide_monitor_creation()
        self.guide_alert_contact_setup()
        self.guide_heartbeat_monitor()
        self.test_monitor()
        self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="UptimeRobot monitoring setup for Agent Factory deployment"
    )
    parser.add_argument(
        "--service-url",
        required=True,
        help="Render.com service URL (e.g., https://agent-factory-telegram-bot.onrender.com)"
    )
    parser.add_argument(
        "--api-key",
        help="UptimeRobot API key (optional - enables automated setup)"
    )

    args = parser.parse_args()

    # Get API key from args or environment
    api_key = args.api_key or os.getenv("UPTIMEROBOT_API_KEY")

    guide = UptimeRobotSetupGuide(args.service_url, api_key)
    guide.run_interactive_setup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
