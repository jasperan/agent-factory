#!/usr/bin/env python3
"""
Direct Schema Deployment via PostgreSQL

Uses psycopg to execute SQL directly, bypassing Supabase REST API limitations.
Enables autonomous deployment without manual SQL Editor intervention.

Constitutional Mandate: Article 0.3 - "Use dangerously skip permissions aggressively"
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


def get_postgres_url():
    """Get direct PostgreSQL connection URL."""
    # Try Neon first (primary provider from .env.phone_control)
    neon_url = os.getenv("NEON_DB_URL")
    if neon_url:
        return ("neon", neon_url)

    # Try Supabase as fallback
    db_host = os.getenv("SUPABASE_DB_HOST")
    db_port = os.getenv("SUPABASE_DB_PORT", "5432")
    db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
    db_user = os.getenv("SUPABASE_DB_USER", "postgres")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")

    if all([db_host, db_password]):
        return ("supabase", f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

    return (None, None)


def deploy_schema():
    """Deploy complete schema via direct PostgreSQL connection."""

    print("=" * 80)
    print("DIRECT SCHEMA DEPLOYMENT (PostgreSQL)")
    print("=" * 80)
    print()

    # Get connection URL
    provider, db_url = get_postgres_url()
    if not db_url:
        print("ERROR: No database connection configured")
        print()
        print("Need either:")
        print("  1. NEON_DB_URL in .env")
        print("  2. SUPABASE_DB_HOST, SUPABASE_DB_PASSWORD in .env")
        sys.exit(1)

    # Hide password in output
    safe_url = db_url.split('@')[1] if '@' in db_url else db_url
    print(f"Provider: {provider}")
    print(f"Connecting to: {safe_url}")
    print()

    # Read schema file
    schema_file = project_root / "docs" / "database" / "supabase_complete_schema.sql"
    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        sys.exit(1)

    schema_sql = schema_file.read_text(encoding='utf-8')
    print(f"Loaded schema: {len(schema_sql)} chars, {schema_sql.count('CREATE TABLE')} tables")
    print()

    # Connect and deploy
    try:
        print("Connecting to database...")
        conn = psycopg.connect(db_url)
        print("[OK] Connected")
        print()

        print("Deploying schema...")
        print("This will create:")
        print("  - pgvector extension")
        print("  - 7 tables (knowledge_atoms, research_staging, video_scripts, etc.)")
        print("  - Vector indexes (HNSW)")
        print("  - Full-text search indexes (GIN)")
        print("  - 8+ performance indexes")
        print()

        # Execute schema
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()

        print("[OK] Schema deployed successfully!")
        print()

        # Verify tables
        print("Verifying deployment...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN (
                    'knowledge_atoms',
                    'research_staging',
                    'video_scripts',
                    'upload_jobs',
                    'agent_messages',
                    'session_memories',
                    'settings'
                )
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]

        print(f"Tables created: {len(tables)}/7")
        for table in tables:
            print(f"  - {table}")
        print()

        if len(tables) == 7:
            print("[OK] All 7 tables deployed successfully!")
            print()
            print("=" * 80)
            print("NEXT STEP: Upload atoms")
            print("=" * 80)
            print()
            print("Run: poetry run python scripts/knowledge/upload_atoms_to_supabase.py")
            print()
        else:
            print(f"[WARNING] Expected 7 tables, got {len(tables)}")
            missing = set(['knowledge_atoms', 'research_staging', 'video_scripts',
                          'upload_jobs', 'agent_messages', 'session_memories', 'settings']) - set(tables)
            if missing:
                print(f"Missing tables: {', '.join(missing)}")

        conn.close()

    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    deploy_schema()
