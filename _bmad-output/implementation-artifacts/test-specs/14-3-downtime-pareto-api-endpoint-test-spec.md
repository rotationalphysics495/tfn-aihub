TEST SPEC START
story_id: 14-3-downtime-pareto-api-endpoint
generated: 2026-02-11

test_specifications:

## AC1: Given downtime events exist for an asset on a given date, When GET /api/v1/downtime/pareto?date={date}&asset_id={id} is called, Then the response includes an array of reason codes sorted by total duration (descending), each entry with reason_code, total_minutes, percentage, event_count, is_planned, total_downtime_minutes, and planned vs. unplanned split.

### 14-3-downtime-pareto-api-endpoint-E2E-001: Pareto endpoint returns items sorted by total_minutes descending
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains 3 reason codes for asset "asset-1" on date "2025-01-15": Mechanical (60min + 30min = 90min), Material Shortage (45min), Changeover (20min)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 200; `items` array has 3 entries ordered [Mechanical(90), Material Shortage(45), Changeover(20)]; each item's `total_minutes` is >= the next item's `total_minutes`
- Data: 4 downtime_events records (2 Mechanical, 1 Material Shortage, 1 Changeover); mock assets and cost_centers tables

### 14-3-downtime-pareto-api-endpoint-E2E-002: Each Pareto item includes reason_code, total_minutes, percentage, event_count, and is_planned
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events for asset "asset-1" on "2025-01-15": Mechanical (60min, is_planned=False), Planned Maintenance (40min, is_planned=True)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Each item in `items` has all required fields: `reason_code` (string), `total_minutes` (int >=0), `percentage` (float 0-100), `event_count` (int >=1), `is_planned` (bool); the Mechanical item has `is_planned=False`; the Planned Maintenance item has `is_planned=True`
- Data: 2 downtime_events records with distinct is_planned values

### 14-3-downtime-pareto-api-endpoint-E2E-003: Response includes total_downtime_minutes matching sum of all item minutes
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events totaling 155 minutes for asset "asset-1" on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: `total_downtime_minutes` equals 155; the sum of all items' `total_minutes` equals 155
- Data: Multiple downtime_events records summing to 155 minutes

### 14-3-downtime-pareto-api-endpoint-E2E-004: Response includes planned_minutes and unplanned_minutes that sum to total
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events for asset "asset-1" on "2025-01-15": Planned Maintenance (40min, is_planned=True), Changeover (25min, is_planned=True), Mechanical (60min, is_planned=False), Material Shortage (30min, is_planned=False)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: `planned_minutes` equals 65; `unplanned_minutes` equals 90; `planned_minutes + unplanned_minutes` equals `total_downtime_minutes` (155)
- Data: 4 downtime_events with mixed is_planned values

### 14-3-downtime-pareto-api-endpoint-E2E-005: Percentage of each item equals (total_minutes / total_downtime_minutes) * 100
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events for asset "asset-1" on "2025-01-15" with total 150 minutes: Mechanical (90min), Material Shortage (45min), Safety Issue (15min)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Mechanical percentage ≈ 60.0%; Material Shortage ≈ 30.0%; Safety Issue ≈ 10.0%; all percentages sum to approximately 100% (within 0.1% tolerance)
- Data: 3 reason codes with clean percentage division

### 14-3-downtime-pareto-api-endpoint-E2E-006: event_count accurately reflects number of events per reason code
- Priority: P1
- Type: e2e
- Given: The `downtime_events` table contains 3 events for "Mechanical" (60min, 30min, 20min) and 1 event for "Changeover" (45min) for asset "asset-1" on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Mechanical item has `event_count=3`; Changeover item has `event_count=1`
- Data: 4 downtime_events records grouped into 2 reason codes

### 14-3-downtime-pareto-api-endpoint-E2E-007: Authentication is required for the Pareto endpoint
- Priority: P0
- Type: e2e
- Given: No authentication token is provided
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called without an Authorization header
- Then: Response status is 401 (Unauthorized)
- Data: None

