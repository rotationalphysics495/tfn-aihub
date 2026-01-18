-- Migration: Add expires_at column and admin RLS policies for supervisor_assignments
-- Story: 9.13 - Admin UI - Asset Assignment
-- Date: 2026-01-19
--
-- This migration adds temporary assignment support (FR49) and admin management:
--   - expires_at column for temporary assignments
--   - Admin-only RLS policies for modification
--   - Admin audit logging table for assignment changes (FR50, FR56)
--
-- References:
-- - [Source: architecture/voice-briefing.md#Admin UI Architecture]
-- - [Source: prd/prd-functional-requirements.md#FR46-FR50]

-- ============================================================================
-- ADD expires_at COLUMN FOR TEMPORARY ASSIGNMENTS (FR49)
-- ============================================================================

-- Add expires_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'supervisor_assignments'
        AND column_name = 'expires_at'
    ) THEN
        ALTER TABLE supervisor_assignments
        ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE NULL;

        COMMENT ON COLUMN supervisor_assignments.expires_at IS
            'Optional expiration date for temporary assignments (FR49). NULL = permanent assignment.';
    END IF;
END $$;

-- Index for efficient filtering of expired assignments
CREATE INDEX IF NOT EXISTS idx_supervisor_assignments_expires_at
    ON supervisor_assignments(expires_at)
    WHERE expires_at IS NOT NULL;

-- ============================================================================
-- TABLE: admin_audit_logs
-- ============================================================================
-- Stores audit logs for all admin configuration changes (FR50, FR56).
-- This table is append-only for immutability.

CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(50) NOT NULL,  -- 'assignment_created', 'assignment_deleted', 'assignment_updated', 'batch_update'
    entity_type VARCHAR(50) NOT NULL,  -- 'supervisor_assignment', 'user_role'
    entity_id UUID,                    -- ID of the affected entity (nullable for batch operations)
    admin_user_id UUID NOT NULL REFERENCES auth.users(id),
    target_user_id UUID REFERENCES auth.users(id),  -- User affected by the change
    state_before JSONB,                -- State before the change
    state_after JSONB,                 -- State after the change
    batch_id UUID,                     -- Groups batch operations together
    metadata JSONB,                    -- Additional context (IP, user agent, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments
COMMENT ON TABLE admin_audit_logs IS 'Audit trail for admin configuration changes (FR50, FR56)';
COMMENT ON COLUMN admin_audit_logs.action_type IS 'Type of action: assignment_created, assignment_deleted, assignment_updated, batch_update';
COMMENT ON COLUMN admin_audit_logs.entity_type IS 'Type of entity affected: supervisor_assignment, user_role';
COMMENT ON COLUMN admin_audit_logs.entity_id IS 'ID of the affected entity (nullable for batch operations)';
COMMENT ON COLUMN admin_audit_logs.admin_user_id IS 'Admin who performed the action';
COMMENT ON COLUMN admin_audit_logs.target_user_id IS 'User affected by the change (supervisor being assigned)';
COMMENT ON COLUMN admin_audit_logs.state_before IS 'JSON snapshot of state before change';
COMMENT ON COLUMN admin_audit_logs.state_after IS 'JSON snapshot of state after change';
COMMENT ON COLUMN admin_audit_logs.batch_id IS 'Groups batch operations for atomic changes';

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin_user_id ON admin_audit_logs(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_target_user_id ON admin_audit_logs(target_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_entity_type ON admin_audit_logs(entity_type);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_action_type ON admin_audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_batch_id ON admin_audit_logs(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON admin_audit_logs(created_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY: admin_audit_logs
-- ============================================================================

-- Enable RLS
ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow service_role full access on admin_audit_logs" ON admin_audit_logs;
DROP POLICY IF EXISTS "Allow admin read access on admin_audit_logs" ON admin_audit_logs;

-- Service role has full access (for API operations)
CREATE POLICY "Allow service_role full access on admin_audit_logs"
    ON admin_audit_logs FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Admins can read audit logs (read-only for integrity)
CREATE POLICY "Allow admin read access on admin_audit_logs"
    ON admin_audit_logs FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_roles.user_id = auth.uid()
            AND user_roles.role = 'admin'
        )
    );

-- ============================================================================
-- ENHANCED RLS POLICIES: supervisor_assignments
-- ============================================================================
-- Add admin-level policies for managing assignments (FR46)

-- Drop existing admin policy if it exists
DROP POLICY IF EXISTS "Allow admin manage all assignments" ON supervisor_assignments;

-- Admins can manage all supervisor assignments
CREATE POLICY "Allow admin manage all assignments"
    ON supervisor_assignments FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_roles.user_id = auth.uid()
            AND user_roles.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_roles.user_id = auth.uid()
            AND user_roles.role = 'admin'
        )
    );

-- ============================================================================
-- HELPER FUNCTION: Check if assignment is expired
-- ============================================================================

CREATE OR REPLACE FUNCTION is_assignment_expired(expires_at TIMESTAMP WITH TIME ZONE)
RETURNS BOOLEAN AS $$
BEGIN
    IF expires_at IS NULL THEN
        RETURN FALSE;  -- Permanent assignment, never expires
    END IF;
    RETURN expires_at < NOW();
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION is_assignment_expired IS 'Check if a supervisor assignment has expired (FR49)';

-- ============================================================================
-- VIEW: active_supervisor_assignments
-- ============================================================================
-- View that excludes expired assignments for easier querying

CREATE OR REPLACE VIEW active_supervisor_assignments AS
SELECT *
FROM supervisor_assignments
WHERE expires_at IS NULL OR expires_at > NOW();

COMMENT ON VIEW active_supervisor_assignments IS 'Supervisor assignments excluding expired ones (FR49)';

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- Check expires_at column exists:
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_name = 'supervisor_assignments' AND column_name = 'expires_at';
--
-- Check admin_audit_logs table exists:
--   SELECT table_name FROM information_schema.tables
--   WHERE table_name = 'admin_audit_logs';
--
-- Check RLS policies:
--   SELECT schemaname, tablename, policyname
--   FROM pg_policies
--   WHERE tablename IN ('supervisor_assignments', 'admin_audit_logs');
