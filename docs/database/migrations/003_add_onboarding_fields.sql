-- Add Onboarding Tracking Fields to rivet_users Table
-- Purpose: Support tier-aware Telegram onboarding system with resumable progress
-- Created: 2025-12-27
-- Phase: Telegram Onboarding (Phase 1 of 6)

-- =============================================================================
-- ADD ONBOARDING COLUMNS
-- =============================================================================

ALTER TABLE rivet_users
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS onboarding_step INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS onboarding_skipped BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS feature_tour_completed JSONB DEFAULT '{"troubleshooting": false, "machine_library": false, "manual_upload": false, "print_qa": false}'::jsonb;

-- =============================================================================
-- FIELD DESCRIPTIONS
-- =============================================================================

-- onboarding_completed: User finished full 5-step onboarding flow
-- onboarding_step: Current step (0-5, allows resuming mid-flow)
--   0 = Not started
--   1 = Welcome + Tier Explanation
--   2 = Feature Tour
--   3 = First Troubleshooting (hands-on)
--   4 = Machine Library Tutorial
--   5 = Completion + Quick Reference

-- onboarding_skipped: User clicked "Skip Tutorial" button
-- onboarding_completed_at: Timestamp when onboarding finished (UTC)
-- feature_tour_completed: JSON object tracking which feature tours user completed
--   {
--     "troubleshooting": true/false,
--     "machine_library": true/false,
--     "manual_upload": true/false,
--     "print_qa": true/false
--   }

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_users_onboarding_completed ON rivet_users(onboarding_completed);
CREATE INDEX IF NOT EXISTS idx_users_onboarding_step ON rivet_users(onboarding_step);

-- =============================================================================
-- EXAMPLE QUERIES
-- =============================================================================

-- Check onboarding completion rate by tier
-- SELECT
--   subscription_tier,
--   COUNT(*) as total_users,
--   SUM(CASE WHEN onboarding_completed THEN 1 ELSE 0 END) as completed,
--   ROUND(100.0 * SUM(CASE WHEN onboarding_completed THEN 1 ELSE 0 END) / COUNT(*), 2) as completion_pct
-- FROM rivet_users
-- GROUP BY subscription_tier;

-- Find users who started but didn't finish onboarding
-- SELECT email, telegram_id, onboarding_step, created_at
-- FROM rivet_users
-- WHERE onboarding_step > 0 AND onboarding_completed = FALSE
-- ORDER BY created_at DESC;

-- Average time to complete onboarding
-- SELECT
--   AVG(EXTRACT(EPOCH FROM (onboarding_completed_at - created_at))) / 60 as avg_minutes
-- FROM rivet_users
-- WHERE onboarding_completed = TRUE;

-- Users who skipped onboarding
-- SELECT COUNT(*) as skipped_count
-- FROM rivet_users
-- WHERE onboarding_skipped = TRUE;
