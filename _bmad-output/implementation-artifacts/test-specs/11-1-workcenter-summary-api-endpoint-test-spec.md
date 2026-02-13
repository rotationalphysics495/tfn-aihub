TEST SPEC START
story_id: 11-1-workcenter-summary-api-endpoint
generated: 2026-02-11

test_specifications:

## AC1: Given daily summary data exists for multiple assets across workcenters, When GET /api/v1/production/workcenter-summary?date={date} is called, Then the response includes one entry per workcenter (grouped by assets.area) with workcenter name, total actual/target, attainment percentage, hit/miss counts, and per-asset breakdown

### 11-1-workcenter-summary-api-endpoint-INT-001: Normal response with multiple workcenters and assets
- Priority: P0
- Type: integration
- Given: Two workcenters ("Grinding" with 2 assets, "Filling" with 1 asset) exist with daily_summaries and shift_targets for date 2026-01-15
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called with valid JWT
- Then: Response status is 200 AND response contains exactly 2 entries in `workcenters` array AND each entry has `workcenter`, `total_actual`, `total_target`, `attainment_pct`, `assets_hit`, `assets_missed`, and `assets` array AND `report_date` equals "2026-01-15"
- Data: Assets: [{id: A1, name: "Grinder 5", area: "Grinding"}, {id: A2, name: "Grinder 6", area: "Grinding"}, {id: A3, name: "Filler 1", area: "Filling"}]. Daily summaries for date 2026-01-15: [{asset_id: A1, units_produced: 950, oee: 83.5, downtime_minutes: 48}, {asset_id: A2, units_produced: 1100, oee: 92.0, downtime_minutes: 12}, {asset_id: A3, units_produced: 800, oee: 75.0, downtime_minutes: 60}]. Shift targets: [{asset_id: A1, shift: "day", target_units: 500}, {asset_id: A1, shift: "night", target_units: 500}, {asset_id: A2, shift: "day", target_units: 1000}, {asset_id: A3, shift: "day", target_units: 900}]

### 11-1-workcenter-summary-api-endpoint-UNIT-001: Workcenter total_actual is sum of units_produced
- Priority: P0
- Type: unit
- Given: Workcenter "Grinding" contains 2 assets with units_produced of 950 and 1100
- When: The aggregation logic computes total_actual for "Grinding"
- Then: total_actual equals 2050
- Data: Two daily_summaries with units_produced 950 and 1100

### 11-1-workcenter-summary-api-endpoint-UNIT-002: Workcenter total_target sums ALL shift_targets per asset
- Priority: P0
- Type: unit
- Given: Asset A1 has shift_targets [{shift: "day", target_units: 500}, {shift: "night", target_units: 500}] and Asset A2 has [{shift: "day", target_units: 1000}], both in workcenter "Grinding"
- When: The aggregation logic computes total_target for "Grinding"
- Then: total_target equals 2000 (500+500+1000)
- Data: Three shift_target rows across 2 assets

### 11-1-workcenter-summary-api-endpoint-UNIT-003: Attainment percentage calculation
- Priority: P0
- Type: unit
- Given: Workcenter total_actual is 2050 and total_target is 2000
- When: Attainment percentage is calculated
- Then: attainment_pct equals 102.5 (2050/2000*100, rounded to 1 decimal)
- Data: Pre-computed totals

### 11-1-workcenter-summary-api-endpoint-UNIT-004: Assets hit vs missed counts
- Priority: P0
- Type: unit
- Given: Workcenter "Grinding" has Asset A1 (actual=950, target=1000 — missed) and Asset A2 (actual=1100, target=1000 — hit)
- When: Hit/miss counts are computed
- Then: assets_hit equals 1 AND assets_missed equals 1
- Data: Two assets where one meets target and one does not

### 11-1-workcenter-summary-api-endpoint-INT-002: Per-asset breakdown contains all required fields
- Priority: P0
- Type: integration
- Given: Workcenter "Grinding" has 1 asset with daily_summary (units_produced=950, oee=83.5, downtime_minutes=48) and shift_targets summing to 1000
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called with valid JWT
- Then: The asset entry in the per-asset breakdown contains: asset_id, asset_name, actual_output (950), target_output (1000), oee (83.5), downtime_minutes (48), attainment_pct (95.0), hit_target (false)
- Data: Single asset with full daily_summary and shift_target data

### 11-1-workcenter-summary-api-endpoint-UNIT-005: Zero target edge case — attainment is 100.0 when target is 0 and actual > 0
- Priority: P1
- Type: unit
- Given: An asset has units_produced=500 but no shift_targets (target=0)
- When: Attainment percentage is calculated via calculate_percentage(500, 0)
- Then: attainment_pct equals 100.0 (no division by zero error)
- Data: Asset with daily_summary but no shift_target rows

