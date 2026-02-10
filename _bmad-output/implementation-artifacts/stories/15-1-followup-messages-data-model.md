# Story 15.1: Follow-Up Messages Data Model

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a `followup_messages` table that logs all outbound notifications and inbound responses,
so that the system maintains a complete conversation thread for each follow-up.

## Acceptance Criteria

1. **AC1 - Table exists with correct schema:** Given the migration runs successfully, when the database is queried, then the `followup_messages` table exists with columns:
   - `id` (UUID PK, default `gen_random_uuid()`)
   - `followup_id` (UUID FK referencing `action_followups(id)` ON DELETE CASCADE)
   - `sender_id` (UUID FK referencing `auth.users(id)`, nullable for email replies from non-app-users)
   - `sender_email` (TEXT, NOT NULL)
   - `direction` (TEXT CHECK IN ('outbound', 'inbound'))
   - `message_type` (TEXT CHECK IN ('assignment', 'response', 'escalation', 'status_update'))
   - `subject` (TEXT)
   - `body` (TEXT)
   - `sent_at` (TIMESTAMPTZ)
   - `created_at` (TIMESTAMPTZ DEFAULT NOW())

2. **AC2 - Indexes exist for query performance:** Given the table is created, when the migration completes, then indexes exist on:
   - `followup_id` (primary query pattern: get all messages for a follow-up)
   - `direction` (filter outbound vs inbound)
   - `sent_at` (chronological ordering of thread)

3. **AC3 - RLS policies enforce access control:** Given RLS is enabled on the table, when a user queries `followup_messages`, then:
   - Users can SELECT messages where the `followup_id` belongs to a follow-up they assigned (`assigned_by`) OR are assigned to (`assigned_to`)
   - Users can INSERT messages where the `followup_id` belongs to a follow-up they assigned or are assigned to
   - Service role has full access for API operations
   - No DELETE policy exists (messages are append-only audit trail)

4. **AC4 - Foreign key cascades:** Given a follow-up is deleted from `action_followups`, when the cascade runs, then all associated `followup_messages` rows are deleted.

5. **AC5 - Migration is idempotent-safe:** The migration file uses standard CREATE TABLE (not IF NOT EXISTS) consistent with project migration patterns. Migration number follows the existing sequence.

## Tasks / Subtasks