### 14-3-downtime-pareto-api-endpoint-E2E-008: Date parameter defaults to yesterday when not provided
- Priority: P1
- Type: e2e
- Given: The `downtime_events` table contains events for asset "asset-1" on yesterday's date
- When: `GET /api/v1/downtime/pareto?asset_id=asset-1` is called (no `date` parameter) with a valid auth token
- Then: Response status is 200; the service queries `downtime_events` with `event_date` = yesterday; items from yesterday's data are returned
- Data: downtime_events records for yesterday's date

### 14-3-downtime-pareto-api-endpoint-E2E-009: is_planned is determined by majority of minutes within a reason code
- Priority: P1
- Type: e2e
- Given: The `downtime_events` table contains events for reason_code "Changeover" on asset "asset-1" on "2025-01-15": one event with 60min (is_planned=True) and one event with 20min (is_planned=False)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: The Changeover item has `is_planned=True` because the majority of its minutes (60 of 80) are planned
- Data: 2 downtime_events for same reason_code with different is_planned values

### 14-3-downtime-pareto-api-endpoint-UNIT-001: ParetoItem model includes is_planned field with default False
- Priority: P0
- Type: unit
- Given: A ParetoItem is instantiated with only required fields (reason_code, total_minutes)
- When: The `is_planned` field is accessed
- Then: `is_planned` is `False` (default value); the field is a boolean type
- Data: Minimal ParetoItem construction

### 14-3-downtime-pareto-api-endpoint-UNIT-002: ParetoResponse model includes planned_minutes and unplanned_minutes with defaults of 0
- Priority: P0
- Type: unit
- Given: A ParetoResponse is instantiated with only required fields (items, total_downtime_minutes, total_financial_impact, total_events, data_source, last_updated)
- When: The `planned_minutes` and `unplanned_minutes` fields are accessed
- Then: Both default to 0; both are integer types with ge=0 constraint
- Data: Minimal ParetoResponse construction

### 14-3-downtime-pareto-api-endpoint-UNIT-003: calculate_pareto tracks planned and unplanned minutes per reason code
- Priority: P0
- Type: unit
- Given: A list of DowntimeEvent objects with mixed is_planned values: [Mechanical 60min planned, Mechanical 30min unplanned, Material Shortage 45min unplanned]
- When: `calculate_pareto(events)` is called
- Then: Mechanical ParetoItem has `is_planned=True` (60 planned > 30 unplanned); Material Shortage has `is_planned=False` (0 planned < 45 unplanned)
- Data: 3 DowntimeEvent objects with is_planned field set

### 14-3-downtime-pareto-api-endpoint-UNIT-004: DowntimeEvent model supports is_planned field
- Priority: P1
- Type: unit
- Given: A DowntimeEvent is instantiated with `is_planned=True`
- When: The object is serialized/accessed
- Then: `is_planned` is `True`; default value when not provided is `False`
- Data: DowntimeEvent with and without is_planned

### 14-3-downtime-pareto-api-endpoint-INT-001: Service queries downtime_events table with correct filters
- Priority: P0
- Type: integration
- Given: A mock Supabase client is configured with downtime_events data for asset "asset-1" on "2025-01-15"
- When: `service.get_downtime_from_events_table(event_date=date(2025,1,15), asset_id="asset-1")` is called
- Then: The Supabase client calls `table("downtime_events").select("*").eq("event_date", "2025-01-15").eq("asset_id", "asset-1").execute()`; returned records match mock data
- Data: Mock Supabase client with chained query expectations

### 14-3-downtime-pareto-api-endpoint-INT-002: Caching returns cached response on second call with same parameters
- Priority: P1
- Type: integration
- Given: The Pareto endpoint has been called once for date="2025-01-15" and asset_id="asset-1", populating the cache
- When: The same endpoint is called again with identical parameters
- Then: The Supabase client is NOT called a second time for downtime_events; the response matches the first call's response; TTL is 15 minutes (900 seconds)
- Data: Mock Supabase client tracking call count

### 14-3-downtime-pareto-api-endpoint-INT-003: Cache key differentiates by date, asset_id, and area
- Priority: P2
- Type: integration
- Given: The Pareto endpoint is called for date="2025-01-15" and asset_id="asset-1"
- When: A second call is made for date="2025-01-16" and asset_id="asset-1"
- Then: The Supabase client IS called again (different cache key); the response reflects the different date's data
- Data: Mock Supabase client with different data for each date

