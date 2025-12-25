-- ============================================================================
-- Knowledge Base Observability Platform - Database Schema Migration
-- ============================================================================
-- Creates 3 tables for tracking ingestion pipeline metrics:
--   1. ingestion_metrics_realtime - Per-source ingestion results
--   2. ingestion_metrics_hourly - Hourly aggregations
--   3. ingestion_metrics_daily - Daily rollups
--
-- Run in Supabase SQL Editor or via psql
-- ============================================================================

-- Table 1: Real-time Ingestion Metrics
-- ============================================================================
-- Tracks every source processed through the 7-stage ingestion pipeline
-- Stores stage-by-stage timing, quality scores, and errors

CREATE TABLE IF NOT EXISTS ingestion_metrics_realtime (
    id BIGSERIAL PRIMARY KEY,

    -- Source identification
    source_url TEXT NOT NULL,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('web', 'pdf', 'youtube')),
    source_hash VARCHAR(64) NOT NULL,

    -- Results
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
    atoms_created INTEGER DEFAULT 0 CHECK (atoms_created >= 0),
    atoms_failed INTEGER DEFAULT 0 CHECK (atoms_failed >= 0),
    chunks_processed INTEGER DEFAULT 0 CHECK (chunks_processed >= 0),

    -- Quality metrics
    avg_quality_score FLOAT CHECK (avg_quality_score >= 0 AND avg_quality_score <= 1),
    quality_pass_rate FLOAT CHECK (quality_pass_rate >= 0 AND quality_pass_rate <= 1),

    -- Stage timings (milliseconds)
    -- Stage 1: Source Acquisition (download/fetch)
    stage_1_acquisition_ms INTEGER CHECK (stage_1_acquisition_ms >= 0),

    -- Stage 2: Content Extraction (parse text)
    stage_2_extraction_ms INTEGER CHECK (stage_2_extraction_ms >= 0),

    -- Stage 3: Semantic Chunking (split into atoms)
    stage_3_chunking_ms INTEGER CHECK (stage_3_chunking_ms >= 0),

    -- Stage 4: Atom Generation (LLM extraction)
    stage_4_generation_ms INTEGER CHECK (stage_4_generation_ms >= 0),

    -- Stage 5: Quality Validation (score 0-100)
    stage_5_validation_ms INTEGER CHECK (stage_5_validation_ms >= 0),

    -- Stage 6: Embedding Generation (OpenAI)
    stage_6_embedding_ms INTEGER CHECK (stage_6_embedding_ms >= 0),

    -- Stage 7: Storage & Indexing (Supabase)
    stage_7_storage_ms INTEGER CHECK (stage_7_storage_ms >= 0),

    -- Total duration
    total_duration_ms INTEGER CHECK (total_duration_ms >= 0),

    -- Error tracking
    error_stage VARCHAR(50),
    error_message TEXT,

    -- Metadata (extracted from atoms)
    vendor TEXT,
    equipment_type TEXT,

    -- Timestamps
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,

    -- Ensure completed_at is after started_at
    CHECK (completed_at IS NULL OR completed_at >= started_at)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_realtime_completed_at
    ON ingestion_metrics_realtime(completed_at DESC);

CREATE INDEX IF NOT EXISTS idx_realtime_status
    ON ingestion_metrics_realtime(status);

CREATE INDEX IF NOT EXISTS idx_realtime_vendor
    ON ingestion_metrics_realtime(vendor)
    WHERE vendor IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_realtime_source_type
    ON ingestion_metrics_realtime(source_type);

CREATE INDEX IF NOT EXISTS idx_realtime_source_hash
    ON ingestion_metrics_realtime(source_hash);

-- Composite index for dashboard queries (last 24h by vendor)
CREATE INDEX IF NOT EXISTS idx_realtime_recent_by_vendor
    ON ingestion_metrics_realtime(completed_at DESC, vendor)
    WHERE completed_at IS NOT NULL;

-- ============================================================================
-- Table 2: Hourly Aggregation Metrics
-- ============================================================================
-- Aggregated statistics per hour for trend analysis and dashboards

