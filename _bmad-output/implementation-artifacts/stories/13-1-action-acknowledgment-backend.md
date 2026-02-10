# Story 13.1: Action Acknowledgment Backend

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to mark action items as reviewed/completed with the acknowledgment persisted**,
so that **there's a record of what I've seen and addressed, turning the morning report from a disposable newspaper into an accountability system**.

## Acceptance Criteria

1. **Acknowledge Endpoint**
   - Given an authenticated user sends `POST /api/v1/actions/{action_id}/acknowledge`
   - When the request includes an optional `note` (text body)
   - Then a record is created in `action_acknowledgments` with:
     - `action_item_id` (the action being acknowledged, TEXT matching the action engine's generated ID format `action-{category}-{hex12}`)
     - `user_id` (who acknowledged it, UUID from JWT `sub` claim)
     - `acknowledged_at` (server-side TIMESTAMPTZ, not client-provided)
     - `note` (optional text from request body)
     - `report_date` (DATE, derived from the action item's report context or request parameter)
   - And the response returns HTTP 201 with the created acknowledgment record (JSON)

2. **Upsert Behavior (Idempotent Re-acknowledge)**
   - Given an action item has already been acknowledged by this user for this report_date
   - When the acknowledge endpoint is called again
   - Then the existing acknowledgment is updated (upsert on unique constraint)
   - And the `acknowledged_at` timestamp is refreshed to current server time
   - And the `note` is updated if provided (or preserved if not)
   - And the response returns HTTP 200 with the updated record

3. **Daily Actions Enrichment**
   - Given the daily actions endpoint `GET /api/v1/actions/daily` is called
   - When acknowledged action items exist for the requested report date and the current user
   - Then each `ActionItem` in the response includes an `acknowledgment` field containing:
     - `acknowledged_by` (user_id)
     - `acknowledged_at` (ISO 8601 timestamp)
     - `note` (text or null)
   - And unacknowledged items have `acknowledgment: null`

4. **Authentication Required**
   - Given an unauthenticated request to the acknowledge endpoint
   - When no valid Bearer token is provided
   - Then the response is HTTP 401 Unauthorized

5. **RLS Enforcement**
   - Given RLS is enabled on `action_acknowledgments`
   - When an authenticated user queries acknowledgments
   - Then they can only read/write their own acknowledgment records
   - And the service role has full access for administrative operations

## Tasks / Subtasks

- [ ] Task 1: Create database migration (AC: #1, #2, #5)
  - [ ] 1.1 Create `supabase/migrations/0027_action_acknowledgments.sql`
  - [ ] 1.2 Define `action_acknowledgments` table with columns: `id` (UUID PK), `action_item_id` (TEXT NOT NULL), `user_id` (UUID NOT NULL REFERENCES auth.users), `acknowledged_at` (TIMESTAMPTZ DEFAULT NOW()), `note` (TEXT), `report_date` (DATE NOT NULL), `created_at` (TIMESTAMPTZ DEFAULT NOW()), `updated_at` (TIMESTAMPTZ DEFAULT NOW())
  - [ ] 1.3 Add UNIQUE constraint on `(action_item_id, user_id, report_date)`
  - [ ] 1.4 Add indexes: `idx_action_ack_user_id`, `idx_action_ack_report_date`, `idx_action_ack_action_item_id`
  - [ ] 1.5 Add `update_updated_at_column()` trigger (reuse existing function from other migrations)
  - [ ] 1.6 Enable RLS and create policies:
    - SELECT: `authenticated` users WHERE `user_id = auth.uid()`
    - INSERT: `authenticated` users WITH CHECK `user_id = auth.uid()`
    - UPDATE: `authenticated` users USING `user_id = auth.uid()`
    - ALL: `service_role` full access

- [ ] Task 2: Create acknowledgment Pydantic schemas (AC: #1, #2, #3)
  - [ ] 2.1 Add `AcknowledgmentCreate` schema to `apps/api/app/schemas/action.py` with fields: `note` (Optional[str])
  - [ ] 2.2 Add `AcknowledgmentResponse` schema with fields: `id` (UUID), `action_item_id` (str), `user_id` (str), `acknowledged_at` (datetime), `note` (Optional[str]), `report_date` (date)
  - [ ] 2.3 Add `AcknowledgmentInfo` schema (lightweight, for embedding in ActionItem): `acknowledged_by` (str), `acknowledged_at` (datetime), `note` (Optional[str])
  - [ ] 2.4 Add `acknowledgment` field (Optional[AcknowledgmentInfo]) to the existing `ActionItem` model with default `None`

- [ ] Task 3: Add acknowledge endpoint to actions router (AC: #1, #2, #4)
  - [ ] 3.1 Add `POST /api/v1/actions/{action_id}/acknowledge` endpoint in `apps/api/app/api/actions.py`
  - [ ] 3.2 Accept `AcknowledgmentCreate` as request body and `report_date` as optional query param (defaults to T-1)
  - [ ] 3.3 Use `get_current_user` dependency for auth (existing pattern)
  - [ ] 3.4 Implement upsert via Supabase `.upsert()` with `on_conflict='action_item_id,user_id,report_date'`
  - [ ] 3.5 Return 201 for new acknowledgments, 200 for updates
  - [ ] 3.6 Add proper error handling and logging

- [ ] Task 4: Enrich action items with acknowledgment status (AC: #3)
  - [ ] 4.1 Add `_load_acknowledgments()` method to `ActionEngine` class in `apps/api/app/services/action_engine.py`
  - [ ] 4.2 Query `action_acknowledgments` for the given `report_date` and `user_id`
  - [ ] 4.3 Build a lookup dict mapping `action_item_id` -> `AcknowledgmentInfo`
  - [ ] 4.4 In `generate_action_list()`, accept optional `user_id` parameter
  - [ ] 4.5 After merging actions, enrich each `ActionItem.acknowledgment` field from the lookup dict
  - [ ] 4.6 Pass `current_user.id` from the API endpoint to `generate_action_list()`

- [ ] Task 5: Write tests (AC: #1-5)
  - [ ] 5.1 Add tests in `apps/api/tests/test_actions_api.py` for the acknowledge endpoint (201 create, 200 upsert, 401 unauth)
  - [ ] 5.2 Add tests in `apps/api/tests/test_action_engine.py` for acknowledgment enrichment logic
  - [ ] 5.3 Test that `acknowledgment` field is null when no acknowledgment exists
  - [ ] 5.4 Test that `acknowledgment` field is populated when acknowledgment exists

## Dev Notes

### Architecture Patterns

- **API Framework:** FastAPI 0.109+ with async endpoints
- **Database:** Supabase (PostgreSQL) via `supabase-py 2.0+`
- **Auth:** JWT Bearer tokens via Supabase Auth; use `get_current_user` dependency from `app.core.security`
- **Models:** Pydantic V2 with `BaseModel`, `ConfigDict`, and `Field`
- **Testing:** pytest with `unittest.mock` (patch, MagicMock, AsyncMock)

### Database Design

The `action_acknowledgments` table follows the same patterns established by `action_followups` (migration 0025):
- UUID primary key with `gen_random_uuid()`
- `user_id` as UUID FK to `auth.users(id)` with CASCADE DELETE
- `report_date` DATE column for day-scoped queries
- `created_at` / `updated_at` TIMESTAMPTZ with auto-trigger
- RLS policies matching the `action_followups` pattern (user can read/write own records, service_role full access)

**Key difference from `action_followups`:** The acknowledgment table uses `action_item_id` as TEXT (not UUID) because action item IDs are generated at runtime by the ActionEngine (format: `action-{category}-{hex12}`) and are not database-persisted entities. The unique constraint ensures one acknowledgment per user per action per day.

### Existing Code Patterns to Follow

**Router pattern** (from `apps/api/app/api/actions.py`):
```python
from app.core.security import get_current_user
from app.models.user import CurrentUser

@router.post("/{action_id}/acknowledge")
async def acknowledge_action(
    action_id: str,
    body: AcknowledgmentCreate,
    report_date: Optional[date] = Query(None, alias="date"),
    current_user: CurrentUser = Depends(get_current_user),
):
```

**Supabase upsert pattern:**
```python
client = self._get_client()
result = client.table("action_acknowledgments").upsert(
    {
        "action_item_id": action_id,
        "user_id": current_user.id,
        "report_date": report_date.isoformat(),
        "note": body.note,
        "acknowledged_at": datetime.utcnow().isoformat(),
    },
    on_conflict="action_item_id,user_id,report_date"
).execute()
```

**ActionEngine enrichment pattern** (follow the existing `_load_assets()` / `_load_shift_targets()` caching pattern):
```python
async def _load_acknowledgments(
    self, report_date: date, user_id: str
) -> Dict[str, dict]:
    client = self._get_client()
    response = client.table("action_acknowledgments").select("*") \
        .eq("report_date", report_date.isoformat()) \
        .eq("user_id", user_id) \
        .execute()
    return {
        row["action_item_id"]: AcknowledgmentInfo(
            acknowledged_by=row["user_id"],
            acknowledged_at=row["acknowledged_at"],
            note=row.get("note"),
        )
        for row in (response.data or [])
    }
```

### Migration Pattern Reference

Follow the `0025_action_followups.sql` migration exactly for:
- Table creation syntax
- Index naming convention (`idx_{table}_{column}`)
- Trigger reuse (`update_updated_at_column()` function already exists)
- RLS policy naming convention (descriptive English sentences)
- Service role full access policy

### Critical Guardrails

- **DO NOT** modify the existing `ActionItem` schema fields or break backward compatibility. The new `acknowledgment` field MUST be `Optional` with default `None` so existing consumers are unaffected.
- **DO NOT** change the action engine's caching behavior. Acknowledgments are user-specific and should NOT be cached in the action list cache (which is shared across users). Query acknowledgments separately per-request.
- **DO NOT** create a separate router file. Add the endpoint directly to the existing `apps/api/app/api/actions.py` router, which is already mounted at both `/api/actions` and `/api/v1/actions`.
- **DO** use server-side timestamps for `acknowledged_at` (not client-provided) to ensure audit trail integrity.
- **DO** handle the upsert gracefully -- Supabase's `.upsert()` with `on_conflict` handles both insert and update in a single call.
- **DO** pass `user_id` through to the action engine only for enrichment, not for filtering actions. All users see the same action items; acknowledgments are per-user overlays.

### API Endpoint Design

```
POST /api/v1/actions/{action_id}/acknowledge
  Headers: Authorization: Bearer {jwt_token}
  Query: ?date=2026-02-09  (optional, defaults to T-1)
  Body: { "note": "Reviewed with team, assigning Carlos" }  (note is optional)

  Response 201 (new):
  {
    "id": "uuid",
    "action_item_id": "action-safety-abc123def456",
    "user_id": "user-uuid",
    "acknowledged_at": "2026-02-10T14:30:00Z",
    "note": "Reviewed with team, assigning Carlos",
    "report_date": "2026-02-09"
  }

  Response 200 (upsert):
  Same shape, with updated acknowledged_at and note
```

### Action Engine Changes (generate_action_list)

The `generate_action_list()` method signature changes to accept an optional `user_id`:

```python
async def generate_action_list(
    self,
    target_date: Optional[date] = None,
    limit: Optional[int] = None,
    category_filter: Optional[ActionCategory] = None,
    use_cache: bool = True,
    config_override: Optional[ActionEngineConfig] = None,
    user_id: Optional[str] = None,  # NEW: for acknowledgment enrichment
) -> ActionListResponse:
```

After the merge step, if `user_id` is provided, load acknowledgments and enrich each action:
```python
if user_id:
    ack_map = await self._load_acknowledgments(target_date, user_id)
    for action in merged:
        action.acknowledgment = ack_map.get(action.id)
```

**Important:** The action list cache key should NOT include `user_id` since the base action list is the same for all users. Acknowledgment enrichment happens AFTER cache retrieval.

### Project Structure Notes

```
supabase/migrations/
  0025_action_followups.sql          # REFERENCE - follow this pattern exactly
  0027_action_acknowledgments.sql    # CREATE - new migration

apps/api/app/
  api/
    actions.py                       # MODIFY - add POST /{action_id}/acknowledge endpoint
  schemas/
    action.py                        # MODIFY - add Acknowledgment schemas, add field to ActionItem
  services/
    action_engine.py                 # MODIFY - add _load_acknowledgments(), update generate_action_list()

apps/api/tests/
  test_actions_api.py                # MODIFY - add acknowledge endpoint tests
  test_action_engine.py              # MODIFY - add acknowledgment enrichment tests
```

### Testing Guidance

**Unit Tests (mock Supabase calls):**

```python
# Test acknowledge endpoint - new acknowledgment
@pytest.mark.asyncio
async def test_acknowledge_action_creates_record(client, mock_supabase):
    mock_supabase.table().upsert().execute.return_value = MagicMock(
        data=[{"id": "ack-uuid", "action_item_id": "action-safety-abc", ...}]
    )
    response = await client.post(
        "/api/v1/actions/action-safety-abc/acknowledge",
        json={"note": "Reviewed"},
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 201

# Test unauthenticated request
async def test_acknowledge_requires_auth(client):
    response = await client.post("/api/v1/actions/action-safety-abc/acknowledge")
    assert response.status_code in (401, 403)

# Test enrichment in action list
async def test_action_list_includes_acknowledgment(mock_engine):
    # Setup: mock acknowledgment exists for one action
    # Assert: that action has acknowledgment field populated
    # Assert: other actions have acknowledgment = None
```

**Follow the existing test patterns in `test_actions_api.py`:** Use `@pytest.fixture` for mock engine, `patch` for Supabase client, and test both success and error paths.

### References

- [Source: _bmad-output/planning-artifacts/epic-13.md#Story 13.1] - Story requirements, acceptance criteria, and file list
- [Source: docs/improvements.md#Action item acknowledgment flow] - Product context, proposed approach, and open questions
- [Source: supabase/migrations/0025_action_followups.sql] - Reference migration pattern for table creation, indexes, triggers, and RLS
- [Source: apps/api/app/api/actions.py] - Existing actions router to extend with acknowledge endpoint
- [Source: apps/api/app/schemas/action.py] - Existing ActionItem and related schemas to extend
- [Source: apps/api/app/services/action_engine.py] - ActionEngine class to add acknowledgment loading/enrichment
- [Source: apps/api/app/core/security.py#get_current_user] - Auth dependency pattern for protected endpoints
- [Source: apps/api/app/models/user.py#CurrentUser] - User model returned by auth dependency
- [Source: apps/api/tests/test_actions_api.py] - Existing test patterns for action endpoints
- [Source: docs/architecture-api.md] - API directory structure and technology stack
- [Source: docs/data-models.md] - Database schema patterns and RLS conventions

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
