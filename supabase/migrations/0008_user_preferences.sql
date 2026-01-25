-- Migration: Add onboarding_complete column to user_preferences
-- Story: 8.8 - User Preference Onboarding
-- Date: 2026-01-15
--
-- This migration adds the onboarding_complete column to track whether
-- users have completed the onboarding flow. It also adjusts defaults
-- to match the onboarding flow requirements.
--
-- The user_preferences table was created in Story 8.5 but needs the
-- onboarding_complete flag for tracking first-time user detection.
--
-- References:
-- - [Source: architecture/voice-briefing.md#User Preferences Architecture]
-- - [Source: epic-8.md#Story 8.8]

-- ============================================================================
-- ADD COLUMNS: onboarding_complete and adjust defaults
-- ============================================================================

-- Add onboarding_complete column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_preferences'
        AND column_name = 'onboarding_complete'
    ) THEN
        ALTER TABLE user_preferences
        ADD COLUMN onboarding_complete BOOLEAN DEFAULT false;
    END IF;
END $$;

-- Ensure area_order has proper default (from architecture spec)
-- Default order: Packing, Rychigers, Grinding, Powder, Roasting, Green Bean, Flavor Room
ALTER TABLE user_preferences
ALTER COLUMN area_order SET DEFAULT ARRAY[
    'Packing',
    'Rychigers',
    'Grinding',
    'Powder',
    'Roasting',
    'Green Bean',
    'Flavor Room'
];

-- Update comment to include onboarding flag
COMMENT ON COLUMN user_preferences.onboarding_complete IS 'Whether user has completed the onboarding flow';

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================
-- These queries can be run to verify the migration was successful:
--
-- Check column exists:
--   SELECT column_name, data_type, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'user_preferences';
--
-- Check defaults:
--   SELECT column_name, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'user_preferences' AND column_name = 'onboarding_complete';
