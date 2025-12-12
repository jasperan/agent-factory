-- ============================================================================
-- KNOWLEDGE ATOMS SCHEMA - Production Ready
-- Supabase PostgreSQL + pgvector for PLC Knowledge Base
-- ============================================================================
-- Purpose: Store knowledge atoms from OEM manuals with vector embeddings
-- Created: 2025-12-10
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for embeddings

-- ============================================================================
-- KNOWLEDGE ATOMS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_atoms (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Core identification
    atom_id TEXT UNIQUE NOT NULL,  -- Format: manufacturer:product:topic-slug
    atom_type TEXT NOT NULL,       -- concept, procedure, specification, pattern, fault, reference

    -- Content (optimally chunked for retrieval)
    title TEXT NOT NULL,           -- 50-100 chars
    summary TEXT NOT NULL,         -- 100-200 chars (for quick preview)
    content TEXT NOT NULL,         -- 200-1000 words (full explanation)

    -- Metadata for filtering
    manufacturer TEXT NOT NULL,     -- allen_bradley, siemens, mitsubishi, etc.
    product_family TEXT,            -- ControlLogix, S7-1200, etc.
    product_version TEXT,           -- 21.0, v1.2, etc.

    -- Learning metadata
    difficulty TEXT NOT NULL,       -- beginner, intermediate, advanced, expert
    prerequisites TEXT[] DEFAULT ARRAY[]::TEXT[],  -- Array of atom_ids
    related_atoms TEXT[] DEFAULT ARRAY[]::TEXT[],  -- Array of related atom_ids

    -- Citations and sources
    source_document TEXT NOT NULL,  -- Original PDF filename
    source_pages INTEGER[] NOT NULL, -- Page numbers (array)
    source_url TEXT,                -- URL to original PDF

    -- Quality and safety
    quality_score FLOAT DEFAULT 1.0,      -- 0.0-1.0 (extraction quality)
    safety_level TEXT DEFAULT 'info',     -- info, caution, warning, danger
    safety_notes TEXT,                    -- Safety warnings from document

    -- Search optimization
    keywords TEXT[] DEFAULT ARRAY[]::TEXT[],  -- Searchable keywords

    -- Vector embedding (OpenAI text-embedding-3-small = 1536 dimensions)
    embedding vector(1536),  -- pgvector for semantic search

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_atom_type CHECK (
        atom_type IN ('concept', 'procedure', 'specification', 'pattern', 'fault', 'reference')
    ),
    CONSTRAINT valid_difficulty CHECK (
        difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')
    ),
    CONSTRAINT valid_safety_level CHECK (
        safety_level IN ('info', 'caution', 'warning', 'danger')
    ),
    CONSTRAINT valid_quality_score CHECK (
        quality_score >= 0.0 AND quality_score <= 1.0
    )
);

-- ============================================================================
-- INDEXES FOR FAST QUERIES
-- ============================================================================

-- Primary lookup: atom_id
CREATE INDEX idx_knowledge_atoms_atom_id ON knowledge_atoms(atom_id);

-- Type filtering
CREATE INDEX idx_knowledge_atoms_type ON knowledge_atoms(atom_type);

-- Manufacturer filtering
CREATE INDEX idx_knowledge_atoms_manufacturer ON knowledge_atoms(manufacturer);

-- Product filtering
CREATE INDEX idx_knowledge_atoms_product ON knowledge_atoms(product_family);

-- Difficulty filtering
CREATE INDEX idx_knowledge_atoms_difficulty ON knowledge_atoms(difficulty);

-- Combined filter (manufacturer + product + type) - common query
CREATE INDEX idx_knowledge_atoms_mfr_product_type
ON knowledge_atoms(manufacturer, product_family, atom_type);

-- Full-text search on content
CREATE INDEX idx_knowledge_atoms_content_fts
ON knowledge_atoms USING GIN (to_tsvector('english', title || ' ' || summary || ' ' || content));

-- Keyword search (GIN index for array)
CREATE INDEX idx_knowledge_atoms_keywords
ON knowledge_atoms USING GIN (keywords);

-- CRITICAL: Vector similarity search (HNSW for fast approximate nearest neighbor)
-- This is THE KEY for semantic search
CREATE INDEX idx_knowledge_atoms_embedding
ON knowledge_atoms USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
-- m = 16: number of connections per layer (higher = more accurate, slower)
-- ef_construction = 64: quality of index construction (higher = better quality)

-- ============================================================================
-- FUNCTIONS FOR SEARCH
-- ============================================================================

-- Function 1: Semantic search (vector similarity)
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

-- Function 2: Hybrid search (vector + keyword)
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
        LIMIT match_count * 3  -- Get more candidates
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

-- Function 3: Get related atoms (via prerequisites/related_atoms)
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
        -- Base case: direct prerequisites and related
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

        -- Recursive case: follow the graph
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
-- ROW-LEVEL SECURITY (Disabled for now - enable in production)
-- ============================================================================

ALTER TABLE knowledge_atoms DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE knowledge_atoms IS
'Knowledge atoms from OEM PLC manuals with vector embeddings for semantic search';

COMMENT ON COLUMN knowledge_atoms.atom_id IS
'Unique identifier: manufacturer:product:topic-slug';

COMMENT ON COLUMN knowledge_atoms.embedding IS
'1536-dimensional vector from OpenAI text-embedding-3-small';

COMMENT ON COLUMN knowledge_atoms.content IS
'Full explanation (200-1000 words) optimally chunked for retrieval';

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Query 1: Vector search (semantic similarity)
/*
SELECT * FROM search_atoms_by_embedding(
    '[0.1, 0.2, ...]'::vector(1536),  -- Your query embedding
    0.7,  -- Similarity threshold (70%)
    10    -- Return top 10
);
*/

-- Query 2: Hybrid search (vector + text)
/*
SELECT * FROM search_atoms_hybrid(
    '[0.1, 0.2, ...]'::vector(1536),
    'motor control ladder logic',
    10
);
*/

-- Query 3: Filter by manufacturer and type
/*
SELECT atom_id, title, summary
FROM knowledge_atoms
WHERE manufacturer = 'allen_bradley'
AND atom_type = 'procedure'
AND difficulty = 'beginner'
ORDER BY created_at DESC
LIMIT 20;
*/

-- Query 4: Get prerequisites for a topic
/*
SELECT * FROM get_related_atoms('allen_bradley:controllogix:motor-control', 2);
*/

-- Query 5: Safety-critical content
/*
SELECT atom_id, title, safety_level, safety_notes
FROM knowledge_atoms
WHERE safety_level IN ('warning', 'danger')
ORDER BY safety_level DESC, created_at DESC;
*/

-- ============================================================================
-- MAINTENANCE
-- ============================================================================

-- Get table size
-- SELECT pg_size_pretty(pg_total_relation_size('knowledge_atoms')) as size;

-- Get index sizes
/*
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as size
FROM pg_indexes
WHERE tablename = 'knowledge_atoms'
ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC;
*/

-- Vacuum and analyze (run weekly)
-- VACUUM ANALYZE knowledge_atoms;

-- Rebuild HNSW index if needed (after bulk inserts)
-- REINDEX INDEX idx_knowledge_atoms_embedding;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
