TEST SPEC START
story_id: 13-1-action-acknowledgment-backend
generated: 2026-02-11

test_specifications:

## AC1: Acknowledge Endpoint

### 13-1-action-acknowledgment-backend-INT-001: Create acknowledgment with note
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT Bearer token
- When: The user sends `POST /api/v1/actions/action-safety-abc123def456/acknowledge` with body `{"note": "Reviewed with team, assigning Carlos"}` and query `?date=2026-02-09`
- Then: A record is created in `action_acknowledgments` via Supabase `.upsert()` with `action_item_id = "action-safety-abc123def456"`, `user_id` from JWT `sub` claim, server-side `acknowledged_at`, `note = "Reviewed with team, assigning Carlos"`, and `report_date = "2026-02-09"`
- And: The response returns HTTP 201 with the created acknowledgment record as JSON containing `id` (UUID), `action_item_id`, `user_id`, `acknowledged_at` (ISO 8601), `note`, and `report_date`
- Data: Valid JWT with `sub = "123e4567-e89b-12d3-a456-426614174000"`, action_id matching format `action-{category}-{hex12}`, Supabase upsert mock returning the created row

### 13-1-action-acknowledgment-backend-INT-002: Create acknowledgment without note
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT Bearer token
- When: The user sends `POST /api/v1/actions/action-oee-def456abc123/acknowledge` with empty body `{}` (no note provided)
- Then: A record is created with `note = null`
- And: The response returns HTTP 201 with the created acknowledgment record where `note` is null
- Data: Valid JWT, action_id `action-oee-def456abc123`, Supabase upsert mock returning row with `note: null`

### 13-1-action-acknowledgment-backend-INT-003: Report date defaults to T-1 when not provided
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT Bearer token and today is 2026-02-11
- When: The user sends `POST /api/v1/actions/action-safety-abc123def456/acknowledge` without the `date` query parameter
- Then: The `report_date` used in the upsert call defaults to yesterday (2026-02-10)
- And: The response returns HTTP 201 with `report_date = "2026-02-10"`
- Data: Valid JWT, no date query param, Supabase upsert mock

### 13-1-action-acknowledgment-backend-INT-004: Server-side timestamp used for acknowledged_at
- Priority: P1
- Type: integration
- Given: An authenticated user with a valid JWT Bearer token
- When: The user sends `POST /api/v1/actions/action-safety-abc123def456/acknowledge`
- Then: The `acknowledged_at` field in the upsert payload is set to a server-side UTC timestamp (not client-provided)
- And: The response `acknowledged_at` reflects the server timestamp
- Data: Valid JWT, verify that `acknowledged_at` in the Supabase `.upsert()` call arguments is a server-generated datetime

### 13-1-action-acknowledgment-backend-INT-005: User ID extracted from JWT sub claim
- Priority: P1
- Type: integration
- Given: An authenticated user with JWT containing `sub = "user-uuid-abc-123"`
- When: The user sends `POST /api/v1/actions/action-financial-111222333444/acknowledge`
- Then: The `user_id` in the upsert payload matches the JWT `sub` claim value `"user-uuid-abc-123"`
- Data: JWT with specific sub claim, verify upsert arguments contain correct user_id

### 13-1-action-acknowledgment-backend-UNIT-001: AcknowledgmentCreate schema validates correctly
- Priority: P1
- Type: unit
- Given: The `AcknowledgmentCreate` Pydantic schema
- When: Instantiated with `{"note": "Some note"}`
- Then: The schema validates successfully with `note = "Some note"`
- Data: `{"note": "Some note"}`

### 13-1-action-acknowledgment-backend-UNIT-002: AcknowledgmentCreate schema allows empty body
- Priority: P1
- Type: unit
- Given: The `AcknowledgmentCreate` Pydantic schema
- When: Instantiated with `{}` (no note)
- Then: The schema validates successfully with `note = None`
- Data: `{}`

