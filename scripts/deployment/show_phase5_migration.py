#!/usr/bin/env python3
"""
Display Phase 5 Migration SQL

Shows the SQL that needs to be pasted into Supabase SQL Editor.
Simplest deployment method when automated deployment fails.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
migration_file = project_root / "docs" / "database" / "phase5_research_pipeline_migration.sql"

if not migration_file.exists():
    print(f"ERROR: Migration file not found: {migration_file}")
    sys.exit(1)

migration_sql = migration_file.read_text(encoding='utf-8')

print("=" * 80)
print("PHASE 5 SCHEMA DEPLOYMENT - SQL TO PASTE")
print("=" * 80)
print()
print("1. Open Supabase SQL Editor:")
print("   https://app.supabase.com")
print()
print("2. Select your RIVET Pro project")
print()
print("3. Click 'SQL Editor' in left sidebar")
print()
print("4. Create new query and paste the SQL below:")
print()
print("=" * 80)
print(migration_sql)
print("=" * 80)
print()
print("5. Click 'Run' (or press F5)")
print()
print("6. After execution, verify deployment:")
print("   poetry run python scripts/deployment/verify_phase5_schema.py")
print()
