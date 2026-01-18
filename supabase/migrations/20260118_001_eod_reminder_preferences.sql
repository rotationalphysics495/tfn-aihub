-- Migration: Add EOD reminder preferences to user_preferences (Story 9.12)
-- Story: 9.12 - EOD Push Notification Reminders
-- Date: 2026-01-18
--
-- This migration adds:
-- 1. eod_reminder_enabled column for enabling EOD reminders
-- 2. eod_reminder_time column for user's preferred reminder time
-- 3. last_eod_viewed_at column for tracking when user last viewed EOD summary
-- 4. eod_notification_failures table for tracking delivery failures
--
-- AC#1: Push Notification Trigger - requires eod_reminder_enabled and eod_reminder_time
-- AC#3: Skip Already-Viewed - requires last_eod_viewed_at tracking
-- AC#4: Delivery Failure Handling - requires failure tracking
--
-- References:
-- - [Source: architecture/voice-briefing.md#Push-Notifications-Architecture]
-- - [Source: epic-9.md#Story-9.12]

-- ============================================================================
-- ADD COLUMNS TO user_preferences (Task 1.3, 1.4)
-- ============================================================================

-- Add eod_reminder_enabled column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_preferences'
        AND column_name = 'eod_reminder_enabled'
    ) THEN
        ALTER TABLE user_preferences
        ADD COLUMN eod_reminder_enabled BOOLEAN DEFAULT false;
    END IF;
END $$;

-- Add eod_reminder_time column if it doesn't exist (default 5:00 PM)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_preferences'
        AND column_name = 'eod_reminder_time'
    ) THEN
        ALTER TABLE user_preferences
        ADD COLUMN eod_reminder_time TIME DEFAULT '17:00:00';
    END IF;
END $$;

-- Add last_eod_viewed_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_preferences'
        AND column_name = 'last_eod_viewed_at'
    ) THEN
        ALTER TABLE user_preferences
        ADD COLUMN last_eod_viewed_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add user_timezone column if it doesn't exist
-- Required for timezone-aware scheduling (Task 3.3)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_preferences'
        AND column_name = 'user_timezone'
    ) THEN
        ALTER TABLE user_preferences
        ADD COLUMN user_timezone TEXT DEFAULT 'America/Chicago';
    END IF;
END $$;

-- ============================================================================
-- CREATE eod_notification_failures TABLE (Task 1, AC#4)
-- ============================================================================

CREATE TABLE IF NOT EXISTS eod_notification_failures (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User who should have received the notification
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Date of the failed notification (for no-retry-same-day logic)
    notification_date DATE NOT NULL,

    -- Number of retry attempts
    retry_count INTEGER NOT NULL DEFAULT 0,

    -- Maximum retries reached
    max_retries_reached BOOLEAN NOT NULL DEFAULT false,

    -- Last failure reason
    failure_reason TEXT,

    -- Timestamps
    first_failure_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_failure_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one failure record per user per day
    UNIQUE(user_id, notification_date)
);

-- ============================================================================
-- INDEXES for eod_notification_failures
-- ============================================================================

-- Index on user_id for efficient lookups
CREATE INDEX IF NOT EXISTS idx_eod_notification_failures_user_id
ON eod_notification_failures(user_id);

-- Index on notification_date for daily cleanup
CREATE INDEX IF NOT EXISTS idx_eod_notification_failures_date
ON eod_notification_failures(notification_date);

-- ============================================================================
-- ROW LEVEL SECURITY for eod_notification_failures
-- ============================================================================

-- Enable RLS
ALTER TABLE eod_notification_failures ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "eod_notification_failures_service_role" ON eod_notification_failures;

-- Service role has full access (for Edge Functions)
CREATE POLICY "eod_notification_failures_service_role"
    ON eod_notification_failures
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON COLUMN user_preferences.eod_reminder_enabled IS
    'Whether user receives EOD summary reminder push notifications (Story 9.12)';

COMMENT ON COLUMN user_preferences.eod_reminder_time IS
    'Time of day to send EOD reminder notification (user local time, Story 9.12)';

COMMENT ON COLUMN user_preferences.last_eod_viewed_at IS
    'When user last viewed the EOD summary page (for skip-if-viewed logic, Story 9.12)';

COMMENT ON COLUMN user_preferences.user_timezone IS
    'User timezone for time-based notification scheduling (Story 9.12)';

COMMENT ON TABLE eod_notification_failures IS
    'Tracks failed EOD notification deliveries per user per day (Story 9.12 AC#4)';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Check columns exist:
--   SELECT column_name, data_type, column_default
--   FROM information_schema.columns
--   WHERE table_name = 'user_preferences'
--   AND column_name IN ('eod_reminder_enabled', 'eod_reminder_time', 'last_eod_viewed_at', 'user_timezone');
--
-- Check failure table exists:
--   SELECT table_name FROM information_schema.tables
--   WHERE table_name = 'eod_notification_failures';
