-- Migration: Create Action Plans tables
-- Story: 16.1 - Action Plans Data Model
-- Date: 2026-02-12
--
-- This migration creates the Action Plans tables:
--   - action_plans: Tracks corrective/preventive actions from investigation to completion
--   - action_plan_updates: Append-only audit trail of progress updates on action plans
--
-- All tables include:
--   - UUID primary keys (auto-generated via gen_random_uuid())
--   - Row Level Security (RLS) policies
--   - Performance indexes
--   - Idempotent CREATE TABLE IF NOT EXISTS / DROP IF EXISTS patterns

-- ============================================================================
-- TABLE: action_plans
-- ============================================================================
-- Tracks corrective, preventive, and improvement actions linked to assets
-- and follow-up items. Supports full lifecycle: draft -> open -> in_progress
-- -> completed -> verified.

CREATE TABLE IF NOT EXISTS action_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,
    category TEXT CHECK (category IN ('corrective', 'preventive', 'improvement')),
    root_cause TEXT,
    corrective_action TEXT,
    preventive_action TEXT,
    source_followup_id UUID REFERENCES action_followups(id) ON DELETE SET NULL,
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'open', 'in_progress', 'completed', 'verified')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    due_date DATE,
    completed_at TIMESTAMPTZ,
    verified_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments for documentation
COMMENT ON TABLE action_plans IS 'Corrective/preventive/improvement action plans linked to assets and follow-up items';
COMMENT ON COLUMN action_plans.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN action_plans.title IS 'Short description of the action plan (e.g., "Replace worn bearing on Grinder 5")';
COMMENT ON COLUMN action_plans.description IS 'Full context and root cause analysis';
COMMENT ON COLUMN action_plans.asset_id IS 'FK to assets(id), nullable for plant-wide plans with no specific asset';
COMMENT ON COLUMN action_plans.category IS 'Plan type: corrective, preventive, or improvement';
COMMENT ON COLUMN action_plans.root_cause IS 'Root cause analysis text';
COMMENT ON COLUMN action_plans.corrective_action IS 'Description of the corrective action to take';
COMMENT ON COLUMN action_plans.preventive_action IS 'What changes to prevent recurrence';
COMMENT ON COLUMN action_plans.source_followup_id IS 'FK to action_followups(id), nullable — links plan back to originating follow-up item';
COMMENT ON COLUMN action_plans.owner_id IS 'FK to auth.users(id), the user responsible for this plan';
COMMENT ON COLUMN action_plans.status IS 'Lifecycle state: draft, open, in_progress, completed, verified';
COMMENT ON COLUMN action_plans.priority IS 'Priority level: low, medium, high, critical';
COMMENT ON COLUMN action_plans.due_date IS 'Target completion date (DATE, daily granularity)';
COMMENT ON COLUMN action_plans.completed_at IS 'Timestamp when the plan was marked completed';
COMMENT ON COLUMN action_plans.verified_by IS 'FK to auth.users(id), the user who verified completion';
COMMENT ON COLUMN action_plans.verified_at IS 'Timestamp when the plan was verified';

-- ============================================================================
-- TABLE: action_plan_updates
-- ============================================================================
-- Append-only audit trail of progress updates on action plans.
-- No updated_at column — this is an insert-only log table.

