TEST SPEC START
story_id: 12-5-schedule-attainment-api
generated: 2026-02-11

test_specifications:

## AC1: Given schedule and actuals data exist for a date, When GET /api/v1/production/schedule-attainment?date={date} is called, Then the response includes per-workcenter schedule attainment with workcenter name, per-product breakdown (product name, scheduled quantity, actual quantity, attainment %), variance callouts (products scheduled but not produced, products produced but not scheduled), and overall workcenter attainment percentage

### 12-5-schedule-attainment-api-INT-001: Happy path returns per-workcenter schedule attainment breakdown
- Priority: P0
- Type: integration
- Given: Two workcenters exist ("Roasting" with 2 assets, "Grinding" with 1 asset). production_schedule has entries for date 2026-02-09 with scheduled products and quantities. production_actuals has matching entries with actual quantities. products and assets tables have corresponding lookup data.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: Response status is 200 AND `has_data` is true AND `date` equals "2026-02-09" AND `workcenters` array contains 2 entries AND each workcenter entry contains `workcenter` name, `products` array, `variances` array, and `overall_attainment_pct`
- Data: Assets: [{id: A1, name: "Roaster 1", area: "Roasting"}, {id: A2, name: "Roaster 2", area: "Roasting"}, {id: A3, name: "Grinder 1", area: "Grinding"}]. Products: [{id: P1, name: "Colombian"}, {id: P2, name: "Brazilian"}]. Schedule: [{asset_id: A1, product_id: P1, scheduled_quantity: 500, scheduled_date: "2026-02-09", shift: "Day"}, {asset_id: A3, product_id: P2, scheduled_quantity: 300, scheduled_date: "2026-02-09", shift: "Day"}]. Actuals: [{asset_id: A1, product_id: P1, actual_quantity: 450, production_date: "2026-02-09", shift: "Day"}, {asset_id: A3, product_id: P2, actual_quantity: 300, production_date: "2026-02-09", shift: "Day"}].

### 12-5-schedule-attainment-api-INT-002: Per-product attainment percentage is correctly calculated
- Priority: P0
- Type: integration
- Given: Schedule has product P1 with scheduled_quantity=500 on asset A1. Actuals have product P1 with actual_quantity=450 on asset A1 for the same date and shift.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The product entry for P1 shows scheduled_quantity=500, actual_quantity=450, and attainment_pct=90.0 (450/500*100)
- Data: Single asset/product/shift combination with known quantities for deterministic calculation

### 12-5-schedule-attainment-api-INT-003: Overall workcenter attainment is weighted average across products
- Priority: P0
- Type: integration
- Given: Workcenter "Roasting" has two schedule entries: asset A1/product P1 (scheduled=500, actual=450) and asset A2/product P2 (scheduled=300, actual=300) both for same date
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The "Roasting" workcenter overall_attainment_pct equals 93.8 ((450+300)/(500+300)*100, rounded to 1 decimal)
- Data: Two assets in same workcenter area with different scheduled and actual quantities

### 12-5-schedule-attainment-api-INT-004: Product entry includes product_name and product_id
- Priority: P0
- Type: integration
- Given: Schedule and actuals exist for product P1 (name: "Colombian", id: P1_UUID)
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The product entry contains `product_name` equal to "Colombian" AND `product_id` equal to P1_UUID (resolved from products table, not hardcoded)
- Data: Products table with id and name, schedule referencing product by id

### 12-5-schedule-attainment-api-INT-005: Variance callout for product scheduled but not produced (missing production)
- Priority: P0
- Type: integration
- Given: Schedule has entry for asset A1/product P1/shift "Day" on 2026-02-09. No matching actuals entry exists for that asset/shift combination.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The workcenter containing asset A1 has a variance callout with variance_type="missing" AND asset_name="Roaster 1" AND message indicates "Scheduled [product_name] but no production recorded"
- Data: Schedule entry with no matching actual for same (asset_id, shift)

### 12-5-schedule-attainment-api-INT-006: Variance callout for product produced but not scheduled (unscheduled production)
- Priority: P0
- Type: integration
- Given: Actuals has entry for asset A2/product P2/shift "Night" on 2026-02-09. No matching schedule entry exists for that asset/shift combination.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The workcenter containing asset A2 has a variance callout with variance_type="unscheduled" AND asset_name is the asset's name AND message indicates "Produced [product_name] but not scheduled"
- Data: Actuals entry with no matching schedule for same (asset_id, shift)

### 12-5-schedule-attainment-api-INT-007: Response structure contains all required top-level fields
- Priority: P0
- Type: integration
- Given: Schedule and actuals data exist for date 2026-02-09
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: Response JSON contains `date` (string), `workcenters` (array), `has_data` (boolean, true), and `message` (null or absent when data exists)
- Data: Minimal schedule and actuals data for a single workcenter

