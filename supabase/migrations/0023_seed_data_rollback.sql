-- Migration: Rollback Seed Data
-- Purpose: Clear all seed data to allow fresh seeding
-- Date: 2026-01-24
--
-- This rollback removes all seed data in reverse order of dependencies.
-- Run this BEFORE running the updated seed data migration.
--
-- IMPORTANT: This will DELETE all data from these tables. Use with caution.

-- ============================================================================
-- CLEAR DATA (in reverse dependency order)
-- ============================================================================

-- Clear user-related data first (depends on auth.users and assets)
-- Note: We skip user_roles deletion because a trigger prevents removing the last admin.
-- The seed data script uses ON CONFLICT DO UPDATE which will handle this correctly.
DELETE FROM user_preferences WHERE user_id IN (SELECT id FROM auth.users WHERE email = 'heimdall@test.com');
DELETE FROM supervisor_assignments WHERE user_id IN (SELECT id FROM auth.users WHERE email = 'heimdall@test.com');
-- Skipped: DELETE FROM user_roles (protected by last-admin trigger)

-- Clear safety events (depends on assets)
DELETE FROM safety_events WHERE asset_id IN (
    SELECT id FROM assets WHERE id::text LIKE 'a0000001-0000-0000-0000-%'
);

-- Clear live snapshots (depends on assets)
DELETE FROM live_snapshots WHERE asset_id IN (
    SELECT id FROM assets WHERE id::text LIKE 'a0000001-0000-0000-0000-%'
);

-- Clear daily summaries (depends on assets)
DELETE FROM daily_summaries WHERE asset_id IN (
    SELECT id FROM assets WHERE id::text LIKE 'a0000001-0000-0000-0000-%'
);

-- Clear shift targets (depends on assets)
DELETE FROM shift_targets WHERE asset_id IN (
    SELECT id FROM assets WHERE id::text LIKE 'a0000001-0000-0000-0000-%'
);

-- Clear cost centers (depends on assets)
DELETE FROM cost_centers WHERE asset_id IN (
    SELECT id FROM assets WHERE id::text LIKE 'a0000001-0000-0000-0000-%'
);

-- Clear assets (base table)
DELETE FROM assets WHERE id::text LIKE 'a0000001-0000-0000-0000-%';

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- Run these queries to verify rollback completed:
--
-- SELECT COUNT(*) as remaining_assets FROM assets WHERE id LIKE 'a0000001-0000-0000-0000-%';
-- SELECT COUNT(*) as remaining_daily_summaries FROM daily_summaries;
-- SELECT COUNT(*) as remaining_live_snapshots FROM live_snapshots;
-- SELECT COUNT(*) as remaining_safety_events FROM safety_events;
