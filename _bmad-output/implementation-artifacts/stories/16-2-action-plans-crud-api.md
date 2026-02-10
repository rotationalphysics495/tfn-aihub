# Story 16.2: Action Plans CRUD API

Status: ready-for-dev

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
