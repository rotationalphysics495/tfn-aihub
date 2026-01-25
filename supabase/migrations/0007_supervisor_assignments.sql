-- Migration: Create Supervisor Assignments and User Roles tables
-- Story: 8.5 - Supervisor Scoped Briefings
-- Date: 2026-01-15
--
-- This migration creates tables for role-based access control:
--   - user_roles: Maps users to their roles (plant_manager, supervisor, admin)
--   - supervisor_assignments: Maps supervisors to their assigned assets
--   - user_preferences: Stores user preferences for briefings
--
-- All tables include:
--   - UUID primary keys (auto-generated)
--   - created_at/updated_at timestamps
--   - Row Level Security (RLS) policies
--   - Performance indexes
--
-- References:
-- - [Source: architecture/voice-briefing.md#Role-Based Access Control]
-- - [Source: prd/prd-functional-requirements.md#FR15]

-- ============================================================================
-- TABLE: user_roles
-- ============================================================================
-- Maps users to their organizational roles.

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('plant_manager', 'supervisor', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE user_roles IS 'Maps users to their organizational roles (plant_manager, supervisor, admin)';
COMMENT ON COLUMN user_roles.user_id IS 'References auth.users(id)';
COMMENT ON COLUMN user_roles.role IS 'User role: plant_manager | supervisor | admin';

-- Index on role for filtering
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role);

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_user_roles_updated_at ON user_roles;
CREATE TRIGGER update_user_roles_updated_at
    BEFORE UPDATE ON user_roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: supervisor_assignments
-- ============================================================================
-- Maps supervisors to the assets they are responsible for.
-- Used to scope briefings to only show relevant assets (FR15).

CREATE TABLE IF NOT EXISTS supervisor_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, asset_id)
);

-- Add comments for documentation
COMMENT ON TABLE supervisor_assignments IS 'Maps supervisors to their assigned assets for scoped briefings';
COMMENT ON COLUMN supervisor_assignments.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN supervisor_assignments.user_id IS 'Supervisor user ID (references auth.users)';
COMMENT ON COLUMN supervisor_assignments.asset_id IS 'Assigned asset ID (references assets)';
COMMENT ON COLUMN supervisor_assignments.assigned_by IS 'Admin who made the assignment';
COMMENT ON COLUMN supervisor_assignments.assigned_at IS 'When the assignment was made';

-- Index on user_id for quick lookups when generating briefings
CREATE INDEX IF NOT EXISTS idx_supervisor_assignments_user_id ON supervisor_assignments(user_id);

-- Index on asset_id for reverse lookups
CREATE INDEX IF NOT EXISTS idx_supervisor_assignments_asset_id ON supervisor_assignments(asset_id);

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_supervisor_assignments_updated_at ON supervisor_assignments;
CREATE TRIGGER update_supervisor_assignments_updated_at
    BEFORE UPDATE ON supervisor_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE: user_preferences
-- ============================================================================
-- Stores user preferences for briefings (FR37, FR39).

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT, -- Denormalized for quick access
    area_order TEXT[], -- ['Grinding', 'Packing', ...] - preferred area order (FR39)
    detail_level TEXT CHECK (detail_level IN ('summary', 'detailed')) DEFAULT 'detailed', -- FR37
    voice_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE user_preferences IS 'User preferences for briefing delivery';
COMMENT ON COLUMN user_preferences.user_id IS 'References auth.users(id)';
COMMENT ON COLUMN user_preferences.role IS 'Denormalized role for quick access';
COMMENT ON COLUMN user_preferences.area_order IS 'Preferred order of areas in briefings (FR39)';
COMMENT ON COLUMN user_preferences.detail_level IS 'Preferred detail level: summary or detailed (FR37)';
COMMENT ON COLUMN user_preferences.voice_enabled IS 'Whether voice briefings are enabled';

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE supervisor_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES: user_roles
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read own role" ON user_roles;
DROP POLICY IF EXISTS "Allow admin read all roles" ON user_roles;
DROP POLICY IF EXISTS "Allow service_role full access on user_roles" ON user_roles;

-- Users can read their own role
CREATE POLICY "Allow authenticated read own role"
    ON user_roles FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Service role has full access
CREATE POLICY "Allow service_role full access on user_roles"
    ON user_roles FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: supervisor_assignments
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read own assignments" ON supervisor_assignments;
DROP POLICY IF EXISTS "Allow service_role full access on supervisor_assignments" ON supervisor_assignments;

-- Users can read their own assignments
CREATE POLICY "Allow authenticated read own assignments"
    ON supervisor_assignments FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Service role has full access (admin operations)
CREATE POLICY "Allow service_role full access on supervisor_assignments"
    ON supervisor_assignments FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: user_preferences
-- ============================================================================

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Allow authenticated read own preferences" ON user_preferences;
DROP POLICY IF EXISTS "Allow authenticated update own preferences" ON user_preferences;
DROP POLICY IF EXISTS "Allow authenticated insert own preferences" ON user_preferences;
DROP POLICY IF EXISTS "Allow service_role full access on user_preferences" ON user_preferences;

-- Users can read their own preferences
CREATE POLICY "Allow authenticated read own preferences"
    ON user_preferences FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Users can update their own preferences
CREATE POLICY "Allow authenticated update own preferences"
    ON user_preferences FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Users can insert their own preferences
CREATE POLICY "Allow authenticated insert own preferences"
    ON user_preferences FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

-- Service role has full access
CREATE POLICY "Allow service_role full access on user_preferences"
    ON user_preferences FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check tables exist:
--   SELECT table_name FROM information_schema.tables
--   WHERE table_name IN ('user_roles', 'supervisor_assignments', 'user_preferences');
--
-- Check constraints:
--   SELECT constraint_name, table_name
--   FROM information_schema.table_constraints
--   WHERE table_name IN ('user_roles', 'supervisor_assignments', 'user_preferences');
--
-- Check indexes:
--   SELECT indexname FROM pg_indexes
--   WHERE tablename IN ('user_roles', 'supervisor_assignments', 'user_preferences');
