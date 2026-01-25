-- Migration: Enhance shift_handoffs table for Story 9.4
-- Story: 9.4 - Persistent Handoff Records
-- Date: 2026-01-15
--
-- This migration enhances the shift_handoffs table with:
--   - Additional columns for comprehensive handoff tracking
--   - Immutability support via supplemental_notes JSONB
--   - Updated constraints and indexes
--
-- AC#1: Handoff stored with created_by, shift_date, shift_type, assets_covered
-- AC#2: Immutability via supplemental_notes append-only pattern
-- AC#3: Voice file references via handoff_voice_notes (created in Story 9.3)
-- AC#4: Status transitions for handoff lifecycle
--
-- Note: The base shift_handoffs table was created in Story 9.3 (20260115_006).
-- This migration adds the additional columns and constraints required for Story 9.4.
--
-- References:
-- - [Source: architecture/voice-briefing.md#Offline-Caching-Architecture]
-- - [Source: prd/prd-functional-requirements.md#FR21-FR30]
-- - [Source: prd/prd-non-functional-requirements.md#NFR24]

-- ============================================================================
-- ENHANCE shift_handoffs TABLE
-- ============================================================================

-- Add missing columns if they don't exist
-- created_by: Maps to the user who created the handoff (for RLS)
DO $$
BEGIN
    -- Add created_by column (FK to auth.users)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'shift_handoffs' AND column_name = 'created_by'
    ) THEN
        ALTER TABLE shift_handoffs
        ADD COLUMN created_by UUID REFERENCES auth.users(id);

        -- Populate from existing user_id column
        UPDATE shift_handoffs SET created_by = user_id WHERE created_by IS NULL;

        -- Make NOT NULL after population
        ALTER TABLE shift_handoffs ALTER COLUMN created_by SET NOT NULL;
    END IF;
END $$;

-- Add summary_text column (the main handoff summary - immutable once submitted)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'shift_handoffs' AND column_name = 'summary_text'
    ) THEN
        ALTER TABLE shift_handoffs
        ADD COLUMN summary_text TEXT;

        -- Copy from existing summary column if present
        UPDATE shift_handoffs
        SET summary_text = summary
        WHERE summary_text IS NULL AND summary IS NOT NULL;
    END IF;
END $$;

-- Add notes column (user notes - immutable once submitted)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'shift_handoffs' AND column_name = 'notes'
    ) THEN
        ALTER TABLE shift_handoffs
        ADD COLUMN notes TEXT;

        -- Copy from existing text_notes column if present
        UPDATE shift_handoffs
        SET notes = text_notes
        WHERE notes IS NULL AND text_notes IS NOT NULL;
    END IF;
END $$;

-- Add supplemental_notes column (JSONB array for append-only notes - AC#2)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'shift_handoffs' AND column_name = 'supplemental_notes'
    ) THEN
        ALTER TABLE shift_handoffs
        ADD COLUMN supplemental_notes JSONB DEFAULT '[]'::jsonb;

        -- Add comment explaining the append-only pattern
        COMMENT ON COLUMN shift_handoffs.supplemental_notes IS
            'Append-only array of supplemental notes. Structure: [{added_at, added_by, note_text}]. AC#2 immutability.';
    END IF;
END $$;

-- Add acknowledged_by column for incoming supervisor
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'shift_handoffs' AND column_name = 'acknowledged_by'
    ) THEN
        ALTER TABLE shift_handoffs
        ADD COLUMN acknowledged_by UUID REFERENCES auth.users(id);

        COMMENT ON COLUMN shift_handoffs.acknowledged_by IS
            'User ID of incoming supervisor who acknowledged the handoff';
    END IF;
END $$;

-- Add acknowledged_at timestamp
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'shift_handoffs' AND column_name = 'acknowledged_at'
    ) THEN
        ALTER TABLE shift_handoffs
        ADD COLUMN acknowledged_at TIMESTAMPTZ;

        COMMENT ON COLUMN shift_handoffs.acknowledged_at IS
            'Timestamp when handoff was acknowledged';
    END IF;
END $$;

-- ============================================================================
-- UPDATE STATUS CHECK CONSTRAINT
-- ============================================================================

-- Update status constraint to include 'expired' status (AC#1)
-- First drop the existing constraint if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'shift_handoffs'
        AND constraint_type = 'CHECK'
        AND constraint_name LIKE '%status%'
    ) THEN
        -- Find and drop the existing status check constraint
        EXECUTE (
            SELECT 'ALTER TABLE shift_handoffs DROP CONSTRAINT ' || constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'shift_handoffs'
            AND constraint_type = 'CHECK'
            AND constraint_name LIKE '%status%'
            LIMIT 1
        );
    END IF;
