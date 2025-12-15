-- ============================================================================
-- AGENT FACTORY - COMPLETE UNIFIED SCHEMA FOR SUPABASE
-- ============================================================================
-- Purpose: Single source of truth for ALL Agent Factory tables
-- Database: Supabase (PostgreSQL + pgvector)
-- Version: 2.0 - Complete Consolidation
-- Date: 2025-12-14
--
-- What This Includes:
--   1. Memory System (session_memories, agent_messages)
--   2. Knowledge Base (knowledge_atoms with vector search)
--   3. Management Dashboard (video_approval_queue, agent_status, alert_history)
--   4. Settings Service (agent_factory_settings)
--   5. Video Production (video_scripts)
--   6. All indexes (B-tree, GIN, HNSW for vectors)
--   7. Search functions (hybrid search, related atoms)
--
-- Run in: Supabase Dashboard → SQL Editor
-- Idempotent: Safe to run multiple times
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for embeddings

-- ============================================================================
-- 1. SETTINGS SERVICE
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_settings_category_key
ON agent_factory_settings(category, key);

-- Default settings
INSERT INTO agent_factory_settings (category, key, value, description)
VALUES
    ('memory', 'BATCH_SIZE', '50', 'Batch size for memory operations'),
    ('memory', 'USE_HYBRID_SEARCH', 'false', 'Enable hybrid vector + text search'),
    ('orchestration', 'MAX_RETRIES', '3', 'Max retries for agent calls'),
    ('orchestration', 'TIMEOUT_SECONDS', '300', 'Default timeout for agent execution'),
    ('llm', 'DEFAULT_MODEL', 'gpt-4o-mini', 'Default LLM model'),
    ('llm', 'DEFAULT_TEMPERATURE', '0.7', 'Default temperature for LLM calls')
ON CONFLICT (category, key) DO NOTHING;

-- ============================================================================
-- 2. MEMORY SYSTEM
-- ============================================================================

-- Session memories table (vector-enabled conversation memory)
CREATE TABLE IF NOT EXISTS session_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    content JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Multi-dimensional embeddings
    embedding_768 vector(768),
    embedding_1024 vector(1024),
    embedding_1536 vector(1536),
    embedding_3072 vector(3072),
    embedding_model TEXT,
    embedding_dimension INT,

    -- Full-text search
    content_tsvector tsvector GENERATED ALWAYS AS (to_tsvector('english', content::text)) STORED
);

CREATE INDEX IF NOT EXISTS idx_session_memories_session ON session_memories(session_id);
CREATE INDEX IF NOT EXISTS idx_session_memories_created ON session_memories(created_at DESC);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_session_memories_content_search
ON session_memories USING gin(content_tsvector);

