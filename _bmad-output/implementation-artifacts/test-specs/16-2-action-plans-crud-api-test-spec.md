TEST SPEC START
story_id: 16-2-action-plans-crud-api
generated: 2026-02-12

test_specifications:

## AC1: Given an authenticated user calls POST /api/v1/action-plans, When the request includes title, description, category, root_cause, corrective_action, asset_id, priority, due_date, Then a new action plan is created with status='open' and the current user as owner, And the response includes the created plan with its ID

### 16-2-action-plans-crud-api-INT-001: Create action plan with all required fields returns 201
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT token
- When: POST /api/v1/action-plans is called with title, description, category='corrective', root_cause, corrective_action, asset_id, priority='high', due_date='2026-03-15'
- Then: Response status is 201, response body includes a generated UUID `id`, status='open', owner_id matches current user's ID, and all submitted fields are echoed back
- Data: Valid ActionPlanCreate payload with all fields populated; mock Supabase insert returning the created record with generated id and timestamps

### 16-2-action-plans-crud-api-INT-002: Create action plan sets status to 'open' regardless of input
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT token
- When: POST /api/v1/action-plans is called with a valid payload (status field is not accepted in create schema)
- Then: The created action plan has status='open', owner_id=current_user.id, and created_at/updated_at are populated
- Data: ActionPlanCreate payload without status field; verify the Supabase insert call includes status='open' and owner_id from JWT sub claim

### 16-2-action-plans-crud-api-INT-003: Create action plan with optional source_followup_id
- Priority: P1
- Type: integration
- Given: An authenticated user and an existing action_followup with a known UUID
- When: POST /api/v1/action-plans is called with a valid payload including source_followup_id
- Then: Response status is 201 and the created plan includes the source_followup_id linking it to the originating followup
- Data: Valid payload with source_followup_id set to a UUID; mock Supabase insert returning record with source_followup_id

### 16-2-action-plans-crud-api-INT-004: Create action plan with minimal fields (only required)
- Priority: P1
- Type: integration
- Given: An authenticated user with a valid JWT token
- When: POST /api/v1/action-plans is called with only the required field (title) and all optional fields omitted
- Then: Response status is 201, the plan is created with defaults (status='open', nullable fields are null)
- Data: Minimal payload with only title; mock Supabase insert returning record with nulls for optional fields

### 16-2-action-plans-crud-api-INT-005: Create action plan fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: POST /api/v1/action-plans is called with a valid payload
- Then: Response status is 401 with appropriate error message
- Data: Valid ActionPlanCreate payload; no Bearer token header

### 16-2-action-plans-crud-api-UNIT-001: ActionPlanCreate schema validates required fields
- Priority: P0
- Type: unit
- Given: An ActionPlanCreate schema instance is being constructed
- When: title is missing from the input data
- Then: Pydantic ValidationError is raised indicating title is required
- Data: Payload missing title field

### 16-2-action-plans-crud-api-UNIT-002: ActionPlanCreate schema validates enum values
- Priority: P1
- Type: unit
- Given: An ActionPlanCreate schema instance is being constructed
- When: category is set to 'invalid_category' (not in ActionPlanCategory enum)
- Then: Pydantic ValidationError is raised for invalid enum value
- Data: Payload with category='invalid_category'

### 16-2-action-plans-crud-api-UNIT-003: ActionPlanCreate schema validates priority enum
- Priority: P1
- Type: unit
- Given: An ActionPlanCreate schema instance is being constructed
- When: priority is set to 'urgent' (not in ActionPlanPriority enum: low, medium, high, critical)
- Then: Pydantic ValidationError is raised for invalid priority value
- Data: Payload with priority='urgent'

### 16-2-action-plans-crud-api-INT-006: Create action plan returns 500 on Supabase error
- Priority: P1
- Type: integration
- Given: An authenticated user, but the Supabase client raises an exception on insert
- When: POST /api/v1/action-plans is called with a valid payload
- Then: Response status is 500 with a descriptive error detail message
- Data: Valid payload; mock Supabase insert to raise an exception

### 16-2-action-plans-crud-api-INT-007: Create action plan uses user-scoped client for RLS enforcement
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT token
- When: POST /api/v1/action-plans is called with a valid payload
- Then: The Supabase client is created with the user's JWT token (not the service role key) so RLS policies enforce owner_id=auth.uid()
- Data: Valid payload; verify create_client is called with the user's Bearer token

