TEST SPEC START
story_id: 13-3-followup-status-updates-rls
generated: 2026-02-11

test_specifications:

## AC1: Assignee can update follow-up status — Given an assignee is authenticated and has follow-ups assigned to them, when they call PATCH /api/v1/followups/{followup_id} with status and optional note, then the follow-up status is updated in action_followups, the updated_at timestamp is refreshed, and only the fields provided are updated (partial update).

### 13-3-followup-status-updates-rls-UNIT-001: Successful full status update by assignee
- Priority: P0
- Type: unit
- Given: An authenticated user (user_id=sub from JWT) has a follow-up assigned to them (assigned_to = user_id) with status "assigned"
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{"status": "in_progress", "note": "Working on this now"}`
- Then: Response is 200, response body contains the updated follow-up with status="in_progress", note="Working on this now", updated_at is refreshed, and all other FollowUpResponse fields (id, action_item_id, action_summary, asset_name, assigned_to, assigned_by, report_date, created_at) are present
- Data: Mock Supabase client returning updated follow-up record; mock_verify_jwt fixture with valid JWT payload; follow-up record with assigned_to matching JWT sub claim

### 13-3-followup-status-updates-rls-UNIT-002: Partial update with status only
- Priority: P0
- Type: unit
- Given: An authenticated assignee has a follow-up assigned to them with status "assigned" and note "Initial note"
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{"status": "resolved"}`
- Then: Response is 200, the Supabase update call only includes `{"status": "resolved"}` (note is NOT included in the update dict via model_dump(exclude_unset=True)), and the response contains the full follow-up record with status="resolved" and the original note preserved
- Data: Mock Supabase client; verify that .update() is called with only the status field, not note

### 13-3-followup-status-updates-rls-UNIT-003: Partial update with note only
- Priority: P0
- Type: unit
- Given: An authenticated assignee has a follow-up assigned to them with status "in_progress"
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{"note": "Still investigating root cause"}`
- Then: Response is 200, the Supabase update call only includes `{"note": "Still investigating root cause"}` (status is NOT included), and the response contains the full follow-up record with the original status preserved
- Data: Mock Supabase client; verify .update() is called with only the note field

### 13-3-followup-status-updates-rls-UNIT-004: Endpoint requires authentication
- Priority: P0
- Type: unit
- Given: No authentication token is provided
- When: PATCH /api/v1/actions/followups/{followup_id} is called without Authorization header
- Then: Response is 401 Unauthorized
- Data: No JWT mock; use mock_verify_jwt_invalid or no mock at all

### 13-3-followup-status-updates-rls-UNIT-005: Validation rejects invalid status values
- Priority: P0
- Type: unit
- Given: An authenticated assignee
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{"status": "completed"}`
- Then: Response is 422 Unprocessable Entity with validation error indicating status must be one of: assigned, in_progress, resolved
- Data: No Supabase call should be made; Pydantic field_validator should reject before reaching endpoint logic

