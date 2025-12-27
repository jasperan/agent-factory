"""
Run Migration 003: RIVET Backend Schema

This script executes the database migration to create 6 new tables:
- machines
- prints
- equipment_manuals
- print_chat_history
- context_extractions
- manual_gaps

Usage:
    poetry run python scripts/run_migration_003.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.core.database_manager import DatabaseManager


def run_migration():
    """Execute migration 003."""

    print("=" * 70)
    print("RIVET BACKEND SCHEMA MIGRATION")
    print("Migration 003: TAB 1 Backend + Knowledge Infrastructure")
    print("=" * 70)
    print()

    # Read migration SQL
    migration_file = project_root / "migrations" / "003_rivet_backend_schema.sql"

    if not migration_file.exists():
        print(f"[FAIL] Migration file not found: {migration_file}")
        sys.exit(1)

    print(f"Reading migration from: {migration_file}")
    sql = migration_file.read_text(encoding='utf-8')

    # Initialize database manager
    print("Initializing database manager...")
    db = DatabaseManager()

    # Check database health
    print("Checking database connection...")
    health_status = db.health_check_all()

    healthy_providers = [name for name, status in health_status.items() if status]
    if not healthy_providers:
        print("[FAIL] No healthy database providers available!")
        print("Health status:", health_status)
        sys.exit(1)

    print(f"[ OK ] Connected to: {db.primary_provider}")
    print(f"       Healthy providers: {', '.join(healthy_providers)}")
    print()

    # Execute migration
    print("Executing migration...")
    print("-" * 70)

    try:
        # Split SQL into statements (PostgreSQL NOTICE blocks need special handling)
        # We'll execute the whole file as one transaction
        result = db.execute_query(sql, fetch_mode="none")

        print("-" * 70)
        print()
        print("[ OK ] Migration completed successfully!")
        print()
        print("Created tables:")
        print("  - machines")
        print("  - prints")
        print("  - equipment_manuals")
        print("  - print_chat_history")
        print("  - context_extractions")
        print("  - manual_gaps")
        print()
        print("Phase 2 tables (commented out, ready for future):")
        print("  - equipment_subsystems")
        print("  - equipment_components")
        print("  - knowledge_atoms")
        print("  - ai_research_jobs")
        print("  - ai_generated_resources")
        print("  - resource_feedback")
        print()

        # Verify tables created
        print("Verifying tables...")
        verify_tables(db)

    except Exception as e:
        print("[FAIL] Migration failed!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def verify_tables(db: DatabaseManager):
    """Verify that all tables were created."""

    expected_tables = [
        "machines",
        "prints",
        "equipment_manuals",
        "print_chat_history",
        "context_extractions",
        "manual_gaps"
    ]

    for table in expected_tables:
        try:
            # Try to query table
            result = db.execute_query(
                f"SELECT COUNT(*) FROM {table}",
                fetch_mode="one"
            )
            print(f"  [ OK ] {table} - {result[0]} rows")
        except Exception as e:
            print(f"  [FAIL] {table} - NOT FOUND ({e})")


if __name__ == "__main__":
    run_migration()