- [ ] Task 1: Create the migration file (AC: #1, #2, #4, #5)
  - [ ] 1.1 Determine next migration number after existing `0025_action_followups.sql` (use `0030` as specified in epic technical notes, or next available if 0026-0029 are taken by other Epic 13/14 stories)
  - [ ] 1.2 Create `supabase/migrations/0030_followup_messages.sql`
  - [ ] 1.3 Define `followup_messages` table with all columns per AC#1
  - [ ] 1.4 Add `ON DELETE CASCADE` on `followup_id` FK to `action_followups(id)`
  - [ ] 1.5 Add `CHECK` constraints on `direction` and `message_type` columns
  - [ ] 1.6 Add `DEFAULT NOW()` on `created_at`
  - [ ] 1.7 Add `DEFAULT gen_random_uuid()` on `id`

- [ ] Task 2: Create indexes (AC: #2)
  - [ ] 2.1 Create index `idx_followup_messages_followup_id` on `followup_id`
  - [ ] 2.2 Create index `idx_followup_messages_direction` on `direction`
  - [ ] 2.3 Create index `idx_followup_messages_sent_at` on `sent_at`

- [ ] Task 3: Enable RLS and create policies (AC: #3)
  - [ ] 3.1 `ALTER TABLE followup_messages ENABLE ROW LEVEL SECURITY;`
  - [ ] 3.2 Create SELECT policy: users can read messages for follow-ups they assigned or are assigned to (JOIN on `action_followups` to check `assigned_by` or `assigned_to`)
  - [ ] 3.3 Create INSERT policy: users can insert messages for follow-ups they own (assigned_by or assigned_to)
  - [ ] 3.4 Create service role full access policy
  - [ ] 3.5 No DELETE or UPDATE policies for authenticated users (append-only)

- [ ] Task 4: Verify migration (AC: #1, #2, #3)
  - [ ] 4.1 Add verification queries as SQL comments at the end of the migration (following pattern from `0012_rls_policies.sql`)

## Dev Notes

### Critical Architecture Patterns

**Database:** This table extends the follow-up system started in `supabase/migrations/0025_action_followups.sql`. The parent table `action_followups` has columns: `id`, `action_item_id`, `action_summary`, `asset_name`, `category`, `assigned_to`, `assigned_by`, `note`, `status`, `report_date`, `created_at`, `updated_at`.

**RLS pattern to follow:** The `action_followups` table uses a JOIN-free pattern where the user columns (`assigned_to`, `assigned_by`) are directly on the row. For `followup_messages`, the user relationship is indirect -- the message belongs to a follow-up, and the follow-up has the user references. The RLS policy MUST join to `action_followups` to check access:

```sql
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
```

This pattern ensures both the assigner (manager) and assignee (team member) can see the full conversation thread.

**Migration numbering:** The epic specifies `0030_followup_messages.sql`. Check `supabase/migrations/` before creating -- the current highest migration is `0025_action_followups.sql`. If migrations 0026-0029 do not exist, use `0030` as specified. If they do exist, still use `0030` unless that number is taken.

**No updated_at trigger needed:** Unlike `action_followups`, messages are append-only records. There is no UPDATE use case, so no `updated_at` column or auto-update trigger is needed. This is intentional -- messages are immutable once created.

**sender_id nullable rationale:** `sender_id` is nullable because Story 15.3 introduces token-based responses where someone can respond via email link without being an authenticated app user. The `sender_email` field captures the email address regardless of whether they have an app account.

### Existing Code to Reuse

- `supabase/migrations/0025_action_followups.sql` -- Parent table definition, FK target, RLS pattern reference
- `supabase/migrations/0012_rls_policies.sql` -- Comprehensive RLS pattern with EXISTS subqueries for cross-table access checks
- `supabase/migrations/0004_safety_alert_enhancements.sql` -- Simple table + index creation pattern
- `supabase/migrations/0011_handoff_acknowledgments.sql` -- FK cascade pattern

### Anti-Patterns to Avoid

- **DO NOT** add an `updated_at` column. Messages are append-only; no updates will occur. Adding an update trigger creates unnecessary overhead.
- **DO NOT** create UPDATE or DELETE policies for authenticated users. The audit trail requires messages to be immutable and permanent.
- **DO NOT** put user access checks directly on `followup_messages` columns. The access check MUST join to `action_followups` to determine if the current user is the assigner or assignee.
- **DO NOT** use `ON DELETE SET NULL` for the `followup_id` FK. Use `CASCADE` -- if a follow-up is deleted, orphan messages have no value.
- **DO NOT** add a `status` or `read_at` column to this table. Unread tracking is handled separately in Story 15.4 via a `last_viewed_at` field on follow-ups or a separate tracking mechanism. Keep this table focused on the message audit trail.
- **DO NOT** create a separate migration for RLS. Include RLS policies in the same migration file as the table creation (following the pattern in `0025_action_followups.sql`).

### Project Structure Notes

- Migration file goes in: `supabase/migrations/0030_followup_messages.sql`
- This is the ONLY file created in this story. No API code, no frontend code, no Pydantic models.
- The table will be consumed by Story 15.2 (email service writes outbound messages), Story 15.3 (response capture writes inbound messages), and Story 15.4 (message thread UI reads messages).

### Schema Reference

The complete table DDL should produce:

```sql
CREATE TABLE followup_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    followup_id UUID NOT NULL REFERENCES action_followups(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES auth.users(id),
    sender_email TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('outbound', 'inbound')),
    message_type TEXT NOT NULL CHECK (message_type IN ('assignment', 'response', 'escalation', 'status_update')),
    subject TEXT,
    body TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### RLS Policy Reference

Four policies total:

1. **SELECT** -- Users can read messages for follow-ups where they are `assigned_to` or `assigned_by` (EXISTS subquery on `action_followups`)
2. **INSERT** -- Users can insert messages for follow-ups where they are `assigned_to` or `assigned_by` (EXISTS subquery on `action_followups`)
3. **Service role** -- Full access (`FOR ALL TO service_role USING (true) WITH CHECK (true)`)
4. **No DELETE or UPDATE** -- Intentionally omitted for authenticated users

### Technology Versions

- **PostgreSQL** (Supabase-managed, RLS enabled)
- **Supabase** migration runner (sequential numbered `.sql` files)
- No application code dependencies for this story

### References

- [Source: _bmad-output/planning-artifacts/epic-15.md#Story 15.1] - Story definition, acceptance criteria, column specification
- [Source: supabase/migrations/0025_action_followups.sql] - Parent table schema, FK target, RLS pattern
- [Source: supabase/migrations/0012_rls_policies.sql] - EXISTS-based cross-table RLS pattern
- [Source: docs/data-models.md#Row Level Security] - Project-wide RLS conventions
- [Source: docs/data-models.md#Migrations] - Migration file naming convention
- [Source: docs/improvements.md#Email notifications with response tracking] - Full feature requirements and data model specification
- [Source: docs/architecture-api.md#Database Connections] - Supabase PostgreSQL connection pattern
- [Source: _bmad-output/implementation-artifacts/stories/13-3-followup-status-updates-rls.md] - Related story with follow-up system patterns

### Git Intelligence

Recent commits show:
- `49fa83e4` - WIP: Epic 10 improvements - action engine, smart summary, and UI updates
- `bf92f59f` - Add Epic 10-19 planning artifacts for improvements roadmap
- `bf77a0ec` - Fix team members loading in Assign Follow-Up dialog
- `3551fc9b` - Fix briefing service tool calls and seed test data

The `bf77a0ec` commit confirms the follow-up assignment feature is actively used. The `action_followups` table (migration 0025) is the direct parent table this story extends with the conversation thread capability.

### Cross-Story Context

This is Story 15.1 of 4 in Epic 15 (Email Notifications & Response Tracking):
- **15.1 (this story):** Data model for `followup_messages` -- the foundation
- **15.2:** Email notification service -- will INSERT outbound messages into this table
- **15.3:** Response capture via token link -- will INSERT inbound messages into this table
- **15.4:** Message thread UI -- will SELECT messages from this table for display

Stories 15.2-15.4 all depend on this table existing. This is a pure database migration story with no application code.

### Epic 15 Dependencies

Epic 15 depends on Epic 13 (follow-up assignments must exist). The `action_followups` table from Epic 13 / migration 0025 is the FK target for `followup_messages.followup_id`.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
