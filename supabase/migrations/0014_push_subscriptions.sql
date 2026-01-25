-- Migration: Create push_subscriptions table and add notification preferences (Story 9.8)
-- Story: 9.8 - Handoff Notifications
-- Date: 2026-01-17
--
-- This migration creates:
-- 1. push_subscriptions table for storing Web Push endpoints
-- 2. handoff_notifications_enabled column in user_preferences
-- 3. notifications table for in-app notification tracking
--
-- AC#3: Push Notification (Background) - requires push_subscriptions table
-- AC#4: Notification Preference Respect - requires handoff_notifications_enabled
--
-- References:
-- - [Source: architecture/voice-briefing.md#Push-Notifications-Architecture]
-- - [Source: epic-9.md#Story-9.8]

-- ============================================================================
-- CREATE push_subscriptions TABLE (Task 1.3)
-- ============================================================================

CREATE TABLE IF NOT EXISTS push_subscriptions (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User who owns the subscription
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Web Push subscription data (from browser)
    endpoint TEXT NOT NULL,

    -- VAPID keys from subscription
    p256dh TEXT NOT NULL,
    auth_key TEXT NOT NULL,

    -- User agent for debugging/tracking
    user_agent TEXT,

    -- Device identifier (for managing multiple devices)
    device_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Last successful push timestamp
    last_push_at TIMESTAMPTZ
);

-- ============================================================================
-- INDEXES for push_subscriptions
-- ============================================================================

-- Index on user_id for efficient lookups
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id
ON push_subscriptions(user_id);

-- Unique constraint: one subscription per endpoint per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_push_subscriptions_unique_endpoint
ON push_subscriptions(user_id, endpoint);

-- ============================================================================
-- ROW LEVEL SECURITY for push_subscriptions
-- ============================================================================

-- Enable RLS
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "push_subscriptions_select" ON push_subscriptions;
DROP POLICY IF EXISTS "push_subscriptions_insert" ON push_subscriptions;
DROP POLICY IF EXISTS "push_subscriptions_delete" ON push_subscriptions;
DROP POLICY IF EXISTS "push_subscriptions_service_role" ON push_subscriptions;

-- Policy: Users can read their own subscriptions
CREATE POLICY "push_subscriptions_select"
    ON push_subscriptions
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Policy: Users can create their own subscriptions
CREATE POLICY "push_subscriptions_insert"
    ON push_subscriptions
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

-- Policy: Users can delete their own subscriptions
CREATE POLICY "push_subscriptions_delete"
    ON push_subscriptions
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- Service role has full access (for Edge Functions)
CREATE POLICY "push_subscriptions_service_role"
    ON push_subscriptions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- CREATE notifications TABLE (Task 2.5)
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User who receives the notification
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Notification type
    notification_type VARCHAR(100) NOT NULL,

    -- Title and message
    title TEXT NOT NULL,
    message TEXT,

    -- Related entity (e.g., handoff_id)
    entity_type VARCHAR(100),
    entity_id UUID,

    -- Additional metadata
    metadata JSONB DEFAULT '{}',

    -- Read status
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMPTZ,

    -- Dismissed status (for in-app display)
    is_dismissed BOOLEAN NOT NULL DEFAULT false,
    dismissed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES for notifications
-- ============================================================================

-- Index on user_id for efficient lookups
CREATE INDEX IF NOT EXISTS idx_notifications_user_id
ON notifications(user_id);

-- Index for unread notifications
CREATE INDEX IF NOT EXISTS idx_notifications_unread
ON notifications(user_id, is_read) WHERE is_read = false;

-- Index on entity for looking up notifications by entity
CREATE INDEX IF NOT EXISTS idx_notifications_entity
ON notifications(entity_type, entity_id);

-- Index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_notifications_created_at
ON notifications(user_id, created_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY for notifications
-- ============================================================================

-- Enable RLS
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "notifications_select" ON notifications;
DROP POLICY IF EXISTS "notifications_insert" ON notifications;
DROP POLICY IF EXISTS "notifications_update" ON notifications;
DROP POLICY IF EXISTS "notifications_service_role" ON notifications;

-- Policy: Users can read their own notifications
CREATE POLICY "notifications_select"
    ON notifications
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Policy: Only service role can create notifications
CREATE POLICY "notifications_insert"
    ON notifications
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Policy: Users can update their own notifications (mark as read/dismissed)
CREATE POLICY "notifications_update"
    ON notifications
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Service role has full access
CREATE POLICY "notifications_service_role"
    ON notifications
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- ADD handoff_notifications_enabled TO user_preferences (Task 4.1)
-- ============================================================================

-- Add handoff_notifications_enabled column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_preferences'
        AND column_name = 'handoff_notifications_enabled'
    ) THEN
        ALTER TABLE user_preferences
        ADD COLUMN handoff_notifications_enabled BOOLEAN DEFAULT true;
    END IF;
END $$;

-- Add comment
COMMENT ON COLUMN user_preferences.handoff_notifications_enabled IS
    'Whether user receives push notifications for handoff acknowledgments (Story 9.8)';

-- ============================================================================
-- ENABLE REALTIME for notifications (AC#2)
-- ============================================================================

-- Enable realtime for notifications table
ALTER PUBLICATION supabase_realtime ADD TABLE notifications;

-- ============================================================================
-- UPDATED_AT TRIGGER
-- ============================================================================

-- Create trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_push_subscriptions_updated_at ON push_subscriptions;
CREATE TRIGGER update_push_subscriptions_updated_at
    BEFORE UPDATE ON push_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TABLE COMMENTS
-- ============================================================================

COMMENT ON TABLE push_subscriptions IS
    'Web Push subscription endpoints for users (Story 9.8, 9.12). Stores VAPID-signed push data.';

COMMENT ON COLUMN push_subscriptions.endpoint IS
    'Web Push endpoint URL from browser PushSubscription';

COMMENT ON COLUMN push_subscriptions.p256dh IS
    'P-256 Diffie-Hellman public key from subscription';

COMMENT ON COLUMN push_subscriptions.auth_key IS
    'Authentication secret from subscription';

COMMENT ON TABLE notifications IS
    'In-app notification records for users (Story 9.8). Tracks read/dismissed state.';

COMMENT ON COLUMN notifications.notification_type IS
    'Type of notification (e.g., handoff_acknowledged, eod_reminder)';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Check table exists:
--   SELECT table_name FROM information_schema.tables
--   WHERE table_name IN ('push_subscriptions', 'notifications');
--
-- Check user_preferences column:
--   SELECT column_name FROM information_schema.columns
--   WHERE table_name = 'user_preferences'
--   AND column_name = 'handoff_notifications_enabled';
