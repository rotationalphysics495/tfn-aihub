-- Audit Logs Enhancements (Story 9.15)
--
-- Adds append-only protections and additional features to audit_logs table
-- created in 0019_user_roles_default_trigger.sql
--
-- AC#3: Entries are tamper-evident (append-only), 90-day retention
--
-- References:
-- - [Source: prd/prd-functional-requirements.md#FR50, FR55, FR56]
-- - [Source: prd/prd-non-functional-requirements.md#NFR25]

-- ============================================================================
-- Add missing columns if needed
-- ============================================================================

-- Add target_type column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'audit_logs' AND column_name = 'target_type'
    ) THEN
        ALTER TABLE audit_logs ADD COLUMN target_type TEXT;
    END IF;
END $$;

-- Add target_id column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'audit_logs' AND column_name = 'target_id'
    ) THEN
        ALTER TABLE audit_logs ADD COLUMN target_id UUID;
    END IF;
END $$;

-- Add created_at column if not exists (for retention tracking)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'audit_logs' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE audit_logs ADD COLUMN created_at TIMESTAMPTZ DEFAULT now() NOT NULL;
    END IF;
END $$;

-- ============================================================================
-- Add indexes for efficient queries (if not exist)
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

-- Composite index for filtered queries by timestamp and action_type
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp_action ON audit_logs(timestamp DESC, action_type);

-- ============================================================================
-- Create append-only triggers (tamper-evident)
-- ============================================================================

-- Create function to block UPDATE/DELETE
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are append-only. UPDATE and DELETE operations are not allowed.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Drop triggers if they exist before creating
DROP TRIGGER IF EXISTS audit_logs_prevent_update ON audit_logs;
DROP TRIGGER IF EXISTS audit_logs_prevent_delete ON audit_logs;

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
