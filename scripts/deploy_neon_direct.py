#!/usr/bin/env python3
"""Deploy ingestion chain migration directly to Neon"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# SQL migration (from ingestion_chain_migration.sql)
SQL = open("docs/database/ingestion_chain_migration.sql").read()

VERIFY_SQL = """
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('source_fingerprints', 'ingestion_logs', 'failed_ingestions', 'human_review_queue', 'atom_relations')
ORDER BY table_name;
"""

def main():
    # Get Neon database URL
    db_url = os.getenv("NEON_DB_URL")

    if not db_url:
        print("ERROR: NEON_DB_URL not found in environment")
        return 1

    print("Connecting to Neon database...")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        print("Executing migration...")

        # Split SQL into statements and execute one by one
        statements = [s.strip() for s in SQL.split(';') if s.strip()]

        for i, stmt in enumerate(statements):
            if stmt and not stmt.startswith('--'):
                try:
                    cur.execute(stmt)
                    conn.commit()
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"  Statement {i+1}: Already exists (OK)")
                    else:
                        print(f"  Statement {i+1}: {e}")
                        conn.rollback()

        print("\nMigration executed successfully!\n")

        # Verify tables created
        print("Verifying tables...")
        cur.execute(VERIFY_SQL)
        tables = cur.fetchall()

        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  ✓ {table[0]}")

        cur.close()
        conn.close()

        if len(tables) == 5:
            print("\n SUCCESS: All 5 ingestion tables ready!")
            print("   Ingestion pipeline UNBLOCKED")
            return 0
        else:
            print(f"\n WARNING: Expected 5 tables, found {len(tables)}")
            return 1

    except Exception as e:
        print(f"ERROR executing migration: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