### 12-5-schedule-attainment-api-INT-008: Endpoint accessible on both /api/production and /api/v1/production paths
- Priority: P0
- Type: integration
- Given: The production router is registered at both /api/production and /api/v1/production prefixes
- When: GET /api/production/schedule-attainment?date=2026-02-09 is called with valid JWT AND GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: Both responses return status 200 with identical structure
- Data: Same mock data, two separate requests to different URL prefixes

### 12-5-schedule-attainment-api-INT-009: Attainment above 100% when actual exceeds scheduled
- Priority: P1
- Type: integration
- Given: Schedule has product P1 with scheduled_quantity=100. Actuals have product P1 with actual_quantity=120 on the same asset/shift/date.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The product entry shows attainment_pct=120.0 (120/100*100)
- Data: Single asset where actual exceeds scheduled quantity

### 12-5-schedule-attainment-api-INT-010: Zero scheduled quantity does not cause division by zero
- Priority: P1
- Type: integration
- Given: Schedule has product P1 with scheduled_quantity=0 on asset A1
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: Response status is 200 AND attainment_pct is 100.0 (safe default, no crash)
- Data: Schedule entry with scheduled_quantity=0

### 12-5-schedule-attainment-api-INT-011: Multiple shifts on same asset are handled independently
- Priority: P1
- Type: integration
- Given: Asset A1 has schedule entries for both "Day" and "Night" shifts. Actuals match on both shifts with different quantities.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: Both shift entries contribute to the workcenter's product attainment and overall_attainment_pct calculation. Attainment is computed correctly across all shifts for the workcenter.
- Data: Two schedule entries and two actuals entries for same asset on different shifts

## AC2: Given an asset produced a different product than scheduled, When the attainment response is generated, Then a variance callout is included (e.g., "Roaster 1 ran Colombian instead of scheduled Brazilian -- X units of Brazilian still needed")

### 12-5-schedule-attainment-api-INT-012: Product swap generates variance callout with descriptive message
- Priority: P0
- Type: integration
- Given: Schedule has asset A1/product P1 ("Brazilian")/shift "Day" with scheduled_quantity=500. Actuals have asset A1/product P2 ("Colombian")/shift "Day" with actual_quantity=480.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The workcenter for asset A1 contains a variance callout with variance_type="swap" AND asset_name="Roaster 1" AND message contains "Roaster 1 ran Colombian instead of scheduled Brazilian" AND message contains "500 units of Brazilian still needed"
- Data: Schedule for Brazilian, actual for Colombian on same asset/shift. Products table: [{id: P1, name: "Brazilian"}, {id: P2, name: "Colombian"}]. Assets: [{id: A1, name: "Roaster 1", area: "Roasting"}]

### 12-5-schedule-attainment-api-INT-013: Multiple product swaps on different assets generate separate callouts
- Priority: P1
- Type: integration
- Given: Asset A1 was scheduled for P1 but ran P2. Asset A2 was scheduled for P2 but ran P3. Both on same date and shift.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The response includes at least 2 variance callouts (one per asset swap), each with variance_type="swap" and correct asset names and product names in their messages
- Data: Two assets in same or different workcenters, each with a product swap scenario

### 12-5-schedule-attainment-api-INT-014: Product swap shows remaining units of scheduled product still needed
- Priority: P0
- Type: integration
- Given: Schedule has asset A1/product P1 with scheduled_quantity=500. Actual has asset A1/product P2 (different product) with actual_quantity=480.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The swap callout message includes the scheduled_quantity (500) as units still needed for the scheduled product, since no units of the scheduled product were actually produced
- Data: Known scheduled and actual quantities with product mismatch

### 12-5-schedule-attainment-api-INT-015: Swap combined with partial production of scheduled product
- Priority: P1
- Type: integration
- Given: Asset A1/shift "Day" has schedule for P1 (500 units). Actuals have two entries for A1/shift "Day": P1 (200 units, partial) and P2 (300 units, swap). So the scheduled product was partially fulfilled.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: The product attainment for P1 shows actual_quantity=200, scheduled_quantity=500, attainment_pct=40.0 AND a variance callout exists for the unscheduled P2 production (variance_type="unscheduled") AND the overall workcenter attainment reflects the partial production
- Data: Two actuals entries on same asset/shift — one matching schedule product (partial), one different product (unscheduled)

## AC3: Given no schedule exists for the requested date, When the endpoint is called, Then the response returns HTTP 200 with an empty result and message "No schedule data for this date"

### 12-5-schedule-attainment-api-INT-016: No schedule data returns 200 with empty result and message
- Priority: P0
- Type: integration
- Given: production_schedule query for date 2026-03-01 returns empty data. Actuals may or may not exist.
- When: GET /api/v1/production/schedule-attainment?date=2026-03-01 is called with valid JWT
- Then: Response status is 200 AND `has_data` is false AND `workcenters` is an empty array AND `message` equals "No schedule data for this date"
- Data: production_schedule returns [], all other tables may have data

