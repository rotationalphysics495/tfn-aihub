# Story 10.2: Live Pulse Schema Fix

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **the live production pulse view to load without errors**,
so that **I can see real-time production status across all assets**.

## Acceptance Criteria

1. **Successful API Response**
   - Given an authenticated user navigates to the live pulse view
   - When the `/api/live-pulse` endpoint is called
   - Then the response returns successfully (200) with current asset statuses
   - And no 500 error from querying non-existent `oee_percentage` column

2. **Correct Column References**
   - Given live snapshot data exists for multiple assets
   - When the live pulse endpoint returns data
   - Then each asset entry includes correct status, current output, target output, and financial loss fields
   - And all column references in the Supabase query match the actual `live_snapshots` table schema

3. **OEE Calculation Graceful Handling**
   - Given the `live_snapshots` table does not contain an `oee_percentage` column
   - When the live pulse endpoint aggregates production data
   - Then OEE is either omitted from the snapshot query or derived from available data
   - And the response still includes a valid `oee_percentage` field (defaulting to 0.0 if no OEE data is available)

4. **Existing Tests Pass**
   - All existing `test_live_pulse_api.py` tests continue to pass after the fix
   - Test mock data is updated to match the corrected column references

## Tasks / Subtasks

- [ ] Task 1: Fix the Supabase query column list in `live_pulse.py` (AC: #1, #2)
  - [ ] 1.1 In `get_live_pulse_data()` (line 252-254), remove `oee_percentage` from the `live_snapshots` select string
  - [ ] 1.2 Update the select string to only reference columns that exist in the `live_snapshots` table: `id, asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars, output_variance`
  - [ ] 1.3 Optionally add `downtime_reason, downtime_minutes` to the select if these columns exist (check migration history -- NOTE: these do NOT exist in the schema, see Dev Notes)

- [ ] Task 2: Update OEE aggregation logic (AC: #3)
  - [ ] 2.1 Remove the code block (lines 291-294) that reads `oee_percentage` from snapshot data
  - [ ] 2.2 Set `avg_oee` to `0.0` as the default since `live_snapshots` does not store OEE data
  - [ ] 2.3 Alternatively, if OEE should still be shown, query `daily_summaries` for the most recent OEE values per asset (optional enhancement -- defer to reviewer)

- [ ] Task 3: Fix downtime-related field references (AC: #2)
  - [ ] 3.1 Review the code block (lines 311-326) that reads `downtime_reason` and `downtime_minutes` from snapshots
  - [ ] 3.2 These columns do NOT exist in the `live_snapshots` table schema -- remove references or guard with `.get()` (which is already done, so they safely return `None`)
  - [ ] 3.3 Confirm the active downtime list logic handles missing fields gracefully (it does via `.get()` with fallbacks)

- [ ] Task 4: Update tests to match corrected query (AC: #4)
  - [ ] 4.1 In `test_live_pulse_api.py`, review `SAMPLE_LIVE_SNAPSHOTS` test data -- it includes `oee_percentage` which the mock returns directly; this is fine for mock-based tests since mocks bypass actual DB queries
  - [ ] 4.2 Verify all existing tests pass with the query fix (the mocks return whatever data is in the sample dicts, so query column changes should not break mock-based tests)
  - [ ] 4.3 Add a comment in the test file noting that `oee_percentage` is included in mock data for backward compatibility but does not exist in the actual `live_snapshots` table

- [ ] Task 5: Verify end-to-end (AC: #1-4)
  - [ ] 5.1 Run `pytest apps/api/tests/test_live_pulse_api.py -v` and confirm all tests pass
  - [ ] 5.2 If a local Supabase instance is available, verify the endpoint returns 200 with seed data

## Dev Notes

### Bug Analysis

**Root Cause:** The `get_live_pulse_data()` function in `apps/api/app/api/live_pulse.py` (line 252-254) queries the `live_snapshots` table requesting the column `oee_percentage`. However, this column does NOT exist in the `live_snapshots` table. It exists in the `daily_summaries` table instead.

**What happens at runtime:** When the Supabase client sends the query with `oee_percentage` in the select list, Supabase/PostgREST returns a 400 error (column not found), which the endpoint catches as a generic exception and converts to a 500 Internal Server Error response.

**Scope:** Single-file fix in `apps/api/app/api/live_pulse.py`. The query select string and OEE aggregation logic need updating. Tests may need minor adjustments.

### Actual `live_snapshots` Table Schema

From migration `0003_analytical_cache.sql` + `0022_live_snapshots_financial_loss.sql`:

```sql
CREATE TABLE live_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    snapshot_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    current_output INTEGER,
    target_output INTEGER,
    output_variance INTEGER GENERATED ALWAYS AS (current_output - target_output) STORED,
    status TEXT NOT NULL CHECK (status IN ('on_target', 'behind', 'ahead')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    financial_loss_dollars DECIMAL(12, 2) DEFAULT 0.00  -- Added in migration 0022
);
```

**Columns that EXIST:** `id`, `asset_id`, `snapshot_timestamp`, `current_output`, `target_output`, `output_variance`, `status`, `created_at`, `financial_loss_dollars`

**Columns that do NOT exist (but are queried):**
- `oee_percentage` -- does NOT exist in `live_snapshots` (exists in `daily_summaries`)
- `downtime_reason` -- does NOT exist in `live_snapshots`
- `downtime_minutes` -- does NOT exist in `live_snapshots`

### The Broken Query (Line 252-254)

```python
snapshots_response = client.table("live_snapshots").select(
    "id, asset_id, snapshot_timestamp, current_output, target_output, "
    "oee_percentage, status, financial_loss_dollars, downtime_reason, downtime_minutes"
).order("snapshot_timestamp", desc=True).execute()
```

### The Fixed Query Should Be

```python
snapshots_response = client.table("live_snapshots").select(
    "id, asset_id, snapshot_timestamp, current_output, target_output, "
    "status, financial_loss_dollars"
).order("snapshot_timestamp", desc=True).execute()
```

### Additional Code Impact

After removing `oee_percentage` from the query, the aggregation code at lines 290-294 that reads `snapshot.get("oee_percentage")` will always return `None`, which is already handled gracefully (the value is skipped when `None`). This results in `avg_oee = 0.0` since `oee_count` stays at 0. This is acceptable behavior -- the `ProductionData` model defaults `oee_percentage` to `0.0`.

Similarly, `downtime_reason` (line 311) and `downtime_minutes` (line 315) are accessed via `.get()` which returns `None` when absent. The downtime logic checks `if downtime_reason and downtime_reason.strip()` which safely handles `None`. So these missing columns do not cause runtime errors -- they just result in empty active downtime data.

**Decision Point:** The query currently references 3 non-existent columns. While `downtime_reason` and `downtime_minutes` silently return `None` through `.get()`, `oee_percentage` may cause the query itself to fail at the Supabase/PostgREST level if the server validates column names in the select string. The safest fix is to remove ALL non-existent columns from the select string.

### Seed Data Context

The seed data in `0021_seed_data.sql` inserts into `live_snapshots` with only the columns that actually exist:
```sql
INSERT INTO live_snapshots (asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars) VALUES ...
```

This confirms `oee_percentage`, `downtime_reason`, and `downtime_minutes` are not part of the table.

### Status Enum Mismatch (Secondary Issue)

The original migration defines `status` with CHECK constraint `('on_target', 'behind', 'ahead')`, but the `LivePulsePipeline` writes status values `'above_target'`, `'below_target'`, `'on_target'`. The API endpoint checks for `'above_target'` and `'below_target'` (line 298-308). The seed data uses `'on_target'`, `'behind'`, `'ahead'`. This is a secondary schema mismatch but is NOT in scope for this story -- just be aware of it and do not change status handling logic.

### Architecture Patterns

- **Backend Framework:** Python FastAPI (apps/api)
- **Database Client:** Supabase Python client (`supabase-py`)
- **Query Style:** Supabase client `.table().select().order().execute()` pattern
- **Error Handling:** Generic `except Exception` catches all errors and returns 500
- **Auth:** JWT Bearer token via FastAPI `Depends(get_current_user)`

### Critical Guardrails

- **DO NOT** change the `ProductionData` response model or any Pydantic schemas
- **DO NOT** change the `LivePulseResponse` structure
- **DO NOT** modify the frontend hook `useLivePulse.ts` -- this is a backend-only fix
- **DO NOT** alter the status enum handling logic (even though there's a mismatch)
- **DO NOT** add new database migrations -- the fix is purely in the Python query code
- **DO** remove all non-existent column names from the select string
- **DO** preserve the existing `.get()` fallback pattern for safe field access

### Project Structure Notes

```
apps/api/app/
  api/
    live_pulse.py              # FIX - query column references (this story)
  services/
    pipelines/
      live_pulse.py            # Pipeline that WRITES snapshots (correct columns)

apps/api/tests/
  test_live_pulse_api.py       # Existing tests - verify still pass

supabase/migrations/
  0003_analytical_cache.sql    # Original live_snapshots schema
  0022_live_snapshots_financial_loss.sql  # Added financial_loss_dollars column
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `apps/api/app/api/live_pulse.py` | MODIFY | Remove `oee_percentage`, `downtime_reason`, `downtime_minutes` from select query (line 252-254) |

No new files need to be created. This is a single-file bug fix.

### Testing Guidance

**Automated Tests:**
```bash
# Run existing live pulse tests
pytest apps/api/tests/test_live_pulse_api.py -v

# Run all API tests to check for regressions
pytest apps/api/tests/ -v --timeout=30
```

**Manual Verification:**
1. If local Supabase is running with seed data, call `GET /api/live-pulse` with a valid JWT and confirm 200 response
2. Verify response JSON includes `production.oee_percentage` field (will be `0.0` since no OEE data in live_snapshots)
3. Verify `production.active_downtime` is an empty list (since no downtime columns in live_snapshots)

### References

- [Source: _bmad-output/planning-artifacts/epic-10.md#Story 10.2] - Story requirements and acceptance criteria
- [Source: apps/api/app/api/live_pulse.py#L252-L254] - The broken Supabase select query
- [Source: apps/api/app/api/live_pulse.py#L290-L294] - OEE aggregation logic that reads non-existent column
- [Source: supabase/migrations/0003_analytical_cache.sql#L70-L79] - Original live_snapshots table schema
- [Source: supabase/migrations/0022_live_snapshots_financial_loss.sql] - Added financial_loss_dollars column
- [Source: supabase/migrations/0021_seed_data.sql#L172] - Seed data confirms correct columns
- [Source: apps/api/app/services/pipelines/live_pulse.py#L83-L97] - Pipeline to_dict() shows correct write columns
- [Source: apps/api/tests/test_live_pulse_api.py] - Existing test suite with mock data
- [Source: docs/data-models.md#live_snapshots] - Documentation of table schema (note: docs may be outdated vs actual migrations)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Implementation Summary

Removed non-existent columns (`oee_percentage`, `downtime_reason`, `downtime_minutes`) from the Supabase `live_snapshots` select query in the `/api/live-pulse` endpoint. This fixes the PostgREST 400 error (column not found) that was caught as a generic exception and returned as a 500 Internal Server Error. The existing `.get()` fallback pattern in the aggregation logic already handles missing keys gracefully, so OEE defaults to 0.0 and active_downtime defaults to an empty list.

### Files Created

None

### Files Modified

- `apps/api/app/api/live_pulse.py` - Removed `oee_percentage`, `downtime_reason`, `downtime_minutes` from the select query string at line 252-254; added inline comment documenting schema reality
- `apps/api/tests/test_live_pulse_api.py` - Added comment to `SAMPLE_LIVE_SNAPSHOTS` noting mock/production divergence for `oee_percentage` and `downtime_reason`

### Key Decisions

- Only removed non-existent columns from the select string; did not modify aggregation logic since `.get()` already handles absent keys gracefully
- Did not include `output_variance` (generated column) or `created_at` in the select string since neither is referenced in the aggregation logic
- Left `SAMPLE_LIVE_SNAPSHOTS` mock data unchanged (still includes `oee_percentage` and `downtime_reason`) to maintain backward compatibility with existing mock-based tests; added documentation comment instead

### Tests Added

- `apps/api/tests/test_live_pulse_schema_fix.py` - 20 TDD tests (5 unit + 15 integration) covering all 4 acceptance criteria plus edge cases:
  - UNIT-001 through UNIT-005: Validate select query string excludes invalid columns, includes only valid columns, and `.get()` safely handles missing keys
  - INT-001 through INT-010: Verify endpoint returns 200 with corrected query, OEE defaults to 0.0 when absent, OEE computes when present (backward compat), production data structure correct
  - INT-016 through INT-020: Edge cases - empty snapshots, downtime absent/present, DB exception, multiple snapshots per asset deduplication

### Notes for Reviewer

- The `test_oee_average_calculation` in `test_live_pulse_api.py` still passes because mock data includes `oee_percentage` values. In production, OEE will be 0.0 since the column doesn't exist in `live_snapshots`. This is documented via comments and is expected behavior per story scope.
- Pre-existing test failures (45 failures + 43 errors in broader suite) are unrelated to this change — they involve `test_plant_object_model.py` (missing migration file), `test_memory_crud_api.py`, `test_chat_api.py`, etc.

### Test Results

```
apps/api/tests/test_live_pulse_schema_fix.py: 20 passed (0.15s)
apps/api/tests/test_live_pulse_api.py: 18 passed (0.14s)
apps/api/tests/ (full suite): 1892 passed, 45 failed, 43 errors (31.15s)
  - All 45 failures and 43 errors are pre-existing and unrelated to this change
```

### Acceptance Criteria Status

- [x] AC1: Successful API Response - Fixed select query in `apps/api/app/api/live_pulse.py:253-254`, removing non-existent columns that caused PostgREST 400/500 errors
- [x] AC2: Correct Column References - Select query now references only `id, asset_id, snapshot_timestamp, current_output, target_output, status, financial_loss_dollars` — all valid per migrations 0003 + 0022
- [x] AC3: OEE Calculation Graceful Handling - Existing `.get("oee_percentage")` returns None when absent, `oee_count` stays 0, `avg_oee` defaults to 0.0; `ProductionData.oee_percentage` field defaults to 0.0
- [x] AC4: Existing Tests Pass - All 18 existing tests in `test_live_pulse_api.py` pass unchanged; comment added to mock data noting schema divergence

### Debug Log References

### Completion Notes List

### File List

- `apps/api/app/api/live_pulse.py`
- `apps/api/tests/test_live_pulse_api.py`
- `apps/api/tests/test_live_pulse_schema_fix.py`

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-02-11
**Diff Size**: 883 lines (4 files changed)

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS
- Test Coverage: PASS
- Security: PASS

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | `datetime.utcnow()` deprecated in Python 3.12+ (pre-existing in prod code, 5 new uses in test file) | LOW | Documented |
| 2 | `AsyncMock` imported but unused in `test_live_pulse_schema_fix.py:18` | LOW | Documented |
| 3 | `Decimal` imported but unused in `test_live_pulse_schema_fix.py:16` | LOW | Documented |
| 4 | `call` imported but unused in `test_live_pulse_schema_fix.py:18` | LOW | Documented |
| 5 | Test ID numbering gap: INT-011 through INT-015 missing (non-contiguous but all 20 tests present) | LOW | Documented |
| 6 | f-string in `logger.error()` at `live_pulse.py:443` (pre-existing, not introduced by this change) | LOW | Documented |

**Totals**: 0 HIGH, 0 MEDIUM, 6 LOW

### Fixes Applied
None required — all issues are LOW severity.

### Remaining Issues (Low Severity)
- Unused imports (`AsyncMock`, `Decimal`, `call`) in new test file — cleanup in future sprint
- `datetime.utcnow()` deprecation — project-wide concern, not specific to this story
- Test ID numbering gap — cosmetic, does not affect functionality
- f-string logging — pre-existing pattern, out of scope

### Final Status
Approved

## Test Quality Review

**Reviewer**: Test Architect (TEA)
**Date**: 2026-02-11
**Quality Score**: 100/100 (A+)
**Tests Reviewed**: 20 (test_live_pulse_schema_fix.py) + 18 (test_live_pulse_api.py) = 38 total

### Criteria Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | BDD Format (Given-When-Then) | PASS (+5) | All 20 new tests use explicit Given-When-Then structure |
| 2 | Test ID Conventions | PASS (+5) | UNIT-001–005, INT-001–010, INT-016–020 all present |
| 3 | Hard Waits Detection | PASS | No sleep(), waitForTimeout(), or hardcoded delays |
| 4 | Determinism | PASS (+5) | All tests use fixed mock data via factories |
| 5 | Isolation & Cleanup | PASS (+5) | Per-test mocks via `with patch(...)`, no shared state |
| 6 | Explicit Assertions | PASS | Every test has explicit `assert` statements |
| 7 | Test Length | WARN | 823 lines (exceeds 500-line guideline, but well-structured) |
| 8 | Test Duration | PASS | 38 tests complete in 0.29s total |
| 9 | Fixture Patterns | PASS (+5) | Excellent factory functions: make_snapshot, make_assets, build_mock_supabase |
| 10 | Data Factories | PASS | Factory functions with sensible defaults and override support |
| 11 | Network-First Pattern | N/A | Python mock-based tests, not E2E browser tests |
| 12 | Flakiness Patterns | PASS | No flaky patterns detected |

### Issues Found
- 0 Critical
- 0 High
- 1 Medium: Test file length (823 lines) — well-structured with 4 logical classes, splitting would harm readability
- 0 Low (unused imports fixed)

### Fixes Applied
- Removed unused imports (`AsyncMock`, `Decimal`, `call`) from `test_live_pulse_schema_fix.py:17-18`
- All 38 tests verified passing after fix

### Score Calculation
Starting: 100, Violations: -2 (medium: file length), Bonuses: +20 (BDD +5, isolation +5, determinism +5, fixtures +5, test IDs +5) = 118 → capped at 100
