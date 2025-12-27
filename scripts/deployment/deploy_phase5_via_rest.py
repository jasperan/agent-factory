#!/usr/bin/env python3
"""
Deploy Phase 5 Schema via Supabase REST API

Alternative deployment method when direct PostgreSQL connection fails.
Uses Supabase Python client to execute SQL via REST API.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import subprocess

# Load environment
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

try:
    from supabase import create_client
except ImportError:
    print("ERROR: supabase package not installed")
    print("Run: poetry install")
    sys.exit(1)


def deploy_via_rest():
    """Deploy Phase 5 schema using Supabase REST API."""

    print("=" * 80)
    print("DEPLOYING PHASE 5 SCHEMA VIA SUPABASE REST API")
    print("=" * 80)
    print()

    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("ERROR: Missing Supabase credentials")
        print("Required: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
        sys.exit(1)

    print(f"Connecting to: {url}")
    print()

    # Connect
    try:
        supabase = create_client(url, key)
        print("[OK] Connected to Supabase")
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        sys.exit(1)

    # Read migration SQL
    migration_file = project_root / "docs" / "database" / "phase5_research_pipeline_migration.sql"
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    migration_sql = migration_file.read_text(encoding='utf-8')
    print(f"[OK] Loaded migration SQL ({len(migration_sql)} chars)")
    print()

    # Note about REST API limitation
    print("NOTE: Supabase REST API doesn't support direct SQL execution.")
    print("      The recommended approach is:")
    print()
    print("      OPTION 1: Manual deployment (copy/paste to SQL Editor)")
    print("      OPTION 2: Use Supabase CLI")
    print()
    print("Attempting OPTION 2: Supabase CLI...")
    print()

    # Check if Supabase CLI is installed
    try:
        result = subprocess.run(
            ["supabase", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[OK] Supabase CLI found: {result.stdout.strip()}")
            print()
            print("To deploy using CLI:")
            print("  1. Save migration to supabase/migrations/")
            print("  2. Run: supabase db push")
            print()
        else:
            raise FileNotFoundError()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("[INFO] Supabase CLI not installed")
        print()
        print("Install CLI: npm install -g supabase")
        print("Or use manual deployment (see below)")
        print()

    # Provide manual deployment instructions
    print("=" * 80)
    print("MANUAL DEPLOYMENT REQUIRED")
    print("=" * 80)
    print()
    print("Copy the SQL below and paste into Supabase SQL Editor:")
    print(f"  https://app.supabase.com/project/{url.split('/')[-1].replace('.supabase.co', '')}/sql")
    print()
    print("SQL to execute:")
    print("-" * 80)
    print(migration_sql)
    print("-" * 80)
    print()
    print("After executing SQL, run verification:")
    print("  poetry run python scripts/deployment/verify_phase5_schema.py")
    print()


if __name__ == "__main__":
    deploy_via_rest()
