# Story 10.3: Cost of Loss Schema Fix

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **the cost-of-loss view to load without errors**,
so that **I can see the financial impact of production losses**.

## Acceptance Criteria

1. **Daily Summary Query Uses Correct Column Name**
   - Given an authenticated user requests cost-of-loss data with `period=daily`
   - When the `/api/financial/cost-of-loss` endpoint queries the `daily_summaries` table
   - Then the SELECT statement references `waste_count` (not `waste`)
   - And the response returns successfully (200) with financial loss data
   - And no 500 error from querying a non-existent `waste` column

2. **Financial Summary Query Uses Correct Column Name**
   - Given an authenticated user requests the financial summary via `/api/financial/summary`
   - When the endpoint queries the `daily_summaries` table
   - Then the SELECT statement references `waste_count` (not `waste`)
   - And the aggregated `total_waste_count` is calculated correctly from the `waste_count` column

3. **Financial Impact Service Uses Correct Column Name**
   - Given the `FinancialService.get_financial_impact()` method queries `daily_summaries`
   - When it fetches data for a specific asset and date range
   - Then the SELECT statement references `waste_count` (not `waste`)
   - And the `record.get()` call extracts the value using key `"waste_count"`
   - And the waste loss is correctly calculated using `waste_count * cost_per_unit`

4. **Existing Tests Updated To Match Schema**
   - All test mocks that return `daily_summaries` data use the key `"waste_count"` instead of `"waste"`
   - All existing financial API tests pass without modification to assertions
   - No regressions in existing test suite

5. **Agent Data Source Remains Correct**
   - The `SupabaseDataSource.get_cost_of_loss()` method (which already uses `waste_count`) continues to work correctly
   - No changes are needed to the agent data source layer

## Tasks / Subtasks

