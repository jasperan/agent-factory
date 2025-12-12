-- ================================================
-- Agent Factory Database Migrations
-- ================================================
-- Run this in Supabase SQL Editor
-- All statements are idempotent (safe to run multiple times)
-- ================================================

-- ================================================
-- 1. Settings Service
-- ================================================

-- Create settings table
CREATE TABLE IF NOT EXISTS agent_factory_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category, key)
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_settings_category_key
ON agent_factory_settings(category, key);

-- Insert default settings
INSERT INTO agent_factory_settings (category, key, value, description)
VALUES
    ('memory', 'BATCH_SIZE', '50', 'Batch size for memory operations'),
    ('memory', 'USE_HYBRID_SEARCH', 'false', 'Enable hybrid vector + text search'),
    ('orchestration', 'MAX_RETRIES', '3', 'Max retries for agent calls'),
    ('orchestration', 'TIMEOUT_SECONDS', '300', 'Default timeout for agent execution'),
    ('llm', 'DEFAULT_MODEL', 'gpt-4o-mini', 'Default LLM model'),
    ('llm', 'DEFAULT_TEMPERATURE', '0.7', 'Default temperature for LLM calls')
ON CONFLICT (category, key) DO NOTHING;

-- ================================================
-- 2. Hybrid Search Support
-- ================================================

-- Add tsvector column for full-text search (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='session_memories' AND column_name='content_tsvector'
    ) THEN
        ALTER TABLE session_memories
        ADD COLUMN content_tsvector tsvector
        GENERATED ALWAYS AS (to_tsvector('english', content::text)) STORED;
    END IF;
END $$;

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_session_memories_content_search
ON session_memories USING gin(content_tsvector);

-- ================================================
-- 3. Multi-Dimensional Embedding Support
-- ================================================

-- Add embedding columns for different dimensions (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='session_memories' AND column_name='embedding_768'
    ) THEN
        ALTER TABLE session_memories
        ADD COLUMN embedding_768 vector(768),
        ADD COLUMN embedding_1024 vector(1024),
        ADD COLUMN embedding_1536 vector(1536),
        ADD COLUMN embedding_3072 vector(3072),
        ADD COLUMN embedding_model TEXT,
        ADD COLUMN embedding_dimension INT;
    END IF;
END $$;

-- Create vector indexes for each dimension
CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_768
ON session_memories USING ivfflat (embedding_768 vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_1024
ON session_memories USING ivfflat (embedding_1024 vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_1536
ON session_memories USING ivfflat (embedding_1536 vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_3072
ON session_memories USING ivfflat (embedding_3072 vector_cosine_ops) WITH (lists = 100);

-- ================================================
-- Verification Queries
-- ================================================

-- Verify settings table
SELECT COUNT(*) as settings_count FROM agent_factory_settings;

-- Verify session_memories columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'session_memories'
ORDER BY ordinal_position;

-- Done!
SELECT 'Migrations completed successfully!' as status;
