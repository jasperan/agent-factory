-- ============================================================================
-- Agent Factory: Supabase Migration for GitHub Strategy Implementation
-- ============================================================================
--
-- This migration adds tables for:
-- 1. Agent communication (inter-agent messaging)
-- 2. Agent health monitoring (heartbeat system)
-- 3. Agent jobs (from GitHub webhooks or manual triggers)
-- 4. Approval requests (human-in-loop workflow)
-- 5. Video analytics (YouTube performance metrics)
--
-- Run this in Supabase SQL Editor after creating your project.
--
-- Based on:
-- - docs/AGENT_ORGANIZATION.md (18-agent system)
-- - Complete GitHub strategy.md (webhook + orchestrator pattern)
-- - docs/TRIUNE_STRATEGY.md (approval workflow)
-- ============================================================================

-- ============================================================================
-- 1. Agent Messages (Inter-Agent Communication)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Routing
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,

    -- Content
    message_type TEXT NOT NULL CHECK (message_type IN ('task', 'notification', 'error', 'query', 'response')),
    payload JSONB NOT NULL,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Indexes
    INDEX idx_agent_messages_to_agent_status (to_agent, status),
    INDEX idx_agent_messages_created_at (created_at DESC)
);

COMMENT ON TABLE agent_messages IS 'Inter-agent message queue for task coordination';
COMMENT ON COLUMN agent_messages.message_type IS 'task=work request, notification=FYI, error=failure report, query=request info, response=answer query';
COMMENT ON COLUMN agent_messages.payload IS 'Flexible JSON payload with task details, error info, etc.';

-- ============================================================================
-- 2. Agent Status (Health Check & Monitoring)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_status (
    agent_name TEXT PRIMARY KEY,

    -- Status
    status TEXT NOT NULL CHECK (status IN ('running', 'idle', 'error', 'stopped')),

    -- Metrics
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tasks_completed_today INT DEFAULT 0 CHECK (tasks_completed_today >= 0),
    tasks_failed_today INT DEFAULT 0 CHECK (tasks_failed_today >= 0),

    -- Current State
    current_task TEXT,
    error_message TEXT,

    -- Metadata
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE agent_status IS 'Real-time agent health monitoring via heartbeat system';
COMMENT ON COLUMN agent_status.last_heartbeat IS 'Last time agent checked in (alerts if >10 min stale)';

-- Index for monitoring queries
CREATE INDEX idx_agent_status_last_heartbeat ON agent_status(last_heartbeat);

-- ============================================================================
-- 3. Agent Jobs (GitHub Webhooks + Manual Triggers)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Job Definition
    job_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    priority INT DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),

    -- Assignment
    assigned_agent TEXT,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'running', 'completed', 'failed')),
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Indexes
    INDEX idx_agent_jobs_status_priority (status, priority),
    INDEX idx_agent_jobs_assigned_agent (assigned_agent),
    INDEX idx_agent_jobs_created_at (created_at DESC)
);

COMMENT ON TABLE agent_jobs IS 'Job queue from GitHub webhooks or manual triggers, processed by orchestrator';
COMMENT ON COLUMN agent_jobs.job_type IS 'Type of job (e.g., "create_video", "validate_atoms", "sync_and_generate_content")';
COMMENT ON COLUMN agent_jobs.priority IS '1=highest (immediate), 10=lowest (background), default=5';
COMMENT ON COLUMN agent_jobs.payload IS 'Job parameters (flexible JSON)';

-- ============================================================================
-- 4. Approval Requests (Human-in-Loop Workflow)
-- ============================================================================

CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What needs approval
    approval_type TEXT NOT NULL CHECK (approval_type IN ('video_script', 'video_final', 'knowledge_atom', 'social_post')),
    item_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,

    -- Context
    preview_url TEXT,
    confidence_score FLOAT CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    reason TEXT,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    feedback TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_approval_requests_status (status),
    INDEX idx_approval_requests_created_at (created_at DESC)
);

COMMENT ON TABLE approval_requests IS 'Human approval queue for videos, atoms, social posts';
COMMENT ON COLUMN approval_requests.confidence_score IS 'Agent confidence (0.0-1.0), approvals required if <0.9';
COMMENT ON COLUMN approval_requests.preview_url IS 'URL to preview item (video, thumbnail, etc.)';

-- ============================================================================
-- 5. Video Analytics (YouTube Performance Metrics)
-- ============================================================================

CREATE TABLE IF NOT EXISTS video_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identification
    youtube_video_id TEXT NOT NULL,
    script_id TEXT NOT NULL,

    -- Performance Metrics
    views INT DEFAULT 0 CHECK (views >= 0),
    watch_time_hours FLOAT DEFAULT 0.0 CHECK (watch_time_hours >= 0.0),
    average_view_duration_seconds FLOAT DEFAULT 0.0 CHECK (average_view_duration_seconds >= 0.0),
    click_through_rate FLOAT DEFAULT 0.0 CHECK (click_through_rate BETWEEN 0.0 AND 1.0),

    -- Engagement
    likes INT DEFAULT 0 CHECK (likes >= 0),
    dislikes INT DEFAULT 0 CHECK (dislikes >= 0),
    comments INT DEFAULT 0 CHECK (comments >= 0),

    -- Traffic Sources
    traffic_sources JSONB DEFAULT '{}',

    -- Timestamps
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_video_analytics_youtube_video_id (youtube_video_id),
    INDEX idx_video_analytics_script_id (script_id),
    INDEX idx_video_analytics_published_at (published_at DESC)
);

COMMENT ON TABLE video_analytics IS 'YouTube video performance metrics, fetched daily by Analytics Agent';
COMMENT ON COLUMN video_analytics.click_through_rate IS 'CTR as decimal (0.05 = 5%)';
COMMENT ON COLUMN video_analytics.traffic_sources IS 'Views by source: {"search": 1000, "suggested": 500, "external": 100}';