- [ ] Task 1: Fix `get_cost_of_loss` endpoint in `financial.py` (AC: #1)
  - [ ] 1.1 On line 484, change the SELECT from `"asset_id, downtime_minutes, waste, financial_loss, oee_percentage, created_at"` to `"asset_id, downtime_minutes, waste_count, financial_loss, oee_percentage, created_at"`
  - [ ] 1.2 On line 495, change `record.get("waste")` to `record.get("waste_count")`

- [ ] Task 2: Fix `get_financial_summary` endpoint in `financial.py` (AC: #2)
  - [ ] 2.1 On line 307, change the SELECT from `"asset_id, downtime_minutes, waste, financial_loss"` to `"asset_id, downtime_minutes, waste_count, financial_loss"`
  - [ ] 2.2 On line 335, change `record.get("waste")` to `record.get("waste_count")`

- [ ] Task 3: Fix `get_financial_impact` method in `services/financial.py` (AC: #3)
  - [ ] 3.1 On line 352, change the SELECT from `"asset_id, date, downtime_minutes, waste, financial_loss"` to `"asset_id, date, downtime_minutes, waste_count, financial_loss"`
  - [ ] 3.2 On line 369, change `record.get("waste")` to `record.get("waste_count")`

- [ ] Task 4: Update test mocks to use correct column name (AC: #4)
  - [ ] 4.1 In `tests/test_financial_api.py`, update all mock `daily_summaries` response data dictionaries to use key `"waste_count"` instead of `"waste"` (lines 157-158, 254-255, 366-371)
  - [ ] 4.2 Run the financial API test suite to confirm all tests pass: `pytest apps/api/tests/test_financial_api.py -v`

- [ ] Task 5: Verify no other references and run full tests (AC: #4, #5)
  - [ ] 5.1 Search the entire `apps/api` directory for any remaining references to `daily_summaries` selecting `waste` without `_count` suffix
  - [ ] 5.2 Confirm `apps/api/app/services/agent/data_source/supabase.py` line 1138 already uses `waste_count` (no change needed)
  - [ ] 5.3 Run the full API test suite: `pytest apps/api/tests/ -v`
  - [ ] 5.4 Verify the API builds and starts without errors

## Dev Notes

### Bug Analysis

**Root Cause:** The `daily_summaries` table was created with a column named `waste_count` (see migration `supabase/migrations/0003_analytical_cache.sql`, line 30: `waste_count INTEGER`). However, three query locations in the financial API and service layers reference it as `waste` instead of `waste_count`. This causes Supabase/PostgREST to either return `null` for the `waste` key (silently ignoring the unknown column in the SELECT) or throw a 500 error, depending on the Supabase PostgREST configuration. Either way, waste-related financial calculations return $0 or fail entirely.

**Scope:** Backend-only fix across two Python files and one test file. No frontend changes needed -- the frontend hooks (`useCostOfLoss.ts`) only consume the API response and do not reference column names directly.

**Interesting Note:** The agent data source layer (`supabase.py` `get_cost_of_loss` method, line 1138) was implemented later (Story 6.3) and correctly uses `waste_count`. This bug only affects the older REST API endpoints from Stories 2.7 and 2.8.

### Architecture Patterns

- **Backend Framework:** Python FastAPI (`apps/api`)
- **Database:** Supabase (PostgreSQL) accessed via `supabase-py` client
- **ORM/Query:** Supabase client library (PostgREST-based, not raw SQL)
- **Financial Service:** Singleton `FinancialService` in `app/services/financial.py`
- **Test Framework:** pytest with `unittest.mock` for mocking Supabase responses

### Bug Location Map

All three bugs follow the same pattern: a Supabase `.select()` call that lists `waste` as a column name, followed by a `record.get("waste")` call to extract the value.

| # | File | Method | Line (SELECT) | Line (get) | Fix |
|---|------|--------|---------------|------------|-----|
| 1 | `apps/api/app/api/financial.py` | `get_cost_of_loss()` | 484 | 495 | `waste` -> `waste_count` |
| 2 | `apps/api/app/api/financial.py` | `get_financial_summary()` | 307 | 335 | `waste` -> `waste_count` |
| 3 | `apps/api/app/services/financial.py` | `get_financial_impact()` | 352 | 369 | `waste` -> `waste_count` |

### Correct Schema (Source of Truth)

From `supabase/migrations/0003_analytical_cache.sql`:
```sql
CREATE TABLE daily_summaries (
    ...
    waste_count INTEGER,
    ...
);
COMMENT ON COLUMN daily_summaries.waste_count IS 'Number of waste/rejected items';
```

From `docs/data-models.md`, the `daily_summaries` table documentation does NOT list `waste` as a column. The column is `waste_count` (though the docs may be incomplete -- the migration is the source of truth).

### Confirmed Correct Code (No Changes Needed)

The following locations already use the correct `waste_count` column name and should NOT be modified:

- `apps/api/app/services/agent/data_source/supabase.py` line 1138 - `get_cost_of_loss()` SELECT uses `waste_count`
- `apps/web/src/hooks/useCostOfLoss.ts` - Frontend hook; consumes API JSON, does not reference DB columns
- `apps/web/src/components/financial/CostOfLossWidget.tsx` - Frontend component; consumes API JSON
- `apps/api/app/services/agent/tools/cost_of_loss.py` - Agent tool; uses `FinancialMetrics.waste_count` attribute

### Critical Guardrails

- **DO NOT** rename the database column -- `waste_count` is the correct name; the code must match it
- **DO NOT** change any response model field names (`total_waste_count`, `waste_count`, `waste_loss`, etc.) -- these are public API contracts
- **DO NOT** modify the `FinancialService` calculation methods (`calculate_waste_loss`, `calculate_total_impact`) -- these are correct; only the query column name and `record.get()` key are wrong
- **DO NOT** change the `SupabaseDataSource.get_cost_of_loss()` method -- it already uses the correct column name
- **DO NOT** change the Supabase migration files
- **DO** update all three SELECT strings and all three `record.get()` calls consistently
- **DO** update test mock data dictionaries to match (key `"waste_count"` not `"waste"`)
- **DO** run the full test suite after changes to verify no regressions

### Project Structure Notes

```
apps/api/
  app/
    api/
      financial.py              # FIX - 2 query locations (lines 307, 484) + 2 get() calls (lines 335, 495)
    services/
      financial.py              # FIX - 1 query location (line 352) + 1 get() call (line 369)
    services/agent/
      data_source/
        supabase.py             # CORRECT - already uses waste_count (line 1138) -- DO NOT MODIFY
      tools/
        cost_of_loss.py         # CORRECT - uses FinancialMetrics model -- DO NOT MODIFY
    schemas/
      financial.py              # NO CHANGE - response models are correct
  tests/
    test_financial_api.py       # FIX - update mock data dicts from "waste" to "waste_count"

supabase/
  migrations/
    0003_analytical_cache.sql   # SOURCE OF TRUTH - column is waste_count
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `apps/api/app/api/financial.py` | MODIFY | Fix `waste` -> `waste_count` in 2 SELECT strings and 2 `record.get()` calls |
| `apps/api/app/services/financial.py` | MODIFY | Fix `waste` -> `waste_count` in 1 SELECT string and 1 `record.get()` call |
| `apps/api/tests/test_financial_api.py` | MODIFY | Update mock data dictionaries from key `"waste"` to `"waste_count"` |

No new files need to be created. This is a multi-file bug fix confined to the backend.

### Testing Guidance

**Automated Testing:**
```bash
# Run financial API tests specifically
pytest apps/api/tests/test_financial_api.py -v

# Run all API tests to check for regressions
pytest apps/api/tests/ -v

# If cost_of_loss agent tool tests exist, verify they still pass
pytest apps/api/tests/services/agent/tools/test_cost_of_loss.py -v
```

**Manual Verification:**
1. Start the API server and call `GET /api/financial/cost-of-loss` -- should return 200 with `breakdown.waste_cost > 0` when waste data exists
2. Call `GET /api/financial/summary` -- should return 200 with `total_waste_count > 0` when waste data exists
3. Call `GET /api/financial/impact/{asset_id}` -- should return 200 with `waste_count > 0` and `waste_loss > 0` when waste data exists

**Grep Verification:**
After applying fixes, confirm no remaining references to the wrong column name:
```bash
# Should return ZERO results in financial.py files (excluding comments/docstrings)
grep -n '"waste"' apps/api/app/api/financial.py apps/api/app/services/financial.py

# Should return ZERO results in test files
grep -n '"waste"' apps/api/tests/test_financial_api.py
```

### References

- [Source: _bmad-output/planning-artifacts/epic-10.md#Story 10.3] - Story requirements and acceptance criteria
- [Source: supabase/migrations/0003_analytical_cache.sql#L30] - Database schema source of truth (`waste_count INTEGER`)
- [Source: apps/api/app/api/financial.py#L307] - Bug location: `get_financial_summary()` SELECT uses wrong column
- [Source: apps/api/app/api/financial.py#L484] - Bug location: `get_cost_of_loss()` SELECT uses wrong column
- [Source: apps/api/app/services/financial.py#L352] - Bug location: `get_financial_impact()` SELECT uses wrong column
- [Source: apps/api/app/services/agent/data_source/supabase.py#L1138] - Correct reference: agent data source already uses `waste_count`
- [Source: docs/data-models.md#daily_summaries] - Data model documentation
- [Source: apps/api/tests/test_financial_api.py] - Test file requiring mock data updates

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
