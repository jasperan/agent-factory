#!/usr/bin/env python3
"""Verify ingestion chain tables exist"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

VERIFY_SQL = """
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('source_fingerprints', 'ingestion_logs', 'failed_ingestions', 'human_review_queue', 'atom_relations')
ORDER BY table_name;
"""

def main():
    db_url = os.getenv("NEON_DB_URL")

    if not db_url:
        print("ERROR: NEON_DB_URL not found")
        return 1

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute(VERIFY_SQL)
        tables = cur.fetchall()

        print(f"\nIngestion Chain Tables ({len(tables)}/5):")
        print("=" * 40)
        for table in tables:
            print(f"  + {table[0]}")

        cur.close()
        conn.close()

        if len(tables) == 5:
            print("\n[SUCCESS] All 5 ingestion tables ready!")
            print("          Ingestion pipeline UNBLOCKED")
            return 0
        else:
            print(f"\n[WARNING] Expected 5 tables, found {len(tables)}")
            return 1

    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
