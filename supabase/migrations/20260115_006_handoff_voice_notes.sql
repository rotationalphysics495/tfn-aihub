-- Migration: Create handoff_voice_notes table for voice note attachments
-- Story: 9.3 - Voice Note Attachment
-- Date: 2026-01-15
--
-- This migration creates the infrastructure for storing voice notes attached
-- to shift handoffs. Each voice note includes audio storage path, transcript,
-- duration, and ordering within the handoff.
--
-- AC#2: Recording completion and transcription
-- AC#3: Multiple voice notes management
--
-- References:
-- - [Source: architecture/voice-briefing.md#Offline Caching Architecture]
-- - [Source: epic-9.md#Story 9.3]
-- - [Source: prd-functional-requirements.md#FR23 Voice Note Support]

-- ============================================================================
-- PREREQUISITE: shift_handoffs table (if not exists)
-- Note: Full implementation in Story 9.4, but basic structure needed here
-- ============================================================================

CREATE TABLE IF NOT EXISTS shift_handoffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    shift_date DATE NOT NULL,
    shift_type TEXT NOT NULL CHECK (shift_type IN ('morning', 'afternoon', 'night')),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending_acknowledgment', 'acknowledged')),
    assets_covered UUID[] DEFAULT '{}',
    summary TEXT,
    text_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Unique constraint: one handoff per user per shift
    CONSTRAINT unique_user_shift UNIQUE (user_id, shift_date, shift_type)
);

-- Enable RLS on shift_handoffs if not already enabled
ALTER TABLE shift_handoffs ENABLE ROW LEVEL SECURITY;

-- Policy for shift_handoffs (users can manage their own handoffs)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'shift_handoffs'
        AND policyname = 'Users can manage own handoffs'
    ) THEN
        CREATE POLICY "Users can manage own handoffs"
        ON shift_handoffs
        FOR ALL
        USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id);
    END IF;
END $$;

-- ============================================================================
-- TABLE: handoff_voice_notes
-- ============================================================================

CREATE TABLE IF NOT EXISTS handoff_voice_notes (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    handoff_id UUID NOT NULL REFERENCES shift_handoffs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Storage reference
    storage_path TEXT NOT NULL,

    -- Transcription (from ElevenLabs Scribe)
    transcript TEXT,

    -- Metadata
    duration_seconds INTEGER NOT NULL,
    sequence_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT valid_duration CHECK (duration_seconds > 0 AND duration_seconds <= 60),
    CONSTRAINT valid_sequence CHECK (sequence_order >= 0)
);

-- Comment on table
COMMENT ON TABLE handoff_voice_notes IS 'Voice notes attached to shift handoffs (Story 9.3)';

-- Comments on columns
COMMENT ON COLUMN handoff_voice_notes.id IS 'Unique identifier for the voice note';
COMMENT ON COLUMN handoff_voice_notes.handoff_id IS 'Reference to the parent shift handoff';
COMMENT ON COLUMN handoff_voice_notes.user_id IS 'Reference to the user who created the voice note';
COMMENT ON COLUMN handoff_voice_notes.storage_path IS 'Path in Supabase Storage: handoff-voice-notes/{user_id}/{handoff_id}/{note_id}.webm';
COMMENT ON COLUMN handoff_voice_notes.transcript IS 'ElevenLabs Scribe transcription of the audio';
COMMENT ON COLUMN handoff_voice_notes.duration_seconds IS 'Duration of the recording in seconds (max 60)';
COMMENT ON COLUMN handoff_voice_notes.sequence_order IS 'Order of the voice note within the handoff (0-indexed)';
COMMENT ON COLUMN handoff_voice_notes.created_at IS 'Timestamp when the voice note was created';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for efficient queries by handoff (ordered by sequence)
CREATE INDEX IF NOT EXISTS idx_voice_notes_handoff_sequence
ON handoff_voice_notes(handoff_id, sequence_order);

