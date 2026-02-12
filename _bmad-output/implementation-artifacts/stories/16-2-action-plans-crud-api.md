# Story 16.2: Action Plans CRUD API

Status: done

## Story

As a Plant Manager,
I want API endpoints to create, read, update, and list action plans,
so that the frontend can manage the full action plan lifecycle.

## Acceptance Criteria

1. **Given** an authenticated user calls `POST /api/v1/action-plans`
   **When** the request includes title, description, category, root_cause, corrective_action, asset_id, priority, due_date
   **Then** a new action plan is created with status='open' and the current user as owner
   **And** the response includes the created plan with its ID

2. **Given** an authenticated user calls `GET /api/v1/action-plans`
   **When** optional filters are provided (status, asset_id, owner_id, priority)
   **Then** matching action plans are returned sorted by priority (critical first) then due_date

3. **Given** an action plan owner calls `PATCH /api/v1/action-plans/{id}`
   **When** the request includes updated fields (status, corrective_action, due_date, etc.)
   **Then** the plan is updated and an `action_plan_updates` record is created logging the change

4. **Given** a user calls `POST /api/v1/action-plans/{id}/updates`
   **When** the request includes update_text and optional status_change
   **Then** a progress update is recorded in `action_plan_updates`
   **And** if status_change is provided, the plan's status is updated

5. **Given** a user calls `POST /api/v1/action-plans/{id}/verify`
   **When** the user confirms the fix worked
   **Then** the plan status is set to 'verified', `verified_by` and `verified_at` are recorded

## Tasks / Subtasks