EXCEPTION WHEN undefined_object THEN
    -- Constraint doesn't exist, continue
    NULL;
END $$;

-- Add the complete status constraint (includes 'expired' for AC#1)
DO $$
BEGIN
    ALTER TABLE shift_handoffs
    ADD CONSTRAINT shift_handoffs_status_check
    CHECK (status IN ('draft', 'pending_acknowledgment', 'acknowledged', 'expired'));
EXCEPTION WHEN duplicate_object THEN
    -- Constraint already exists
    NULL;
END $$;

-- ============================================================================
-- UPDATE SHIFT_TYPE CONSTRAINT
-- ============================================================================

-- Update shift_type constraint to align with ShiftType enum
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'shift_handoffs'
        AND constraint_type = 'CHECK'
        AND constraint_name LIKE '%shift_type%'
    ) THEN
        EXECUTE (
            SELECT 'ALTER TABLE shift_handoffs DROP CONSTRAINT ' || constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'shift_handoffs'
            AND constraint_type = 'CHECK'
            AND constraint_name LIKE '%shift_type%'
            LIMIT 1
        );
    END IF;
EXCEPTION WHEN undefined_object THEN
    NULL;
END $$;

-- Add shift_type constraint supporting all shift types
DO $$
BEGIN
    ALTER TABLE shift_handoffs
    ADD CONSTRAINT shift_handoffs_shift_type_check
    CHECK (shift_type IN ('morning', 'afternoon', 'night', 'day', 'swing'));
EXCEPTION WHEN duplicate_object THEN
    NULL;
END $$;

-- ============================================================================
-- INDEXES FOR EFFICIENT QUERIES
-- ============================================================================

-- Index for querying handoffs by creator (AC#1)
CREATE INDEX IF NOT EXISTS idx_shift_handoffs_created_by
ON shift_handoffs(created_by);

-- Index for querying by shift date (AC#1)
CREATE INDEX IF NOT EXISTS idx_shift_handoffs_shift_date
ON shift_handoffs(shift_date);

-- Index for querying by status (filtering pending handoffs)
CREATE INDEX IF NOT EXISTS idx_shift_handoffs_status
ON shift_handoffs(status);

-- Composite index for common query pattern: user's handoffs by date
CREATE INDEX IF NOT EXISTS idx_shift_handoffs_created_by_date
ON shift_handoffs(created_by, shift_date DESC);

-- Index for acknowledged_by to support incoming supervisor queries
CREATE INDEX IF NOT EXISTS idx_shift_handoffs_acknowledged_by
ON shift_handoffs(acknowledged_by) WHERE acknowledged_by IS NOT NULL;

-- ============================================================================
-- UPDATED_AT TRIGGER
-- ============================================================================

-- Ensure the update_updated_at_column function exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_shift_handoffs_updated_at ON shift_handoffs;
CREATE TRIGGER update_shift_handoffs_updated_at
    BEFORE UPDATE ON shift_handoffs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE shift_handoffs IS
    'Shift handoff records with immutability guarantees (Story 9.4). Core fields are immutable once status != draft.';

COMMENT ON COLUMN shift_handoffs.id IS
    'Unique identifier (UUID)';

COMMENT ON COLUMN shift_handoffs.created_by IS
    'User ID of outgoing supervisor who created the handoff (FK to auth.users)';

COMMENT ON COLUMN shift_handoffs.shift_date IS
    'Date of the shift being handed off';

COMMENT ON COLUMN shift_handoffs.shift_type IS
    'Type of shift (morning/afternoon/night/day/swing)';

COMMENT ON COLUMN shift_handoffs.summary_text IS
    'Auto-generated shift summary (immutable once submitted)';

COMMENT ON COLUMN shift_handoffs.notes IS
    'User-provided text notes (immutable once submitted)';

COMMENT ON COLUMN shift_handoffs.supplemental_notes IS
    'Append-only JSONB array of supplemental notes added after submission';

COMMENT ON COLUMN shift_handoffs.status IS
    'Handoff status: draft, pending_acknowledgment, acknowledged, expired';

COMMENT ON COLUMN shift_handoffs.assets_covered IS
    'Array of asset UUIDs covered by this handoff';

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check table columns:
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_name = 'shift_handoffs'
--   ORDER BY ordinal_position;
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename = 'shift_handoffs';
--
-- Check constraints:
--   SELECT constraint_name, constraint_type
--   FROM information_schema.table_constraints
--   WHERE table_name = 'shift_handoffs';
