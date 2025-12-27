-- Migration: Add enrichment tracking columns to gap_requests
-- Created: 2025-12-27
-- Purpose: Support Phase 5 Route B enrichment pipeline

-- Add enrichment tracking columns
ALTER TABLE gap_requests ADD COLUMN IF NOT EXISTS enrichment_type VARCHAR(50);
ALTER TABLE gap_requests ADD COLUMN IF NOT EXISTS sources_queued INTEGER DEFAULT 0;
ALTER TABLE gap_requests ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;

-- Add index for worker queries (efficient lookup of unprocessed thin coverage gaps)
CREATE INDEX IF NOT EXISTS idx_gap_requests_enrichment
ON gap_requests(ingestion_completed, priority_score DESC, first_requested_at ASC)
WHERE enrichment_type = 'thin_coverage';

-- Comments for documentation
COMMENT ON COLUMN gap_requests.enrichment_type IS 'Type of enrichment: thin_coverage (Route B) or no_coverage (Route C)';
COMMENT ON COLUMN gap_requests.sources_queued IS 'Number of source URLs queued for ingestion';
COMMENT ON COLUMN gap_requests.processed_at IS 'When enrichment worker processed this gap';
