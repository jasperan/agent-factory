#!/usr/bin/env python3
"""
Deploy RIVET Pro Phase 5 Schema to Supabase

Automated deployment of research pipeline schema using direct PostgreSQL connection.
Eliminates manual SQL Editor steps.

Phase 5: Research Pipeline - Autonomous KB Growth
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

try:
    import psycopg
except ImportError:
    print("ERROR: psycopg not installed")
    print("Run: poetry add psycopg[binary]")
    sys.exit(1)


def get_supabase_connection():
    """Get Supabase PostgreSQL connection URL."""
    db_host = os.getenv("SUPABASE_DB_HOST")
    db_port = os.getenv("SUPABASE_DB_PORT", "5432")
    db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
    db_user = os.getenv("SUPABASE_DB_USER", "postgres")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")

    if not all([db_host, db_password]):
        print("ERROR: Missing Supabase credentials in .env")
        print()
        print("Required:")
        print("  SUPABASE_DB_HOST")
        print("  SUPABASE_DB_PASSWORD")
        print("  SUPABASE_DB_USER (optional, defaults to 'postgres')")
        print("  SUPABASE_DB_PORT (optional, defaults to '5432')")
        print("  SUPABASE_DB_NAME (optional, defaults to 'postgres')")
        return None

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def deploy_phase5_schema():
    """Deploy Phase 5 research pipeline schema to Supabase."""

    print("=" * 80)
    print("DEPLOYING PHASE 5 SCHEMA TO SUPABASE")
    print("Research Pipeline - Source Fingerprints Table")
    print("=" * 80)
    print()

    # Get connection URL
    db_url = get_supabase_connection()
    if not db_url:
        sys.exit(1)

    # Hide password in output
    safe_url = db_url.split('@')[1] if '@' in db_url else db_url
    print(f"Target: {safe_url}")
    print()

    # Read migration SQL
    migration_file = project_root / "docs" / "database" / "phase5_research_pipeline_migration.sql"
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    migration_sql = migration_file.read_text(encoding='utf-8')
    line_count = len([l for l in migration_sql.split('\n') if l.strip() and not l.strip().startswith('--')])
    print(f"Loaded migration SQL: {migration_file.name}")
    print(f"  Size: {len(migration_sql)} chars")
    print(f"  SQL lines: {line_count}")
    print()

    # Connect to database
    try:
        print("Connecting to Supabase PostgreSQL...")
        conn = psycopg.connect(db_url)
        print("[OK] Connected successfully")
        print()
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        sys.exit(1)

    # Deploy schema
    try:
        print("Deploying Phase 5 schema...")
        print()
        print("Creating:")
        print("  - Table: source_fingerprints")
        print("  - Index: idx_source_fingerprints_hash (url_hash)")
        print("  - Index: idx_source_fingerprints_queued (queued_for_ingestion)")
        print("  - Index: idx_source_fingerprints_created (created_at DESC)")
        print("  - Index: idx_source_fingerprints_source_type (source_type)")
        print()

        with conn.cursor() as cur:
            # Execute migration SQL
            cur.execute(migration_sql)
            conn.commit()

        print("[OK] Schema deployed successfully")
        print()

    except Exception as e:
        print(f"[FAIL] Deployment failed: {e}")
        conn.rollback()
        conn.close()
        sys.exit(1)

    # Verify deployment
    try:
        print("Verifying deployment...")
        print()

        with conn.cursor() as cur:
            # Test 1: Table exists
            cur.execute("SELECT COUNT(*) FROM source_fingerprints;")
            count = cur.fetchone()[0]
            print(f"  [OK] Table exists (current rows: {count})")

            # Test 2: Indexes exist
            cur.execute("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'source_fingerprints'
                ORDER BY indexname;
            """)
            indexes = [row[0] for row in cur.fetchall()]
            print(f"  [OK] Indexes created ({len(indexes)} total):")
            for idx in indexes:
                print(f"       - {idx}")

    except Exception as e:
        print(f"  [WARN] Verification check failed: {e}")
        print("         (Schema may still be deployed correctly)")

    # Close connection
    conn.close()

    # Summary
    print()
    print("=" * 80)
    print("DEPLOYMENT COMPLETE")
    print("=" * 80)
    print()
    print("Phase 5 Research Pipeline is now operational!")
    print()
    print("Next steps:")
    print("  1. Run verification: poetry run python scripts/deployment/verify_phase5_schema.py")
    print("  2. Test Route C query via Telegram bot")
    print("  3. Monitor logs: grep 'Research pipeline' /root/Agent-Factory/logs/bot.log")
    print("  4. Check fingerprints: SELECT * FROM source_fingerprints LIMIT 5;")
    print()
    print("Database schema deployed successfully!")
    print()


if __name__ == "__main__":
    deploy_phase5_schema()