### 11-1-workcenter-summary-api-endpoint-UNIT-006: Zero target and zero actual — attainment is 100.0
- Priority: P1
- Type: unit
- Given: An asset has units_produced=0 and no shift_targets (target=0)
- When: Attainment percentage is calculated via calculate_percentage(0, 0)
- Then: attainment_pct equals 100.0
- Data: Asset with zero production and no targets

### 11-1-workcenter-summary-api-endpoint-INT-003: Assets with NULL area are excluded or grouped under "Unassigned"
- Priority: P1
- Type: integration
- Given: 3 assets exist — 2 with area="Grinding" and 1 with area=None — all have daily_summaries
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called with valid JWT
- Then: The response does not crash AND the null-area asset is either excluded or grouped under an "Unassigned" workcenter AND the "Grinding" workcenter aggregation is correct
- Data: Assets with mixed area values including None/null

### 11-1-workcenter-summary-api-endpoint-INT-004: Asset with daily_summary but no shift_target (partial data)
- Priority: P1
- Type: integration
- Given: Asset A1 has a daily_summary (units_produced=800) but no rows in shift_targets
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called with valid JWT
- Then: Response is 200 AND asset A1 appears in its workcenter with target_output=0 AND attainment_pct=100.0 AND hit_target=true
- Data: One asset with daily_summary only, no shift_targets

### 11-1-workcenter-summary-api-endpoint-INT-005: Asset with shift_target but no daily_summary (partial data)
- Priority: P1
- Type: integration
- Given: Asset A1 has shift_targets (total=1000) but no daily_summary for the requested date
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called with valid JWT
- Then: Response is 200 AND the asset either does not appear (no production data) or appears with actual=0. The workcenter aggregation does not crash.
- Data: One asset with shift_targets only, no daily_summary for the date

### 11-1-workcenter-summary-api-endpoint-INT-006: Versioned endpoint alias /api/v1/production/workcenter-summary works
- Priority: P0
- Type: integration
- Given: The production router is registered at both /api/production and /api/v1/production
- When: GET /api/v1/production/workcenter-summary?date=2026-01-15 is called with valid JWT
- Then: Response status is 200 AND response structure is identical to the non-versioned path
- Data: Same mock data as INT-001

### 11-1-workcenter-summary-api-endpoint-INT-007: Authentication required — 401 without token
- Priority: P0
- Type: integration
- Given: No Authorization header is provided
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called
- Then: Response status is 401
- Data: No auth token

### 11-1-workcenter-summary-api-endpoint-INT-008: Authentication required — 401 with expired token
- Priority: P1
- Type: integration
- Given: An expired JWT token is provided
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called with expired token
- Then: Response status is 401
- Data: Expired JWT token (use mock_verify_jwt_expired fixture)

### 11-1-workcenter-summary-api-endpoint-INT-009: Response includes report_date field
- Priority: P0
- Type: integration
- Given: Daily summary data exists for 2026-01-15
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called with valid JWT
- Then: Response contains `report_date` field equal to "2026-01-15"
- Data: Same mock data as INT-001

## AC2: Given no daily summary data exists for the requested date, When the endpoint is called, Then the response returns an empty array with 200 status and a message indicating no data available for that date

### 11-1-workcenter-summary-api-endpoint-INT-010: Empty data returns 200 with empty workcenters array and message
- Priority: P0
- Type: integration
- Given: Assets exist but daily_summaries query returns empty data for date 2026-01-20
- When: GET /api/production/workcenter-summary?date=2026-01-20 is called with valid JWT
- Then: Response status is 200 AND `workcenters` is an empty array AND `message` field is present and indicates no data available for that date AND `report_date` equals "2026-01-20"
- Data: Assets table has rows, daily_summaries returns [] for the given date, shift_targets may or may not have rows

### 11-1-workcenter-summary-api-endpoint-INT-011: No assets exist — returns 200 with empty array
- Priority: P2
- Type: integration
- Given: Assets table returns empty data
- When: GET /api/production/workcenter-summary?date=2026-01-20 is called with valid JWT
- Then: Response status is 200 AND `workcenters` is an empty array AND `message` indicates no data available
- Data: All three queries return empty arrays

### 11-1-workcenter-summary-api-endpoint-UNIT-007: Message field is null/absent when data exists
- Priority: P1
- Type: unit
- Given: Daily summary data exists for the requested date
- When: WorkcenterSummaryResponse is built with data present
- Then: `message` field is None/null (not included or null in JSON)
- Data: Valid workcenter data

## AC3: Given a date parameter is not provided, When the endpoint is called, Then it defaults to yesterday (T-1)

### 11-1-workcenter-summary-api-endpoint-INT-012: Date defaults to T-1 when not provided
- Priority: P0
- Type: integration
- Given: Daily summary data exists for yesterday's date
- When: GET /api/production/workcenter-summary is called with valid JWT (no date param)
- Then: The Supabase query filters daily_summaries by yesterday's date (date.today() - timedelta(days=1)) AND `report_date` in response equals yesterday's date
- Data: Daily summaries for yesterday. Verify by inspecting mock call args that the date filter used is yesterday's ISO string.

