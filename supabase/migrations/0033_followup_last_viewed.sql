-- Story 15.4: Message Thread UI
-- Add last_viewed_at column to action_followups for server-side unread tracking

ALTER TABLE action_followups
ADD COLUMN IF NOT EXISTS last_viewed_at TIMESTAMPTZ DEFAULT NULL;

COMMENT ON COLUMN action_followups.last_viewed_at IS 'Timestamp when the assigner last viewed the message thread. Used for unread indicator computation.';
