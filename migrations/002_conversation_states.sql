-- Conversation States Table
-- Stores persistent conversation state for resumable multi-step flows

CREATE TABLE IF NOT EXISTS conversation_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    conversation_type TEXT NOT NULL,  -- 'add_machine', 'troubleshoot', etc.
    current_state TEXT NOT NULL,      -- 'NICKNAME', 'MANUFACTURER', 'MODEL', etc.
    data JSONB NOT NULL DEFAULT '{}'::jsonb,  -- Collected data so far
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '24 hours'),  -- Auto-cleanup

    -- One active conversation per user per type
    UNIQUE(user_id, conversation_type)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_conversation_states_user
    ON conversation_states(user_id, conversation_type);

-- Index for cleanup
CREATE INDEX IF NOT EXISTS idx_conversation_states_expires
    ON conversation_states(expires_at);

-- Auto-delete expired conversations (PostgreSQL only)
-- For local SQLite, this will be ignored gracefully
CREATE OR REPLACE FUNCTION cleanup_expired_conversations() RETURNS void AS $$
BEGIN
    DELETE FROM conversation_states WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE conversation_states IS 'Persistent state for multi-step conversations with 24h TTL';
COMMENT ON COLUMN conversation_states.data IS 'JSONB: {nickname, manufacturer, model_number, serial_number, location, notes, photo_file_id}';
COMMENT ON COLUMN conversation_states.expires_at IS 'Auto-cleanup abandoned conversations after 24 hours';
