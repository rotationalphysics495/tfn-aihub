TEST SPEC START
story_id: 14-2-trend-data-api-endpoint
generated: 2026-02-11

test_specifications:

## AC1: Action item includes trend_data field with 7-day metric array, days_on_report, consecutive_days, week_over_week_change

### 14-2-trend-data-api-endpoint-UNIT-001: TrendData field present on action items with full 7-day OEE history
- Priority: P0
- Type: unit
- Given: An action item exists for asset-1 (category=OEE) and daily_summaries contains 7 consecutive days of data for asset-1 with oee_percentage values [78.5, 76.2, 74.8, 80.1, 72.5, 73.0, 71.3]
- When: _calculate_trend_data() is called for the OEE action item with target_date = day 7
- Then: The returned TrendData has metric_values = [78.5, 76.2, 74.8, 80.1, 72.5, 73.0, 71.3] (index 0 = oldest, index 6 = target_date), and days_on_report, consecutive_days, and week_over_week_change are populated
- Data: 7 daily_summary records for asset-1 with ascending report_date, all with oee_percentage below target_oee_percentage (85.0)

### 14-2-trend-data-api-endpoint-UNIT-002: OEE metric uses oee_percentage column from daily_summaries
- Priority: P0
- Type: unit
- Given: An OEE-category action item for asset-1 and trailing daily_summaries with oee_percentage values
- When: _calculate_trend_data() is called
- Then: metric_values array contains oee_percentage values (not downtime_minutes or financial_loss_dollars)
- Data: daily_summaries rows with oee_percentage=72.5, downtime_minutes=120, financial_loss_dollars=3500

### 14-2-trend-data-api-endpoint-UNIT-003: FINANCIAL metric uses financial_loss_dollars column from daily_summaries
- Priority: P0
- Type: unit
- Given: A FINANCIAL-category action item for asset-2 and trailing daily_summaries with financial_loss_dollars values
- When: _calculate_trend_data() is called
- Then: metric_values array contains financial_loss_dollars values (not oee_percentage)
- Data: daily_summaries rows with financial_loss_dollars=4500.0 and oee_percentage=82.0

### 14-2-trend-data-api-endpoint-UNIT-004: SAFETY metric uses event count per day from safety_events
- Priority: P0
- Type: unit
- Given: A SAFETY-category action item for asset-3, and trailing_safety_counts shows {day1: 2, day3: 1, day5: 3, day7: 1} for asset-3
- When: _calculate_trend_data() is called
- Then: metric_values array contains daily safety event counts [2, 0, 1, 0, 3, 0, 1] where 0 = no events that day
- Data: safety_events records spread across 7 days with varying counts per day

### 14-2-trend-data-api-endpoint-UNIT-005: days_on_report counts days OEE asset was below target
- Priority: P0
- Type: unit
- Given: An OEE action item for asset-1 with target_oee=85.0, and 7 days of trailing summaries where oee_percentage = [78.5, 86.0, 74.8, 80.1, 72.5, 88.0, 71.3]
- When: _calculate_trend_data() is called
- Then: days_on_report = 5 (counting only days where oee_percentage < 85.0: days 1,3,4,5,7)
- Data: 7 daily_summaries with mix of above/below target OEE values

### 14-2-trend-data-api-endpoint-UNIT-006: days_on_report counts days FINANCIAL asset exceeded threshold
- Priority: P1
- Type: unit
- Given: A FINANCIAL action item for asset-2 with financial_loss_threshold=1000.0, and 7 days where financial_loss_dollars = [500, 1200, 800, 2500, 950, 3000, 1500]
- When: _calculate_trend_data() is called
- Then: days_on_report = 4 (counting days where financial_loss_dollars > 1000: days 2,4,6,7)
- Data: 7 daily_summaries with mix of above/below threshold financial loss values

