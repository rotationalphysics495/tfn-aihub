-- Migration: Set up cron job for EOD reminder notifications (Story 9.12)
-- Story: 9.12 - EOD Push Notification Reminders
-- Date: 2026-01-18
--
-- This migration creates:
-- 1. pg_cron extension (if not exists)
-- 2. Scheduled job to trigger send-eod-reminder Edge Function hourly
--
-- Task 3: Supabase Scheduled Job (Cron Trigger) (AC: 1)
-- - 3.1: Configure Supabase cron job to trigger Edge Function
-- - 3.2: Set up hourly trigger to check for users at their configured reminder times
-- - 3.3: Handle timezone-aware scheduling (user local time - handled in Edge Function)
--
-- References:
-- - [Source: architecture/voice-briefing.md#Push-Notifications-Architecture]
-- - [Source: epic-9.md#Story-9.12]

-- ============================================================================
-- ENABLE pg_cron EXTENSION (Task 3.1)
-- ============================================================================

-- Note: pg_cron must be enabled via Supabase dashboard or CLI first
-- This extension allows scheduling PostgreSQL functions to run at specified times

CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Grant usage to postgres user (required for Supabase)
GRANT USAGE ON SCHEMA cron TO postgres;

-- ============================================================================
-- CREATE HTTP EXTENSION for calling Edge Functions
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS http;

-- ============================================================================
-- CREATE FUNCTION to call Edge Function (Task 3.1)
-- ============================================================================

-- Function to invoke the send-eod-reminder Edge Function
CREATE OR REPLACE FUNCTION invoke_eod_reminder()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    supabase_url TEXT;
    service_role_key TEXT;
    response_status INT;
BEGIN
    -- Get Supabase URL and service role key from environment
    -- These are stored as database secrets
    SELECT decrypted_secret INTO supabase_url
    FROM vault.decrypted_secrets
    WHERE name = 'supabase_url'
    LIMIT 1;

    SELECT decrypted_secret INTO service_role_key
    FROM vault.decrypted_secrets
    WHERE name = 'service_role_key'
    LIMIT 1;

    -- If secrets not found, try environment variables (fallback)
    IF supabase_url IS NULL THEN
        supabase_url := current_setting('app.settings.supabase_url', true);
    END IF;

    IF service_role_key IS NULL THEN
        service_role_key := current_setting('app.settings.service_role_key', true);
    END IF;

    -- Call the Edge Function
    IF supabase_url IS NOT NULL AND service_role_key IS NOT NULL THEN
        PERFORM http_post(
            supabase_url || '/functions/v1/send-eod-reminder',
            '{}',
            'application/json',
            ARRAY[
                http_header('Authorization', 'Bearer ' || service_role_key)
            ]
        );

        RAISE NOTICE 'EOD reminder function invoked at %', NOW();
    ELSE
        RAISE WARNING 'Cannot invoke EOD reminder: missing configuration';
    END IF;
END;
$$;

-- ============================================================================
-- SCHEDULE CRON JOB (Task 3.2)
-- ============================================================================

-- Run every hour at minute 0 to check for users whose reminder time matches
-- Task 3.2: Set up hourly trigger to check for users at their configured reminder times
-- The Edge Function handles timezone-aware filtering (Task 3.3)

-- First, unschedule if exists (for idempotency)
SELECT cron.unschedule('eod-reminder-hourly')
WHERE EXISTS (
    SELECT 1 FROM cron.job WHERE jobname = 'eod-reminder-hourly'
);

-- Schedule the job to run every hour at minute 0
SELECT cron.schedule(
    'eod-reminder-hourly',
    '0 * * * *',  -- Every hour at minute 0
    $$SELECT invoke_eod_reminder()$$
);

-- ============================================================================
-- ALTERNATIVE: Direct Edge Function invocation via pg_net
-- ============================================================================

-- If pg_net is available (preferred for Supabase), use this approach instead:
-- This is more reliable than pg_cron + http_post

-- CREATE OR REPLACE FUNCTION invoke_eod_reminder_pgnet()
-- RETURNS void
-- LANGUAGE plpgsql
-- SECURITY DEFINER
-- AS $$
-- BEGIN
--     PERFORM net.http_post(
--         url := 'https://your-project.supabase.co/functions/v1/send-eod-reminder',
--         headers := '{"Content-Type": "application/json", "Authorization": "Bearer YOUR_SERVICE_ROLE_KEY"}'::jsonb,
--         body := '{}'::jsonb
--     );
-- END;
-- $$;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Check cron jobs:
--   SELECT * FROM cron.job;
--
-- Check job runs:
--   SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;
--
-- Manual test invoke:
--   SELECT invoke_eod_reminder();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON FUNCTION invoke_eod_reminder() IS
    'Invokes the send-eod-reminder Edge Function (Story 9.12). Called hourly by pg_cron.';
