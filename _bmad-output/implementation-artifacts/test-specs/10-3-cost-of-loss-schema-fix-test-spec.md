TEST SPEC START
story_id: 10-3-cost-of-loss-schema-fix
generated: 2026-02-11

test_specifications:

## AC1: Daily Summary Query Uses Correct Column Name

### 10-3-cost-of-loss-schema-fix-UNIT-001: Cost-of-loss daily query SELECT references waste_count column
- Priority: P0
- Type: unit
- Given: An authenticated user and the `get_cost_of_loss` endpoint handler in `financial.py`
- When: The endpoint queries the `daily_summaries` table with `period=daily`
- Then: The Supabase `.select()` call includes `waste_count` in the column list (not `waste`)
- Data: Mock Supabase client; verify the string passed to `.select()` contains `waste_count`

### 10-3-cost-of-loss-schema-fix-UNIT-002: Cost-of-loss daily query extracts waste_count from record
- Priority: P0
- Type: unit
- Given: The `daily_summaries` query returns records with key `"waste_count"`
- When: The endpoint iterates over response data and calls `record.get()`
- Then: The value is extracted using key `"waste_count"` (not `"waste"`)
- And: The extracted value is passed to `calculate_waste_loss()` for cost computation
- Data: Mock response data: `[{"asset_id": "asset-1", "downtime_minutes": 60, "waste_count": 10, "financial_loss": 500.00, "oee_percentage": 75.0, "created_at": "2026-01-05T06:00:00Z"}]`

### 10-3-cost-of-loss-schema-fix-INT-001: Cost-of-loss daily endpoint returns 200 with correct waste cost
- Priority: P0
- Type: integration
- Given: An authenticated user and mock `daily_summaries` data with `waste_count: 10` and a cost center with `cost_per_unit: 20.00`
- When: `GET /api/financial/cost-of-loss?period=daily` is called
- Then: The response status is 200
- And: `breakdown.waste_cost` equals `10 * 20.00 = 200.00` (not 0)
- And: `total_loss` includes the waste cost contribution
- Data: Mock Supabase response with `{"asset_id": "asset-1", "downtime_minutes": 30, "waste_count": 10, "financial_loss": 500.00, "oee_percentage": 85.0, "created_at": "2026-02-10T06:00:00Z"}`; mock cost center `{"asset_id": "asset-1", "standard_hourly_rate": 100.00, "cost_per_unit": 20.00}`

### 10-3-cost-of-loss-schema-fix-INT-002: Cost-of-loss daily endpoint does not produce 500 error from wrong column
- Priority: P0
- Type: integration
- Given: An authenticated user and valid `daily_summaries` data in the database
- When: `GET /api/financial/cost-of-loss?period=daily` is called
- Then: The response status is 200 (not 500)
- And: No error is raised about a non-existent `waste` column
- Data: Standard mock daily_summaries data with `waste_count` key

### 10-3-cost-of-loss-schema-fix-UNIT-003: Cost-of-loss daily query handles null/zero waste_count gracefully
- Priority: P1
- Type: unit
- Given: A `daily_summaries` record where `waste_count` is `null` (returned as `None` by Supabase)
- When: The endpoint processes this record
- Then: `waste_count` defaults to 0 via `record.get("waste_count") or 0`
- And: `waste_cost` is calculated as 0.00
- And: No exception is raised
- Data: Mock response: `{"asset_id": "asset-1", "downtime_minutes": 30, "waste_count": null, "financial_loss": 100.00, "oee_percentage": 90.0, "created_at": "2026-02-10T06:00:00Z"}`

### 10-3-cost-of-loss-schema-fix-INT-003: Cost-of-loss with asset_id filter uses correct column
- Priority: P1
- Type: integration
- Given: An authenticated user requesting cost-of-loss filtered by `asset_id=asset-1`
- When: `GET /api/financial/cost-of-loss?period=daily&asset_id=asset-1` is called
- Then: The query still uses `waste_count` in the SELECT
- And: The response returns data only for the specified asset with correct waste calculations
- Data: Mock two assets; verify only the filtered asset appears with correct waste_cost

## AC2: Financial Summary Query Uses Correct Column Name

### 10-3-cost-of-loss-schema-fix-UNIT-004: Financial summary SELECT references waste_count column
- Priority: P0
- Type: unit
- Given: The `get_financial_summary` endpoint handler in `financial.py`
- When: The endpoint queries `daily_summaries` for the summary
- Then: The Supabase `.select()` call includes `waste_count` in the column list (not `waste`)
- Data: Mock Supabase client; verify the string passed to `.select()` contains `waste_count`

### 10-3-cost-of-loss-schema-fix-UNIT-005: Financial summary extracts waste_count and aggregates correctly
- Priority: P0
- Type: unit
- Given: Multiple `daily_summaries` records with `waste_count` values of 5, 10, and 15
- When: The endpoint aggregates `total_waste_count` across all records
- Then: `total_waste_count` equals 30 (sum of 5 + 10 + 15)
- And: The value is extracted using key `"waste_count"` (not `"waste"`)
- Data: Mock response: `[{"asset_id": "a1", "downtime_minutes": 30, "waste_count": 5, "financial_loss": 200.00}, {"asset_id": "a2", "downtime_minutes": 45, "waste_count": 10, "financial_loss": 300.00}, {"asset_id": "a3", "downtime_minutes": 60, "waste_count": 15, "financial_loss": 400.00}]`

