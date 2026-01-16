# Story 8.5: Supervisor Scoped Briefings

Status: ready-for-dev

## Story

As a **Supervisor**,
I want **my morning briefing to cover only my assigned assets**,
So that **I get focused information relevant to my responsibilities**.

## Acceptance Criteria

1. **Given** a Supervisor triggers "Start Morning Briefing"
   **When** the briefing is generated
   **Then** only assets from `supervisor_assignments` table are included (FR15)
   **And** no plant-wide headline is shown (straight to their areas)
   **And** detail level matches their preference (FR37)

2. **Given** a Supervisor has 3 assigned assets across 2 areas
   **When** the briefing is generated
   **Then** those 3 assets are covered in detail
   **And** areas are delivered in user's preferred order (FR39)

3. **Given** a Supervisor has no assets assigned
   **When** they trigger a briefing
   **Then** the system displays "No assets assigned - contact your administrator"
   **And** no briefing is generated

4. **Given** a Supervisor's assignment changes mid-session
   **When** they request a new briefing
   **Then** the new assignment is reflected immediately

## Tasks / Subtasks

- [ ] Task 1: Create supervisor_assignments database migration (AC: #1, #2)
  - [ ] 1.1: Create migration file `20260115_002_supervisor_assignments.sql`
  - [ ] 1.2: Define table schema with user_id, asset_id, assigned_by, assigned_at
  - [ ] 1.3: Add UNIQUE constraint on (user_id, asset_id)
  - [ ] 1.4: Add foreign key references to auth.users and assets tables
  - [ ] 1.5: Add RLS policies for read access

- [ ] Task 2: Extend CurrentUser model with role context (AC: #1)
  - [ ] 2.1: Create `CurrentUserWithRole` model in `app/models/user.py`
  - [ ] 2.2: Add `user_role` field (plant_manager | supervisor | admin)
  - [ ] 2.3: Add optional `assigned_asset_ids: List[UUID]` field

- [ ] Task 3: Create `get_current_user_with_role()` dependency (AC: #1, #4)
  - [ ] 3.1: Add dependency function in `app/core/dependencies.py` (new file)
  - [ ] 3.2: Query `user_roles` table for user's role
  - [ ] 3.3: If supervisor, query `supervisor_assignments` for assigned assets
  - [ ] 3.4: Return `CurrentUserWithRole` with populated asset list
  - [ ] 3.5: No caching - always query fresh for immediate assignment changes

- [ ] Task 4: Update BriefingService with supervisor scoping logic (AC: #1, #2, #3)
  - [ ] 4.1: Modify `apps/api/app/services/briefing/morning.py` (or create if not exists)
  - [ ] 4.2: Add `get_supervisor_assets()` helper function
  - [ ] 4.3: Filter `daily_summaries` query by assigned asset_ids for supervisors
  - [ ] 4.4: Return "No assets assigned" error for supervisors with empty assignments
  - [ ] 4.5: Skip plant-wide headline generation for supervisor role

- [ ] Task 5: Implement preference-aware area ordering (AC: #2)
  - [ ] 5.1: Query `user_preferences.area_order` for supervisor
  - [ ] 5.2: Sort briefing sections by user's preferred order
  - [ ] 5.3: Apply detail_level preference (summary | detailed)

- [ ] Task 6: Write unit tests for supervisor scoping (AC: #1-4)
  - [ ] 6.1: Test supervisor with assigned assets gets scoped data
  - [ ] 6.2: Test supervisor with no assignments gets error message
  - [ ] 6.3: Test plant manager still gets all areas
  - [ ] 6.4: Test assignment changes are reflected immediately
  - [ ] 6.5: Test area ordering respects user preferences

## Dev Notes

### Architecture Compliance

**RBAC Pattern (from architecture/voice-briefing.md):**
- Service-level filtering in BriefingService (NOT RLS for aggregations)
- `get_current_user_with_role()` dependency injects role context
- Fresh queries for supervisor_assignments (no caching)

**Database Tables Required:**
```sql
-- From architecture/voice-briefing.md
CREATE TABLE supervisor_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    asset_id UUID REFERENCES assets(id),
    assigned_by UUID REFERENCES auth.users(id),
    assigned_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, asset_id)
);
```

### Technical Implementation Pattern

**Briefing Scoping Logic:**
```python
# Pseudo-code for BriefingService
async def generate_morning_briefing(user: CurrentUserWithRole) -> BriefingResponse:
    if user.user_role == "supervisor":
        if not user.assigned_asset_ids:
            raise HTTPException(
                status_code=400,
                detail="No assets assigned - contact your administrator"
            )
        # Query daily_summaries WHERE asset_id IN user.assigned_asset_ids
        summaries = await get_daily_summaries(asset_ids=user.assigned_asset_ids)
        # Skip plant-wide headline
        include_headline = False
    else:
        # Plant Manager gets all areas
        summaries = await get_daily_summaries()
        include_headline = True
```

**Dependency Pattern:**
```python
# apps/api/app/core/dependencies.py
async def get_current_user_with_role(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUserWithRole:
    # Query user_roles table
    role = await get_user_role(current_user.id)
    assigned_assets = []

    if role == "supervisor":
        # Always query fresh - no caching
        assigned_assets = await get_supervisor_assignments(current_user.id)

    return CurrentUserWithRole(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        user_role=role,
        assigned_asset_ids=assigned_assets
    )
```

### Project Structure Notes

**Files to Create:**
- `supabase/migrations/20260115_002_supervisor_assignments.sql` - Table migration
- `apps/api/app/core/dependencies.py` - New dependencies module

**Files to Modify:**
- `apps/api/app/models/user.py` - Add CurrentUserWithRole
- `apps/api/app/services/briefing/morning.py` - Add supervisor scoping (create if not exists)

**Existing Patterns to Follow:**
- Security patterns from `apps/api/app/core/security.py` (JWT validation, dependencies)
- Model patterns from `apps/api/app/models/user.py` (Pydantic BaseModel)
- Supabase client pattern from `apps/api/app/services/pipelines/morning_report.py`

### Testing Standards

**Test Location:** `apps/api/app/tests/services/test_briefing_scoping.py`

**Test Cases:**
1. `test_supervisor_gets_scoped_briefing` - Verify only assigned assets returned
2. `test_supervisor_no_assignments_error` - Verify error message for no assignments
3. `test_plant_manager_gets_all_areas` - Verify PM sees everything
4. `test_assignment_change_reflects_immediately` - No caching verification
5. `test_area_order_preference_applied` - Verify user preferences respected

### Performance Considerations

- Supervisor assignment queries are NOT cached (per AC#4 - immediate reflection)
- `daily_summaries` cache from morning pipeline (T-1 data) is still used
- Expected query: `SELECT asset_id FROM supervisor_assignments WHERE user_id = $1`

### Dependencies

**Depends On:**
- Story 8.3 (Briefing Synthesis Engine) - BriefingService must exist
- Story 8.4 (Morning Briefing Workflow) - Morning briefing API endpoint
- user_roles table (created in Epic 8 migration set)
- user_preferences table (Story 8.8)

**Note:** If BriefingService doesn't exist yet, this story creates the supervisor scoping logic that will integrate with it. Create stub/interface if needed.

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Role-Based Access Control]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR15]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR37]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR39]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR54]
- [Source: _bmad-output/planning-artifacts/epic-8.md#Story 8.5]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

