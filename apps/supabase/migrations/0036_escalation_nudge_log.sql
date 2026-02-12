-- Story 18.5: Escalation Nudge Notifications
-- Creates the escalation_nudge_log table for persistent rate-limit tracking
-- across process restarts. Records when nudge notifications were sent per item.

CREATE TABLE IF NOT EXISTS escalation_nudge_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    nudge_sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel TEXT NOT NULL DEFAULT 'teams'
);

-- Composite index for fast recent-nudge lookups (rate limiting)
CREATE INDEX idx_escalation_nudge_log_lookup
    ON escalation_nudge_log (item_type, item_id, nudge_sent_at DESC);

-- Enable Row Level Security
ALTER TABLE escalation_nudge_log ENABLE ROW LEVEL SECURITY;

-- Service-role-only full access policy (background task runs as service role)
CREATE POLICY "service_role_full_access"
    ON escalation_nudge_log
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