### 11-1-workcenter-summary-api-endpoint-INT-013: Explicit date parameter is respected
- Priority: P0
- Type: integration
- Given: Daily summary data exists for 2026-01-10
- When: GET /api/production/workcenter-summary?date=2026-01-10 is called with valid JWT
- Then: The Supabase query filters daily_summaries by "2026-01-10" (NOT yesterday) AND `report_date` equals "2026-01-10"
- Data: Daily summaries for 2026-01-10. Verify by inspecting mock call args.

### 11-1-workcenter-summary-api-endpoint-INT-014: Invalid date format returns 422
- Priority: P1
- Type: integration
- Given: An invalid date string is provided
- When: GET /api/production/workcenter-summary?date=not-a-date is called with valid JWT
- Then: Response status is 422 (Unprocessable Entity) with validation error details
- Data: Invalid date string "not-a-date"

### 11-1-workcenter-summary-api-endpoint-INT-015: Future date is accepted
- Priority: P2
- Type: integration
- Given: No data exists for a future date
- When: GET /api/production/workcenter-summary?date=2099-12-31 is called with valid JWT
- Then: Response status is 200 AND `workcenters` is empty AND `message` indicates no data AND `report_date` equals "2099-12-31"
- Data: All queries return empty for the future date

## Error Scenarios

### 11-1-workcenter-summary-api-endpoint-INT-016: Supabase unavailable returns 503
- Priority: P1
- Type: integration
- Given: Supabase URL or key is not configured (get_supabase_client raises HTTPException 503)
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called with valid JWT
- Then: Response status is 503 with detail "Supabase not configured"
- Data: Mock get_supabase_client to raise HTTPException(503)

### 11-1-workcenter-summary-api-endpoint-INT-017: Unexpected Supabase error returns 500
- Priority: P1
- Type: integration
- Given: Supabase client raises an unexpected exception during query execution
- When: GET /api/production/workcenter-summary?date=2026-01-15 is called with valid JWT
- Then: Response status is 500 with detail "Failed to fetch workcenter summary data" AND the error is logged
- Data: Mock Supabase table().select().execute() to raise RuntimeError

## Schema Validation

### 11-1-workcenter-summary-api-endpoint-UNIT-008: WorkcenterSummaryResponse schema validates correctly
- Priority: P1
- Type: unit
- Given: Valid data for WorkcenterSummaryResponse model
- When: The Pydantic model is instantiated
- Then: All fields are correctly typed and validated — workcenters is List[WorkcenterEntry], report_date is date, message is Optional[str]
- Data: Construct WorkcenterSummaryResponse with sample WorkcenterEntry and AssetDetail objects

### 11-1-workcenter-summary-api-endpoint-UNIT-009: AssetDetail hit_target is true when actual >= target
- Priority: P1
- Type: unit
- Given: AssetDetail with actual_output=1000 and target_output=1000
- When: hit_target is evaluated
- Then: hit_target is true
- Data: actual_output=1000, target_output=1000

### 11-1-workcenter-summary-api-endpoint-UNIT-010: AssetDetail hit_target is false when actual < target
- Priority: P1
- Type: unit
- Given: AssetDetail with actual_output=950 and target_output=1000
- When: hit_target is evaluated
- Then: hit_target is false
- Data: actual_output=950, target_output=1000

edge_cases:
  - Zero target for all assets in a workcenter — attainment_pct should be 100.0 without division by zero
  - Asset with NULL/empty area field — should not crash aggregation, either excluded or grouped as "Unassigned"
  - Asset has daily_summary but no shift_targets — target treated as 0, attainment 100.0
  - Asset has shift_targets but no daily_summary for the date — gracefully handled (excluded or actual=0)
  - Multiple shift_targets per asset (day/night/swing) — all must be summed for daily total
  - Very large numbers — units_produced and target_units with large values should not cause overflow
  - Single asset in a workcenter — workcenter totals equal the single asset's values
  - Future date requested — returns empty data with message, not an error
  - Date at epoch boundaries (e.g., 2000-01-01) — should work without issues

error_scenarios:
  - 401 Unauthorized — no token provided
  - 401 Unauthorized — expired JWT token
  - 401 Unauthorized — invalid JWT token
  - 422 Unprocessable Entity — invalid date format in query parameter
  - 503 Service Unavailable — Supabase not configured
  - 500 Internal Server Error — unexpected exception during Supabase query or aggregation logic

test_file_mapping:
  - 11-1-workcenter-summary-api-endpoint-INT-*: apps/api/tests/api/test_production_workcenter.py
  - 11-1-workcenter-summary-api-endpoint-UNIT-*: apps/api/tests/api/test_production_workcenter.py

TEST SPEC END
