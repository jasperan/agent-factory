-- ============================================================================
-- AGENT FACTORY - COMPLETE SCHEMA (Production Ready)
-- ============================================================================
-- Purpose: Complete database schema for Agent Factory + PLC Tutor + RIVET
-- Version: 1.0
-- Created: 2025-12-10
-- ============================================================================
--
-- This is the SINGLE SOURCE OF TRUTH migration.
-- Run this in Supabase SQL Editor to deploy complete schema.
--
-- Tables:
--   1. knowledge_atoms      - Knowledge base with vector embeddings
--   2. research_staging     - Research Agent raw data
--   3. video_scripts        - Scriptwriter Agent output
--   4. upload_jobs          - YouTube Uploader queue
--   5. agent_messages       - Inter-agent communication
--   6. session_memories     - Memory atoms (context, decisions, actions)
--   7. settings             - Runtime configuration (Settings Service)
--
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for embeddings

-- ============================================================================
-- 1. KNOWLEDGE ATOMS (Knowledge Base with Vector Embeddings)
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_atoms (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Core identification
    atom_id TEXT UNIQUE NOT NULL,  -- Format: manufacturer:product:topic-slug
    atom_type TEXT NOT NULL CHECK (atom_type IN ('concept', 'procedure', 'specification', 'pattern', 'fault', 'reference')),

    -- Content (optimally chunked for retrieval)
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,

    -- Metadata for filtering
    manufacturer TEXT NOT NULL,
    product_family TEXT,
    product_version TEXT,

    -- Learning metadata
    difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')),
    prerequisites TEXT[] DEFAULT ARRAY[]::TEXT[],
    related_atoms TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Citations and sources
    source_document TEXT NOT NULL,
    source_pages INTEGER[] NOT NULL,
    source_url TEXT,

    -- Quality and safety
    quality_score FLOAT DEFAULT 1.0 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    safety_level TEXT DEFAULT 'info' CHECK (safety_level IN ('info', 'caution', 'warning', 'danger')),
    safety_notes TEXT,

    -- Search optimization
    keywords TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Vector embedding (OpenAI text-embedding-3-small = 1536 dimensions)
    embedding vector(1536),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ
);

-- Indexes for knowledge_atoms
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_atom_id ON knowledge_atoms(atom_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_type ON knowledge_atoms(atom_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_manufacturer ON knowledge_atoms(manufacturer);
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_product ON knowledge_atoms(product_family);
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_difficulty ON knowledge_atoms(difficulty);
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_mfr_product_type ON knowledge_atoms(manufacturer, product_family, atom_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_content_fts ON knowledge_atoms USING GIN (to_tsvector('english', title || ' ' || summary || ' ' || content));

-- Vector similarity search index (HNSW for fast approximate search)
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_embedding ON knowledge_atoms USING hnsw (embedding vector_cosine_ops);

COMMENT ON TABLE knowledge_atoms IS 'Knowledge base with vector embeddings for semantic search';

-- ============================================================================
-- 2. RESEARCH STAGING (Research Agent Raw Data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS research_staging (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Source identification
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('web', 'youtube', 'pdf', 'manual')),
    content_hash TEXT UNIQUE NOT NULL,  -- Deduplication

    -- Raw content
    raw_content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Processing status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_research_staging_status ON research_staging(status);
CREATE INDEX IF NOT EXISTS idx_research_staging_source_type ON research_staging(source_type);
CREATE INDEX IF NOT EXISTS idx_research_staging_hash ON research_staging(content_hash);

COMMENT ON TABLE research_staging IS 'Research Agent raw data staging area';

-- ============================================================================
-- 3. VIDEO SCRIPTS (Scriptwriter Agent Output)
-- ============================================================================

CREATE TABLE IF NOT EXISTS video_scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Script identification
    script_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,

    -- Script structure
    hook TEXT NOT NULL,              -- 30-45 seconds
    main_content TEXT NOT NULL,      -- 4-6 minutes
    recap TEXT NOT NULL,             -- 20-30 seconds

    -- Citations
    atom_ids TEXT[] NOT NULL,        -- Knowledge atoms used
    citations JSONB DEFAULT '[]'::JSONB,

    -- Metadata
    estimated_duration_seconds INTEGER,
    keywords TEXT[] DEFAULT ARRAY[]::TEXT[],
    target_difficulty TEXT CHECK (target_difficulty IN ('beginner', 'intermediate', 'advanced')),

    -- Status
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'rejected', 'published')),
    approval_notes TEXT,

    -- Additional fields
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_video_scripts_status ON video_scripts(status);
CREATE INDEX IF NOT EXISTS idx_video_scripts_script_id ON video_scripts(script_id);

COMMENT ON TABLE video_scripts IS 'Scriptwriter Agent output (video scripts)';

-- ============================================================================
-- 4. UPLOAD JOBS (YouTube Uploader Queue)
-- ============================================================================

CREATE TABLE IF NOT EXISTS upload_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Job identification
    job_id TEXT UNIQUE NOT NULL,

    -- Video details
    video_path TEXT NOT NULL,
    script_id TEXT REFERENCES video_scripts(script_id),

    -- YouTube metadata
    youtube_title TEXT NOT NULL,
    youtube_description TEXT,
    youtube_tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    thumbnail_path TEXT,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'uploading', 'completed', 'failed')),
    youtube_video_id TEXT,
    error_message TEXT,

    -- Additional metadata
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON upload_jobs(status);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_job_id ON upload_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_script_id ON upload_jobs(script_id);

