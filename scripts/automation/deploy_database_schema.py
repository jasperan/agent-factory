#!/usr/bin/env python3
"""
Database Schema Deployment Script for Render.

Automatically deploys management tables on startup if they don't exist.
This ensures the Telegram bot has all required tables for management commands.

Tables deployed:
- video_approval_queue
- agent_status
- alert_history

Usage:
    python scripts/automation/deploy_database_schema.py

Exit codes:
    0 - Success (schema deployed or already exists)
    1 - Failure (database connection or deployment error)
"""

import os
import sys
from pathlib import Path
import psycopg


def check_tables_exist(conn) -> dict:
    """
    Check which management tables already exist.

    Args:
        conn: psycopg connection

    Returns:
        Dict with table names as keys, existence as boolean values
    """
    required_tables = [
        'video_approval_queue',
        'agent_status',
        'alert_history'
    ]

    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN %s
        """, (tuple(required_tables),))

        existing = {row[0] for row in cur.fetchall()}

    return {table: table in existing for table in required_tables}


def deploy_schema(conn, sql_file_path: Path):
    """
    Deploy database schema from SQL file.

    Args:
        conn: psycopg connection
        sql_file_path: Path to SQL migration file
    """
    print(f"Reading SQL from: {sql_file_path}")

    sql_content = sql_file_path.read_text(encoding='utf-8')

    print("Executing SQL migration...")

    with conn.cursor() as cur:
        cur.execute(sql_content)

    conn.commit()
    print("✅ Schema deployed successfully")


def main():
    """Main entry point."""
    print("=" * 80)
    print("Database Schema Deployment - Management Tables")
    print("=" * 80)

    # Get database URL from environment
    db_url = os.getenv('NEON_DB_URL') or os.getenv('DATABASE_URL')

    if not db_url:
        print("❌ ERROR: No database URL found")
        print("   Set NEON_DB_URL or DATABASE_URL environment variable")
        sys.exit(1)

    # Mask password in output
    db_url_display = db_url.split('@')[1] if '@' in db_url else db_url
    print(f"Database: ...@{db_url_display}")

    # Find SQL migration file
    project_root = Path(__file__).parent.parent.parent
    sql_file = project_root / "docs" / "database" / "management_tables_migration.sql"

    if not sql_file.exists():
        print(f"❌ ERROR: SQL file not found: {sql_file}")
        sys.exit(1)

    try:
        # Connect to database
        print("Connecting to database...")
        with psycopg.connect(db_url) as conn:
            print("✅ Connected")

            # Check existing tables
            print("\nChecking existing tables...")
            table_status = check_tables_exist(conn)

            for table, exists in table_status.items():
                status = "✅ EXISTS" if exists else "❌ MISSING"
                print(f"  {table}: {status}")

            # Deploy if any tables missing
            if not all(table_status.values()):
                print("\n⚠️  Some tables missing - deploying schema...")
                deploy_schema(conn, sql_file)

                # Verify deployment
                print("\nVerifying deployment...")
                table_status = check_tables_exist(conn)

                all_exist = all(table_status.values())

                for table, exists in table_status.items():
                    status = "✅" if exists else "❌"
                    print(f"  {status} {table}")

                if not all_exist:
                    print("\n❌ ERROR: Schema deployment incomplete")
                    sys.exit(1)

                print("\n✅ Schema deployment complete")

            else:
                print("\n✅ All tables exist - no deployment needed")

    except psycopg.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("=" * 80)
    print("✅ Database schema ready")
    print("=" * 80)


if __name__ == "__main__":
    main()
