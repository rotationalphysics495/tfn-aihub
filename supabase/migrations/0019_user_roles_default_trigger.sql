-- Migration: Add default Supervisor role trigger and audit_logs table for role changes
-- Story: 9.14 - Admin UI - Role Management
-- Date: 2026-01-19
--
-- This migration:
--   - Adds trigger for default Supervisor role on new user (AC#4)
--   - Creates audit_logs table for role changes (FR56) distinct from admin_audit_logs
--   - Adds RLS policies for role management
--
-- References:
-- - [Source: architecture/voice-briefing.md#Role-Based-Access-Control]
-- - [Source: prd/prd-functional-requirements.md#FR47, FR56]

-- ============================================================================
-- FUNCTION: Assign default Supervisor role on new user signup
-- ============================================================================
-- AC#4: When a new user is created via Supabase Auth, default role is "Supervisor"

CREATE OR REPLACE FUNCTION assign_default_user_role()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert default Supervisor role for new users
    INSERT INTO user_roles (user_id, role)
    VALUES (NEW.id, 'supervisor')
    ON CONFLICT (user_id) DO NOTHING;  -- Don't overwrite if role already exists

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION assign_default_user_role() IS
    'Assigns default Supervisor role when a new user signs up (Story 9.14 AC#4)';

-- ============================================================================
-- TRIGGER: Auto-assign default role on auth.users insert
-- ============================================================================

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS on_auth_user_created_assign_role ON auth.users;

-- Create trigger to assign default role on user creation
CREATE TRIGGER on_auth_user_created_assign_role
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION assign_default_user_role();

-- ============================================================================
-- TABLE: audit_logs (FR56)
-- ============================================================================
-- General audit logs for role changes and other security-sensitive operations.
-- This is separate from admin_audit_logs which is specific to assignment operations.

-- Drop and recreate to ensure correct schema
DROP TABLE IF EXISTS audit_logs CASCADE;

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    admin_user_id UUID NOT NULL REFERENCES auth.users(id),
    action_type TEXT NOT NULL,  -- 'role_change', 'assignment_change', etc.
    target_user_id UUID REFERENCES auth.users(id),
    target_asset_id UUID REFERENCES assets(id),
    before_value JSONB,
    after_value JSONB,
    batch_id UUID,  -- For linking bulk operations
    metadata JSONB
);

-- Add comments
COMMENT ON TABLE audit_logs IS 'Audit trail for role changes and security-sensitive operations (FR56)';

-- Indexes for efficient querying (NFR25: 90-day retention means we need fast queries)
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_user_id ON audit_logs(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target_user_id ON audit_logs(target_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_batch_id ON audit_logs(batch_id) WHERE batch_id IS NOT NULL;

-- ============================================================================
-- ROW LEVEL SECURITY: audit_logs
-- ============================================================================
-- Append-only: no UPDATE/DELETE allowed (NFR25 compliance)

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow service_role full access on audit_logs" ON audit_logs;
DROP POLICY IF EXISTS "Allow admin read access on audit_logs" ON audit_logs;
DROP POLICY IF EXISTS "Allow admin insert on audit_logs" ON audit_logs;

-- Service role has full access (for API operations)
CREATE POLICY "Allow service_role full access on audit_logs"
    ON audit_logs FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Admins can read audit logs (read-only for integrity)
CREATE POLICY "Allow admin read access on audit_logs"
    ON audit_logs FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_roles.user_id = auth.uid()
            AND user_roles.role = 'admin'
        )
    );

-- Admins can insert audit logs (through service role typically, but allow direct)
CREATE POLICY "Allow admin insert on audit_logs"
    ON audit_logs FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_roles.user_id = auth.uid()
            AND user_roles.role = 'admin'
        )
    );

-- ============================================================================
-- ENHANCED RLS POLICIES: user_roles for admin management
-- ============================================================================

-- Drop existing admin policy if it exists
DROP POLICY IF EXISTS "Allow admin manage all roles" ON user_roles;
DROP POLICY IF EXISTS "Allow admin read all roles" ON user_roles;

-- Admins can read all user roles (for user management UI)
CREATE POLICY "Allow admin read all roles"
    ON user_roles FOR SELECT
    TO authenticated
    USING (
        user_id = auth.uid()  -- Users can always read their own role
        OR EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role = 'admin'
        )
    );

-- Admins can manage (insert/update) user roles
CREATE POLICY "Allow admin manage all roles"
    ON user_roles FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role = 'admin'
        )
    );

-- ============================================================================
-- FUNCTION: Prevent removing last admin (AC#3)
-- ============================================================================

CREATE OR REPLACE FUNCTION prevent_last_admin_removal()
RETURNS TRIGGER AS $$
DECLARE
    admin_count INTEGER;
BEGIN
    -- Only check when changing away from admin role or deleting an admin
    IF (TG_OP = 'UPDATE' AND OLD.role = 'admin' AND NEW.role != 'admin') OR
       (TG_OP = 'DELETE' AND OLD.role = 'admin') THEN

        -- Count remaining admins (excluding the one being changed/deleted)
        SELECT COUNT(*) INTO admin_count
        FROM user_roles
        WHERE role = 'admin'
        AND user_id != OLD.user_id;

        IF admin_count = 0 THEN
            RAISE EXCEPTION 'Cannot remove last admin';
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION prevent_last_admin_removal() IS
    'Prevents removing the last admin user (Story 9.14 AC#3)';

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS check_last_admin_before_change ON user_roles;

-- Create trigger to prevent last admin removal
CREATE TRIGGER check_last_admin_before_change
    BEFORE UPDATE OR DELETE ON user_roles
    FOR EACH ROW
    EXECUTE FUNCTION prevent_last_admin_removal();

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- Check trigger exists:
--   SELECT trigger_name, event_manipulation, action_statement
--   FROM information_schema.triggers
--   WHERE trigger_name = 'on_auth_user_created_assign_role';
--
-- Check audit_logs table exists:
--   SELECT table_name FROM information_schema.tables
--   WHERE table_name = 'audit_logs';
--
-- Check RLS policies:
--   SELECT schemaname, tablename, policyname
--   FROM pg_policies
--   WHERE tablename IN ('user_roles', 'audit_logs');
--
-- Test last admin protection:
--   -- This should fail if there's only one admin
--   UPDATE user_roles SET role = 'supervisor' WHERE role = 'admin';
