#!/usr/bin/env python3
"""Test Neon database connection"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Test 1: Check if psycopg2 is available
try:
    import psycopg2
    print("[1/3] psycopg2: [OK]")
except ImportError:
    print("[1/3] psycopg2: [FAIL] Not installed")
    sys.exit(1)

# Test 2: Check if NEON_DB_URL exists
neon_url = os.getenv('NEON_DB_URL')
if not neon_url:
    print("[2/3] NEON_DB_URL: [FAIL] Not found in .env")
    sys.exit(1)
print(f"[2/3] NEON_DB_URL: [OK] {neon_url[:60]}...")

# Test 3: Connect to Neon
print("[3/3] Testing connection...")
try:
    conn = psycopg2.connect(neon_url)
    print("      [OK] Connected successfully")

    # Get PostgreSQL version
    cur = conn.cursor()
    cur.execute('SELECT version();')
    version = cur.fetchone()[0]
    print(f"      [OK] {version[:80]}...")

    # Check if pgvector is installed
    cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    if cur.fetchone():
        print("      [OK] pgvector extension found")
    else:
        print("      [WARN] pgvector extension not found (needs to be enabled)")

    cur.close()
    conn.close()
    print("\n[SUCCESS] Neon database is ready!")

except Exception as e:
    print(f"      [FAIL] Connection error: {e}")
    sys.exit(1)
