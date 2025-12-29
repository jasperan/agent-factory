-- Migration 002: Add Quality Scoring Columns to knowledge_atoms
-- Date: December 29, 2025
-- Purpose: Enable quality-based retrieval for comprehensive manuals

-- Description:
-- Adds metadata columns to track manual quality and prioritize comprehensive
-- documentation over partial docs and redirects.

-- Add quality scoring columns
ALTER TABLE knowledge_atoms
ADD COLUMN IF NOT EXISTS manual_quality_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS page_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_direct_pdf BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS manual_type VARCHAR(50) DEFAULT 'unknown';

-- Create index for fast quality-based retrieval
CREATE INDEX IF NOT EXISTS idx_manual_quality
ON knowledge_atoms(manual_quality_score DESC, page_count DESC);

-- Create index for manual type filtering
CREATE INDEX IF NOT EXISTS idx_manual_type
ON knowledge_atoms(manual_type);

-- Create composite index for vendor + quality queries
CREATE INDEX IF NOT EXISTS idx_vendor_quality
ON knowledge_atoms(vendor, manual_type, manual_quality_score DESC);

-- Add comment explaining the scoring system
COMMENT ON COLUMN knowledge_atoms.manual_quality_score IS
'Quality score (0-100): 90-100=comprehensive, 70-89=technical_doc, 50-69=partial_doc, 0-49=marketing. Based on page count, parameters, fault codes, specs, diagrams, TOC. Redirect penalty: -30pts.';

COMMENT ON COLUMN knowledge_atoms.page_count IS
'Total pages in source PDF. Used for quality scoring (200+ pages = 30pts).';

COMMENT ON COLUMN knowledge_atoms.is_direct_pdf IS
'True if direct PDF download, false if redirect detected (301/302/303/307/308). Redirect penalty: -30pts quality score.';

COMMENT ON COLUMN knowledge_atoms.manual_type IS
'Manual classification: comprehensive_manual (90-100), technical_doc (70-89), partial_doc (50-69), marketing (0-49), unknown (not scored).';

-- Verification query
-- Run this to confirm migration success:
-- SELECT COUNT(*) as total_atoms,
--        COUNT(manual_quality_score) as scored_atoms,
--        AVG(manual_quality_score) as avg_score,
--        COUNT(DISTINCT manual_type) as types_count
-- FROM knowledge_atoms;