### 14-2-trend-data-api-endpoint-UNIT-007: days_on_report counts days SAFETY asset had unresolved events
- Priority: P1
- Type: unit
- Given: A SAFETY action item for asset-3, trailing_safety_counts = {day1: 1, day3: 2, day7: 1}
- When: _calculate_trend_data() is called
- Then: days_on_report = 3 (days 1, 3, and 7 had > 0 events)
- Data: Safety event counts per day for asset-3

### 14-2-trend-data-api-endpoint-UNIT-008: consecutive_days counts backward from target_date for OEE
- Priority: P0
- Type: unit
- Given: An OEE action item with target_oee=85.0, and trailing summaries where oee_percentage (oldest→newest) = [86.0, 72.0, 88.0, 74.0, 71.0, 73.0, 70.0]
- When: _calculate_trend_data() is called
- Then: consecutive_days = 4 (days 4,5,6,7 all below target; day 3 breaks the streak)
- Data: Daily summaries where the most recent 4 days are below target but day 3 from end is above

### 14-2-trend-data-api-endpoint-UNIT-009: consecutive_days stops at first non-triggering day
- Priority: P1
- Type: unit
- Given: An OEE action item with target_oee=85.0, and trailing summaries where oee_percentage = [72.0, 73.0, 74.0, 90.0, 71.0, 73.0, 70.0]
- When: _calculate_trend_data() is called
- Then: consecutive_days = 3 (days 5,6,7 below target; day 4 at 90% breaks the streak)
- Data: Daily summaries with a gap day (above target) in the middle

### 14-2-trend-data-api-endpoint-UNIT-010: consecutive_days minimum is 1 when today triggers
- Priority: P1
- Type: unit
- Given: An OEE action item where only target_date has oee_percentage below target (day 7 = 70.0, day 6 = 90.0)
- When: _calculate_trend_data() is called
- Then: consecutive_days = 1
- Data: Daily summaries where only the most recent day triggers the threshold

### 14-2-trend-data-api-endpoint-UNIT-011: week_over_week_change calculates percentage correctly for OEE
- Priority: P0
- Type: unit
- Given: An OEE action item with metric_values[0] = 78.5 (7 days ago) and metric_values[6] = 71.3 (today)
- When: _calculate_trend_data() computes week_over_week_change
- Then: week_over_week_change = ((71.3 - 78.5) / 78.5) * 100 ≈ -9.17 (negative means OEE dropped)
- Data: Full 7-day metric_values array with known first and last values

### 14-2-trend-data-api-endpoint-UNIT-012: week_over_week_change returns null when 7-day-ago value is None
- Priority: P0
- Type: unit
- Given: An action item where metric_values[0] = None (no data 7 days ago) and metric_values[6] = 71.3
- When: _calculate_trend_data() computes week_over_week_change
- Then: week_over_week_change = None
- Data: Trailing summaries missing the oldest day

### 14-2-trend-data-api-endpoint-UNIT-013: week_over_week_change returns null when 7-day-ago value is zero
- Priority: P1
- Type: unit
- Given: An action item where metric_values[0] = 0.0 (zero value 7 days ago) and metric_values[6] = 5.0
- When: _calculate_trend_data() computes week_over_week_change
- Then: week_over_week_change = None (avoids division by zero)
- Data: Trailing summaries with zero value on the oldest day

### 14-2-trend-data-api-endpoint-INT-001: GET /api/v1/actions/daily returns trend_data on each action item
- Priority: P0
- Type: integration
- Given: Action items exist for multiple assets with 7 days of daily_summaries history
- When: GET /api/v1/actions/daily?date={date} is called
- Then: Each action item in the response includes a trend_data field with metric_values (array), days_on_report (int), consecutive_days (int), and week_over_week_change (float or null)
- Data: Mocked action engine returning ActionListResponse with trend_data populated

