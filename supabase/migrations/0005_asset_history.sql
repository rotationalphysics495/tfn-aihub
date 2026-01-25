-- Migration: Create Asset History tables
-- Story: 4.4 - Asset History Memory
-- Date: 2026-01-06
--
-- This migration creates the Asset History layer tables:
--   - asset_history: Stores historical events, resolutions, and notes for assets
--   - asset_history_embeddings: Vector embeddings for semantic search
--
-- All tables include:
--   - UUID primary keys (auto-generated)
--   - Foreign key relationships to assets table
--   - Row Level Security (RLS) policies
--   - Performance indexes for common query patterns

-- ============================================================================
-- SETUP: Enable required extensions
-- ============================================================================

-- Enable pgvector extension for vector similarity search (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- TABLE: asset_history
-- ============================================================================
-- Stores historical events, maintenance actions, resolutions, and notes for assets.
-- Used for AI context retrieval when answering questions like "Why does X keep failing?"

CREATE TABLE IF NOT EXISTS asset_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('downtime', 'maintenance', 'resolution', 'note', 'incident')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    resolution TEXT,
    outcome VARCHAR(100) CHECK (outcome IS NULL OR outcome IN ('resolved', 'ongoing', 'escalated', 'deferred')),
    source VARCHAR(50) NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'system', 'ai-generated')),
    related_record_type VARCHAR(50),  -- e.g., 'downtime_event', 'safety_event'
    related_record_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- Add comments for documentation
COMMENT ON TABLE asset_history IS 'Historical events, resolutions, and context for manufacturing assets (Story 4.4)';
COMMENT ON COLUMN asset_history.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN asset_history.asset_id IS 'Foreign key reference to assets table';
COMMENT ON COLUMN asset_history.event_type IS 'Type of event: downtime, maintenance, resolution, note, incident';
COMMENT ON COLUMN asset_history.title IS 'Short title describing the event';
COMMENT ON COLUMN asset_history.description IS 'Detailed description of the event';
COMMENT ON COLUMN asset_history.resolution IS 'How the issue was resolved (if applicable)';
COMMENT ON COLUMN asset_history.outcome IS 'Current status: resolved, ongoing, escalated, deferred';
COMMENT ON COLUMN asset_history.source IS 'How the entry was created: manual, system, ai-generated';
COMMENT ON COLUMN asset_history.related_record_type IS 'Type of related record (e.g., downtime_event, safety_event)';
COMMENT ON COLUMN asset_history.related_record_id IS 'UUID of the related record';
COMMENT ON COLUMN asset_history.created_by IS 'User who created this entry (references auth.users)';

