"""Deploy Slack Supervisor database schema to production."""

import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def deploy_schema():
    """Deploy database schema using asyncpg."""
    try:
        import asyncpg
    except ImportError:
        print("[ERROR] asyncpg not installed. Run: poetry install")
        return False

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL not found in .env")
        return False

    print("="*60)
    print("Deploying Slack Supervisor Database Schema")
    print("="*60)
    print(f"\nDatabase: {database_url.split('@')[1] if '@' in database_url else 'configured'}")
    print("")

    # Read schema
    try:
        with open("sql/supervisor_schema.sql", "r") as f:
            schema_sql = f.read()
        print(f"[OK] Schema file loaded ({len(schema_sql)} bytes)")
    except FileNotFoundError:
        print("[ERROR] sql/supervisor_schema.sql not found")
        return False

    # Connect and deploy
    try:
        print("[...] Connecting to database...")
        conn = await asyncpg.connect(database_url)
        print("[OK] Connected")

        print("[...] Deploying schema...")
        await conn.execute(schema_sql)
        print("[OK] Schema deployed")

        # Verify tables created
        print("[...] Verifying tables...")
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'agent_%'
            ORDER BY table_name
        """)

        if tables:
            print(f"[OK] {len(tables)} tables created:")
            for row in tables:
                print(f"     - {row['table_name']}")
        else:
            print("[WARN] No tables found (may already exist)")

        await conn.close()
        print("\n[OK] Database schema deployment complete")
        return True

    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(deploy_schema())
    sys.exit(0 if success else 1)