## AC2: Given an area parameter is provided instead of asset_id, When the Pareto endpoint is called, Then downtime is aggregated across all assets in that workcenter area.

### 14-3-downtime-pareto-api-endpoint-E2E-010: Area parameter aggregates downtime across all assets in that workcenter
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains events on "2025-01-15": asset-1 (area="Workcenter A", Mechanical 60min), asset-2 (area="Workcenter A", Mechanical 30min, Material Shortage 45min), asset-3 (area="Workcenter B", Mechanical 20min)
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&area=Workcenter A` is called with a valid auth token
- Then: Response includes only assets from "Workcenter A"; Mechanical total_minutes = 90 (60+30); Material Shortage total_minutes = 45; total_downtime_minutes = 135; asset-3's events are excluded
- Data: 4 downtime_events across 3 assets in 2 areas; mock assets table with area assignments

### 14-3-downtime-pareto-api-endpoint-E2E-011: Area filter is case-insensitive
- Priority: P1
- Type: e2e
- Given: Assets have area="Workcenter A" in the database; downtime_events exist for those assets on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&area=workcenter a` is called (lowercase)
- Then: Response status is 200; events from "Workcenter A" assets are included in the aggregation
- Data: Assets with mixed-case area names; downtime_events for those assets

### 14-3-downtime-pareto-api-endpoint-INT-004: Service method filters events by area using assets_map lookup
- Priority: P0
- Type: integration
- Given: A mock Supabase client returns 5 downtime_events records for "2025-01-15" across multiple areas; assets_map maps asset IDs to areas
- When: `service.get_downtime_from_events_table(event_date=date(2025,1,15), area="Assembly")` is called
- Then: Only records whose asset_id maps to area "Assembly" are returned; other area records are filtered out
- Data: Mock assets table, mock downtime_events with assets in different areas

