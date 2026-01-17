-- Migration: Create handoff_qa_entries table for Story 9.6
-- Story: 9.6 - Handoff Q&A
-- Date: 2026-01-16
--
-- This migration creates the handoff_qa_entries table for storing
-- Q&A threads on shift handoffs.
--
-- AC#1: Users can type or speak questions about handoff content
-- AC#2: AI responses include citations to source data (FR52)
-- AC#3: Outgoing supervisor can respond directly
-- AC#4: All Q&A entries are preserved and visible
--
-- References:
-- - [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
-- - [Source: prd/prd-functional-requirements.md#FR26,FR52]
-- - [Source: prd/prd-non-functional-requirements.md#NFR24]

-- ============================================================================
-- CREATE handoff_qa_entries TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS handoff_qa_entries (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to parent handoff
    handoff_id UUID NOT NULL REFERENCES shift_handoffs(id) ON DELETE CASCADE,

    -- User who created this entry (questioner or responder)
    user_id UUID NOT NULL REFERENCES auth.users(id),

    -- Display name of user (denormalized for performance)
    user_name TEXT,

    -- Content type: question, ai_answer, human_response
    content_type TEXT NOT NULL,

    -- The actual content (question text or response text)
    content TEXT NOT NULL,

    -- Citations for AI responses (JSONB array)
    -- Structure: [{value, field, table, context, timestamp}]
    citations JSONB DEFAULT '[]'::jsonb,

    -- Optional voice transcript if question was spoken
    voice_transcript TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- CONSTRAINTS
-- ============================================================================

-- Content type must be valid
ALTER TABLE handoff_qa_entries
ADD CONSTRAINT handoff_qa_entries_content_type_check
CHECK (content_type IN ('question', 'ai_answer', 'human_response'));

-- Content cannot be empty
ALTER TABLE handoff_qa_entries
ADD CONSTRAINT handoff_qa_entries_content_not_empty
CHECK (LENGTH(TRIM(content)) > 0);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index on handoff_id for efficient thread retrieval (AC#4)
CREATE INDEX IF NOT EXISTS idx_handoff_qa_entries_handoff_id
ON handoff_qa_entries(handoff_id);

-- Index for ordering entries by creation time
CREATE INDEX IF NOT EXISTS idx_handoff_qa_entries_created_at
ON handoff_qa_entries(handoff_id, created_at);

-- Index on user_id for querying user's questions
CREATE INDEX IF NOT EXISTS idx_handoff_qa_entries_user_id
ON handoff_qa_entries(user_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE handoff_qa_entries ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read Q&A entries for handoffs they have access to
-- Access is granted if:
-- 1. User created the handoff (outgoing supervisor)
-- 2. User is assigned to assets covered by the handoff (incoming supervisor)
CREATE POLICY handoff_qa_entries_select_policy ON handoff_qa_entries
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM shift_handoffs h
        WHERE h.id = handoff_qa_entries.handoff_id
        AND (
            -- Creator can always see (user_id is the creator)
            h.user_id = auth.uid()
            -- Or user is assigned to covered assets
            OR EXISTS (
                SELECT 1 FROM supervisor_assignments sa
                WHERE sa.user_id = auth.uid()
                AND sa.asset_id = ANY(h.assets_covered)
            )
        )
    )
);

-- Policy: Users can insert Q&A entries for handoffs they have access to
CREATE POLICY handoff_qa_entries_insert_policy ON handoff_qa_entries
FOR INSERT
WITH CHECK (
    -- User must be authenticated
    auth.uid() IS NOT NULL
    -- User must have access to the handoff
    AND EXISTS (
        SELECT 1 FROM shift_handoffs h
        WHERE h.id = handoff_qa_entries.handoff_id
        AND (
            h.user_id = auth.uid()
            OR EXISTS (
                SELECT 1 FROM supervisor_assignments sa
                WHERE sa.user_id = auth.uid()
                AND sa.asset_id = ANY(h.assets_covered)
            )
        )
    )
    -- User must match the entry's user_id
    AND handoff_qa_entries.user_id = auth.uid()
);

-- Policy: No updates allowed (append-only per NFR24)
-- Entries are immutable once created
CREATE POLICY handoff_qa_entries_update_policy ON handoff_qa_entries
FOR UPDATE
USING (false);

-- Policy: No deletes allowed (append-only per NFR24)
CREATE POLICY handoff_qa_entries_delete_policy ON handoff_qa_entries
FOR DELETE
USING (false);

-- ============================================================================
-- REALTIME CONFIGURATION (AC#3)
-- ============================================================================

-- Enable Supabase Realtime for this table
-- This allows real-time notifications when new Q&A entries are added
ALTER PUBLICATION supabase_realtime ADD TABLE handoff_qa_entries;

-- ============================================================================
-- TABLE COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE handoff_qa_entries IS
    'Q&A entries for shift handoffs (Story 9.6). Append-only (immutable) per NFR24.';

COMMENT ON COLUMN handoff_qa_entries.id IS
    'Unique identifier (UUID)';

COMMENT ON COLUMN handoff_qa_entries.handoff_id IS
    'Parent handoff ID (FK to shift_handoffs)';

COMMENT ON COLUMN handoff_qa_entries.user_id IS
    'User who created this entry (FK to auth.users)';

COMMENT ON COLUMN handoff_qa_entries.user_name IS
    'Display name of user (denormalized for performance)';

COMMENT ON COLUMN handoff_qa_entries.content_type IS
    'Type of entry: question, ai_answer, human_response';

COMMENT ON COLUMN handoff_qa_entries.content IS
    'Question text or response text';

COMMENT ON COLUMN handoff_qa_entries.citations IS
    'JSONB array of citations for AI responses. Structure: [{value, field, table, context, timestamp}]';

COMMENT ON COLUMN handoff_qa_entries.voice_transcript IS
    'Original voice transcript if question was spoken';

COMMENT ON COLUMN handoff_qa_entries.created_at IS
    'Timestamp when entry was created';

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check table exists:
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_name = 'handoff_qa_entries'
--   ORDER BY ordinal_position;
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename = 'handoff_qa_entries';
--
-- Check RLS policies:
--   SELECT policyname, cmd, qual
--   FROM pg_policies
--   WHERE tablename = 'handoff_qa_entries';
--
-- Check Realtime is enabled:
--   SELECT * FROM pg_publication_tables
--   WHERE tablename = 'handoff_qa_entries';