### 10-3-cost-of-loss-schema-fix-INT-004: Financial summary endpoint returns correct total_waste_count
- Priority: P0
- Type: integration
- Given: An authenticated user and mock `daily_summaries` with known waste_count values
- When: `GET /api/financial/summary` is called
- Then: The response status is 200
- And: `total_waste_count` is the correct sum of all `waste_count` values
- And: `total_waste_loss` reflects the sum of calculated waste losses
- Data: Mock two records: `waste_count: 5` (cost_per_unit: 10.00) and `waste_count: 10` (cost_per_unit: 15.00); expected `total_waste_count: 15`, `total_waste_loss: 200.00`

### 10-3-cost-of-loss-schema-fix-UNIT-006: Financial summary handles empty daily_summaries response
- Priority: P1
- Type: unit
- Given: The `daily_summaries` query returns an empty list
- When: The endpoint aggregates waste data
- Then: `total_waste_count` is 0
- And: `total_waste_loss` is 0.00
- And: The response returns 200 with zeroed financial data
- Data: Mock response: `[]`

## AC3: Financial Impact Service Uses Correct Column Name

### 10-3-cost-of-loss-schema-fix-UNIT-007: Financial impact SELECT references waste_count column
- Priority: P0
- Type: unit
- Given: The `FinancialService.get_financial_impact()` method in `services/financial.py`
- When: It queries `daily_summaries` for an asset's date range
- Then: The Supabase `.select()` call includes `waste_count` in the column list (not `waste`)
- Data: Mock Supabase client; verify the string passed to `.select()` contains `waste_count`

### 10-3-cost-of-loss-schema-fix-UNIT-008: Financial impact extracts waste_count with correct key
- Priority: P0
- Type: unit
- Given: `daily_summaries` records containing `"waste_count": 23`
- When: `get_financial_impact()` processes the records via `record.get()`
- Then: The value is extracted using key `"waste_count"` (not `"waste"`)
- And: `total_waste` is summed correctly across all records
- Data: Mock response: `[{"asset_id": "asset-grd-005", "date": "2026-02-10", "downtime_minutes": 47, "waste_count": 23, "financial_loss": 500.00}]`

### 10-3-cost-of-loss-schema-fix-UNIT-009: Financial impact calculates waste_loss using waste_count * cost_per_unit
- Priority: P0
- Type: unit
- Given: A single `daily_summaries` record with `waste_count: 23` and a cost center with `cost_per_unit: 20.24`
- When: `get_financial_impact()` calculates the waste loss
- Then: `waste_loss` equals `23 * 20.24 = 465.52`
- And: `total_loss` includes both `downtime_loss` and `waste_loss`
- Data: Mock cost center: `{"standard_hourly_rate": 2393.62, "cost_per_unit": 20.24}`; mock record: `{"waste_count": 23, "downtime_minutes": 47}`

### 10-3-cost-of-loss-schema-fix-UNIT-010: Financial impact with multiple records sums waste_count correctly
- Priority: P1
- Type: unit
- Given: Three `daily_summaries` records with `waste_count` values of 10, 20, and 30
- When: `get_financial_impact()` aggregates waste data over the date range
- Then: `total_waste` equals 60
- And: `waste_loss` is calculated as `60 * cost_per_unit`
- Data: Mock three records across three consecutive dates; cost_per_unit: 15.00; expected waste_loss: 900.00

### 10-3-cost-of-loss-schema-fix-UNIT-011: Financial impact handles null waste_count in records
- Priority: P1
- Type: unit
- Given: A `daily_summaries` record where `waste_count` is `None`
- When: `get_financial_impact()` processes the record
- Then: `waste_count` defaults to 0
- And: `waste_loss` is 0.00 for that record
- And: No exception is raised
- Data: Mock record: `{"asset_id": "asset-1", "date": "2026-02-10", "downtime_minutes": 30, "waste_count": null, "financial_loss": 100.00}`

## AC4: Existing Tests Updated To Match Schema

### 10-3-cost-of-loss-schema-fix-UNIT-012: All test mock data uses waste_count key
- Priority: P0
- Type: unit
- Given: The test file `test_financial_api.py` with mock `daily_summaries` data
- When: A grep/search for `"waste"` (without `_count` suffix) is performed on mock data dictionaries
- Then: Zero matches are found — all mock data uses key `"waste_count"`
- Data: Grep pattern: `"waste"` excluding `"waste_count"`, `"waste_cost"`, `"waste_loss"`, `"total_waste_count"`, `"total_waste_loss"` in test files