### 12-5-schedule-attainment-api-INT-017: No schedule data does NOT return 404
- Priority: P0
- Type: integration
- Given: production_schedule query for the requested date returns no rows
- When: GET /api/v1/production/schedule-attainment?date=2026-03-01 is called with valid JWT
- Then: Response status is explicitly 200, NOT 404 or any other error code
- Data: Empty production_schedule response

### 12-5-schedule-attainment-api-INT-018: Empty schedule with actuals present still returns empty result
- Priority: P1
- Type: integration
- Given: No schedule entries for date 2026-03-01. Actuals entries DO exist for that date.
- When: GET /api/v1/production/schedule-attainment?date=2026-03-01 is called with valid JWT
- Then: Response status is 200 AND `has_data` is false AND `workcenters` is empty AND `message` equals "No schedule data for this date" (actuals without schedule are irrelevant for attainment)
- Data: production_schedule returns [], production_actuals returns non-empty data

## AC4: Given no authentication token is provided, When the endpoint is called, Then a 401 Unauthorized response is returned (standard JWT auth via get_current_user dependency)

### 12-5-schedule-attainment-api-INT-019: No auth token returns 401
- Priority: P0
- Type: integration
- Given: No Authorization header is provided in the request
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called without any auth headers
- Then: Response status is 401
- Data: No auth token, no mock_verify_jwt fixture active

### 12-5-schedule-attainment-api-INT-020: No auth token returns 401 on legacy path
- Priority: P0
- Type: integration
- Given: No Authorization header is provided in the request
- When: GET /api/production/schedule-attainment?date=2026-02-09 is called without any auth headers
- Then: Response status is 401
- Data: No auth token, no mock_verify_jwt fixture active, testing /api/production path

### 12-5-schedule-attainment-api-INT-021: Expired token returns 401
- Priority: P1
- Type: integration
- Given: An expired JWT token is provided
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with expired token
- Then: Response status is 401
- Data: Use mock_verify_jwt_expired fixture from conftest.py

### 12-5-schedule-attainment-api-INT-022: Invalid token returns 401
- Priority: P1
- Type: integration
- Given: An invalid JWT token is provided
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with invalid token
- Then: Response status is 401
- Data: Use mock_verify_jwt_invalid fixture from conftest.py

## AC5: Given the endpoint is called with an optional area query parameter, When data exists for that area, Then results are filtered to only workcenters matching that area

### 12-5-schedule-attainment-api-INT-023: Area filter returns only matching workcenters
- Priority: P0
- Type: integration
- Given: Schedule and actuals data exist for workcenters "Roasting" and "Grinding" on date 2026-02-09
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09&area=Roasting is called with valid JWT
- Then: Response status is 200 AND `workcenters` array contains only entries where workcenter matches "Roasting" AND "Grinding" workcenter is excluded
- Data: Assets in two areas, schedule/actuals for both areas. Area param filters to "Roasting" only.

### 12-5-schedule-attainment-api-INT-024: Area filter is case-insensitive
- Priority: P1
- Type: integration
- Given: Assets have area "Roasting" (title case). Schedule and actuals data exist.
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09&area=roasting is called with valid JWT (lowercase area param)
- Then: Response status is 200 AND `workcenters` array includes the "Roasting" workcenter (case-insensitive match per existing pattern in production.py lines 182-186)
- Data: Assets with "Roasting" area, query param in lowercase "roasting"

### 12-5-schedule-attainment-api-INT-025: Area filter with no matching workcenters returns empty
- Priority: P1
- Type: integration
- Given: Schedule data exists for date 2026-02-09 but no assets have area "NonExistent"
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09&area=NonExistent is called with valid JWT
- Then: Response status is 200 AND `workcenters` is an empty array AND `has_data` is true (schedule data exists, just no matching area)
- Data: Schedule and assets exist but area param does not match any asset area

### 12-5-schedule-attainment-api-INT-026: No area parameter returns all workcenters
- Priority: P0
- Type: integration
- Given: Schedule and actuals data exist for multiple workcenters ("Roasting", "Grinding") on date 2026-02-09
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT (no area param)
- Then: Response status is 200 AND `workcenters` array includes entries for both "Roasting" and "Grinding"
- Data: Assets in two different areas with schedule and actuals data for both

## Error Scenarios

### 12-5-schedule-attainment-api-INT-027: Supabase query failure returns 500
- Priority: P1
- Type: integration
- Given: Supabase client raises an unexpected exception during query execution
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: Response status is 500 AND detail equals "Failed to fetch schedule attainment data"
- Data: Mock Supabase client.table() to raise Exception("Connection refused")

