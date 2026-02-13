TEST SPEC START
story_id: 10-2-live-pulse-schema-fix
generated: 2026-02-11

test_specifications:

## AC1: Successful API Response
Given an authenticated user navigates to the live pulse view, When the `/api/live-pulse` endpoint is called, Then the response returns successfully (200) with current asset statuses, And no 500 error from querying non-existent `oee_percentage` column.

### 10-2-live-pulse-schema-fix-INT-001: Endpoint returns 200 with corrected query columns
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT token, and live snapshot data exists for 3 assets (mocked via Supabase client mock returning snapshots with only columns that exist in the actual `live_snapshots` table: id, asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars)
- When: GET `/api/live-pulse` is called with Authorization: Bearer header
- Then: The response status code is 200, the response body contains `timestamp`, `production`, `financial`, `safety`, and `meta` top-level keys
- Data: Mock snapshots without `oee_percentage`, `downtime_reason`, or `downtime_minutes` fields — simulating what Supabase actually returns from the corrected query

### 10-2-live-pulse-schema-fix-INT-002: No 500 error when oee_percentage column is absent from query results
- Priority: P0
- Type: integration
- Given: An authenticated user with a valid JWT, and the mock Supabase client returns snapshot data that does NOT include `oee_percentage` in any row
- When: GET `/api/live-pulse` is called
- Then: The response status code is 200 (not 500), the response JSON is a valid LivePulseResponse, and `production.oee_percentage` is present in the response (defaulting to 0.0)
- Data: Mock snapshots with fields: id, asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars only

### 10-2-live-pulse-schema-fix-UNIT-001: Supabase select query string contains only valid live_snapshots columns
- Priority: P0
- Type: unit
- Given: The `get_live_pulse_data()` function in `apps/api/app/api/live_pulse.py` is invoked
- When: The Supabase client `.table("live_snapshots").select(...)` call is made
- Then: The select string argument does NOT contain `oee_percentage`, `downtime_reason`, or `downtime_minutes`
- And: The select string contains only columns that exist in the `live_snapshots` table: `id`, `asset_id`, `snapshot_timestamp`, `current_output`, `target_output`, `status`, `financial_loss_dollars`
- Data: Inspect the select() call argument on the mock Supabase client

### 10-2-live-pulse-schema-fix-INT-003: Endpoint returns valid production data structure on success
- Priority: P0
- Type: integration
- Given: An authenticated user, mock returns 2 assets and 2 snapshots (one on_target, one below_target)
- When: GET `/api/live-pulse` is called
- Then: Response is 200, `production` object contains `current_output`, `target_output`, `output_percentage`, `oee_percentage`, `machine_status`, and `active_downtime`
- Data: Two mock snapshots with current_output=1500/2000, target_output=1800/1800, status=below_target/above_target, financial_loss_dollars=250/0

## AC2: Correct Column References
Given live snapshot data exists for multiple assets, When the live pulse endpoint returns data, Then each asset entry includes correct status, current output, target output, and financial loss fields, And all column references in the Supabase query match the actual `live_snapshots` table schema.

### 10-2-live-pulse-schema-fix-UNIT-002: Select query references only columns from live_snapshots schema
- Priority: P0
- Type: unit
- Given: The corrected `live_pulse.py` source code
- When: The select string passed to `.table("live_snapshots").select()` is examined
- Then: Every column name in the select string is one of: `id`, `asset_id`, `snapshot_timestamp`, `current_output`, `target_output`, `output_variance`, `status`, `created_at`, `financial_loss_dollars` (the full set of columns defined in migrations 0003 + 0022)
- And: No column names outside this set appear in the select string
- Data: Capture the string argument to `.select()` via the mock Supabase client and parse it

