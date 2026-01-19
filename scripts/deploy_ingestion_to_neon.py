#!/usr/bin/env python3
"""Deploy ingestion chain migration using DatabaseManager (multi-provider)"""

import asyncio
from pathlib import Path
from agent_factory.core.database_manager import DatabaseManager

async def main():
    print("Deploying ingestion chain migration to database...")

    # Read migration SQL
    sql_file = Path(__file__).parent / "docs" / "database" / "ingestion_chain_migration.sql"

    if not sql_file.exists():
        print(f"ERROR: Migration file not found: {sql_file}")
        return 1

    migration_sql = sql_file.read_text()

    # Use DatabaseManager with failover
    db = DatabaseManager()

    try:
        print(f"Using provider: {db.current_provider}")

        # Execute migration (split into individual statements to avoid issues)
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for i, statement in enumerate(statements):
            if statement and not statement.startswith('COMMENT'):
                try:
                    await asyncio.to_thread(
                        db.execute_query,
                        statement,
                        fetch_mode="none"
                    )
                    print(f"  Executed statement {i+1}/{len(statements)}")
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"  Warning on statement {i+1}: {e}")

        print("\nMigration executed successfully!")

        # Verify tables
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

        print(f"\nCreated {len(tables)} tables:")
        for table in tables:
            print(f"  ✓ {table}")

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
    exit(asyncio.run(main()))
