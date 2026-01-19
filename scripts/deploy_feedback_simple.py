#!/usr/bin/env python3
"""Deploy feedback tracking columns directly (no complex functions)"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Simple SQL statements (one at a time)
STATEMENTS = [
    # Add columns to knowledge_atoms
    """
    ALTER TABLE knowledge_atoms
    ADD COLUMN IF NOT EXISTS success_rate FLOAT DEFAULT NULL
    """,
    """
    ALTER TABLE knowledge_atoms
    ADD COLUMN IF NOT EXISTS feedback_positive_count INTEGER DEFAULT 0
    """,
    """
    ALTER TABLE knowledge_atoms
    ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0
    """,
    """
    ALTER TABLE knowledge_atoms
    DROP CONSTRAINT IF EXISTS valid_success_rate
    """,
    """
    ALTER TABLE knowledge_atoms
    ADD CONSTRAINT valid_success_rate CHECK (
        success_rate IS NULL OR (success_rate >= 0.0 AND success_rate <= 1.0)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_success_rate
    ON knowledge_atoms(success_rate)
    WHERE success_rate IS NOT NULL
    """,
    # Create FeedbackType enum
    """
    DO $$ BEGIN
        CREATE TYPE FeedbackType AS ENUM ('positive', 'negative', 'none');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$
    """,
    # Add columns to work_orders
    """
    ALTER TABLE work_orders
    ADD COLUMN IF NOT EXISTS user_feedback FeedbackType DEFAULT 'none'
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_work_orders_feedback
    ON work_orders(user_feedback)
    WHERE user_feedback != 'none'
    """,
]

def main():
    db_url = os.getenv("NEON_DB_URL")

    if not db_url:
        print("ERROR: NEON_DB_URL not found")
        return 1

    print("Deploying feedback tracking columns...")

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        for i, stmt in enumerate(STATEMENTS, 1):
            try:
                cur.execute(stmt)
                conn.commit()
                print(f"  Statement {i}: OK")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e):
                    print(f"  Statement {i}: Already exists (OK)")
                else:
                    print(f"  Statement {i}: {e}")
                conn.rollback()

        print("\nVerifying columns...")

        # Check knowledge_atoms columns
        cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'knowledge_atoms'
        AND column_name IN ('success_rate', 'feedback_positive_count', 'feedback_negative_count', 'usage_count')
        ORDER BY column_name;
        """)
        ka_cols = cur.fetchall()

        print(f"\nknowledge_atoms columns ({len(ka_cols)}/4):")
        for col in ka_cols:
            print(f"  + {col[0]} ({col[1]})")

        # Check work_orders columns
        cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'work_orders'
        AND column_name IN ('user_feedback', 'feedback_at')
        ORDER BY column_name;
        """)
        wo_cols = cur.fetchall()

        print(f"\nwork_orders columns ({len(wo_cols)}/2):")
        for col in wo_cols:
            print(f"  + {col[0]} ({col[1]})")

        cur.close()
        conn.close()

        if len(ka_cols) >= 3 and len(wo_cols) >= 1:
            print("\n[SUCCESS] Feedback tracking columns deployed!")
            return 0
        else:
            print(f"\n[WARNING] Some columns missing")
            return 1

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