CREATE TABLE IF NOT EXISTS ingestion_metrics_hourly (
    id BIGSERIAL PRIMARY KEY,
    hour_start TIMESTAMPTZ NOT NULL UNIQUE,

    -- Throughput metrics
    sources_processed INTEGER DEFAULT 0 CHECK (sources_processed >= 0),
    atoms_created INTEGER DEFAULT 0 CHECK (atoms_created >= 0),
    atoms_failed INTEGER DEFAULT 0 CHECK (atoms_failed >= 0),
    success_rate FLOAT CHECK (success_rate >= 0 AND success_rate <= 1),

    -- Quality metrics
    avg_quality_score FLOAT CHECK (avg_quality_score >= 0 AND avg_quality_score <= 1),
    quality_pass_rate FLOAT CHECK (quality_pass_rate >= 0 AND quality_pass_rate <= 1),

    -- Performance metrics
    avg_total_duration_ms INTEGER CHECK (avg_total_duration_ms >= 0),
    p95_duration_ms INTEGER CHECK (p95_duration_ms >= 0),

    -- Stage bottleneck analysis (avg milliseconds per stage)
    avg_stage_1_ms INTEGER CHECK (avg_stage_1_ms >= 0),
    avg_stage_2_ms INTEGER CHECK (avg_stage_2_ms >= 0),
    avg_stage_3_ms INTEGER CHECK (avg_stage_3_ms >= 0),
    avg_stage_4_ms INTEGER CHECK (avg_stage_4_ms >= 0),
    avg_stage_5_ms INTEGER CHECK (avg_stage_5_ms >= 0),
    avg_stage_6_ms INTEGER CHECK (avg_stage_6_ms >= 0),
    avg_stage_7_ms INTEGER CHECK (avg_stage_7_ms >= 0),

    -- Coverage analysis (JSONB for flexibility)
    -- Example: {"Siemens": 45, "Rockwell": 38, "ABB": 23}
    vendor_counts JSONB,

    -- Example: {"PLC": 67, "VFD": 41, "HMI": 19}
    equipment_counts JSONB,

    -- Error tracking
    failed_sources INTEGER DEFAULT 0 CHECK (failed_sources >= 0),

    -- Example: {"stage_4": 3, "stage_5": 1}
    error_distribution JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_hourly_hour_start
    ON ingestion_metrics_hourly(hour_start DESC);

-- ============================================================================
-- Table 3: Daily Rollup Metrics
-- ============================================================================
-- Daily aggregates for long-term trend analysis and reporting

CREATE TABLE IF NOT EXISTS ingestion_metrics_daily (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Throughput metrics
    sources_processed INTEGER DEFAULT 0 CHECK (sources_processed >= 0),
    atoms_created INTEGER DEFAULT 0 CHECK (atoms_created >= 0),
    atoms_failed INTEGER DEFAULT 0 CHECK (atoms_failed >= 0),
    success_rate FLOAT CHECK (success_rate >= 0 AND success_rate <= 1),

    -- Quality metrics
    avg_quality_score FLOAT CHECK (avg_quality_score >= 0 AND avg_quality_score <= 1),

    -- Coverage analysis
    unique_vendors INTEGER CHECK (unique_vendors >= 0),
    unique_equipment_types INTEGER CHECK (unique_equipment_types >= 0),

    -- Distribution (JSONB)
    vendor_distribution JSONB,
    equipment_distribution JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_daily_date
    ON ingestion_metrics_daily(date DESC);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Calculate hourly aggregates from realtime table
CREATE OR REPLACE FUNCTION aggregate_hourly_metrics(target_hour TIMESTAMPTZ)
RETURNS VOID AS $$
BEGIN
    INSERT INTO ingestion_metrics_hourly (
        hour_start,
        sources_processed,
        atoms_created,
        atoms_failed,
        success_rate,
        avg_quality_score,
        quality_pass_rate,
        avg_total_duration_ms,
        p95_duration_ms,
        avg_stage_1_ms,
        avg_stage_2_ms,
        avg_stage_3_ms,
        avg_stage_4_ms,
        avg_stage_5_ms,
        avg_stage_6_ms,
        avg_stage_7_ms,
        vendor_counts,
        equipment_counts,
        failed_sources,
        error_distribution
    )
    SELECT
        DATE_TRUNC('hour', target_hour) as hour_start,
        COUNT(*) as sources_processed,
        SUM(atoms_created) as atoms_created,
        SUM(atoms_failed) as atoms_failed,
        AVG(CASE WHEN status = 'success' THEN 1.0 ELSE 0.0 END) as success_rate,
        AVG(avg_quality_score) as avg_quality_score,
        AVG(quality_pass_rate) as quality_pass_rate,
        AVG(total_duration_ms)::INTEGER as avg_total_duration_ms,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms)::INTEGER as p95_duration_ms,
        AVG(stage_1_acquisition_ms)::INTEGER as avg_stage_1_ms,
        AVG(stage_2_extraction_ms)::INTEGER as avg_stage_2_ms,
        AVG(stage_3_chunking_ms)::INTEGER as avg_stage_3_ms,
        AVG(stage_4_generation_ms)::INTEGER as avg_stage_4_ms,
        AVG(stage_5_validation_ms)::INTEGER as avg_stage_5_ms,
        AVG(stage_6_embedding_ms)::INTEGER as avg_stage_6_ms,
        AVG(stage_7_storage_ms)::INTEGER as avg_stage_7_ms,
        jsonb_object_agg(vendor, vendor_count) as vendor_counts,
        jsonb_object_agg(equipment_type, equipment_count) as equipment_counts,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)::INTEGER as failed_sources,
        jsonb_object_agg(error_stage, error_count) FILTER (WHERE error_stage IS NOT NULL) as error_distribution
    FROM (
        SELECT
            *,
            COUNT(*) FILTER (WHERE vendor IS NOT NULL) OVER (PARTITION BY vendor) as vendor_count,
            COUNT(*) FILTER (WHERE equipment_type IS NOT NULL) OVER (PARTITION BY equipment_type) as equipment_count,
            COUNT(*) FILTER (WHERE error_stage IS NOT NULL) OVER (PARTITION BY error_stage) as error_count
        FROM ingestion_metrics_realtime
        WHERE completed_at >= DATE_TRUNC('hour', target_hour)
          AND completed_at < DATE_TRUNC('hour', target_hour) + INTERVAL '1 hour'
    ) subq
    ON CONFLICT (hour_start) DO UPDATE SET
        sources_processed = EXCLUDED.sources_processed,
        atoms_created = EXCLUDED.atoms_created,
        atoms_failed = EXCLUDED.atoms_failed,
        success_rate = EXCLUDED.success_rate,
        avg_quality_score = EXCLUDED.avg_quality_score,
        quality_pass_rate = EXCLUDED.quality_pass_rate,
        avg_total_duration_ms = EXCLUDED.avg_total_duration_ms,
        p95_duration_ms = EXCLUDED.p95_duration_ms,
        avg_stage_1_ms = EXCLUDED.avg_stage_1_ms,
        avg_stage_2_ms = EXCLUDED.avg_stage_2_ms,
        avg_stage_3_ms = EXCLUDED.avg_stage_3_ms,
        avg_stage_4_ms = EXCLUDED.avg_stage_4_ms,
        avg_stage_5_ms = EXCLUDED.avg_stage_5_ms,
        avg_stage_6_ms = EXCLUDED.avg_stage_6_ms,
        avg_stage_7_ms = EXCLUDED.avg_stage_7_ms,
        vendor_counts = EXCLUDED.vendor_counts,
        equipment_counts = EXCLUDED.equipment_counts,
        failed_sources = EXCLUDED.failed_sources,
        error_distribution = EXCLUDED.error_distribution;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Sample Data for Testing
