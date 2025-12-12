-- ============================================================================
-- VECTOR SEARCH SETUP FOR KNOWLEDGE BASE
-- ============================================================================
-- Run this in Supabase SQL Editor to enable semantic search
-- ============================================================================

-- Step 1: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Create vector index on embeddings (HNSW for fast similarity search)
-- Note: embedding column should be type vector(1536) for OpenAI text-embedding-3-small
CREATE INDEX IF NOT EXISTS idx_knowledge_atoms_embedding
ON knowledge_atoms
USING hnsw (embedding vector_cosine_ops);

-- Step 3: Create RPC function for semantic search
CREATE OR REPLACE FUNCTION search_atoms_by_embedding(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    atom_id text,
    atom_type text,
    title text,
    summary text,
    content text,
    manufacturer text,
    product text,
    difficulty text,
    keywords text[],
    source_manual text,
    source_page int,
    similarity float
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        atom_id,
        atom_type,
        title,
        summary,
        content,
        manufacturer,
        product,
        difficulty,
        keywords,
        source_manual,
        source_page,
        1 - (embedding <=> query_embedding) AS similarity
    FROM knowledge_atoms
    WHERE embedding IS NOT NULL
        AND 1 - (embedding <=> query_embedding) >= match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Step 4: Test the function
SELECT * FROM search_atoms_by_embedding(
    (SELECT embedding FROM knowledge_atoms WHERE embedding IS NOT NULL LIMIT 1),
    0.5,
    3
);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'knowledge_atoms'
    AND indexname = 'idx_knowledge_atoms_embedding';

-- Check function exists
SELECT proname, pronargs
FROM pg_proc
WHERE proname = 'search_atoms_by_embedding';

-- Count atoms with embeddings
SELECT
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE embedding IS NULL) as without_embeddings,
    COUNT(*) as total
FROM knowledge_atoms;

-- ============================================================================
-- EXPECTED OUTPUT
-- ============================================================================
--
-- pg_extension: Should show vector extension installed
-- pg_indexes: Should show idx_knowledge_atoms_embedding index
-- pg_proc: Should show search_atoms_by_embedding function
-- COUNT: Should show all atoms have embeddings
--
-- ============================================================================
