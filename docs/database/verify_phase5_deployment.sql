-- ============================================
-- RIVET Pro Phase 5: Deployment Verification
-- ============================================
-- Run these queries in Supabase SQL Editor AFTER deploying
-- phase5_research_pipeline_migration.sql
--
-- Expected results are documented after each query.
-- ============================================

-- ====================
-- Test 1: Table Exists
-- ====================
-- Verify source_fingerprints table was created

SELECT COUNT(*) as initial_count FROM source_fingerprints;

-- Expected: 0 rows (if freshly deployed)
-- If > 0: Table already has data (check if from previous deployment)


-- ====================
-- Test 2: All Indexes Exist
-- ====================
-- Verify all 4 performance indexes were created

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'source_fingerprints'
ORDER BY indexname;

-- Expected: 5 total indexes
--   1. source_fingerprints_pkey (primary key - auto-created)
--   2. idx_source_fingerprints_created (created_at DESC)
--   3. idx_source_fingerprints_hash (url_hash)
--   4. idx_source_fingerprints_queued (queued_for_ingestion)
--   5. idx_source_fingerprints_source_type (source_type)


-- ====================
-- Test 3: Insert + Select
-- ====================
-- Test basic CRUD operations

INSERT INTO source_fingerprints (url_hash, url, source_type, queued_for_ingestion)
VALUES (
  'test_hash_verification_12345',
  'https://stackoverflow.com/questions/test-verification',
  'stackoverflow',
  TRUE
)
RETURNING *;

-- Expected: 1 row inserted with auto-generated id and created_at


-- ====================
-- Test 4: Query by Hash
-- ====================
-- Verify hash index works (critical for deduplication)

SELECT url, source_type, created_at, queued_for_ingestion
FROM source_fingerprints
WHERE url_hash = 'test_hash_verification_12345';

-- Expected: 1 row (the test row just inserted)


-- ====================
-- Test 5: Deduplication Test
-- ====================
-- Verify unique constraint on url_hash prevents duplicates

INSERT INTO source_fingerprints (url_hash, url, source_type)
VALUES (
  'test_hash_verification_12345',
  'https://stackoverflow.com/questions/duplicate-test',
  'stackoverflow'
);

-- Expected: ERROR - duplicate key value violates unique constraint
-- This is CORRECT behavior - deduplication working!


-- ====================
-- Test 6: Query Queued Sources
-- ====================
-- Verify queued index works (used by ingestion worker)

SELECT COUNT(*) as queued_count
FROM source_fingerprints
WHERE queued_for_ingestion = TRUE
  AND ingestion_completed_at IS NULL;

-- Expected: 1 (the test row)


-- ====================
-- Test 7: Mark Ingestion Complete
-- ====================
-- Simulate ingestion completion

UPDATE source_fingerprints
SET ingestion_completed_at = NOW()
WHERE url_hash = 'test_hash_verification_12345'
RETURNING *;

-- Expected: 1 row updated with ingestion_completed_at timestamp


-- ====================
-- Test 8: Cleanup Test Data
-- ====================
-- Remove test fingerprint

DELETE FROM source_fingerprints
WHERE url_hash = 'test_hash_verification_12345';

-- Expected: 1 row deleted


-- ====================
-- Test 9: Verify Empty State
-- ====================
-- Confirm cleanup succeeded

SELECT COUNT(*) as final_count FROM source_fingerprints;

-- Expected: 0 rows (if no production data)
-- If > 0: Production fingerprints remain (expected in live system)


-- ============================================
-- Optional: Production Readiness Checks
-- ============================================

-- Check table structure
\d source_fingerprints

-- Check index details
\di idx_source_fingerprints_*

-- Estimate table size (should be ~0 KB initially)
SELECT pg_size_pretty(pg_total_relation_size('source_fingerprints')) as table_size;

-- ============================================
-- Success Criteria
-- ============================================
-- If all tests pass:
--   - source_fingerprints table exists
--   - 5 indexes created (1 PK + 4 performance)
--   - Insert/select/update/delete work
--   - Deduplication constraint active
--   - Ready for production use!
--
-- Next step:
--   Run Python verification: poetry run python scripts/deployment/verify_phase5_schema.py
-- ============================================