-- ============================================================================
-- 6. Agent Metrics (Performance Tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Agent & Metric
    agent_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value FLOAT NOT NULL,

    -- Metadata
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_agent_metrics_agent_name_metric_name (agent_name, metric_name),
    INDEX idx_agent_metrics_recorded_at (recorded_at DESC)
);

COMMENT ON TABLE agent_metrics IS 'Time-series metrics for agent performance (scripts_generated_per_day, upload_success_rate, etc.)';

-- Example metrics:
-- scriptwriter_agent.scripts_generated_per_day
-- youtube_uploader_agent.upload_success_rate
-- community_agent.response_time_seconds
-- analytics_agent.insight_count_per_report

-- ============================================================================
-- 7. Webhook Events (GitHub Webhook Log)
-- ============================================================================

CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source
    source TEXT NOT NULL CHECK (source IN ('github', 'manual', 'telegram')),
    event_type TEXT NOT NULL,

    -- Payload
    payload JSONB NOT NULL,

    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    created_job_id UUID REFERENCES agent_jobs(id),

    -- Timestamps
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Indexes
    INDEX idx_webhook_events_processed (processed),
    INDEX idx_webhook_events_received_at (received_at DESC)
);

COMMENT ON TABLE webhook_events IS 'Log of all webhook events (GitHub push, release, issue) for audit trail';
COMMENT ON COLUMN webhook_events.source IS 'github=GitHub webhook, manual=user-triggered, telegram=Telegram bot command';

-- ============================================================================
-- 8. Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (for orchestrator + agents)
CREATE POLICY "Service role has full access" ON agent_messages FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role has full access" ON agent_status FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role has full access" ON agent_jobs FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role has full access" ON approval_requests FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role has full access" ON video_analytics FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role has full access" ON agent_metrics FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role has full access" ON webhook_events FOR ALL USING (auth.role() = 'service_role');

-- Allow anon key read-only access to status/metrics (for monitoring dashboards)
CREATE POLICY "Anon can read agent status" ON agent_status FOR SELECT USING (true);
CREATE POLICY "Anon can read agent metrics" ON agent_metrics FOR SELECT USING (true);
CREATE POLICY "Anon can read video analytics" ON video_analytics FOR SELECT USING (true);

-- ============================================================================
-- 9. Functions & Triggers
-- ============================================================================

-- Automatically reset daily counters at midnight
CREATE OR REPLACE FUNCTION reset_agent_daily_counters()
RETURNS void AS $$
BEGIN
    UPDATE agent_status
    SET tasks_completed_today = 0,
        tasks_failed_today = 0;
END;
$$ LANGUAGE plpgsql;

-- Schedule daily reset (requires pg_cron extension)
-- SELECT cron.schedule('reset-agent-counters', '0 0 * * *', 'SELECT reset_agent_daily_counters();');

-- ============================================================================
-- 10. Sample Data (for testing)
-- ============================================================================

-- Insert sample agent statuses
INSERT INTO agent_status (agent_name, status, tasks_completed_today, tasks_failed_today)
VALUES
    ('research_agent', 'idle', 0, 0),
    ('scriptwriter_agent', 'idle', 0, 0),
    ('youtube_uploader_agent', 'idle', 0, 0)
ON CONFLICT (agent_name) DO NOTHING;

-- Insert sample job
INSERT INTO agent_jobs (job_type, payload, priority)
VALUES
    ('sync_and_generate_content', '{"count": 3, "target": "video_production"}', 5)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 11. Views (for monitoring)
-- ============================================================================

-- View: Agent Health Summary
CREATE OR REPLACE VIEW agent_health_summary AS
SELECT
    agent_name,
    status,
    EXTRACT(EPOCH FROM (NOW() - last_heartbeat)) AS seconds_since_heartbeat,
    tasks_completed_today,
    tasks_failed_today,
    current_task
FROM agent_status
ORDER BY agent_name;

COMMENT ON VIEW agent_health_summary IS 'Real-time agent health dashboard';

-- View: Pending Work Summary
CREATE OR REPLACE VIEW pending_work_summary AS
SELECT
    'jobs' AS queue_type,
    status,
    COUNT(*) AS count
FROM agent_jobs
WHERE status IN ('pending', 'assigned', 'running')
GROUP BY status
UNION ALL
SELECT
    'approvals' AS queue_type,
    status,
    COUNT(*) AS count
FROM approval_requests
WHERE status = 'pending'
GROUP BY status;

COMMENT ON VIEW pending_work_summary IS 'Summary of pending jobs and approvals';

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Agent Factory Migration Complete!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - agent_messages (inter-agent communication)';
    RAISE NOTICE '  - agent_status (health monitoring)';
    RAISE NOTICE '  - agent_jobs (GitHub webhooks + manual triggers)';
    RAISE NOTICE '  - approval_requests (human-in-loop workflow)';
    RAISE NOTICE '  - video_analytics (YouTube performance)';
    RAISE NOTICE '  - agent_metrics (time-series metrics)';
    RAISE NOTICE '  - webhook_events (audit log)';
    RAISE NOTICE '';
    RAISE NOTICE 'Views created:';
    RAISE NOTICE '  - agent_health_summary (monitoring dashboard)';
    RAISE NOTICE '  - pending_work_summary (work queue status)';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Update .env with SUPABASE_URL and SUPABASE_KEY';
    RAISE NOTICE '  2. Run orchestrator.py (24/7 loop)';
    RAISE NOTICE '  3. Test with: SELECT * FROM agent_health_summary;';
    RAISE NOTICE '============================================================';
END $$;
