"""Run Phase 5 enrichment tracking migration."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.core.database_manager import DatabaseManager

db = DatabaseManager()

# SQL migration statements
sqls = [
    "ALTER TABLE gap_requests ADD COLUMN IF NOT EXISTS enrichment_type VARCHAR(50);",
    "ALTER TABLE gap_requests ADD COLUMN IF NOT EXISTS sources_queued INTEGER DEFAULT 0;",
    "ALTER TABLE gap_requests ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;",
    """CREATE INDEX IF NOT EXISTS idx_gap_requests_enrichment
    ON gap_requests(ingestion_completed, priority_score DESC, first_requested_at ASC)
    WHERE enrichment_type = 'thin_coverage';""",
    "COMMENT ON COLUMN gap_requests.enrichment_type IS 'Type of enrichment: thin_coverage (Route B) or no_coverage (Route C)';",
    "COMMENT ON COLUMN gap_requests.sources_queued IS 'Number of source URLs queued for ingestion';",
    "COMMENT ON COLUMN gap_requests.processed_at IS 'When enrichment worker processed this gap';"
]

print("=" * 80)
print("Phase 5 Enrichment Tracking Migration")
print("=" * 80)
print()

success_count = 0
for i, sql in enumerate(sqls, 1):
    try:
        db.execute_query(sql, fetch_mode='none')
        print(f"✓ Step {i}/{len(sqls)}: {sql[:70]}...")
        success_count += 1
    except Exception as e:
        print(f"✗ Step {i}/{len(sqls)} failed: {e}")
        print(f"  SQL: {sql}")

print()
print("=" * 80)
print(f"Migration complete: {success_count}/{len(sqls)} statements succeeded")
print("=" * 80)
