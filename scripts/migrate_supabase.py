#!/usr/bin/env python3
"""
Automated Supabase Migration Runner

Three methods to run migrations:
1. Direct PostgreSQL connection (BEST - fully automated)
2. Supabase Management API (requires API token)
3. Manual fallback (copy to clipboard)

Usage:
    poetry run python migrate_supabase.py
    poetry run python migrate_supabase.py --method postgres
    poetry run python migrate_supabase.py --method api
    poetry run python migrate_supabase.py --method manual
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def method_1_postgres():
    """
    METHOD 1: Direct PostgreSQL Connection (BEST - FULLY AUTOMATED)

    Uses psycopg2 to connect directly to Supabase PostgreSQL database.
    Requires: SUPABASE_DB_PASSWORD in .env

    Get password from: https://supabase.com/dashboard/project/_/settings/database
    Under "Connection string" → "Password" (click "eye" icon to reveal)
    """
    print("="*70)
    print("METHOD 1: Direct PostgreSQL Connection (FULLY AUTOMATED)")
    print("="*70)

    try:
        import psycopg2
    except ImportError:
        print("\n[ERROR] psycopg2 not installed")
        print("Install: poetry add psycopg2-binary")
        return False

    # Get connection details
    url = os.getenv('SUPABASE_URL')
    password = os.getenv('SUPABASE_DB_PASSWORD')

    if not password:
        print("\n[ERROR] SUPABASE_DB_PASSWORD not found in .env")
        print("\nTo fix:")
        print("1. Go to: https://supabase.com/dashboard/project/_/settings/database")
        print("2. Under 'Connection string' → Click 'eye' icon to reveal password")
        print("3. Add to .env: SUPABASE_DB_PASSWORD=<your_password>")
        return False

    # Extract project ID from URL
    project_id = url.replace('https://', '').split('.')[0]

    # Build connection string
    conn_string = f"postgresql://postgres.{project_id}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

    print(f"\nConnecting to: {project_id}.supabase.co...")

    try:
        # Connect to database
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Read SQL file
        sql_file = Path('docs/supabase_agent_migrations.sql')
        sql = sql_file.read_text(encoding='utf-8')

        print(f"Executing migration ({sql_file.stat().st_size} bytes)...\n")

        # Execute SQL
        cursor.execute(sql)
        conn.commit()

        print("[OK] Migration completed successfully!")
        print("\nTables created:")

        # Verify tables
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE 'agent_%' OR tablename LIKE 'approval_%' OR tablename LIKE 'video_%' OR tablename LIKE 'webhook_%'
            ORDER BY tablename
        """)

        tables = cursor.fetchall()
        for (table,) in tables:
            print(f"  - {table}")

        cursor.close()
        conn.close()

        print("\n" + "="*70)
        print("[SUCCESS] Automated migration complete!")
        print("="*70)
        return True

    except psycopg2.Error as e:
        print(f"\n[ERROR] PostgreSQL error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify SUPABASE_DB_PASSWORD is correct")
        print("2. Check database is accessible (not paused)")
        print("3. Try method 2 (API) or method 3 (manual)")
        return False


def method_2_api():
    """
    METHOD 2: Supabase Management API (AUTOMATED)

    Uses Supabase Management API to execute SQL.
    Requires: SUPABASE_ACCESS_TOKEN (personal access token)

    Get token from: https://supabase.com/dashboard/account/tokens
    Click "Generate new token" → Copy token → Add to .env
    """
    print("="*70)
    print("METHOD 2: Supabase Management API (AUTOMATED)")
    print("="*70)

    access_token = os.getenv('SUPABASE_ACCESS_TOKEN')

    if not access_token:
        print("\n[ERROR] SUPABASE_ACCESS_TOKEN not found in .env")
        print("\nTo fix:")
        print("1. Go to: https://supabase.com/dashboard/account/tokens")
        print("2. Click 'Generate new token'")
        print("3. Add to .env: SUPABASE_ACCESS_TOKEN=<your_token>")
        return False

    try:
        import requests
    except ImportError:
        print("\n[ERROR] requests not installed")
        print("Install: poetry add requests")
        return False

    url = os.getenv('SUPABASE_URL')
    project_id = url.replace('https://', '').split('.')[0]

    # Read SQL file
    sql_file = Path('docs/supabase_agent_migrations.sql')
    sql = sql_file.read_text(encoding='utf-8')

    print(f"\nExecuting via Management API...")

    # Supabase Management API endpoint
    api_url = f"https://api.supabase.com/v1/projects/{project_id}/database/query"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": sql
    }

    response = requests.post(api_url, json=payload, headers=headers)

    if response.status_code == 200:
        print("[OK] Migration completed successfully!")
        print("\n" + "="*70)
        print("[SUCCESS] Automated migration complete!")
        print("="*70)
        return True
    else:
        print(f"\n[ERROR] API request failed: {response.status_code}")
        print(f"Response: {response.text}")
        print("\nTry method 1 (postgres) or method 3 (manual)")
        return False


def method_3_manual():
    """
    METHOD 3: Manual Copy-Paste (FALLBACK)

    Copies SQL to clipboard, opens browser to SQL editor.
    User pastes and clicks RUN.
    """
    print("="*70)
    print("METHOD 3: Manual Copy-Paste (FALLBACK)")
    print("="*70)

    import subprocess

    # Copy to clipboard
    sql_file = Path('docs/supabase_agent_migrations.sql')

    try:
        # Windows: clip
        subprocess.run(['clip'], input=sql_file.read_bytes(), check=True)
        print("\n[OK] SQL copied to clipboard!")
    except Exception as e:
        print(f"\n[ERROR] Could not copy to clipboard: {e}")
        print("Manually copy: docs/supabase_agent_migrations.sql")

    # Open browser
    url = os.getenv('SUPABASE_URL')
    project_id = url.replace('https://', '').split('.')[0]
    sql_editor_url = f"https://supabase.com/dashboard/project/{project_id}/sql/new"

    print(f"\nOpening SQL Editor: {sql_editor_url}")

    try:
        # Windows: start
        subprocess.run(['cmd', '/c', 'start', sql_editor_url], check=True)
    except Exception as e:
        print(f"Could not open browser: {e}")
        print(f"Manually open: {sql_editor_url}")

    print("\nSteps:")
    print("1. SQL Editor should open in browser")
    print("2. Paste SQL (Ctrl+V)")
    print("3. Click RUN button")
    print("4. Wait for success message")

    return None  # Not automated, user must complete


def main():
    parser = argparse.ArgumentParser(description='Run Supabase migrations')
    parser.add_argument('--method', choices=['postgres', 'api', 'manual'],
                       help='Migration method (default: try all in order)')
    args = parser.parse_args()

    print("\n" + "="*70)
    print("SUPABASE MIGRATION AUTOMATION")
    print("="*70)

    if args.method == 'postgres':
        success = method_1_postgres()
    elif args.method == 'api':
        success = method_2_api()
    elif args.method == 'manual':
        success = method_3_manual()
    else:
        # Try methods in order until one succeeds
        print("\nTrying automated methods...\n")

        # Try METHOD 1: PostgreSQL (best)
        success = method_1_postgres()

        if not success:
            print("\nTrying METHOD 2: Management API...\n")
            success = method_2_api()

        if not success:
            print("\nFalling back to METHOD 3: Manual...\n")
            success = method_3_manual()

    if success:
        # Verify tables
        print("\nVerifying tables...")
        os.system('poetry run python check_tables.py')

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
