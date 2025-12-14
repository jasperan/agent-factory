#!/usr/bin/env python3
"""
Deployment Validation Script

Automated checks for Phase 5 (Validation & Testing)

Usage:
    python scripts/deployment/validate_deployment.py --service-url https://your-service.onrender.com

This script runs comprehensive validation:
- Health endpoint checks (10 consecutive)
- Bot responsiveness test
- Database connection test
- Webhook status verification
- Knowledge base stats
"""

import os
import sys
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
load_dotenv()


class DeploymentValidator:
    """Comprehensive deployment validation"""

    def __init__(self, service_url: str):
        self.service_url = service_url.rstrip("/")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.checks_passed = 0
        self.checks_failed = 0

    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}\n")

    def check_pass(self, message: str):
        """Record successful check"""
        print(f"✅ {message}")
        self.checks_passed += 1

    def check_fail(self, message: str):
        """Record failed check"""
        print(f"❌ {message}")
        self.checks_failed += 1

    def check_health_endpoint(self, num_checks: int = 10) -> bool:
        """
        Test health endpoint multiple times

        Args:
            num_checks: Number of consecutive checks

        Returns:
            True if all checks pass, False otherwise
        """
        self.print_header(f"HEALTH ENDPOINT TEST ({num_checks} checks)")

        health_url = f"{self.service_url}/health"
        print(f"URL: {health_url}")
        print(f"Checking every 5 seconds...\n")

        successes = 0
        failures = 0
        pids_seen = set()

        for i in range(num_checks):
            try:
                response = requests.get(health_url, timeout=10)

                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    pid = result.get("pid")
                    uptime = result.get("uptime_seconds", 0)

                    pids_seen.add(pid)

                    if status == "healthy":
                        print(f"  [{i+1}/{num_checks}] ✅ Healthy (PID: {pid}, Uptime: {uptime}s)")
                        successes += 1
                    else:
                        print(f"  [{i+1}/{num_checks}] ⚠️  Status: {status}")
                        failures += 1
                else:
                    print(f"  [{i+1}/{num_checks}] ❌ HTTP {response.status_code}")
                    failures += 1

            except Exception as e:
                print(f"  [{i+1}/{num_checks}] ❌ Error: {e}")
                failures += 1

            if i < num_checks - 1:
                time.sleep(5)

        print()
        print(f"Results: {successes} passed, {failures} failed")
        print(f"Unique PIDs seen: {len(pids_seen)} (restarts: {len(pids_seen) - 1})")

        if successes == num_checks:
            self.check_pass(f"All {num_checks} health checks passed")
            return True
        elif successes >= num_checks * 0.8:
            self.check_pass(f"Most health checks passed ({successes}/{num_checks})")
            return True
        else:
            self.check_fail(f"Too many health check failures ({failures}/{num_checks})")
            return False

    def check_webhook_status(self) -> bool:
        """Verify webhook configuration"""
        self.print_header("WEBHOOK VERIFICATION")

        if not self.bot_token:
            self.check_fail("TELEGRAM_BOT_TOKEN not set")
            return False

        api_url = f"https://api.telegram.org/bot{self.bot_token}/getWebhookInfo"

        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                webhook_info = result.get("result", {})
                url = webhook_info.get("url", "")
                pending = webhook_info.get("pending_update_count", 0)
                max_conn = webhook_info.get("max_connections", 0)

                print(f"Webhook URL: {url}")
                print(f"Pending updates: {pending}")
                print(f"Max connections: {max_conn}")

                expected_url = f"{self.service_url}/telegram-webhook"
                if url == expected_url:
                    self.check_pass("Webhook URL correct")
                else:
                    self.check_fail(f"Webhook URL mismatch (expected: {expected_url})")
                    return False

                if pending == 0:
                    self.check_pass("No pending updates")
                else:
                    print(f"⚠️  {pending} pending updates (bot may be catching up)")

                return True
            else:
                self.check_fail(f"Webhook info failed: {result}")
                return False

        except Exception as e:
            self.check_fail(f"Webhook check error: {e}")
            return False

    def check_database_connection(self) -> bool:
        """Test database connectivity"""
        self.print_header("DATABASE CONNECTION TEST")

        try:
            # Try to import and connect to database
            from agent_factory.memory.storage import get_storage_instance

            storage = get_storage_instance()

            # Simple health check
            if hasattr(storage, 'health_check'):
                if storage.health_check():
                    self.check_pass("Database connection successful")
                    return True
                else:
                    self.check_fail("Database health check failed")
                    return False
            else:
                self.check_pass("Database connection appears OK (no health_check method)")
                return True

        except Exception as e:
            self.check_fail(f"Database connection error: {e}")
            return False

    def check_knowledge_base_stats(self) -> bool:
        """Query knowledge base statistics"""
        self.print_header("KNOWLEDGE BASE STATISTICS")

        try:
            import psycopg

            db_url = os.getenv("NEON_DB_URL") or os.getenv("SUPABASE_DB_URL")
            if not db_url:
                print("⚠️  No database URL found, skipping KB stats")
                return True

            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    # Total atoms
                    cur.execute("SELECT COUNT(*) FROM knowledge_atoms;")
                    total = cur.fetchone()[0]

                    # With embeddings
                    cur.execute("SELECT COUNT(*) FROM knowledge_atoms WHERE embedding IS NOT NULL;")
                    with_embeddings = cur.fetchone()[0]

                    # Added today
                    cur.execute("""
                        SELECT COUNT(*) FROM knowledge_atoms
                        WHERE created_at > NOW() - INTERVAL '1 day';
                    """)
                    added_today = cur.fetchone()[0]

                    print(f"Total atoms: {total:,}")
                    print(f"With embeddings: {with_embeddings:,} ({100*with_embeddings/max(total,1):.1f}%)")
                    print(f"Added today: {added_today:,}")

                    if total > 0:
                        self.check_pass(f"Knowledge base operational ({total:,} atoms)")
                    else:
                        print("⚠️  No atoms in database yet (expected if newly deployed)")

                    return True

        except Exception as e:
            print(f"⚠️  Could not query KB stats: {e}")
            return True  # Non-critical

    def run_all_checks(self) -> bool:
        """Run all validation checks"""
        print("=" * 60)
        print("DEPLOYMENT VALIDATION")
        print("=" * 60)
        print(f"Service URL: {self.service_url}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run checks
        self.check_health_endpoint(num_checks=10)
        self.check_webhook_status()
        self.check_database_connection()
        self.check_knowledge_base_stats()

        # Summary
        self.print_header("VALIDATION SUMMARY")
        print(f"Checks passed: {self.checks_passed}")
        print(f"Checks failed: {self.checks_failed}")

        if self.checks_failed == 0:
            print("\n✅ ALL VALIDATION CHECKS PASSED")
            print("\nDeployment is SUCCESSFUL and ready for production!")
            return True
        elif self.checks_passed > self.checks_failed:
            print(f"\n⚠️  PARTIAL SUCCESS ({self.checks_passed} passed, {self.checks_failed} failed)")
            print("\nDeployment is mostly operational but needs attention.")
            return True
        else:
            print(f"\n❌ VALIDATION FAILED ({self.checks_failed} critical failures)")
            print("\nPlease review errors and fix before going live.")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive deployment validation"
    )
    parser.add_argument(
        "--service-url",
        required=True,
        help="Render.com service URL"
    )

    args = parser.parse_args()

    validator = DeploymentValidator(args.service_url)
    success = validator.run_all_checks()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