### 10-2-live-pulse-schema-fix-INT-004: Response includes correct status field per asset
- Priority: P0
- Type: integration
- Given: An authenticated user, 3 assets with snapshots: asset-001 status=below_target, asset-002 status=above_target, asset-003 status=on_target
- When: GET `/api/live-pulse` is called
- Then: Response is 200, `production.machine_status.total` equals 3, and `machine_status.running` reflects the count of assets with above_target/on_target/below_target status (all map to running per current logic)
- Data: Three mock snapshots with different status values, financial_loss_dollars of 250, 0, 150

### 10-2-live-pulse-schema-fix-INT-005: Response includes correct current_output and target_output aggregation
- Priority: P0
- Type: integration
- Given: An authenticated user, 2 assets with snapshots: asset-001 (current_output=750, target_output=1000), asset-002 (current_output=1250, target_output=1000)
- When: GET `/api/live-pulse` is called
- Then: `production.current_output` is 2000, `production.target_output` is 2000, `production.output_percentage` is 100.0
- Data: Two mock snapshots with known output values

### 10-2-live-pulse-schema-fix-INT-006: Response includes correct financial_loss_dollars aggregation
- Priority: P0
- Type: integration
- Given: An authenticated user, 3 assets with snapshots having financial_loss_dollars of 250.00, 0.00, and 150.00
- When: GET `/api/live-pulse` is called
- Then: `financial.shift_to_date_loss` equals 400.00
- Data: Three mock snapshots with recent timestamps and known financial_loss_dollars values

### 10-2-live-pulse-schema-fix-UNIT-003: downtime_reason and downtime_minutes not in select query
- Priority: P0
- Type: unit
- Given: The corrected `get_live_pulse_data()` function
- When: The `.table("live_snapshots").select()` call is inspected
- Then: The select string does NOT contain `downtime_reason` or `downtime_minutes`
- Data: Inspect select string argument on mock

## AC3: OEE Calculation Graceful Handling
Given the `live_snapshots` table does not contain an `oee_percentage` column, When the live pulse endpoint aggregates production data, Then OEE is either omitted from the snapshot query or derived from available data, And the response still includes a valid `oee_percentage` field (defaulting to 0.0 if no OEE data is available).

### 10-2-live-pulse-schema-fix-INT-007: OEE defaults to 0.0 when snapshots lack oee_percentage field
- Priority: P0
- Type: integration
- Given: An authenticated user, mock returns 3 snapshots that do NOT contain `oee_percentage` key (simulating the real Supabase response from the corrected query)
- When: GET `/api/live-pulse` is called
- Then: Response is 200, `production.oee_percentage` is 0.0
- Data: Three mock snapshots with only: id, asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars (no oee_percentage key)

### 10-2-live-pulse-schema-fix-INT-008: OEE still computed when oee_percentage is present in data (backward compat with mock tests)
- Priority: P1
- Type: integration
- Given: An authenticated user, mock returns 3 snapshots that DO include `oee_percentage` values (85.5, 92.0, 75.0) — as in existing mock test data
- When: GET `/api/live-pulse` is called
- Then: Response is 200, `production.oee_percentage` is approximately 84.2 (average of 85.5, 92.0, 75.0)
- And: The `.get("oee_percentage")` aggregation logic correctly averages available values
- Data: SAMPLE_LIVE_SNAPSHOTS with oee_percentage values (existing test data pattern)

### 10-2-live-pulse-schema-fix-INT-009: OEE defaults to 0.0 when oee_percentage is None for all snapshots
- Priority: P0
- Type: integration
- Given: An authenticated user, mock returns 2 snapshots where `oee_percentage` key exists but value is None for all
- When: GET `/api/live-pulse` is called
- Then: Response is 200, `production.oee_percentage` is 0.0 (oee_count stays 0, so avg_oee defaults to 0.0)
- Data: Two mock snapshots with `oee_percentage: None`

### 10-2-live-pulse-schema-fix-UNIT-004: oee_percentage is NOT in the Supabase select string
- Priority: P0
- Type: unit
- Given: The corrected `get_live_pulse_data()` function
- When: The `.table("live_snapshots").select()` call argument is inspected
- Then: The string `oee_percentage` does not appear in the select argument
- Data: Capture select argument from mock

