-- Migration: Create Mem0 Vector Memory Schema
-- Story: 4.1 - Mem0 Vector Memory Integration
-- Date: 2026-01-06
--
-- This migration creates the vector storage infrastructure for Mem0:
--   - Enables pgvector extension
--   - Creates memories table with vector(1536) embedding column
--   - Creates match_vectors RPC function for similarity search
--   - Creates HNSW index for optimal search performance
--   - Creates metadata indexes for filtering

-- ============================================================================
-- SETUP: Enable pgvector extension
-- ============================================================================
-- AC#2: Enable the pgvector extension for vector similarity search

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- TABLE: memories
-- ============================================================================
-- AC#2: Create the memories table for Mem0 vector storage
-- Stores embeddings and metadata for user interactions

CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Add comments for documentation
COMMENT ON TABLE memories IS 'Vector memory storage for Mem0 - stores user interactions with embeddings for semantic search';
COMMENT ON COLUMN memories.id IS 'Unique identifier for the memory (TEXT primary key)';
COMMENT ON COLUMN memories.embedding IS 'OpenAI text-embedding-ada-002 1536-dimensional vector';
COMMENT ON COLUMN memories.metadata IS 'JSONB metadata including user_id, asset_id, timestamp, and context';
COMMENT ON COLUMN memories.created_at IS 'Timestamp when memory was created';
COMMENT ON COLUMN memories.updated_at IS 'Timestamp when memory was last updated';

-- ============================================================================
-- INDEX: HNSW for vector similarity search
-- ============================================================================
-- AC#2: Create HNSW index for optimal similarity search performance
-- HNSW provides faster search at the cost of more memory

CREATE INDEX IF NOT EXISTS memories_embedding_idx
ON memories USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- FUNCTION: match_vectors
-- ============================================================================
-- AC#2: Create the vector similarity search function
-- Used by Mem0 to find semantically similar memories

CREATE OR REPLACE FUNCTION match_vectors(
    query_embedding vector(1536),
    match_count INT,
    filter JSONB DEFAULT '{}'::JSONB
)
RETURNS TABLE (
    id TEXT,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id::TEXT,
        1 - (t.embedding <=> query_embedding) AS similarity,
        t.metadata
    FROM memories t
    WHERE CASE
        WHEN filter::TEXT = '{}'::TEXT THEN TRUE
        ELSE t.metadata @> filter
    END
    ORDER BY t.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_vectors IS 'Semantic similarity search using cosine distance with optional JSONB filter';

-- ============================================================================
-- INDEXES: Metadata filtering
-- ============================================================================
-- AC#2: Create indexes on metadata for filtered queries

-- GIN index for general JSONB containment queries
CREATE INDEX IF NOT EXISTS memories_metadata_idx
ON memories USING gin (metadata);

-- Index on user_id within metadata for user-specific queries (AC#3)
CREATE INDEX IF NOT EXISTS memories_user_id_idx
ON memories ((metadata->>'user_id'));

-- Index on asset_id within metadata for asset-specific queries (AC#4)
CREATE INDEX IF NOT EXISTS memories_asset_id_idx
ON memories ((metadata->>'asset_id'));

-- ============================================================================
-- TRIGGER: Auto-update updated_at
-- ============================================================================
-- Use the existing update_updated_at_column function from plant object model

DROP TRIGGER IF EXISTS update_memories_updated_at ON memories;
CREATE TRIGGER update_memories_updated_at
    BEFORE UPDATE ON memories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- Enable RLS on memories table

ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read own memories" ON memories;
DROP POLICY IF EXISTS "Allow authenticated insert own memories" ON memories;
DROP POLICY IF EXISTS "Allow service_role full access on memories" ON memories;

-- Authenticated users can SELECT their own memories (user_id in metadata matches auth.uid())
CREATE POLICY "Allow authenticated read own memories"
    ON memories FOR SELECT
    TO authenticated
    USING (metadata->>'user_id' = auth.uid()::TEXT);

-- Authenticated users can INSERT their own memories
CREATE POLICY "Allow authenticated insert own memories"
    ON memories FOR INSERT
    TO authenticated
    WITH CHECK (metadata->>'user_id' = auth.uid()::TEXT);

-- Service role has full access (for backend operations)
CREATE POLICY "Allow service_role full access on memories"
    ON memories FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check pgvector extension:
--   SELECT * FROM pg_extension WHERE extname = 'vector';
--
-- Check table exists and has correct columns:
--   SELECT column_name, data_type, udt_name
--   FROM information_schema.columns
--   WHERE table_name = 'memories';
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename = 'memories';
--
-- Check function exists:
--   SELECT routine_name, routine_type
--   FROM information_schema.routines
--   WHERE routine_name = 'match_vectors';
--
-- Test vector similarity search (requires existing data):
--   SELECT * FROM match_vectors(
--     '[0.1, 0.2, ...]'::vector(1536),
--     5,
--     '{"user_id": "test-user"}'::JSONB
--   );
