-- Action Follow-Up Assignments
-- Allows plant managers to assign action items to teammates for follow-up.

CREATE TABLE action_followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_item_id TEXT NOT NULL,
    action_summary TEXT NOT NULL,
    asset_name TEXT,
    category TEXT CHECK (category IN ('safety', 'oee', 'financial')),
    assigned_to UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    assigned_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    note TEXT,
    status TEXT DEFAULT 'assigned' CHECK (status IN ('assigned', 'in_progress', 'resolved')),
    report_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_action_followups_assigned_to ON action_followups(assigned_to);
CREATE INDEX idx_action_followups_assigned_by ON action_followups(assigned_by);
CREATE INDEX idx_action_followups_report_date ON action_followups(report_date);
CREATE INDEX idx_action_followups_status ON action_followups(status);

-- Auto-update updated_at
CREATE TRIGGER update_action_followups_updated_at
    BEFORE UPDATE ON action_followups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS
ALTER TABLE action_followups ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read followups assigned to or by them"
    ON action_followups FOR SELECT
    TO authenticated
    USING (assigned_to = auth.uid() OR assigned_by = auth.uid());

CREATE POLICY "Authenticated users can create followups"
    ON action_followups FOR INSERT
    TO authenticated
    WITH CHECK (assigned_by = auth.uid());

CREATE POLICY "Assigners can update their followups"
    ON action_followups FOR UPDATE
    TO authenticated
    USING (assigned_by = auth.uid());

CREATE POLICY "Service role full access"
    ON action_followups FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