- [ ] Task 1: Create Pydantic schemas (AC: #1, #2, #3, #4, #5)
  - [ ] 1.1 Create `apps/api/app/schemas/action_plan.py`
  - [ ] 1.2 Define `ActionPlanCategory` enum: 'corrective', 'preventive', 'improvement'
  - [ ] 1.3 Define `ActionPlanStatus` enum: 'draft', 'open', 'in_progress', 'completed', 'verified'
  - [ ] 1.4 Define `ActionPlanPriority` enum: 'low', 'medium', 'high', 'critical'
  - [ ] 1.5 Define `ActionPlanCreate` request schema (title, description, category, root_cause, corrective_action, preventive_action, asset_id, priority, due_date, source_followup_id)
  - [ ] 1.6 Define `ActionPlanUpdate` request schema (all fields optional except id)
  - [ ] 1.7 Define `ActionPlanResponse` response schema (full plan with all fields)
  - [ ] 1.8 Define `ActionPlanListResponse` with pagination (items, total_count, page, page_size)
  - [ ] 1.9 Define `ActionPlanUpdateCreate` request schema (update_text, status_change)
  - [ ] 1.10 Define `ActionPlanUpdateResponse` response schema
  - [ ] 1.11 Define `ActionPlanVerifyRequest` schema (optional verification_notes)
- [ ] Task 2: Create CRUD API router (AC: #1, #2, #3, #4, #5)
  - [ ] 2.1 Create `apps/api/app/api/action_plans.py` with `router = APIRouter()`
  - [ ] 2.2 Implement `POST /` - Create action plan (AC #1)
  - [ ] 2.3 Implement `GET /` - List action plans with filters and pagination (AC #2)
  - [ ] 2.4 Implement `GET /{id}` - Get single action plan by ID
  - [ ] 2.5 Implement `PATCH /{id}` - Update action plan with change logging (AC #3)
  - [ ] 2.6 Implement `POST /{id}/updates` - Add progress update (AC #4)
  - [ ] 2.7 Implement `GET /{id}/updates` - List progress updates for a plan
  - [ ] 2.8 Implement `POST /{id}/verify` - Verify action plan completion (AC #5)
- [ ] Task 3: Register router in main.py (AC: #1)
  - [ ] 3.1 Import `action_plans` in `apps/api/app/main.py`
  - [ ] 3.2 Register with `app.include_router(action_plans.router, prefix="/api/v1/action-plans", tags=["Action Plans"])`
- [ ] Task 4: Supabase data access layer (AC: #1, #2, #3, #4, #5)
  - [ ] 4.1 Create helper function `_get_supabase_client()` (follow pattern from `handoff.py`)
  - [ ] 4.2 Implement `_create_action_plan()` - insert into `action_plans` table
  - [ ] 4.3 Implement `_get_action_plan_by_id()` - select with joins
  - [ ] 4.4 Implement `_list_action_plans()` - filtered query with sorting
  - [ ] 4.5 Implement `_update_action_plan()` - partial update
  - [ ] 4.6 Implement `_create_update_record()` - insert into `action_plan_updates`
  - [ ] 4.7 Implement `_get_updates_for_plan()` - list updates chronologically

## Dev Notes

### Critical Architecture Patterns

**Authentication:** All endpoints MUST use `Depends(get_current_user)` from `app.core.security`. Import `CurrentUser` from `app.models.user`. Follow the exact pattern used in `actions.py` and `handoff.py`.

**Supabase client pattern:** Use `create_client(settings.supabase_url, settings.supabase_key)` from `supabase` package, via `app.core.config.get_settings()`. Follow the `_get_supabase_client()` helper pattern from `handoff.py`.

**API versioning:** Use `/api/v1/action-plans` prefix. This project uses versioned endpoints for newer features (see `voice`, `briefing`, `preferences`, `handoff`, `admin`, `team` routers).

**Router registration pattern in `main.py`:**
```python
from app.api import ..., action_plans
# Add at end of router registrations:
# Story 16.2: Action Plans CRUD API
app.include_router(action_plans.router, prefix="/api/v1/action-plans", tags=["Action Plans"])
```

**Pydantic schema conventions:** Use `BaseModel` with `ConfigDict`, `Field` with descriptions, and `str(Enum)` for status/category/priority enums. Follow the patterns in `app/schemas/action.py` and `app/schemas/financial.py`.

**Error handling:** Use `HTTPException` with appropriate status codes (400 for validation, 403 for authorization, 404 for not found, 500 for server errors). Include descriptive `detail` messages.

### Database Dependency

This story depends on Story 16.1 (Action Plans Data Model) which creates the `action_plans` and `action_plan_updates` tables. The migration file is `supabase/migrations/0031_action_plans.sql`.

**Expected table schema for `action_plans`:**
- `id` UUID PK, `title` TEXT, `description` TEXT, `asset_id` UUID FK nullable
- `category` TEXT CHECK ('corrective','preventive','improvement')
- `root_cause` TEXT, `corrective_action` TEXT, `preventive_action` TEXT
- `source_followup_id` UUID FK nullable (links to `action_followups`)
- `owner_id` UUID FK, `status` TEXT CHECK ('draft','open','in_progress','completed','verified')
- `priority` TEXT CHECK ('low','medium','high','critical')
- `due_date` DATE, `completed_at` TIMESTAMPTZ
- `verified_by` UUID FK nullable, `verified_at` TIMESTAMPTZ
- `created_at` TIMESTAMPTZ, `updated_at` TIMESTAMPTZ

**Expected table schema for `action_plan_updates`:**
- `id` UUID PK, `action_plan_id` UUID FK
- `author_id` UUID FK, `update_text` TEXT
- `status_change` TEXT nullable (e.g., "open -> in_progress")
- `created_at` TIMESTAMPTZ

**RLS policies (set in 16.1 migration):**
- Owners can CRUD their own plans
- All authenticated users can read all plans
- Service role has full access

### Sorting Logic (AC #2)

Priority sort order: critical=0, high=1, medium=2, low=3. Then sort by `due_date` ascending (soonest first). Use a `PRIORITY_SORT_MAP` similar to `PRIORITY_RANK_MAP` in `app/schemas/action.py`.

For Supabase queries, use `.order()` chaining. Since Supabase-py doesn't support custom sort expressions natively, apply priority sorting in Python after fetching, or use a `.rpc()` call if needed.

### Change Logging (AC #3)

When `PATCH /api/v1/action-plans/{id}` is called, compare old vs new values and create an `action_plan_updates` record with:
- `update_text`: Auto-generated description of what changed (e.g., "Status changed from open to in_progress. Due date updated to 2026-03-15.")
- `status_change`: If status changed, record "old_status -> new_status"

### Verify Endpoint Logic (AC #5)

The `POST /api/v1/action-plans/{id}/verify` endpoint should:
1. Verify plan is in 'completed' status (return 400 if not)
2. Set `status` to 'verified'
3. Set `verified_by` to current user ID
4. Set `verified_at` to current timestamp
5. Create an `action_plan_updates` record logging the verification

### Pagination Pattern

Follow standard offset/limit pagination pattern:
```python
@router.get("/", response_model=ActionPlanListResponse)
async def list_action_plans(
    status: Optional[ActionPlanStatus] = Query(None),
    asset_id: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    priority: Optional[ActionPlanPriority] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
```

### Project Structure Notes

- New files must go in the existing project structure - do NOT create new directories
- `apps/api/app/api/action_plans.py` - New router file (same level as `actions.py`, `handoff.py`)
- `apps/api/app/schemas/action_plan.py` - New schema file (same level as `action.py`, `financial.py`)
- `apps/api/app/main.py` - Modify to register new router
- Do NOT create a separate service layer for this story; keep Supabase queries as helper functions in the router file (consistent with `handoff.py` pattern)

### Anti-Patterns to Avoid

- Do NOT use SQLAlchemy ORM for this - use `supabase-py` client for all Supabase table operations
- Do NOT create a `models/action_plan.py` - schemas go in `schemas/` directory
- Do NOT duplicate the `_get_supabase_client()` helper - import it or define it locally following the handoff.py pattern
- Do NOT add `action_plans` to the `app/api/__init__.py` - the import is done directly in `main.py`
- Do NOT use `response_model_exclude_unset=True` - return full response models

### Existing Code References

- **Authentication pattern:** `apps/api/app/core/security.py` - `get_current_user` dependency
- **Schema pattern:** `apps/api/app/schemas/action.py` - Enum + Pydantic model conventions
- **Router pattern:** `apps/api/app/api/actions.py` - APIRouter with auth dependency
- **CRUD router pattern:** `apps/api/app/api/handoff.py` - Full CRUD with Supabase client
- **main.py registration:** `apps/api/app/main.py` - Import and `include_router` pattern
- **Migration reference:** `supabase/migrations/0025_action_followups.sql` - RLS pattern for `action_followups` table that `source_followup_id` references

### Testing Standards

- Tests should go in `apps/api/tests/` directory
- Use pytest with `httpx.AsyncClient` for endpoint testing
- Mock Supabase client for unit tests
- Test all 5 acceptance criteria with positive and negative cases
- Test authorization (only owner can update, any auth user can read)
- Test validation (required fields, enum values, status transitions)

### References

- [Source: _bmad-output/planning-artifacts/epic-16.md#Story 16.2]
- [Source: docs/architecture-api.md#API Endpoints]
- [Source: docs/architecture-api.md#Security]
- [Source: docs/data-models.md#Row Level Security]
- [Source: apps/api/app/api/handoff.py - CRUD pattern reference]
- [Source: apps/api/app/api/actions.py - Router pattern reference]
- [Source: apps/api/app/schemas/action.py - Schema pattern reference]
- [Source: apps/api/app/main.py - Router registration pattern]
- [Source: apps/api/app/core/security.py - Auth dependency pattern]
- [Source: supabase/migrations/0025_action_followups.sql - RLS and FK pattern for source_followup_id]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Implementation Summary

Implemented the complete Action Plans CRUD API with 7 endpoints covering all 5 acceptance criteria. The API supports creating, listing (with filters/sorting/pagination), updating (with auto-generated change logs), adding progress updates, and verifying action plans. Uses the two-client Supabase pattern for RLS enforcement on write operations and service-role client for reads and cross-user verification.

### Files Created
- `apps/api/app/schemas/action_plan.py` - Pydantic schemas: enums (ActionPlanCategory, ActionPlanStatus, ActionPlanPriority), PRIORITY_SORT_MAP, request models (ActionPlanCreate, ActionPlanUpdate, ActionPlanUpdateCreate, ActionPlanVerifyRequest), response models (ActionPlanResponse, ActionPlanListResponse, ActionPlanUpdateResponse)
- `apps/api/app/api/action_plans.py` - APIRouter with 7 endpoints: POST /, GET /, GET /{id}, PATCH /{id}, POST /{id}/updates, GET /{id}/updates, POST /{id}/verify. Includes helper functions for Supabase client management, change description building, and priority-based sorting.

### Files Modified
- `apps/api/app/main.py` - Added action_plans to import line and registered router with prefix="/api/v1/action-plans", tags=["Action Plans"]

### Key Decisions
- Python-side sorting for priority ranking using PRIORITY_SORT_MAP since Supabase-py doesn't support custom sort expressions. Fetches all filtered results then sorts and paginates in Python.
- Service-role client used for auto-generated change log inserts in PATCH endpoint (system recording changes on behalf of user) and for verify endpoint (cross-user verification bypasses owner-only RLS).
- User-scoped client used for POST / (create) and PATCH /{id} (update) to enforce RLS policies.
- No strict state machine enforcement for status transitions — relies on DB CHECK constraint for valid values per design plan.
- Empty PATCH body returns 422 before any DB operation via model_dump(exclude_unset=True) check.

### Tests Added
- `apps/api/tests/test_action_plans_api.py` - 59 tests covering all 5 ACs: 10 unit tests for schema validation, 49 integration tests for endpoint behavior including auth, filters, sorting, pagination, change logging, progress updates, verification, error handling, and router registration.

### Notes for Reviewer
- The test file was provided as a pre-written TDD specification. All 59 tests pass.
- The _sort_plans function handles null priorities (rank 99) and null due_dates (sort last) gracefully.
- The verify endpoint uses service-role client for both the status update and the change log insert, allowing any authenticated user to verify (not just the owner).

### Test Results
```
59 passed, 24 warnings in 0.25s
```

### Acceptance Criteria Status
- [x] AC#1: POST /api/v1/action-plans creates plan with status='open' and current user as owner — implemented in `apps/api/app/api/action_plans.py::create_action_plan()`
- [x] AC#2: GET /api/v1/action-plans returns filtered/sorted/paginated results — implemented in `apps/api/app/api/action_plans.py::list_action_plans()`
- [x] AC#3: PATCH /api/v1/action-plans/{id} updates plan and creates change log — implemented in `apps/api/app/api/action_plans.py::update_action_plan()`
- [x] AC#4: POST /api/v1/action-plans/{id}/updates adds progress update with optional status change — implemented in `apps/api/app/api/action_plans.py::add_progress_update()`
- [x] AC#5: POST /api/v1/action-plans/{id}/verify sets status to 'verified' with verified_by/verified_at — implemented in `apps/api/app/api/action_plans.py::verify_action_plan()`

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-02-12
**Diff Size**: 2875 lines

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS
- Test Coverage: PASS
- Security: PASS

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Inconsistent client creation in update_action_plan — uses inline create_client() instead of _get_supabase_client()/_get_user_client() helpers | MEDIUM | Fixed |
| 2 | List endpoint fetches ALL matching records for Python-side sorting (documented architectural decision) | MEDIUM | Documented |
| 3 | _build_change_description str() comparison could produce false positives with enum repr | LOW | Documented |
| 4 | Helper functions lack return type annotations (handoff.py uses -> Optional[Client]) | LOW | Documented |
| 5 | New Supabase client created per request (consistent with codebase-wide pattern) | LOW | Documented |
| 6 | ActionPlanCreate.description is Optional but AC#1 wording implies required (DB allows NULL, tests confirm intentional) | LOW | Documented |
| 7 | User JWT passed as API key to create_client for RLS (consistent with actions.py and followups.py pattern) | LOW | Documented |

**Totals**: 0 HIGH, 2 MEDIUM, 5 LOW

### Fixes Applied

| Issue # | Fix Description | Verified |
|---------|-----------------|----------|
| 1 | Replaced inline `create_client(settings.supabase_url, settings.supabase_key)` and `create_client(settings.supabase_url, user_token)` in `update_action_plan()` with `_get_supabase_client()` and `_get_user_client(user_token)` helper calls for consistency | 59 tests pass |

### Remaining Issues (Low Severity)
- Issue #3: _build_change_description uses str() comparison — works for current use case but could be fragile with enum types
- Issue #4: Helper functions missing return type annotations — cosmetic inconsistency with handoff.py
- Issue #5: Client-per-request pattern — codebase-wide concern, not specific to this PR
- Issue #6: Optional description field — intentional design decision confirmed by DB schema and tests
- Issue #7: JWT-as-API-key pattern — established pattern in codebase for RLS enforcement

### Final Status
Approved with fixes

## Test Quality Review

**Reviewer**: Test Architect (TEA)
**Date**: 2026-02-12
**Quality Score**: 100/100 (A+)
**Tests Reviewed**: 59 (10 unit, 49 integration)
**Test Duration**: 0.25s total (all 59 tests)

### Criteria Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | BDD Format | ✅ PASS (+5 bonus) | All 59 tests have explicit Given-When-Then docstrings |
| 2 | Test ID Conventions | ✅ PASS (+5 bonus) | UNIT-001–010, INT-001–049, all traceable |
| 3 | Hard Waits | ✅ PASS | No sleep/delay/timeout calls |
| 4 | Determinism | ✅ PASS | No conditional flow, no random values |
| 5 | Isolation & Cleanup | ✅ PASS (+5 bonus) | Context-managed mocks, no shared state |
| 6 | Explicit Assertions | ✅ PASS | Every test has assert statements |
| 7 | Test Length | ⚠️ WARN | 2133 lines (>500), but well-structured with 8 classes |
| 8 | Test Duration | ✅ PASS | ~4ms per test, 0.25s total |
| 9 | Fixture Patterns | ✅ PASS (+5 bonus) | 7 fixtures + helper function |
| 10 | Data Factories | ⚠️ WARN | Some inline hardcoded dicts, could use factory pattern |
| 11 | Network-First | ✅ N/A | Synchronous TestClient, no browser |
| 12 | Flakiness Patterns | ✅ PASS | No flaky patterns detected |

### Issues Found
- 0 Critical
- 0 High
- 2 Medium: file length (2133 lines), some hardcoded inline test data
- 0 Low

### Fixes Applied
- None required — no critical or high severity issues
