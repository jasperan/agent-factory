--
-- Field Eye Database Schema
-- Agent Factory's 3rd Vertical: Industrial Vision Platform
--
-- Deploy to Supabase: Run in SQL Editor
-- Extends existing Agent Factory database with Field Eye tables
--

-- ============================================================================
-- Inspection Sessions Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS field_eye_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  technician_id TEXT NOT NULL,
  vehicle_id TEXT,
  equipment_type TEXT,  -- 'coaster', 'motor', 'panel', 'pump', etc.
  date TIMESTAMP DEFAULT NOW(),
  duration_sec INTEGER,
  total_frames INTEGER,
  pause_count INTEGER,  -- Number of times tech paused (defect marker)
  pauses JSONB,  -- [{frame: 123, timestamp: 45.6, motion_score: 234}, ...]
  camera_model TEXT,  -- 'RunCam 6', 'Generic 1080p', etc.
  mount_type TEXT,  -- 'flat_clip', 'ring_clamp', 'lapel_clip'
  video_path TEXT,  -- S3 or local path
  metadata JSONB,  -- {lighting: 'outdoor', weather: 'sunny', shift: 'morning'}
  created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE field_eye_sessions IS 'Inspection sessions - one per shift/video file';
COMMENT ON COLUMN field_eye_sessions.pause_count IS 'Auto-detected pauses (motion analysis)';
COMMENT ON COLUMN field_eye_sessions.pauses IS 'JSON array of pause events with timestamps';

-- ============================================================================
-- Frame Storage Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS field_eye_frames (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES field_eye_sessions(id) ON DELETE CASCADE,
  frame_number INTEGER NOT NULL,
  timestamp_sec FLOAT NOT NULL,
  frame_path TEXT,  -- S3 or local path to extracted frame
  embedding VECTOR(1536),  -- OpenAI embedding for semantic search
  is_defect BOOLEAN DEFAULT NULL,  -- NULL = unlabeled, TRUE/FALSE = labeled
  defect_type TEXT,  -- 'missing_stripe', 'rotated', 'contaminated', etc.
  confidence FLOAT,  -- Model confidence (0.0-1.0)
  labels JSONB,  -- Manual labels: {torque_stripe: true, paint_chip: false, ...}
  thermal_data JSONB,  -- If thermal camera present: {avg_temp: 45.2, max_temp: 78.1}
  created_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(session_id, frame_number)
);

COMMENT ON TABLE field_eye_frames IS 'Extracted frames from inspection videos';
COMMENT ON COLUMN field_eye_frames.embedding IS 'Vector embedding for semantic similarity search';
COMMENT ON COLUMN field_eye_frames.is_defect IS 'Null = unlabeled, Boolean = labeled by human/AI';

-- ============================================================================
-- Defect Logs Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS field_eye_defects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  frame_id UUID REFERENCES field_eye_frames(id) ON DELETE CASCADE,
  defect_type TEXT NOT NULL,  -- 'torque_stripe_missing', 'bearing_overheat', etc.
  confidence FLOAT NOT NULL,  -- Model confidence
  bounding_box JSONB,  -- {x: 100, y: 200, width: 50, height: 30}
  severity TEXT DEFAULT 'warning',  -- 'critical', 'warning', 'info'
  auto_detected BOOLEAN DEFAULT TRUE,  -- True = AI found it, False = human marked
  human_verified BOOLEAN DEFAULT FALSE,  -- Has human reviewed this defect?
  notes TEXT,  -- Human notes or AI reasoning
  sensor_data JSONB,  -- Multi-modal: {thermal_max: 95.3, vibration_fft: [...]}
  created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE field_eye_defects IS 'Individual defect instances with bounding boxes';
COMMENT ON COLUMN field_eye_defects.severity IS 'Defect severity for prioritization';
COMMENT ON COLUMN field_eye_defects.sensor_data IS 'Multi-modal sensor readings (thermal, vibration, etc.)';