## AC2: Given an authenticated user calls GET /api/v1/action-plans, When optional filters are provided (status, asset_id, owner_id, priority), Then matching action plans are returned sorted by priority (critical first) then due_date

### 16-2-action-plans-crud-api-INT-008: List action plans without filters returns all plans sorted
- Priority: P0
- Type: integration
- Given: An authenticated user and multiple action plans exist with varying priorities and due dates
- When: GET /api/v1/action-plans is called without any query parameters
- Then: Response status is 200, all plans are returned in ActionPlanListResponse format with items sorted by priority (critical=0, high=1, medium=2, low=3) then by due_date ascending
- Data: Mock Supabase returning 4 plans with priorities [low, critical, medium, high] and varied due_dates; verify output order is critical, high, medium, low

### 16-2-action-plans-crud-api-INT-009: List action plans filtered by status
- Priority: P0
- Type: integration
- Given: An authenticated user and action plans exist with statuses 'open', 'in_progress', 'completed'
- When: GET /api/v1/action-plans?status=open is called
- Then: Response status is 200, only plans with status='open' are returned
- Data: Mock Supabase .eq('status', 'open') returning filtered results; verify the .eq() call is made with correct parameters

### 16-2-action-plans-crud-api-INT-010: List action plans filtered by asset_id
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist linked to different assets
- When: GET /api/v1/action-plans?asset_id=asset-uuid-123 is called
- Then: Response status is 200, only plans for the specified asset are returned
- Data: Mock Supabase .eq('asset_id', 'asset-uuid-123') returning filtered results

### 16-2-action-plans-crud-api-INT-011: List action plans filtered by owner_id
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist owned by different users
- When: GET /api/v1/action-plans?owner_id=user-uuid-456 is called
- Then: Response status is 200, only plans owned by the specified user are returned
- Data: Mock Supabase .eq('owner_id', 'user-uuid-456') returning filtered results

### 16-2-action-plans-crud-api-INT-012: List action plans filtered by priority
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist with various priorities
- When: GET /api/v1/action-plans?priority=critical is called
- Then: Response status is 200, only plans with priority='critical' are returned
- Data: Mock Supabase .eq('priority', 'critical') returning filtered results

### 16-2-action-plans-crud-api-INT-013: List action plans with multiple filters combined
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist with various combinations of status, asset, owner, and priority
- When: GET /api/v1/action-plans?status=open&priority=high&asset_id=asset-uuid-123 is called
- Then: Response status is 200, only plans matching ALL filters are returned
- Data: Mock Supabase with chained .eq() calls for all three filters

### 16-2-action-plans-crud-api-INT-014: List action plans with pagination (page and page_size)
- Priority: P0
- Type: integration
- Given: An authenticated user and 25 action plans exist
- When: GET /api/v1/action-plans?page=2&page_size=10 is called
- Then: Response status is 200, ActionPlanListResponse contains items (up to 10), total_count=25, page=2, page_size=10
- Data: Mock Supabase returning 25 total records; verify Python-side pagination slices correctly (offset=10, limit=10)

### 16-2-action-plans-crud-api-INT-015: List action plans with default pagination
- Priority: P1
- Type: integration
- Given: An authenticated user and action plans exist
- When: GET /api/v1/action-plans is called without page/page_size parameters
- Then: Response defaults to page=1, page_size=20
- Data: Mock Supabase returning results; verify pagination defaults applied

### 16-2-action-plans-crud-api-INT-016: List action plans sorts by priority then due_date
- Priority: P0
- Type: integration
- Given: An authenticated user and plans exist: Plan A (priority=medium, due_date=2026-03-01), Plan B (priority=critical, due_date=2026-04-01), Plan C (priority=medium, due_date=2026-02-15), Plan D (priority=high, due_date=2026-03-10)
- When: GET /api/v1/action-plans is called
- Then: Plans are returned in order: B (critical), D (high), C (medium, earlier date), A (medium, later date)
- Data: Mock Supabase returning 4 plans in arbitrary order; verify Python-side PRIORITY_SORT_MAP sorting with due_date as secondary sort

