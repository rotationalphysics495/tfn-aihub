# Story 8.5: Supervisor Scoped Briefings

Status: Done

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

- [x] Task 1: Create supervisor_assignments database migration (AC: #1, #2)
  - [x] 1.1: Create migration file `20260115_002_supervisor_assignments.sql`
  - [x] 1.2: Define table schema with user_id, asset_id, assigned_by, assigned_at
  - [x] 1.3: Add UNIQUE constraint on (user_id, asset_id)
  - [x] 1.4: Add foreign key references to auth.users and assets tables
  - [x] 1.5: Add RLS policies for read access

- [x] Task 2: Extend CurrentUser model with role context (AC: #1)
  - [x] 2.1: Create `CurrentUserWithRole` model in `app/models/user.py`
  - [x] 2.2: Add `user_role` field (plant_manager | supervisor | admin)
  - [x] 2.3: Add optional `assigned_asset_ids: List[UUID]` field

- [x] Task 3: Create `get_current_user_with_role()` dependency (AC: #1, #4)
  - [x] 3.1: Add dependency function in `app/core/dependencies.py` (new file)
  - [x] 3.2: Query `user_roles` table for user's role
  - [x] 3.3: If supervisor, query `supervisor_assignments` for assigned assets
  - [x] 3.4: Return `CurrentUserWithRole` with populated asset list
  - [x] 3.5: No caching - always query fresh for immediate assignment changes

- [x] Task 4: Update BriefingService with supervisor scoping logic (AC: #1, #2, #3)
  - [x] 4.1: Modify `apps/api/app/services/briefing/morning.py` (or create if not exists)
  - [x] 4.2: Add `get_supervisor_assets()` helper function
  - [x] 4.3: Filter `daily_summaries` query by assigned asset_ids for supervisors
  - [x] 4.4: Return "No assets assigned" error for supervisors with empty assignments
  - [x] 4.5: Skip plant-wide headline generation for supervisor role

- [x] Task 5: Implement preference-aware area ordering (AC: #2)
  - [x] 5.1: Query `user_preferences.area_order` for supervisor
  - [x] 5.2: Sort briefing sections by user's preferred order
  - [x] 5.3: Apply detail_level preference (summary | detailed)

- [x] Task 6: Write unit tests for supervisor scoping (AC: #1-4)
  - [x] 6.1: Test supervisor with assigned assets gets scoped data
  - [x] 6.2: Test supervisor with no assignments gets error message
  - [x] 6.3: Test plant manager still gets all areas
  - [x] 6.4: Test assignment changes are reflected immediately
  - [x] 6.5: Test area ordering respects user preferences

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

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Implementation Summary

Story 8.5 implements supervisor-scoped briefings, allowing supervisors to receive morning briefings that cover only their assigned assets. The implementation includes:

1. **Database Migration**: Created `supervisor_assignments` table with RLS policies, along with `user_roles` and `user_preferences` tables for role-based access control.

2. **User Model Extension**: Extended `CurrentUser` with `CurrentUserWithRole` model that includes `user_role` enum and `assigned_asset_ids` list.

3. **FastAPI Dependencies**: Created `get_current_user_with_role()` dependency that queries role and assignments fresh (no caching per AC#4).

4. **Supervisor Scoping Logic**: Added `generate_supervisor_briefing()` method to `MorningBriefingService` that:
   - Filters areas to only those with assigned assets
   - Skips plant-wide headline (supervisors go straight to their areas)
   - Returns "No assets assigned" error for supervisors without assignments
   - Applies detail_level preference (summary/detailed)

5. **Preference-Aware Ordering**: Areas are ordered according to `user_preferences.area_order` (FR39).

### Files Created/Modified

**Files Created:**
- `supabase/migrations/20260115_002_supervisor_assignments.sql` - Database migration for RBAC tables
- `apps/api/app/core/dependencies.py` - FastAPI dependencies for role-based access
- `apps/api/app/tests/services/briefing/test_briefing_scoping.py` - 27 unit tests for supervisor scoping

**Files Modified:**
- `apps/api/app/models/user.py` - Added `CurrentUserWithRole`, `UserRole`, `UserPreferences` models
- `apps/api/app/services/briefing/morning.py` - Added `generate_supervisor_briefing()` and scoping logic

### Key Decisions

1. **Service-Level Filtering**: Implemented RBAC at the service level (not RLS) per architecture guidance, as briefings require aggregation across multiple tables.

2. **No Caching for Assignments**: Supervisor assignments are always queried fresh to ensure immediate reflection of changes (AC#4).

3. **Case-Insensitive Asset Matching**: Asset names are matched case-insensitively for flexibility.

4. **Graceful Error Handling**: Supervisors with no assignments receive a friendly error response rather than an exception.

### Tests Added

Created `test_briefing_scoping.py` with 27 tests covering:
- `TestSupervisorScopedBriefings` (16 tests): Core AC#1-4 tests
- `TestCurrentUserWithRoleModel` (4 tests): Model property tests
- `TestUserPreferencesModel` (2 tests): Preferences model tests
- `TestGetSupervisorAreas` (5 tests): Area filtering helper tests

### Test Results

```
======================= 27 passed in 0.64s =======================
```

All 27 Story 8.5 tests pass. Additionally, all 23 Story 8.4 (Morning Briefing) tests pass (50 total).

Note: 5 pre-existing failures in `test_service.py` are unrelated to this story - they're caused by Python 3.9 lacking `asyncio.timeout` (added in Python 3.11).

### Notes for Reviewer

1. The migration file creates three tables: `user_roles`, `supervisor_assignments`, and `user_preferences`. All include proper RLS policies.

2. The `filter_areas_by_supervisor_assets()` method creates new area dicts with only assigned assets, preserving immutability.

3. The implementation follows the existing patterns in the codebase for Pydantic models, FastAPI dependencies, and service architecture.

4. Tests use mocking to isolate the scoping logic from external dependencies (tools, database).

### Acceptance Criteria Status

- [x] **AC#1**: Supervisor briefings only include assigned assets (FR15)
  - `generate_supervisor_briefing()` in `apps/api/app/services/briefing/morning.py:353-494`
  - `filter_areas_by_supervisor_assets()` in `apps/api/app/services/briefing/morning.py:315-351`
  - Tests: `test_supervisor_gets_scoped_briefing`, `test_supervisor_briefing_excludes_unassigned_areas`, `test_supervisor_briefing_no_plant_wide_headline`

- [x] **AC#2**: Areas delivered in user's preferred order (FR39), detail level matches preference (FR37)
  - `order_areas()` in `apps/api/app/services/briefing/morning.py:234-266`
  - `generate_supervisor_briefing()` applies detail_level at line 394-397
  - Tests: `test_area_order_preference_applied`, `test_supervisor_with_multiple_areas_ordered`, `test_detail_level_preference_applied`

- [x] **AC#3**: No assets assigned → error message
  - `_create_no_assets_response()` in `apps/api/app/services/briefing/morning.py:496-528`
  - Tests: `test_supervisor_no_assignments_error`, `test_create_no_assets_response`, `test_supervisor_empty_areas_after_filtering_error`

- [x] **AC#4**: Assignment changes reflected immediately (no caching)
  - `get_supervisor_assignments()` in `apps/api/app/core/dependencies.py:85-114` - no caching
  - Tests: `test_assignment_change_reflects_immediately`, `test_no_cached_asset_area_mapping`

### File List

- `supabase/migrations/20260115_002_supervisor_assignments.sql`
- `apps/api/app/core/dependencies.py`
- `apps/api/app/models/user.py`
- `apps/api/app/services/briefing/morning.py`
- `apps/api/app/tests/services/briefing/test_briefing_scoping.py`

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-01-16

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Global `_supabase_client` singleton in `dependencies.py:29` uses module-level global state. For production use, consider dependency injection or async-safe context management. | MEDIUM | Documented |
| 2 | Missing unit tests for `get_current_user_with_role()` and other dependency functions. Service-level tests provide coverage but dedicated dependency tests would improve confidence. | MEDIUM | Documented |
| 3 | Migration assumes `update_updated_at_column()` function exists in database. This is a standard Supabase function but should be documented as a dependency. | MEDIUM | Documented |
| 4 | `tuple[CurrentUserWithRole, Optional[UserPreferences]]` in `dependencies.py:202` uses Python 3.9+ generic syntax. Works but could use `Tuple` from typing for wider compatibility. | LOW | Documented |
| 5 | `SupervisorBriefingError` exception is defined (line 74-76) but never raised. Implementation uses error responses instead, which is valid but the unused exception could be removed. | LOW | Documented |

**Totals**: 0 HIGH, 3 MEDIUM, 2 LOW

### Acceptance Criteria Verification

| AC | Description | Implemented | Tested | Status |
|----|-------------|-------------|--------|--------|
| AC#1 | Supervisor briefings only include assigned assets (FR15) | ✓ | ✓ | PASS |
| AC#2 | Areas in user's preferred order (FR39), detail level matches preference (FR37) | ✓ | ✓ | PASS |
| AC#3 | No assets assigned → error message | ✓ | ✓ | PASS |
| AC#4 | Assignment changes reflected immediately | ✓ | ✓ | PASS |

### Test Results

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2
collected 27 items
======================= 27 passed in 0.48s ====================================
```

All 27 Story 8.5 tests pass.

### Fixes Applied

None - no HIGH severity issues. MEDIUM issues documented for future improvement.

### Remaining Issues

**For future cleanup (LOW priority):**
1. Consider adding dedicated unit tests for FastAPI dependencies
2. Consider removing unused `SupervisorBriefingError` exception
3. Consider adding `from __future__ import annotations` for cleaner type hints

### Code Quality Assessment

- **Patterns**: ✓ Follows existing codebase patterns (Pydantic models, FastAPI dependencies, service architecture)
- **Security**: ✓ RLS policies properly configured, no credential exposure
- **Error Handling**: ✓ Appropriate error responses for edge cases
- **Tests**: ✓ 27 comprehensive tests covering all acceptance criteria
- **Documentation**: ✓ Well-documented with docstrings and comments

### Final Status

**APPROVED** - All acceptance criteria met, all tests pass, no HIGH severity issues.