### 14-2-trend-data-api-endpoint-INT-002: generate_action_list integrates trend data after merge step
- Priority: P0
- Type: integration
- Given: Mocked Supabase client returns safety, OEE, and financial actions along with trailing summaries and safety events
- When: generate_action_list(target_date) is called
- Then: Every ActionItem in the response has trend_data populated (not None)
- Data: Complete mock data for assets, daily_summaries, safety_events, shift_targets, cost_centers with 7-day history

## AC2: Fewer than 7 days of history returns partial data

### 14-2-trend-data-api-endpoint-UNIT-014: Partial history returns correctly sized metric array with None padding
- Priority: P0
- Type: unit
- Given: An OEE action item for asset-1 with only 3 days of daily_summaries (days 5, 6, 7 relative to target_date)
- When: _calculate_trend_data() is called
- Then: metric_values = [None, None, None, None, 80.1, 73.0, 71.3] (None for missing days, values for available days), array length is always 7
- Data: 3 daily_summary records with report_dates for the 3 most recent days only

### 14-2-trend-data-api-endpoint-UNIT-015: days_on_report uses only available data when fewer than 7 days
- Priority: P0
- Type: unit
- Given: An OEE action item with only 3 days of history, all below target (oee_percentage = [80.1, 73.0, 71.3])
- When: _calculate_trend_data() is called
- Then: days_on_report = 3 (counts only available days that meet criteria, not counting None days)
- Data: 3 daily_summaries, all with OEE below target_oee_percentage

### 14-2-trend-data-api-endpoint-UNIT-016: consecutive_days uses only available data when fewer than 7 days
- Priority: P0
- Type: unit
- Given: An OEE action item with 4 days of history where all 4 are below target
- When: _calculate_trend_data() is called
- Then: consecutive_days = 4 (counts backward through all available data since all qualify)
- Data: 4 daily_summaries, all with OEE below target

### 14-2-trend-data-api-endpoint-UNIT-017: Partial history with gap days in available data
- Priority: P1
- Type: unit
- Given: An OEE action item with data on days 1, 3, 5, 7 (gaps on days 2, 4, 6)
- When: _calculate_trend_data() is called
- Then: metric_values has values at indices 0, 2, 4, 6 and None at indices 1, 3, 5; consecutive_days considers None/missing days as non-triggering (breaks the streak)
- Data: 4 daily_summaries with non-consecutive report_dates

### 14-2-trend-data-api-endpoint-UNIT-018: week_over_week_change computed correctly with partial data
- Priority: P1
- Type: unit
- Given: An action item with 5 days of history (days 3-7 only), so metric_values[0] = None
- When: _calculate_trend_data() computes week_over_week_change
- Then: week_over_week_change = None (no data 7 days ago)
- Data: 5 daily_summaries starting from day 3

## AC3: First appearance returns default trend values

### 14-2-trend-data-api-endpoint-UNIT-019: First appearance returns days_on_report=1 and consecutive_days=1
- Priority: P0
- Type: unit
- Given: An OEE action item for asset-1 that appears for the first time today with only today's daily_summary available (oee_percentage=71.3)
- When: _calculate_trend_data() is called
- Then: days_on_report = 1, consecutive_days = 1
- Data: 1 daily_summary record for target_date only

### 14-2-trend-data-api-endpoint-UNIT-020: First appearance returns week_over_week_change=null
- Priority: P0
- Type: unit
- Given: An action item with only today's value and no prior history
- When: _calculate_trend_data() is called
- Then: week_over_week_change = None (null)
- Data: 1 daily_summary record for target_date only

### 14-2-trend-data-api-endpoint-UNIT-021: First appearance metric_values has only today's value
- Priority: P0
- Type: unit
- Given: An OEE action item first appearing today with oee_percentage=71.3
- When: _calculate_trend_data() is called
- Then: metric_values = [None, None, None, None, None, None, 71.3] (only index 6 has a value)
- Data: 1 daily_summary record for target_date