COMMENT ON TABLE upload_jobs IS 'YouTube upload queue';

-- ============================================================================
-- 5. AGENT MESSAGES (Inter-Agent Communication)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Routing (keep session_id for compatibility)
    session_id TEXT,
    agent_name TEXT NOT NULL,

    -- Message details
    message_type TEXT NOT NULL CHECK (message_type IN ('log', 'error', 'task', 'notification', 'query', 'response')),
    content JSONB NOT NULL,

    -- Additional metadata
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_agent ON agent_messages(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_messages_type ON agent_messages(message_type);

COMMENT ON TABLE agent_messages IS 'Inter-agent communication logs';

-- ============================================================================
-- 6. SESSION MEMORIES (Memory Atoms - Context, Decisions, Actions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS session_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Session identification
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Memory classification
    memory_type TEXT NOT NULL CHECK (memory_type IN ('context', 'decision', 'action', 'issue', 'log')),

    -- Content
    content JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_memories_session ON session_memories(session_id);
CREATE INDEX IF NOT EXISTS idx_session_memories_user ON session_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_session_memories_type ON session_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_session_memories_created ON session_memories(created_at DESC);

COMMENT ON TABLE session_memories IS 'Memory atoms (context, decisions, actions, issues, logs)';

-- ============================================================================
-- 7. SETTINGS (Runtime Configuration - Settings Service)
-- ============================================================================

CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Setting identification
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,

    -- Organization
    category TEXT DEFAULT 'general',
    description TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_settings_category ON settings(category);

COMMENT ON TABLE settings IS 'Runtime configuration (Settings Service)';

-- ============================================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================================

-- Sample settings
INSERT INTO settings (setting_key, setting_value, category, description) VALUES
    ('DEFAULT_MODEL', 'gpt-4', 'llm', 'Default LLM model for agents'),
    ('DEFAULT_TEMPERATURE', '0.7', 'llm', 'Default temperature for LLM calls'),
    ('BATCH_SIZE', '50', 'memory', 'Batch size for memory operations'),
    ('USE_HYBRID_SEARCH', 'true', 'memory', 'Enable hybrid vector + text search')
ON CONFLICT (setting_key) DO NOTHING;

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Run these after migration to verify deployment:

-- 1. Check all tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
  AND table_name IN ('knowledge_atoms', 'research_staging', 'video_scripts',
                     'upload_jobs', 'agent_messages', 'session_memories', 'settings')
ORDER BY table_name;

-- 2. Check indexes
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('knowledge_atoms', 'research_staging', 'video_scripts',
                    'upload_jobs', 'agent_messages', 'session_memories', 'settings')
ORDER BY tablename, indexname;

-- 3. Check extensions
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('uuid-ossp', 'vector');

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify deployment by running:
-- poetry run python scripts/validate_supabase_schema.py