### 16-2-action-plans-crud-api-INT-017: List action plans with null due_date sorts last within priority
- Priority: P2
- Type: integration
- Given: An authenticated user and plans exist with same priority but some have null due_date
- When: GET /api/v1/action-plans is called
- Then: Plans with null due_date appear after plans with due_date within the same priority group
- Data: Mock Supabase returning plans with mixed null/non-null due_dates at same priority level

### 16-2-action-plans-crud-api-INT-018: List action plans returns empty list when no matches
- Priority: P1
- Type: integration
- Given: An authenticated user and no action plans match the filters
- When: GET /api/v1/action-plans?status=verified is called
- Then: Response status is 200, items=[], total_count=0
- Data: Mock Supabase returning empty data list

### 16-2-action-plans-crud-api-INT-019: List action plans fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: GET /api/v1/action-plans is called
- Then: Response status is 401
- Data: No Bearer token header

### 16-2-action-plans-crud-api-UNIT-004: PRIORITY_SORT_MAP maps all enum values correctly
- Priority: P1
- Type: unit
- Given: The PRIORITY_SORT_MAP dictionary is defined in schemas
- When: All ActionPlanPriority enum values are looked up
- Then: critical=0, high=1, medium=2, low=3
- Data: Direct assertion on PRIORITY_SORT_MAP values

### 16-2-action-plans-crud-api-INT-020: List action plans validates page_size upper bound
- Priority: P2
- Type: integration
- Given: An authenticated user
- When: GET /api/v1/action-plans?page_size=200 is called (exceeds max of 100)
- Then: Response status is 422 (validation error from FastAPI Query constraint le=100)
- Data: page_size=200 exceeding the Query(ge=1, le=100) constraint

## AC2 (supplemental): GET /api/v1/action-plans/{id} - Get single action plan

### 16-2-action-plans-crud-api-INT-021: Get single action plan by ID
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with a known UUID
- When: GET /api/v1/action-plans/{id} is called with the plan's UUID
- Then: Response status is 200, the full ActionPlanResponse is returned with all fields
- Data: Mock Supabase select returning a single plan record

### 16-2-action-plans-crud-api-INT-022: Get action plan returns 404 for non-existent ID
- Priority: P0
- Type: integration
- Given: An authenticated user
- When: GET /api/v1/action-plans/{id} is called with a UUID that does not exist
- Then: Response status is 404 with detail message indicating plan not found
- Data: Mock Supabase select returning empty data

### 16-2-action-plans-crud-api-INT-023: Get action plan fails without authentication
- Priority: P1
- Type: integration
- Given: No Authorization header is provided
- When: GET /api/v1/action-plans/{id} is called
- Then: Response status is 401
- Data: No Bearer token header

## AC3: Given an action plan owner calls PATCH /api/v1/action-plans/{id}, When the request includes updated fields, Then the plan is updated and an action_plan_updates record is created logging the change

### 16-2-action-plans-crud-api-INT-024: Update action plan with status change creates change log
- Priority: P0
- Type: integration
- Given: An authenticated user who owns an action plan with status='open'
- When: PATCH /api/v1/action-plans/{id} is called with {status: 'in_progress'}
- Then: Response status is 200, the plan's status is updated to 'in_progress', and an action_plan_updates record is created with update_text containing "Status changed from open to in_progress" and status_change="open -> in_progress"
- Data: Mock service-role client returning existing plan with status='open'; mock user-scoped client update succeeding; verify insert into action_plan_updates table

### 16-2-action-plans-crud-api-INT-025: Update action plan with multiple field changes logs all changes
- Priority: P0
- Type: integration
- Given: An authenticated user who owns an action plan
- When: PATCH /api/v1/action-plans/{id} is called with {status: 'in_progress', due_date: '2026-04-01', corrective_action: 'New corrective action'}
- Then: Response status is 200, all fields are updated, and the action_plan_updates record's update_text describes all changed fields
- Data: Mock existing plan with original values; verify the auto-generated update_text mentions all three changes

### 16-2-action-plans-crud-api-INT-026: Update action plan by non-owner returns 403
- Priority: P0
- Type: integration
- Given: An authenticated user who does NOT own the action plan (different owner_id)
- When: PATCH /api/v1/action-plans/{id} is called with updated fields
- Then: Response status is 403 indicating the user is not authorized to update this plan (RLS blocks the update via user-scoped client)
- Data: Mock service-role client returning plan with different owner_id; mock user-scoped client update returning empty data (RLS denial)