### 14-2-trend-data-api-endpoint-UNIT-022: First appearance SAFETY item with 1 event today
- Priority: P1
- Type: unit
- Given: A SAFETY action item for an asset with 1 unresolved safety event today and no prior events
- When: _calculate_trend_data() is called
- Then: days_on_report = 1, consecutive_days = 1, week_over_week_change = None, metric_values = [None, None, None, None, None, None, 1]
- Data: 1 safety_event for target_date, no trailing safety events

### 14-2-trend-data-api-endpoint-UNIT-023: Asset with no trailing summaries at all (empty result)
- Priority: P1
- Type: unit
- Given: An action item for an asset where _load_trailing_summaries returns empty list for that asset_id
- When: _calculate_trend_data() is called
- Then: metric_values = [None] * 7, days_on_report = 0, consecutive_days = 0, week_over_week_change = None
- Data: Empty trailing summaries and safety events for the asset

## AC4: TrendData schema validates correctly with all required fields

### 14-2-trend-data-api-endpoint-UNIT-024: TrendData schema validates with all fields populated
- Priority: P0
- Type: unit
- Given: A TrendData instance with metric_values=[78.5, 76.2, 74.8, 80.1, 72.5, None, 71.3], days_on_report=5, consecutive_days=3, week_over_week_change=-9.2
- When: The TrendData model is instantiated
- Then: Validation passes and all fields are accessible with correct types
- Data: Complete TrendData constructor arguments

### 14-2-trend-data-api-endpoint-UNIT-025: TrendData schema validates with week_over_week_change=None
- Priority: P0
- Type: unit
- Given: A TrendData instance with week_over_week_change=None (first appearance scenario)
- When: The TrendData model is instantiated
- Then: Validation passes; week_over_week_change is None
- Data: TrendData with metric_values=[None]*6 + [71.3], days_on_report=1, consecutive_days=1, week_over_week_change=None

### 14-2-trend-data-api-endpoint-UNIT-026: TrendData schema rejects days_on_report > 7
- Priority: P1
- Type: unit
- Given: A TrendData constructor with days_on_report=8
- When: The TrendData model is instantiated
- Then: Pydantic validation error is raised (le=7 constraint violated)
- Data: Invalid days_on_report=8

### 14-2-trend-data-api-endpoint-UNIT-027: TrendData schema rejects negative days_on_report
- Priority: P1
- Type: unit
- Given: A TrendData constructor with days_on_report=-1
- When: The TrendData model is instantiated
- Then: Pydantic validation error is raised (ge=0 constraint violated)
- Data: Invalid days_on_report=-1

### 14-2-trend-data-api-endpoint-UNIT-028: TrendData schema rejects metric_values array longer than 7
- Priority: P1
- Type: unit
- Given: A TrendData constructor with metric_values containing 8 elements
- When: The TrendData model is instantiated
- Then: Pydantic validation error is raised (max_length=7 constraint violated)
- Data: metric_values with 8 float values

### 14-2-trend-data-api-endpoint-UNIT-029: TrendData serializes to JSON correctly
- Priority: P0
- Type: unit
- Given: A valid TrendData instance
- When: model_dump() / model_dump_json() is called
- Then: JSON output contains all fields with correct keys: metric_values, days_on_report, consecutive_days, week_over_week_change
- Data: Valid TrendData instance

### 14-2-trend-data-api-endpoint-UNIT-030: ActionItem includes optional trend_data field defaulting to None
- Priority: P0
- Type: unit
- Given: An ActionItem constructed without trend_data argument
- When: The ActionItem is instantiated
- Then: trend_data field is None (backward compatible with existing action items)
- Data: Standard ActionItem constructor without trend_data

### 14-2-trend-data-api-endpoint-UNIT-031: ActionItem with trend_data serializes correctly in ActionListResponse
- Priority: P0
- Type: unit
- Given: An ActionListResponse containing ActionItems with trend_data populated
- When: The response is serialized to JSON (model_dump())
- Then: Each action in the actions array contains a trend_data object with all TrendData fields
- Data: ActionListResponse with 2 ActionItems each having TrendData