### 10-2-live-pulse-schema-fix-INT-010: Response oee_percentage field exists and is a float regardless of source data
- Priority: P1
- Type: integration
- Given: An authenticated user, mock returns empty snapshots (no data at all)
- When: GET `/api/live-pulse` is called
- Then: Response is 200, `production.oee_percentage` is present and equals 0.0 (default from ProductionData model)
- Data: Empty snapshot list

## AC4: Existing Tests Pass
All existing `test_live_pulse_api.py` tests continue to pass after the fix. Test mock data is updated to match the corrected column references.

### 10-2-live-pulse-schema-fix-INT-011: test_endpoint_requires_authentication still passes
- Priority: P0
- Type: integration
- Given: The corrected `live_pulse.py` with the fixed select query
- When: `pytest apps/api/tests/test_live_pulse_api.py::TestLivePulseEndpoint::test_endpoint_requires_authentication -v` is run
- Then: The test passes (status code 401 for unauthenticated requests)
- Data: No mock data needed — test sends request without auth header

### 10-2-live-pulse-schema-fix-INT-012: test_returns_live_pulse_data still passes
- Priority: P0
- Type: integration
- Given: The corrected `live_pulse.py`, existing SAMPLE_LIVE_SNAPSHOTS mock data (which includes oee_percentage for backward compatibility)
- When: `pytest apps/api/tests/test_live_pulse_api.py::TestLivePulseEndpoint::test_returns_live_pulse_data -v` is run
- Then: The test passes — mock bypasses actual Supabase query, so column changes do not affect mock-based tests
- Data: Existing SAMPLE_LIVE_SNAPSHOTS, SAMPLE_ASSETS, SAMPLE_COST_CENTERS

### 10-2-live-pulse-schema-fix-INT-013: test_oee_average_calculation still passes with mock data
- Priority: P0
- Type: integration
- Given: The corrected `live_pulse.py`, existing SAMPLE_LIVE_SNAPSHOTS mock data with oee_percentage values (85.5, 92.0, 75.0)
- When: `pytest apps/api/tests/test_live_pulse_api.py::TestDataCalculations::test_oee_average_calculation -v` is run
- Then: The test passes — assertion `80 < production["oee_percentage"] < 90` is satisfied because mock data still contains oee_percentage and aggregation logic reads it via `.get()`
- Data: Existing SAMPLE_LIVE_SNAPSHOTS with oee_percentage values

### 10-2-live-pulse-schema-fix-INT-014: All 16 existing tests in test_live_pulse_api.py pass
- Priority: P0
- Type: integration
- Given: The corrected `live_pulse.py` with non-existent columns removed from the select query
- When: `pytest apps/api/tests/test_live_pulse_api.py -v` is run
- Then: All tests pass (16/16), exit code 0
- Data: All existing mock data unchanged

### 10-2-live-pulse-schema-fix-INT-015: No regressions in broader API test suite
- Priority: P1
- Type: integration
- Given: The corrected `live_pulse.py`
- When: `pytest apps/api/tests/ -v --timeout=30` is run
- Then: All tests pass, no regressions introduced by the query fix
- Data: All existing test fixtures

## Edge Cases and Error Scenarios

### 10-2-live-pulse-schema-fix-INT-016: Endpoint handles empty live_snapshots gracefully after fix
- Priority: P1
- Type: integration
- Given: An authenticated user, mock Supabase returns empty list for live_snapshots
- When: GET `/api/live-pulse` is called
- Then: Response is 200, `production.current_output` is 0, `production.target_output` is 0, `production.oee_percentage` is 0.0, `production.active_downtime` is an empty list, `financial.shift_to_date_loss` is 0
- Data: Empty snapshot list, valid assets list