-- ============================================================================
-- Product Kits Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS field_eye_kits (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  kit_serial TEXT UNIQUE NOT NULL,  -- 'FE-2025-001'
  hardware_version TEXT DEFAULT 'v1.0',  -- Hardware revision
  mount_variant TEXT,  -- 'flat_clip', 'ring_clamp', 'lapel_clip'
  camera_model TEXT,  -- Camera included in kit
  purchase_date TIMESTAMP,
  owner_id TEXT,  -- Telegram user ID or email
  owner_name TEXT,
  status TEXT DEFAULT 'shipped',  -- 'assembled', 'shipped', 'active', 'inactive'
  first_upload_date TIMESTAMP,  -- When kit was first used (success metric)
  total_uploads INTEGER DEFAULT 0,
  metadata JSONB,  -- {sensors: ['RGB', 'thermal'], firmware: 'v1.2'}
  created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE field_eye_kits IS 'Product kit inventory and tracking';
COMMENT ON COLUMN field_eye_kits.first_upload_date IS 'Activation date - key success metric';
COMMENT ON COLUMN field_eye_kits.total_uploads IS 'Number of sessions uploaded by this kit';

-- ============================================================================
-- Model Training Runs Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS field_eye_models (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  model_name TEXT NOT NULL,  -- 'torque_stripe_v3', 'bearing_thermal_v1'
  model_type TEXT,  -- 'classification', 'detection', 'segmentation'
  architecture TEXT,  -- 'ResNet50', 'YOLOv8', 'UNet'
  training_frames INTEGER,  -- Number of frames used for training
  accuracy FLOAT,  -- Validation accuracy
  precision_score FLOAT,
  recall FLOAT,
  f1_score FLOAT,
  model_path TEXT,  -- S3 path to ONNX model
  onnx_size_mb FLOAT,
  inference_time_ms FLOAT,  -- Average inference time
  training_duration_min INTEGER,
  hyperparams JSONB,  -- {learning_rate: 1e-4, batch_size: 32, epochs: 20}
  created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE field_eye_models IS 'Model training run logs and metrics';
COMMENT ON COLUMN field_eye_models.inference_time_ms IS 'Target: <100ms for real-time';

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_sessions_tech ON field_eye_sessions(technician_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON field_eye_sessions(date DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_equipment ON field_eye_sessions(equipment_type);

CREATE INDEX IF NOT EXISTS idx_frames_session ON field_eye_frames(session_id);
CREATE INDEX IF NOT EXISTS idx_frames_defect ON field_eye_frames(is_defect) WHERE is_defect IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_frames_timestamp ON field_eye_frames(timestamp_sec);

CREATE INDEX IF NOT EXISTS idx_defects_type ON field_eye_defects(defect_type);
CREATE INDEX IF NOT EXISTS idx_defects_severity ON field_eye_defects(severity);
CREATE INDEX IF NOT EXISTS idx_defects_verified ON field_eye_defects(human_verified);

CREATE INDEX IF NOT EXISTS idx_kits_serial ON field_eye_kits(kit_serial);
CREATE INDEX IF NOT EXISTS idx_kits_status ON field_eye_kits(status);
CREATE INDEX IF NOT EXISTS idx_kits_owner ON field_eye_kits(owner_id);

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS
ALTER TABLE field_eye_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_eye_frames ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_eye_defects ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_eye_kits ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_eye_models ENABLE ROW LEVEL SECURITY;

-- Public read access (for authenticated users)
CREATE POLICY "Public read access"
  ON field_eye_sessions FOR SELECT
  USING (true);

CREATE POLICY "Public read access"
  ON field_eye_frames FOR SELECT
  USING (true);

CREATE POLICY "Public read access"
  ON field_eye_defects FOR SELECT
  USING (true);

CREATE POLICY "Public read access"
  ON field_eye_kits FOR SELECT
  USING (true);

CREATE POLICY "Public read access"
  ON field_eye_models FOR SELECT
  USING (true);

-- Service role can do anything (for backend agents)
CREATE POLICY "Service role all access"
  ON field_eye_sessions FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role all access"
  ON field_eye_frames FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role all access"
  ON field_eye_defects FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role all access"
  ON field_eye_kits FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "Service role all access"
  ON field_eye_models FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Get session statistics
CREATE OR REPLACE FUNCTION get_field_eye_stats()
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'total_sessions', (SELECT COUNT(*) FROM field_eye_sessions),
    'total_frames', (SELECT COUNT(*) FROM field_eye_frames),
    'total_defects', (SELECT COUNT(*) FROM field_eye_defects),
    'labeled_frames', (SELECT COUNT(*) FROM field_eye_frames WHERE is_defect IS NOT NULL),
    'active_kits', (SELECT COUNT(*) FROM field_eye_kits WHERE status = 'active'),
    'latest_session', (SELECT MAX(date) FROM field_eye_sessions),
    'avg_pauses_per_session', (SELECT AVG(pause_count) FROM field_eye_sessions)
  ) INTO result;

  RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_field_eye_stats IS 'Quick stats for dashboard and Telegram bot';

-- ============================================================================
-- Sample Data (Development Only)
-- ============================================================================

-- Uncomment for development testing
-- INSERT INTO field_eye_sessions (technician_id, vehicle_id, equipment_type, duration_sec, total_frames, pause_count)
-- VALUES ('john_smith', 'COASTER_001', 'coaster', 1800, 900, 12);

-- ============================================================================
-- Deployment Notes
-- ============================================================================

-- 1. Run this script in Supabase SQL Editor
-- 2. Verify tables created: SELECT * FROM field_eye_sessions LIMIT 1;
-- 3. Test stats function: SELECT get_field_eye_stats();
-- 4. Configure S3 bucket for video/frame storage
-- 5. Update .env with FIELD_EYE_BUCKET_NAME

-- ============================================================================
-- Migration History
-- ============================================================================

-- v0.1.0 (2025-12-11): Initial schema
-- - Core tables: sessions, frames, defects, kits, models
-- - Indexes for performance
-- - RLS policies
-- - Helper functions