### 14-2-trend-data-api-endpoint-UNIT-032: TrendData metric_values allows all None values
- Priority: P1
- Type: unit
- Given: A TrendData with metric_values=[None, None, None, None, None, None, None]
- When: The TrendData model is instantiated
- Then: Validation passes (all None is valid for assets with no metric data)
- Data: TrendData with all-None metric_values

## AC5: Trend queries are batched per asset (not N+1 per action item)

### 14-2-trend-data-api-endpoint-UNIT-033: _load_trailing_summaries makes a single batched query for multiple assets
- Priority: P0
- Type: unit
- Given: 5 action items spanning 3 unique asset_ids [asset-1, asset-2, asset-3]
- When: _load_trailing_summaries(target_date, [asset-1, asset-2, asset-3]) is called
- Then: Exactly 1 Supabase query is executed using .in_("asset_id", [...]) with all 3 asset_ids, not 3 separate queries
- Data: Mock Supabase client tracking call count; 3 asset_ids

### 14-2-trend-data-api-endpoint-UNIT-034: _load_trailing_summaries groups results by asset_id
- Priority: P0
- Type: unit
- Given: A batch query returns mixed results for asset-1 (3 rows), asset-2 (7 rows), asset-3 (5 rows)
- When: _load_trailing_summaries() processes the results
- Then: Returns Dict[str, List[dict]] grouped by asset_id with each list sorted by report_date ascending
- Data: 15 daily_summary rows interleaved across 3 assets

### 14-2-trend-data-api-endpoint-UNIT-035: _load_trailing_safety_events makes a single batched query
- Priority: P0
- Type: unit
- Given: 2 SAFETY action items for asset-1 and asset-3
- When: _load_trailing_safety_events(target_date, [asset-1, asset-3]) is called
- Then: Exactly 1 Supabase query is executed using .in_("asset_id", [...]) covering both assets
- Data: Mock Supabase client tracking call count; 2 asset_ids

### 14-2-trend-data-api-endpoint-UNIT-036: _load_trailing_safety_events groups results by asset_id and date
- Priority: P1
- Type: unit
- Given: A batch query returns safety events for asset-1 (3 events across 2 days) and asset-3 (1 event on 1 day)
- When: _load_trailing_safety_events() processes the results
- Then: Returns Dict[str, Dict[str, int]] = {asset-1: {date1: 2, date2: 1}, asset-3: {date3: 1}}
- Data: 4 safety_event rows with varying event_timestamps

### 14-2-trend-data-api-endpoint-INT-003: generate_action_list makes at most 2 additional queries for trend data
- Priority: P0
- Type: integration
- Given: Merged action list contains safety, OEE, and financial items for 4 unique assets
- When: generate_action_list() is called and trend data is computed
- Then: At most 2 additional Supabase queries are made: 1 for trailing daily_summaries, 1 for trailing safety_events (only if safety items exist). No N+1 pattern.
- Data: Mock Supabase client that counts total .execute() calls; verify only expected number of calls

### 14-2-trend-data-api-endpoint-INT-004: Safety event trailing query is skipped when no safety items exist
- Priority: P1
- Type: integration
- Given: Merged action list contains only OEE and FINANCIAL items (no SAFETY items)
- When: generate_action_list() computes trend data
- Then: _load_trailing_safety_events() is NOT called; only 1 additional query for trailing daily_summaries
- Data: Mock data producing only OEE and financial actions

### 14-2-trend-data-api-endpoint-UNIT-037: _load_trailing_summaries queries correct 7-day date range
- Priority: P0
- Type: unit
- Given: target_date = 2026-02-10
- When: _load_trailing_summaries() is called
- Then: Query filters use .gte("report_date", "2026-02-04") and .lte("report_date", "2026-02-10") (7 days inclusive)
- Data: Mock Supabase client capturing query parameters