### 14-3-downtime-pareto-api-endpoint-E2E-012: Area with no matching assets returns empty result
- Priority: P1
- Type: e2e
- Given: No assets exist in area "Nonexistent Area"; downtime_events exist for other areas on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&area=Nonexistent Area` is called with a valid auth token
- Then: Response status is 200; `items` is an empty array; `total_downtime_minutes` is 0; `planned_minutes` is 0; `unplanned_minutes` is 0
- Data: downtime_events for other areas; no assets with the queried area

## AC3: Given no downtime events exist for the query, When the endpoint is called, Then the response returns an empty array with total_minutes = 0.

### 14-3-downtime-pareto-api-endpoint-E2E-013: No downtime events returns empty items and zero totals
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table contains no records for asset "asset-1" on "2025-01-15"; the `daily_summaries` table also contains no records for this query
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 200; `items` is an empty array `[]`; `total_downtime_minutes` is 0; `planned_minutes` is 0; `unplanned_minutes` is 0; `total_events` is 0
- Data: Empty mock tables for both downtime_events and daily_summaries

### 14-3-downtime-pareto-api-endpoint-E2E-014: No downtime_events falls back to daily_summaries data
- Priority: P0
- Type: e2e
- Given: The `downtime_events` table has no records for asset "asset-1" on "2025-01-15"; the `daily_summaries` table HAS records for asset "asset-1" in that date range with downtime data
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 200; `items` are populated from `daily_summaries` data; `data_source` is "daily_summaries"; `planned_minutes` defaults to 0 (daily_summaries has no is_planned data); `unplanned_minutes` defaults to 0
- Data: Empty downtime_events; populated daily_summaries with reason codes and downtime minutes

### 14-3-downtime-pareto-api-endpoint-INT-005: Fallback queries daily_summaries when downtime_events returns empty
- Priority: P0
- Type: integration
- Given: A mock Supabase client returns empty data for `downtime_events` table query; returns populated data for `daily_summaries` query
- When: The Pareto endpoint handler executes the downtime_events-first strategy
- Then: The service first queries `downtime_events`; upon receiving empty results, falls through to query `daily_summaries`; the final response uses daily_summaries data
- Data: Mock Supabase client with empty downtime_events and populated daily_summaries

### 14-3-downtime-pareto-api-endpoint-E2E-015: Both tables empty returns valid empty response
- Priority: P1
- Type: e2e
- Given: Both `downtime_events` and `daily_summaries` tables have no records for asset "asset-1" on "2025-01-15"
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 200 (not 404); `items` is `[]`; all totals are 0; response is a valid ParetoResponse
- Data: Empty mock data for both tables

## Additional Specifications (Cross-cutting concerns)

### 14-3-downtime-pareto-api-endpoint-E2E-016: Endpoint handles database errors gracefully
- Priority: P1
- Type: e2e
- Given: The Supabase client raises an exception when querying `downtime_events`
- When: `GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1` is called with a valid auth token
- Then: Response status is 500; response body contains an error message; the error is logged
- Data: Mock Supabase client configured to raise an exception

### 14-3-downtime-pareto-api-endpoint-UNIT-005: New ParetoResponse fields are backward compatible
- Priority: P1
- Type: unit
- Given: A ParetoResponse is constructed using only the fields that existed before this story (items, total_downtime_minutes, total_financial_impact, total_events, data_source, last_updated)
- When: The response is serialized to JSON
- Then: `planned_minutes` appears with default value 0; `unplanned_minutes` appears with default value 0; all ParetoItem objects have `is_planned` with default value False; existing fields remain unchanged
- Data: ParetoResponse with pre-story-14.3 field set only

### 14-3-downtime-pareto-api-endpoint-INT-006: Endpoint is async and uses async service methods
- Priority: P2
- Type: integration
- Given: The endpoint handler and new service methods are defined
- When: The code is inspected
- Then: `get_downtime_pareto()` is an async function; `get_downtime_from_events_table()` is an async method; `transform_downtime_events_records()` is an async method; all Supabase queries use `.execute()` (not blocking the event loop)
- Data: Code inspection / import verification

### 14-3-downtime-pareto-api-endpoint-INT-007: Data source is reported as "downtime_events" when events table is used
- Priority: P1
- Type: integration
- Given: The `downtime_events` table contains records for the query parameters
- When: The Pareto endpoint processes the request using the events table path
- Then: The response `data_source` field is "downtime_events" (not "daily_summaries" or "live_snapshots")
- Data: Populated downtime_events mock data

edge_cases:
  - Single reason code across all events: should return 1 ParetoItem with percentage=100%, cumulative_percentage=100%, threshold_80_index=0
  - All events have the same duration: ordering is stable; percentages are evenly distributed
  - Reason code appears for both planned and unplanned events: is_planned determined by majority of minutes
  - Very large number of distinct reason codes (e.g., 50): all returned, percentages still sum to ~100%
  - Reason code with exactly 50/50 planned vs unplanned minutes: is_planned=False (planned_minutes not > unplanned_minutes)
  - Date far in the past with no data: returns empty response, not an error
  - Both asset_id and area provided simultaneously: asset_id should take precedence or both filters should apply (verify behavior)
  - Downtime events with very large duration_minutes (e.g., 10000): no overflow, correct percentage calculation

error_scenarios:
  - Database connection failure on downtime_events query → 500 Internal Server Error
  - Database connection failure on fallback daily_summaries query → 500 Internal Server Error
  - Invalid date format in query parameter → 422 Validation Error (FastAPI auto-validates)
  - Invalid UUID for asset_id → 422 Validation Error or empty results (depending on validation)
  - Missing auth token → 401 Unauthorized
  - Expired auth token → 401 Unauthorized
  - Assets table query fails during area filtering → 500 Internal Server Error

test_file_mapping:
  - 14-3-downtime-pareto-api-endpoint-E2E-*: apps/api/tests/test_downtime_pareto.py
  - 14-3-downtime-pareto-api-endpoint-UNIT-*: apps/api/tests/test_downtime_pareto.py
  - 14-3-downtime-pareto-api-endpoint-INT-*: apps/api/tests/test_downtime_pareto.py

TEST SPEC END
