-- Follow-Up Messages
-- Story 15.1: Follow-Up Messages Data Model
-- Logs all outbound notifications and inbound responses for follow-up conversation threads.
-- This is an append-only audit trail — no UPDATE or DELETE policies for authenticated users.

CREATE TABLE followup_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    followup_id UUID NOT NULL REFERENCES action_followups(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    sender_email TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('outbound', 'inbound')),
    message_type TEXT NOT NULL CHECK (message_type IN ('assignment', 'response', 'escalation', 'status_update')),
    subject TEXT,
    body TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_followup_messages_followup_id ON followup_messages(followup_id);
CREATE INDEX idx_followup_messages_direction ON followup_messages(direction);
CREATE INDEX idx_followup_messages_sent_at ON followup_messages(sent_at);

-- RLS
ALTER TABLE followup_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read messages for their followups"
    ON followup_messages FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM action_followups af
            WHERE af.id = followup_messages.followup_id
            AND (af.assigned_to = auth.uid() OR af.assigned_by = auth.uid())
        )
    );

CREATE POLICY "Users can insert messages for their followups"
    ON followup_messages FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM action_followups af
            WHERE af.id = followup_messages.followup_id
            AND (af.assigned_to = auth.uid() OR af.assigned_by = auth.uid())
        )
    );

CREATE POLICY "Service role full access"
    ON followup_messages FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Verification queries (for manual validation):
-- SELECT table_name FROM information_schema.tables WHERE table_name = 'followup_messages';
-- SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'followup_messages' ORDER BY ordinal_position;
-- SELECT indexname FROM pg_indexes WHERE tablename = 'followup_messages';
-- SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'followup_messages';
-- SELECT policyname, cmd, roles FROM pg_policies WHERE tablename = 'followup_messages';