### 14-2-trend-data-api-endpoint-UNIT-038: _load_trailing_summaries returns empty dict when no data found
- Priority: P1
- Type: unit
- Given: Supabase returns empty data for the trailing query
- When: _load_trailing_summaries() is called
- Then: Returns empty Dict (not None, not exception)
- Data: Mock Supabase returning .execute().data = []

## AC6: Cached trend data is returned within cache TTL

### 14-2-trend-data-api-endpoint-INT-005: Trend data is included in cached ActionListResponse
- Priority: P0
- Type: integration
- Given: generate_action_list() has been called once and the response (with trend_data) is cached
- When: generate_action_list() is called again with the same target_date within cache TTL
- Then: The cached response is returned (with trend_data intact), and no new Supabase queries are made for trailing summaries
- Data: Mock Supabase client tracking call count; call generate_action_list twice

### 14-2-trend-data-api-endpoint-INT-006: Cached response trend_data matches original computation
- Priority: P1
- Type: integration
- Given: First call to generate_action_list() returns actions with specific trend_data values
- When: Second call within cache TTL retrieves cached response
- Then: trend_data on each action item is identical to the first call's output (metric_values, days_on_report, consecutive_days, week_over_week_change)
- Data: Compare trend_data fields between first and second call responses

### 14-2-trend-data-api-endpoint-INT-007: Cache invalidation clears trend data with the rest of the response
- Priority: P1
- Type: integration
- Given: A cached ActionListResponse exists with trend_data
- When: invalidate_cache(target_date) is called, then generate_action_list() is called again
- Then: Fresh data is fetched (new Supabase queries made including trailing summaries), trend_data is recomputed
- Data: Mock Supabase with different data for second call to verify recomputation

edge_cases:
  - Asset appears in multiple categories (e.g., OEE and FINANCIAL) -- after deduplication, trend_data should reflect the winning (highest-tier) category's metric
  - daily_summaries has null oee_percentage for a day -- metric_values should contain None for that day, and that day should not count toward days_on_report
  - daily_summaries has null financial_loss_dollars -- same handling as null OEE
  - Safety event exactly on lookback boundary (event_timestamp = start of lookback day 00:00:00) -- should be included
  - All 7 days below target -- days_on_report=7, consecutive_days=7
  - Only today below target, all prior 6 days above -- days_on_report=1, consecutive_days=1
  - week_over_week_change with both values being identical -- should return 0.0 (no change)
  - Asset with daily_summaries data but all values are null -- metric_values=[None]*7, days_on_report=0, consecutive_days=0, week_over_week_change=None
  - Empty asset_ids list passed to _load_trailing_summaries -- should return empty dict without querying
  - Concurrent requests during cache population -- second request should wait for or use cached result (existing pattern)

error_scenarios:
  - Supabase query failure in _load_trailing_summaries -- should log error and return empty dict (follow existing _load_assets pattern), action items should still be returned with trend_data=None
  - Supabase query failure in _load_trailing_safety_events -- should log error and return empty dict, safety action items get trend_data with empty/null metric values
  - Invalid/unexpected data types in daily_summaries columns (string instead of float) -- should handle gracefully, treat as None
  - Supabase timeout on trailing summaries batch query -- action list generation should not fail entirely (degrade gracefully, return actions without trend_data)

test_file_mapping:
  - 14-2-trend-data-api-endpoint-UNIT-*: apps/api/tests/test_action_engine.py (TestTrendDataSchema, TestTrendDataCalculation, TestTrendBatchLoading classes)
  - 14-2-trend-data-api-endpoint-INT-*: apps/api/tests/test_action_engine.py (TestTrendDataIntegration class)
  - 14-2-trend-data-api-endpoint-E2E-*: N/A (no E2E tests -- this is a backend-only API story; integration tests cover the API endpoint via TestClient)

TEST SPEC END