-- ============================================================================

-- Insert sample realtime record
COMMENT ON TABLE ingestion_metrics_realtime IS
'Tracks every source processed through the 7-stage KB ingestion pipeline.
Use for real-time monitoring and Telegram notifications.';

COMMENT ON TABLE ingestion_metrics_hourly IS
'Hourly aggregates for trend analysis and dashboard queries.
Populated by aggregate_hourly_metrics() function.';

COMMENT ON TABLE ingestion_metrics_daily IS
'Daily rollups for long-term reporting and capacity planning.';

-- ============================================================================
-- Grant Permissions (if using RLS)
-- ============================================================================

-- Grant access to service role
-- ALTER TABLE ingestion_metrics_realtime OWNER TO postgres;
-- ALTER TABLE ingestion_metrics_hourly OWNER TO postgres;
-- ALTER TABLE ingestion_metrics_daily OWNER TO postgres;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- List all tables created
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'ingestion_metrics%';

-- Check table sizes
-- SELECT
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
-- FROM pg_tables
-- WHERE schemaname = 'public' AND tablename LIKE 'ingestion_metrics%';

-- Test insert into realtime table
-- INSERT INTO ingestion_metrics_realtime (
--     source_url, source_type, source_hash, status,
--     atoms_created, atoms_failed, chunks_processed,
--     avg_quality_score, quality_pass_rate,
--     stage_1_acquisition_ms, stage_2_extraction_ms, stage_3_chunking_ms,
--     stage_4_generation_ms, stage_5_validation_ms, stage_6_embedding_ms,
--     stage_7_storage_ms, total_duration_ms,
--     vendor, equipment_type,
--     started_at, completed_at
-- ) VALUES (
--     'https://example.com/manual.pdf', 'pdf', 'abc123xyz789', 'success',
--     15, 2, 8,
--     0.87, 0.93,
--     1200, 850, 450,
--     2100, 780, 950,
--     340, 6670,
--     'Siemens', 'PLC',
--     NOW() - INTERVAL '10 minutes', NOW()
-- );

-- Query recent ingestions
-- SELECT * FROM ingestion_metrics_realtime ORDER BY completed_at DESC LIMIT 10;

-- Test hourly aggregation
-- SELECT aggregate_hourly_metrics(NOW() - INTERVAL '1 hour');
-- SELECT * FROM ingestion_metrics_hourly ORDER BY hour_start DESC LIMIT 5;
