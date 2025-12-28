-- Migration 004: KB Weakness Tracking
-- Adds columns to gap_requests table for Phoenix trace weakness tracking

-- Add weakness tracking columns
ALTER TABLE gap_requests
ADD COLUMN IF NOT EXISTS weakness_type TEXT,
ADD COLUMN IF NOT EXISTS trace_id TEXT,
ADD COLUMN IF NOT EXISTS ingestion_started BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ingestion_started_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS ingestion_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ingestion_completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS atoms_created INTEGER DEFAULT 0;

-- Add index for fast lookups by ingestion status and priority
CREATE INDEX IF NOT EXISTS idx_gap_requests_ingestion_status
ON gap_requests(ingestion_completed, priority_score DESC);

-- Add index for trace_id lookups
CREATE INDEX IF NOT EXISTS idx_gap_requests_trace_id
ON gap_requests(trace_id);

-- Add index for weakness_type filtering
CREATE INDEX IF NOT EXISTS idx_gap_requests_weakness_type
ON gap_requests(weakness_type);

-- Update existing records to have default values
UPDATE gap_requests
SET ingestion_started = FALSE,
    ingestion_completed = FALSE,
    atoms_created = 0
WHERE ingestion_started IS NULL;

-- Add comment
COMMENT ON COLUMN gap_requests.weakness_type IS 'Type of KB weakness detected from Phoenix trace (zero_atoms, thin_coverage, low_relevance, missing_citations, hallucination_risk, high_latency)';
COMMENT ON COLUMN gap_requests.trace_id IS 'Phoenix trace ID for tracking back to original trace';
COMMENT ON COLUMN gap_requests.ingestion_started IS 'Whether research/ingestion has been triggered for this gap';
COMMENT ON COLUMN gap_requests.ingestion_completed IS 'Whether ingestion completed and atoms were created';
COMMENT ON COLUMN gap_requests.atoms_created IS 'Number of atoms created from ingestion for this gap';
