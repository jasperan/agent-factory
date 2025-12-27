"""Quick database connection test"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import psycopg2

load_dotenv()

print("Testing database connection...")
print(f"DATABASE_PROVIDER: {os.getenv('DATABASE_PROVIDER')}")

try:
    provider = os.getenv("DATABASE_PROVIDER", "neon")
    print(f"\nAttempting connection to {provider}...")

    if provider == "neon":
        db_url = os.getenv("NEON_DB_URL")
        if not db_url:
            print("ERROR: NEON_DB_URL not found in .env")
            sys.exit(1)
        print(f"Connection string: {db_url[:50]}...")  # Show first 50 chars

        conn = psycopg2.connect(db_url, connect_timeout=10)
        print("[OK] Connection successful!")

        # Try a simple query
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"[OK] PostgreSQL version: {version[0][:80]}...")

        cur.close()
        conn.close()
        print("[OK] Connection closed cleanly")

except Exception as e:
    print(f"[FAIL] Connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nDatabase connection test passed!")