### 16-2-action-plans-crud-api-INT-027: Update action plan returns 404 for non-existent ID
- Priority: P0
- Type: integration
- Given: An authenticated user
- When: PATCH /api/v1/action-plans/{id} is called with a non-existent UUID
- Then: Response status is 404 with detail message
- Data: Mock service-role client select returning empty data

### 16-2-action-plans-crud-api-INT-028: Update action plan with empty body returns 422
- Priority: P1
- Type: integration
- Given: An authenticated user who owns an action plan
- When: PATCH /api/v1/action-plans/{id} is called with an empty JSON body {} (no fields set)
- Then: Response status is 422 indicating at least one field must be provided for update
- Data: Empty update payload; model_dump(exclude_unset=True) returns {}

### 16-2-action-plans-crud-api-INT-029: Update action plan with only due_date change creates appropriate log
- Priority: P1
- Type: integration
- Given: An authenticated user who owns an action plan with due_date='2026-03-01'
- When: PATCH /api/v1/action-plans/{id} is called with {due_date: '2026-04-15'}
- Then: Response status is 200, due_date is updated, action_plan_updates record has update_text mentioning the date change and status_change is null (no status change occurred)
- Data: Mock existing plan with due_date='2026-03-01'; verify status_change field is null in the inserted update record

### 16-2-action-plans-crud-api-INT-030: Update action plan fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: PATCH /api/v1/action-plans/{id} is called
- Then: Response status is 401
- Data: No Bearer token header

### 16-2-action-plans-crud-api-INT-031: Update action plan uses two-client pattern
- Priority: P1
- Type: integration
- Given: An authenticated user who owns an action plan
- When: PATCH /api/v1/action-plans/{id} is called with valid updates
- Then: create_client is called twice — once with service role key (for existence check) and once with user JWT token (for the update, enforcing RLS)
- Data: Valid update payload; verify create_client call args for both invocations

## AC4: Given a user calls POST /api/v1/action-plans/{id}/updates, When the request includes update_text and optional status_change, Then a progress update is recorded in action_plan_updates, And if status_change is provided, the plan's status is updated

### 16-2-action-plans-crud-api-INT-032: Add progress update without status change
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with status='open'
- When: POST /api/v1/action-plans/{id}/updates is called with {update_text: 'Investigation completed, root cause identified'}
- Then: Response status is 201, an action_plan_updates record is created with the update_text, author_id=current_user.id, and status_change is null; the plan's status remains 'open'
- Data: Mock plan existence check; mock insert into action_plan_updates; verify no update to action_plans table status

### 16-2-action-plans-crud-api-INT-033: Add progress update with status change updates plan status
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with status='open'
- When: POST /api/v1/action-plans/{id}/updates is called with {update_text: 'Started working on corrective action', status_change: 'in_progress'}
- Then: Response status is 201, action_plan_updates record is created with update_text and status_change='open -> in_progress', AND the action_plans table is updated with status='in_progress'
- Data: Mock plan existence check returning status='open'; mock both insert into action_plan_updates and update of action_plans.status

### 16-2-action-plans-crud-api-INT-034: Add progress update returns 404 for non-existent plan
- Priority: P0
- Type: integration
- Given: An authenticated user
- When: POST /api/v1/action-plans/{id}/updates is called with a non-existent plan UUID
- Then: Response status is 404 with detail message
- Data: Mock Supabase select returning empty data for plan lookup

### 16-2-action-plans-crud-api-INT-035: Add progress update fails without update_text
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan exists
- When: POST /api/v1/action-plans/{id}/updates is called with {} (missing update_text)
- Then: Response status is 422 (Pydantic validation error for missing required field)
- Data: Empty or missing update_text in request body

### 16-2-action-plans-crud-api-INT-036: Add progress update fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: POST /api/v1/action-plans/{id}/updates is called
- Then: Response status is 401
- Data: No Bearer token header