CREATE TABLE IF NOT EXISTS action_plan_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_plan_id UUID NOT NULL REFERENCES action_plans(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    update_text TEXT NOT NULL,
    status_change TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments for documentation
COMMENT ON TABLE action_plan_updates IS 'Append-only audit trail of progress updates on action plans (NFR-I3 compliance)';
COMMENT ON COLUMN action_plan_updates.action_plan_id IS 'FK to action_plans(id), CASCADE DELETE removes updates when plan is deleted';
COMMENT ON COLUMN action_plan_updates.author_id IS 'FK to auth.users(id), the user who created this update';
COMMENT ON COLUMN action_plan_updates.update_text IS 'Progress update text content';
COMMENT ON COLUMN action_plan_updates.status_change IS 'Optional status transition description (e.g., "open -> in_progress")';

-- ============================================================================
-- INDEXES: Performance indexes for common query patterns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_action_plans_asset_id ON action_plans(asset_id);
CREATE INDEX IF NOT EXISTS idx_action_plans_status ON action_plans(status);
CREATE INDEX IF NOT EXISTS idx_action_plans_owner_id ON action_plans(owner_id);
CREATE INDEX IF NOT EXISTS idx_action_plans_source_followup_id ON action_plans(source_followup_id);
CREATE INDEX IF NOT EXISTS idx_action_plan_updates_action_plan_id ON action_plan_updates(action_plan_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE action_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_plan_updates ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES: action_plans
-- ============================================================================

-- All authenticated users can read all plans (shared visibility)
DROP POLICY IF EXISTS "Allow authenticated read access on action_plans" ON action_plans;
CREATE POLICY "Allow authenticated read access on action_plans"
    ON action_plans FOR SELECT
    TO authenticated
    USING (true);

-- Owners can insert their own plans
DROP POLICY IF EXISTS "Owners can insert action_plans" ON action_plans;
CREATE POLICY "Owners can insert action_plans"
    ON action_plans FOR INSERT
    TO authenticated
    WITH CHECK (owner_id = auth.uid());

-- Owners can update their own plans
DROP POLICY IF EXISTS "Owners can update action_plans" ON action_plans;
CREATE POLICY "Owners can update action_plans"
    ON action_plans FOR UPDATE
    TO authenticated
    USING (owner_id = auth.uid())
    WITH CHECK (owner_id = auth.uid());

-- Service role has full access
DROP POLICY IF EXISTS "Service role full access on action_plans" ON action_plans;
CREATE POLICY "Service role full access on action_plans"
    ON action_plans FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RLS POLICIES: action_plan_updates
-- ============================================================================

-- All authenticated users can read all updates (timeline visibility)
DROP POLICY IF EXISTS "Allow authenticated read access on action_plan_updates" ON action_plan_updates;
CREATE POLICY "Allow authenticated read access on action_plan_updates"
    ON action_plan_updates FOR SELECT
    TO authenticated
    USING (true);

-- Authenticated users can insert updates with their own author_id
DROP POLICY IF EXISTS "Authors can insert action_plan_updates" ON action_plan_updates;
CREATE POLICY "Authors can insert action_plan_updates"
    ON action_plan_updates FOR INSERT
    TO authenticated
    WITH CHECK (author_id = auth.uid());

-- Service role has full access
DROP POLICY IF EXISTS "Service role full access on action_plan_updates" ON action_plan_updates;
CREATE POLICY "Service role full access on action_plan_updates"
    ON action_plan_updates FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- TRIGGER: Auto-update updated_at on action_plans
-- ============================================================================
-- Reuses the existing update_updated_at_column() function from migration 0002.
-- No trigger on action_plan_updates (append-only table).

DROP TRIGGER IF EXISTS update_action_plans_updated_at ON action_plans;
CREATE TRIGGER update_action_plans_updated_at
    BEFORE UPDATE ON action_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check action_plans table columns:
--   SELECT column_name, data_type, is_nullable, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'action_plans'
--   ORDER BY ordinal_position;
--
-- Check action_plan_updates table columns:
--   SELECT column_name, data_type, is_nullable, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'action_plan_updates'
--   ORDER BY ordinal_position;
--
-- Check foreign keys on action_plans:
--   SELECT tc.constraint_name, kcu.column_name,
--          ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
--   FROM information_schema.table_constraints tc
--   JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
--   JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
--   WHERE tc.table_name = 'action_plans' AND tc.constraint_type = 'FOREIGN KEY';
--
-- Check indexes:
--   SELECT indexname, indexdef
--   FROM pg_indexes
--   WHERE tablename IN ('action_plans', 'action_plan_updates');
--
-- Check RLS is enabled:
--   SELECT tablename, rowsecurity
--   FROM pg_tables
--   WHERE tablename IN ('action_plans', 'action_plan_updates');
--
-- Check RLS policies:
--   SELECT policyname, cmd, qual
--   FROM pg_policies
--   WHERE tablename IN ('action_plans', 'action_plan_updates');
--
-- Check triggers:
--   SELECT tgname
--   FROM pg_trigger
--   WHERE tgrelid IN ('action_plans'::regclass);