### 13-1-action-acknowledgment-backend-UNIT-003: AcknowledgmentResponse schema has all required fields
- Priority: P1
- Type: unit
- Given: The `AcknowledgmentResponse` Pydantic schema
- When: Instantiated with `id`, `action_item_id`, `user_id`, `acknowledged_at`, `note`, `report_date`
- Then: All fields are present and correctly typed (id: UUID, action_item_id: str, user_id: str, acknowledged_at: datetime, note: Optional[str], report_date: date)
- Data: Complete set of acknowledgment fields with valid types

### 13-1-action-acknowledgment-backend-INT-006: Acknowledge endpoint returns correct JSON structure
- Priority: P0
- Type: integration
- Given: An authenticated user sends a successful acknowledge request
- When: The Supabase upsert returns the created record
- Then: The response JSON contains exactly the fields: `id`, `action_item_id`, `user_id`, `acknowledged_at`, `note`, `report_date`
- And: `acknowledged_at` is in ISO 8601 format
- And: `report_date` is in `YYYY-MM-DD` format
- Data: Mock Supabase response with complete row data

## AC2: Upsert Behavior (Idempotent Re-acknowledge)

### 13-1-action-acknowledgment-backend-INT-007: Re-acknowledge updates existing record (upsert)
- Priority: P0
- Type: integration
- Given: An action item `action-safety-abc123def456` has already been acknowledged by user `user-uuid` for report_date `2026-02-09`
- When: The same user sends `POST /api/v1/actions/action-safety-abc123def456/acknowledge` again with `?date=2026-02-09` and `{"note": "Updated note"}`
- Then: The existing acknowledgment is updated (via Supabase `.upsert()` with `on_conflict="action_item_id,user_id,report_date"`)
- And: The response returns HTTP 200 (not 201) with the updated record
- And: The `acknowledged_at` timestamp is refreshed to the current server time
- And: The `note` is updated to `"Updated note"`
- Data: Supabase upsert mock returning the updated row; pre-check SELECT returns existing record

### 13-1-action-acknowledgment-backend-INT-008: Re-acknowledge preserves note when not provided
- Priority: P1
- Type: integration
- Given: An existing acknowledgment with `note = "Original note"` for user `user-uuid`, action `action-safety-abc123`, report_date `2026-02-09`
- When: The user re-acknowledges with an empty body `{}` (no note field)
- Then: The existing `note` is preserved (or the behavior matches the design — if the upsert sends `note: null`, the note may be cleared; verify expected behavior)
- And: The `acknowledged_at` timestamp is refreshed
- And: The response returns HTTP 200
- Data: Existing acknowledgment mock, upsert with `note: None`

### 13-1-action-acknowledgment-backend-INT-009: 201 vs 200 status differentiation
- Priority: P0
- Type: integration
- Given: The acknowledge endpoint distinguishes between new and updated acknowledgments
- When: A first-time acknowledgment is created
- Then: The response status is 201 (Created)
- When: The same acknowledgment is re-submitted (same action_id, user_id, report_date)
- Then: The response status is 200 (OK)
- Data: Two sequential requests; first with no pre-existing record (SELECT returns empty), second with pre-existing record (SELECT returns a row)

### 13-1-action-acknowledgment-backend-UNIT-004: Upsert uses correct on_conflict columns
- Priority: P1
- Type: unit
- Given: The acknowledge endpoint implementation
- When: The Supabase `.upsert()` call is made
- Then: The `on_conflict` parameter is set to `"action_item_id,user_id,report_date"` matching the unique constraint
- Data: Verify mock call arguments include correct on_conflict value

## AC3: Daily Actions Enrichment

### 13-1-action-acknowledgment-backend-INT-010: Action list includes acknowledgment for acknowledged items
- Priority: P0
- Type: integration
- Given: An authenticated user calls `GET /api/v1/actions/daily` for `2026-02-09`
- And: The user has acknowledged action `action-safety-abc123def456` on that date with note `"Reviewed"`
- When: The response is returned
- Then: The action item with id `action-safety-abc123def456` includes an `acknowledgment` field containing `acknowledged_by` (user_id), `acknowledged_at` (ISO 8601 timestamp), and `note = "Reviewed"`
- Data: Mock engine returning actions with acknowledgment enrichment, mock acknowledgments query

