-- Action Acknowledgments
-- Allows plant managers to acknowledge action items as reviewed/completed.
-- Unique constraint ensures one acknowledgment per user per action per report day.

CREATE TABLE action_acknowledgments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_item_id TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    acknowledged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    note TEXT,
    report_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (action_item_id, user_id, report_date)
);

CREATE INDEX idx_action_ack_user_id ON action_acknowledgments(user_id);
CREATE INDEX idx_action_ack_report_date ON action_acknowledgments(report_date);
CREATE INDEX idx_action_ack_action_item_id ON action_acknowledgments(action_item_id);

-- Auto-update updated_at
CREATE TRIGGER update_action_acknowledgments_updated_at
    BEFORE UPDATE ON action_acknowledgments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS
ALTER TABLE action_acknowledgments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read their own acknowledgments"
    ON action_acknowledgments FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can create their own acknowledgments"
    ON action_acknowledgments FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own acknowledgments"
    ON action_acknowledgments FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Service role full access"
    ON action_acknowledgments FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
