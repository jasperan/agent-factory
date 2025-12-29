#!/bin/bash
# Run database migration 002 - Quality Scoring Columns
# Execute this script directly on the VPS when SSH is stable

set -e  # Exit on error

echo "=========================================="
echo "Running Migration 002: Quality Scoring"
echo "=========================================="

# Run migration via Docker
docker exec -i infra_postgres_1 psql -U rivet -d rivet << 'EOF'
-- Add quality scoring columns
ALTER TABLE knowledge_atoms
ADD COLUMN IF NOT EXISTS manual_quality_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS page_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_direct_pdf BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS manual_type VARCHAR(50) DEFAULT 'unknown';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_manual_quality
ON knowledge_atoms(manual_quality_score DESC, page_count DESC);

CREATE INDEX IF NOT EXISTS idx_manual_type
ON knowledge_atoms(manual_type);

CREATE INDEX IF NOT EXISTS idx_vendor_quality
ON knowledge_atoms(vendor, manual_type, manual_quality_score DESC);

-- Add column comments
COMMENT ON COLUMN knowledge_atoms.manual_quality_score IS
'Quality score (0-100): 90-100=comprehensive, 70-89=technical_doc, 50-69=partial_doc, 0-49=marketing';

COMMENT ON COLUMN knowledge_atoms.page_count IS
'Total pages in source PDF. Used for quality scoring (200+ pages = 30pts).';

COMMENT ON COLUMN knowledge_atoms.is_direct_pdf IS
'True if direct PDF download, false if redirect detected. Redirect penalty: -30pts quality score.';

COMMENT ON COLUMN knowledge_atoms.manual_type IS
'Manual classification: comprehensive_manual (90-100), technical_doc (70-89), partial_doc (50-69), marketing (0-49)';

-- Verification
\echo 'Migration complete! Verifying...'
SELECT
  COUNT(*) as total_atoms,
  COUNT(CASE WHEN manual_quality_score > 0 THEN 1 END) as scored_atoms,
  AVG(CASE WHEN manual_quality_score > 0 THEN manual_quality_score END) as avg_score
FROM knowledge_atoms;
EOF

echo "=========================================="
echo "Migration 002 complete!"
echo "=========================================="