### 16-2-action-plans-crud-api-INT-037: Add progress update with status_change to invalid status returns 422
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan exists
- When: POST /api/v1/action-plans/{id}/updates is called with {update_text: 'text', status_change: 'invalid_status'}
- Then: Response status is 422 (Pydantic validation error for invalid enum value)
- Data: Payload with status_change set to an invalid ActionPlanStatus value

## AC4 (supplemental): GET /api/v1/action-plans/{id}/updates - List progress updates

### 16-2-action-plans-crud-api-INT-038: List progress updates for a plan returns chronological order
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan with multiple progress updates
- When: GET /api/v1/action-plans/{id}/updates is called
- Then: Response status is 200, updates are returned sorted chronologically (oldest first) by created_at
- Data: Mock Supabase returning multiple update records with varying created_at timestamps

### 16-2-action-plans-crud-api-INT-039: List progress updates returns 404 for non-existent plan
- Priority: P1
- Type: integration
- Given: An authenticated user
- When: GET /api/v1/action-plans/{id}/updates is called with a non-existent plan UUID
- Then: Response status is 404
- Data: Mock Supabase select returning empty data for plan lookup

### 16-2-action-plans-crud-api-INT-040: List progress updates returns empty list when no updates exist
- Priority: P2
- Type: integration
- Given: An authenticated user and an action plan exists but has no progress updates
- When: GET /api/v1/action-plans/{id}/updates is called
- Then: Response status is 200, returns empty list
- Data: Mock Supabase returning empty data for updates query

## AC5: Given a user calls POST /api/v1/action-plans/{id}/verify, When the user confirms the fix worked, Then the plan status is set to 'verified', verified_by and verified_at are recorded

### 16-2-action-plans-crud-api-INT-041: Verify completed action plan succeeds
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with status='completed'
- When: POST /api/v1/action-plans/{id}/verify is called (with optional verification_notes)
- Then: Response status is 200, plan status is set to 'verified', verified_by=current_user.id, verified_at is a valid timestamp, and an action_plan_updates record is created logging the verification
- Data: Mock service-role client returning plan with status='completed'; mock service-role update setting verified fields; mock insert into action_plan_updates

### 16-2-action-plans-crud-api-INT-042: Verify action plan returns 400 when status is not 'completed'
- Priority: P0
- Type: integration
- Given: An authenticated user and an action plan exists with status='open'
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 400 with detail message indicating plan must be in 'completed' status to verify
- Data: Mock service-role client returning plan with status='open'

### 16-2-action-plans-crud-api-INT-043: Verify action plan returns 400 when status is 'in_progress'
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan exists with status='in_progress'
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 400 with detail message
- Data: Mock service-role client returning plan with status='in_progress'

### 16-2-action-plans-crud-api-INT-044: Verify action plan returns 404 for non-existent ID
- Priority: P0
- Type: integration
- Given: An authenticated user
- When: POST /api/v1/action-plans/{id}/verify is called with a non-existent UUID
- Then: Response status is 404
- Data: Mock service-role client select returning empty data

### 16-2-action-plans-crud-api-INT-045: Verify action plan can be done by non-owner (cross-user verification)
- Priority: P0
- Type: integration
- Given: An authenticated user who is NOT the owner of the action plan, and the plan has status='completed'
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 200, plan is verified with verified_by set to the current (non-owner) user's ID (uses service-role client to bypass owner-only RLS)
- Data: Mock service-role client returning plan with different owner_id than current user; verify service-role client used for update (not user-scoped)

### 16-2-action-plans-crud-api-INT-046: Verify action plan fails without authentication
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 401
- Data: No Bearer token header

### 16-2-action-plans-crud-api-INT-047: Verify action plan with verification_notes records notes
- Priority: P2
- Type: integration
- Given: An authenticated user and an action plan exists with status='completed'
- When: POST /api/v1/action-plans/{id}/verify is called with {verification_notes: 'Verified fix on production line 3'}
- Then: Response status is 200 and the action_plan_updates record includes the verification notes in its update_text
- Data: Mock service-role client returning completed plan; verify notes appear in the logged update record

### 16-2-action-plans-crud-api-INT-048: Verify already verified plan returns 400
- Priority: P1
- Type: integration
- Given: An authenticated user and an action plan exists with status='verified'
- When: POST /api/v1/action-plans/{id}/verify is called
- Then: Response status is 400 with detail message indicating plan is already verified (or must be in 'completed' status)
- Data: Mock service-role client returning plan with status='verified'