### 10-2-live-pulse-schema-fix-INT-017: Active downtime list is empty when downtime columns are absent
- Priority: P1
- Type: integration
- Given: An authenticated user, mock returns 3 snapshots WITHOUT `downtime_reason` or `downtime_minutes` keys (reflecting the real corrected query response)
- When: GET `/api/live-pulse` is called
- Then: Response is 200, `production.active_downtime` is an empty list
- And: No error is raised from the `.get("downtime_reason")` fallback returning None
- Data: Three mock snapshots without downtime_reason/downtime_minutes keys

### 10-2-live-pulse-schema-fix-INT-018: Active downtime populates when downtime_reason is present in data (backward compat)
- Priority: P2
- Type: integration
- Given: An authenticated user, mock returns a snapshot WITH `downtime_reason: "Mechanical Failure"` and `downtime_minutes: 30` (even though these don't exist in the real table — tests use mock data)
- When: GET `/api/live-pulse` is called
- Then: Response is 200, `production.active_downtime` contains one entry with `reason_code: "Mechanical Failure"` and `duration_minutes: 30`
- Data: One mock snapshot with downtime_reason and downtime_minutes fields populated

### 10-2-live-pulse-schema-fix-INT-019: Database exception still returns 500 with descriptive message
- Priority: P1
- Type: integration
- Given: An authenticated user, `get_supabase_client()` raises an Exception("DB connection failed")
- When: GET `/api/live-pulse` is called
- Then: Response status code is 500, response body contains `"Failed to fetch live pulse data"`
- Data: Mock get_supabase_client with side_effect=Exception("DB connection failed")

### 10-2-live-pulse-schema-fix-INT-020: Multiple snapshots per asset — only latest per asset is used
- Priority: P1
- Type: integration
- Given: An authenticated user, mock returns 4 snapshots for 2 assets (2 snapshots each, ordered by timestamp desc), where asset-001 has latest current_output=500 and older current_output=300
- When: GET `/api/live-pulse` is called
- Then: Only the latest snapshot per asset is used — `production.current_output` reflects sum of latest snapshots only (not duplicates)
- Data: Four mock snapshots: asset-001 (500, newer timestamp), asset-001 (300, older), asset-002 (700, newer), asset-002 (400, older). Expected total_output = 500 + 700 = 1200

### 10-2-live-pulse-schema-fix-UNIT-005: Snapshot .get() pattern safely handles missing keys
- Priority: P1
- Type: unit
- Given: A snapshot dict with only the columns returned by the corrected query (id, asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars)
- When: `.get("oee_percentage")`, `.get("downtime_reason")`, and `.get("downtime_minutes")` are called on it
- Then: All return None without raising KeyError
- Data: Dict with only the 7 corrected columns

edge_cases:
  - Empty live_snapshots table returns valid response with zero/default values (INT-016)
  - Active downtime list empty when downtime columns absent from query results (INT-017)
  - Multiple snapshots per asset — deduplication uses latest only (INT-020)
  - Snapshots with None values for current_output and target_output — `or 0` fallback handles gracefully
  - Snapshot with financial_loss_dollars = None — Decimal conversion skipped via `if loss is not None` guard
  - OEE aggregation with mix of present and None oee_percentage values — only non-None values averaged

error_scenarios:
  - Database connection failure returns 500 with "Failed to fetch live pulse data" (INT-019)
  - PostgREST column-not-found error no longer occurs after removing non-existent columns (INT-001, INT-002)
  - Malformed snapshot_timestamp handled by calculate_data_age try/except (existing tests cover this)
  - Supabase returns empty data arrays — endpoint returns defaults without error (INT-016)

test_file_mapping:
  - 10-2-live-pulse-schema-fix-UNIT-*: apps/api/tests/test_live_pulse_schema_fix.py
  - 10-2-live-pulse-schema-fix-INT-*: apps/api/tests/test_live_pulse_schema_fix.py
  - 10-2-live-pulse-schema-fix-INT-011 through INT-015: apps/api/tests/test_live_pulse_api.py (existing tests — run as regression verification, no new test code needed)

TEST SPEC END
