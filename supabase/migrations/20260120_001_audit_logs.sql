-- Audit Logs Migration (Story 9.15, Task 1)
--
-- Creates the audit_logs table for admin action tracking.
-- Implements append-only design for tamper-evidence (NFR25).
--
-- AC#1: Log entries with timestamp, admin_user_id, action_type, target, before/after values
-- AC#3: Entries are tamper-evident (append-only), 90-day retention
-- AC#4: batch_id links bulk operations
--
-- References:
-- - [Source: prd/prd-functional-requirements.md#FR50, FR55, FR56]
-- - [Source: prd/prd-non-functional-requirements.md#NFR25]

-- ============================================================================
-- Task 1.2: Create audit_logs table
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task 1.2: Timestamp and admin user
    timestamp TIMESTAMPTZ DEFAULT now() NOT NULL,
    admin_user_id UUID REFERENCES auth.users(id) NOT NULL,

    -- Task 1.2: Action type and target columns
    action_type TEXT NOT NULL,
    target_type TEXT,                              -- 'user', 'assignment', 'role', etc.
    target_id UUID,                                -- Generic target reference
    target_user_id UUID REFERENCES auth.users(id),
    target_asset_id UUID,                          -- References assets(id) but no FK to avoid issues

    -- Task 1.3: JSONB columns for before/after values
    before_value JSONB,
    after_value JSONB,

    -- Task 1.4: batch_id for linking bulk operations
    batch_id UUID,

    -- Additional context
    metadata JSONB,

    -- Task 1.9: Retention tracking
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Add comment for retention policy (Task 1.9)
COMMENT ON TABLE audit_logs IS 'Audit trail for admin actions. Append-only, 90-day minimum retention per NFR25.';
COMMENT ON COLUMN audit_logs.batch_id IS 'Links related entries from batch operations (AC#4).';
COMMENT ON COLUMN audit_logs.before_value IS 'State before the change for updates/deletes.';
COMMENT ON COLUMN audit_logs.after_value IS 'State after the change for creates/updates.';

-- ============================================================================
-- Task 1.5: Create indexes for efficient queries
-- ============================================================================

-- Index on timestamp (for reverse chronological order queries)
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);

-- Index on admin_user_id (for filtering by admin who performed action)
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_user_id ON audit_logs(admin_user_id);

-- Index on action_type (for filtering by action type)
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);

-- Index on target_user_id (for filtering by affected user)
CREATE INDEX IF NOT EXISTS idx_audit_logs_target_user_id ON audit_logs(target_user_id);

-- Index on batch_id (for grouping batch operations)
CREATE INDEX IF NOT EXISTS idx_audit_logs_batch_id ON audit_logs(batch_id);

-- Task 1.6: Composite index for filtered queries by timestamp and action_type
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp_action ON audit_logs(timestamp DESC, action_type);

-- ============================================================================
-- Task 1.7: Create append-only RLS policy
-- ============================================================================

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Admin read-only policy (SELECT for admin users)
CREATE POLICY "Admins can read audit logs"
    ON audit_logs FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_roles.user_id = auth.uid()
            AND user_roles.role = 'admin'
        )
    );

-- Service role can INSERT (for backend audit logging)
-- No explicit INSERT policy needed as service role bypasses RLS
-- This is intentional - only the backend should write to audit logs

-- ============================================================================
-- Task 1.8: Add trigger to prevent UPDATE and DELETE operations
-- ============================================================================

-- Create function to block UPDATE/DELETE
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are append-only. UPDATE and DELETE operations are not allowed.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to block UPDATE operations
CREATE TRIGGER audit_logs_prevent_update
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_log_modification();

-- Trigger to block DELETE operations
CREATE TRIGGER audit_logs_prevent_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_log_modification();

-- ============================================================================
-- Grant permissions
-- ============================================================================

-- Allow authenticated users to read (RLS will filter based on role)
GRANT SELECT ON audit_logs TO authenticated;

-- Service role has full access for backend operations
GRANT ALL ON audit_logs TO service_role;
