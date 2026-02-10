# Story 13.3: Follow-Up Status Updates & RLS

Status: ready-for-dev

## Story

As a team member assigned a follow-up,
I want to update the status of my assignment (in-progress, resolved) with a note,
so that the manager can see progress without asking in person.

## Acceptance Criteria

1. **AC1 - Assignee can update follow-up status:** Given an assignee is authenticated and has follow-ups assigned to them, when they call `PATCH /api/v1/followups/{followup_id}` with `status` and optional `note`, then the follow-up status is updated in `action_followups`, the `updated_at` timestamp is refreshed, and only the fields provided are updated (partial update).

2. **AC2 - RLS denies unauthorized updates:** Given an assignee tries to update a follow-up not assigned to them, when the update request is made, then the request is denied with 403 (RLS enforcement).

3. **AC3 - Manager sees updated follow-up status:** Given a manager queries follow-ups they created, when the follow-up has been updated by the assignee, then the response includes the current status and the assignee's note.

## Tasks / Subtasks

- [ ] Task 1: Create RLS migration for assignee UPDATE policy (AC: #1, #2)
  - [ ] 1.1 Create `supabase/migrations/0028_followup_assignee_rls.sql`
  - [ ] 1.2 Add new RLS policy: `"Assignees can update their own followups"` with `USING (assigned_to = auth.uid())`
  - [ ] 1.3 Add `WITH CHECK (assigned_to = auth.uid())` to prevent reassignment via UPDATE
  - [ ] 1.4 Verify existing policies remain intact (SELECT, INSERT, existing UPDATE for assigners)

- [ ] Task 2: Add follow-up update Pydantic schemas (AC: #1)
  - [ ] 2.1 Add `FollowUpUpdateRequest` schema to `apps/api/app/schemas/action.py`
  - [ ] 2.2 Add `FollowUpResponse` schema to `apps/api/app/schemas/action.py`
  - [ ] 2.3 Validate `status` field against allowed values: `assigned`, `in_progress`, `resolved`
  - [ ] 2.4 Make both `status` and `note` optional for partial update support

- [ ] Task 3: Create PATCH endpoint for follow-up updates (AC: #1, #2, #3)
  - [ ] 3.1 Add `PATCH /followups/{followup_id}` endpoint in `apps/api/app/api/actions.py`
  - [ ] 3.2 Authenticate via `get_current_user` dependency
  - [ ] 3.3 Use Supabase client with user's JWT (not service role) so RLS is enforced
  - [ ] 3.4 Return updated follow-up record with current status and note
  - [ ] 3.5 Return 404 if follow-up not found, 403 if RLS blocks the update

- [ ] Task 4: Register the new endpoint (AC: #1)
  - [ ] 4.1 Verify the actions router is already mounted at `/api/v1/actions` in `main.py` (it is -- reuse this router)
  - [ ] 4.2 The PATCH endpoint path will be `/api/v1/actions/followups/{followup_id}` since the actions router is mounted at `/api/v1/actions`

- [ ] Task 5: Write tests (AC: #1, #2, #3)
  - [ ] 5.1 Unit test: successful status update by assignee
  - [ ] 5.2 Unit test: partial update (status only, note only)
  - [ ] 5.3 Unit test: 403 when non-assignee tries to update
  - [ ] 5.4 Unit test: 404 when follow-up doesn't exist
  - [ ] 5.5 Unit test: validation rejects invalid status values

## Dev Notes

### Critical Architecture Patterns

**Database:** The `action_followups` table already exists (migration `0025_action_followups.sql`). It has:
- `status TEXT DEFAULT 'assigned' CHECK (status IN ('assigned', 'in_progress', 'resolved'))`
- `updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()` with auto-update trigger
- Indexes on `assigned_to`, `assigned_by`, `report_date`, `status`
- Existing RLS policies: SELECT (assigned_to OR assigned_by), INSERT (assigned_by = auth.uid()), UPDATE (assigned_by = auth.uid()), ALL for service_role

**The key gap this story fills:** The existing UPDATE RLS policy only allows the **assigner** (manager) to update follow-ups. Assignees (team members) cannot update their own records. This story adds a second UPDATE policy for assignees.

**API patterns (MUST follow):**
- FastAPI router in `apps/api/app/api/actions.py` -- add the PATCH endpoint here alongside existing action endpoints
- Authentication via `Depends(get_current_user)` from `app.core.security`
- The `CurrentUser` model provides `id`, `email`, `role` fields
- Supabase client pattern: use `supabase-py` client. For RLS enforcement, pass the user's JWT token to the Supabase client so Postgres RLS policies are applied server-side
- Pydantic schemas in `apps/api/app/schemas/action.py`
- Router is mounted at both `/api/actions` and `/api/v1/actions` in `main.py`

**Supabase RLS enforcement pattern:**
- The existing code in `AssignFollowUpDialog.tsx` uses the Supabase JS client directly with the user's session token for INSERT operations
- For the API endpoint, the Python backend needs to forward the user's JWT to Supabase so RLS policies apply
- Check how other endpoints handle this -- the `team.py` router uses `create_client(settings.supabase_url, settings.supabase_key)` with the **service role key**, which bypasses RLS
- For this story, you MUST NOT use the service role key for the update operation. Use one of these approaches:
  1. Create a Supabase client initialized with the user's access token (preferred for RLS)
  2. Or manually verify ownership in Python code before using service role client
- Approach 1 is preferred because it lets Postgres enforce the RLS policy directly, matching AC#2

**Response format:** Return the updated follow-up record as JSON. Include at minimum: `id`, `status`, `note`, `updated_at`, `action_item_id`, `action_summary`, `asset_name`.

### Existing Code to Reuse

- `apps/api/app/core/security.py` -- `get_current_user` dependency for authentication
- `apps/api/app/core/config.py` -- `get_settings()` for Supabase URL/key
- `apps/api/app/schemas/action.py` -- add new schemas alongside existing `ActionItem`, `ActionCategory`, etc.
- `apps/api/app/api/actions.py` -- add PATCH endpoint to existing router
- `supabase/migrations/0025_action_followups.sql` -- reference for table schema and existing policies

### Anti-Patterns to Avoid

- **DO NOT** create a separate router file for follow-ups. Add the endpoint to the existing `actions.py` router.
- **DO NOT** use the service role Supabase key for the PATCH operation if you want RLS enforcement. The whole point of AC#2 is that RLS blocks unauthorized updates.
- **DO NOT** add columns to the `action_followups` table. The existing schema already supports status and note fields.
- **DO NOT** create a separate migration for schema changes -- only RLS policy changes are needed.
- **DO NOT** modify existing RLS policies. ADD a new policy alongside the existing ones.

### Project Structure Notes

- Migration goes in: `supabase/migrations/0028_followup_assignee_rls.sql`
  - NOTE: Migration numbering assumes 0026 and 0027 may be created by stories 13.1 and 13.2. If those don't exist yet, use the next available number after 0025. Check `supabase/migrations/` directory before creating.
- API endpoint in: `apps/api/app/api/actions.py`
- Schemas in: `apps/api/app/schemas/action.py`
- Tests in: `apps/api/tests/api/test_followup_update.py` (new file) or alongside existing action tests

### RLS Migration Details

The new migration should add ONE new policy:

```sql
-- Allow assignees to update their own follow-ups
CREATE POLICY "Assignees can update their own followups"
    ON action_followups FOR UPDATE
    TO authenticated
    USING (assigned_to = auth.uid())
    WITH CHECK (assigned_to = auth.uid());
```

**IMPORTANT:** This will result in TWO UPDATE policies on the table:
1. Existing: `"Assigners can update their followups"` -- USING (assigned_by = auth.uid())
2. New: `"Assignees can update their own followups"` -- USING (assigned_to = auth.uid())

PostgreSQL RLS is OR-based for multiple policies of the same command type. Either policy passing grants access. This is correct behavior -- both the assigner AND assignee should be able to update.

**WAIT:** The existing policy name is `"Assigners can update their followups"` and the new policy name must be different. The epic suggests: `"Assignees can update their own followups"`. Use this exact name.

### PATCH Endpoint Implementation Notes

```python
# Endpoint signature pattern:
@router.patch("/followups/{followup_id}")
async def update_followup(
    followup_id: str,  # UUID as string
    update: FollowUpUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
```

**Partial update logic:**
- Only update fields that are explicitly provided (not None)
- Build the update dict dynamically: `update_data = update.model_dump(exclude_unset=True)`
- The `updated_at` column auto-updates via the existing database trigger

**Error handling:**
- If Supabase returns no rows updated and no error, the follow-up either doesn't exist or RLS blocked it
- Query the follow-up first with a SELECT to distinguish 404 (not found) from 403 (unauthorized)
- Or catch the PostgREST error codes to differentiate

### Schema Definitions

```python
class FollowUpUpdateRequest(BaseModel):
    """Request to update a follow-up assignment status."""
    status: Optional[str] = Field(
        None,
        description="New status: assigned, in_progress, resolved"
    )
    note: Optional[str] = Field(
        None,
        description="Status update note from assignee"
    )

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            allowed = {'assigned', 'in_progress', 'resolved'}
            if v not in allowed:
                raise ValueError(f'Status must be one of: {allowed}')
        return v


class FollowUpResponse(BaseModel):
    """Response for a follow-up record."""
    id: str
    action_item_id: str
    action_summary: str
    asset_name: Optional[str] = None
    category: Optional[str] = None
    assigned_to: str
    assigned_by: str
    status: str
    note: Optional[str] = None
    report_date: str
    created_at: str
    updated_at: str
```

### References

- [Source: supabase/migrations/0025_action_followups.sql] - Existing table schema and RLS policies
- [Source: apps/api/app/api/actions.py] - Existing actions router pattern
- [Source: apps/api/app/schemas/action.py] - Existing action schemas
- [Source: apps/api/app/core/security.py] - Authentication dependency
- [Source: apps/api/app/api/team.py] - Supabase client pattern (but uses service role -- do NOT copy for RLS)
- [Source: apps/web/src/components/action-engine/AssignFollowUpDialog.tsx] - Frontend follow-up insert pattern (uses user session token for RLS)
- [Source: docs/improvements.md#Follow-up status tracking] - Product requirements context
- [Source: _bmad-output/planning-artifacts/epic-13.md#Story 13.3] - Epic story definition
- [Source: docs/architecture-api.md] - API architecture patterns
- [Source: docs/data-models.md#Row Level Security] - RLS patterns

### Technology Versions

- **FastAPI** 0.109+ (async endpoints, Depends injection)
- **Pydantic** v2 (BaseModel, Field, field_validator, model_dump with exclude_unset)
- **supabase-py** 2.0+ (PostgreSQL client)
- **Python** 3.11+
- **PostgreSQL** (Supabase-managed, RLS enabled)

### Git Intelligence

Recent commits show:
- `49fa83e4` - WIP: Epic 10 improvements - action engine, smart summary, and UI updates
- `bf77a0ec` - Fix team members loading in Assign Follow-Up dialog
- `3551fc9b` - Fix briefing service tool calls and seed test data

The `bf77a0ec` commit is directly relevant -- it fixed the team member loading in the AssignFollowUpDialog, confirming the follow-up assignment feature is actively being used and this story builds directly on top of it.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