### 12-5-schedule-attainment-api-INT-028: Supabase not configured returns 503
- Priority: P1
- Type: integration
- Given: get_supabase_client raises HTTPException 503 because settings lack supabase_url/key
- When: GET /api/v1/production/schedule-attainment?date=2026-02-09 is called with valid JWT
- Then: Response status is 503 AND detail equals "Supabase not configured"
- Data: Mock get_supabase_client to raise HTTPException(status_code=503, detail="Supabase not configured")

### 12-5-schedule-attainment-api-INT-029: Invalid date format returns 422
- Priority: P1
- Type: integration
- Given: An invalid date string is provided as the date query parameter
- When: GET /api/v1/production/schedule-attainment?date=not-a-date is called with valid JWT
- Then: Response status is 422 (Unprocessable Entity) with validation error
- Data: Invalid date string "not-a-date"

### 12-5-schedule-attainment-api-INT-030: Missing required date parameter returns 422
- Priority: P1
- Type: integration
- Given: The date query parameter is omitted from the request
- When: GET /api/v1/production/schedule-attainment is called with valid JWT (no date param)
- Then: Response status is 422 (Unprocessable Entity) because date is a required parameter
- Data: No date parameter in request URL

## Schema Validation

### 12-5-schedule-attainment-api-UNIT-001: ScheduleAttainmentResponse schema validates correctly
- Priority: P1
- Type: unit
- Given: Valid data for ScheduleAttainmentResponse model
- When: The Pydantic model is instantiated with date="2026-02-09", workcenters=[], has_data=True, message=None
- Then: All fields are correctly typed and validated — date is str, workcenters is List[WorkcenterScheduleAttainment], has_data is bool, message is Optional[str]
- Data: Construct ScheduleAttainmentResponse with minimal valid data

### 12-5-schedule-attainment-api-UNIT-002: ProductAttainment schema validates correctly
- Priority: P1
- Type: unit
- Given: Valid data for ProductAttainment model
- When: The Pydantic model is instantiated with product_name="Colombian", product_id="uuid-string", scheduled_quantity=500, actual_quantity=450, attainment_pct=90.0
- Then: All fields are correctly typed
- Data: Construct ProductAttainment with known values

### 12-5-schedule-attainment-api-UNIT-003: VarianceCallout schema validates correctly
- Priority: P1
- Type: unit
- Given: Valid data for VarianceCallout model
- When: The Pydantic model is instantiated with asset_name="Roaster 1", message="Roaster 1 ran Colombian instead of scheduled Brazilian", variance_type="swap"
- Then: All fields are correctly typed AND variance_type accepts "swap", "missing", and "unscheduled"
- Data: Construct VarianceCallout for each variance_type value

### 12-5-schedule-attainment-api-UNIT-004: WorkcenterScheduleAttainment schema validates correctly
- Priority: P1
- Type: unit
- Given: Valid data for WorkcenterScheduleAttainment model
- When: The Pydantic model is instantiated with workcenter="Roasting", products=[ProductAttainment(...)], variances=[VarianceCallout(...)], overall_attainment_pct=93.8
- Then: All fields are correctly typed — products is List[ProductAttainment], variances is List[VarianceCallout]
- Data: Construct with nested models

edge_cases:
  - Zero scheduled quantity for a product — attainment_pct should be 100.0 without division by zero
  - Overall workcenter attainment with all scheduled quantities summing to zero — should return 100.0
  - Multiple shifts on the same asset with different products each shift — each shift comparison is independent
  - Asset with actuals on both Day and Night shifts but schedule on only Day shift — Night shift production should generate "unscheduled" callout
  - Asset exists in assets table but has no schedule or actuals entries — should not appear in response
  - Product ID in actuals that does not exist in products table — should handle gracefully (use ID as fallback name or skip)
  - Very large quantities (>1M units) — should not cause numeric overflow in attainment calculation
  - Schedule entry with same product on same asset across multiple shifts — each shift is matched independently
  - Actuals entry with actual_quantity=0 — should show 0% attainment for that product, not be confused with "missing"

error_scenarios:
  - 401 Unauthorized — no token provided
  - 401 Unauthorized — expired JWT token
  - 401 Unauthorized — invalid JWT token
  - 422 Unprocessable Entity — invalid date format in query parameter
  - 422 Unprocessable Entity — missing required date parameter
  - 503 Service Unavailable — Supabase not configured
  - 500 Internal Server Error — unexpected exception during Supabase query
  - 500 Internal Server Error — unexpected exception during attainment calculation logic

test_file_mapping:
  - 12-5-schedule-attainment-api-INT-*: apps/api/tests/api/test_schedule_attainment.py
  - 12-5-schedule-attainment-api-UNIT-*: apps/api/tests/api/test_schedule_attainment.py

TEST SPEC END