-- Index on asset_id for efficient lookups by asset (AC#1 Task 1.3)
CREATE INDEX IF NOT EXISTS idx_asset_history_asset_id ON asset_history(asset_id);

-- Index on event_type for filtering by event type (AC#1 Task 1.4)
CREATE INDEX IF NOT EXISTS idx_asset_history_event_type ON asset_history(event_type);

-- Index on created_at for temporal queries (AC#2 - recent events)
CREATE INDEX IF NOT EXISTS idx_asset_history_created_at ON asset_history(created_at DESC);

-- Composite index for asset + time queries
CREATE INDEX IF NOT EXISTS idx_asset_history_asset_created ON asset_history(asset_id, created_at DESC);

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_asset_history_updated_at ON asset_history;
CREATE TRIGGER update_asset_history_updated_at
    BEFORE UPDATE ON asset_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: asset_history_embeddings
-- ============================================================================
-- Stores vector embeddings for semantic search of asset history entries.
-- Uses OpenAI text-embedding-3-small (1536 dimensions).

CREATE TABLE IF NOT EXISTS asset_history_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    history_id UUID NOT NULL REFERENCES asset_history(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT asset_history_embeddings_history_id_unique UNIQUE (history_id)
);

-- Add comments for documentation
COMMENT ON TABLE asset_history_embeddings IS 'Vector embeddings for semantic search of asset history (Story 4.4)';
COMMENT ON COLUMN asset_history_embeddings.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN asset_history_embeddings.history_id IS 'Foreign key reference to asset_history table';
COMMENT ON COLUMN asset_history_embeddings.embedding IS 'Vector embedding (1536 dimensions for text-embedding-3-small)';

-- HNSW index for fast similarity search (AC#2 Task 2.4)
-- Using cosine distance operator for semantic similarity
CREATE INDEX IF NOT EXISTS idx_asset_history_embeddings_vector
ON asset_history_embeddings
USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- Enable RLS on all tables and create policies:
--   - Authenticated users can SELECT and INSERT
--   - Service role has full access for backend operations

-- Enable RLS on all tables (AC#1 Task 1.5)
ALTER TABLE asset_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_history_embeddings ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES: asset_history
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Authenticated users can view asset history" ON asset_history;
DROP POLICY IF EXISTS "Authenticated users can create asset history" ON asset_history;
DROP POLICY IF EXISTS "Allow service_role full access on asset_history" ON asset_history;

-- Authenticated users can SELECT (AC#3 - read access)
CREATE POLICY "Authenticated users can view asset history"
    ON asset_history FOR SELECT
    TO authenticated
    USING (true);

-- Authenticated users can INSERT (AC#3 - create entries)
CREATE POLICY "Authenticated users can create asset history"
    ON asset_history FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Service role has full access (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "Allow service_role full access on asset_history"
    ON asset_history FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: asset_history_embeddings
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Authenticated users can view asset history embeddings" ON asset_history_embeddings;
DROP POLICY IF EXISTS "Allow service_role full access on asset_history_embeddings" ON asset_history_embeddings;

-- Authenticated users can SELECT (needed for search)
CREATE POLICY "Authenticated users can view asset history embeddings"
    ON asset_history_embeddings FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (embeddings created by backend only)
CREATE POLICY "Allow service_role full access on asset_history_embeddings"
    ON asset_history_embeddings FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- HELPER FUNCTION: Semantic search for asset history
-- ============================================================================
-- Function to search asset history by vector similarity with optional asset filter

CREATE OR REPLACE FUNCTION search_asset_history(
    query_embedding vector(1536),
    p_asset_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    history_id UUID,
    asset_id UUID,
    event_type VARCHAR(50),
    title VARCHAR(255),
    description TEXT,
    resolution TEXT,
    outcome VARCHAR(100),
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ah.id AS history_id,
        ah.asset_id,
        ah.event_type,
        ah.title,
        ah.description,
        ah.resolution,
        ah.outcome,
        ah.source,
        ah.created_at,
        1 - (ahe.embedding <=> query_embedding) AS similarity
    FROM asset_history ah
    JOIN asset_history_embeddings ahe ON ah.id = ahe.history_id
    WHERE (p_asset_id IS NULL OR ah.asset_id = p_asset_id)
    ORDER BY ahe.embedding <=> query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check tables exist and have correct columns:
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_name IN ('asset_history', 'asset_history_embeddings')
--   ORDER BY table_name, ordinal_position;
--
-- Check foreign keys:
--   SELECT tc.constraint_name, tc.table_name, kcu.column_name,
--          ccu.table_name AS foreign_table_name,
--          ccu.column_name AS foreign_column_name
--   FROM information_schema.table_constraints AS tc
--   JOIN information_schema.key_column_usage AS kcu
--     ON tc.constraint_name = kcu.constraint_name
--   JOIN information_schema.constraint_column_usage AS ccu
--     ON ccu.constraint_name = tc.constraint_name
--   WHERE constraint_type = 'FOREIGN KEY'
--     AND tc.table_name IN ('asset_history', 'asset_history_embeddings');
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename IN ('asset_history', 'asset_history_embeddings');
--
-- Check RLS is enabled:
--   SELECT tablename, rowsecurity
--   FROM pg_tables
--   WHERE tablename IN ('asset_history', 'asset_history_embeddings');
--
-- Check vector extension:
--   SELECT * FROM pg_extension WHERE extname = 'vector';
