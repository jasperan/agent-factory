#!/usr/bin/env python3
"""
Monitoring Verification Script

Verifies UptimeRobot monitoring is working correctly

Usage:
    python scripts/deployment/verify_monitoring.py --service-url https://your-service.onrender.com

Optional with UptimeRobot API key:
    python scripts/deployment/verify_monitoring.py --service-url <URL> --api-key <KEY>

This script checks:
- Health endpoint accessibility
- Response time consistency
- UptimeRobot monitor status (if API key provided)
- Alert webhook configuration (if API key provided)
"""

import os
import sys
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MonitoringVerifier:
    """Verify UptimeRobot monitoring configuration"""

    def __init__(self, service_url: str, api_key: str = None):
        self.service_url = service_url.rstrip("/")
        self.api_key = api_key
        self.checks_passed = 0
        self.checks_failed = 0

    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}\n")

    def check_pass(self, message: str):
        """Record successful check"""
        print(f"PASS: {message}")
        self.checks_passed += 1

    def check_fail(self, message: str):
        """Record failed check"""
        print(f"FAIL: {message}")
        self.checks_failed += 1

    def check_health_endpoint_reachability(self, num_checks: int = 5) -> bool:
        """
        Test health endpoint is consistently reachable

        Args:
            num_checks: Number of consecutive checks

        Returns:
            True if all checks pass, False otherwise
        """
        self.print_header(f"HEALTH ENDPOINT REACHABILITY ({num_checks} checks)")

        health_url = f"{self.service_url}/health"
        print(f"URL: {health_url}")
        print(f"Testing every 3 seconds...\n")

        successes = 0
        failures = 0
        response_times = []

        for i in range(num_checks):
            start_time = time.time()

            try:
                response = requests.get(health_url, timeout=10)
                elapsed = (time.time() - start_time) * 1000  # Convert to ms

                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    pid = result.get("pid")

                    if status == "healthy":
                        print(f"  [{i+1}/{num_checks}] OK (PID: {pid}, Response: {elapsed:.0f}ms)")
                        successes += 1
                        response_times.append(elapsed)
                    else:
                        print(f"  [{i+1}/{num_checks}] WARN - Status: {status}")
                        failures += 1
                else:
                    print(f"  [{i+1}/{num_checks}] FAIL - HTTP {response.status_code}")
                    failures += 1

            except Exception as e:
                print(f"  [{i+1}/{num_checks}] FAIL - Error: {e}")
                failures += 1

            if i < num_checks - 1:
                time.sleep(3)

        print()
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            print(f"Results: {successes} passed, {failures} failed")
            print(f"Average response time: {avg_response:.0f}ms")

            if successes == num_checks:
                self.check_pass(f"All {num_checks} health checks passed")
                return True
            else:
                self.check_fail(f"Health check failures: {failures}/{num_checks}")
                return False
        else:
            self.check_fail("No successful health checks")
            return False

    def check_uptimerobot_monitor_status(self) -> bool:
        """
        Query UptimeRobot API for monitor status

        Returns:
            True if monitor found and active, False otherwise
        """
        if not self.api_key:
            print("\nNo UptimeRobot API key - skipping monitor status check")
            return True  # Non-critical if no API key

        self.print_header("UPTIMEROBOT MONITOR STATUS")

        api_url = "https://api.uptimerobot.com/v2/getMonitors"

        payload = {
            "api_key": self.api_key,
            "format": "json",
            "logs": 1,
            "log_limit": 10
        }

        try:
            response = requests.post(api_url, data=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("stat") == "ok":
                monitors = result.get("monitors", [])
                bot_monitor = None

                # Find Agent Factory monitor
                for monitor in monitors:
                    url = monitor.get("url", "")
                    if self.service_url in url:
                        bot_monitor = monitor
                        break

                if bot_monitor:
                    name = bot_monitor.get("friendly_name")
                    status = bot_monitor.get("status")
                    uptime = bot_monitor.get("all_time_uptime_ratio", 0)
                    interval = bot_monitor.get("interval")

                    print(f"Monitor Name: {name}")
                    print(f"Monitor URL: {bot_monitor.get('url')}")
                    print(f"Status: {status} (2 = Up, 1 = Not checked yet, 0 = Down)")
                    print(f"Uptime Ratio: {uptime}%")
                    print(f"Check Interval: {interval} seconds ({interval/60:.0f} minutes)")

                    # Check recent logs
                    logs = bot_monitor.get("logs", [])
                    if logs:
                        print(f"\nRecent Checks (last {len(logs)}):")
                        for log in logs[:5]:
                            log_type = log.get("type")
                            log_datetime = datetime.fromtimestamp(log.get("datetime", 0))
                            reason = log.get("reason", {}).get("detail", "N/A")

                            log_status = "UP" if log_type == 2 else "DOWN"
                            print(f"  [{log_datetime}] {log_status} - {reason}")

                    if status == 2:
                        self.check_pass("Monitor is active and reporting 'Up'")
                    elif status == 1:
                        print("\nWARN: Monitor not checked yet (newly created)")
                        self.check_pass("Monitor exists (pending first check)")
                    else:
                        self.check_fail(f"Monitor status is DOWN (status: {status})")
                        return False

                    return True
                else:
                    self.check_fail(f"No monitor found for {self.service_url}")
                    return False
            else:
                self.check_fail(f"UptimeRobot API error: {result}")
                return False

        except Exception as e:
            self.check_fail(f"Error querying UptimeRobot API: {e}")
            return False

    def check_alert_contacts(self) -> bool:
        """
        Verify alert contacts are configured

        Returns:
            True if alert contacts found, False otherwise
        """
        if not self.api_key:
            print("\nNo UptimeRobot API key - skipping alert contact check")
            return True  # Non-critical

        self.print_header("ALERT CONTACTS VERIFICATION")

        api_url = "https://api.uptimerobot.com/v2/getAlertContacts"

        payload = {
            "api_key": self.api_key,
            "format": "json"
        }

        try:
            response = requests.post(api_url, data=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("stat") == "ok":
                contacts = result.get("alert_contacts", [])

                if contacts:
                    print(f"Found {len(contacts)} alert contact(s):\n")
                    for contact in contacts:
                        contact_type = contact.get("type")
                        friendly_name = contact.get("friendly_name")
                        status = contact.get("status")

                        type_name = {
                            1: "SMS",
                            2: "Email",
                            3: "Twitter",
                            4: "Boxcar",
                            5: "Webhook",
                            6: "Pushbullet",
                            7: "Zapier",
                            10: "Slack",
                            11: "Telegram"
                        }.get(contact_type, f"Type {contact_type}")

                        status_name = "Active" if status == 2 else "Paused"

                        print(f"  - {friendly_name} ({type_name}) - {status_name}")

                    self.check_pass(f"{len(contacts)} alert contact(s) configured")
                    return True
                else:
                    print("WARN: No alert contacts configured")
                    print("Consider adding Telegram webhook for downtime alerts")
                    return True  # Non-blocking warning

            else:
                self.check_fail(f"Alert contacts API error: {result}")
                return False

        except Exception as e:
            self.check_fail(f"Error querying alert contacts: {e}")
            return False

    def check_monitoring_interval(self) -> bool:
        """
        Verify monitoring interval is optimal (5 minutes)

        Returns:
            True if interval is 5 minutes or less, False otherwise
        """
        if not self.api_key:
            return True  # Skip if no API

        self.print_header("MONITORING INTERVAL CHECK")

        api_url = "https://api.uptimerobot.com/v2/getMonitors"

        payload = {
            "api_key": self.api_key,
            "format": "json"
        }

        try:
            response = requests.post(api_url, data=payload, timeout=10)
            result = response.json()

            if result.get("stat") == "ok":
                monitors = result.get("monitors", [])

                for monitor in monitors:
                    if self.service_url in monitor.get("url", ""):
                        interval = monitor.get("interval")
                        interval_min = interval / 60

                        print(f"Current monitoring interval: {interval} seconds ({interval_min:.0f} minutes)")

                        if interval <= 300:  # 5 minutes or less
                            self.check_pass(f"Optimal interval ({interval_min:.0f} min)")
                            return True
                        else:
                            print(f"\nWARN: Interval is {interval_min:.0f} minutes")
                            print("Recommended: 5 minutes (300 seconds) to prevent free tier sleep")
                            return True  # Non-blocking warning

                self.check_fail("Monitor not found for interval check")
                return False

        except Exception as e:
            print(f"WARN: Could not check interval: {e}")
            return True  # Non-blocking

    def run_all_checks(self) -> bool:
        """Run all verification checks"""
        print("="*60)
        print("MONITORING VERIFICATION")
        print("="*60)
        print(f"Service URL: {self.service_url}")
        print(f"API Key: {'Provided' if self.api_key else 'Not provided'}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run checks
        self.check_health_endpoint_reachability(num_checks=5)
        self.check_uptimerobot_monitor_status()
        self.check_alert_contacts()
        self.check_monitoring_interval()

        # Summary
        self.print_header("VERIFICATION SUMMARY")
        print(f"Checks passed: {self.checks_passed}")
        print(f"Checks failed: {self.checks_failed}")

        if self.checks_failed == 0:
            print("\nSUCCESS: All monitoring checks passed")
            print("\nMonitoring is operational and configured correctly!")
            return True
        else:
            print(f"\nWARNING: {self.checks_failed} check(s) failed")
            print("\nReview errors above and fix configuration.")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Verify UptimeRobot monitoring configuration"
    )
    parser.add_argument(
        "--service-url",
        required=True,
        help="Render.com service URL"
    )
    parser.add_argument(
        "--api-key",
        help="UptimeRobot API key (optional - enables full verification)"
    )

    args = parser.parse_args()

    # Get API key from args or environment
    api_key = args.api_key or os.getenv("UPTIMEROBOT_API_KEY")

    verifier = MonitoringVerifier(args.service_url, api_key)
    success = verifier.run_all_checks()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