## Schema Validation (Cross-cutting)

### 16-2-action-plans-crud-api-UNIT-005: ActionPlanCategory enum has correct values
- Priority: P1
- Type: unit
- Given: The ActionPlanCategory enum is defined
- When: Enum members are inspected
- Then: Values are exactly 'corrective', 'preventive', 'improvement' matching DB CHECK constraint
- Data: Direct enum value assertions

### 16-2-action-plans-crud-api-UNIT-006: ActionPlanStatus enum has correct values
- Priority: P1
- Type: unit
- Given: The ActionPlanStatus enum is defined
- When: Enum members are inspected
- Then: Values are exactly 'draft', 'open', 'in_progress', 'completed', 'verified' matching DB CHECK constraint
- Data: Direct enum value assertions

### 16-2-action-plans-crud-api-UNIT-007: ActionPlanPriority enum has correct values
- Priority: P1
- Type: unit
- Given: The ActionPlanPriority enum is defined
- When: Enum members are inspected
- Then: Values are exactly 'low', 'medium', 'high', 'critical' matching DB CHECK constraint
- Data: Direct enum value assertions

### 16-2-action-plans-crud-api-UNIT-008: ActionPlanResponse schema includes all expected fields
- Priority: P1
- Type: unit
- Given: The ActionPlanResponse schema is defined
- When: Schema model_fields are inspected
- Then: All fields are present: id, title, description, asset_id, category, root_cause, corrective_action, preventive_action, source_followup_id, owner_id, status, priority, due_date, completed_at, verified_by, verified_at, created_at, updated_at
- Data: Direct schema field inspection

### 16-2-action-plans-crud-api-UNIT-009: ActionPlanListResponse schema includes pagination fields
- Priority: P1
- Type: unit
- Given: The ActionPlanListResponse schema is defined
- When: Schema model_fields are inspected
- Then: Fields include items (list of ActionPlanResponse), total_count, page, page_size
- Data: Direct schema field inspection

### 16-2-action-plans-crud-api-UNIT-010: ActionPlanUpdate schema uses model_dump exclude_unset correctly
- Priority: P1
- Type: unit
- Given: An ActionPlanUpdate instance with only due_date set
- When: model_dump(exclude_unset=True) is called
- Then: Only the due_date field is in the resulting dict (other optional fields are excluded)
- Data: ActionPlanUpdate(due_date='2026-04-01'); verify dict has only 'due_date' key

## Router Registration

### 16-2-action-plans-crud-api-INT-049: Action plans router is registered at correct prefix
- Priority: P0
- Type: integration
- Given: The FastAPI application is initialized
- When: The app's routes are inspected
- Then: Routes exist under the /api/v1/action-plans prefix with all expected methods (GET, POST, PATCH)
- Data: Inspect app.routes for /api/v1/action-plans paths

edge_cases:
  - Action plan with due_date in the past is still accepted (no server-side future-date validation)
  - Concurrent updates to the same action plan (last write wins, no optimistic locking)
  - Very long update_text or description fields (DB TEXT type has no practical limit)
  - Unicode characters in title, description, and update_text fields
  - UUID format validation for asset_id, source_followup_id path parameters
  - Pagination beyond available results (page=100 when only 5 records exist) returns empty items with correct total_count
  - Updating a 'verified' plan back to a different status (no state machine enforcement in this story)

error_scenarios:
  - Supabase connection failure on any endpoint returns 500
  - Expired JWT token returns 401
  - Invalid JWT token returns 401
  - Malformed UUID in path parameter returns 422
  - Request body with extra fields rejected (ConfigDict extra="forbid") returns 422
  - RLS policy denial on update by non-owner returns 403
  - Empty PATCH body returns 422
  - Verify on non-completed plan returns 400
  - Non-existent plan ID on GET/PATCH/POST updates/verify returns 404

test_file_mapping:
  - 16-2-action-plans-crud-api-INT-*: apps/api/tests/test_action_plans_api.py
  - 16-2-action-plans-crud-api-UNIT-*: apps/api/tests/test_action_plans_api.py
  - 16-2-action-plans-crud-api-E2E-*: apps/api/tests/test_action_plans_api.py

TEST SPEC END
