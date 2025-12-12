-- ============================================================================
-- AGENT FACTORY - MEMORY STORAGE SCHEMA
-- Supabase PostgreSQL Schema for Session Memory
-- ============================================================================
-- Purpose: Store session context, decisions, issues, and conversation history
-- Created: 2025-12-09
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- SESSION MEMORIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS session_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Session identification
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Memory classification
    memory_type TEXT NOT NULL,
    -- Types: 'session_metadata', 'message_user', 'message_assistant', 'message_system',
    --        'context', 'action', 'issue', 'decision', 'log'

    -- Content (stored as JSONB for flexible querying)
    content JSONB NOT NULL,

    -- Metadata (optional additional data)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_memory_type CHECK (
        memory_type IN (
            'session_metadata',
            'message_user',
            'message_assistant',
            'message_system',
            'context',
            'action',
            'issue',
            'decision',
            'log'
        )
    )
);

-- ============================================================================
-- INDEXES (for fast querying)
-- ============================================================================

-- Primary lookup: Get all memories for a session
CREATE INDEX idx_session_memories_session_id
ON session_memories(session_id, created_at DESC);

-- User lookup: Get all sessions for a user
CREATE INDEX idx_session_memories_user_id
ON session_memories(user_id, created_at DESC);

-- Type filtering: Get specific types of memories
CREATE INDEX idx_session_memories_type
ON session_memories(memory_type, created_at DESC);

-- Combined filter: Session + Type (most common query)
CREATE INDEX idx_session_memories_session_type
ON session_memories(session_id, memory_type, created_at DESC);

-- Content search (GIN index for JSONB)
CREATE INDEX idx_session_memories_content
ON session_memories USING GIN (content);

-- Full-text search support (optional, for searching content text)
CREATE INDEX idx_session_memories_content_text
ON session_memories USING GIN (to_tsvector('english', content::text));

-- ============================================================================
-- UNIQUE CONSTRAINT (for session metadata upserts)
-- ============================================================================

-- Ensure only one metadata record per session
CREATE UNIQUE INDEX idx_session_memories_unique_metadata
ON session_memories(session_id, memory_type)
WHERE memory_type = 'session_metadata';

-- ============================================================================
-- TRIGGERS (automatic timestamp updates)
-- ============================================================================

-- Update updated_at timestamp on record modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_session_memories_updated_at
    BEFORE UPDATE ON session_memories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW-LEVEL SECURITY (RLS) - Optional but Recommended
-- ============================================================================

-- Enable RLS
ALTER TABLE session_memories ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own memories
CREATE POLICY user_isolation ON session_memories
    FOR ALL
    USING (user_id = current_user);

-- Policy: Service role can access all (for admin operations)
CREATE POLICY service_role_access ON session_memories
    FOR ALL
    TO service_role
    USING (true);

-- IMPORTANT: After creating table, you must:
-- 1. Disable RLS initially (if testing with anon key)
-- 2. Later enable it for production with proper auth

-- Temporarily disable RLS for development (REMOVE IN PRODUCTION!)
ALTER TABLE session_memories DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- COMMENTS (for documentation)
-- ============================================================================

COMMENT ON TABLE session_memories IS
'Stores session context, conversation history, and project memory for Agent Factory';

COMMENT ON COLUMN session_memories.session_id IS
'Unique session identifier (e.g., session_abc123)';

COMMENT ON COLUMN session_memories.user_id IS
'User identifier (e.g., user email or ID)';

COMMENT ON COLUMN session_memories.memory_type IS
'Type of memory: session_metadata, message_*, context, action, issue, decision, log';

COMMENT ON COLUMN session_memories.content IS
'Memory content stored as JSONB for flexible querying';

COMMENT ON COLUMN session_memories.metadata IS
'Optional metadata (tags, priority, status, etc.)';

-- ============================================================================
-- EXAMPLE DATA (for testing)
-- ============================================================================

-- Example 1: Session metadata
INSERT INTO session_memories (session_id, user_id, memory_type, content) VALUES
(
    'session_test_001',
    'user@example.com',
    'session_metadata',
    '{
        "created_at": "2025-12-09T10:00:00Z",
        "last_active": "2025-12-09T11:30:00Z",
        "message_count": 5,
        "project": "Agent Factory",
        "phase": "Supabase Memory Integration"
    }'::jsonb
);

-- Example 2: User message
INSERT INTO session_memories (session_id, user_id, memory_type, content) VALUES
(
    'session_test_001',
    'user@example.com',
    'message_user',
    '{
        "role": "user",
        "content": "Can we use Supabase for memory storage?",
        "timestamp": "2025-12-09T10:05:00Z",
        "message_index": 0
    }'::jsonb
);

-- Example 3: Assistant message
INSERT INTO session_memories (session_id, user_id, memory_type, content) VALUES
(
    'session_test_001',
    'user@example.com',
    'message_assistant',
    '{
        "role": "assistant",
        "content": "Yes! Supabase is 10x faster than file-based storage.",
        "timestamp": "2025-12-09T10:05:30Z",
        "message_index": 1
    }'::jsonb
);

-- Example 4: Decision atom
INSERT INTO session_memories (session_id, user_id, memory_type, content) VALUES
(
    'session_test_001',
    'user@example.com',
    'decision',
    '{
        "title": "Use Supabase for Memory Storage",
        "rationale": "10-100x faster than file I/O, no line limits, better querying",
        "alternatives": ["File-based markdown", "SQLite local storage"],
        "decision_date": "2025-12-09",
        "impact": "high"
    }'::jsonb
);

-- Example 5: Action item
INSERT INTO session_memories (session_id, user_id, memory_type, content) VALUES
(
    'session_test_001',
    'user@example.com',
    'action',
    '{
        "task": "Test Supabase memory storage",
        "priority": "high",
        "status": "in_progress",
        "due_date": "2025-12-10",
        "tags": ["testing", "supabase"]
    }'::jsonb
);

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Query 1: Get all memories for a session
-- SELECT * FROM session_memories
-- WHERE session_id = 'session_test_001'
-- ORDER BY created_at DESC;

-- Query 2: Get session metadata
-- SELECT content FROM session_memories
-- WHERE session_id = 'session_test_001'
-- AND memory_type = 'session_metadata';

-- Query 3: Get all decisions across all sessions
-- SELECT session_id, content->'title' as title, created_at
-- FROM session_memories
-- WHERE memory_type = 'decision'
-- ORDER BY created_at DESC
-- LIMIT 10;

-- Query 4: Get conversation messages for a session
-- SELECT content->>'role' as role,
--        content->>'content' as message,
--        created_at
-- FROM session_memories
-- WHERE session_id = 'session_test_001'
-- AND memory_type LIKE 'message_%'
-- ORDER BY created_at;

-- Query 5: Search content for keywords
-- SELECT session_id, memory_type, content
-- FROM session_memories
-- WHERE content::text ILIKE '%supabase%'
-- LIMIT 20;

-- Query 6: Get high-priority action items
-- SELECT session_id, content
-- FROM session_memories
-- WHERE memory_type = 'action'
-- AND content->>'priority' = 'high'
-- AND content->>'status' != 'completed';

-- ============================================================================
-- MAINTENANCE
-- ============================================================================

-- Clean up old test data (run periodically)
-- DELETE FROM session_memories WHERE session_id LIKE 'session_test_%';

-- Get table size
-- SELECT pg_size_pretty(pg_total_relation_size('session_memories')) as size;

-- Vacuum and analyze (run weekly for performance)
-- VACUUM ANALYZE session_memories;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