### 13-1-action-acknowledgment-backend-INT-011: Unacknowledged action items have acknowledgment null
- Priority: P0
- Type: integration
- Given: An authenticated user calls `GET /api/v1/actions/daily` for `2026-02-09`
- And: The user has NOT acknowledged action `action-oee-def456abc123` on that date
- When: The response is returned
- Then: The action item with id `action-oee-def456abc123` has `acknowledgment: null`
- Data: Mock engine returning actions where some have no acknowledgment

### 13-1-action-acknowledgment-backend-UNIT-005: _load_acknowledgments returns correct lookup dict
- Priority: P0
- Type: unit
- Given: The `action_acknowledgments` table contains 2 records for user `user-uuid` on `2026-02-09`:
  - `action-safety-abc123` acknowledged with note `"Checked"`
  - `action-oee-def456` acknowledged with note `null`
- When: `_load_acknowledgments(report_date=date(2026,2,9), user_id="user-uuid")` is called
- Then: Returns a dict with keys `"action-safety-abc123"` and `"action-oee-def456"` mapped to `AcknowledgmentInfo` objects with correct `acknowledged_by`, `acknowledged_at`, and `note` values
- Data: Mock Supabase query returning 2 rows

### 13-1-action-acknowledgment-backend-UNIT-006: _load_acknowledgments returns empty dict when no acknowledgments
- Priority: P1
- Type: unit
- Given: The `action_acknowledgments` table has no records for user `user-uuid` on `2026-02-09`
- When: `_load_acknowledgments(report_date=date(2026,2,9), user_id="user-uuid")` is called
- Then: Returns an empty dict `{}`
- Data: Mock Supabase query returning empty data `[]`

### 13-1-action-acknowledgment-backend-UNIT-007: generate_action_list enriches actions when user_id provided
- Priority: P0
- Type: unit
- Given: The action engine generates 3 action items for `2026-02-09`
- And: The user has acknowledged 1 of them (`action-safety-abc123`)
- When: `generate_action_list(target_date=date(2026,2,9), user_id="user-uuid")` is called
- Then: The returned `ActionListResponse.actions` contains:
  - `action-safety-abc123` with `acknowledgment` populated (AcknowledgmentInfo)
  - Other 2 actions with `acknowledgment = None`
- Data: Mock Supabase queries for actions and acknowledgments

### 13-1-action-acknowledgment-backend-UNIT-008: generate_action_list skips enrichment when user_id is None
- Priority: P1
- Type: unit
- Given: The action engine generates action items
- When: `generate_action_list(target_date=date(2026,2,9), user_id=None)` is called
- Then: `_load_acknowledgments()` is NOT called
- And: All action items have `acknowledgment = None`
- Data: Verify `_load_acknowledgments` is not called via mock

### 13-1-action-acknowledgment-backend-UNIT-009: AcknowledgmentInfo schema has correct fields
- Priority: P1
- Type: unit
- Given: The `AcknowledgmentInfo` Pydantic schema
- When: Instantiated with `acknowledged_by="user-uuid"`, `acknowledged_at=datetime(...)`, `note="Checked"`
- Then: All fields are present and correctly typed
- Data: Valid AcknowledgmentInfo construction

### 13-1-action-acknowledgment-backend-UNIT-010: ActionItem model accepts optional acknowledgment field
- Priority: P0
- Type: unit
- Given: The `ActionItem` Pydantic model with the new `acknowledgment` field
- When: An `ActionItem` is created WITHOUT providing `acknowledgment`
- Then: The field defaults to `None` and the model validates successfully (backward compatible)
- Data: Existing ActionItem construction code from test fixtures (no acknowledgment field)

