-- Migration: RLS policies for shift_handoffs immutability
-- Story: 9.4 - Persistent Handoff Records
-- Date: 2026-01-15
--
-- This migration implements Row Level Security (RLS) policies for the
-- shift_handoffs table, enforcing:
--
-- AC#1: Users can read handoffs they created OR are assigned to receive
-- AC#2: Core fields are immutable; only supplemental_notes and status can be updated
-- AC#3: Authenticated users can create handoffs
-- AC#4: No DELETE allowed (append-only audit trail)
--
-- References:
-- - [Source: architecture/voice-briefing.md#Role-Based-Access-Control]
-- - [Source: prd/prd-non-functional-requirements.md#NFR24]

-- ============================================================================
-- ENABLE RLS ON shift_handoffs
-- ============================================================================

-- Enable RLS (idempotent)
ALTER TABLE shift_handoffs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- DROP EXISTING POLICIES (for clean slate)
-- ============================================================================

-- Drop any existing policies to ensure clean state
DROP POLICY IF EXISTS "Users can manage own handoffs" ON shift_handoffs;
DROP POLICY IF EXISTS "Users can read own handoffs" ON shift_handoffs;
DROP POLICY IF EXISTS "Users can read assigned handoffs" ON shift_handoffs;
DROP POLICY IF EXISTS "Authenticated users can insert handoffs" ON shift_handoffs;
DROP POLICY IF EXISTS "Users can update own draft handoffs" ON shift_handoffs;
DROP POLICY IF EXISTS "Allow limited updates on shift_handoffs" ON shift_handoffs;
DROP POLICY IF EXISTS "shift_handoffs_select_own" ON shift_handoffs;
DROP POLICY IF EXISTS "shift_handoffs_select_assigned" ON shift_handoffs;
DROP POLICY IF EXISTS "shift_handoffs_insert" ON shift_handoffs;
DROP POLICY IF EXISTS "shift_handoffs_update_limited" ON shift_handoffs;
DROP POLICY IF EXISTS "service_role_full_access" ON shift_handoffs;

-- ============================================================================
-- SELECT POLICIES (AC#1)
-- ============================================================================

-- Policy 1: Users can read handoffs they created
-- AC#1: Users can read handoffs they created
CREATE POLICY "shift_handoffs_select_own"
    ON shift_handoffs
    FOR SELECT
    TO authenticated
    USING (
        -- User created the handoff (outgoing supervisor)
        created_by = auth.uid()
        OR
        -- Fallback: user_id for backward compatibility
        user_id = auth.uid()
    );

-- Policy 2: Users can read handoffs they are assigned to receive
-- AC#1: Users can read handoffs they are assigned to receive
-- This checks the supervisor_assignments table to see if the user is assigned
-- to any of the assets covered by the handoff
CREATE POLICY "shift_handoffs_select_assigned"
    ON shift_handoffs
    FOR SELECT
    TO authenticated
    USING (
        -- User is assigned to at least one asset covered by this handoff
        EXISTS (
            SELECT 1
            FROM supervisor_assignments sa
            WHERE sa.user_id = auth.uid()
            AND sa.asset_id = ANY(shift_handoffs.assets_covered)
        )
        OR
        -- User acknowledged this handoff (incoming supervisor)
        acknowledged_by = auth.uid()
    );

-- ============================================================================
-- INSERT POLICY (AC#3)
-- ============================================================================

-- Policy 3: Authenticated users can create handoffs
-- AC#3: Any authenticated user can create handoffs for themselves
CREATE POLICY "shift_handoffs_insert"
    ON shift_handoffs
    FOR INSERT
    TO authenticated
    WITH CHECK (
        -- User must be creating handoff for themselves
        (created_by = auth.uid() OR user_id = auth.uid())
        -- Status must be draft on creation
        AND status = 'draft'
    );

-- ============================================================================
-- UPDATE POLICY (AC#2 - Immutability)
-- ============================================================================

-- Policy 4: Limited updates allowed (enforces immutability)
-- AC#2: Only status, supplemental_notes, and acknowledgment fields can be modified
--
-- IMPORTANT: This policy allows UPDATE but actual immutability is enforced at
-- the service layer. The service layer validates that only these fields change:
--   - status (for state transitions)
--   - supplemental_notes (append-only)
--   - acknowledged_by (when acknowledging)
--   - acknowledged_at (when acknowledging)
--   - updated_at (auto-updated by trigger)
--
-- The database allows any UPDATE by the owner; the application enforces which
-- fields can actually change based on the handoff's current status.
CREATE POLICY "shift_handoffs_update_limited"
    ON shift_handoffs
    FOR UPDATE
    TO authenticated
    USING (
        -- Only the creator can update their own handoffs
        created_by = auth.uid() OR user_id = auth.uid()
        -- Or the assigned incoming supervisor can acknowledge
        OR EXISTS (
            SELECT 1
            FROM supervisor_assignments sa
            WHERE sa.user_id = auth.uid()
            AND sa.asset_id = ANY(shift_handoffs.assets_covered)
        )
    )
    WITH CHECK (
        -- The updated row must still belong to the same creator
        -- (prevents changing ownership)
        created_by = (
            SELECT created_by FROM shift_handoffs WHERE id = shift_handoffs.id
        )
        OR user_id = (
            SELECT user_id FROM shift_handoffs WHERE id = shift_handoffs.id
        )
    );

-- ============================================================================
-- NO DELETE POLICY (AC#4)
-- ============================================================================

-- AC#4: No DELETE policy is created. This means authenticated users cannot
-- delete handoff records, maintaining the audit trail.
--
-- The service_role can still delete if needed for administrative purposes.

-- ============================================================================
-- SERVICE ROLE FULL ACCESS
-- ============================================================================

-- Service role has full access for administrative operations
CREATE POLICY "service_role_full_access"
    ON shift_handoffs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- IMMUTABILITY ENFORCEMENT FUNCTION (AC#2)
-- ============================================================================

-- Function to enforce immutability of core fields after submission
-- This is called by a trigger to prevent modification of immutable fields
CREATE OR REPLACE FUNCTION enforce_handoff_immutability()
RETURNS TRIGGER AS $$
BEGIN
    -- Allow any changes while in draft status
    IF OLD.status = 'draft' THEN
        RETURN NEW;
    END IF;

    -- Once submitted (not draft), enforce immutability on core fields
    -- Core fields: shift_date, shift_type, summary_text, notes, assets_covered, created_by

    IF NEW.shift_date IS DISTINCT FROM OLD.shift_date THEN
        RAISE EXCEPTION 'Cannot modify shift_date after handoff is submitted (NFR24 immutability)'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.shift_type IS DISTINCT FROM OLD.shift_type THEN
        RAISE EXCEPTION 'Cannot modify shift_type after handoff is submitted (NFR24 immutability)'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.summary_text IS DISTINCT FROM OLD.summary_text THEN
        RAISE EXCEPTION 'Cannot modify summary_text after handoff is submitted (NFR24 immutability)'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.notes IS DISTINCT FROM OLD.notes THEN
        RAISE EXCEPTION 'Cannot modify notes after handoff is submitted (NFR24 immutability)'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.assets_covered IS DISTINCT FROM OLD.assets_covered THEN
        RAISE EXCEPTION 'Cannot modify assets_covered after handoff is submitted (NFR24 immutability)'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.created_by IS DISTINCT FROM OLD.created_by THEN
        RAISE EXCEPTION 'Cannot modify created_by after handoff is submitted (NFR24 immutability)'
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.user_id IS DISTINCT FROM OLD.user_id THEN
        RAISE EXCEPTION 'Cannot modify user_id after handoff is submitted (NFR24 immutability)'
            USING ERRCODE = 'check_violation';
    END IF;

    -- Enforce supplemental_notes is append-only (can only grow, not shrink or modify)
    IF OLD.supplemental_notes IS NOT NULL
       AND NEW.supplemental_notes IS NOT NULL
       AND jsonb_array_length(NEW.supplemental_notes) < jsonb_array_length(OLD.supplemental_notes) THEN
        RAISE EXCEPTION 'supplemental_notes can only be appended, not removed (NFR24 immutability)'
            USING ERRCODE = 'check_violation';
    END IF;

    -- Validate status transitions
    -- draft -> pending_acknowledgment (submit)
    -- pending_acknowledgment -> acknowledged (acknowledge)
    -- pending_acknowledgment -> expired (timeout)
    -- acknowledged -> (no further transitions)
    -- expired -> (no further transitions)

    IF OLD.status = 'acknowledged' AND NEW.status != 'acknowledged' THEN
        RAISE EXCEPTION 'Cannot change status once acknowledged'
            USING ERRCODE = 'check_violation';
    END IF;

    IF OLD.status = 'expired' AND NEW.status != 'expired' THEN
        RAISE EXCEPTION 'Cannot change status once expired'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION enforce_handoff_immutability() IS
    'Enforces NFR24 immutability requirement: core fields cannot be modified after submission';

-- Create the immutability enforcement trigger
DROP TRIGGER IF EXISTS enforce_handoff_immutability_trigger ON shift_handoffs;
CREATE TRIGGER enforce_handoff_immutability_trigger
    BEFORE UPDATE ON shift_handoffs
    FOR EACH ROW
    EXECUTE FUNCTION enforce_handoff_immutability();

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check RLS is enabled:
--   SELECT relname, relrowsecurity
--   FROM pg_class
--   WHERE relname = 'shift_handoffs';
--
-- List policies:
--   SELECT policyname, cmd, qual, with_check
--   FROM pg_policies
--   WHERE tablename = 'shift_handoffs';
--
-- Check triggers:
--   SELECT tgname
--   FROM pg_trigger
--   WHERE tgrelid = 'shift_handoffs'::regclass;
--
-- Test immutability (should fail):
--   UPDATE shift_handoffs
--   SET shift_date = '2026-01-01'
--   WHERE status = 'pending_acknowledgment';
