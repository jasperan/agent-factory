-- Add citations column to knowledge_atoms table
-- Run this in Supabase SQL Editor if you don't want to run the full schema

ALTER TABLE knowledge_atoms
ADD COLUMN IF NOT EXISTS citations JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN knowledge_atoms.citations IS 'Perplexity-style citations: [{"id": 1, "url": "...", "title": "...", "accessed_at": "..."}]';

-- Verify column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'knowledge_atoms'
  AND column_name = 'citations';