-- Index for efficient user lookups (for RLS and queries)
CREATE INDEX IF NOT EXISTS idx_voice_notes_user
ON handoff_voice_notes(user_id);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on the table
ALTER TABLE handoff_voice_notes ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own voice notes
-- This allows SELECT, INSERT, UPDATE, DELETE on voice notes the user created
CREATE POLICY "Users can manage own voice notes"
ON handoff_voice_notes
FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can view voice notes for handoffs they have access to
-- This allows incoming supervisors to view voice notes on handoffs assigned to them
-- (will be expanded in Story 9.5 for incoming supervisor view)
CREATE POLICY "Users can view handoff voice notes"
ON handoff_voice_notes
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM shift_handoffs
        WHERE shift_handoffs.id = handoff_voice_notes.handoff_id
        AND (
            shift_handoffs.user_id = auth.uid()  -- Owner
            -- OR shift_handoffs.acknowledged_by_user_id = auth.uid()  -- Incoming (Story 9.7)
        )
    )
);

-- ============================================================================
-- FUNCTION: Enforce max 5 notes per handoff
-- ============================================================================

-- Function to check voice note count before insert
CREATE OR REPLACE FUNCTION check_voice_note_limit()
RETURNS TRIGGER AS $$
DECLARE
    note_count INTEGER;
BEGIN
    -- Count existing notes for this handoff
    SELECT COUNT(*)
    INTO note_count
    FROM handoff_voice_notes
    WHERE handoff_id = NEW.handoff_id;

    -- Enforce 5 note maximum
    IF note_count >= 5 THEN
        RAISE EXCEPTION 'Maximum of 5 voice notes per handoff exceeded'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to enforce limit on insert
DROP TRIGGER IF EXISTS enforce_voice_note_limit ON handoff_voice_notes;
CREATE TRIGGER enforce_voice_note_limit
    BEFORE INSERT ON handoff_voice_notes
    FOR EACH ROW
    EXECUTE FUNCTION check_voice_note_limit();

-- Comment on function
COMMENT ON FUNCTION check_voice_note_limit() IS 'Enforces maximum of 5 voice notes per handoff';

-- ============================================================================
-- FUNCTION: Auto-assign sequence order
-- ============================================================================

-- Function to auto-assign sequence order on insert
CREATE OR REPLACE FUNCTION auto_assign_sequence_order()
RETURNS TRIGGER AS $$
DECLARE
    max_sequence INTEGER;
BEGIN
    -- Get the current max sequence for this handoff
    SELECT COALESCE(MAX(sequence_order), -1)
    INTO max_sequence
    FROM handoff_voice_notes
    WHERE handoff_id = NEW.handoff_id;

    -- Assign next sequence number
    NEW.sequence_order := max_sequence + 1;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-assign sequence
DROP TRIGGER IF EXISTS auto_voice_note_sequence ON handoff_voice_notes;
CREATE TRIGGER auto_voice_note_sequence
    BEFORE INSERT ON handoff_voice_notes
    FOR EACH ROW
    WHEN (NEW.sequence_order IS NULL OR NEW.sequence_order = 0)
    EXECUTE FUNCTION auto_assign_sequence_order();

-- Comment on function
COMMENT ON FUNCTION auto_assign_sequence_order() IS 'Auto-assigns sequence order to new voice notes';

-- ============================================================================
-- STORAGE BUCKET SETUP
-- ============================================================================

-- Note: Supabase Storage bucket creation is done via Supabase Dashboard or API
-- The bucket should be configured with:
--   Name: handoff-voice-notes
--   Public: false (private)
--   File size limit: 10MB
--   Allowed MIME types: audio/webm, audio/ogg, audio/mp4
--
-- Storage policies should be configured as:
--   SELECT: Allow authenticated users to read their own files
--   INSERT: Allow authenticated users to upload to their user_id folder
--   DELETE: Allow authenticated users to delete their own files
--
-- Path structure: {user_id}/{handoff_id}/{note_id}.webm

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check table exists:
--   SELECT table_name FROM information_schema.tables
--   WHERE table_name = 'handoff_voice_notes';
--
-- Check indexes:
--   SELECT indexname FROM pg_indexes
--   WHERE tablename = 'handoff_voice_notes';
--
-- Check RLS policies:
--   SELECT policyname FROM pg_policies
--   WHERE tablename = 'handoff_voice_notes';
--
-- Check triggers:
--   SELECT tgname FROM pg_trigger
--   WHERE tgrelid = 'handoff_voice_notes'::regclass;
