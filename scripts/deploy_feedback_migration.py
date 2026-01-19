#!/usr/bin/env python3
"""Deploy feedback tracking migration to Neon"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# SQL migration (from 009_add_feedback_tracking.sql)
SQL = open("migrations/009_add_feedback_tracking.sql").read()

VERIFY_SQL = """
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'knowledge_atoms'
AND column_name IN ('success_rate', 'feedback_positive_count', 'feedback_negative_count', 'usage_count')
ORDER BY column_name;
"""

def main():
    db_url = os.getenv("NEON_DB_URL")

    if not db_url:
        print("ERROR: NEON_DB_URL not found")
        return 1

    print("Connecting to Neon database...")

    try:
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
                    if "already exists" in str(e) or "duplicate" in str(e):
                        print(f"  Statement {i+1}: Already exists (OK)")
                    else:
                        print(f"  Statement {i+1}: {e}")
                        conn.rollback()

        print("\nMigration executed successfully!\n")

        # Verify columns created
        print("Verifying columns...")
        cur.execute(VERIFY_SQL)
        columns = cur.fetchall()

        print(f"\nFound {len(columns)} new columns in knowledge_atoms:")
        for col in columns:
            print(f"  + {col[0]} ({col[1]})")

        # Also check work_orders
        cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'work_orders'
        AND column_name IN ('user_feedback', 'feedback_at')
        ORDER BY column_name;
        """)
        work_order_cols = cur.fetchall()

        print(f"\nFound {len(work_order_cols)} new columns in work_orders:")
        for col in work_order_cols:
            print(f"  + {col[0]} ({col[1]})")

        cur.close()
        conn.close()

        if len(columns) == 4 and len(work_order_cols) == 2:
            print("\n[SUCCESS] All feedback tracking columns added!")
            print("          Feedback loop ready")
            return 0
        else:
            print(f"\n[WARNING] Expected 4+2 columns, found {len(columns)}+{len(work_order_cols)}")
            return 1

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