### 10-3-cost-of-loss-schema-fix-INT-005: test_financial_summary_aggregates_data passes with waste_count mocks
- Priority: P0
- Type: integration
- Given: The `TestFinancialSummaryEndpoint.test_financial_summary_aggregates_data` test with updated mock data using `"waste_count"` keys
- When: The test is executed via `pytest apps/api/tests/test_financial_api.py::TestFinancialSummaryEndpoint::test_financial_summary_aggregates_data -v`
- Then: The test passes without any assertion failures
- And: The endpoint correctly reads `waste_count` from the mock data
- Data: Existing test data updated from `"waste": 5` to `"waste_count": 5`

### 10-3-cost-of-loss-schema-fix-INT-006: test_cost_of_loss_calculates_breakdown passes with waste_count mocks
- Priority: P0
- Type: integration
- Given: The `TestCostOfLossEndpoint.test_cost_of_loss_calculates_breakdown` test with updated mock data using `"waste_count"` keys
- When: The test is executed via `pytest apps/api/tests/test_financial_api.py::TestCostOfLossEndpoint -v`
- Then: All cost-of-loss tests pass without assertion failures
- And: `breakdown.waste_cost` is calculated correctly from the mock `waste_count` values
- Data: Existing test data updated from `"waste": 10` to `"waste_count": 10` and `"waste": 20` to `"waste_count": 20`

### 10-3-cost-of-loss-schema-fix-INT-007: Full financial API test suite passes with no regressions
- Priority: P0
- Type: integration
- Given: All changes applied (SELECT fixes, record.get() fixes, mock data fixes)
- When: `pytest apps/api/tests/test_financial_api.py -v` is executed
- Then: All tests pass (0 failures, 0 errors)
- And: No test assertions are broken by the column name change
- Data: Full test suite run

### 10-3-cost-of-loss-schema-fix-REG-001: Full API test suite has no regressions
- Priority: P0
- Type: integration
- Given: All code changes from this story are applied
- When: `pytest apps/api/tests/ -v --timeout=120` is executed
- Then: All API tests pass with 0 failures and 0 errors
- And: No tests outside `test_financial_api.py` are affected by the changes
- Data: Full API test suite

## AC5: Agent Data Source Remains Correct

### 10-3-cost-of-loss-schema-fix-UNIT-013: SupabaseDataSource.get_cost_of_loss() already uses waste_count
- Priority: P0
- Type: unit
- Given: The `SupabaseDataSource.get_cost_of_loss()` method in `apps/api/app/services/agent/data_source/supabase.py`
- When: The SELECT fields string is inspected
- Then: The select includes `waste_count` (confirmed at line 1138)
- And: No code changes have been made to this file as part of this story
- Data: Static code verification — grep for `waste_count` in supabase.py `get_cost_of_loss` method

### 10-3-cost-of-loss-schema-fix-INT-008: Agent cost-of-loss tool tests pass without changes
- Priority: P0
- Type: integration
- Given: No changes have been made to `supabase.py` or agent tool files
- When: `pytest apps/api/tests/services/agent/tools/test_cost_of_loss.py -v` is executed
- Then: All tests pass (0 failures, 0 errors)
- And: The `waste_count` field is correctly used throughout the agent data source layer
- Data: Full agent cost-of-loss test suite

### 10-3-cost-of-loss-schema-fix-INT-009: Agent financial impact tool tests pass without changes
- Priority: P1
- Type: integration
- Given: No changes have been made to agent tool files
- When: `pytest apps/api/tests/services/agent/tools/test_financial_impact.py -v` is executed
- Then: All tests pass (0 failures, 0 errors)
- Data: Full agent financial impact test suite

edge_cases:
  - Null/None waste_count value in daily_summaries record — should default to 0 via `or 0` pattern, not raise exception
  - Empty daily_summaries response (no records returned) — totals should all be 0.00
  - Mixed records where some have waste_count=0 and others have positive values — only positive values should contribute to totals
  - Large waste_count values (e.g., 999999) — should not overflow or cause precision issues in Decimal calculations
  - Records with waste_count but no matching cost_center (no cost_per_unit) — should use default rate, waste_loss should still calculate

error_scenarios:
  - Supabase query failure (connection error) — should return 500/503 with error message, not crash
  - Invalid period parameter (e.g., period=weekly) — should return 400 or fall through to default daily behavior
  - Unauthenticated request — should return 401 before any query is attempted
  - cost_per_unit is None/null for an asset — waste_loss should be 0.00 for that asset (defensive calculation)

test_file_mapping:
  - 10-3-cost-of-loss-schema-fix-UNIT-*: apps/api/tests/test_financial_api.py
  - 10-3-cost-of-loss-schema-fix-INT-*: apps/api/tests/test_financial_api.py
  - 10-3-cost-of-loss-schema-fix-REG-001: apps/api/tests/ (full suite)
  - 10-3-cost-of-loss-schema-fix-INT-008: apps/api/tests/services/agent/tools/test_cost_of_loss.py
  - 10-3-cost-of-loss-schema-fix-INT-009: apps/api/tests/services/agent/tools/test_financial_impact.py

TEST SPEC END
