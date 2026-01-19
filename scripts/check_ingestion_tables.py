#!/usr/bin/env python3
"""Check if ingestion chain tables already exist"""

import asyncio
from agent_factory.core.database_manager import DatabaseManager

async def main():
    print("Checking for ingestion chain tables...")

    db = DatabaseManager()
    print(f"Using provider: {db.current_provider}")

    try:
        # Check for tables
        verify_sql = """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('source_fingerprints', 'ingestion_logs', 'failed_ingestions', 'human_review_queue', 'atom_relations')
        ORDER BY table_name;
        """

        result = await asyncio.to_thread(
            db.execute_query,
            verify_sql,
            fetch_mode="all"
        )

        tables = [row[0] for row in result] if result else []

        if len(tables) == 5:
            print(f"\nALL 5 tables already exist:")
            for table in tables:
                print(f"  ✓ {table}")
            print("\n SUCCESS: Ingestion tables are ready!")
            print("   No migration needed - tables already deployed")
            return 0
        elif len(tables) > 0:
            print(f"\nFound {len(tables)} of 5 tables:")
            for table in tables:
                print(f"  ✓ {table}")
            print("\n PARTIAL: Some tables exist, migration may be incomplete")
            return 1
        else:
            print("\n NO tables found - migration needed")
            return 2

    except Exception as e:
        print(f"ERROR checking tables: {e}")
        import traceback
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    exit(asyncio.run(main()))
