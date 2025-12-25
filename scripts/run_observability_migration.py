#!/usr/bin/env python3
"""Run observability database migration."""

import sys
import os
from pathlib import Path
import psycopg
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()


def main():
    print("=" * 80)
    print("OBSERVABILITY PLATFORM - DATABASE MIGRATION")
    print("=" * 80)
    print()

    # Read SQL migration file
    migration_file = project_root / "docs" / "database" / "observability_migration.sql"

    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    print(f"[OK] Loaded migration SQL ({len(sql):,} bytes)")
    print()

    # Connect to VPS PostgreSQL database
    print("Connecting to VPS database...")

    vps_host = os.getenv("VPS_KB_HOST", "72.60.175.144")
    vps_port = os.getenv("VPS_KB_PORT", "5432")
    vps_user = os.getenv("VPS_KB_USER", "rivet")
    vps_password = os.getenv("VPS_KB_PASSWORD", "rivet_factory_2025!")
    vps_database = os.getenv("VPS_KB_DATABASE", "rivet")

    print(f"  Host: {vps_host}")
    print(f"  Port: {vps_port}")
    print(f"  Database: {vps_database}")
    print(f"  User: {vps_user}")
    print()

    try:
        conn = psycopg.connect(
            host=vps_host,
            port=vps_port,
            dbname=vps_database,
            user=vps_user,
            password=vps_password,
            connect_timeout=10
        )
        print("[OK] Connected to VPS PostgreSQL")
        print()
    except Exception as e:
        print(f"ERROR: Could not connect to VPS database: {e}")
        return False

    # Execute migration
    print("Executing migration...")
    cursor = conn.cursor()

    try:
        # Execute the entire SQL file at once
        cursor.execute(sql)
        conn.commit()
        print("[OK] Migration executed successfully")
        print()

    except Exception as e:
        print(f"ERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False

    # Verify tables created
    print("Verifying tables...")
    cursor.execute("""
        SELECT tablename,
               pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename LIKE 'ingestion_metrics%'
        ORDER BY tablename
    """)

    tables = cursor.fetchall()

    if not tables:
        print("WARNING: No tables found matching 'ingestion_metrics%'")
        cursor.close()
        conn.close()
        return False

    print(f"[OK] Created {len(tables)} tables:")
    for table, size in tables:
        print(f"  - {table:40} {size}")
    print()

    # Verify indexes
    print("Verifying indexes...")
    cursor.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename LIKE 'ingestion_metrics%'
        ORDER BY indexname
    """)

    indexes = cursor.fetchall()
    print(f"[OK] Created {len(indexes)} indexes")
    print()

    # Verify function
    print("Verifying helper function...")
    cursor.execute("""
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_name = 'aggregate_hourly_metrics'
    """)

    functions = cursor.fetchall()
    if functions:
        print(f"[OK] Created function: aggregate_hourly_metrics()")
    else:
        print("WARNING: Function aggregate_hourly_metrics() not found")
    print()

    cursor.close()
    conn.close()

    print("=" * 80)
    print("MIGRATION COMPLETE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Implement IngestionMonitor class")
    print("2. Implement TelegramNotifier class")
    print("3. Hook into ingestion pipeline")
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