### 13-3-followup-status-updates-rls-UNIT-006: Validation rejects empty update body
- Priority: P1
- Type: unit
- Given: An authenticated assignee
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{}`
- Then: Response is 422 Unprocessable Entity indicating at least one field (status or note) must be provided
- Data: Empty body; endpoint should check model_dump(exclude_unset=True) is non-empty before proceeding

### 13-3-followup-status-updates-rls-UNIT-007: Status transition from assigned to in_progress
- Priority: P1
- Type: unit
- Given: An authenticated assignee has a follow-up with status "assigned"
- When: They call PATCH with `{"status": "in_progress"}`
- Then: Response is 200, status is updated to "in_progress"
- Data: Mock Supabase returning updated record with status="in_progress"

### 13-3-followup-status-updates-rls-UNIT-008: Status transition from in_progress to resolved
- Priority: P1
- Type: unit
- Given: An authenticated assignee has a follow-up with status "in_progress"
- When: They call PATCH with `{"status": "resolved"}`
- Then: Response is 200, status is updated to "resolved"
- Data: Mock Supabase returning updated record with status="resolved"

### 13-3-followup-status-updates-rls-UNIT-009: Status can be set back to assigned
- Priority: P2
- Type: unit
- Given: An authenticated assignee has a follow-up with status "in_progress"
- When: They call PATCH with `{"status": "assigned"}`
- Then: Response is 200, status is updated to "assigned" (no enforced forward-only transitions)
- Data: Mock Supabase returning updated record with status="assigned"

### 13-3-followup-status-updates-rls-UNIT-010: Update with both status and note simultaneously
- Priority: P1
- Type: unit
- Given: An authenticated assignee has a follow-up with status "assigned" and no note
- When: They call PATCH with `{"status": "resolved", "note": "Issue was resolved by replacing the valve"}`
- Then: Response is 200, both fields are updated, Supabase .update() is called with both status and note in the update dict
- Data: Mock Supabase returning updated record with both fields

### 13-3-followup-status-updates-rls-UNIT-011: FollowUpUpdateRequest schema validates correctly
- Priority: P1
- Type: unit
- Given: Various input payloads for FollowUpUpdateRequest
- When: Pydantic model is constructed with valid statuses ("assigned", "in_progress", "resolved"), None status, invalid status ("pending", "done", ""), and optional note
- Then: Valid statuses pass validation, None status is allowed (optional field), invalid statuses raise ValidationError with descriptive message
- Data: Direct Pydantic model instantiation tests

### 13-3-followup-status-updates-rls-UNIT-012: FollowUpResponse schema serializes correctly
- Priority: P1
- Type: unit
- Given: A raw follow-up record dict from Supabase with all fields populated
- When: FollowUpResponse is constructed from the dict
- Then: All fields (id, action_item_id, action_summary, asset_name, category, assigned_to, assigned_by, status, note, report_date, created_at, updated_at) are correctly serialized, and optional fields (asset_name, category, note) handle None values
- Data: Sample follow-up record dicts with various field combinations

## AC2: RLS denies unauthorized updates — Given an assignee tries to update a follow-up not assigned to them, when the update request is made, then the request is denied with 403 (RLS enforcement).

### 13-3-followup-status-updates-rls-UNIT-013: 403 when non-assignee tries to update (RLS blocks)
- Priority: P0
- Type: unit
- Given: An authenticated user (user_id=A) attempts to update a follow-up that is assigned_to user_id=B (a different user)
- When: They call PATCH /api/v1/actions/followups/{followup_id} with `{"status": "resolved"}`
- Then: Response is 403 Forbidden. The service-role SELECT found the follow-up (it exists), but the user-scoped UPDATE returned 0 rows (RLS blocked), so the endpoint correctly returns 403
- Data: Mock service-role Supabase client returning the follow-up on SELECT (exists check); mock user-scoped Supabase client returning empty data on UPDATE (RLS denial)

### 13-3-followup-status-updates-rls-UNIT-014: 404 when follow-up does not exist
- Priority: P0
- Type: unit
- Given: An authenticated user attempts to update a follow-up with an ID that does not exist in the database
- When: They call PATCH /api/v1/actions/followups/{followup_id} with `{"status": "in_progress"}`
- Then: Response is 404 Not Found. The service-role SELECT returned no rows, indicating the follow-up does not exist
- Data: Mock service-role Supabase client returning empty data on SELECT (not found)

### 13-3-followup-status-updates-rls-UNIT-015: User-scoped Supabase client is used for update (not service role)
- Priority: P0
- Type: unit
- Given: An authenticated assignee with a valid JWT token
- When: They call PATCH /api/v1/actions/followups/{followup_id}
- Then: The update operation uses a Supabase client initialized with the user's JWT token (not the service role key), ensuring RLS policies are enforced at the database level
- Data: Verify the user-scoped client creation is called with the user's token; verify service-role client is NOT used for the update call

### 13-3-followup-status-updates-rls-INT-001: RLS migration adds correct assignee update policy
- Priority: P0
- Type: integration
- Given: The migration 0028_followup_assignee_rls.sql has been applied
- When: The policy is inspected
- Then: A new RLS policy "Assignees can update their own followups" exists on action_followups for UPDATE command, with USING clause `(assigned_to = auth.uid())` and WITH CHECK clause `(assigned_to = auth.uid())`
- Data: SQL migration file content validation

### 13-3-followup-status-updates-rls-INT-002: RLS migration preserves existing policies
- Priority: P0
- Type: integration
- Given: The migration 0028_followup_assignee_rls.sql is applied on top of existing 0025 migration
- When: All RLS policies on action_followups are listed
- Then: All existing policies remain intact: SELECT for assigned_to/assigned_by, INSERT for assigned_by, UPDATE for assigned_by (assigner), ALL for service_role — AND the new UPDATE for assigned_to (assignee) is added alongside them
- Data: Migration only contains CREATE POLICY, no DROP or ALTER POLICY statements

### 13-3-followup-status-updates-rls-INT-003: WITH CHECK prevents assignee field reassignment
- Priority: P1
- Type: integration
- Given: The RLS policy has WITH CHECK (assigned_to = auth.uid())
- When: An assignee attempts to update the assigned_to field to a different user ID via the PATCH endpoint
- Then: The database rejects the update because WITH CHECK ensures assigned_to still equals auth.uid() after the update — preventing reassignment
- Data: Attempt to include assigned_to in the update payload (should be rejected either by schema validation or WITH CHECK constraint)

### 13-3-followup-status-updates-rls-E2E-001: Assignee update blocked, assigner update allowed on same follow-up
- Priority: P1
- Type: e2e
- Given: A follow-up exists with assigned_to=UserA and assigned_by=UserB
- When: UserC (neither assignee nor assigner) attempts PATCH with `{"status": "resolved"}`
- Then: UserC receives 403 Forbidden; confirming that only UserA (assignee) and UserB (assigner) can update the record
- Data: Three distinct user JWTs; follow-up record linking UserA and UserB

## AC3: Manager sees updated follow-up status — Given a manager queries follow-ups they created, when the follow-up has been updated by the assignee, then the response includes the current status and the assignee's note.

### 13-3-followup-status-updates-rls-UNIT-016: FollowUpResponse includes status and note after assignee update
- Priority: P0
- Type: unit
- Given: An assignee has updated a follow-up to status="resolved" with note="Fixed the alignment issue"
- When: The PATCH endpoint returns the updated record
- Then: The FollowUpResponse includes status="resolved" and note="Fixed the alignment issue", along with all other fields (id, action_item_id, action_summary, asset_name, assigned_to, assigned_by, report_date, created_at, updated_at)
- Data: Mock Supabase returning the complete updated record with status and note populated

### 13-3-followup-status-updates-rls-UNIT-017: Response includes updated_at timestamp reflecting the update time
- Priority: P1
- Type: unit
- Given: An assignee updates a follow-up's status
- When: The PATCH endpoint returns the updated record
- Then: The updated_at field in the response reflects a recent timestamp (updated by the database trigger), different from created_at
- Data: Mock Supabase returning record where updated_at > created_at

### 13-3-followup-status-updates-rls-INT-004: Existing SELECT RLS allows manager to read updated follow-ups
- Priority: P1
- Type: integration
- Given: The existing SELECT RLS policy allows users to read follow-ups where assigned_by = auth.uid()
- When: A manager (assigned_by) queries follow-ups after an assignee has updated status and note
- Then: The manager sees the current status and note values as updated by the assignee — no additional code changes needed for this, just confirming existing SELECT policy handles it
- Data: Verify the existing RLS SELECT policy from migration 0025 permits this read pattern

### 13-3-followup-status-updates-rls-UNIT-018: Response includes action context fields for manager visibility
- Priority: P1
- Type: unit
- Given: A follow-up has been updated by the assignee
- When: The response is serialized via FollowUpResponse
- Then: The response includes action_summary and asset_name fields so the manager can identify which action item the follow-up relates to without needing a separate query
- Data: Mock record with action_summary="Check valve pressure on Line 3" and asset_name="Line 3 Assembly"

edge_cases:
  - Follow-up ID is not a valid UUID format — should return 422 validation error
  - Note field contains very long text (e.g., 10,000+ characters) — should either accept or have a documented max length
  - Status is provided as null explicitly ({"status": null}) vs not provided at all — model_dump(exclude_unset=True) should handle this correctly
  - Concurrent updates by both assignee and assigner on the same follow-up — last-write-wins, updated_at reflects latest
  - Follow-up ID contains SQL injection attempt — Supabase client parameterization prevents injection
  - JWT token is expired mid-request — should return 401 not 500
  - Supabase service is temporarily unavailable during update — should return 500/502 with appropriate error message

error_scenarios:
  - 401 Unauthorized: Missing or invalid JWT token
  - 403 Forbidden: Authenticated user is not the assignee (RLS blocks update)
  - 404 Not Found: Follow-up ID does not exist in the database
  - 422 Unprocessable Entity: Invalid status value (not in allowed enum)
  - 422 Unprocessable Entity: Empty update body (no fields provided)
  - 500 Internal Server Error: Supabase client connection failure or unexpected database error

test_file_mapping:
  - 13-3-followup-status-updates-rls-UNIT-*: apps/api/tests/test_followup_update.py
  - 13-3-followup-status-updates-rls-INT-*: apps/api/tests/test_followup_update.py
  - 13-3-followup-status-updates-rls-E2E-*: apps/api/tests/test_followup_update.py

TEST SPEC END
