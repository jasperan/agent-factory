#!/usr/bin/env python3
"""Deploy schema to Neon database"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def deploy_schema():
    """Deploy the complete schema to Neon."""

    # Get Neon URL
    neon_url = os.getenv('NEON_DB_URL')
    if not neon_url:
        print("[FAIL] NEON_DB_URL not found in .env")
        sys.exit(1)

    # Read schema file
    schema_file = Path("docs/database/supabase_complete_schema.sql")
    if not schema_file.exists():
        print(f"[FAIL] Schema file not found: {schema_file}")
        sys.exit(1)

    print("="*80)
    print("DEPLOYING SCHEMA TO NEON DATABASE")
    print("="*80)
    print()

    schema_sql = schema_file.read_text()
    print(f"[1/3] Schema file: {schema_file}")
    print(f"      Size: {len(schema_sql)} bytes")

    # Connect to Neon
    print()
    print("[2/3] Connecting to Neon...")
    try:
        conn = psycopg2.connect(neon_url)
        conn.autocommit = True  # Auto-commit each statement
        print("      [OK] Connected")
    except Exception as e:
        print(f"      [FAIL] Connection error: {e}")
        sys.exit(1)

    # Execute schema
    print()
    print("[3/3] Executing schema SQL...")
    try:
        cur = conn.cursor()

        # Execute the entire schema as one block
        cur.execute(schema_sql)

        print(f"      [OK] Schema deployed successfully")

    except Exception as e:
        print(f"      [FAIL] Deployment error: {e}")
        conn.close()
        sys.exit(1)

    # Verify tables created
    print()
    print("Verifying tables...")
    try:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]

        expected_tables = [
            'knowledge_atoms',
            'research_staging',
            'video_scripts',
            'upload_jobs',
            'agent_messages',
            'session_memories',
            'settings'
        ]

        print()
        for table in expected_tables:
            if table in tables:
                # Count rows
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"      [OK] {table:20s} ({count} rows)")
            else:
                print(f"      [MISSING] {table}")

        created_count = len([t for t in expected_tables if t in tables])

        cur.close()
        conn.close()

        print()
        print("="*80)
        if created_count == len(expected_tables):
            print("[SUCCESS] All tables deployed to Neon!")
        else:
            print(f"[PARTIAL] {created_count}/{len(expected_tables)} tables deployed")
        print("="*80)
        print()
        print("Next steps:")
        print("  1. Update .env: DATABASE_PROVIDER=neon")
        print("  2. Run: poetry run python scripts/knowledge/upload_atoms_to_supabase.py")
        print("     (Will automatically use Neon from DATABASE_PROVIDER)")

    except Exception as e:
        print(f"      [FAIL] Verification error: {e}")
        conn.close()
        sys.exit(1)

if __name__ == "__main__":
    deploy_schema()