-- Vector indexes for each dimension
CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_768
ON session_memories USING ivfflat (embedding_768 vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_1024
ON session_memories USING ivfflat (embedding_1024 vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_1536
ON session_memories USING ivfflat (embedding_1536 vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_session_memories_embedding_3072
ON session_memories USING ivfflat (embedding_3072 vector_cosine_ops) WITH (lists = 100);

-- Agent messages table (conversation history)
CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,  -- FIXED: Added missing column
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_created ON agent_messages(created_at DESC);

-- ============================================================================
-- 3. KNOWLEDGE BASE (Knowledge Atoms)
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_atoms (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Core identification
    atom_id TEXT UNIQUE NOT NULL,
    atom_type TEXT NOT NULL CHECK (
        atom_type IN ('concept', 'procedure', 'specification', 'pattern', 'fault', 'reference')
    ),

    -- Content (FIXED: Added missing content column)
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,  -- 200-1000 words (full explanation)

    -- Metadata
    manufacturer TEXT NOT NULL,
    product_family TEXT,
    product_version TEXT,

    -- Learning metadata
    difficulty TEXT NOT NULL CHECK (
        difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')
    ),
    prerequisites TEXT[] DEFAULT ARRAY[]::TEXT[],
    related_atoms TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Citations
    source_document TEXT NOT NULL,
    source_pages INTEGER[] NOT NULL,
    source_url TEXT,

    -- Quality and safety
    quality_score FLOAT DEFAULT 1.0 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    safety_level TEXT DEFAULT 'info' CHECK (
        safety_level IN ('info', 'caution', 'warning', 'danger')
    ),
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

-- Combined filter (common query pattern)
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_mfr_product_type
ON knowledge_atoms(manufacturer, product_family, atom_type);

-- Full-text search on content (GIN on tsvector, NOT on raw text)
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_content_fts
ON knowledge_atoms USING GIN (to_tsvector('english', title || ' ' || summary || ' ' || content));

-- Keyword search (GIN for arrays)
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_keywords
ON knowledge_atoms USING GIN (keywords);

-- Vector similarity search (HNSW for fast approximate nearest neighbor)
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_embedding
ON knowledge_atoms USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- 4. VIDEO PRODUCTION (Video Scripts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS video_scripts (
    script_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    atom_ids TEXT[] NOT NULL,
    script_content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'in_production', 'completed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_video_scripts_status ON video_scripts(status);
CREATE INDEX IF NOT EXISTS idx_video_scripts_created ON video_scripts(created_at DESC);

-- ============================================================================
-- 5. MANAGEMENT DASHBOARD
-- ============================================================================

-- Video approval queue
CREATE TABLE IF NOT EXISTS video_approval_queue (
    video_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    script_id UUID REFERENCES video_scripts(script_id) ON DELETE SET NULL,

    -- File paths
    video_path TEXT NOT NULL,
    thumbnail_path TEXT,
    audio_path TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Approval workflow
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'published')),
    priority INTEGER DEFAULT 0,

    -- Timestamps
    submitted_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    published_at TIMESTAMP,

    -- Review details
    reviewed_by VARCHAR(100),
    review_notes TEXT,

    -- YouTube publish details
    youtube_video_id VARCHAR(20),
    youtube_url TEXT,

    -- Additional metadata
    quality_score DECIMAL(3, 2),
    estimated_views INTEGER,
    target_keywords TEXT[],

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_video_approval_status ON video_approval_queue(status);
CREATE INDEX IF NOT EXISTS idx_video_approval_priority ON video_approval_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_video_approval_submitted ON video_approval_queue(submitted_at DESC);

-- Agent status tracking
CREATE TABLE IF NOT EXISTS agent_status (
    agent_name VARCHAR(100) PRIMARY KEY,
    team VARCHAR(50),
    status VARCHAR(20) DEFAULT 'stopped' CHECK (status IN ('running', 'paused', 'error', 'stopped')),

    -- Execution tracking
    last_run_at TIMESTAMP,
    last_success_at TIMESTAMP,
    last_error_at TIMESTAMP,
    last_error TEXT,

    -- Counters
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    uptime_seconds INTEGER DEFAULT 0,

    -- Performance metrics
    avg_execution_time_seconds DECIMAL(10, 2),
    last_execution_time_seconds DECIMAL(10, 2),

    -- Resource usage
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5, 2),

    -- Configuration
    enabled BOOLEAN DEFAULT true,
    auto_restart BOOLEAN DEFAULT true,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_status_status ON agent_status(status);
CREATE INDEX IF NOT EXISTS idx_agent_status_team ON agent_status(team);
CREATE INDEX IF NOT EXISTS idx_agent_status_last_run ON agent_status(last_run_at DESC);

-- Alert history
CREATE TABLE IF NOT EXISTS alert_history (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Classification
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('critical', 'high', 'medium', 'low')),

    -- Content
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',

    -- Delivery tracking
    sent_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,

    -- Acknowledgment
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100),
    acknowledgment_notes TEXT,

    -- Action tracking
    action_required BOOLEAN DEFAULT false,
    action_taken TEXT,
    resolved_at TIMESTAMP,

    -- Related entities
    related_agent VARCHAR(100),
    related_video_id UUID,
    related_error_id UUID,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_history_type ON alert_history(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_history_severity ON alert_history(severity);
CREATE INDEX IF NOT EXISTS idx_alert_history_sent ON alert_history(sent_at DESC);

-- ============================================================================
-- 6. SEARCH FUNCTIONS
-- ============================================================================

-- Function: Semantic search (vector similarity)
CREATE OR REPLACE FUNCTION search_atoms_by_embedding(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    atom_id text,
    title text,
    summary text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ka.atom_id,
        ka.title,
        ka.summary,
        1 - (ka.embedding <=> query_embedding) as similarity
    FROM knowledge_atoms ka
    WHERE 1 - (ka.embedding <=> query_embedding) > match_threshold
    ORDER BY ka.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function: Hybrid search (vector + keyword)
CREATE OR REPLACE FUNCTION search_atoms_hybrid(
    query_embedding vector(1536),
    query_text text,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    atom_id text,
    title text,
    summary text,
    vector_score float,
    text_rank float,
    combined_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_search AS (
        SELECT
            ka.atom_id,
            ka.title,
            ka.summary,
            1 - (ka.embedding <=> query_embedding) as similarity
        FROM knowledge_atoms ka
        ORDER BY ka.embedding <=> query_embedding
        LIMIT match_count * 3
    ),
    text_search AS (
        SELECT
            ka.atom_id,
            ts_rank(
                to_tsvector('english', ka.title || ' ' || ka.summary || ' ' || ka.content),
                plainto_tsquery('english', query_text)
            ) as rank
        FROM knowledge_atoms ka
        WHERE to_tsvector('english', ka.title || ' ' || ka.summary || ' ' || ka.content)
            @@ plainto_tsquery('english', query_text)
    )
    SELECT
        vs.atom_id,
        vs.title,
        vs.summary,
        vs.similarity as vector_score,
        COALESCE(ts.rank, 0) as text_rank,
        (vs.similarity * 0.7 + COALESCE(ts.rank, 0) * 0.3) as combined_score
    FROM vector_search vs
    LEFT JOIN text_search ts ON vs.atom_id = ts.atom_id
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;

-- Function: Get related atoms (via prerequisites/related_atoms)
CREATE OR REPLACE FUNCTION get_related_atoms(
    source_atom_id text,
    max_depth int DEFAULT 2
)
RETURNS TABLE (
    atom_id text,
    title text,
    relation_type text,
    depth int
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE atom_graph AS (
        SELECT
            ka.atom_id,
            ka.title,
            'prerequisite'::text as relation_type,
            1 as depth
        FROM knowledge_atoms ka
        WHERE ka.atom_id = ANY(
            SELECT unnest(prerequisites)
            FROM knowledge_atoms
            WHERE knowledge_atoms.atom_id = source_atom_id
        )

        UNION

        SELECT
            ka.atom_id,
            ka.title,
            'related'::text as relation_type,
            1 as depth
        FROM knowledge_atoms ka
        WHERE ka.atom_id = ANY(
            SELECT unnest(related_atoms)
            FROM knowledge_atoms
            WHERE knowledge_atoms.atom_id = source_atom_id
        )

        UNION

        SELECT
            ka.atom_id,
            ka.title,
            ag.relation_type,
            ag.depth + 1
        FROM atom_graph ag
        JOIN knowledge_atoms ka ON ka.atom_id = ANY(
            SELECT unnest(ka2.prerequisites || ka2.related_atoms)
            FROM knowledge_atoms ka2
            WHERE ka2.atom_id = ag.atom_id
        )
        WHERE ag.depth < max_depth
    )
    SELECT DISTINCT * FROM atom_graph
    ORDER BY depth, atom_id;
END;
$$;

-- ============================================================================
-- 7. INITIAL DATA (24 Agents)
-- ============================================================================

INSERT INTO agent_status (agent_name, team, status) VALUES
    -- Executive Team (2)
    ('AICEOAgent', 'Executive', 'stopped'),
    ('AIChiefOfStaffAgent', 'Executive', 'stopped'),

    -- Research & Knowledge Team (6)
    ('ResearchAgent', 'Research', 'stopped'),
    ('AtomBuilderAgent', 'Research', 'stopped'),
    ('AtomLibrarianAgent', 'Research', 'stopped'),
    ('QualityCheckerAgent', 'Research', 'stopped'),
    ('OEMPDFScraperAgent', 'Research', 'stopped'),
    ('AtomBuilderFromPDF', 'Research', 'stopped'),

    -- Content Production Team (8)
    ('MasterCurriculumAgent', 'Content', 'stopped'),
    ('ContentStrategyAgent', 'Content', 'stopped'),
    ('ScriptwriterAgent', 'Content', 'stopped'),
    ('SEOAgent', 'Content', 'stopped'),
    ('ThumbnailAgent', 'Content', 'stopped'),
    ('ContentCuratorAgent', 'Content', 'stopped'),
    ('TrendScoutAgent', 'Content', 'stopped'),
    ('VideoQualityReviewerAgent', 'Content', 'stopped'),

    -- Media & Publishing Team (4)
    ('VoiceProductionAgent', 'Media', 'stopped'),
    ('VideoAssemblyAgent', 'Media', 'stopped'),
    ('PublishingStrategyAgent', 'Media', 'stopped'),
    ('YouTubeUploaderAgent', 'Media', 'stopped'),

    -- Engagement & Analytics Team (3)
    ('CommunityAgent', 'Engagement', 'stopped'),
    ('AnalyticsAgent', 'Engagement', 'stopped'),
    ('SocialAmplifierAgent', 'Engagement', 'stopped'),

    -- Orchestration (1)
    ('MasterOrchestratorAgent', 'Orchestration', 'stopped')
ON CONFLICT (agent_name) DO NOTHING;

-- ============================================================================
-- 8. ROW-LEVEL SECURITY (Disabled for now)
-- ============================================================================

ALTER TABLE agent_factory_settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE session_memories DISABLE ROW LEVEL SECURITY;
ALTER TABLE agent_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_atoms DISABLE ROW LEVEL SECURITY;
ALTER TABLE video_scripts DISABLE ROW LEVEL SECURITY;
ALTER TABLE video_approval_queue DISABLE ROW LEVEL SECURITY;
ALTER TABLE agent_status DISABLE ROW LEVEL SECURITY;
ALTER TABLE alert_history DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check all tables exist
SELECT table_name,
       (SELECT COUNT(*) FROM information_schema.columns WHERE columns.table_name = tables.table_name) as column_count
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'agent_factory_settings',
      'session_memories',
      'agent_messages',
      'knowledge_atoms',
      'video_scripts',
      'video_approval_queue',
      'agent_status',
      'alert_history'
  )
ORDER BY table_name;

-- Expected: 8 tables

-- Check critical columns exist
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('agent_messages', 'knowledge_atoms')
  AND column_name IN ('session_id', 'content')
ORDER BY table_name, column_name;

-- Expected:
-- agent_messages | session_id | text
-- knowledge_atoms | content | text

-- Check vector indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE tablename IN ('knowledge_atoms', 'session_memories')
  AND indexname LIKE '%embedding%'
ORDER BY tablename, indexname;

-- Check agent count
SELECT team, COUNT(*) as agent_count
FROM agent_status
GROUP BY team
ORDER BY team;

-- Expected:
-- Content: 8, Engagement: 3, Executive: 2, Media: 4, Orchestration: 1, Research: 6

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '==================================================================';
    RAISE NOTICE 'SUPABASE COMPLETE UNIFIED SCHEMA - DEPLOYMENT COMPLETE';
    RAISE NOTICE '==================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables Created (8):';
    RAISE NOTICE '  ✅ agent_factory_settings - Runtime configuration';
    RAISE NOTICE '  ✅ session_memories - Vector-enabled conversation memory';
    RAISE NOTICE '  ✅ agent_messages - Conversation history';
    RAISE NOTICE '  ✅ knowledge_atoms - PLC knowledge base with vector search';
    RAISE NOTICE '  ✅ video_scripts - Video production scripts';
    RAISE NOTICE '  ✅ video_approval_queue - CEO approval workflow';
    RAISE NOTICE '  ✅ agent_status - 24 agents tracking';
    RAISE NOTICE '  ✅ alert_history - Management alerts';
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes Created: 30+ (B-tree, GIN, HNSW for vectors)';
    RAISE NOTICE 'Search Functions: 3 (semantic, hybrid, related atoms)';
    RAISE NOTICE 'Initial Data: 24 agents, 6 default settings';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Upload knowledge atoms (2,045 ready)';
    RAISE NOTICE '  2. Test vector search functions';
    RAISE NOTICE '  3. Verify Telegram bot commands work';
    RAISE NOTICE '';
    RAISE NOTICE '==================================================================';
END $$;

-- ============================================================================
-- END OF UNIFIED SCHEMA
-- ============================================================================
