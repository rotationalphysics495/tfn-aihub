-- Story 13.3: Allow assignees to update their own follow-ups
-- This adds a second UPDATE policy alongside the existing assigner UPDATE policy.
-- PostgreSQL OR-combines multiple policies of the same command type,
-- so both assigners AND assignees can update independently.

CREATE POLICY "Assignees can update their own followups"
    ON action_followups FOR UPDATE
    TO authenticated
    USING (assigned_to = auth.uid())
    WITH CHECK (assigned_to = auth.uid());