### 13-1-action-acknowledgment-backend-UNIT-011: Enrichment happens after cache retrieval, not before
- Priority: P1
- Type: unit
- Given: The action list for `2026-02-09` is cached (from a previous request by any user)
- When: User A calls `generate_action_list(target_date=date(2026,2,9), user_id="user-a-uuid")`
- And: User B calls `generate_action_list(target_date=date(2026,2,9), user_id="user-b-uuid")`
- Then: Both requests use the same cached action list
- And: Acknowledgment enrichment is applied independently per user (User A's acknowledgments don't appear for User B)
- Data: Two different user_ids with different acknowledgment records; verify cache key does NOT include user_id

### 13-1-action-acknowledgment-backend-INT-012: GET /daily passes current_user.id to generate_action_list
- Priority: P0
- Type: integration
- Given: An authenticated user with JWT `sub = "user-uuid-123"`
- When: `GET /api/v1/actions/daily` is called
- Then: The `generate_action_list()` method is called with `user_id="user-uuid-123"` (matching the authenticated user's ID)
- Data: Valid JWT with known sub claim, verify engine call arguments

## AC4: Authentication Required

### 13-1-action-acknowledgment-backend-INT-013: Acknowledge endpoint returns 401 without token
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: `POST /api/v1/actions/action-safety-abc123def456/acknowledge` is sent without a Bearer token
- Then: The response is HTTP 401 Unauthorized (or 403 Forbidden)
- Data: No auth header

### 13-1-action-acknowledgment-backend-INT-014: Acknowledge endpoint returns 401 with expired token
- Priority: P1
- Type: integration
- Given: An expired JWT Bearer token is provided
- When: `POST /api/v1/actions/action-safety-abc123def456/acknowledge` is sent with `Authorization: Bearer expired-token`
- Then: The response is HTTP 401 Unauthorized
- Data: Use `mock_verify_jwt_expired` fixture

### 13-1-action-acknowledgment-backend-INT-015: Acknowledge endpoint returns 401 with invalid token
- Priority: P1
- Type: integration
- Given: An invalid/malformed JWT Bearer token is provided
- When: `POST /api/v1/actions/action-safety-abc123def456/acknowledge` is sent with `Authorization: Bearer invalid-token`
- Then: The response is HTTP 401 Unauthorized
- Data: Use `mock_verify_jwt_invalid` fixture

## AC5: RLS Enforcement

### 13-1-action-acknowledgment-backend-UNIT-012: Migration creates RLS SELECT policy for authenticated users
- Priority: P0
- Type: unit (migration validation)
- Given: The migration `0027_action_acknowledgments.sql` is applied
- When: The RLS policies are inspected
- Then: A SELECT policy exists for role `authenticated` with condition `user_id = auth.uid()`
- Data: Migration SQL content validation

### 13-1-action-acknowledgment-backend-UNIT-013: Migration creates RLS INSERT policy for authenticated users
- Priority: P0
- Type: unit (migration validation)
- Given: The migration `0027_action_acknowledgments.sql` is applied
- When: The RLS policies are inspected
- Then: An INSERT policy exists for role `authenticated` with CHECK `user_id = auth.uid()`
- Data: Migration SQL content validation

### 13-1-action-acknowledgment-backend-UNIT-014: Migration creates RLS UPDATE policy for authenticated users
- Priority: P0
- Type: unit (migration validation)
- Given: The migration `0027_action_acknowledgments.sql` is applied
- When: The RLS policies are inspected
- Then: An UPDATE policy exists for role `authenticated` with USING `user_id = auth.uid()`
- Data: Migration SQL content validation

### 13-1-action-acknowledgment-backend-UNIT-015: Migration creates service_role full access policy
- Priority: P0
- Type: unit (migration validation)
- Given: The migration `0027_action_acknowledgments.sql` is applied
- When: The RLS policies are inspected
- Then: A policy for `service_role` grants full access (ALL or separate SELECT/INSERT/UPDATE/DELETE)
- Data: Migration SQL content validation

### 13-1-action-acknowledgment-backend-UNIT-016: Migration enables RLS on action_acknowledgments table
- Priority: P0
- Type: unit (migration validation)
- Given: The migration `0027_action_acknowledgments.sql` is applied
- When: The table definition is inspected
- Then: `ALTER TABLE action_acknowledgments ENABLE ROW LEVEL SECURITY` is present
- Data: Migration SQL content validation

### 13-1-action-acknowledgment-backend-UNIT-017: Migration creates unique constraint on (action_item_id, user_id, report_date)
- Priority: P0
- Type: unit (migration validation)
- Given: The migration `0027_action_acknowledgments.sql` is applied
- When: The constraints are inspected
- Then: A UNIQUE constraint exists on columns `(action_item_id, user_id, report_date)`
- Data: Migration SQL content validation

### 13-1-action-acknowledgment-backend-UNIT-018: Migration creates required indexes
- Priority: P1
- Type: unit (migration validation)
- Given: The migration `0027_action_acknowledgments.sql` is applied
- When: The indexes are inspected
- Then: Indexes exist for: `idx_action_ack_user_id`, `idx_action_ack_report_date`, `idx_action_ack_action_item_id`
- Data: Migration SQL content validation

### 13-1-action-acknowledgment-backend-UNIT-019: Migration creates updated_at trigger
- Priority: P1
- Type: unit (migration validation)
- Given: The migration `0027_action_acknowledgments.sql` is applied
- When: The triggers are inspected
- Then: A trigger reusing `update_updated_at_column()` exists on the `action_acknowledgments` table
- Data: Migration SQL content validation

### 13-1-action-acknowledgment-backend-UNIT-020: Migration defines correct column types
- Priority: P1
- Type: unit (migration validation)
- Given: The migration `0027_action_acknowledgments.sql` is applied
- When: The table columns are inspected
- Then: Columns match: `id` (UUID PK, gen_random_uuid()), `action_item_id` (TEXT NOT NULL), `user_id` (UUID NOT NULL REFERENCES auth.users), `acknowledged_at` (TIMESTAMPTZ DEFAULT NOW()), `note` (TEXT), `report_date` (DATE NOT NULL), `created_at` (TIMESTAMPTZ DEFAULT NOW()), `updated_at` (TIMESTAMPTZ DEFAULT NOW())
- Data: Migration SQL content validation

edge_cases:
  - Action ID with unexpected format (not matching `action-{category}-{hex12}`) — the endpoint should still accept any string action_id since validation is not enforced at this layer
  - Very long note text — ensure no length limit causes silent truncation (TEXT column has no limit)
  - Concurrent acknowledge requests from same user for same action — upsert should handle gracefully via unique constraint
  - Acknowledgment for an action_id that doesn't exist in the current action list — should still succeed (acknowledgments are independent of runtime action generation)
  - Report date in the future — the endpoint should accept any valid date (no business rule restricting to past dates)
  - Report date far in the past — should work without error
  - Multiple users acknowledging the same action_id on the same date — each gets their own record (unique constraint is per user)
  - Empty string note vs null note — `""` vs `None` handling in the schema
  - Action engine `_load_acknowledgments` database error — should handle gracefully (log error, return empty dict or propagate)

error_scenarios:
  - Supabase upsert failure (500 from database) — endpoint should return HTTP 500 with error message
  - Supabase query failure during _load_acknowledgments — daily endpoint should handle gracefully (not crash, possibly return actions without enrichment)
  - Invalid date format in query parameter — should return HTTP 422 validation error
  - Missing Authorization header — should return HTTP 401
  - Expired JWT token — should return HTTP 401
  - Malformed JWT token — should return HTTP 401
  - Request body with unexpected fields (extra fields) — should be ignored by Pydantic (default behavior)

test_file_mapping:
  - 13-1-action-acknowledgment-backend-INT-*: apps/api/tests/test_actions_api.py
  - 13-1-action-acknowledgment-backend-UNIT-001 to UNIT-004: apps/api/tests/test_actions_api.py (schema validation can colocate with API tests)
  - 13-1-action-acknowledgment-backend-UNIT-005 to UNIT-011: apps/api/tests/test_action_engine.py
  - 13-1-action-acknowledgment-backend-UNIT-012 to UNIT-020: apps/api/tests/test_actions_api.py (migration SQL validation, or a dedicated migration test file)

TEST SPEC END
