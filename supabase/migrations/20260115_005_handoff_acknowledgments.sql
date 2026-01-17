-- Migration: Create handoff_acknowledgments table (Story 9.7)
-- Story: 9.7 - Acknowledgment Flow
-- Date: 2026-01-15
--
-- This migration creates the handoff_acknowledgments table for tracking
-- when incoming supervisors acknowledge receipt of shift handoffs.
--
-- AC#2: Acknowledgment Record Creation
-- - Creates record in handoff_acknowledgments
-- - Tracks acknowledged_by, acknowledged_at, notes
-- - Updates handoff status to "acknowledged"
-- - Creates audit trail entry (FR55)
--
-- AC#3: Optional Notes Attachment
-- - Notes are attached to the acknowledgment record
-- - Visible to both supervisors
--
-- References:
-- - [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
-- - [Source: prd/prd-functional-requirements.md#FR27-FR29]
-- - [Source: prd/prd-non-functional-requirements.md#NFR24]

-- ============================================================================
-- CREATE handoff_acknowledgments TABLE (AC#2)
-- ============================================================================

CREATE TABLE IF NOT EXISTS handoff_acknowledgments (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to shift_handoffs
    handoff_id UUID NOT NULL REFERENCES shift_handoffs(id) ON DELETE RESTRICT,

    -- User who acknowledged (incoming supervisor)
    acknowledged_by UUID NOT NULL REFERENCES auth.users(id),

    -- Timestamp when acknowledged
    acknowledged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Optional acknowledgment notes (AC#3)
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES (Task 1.5)
-- ============================================================================

-- Index on handoff_id for efficient lookups
CREATE INDEX IF NOT EXISTS idx_handoff_acknowledgments_handoff_id
ON handoff_acknowledgments(handoff_id);

-- Index on acknowledged_by for user queries
CREATE INDEX IF NOT EXISTS idx_handoff_acknowledgments_acknowledged_by
ON handoff_acknowledgments(acknowledged_by);

-- Index on acknowledged_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_handoff_acknowledgments_acknowledged_at
ON handoff_acknowledgments(acknowledged_at DESC);

-- Composite index for common query: user's acknowledgments by date
CREATE INDEX IF NOT EXISTS idx_handoff_acknowledgments_user_date
ON handoff_acknowledgments(acknowledged_by, acknowledged_at DESC);

-- ============================================================================
-- UNIQUE CONSTRAINT
-- ============================================================================

-- Each handoff can only be acknowledged once (prevent duplicate acknowledgments)
CREATE UNIQUE INDEX IF NOT EXISTS idx_handoff_acknowledgments_unique_handoff
ON handoff_acknowledgments(handoff_id);

-- ============================================================================
-- ROW LEVEL SECURITY (Task 1.4)
-- ============================================================================

-- Enable RLS
ALTER TABLE handoff_acknowledgments ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any (for clean slate)
DROP POLICY IF EXISTS "acknowledgments_select" ON handoff_acknowledgments;
DROP POLICY IF EXISTS "acknowledgments_insert" ON handoff_acknowledgments;
DROP POLICY IF EXISTS "acknowledgments_service_role" ON handoff_acknowledgments;

-- Policy: Users can read acknowledgments for handoffs they created or are assigned to
-- AC#3: Notes are visible to both supervisors
CREATE POLICY "acknowledgments_select"
    ON handoff_acknowledgments
    FOR SELECT
    TO authenticated
    USING (
        -- User created the acknowledgment
        acknowledged_by = auth.uid()
        OR
        -- User created the handoff (outgoing supervisor)
        EXISTS (
            SELECT 1 FROM shift_handoffs sh
            WHERE sh.id = handoff_acknowledgments.handoff_id
            AND (sh.created_by = auth.uid() OR sh.user_id = auth.uid())
        )
        OR
        -- User is assigned to the handoff's assets (incoming supervisor)
        EXISTS (
            SELECT 1 FROM shift_handoffs sh
            JOIN supervisor_assignments sa ON sa.asset_id = ANY(sh.assets_covered)
            WHERE sh.id = handoff_acknowledgments.handoff_id
            AND sa.user_id = auth.uid()
        )
    );

-- Policy: Users can only acknowledge handoffs assigned to them (Task 1.4)
-- This enforces that only the incoming supervisor can acknowledge
CREATE POLICY "acknowledgments_insert"
    ON handoff_acknowledgments
    FOR INSERT
    TO authenticated
    WITH CHECK (
        -- User must be the one acknowledging
        acknowledged_by = auth.uid()
        AND
        -- User must be assigned to at least one asset covered by the handoff
        EXISTS (
            SELECT 1 FROM shift_handoffs sh
            JOIN supervisor_assignments sa ON sa.asset_id = ANY(sh.assets_covered)
            WHERE sh.id = handoff_acknowledgments.handoff_id
            AND sa.user_id = auth.uid()
        )
        AND
        -- Handoff must be in pending_acknowledgment status
        EXISTS (
            SELECT 1 FROM shift_handoffs sh
            WHERE sh.id = handoff_acknowledgments.handoff_id
            AND sh.status = 'pending_acknowledgment'
        )
        AND
        -- User must NOT be the creator of the handoff (can't acknowledge own handoff)
        NOT EXISTS (
            SELECT 1 FROM shift_handoffs sh
            WHERE sh.id = handoff_acknowledgments.handoff_id
            AND (sh.created_by = auth.uid() OR sh.user_id = auth.uid())
        )
    );

-- Service role has full access
CREATE POLICY "acknowledgments_service_role"
    ON handoff_acknowledgments
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Note: No UPDATE or DELETE policies - acknowledgments are immutable (NFR24)

-- ============================================================================
-- AUDIT LOGS TABLE (Task 4: AC#2, FR55)
-- ============================================================================

-- Create audit_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS audit_logs (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Action type (e.g., 'handoff_acknowledged')
    action_type VARCHAR(100) NOT NULL,

    -- Related entity
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,

    -- Actor (user who performed the action)
    user_id UUID NOT NULL REFERENCES auth.users(id),

    -- Before/after state (Task 4.3)
    state_before JSONB,
    state_after JSONB,

    -- Additional metadata
    metadata JSONB,

    -- Timestamp (immutable)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index on entity for looking up logs by entity
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
ON audit_logs(entity_type, entity_id);

-- Index on user for looking up user activity
CREATE INDEX IF NOT EXISTS idx_audit_logs_user
ON audit_logs(user_id, created_at DESC);

-- Index on action_type for filtering by action
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type
ON audit_logs(action_type);

-- Index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
ON audit_logs(created_at DESC);

-- ============================================================================
-- AUDIT LOGS RLS (Task 4.4)
-- ============================================================================

-- Enable RLS
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "audit_logs_select" ON audit_logs;
DROP POLICY IF EXISTS "audit_logs_insert" ON audit_logs;
DROP POLICY IF EXISTS "audit_logs_service_role" ON audit_logs;

-- Policy: Users can read logs for entities they have access to
CREATE POLICY "audit_logs_select"
    ON audit_logs
    FOR SELECT
    TO authenticated
    USING (
        -- User is the actor
        user_id = auth.uid()
        OR
        -- For handoff logs, user can read if they have access to the handoff
        (
            entity_type = 'shift_handoff'
            AND EXISTS (
                SELECT 1 FROM shift_handoffs sh
                WHERE sh.id = audit_logs.entity_id
                AND (
                    sh.created_by = auth.uid()
                    OR sh.user_id = auth.uid()
                    OR sh.acknowledged_by = auth.uid()
                    OR EXISTS (
                        SELECT 1 FROM supervisor_assignments sa
                        WHERE sa.user_id = auth.uid()
                        AND sa.asset_id = ANY(sh.assets_covered)
                    )
                )
            )
        )
    );

-- Policy: Authenticated users can insert audit logs for their own actions (Task 4.4: append-only)
-- User must be the actor in the log entry to prevent tampering
CREATE POLICY "audit_logs_insert"
    ON audit_logs
    FOR INSERT
    TO authenticated
    WITH CHECK (
        -- User must be the actor in the log
        user_id = auth.uid()
    );

-- Service role has full access
CREATE POLICY "audit_logs_service_role"
    ON audit_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- No UPDATE or DELETE policies - audit logs are append-only (Task 4.4)

-- ============================================================================
-- UPDATED_AT TRIGGER FOR handoff_acknowledgments
-- ============================================================================

-- Create trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_handoff_acknowledgments_updated_at ON handoff_acknowledgments;
CREATE TRIGGER update_handoff_acknowledgments_updated_at
    BEFORE UPDATE ON handoff_acknowledgments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE handoff_acknowledgments IS
    'Acknowledgment records for shift handoffs (Story 9.7). Tracks when incoming supervisors acknowledge receipt.';

COMMENT ON COLUMN handoff_acknowledgments.id IS
    'Unique identifier (UUID)';

COMMENT ON COLUMN handoff_acknowledgments.handoff_id IS
    'Foreign key to shift_handoffs - the handoff being acknowledged';

COMMENT ON COLUMN handoff_acknowledgments.acknowledged_by IS
    'User ID of incoming supervisor who acknowledged';

COMMENT ON COLUMN handoff_acknowledgments.acknowledged_at IS
    'Timestamp when handoff was acknowledged';

COMMENT ON COLUMN handoff_acknowledgments.notes IS
    'Optional acknowledgment notes (FR29)';

COMMENT ON TABLE audit_logs IS
    'Append-only audit trail for all system actions (FR55). No UPDATE/DELETE allowed.';

COMMENT ON COLUMN audit_logs.action_type IS
    'Action performed (e.g., handoff_acknowledged, handoff_created)';

COMMENT ON COLUMN audit_logs.entity_type IS
    'Type of entity (e.g., shift_handoff)';

COMMENT ON COLUMN audit_logs.entity_id IS
    'ID of the affected entity';

COMMENT ON COLUMN audit_logs.state_before IS
    'Entity state before the action (JSONB)';

COMMENT ON COLUMN audit_logs.state_after IS
    'Entity state after the action (JSONB)';

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check table exists:
--   SELECT table_name FROM information_schema.tables
--   WHERE table_name IN ('handoff_acknowledgments', 'audit_logs');
--
-- Check columns:
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_name = 'handoff_acknowledgments'
--   ORDER BY ordinal_position;
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename = 'handoff_acknowledgments';
--
-- Check RLS policies:
--   SELECT policyname, cmd
--   FROM pg_policies
--   WHERE tablename = 'handoff_acknowledgments';
